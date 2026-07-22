"""Unit tests for :class:`~isalhg.metric_space.representations.degree_seq_l1`.

Acceptance criteria (T-M7c):

1. Non-negativity: ``d(H1, H2) >= 0`` for all pairs.
2. Symmetry: ``d(H1, H2) == d(H2, H1)``.
3. Triangle inequality: ``d(A, C) <= d(A, B) + d(B, C)`` on a pinned triple.
4. ``d = 0`` for isomorphic pairs (equal degree sequences follow from iso).
5. Incompleteness witness: the pinned ``non_iso_pair_small`` fixture has
   ``d = 0`` despite being non-isomorphic — documented and asserted.

Metric-axiom tests use simple hand-constructed hypergraphs so the expected
values can be verified by inspection.
"""

from __future__ import annotations

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.metric_space import registry
from isalhg.metric_space.representations.degree_seq_l1 import DegreeSequenceL1Distance

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Small helper hypergraphs
# ---------------------------------------------------------------------------


def _triangle() -> SparseHypergraph:
    """3-node, single 3-edge: all degrees 1. Degree seq [1, 1, 1]."""
    return SparseHypergraph(n_nodes=3, hyperedges=[frozenset({0, 1, 2})])


def _star3() -> SparseHypergraph:
    """4-node star: hub (degree 3) + 3 leaves (degree 1). Degree seq [3, 1, 1, 1]."""
    return SparseHypergraph(
        n_nodes=4,
        hyperedges=[frozenset({0, 1}), frozenset({0, 2}), frozenset({0, 3})],
    )


def _path3() -> SparseHypergraph:
    """4-node path: degrees [1, 2, 2, 1]. Degree seq [2, 2, 1, 1]."""
    return SparseHypergraph(
        n_nodes=4,
        hyperedges=[frozenset({0, 1}), frozenset({1, 2}), frozenset({2, 3})],
    )


class TestMetricAxioms:
    """Verify the three non-trivial metric axioms on pinned triples."""

    def test_non_negativity(self) -> None:
        d = DegreeSequenceL1Distance()
        assert d.pairwise(_triangle(), _star3()) >= 0.0
        assert d.pairwise(_star3(), _path3()) >= 0.0

    def test_symmetry(self) -> None:
        d = DegreeSequenceL1Distance()
        assert d.pairwise(_triangle(), _star3()) == d.pairwise(_star3(), _triangle())
        assert d.pairwise(_star3(), _path3()) == d.pairwise(_path3(), _star3())

    def test_self_distance_zero(self) -> None:
        d = DegreeSequenceL1Distance()
        for H in [_triangle(), _star3(), _path3()]:
            assert d.pairwise(H, H) == 0.0

    def test_triangle_inequality_pinned(self) -> None:
        """d(triangle, path3) <= d(triangle, star3) + d(star3, path3).

        Verified by hand:
        - triangle: [1, 1, 1] → padded to length 4: [1, 1, 1, 0]
        - star3:    [3, 1, 1, 1]
        - path3:    [2, 2, 1, 1]

        d(tri, star3) = |1-3| + |1-1| + |1-1| + |0-1| = 2 + 0 + 0 + 1 = 3
        d(star3, path3) = |3-2| + |1-2| + |1-1| + |1-1| = 1 + 1 + 0 + 0 = 2
        d(tri, path3) = |1-2| + |1-2| + |1-1| + |0-1| = 1 + 1 + 0 + 1 = 3

        Triangle: 3 <= 3 + 2 = 5 ✓
        """
        d = DegreeSequenceL1Distance()
        tri, star, path = _triangle(), _star3(), _path3()
        d_tri_star = d.pairwise(tri, star)
        d_star_path = d.pairwise(star, path)
        d_tri_path = d.pairwise(tri, path)
        # Pinned values for regression
        assert d_tri_star == pytest.approx(3.0)
        assert d_star_path == pytest.approx(2.0)
        assert d_tri_path == pytest.approx(3.0)
        # Axiom
        assert d_tri_path <= d_tri_star + d_star_path + 1e-10


class TestIsoInvariance:
    """d = 0 on isomorphic pairs (degree sequences are iso-invariant)."""

    def test_zero_on_iso_pair_fixture(
        self, iso_pair_small: tuple[SparseHypergraph, SparseHypergraph, list[int]]
    ) -> None:
        h1, h2, _ = iso_pair_small
        assert DegreeSequenceL1Distance().pairwise(h1, h2) == 0.0

    def test_zero_on_permuted_fano(self, fano_plane: SparseHypergraph) -> None:
        sigma = list(range(6, -1, -1))  # reverse of 0..6
        d = DegreeSequenceL1Distance()
        assert d.pairwise(fano_plane, permute(fano_plane, sigma)) == 0.0

    def test_zero_on_permuted_sts9(self, sts_9: SparseHypergraph) -> None:
        sigma = list(range(8, -1, -1))
        d = DegreeSequenceL1Distance()
        assert d.pairwise(sts_9, permute(sts_9, sigma)) == 0.0


class TestIncompletenessWitness:
    """Pinned non-isomorphic pair with d = 0 — documents incompleteness.

    ``non_iso_pair_small``:
    - H1: 4 nodes, edges {{0,1,2}, {0,1,3}}   → degrees [2, 2, 1, 1]
    - H2: 4 nodes, edges {{0,1}, {1,2}, {2,3}} → degrees [2, 2, 1, 1]

    H1 and H2 are trivially non-isomorphic (arity profiles {3,3} ≠ {2,2,2}),
    yet share the same primal-degree multiset. The L1 distance is 0.
    This is the incompleteness witness: degree-sequence L1 cannot distinguish
    hypergraphs that differ only in hyperedge arity structure.
    """

    def test_incompleteness_witness_d_is_zero(
        self, non_iso_pair_small: tuple[SparseHypergraph, SparseHypergraph]
    ) -> None:
        h1, h2 = non_iso_pair_small
        d = DegreeSequenceL1Distance()
        assert d.pairwise(h1, h2) == pytest.approx(0.0), (
            "Incompleteness witness: non_iso_pair_small has degree seq [2,2,1,1] "
            "for both H1 and H2, so d_DS=0 despite non-isomorphism."
        )

    def test_distinct_designs_positive(
        self, fano_plane: SparseHypergraph, sts_9: SparseHypergraph
    ) -> None:
        """Fano (7 nodes, all degree 3) vs STS(9) (9 nodes, all degree 4) → positive."""
        d = DegreeSequenceL1Distance()
        assert d.pairwise(fano_plane, sts_9) > 0.0


class TestMatrix:
    def test_matrix_shape_and_symmetry(self) -> None:
        np = pytest.importorskip("numpy")
        corpus = [_triangle(), _star3(), _path3()]
        d = DegreeSequenceL1Distance()
        M = d.matrix(corpus)
        assert M.shape == (3, 3)
        assert np.allclose(M, M.T)
        assert np.allclose(np.diag(M), 0.0)

    def test_matrix_matches_pairwise(self) -> None:
        pytest.importorskip("numpy")
        corpus = [_triangle(), _star3(), _path3()]
        d = DegreeSequenceL1Distance()
        M = d.matrix(corpus)
        for i, Hi in enumerate(corpus):
            for j, Hj in enumerate(corpus):
                assert M[i, j] == pytest.approx(d.pairwise(Hi, Hj))

    def test_empty_corpus(self) -> None:
        pytest.importorskip("numpy")
        M = DegreeSequenceL1Distance().matrix([])
        assert M.shape == (0, 0)


class TestFingerprintAndName:
    def test_name(self) -> None:
        assert DegreeSequenceL1Distance().name == "degree_seq_l1"

    def test_fingerprint_is_sorted_descending(self) -> None:
        """Fingerprint is the degree sequence, sorted descending."""
        H = _star3()  # hub degree 3, three leaves degree 1
        fp = DegreeSequenceL1Distance().fingerprint(H)
        assert list(fp) == [3, 1, 1, 1]

    def test_fingerprint_iso_invariant(self, fano_plane: SparseHypergraph) -> None:
        sigma = [1, 2, 3, 4, 5, 6, 0]
        d = DegreeSequenceL1Distance()
        fp1 = d.fingerprint(fano_plane)
        fp2 = d.fingerprint(permute(fano_plane, sigma))
        assert fp1 == fp2


class TestRegistry:
    def test_registered_and_retrievable(self) -> None:
        d = registry.get_distance("degree_seq_l1")
        assert isinstance(d, DegreeSequenceL1Distance)
        assert d.name == "degree_seq_l1"
        assert "degree_seq_l1" in registry.available_distances()
