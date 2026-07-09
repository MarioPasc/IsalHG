"""Benchmark the exact-HGED oracle's problem-size ceiling (T-M2 / DQ1).

``ExactHGED`` is NP-hard (Qin et al., ICDE 2023), so the exact oracle is only
tractable up to some vertex count. This script sweeps ``n``, times
``ExactHGED.pairwise`` on random hypergraph pairs of that size with a per-pair
timeout, and reports where the exact solve falls over -- the number DATA.md's
DQ1 asks for. Because the Layer-1 study computes an ``O(N^2)`` matrix on HPC with
high parallelism, the relevant quantity is per-pair wall-clock: the reported
ceiling is the largest ``n`` whose pairs all complete under the budget.

Run (in the isalhg env)::

    python scripts/bench_hged_ceiling.py
    python scripts/bench_hged_ceiling.py --n-values 6 8 10 12 14 --pairs-per-n 30 --timeout 10

This is a script (``print`` is intentional); it is not imported by the package.
"""

from __future__ import annotations

import argparse
import random
import statistics
import time

from isalhg.datasets.synthetic._random_hg import random_hypergraph
from isalhg.errors import HGEDComputationError
from isalhg.metric_space.distances.hged import ExactHGED


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--n-values",
        type=int,
        nargs="+",
        default=[6, 8, 10, 12, 14, 16],
        help="Vertex counts to sweep.",
    )
    parser.add_argument("--pairs-per-n", type=int, default=25, help="Random pairs timed per n.")
    parser.add_argument(
        "--edges-factor",
        type=float,
        default=1.5,
        help="Mean edge count as a multiple of n (m = round(factor * n)).",
    )
    parser.add_argument("--arity-max", type=int, default=3, help="Maximum hyperedge arity.")
    parser.add_argument(
        "--timeout", type=float, default=10.0, help="Per-pair wall-clock budget (seconds)."
    )
    parser.add_argument(
        "--completion-threshold",
        type=float,
        default=1.0,
        help="p95 seconds under which an n is deemed comfortably tractable.",
    )
    parser.add_argument("--seed", type=int, default=0, help="Master seed.")
    return parser.parse_args()


def _bench_n(
    n: int,
    *,
    pairs: int,
    m: int,
    arity_max: int,
    timeout: float,
    seed: int,
) -> tuple[list[float], int]:
    """Return ``(completed_times_seconds, dnf_count)`` for ``pairs`` random pairs."""
    rng = random.Random(seed)
    exact = ExactHGED(timeout=timeout)
    times: list[float] = []
    dnf = 0
    for _ in range(pairs):
        h1 = random_hypergraph(n_nodes=n, n_edges=m, arity_range=(2, arity_max), rng=rng)
        h2 = random_hypergraph(n_nodes=n, n_edges=m, arity_range=(2, arity_max), rng=rng)
        start = time.perf_counter()
        try:
            exact.pairwise(h1, h2)
        except HGEDComputationError:
            dnf += 1
            continue
        times.append(time.perf_counter() - start)
    return times, dnf


def main() -> None:
    args = _parse_args()
    print(
        f"Exact-HGED ceiling benchmark | pairs/n={args.pairs_per_n} "
        f"edges_factor={args.edges_factor} arity_max={args.arity_max} "
        f"timeout={args.timeout:g}s seed={args.seed}\n"
    )
    header = (
        f"{'n':>4} {'m':>4} {'done':>7} {'median_ms':>11} {'p95_ms':>10} {'max_ms':>10} {'DNF':>5}"
    )
    print(header)
    print("-" * len(header))

    tractable: list[int] = []
    for i, n in enumerate(args.n_values):
        m = round(args.edges_factor * n)
        times, dnf = _bench_n(
            n,
            pairs=args.pairs_per_n,
            m=m,
            arity_max=args.arity_max,
            timeout=args.timeout,
            seed=args.seed + i * 104_729,
        )
        done = len(times)
        if times:
            times_ms = sorted(t * 1e3 for t in times)
            median_ms = statistics.median(times_ms)
            p95_ms = times_ms[min(len(times_ms) - 1, int(0.95 * len(times_ms)))]
            max_ms = times_ms[-1]
        else:
            median_ms = p95_ms = max_ms = float("nan")
        print(
            f"{n:>4} {m:>4} {done:>3}/{args.pairs_per_n:<3} "
            f"{median_ms:>11.2f} {p95_ms:>10.2f} {max_ms:>10.2f} {dnf:>5}"
        )
        if dnf == 0 and times and p95_ms <= args.completion_threshold * 1e3:
            tractable.append(n)

    print()
    if tractable:
        ceiling = max(tractable)
        print(
            f"RECOMMENDATION: exact HGED is comfortably tractable up to n={ceiling} "
            f"(all pairs complete, p95 <= {args.completion_threshold:g}s). "
            f"Above n={ceiling}, fall back to the perturbation ladder / BP-HGED."
        )
    else:
        print(
            "RECOMMENDATION: no swept n met the completion threshold; lower "
            "--edges-factor / --arity-max or raise --timeout, or rely on the ladder."
        )


if __name__ == "__main__":
    main()
