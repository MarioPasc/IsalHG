"""Unit tests for the H2S algorithm ABC + concrete variants."""

from __future__ import annotations

import pytest

from isalhg.core.algorithms.base import H2SAlgorithm
from isalhg.core.algorithms.greedy_min import GreedyMin
from isalhg.core.canonical import required_k
from isalhg.core.sparse_hypergraph import SparseHypergraph

pytestmark = pytest.mark.unit


class TestGreedyMin:
    def test_is_subclass(self) -> None:
        assert issubclass(GreedyMin, H2SAlgorithm)

    def test_name(self) -> None:
        assert GreedyMin(k=3).name == "greedy_min"

    def test_encode_returns_tuple(self, single_edge_hypergraph: SparseHypergraph) -> None:
        algo = GreedyMin(k=required_k(single_edge_hypergraph))
        tokens = algo.encode(single_edge_hypergraph)
        assert isinstance(tokens, tuple)
        assert len(tokens) >= 1

    def test_encode_empty_hypergraph(self) -> None:
        algo = GreedyMin(k=2)
        H = SparseHypergraph(n_nodes=0)
        assert algo.encode(H) == ()


class TestAbstractness:
    def test_cannot_instantiate_abc(self) -> None:
        with pytest.raises(TypeError):
            H2SAlgorithm()  # type: ignore[abstract]
