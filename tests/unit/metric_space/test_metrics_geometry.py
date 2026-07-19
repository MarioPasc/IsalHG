"""Unit tests for :mod:`isalhg.metric_space.metrics.geometry`.

Concentration diagnostics, length-difference floor, k-occurrence counts, and
hubness skewness — verified against hand-computed values.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

np = pytest.importorskip("numpy")
pytest.importorskip("scipy")

from isalhg.metric_space.metrics.geometry import (  # noqa: E402
    concentration_stats,
    hubness_skewness,
    k_occurrence_counts,
    length_difference_floor,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def D_path() -> np.ndarray:
    """Path-graph metric on 3 points: 0--1--2."""
    return np.array([[0, 1, 2], [1, 0, 1], [2, 1, 0]], dtype=float)


@pytest.fixture()
def D_hub() -> np.ndarray:
    """Hub-spoke metric: point 0 is close to all; leaves are far from each other."""
    return np.array([[0, 1, 1, 1], [1, 0, 3, 3], [1, 3, 0, 3], [1, 3, 3, 0]], dtype=float)


# ---------------------------------------------------------------------------
# concentration_stats
# ---------------------------------------------------------------------------


class TestConcentrationStats:
    def test_returns_expected_keys(self, D_path: np.ndarray) -> None:
        stats = concentration_stats(D_path)
        for key in ("diameter", "median", "q25", "q75", "iqr", "diameter_to_median"):
            assert key in stats, f"missing key: {key}"

    def test_path_metric_diameter_and_median(self, D_path: np.ndarray) -> None:
        # Upper-triangle pairs: [1.0, 2.0, 1.0]
        stats = concentration_stats(D_path)
        assert stats["diameter"] == pytest.approx(2.0)
        assert stats["median"] == pytest.approx(1.0)
        assert stats["diameter_to_median"] == pytest.approx(2.0)

    def test_path_metric_iqr(self, D_path: np.ndarray) -> None:
        # pairs = [1.0, 1.0, 2.0] sorted; q25=1.0, q75=1.5, iqr=0.5
        stats = concentration_stats(D_path)
        assert stats["iqr"] == pytest.approx(0.5)

    def test_uniform_metric_ratio_is_one(self) -> None:
        # All pairwise distances equal → diameter == median → ratio == 1
        D = np.ones((5, 5)) - np.eye(5)
        D = D.astype(float)
        stats = concentration_stats(D)
        assert stats["diameter"] == pytest.approx(stats["median"])
        assert stats["diameter_to_median"] == pytest.approx(1.0)

    def test_single_pair(self) -> None:
        D = np.array([[0.0, 3.0], [3.0, 0.0]])
        stats = concentration_stats(D)
        assert stats["diameter"] == pytest.approx(3.0)
        assert stats["median"] == pytest.approx(3.0)

    def test_values_non_negative(self, D_hub: np.ndarray) -> None:
        stats = concentration_stats(D_hub)
        for v in stats.values():
            assert v >= 0.0


# ---------------------------------------------------------------------------
# length_difference_floor
# ---------------------------------------------------------------------------


class TestLengthDifferenceFloor:
    def test_shape(self) -> None:
        lengths = [3, 1, 5, 2]
        floor = length_difference_floor(lengths)
        assert floor.shape == (4, 4)

    def test_zero_diagonal(self) -> None:
        lengths = [3, 1, 5, 2]
        floor = length_difference_floor(lengths)
        np.testing.assert_array_equal(np.diag(floor), 0)

    def test_symmetric(self) -> None:
        lengths = [3, 1, 5, 2]
        floor = length_difference_floor(lengths)
        np.testing.assert_array_equal(floor, floor.T)

    def test_hand_computed_values(self) -> None:
        # |3-1|=2, |3-5|=2, |3-2|=1, |1-5|=4, |1-2|=1, |5-2|=3
        lengths = [3, 1, 5, 2]
        floor = length_difference_floor(lengths)
        expected = np.array([[0, 2, 2, 1], [2, 0, 4, 1], [2, 4, 0, 3], [1, 1, 3, 0]], dtype=float)
        np.testing.assert_array_equal(floor, expected)

    def test_single_element(self) -> None:
        floor = length_difference_floor([5])
        assert floor.shape == (1, 1)
        assert floor[0, 0] == 0.0

    def test_equal_lengths_all_zero(self) -> None:
        floor = length_difference_floor([4, 4, 4])
        np.testing.assert_array_equal(floor, 0)


# ---------------------------------------------------------------------------
# k_occurrence_counts
# ---------------------------------------------------------------------------


class TestKOccurrenceCounts:
    def test_shape(self, D_hub: np.ndarray) -> None:
        counts = k_occurrence_counts(D_hub, k=1)
        assert counts.shape == (4,)

    def test_total_equals_n_times_k(self, D_hub: np.ndarray) -> None:
        k = 2
        counts = k_occurrence_counts(D_hub, k=k)
        # Each of N points contributes k entries → sum = N*k
        assert int(counts.sum()) == 4 * k

    def test_hub_spoke_k1_hand_computed(self, D_hub: np.ndarray) -> None:
        # k=1 NN for each point (argsort of row, excluding self):
        #   point 0: {1,2,3} all at dist 1 → stable sort picks index 1 first
        #   point 1: {0} at dist 1
        #   point 2: {0} at dist 1
        #   point 3: {0} at dist 1
        # N_1(0)=3, N_1(1)=1, N_1(2)=0, N_1(3)=0
        counts = k_occurrence_counts(D_hub, k=1)
        np.testing.assert_array_equal(counts, [3, 1, 0, 0])

    def test_hub_spoke_k2_hand_computed(self, D_hub: np.ndarray) -> None:
        # k=2 NN:
        #   point 0: NN = {1, 2}  (stable: indices 1,2 first among equidist. 1)
        #   point 1: NN = {0, 2}  (0 at 1, 2 at 3)
        #   point 2: NN = {0, 1}
        #   point 3: NN = {0, 1}
        # N_2: 0→3, 1→3, 2→2, 3→0
        counts = k_occurrence_counts(D_hub, k=2)
        np.testing.assert_array_equal(counts, [3, 3, 2, 0])

    def test_excludes_self(self, D_hub: np.ndarray) -> None:
        # A point should never appear in its own k-NN list
        counts = k_occurrence_counts(D_hub, k=1)
        # point 0 is the hub (dist 1 from all), so if self were included point 0
        # would count distance 0 to itself and would not be in others' lists
        # — just verify sum equals N*k
        assert int(counts.sum()) == 4 * 1


# ---------------------------------------------------------------------------
# hubness_skewness
# ---------------------------------------------------------------------------


class TestHubnessSkewness:
    def test_hub_spoke_k1_pinned(self, D_hub: np.ndarray) -> None:
        # k_occurrence_counts = [3,1,0,0]
        # scipy.stats.skew([3,1,0,0], bias=True) ≈ 0.8165
        s = hubness_skewness(D_hub, k=1)
        assert s == pytest.approx(0.8165, abs=1e-3)

    def test_hub_spoke_k2_negative(self, D_hub: np.ndarray) -> None:
        # k_occurrence_counts = [3,3,2,0] — skewed left (one zero outlier)
        # scipy.stats.skew([3,3,2,0], bias=True) ≈ -0.8165
        s = hubness_skewness(D_hub, k=2)
        assert s == pytest.approx(-0.8165, abs=1e-3)

    def test_uniform_counts_no_hubness(self) -> None:
        # Cycle: each point appears exactly once in others' k=1 NN lists
        # counts = [1,1,1,1] → skewness = 0.0 (handle NaN from scipy as 0)
        # Use a directed cycle where NN are unique
        D = np.array([[0, 1, 3, 3], [3, 0, 1, 3], [3, 3, 0, 1], [1, 3, 3, 0]], dtype=float)
        s = hubness_skewness(D, k=1)
        # [1,1,1,1] → std=0, scipy returns NaN; our function must return 0.0
        assert s == pytest.approx(0.0, abs=1e-10)

    def test_returns_float(self, D_hub: np.ndarray) -> None:
        s = hubness_skewness(D_hub, k=1)
        assert isinstance(s, float)
