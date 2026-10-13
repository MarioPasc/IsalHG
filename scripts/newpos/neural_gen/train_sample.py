"""Train one GRU on one serialization of one collection, sample 10,000 draws, decode and write them.

One call is one unit ``(collection, serialization, seed)``. Output is the frozen
gzipped JSONL sample file plus a per-unit JSON summary, both written atomically.
"""

from __future__ import annotations

import argparse
import logging
import math
import resource
import subprocess
import sys
import time
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[2]
for _path in (str(_HERE), str(_REPO_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import ng_decode  # noqa: E402
import ng_model  # noqa: E402
import torch  # noqa: E402
from ng_data import (  # noqa: E402
    GENERATOR_NAMES,
    SERIALIZATIONS,
    CollectionLike,
    NeuralGenError,
    Vocabulary,
    serialization_sequences,
    split_members,
)

logger = logging.getLogger(__name__)

DEFAULT_RESULTS_DIR = Path(
    "/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/NEWPOS_2026-10-13/neural_gen"
)
RQ6_CONFIG = _REPO_ROOT / "experiments" / "tkde" / "configs" / "rq6.yaml"
RQ6_INDEX = 6
N_DRAWS = 10_000
CAP_FACTOR = 1.25


@dataclass(frozen=True)
class UnitSpec:
    """One ``(collection, serialization, seed)`` unit."""

    collection: str
    serialization: str
    seed: int

    @property
    def generator(self) -> str:
        """Generator name written into the sample file."""
        return GENERATOR_NAMES[self.serialization]

    @property
    def stem(self) -> str:
        """File stem shared by the sample file and the summary."""
        return f"{self.collection}__{self.generator}__s{self.seed}"


@dataclass
class CollectionBundle:
    """A collection context with the quantities every unit of it re-uses."""

    ctx: CollectionLike
    spec: ng_decode.DecodeSpec
    keys: list[ng_decode.ClassKey]

    @classmethod
    def from_context(cls, ctx: CollectionLike) -> CollectionBundle:
        """Compute the decoder spec and the members' class keys once."""
        spec = ng_decode.DecodeSpec(n_types=ctx.n_types, n_preds=ctx.n_preds, k=ctx.k)
        return cls(ctx=ctx, spec=spec, keys=ng_decode.member_keys(ctx.hypergraphs))

    @classmethod
    def load(cls, collection: str) -> CollectionBundle:
        """Build the collection context exactly as the n-gram experiment does."""
        from experiments.tkde import rq6
        from experiments.tkde.config import load_yaml

        config = load_yaml(RQ6_CONFIG)
        return cls.from_context(rq6.build_context(collection, config, None))


def sample_path(out_dir: Path, unit: UnitSpec) -> Path:
    """Path of the gzipped JSONL sample file."""
    return out_dir / f"{unit.stem}.jsonl.gz"


def summary_path(out_dir: Path, unit: UnitSpec) -> Path:
    """Path of the per-unit JSON summary."""
    return out_dir / f"{unit.stem}.summary.json"


def _git_sha() -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(_REPO_ROOT), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return out.stdout.strip()


def root_bits_per_kb(train_roots: Sequence[int], test_roots: Sequence[int], n_types: int) -> float:
    """Mean code length of the root type under the add-one-smoothed training root law.

    The ordered-walk word does not write the root's type; this is what the missing
    symbol would cost, reported beside (not inside) the word's bits.
    """
    counts = Counter(train_roots)
    total = len(train_roots) + max(1, n_types)
    bits = [-math.log2((counts[r] + 1) / total) for r in test_roots]
    return sum(bits) / len(bits)


def run_unit(
    bundle: CollectionBundle,
    unit: UnitSpec,
    out_dir: Path,
    config: ng_model.GRUConfig,
    *,
    n_draws: int = N_DRAWS,
    device: torch.device | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Train, sample, decode and write one unit.

    Parameters
    ----------
    bundle : CollectionBundle
        Output of :meth:`CollectionBundle.load`.
    unit : UnitSpec
        The unit.
    out_dir : Path
        Directory receiving ``<stem>.jsonl.gz`` and ``<stem>.summary.json``.
    config : ng_model.GRUConfig
        Shared hyperparameters.
    n_draws : int, optional
        Number of draws.
    device : torch.device or None, optional
        Defaults to CUDA when available.
    force : bool, optional
        Recompute even if both outputs exist.

    Returns
    -------
    dict[str, Any]
        The summary that was written (or read, when the unit is already done).

    Raises
    ------
    NeuralGenError
        On an unknown serialization.
    """
    if unit.serialization not in SERIALIZATIONS:
        raise NeuralGenError(f"unknown serialization {unit.serialization!r}")
    out_dir.mkdir(parents=True, exist_ok=True)
    sample_file, summary_file = sample_path(out_dir, unit), summary_path(out_dir, unit)
    if not force and sample_file.is_file() and summary_file.is_file():
        import json

        return {**json.loads(summary_file.read_text(encoding="utf-8")), "skipped": True}

    device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()
    ng_model.seed_everything(unit.seed)

    ctx = bundle.ctx
    sequences = serialization_sequences(ctx, unit.serialization)
    vocab = Vocabulary.fit(sequences)
    id_sequences = [vocab.encode(s) for s in sequences]
    train_idx, val_idx, test_idx = split_members(len(sequences), unit.collection, unit.seed)
    train_ids = [id_sequences[i] for i in train_idx]
    val_ids = [id_sequences[i] for i in val_idx]
    test_ids = [id_sequences[i] for i in test_idx]
    max_train_len = max(len(sequences[i]) for i in train_idx)
    max_len = math.ceil(CAP_FACTOR * max_train_len)

    model = ng_model.GRULM(len(vocab), config).to(device)
    fit = ng_model.fit(model, train_ids, val_ids, config, unit.seed, device)
    test = ng_model.evaluate(model, test_ids, device)

    sample_started = time.perf_counter()
    drawn_ids, capped = ng_model.sample_sequences(
        model, n_draws, max_len, device, unit.seed, config
    )
    sample_secs = time.perf_counter() - sample_started

    decode_started = time.perf_counter()
    roots: list[int | None]
    if unit.serialization == "ow":
        train_roots = [ctx.ow_roots[i] for i in train_idx]
        roots = list(ng_decode.draw_roots(unit.collection, unit.seed, train_roots, n_draws))
    else:
        roots = [None] * n_draws
    outcomes = [
        ng_decode.process_draw(
            unit.collection,
            unit.serialization,
            unit.generator,
            unit.seed,
            draw,
            vocab.decode(ids),
            roots[draw],
            bundle.spec,
        )
        for draw, ids in enumerate(drawn_ids)
    ]
    train_keys = {bundle.keys[i] for i in train_idx}
    heldout_keys = {bundle.keys[i] for i in (*val_idx, *test_idx)}
    counts = ng_decode.tally(outcomes, capped, train_keys, heldout_keys)
    decode_secs = time.perf_counter() - decode_started

    ng_decode.write_samples_atomic(sample_file, outcomes)
    sample_lengths = [len(ids) for ids in drawn_ids]
    summary: dict[str, Any] = {
        "collection": unit.collection,
        "serialization": unit.serialization,
        "generator": unit.generator,
        "seed": unit.seed,
        "n_members": len(sequences),
        "n_train": len(train_idx),
        "n_val": len(val_idx),
        "n_test": len(test_idx),
        "vocab_tokens": len(vocab.tokens),
        "max_train_len": max_train_len,
        "max_len": max_len,
        "mean_train_len": sum(len(s) for s in train_ids) / len(train_ids),
        "mean_sample_len": sum(sample_lengths) / len(sample_lengths),
        "epochs_run": fit["epochs_run"],
        "best_epoch": fit["best_epoch"],
        "stopped_early": fit["stopped_early"],
        "best_val_nats_per_kb": fit["best_val_nats_per_kb"],
        "best_val_bits_per_kb": fit["best_val_nats_per_kb"] / math.log(2.0),
        "test_bits_per_kb": test["bits_per_kb"],
        "test_bits_per_token": test["bits_per_token"],
        "test_nats_per_kb": test["nats_per_kb"],
        "test_root_bits_per_kb": (
            root_bits_per_kb(
                [ctx.ow_roots[i] for i in train_idx],
                [ctx.ow_roots[i] for i in test_idx],
                ctx.n_types,
            )
            if unit.serialization == "ow"
            else None
        ),
        **counts,
        "train_secs": fit["train_secs"],
        "sample_secs": sample_secs,
        "decode_secs": decode_secs,
        "wall_secs": time.perf_counter() - started,
        "peak_gpu_mb": (
            torch.cuda.max_memory_allocated() / 2**20 if device.type == "cuda" else None
        ),
        "peak_rss_mb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
        "history": fit["history"],
        "config": config.as_dict(),
        "decode_spec": {
            "n_types": bundle.spec.n_types,
            "n_preds": bundle.spec.n_preds,
            "k": bundle.spec.k,
        },
        "torch": torch.__version__,
        "device": str(device),
        "device_name": torch.cuda.get_device_name(device) if device.type == "cuda" else "cpu",
        "git_sha": _git_sha(),
        "skipped": False,
    }
    ng_decode.write_json_atomic(summary_file, summary)
    logger.info(
        "%s: epochs %d (best %d) test %.1f bits/KB usable %.4f vun %.4f wall %.0fs",
        unit.stem,
        summary["epochs_run"],
        summary["best_epoch"],
        summary["test_bits_per_kb"],
        summary["usable_per_draw"],
        summary["vun_per_draw"],
        summary["wall_secs"],
    )
    return summary


def main(argv: Sequence[str] | None = None) -> None:
    """Command line entry point for a single unit."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection", required=True)
    parser.add_argument("--serialization", required=True, choices=SERIALIZATIONS)
    parser.add_argument("--seed", type=int, default=RQ6_INDEX * 10_000)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--n-draws", type=int, default=N_DRAWS)
    parser.add_argument("--max-epochs", type=int, default=ng_model.GRUConfig.max_epochs)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    config = ng_model.GRUConfig(max_epochs=args.max_epochs)
    bundle = CollectionBundle.load(args.collection)
    unit = UnitSpec(args.collection, args.serialization, args.seed)
    summary = run_unit(bundle, unit, args.out_dir, config, n_draws=args.n_draws, force=args.force)
    print(
        f"{unit.stem}: usable/draw {summary['usable_per_draw']:.4f} "
        f"vun/draw {summary['vun_per_draw']:.4f} test bits/KB {summary['test_bits_per_kb']:.1f}"
    )


if __name__ == "__main__":
    main()
