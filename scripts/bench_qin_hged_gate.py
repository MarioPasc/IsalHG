"""Speed-gate probe for T-M2a step 5: the official (Qin) HGED vs the article's use.

Measures unclamped-exact per-pair wall-clock of the two solvers of the
official Qin-taxonomy HGED -- ``ExactHGED`` (LSAP branch-and-bound, the
experiments' oracle) and ``QinHGED`` (the paper's HGED-BFS) -- on the two
T-M5a regimes:

1. the Layer-1 exact-correlation corpus (``correlation_corpus`` defaults,
   n in [4, 7]) -- every pair;
2. density-sweep cells at n in {10, 12, 14} with m/n in {0.5, 1, 2} -- sampled
   pairs with a per-pair timeout, DNF rates reported.

The output feeds the written go/no-go recommendation on the C++ port
(decision D3: PI decides after the numbers). Results land in the T-M2a
results directory.
"""

from __future__ import annotations

import argparse
import json
import platform
import random
import statistics
import sys
import time
from pathlib import Path
from typing import Any

from isalhg.datasets.synthetic._random_hg import random_hypergraph
from isalhg.datasets.synthetic.correlation_corpus import CorrelationCorpusHypergraphs
from isalhg.errors import HGEDComputationError
from isalhg.metric_space.base import HypergraphDistance
from isalhg.metric_space.distances.hged import ExactHGED
from isalhg.metric_space.distances.qin_hged import QinHGED

DEFAULT_OUT = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/misc/HGED/results")


def _time_pairs(
    distance: HypergraphDistance,
    pairs: list[tuple[Any, Any]],
) -> dict[str, Any]:
    times: list[float] = []
    dnf = 0
    values: list[float] = []
    for h1, h2 in pairs:
        t0 = time.perf_counter()
        try:
            values.append(distance.pairwise(h1, h2))
        except HGEDComputationError:
            dnf += 1
        times.append(time.perf_counter() - t0)
    return {
        "n_pairs": len(pairs),
        "dnf": dnf,
        "mean_s": statistics.fmean(times),
        "median_s": statistics.median(times),
        "max_s": max(times),
        "mean_value": statistics.fmean(values) if values else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--sweep-pairs", type=int, default=15, help="pairs per sweep cell")
    parser.add_argument("--timeout", type=float, default=10.0, help="per-pair budget (s)")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "machine": platform.platform(),
        "python": platform.python_version(),
        "seed": args.seed,
        "timeout_s": args.timeout,
    }

    # --- Regime 1: the Layer-1 exact-correlation corpus, all pairs ---------
    corpus = [item.hypergraph for item in CorrelationCorpusHypergraphs(seed=args.seed)]
    pairs = [(corpus[i], corpus[j]) for i in range(len(corpus)) for j in range(i + 1, len(corpus))]
    print(f"[corpus] {len(corpus)} items -> {len(pairs)} pairs")
    report["layer1_bfs"] = _time_pairs(QinHGED(timeout=args.timeout), pairs)
    report["layer1_bnb_oracle"] = _time_pairs(ExactHGED(timeout=args.timeout), pairs)
    print(
        f"[corpus] bfs median {report['layer1_bfs']['median_s'] * 1e3:.2f} ms, "
        f"bnb-oracle median {report['layer1_bnb_oracle']['median_s'] * 1e3:.2f} ms, "
        f"bfs DNF {report['layer1_bfs']['dnf']}/{len(pairs)}"
    )

    # --- Regime 2: density-sweep cells (T-M5a E2) --------------------------
    sweep: list[dict[str, Any]] = []
    rng = random.Random(args.seed)
    for n in (10, 12, 14):
        for density in (0.5, 1.0, 2.0):
            m = max(2, int(round(density * n)))
            cell_pairs = []
            for _ in range(args.sweep_pairs):
                h1 = random_hypergraph(n_nodes=n, n_edges=m, arity_range=(2, 4), rng=rng)
                h2 = random_hypergraph(n_nodes=n, n_edges=m, arity_range=(2, 4), rng=rng)
                cell_pairs.append((h1, h2))
            cell = {"n": n, "m": m, "density": density}
            cell["bfs"] = _time_pairs(QinHGED(timeout=args.timeout), cell_pairs)
            cell["bnb_oracle"] = _time_pairs(ExactHGED(timeout=args.timeout), cell_pairs)
            sweep.append(cell)
            print(
                f"[sweep n={n} m={m}] bfs median {cell['bfs']['median_s']:.4f}s "
                f"(DNF {cell['bfs']['dnf']}/{args.sweep_pairs}), "
                f"bnb-oracle median {cell['bnb_oracle']['median_s']:.4f}s "
                f"(DNF {cell['bnb_oracle']['dnf']}/{args.sweep_pairs})",
                flush=True,
            )
    report["density_sweep"] = sweep

    out = args.out_dir / f"gate_probe_seed{args.seed}.json"
    out.write_text(json.dumps(report, indent=1))
    print(f"report -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
