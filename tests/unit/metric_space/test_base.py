"""Unit tests for :mod:`isalhg.metric_space.base` via a trivial stub distance."""

from __future__ import annotations

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.metric_space.base import HypergraphDistance

pytestmark = pytest.mark.unit


class _NodeCountDistance(HypergraphDistance):
    """Trivial concrete distance: ``|n_nodes(H1) - n_nodes(H2)|``."""

    @property
    def name(self) -> str:
        return "nodecount_stub"

    def pairwise(self, H1: SparseHypergraph, H2: SparseHypergraph) -> float:
        return float(abs(H1.n_nodes - H2.n_nodes))


def _chain(n: int) -> SparseHypergraph:
    """A single hyperedge spanning all ``n`` vertices."""
    return SparseHypergraph(n_nodes=n, hyperedges=[frozenset(range(n))])


class TestABCContract:
    def test_cannot_instantiate_abc(self) -> None:
        with pytest.raises(TypeError):
            HypergraphDistance()  # type: ignore[abstract]

    def test_name(self) -> None:
        assert _NodeCountDistance().name == "nodecount_stub"

    def test_pairwise_identity_and_value(self) -> None:
        d = _NodeCountDistance()
        a, b = _chain(3), _chain(5)
        assert d.pairwise(a, a) == 0.0
        assert d.pairwise(a, b) == 2.0

    def test_fingerprint_default_none(self) -> None:
        assert _NodeCountDistance().fingerprint(_chain(2)) is None

    def test_repr_contains_name(self) -> None:
        assert "nodecount_stub" in repr(_NodeCountDistance())


class TestMatrix:
    def test_matrix_shape_symmetry_zero_diagonal(self) -> None:
        np = pytest.importorskip("numpy")
        d = _NodeCountDistance()
        corpus = [_chain(1), _chain(2), _chain(4)]
        matrix = d.matrix(corpus)
        assert matrix.shape == (3, 3)
        assert np.allclose(matrix, matrix.T)
        assert np.allclose(np.diag(matrix), 0.0)
        assert matrix[0, 1] == 1.0
        assert matrix[0, 2] == 3.0
        assert matrix[1, 2] == 2.0

    def test_matrix_empty_corpus(self) -> None:
        pytest.importorskip("numpy")
        matrix = _NodeCountDistance().matrix([])
        assert matrix.shape == (0, 0)
