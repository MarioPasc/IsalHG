"""Score the usable samples of any frozen-format sample directory against a collection.

Per ``(collection, generator, seed)`` unit it reports yield (decoded, connected,
usable, unique, novel, VUN per draw), the five RQ6 JSDs on all decoded and on
usable samples, W1 on n and m, the star/relational structure of the usable
samples and the collection's own values. It never assumes the generator is an
n-gram: it only reads the frozen JSONL contract.

The derived repair arm ``<generator>_lcc`` (``--repair-lcc-of``) keeps the largest
connected component of every decoded sample of a fact-list generator.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import gzip
import json
import logging
import math
import multiprocessing as mp
import sys
import time
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.newpos.genbench import common as gb  # noqa: E402

logger = logging.getLogger("genbench.evaluate")

MAX_WORKERS = 6
N_SPLITS = 27
RESAMPLE_SIZE = 10_000

ROW_COLUMNS: tuple[str, ...] = (
    "collection",
    "generator",
    "seed",
    "source_generator",
    "n_draws",
    "n_decoded",
    "n_rejected",
    "n_connected",
    "n_empty",
    "n_usable",
    "n_unique_usable",
    "n_novel_usable",
    "n_unique_novel_usable",
    "n_singleton_novel_usable",
    "vun_per_draw",
    "vun_singleton_per_draw",
    "validity",
    "connectivity",
    "usable_rate",
    "fidelity_ok",
    "n_flag_mismatch",
    "n_key_error",
    "n_lcc_rule_disagree",
    "reasons",
    *(f"jsd_{k}_all" for k in gb.PROFILE_KEYS),
    *(f"jsd_{k}_use" for k in gb.PROFILE_KEYS),
    "w1_n_use",
    "w1_m_use",
    "mean_n_use",
    "mean_m_use",
    "star_frac_use",
    "rel_frac_use",
    "rel_dev_use",
    "shared_use",
    "n_usable_inenv",
    "n_unique_novel_inenv",
    "vun_inenv_per_draw",
    "jsd_n_inenv",
    "jsd_m_inenv",
    "w1_m_inenv",
    "mean_m_inenv",
    "coll_mean_n",
    "coll_mean_m",
    "coll_star_frac",
    "coll_rel_frac",
    "coll_shared",
    "secs",
)


@dataclass
class EvalContext:
    """Collection-scoped quantities every unit is scored against."""

    name: str
    n_types: int
    n_preds: int
    reference: gb.SampleSet
    ref_profile: dict[str, np.ndarray]
    ref_keys: frozenset[gb.IsoKey]

    @classmethod
    def from_kbs(cls, name: str, kbs: list[gb.KB], n_types: int, n_preds: int) -> EvalContext:
        """Build a context from in-memory members (used by tests and by ``from_collection``)."""
        reference = gb.SampleSet.from_kbs(kbs)
        keys = frozenset(gb.iso_key(kb, n_types, n_preds) for kb in kbs)
        return cls(name, n_types, n_preds, reference, reference.profile(), keys)

    @classmethod
    def from_collection(cls, name: str, corpus_root: Path = gb.CORPUS_ROOT) -> EvalContext:
        """Load a frozen TKDE collection."""
        from experiments.tkde import corpora

        collection = corpora.load_collection(name, corpus_root)
        kbs = [(r.n, r.types, r.facts) for r in collection.records]
        return cls.from_kbs(name, kbs, collection.n_types, collection.n_preds)

    def summary(self) -> dict[str, float]:
        """The collection's own mean n, mean m, star/relational fraction and shared constants."""
        ref = self.reference
        return {
            "coll_mean_n": float(ref.n.mean()),
            "coll_mean_m": float(ref.m.mean()),
            "coll_star_frac": float(ref.star.mean()),
            "coll_rel_frac": 1.0 - float(ref.star.mean()),
            "coll_shared": float(ref.shared.mean()),
        }


# ---------------------------------------------------------------------------
# One unit
# ---------------------------------------------------------------------------


def evaluate_unit(
    ctx: EvalContext,
    generator: str,
    seed: int,
    draws: Iterable[gb.Draw],
    *,
    repair: bool = False,
    source_generator: str | None = None,
    repaired_sink: IO[str] | None = None,
) -> tuple[dict[str, Any], gb.SampleSet]:
    """Score one unit; return its row and the :class:`SampleSet` of its usable samples.

    Parameters
    ----------
    ctx : EvalContext
        The collection scored against.
    generator, seed : str, int
        Unit identity, copied into the row.
    draws : Iterable[Draw]
        The unit's draws.
    repair : bool, optional
        Replace every decoded sample by its largest connected component.
    source_generator : str or None, optional
        Generator whose files the draws came from (differs from ``generator`` for a derived arm).
    repaired_sink : file-like or None, optional
        If given, every repaired draw is written to it in the frozen format.

    Returns
    -------
    tuple[dict, SampleSet]
        The row (keys ``ROW_COLUMNS``) and the usable samples.
    """
    started = time.perf_counter()
    n_draws = n_connected = n_empty = n_mismatch = n_rule_disagree = 0
    reasons: list[str | None] = []
    decoded: list[gb.KB] = []
    usable: list[gb.KB] = []
    for d in draws:
        n_draws += 1
        if d.status == "rejected" or d.kb is None:
            reasons.append(d.reason)
            continue
        kb = d.kb
        if repair:
            fixed = gb.repair_lcc(kb, ctx.n_types, ctx.n_preds)
            kb, n_rule_disagree = fixed.kb, n_rule_disagree + int(fixed.rule_disagree)
            if repaired_sink is not None:
                repaired_sink.write(
                    gb.draw_line(
                        collection=ctx.name,
                        generator=generator,
                        seed=seed,
                        draw=d.draw,
                        tokens=d.tokens,
                        root_type=d.root_type,
                        status="decoded",
                        reason=None,
                        kb=kb,
                        connected=True,
                    )
                    + "\n"
                )
        n, _types, facts = kb
        connected = gb.is_connected(n, facts)
        if d.connected_flag is not None and not repair and d.connected_flag != connected:
            n_mismatch += 1
        n_connected += int(connected)
        decoded.append(kb)
        if connected and facts:
            usable.append(kb)
        elif connected:
            n_empty += 1

    keys, n_key_error = _iso_keys(ctx, usable)
    novel = {k: c for k, c in keys.items() if k not in ctx.ref_keys}
    n_decoded = len(decoded)
    usable_set = gb.SampleSet.from_kbs(usable)
    all_profile = gb.SampleSet.from_kbs(decoded).profile()
    all_jsd = gb.jsd_profiles(all_profile, ctx.ref_profile) if decoded else {}
    fidelity_ok = len(usable_set) >= gb.MIN_USABLE
    use = (
        gb.set_metrics(usable_set, ctx.reference, ctx.ref_profile)
        if fidelity_ok
        else gb.set_metrics(gb.SampleSet.from_kbs([]), ctx.reference, ctx.ref_profile)
    )
    inenv = [kb for kb in usable if gb.in_envelope(kb)]
    inenv_keys, _ = _iso_keys(ctx, inenv)
    inenv_novel = sum(1 for k in inenv_keys if k not in ctx.ref_keys)
    inenv_set = gb.SampleSet.from_kbs(inenv)
    inenv_use = gb.set_metrics(
        inenv_set if len(inenv_set) >= gb.MIN_USABLE else gb.SampleSet.from_kbs([]),
        ctx.reference,
        ctx.ref_profile,
    )
    n_unique_novel = len(novel)
    n_singleton_novel = sum(1 for c in novel.values() if c == 1)
    row: dict[str, Any] = {
        "collection": ctx.name,
        "generator": generator,
        "seed": seed,
        "source_generator": source_generator or generator,
        "n_draws": n_draws,
        "n_decoded": n_decoded,
        "n_rejected": n_draws - n_decoded,
        "n_connected": n_connected,
        "n_empty": n_empty,
        "n_usable": len(usable),
        "n_unique_usable": len(keys),
        "n_novel_usable": sum(novel.values()),
        "n_unique_novel_usable": n_unique_novel,
        "n_singleton_novel_usable": n_singleton_novel,
        "vun_per_draw": n_unique_novel / n_draws if n_draws else math.nan,
        "vun_singleton_per_draw": n_singleton_novel / n_draws if n_draws else math.nan,
        "validity": n_decoded / n_draws if n_draws else math.nan,
        "connectivity": n_connected / n_decoded if n_decoded else math.nan,
        "usable_rate": len(usable) / n_draws if n_draws else math.nan,
        "fidelity_ok": int(fidelity_ok),
        "n_flag_mismatch": n_mismatch,
        "n_key_error": n_key_error,
        "n_lcc_rule_disagree": n_rule_disagree,
        "reasons": json.dumps(gb.count_reasons(reasons), sort_keys=True),
        **{f"jsd_{k}_all": all_jsd.get(k, math.nan) for k in gb.PROFILE_KEYS},
        **{f"jsd_{k}_use": use[f"jsd_{k}"] for k in gb.PROFILE_KEYS},
        "w1_n_use": use["w1_n"],
        "w1_m_use": use["w1_m"],
        "mean_n_use": use["mean_n"],
        "mean_m_use": use["mean_m"],
        "star_frac_use": use["star_frac"],
        "rel_frac_use": use["rel_frac"],
        "rel_dev_use": use["rel_dev"],
        "shared_use": use["shared"],
        "n_usable_inenv": len(inenv),
        "n_unique_novel_inenv": inenv_novel,
        "vun_inenv_per_draw": inenv_novel / n_draws if n_draws else math.nan,
        "jsd_n_inenv": inenv_use["jsd_n"],
        "jsd_m_inenv": inenv_use["jsd_m"],
        "w1_m_inenv": inenv_use["w1_m"],
        "mean_m_inenv": inenv_use["mean_m"],
        **ctx.summary(),
        "secs": time.perf_counter() - started,
    }
    return row, usable_set


def _iso_keys(ctx: EvalContext, usable: list[gb.KB]) -> tuple[Counter[gb.IsoKey], int]:
    """Count the isomorphism classes of ``usable``; a failing fingerprint gets a raw key."""
    counts: Counter[gb.IsoKey] = Counter()
    memo: dict[gb.KB, gb.IsoKey] = {}
    n_error = 0
    for kb in usable:
        key = memo.get(kb)
        if key is None:
            try:
                key = gb.iso_key(kb, ctx.n_types, ctx.n_preds)
            except Exception as exc:  # noqa: BLE001 - count, never crash a shard
                logger.error("fingerprint failed (%s): %r", type(exc).__name__, kb)
                key = ("raw", kb)
                n_error += 1
            memo[kb] = key
        counts[key] += 1
    return counts, n_error


# ---------------------------------------------------------------------------
# Collection summary and noise floors
# ---------------------------------------------------------------------------


def collection_summary(ctx: EvalContext) -> dict[str, Any]:
    """Own values and two noise floors of one collection.

    ``split_half``: 27 random disjoint halves of the collection compared with
    each other. ``resample``: 27 draws of 10,000 members with replacement
    against the collection, i.e. what an ideal sampler of the empirical
    distribution scores at the campaign's sample size.
    """
    ref = ctx.reference
    n_members = len(ref)
    summary: dict[str, Any] = {"n_members": n_members, **ctx.summary(), "n_keys": len(ctx.ref_keys)}
    split_rows, resample_rows = [], []
    half = n_members // 2
    for s in range(N_SPLITS):
        rng = np.random.default_rng(s)
        perm = rng.permutation(n_members)
        a, b = ref.take(perm[:half]), ref.take(perm[half : 2 * half])
        split_rows.append(_pair_row(a, b))
        idx = np.random.default_rng(10_000 + s).integers(0, n_members, RESAMPLE_SIZE)
        resample_rows.append(gb.set_metrics(ref.take(idx), ref, ctx.ref_profile))
    summary["split_half"] = _mean_over(split_rows)
    summary["resample"] = _mean_over(resample_rows)
    summary["split_half_rows"] = split_rows
    summary["resample_rows"] = resample_rows
    return summary


def _pair_row(a: gb.SampleSet, b: gb.SampleSet) -> dict[str, float]:
    """Metrics of ``a`` against ``b`` as the reference (both finite samples)."""
    row = gb.set_metrics(a, b, b.profile())
    row["rel_dev"] = abs(float(a.star.mean()) - float(b.star.mean()))
    return row


def _mean_over(rows: list[dict[str, float]]) -> dict[str, float]:
    return {k: float(np.nanmean([r[k] for r in rows])) for k in rows[0]}


# ---------------------------------------------------------------------------
# Parallel driver
# ---------------------------------------------------------------------------

_CONTEXTS: dict[str, EvalContext] = {}


def _context(name: str, corpus_root: str) -> EvalContext:
    if name not in _CONTEXTS:
        _CONTEXTS[name] = EvalContext.from_collection(name, Path(corpus_root))
    return _CONTEXTS[name]


def _task(args: tuple[Any, ...]) -> str:
    unit, arm, repair, out_dir, repaired_dir, corpus_root = args
    ctx = _context(unit.collection, corpus_root)
    out = Path(out_dir)
    stem = gb.unit_stem(unit.collection, arm, unit.seed)
    tmp: Path | None = None
    with contextlib.ExitStack() as stack:
        sink: IO[str] | None = None
        if repair and repaired_dir:
            target = Path(repaired_dir) / f"{stem}.jsonl.gz"
            tmp = target.with_name(target.name + ".part")
            sink = stack.enter_context(gzip.open(tmp, "wt", encoding="utf-8"))
        row, usable = evaluate_unit(
            ctx,
            arm,
            unit.seed,
            gb.read_draws(unit.path),
            repair=repair,
            source_generator=unit.generator,
            repaired_sink=sink,
        )
    if tmp is not None:
        tmp.replace(tmp.with_name(tmp.name[: -len(".part")]))
    usable.save(out / "arrays" / f"{stem}.npz")
    (out / "rows" / f"{stem}.json").write_text(json.dumps(row))
    return stem


def run(args: argparse.Namespace) -> None:
    """Evaluate every selected unit in parallel and aggregate the results."""
    samples, out = Path(args.samples), Path(args.out)
    for sub in ("rows", "arrays"):
        (out / sub).mkdir(parents=True, exist_ok=True)
    wanted_seeds = _wanted_seeds(args)
    tasks: list[tuple[Any, ...]] = []
    for collection in args.collection:
        files = gb.scan_directory(samples, collection, args.generator or None)
        if wanted_seeds is None and args.n_seeds:
            keep = sorted({f.seed for f in files})[: args.n_seeds]
            files = [f for f in files if f.seed in keep]
        elif wanted_seeds is not None:
            files = [f for f in files if f.seed in wanted_seeds]
        for unit in files:
            tasks.append((unit, unit.generator, False, str(out), None, str(args.corpus_root)))
            if args.repair_lcc_of == unit.generator:
                arm = f"{unit.generator}_lcc"
                tasks.append(
                    (unit, arm, True, str(out), args.write_repaired, str(args.corpus_root))
                )
    if args.write_repaired:
        Path(args.write_repaired).mkdir(parents=True, exist_ok=True)
    pending = [
        t
        for t in tasks
        if args.force
        or not (out / "rows" / f"{gb.unit_stem(t[0].collection, t[1], t[0].seed)}.json").exists()
        or (
            t[2]
            and args.write_repaired
            and not (
                Path(args.write_repaired)
                / f"{gb.unit_stem(t[0].collection, t[1], t[0].seed)}.jsonl.gz"
            ).exists()
        )
    ]
    workers = max(1, min(int(args.workers), MAX_WORKERS))
    print(f"[evaluate] {len(tasks)} units, {len(pending)} pending, {workers} workers", flush=True)
    started = time.perf_counter()
    if pending:
        with mp.get_context("spawn").Pool(workers, maxtasksperchild=40) as pool:
            for i, stem in enumerate(pool.imap_unordered(_task, pending), 1):
                if i % 10 == 0 or i == len(pending):
                    print(
                        f"[evaluate] {i}/{len(pending)} {stem} "
                        f"({time.perf_counter() - started:.0f}s)",
                        flush=True,
                    )
    selected = {gb.unit_stem(t[0].collection, t[1], t[0].seed) for t in tasks}
    _aggregate(out, selected)
    summaries = {c: collection_summary(_context(c, str(args.corpus_root))) for c in args.collection}
    (out / "collections.json").write_text(json.dumps(summaries, indent=1))
    print(f"[evaluate] wrote {out / 'units.csv'} and {out / 'collections.json'}", flush=True)


def _wanted_seeds(args: argparse.Namespace) -> set[int] | None:
    if not args.seeds:
        return None
    return {int(s) for s in args.seeds.split(",") if s}


def _aggregate(out: Path, stems: set[str]) -> None:
    """Concatenate the per-unit row files into ``units.csv`` (selected units only)."""
    rows = []
    for stem in sorted(stems):
        path = out / "rows" / f"{stem}.json"
        if path.exists():
            rows.append(json.loads(path.read_text()))
    with (out / "units.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ROW_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in ROW_COLUMNS})


def build_parser() -> argparse.ArgumentParser:
    """Command-line interface."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--samples",
        required=True,
        help="directory of <collection>__<generator>__s<seed>.jsonl[.gz]",
    )
    p.add_argument(
        "--collection", action="append", required=True, help="collection name (repeatable)"
    )
    p.add_argument(
        "--out",
        required=True,
        help="output directory (rows/, arrays/, units.csv, collections.json)",
    )
    p.add_argument("--generator", action="append", help="restrict to these generators (repeatable)")
    p.add_argument("--seeds", help="comma-separated seeds to keep")
    p.add_argument("--n-seeds", type=int, help="keep the first k seeds present")
    p.add_argument(
        "--workers",
        type=int,
        default=MAX_WORKERS,
        help=f"worker processes (capped at {MAX_WORKERS})",
    )
    p.add_argument(
        "--repair-lcc-of",
        help="derive <generator>_lcc by keeping the largest component of this generator's samples",
    )
    p.add_argument("--write-repaired", help="also write the derived arm's frozen-format files here")
    p.add_argument("--corpus-root", default=str(gb.CORPUS_ROOT))
    p.add_argument("--force", action="store_true")
    return p


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    run(build_parser().parse_args())
