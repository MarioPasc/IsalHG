"""Unit tests for the geometric licences: non-Euclidean mass and hubness.

``non_euclidean_mass`` must read exactly 0 on a matrix that *is* Euclidean and
strictly positive on one that provably is not. The negative case uses the
4-point star (tree) metric, the textbook Schoenberg counterexample: three leaves
at distance 1 from a centre are pairwise at distance 2, and no embedding into a
Euclidean space realises that (three points at mutual distance 2 sit on a
circle of radius 2/sqrt(3) > 1, so the centre cannot be at distance 1 from all
three).

``hubness`` is checked against a hand-computed skewness on a matrix whose
k-occurrence vector is known by inspection.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.stats import skew

from isalhg.errors import MetricSpaceError
from isalhg.metric_space.toolkit import hubness, non_euclidean_mass

pytestmark = pytest.mark.unit


def euclidean_matrix(points: np.ndarray) -> np.ndarray:
    diff = points[:, None, :] - points[None, :, :]
    D = np.sqrt((diff**2).sum(axis=-1))
    np.fill_diagonal(D, 0.0)
    return D


STAR_METRIC = np.array(
    [
        [0.0, 1.0, 1.0, 1.0],
        [1.0, 0.0, 2.0, 2.0],
        [1.0, 2.0, 0.0, 2.0],
        [1.0, 2.0, 2.0, 0.0],
    ]
)


class TestNonEuclideanMass:
    @pytest.mark.parametrize("dim", [1, 2, 3, 5])
    def test_zero_on_euclidean_matrices(self, dim: int) -> None:
        rng = np.random.default_rng(dim)
        D = euclidean_matrix(rng.normal(size=(30, dim)))
        nu, eigenvalues = non_euclidean_mass(D)
        assert nu == pytest.approx(0.0, abs=1e-9)
        assert eigenvalues.shape == (30,)
        assert np.all(np.diff(eigenvalues) <= 1e-9)

    def test_positive_on_the_four_point_star_metric(self) -> None:
        nu, eigenvalues = non_euclidean_mass(STAR_METRIC)
        assert nu > 0.0
        assert (eigenvalues < -1e-9).any()

    def test_empty_matrix(self) -> None:
        nu, eigenvalues = non_euclidean_mass(np.zeros((0, 0)))
        assert nu == 0.0
        assert eigenvalues.shape == (0,)

    def test_non_square_raises(self) -> None:
        with pytest.raises(MetricSpaceError, match="square"):
            non_euclidean_mass(np.zeros((2, 3)))


class TestHubness:
    def test_reproduces_a_hand_computed_skewness(self) -> None:
        # Five points on a line at 0, 1, 2, 10, 11 with k = 1. Nearest
        # neighbours: 0->1, 1->0 (tie with 2, broken by index), 2->1, 10->11,
        # 11->10.  N_1 = [1, 2, 0, 1, 1].
        positions = np.array([[0.0], [1.0], [2.0], [10.0], [11.0]])
        D = euclidean_matrix(positions)
        expected_counts = np.array([1, 2, 0, 1, 1])
        expected_skew = float(skew(expected_counts, bias=True))

        skewness, max_occurrence = hubness(D, k=1)
        assert skewness == pytest.approx(expected_skew)
        assert max_occurrence == 2

    def test_uniform_occurrence_gives_zero_skewness(self) -> None:
        # A regular simplex: every point is every other point's neighbour, so
        # N_k is constant and the skewness of a constant vector is defined as 0.
        D = np.ones((6, 6))
        np.fill_diagonal(D, 0.0)
        skewness, max_occurrence = hubness(D, k=5)
        assert skewness == pytest.approx(0.0)
        assert max_occurrence == 5

    def test_counts_sum_to_n_times_k(self) -> None:
        rng = np.random.default_rng(2)
        D = euclidean_matrix(rng.normal(size=(40, 3)))
        _, max_occurrence = hubness(D, k=10)
        assert 10 <= max_occurrence <= 39

    @pytest.mark.parametrize("k", [0, 10])
    def test_k_out_of_range_raises(self, k: int) -> None:
        D = np.zeros((10, 10))
        with pytest.raises(MetricSpaceError, match="k must satisfy"):
            hubness(D, k=k)
