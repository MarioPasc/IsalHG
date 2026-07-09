"""Reproduce Qin et al. (ICDE 2023) Table II on PS / HS / MO (T-M2a).

The paper invokes each HGED algorithm on 1,000 sampled node pairs per dataset
and reports the average wall-clock of one computation
``HGED(EGO(u), EGO(v))``; their HGED-BFS column (Python, i5-8400 @ 3.80 GHz)
reads PS 0.23 s, HS 0.14 s, MO 10.3 s. Their search runs under a Strategy-2
clamp ("we can set the upper bound HGED to be 10 in most situations"), which
is what makes random pairs cheap: the Def 5 + Def 6 root bound usually already
exceeds the clamp. This script therefore benchmarks the clamped regime by
default (``--upper-bound 10``) and can also run unclamped (``--exact``), where
per-pair cost is unbounded and the ``--timeout`` guard reports DNFs honestly.

Outputs one JSON per (dataset, regime) with per-pair records + summary, and a
combined markdown summary, into ``--out-dir`` (defaults to the T-M2a results
directory on /media).
"""

from __future__ import annotations

import argparse
import json
import math
import platform
import random
import statistics
import sys
import time
from pathlib import Path
from typing import Any

from isalhg.core.sparse_hypergraph import SparseHypergraph, ego_network
from isalhg.datasets.arb_benson import ARBBensonDataset
from isalhg.errors import HGEDComputationError
from isalhg.metric_space.distances.qin_hged import QinHGED

DATASETS = {
    "PS": "contact-primary-school",
    "HS": "contact-high-school",
    "MO": "mathoverflow-answers",
}
PAPER_BFS_SECONDS = {"PS": 0.23, "HS": 0.14, "MO": 10.3}
DEFAULT_DATA = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/misc/HGED/data")
DEFAULT_OUT = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/misc/HGED/results")


def _cpu_model() -> str:
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or "unknown"


def bench_dataset(
    tag: str,
    hypergraph: SparseHypergraph,
    *,
    n_pairs: int,
    seed: int,
    upper_bound: int | None,
    timeout: float,
    pair_mode: str = "random",
    progress_every: int = 100,
) -> dict[str, Any]:
    rng = random.Random(seed)
    nodes = list(range(hypergraph.n_nodes))
    pairs: list[tuple[int, int]] = []
    while len(pairs) < n_pairs:
        if pair_mode == "random":
            u, v = rng.sample(nodes, 2)
        else:
            # HEP regime: v drawn from NEI(u) -- the pairs Algorithm 4 actually
            # feeds to HGED, where egos overlap and real search happens.
            u = rng.choice(nodes)
            nei: set[int] = set()
            for e in hypergraph.incident_edges(u):
                nei |= hypergraph.members(e)
            nei.discard(u)
            if not nei:
                continue
            v = rng.choice(sorted(nei))
        pairs.append((u, v))

    distance = QinHGED(upper_bound=upper_bound, timeout=timeout)
    ego_cache: dict[int, SparseHypergraph] = {}
    records: list[dict[str, Any]] = []
    for idx, (u, v) in enumerate(pairs):
        t0 = time.perf_counter()
        if u not in ego_cache:
            ego_cache[u] = ego_network(hypergraph, u)
        if v not in ego_cache:
            ego_cache[v] = ego_network(hypergraph, v)
        ego_u, ego_v = ego_cache[u], ego_cache[v]
        t_ego = time.perf_counter() - t0

        record: dict[str, Any] = {
            "u": u,
            "v": v,
            "ego_u": [ego_u.n_nodes, ego_u.n_edges],
            "ego_v": [ego_v.n_nodes, ego_v.n_edges],
            "ego_seconds": t_ego,
        }
        t1 = time.perf_counter()
        try:
            value = distance.pairwise(ego_u, ego_v)
            record["hged"] = None if math.isinf(value) else value
            record["exceeds_bound"] = math.isinf(value)
            record["dnf"] = False
        except HGEDComputationError:
            record["hged"] = None
            record["exceeds_bound"] = False
            record["dnf"] = True
        record["hged_seconds"] = time.perf_counter() - t1
        records.append(record)
        if (idx + 1) % progress_every == 0:
            done = [r["hged_seconds"] for r in records]
            print(
                f"[{tag}] {idx + 1}/{n_pairs} pairs, "
                f"median {statistics.median(done):.4f}s, "
                f"mean {statistics.fmean(done):.4f}s",
                flush=True,
            )

    hged_secs = [r["hged_seconds"] for r in records]
    total_secs = [r["hged_seconds"] + r["ego_seconds"] for r in records]
    summary = {
        "dataset": tag,
        "n_pairs": n_pairs,
        "pair_mode": pair_mode,
        "seed": seed,
        "upper_bound": upper_bound,
        "timeout_s": timeout,
        "mean_hged_s": statistics.fmean(hged_secs),
        "median_hged_s": statistics.median(hged_secs),
        "p90_hged_s": statistics.quantiles(hged_secs, n=10)[-1],
        "max_hged_s": max(hged_secs),
        "mean_with_ego_s": statistics.fmean(total_secs),
        "exceeds_bound_frac": statistics.fmean(r["exceeds_bound"] for r in records),
        "dnf_count": sum(r["dnf"] for r in records),
        "finite_hged_values": sorted(r["hged"] for r in records if r["hged"] is not None),
        "paper_bfs_seconds_per_pair": PAPER_BFS_SECONDS.get(tag),
        "speed_factor_vs_paper": (
            PAPER_BFS_SECONDS[tag] / statistics.fmean(hged_secs)
            if tag in PAPER_BFS_SECONDS
            else None
        ),
    }
    return {"summary": summary, "records": records}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datasets", nargs="+", default=["PS", "HS", "MO"], choices=DATASETS)
    parser.add_argument("--n-pairs", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--upper-bound", type=int, default=10)
    parser.add_argument(
        "--exact", action="store_true", help="unclamped exact mode (no upper bound)"
    )
    parser.add_argument("--timeout", type=float, default=60.0, help="per-pair budget (s)")
    parser.add_argument(
        "--pair-mode",
        choices=["random", "neighbor"],
        default="random",
        help="uniform random pairs, or HEP-style pairs (v drawn from NEI(u))",
    )
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    upper_bound = None if args.exact else args.upper_bound
    regime = ("exact" if args.exact else f"clamp{args.upper_bound}") + (
        "_nbr" if args.pair_mode == "neighbor" else ""
    )
    machine = {
        "cpu": _cpu_model(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "paper_machine": "Intel Core i5-8400 @ 3.80 GHz, 32 GB RAM, Python (Table II)",
    }
    print(f"machine: {machine['cpu']} | Python {machine['python']} | regime {regime}")

    all_summaries = []
    for tag in args.datasets:
        dataset = ARBBensonDataset(args.data_root, DATASETS[tag])
        item = next(iter(dataset))
        print(
            f"[{tag}] loaded {DATASETS[tag]}: n={item.extra['n_nodes']} "
            f"m={item.extra['m_loaded']} (file {item.extra['m_file']})",
            flush=True,
        )
        started = time.perf_counter()
        result = bench_dataset(
            tag,
            item.hypergraph,
            n_pairs=args.n_pairs,
            seed=args.seed,
            upper_bound=upper_bound,
            timeout=args.timeout,
            pair_mode=args.pair_mode,
        )
        result["machine"] = machine
        result["dataset_stats"] = item.extra
        out = args.out_dir / f"table2_{tag}_{regime}_seed{args.seed}_n{args.n_pairs}.json"
        out.write_text(json.dumps(result, indent=1))
        summary = result["summary"]
        all_summaries.append(summary)
        print(
            f"[{tag}] DONE in {time.perf_counter() - started:.1f}s -- "
            f"mean {summary['mean_hged_s']:.4f}s/pair (paper "
            f"{summary['paper_bfs_seconds_per_pair']}s), "
            f"exceeds-bound {summary['exceeds_bound_frac']:.1%}, "
            f"DNF {summary['dnf_count']} -> {out}",
            flush=True,
        )

    lines = [
        "# Table II reproduction (HGED-BFS column)",
        "",
        f"Machine: {machine['cpu']} | Python {machine['python']} | regime {regime} | "
        f"seed {args.seed} | {args.n_pairs} pairs | per-pair timeout {args.timeout}s",
        "",
        "| Dataset | paper s/pair | ours mean s/pair | ours median | p90 | max | >bound | DNF |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for s in all_summaries:
        lines.append(
            f"| {s['dataset']} | {s['paper_bfs_seconds_per_pair']} | "
            f"{s['mean_hged_s']:.4f} | {s['median_hged_s']:.4f} | "
            f"{s['p90_hged_s']:.4f} | {s['max_hged_s']:.2f} | "
            f"{s['exceeds_bound_frac']:.1%} | {s['dnf_count']} |"
        )
    md = args.out_dir / f"table2_summary_{regime}_seed{args.seed}.md"
    md.write_text("\n".join(lines) + "\n")
    print(f"summary -> {md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
