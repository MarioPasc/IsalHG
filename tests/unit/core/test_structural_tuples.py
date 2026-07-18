"""Unit tests for :mod:`isalhg.core.structural_tuples`."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.structural_tuples import (
    _python_max_neighbor_degree_nodes,
    eta,
    max_xi_nodes,
    xi,
)

pytestmark = pytest.mark.unit


class TestXi:
    def test_isolated_node(self) -> None:
        H = SparseHypergraph(n_nodes=1)
        assert xi(H, 0, depth=3) == (0, 0, 0)

    def test_path_3_nodes(self) -> None:
        H = SparseHypergraph(
            n_nodes=3,
            hyperedges=[frozenset({0, 1}), frozenset({1, 2})],
        )
        # From 0: shell_1={1}, shell_2={2}, shell_3={}.
        assert xi(H, 0, depth=3) == (1, 1, 0)
        assert xi(H, 1, depth=3) == (2, 0, 0)

    def test_fano_is_distance_1(self, fano_plane: SparseHypergraph) -> None:
        for v in range(7):
            assert xi(fano_plane, v, depth=3) == (6, 0, 0)


class TestEta:
    def test_single_edge(self, single_edge_hypergraph: SparseHypergraph) -> None:
        # Edge {0,1,2}; xi(v) = (2, 0, 0) for each member. eta = (6, 0, 0).
        assert eta(single_edge_hypergraph, 0, depth=3) == (6, 0, 0)

    def test_fano_eta(self, fano_plane: SparseHypergraph) -> None:
        for e in fano_plane.edges():
            assert eta(fano_plane, e, depth=3) == (18, 0, 0)


class TestMaxXi:
    def test_singleton(self) -> None:
        H = SparseHypergraph(n_nodes=1)
        assert max_xi_nodes(H) == (0,)

    def test_fano_vertex_transitive(self, fano_plane: SparseHypergraph) -> None:
        assert set(max_xi_nodes(fano_plane)) == set(range(7))

    def test_path_central_node(self) -> None:
        H = SparseHypergraph(
            n_nodes=3,
            hyperedges=[frozenset({0, 1}), frozenset({1, 2})],
        )
        assert max_xi_nodes(H) == (1,)


class TestNeighbourDegreeKeyCallCount:
    """Regression guard: primal_graph() is built exactly once per seeder call.

    Before the T-M0b fix, _neighbour_degree_key called H.primal_graph()
    internally for every survivor node, giving (1 + |survivors|) total builds.
    The Fano plane is vertex-transitive so all 7 nodes survive step 2, making
    the old cost 8 builds vs 1 after the fix.  This test fails against the old
    _neighbour_degree_key body (restore ``adj = H.primal_graph()`` inside it to
    reproduce the failure).

    SparseHypergraph uses __slots__, so instance-level patching is not
    supported.  We patch the class method instead (class-level patch is
    equivalent for a single-threaded unit test).
    """

    def test_primal_graph_built_once_fano(self, fano_plane: SparseHypergraph) -> None:
        _real = SparseHypergraph.primal_graph
        call_count: list[int] = [0]

        def _counting(self):  # type: ignore[no-untyped-def]
            call_count[0] += 1
            return _real(self)

        with patch.object(SparseHypergraph, "primal_graph", _counting):
            _python_max_neighbor_degree_nodes(fano_plane)

        assert call_count[0] == 1, (
            f"primal_graph() called {call_count[0]} times; expected 1. "
            "Restoring 'adj = H.primal_graph()' inside _neighbour_degree_key "
            "reproduces this failure on the 7-survivor Fano plane (old cost: 8)."
        )

    def test_primal_graph_built_once_path(self) -> None:
        H = SparseHypergraph(
            n_nodes=4,
            hyperedges=[
                frozenset({0, 1}),
                frozenset({1, 2}),
                frozenset({2, 3}),
            ],
        )
        _real = SparseHypergraph.primal_graph
        call_count: list[int] = [0]

        def _counting(self):  # type: ignore[no-untyped-def]
            call_count[0] += 1
            return _real(self)

        with patch.object(SparseHypergraph, "primal_graph", _counting):
            _python_max_neighbor_degree_nodes(H)

        assert call_count[0] == 1
