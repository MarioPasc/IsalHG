"""Unit tests for :class:`isalhg.core.sparse_hypergraph.SparseHypergraph`."""

from __future__ import annotations

import pytest

from isalhg.core.sparse_hypergraph import (
    SparseHypergraph,
    assert_vocab_compatible,
    permute,
)
from isalhg.errors import InvalidLabelError, VocabularyMismatchError

pytestmark = pytest.mark.unit


class TestConstruction:
    def test_trivial_no_edges(self) -> None:
        H = SparseHypergraph(n_nodes=3)
        assert H.n_nodes == 3
        assert H.n_edges == 0
        assert list(H.nodes()) == [0, 1, 2]
        assert list(H.hyperedges()) == []

    def test_with_edges(self, fano_plane: SparseHypergraph) -> None:
        assert fano_plane.n_nodes == 7
        assert fano_plane.n_edges == 7

    def test_duplicate_edges_silently_dropped(self) -> None:
        H = SparseHypergraph(
            n_nodes=3,
            hyperedges=[frozenset({0, 1, 2}), frozenset({0, 1, 2})],
        )
        assert H.n_edges == 1

    def test_negative_n_nodes_rejected(self) -> None:
        with pytest.raises(ValueError):
            SparseHypergraph(n_nodes=-1)

    def test_label_vocab_size_must_be_positive(self) -> None:
        with pytest.raises(ValueError):
            SparseHypergraph(n_nodes=1, n_vertex_labels=0)


class TestAddOperations:
    def test_add_node_returns_id(self) -> None:
        H = SparseHypergraph(n_nodes=0)
        v0 = H.add_node()
        v1 = H.add_node()
        assert v0 == 0
        assert v1 == 1
        assert H.n_nodes == 2

    def test_add_hyperedge(self) -> None:
        H = SparseHypergraph(n_nodes=4)
        e = H.add_hyperedge([0, 1, 2])
        assert e == 0
        assert H.members(e) == frozenset({0, 1, 2})
        assert H.degree(0) == 1
        assert H.degree(3) == 0

    def test_add_hyperedge_dedup(self) -> None:
        H = SparseHypergraph(n_nodes=3)
        e0 = H.add_hyperedge([0, 1, 2])
        e1 = H.add_hyperedge([0, 1, 2])
        assert e0 == e1
        assert H.n_edges == 1

    def test_add_hyperedge_out_of_range_vertex(self) -> None:
        H = SparseHypergraph(n_nodes=3)
        with pytest.raises(ValueError):
            H.add_hyperedge([0, 1, 5])

    def test_invalid_label(self) -> None:
        H = SparseHypergraph(n_nodes=3, n_vertex_labels=1)
        with pytest.raises(InvalidLabelError):
            H.add_node(label=1)


class TestQueries:
    def test_neighbors_distance_1(self, fano_plane: SparseHypergraph) -> None:
        for v in range(7):
            assert fano_plane.neighbors(v, depth=1) == set(range(7)) - {v}

    def test_neighbors_invalid_depth(self) -> None:
        H = SparseHypergraph(n_nodes=3, hyperedges=[frozenset({0, 1, 2})])
        assert H.neighbors(0, depth=0) == set()

    def test_degree(self, fano_plane: SparseHypergraph) -> None:
        for v in range(7):
            assert fano_plane.degree(v) == 3

    def test_is_connected_singleton(self) -> None:
        H = SparseHypergraph(n_nodes=1)
        assert H.is_connected()

    def test_is_connected_isolated_vertex(self) -> None:
        H = SparseHypergraph(n_nodes=3, hyperedges=[frozenset({0, 1})])
        assert not H.is_connected()

    def test_is_connected_path(self) -> None:
        H = SparseHypergraph(
            n_nodes=4,
            hyperedges=[frozenset({0, 1}), frozenset({1, 2}), frozenset({2, 3})],
        )
        assert H.is_connected()

    def test_primal_graph(self) -> None:
        H = SparseHypergraph(
            n_nodes=4,
            hyperedges=[frozenset({0, 1, 2}), frozenset({2, 3})],
        )
        adj = H.primal_graph()
        assert adj[0] == {1, 2}
        assert adj[2] == {0, 1, 3}
        assert adj[3] == {2}


class TestPermute:
    def test_identity_permutation(self, fano_plane: SparseHypergraph) -> None:
        sigma = list(range(7))
        H2 = permute(fano_plane, sigma)
        assert fano_plane == H2

    def test_non_trivial_permutation(self, single_edge_hypergraph: SparseHypergraph) -> None:
        sigma = [2, 0, 1]
        H2 = permute(single_edge_hypergraph, sigma)
        assert list(H2.hyperedges()) == list(single_edge_hypergraph.hyperedges())

    def test_invalid_permutation(self, single_edge_hypergraph: SparseHypergraph) -> None:
        with pytest.raises(ValueError):
            permute(single_edge_hypergraph, [0, 0, 2])

    def test_iso_pair_fixture_consistency(
        self,
        iso_pair_small: tuple[SparseHypergraph, SparseHypergraph, list[int]],
    ) -> None:
        h1, h2, sigma = iso_pair_small
        assert permute(h1, sigma) == h2

    def test_double_permute_inverse(self, fano_plane: SparseHypergraph) -> None:
        sigma = [3, 1, 4, 0, 5, 6, 2]
        inverse = [0] * 7
        for i, v in enumerate(sigma):
            inverse[v] = i
        H2 = permute(fano_plane, sigma)
        H3 = permute(H2, inverse)
        assert fano_plane == H3


class TestVocabularyChecks:
    def test_compatible(self) -> None:
        H1 = SparseHypergraph(n_nodes=2, n_vertex_labels=2, n_edge_labels=3)
        H2 = SparseHypergraph(n_nodes=4, n_vertex_labels=2, n_edge_labels=3)
        assert_vocab_compatible(H1, H2)

    def test_incompatible(self) -> None:
        H1 = SparseHypergraph(n_nodes=2, n_vertex_labels=2)
        H2 = SparseHypergraph(n_nodes=2, n_vertex_labels=3)
        with pytest.raises(VocabularyMismatchError):
            assert_vocab_compatible(H1, H2)
