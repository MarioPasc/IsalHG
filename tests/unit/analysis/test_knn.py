"""Unit tests for experiments.article.analysis.knn — A3 kNN classification.

Acceptance criteria (T-M5d):
- loo_fold_indices(n) returns n folds; every (train, test) is disjoint and covers {0..n-1}.
- stratified_fold_indices returns n_folds folds; same seed is reproducible.
- run_knn_cv on a perfect block-diagonal D (ideal separation) returns AUC-OvR = 1.0 for
  any k < min_class_size.
- run_knn_cv result dicts carry keys {k, accuracy, macro_f1, auc_ovr}.
- load_g1_profile parses a geometry table CSV and returns the expected columns.

Pre-fix failure note
--------------------
Before knn.py exists all imports below raise ModuleNotFoundError — that is the
failing baseline from which the implementation makes the tests pass.
"""

from __future__ import annotations

import csv
import io
import tempfile
from pathlib import Path

import numpy as np
import pytest

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers shared across tests
# ---------------------------------------------------------------------------


def _block_diagonal_D(n_classes: int, members_per_class: int) -> np.ndarray:
    """Return a perfect block-diagonal distance matrix.

    Points within the same class have distance 0; points in different classes
    have distance 100.  Any kNN at k < members_per_class should achieve
    perfect separation.
    """
    n = n_classes * members_per_class
    D = np.full((n, n), 100.0)
    np.fill_diagonal(D, 0.0)
    for c in range(n_classes):
        start = c * members_per_class
        end = start + members_per_class
        D[start:end, start:end] = 0.0
    return D


def _block_labels(n_classes: int, members_per_class: int) -> np.ndarray:
    return np.repeat(np.arange(n_classes), members_per_class)


# ---------------------------------------------------------------------------
# Tests for loo_fold_indices
# ---------------------------------------------------------------------------


def test_loo_fold_count() -> None:
    """LOO on n points yields exactly n folds."""
    from experiments.article.analysis.knn import loo_fold_indices

    for n in [5, 10, 20]:
        folds = loo_fold_indices(n)
        assert len(folds) == n, f"Expected {n} folds, got {len(folds)}"


def test_loo_fold_disjoint_and_covers() -> None:
    """Each LOO fold's train + test covers {0..n-1} with no overlap."""
    from experiments.article.analysis.knn import loo_fold_indices

    n = 8
    all_idx = set(range(n))
    for train_idx, test_idx in loo_fold_indices(n):
        assert len(test_idx) == 1, "LOO test set must have exactly 1 point"
        assert len(train_idx) == n - 1, f"LOO train size wrong: {len(train_idx)}"
        assert set(train_idx) | set(test_idx) == all_idx
        assert set(train_idx) & set(test_idx) == set()


def test_loo_fold_each_point_tested_once() -> None:
    """Each point is the test point in exactly one LOO fold."""
    from experiments.article.analysis.knn import loo_fold_indices

    n = 7
    test_counts = np.zeros(n, dtype=int)
    for _, test_idx in loo_fold_indices(n):
        test_counts[test_idx] += 1
    np.testing.assert_array_equal(test_counts, np.ones(n, dtype=int))


# ---------------------------------------------------------------------------
# Tests for stratified_fold_indices
# ---------------------------------------------------------------------------


def test_stratified_fold_count() -> None:
    """stratified_fold_indices returns exactly n_folds folds."""
    from experiments.article.analysis.knn import stratified_fold_indices

    labels = np.repeat(np.arange(3), 10)
    for n_folds in [3, 5]:
        folds = stratified_fold_indices(labels, n_folds=n_folds, rng_seed=42)
        assert len(folds) == n_folds, f"Expected {n_folds} folds, got {len(folds)}"


def test_stratified_fold_disjoint_and_covers() -> None:
    """Stratified folds cover all indices exactly once."""
    from experiments.article.analysis.knn import stratified_fold_indices

    n = 30
    labels = np.repeat(np.arange(5), 6)  # 5 classes × 6 members
    folds = stratified_fold_indices(labels, n_folds=5, rng_seed=0)
    test_counts = np.zeros(n, dtype=int)
    for train_idx, test_idx in folds:
        test_counts[test_idx] += 1
        assert len(set(train_idx) & set(test_idx)) == 0
    np.testing.assert_array_equal(test_counts, np.ones(n, dtype=int))


def test_stratified_fold_reproducible() -> None:
    """Same rng_seed produces identical fold assignments."""
    from experiments.article.analysis.knn import stratified_fold_indices

    labels = np.repeat(np.arange(3), 10)
    folds_a = stratified_fold_indices(labels, n_folds=3, rng_seed=7)
    folds_b = stratified_fold_indices(labels, n_folds=3, rng_seed=7)
    for (tr_a, te_a), (tr_b, te_b) in zip(folds_a, folds_b, strict=True):
        np.testing.assert_array_equal(tr_a, tr_b)
        np.testing.assert_array_equal(te_a, te_b)


# ---------------------------------------------------------------------------
# Tests for run_knn_cv
# ---------------------------------------------------------------------------


def test_run_knn_cv_result_keys() -> None:
    """run_knn_cv returns list of dicts with required keys."""
    from experiments.article.analysis.knn import loo_fold_indices, run_knn_cv

    n_classes, mpc = 3, 6
    D = _block_diagonal_D(n_classes, mpc)
    labels = _block_labels(n_classes, mpc)
    folds = loo_fold_indices(len(labels))
    k_values = [1, 3]

    results = run_knn_cv(D, labels, k_values=k_values, fold_indices=folds, n_classes=n_classes)
    assert len(results) == len(k_values)
    required_keys = {"k", "accuracy", "macro_f1", "auc_ovr"}
    for row in results:
        assert required_keys.issubset(set(row.keys())), f"Missing keys: {set(row.keys())}"


def test_run_knn_cv_perfect_separation_auc() -> None:
    """Perfect block-diagonal D + LOO → AUC-OvR = 1.0 for k < class size."""
    from experiments.article.analysis.knn import loo_fold_indices, run_knn_cv

    n_classes, mpc = 4, 8  # 32 points, 8 per class
    D = _block_diagonal_D(n_classes, mpc)
    labels = _block_labels(n_classes, mpc)
    folds = loo_fold_indices(len(labels))
    k_values = [1, 3, 5]  # all < mpc=8

    results = run_knn_cv(D, labels, k_values=k_values, fold_indices=folds, n_classes=n_classes)
    for row in results:
        np.testing.assert_allclose(
            row["accuracy"],
            1.0,
            atol=1e-9,
            err_msg=f"accuracy={row['accuracy']} != 1.0 for k={row['k']}",
        )
        np.testing.assert_allclose(
            row["auc_ovr"],
            1.0,
            atol=1e-9,
            err_msg=f"auc_ovr={row['auc_ovr']} != 1.0 for k={row['k']}",
        )
        np.testing.assert_allclose(
            row["macro_f1"],
            1.0,
            atol=1e-9,
            err_msg=f"macro_f1={row['macro_f1']} != 1.0 for k={row['k']}",
        )


def test_run_knn_cv_k_value_in_result() -> None:
    """Each result dict carries the correct k value."""
    from experiments.article.analysis.knn import loo_fold_indices, run_knn_cv

    n_classes, mpc = 2, 5
    D = _block_diagonal_D(n_classes, mpc)
    labels = _block_labels(n_classes, mpc)
    folds = loo_fold_indices(len(labels))
    k_values = [1, 3, 5]

    results = run_knn_cv(D, labels, k_values=k_values, fold_indices=folds, n_classes=n_classes)
    returned_ks = [r["k"] for r in results]
    assert returned_ks == k_values, f"Expected k_values {k_values}, got {returned_ks}"


def test_run_knn_cv_metrics_in_unit_interval() -> None:
    """All metrics (accuracy, macro_f1, auc_ovr) lie in [0, 1]."""
    from experiments.article.analysis.knn import run_knn_cv, stratified_fold_indices

    rng = np.random.default_rng(0)
    n = 40
    n_classes = 4
    D = rng.uniform(0, 10, (n, n))
    D = (D + D.T) / 2
    np.fill_diagonal(D, 0.0)
    labels = np.repeat(np.arange(n_classes), n // n_classes)
    folds = stratified_fold_indices(labels, n_folds=5, rng_seed=0)

    results = run_knn_cv(D, labels, k_values=[1, 3], fold_indices=folds, n_classes=n_classes)
    for row in results:
        assert 0.0 <= row["accuracy"] <= 1.0
        assert 0.0 <= row["macro_f1"] <= 1.0
        assert 0.0 <= row["auc_ovr"] <= 1.0 or np.isnan(row["auc_ovr"])


# ---------------------------------------------------------------------------
# Tests for load_g1_profile
# ---------------------------------------------------------------------------


def _write_minimal_geometry_table(f: io.StringIO) -> None:
    """Write a minimal geometry table CSV for testing."""
    writer = csv.writer(f)
    writer.writerow(
        [
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
            "mardia_p1",
            "mardia_p2",
            "neg_eigenvalue_floor",
        ]
    )
    writer.writerow(
        [
            "planted_main",
            "IsalHG",
            60,
            "False",
            0.12,
            21,
            0.05,
            24.0,
            16.0,
            1.5,
            4.0,
            0.23,
            0.88,
            0.98,
            38,
        ]
    )
    writer.writerow(
        [
            "planted_main",
            "WL-L1",
            60,
            "True",
            0.0,
            40,
            0.24,
            22.0,
            20.0,
            1.1,
            0.0,
            1.78,
            1.0,
            1.0,
            60,
        ]
    )
    writer.writerow(
        [
            "other_corpus",
            "IsalHG",
            20,
            "False",
            0.10,
            8,
            0.08,
            12.0,
            6.0,
            2.0,
            3.0,
            0.03,
            0.90,
            0.98,
            14,
        ]
    )


def test_load_g1_profile_returns_correct_keys() -> None:
    """load_g1_profile returns a dict with the expected representation names."""
    from experiments.article.analysis.knn import load_g1_profile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as fh:
        buf = io.StringIO()
        _write_minimal_geometry_table(buf)
        fh.write(buf.getvalue())
        tmp_path = Path(fh.name)

    try:
        profile = load_g1_profile(tmp_path, corpus_label="planted_main")
        assert "IsalHG" in profile
        assert "WL-L1" in profile
        assert "other_corpus" not in profile  # filtered by corpus_label
    finally:
        tmp_path.unlink(missing_ok=True)


def test_load_g1_profile_values() -> None:
    """load_g1_profile returns the correct diameter_to_median and hubness_skewness values."""
    from experiments.article.analysis.knn import load_g1_profile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as fh:
        buf = io.StringIO()
        _write_minimal_geometry_table(buf)
        fh.write(buf.getvalue())
        tmp_path = Path(fh.name)

    try:
        profile = load_g1_profile(tmp_path, corpus_label="planted_main")
        np.testing.assert_allclose(profile["IsalHG"]["diameter_to_median"], 1.5)
        np.testing.assert_allclose(profile["IsalHG"]["hubness_skewness"], 0.23)
        np.testing.assert_allclose(profile["WL-L1"]["hubness_skewness"], 1.78)
    finally:
        tmp_path.unlink(missing_ok=True)


def test_load_g1_profile_corpus_filter() -> None:
    """load_g1_profile only returns rows matching corpus_label."""
    from experiments.article.analysis.knn import load_g1_profile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as fh:
        buf = io.StringIO()
        _write_minimal_geometry_table(buf)
        fh.write(buf.getvalue())
        tmp_path = Path(fh.name)

    try:
        profile = load_g1_profile(tmp_path, corpus_label="other_corpus")
        assert set(profile.keys()) == {"IsalHG"}
        assert "WL-L1" not in profile
    finally:
        tmp_path.unlink(missing_ok=True)
