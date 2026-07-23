"""Paired statistical tests and bootstrap CIs for the S7 body re-run.

Functions
---------
bca_bootstrap_ci
    BCa bootstrap 95% CI on a 1-D sample (scipy.stats.bootstrap).
wilcoxon_one_sided
    One-sided Wilcoxon signed-rank test (H1: IsalHG > baseline) with
    rank-biserial effect size.
holm_bonferroni
    Holm-Bonferroni correction across a family of p-values.
aggregate_a3_seed_scores
    Collapse nested-CV fold scores to seed-level scores (mean per seed).
    The resampling unit is always the seed, never the fold × seed product.

Dataclasses
-----------
BootstrapCI
    Holds (lower, upper, n_samples).
PairedTestResult
    Holds (statistic, p_value, effect_size, median_diff, test_used).
HolmResult
    Holds (adjusted_p_values, rejected).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BootstrapCI:
    """Bias-corrected accelerated bootstrap confidence interval."""

    lower: float
    upper: float
    n_samples: int


@dataclass(frozen=True)
class PairedTestResult:
    """Outcome of one paired comparison (IsalHG vs one baseline)."""

    statistic: float
    p_value: float
    effect_size: float  # rank-biserial r  in  [-1, +1]
    median_diff: float  # median(isalhg - baseline)
    test_used: str  # "wilcoxon"


@dataclass(frozen=True)
class HolmResult:
    """Holm-Bonferroni-corrected family of p-values."""

    adjusted_p_values: list[float]
    rejected: list[bool]  # at the requested alpha level


# ---------------------------------------------------------------------------
# BCa bootstrap CI
# ---------------------------------------------------------------------------


def bca_bootstrap_ci(
    samples: Sequence[float],
    *,
    n_resamples: int = 10_000,
    confidence: float = 0.95,
    rng_seed: int = 0,
) -> BootstrapCI:
    """BCa bootstrap confidence interval for the mean of *samples*.

    Uses ``scipy.stats.bootstrap`` with ``method='BCa'``.  The CI is
    bias- and skewness-corrected, making it more accurate than the
    percentile CI for small samples.

    Parameters
    ----------
    samples : sequence of float
        The observed values (S seed-level scores, for instance).
    n_resamples : int, optional
        Number of bootstrap replicates.  Default 10 000.
    confidence : float, optional
        Coverage level.  Default 0.95.
    rng_seed : int, optional
        Seed for the bootstrap RNG.  Default 0.

    Returns
    -------
    BootstrapCI
        Tuple (lower, upper, n_samples).

    Raises
    ------
    ValueError
        If *samples* is empty.
    """
    from scipy import stats

    arr = np.asarray(samples, dtype=float)
    if arr.size == 0:
        raise ValueError("samples must not be empty")

    # Degenerate case: constant data has zero variance; BCa is undefined.
    # Return a point interval at the common value.
    if np.all(arr == arr[0]):
        c = float(arr[0])
        return BootstrapCI(lower=c, upper=c, n_samples=int(arr.size))

    # scipy.stats.bootstrap expects a tuple of 1-D arrays.
    result = stats.bootstrap(
        (arr,),
        np.mean,
        n_resamples=n_resamples,
        confidence_level=confidence,
        method="BCa",
        random_state=int(rng_seed),
    )
    return BootstrapCI(
        lower=float(result.confidence_interval.low),
        upper=float(result.confidence_interval.high),
        n_samples=int(arr.size),
    )


# ---------------------------------------------------------------------------
# One-sided Wilcoxon signed-rank + rank-biserial
# ---------------------------------------------------------------------------


def wilcoxon_one_sided(
    isalhg_samples: Sequence[float],
    baseline_samples: Sequence[float],
) -> PairedTestResult:
    """One-sided Wilcoxon signed-rank test (H1: IsalHG > baseline).

    The resampling unit must be seeds: ``isalhg_samples[i]`` and
    ``baseline_samples[i]`` are the seed-level scores for seed *i*
    (each already aggregated over CV folds via :func:`aggregate_a3_seed_scores`
    where applicable).

    Effect size is the rank-biserial correlation
    ``r = (W+ − W−) / (S*(S+1)/2)`` ∈ [−1, +1].

    Parameters
    ----------
    isalhg_samples : sequence of float
        IsalHG seed-level scores.
    baseline_samples : sequence of float
        Competitor seed-level scores, same length.

    Returns
    -------
    PairedTestResult
        statistic = W+ (sum of positive ranks),
        p_value   = one-sided p (H1: differences > 0),
        effect_size = rank-biserial r,
        median_diff = median(isalhg − baseline),
        test_used = "wilcoxon".

    Notes
    -----
    When all differences are zero ``scipy.stats.wilcoxon`` raises a
    ``ValueError``; we return statistic=0, p_value=1.0 in that case.
    """
    from scipy import stats

    a = np.asarray(isalhg_samples, dtype=float)
    b = np.asarray(baseline_samples, dtype=float)
    diff = a - b
    median_diff = float(np.median(diff))
    n = len(diff)

    try:
        res = stats.wilcoxon(diff, alternative="greater")
        W_plus = float(res.statistic)
        p_value = float(res.pvalue)
    except ValueError:
        # All differences zero or only one pair.
        W_plus = 0.0
        p_value = 1.0

    W_total = n * (n + 1) / 2.0
    W_minus = W_total - W_plus
    # rank-biserial r = (W+ - W-) / W_total
    effect_size = (W_plus - W_minus) / W_total if W_total > 0 else 0.0

    return PairedTestResult(
        statistic=W_plus,
        p_value=p_value,
        effect_size=effect_size,
        median_diff=median_diff,
        test_used="wilcoxon",
    )


# ---------------------------------------------------------------------------
# Holm–Bonferroni correction
# ---------------------------------------------------------------------------


def holm_bonferroni(
    p_values: Sequence[float],
    *,
    alpha: float = 0.05,
) -> HolmResult:
    """Holm-Bonferroni correction across a family of p-values.

    Adjusted p-values are returned in the **same order** as the input.
    The adjusted values are non-decreasing along the rank order (smallest
    raw p-value first) and capped at 1.0.

    Parameters
    ----------
    p_values : sequence of float
        Raw p-values, one per test in the family.
    alpha : float, optional
        Family-wise error rate.  Default 0.05.

    Returns
    -------
    HolmResult
        adjusted_p_values : list of float, original order.
        rejected : list of bool, True when adjusted p ≤ alpha.

    Notes
    -----
    Algorithm (Holm 1979):
      1. Sort indices by raw p-value ascending.
      2. For rank j (1-indexed): adjusted_p[j] = p[j] * (m − j + 1).
      3. Enforce monotonicity: cumulative maximum over ranks.
      4. Cap at 1.0.
      5. Map back to original index order.
    """
    p_arr = np.asarray(p_values, dtype=float)
    m = len(p_arr)
    if m == 0:
        return HolmResult(adjusted_p_values=[], rejected=[])

    sorted_idx = np.argsort(p_arr, kind="stable")
    sorted_p = p_arr[sorted_idx]

    # Multiply by decreasing correction factors
    factors = np.arange(m, 0, -1, dtype=float)  # [m, m-1, ..., 1]
    adjusted_sorted = np.minimum(sorted_p * factors, 1.0)

    # Enforce non-decreasing order (cumulative maximum)
    for i in range(1, m):
        adjusted_sorted[i] = max(adjusted_sorted[i], adjusted_sorted[i - 1])

    # Map back to original order
    adjusted_original = np.empty(m, dtype=float)
    adjusted_original[sorted_idx] = adjusted_sorted

    adj_list = adjusted_original.tolist()
    rejected = [float(p) <= alpha for p in adj_list]
    return HolmResult(adjusted_p_values=adj_list, rejected=rejected)


# ---------------------------------------------------------------------------
# A3 nested-CV seed aggregation
# ---------------------------------------------------------------------------


def aggregate_a3_seed_scores(
    fold_scores_per_seed: list[list[float]],
) -> list[float]:
    """Aggregate nested-CV fold scores to seed-level scores (mean per seed).

    The resampling unit for bootstrap and Wilcoxon is the **seed**, not the
    fold.  This function reduces S × F scores to S seed-level values by
    taking the arithmetic mean over folds within each seed.  The caller then
    passes the returned list of S values to :func:`bca_bootstrap_ci` or
    :func:`wilcoxon_one_sided`.

    Using the S × F raw fold scores directly in a bootstrap would inflate
    the effective sample size by F, underestimating the CI width by √F
    (double-counting variance).

    Parameters
    ----------
    fold_scores_per_seed : list of list of float
        Outer list length S (seeds); each inner list has F fold-level scores
        for that seed (e.g., AUC from each fold of stratified CV).

    Returns
    -------
    list of float
        Length S; entry i = ``mean(fold_scores_per_seed[i])``.

    Raises
    ------
    ValueError
        If *fold_scores_per_seed* is empty or any inner list is empty.
    """
    if not fold_scores_per_seed:
        raise ValueError("fold_scores_per_seed must not be empty")
    seed_scores: list[float] = []
    for i, fold_scores in enumerate(fold_scores_per_seed):
        if not fold_scores:
            raise ValueError(f"seed {i}: fold_scores must not be empty")
        seed_scores.append(float(np.mean(fold_scores)))
    return seed_scores


# ---------------------------------------------------------------------------
# Legacy stubs (retained for backward compatibility with preprint sweep)
# ---------------------------------------------------------------------------


def paired_test(
    isalhg_samples: Sequence[float],
    baseline_samples: Sequence[float],
) -> PairedTestResult:
    """Backward-compat wrapper: delegates to :func:`wilcoxon_one_sided`."""
    return wilcoxon_one_sided(isalhg_samples, baseline_samples)


def bootstrap_ci(
    samples: Sequence[float],
    *,
    n_resamples: int = 10_000,
) -> tuple[float, float]:
    """Backward-compat: percentile-bootstrap wrapper over BCa implementation.

    Returns (lower, upper) only; use :func:`bca_bootstrap_ci` for the full
    BootstrapCI object.
    """
    ci = bca_bootstrap_ci(samples, n_resamples=n_resamples)
    return (ci.lower, ci.upper)
