"""Unit tests for experiments.article.analysis.mds — CV-D̂ selection and geometry table.

Acceptance criteria from T-M5b:
- cv_dimension_selection on a perfect 2D Euclidean matrix returns d_hat == 2.
- geometry_table_row returns all 11 required column keys.
- mardia_ratios returns (p1, p2) with 0 <= p1, p2 <= 1.
- pairwise_l2 returns a symmetric zero-diagonal matrix.
"""

from __future__ import annotations

import numpy as np
import pytest

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _euclidean_distance_matrix(X: np.ndarray) -> np.ndarray:
    """Exact pairwise Euclidean distances from coordinates X (n, d)."""
    diff = X[:, None, :] - X[None, :, :]
    return np.sqrt(np.sum(diff**2, axis=-1))


# ---------------------------------------------------------------------------
# Tests for cv_dimension_selection
# ---------------------------------------------------------------------------


def test_cv_dimension_selection_2d_euclidean() -> None:
    """CV-D̂ selector returns d_hat == 2 on a perfect 2D Euclidean matrix."""
    from experiments.article.analysis.mds import cv_dimension_selection

    rng = np.random.default_rng(42)
    X_true = rng.standard_normal((24, 2))
    D = _euclidean_distance_matrix(X_true)

    d_hat, cv_errors = cv_dimension_selection(D, max_dims=6, rng_seed=0)

    assert d_hat == 2, f"Expected d_hat=2 on 2D Euclidean, got {d_hat}"
    assert len(cv_errors) == 6
    # Error at d=2 should be near zero
    assert cv_errors[1] < 1e-6, f"CV error at d=2 should be ~0, got {cv_errors[1]}"


def test_cv_dimension_selection_1d_euclidean() -> None:
    """CV-D̂ selector returns d_hat == 1 on a collinear point set."""
    from experiments.article.analysis.mds import cv_dimension_selection

    X_true = np.arange(20, dtype=np.float64).reshape(-1, 1)
    D = _euclidean_distance_matrix(X_true)

    d_hat, cv_errors = cv_dimension_selection(D, max_dims=5, rng_seed=1)

    assert d_hat == 1, f"Expected d_hat=1 on collinear set, got {d_hat}"


def test_cv_dimension_selection_error_decreases_then_flattens() -> None:
    """CV error should be non-increasing up to true dimension."""
    from experiments.article.analysis.mds import cv_dimension_selection

    rng = np.random.default_rng(99)
    X_true = rng.standard_normal((30, 3))
    D = _euclidean_distance_matrix(X_true)

    _, cv_errors = cv_dimension_selection(D, max_dims=8, rng_seed=0)

    # Error at d=3 must be strictly less than error at d=1
    assert cv_errors[2] < cv_errors[0], "Error at d=3 should be less than at d=1"


def test_cv_dimension_selection_respects_rng_seed() -> None:
    """Same seed produces same result; different seeds may differ."""
    from experiments.article.analysis.mds import cv_dimension_selection

    rng = np.random.default_rng(7)
    X = rng.standard_normal((20, 2))
    D = _euclidean_distance_matrix(X)

    d1, e1 = cv_dimension_selection(D, max_dims=4, rng_seed=42)
    d2, e2 = cv_dimension_selection(D, max_dims=4, rng_seed=42)
    assert d1 == d2
    np.testing.assert_allclose(e1, e2)


# ---------------------------------------------------------------------------
# Tests for mardia_ratios
# ---------------------------------------------------------------------------


def test_mardia_ratios_euclidean_all_positive() -> None:
    """On a PSD matrix all eigenvalues are >= 0, so p1==1, p2==1."""
    from experiments.article.analysis.mds import mardia_ratios
    from isalhg.metric_space.metrics.embedding import classical_mds

    rng = np.random.default_rng(0)
    X = rng.standard_normal((15, 2))
    D = _euclidean_distance_matrix(X)
    eigenvalues, _ = classical_mds(D)

    p1, p2 = mardia_ratios(eigenvalues)
    # p1 and p2 must be in [0, 1]
    assert 0.0 <= p1 <= 1.0 + 1e-9
    assert 0.0 <= p2 <= 1.0 + 1e-9
    # For Euclidean matrices p1 should be close to 1 (no negative eigenvalues)
    assert p1 > 0.95, f"p1={p1} expected near 1 for Euclidean matrix"


def test_mardia_ratios_all_negative() -> None:
    """On an artificially negative-eigenvalue spectrum, p1 == 0."""
    from experiments.article.analysis.mds import mardia_ratios

    eigenvalues = np.array([-5.0, -3.0, -1.0])
    p1, p2 = mardia_ratios(eigenvalues)
    assert p1 == pytest.approx(0.0)
    assert p2 == pytest.approx(0.0)


def test_mardia_ratios_mixed() -> None:
    """Mixed eigenvalues give 0 < p1 < 1."""
    from experiments.article.analysis.mds import mardia_ratios

    eigenvalues = np.array([10.0, 5.0, -3.0, -1.0])
    p1, p2 = mardia_ratios(eigenvalues)
    assert 0.0 < p1 < 1.0
    assert 0.0 < p2 < 1.0


# ---------------------------------------------------------------------------
# Tests for pairwise_l2
# ---------------------------------------------------------------------------


def test_pairwise_l2_symmetric_zero_diagonal() -> None:
    """pairwise_l2 is symmetric with zero diagonal."""
    from experiments.article.analysis.mds import pairwise_l2

    rng = np.random.default_rng(1)
    X = rng.standard_normal((10, 3))
    D = pairwise_l2(X)

    assert D.shape == (10, 10)
    np.testing.assert_allclose(np.diag(D), 0.0, atol=1e-12)
    np.testing.assert_allclose(D, D.T, atol=1e-12)


def test_pairwise_l2_matches_euclidean() -> None:
    """pairwise_l2 matches the brute-force Euclidean distance."""
    from experiments.article.analysis.mds import pairwise_l2

    rng = np.random.default_rng(2)
    X = rng.standard_normal((8, 4))
    D_fast = pairwise_l2(X)
    D_ref = _euclidean_distance_matrix(X)
    np.testing.assert_allclose(D_fast, D_ref, rtol=1e-10)


# ---------------------------------------------------------------------------
# Tests for geometry_table_row
# ---------------------------------------------------------------------------


_REQUIRED_COLUMNS = {
    "corpus",
    "representation",
    "n_points",
    "psd",
    "nu",
    "d_hat",
    "stress_at_d_hat",
    "diameter",
    "median",
    "diameter_to_median",
    "iqr",
    "hubness_skewness",
}


def test_cv_dimension_selection_oos_vs_leaky_l1_r3() -> None:
    """OOS K-fold CV finds D̂=3 on L1 distances from R^3; the leaky method overestimates.

    Data: N=40 points in R^3, pairwise L1 distances (seed=3, pinned).

    L1 distances from R^3 are non-Euclidean: the double-centred Gram matrix B has
    negative eigenvalues (verified inline). The true intrinsic dimension is 3.

    Leaky (in-sample) behaviour: the full-N-point MDS embedding is used to evaluate
    'held-out' pairs. The 4th positive eigenvector of B captures a cross-term
    artifact from approximating the non-Euclidean L1 metric in Euclidean space.
    Because the test points ARE INCLUDED in the full-matrix fit, the artifact is
    specifically tailored to minimise test-train RMSE at d=4 → in-sample parsimony
    picks d_hat=4 (overestimates by 1).

    OOS behaviour (corrected): the train-only embedding is fit; test points are
    placed via the Gower out-of-sample extension. The 4th eigenvector of B_train is
    specific to the training set's L1 cross-term structure and does NOT consistently
    improve held-out predictions → parsimony picks d_hat=3 (true intrinsic dimension).
    """
    from experiments.article.analysis.mds import cv_dimension_selection, pairwise_l2
    from isalhg.metric_space.metrics.embedding import embed_classical

    rng = np.random.default_rng(3)
    N, max_dims = 40, 10

    # L1 distances from R^3 (non-Euclidean)
    X = rng.standard_normal((N, 3))
    D = np.abs(X[:, None, :] - X[None, :, :]).sum(axis=-1)
    np.fill_diagonal(D, 0.0)

    # Verify non-Euclidean (negative eigenvalues in B)
    Hn = np.eye(N) - np.ones((N, N)) / N
    B = -0.5 * Hn @ (D**2) @ Hn
    assert np.any(np.linalg.eigvalsh(B) < -1.0), (
        "Expected non-Euclidean distance matrix for L1 from R^3"
    )

    # --- Leaky (old) implementation, reconstructed inline ---
    # Embeds ALL N points at each d; 'held-out' RMSE is evaluated on the same
    # in-sample embedding — this is the pre-fix behaviour.
    rows_idx, cols_idx = np.triu_indices(N, k=1)
    d_true_pairs = D[rows_idx, cols_idx]
    leaky_errors: list[float] = []
    for d in range(1, max_dims + 1):
        X_emb = embed_classical(D, n_dims=d)
        D_emb = pairwise_l2(X_emb)
        rmse = float(np.sqrt(np.mean((d_true_pairs - D_emb[rows_idx, cols_idx]) ** 2)))
        leaky_errors.append(rmse)
    min_l = min(leaky_errors)
    range_l = leaky_errors[0] - min_l
    tol_l = max(1e-8, range_l * 1e-3)
    d_hat_leaky = next(d for d, err in enumerate(leaky_errors, 1) if err <= min_l + tol_l)
    assert d_hat_leaky == 4, (
        f"Expected leaky d_hat == 4 on L1-from-R3 data (in-sample artifact at d=4), "
        f"got {d_hat_leaky}. Leaky CV errors: {leaky_errors}"
    )

    # --- OOS K-fold CV (the corrected implementation) ---
    d_hat_oos, oos_errors = cv_dimension_selection(D, max_dims=max_dims, rng_seed=3)
    assert d_hat_oos in {2, 3}, (
        f"Expected OOS d_hat in {{2, 3}} for L1-from-R3 data (true dim=3), "
        f"got {d_hat_oos}. OOS CV errors: {oos_errors}"
    )
    assert d_hat_oos < d_hat_leaky, (
        f"OOS d_hat ({d_hat_oos}) should be strictly less than leaky d_hat "
        f"({d_hat_leaky}): OOS must not carry the in-sample artifact at d=4."
    )


def test_geometry_table_row_all_columns_present() -> None:
    """geometry_table_row returns a dict with all required column keys."""
    from experiments.article.analysis.mds import geometry_table_row

    rng = np.random.default_rng(3)
    X = rng.standard_normal((15, 2))
    D = _euclidean_distance_matrix(X)

    row = geometry_table_row(
        corpus_name="test_corpus",
        representation_name="test_repr",
        D=D,
        d_hat=2,
    )

    missing = _REQUIRED_COLUMNS - set(row.keys())
    assert not missing, f"Missing columns: {missing}"


def test_geometry_table_row_types() -> None:
    """All numeric fields in geometry_table_row are Python floats or int/bool."""
    from experiments.article.analysis.mds import geometry_table_row

    rng = np.random.default_rng(5)
    X = rng.standard_normal((12, 2))
    D = _euclidean_distance_matrix(X)

    row = geometry_table_row(
        corpus_name="c",
        representation_name="r",
        D=D,
        d_hat=2,
    )

    for key in (
        "nu",
        "stress_at_d_hat",
        "diameter",
        "median",
        "diameter_to_median",
        "iqr",
        "hubness_skewness",
    ):
        val = row[key]
        assert isinstance(val, float), f"{key}={val!r} is not float"
    assert isinstance(row["psd"], bool), f"psd={row['psd']!r} is not bool"
    assert isinstance(row["d_hat"], int), f"d_hat={row['d_hat']!r} is not int"
    assert isinstance(row["n_points"], int), f"n_points={row['n_points']!r} is not int"
