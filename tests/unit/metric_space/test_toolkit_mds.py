"""Unit tests for metric MDS.

The decisive case is a matrix that is exactly realisable in the target
dimension: the Euclidean distances of random 2-D points embedded back into 2-D
must reach stress-1 near zero. If the stress definition or the coordinate
orientation were wrong, this is where it shows.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.spatial.distance import pdist, squareform

from isalhg.errors import MetricSpaceError
from isalhg.metric_space.toolkit import metric_mds

pytestmark = pytest.mark.unit


class TestMetricMds:
    def test_euclidean_2d_matrix_embeds_with_near_zero_stress(self) -> None:
        rng = np.random.default_rng(0)
        points = rng.normal(size=(40, 2))
        D = squareform(pdist(points))

        coordinates, stress = metric_mds(D, dim=2, seed=0)
        assert coordinates.shape == (40, 2)
        assert 0.0 <= stress <= 1.0
        assert stress < 0.01

    def test_stress_lies_in_the_unit_interval_on_a_non_euclidean_matrix(self) -> None:
        star = np.array(
            [
                [0.0, 1.0, 1.0, 1.0],
                [1.0, 0.0, 2.0, 2.0],
                [1.0, 2.0, 0.0, 2.0],
                [1.0, 2.0, 2.0, 0.0],
            ]
        )
        _, stress = metric_mds(star, dim=2, seed=0)
        assert 0.0 <= stress <= 1.0

    def test_stress_does_not_increase_with_dimension(self) -> None:
        rng = np.random.default_rng(1)
        points = rng.normal(size=(30, 4))
        D = squareform(pdist(points))
        _, stress_2d = metric_mds(D, dim=2, seed=0)
        _, stress_4d = metric_mds(D, dim=4, seed=0)
        assert stress_4d <= stress_2d + 1e-6

    def test_is_deterministic_under_the_seed(self) -> None:
        rng = np.random.default_rng(2)
        D = squareform(pdist(rng.normal(size=(20, 3))))
        first, first_stress = metric_mds(D, dim=2, seed=7)
        second, second_stress = metric_mds(D, dim=2, seed=7)
        np.testing.assert_allclose(first, second)
        assert first_stress == pytest.approx(second_stress)

    @pytest.mark.parametrize(
        ("D", "dim", "message"),
        [
            (np.zeros((2, 3)), 2, "square"),
            (np.zeros((1, 1)), 2, "at least two"),
            (np.zeros((4, 4)), 0, "dim must be"),
        ],
    )
    def test_invalid_input_raises(self, D: np.ndarray, dim: int, message: str) -> None:
        with pytest.raises(MetricSpaceError, match=message):
            metric_mds(D, dim=dim, seed=0)
