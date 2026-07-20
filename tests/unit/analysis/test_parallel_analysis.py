"""Unit tests for parallel_analysis in experiments.article.analysis.mds.

Acceptance criteria from T-M5l:
- parallel_analysis on a synthetic Euclidean rank-3 matrix → d_hat_horn in [2, 4].
- parallel_analysis on an i.i.d. noise dissimilarity matrix → d_hat_horn in [0, 2].
- The two cases discriminate: euclidean result > noise result.
- Return shapes match (n,) for observed_eigs and null_threshold_curve.
"""

from __future__ import annotations

import numpy as np
import pytest

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _euclidean_distance_matrix(X: np.ndarray) -> np.ndarray:
    """Exact pairwise Euclidean distances from coordinates X of shape (n, d)."""
    diff = X[:, None, :] - X[None, :, :]
    return np.sqrt(np.sum(diff**2, axis=-1))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_parallel_analysis_rank3_euclidean() -> None:
    """Horn PA recovers approximately 3 dimensions from a rank-3 Euclidean matrix."""
    from experiments.article.analysis.mds import parallel_analysis

    rng = np.random.default_rng(7)
    n = 40
    X_3d = rng.standard_normal((n, 3))
    D = _euclidean_distance_matrix(X_3d)

    d_hat_horn, obs_eigs, null_thresh = parallel_analysis(
        D, n_permutations=100, percentile=95, rng_seed=11
    )

    assert 2 <= d_hat_horn <= 4, (
        f"Expected d_hat_horn in [2, 4] for rank-3 Euclidean matrix, got {d_hat_horn}"
    )
    # Observed eigenvalues should have at least one large positive entry.
    assert obs_eigs[0] > 0, "Largest observed eigenvalue must be positive"
    # Null threshold should be below observed top eigenvalue (discrimination).
    assert obs_eigs[0] > null_thresh[0], (
        "Largest observed eigenvalue should exceed its null threshold for structured data"
    )


def test_parallel_analysis_noise_returns_zero() -> None:
    """Horn PA returns d_hat_horn near 0 for a pure-noise dissimilarity matrix."""
    from experiments.article.analysis.mds import parallel_analysis

    rng = np.random.default_rng(99)
    n = 30
    # Random symmetric matrix with positive off-diagonal entries — no geometric structure.
    A = rng.uniform(1.0, 5.0, (n, n))
    D_noise = (A + A.T) / 2.0
    np.fill_diagonal(D_noise, 0.0)

    d_hat_horn, obs_eigs, null_thresh = parallel_analysis(
        D_noise, n_permutations=100, percentile=95, rng_seed=17
    )

    assert d_hat_horn <= 2, f"Expected d_hat_horn in [0, 2] for noise matrix, got {d_hat_horn}"


def test_parallel_analysis_discriminates() -> None:
    """Euclidean D̂_Horn must strictly exceed noise D̂_Horn (discrimination check)."""
    from experiments.article.analysis.mds import parallel_analysis

    n = 40

    # Structured: rank-3 Euclidean.
    rng_s = np.random.default_rng(13)
    X_3d = rng_s.standard_normal((n, 3))
    D_eucl = _euclidean_distance_matrix(X_3d)
    d_eucl, _, _ = parallel_analysis(D_eucl, n_permutations=100, percentile=95, rng_seed=21)

    # Unstructured: noise.
    rng_n = np.random.default_rng(77)
    A = rng_n.uniform(1.0, 5.0, (n, n))
    D_noise = (A + A.T) / 2.0
    np.fill_diagonal(D_noise, 0.0)
    d_noise, _, _ = parallel_analysis(D_noise, n_permutations=100, percentile=95, rng_seed=31)

    assert d_eucl > d_noise, f"Euclidean D̂_Horn={d_eucl} should exceed noise D̂_Horn={d_noise}"


def test_parallel_analysis_return_shapes() -> None:
    """Return shapes and types are correct."""
    from experiments.article.analysis.mds import parallel_analysis

    rng = np.random.default_rng(55)
    n = 15
    X = rng.standard_normal((n, 2))
    D = _euclidean_distance_matrix(X)

    d_hat, obs_eigs, null_thresh = parallel_analysis(
        D, n_permutations=20, percentile=95, rng_seed=0
    )

    assert isinstance(d_hat, int), f"d_hat_horn must be int, got {type(d_hat)}"
    assert obs_eigs.shape == (n,), f"observed_eigs shape must be ({n},), got {obs_eigs.shape}"
    assert null_thresh.shape == (n,), (
        f"null_threshold_curve shape must be ({n},), got {null_thresh.shape}"
    )
    # Observed eigenvalues should be in descending order.
    assert np.all(obs_eigs[:-1] >= obs_eigs[1:] - 1e-10), "obs_eigs must be in descending order"
    # d_hat_horn must be in [0, n].
    assert 0 <= d_hat <= n, f"d_hat_horn={d_hat} out of valid range [0, {n}]"
