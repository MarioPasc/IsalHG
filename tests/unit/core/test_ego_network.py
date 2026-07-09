"""Unit tests for :func:`isalhg.core.sparse_hypergraph.ego_network`.

The ego network is Qin et al. (ICDE 2023) Definition 1: the sub-hypergraph
*induced* on the closed neighbourhood ``NEI(v)``, keeping only hyperedges
fully contained in it. The Fig. 1 fixture anchors the extraction against the
paper's Example 1 (both stated ``NEI`` sets and both ego networks).
"""

from __future__ import annotations

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph, ego_network

pytestmark = pytest.mark.unit

U4, U5 = 3, 4  # paper node u_i -> fixture id i - 1


class TestQinExample1:
    def test_ego_u4_nodes_and_labels(self, qin_fig1_hypergraph: SparseHypergraph) -> None:
        # NEI(u4) = {u1, u2, u4, u5, u6, u7, u8} -- u3 excluded.
        ego = ego_network(qin_fig1_hypergraph, U4)
        assert ego.n_nodes == 7
        assert [ego.vertex_label(v) for v in range(7)] == [0, 0, 1, 1, 2, 2, 2]

    def test_ego_u4_edges(self, qin_fig1_hypergraph: SparseHypergraph) -> None:
        # Kept: E1, E2, E4 (E3 contains u3 outside NEI(u4)). Remap:
        # keep = [0,1,3,4,5,6,7] -> {0:0, 1:1, 3:2, 4:3, 5:4, 6:5, 7:6}.
        ego = ego_network(qin_fig1_hypergraph, U4)
        expected = {
            (0, frozenset({0, 1, 2})),  # E1
            (0, frozenset({2, 4, 5})),  # E2
            (1, frozenset({2, 3, 5, 6})),  # E4
        }
        actual = {(ell, members) for _, members, ell in ego.iter_edges()}
        assert actual == expected

    def test_ego_u5_nodes_and_edges(self, qin_fig1_hypergraph: SparseHypergraph) -> None:
        # NEI(u5) = {u2, u3, u4, u5, u7, u8}; kept edges E3, E4.
        ego = ego_network(qin_fig1_hypergraph, U5)
        assert ego.n_nodes == 6
        assert [ego.vertex_label(v) for v in range(6)] == [0, 0, 1, 1, 2, 2]
        actual = {(ell, members) for _, members, ell in ego.iter_edges()}
        expected = {
            (1, frozenset({0, 1, 3})),  # E3 = {u2, u3, u5}
            (1, frozenset({2, 3, 4, 5})),  # E4 = {u4, u5, u7, u8}
        }
        assert actual == expected


class TestEdgeCases:
    def test_isolated_centre(self) -> None:
        h = SparseHypergraph(3, [frozenset({0, 1})])
        ego = ego_network(h, 2)
        assert ego.n_nodes == 1
        assert ego.n_edges == 0

    def test_partial_overlap_edge_dropped_not_truncated(self) -> None:
        # {0,1} puts 1 in NEI(0); {1,2} straddles the boundary and must be
        # dropped whole, never truncated to {1}.
        h = SparseHypergraph(3, [frozenset({0, 1}), frozenset({1, 2})])
        ego = ego_network(h, 0)
        assert ego.n_nodes == 2
        assert [m for _, m, _ in ego.iter_edges()] == [frozenset({0, 1})]

    def test_whole_graph_when_fully_connected(self) -> None:
        h = SparseHypergraph(4, [frozenset({0, 1, 2, 3}), frozenset({1, 2})])
        ego = ego_network(h, 0)
        assert ego.n_nodes == 4
        assert ego.n_edges == 2

    def test_vocabulary_sizes_preserved(self, qin_fig1_hypergraph: SparseHypergraph) -> None:
        ego = ego_network(qin_fig1_hypergraph, U4)
        assert ego.n_vertex_labels == qin_fig1_hypergraph.n_vertex_labels
        assert ego.n_edge_labels == qin_fig1_hypergraph.n_edge_labels

    def test_out_of_range_raises(self) -> None:
        h = SparseHypergraph(2, [frozenset({0, 1})])
        with pytest.raises(ValueError):
            ego_network(h, 2)
        with pytest.raises(ValueError):
            ego_network(h, -1)
