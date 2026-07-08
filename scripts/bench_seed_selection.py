"""T-M0 wall-clock benchmark: xi-cascade vs neighbour-degree-cascade seeding.

Compares ``canonical_string`` under ``greedy_min`` (historical xi seed set)
and ``greedy_min_nbrdeg`` (the T-M0 default) on the design fixtures
(Fano / STS(9) / two STS(13) / GQ(2,2)) plus one asymmetric sample. Reports,
per instance, the two seed-set sizes, the median wall-clock (with IQR) of
each variant, the speedup ratio, and whether the two canonical strings
coincide.

Honest expectation (see docs/article/theoretical/stability.md §3): the
design fixtures are vertex-transitive, so both seeders select the *entire*
vertex orbit and the wall-clock difference reduces to the (small) seed-
selection cost -- near parity. The seed-*count* win, and hence the fan-out
speedup, appears only on non-vertex-transitive inputs. The GQ(2,2) fixture
happens to be asymmetric (a transcription that is not a valid generalised
quadrangle -- see the T-M0 handoff) and therefore does show a seed drop.

Run: ``python -m scripts.bench_seed_selection`` (or pass the path directly).
"""

from __future__ import annotations

import random

from isalhg.core.canonical import canonical_string
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.structural_tuples import max_neighbor_degree_nodes, max_xi_nodes
from isalhg.metrics.runtime import (
    iqr_wall_clock_s,
    median_wall_clock_s,
    time_call_repeated,
)

_REPEATS = 100


def _hg(n: int, edges: list[tuple[int, ...]]) -> SparseHypergraph:
    return SparseHypergraph(n_nodes=n, hyperedges=[frozenset(e) for e in edges])


def _asymmetric(n: int = 12, seed: int = 0) -> SparseHypergraph:
    """Connected, non-vertex-transitive hypergraph: a spanning path plus a
    few seeded higher-arity edges, giving a clear degree hierarchy."""
    rng = random.Random(seed)
    edges: list[tuple[int, ...]] = [(i, i + 1) for i in range(n - 1)]
    for _ in range(4):
        arity = rng.randint(2, 4)
        members = tuple(sorted(rng.sample(range(n), arity)))
        edges.append(members)
    return _hg(n, edges)


def _fixtures() -> list[tuple[str, SparseHypergraph]]:
    fano = _hg(7, [(0, 1, 2), (0, 3, 4), (0, 5, 6), (1, 3, 5), (1, 4, 6), (2, 3, 6), (2, 4, 5)])
    sts9 = _hg(
        9,
        [
            (0, 1, 2),
            (3, 4, 5),
            (6, 7, 8),
            (0, 3, 6),
            (1, 4, 7),
            (2, 5, 8),
            (0, 4, 8),
            (1, 5, 6),
            (2, 3, 7),
            (0, 5, 7),
            (1, 3, 8),
            (2, 4, 6),
        ],
    )
    sts13_a = _hg(13, [tuple((b + i) % 13 for b in (0, 1, 4)) for i in range(13)])
    sts13_b = _hg(13, [tuple((b + i) % 13 for b in (0, 1, 6)) for i in range(13)])
    gq22 = _hg(
        15,
        [
            (0, 1, 2),
            (0, 3, 4),
            (0, 5, 6),
            (1, 3, 7),
            (1, 5, 8),
            (2, 4, 9),
            (2, 6, 10),
            (3, 8, 11),
            (4, 7, 12),
            (5, 10, 13),
            (6, 9, 14),
            (7, 11, 13),
            (8, 12, 14),
            (9, 11, 12),
            (10, 13, 14),
        ],
    )
    return [
        ("fano_7", fano),
        ("sts9", sts9),
        ("sts13_a", sts13_a),
        ("sts13_b", sts13_b),
        ("gq22*", gq22),
        ("asym_er12", _asymmetric()),
    ]


def _median_ms(H: SparseHypergraph, algorithm: str) -> tuple[float, float]:
    results = time_call_repeated(lambda: canonical_string(H, algorithm=algorithm), repeats=_REPEATS)
    return median_wall_clock_s(results) * 1e3, iqr_wall_clock_s(results) * 1e3


def main() -> None:
    header = (
        f"{'fixture':10} {'n':>3} {'m':>3} {'|xi|':>5} {'|nbr|':>6} "
        f"{'t_min(ms)':>12} {'t_nbr(ms)':>12} {'speedup':>8} {'w*eq':>5}"
    )
    print(header)
    print("-" * len(header))
    for name, H in _fixtures():
        n_xi = len(max_xi_nodes(H))
        n_nbr = len(max_neighbor_degree_nodes(H))
        t_min, iqr_min = _median_ms(H, "greedy_min")
        t_nbr, iqr_nbr = _median_ms(H, "greedy_min_nbrdeg")
        w_eq = canonical_string(H, algorithm="greedy_min") == canonical_string(
            H, algorithm="greedy_min_nbrdeg"
        )
        speedup = t_min / t_nbr if t_nbr > 0 else float("nan")
        print(
            f"{name:10} {H.n_nodes:>3} {H.n_edges:>3} {n_xi:>5} {n_nbr:>6} "
            f"{t_min:>8.3f}±{iqr_min:<3.2f} {t_nbr:>8.3f}±{iqr_nbr:<3.2f} "
            f"{speedup:>8.2f} {str(w_eq):>5}"
        )
    print(
        f"\n(median of {_REPEATS} runs; '*' = fixture is not the true vertex-transitive "
        "design, see T-M0 handoff; speedup = t_min / t_nbr.)"
    )


if __name__ == "__main__":
    main()
