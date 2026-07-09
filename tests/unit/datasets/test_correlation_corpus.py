"""Unit tests for the exact-HGED correlation corpus.

The corpus supplies small, exact-HGED-tractable hypergraphs for the Layer-1
study. The tests check determinism, that item sizes stay within the configured
range (so the exact oracle remains feasible), the labelled variant, the registry
wiring, and that ``ExactHGED.matrix`` runs over the corpus.
"""

from __future__ import annotations

import pytest

from isalhg.datasets import registry
from isalhg.datasets.synthetic.correlation_corpus import CorrelationCorpusHypergraphs

pytestmark = pytest.mark.unit


class TestStructure:
    def test_length(self) -> None:
        ds = CorrelationCorpusHypergraphs(n_items=12, seed=0)
        assert len(ds) == 12
        assert len(list(ds)) == 12

    def test_deterministic_under_seed(self) -> None:
        a = CorrelationCorpusHypergraphs(n_items=10, seed=5)
        b = CorrelationCorpusHypergraphs(n_items=10, seed=5)
        for x, y in zip(list(a), list(b), strict=True):
            assert x.item_id == y.item_id
            assert x.hypergraph == y.hypergraph

    def test_sizes_within_range(self) -> None:
        ds = CorrelationCorpusHypergraphs(n_range=(4, 7), n_edges_range=(2, 5), n_items=25, seed=1)
        for it in ds:
            assert 4 <= it.hypergraph.n_nodes <= 7
            assert it.iso_class is None

    def test_metadata(self) -> None:
        ds = CorrelationCorpusHypergraphs(n_range=(4, 6), n_items=15, seed=2)
        meta = ds.metadata
        assert meta.name == "correlation_corpus"
        assert meta.n_items == 15
        assert meta.has_iso_labels is False
        assert 4 <= meta.n_nodes_range[0] <= meta.n_nodes_range[1] <= 6

    def test_labelled_variant(self) -> None:
        ds = CorrelationCorpusHypergraphs(n_items=6, seed=3, n_vertex_labels=3, n_edge_labels=2)
        assert ds.metadata.label_vocabulary.n_vertex_labels == 3
        assert ds.metadata.label_vocabulary.n_edge_labels == 2
        for it in ds:
            assert it.hypergraph.n_vertex_labels == 3
            assert it.hypergraph.n_edge_labels == 2

    def test_seed_returns_new_instance(self) -> None:
        ds = CorrelationCorpusHypergraphs(n_items=8, seed=0)
        other = ds.seed(42)
        assert isinstance(other, CorrelationCorpusHypergraphs)
        assert other is not ds
        assert [it.hypergraph for it in other] != [it.hypergraph for it in ds]


class TestRegistry:
    def test_registered_and_retrievable(self) -> None:
        ds = registry.get_dataset("correlation_corpus", {"n_items": 6})
        assert isinstance(ds, CorrelationCorpusHypergraphs)
        assert "correlation_corpus" in registry.available_datasets()


class TestExactHGEDOverCorpus:
    def test_matrix_runs(self) -> None:
        np = pytest.importorskip("numpy")
        pytest.importorskip("scipy")
        from isalhg.metric_space.distances.hged import ExactHGED

        ds = CorrelationCorpusHypergraphs(n_range=(4, 6), n_items=8, seed=4)
        corpus = [it.hypergraph for it in ds]
        matrix = ExactHGED().matrix(corpus)
        assert matrix.shape == (8, 8)
        assert np.allclose(matrix, matrix.T)
        assert np.allclose(np.diag(matrix), 0.0)
        assert (matrix >= 0).all()
