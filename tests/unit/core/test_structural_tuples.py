"""Unit tests for :mod:`isalhg.core.structural_tuples`."""

from __future__ import annotations

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.structural_tuples import eta, max_xi_nodes, xi

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
