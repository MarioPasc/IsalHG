"""Unit tests for :class:`isalhg.metric_space.distances.hged.BipartiteHGED`.

BP-HGED is the optional scalable cross-check (decision DQ2). It fixes a single
Riesen-Bunke node correspondence and returns the exact cost under it, so it is a
genuine edit sequence and therefore an **upper bound** on the exact oracle:
``ExactHGED <= BipartiteHGED``. The tests assert that inequality across a
perturbation-ladder sweep, plus the registry contract.
"""

from __future__ import annotations

import random

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph, edit_path
from isalhg.metric_space import registry
from isalhg.metric_space.distances.hged import BipartiteHGED, ExactHGED

pytestmark = pytest.mark.unit

pytest.importorskip("scipy")
pytest.importorskip("numpy")


class TestUpperBound:
    def test_self_distance_zero(self) -> None:
        h = SparseHypergraph(4, [frozenset({0, 1, 2}), frozenset({2, 3})])
        assert BipartiteHGED().pairwise(h, h) == 0.0

    def test_bp_ge_exact_on_ladder(self) -> None:
        exact = ExactHGED()
        bp = BipartiteHGED()
        rng = random.Random(2024)
        base = SparseHypergraph(5, [frozenset({0, 1, 2}), frozenset({2, 3}), frozenset({3, 4})])
        checked = 0
        for _ in range(25):
            t = rng.randint(0, 6)
            pert, _ = edit_path(base, t, rng)
            assert bp.pairwise(base, pert) >= exact.pairwise(base, pert)
            checked += 1
        assert checked == 25

    def test_bp_ge_exact_on_non_iso(
        self, non_iso_pair_small: tuple[SparseHypergraph, SparseHypergraph]
    ) -> None:
        h1, h2 = non_iso_pair_small
        assert BipartiteHGED().pairwise(h1, h2) >= ExactHGED().pairwise(h1, h2) > 0.0

    def test_non_negative(self) -> None:
        h1 = SparseHypergraph(3, [frozenset({0, 1, 2})])
        h2 = SparseHypergraph(4, [frozenset({0, 1}), frozenset({2, 3})])
        assert BipartiteHGED().pairwise(h1, h2) >= 0.0


class TestMatrixAndRegistry:
    def test_matrix_runs(self) -> None:
        np = pytest.importorskip("numpy")
        corpus = [
            SparseHypergraph(3, [frozenset({0, 1, 2})]),
            SparseHypergraph(4, [frozenset({0, 1}), frozenset({2, 3})]),
            SparseHypergraph(2, [frozenset({0, 1})]),
        ]
        matrix = BipartiteHGED().matrix(corpus)
        assert matrix.shape == (3, 3)
        assert np.allclose(matrix, matrix.T)
        assert np.allclose(np.diag(matrix), 0.0)

    def test_registered_and_retrievable(self) -> None:
        d = registry.get_distance("bipartite_hged")
        assert isinstance(d, BipartiteHGED)
        assert d.name == "bipartite_hged"
        assert "bipartite_hged" in registry.available_distances()
