"""Unit tests for PAM, the average-linkage hierarchy and the per-class table.

Three well-separated Gaussian blobs give a partition every correct clustering
recovers, so the tests can assert exact ARI = 1 rather than a threshold.
"""

from __future__ import annotations

import numpy as np
import pytest

from isalhg.errors import MetricSpaceError
from isalhg.metric_space.toolkit import (
    ari,
    average_linkage,
    cut,
    nmi,
    pam,
    per_class_table,
)
from isalhg.metric_space.toolkit.clustering import _pam_numpy

pytestmark = pytest.mark.unit


def blobs(seed: int = 0, per_blob: int = 12) -> tuple[np.ndarray, list[int]]:
    """Three well-separated blobs; returns (distance matrix, true labels)."""
    rng = np.random.default_rng(seed)
    centres = np.array([[0.0, 0.0], [30.0, 0.0], [0.0, 30.0]])
    points = np.vstack([centre + rng.normal(scale=0.5, size=(per_blob, 2)) for centre in centres])
    diff = points[:, None, :] - points[None, :, :]
    D = np.sqrt((diff**2).sum(axis=-1))
    np.fill_diagonal(D, 0.0)
    labels = [i for i in range(3) for _ in range(per_blob)]
    return D, labels


class TestPam:
    def test_returns_k_clusters_and_recovers_the_blobs(self) -> None:
        D, truth = blobs()
        labels = pam(D, k=3, seed=0)
        assert labels.shape == (D.shape[0],)
        assert len(set(labels.tolist())) == 3
        assert set(labels.tolist()) <= {0, 1, 2}
        assert ari(truth, labels.tolist()) == pytest.approx(1.0)
        assert nmi(truth, labels.tolist()) == pytest.approx(1.0)

    def test_is_deterministic_under_the_seed(self) -> None:
        D, _ = blobs(seed=5)
        first = pam(D, k=3, seed=42)
        second = pam(D, k=3, seed=42)
        np.testing.assert_array_equal(first, second)

    @pytest.mark.parametrize("k", [0, 37])
    def test_k_out_of_range_raises(self, k: int) -> None:
        D, _ = blobs()
        with pytest.raises(MetricSpaceError, match="k must satisfy"):
            pam(D, k=k, seed=0)

    def test_numpy_fallback_agrees_with_fasterpam_on_the_blobs(self) -> None:
        D, truth = blobs(seed=3)
        fallback = _pam_numpy(D.astype(np.float64), 3, 0)
        assert ari(truth, fallback.tolist()) == pytest.approx(1.0)


class TestAverageLinkage:
    def test_cophenetic_correlation_is_a_correlation(self) -> None:
        D, _ = blobs()
        linkage_matrix, cophenetic = average_linkage(D)
        assert linkage_matrix.shape == (D.shape[0] - 1, 4)
        assert -1.0 <= cophenetic <= 1.0
        assert cophenetic > 0.9

    def test_cut_recovers_the_blobs_and_is_zero_based(self) -> None:
        D, truth = blobs()
        linkage_matrix, _ = average_linkage(D)
        labels = cut(linkage_matrix, 3)
        assert labels.min() == 0
        assert len(set(labels.tolist())) == 3
        assert ari(truth, labels.tolist()) == pytest.approx(1.0)

    def test_single_item_raises(self) -> None:
        with pytest.raises(MetricSpaceError, match="at least two"):
            average_linkage(np.zeros((1, 1)))


class TestPerClassTable:
    def test_perfect_clustering_gives_recall_and_precision_one(self) -> None:
        truth = ["a", "a", "b", "b", "c", "c"]
        predicted = [2, 2, 0, 0, 1, 1]
        rows = per_class_table(truth, predicted)
        assert [row["class"] for row in rows] == ["a", "b", "c"]
        for row in rows:
            assert row["support"] == 2
            assert row["recall"] == pytest.approx(1.0)
            assert row["precision"] == pytest.approx(1.0)

    def test_partial_recovery(self) -> None:
        truth = ["a", "a", "a", "b"]
        predicted = [0, 0, 1, 1]
        rows = {row["class"]: row for row in per_class_table(truth, predicted)}
        assert rows["a"]["support"] == 3
        assert rows["a"]["recall"] == pytest.approx(2 / 3)
        assert rows["a"]["precision"] == pytest.approx(1.0)
        assert rows["b"]["recall"] == pytest.approx(1.0)
        assert rows["b"]["precision"] == pytest.approx(0.5)

    def test_more_classes_than_clusters_leaves_one_unmatched(self) -> None:
        truth = ["a", "b", "c"]
        predicted = [0, 0, 0]
        rows = per_class_table(truth, predicted)
        matched = [row for row in rows if row["cluster"] is not None]
        unmatched = [row for row in rows if row["cluster"] is None]
        assert len(matched) == 1
        assert len(unmatched) == 2
        assert all(row["recall"] == 0.0 and row["precision"] == 0.0 for row in unmatched)

    def test_empty_input(self) -> None:
        assert per_class_table([], []) == []

    def test_length_mismatch_raises(self) -> None:
        with pytest.raises(MetricSpaceError, match="entries"):
            per_class_table(["a", "b"], [0])
