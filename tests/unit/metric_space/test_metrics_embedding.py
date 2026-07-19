"""Unit tests for :mod:`isalhg.metric_space.metrics.embedding`.

Classical MDS, Kruskal stress-1, and PSD check — all verified with
hand-computable or analytically-known values.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

np = pytest.importorskip("numpy")
pytest.importorskip("scipy")


from isalhg.metric_space.metrics.embedding import (  # noqa: E402
    classical_mds,
    embed_classical,
    is_psd,
    kruskal_stress_1,
    neg_eigenvalue_mass,
    shepard_data,
)


def _euclidean_distance_matrix(X: np.ndarray) -> np.ndarray:
    """Compute the pairwise Euclidean distance matrix from a coordinate matrix."""
    n = X.shape[0]
    D = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            d = float(np.linalg.norm(X[i] - X[j]))
            D[i, j] = d
            D[j, i] = d
    return D


class TestClassicalMds:
    def test_returns_eigenvalues_and_eigenvectors(self) -> None:
        D = np.array([[0, 1, 2], [1, 0, 1], [2, 1, 0]], dtype=float)
        eigenvalues, eigenvectors = classical_mds(D)
        assert eigenvalues.shape == (3,)
        assert eigenvectors.shape == (3, 3)

    def test_eigenvalues_sorted_descending(self) -> None:
        rng = np.random.default_rng(5)
        X = rng.random((6, 2))
        D = _euclidean_distance_matrix(X)
        eigenvalues, _ = classical_mds(D)
        # Must be returned largest-first so embed_classical can slice [:n_dims]
        assert all(eigenvalues[i] >= eigenvalues[i + 1] for i in range(len(eigenvalues) - 1))

    def test_zero_matrix_all_eigenvalues_zero(self) -> None:
        D = np.zeros((4, 4))
        eigenvalues, _ = classical_mds(D)
        np.testing.assert_allclose(eigenvalues, 0.0, atol=1e-10)


class TestIsPsd:
    def test_positive_eigenvalues(self) -> None:
        eigs = np.array([3.0, 2.0, 1.0, 0.0])
        assert is_psd(eigs) is True

    def test_slightly_negative_within_tol(self) -> None:
        eigs = np.array([3.0, 1.0, -1e-12])
        assert is_psd(eigs, tol=1e-10) is True

    def test_clearly_negative(self) -> None:
        eigs = np.array([3.0, 1.0, -0.5])
        assert is_psd(eigs) is False

    def test_euclidean_distance_matrix_is_psd(self) -> None:
        # Points on a line embed exactly; Gram matrix should be PSD
        X = np.array([[0.0], [1.0], [2.0], [3.0]])
        D = _euclidean_distance_matrix(X)
        eigenvalues, _ = classical_mds(D)
        assert is_psd(eigenvalues, tol=1e-8)


class TestEmbedClassical:
    def test_1d_line_reconstruction(self) -> None:
        # 4 collinear points; classical MDS in 1D should recover distances exactly
        X_true = np.array([[0.0], [1.0], [2.0], [3.0]])
        D = _euclidean_distance_matrix(X_true)
        X_emb = embed_classical(D, n_dims=1)
        assert X_emb.shape == (4, 1)
        # Pairwise distances of embedding should match original (up to sign/reflection)
        D_emb = _euclidean_distance_matrix(X_emb)
        np.testing.assert_allclose(D_emb, D, atol=1e-6)

    def test_2d_plane_reconstruction(self) -> None:
        rng = np.random.default_rng(6)
        X_true = rng.random((5, 2))
        D = _euclidean_distance_matrix(X_true)
        X_emb = embed_classical(D, n_dims=2)
        assert X_emb.shape == (5, 2)
        D_emb = _euclidean_distance_matrix(X_emb)
        np.testing.assert_allclose(D_emb, D, atol=1e-6)

    def test_n_dims_larger_than_rank_clips(self) -> None:
        # 3 collinear points: rank of B = 1, but we request 2 dims
        X_true = np.array([[0.0], [1.0], [2.0]])
        D = _euclidean_distance_matrix(X_true)
        X_emb = embed_classical(D, n_dims=2)
        assert X_emb.shape == (3, 2)


class TestKruskalStress1:
    def test_zero_stress_on_perfect_embedding(self) -> None:
        X_true = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
        D = _euclidean_distance_matrix(X_true)
        X_emb = embed_classical(D, n_dims=2)
        D_emb = _euclidean_distance_matrix(X_emb)
        stress = kruskal_stress_1(D, D_emb)
        assert stress < 1e-6

    def test_stress_in_0_1(self) -> None:
        rng = np.random.default_rng(7)
        n = 8
        D1 = rng.random((n, n))
        D1 = (D1 + D1.T) / 2
        np.fill_diagonal(D1, 0.0)
        D2 = rng.random((n, n))
        D2 = (D2 + D2.T) / 2
        np.fill_diagonal(D2, 0.0)
        stress = kruskal_stress_1(D1, D2)
        assert stress >= 0.0

    def test_stress_zero_when_equal(self) -> None:
        D = np.array([[0, 1, 3], [1, 0, 2], [3, 2, 0]], dtype=float)
        stress = kruskal_stress_1(D, D)
        assert stress < 1e-10


class TestNegEigenvalueMass:
    def test_all_positive_mass_zero(self) -> None:
        eigs = np.array([3.0, 2.0, 1.0, 0.5])
        assert neg_eigenvalue_mass(eigs) == pytest.approx(0.0)

    def test_known_mix(self) -> None:
        # eigenvalues [1.2, 0.8, 0.1, -0.5]
        # ν = 0.5 / (1.2+0.8+0.1+0.5) = 0.5/2.6
        eigs = np.array([1.2, 0.8, 0.1, -0.5])
        expected = 0.5 / 2.6
        assert neg_eigenvalue_mass(eigs) == pytest.approx(expected, rel=1e-9)

    def test_all_zero_returns_zero(self) -> None:
        eigs = np.array([0.0, 0.0, 0.0])
        assert neg_eigenvalue_mass(eigs) == pytest.approx(0.0)

    def test_numerical_noise_not_counted(self) -> None:
        # Eigenvalue at -1e-15 is numerical noise; should not inflate ν
        eigs = np.array([2.0, 0.5, -1e-15, -0.25])
        # Only -0.25 should count (tol=1e-10 by default)
        expected = 0.25 / (2.0 + 0.5 + 1e-15 + 0.25)
        assert neg_eigenvalue_mass(eigs) == pytest.approx(expected, rel=1e-6)

    def test_pinned_spectrum_edit_distance_matrix(self) -> None:
        # D from edit distances on 4 strings: "ab", "ba", "a", "b"
        # d("ab","ba")=2; others=1 — a non-Euclidean metric
        D = np.array([[0, 2, 1, 1], [2, 0, 1, 1], [1, 1, 0, 1], [1, 1, 1, 0]], dtype=float)
        eigenvalues, _ = classical_mds(D)
        # Largest eigenvalue ≈ 2.0; smallest ≈ -0.25 (non-Euclidean)
        assert eigenvalues[0] == pytest.approx(2.0, rel=1e-6)
        assert eigenvalues[-1] < -0.1
        nu = neg_eigenvalue_mass(eigenvalues)
        # ν = 0.25 / (2.0+0.5+~0+0.25) ≈ 0.0909
        assert nu == pytest.approx(0.25 / 2.75, rel=1e-4)
        assert is_psd(eigenvalues) is False

    def test_euclidean_distance_matrix_mass_zero(self) -> None:
        rng = np.random.default_rng(42)
        X = rng.random((6, 2))
        D = _euclidean_distance_matrix(X)
        eigenvalues, _ = classical_mds(D)
        # Euclidean metric → PSD Gram matrix → ν = 0
        assert neg_eigenvalue_mass(eigenvalues) == pytest.approx(0.0, abs=1e-8)


class TestShepardData:
    def test_shape(self) -> None:
        n = 5
        rng = np.random.default_rng(1)
        D = rng.random((n, n))
        D = (D + D.T) / 2
        np.fill_diagonal(D, 0.0)
        d_orig, d_emb = shepard_data(D, D)
        expected_len = n * (n - 1) // 2
        assert d_orig.shape == (expected_len,)
        assert d_emb.shape == (expected_len,)

    def test_identical_matrices_gives_equal_arrays(self) -> None:
        D = np.array([[0, 1, 3], [1, 0, 2], [3, 2, 0]], dtype=float)
        d_orig, d_emb = shepard_data(D, D)
        np.testing.assert_allclose(d_orig, d_emb)

    def test_values_are_upper_triangle(self) -> None:
        D = np.array([[0, 2, 1, 1], [2, 0, 1, 1], [1, 1, 0, 1], [1, 1, 1, 0]], dtype=float)
        d_orig, _ = shepard_data(D, D)
        # Upper triangle of 4x4: indices (0,1),(0,2),(0,3),(1,2),(1,3),(2,3)
        expected = np.array([2.0, 1.0, 1.0, 1.0, 1.0, 1.0])
        np.testing.assert_allclose(d_orig, expected)

    def test_perfect_embedding_low_stress(self) -> None:
        X_true = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
        D = _euclidean_distance_matrix(X_true)
        X_emb = embed_classical(D, n_dims=2)
        D_emb = _euclidean_distance_matrix(X_emb)
        d_orig, d_emb = shepard_data(D, D_emb)
        # Perfect embedding: d_ij ≈ δ_ij
        np.testing.assert_allclose(d_orig, d_emb, atol=1e-6)
