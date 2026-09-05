"""Unit tests for the anomaly scores and AUROC.

The two things that silently ruin a screening experiment are a score that
includes the item's own zero self-distance (deflating every score by a factor
``k/(k+1)``) and a score whose sign is inverted (turning an AUC of 0.95 into
0.05). Both are pinned here on inputs where the right answer is arithmetic.
"""

from __future__ import annotations

import numpy as np
import pytest

from isalhg.errors import MetricSpaceError
from isalhg.metric_space.toolkit import auroc, knn_score, lof_score

pytestmark = pytest.mark.unit


def line_matrix(positions: list[float]) -> np.ndarray:
    points = np.asarray(positions, dtype=float)[:, None]
    D = np.abs(points - points.T)
    np.fill_diagonal(D, 0.0)
    return D


class TestKnnScore:
    def test_excludes_self_and_matches_hand_computation(self) -> None:
        # Points at 0, 1, 2, 3.  With k = 2 the two nearest *others* of point 0
        # are 1 and 2 -> mean 1.5; of point 1 they are 0 and 2 -> mean 1.0.
        D = line_matrix([0.0, 1.0, 2.0, 3.0])
        scores = knn_score(D, k=2)
        np.testing.assert_allclose(scores, [1.5, 1.0, 1.0, 1.5])

    def test_isolated_point_scores_highest(self) -> None:
        D = line_matrix([0.0, 0.5, 1.0, 40.0])
        scores = knn_score(D, k=2)
        assert int(np.argmax(scores)) == 3

    @pytest.mark.parametrize("k", [0, 4])
    def test_k_out_of_range_raises(self, k: int) -> None:
        with pytest.raises(MetricSpaceError, match="k must satisfy"):
            knn_score(np.zeros((4, 4)), k=k)


class TestLofScore:
    def test_higher_is_more_anomalous(self) -> None:
        rng = np.random.default_rng(0)
        inliers = rng.normal(scale=0.3, size=(30, 2))
        points = np.vstack([inliers, np.array([[25.0, 25.0]])])
        diff = points[:, None, :] - points[None, :, :]
        D = np.sqrt((diff**2).sum(axis=-1))
        np.fill_diagonal(D, 0.0)

        scores = lof_score(D, k=10)
        assert scores.shape == (31,)
        assert int(np.argmax(scores)) == 30
        assert scores[30] > scores[:30].max()

    def test_k_out_of_range_raises(self) -> None:
        with pytest.raises(MetricSpaceError, match="k must satisfy"):
            lof_score(np.zeros((5, 5)), k=5)


class TestAuroc:
    def test_perfectly_separable_scores_give_one(self) -> None:
        scores = np.array([0.1, 0.2, 0.3, 0.9, 1.0])
        truth = np.array([False, False, False, True, True])
        assert auroc(scores, truth) == pytest.approx(1.0)

    def test_inverted_scores_give_zero(self) -> None:
        scores = np.array([1.0, 0.9, 0.3, 0.2, 0.1])
        truth = np.array([False, False, False, True, True])
        assert auroc(scores, truth) == pytest.approx(0.0)

    def test_constant_scores_give_chance(self) -> None:
        scores = np.ones(6)
        truth = np.array([True, True, True, False, False, False])
        assert auroc(scores, truth) == pytest.approx(0.5)

    def test_single_class_raises(self) -> None:
        with pytest.raises(MetricSpaceError, match="both classes"):
            auroc(np.array([1.0, 2.0]), np.array([True, True]))

    def test_shape_mismatch_raises(self) -> None:
        with pytest.raises(MetricSpaceError, match="shape"):
            auroc(np.array([1.0, 2.0]), np.array([True, False, True]))
