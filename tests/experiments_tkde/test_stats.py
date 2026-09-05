"""Unit tests for the statistics harness.

Every function is checked against an independent authority: ``wilson_ci``
against the published interval for 2/10 successes, ``wilcoxon_paired`` against
``scipy.stats.wilcoxon`` on the same data, ``holm`` against a family adjusted by
hand, ``cliffs_delta`` against its two saturating cases, and ``spearman_ci``
against the behaviour that motivates it (a clustered bootstrap must be wider
than the i.i.d. one on clustered data).
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.stats import wilcoxon as scipy_wilcoxon

from experiments.tkde.config import TkdeStatsError
from experiments.tkde.stats import (
    Interval,
    bca_ci,
    cliffs_delta,
    holm,
    paired_family,
    spearman_ci,
    wilcoxon_paired,
    wilson_ci,
)

pytestmark = pytest.mark.unit


class TestWilsonCi:
    def test_matches_the_published_interval_for_2_of_10(self) -> None:
        # Wilson 95 % for p̂ = 0.2, n = 10: (0.0567, 0.5098) — Brown, Cai &
        # DasGupta, Statistical Science 16(2), 2001, Table 1.
        interval = wilson_ci(2, 10)
        assert interval.point == pytest.approx(0.2)
        assert interval.low == pytest.approx(0.0567, abs=5e-4)
        assert interval.high == pytest.approx(0.5098, abs=5e-4)
        assert interval.method == "wilson"
        assert interval.n == 10

    def test_zero_successes_has_positive_width_and_stays_in_range(self) -> None:
        interval = wilson_ci(0, 20)
        assert interval.point == 0.0
        assert interval.low == 0.0
        assert 0.0 < interval.high < 1.0

    def test_all_successes(self) -> None:
        interval = wilson_ci(20, 20)
        assert interval.point == 1.0
        assert interval.high == 1.0
        assert 0.0 < interval.low < 1.0

    def test_interval_narrows_with_n(self) -> None:
        narrow = wilson_ci(500, 1000)
        wide = wilson_ci(5, 10)
        assert (narrow.high - narrow.low) < (wide.high - wide.low)

    @pytest.mark.parametrize(("successes", "n"), [(1, 0), (-1, 10), (11, 10)])
    def test_invalid_counts_raise(self, successes: int, n: int) -> None:
        with pytest.raises(TkdeStatsError):
            wilson_ci(successes, n)


class TestBcaCi:
    def test_contains_the_point_estimate(self) -> None:
        rng = np.random.default_rng(0)
        samples = rng.normal(loc=5.0, scale=1.0, size=27)
        interval = bca_ci(samples)
        assert interval.point == pytest.approx(float(np.mean(samples)))
        assert interval.low <= interval.point <= interval.high
        assert interval.method == "bca_mean"
        assert interval.n == 27

    def test_shrinks_with_n(self) -> None:
        rng = np.random.default_rng(1)
        small = bca_ci(rng.normal(size=20), n_resamples=2000)
        large = bca_ci(rng.normal(size=2000), n_resamples=2000)
        assert (large.high - large.low) < (small.high - small.low)

    def test_median_statistic(self) -> None:
        samples = [1.0, 2.0, 3.0, 4.0, 100.0]
        interval = bca_ci(samples, stat="median", n_resamples=2000)
        assert interval.point == pytest.approx(3.0)
        assert interval.method == "bca_median"

    def test_constant_input_is_degenerate(self) -> None:
        interval = bca_ci([2.0] * 10)
        assert (interval.point, interval.low, interval.high) == (2.0, 2.0, 2.0)

    def test_empty_and_unknown_stat_raise(self) -> None:
        with pytest.raises(TkdeStatsError, match="at least one"):
            bca_ci([])
        with pytest.raises(TkdeStatsError, match="mean"):
            bca_ci([1.0, 2.0], stat="mode")


class TestWilcoxonPaired:
    def test_agrees_with_scipy(self) -> None:
        rng = np.random.default_rng(3)
        a = rng.normal(size=27)
        b = a + rng.normal(scale=0.5, size=27)
        result = wilcoxon_paired(a, b)
        reference = scipy_wilcoxon(a, b, alternative="two-sided", zero_method="wilcox")
        assert result["statistic"] == pytest.approx(float(reference.statistic))
        assert result["p_value"] == pytest.approx(float(reference.pvalue))
        assert result["n"] == 27
        assert result["n_ties"] == 0

    def test_rank_biserial_saturates_when_ours_always_wins(self) -> None:
        a = [2.0, 3.0, 4.0, 5.0]
        b = [1.0, 2.0, 3.0, 4.0]
        assert wilcoxon_paired(a, b)["rank_biserial"] == pytest.approx(1.0)
        assert wilcoxon_paired(b, a)["rank_biserial"] == pytest.approx(-1.0)

    def test_zero_differences_are_counted_not_tested(self) -> None:
        result = wilcoxon_paired([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])
        assert result["n"] == 0
        assert result["n_ties"] == 3
        assert result["p_value"] == 1.0
        assert result["rank_biserial"] == 0.0

    def test_partial_ties_are_excluded_from_n(self) -> None:
        result = wilcoxon_paired([1.0, 2.0, 5.0, 4.0], [1.0, 1.0, 3.0, 1.0])
        assert result["n"] == 3
        assert result["n_ties"] == 1

    def test_one_sided_p_is_smaller_when_the_effect_agrees(self) -> None:
        rng = np.random.default_rng(4)
        a = rng.normal(loc=1.0, size=27)
        b = rng.normal(loc=0.0, size=27)
        two_sided = wilcoxon_paired(a, b)["p_value"]
        greater = wilcoxon_paired(a, b, alternative="greater")["p_value"]
        assert greater < two_sided

    def test_length_mismatch_raises(self) -> None:
        with pytest.raises(TkdeStatsError, match="entries"):
            wilcoxon_paired([1.0, 2.0], [1.0])


class TestHolm:
    def test_matches_a_hand_computed_family(self) -> None:
        # m = 4.  Sorted: 0.001, 0.010, 0.030, 0.040.
        # Raw multipliers 4, 3, 2, 1 -> 0.004, 0.030, 0.060, 0.040; the
        # monotonicity pass lifts the last to 0.060.
        rows = holm([0.030, 0.001, 0.040, 0.010], alpha=0.05)
        adjusted = {row["index"]: row["p_holm"] for row in rows}
        assert adjusted[1] == pytest.approx(0.004)
        assert adjusted[3] == pytest.approx(0.030)
        assert adjusted[0] == pytest.approx(0.060)
        assert adjusted[2] == pytest.approx(0.060)
        assert [row["reject"] for row in rows] == [False, True, False, True]

    def test_preserves_input_order_and_raw_values(self) -> None:
        raw = [0.5, 0.01, 0.2]
        rows = holm(raw)
        assert [row["index"] for row in rows] == [0, 1, 2]
        assert [row["p_raw"] for row in rows] == raw

    def test_adjusted_never_below_raw(self) -> None:
        raw = [0.001, 0.02, 0.3, 0.4, 0.9]
        assert all(row["p_holm"] >= row["p_raw"] - 1e-12 for row in holm(raw))

    def test_empty_family(self) -> None:
        assert holm([]) == []


class TestCliffsDelta:
    def test_plus_one_when_a_dominates(self) -> None:
        result = cliffs_delta([10.0, 11.0, 12.0], [1.0, 2.0, 3.0], n_resamples=200)
        assert result.point == pytest.approx(1.0)
        assert result.n == 6

    def test_minus_one_when_b_dominates(self) -> None:
        assert cliffs_delta([1.0, 2.0], [10.0, 11.0], n_resamples=200).point == pytest.approx(-1.0)

    def test_near_zero_on_identical_distributions(self) -> None:
        rng = np.random.default_rng(5)
        a = rng.normal(size=400)
        b = rng.normal(size=400)
        result = cliffs_delta(a, b, n_resamples=300)
        assert abs(result.point) < 0.12
        assert result.low <= result.point <= result.high

    def test_exactly_zero_on_the_same_sample(self) -> None:
        values = [1.0, 2.0, 3.0, 4.0]
        assert cliffs_delta(values, values, n_resamples=100).point == pytest.approx(0.0)

    def test_is_deterministic_under_the_seed(self) -> None:
        rng = np.random.default_rng(6)
        a, b = rng.normal(size=50), rng.normal(size=50)
        first = cliffs_delta(a, b, n_resamples=200, seed=3)
        second = cliffs_delta(a, b, n_resamples=200, seed=3)
        assert first == second

    def test_empty_sample_raises(self) -> None:
        with pytest.raises(TkdeStatsError, match="non-empty"):
            cliffs_delta([], [1.0])


class TestSpearmanCi:
    def test_point_estimate_and_monotone_data(self) -> None:
        x = list(range(20))
        y = [value**3 for value in x]
        result = spearman_ci(x, y, n_resamples=200)
        assert result.point == pytest.approx(1.0)
        assert result.method == "spearman_percentile_bootstrap"
        assert result.n == 20

    def test_cluster_bootstrap_differs_from_the_iid_one(self) -> None:
        # Twelve clusters of five observations each; within a cluster the
        # observations are near-identical, so the effective sample size is 12,
        # not 60, and the clustered interval must be the wider of the two.
        rng = np.random.default_rng(7)
        clusters: list[int] = []
        x: list[float] = []
        y: list[float] = []
        for cluster in range(12):
            base_x = rng.normal()
            base_y = base_x + rng.normal(scale=0.8)
            for _ in range(5):
                clusters.append(cluster)
                x.append(base_x + rng.normal(scale=0.01))
                y.append(base_y + rng.normal(scale=0.01))

        iid = spearman_ci(x, y, n_resamples=500, seed=0)
        clustered = spearman_ci(x, y, clusters=clusters, n_resamples=500, seed=0)
        assert clustered.method == "spearman_cluster_bootstrap"
        assert iid.method == "spearman_percentile_bootstrap"
        assert clustered.point == pytest.approx(iid.point)
        assert (clustered.high - clustered.low) > (iid.high - iid.low)

    def test_interval_brackets_the_point_on_noisy_data(self) -> None:
        rng = np.random.default_rng(8)
        x = rng.normal(size=60)
        y = x + rng.normal(scale=1.5, size=60)
        result = spearman_ci(x, y, n_resamples=400)
        assert result.low <= result.point <= result.high

    @pytest.mark.parametrize(
        ("x", "y", "clusters", "message"),
        [
            ([1.0, 2.0, 3.0], [1.0, 2.0], None, "entries"),
            ([1.0, 2.0], [1.0, 2.0], None, "three observations"),
            ([1.0, 2.0, 3.0], [1.0, 2.0, 3.0], [0, 1], "clusters"),
        ],
    )
    def test_invalid_input_raises(
        self, x: list[float], y: list[float], clusters: list[int] | None, message: str
    ) -> None:
        with pytest.raises(TkdeStatsError, match=message):
            spearman_ci(x, y, clusters=clusters)


class TestPairedFamily:
    def test_holm_adjusts_across_the_family(self) -> None:
        rng = np.random.default_rng(9)
        ours = rng.normal(loc=1.0, size=27)
        others = {
            "clear_loser": ours - 3.0 - rng.random(27),
            "near_tie": ours + rng.normal(scale=0.02, size=27),
            "clear_winner": ours + 3.0 + rng.random(27),
        }
        rows = paired_family(ours, others)

        assert [row["name"] for row in rows] == list(others)
        for row in rows:
            assert row["n"] == 27
            assert row["p_holm"] >= row["p_raw"] - 1e-12
            assert set(row["diff_ci"]) == {"point", "low", "high", "method", "n"}
            assert row["diff_ci"]["low"] <= row["diff_ci"]["point"] <= row["diff_ci"]["high"]

        by_name = {row["name"]: row for row in rows}
        assert by_name["clear_loser"]["rank_biserial"] == pytest.approx(1.0)
        assert by_name["clear_winner"]["rank_biserial"] == pytest.approx(-1.0)
        assert by_name["clear_loser"]["reject"]
        assert by_name["clear_winner"]["reject"]
        assert by_name["clear_loser"]["mean_ours"] > by_name["clear_loser"]["mean_other"]

    def test_family_of_one_leaves_p_unchanged(self) -> None:
        rng = np.random.default_rng(10)
        ours = rng.normal(size=27)
        rows = paired_family(ours, {"only": ours - 1.0})
        assert rows[0]["p_holm"] == pytest.approx(rows[0]["p_raw"])

    def test_length_mismatch_raises(self) -> None:
        with pytest.raises(TkdeStatsError, match="scores"):
            paired_family([1.0, 2.0, 3.0], {"bad": [1.0, 2.0]})


class TestInterval:
    def test_as_dict_is_json_ready(self) -> None:
        interval = Interval(point=0.5, low=0.4, high=0.6, method="wilson", n=10)
        assert interval.as_dict() == {
            "point": 0.5,
            "low": 0.4,
            "high": 0.6,
            "method": "wilson",
            "n": 10,
        }
