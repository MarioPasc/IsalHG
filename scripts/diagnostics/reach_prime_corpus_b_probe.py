"""Corpus B feasibility and cost of RQ3's reach, before and after ``reach'``.

Two modes over the ``T >= min_run_length`` consecutive runs of a time-series
collection (members are ``kb_ids[:-1]``; the last quarter is the truth):

``--mode gate``
    How many natural member pairs are out of reach: pairs the cheap gate
    rejects outright, pairs with no finite reach inside the frozen radius
    ``r = 2``, and how many runs contain at least one such pair.
``--mode timing``
    One run's coverage consensus at ``r = 2``: wall-clock, candidate count, tie
    count, and how many of its member pairs are at finite reach.  The run is
    picked by ``--rank``, ordering runs by ``(T, max member m, total m)``;
    ``--rank -1`` is the worst run, ``--rank 34`` (of 69) the median one.

Run ``--mode gate`` once against the frozen reach and once against ``reach'`` to
see what compacting the remainders buys.  The gate adapter accepts both the
frozen two-argument ``compatible`` and the radius-aware one.
"""

from __future__ import annotations

import argparse
import inspect
import json
import time
from itertools import combinations
from pathlib import Path
from typing import Any

from experiments.tkde import corpora
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.datasets.kb.base import KBCollection, KBRecord
from isalhg.language.consensus import coverage_consensus
from isalhg.language.reach import compatible, reach

_GATE_TAKES_RADIUS = len(inspect.signature(compatible).parameters) >= 3


def gate(left: SparseHypergraph, right: SparseHypergraph, r: int) -> bool:
    """Call ``compatible`` under whichever signature the installed module has."""
    return compatible(left, right, r) if _GATE_TAKES_RADIUS else compatible(left, right)


def run_members(
    collection: KBCollection, by_id: dict[str, KBRecord], run: dict[str, Any]
) -> list[SparseHypergraph]:
    """Return the members of one run --- every quarter but the last, which is the truth."""
    records = [by_id[kb_id] for kb_id in run["kb_ids"]]
    return [
        record.to_hypergraph(n_types=collection.n_types, n_preds=collection.n_preds)
        for record in records[:-1]
    ]


def ranked_runs(
    collection: KBCollection, by_id: dict[str, KBRecord], runs: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Return ``runs`` ordered by size: run length, then largest member, then total facts."""

    def size(run: dict[str, Any]) -> tuple[int, int, int]:
        records = [by_id[kb_id] for kb_id in run["kb_ids"]][:-1]
        return len(run["kb_ids"]), max(r.m for r in records), sum(r.m for r in records)

    return sorted(runs, key=size)


def finite_pairs(members: list[SparseHypergraph], r: int) -> int:
    """Return how many unordered member pairs are at finite reach within ``r``."""
    return sum(
        1
        for left, right in combinations(members, 2)
        if gate(left, right, r) and reach(left, right, r_max=r) is not None
    )


def mode_gate(
    collection: KBCollection,
    by_id: dict[str, KBRecord],
    runs: list[dict[str, Any]],
    radius: int,
) -> dict[str, Any]:
    """Count the member pairs the reach cannot serve, per run and in total."""
    n_pairs = n_gate_rejected = n_unreached = 0
    runs_with_gate_reject = runs_with_unreached = 0
    started = time.perf_counter()
    for index, run in enumerate(runs):
        members = run_members(collection, by_id, run)
        rejected_here = unreached_here = 0
        for left, right in combinations(members, 2):
            n_pairs += 1
            if not gate(left, right, radius):
                rejected_here += 1
                unreached_here += 1
                continue
            if reach(left, right, r_max=radius) is None:
                unreached_here += 1
        n_gate_rejected += rejected_here
        n_unreached += unreached_here
        runs_with_gate_reject += int(rejected_here > 0)
        runs_with_unreached += int(unreached_here > 0)
        print(
            f"[{index + 1}/{len(runs)}] {run['class_id']} T={len(run['kb_ids'])} "
            f"pairs={len(members) * (len(members) - 1) // 2} "
            f"gate_rejected={rejected_here} unreached={unreached_here} "
            f"{time.perf_counter() - started:.0f}s",
            flush=True,
        )
    return {
        "n_runs": len(runs),
        "n_pairs": n_pairs,
        "n_gate_rejected": n_gate_rejected,
        "n_unreached_at_radius": n_unreached,
        "runs_with_gate_reject": runs_with_gate_reject,
        "runs_with_unreached": runs_with_unreached,
        "secs": round(time.perf_counter() - started, 1),
    }


def mode_timing(
    collection: KBCollection,
    by_id: dict[str, KBRecord],
    runs: list[dict[str, Any]],
    radius: int,
    rank: int,
) -> dict[str, Any]:
    """Time one run's coverage consensus and report the candidate counts beside it."""
    run = ranked_runs(collection, by_id, runs)[rank]
    members = run_members(collection, by_id, run)
    finite = finite_pairs(members, radius)
    started = time.perf_counter()
    result = coverage_consensus(members, radius)
    secs = time.perf_counter() - started
    return {
        "class_id": run["class_id"],
        "T": len(run["kb_ids"]),
        "n_members": len(members),
        "max_member_m": max(H.n_edges for H in members),
        "max_member_n": max(H.n_nodes for H in members),
        "n_member_pairs": len(members) * (len(members) - 1) // 2,
        "n_finite_reach_pairs": finite,
        "n_candidates": result.n_candidates,
        "n_ties": result.n_ties,
        "coverage": result.coverage,
        "sum_reach": result.sum_reach,
        "consensus_secs": round(secs, 1),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection", default="ndc_classes")
    parser.add_argument("--root", default=None)
    parser.add_argument("--min-run-length", type=int, default=4)
    parser.add_argument("--radius", type=int, default=2)
    parser.add_argument("--mode", choices=("gate", "timing"), default="gate")
    parser.add_argument("--rank", type=int, default=-1)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    root = None if args.root is None else Path(args.root)
    collection = corpora.load_collection(args.collection, root)
    by_id = corpora.records_by_id(collection)
    runs = corpora.consecutive_runs(collection, args.min_run_length)

    if args.mode == "gate":
        summary = mode_gate(collection, by_id, runs, args.radius)
    else:
        summary = mode_timing(collection, by_id, runs, args.radius, args.rank)
    summary = {
        "collection": args.collection,
        "mode": args.mode,
        "radius": args.radius,
        "gate_takes_radius": _GATE_TAKES_RADIUS,
        **summary,
    }
    print(json.dumps(summary, indent=1))
    if args.out is not None:
        Path(args.out).write_text(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
