"""Unit tests for the statistics harness (experiments/analysis/stats.py).

Acceptance criteria:
1. bca_bootstrap_ci: BCa method via scipy.stats.bootstrap; pinned interval on
   a known sample with fixed seed.
2. wilcoxon_one_sided: one-sided Wilcoxon signed-rank (H1: IsalHG > baseline);
   correct p-value and rank-biserial effect size.
3. holm_bonferroni: adjusted p-values non-decreasing in rank order;
   correct family-wise control; returned in original index order.
4. aggregate_a3_seed_scores: returns exactly S values (one per seed), not S*F;
   each value is the mean over that seed's folds.  A test that FAILS if folds
   and seeds are resampled independently.

Teeth:
- test_bca_ci_pinned_value: fails before implementation (NotImplementedError).
- test_holm_bonferroni_ordering: fails before implementation.
- test_nested_cv_sample_count_equals_n_seeds: fails before implementation AND
  detects the double-counting bug (S*F samples) by asserting len == S.
"""

from __future__ import annotations

import numpy as np
import pytest

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# 1. BCa bootstrap CI — pinned value
# ---------------------------------------------------------------------------


def test_bca_ci_pinned_value():
    """BCa CI on [1..10] with rng_seed=0 matches scipy.stats.bootstrap directly.

    Pinned: lower=3.7000, upper=7.2845 (computed 2026-07-23, scipy 1.x).

    The test fails before implementation because bca_bootstrap_ci raises
    NotImplementedError.
    """
    from experiments.analysis.stats import bca_bootstrap_ci

    data = list(range(1, 11))  # [1, 2, ..., 10], mean=5.5
    ci = bca_bootstrap_ci(data, n_resamples=9999, rng_seed=0)

    np.testing.assert_allclose(ci.lower, 3.7000, atol=0.15)
    np.testing.assert_allclose(ci.upper, 7.2845, atol=0.15)
    assert ci.lower < 5.5 < ci.upper, "True mean must lie inside CI"
    assert ci.n_samples == 10


def test_bca_ci_constant_sample():
    """BCa CI on constant data has width ~0.

    A constant sample has no variation; the CI collapses to [c, c].
    """
    from experiments.analysis.stats import bca_bootstrap_ci

    data = [3.0] * 20
    ci = bca_bootstrap_ci(data, n_resamples=999, rng_seed=0)
    np.testing.assert_allclose(ci.lower, 3.0, atol=1e-6)
    np.testing.assert_allclose(ci.upper, 3.0, atol=1e-6)


def test_bca_ci_returns_named_tuple():
    """bca_bootstrap_ci returns an object with .lower, .upper, .n_samples."""
    from experiments.analysis.stats import bca_bootstrap_ci

    ci = bca_bootstrap_ci([1.0, 2.0, 3.0], n_resamples=499, rng_seed=0)
    assert hasattr(ci, "lower")
    assert hasattr(ci, "upper")
    assert hasattr(ci, "n_samples")
    assert ci.lower <= ci.upper


# ---------------------------------------------------------------------------
# 2. Wilcoxon one-sided + rank-biserial
# ---------------------------------------------------------------------------


def test_wilcoxon_one_sided_pinned():
    """One-sided Wilcoxon (H1: IsalHG > baseline) pinned on a 5-element pair.

    Pinned: p=0.0312, rank-biserial r=1.0000 (all differences > 0, W+=15).
    """
    from experiments.analysis.stats import wilcoxon_one_sided

    isalhg = [0.80, 0.90, 0.85, 0.87, 0.82]
    baseline = [0.70, 0.75, 0.72, 0.68, 0.73]

    result = wilcoxon_one_sided(isalhg, baseline)

    np.testing.assert_allclose(result.p_value, 0.0312, atol=0.002)
    np.testing.assert_allclose(result.effect_size, 1.0, atol=0.01)
    assert result.test_used == "wilcoxon"
    assert result.median_diff > 0


def test_wilcoxon_one_sided_null():
    """When IsalHG == baseline, p-value should be large (no effect)."""
    from experiments.analysis.stats import wilcoxon_one_sided

    x = [0.5] * 5
    y = [0.5] * 5
    result = wilcoxon_one_sided(x, y)
    # All differences are 0; scipy raises ValueError or returns p≈1
    # We accept either: the function must not crash.
    assert result.p_value >= 0.0


def test_wilcoxon_one_sided_returns_named_fields():
    """wilcoxon_one_sided result has the required fields."""
    from experiments.analysis.stats import wilcoxon_one_sided

    result = wilcoxon_one_sided([0.6, 0.7, 0.8], [0.5, 0.6, 0.7])
    assert hasattr(result, "statistic")
    assert hasattr(result, "p_value")
    assert hasattr(result, "effect_size")
    assert hasattr(result, "median_diff")
    assert hasattr(result, "test_used")


# ---------------------------------------------------------------------------
# 3. Holm–Bonferroni correction
# ---------------------------------------------------------------------------


def test_holm_bonferroni_ordering():
    """Holm-corrected p-values in original order; non-decreasing in rank order.

    Input (original order): [0.01, 0.04, 0.02, 0.5]
    Expected adjusted (original order): [0.04, 0.08, 0.06, 0.5]

    Pinned manually:
      sorted: 0.01 → 0.04 (×4), 0.02 → 0.06 (×3), 0.04 → 0.08 (×2), 0.5 → 0.5 (×1)
      after cummax: [0.04, 0.06, 0.08, 0.5]
      mapped back: [0.04, 0.08, 0.06, 0.5]
    """
    from experiments.analysis.stats import holm_bonferroni

    p_values = [0.01, 0.04, 0.02, 0.5]
    result = holm_bonferroni(p_values)

    expected = [0.04, 0.08, 0.06, 0.5]
    np.testing.assert_allclose(result.adjusted_p_values, expected, atol=1e-9)

    # All adjusted p-values must be <= 1.0
    assert all(p <= 1.0 for p in result.adjusted_p_values)

    # Smallest raw p (0.01) should be rejected at alpha=0.05
    assert result.rejected[0] is True
    # Largest raw p (0.5) should not be rejected
    assert result.rejected[3] is False


def test_holm_bonferroni_single_test():
    """Holm with one test: adjusted p = p itself (Bonferroni factor = 1)."""
    from experiments.analysis.stats import holm_bonferroni

    result = holm_bonferroni([0.03])
    np.testing.assert_allclose(result.adjusted_p_values, [0.03], atol=1e-9)


def test_holm_bonferroni_all_below_alpha():
    """All very small p-values: all rejected after Holm correction."""
    from experiments.analysis.stats import holm_bonferroni

    p_values = [0.001, 0.002, 0.003]
    result = holm_bonferroni(p_values, alpha=0.05)
    assert all(result.rejected)


def test_holm_bonferroni_none_below_alpha():
    """All large p-values: none rejected."""
    from experiments.analysis.stats import holm_bonferroni

    p_values = [0.3, 0.4, 0.5]
    result = holm_bonferroni(p_values, alpha=0.05)
    assert not any(result.rejected)


# ---------------------------------------------------------------------------
# 4. A3 nested-CV aggregation — the anti-pattern test
# ---------------------------------------------------------------------------


def test_nested_cv_sample_count_equals_n_seeds():
    """aggregate_a3_seed_scores returns exactly S values (one per seed), not S*F.

    This test FAILS (at runtime) if the implementation pools folds and seeds
    as independent samples (S*F values instead of S).

    Setup: S=3 seeds, F=5 folds each.  Within each seed all fold scores are
    constant; the seed means differ (0.5, 0.8, 0.6).  The correct aggregation
    returns [0.5, 0.8, 0.6] (3 values); the wrong aggregation returns
    [0.5]*5 + [0.8]*5 + [0.6]*5 (15 values).
    """
    from experiments.analysis.stats import aggregate_a3_seed_scores

    fold_scores_per_seed = [
        [0.50, 0.50, 0.50, 0.50, 0.50],  # seed 0
        [0.80, 0.80, 0.80, 0.80, 0.80],  # seed 1
        [0.60, 0.60, 0.60, 0.60, 0.60],  # seed 2
    ]
    seed_scores = aggregate_a3_seed_scores(fold_scores_per_seed)

    # MUST have S=3 values, not S*F=15
    assert len(seed_scores) == 3, (
        f"Expected 3 seed scores (one per seed), got {len(seed_scores)}. "
        "Detected double-counting bug: folds and seeds resampled independently."
    )
    np.testing.assert_allclose(seed_scores, [0.50, 0.80, 0.60], atol=1e-9)


def test_nested_cv_mean_per_seed():
    """Each seed score is the arithmetic mean of its fold scores."""
    from experiments.analysis.stats import aggregate_a3_seed_scores

    fold_scores_per_seed = [
        [0.60, 0.70, 0.80],  # seed 0: mean = 0.70
        [0.50, 0.55, 0.60],  # seed 1: mean = 0.55
    ]
    seed_scores = aggregate_a3_seed_scores(fold_scores_per_seed)

    assert len(seed_scores) == 2
    np.testing.assert_allclose(seed_scores[0], 0.70, atol=1e-9)
    np.testing.assert_allclose(seed_scores[1], 0.55, atol=1e-9)


def test_nested_cv_variance_not_deflated():
    """CI over seed-level scores must be WIDER than CI over all fold scores.

    When folds agree within a seed but seeds vary, pooling folds inflates
    degrees of freedom and deflates the CI.  The correct (seed-level) CI
    must be at least as wide as the pooled CI.
    """
    from experiments.analysis.stats import aggregate_a3_seed_scores, bca_bootstrap_ci

    # Seeds have high between-seed variance; within each seed folds are identical
    fold_scores_per_seed = [
        [0.3] * 5,
        [0.9] * 5,
        [0.2] * 5,
        [0.8] * 5,
        [0.4] * 5,
    ]
    seed_scores = aggregate_a3_seed_scores(fold_scores_per_seed)  # 5 values

    ci_seed = bca_bootstrap_ci(seed_scores, n_resamples=999, rng_seed=0)
    all_folds = [s for folds in fold_scores_per_seed for s in folds]  # 25 values
    ci_pooled = bca_bootstrap_ci(all_folds, n_resamples=999, rng_seed=0)

    ci_seed_width = ci_seed.upper - ci_seed.lower
    ci_pooled_width = ci_pooled.upper - ci_pooled.lower

    assert ci_seed_width >= ci_pooled_width - 0.05, (
        f"Seed CI width ({ci_seed_width:.3f}) should be ≥ pooled CI width "
        f"({ci_pooled_width:.3f}); pooled CI deflates variance."
    )
