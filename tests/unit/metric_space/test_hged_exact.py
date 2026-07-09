"""Unit tests for :class:`isalhg.metric_space.distances.hged.ExactHGED`.

The exact HGED oracle is validated three ways: (1) against hand-computed edit
counts on tiny fixtures -- one per atomic op plus a composite path; (2) the
metric identities self-distance-0, symmetry, and permutation-invariance
(``w*`` is iso-invariant, so is HGED); (3) the ceiling guard
(``max_expansions`` raises :class:`HGEDComputationError`). Costs follow the
article's official Qin et al. (ICDE 2023) empty-shell taxonomy: deleting or
inserting a ``k``-node hyperedge costs ``k + 1``.
"""

from __future__ import annotations

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.errors import HGEDComputationError
from isalhg.metric_space import registry
from isalhg.metric_space.distances.hged import ExactHGED

pytestmark = pytest.mark.unit

pytest.importorskip("scipy")
pytest.importorskip("numpy")


def _hged(h1: SparseHypergraph, h2: SparseHypergraph) -> float:
    return ExactHGED().pairwise(h1, h2)


class TestHandComputed:
    """Each fixture isolates one unit edit (or a short composite path)."""

    def test_identical_is_zero(self) -> None:
        h = SparseHypergraph(3, [frozenset({0, 1, 2})])
        assert _hged(h, h) == 0.0

    def test_insert_isolated_vertex(self) -> None:
        h1 = SparseHypergraph(3, [frozenset({0, 1, 2})])
        h2 = SparseHypergraph(4, [frozenset({0, 1, 2})])
        assert _hged(h1, h2) == 1.0

    def test_add_incidence(self) -> None:
        h1 = SparseHypergraph(3, [frozenset({0, 1})])
        h2 = SparseHypergraph(3, [frozenset({0, 1, 2})])
        assert _hged(h1, h2) == 1.0

    def test_delete_edge_costs_k_plus_1(self) -> None:
        # Qin empty-shell convention: 3 incidence reduces + 1 shell delete = 4.
        h1 = SparseHypergraph(3, [frozenset({0, 1, 2})])
        h2 = SparseHypergraph(3, [])
        assert _hged(h1, h2) == 4.0

    def test_insert_edge_costs_k_plus_1(self) -> None:
        h1 = SparseHypergraph(3, [])
        h2 = SparseHypergraph(3, [frozenset({0, 1, 2})])
        assert _hged(h1, h2) == 4.0

    def test_vertex_label_substitution(self) -> None:
        h1 = SparseHypergraph(2, [frozenset({0, 1})], n_vertex_labels=2, vertex_labels=[0, 0])
        h2 = SparseHypergraph(2, [frozenset({0, 1})], n_vertex_labels=2, vertex_labels=[0, 1])
        assert _hged(h1, h2) == 1.0

    def test_edge_label_substitution(self) -> None:
        h1 = SparseHypergraph(2, [frozenset({0, 1})], n_edge_labels=2, edge_labels=[0])
        h2 = SparseHypergraph(2, [frozenset({0, 1})], n_edge_labels=2, edge_labels=[1])
        assert _hged(h1, h2) == 1.0

    def test_composite_path(self) -> None:
        # {0,1,2} -> remove incidence 2 (1) -> {0,1}; insert {1,2} = shell +
        # 2 extends (3): total 4. Def 6 ({3} vs {2,2} -> 3) + edge-count Ψ (1)
        # confirm 4 as a lower bound.
        h1 = SparseHypergraph(3, [frozenset({0, 1, 2})])
        h2 = SparseHypergraph(3, [frozenset({0, 1}), frozenset({1, 2})])
        assert _hged(h1, h2) == 4.0

    def test_two_labelled_vertices_and_edge(self) -> None:
        # One vertex relabel + one edge relabel = 2.
        h1 = SparseHypergraph(
            2,
            [frozenset({0, 1})],
            n_vertex_labels=2,
            n_edge_labels=2,
            vertex_labels=[0, 0],
            edge_labels=[0],
        )
        h2 = SparseHypergraph(
            2,
            [frozenset({0, 1})],
            n_vertex_labels=2,
            n_edge_labels=2,
            vertex_labels=[0, 1],
            edge_labels=[1],
        )
        assert _hged(h1, h2) == 2.0


class TestMetricIdentities:
    def test_self_distance_zero(self, fano_plane: SparseHypergraph) -> None:
        assert _hged(fano_plane, fano_plane) == 0.0

    def test_symmetry(self) -> None:
        h1 = SparseHypergraph(4, [frozenset({0, 1, 2}), frozenset({2, 3})])
        h2 = SparseHypergraph(3, [frozenset({0, 1})])
        assert _hged(h1, h2) == _hged(h2, h1)

    def test_permutation_invariance_is_zero(self) -> None:
        h = SparseHypergraph(5, [frozenset({0, 1, 2}), frozenset({2, 3}), frozenset({3, 4})])
        assert _hged(h, permute(h, [4, 3, 2, 1, 0])) == 0.0

    def test_positive_on_non_iso(
        self, non_iso_pair_small: tuple[SparseHypergraph, SparseHypergraph]
    ) -> None:
        h1, h2 = non_iso_pair_small
        assert _hged(h1, h2) > 0.0


class TestCeilingGuard:
    # Two 4-vertex hypergraphs (disjoint edges vs a path) whose optimum the
    # incumbent bound does not prove at the root, so the search must expand.
    _H1 = SparseHypergraph(4, [frozenset({0, 1}), frozenset({2, 3})])
    _H2 = SparseHypergraph(4, [frozenset({0, 1}), frozenset({1, 2})])

    def test_max_expansions_raises(self) -> None:
        with pytest.raises(HGEDComputationError):
            ExactHGED(max_expansions=1).pairwise(self._H1, self._H2)

    def test_generous_budget_completes(self) -> None:
        assert ExactHGED(max_expansions=100_000, timeout=30.0).pairwise(self._H1, self._H2) == 2.0


class TestMatrix:
    def test_matrix_symmetric_zero_diagonal(self) -> None:
        np = pytest.importorskip("numpy")
        corpus = [
            SparseHypergraph(3, [frozenset({0, 1, 2})]),
            SparseHypergraph(3, [frozenset({0, 1}), frozenset({1, 2})]),
            SparseHypergraph(4, [frozenset({0, 1}), frozenset({2, 3})]),
            SparseHypergraph(2, [frozenset({0, 1})]),
        ]
        matrix = ExactHGED().matrix(corpus)
        assert matrix.shape == (4, 4)
        assert np.allclose(matrix, matrix.T)
        assert np.allclose(np.diag(matrix), 0.0)
        assert (matrix[~np.eye(4, dtype=bool)] > 0).all()


class TestRegistry:
    def test_registered_and_retrievable(self) -> None:
        d = registry.get_distance("exact_hged")
        assert isinstance(d, ExactHGED)
        assert d.name == "exact_hged"
        assert "exact_hged" in registry.available_distances()
