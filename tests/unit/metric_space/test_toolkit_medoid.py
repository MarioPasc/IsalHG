"""Unit tests for the certified medoid.

The load-bearing assertion is Prop 3: in any metric, the medoid's cost is within
``2 - 2/N`` of the pairwise lower bound. The test builds 200 genuine metric
matrices (Euclidean distances of random points) and checks that both the bound
and ``LB <= cost`` hold on every one of them.

The mirror-image measurement -- how often ``LB > cost`` on matrices that are
*not* metrics -- is RQ2's certificate-validity probe, so it is measured here
rather than asserted, and the rate is printed with the test.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from isalhg.errors import MetricSpaceError
from isalhg.metric_space.toolkit import MedoidResult, medoid

pytestmark = pytest.mark.unit


def euclidean_matrix(rng: np.random.Generator, n: int, dim: int) -> np.ndarray:
    points = rng.normal(size=(n, dim))
    diff = points[:, None, :] - points[None, :, :]
    D = np.sqrt((diff**2).sum(axis=-1))
    np.fill_diagonal(D, 0.0)
    return D


def random_nonmetric_matrix(rng: np.random.Generator, n: int) -> np.ndarray:
    """Symmetric non-negative matrix with a zero diagonal and no triangle law."""
    upper = rng.random((n, n))
    D = np.triu(upper, k=1)
    D = D + D.T
    np.fill_diagonal(D, 0.0)
    return D


class TestMedoidOnMetrics:
    def test_lower_bound_and_ratio_hold_on_200_metric_matrices(self) -> None:
        rng = np.random.default_rng(20260905)
        violations_lb = 0
        violations_ratio = 0
        max_ratio = 0.0
        for _ in range(200):
            n = int(rng.integers(3, 25))
            D = euclidean_matrix(rng, n, dim=int(rng.integers(1, 6)))
            result = medoid(D)
            bound = 2.0 - 2.0 / n
            if result.lower_bound > result.cost + 1e-9:
                violations_lb += 1
            if result.ratio > bound + 1e-9:
                violations_ratio += 1
            max_ratio = max(max_ratio, result.ratio)
        assert violations_lb == 0
        assert violations_ratio == 0
        assert max_ratio <= 2.0

    def test_index_is_the_argmin_of_the_row_sums(self) -> None:
        rng = np.random.default_rng(7)
        D = euclidean_matrix(rng, 12, 3)
        result = medoid(D)
        assert result.index == int(np.argmin(D.sum(axis=1)))
        assert result.cost == pytest.approx(float(D[result.index].sum()))

    def test_lower_bound_matches_the_definition(self) -> None:
        rng = np.random.default_rng(11)
        n = 9
        D = euclidean_matrix(rng, n, 2)
        expected = float(np.triu(D, k=1).sum()) / (n - 1)
        assert medoid(D).lower_bound == pytest.approx(expected)


class TestMedoidDegenerateCases:
    def test_single_item(self) -> None:
        assert medoid(np.zeros((1, 1))) == MedoidResult(0, 0.0, 0.0, 1.0)

    def test_all_zero_matrix_gives_ratio_one(self) -> None:
        assert medoid(np.zeros((5, 5))).ratio == 1.0

    def test_zero_lower_bound_always_implies_zero_cost(self) -> None:
        # The contract specifies ratio = inf when LB == 0 < cost. That branch is
        # defensive, not reachable: LB == 0 forces the strict upper triangle to
        # vanish, and then row 0 -- whose off-diagonal entries are all in that
        # triangle -- has cost 0, so the argmin cost is 0 too. Pinning the
        # implication keeps a future edit from silently making it reachable.
        rng = np.random.default_rng(3)
        for _ in range(50):
            n = int(rng.integers(2, 8))
            D = np.zeros((n, n))
            D[np.tril_indices(n, k=-1)] = rng.random(n * (n - 1) // 2) * 5.0
            result = medoid(D)
            assert result.lower_bound == 0.0
            assert result.cost == 0.0
            assert result.ratio == 1.0
            assert not math.isinf(result.ratio)

    def test_empty_matrix_raises(self) -> None:
        with pytest.raises(MetricSpaceError, match="empty collection"):
            medoid(np.zeros((0, 0)))

    def test_non_square_raises(self) -> None:
        with pytest.raises(MetricSpaceError, match="square"):
            medoid(np.zeros((3, 4)))


class TestCertificateValidityProbe:
    """RQ2's probe: how often does the certificate lie under a non-metric?"""

    def test_measure_lb_above_cost_rate_on_non_metric_matrices(self) -> None:
        rng = np.random.default_rng(20260905)
        trials = 200
        invalid = 0
        for _ in range(trials):
            n = int(rng.integers(3, 25))
            result = medoid(random_nonmetric_matrix(rng, n))
            if result.lower_bound > result.cost + 1e-12:
                invalid += 1
        rate = invalid / trials
        print(f"\nLB > cost on random non-metric matrices: {invalid}/{trials} = {rate:.3f}")
        assert 0.0 <= rate <= 1.0
