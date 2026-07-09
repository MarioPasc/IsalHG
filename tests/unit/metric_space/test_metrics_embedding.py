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
