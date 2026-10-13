"""Run the (collection x serialization x seed) grid of GRU units, optionally over worker processes.

Units are ordered seed-major so a partial run always holds complete seeds first, and are
skipped when both of their output files exist. ``--workers N`` launches N child processes,
each taking every N-th unit; the cap on CPU processes is the caller's to respect.
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
import time
import traceback
from collections.abc import Sequence
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[2]
for _path in (str(_HERE), str(_REPO_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import ng_model  # noqa: E402
from ng_data import SERIALIZATIONS, NeuralGenError  # noqa: E402
from train_sample import (  # noqa: E402
    DEFAULT_RESULTS_DIR,
    N_DRAWS,
    RQ6_INDEX,
    CollectionBundle,
    UnitSpec,
    run_unit,
)

logger = logging.getLogger(__name__)

COLLECTIONS: tuple[str, ...] = ("ndc_classes", "wd50k66")
PILOT_SEEDS = 3
FULL_SEEDS = 27


def parse_seeds(text: str) -> list[int]:
    """``pilot`` (first 3 RQ6 seeds), ``all`` (27), or a comma-separated list of seeds.

    Raises
    ------
    NeuralGenError
        If the text is none of these.
    """
    from experiments.tkde.config import seeds

    if text == "pilot":
        return seeds(RQ6_INDEX, FULL_SEEDS)[:PILOT_SEEDS]
    if text == "all":
        return seeds(RQ6_INDEX, FULL_SEEDS)
    try:
        return [int(part) for part in text.split(",") if part]
    except ValueError as exc:
        raise NeuralGenError(f"cannot parse seeds {text!r}") from exc


def build_units(
    collections: Sequence[str], serializations: Sequence[str], seeds: Sequence[int]
) -> list[UnitSpec]:
    """Seed-major unit list."""
    return [
        UnitSpec(collection, serialization, seed)
        for seed in seeds
        for collection in collections
        for serialization in serializations
    ]


def parse_shard(text: str) -> tuple[int, int]:
    """``"i/N"`` -> ``(i, N)`` with ``0 <= i < N``."""
    index, count = (int(part) for part in text.split("/"))
    if not 0 <= index < count:
        raise NeuralGenError(f"shard {text!r} is out of range")
    return index, count


def run_shard(
    units: Sequence[UnitSpec],
    out_dir: Path,
    config: ng_model.GRUConfig,
    n_draws: int,
    force: bool,
) -> int:
    """Run the given units in this process; return the number of failed units."""
    bundles: dict[str, CollectionBundle] = {}
    failures = 0
    for position, unit in enumerate(units, start=1):
        started = time.perf_counter()
        try:
            if unit.collection not in bundles:
                bundles[unit.collection] = CollectionBundle.load(unit.collection)
            summary = run_unit(
                bundles[unit.collection], unit, out_dir, config, n_draws=n_draws, force=force
            )
        except Exception:  # noqa: BLE001 - one failed unit must not stop the shard; it is counted and logged
            failures += 1
            logger.error("unit %s FAILED:\n%s", unit.stem, traceback.format_exc())
            continue
        logger.info(
            "[%d/%d] %s %s in %.0fs",
            position,
            len(units),
            unit.stem,
            "skipped" if summary.get("skipped") else "done",
            time.perf_counter() - started,
        )
    return failures


def main(argv: Sequence[str] | None = None) -> int:
    """Command line entry point; returns the process exit code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collections", default=",".join(COLLECTIONS))
    parser.add_argument("--serializations", default=",".join(SERIALIZATIONS))
    parser.add_argument("--seeds", default="pilot", help="pilot | all | comma-separated seeds")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--n-draws", type=int, default=N_DRAWS)
    parser.add_argument("--lr", type=float, default=ng_model.GRUConfig.lr)
    parser.add_argument("--patience", type=int, default=ng_model.GRUConfig.patience)
    parser.add_argument("--max-epochs", type=int, default=ng_model.GRUConfig.max_epochs)
    parser.add_argument("--shard", default="0/1")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if args.workers > 1:
        children = [
            subprocess.Popen(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    *_forwarded(args),
                    "--shard",
                    f"{i}/{args.workers}",
                ]
            )
            for i in range(args.workers)
        ]
        return int(any(child.wait() for child in children))

    units = build_units(
        args.collections.split(","), args.serializations.split(","), parse_seeds(args.seeds)
    )
    index, count = parse_shard(args.shard)
    mine = units[index::count]
    logger.info("shard %d/%d: %d of %d units", index, count, len(mine), len(units))
    import torch

    torch.set_num_threads(1)
    config = ng_model.GRUConfig(lr=args.lr, patience=args.patience, max_epochs=args.max_epochs)
    failures = run_shard(mine, args.out_dir, config, args.n_draws, args.force)
    return int(failures > 0)


def _forwarded(args: argparse.Namespace) -> list[str]:
    forwarded = [
        "--collections",
        args.collections,
        "--serializations",
        args.serializations,
        "--seeds",
        args.seeds,
        "--out-dir",
        str(args.out_dir),
        "--n-draws",
        str(args.n_draws),
        "--lr",
        repr(args.lr),
        "--patience",
        str(args.patience),
        "--max-epochs",
        str(args.max_epochs),
    ]
    return [*forwarded, "--force"] if args.force else forwarded


if __name__ == "__main__":
    sys.exit(main())
