"""Design axioms for the shared builders in ``isalhg.datasets.synthetic.designs``.

These assertions encode the *defining* incidence axioms of each design rather
than a transcribed edge list, so a builder cannot silently drift into a
structure that merely resembles the design it names. Written for T-M0a, after a
hardcoded 15-line "GQ(2,2)" was found to have two lines meeting in two points.
"""

from __future__ import annotations

import itertools
from collections import Counter

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.structural_tuples import max_neighbor_degree_nodes, max_xi_nodes
from isalhg.datasets.synthetic.designs import (
    cyclic_triple_orbit_13,
    fano_plane,
    gq_2_2_doily,
    sts_9,
)

pytestmark = pytest.mark.unit


def _primal_neighbours(H: SparseHypergraph) -> dict[int, set[int]]:
    """Vertices co-occurring in at least one hyperedge, per vertex."""
    nbrs: dict[int, set[int]] = {v: set() for v in H.nodes()}
    for _, members, _ in H.iter_edges():
        for v in members:
            nbrs[v] |= members - {v}
    return nbrs


def _pair_coverage(H: SparseHypergraph) -> Counter[tuple[int, int]]:
    """How many hyperedges cover each unordered vertex pair."""
    counts: Counter[tuple[int, int]] = Counter()
    for _, members, _ in H.iter_edges():
        for pair in itertools.combinations(sorted(members), 2):
            counts[pair] += 1
    return counts


# ---------------------------------------------------------------------------
# Steiner triple systems: every pair of points on exactly one block
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("builder,n,m", [(fano_plane, 7, 7), (sts_9, 9, 12)])
def test_steiner_triple_system_axioms(builder, n: int, m: int) -> None:
    H = builder()
    assert (H.n_nodes, H.n_edges) == (n, m)
    assert all(len(members) == 3 for _, members, _ in H.iter_edges())
    coverage = _pair_coverage(H)
    assert len(coverage) == n * (n - 1) // 2
    assert set(coverage.values()) == {1}


@pytest.mark.parametrize("base", [(0, 1, 3), (0, 1, 4), (0, 1, 6)])
def test_cyclic_13_is_a_vertex_transitive_partial_triple_system(base) -> None:
    H = cyclic_triple_orbit_13(base)
    assert (H.n_nodes, H.n_edges) == (13, 13)
    assert all(len(members) == 3 for _, members, _ in H.iter_edges())
    assert {H.degree(v) for v in H.nodes()} == {3}
    assert max(_pair_coverage(H).values()) == 1


@pytest.mark.parametrize("base", [(0, 1, 3), (0, 1, 4), (0, 1, 6)])
def test_cyclic_13_is_not_a_steiner_triple_system_known_limitation(base) -> None:
    """Documents a misnomer, not a design goal.

    A single starter block generates one orbit of 13 blocks covering 39 of the
    78 point-pairs; STS(13) needs 26 blocks from two starters (e.g. adding
    ``(0, 2, 7)``). The structures these builders return are still 3-uniform,
    3-regular and vertex-transitive under ``Z/13Z``, which is all any current
    caller relies on. Renaming them is tracked in the ledger; if this test
    starts failing, the builder became a real STS and the callers' names,
    citations and iso-class expectations must be revisited.
    """
    coverage = _pair_coverage(cyclic_triple_orbit_13(base))
    assert len(coverage) == 39 < 13 * 12 // 2


# ---------------------------------------------------------------------------
# GQ(2,2), the doily
# ---------------------------------------------------------------------------


def test_doily_is_3_uniform_with_15_points_and_15_lines() -> None:
    H = gq_2_2_doily()
    assert (H.n_nodes, H.n_edges) == (15, 15)
    assert all(len(members) == 3 for _, members, _ in H.iter_edges())


def test_doily_every_point_lies_on_exactly_three_lines() -> None:
    H = gq_2_2_doily()
    assert {H.degree(v) for v in H.nodes()} == {3}


def test_doily_is_a_partial_linear_space() -> None:
    """Two distinct lines meet in at most one point.

    This is the axiom the superseded hardcoded edge list violated: its lines
    ``{5, 10, 13}`` and ``{10, 13, 14}`` shared the pair ``{10, 13}``.
    """
    coverage = _pair_coverage(gq_2_2_doily())
    assert max(coverage.values()) == 1
    assert len(coverage) == 45


def test_doily_point_graph_is_srg_15_6_1_3() -> None:
    """Collinearity graph is the Kneser graph K(6,2): srg(15, 6, 1, 3)."""
    H = gq_2_2_doily()
    nbrs = _primal_neighbours(H)
    assert {len(s) for s in nbrs.values()} == {6}
    for u, v in itertools.combinations(range(15), 2):
        common = len(nbrs[u] & nbrs[v])
        expected = 1 if v in nbrs[u] else 3
        assert common == expected, f"({u}, {v}): {common} common neighbours"


def test_doily_satisfies_the_gq_axiom() -> None:
    """For a point ``p`` off a line ``L``, exactly one point of ``L`` is
    collinear with ``p`` -- the generalised-quadrangle axiom GQ(s=2, t=2)."""
    H = gq_2_2_doily()
    nbrs = _primal_neighbours(H)
    for _, line, _ in H.iter_edges():
        for p in H.nodes():
            if p in line:
                continue
            assert len(line & nbrs[p]) == 1


def test_doily_is_vertex_transitive_under_both_seed_cascades() -> None:
    """Every iso-invariant vertex statistic is constant on a vertex-transitive
    design, so both seed rules must return the whole vertex set. The rule that
    exposed the superseded fixture: it returned 7 of 15 seeds."""
    H = gq_2_2_doily()
    assert len(max_neighbor_degree_nodes(H)) == 15
    assert len(max_xi_nodes(H)) == 15
