"""Unit tests for ``SizeL1Distance`` — the two-integer size baseline (T-M4b)."""

from __future__ import annotations

import numpy as np
import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.metric_space.registry import get_distance
from isalhg.metric_space.representations.size_l1 import SizeL1Distance

pytestmark = pytest.mark.unit


def _hg(n: int, edges: list[set[int]]) -> SparseHypergraph:
    return SparseHypergraph(n_nodes=n, hyperedges=[frozenset(e) for e in edges])


class TestSizeL1:
    def test_registry_name(self) -> None:
        d = get_distance("size_l1")
        assert isinstance(d, SizeL1Distance)
        assert d.name == "size_l1"

    def test_definition(self) -> None:
        d = SizeL1Distance()
        H1 = _hg(4, [{0, 1, 2}, {2, 3}])
        H2 = _hg(6, [{0, 1}, {1, 2}, {3, 4, 5}])
        assert d.pairwise(H1, H2) == pytest.approx(abs(4 - 6) + abs(2 - 3))

    def test_symmetry(self) -> None:
        d = SizeL1Distance()
        H1 = _hg(4, [{0, 1, 2}, {2, 3}])
        H2 = _hg(6, [{0, 1}, {1, 2}, {3, 4, 5}])
        assert d.pairwise(H1, H2) == d.pairwise(H2, H1)

    def test_blind_to_structure(self) -> None:
        # Same (n, m), different structure: distance must be exactly 0.
        d = SizeL1Distance()
        H1 = _hg(4, [{0, 1, 2}, {2, 3}])
        H2 = _hg(4, [{0, 1}, {1, 2, 3}])
        assert d.pairwise(H1, H2) == 0.0

    def test_fingerprint(self) -> None:
        d = SizeL1Distance()
        assert d.fingerprint(_hg(4, [{0, 1, 2}, {2, 3}])) == (4, 2)

    def test_matrix_matches_pairwise(self) -> None:
        d = SizeL1Distance()
        corpus = [
            _hg(4, [{0, 1, 2}, {2, 3}]),
            _hg(6, [{0, 1}, {1, 2}, {3, 4, 5}]),
            _hg(4, [{0, 1}, {1, 2, 3}]),
        ]
        D = d.matrix(corpus)
        assert D.shape == (3, 3)
        assert np.allclose(D, D.T)
        assert np.allclose(np.diag(D), 0.0)
        for i in range(3):
            for j in range(3):
                assert D[i, j] == pytest.approx(d.pairwise(corpus[i], corpus[j]))

    def test_matrix_empty(self) -> None:
        assert SizeL1Distance().matrix([]).shape == (0, 0)
