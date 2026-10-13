"""Sample the three RQ6 n-gram generators and write them in the frozen JSONL format.

The sampling and decoding replicate ``experiments.tkde.rq6.run_sample_unit``
exactly: a freshly fitted order-3 model per unit (``CollectionContext.model``),
``model.sample(n, seed=, max_len=)``, the seeded root-type draw for the
ordered-walk alphabet, and the strict decoder for the incidence list. Nothing is
filtered here; filtering to the usable subset is the evaluator's job.
"""

from __future__ import annotations

import argparse
import gzip
import json
import logging
import multiprocessing as mp
import random
import sys
import time
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.newpos.genbench import common as gb  # noqa: E402

if TYPE_CHECKING:
    from experiments.tkde.rq6 import CollectionContext
    from isalhg.core.sparse_hypergraph import SparseHypergraph

logger = logging.getLogger("genbench.sample")

MAX_WORKERS = 6
_CONTEXTS: dict[str, CollectionContext] = {}


def rq6_config() -> dict[str, Any]:
    """Load RQ6's frozen configuration."""
    import yaml

    with (gb.REPO_ROOT / "experiments/tkde/configs/rq6.yaml").open() as handle:
        return dict(yaml.safe_load(handle))


def rq6_seeds(config: dict[str, Any]) -> list[int]:
    """RQ6's replication seeds."""
    from experiments.tkde.config import seeds

    return list(seeds(6, int(config["seed_count"])))


def _context(name: str, corpus_root: str, config: dict[str, Any]) -> CollectionContext:
    if name not in _CONTEXTS:
        from experiments.tkde.rq6 import build_context

        _CONTEXTS[name] = build_context(name, config, Path(corpus_root))
    return _CONTEXTS[name]


def _kb_of(H: SparseHypergraph) -> gb.KB:
    """The ``(n, types, facts)`` triple of a decoded hypergraph."""
    n = H.n_nodes
    types = tuple(H.vertex_label(v) for v in range(n))
    facts = tuple((int(label), tuple(sorted(members))) for _, members, label in H.iter_edges())
    return n, types, facts


def _token_strings(word: Sequence[Any]) -> list[str]:
    """Serialise a word's tokens; tuple tokens become compact JSON arrays."""
    return [t if isinstance(t, str) else json.dumps(t, separators=(",", ":")) for t in word]


def sample_unit(
    context: CollectionContext, kind: str, seed: int, n_samples: int, max_len: int
) -> Iterator[dict[str, Any]]:
    """Yield the frozen-format records of one ``(collection, model, seed)`` unit.

    Parameters
    ----------
    context : experiments.tkde.rq6.CollectionContext
        The collection's cached derivations.
    kind : str
        ``ow_ngram``, ``fact_ngram`` or ``incidence_ngram``.
    seed : int
        RQ6 sampling seed.
    n_samples, max_len : int
        Draws per unit and the token cap.

    Yields
    ------
    dict
        One record per draw, keys exactly those of the frozen contract.
    """
    from experiments.tkde import rq6
    from isalhg.core.fact_word import decode_fact_word
    from isalhg.generation.incidence_baseline import strict_decode, strict_decode_reason

    model = context.model(kind)
    words = model.sample(n_samples, seed=seed, max_len=max_len)
    root_rng = random.Random(f"rq6-ow-root|{context.name}|{seed}")
    for draw, word in enumerate(words):
        root_type: int | None = None
        reason: str | None = None
        H: Any = None
        if kind == rq6.MODEL_OURS:
            H, _ = decode_fact_word(word, n_types=context.n_types, n_preds=context.n_preds)
        elif kind == rq6.MODEL_OW:
            root_type = root_rng.choice(context.ow_roots) if context.ow_roots else 0
            try:
                H = rq6._ow_decode(word, context.k, context.n_types, context.n_preds, root_type)
            except Exception as exc:  # noqa: BLE001 - recorded as a rejection, as in RQ6
                reason = type(exc).__name__
        else:
            H = strict_decode(word, n_types=context.n_types, n_preds=context.n_preds)
            if H is None:
                reason = (
                    strict_decode_reason(word, n_types=context.n_types, n_preds=context.n_preds)
                    or "unknown"
                )
        yield _record(context.name, kind, seed, draw, word, root_type, H, reason)


def _record(
    collection: str,
    kind: str,
    seed: int,
    draw: int,
    word: Sequence[Any],
    root_type: int | None,
    H: SparseHypergraph | None,
    reason: str | None,
) -> dict[str, Any]:
    kb = None if H is None else _kb_of(H)
    return {
        "collection": collection,
        "generator": kind,
        "seed": seed,
        "draw": draw,
        "tokens": _token_strings(word),
        "root_type": root_type,
        "status": "rejected" if H is None else "decoded",
        "reason": reason,
        "n": None if kb is None else kb[0],
        "types": None if kb is None else list(kb[1]),
        "facts": None if kb is None else [[p, list(m)] for p, m in kb[2]],
        "connected": None if H is None else bool(H.is_connected()),
    }


def unit_path(out: Path, collection: str, kind: str, seed: int, seeds: Sequence[int]) -> Path:
    """Plain ``.jsonl`` for the first three seeds (inspection), ``.jsonl.gz`` otherwise."""
    stem = gb.unit_stem(collection, kind, seed)
    plain = seed in set(sorted(seeds)[: gb.N_UNCOMPRESSED_SEEDS])
    return out / f"{stem}.jsonl" if plain else out / f"{stem}.jsonl.gz"


def _task(args: tuple[Any, ...]) -> tuple[str, float]:
    collection, kind, seed, path, corpus_root, config, n_samples, max_len = args
    started = time.perf_counter()
    context = _context(collection, corpus_root, config)
    target = Path(path)
    tmp = target.with_name(target.name + ".part")
    opener = gzip.open if target.suffix == ".gz" else open
    with opener(tmp, "wt", encoding="utf-8") as handle:
        for record in sample_unit(context, kind, seed, n_samples, max_len):
            handle.write(json.dumps(record, separators=(",", ":")) + "\n")
    tmp.replace(target)
    return target.name, time.perf_counter() - started


def run(args: argparse.Namespace) -> None:
    """Sample every missing unit in parallel."""
    config = rq6_config()
    seeds = rq6_seeds(config)
    if args.n_seeds:
        seeds = seeds[: args.n_seeds]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    n_samples = int(args.n_samples or config["n_samples"])
    max_len = int(config.get("max_len", gb.MAX_LEN))
    tasks = []
    for collection in args.collection:
        for kind in args.generator or gb.NGRAM_ARMS:
            for seed in seeds:
                path = unit_path(out, collection, kind, seed, rq6_seeds(config))
                if path.exists() and not args.force:
                    continue
                tasks.append(
                    (
                        collection,
                        kind,
                        seed,
                        str(path),
                        str(args.corpus_root),
                        config,
                        n_samples,
                        max_len,
                    )
                )
    workers = max(1, min(int(args.workers), MAX_WORKERS))
    print(
        f"[sample] {len(tasks)} pending units, {workers} workers, {n_samples} draws each",
        flush=True,
    )
    started = time.perf_counter()
    if tasks:
        with mp.get_context("spawn").Pool(workers, maxtasksperchild=12) as pool:
            for i, (name, secs) in enumerate(pool.imap_unordered(_task, tasks), 1):
                print(
                    f"[sample] {i}/{len(tasks)} {name} {secs:.0f}s "
                    f"(elapsed {time.perf_counter() - started:.0f}s)",
                    flush=True,
                )


def build_parser() -> argparse.ArgumentParser:
    """Command-line interface."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", required=True, help="directory for the frozen-format files")
    p.add_argument("--collection", action="append", default=None)
    p.add_argument("--generator", action="append", choices=list(gb.NGRAM_ARMS))
    p.add_argument("--n-seeds", type=int, help="use only the first k RQ6 seeds")
    p.add_argument("--n-samples", type=int, help="draws per unit (default: RQ6's 10,000)")
    p.add_argument("--workers", type=int, default=MAX_WORKERS)
    p.add_argument("--corpus-root", default=str(gb.CORPUS_ROOT))
    p.add_argument("--force", action="store_true")
    return p


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    parsed = build_parser().parse_args()
    parsed.collection = parsed.collection or list(gb.COLLECTIONS)
    run(parsed)
