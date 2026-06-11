"""Unit tests for :mod:`isalhg.iso_backends.levi_reduction`."""

from __future__ import annotations

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.iso_backends.levi_reduction import to_levi

pytestmark = pytest.mark.unit


class TestStructure:
    def test_empty_hypergraph(self) -> None:
        H = SparseHypergraph(n_nodes=0)
        levi = to_levi(H)
        assert levi.n_vertex_nodes == 0
        assert levi.n_edge_nodes == 0
        assert levi.edges == ()
        assert levi.colors == ()

    def test_single_edge(self, single_edge_hypergraph: SparseHypergraph) -> None:
        levi = to_levi(single_edge_hypergraph)
        # 3 vertex nodes + 1 edge node.
        assert levi.n_vertex_nodes == 3
        assert levi.n_edge_nodes == 1
        # Bipartite edges = arity = 3.
        assert len(levi.edges) == 3
        # Edge node has ID 3.
        for u, v in levi.edges:
            assert {u, v} & {3} == {3}

    def test_fano_dimensions(self, fano_plane: SparseHypergraph) -> None:
        levi = to_levi(fano_plane)
        assert levi.n_vertex_nodes == 7
        assert levi.n_edge_nodes == 7
        # 7 lines * 3 vertices = 21 incidences.
        assert len(levi.edges) == 21


class TestColours:
    def test_trivial_vocab_two_classes(self, fano_plane: SparseHypergraph) -> None:
        levi = to_levi(fano_plane)
        # All vertices share label 0; all edges share label 0; vertex side
        # colour = 0; edge side colour = n_vertex_labels = 1.
        assert set(levi.colors) == {0, 1}
        # First 7 are vertex side (colour 0), last 7 are edge side (colour 1).
        assert all(c == 0 for c in levi.colors[:7])
        assert all(c == 1 for c in levi.colors[7:])

    def test_labelled_disjoint_ranges(self) -> None:
        H = SparseHypergraph(
            n_nodes=2,
            hyperedges=[frozenset({0, 1})],
            n_vertex_labels=2,
            n_edge_labels=3,
            vertex_labels=[0, 1],
            edge_labels=[2],
        )
        levi = to_levi(H)
        # Vertex side colours: 0, 1. Edge side colour: |Sigma_v| + 2 = 4.
        assert levi.colors == (0, 1, 4)

    def test_color_classes(self, fano_plane: SparseHypergraph) -> None:
        levi = to_levi(fano_plane)
        classes = levi.color_classes()
        assert len(classes) == 2
        assert classes[0] == set(range(7))
        assert classes[1] == set(range(7, 14))


class TestPartition:
    def test_partition_indices(self, fano_plane: SparseHypergraph) -> None:
        levi = to_levi(fano_plane)
        v_side, e_side = levi.vertex_partition()
        assert v_side == tuple(range(7))
        assert e_side == tuple(range(7, 14))
