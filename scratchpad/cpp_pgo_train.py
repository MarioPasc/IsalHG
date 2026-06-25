"""PGO training driver.

Invoke after the instrumented build (``ISALHG_PGO_GENERATE=ON``). Runs
``canonical_string`` on the named designs enough times to exercise the
hot loops the optimiser will be retrained against.
"""

from __future__ import annotations

import itertools

from isalhg.core.canonical import canonical_string
from isalhg.core.sparse_hypergraph import SparseHypergraph


def fano() -> SparseHypergraph:
    return SparseHypergraph(
        n_nodes=7,
        hyperedges=[
            [0, 1, 2],
            [0, 3, 4],
            [0, 5, 6],
            [1, 3, 5],
            [1, 4, 6],
            [2, 3, 6],
            [2, 4, 5],
        ],
    )


def sts9() -> SparseHypergraph:
    return SparseHypergraph(
        n_nodes=9,
        hyperedges=[
            [0, 1, 2],
            [3, 4, 5],
            [6, 7, 8],
            [0, 3, 6],
            [1, 4, 7],
            [2, 5, 8],
            [0, 4, 8],
            [1, 5, 6],
            [2, 3, 7],
            [0, 5, 7],
            [1, 3, 8],
            [2, 4, 6],
        ],
    )


def sts13() -> SparseHypergraph:
    return SparseHypergraph(
        n_nodes=13,
        hyperedges=[[i, (i + 1) % 13, (i + 3) % 13] for i in range(13)],
    )


def doily() -> SparseHypergraph:
    pairs = list(itertools.combinations(range(1, 7), 2))
    pid = {p: i for i, p in enumerate(pairs)}

    def matchings(es: tuple[int, ...]):
        if not es:
            yield ()
            return
        a = es[0]
        rest = es[1:]
        for i, b in enumerate(rest):
            for tail in matchings(rest[:i] + rest[i + 1 :]):
                yield ((a, b),) + tail

    return SparseHypergraph(
        n_nodes=15,
        hyperedges=[
            sorted(pid[tuple(sorted(p))] for p in m) for m in matchings(tuple(range(1, 7)))
        ],
    )


def main() -> None:
    designs = [
        ("Fano", fano(), 30),
        ("STS9", sts9(), 15),
        ("STS13", sts13(), 6),
        ("Doily", doily(), 4),
    ]
    variants = [
        "greedy_min",
        "greedy_single",
        "greedy_min_wl_pruned",
        # PI 2026-06-23 — train the neighbour-degree selector variants too
        # so GCC sees their branch-distribution and inlines the cascade.
        "greedy_min_nbrdeg",
        "greedy_single_nbrdeg",
    ]
    for name, H, reps in designs:
        for algo in variants:
            for _ in range(reps):
                canonical_string(H, algorithm=algo)
        print(f"trained on {name} x {len(variants)} variants x {reps} reps")


if __name__ == "__main__":
    main()
