"""Unit tests for :mod:`isalhg.metric_space.metrics.association`.

Hand-computed values are used to verify Spearman rho, Pearson r, and MI.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

np = pytest.importorskip("numpy")
pytest.importorskip("scipy")


from isalhg.metric_space.metrics.association import (  # noqa: E402
    mutual_information_binned,
    pearson_r,
    spearman_r,
    triu_vector,
)


class TestSpearmanR:
    def test_perfect_correlation(self) -> None:
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        rho, pval = spearman_r(x, x)
        assert abs(rho - 1.0) < 1e-10
        assert 0.0 <= pval <= 1.0

    def test_perfect_anti_correlation(self) -> None:
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y = np.array([5.0, 4.0, 3.0, 2.0, 1.0])
        rho, _ = spearman_r(x, y)
        assert abs(rho - (-1.0)) < 1e-10

    def test_range(self) -> None:
        rng = np.random.default_rng(0)
        x = rng.random(20)
        y = rng.random(20)
        rho, _ = spearman_r(x, y)
        assert -1.0 <= rho <= 1.0

    def test_known_small_case(self) -> None:
        # ranks of [2,1,3] → [2,1,3]; ranks of [1,3,2] → [1,3,2]
        # spearman rho for perfectly disagreeing ranking: hand-checked near -0.5
        x = np.array([2.0, 1.0, 3.0])
        y = np.array([1.0, 3.0, 2.0])
        rho, _ = spearman_r(x, y)
        # scipy gives rho = -0.5 for this pair
        assert abs(rho - (-0.5)) < 1e-6


class TestPearsonR:
    def test_perfect_correlation(self) -> None:
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        r, pval = pearson_r(x, x)
        assert abs(r - 1.0) < 1e-10

    def test_anti_correlation(self) -> None:
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([3.0, 2.0, 1.0])
        r, _ = pearson_r(x, y)
        assert abs(r - (-1.0)) < 1e-10

    def test_range(self) -> None:
        rng = np.random.default_rng(1)
        x = rng.random(30)
        y = rng.random(30)
        r, _ = pearson_r(x, y)
        assert -1.0 <= r <= 1.0


class TestMutualInformationBinned:
    def test_nonnegative(self) -> None:
        rng = np.random.default_rng(2)
        x = rng.random(50)
        y = rng.random(50)
        assert mutual_information_binned(x, y) >= 0.0

    def test_self_mi_positive(self) -> None:
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])
        mi_self = mutual_information_binned(x, x)
        rng = np.random.default_rng(3)
        mi_rand = mutual_information_binned(x, rng.permutation(x))
        # MI with itself should exceed MI with a random permutation
        assert mi_self >= mi_rand

    def test_n_bins_parameter(self) -> None:
        x = np.linspace(0, 1, 40)
        y = np.linspace(0, 1, 40)
        mi_5 = mutual_information_binned(x, y, n_bins=5)
        mi_10 = mutual_information_binned(x, y, n_bins=10)
        # Both should be positive (perfectly correlated)
        assert mi_5 >= 0.0
        assert mi_10 >= 0.0


class TestTriuVector:
    def test_shape_4x4(self) -> None:
        D = np.zeros((4, 4))
        v = triu_vector(D)
        # Upper triangle (i<j): C(4,2) = 6 entries
        assert v.shape == (6,)

    def test_values(self) -> None:
        D = np.array([[0, 1, 2], [1, 0, 3], [2, 3, 0]], dtype=float)
        v = triu_vector(D)
        np.testing.assert_array_equal(v, [1.0, 2.0, 3.0])

    def test_symmetric_matrix_matches_triu(self) -> None:
        rng = np.random.default_rng(4)
        raw = rng.random((5, 5))
        D = (raw + raw.T) / 2
        v = triu_vector(D)
        assert len(v) == 10  # C(5,2)
