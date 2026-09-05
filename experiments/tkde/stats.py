"""The statistics harness of ``DESIGN.md`` G5 -- one procedure for every table.

Seven primitives, used by all seven research questions:

===========================  =========================================
:func:`bca_ci`               95 % BCa interval of a mean or median
:func:`wilson_ci`            95 % Wilson interval of a proportion
:func:`wilcoxon_paired`      paired Wilcoxon + matched-pairs rank-biserial
:func:`holm`                 Holm correction across one table's family
:func:`cliffs_delta`         unpaired effect size with a bootstrap interval
:func:`spearman_ci`          Spearman rho, clustered percentile bootstrap
:func:`paired_family`        ours vs every competitor, Holm-corrected
===========================  =========================================

``bca_ci`` and ``holm`` delegate to :mod:`experiments.analysis.stats`
(``bca_bootstrap_ci``, ``holm_bonferroni``), which are already reviewer-tested;
this module adds only what that module does not provide, and never duplicates
what it does.

Two conventions worth stating once. First, the *replication unit* is whatever
carries the randomness: 27 seed-level scores where a procedure is seeded, and a
cluster bootstrap over the natural cluster (base knowledge base, member) where
the unit is a real object. Second, every default here is two-sided; a
directional hypothesis passes ``alternative`` explicitly, because
``DESIGN.md`` pre-registers which those are.
"""

from __future__ import annotations

import logging
import math
import warnings
from collections.abc import Hashable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

from experiments.tkde.config import TkdeStatsError

DEFAULT_CONFIDENCE = 0.95

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Interval:
    """A point estimate with an interval and the method that produced it.

    Attributes
    ----------
    point : float
        The statistic on the observed sample.
    low, high : float
        Interval bounds at the requested confidence.
    method : str
        How the interval was obtained, verbatim in ``stats.json`` so a reader
        never has to guess (e.g. ``"bca_mean"``, ``"wilson"``).
    n : int
        Sample size the interval rests on.
    """

    point: float
    low: float
    high: float
    method: str
    n: int

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-ready mapping of the interval."""
        return {
            "point": self.point,
            "low": self.low,
            "high": self.high,
            "method": self.method,
            "n": self.n,
        }


# ---------------------------------------------------------------------------
# Intervals
# ---------------------------------------------------------------------------


def bca_ci(
    samples: Sequence[float],
    *,
    stat: str = "mean",
    n_resamples: int = 10_000,
    seed: int = 0,
) -> Interval:
    """BCa bootstrap interval of the mean or the median of ``samples``.

    Parameters
    ----------
    samples : Sequence[float]
        The replication-level scores (27 seed-level values, typically).
    stat : {"mean", "median"}, optional
        Statistic to bound. ``"mean"`` routes through
        :func:`experiments.analysis.stats.bca_bootstrap_ci`.
    n_resamples : int, optional
        Bootstrap replicates. Default 10 000 (``DESIGN.md`` G5).
    seed : int, optional
        Bootstrap RNG seed. Default 0.

    Returns
    -------
    Interval
        ``method`` is ``"bca_mean"`` or ``"bca_median"``. Constant input has
        zero variance and yields the degenerate interval at that value.

    Raises
    ------
    TkdeStatsError
        If ``samples`` is empty or ``stat`` is not one of the two names.
    """
    values = _as_1d(samples, "samples")
    if values.size == 0:
        raise TkdeStatsError("bca_ci needs at least one sample")
    if stat not in {"mean", "median"}:
        raise TkdeStatsError(f"stat must be 'mean' or 'median', got {stat!r}")

    point = float(np.mean(values) if stat == "mean" else np.median(values))
    method = f"bca_{stat}"

    if values.size == 1 or bool(np.all(values == values[0])):
        return Interval(point=point, low=point, high=point, method=method, n=int(values.size))

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if stat == "mean":
            from experiments.analysis.stats import bca_bootstrap_ci

            interval = bca_bootstrap_ci(
                values.tolist(),
                n_resamples=n_resamples,
                confidence=DEFAULT_CONFIDENCE,
                rng_seed=seed,
            )
            low, high = float(interval.lower), float(interval.upper)
        else:
            low, high = _bootstrap_bounds(values, np.median, n_resamples, seed, "BCa")

        if math.isfinite(low) and math.isfinite(high):
            return Interval(point=point, low=low, high=high, method=method, n=int(values.size))

        # BCa is undefined when the acceleration is degenerate -- near-constant
        # data, which the paired differences of two close arms often are. The
        # percentile interval is defined there; the method string says which one
        # the number came from, so no reader mistakes one for the other.
        estimator = np.mean if stat == "mean" else np.median
        low, high = _bootstrap_bounds(values, estimator, n_resamples, seed, "percentile")

    logger.warning(
        "BCa was degenerate for the %s of %d samples; reporting the percentile interval",
        stat,
        values.size,
    )
    return Interval(
        point=point,
        low=low,
        high=high,
        method=f"percentile_{stat}_bca_degenerate",
        n=int(values.size),
    )


def wilson_ci(successes: int, n: int, *, confidence: float = DEFAULT_CONFIDENCE) -> Interval:
    """Wilson score interval for a binomial proportion.

    Preferred over the normal approximation because the rates this design
    reports are frequently 0 or 1 (a false-merge count, a validity rate), where
    the Wald interval degenerates to zero width.

    Parameters
    ----------
    successes : int
        Number of successes, ``0 <= successes <= n``.
    n : int
        Number of trials, ``n >= 1``.
    confidence : float, optional
        Coverage. Default 0.95.

    Returns
    -------
    Interval
        ``point`` is ``successes / n``; ``method`` is ``"wilson"``.

    Raises
    ------
    TkdeStatsError
        If ``n < 1`` or ``successes`` is out of range.
    """
    if n < 1:
        raise TkdeStatsError(f"n must be >= 1, got {n}")
    if not 0 <= successes <= n:
        raise TkdeStatsError(f"successes must lie in [0, {n}], got {successes}")

    from scipy.stats import norm

    z = float(norm.ppf(1.0 - (1.0 - confidence) / 2.0))
    p = successes / n
    denominator = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / denominator
    half_width = (z / denominator) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return Interval(
        point=p,
        low=max(0.0, centre - half_width),
        high=min(1.0, centre + half_width),
        method="wilson",
        n=int(n),
    )


# ---------------------------------------------------------------------------
# Paired comparison
# ---------------------------------------------------------------------------


def wilcoxon_paired(
    a: Sequence[float], b: Sequence[float], *, alternative: str = "two-sided"
) -> dict[str, Any]:
    """Paired Wilcoxon signed-rank test with the matched-pairs rank-biserial.

    Parameters
    ----------
    a, b : Sequence[float]
        Paired observations of equal length; ``a`` is "ours" by convention, so
        a positive ``rank_biserial`` means ``a`` scores higher.
    alternative : {"two-sided", "greater", "less"}, optional
        Passed to ``scipy.stats.wilcoxon``. Default two-sided
        (``DESIGN.md`` G5: directional hypotheses ask for it explicitly).

    Returns
    -------
    dict
        ``statistic``, ``p_value``, ``rank_biserial`` (``(R+ - R-) / (R+ + R-)``
        over the non-zero differences), ``n`` (non-zero pairs actually tested)
        and ``n_ties`` (pairs whose difference is exactly zero). When every
        difference is zero the test is undefined and the row reports
        ``p_value = 1.0``, ``rank_biserial = 0.0``.

    Raises
    ------
    TkdeStatsError
        If the two sequences differ in length or are empty.
    """
    first = _as_1d(a, "a")
    second = _as_1d(b, "b")
    if first.size != second.size:
        raise TkdeStatsError(f"a has {first.size} entries, b has {second.size}")
    if first.size == 0:
        raise TkdeStatsError("wilcoxon_paired needs at least one pair")

    differences = first - second
    non_zero = differences[differences != 0.0]
    n_ties = int(differences.size - non_zero.size)

    if non_zero.size == 0:
        return {
            "statistic": 0.0,
            "p_value": 1.0,
            "rank_biserial": 0.0,
            "n": 0,
            "n_ties": n_ties,
        }

    from scipy.stats import rankdata, wilcoxon

    ranks = rankdata(np.abs(non_zero))
    positive = float(ranks[non_zero > 0].sum())
    negative = float(ranks[non_zero < 0].sum())
    total = positive + negative
    rank_biserial = (positive - negative) / total if total else 0.0

    result = wilcoxon(first, second, alternative=alternative, zero_method="wilcox")
    return {
        "statistic": float(result.statistic),
        "p_value": float(result.pvalue),
        "rank_biserial": float(rank_biserial),
        "n": int(non_zero.size),
        "n_ties": n_ties,
    }


def holm(p_values: Sequence[float], *, alpha: float = 0.05) -> list[dict[str, Any]]:
    """Holm-Bonferroni correction across one table's family of tests.

    Parameters
    ----------
    p_values : Sequence[float]
        Raw p-values, one per test in the family.
    alpha : float, optional
        Family-wise error rate. Default 0.05.

    Returns
    -------
    list[dict]
        One row per input, in input order, with ``index``, ``p_raw``,
        ``p_holm`` and ``reject``.
    """
    from experiments.analysis.stats import holm_bonferroni

    result = holm_bonferroni(list(p_values), alpha=alpha)
    return [
        {
            "index": index,
            "p_raw": float(raw),
            "p_holm": float(adjusted),
            "reject": bool(rejected),
        }
        for index, (raw, adjusted, rejected) in enumerate(
            zip(p_values, result.adjusted_p_values, result.rejected, strict=True)
        )
    ]


def paired_family(
    ours: Sequence[float],
    others: Mapping[str, Sequence[float]],
    *,
    alternative: str = "two-sided",
) -> list[dict[str, Any]]:
    """Compare ours against every competitor on the same replications.

    The family for the Holm correction is exactly the competitors of one table
    (``DESIGN.md`` G5), so the correction happens here and not at the call site.

    Parameters
    ----------
    ours : Sequence[float]
        Our replication-level scores.
    others : Mapping[str, Sequence[float]]
        Competitor name to its scores on the *same* replications, same order.
    alternative : {"two-sided", "greater", "less"}, optional
        Passed through to :func:`wilcoxon_paired`.

    Returns
    -------
    list[dict]
        One row per competitor, in the mapping's order, with ``name``, ``n``,
        ``mean_ours``, ``mean_other``, ``diff_ci`` (BCa interval of the paired
        differences, as a mapping), ``p_raw``, ``p_holm``, ``reject`` and
        ``rank_biserial``.

    Raises
    ------
    TkdeStatsError
        If any competitor's scores differ in length from ``ours``.
    """
    our_scores = _as_1d(ours, "ours")
    rows: list[dict[str, Any]] = []
    for name, values in others.items():
        their_scores = _as_1d(values, name)
        if their_scores.size != our_scores.size:
            raise TkdeStatsError(
                f"{name} has {their_scores.size} scores, ours has {our_scores.size}"
            )
        test = wilcoxon_paired(our_scores, their_scores, alternative=alternative)
        difference_ci = bca_ci(our_scores - their_scores, stat="mean")
        rows.append(
            {
                "name": name,
                "n": int(our_scores.size),
                "mean_ours": float(np.mean(our_scores)),
                "mean_other": float(np.mean(their_scores)),
                "diff_ci": difference_ci.as_dict(),
                "p_raw": test["p_value"],
                "rank_biserial": test["rank_biserial"],
            }
        )

    for row, correction in zip(rows, holm([r["p_raw"] for r in rows]), strict=True):
        row["p_holm"] = correction["p_holm"]
        row["reject"] = correction["reject"]
    return rows


# ---------------------------------------------------------------------------
# Unpaired effect size and correlation
# ---------------------------------------------------------------------------


def cliffs_delta(
    a: Sequence[float],
    b: Sequence[float],
    *,
    n_resamples: int = 2_000,
    seed: int = 0,
) -> Interval:
    """Cliff's delta between two independent samples, with a bootstrap interval.

    ``delta = (#{a > b} - #{a < b}) / (|a| * |b|)`` in ``[-1, 1]``: +1 when every
    ``a`` exceeds every ``b``, 0 under stochastic equality. Used for the regime
    and stratum contrasts, where the two groups are not paired.

    Parameters
    ----------
    a, b : Sequence[float]
        The two samples; they need not have the same length.
    n_resamples : int, optional
        Percentile-bootstrap replicates (both samples resampled
        independently). Default 2 000.
    seed : int, optional
        Bootstrap RNG seed.

    Returns
    -------
    Interval
        ``method`` is ``"cliffs_delta_percentile_bootstrap"``; ``n`` is
        ``|a| + |b|``.

    Raises
    ------
    TkdeStatsError
        If either sample is empty.
    """
    first = _as_1d(a, "a")
    second = _as_1d(b, "b")
    if first.size == 0 or second.size == 0:
        raise TkdeStatsError("cliffs_delta needs both samples non-empty")

    point = _cliffs_delta_point(first, second)
    rng = np.random.default_rng(seed)
    replicates = np.empty(n_resamples, dtype=np.float64)
    for index in range(n_resamples):
        resampled_a = rng.choice(first, size=first.size, replace=True)
        resampled_b = rng.choice(second, size=second.size, replace=True)
        replicates[index] = _cliffs_delta_point(resampled_a, resampled_b)

    low, high = np.percentile(replicates, [2.5, 97.5])
    return Interval(
        point=point,
        low=float(low),
        high=float(high),
        method="cliffs_delta_percentile_bootstrap",
        n=int(first.size + second.size),
    )


def spearman_ci(
    x: Sequence[float],
    y: Sequence[float],
    *,
    clusters: Sequence[Hashable] | None = None,
    n_resamples: int = 1_000,
    seed: int = 0,
) -> Interval:
    """Spearman rho with a percentile bootstrap interval, clustered on request.

    When several observations come from one base object -- the ladders built
    off one knowledge base, the corruptions of one member -- they are not
    independent, and an i.i.d. bootstrap understates the interval. Passing
    ``clusters`` resamples whole clusters instead, which is the interval
    ``DESIGN.md`` G5 asks for.

    Parameters
    ----------
    x, y : Sequence[float]
        Paired observations of equal length.
    clusters : Sequence[Hashable] or None, optional
        Cluster id per observation. ``None`` resamples observations i.i.d.
    n_resamples : int, optional
        Bootstrap replicates. Default 1 000.
    seed : int, optional
        Bootstrap RNG seed.

    Returns
    -------
    Interval
        ``method`` is ``"spearman_cluster_bootstrap"`` or
        ``"spearman_percentile_bootstrap"``. Replicates in which either
        resampled variable is constant are dropped (rho is undefined there) and
        the surviving count is not the ``n`` field, which stays the number of
        observations.

    Raises
    ------
    TkdeStatsError
        If the inputs differ in length, hold fewer than three observations, or
        ``clusters`` does not match them in length.
    """
    first = _as_1d(x, "x")
    second = _as_1d(y, "y")
    if first.size != second.size:
        raise TkdeStatsError(f"x has {first.size} entries, y has {second.size}")
    if first.size < 3:
        raise TkdeStatsError("spearman_ci needs at least three observations")
    if clusters is not None and len(clusters) != first.size:
        raise TkdeStatsError(f"clusters has {len(clusters)} entries, x has {first.size}")

    from scipy.stats import spearmanr

    point = float(spearmanr(first, second).statistic)

    rng = np.random.default_rng(seed)
    if clusters is None:
        method = "spearman_percentile_bootstrap"
        index_groups = [np.array([i]) for i in range(first.size)]
    else:
        method = "spearman_cluster_bootstrap"
        grouped: dict[Hashable, list[int]] = {}
        for position, cluster in enumerate(clusters):
            grouped.setdefault(cluster, []).append(position)
        index_groups = [np.asarray(v, dtype=np.int64) for v in grouped.values()]

    n_groups = len(index_groups)
    replicates: list[float] = []
    for _ in range(n_resamples):
        drawn = rng.integers(0, n_groups, size=n_groups)
        picked = np.concatenate([index_groups[g] for g in drawn])
        sample_x = first[picked]
        sample_y = second[picked]
        if np.all(sample_x == sample_x[0]) or np.all(sample_y == sample_y[0]):
            continue
        value = float(spearmanr(sample_x, sample_y).statistic)
        if math.isfinite(value):
            replicates.append(value)

    if not replicates:
        return Interval(point=point, low=point, high=point, method=method, n=int(first.size))
    low, high = np.percentile(replicates, [2.5, 97.5])
    return Interval(point=point, low=float(low), high=float(high), method=method, n=int(first.size))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _bootstrap_bounds(
    values: np.ndarray,
    statistic: Any,
    n_resamples: int,
    seed: int,
    method: str,
) -> tuple[float, float]:
    """Return the ``(low, high)`` bounds of one ``scipy.stats.bootstrap`` call."""
    from scipy import stats as scipy_stats

    result = scipy_stats.bootstrap(
        (values,),
        statistic,
        n_resamples=n_resamples,
        confidence_level=DEFAULT_CONFIDENCE,
        method=method,
        random_state=seed,
    )
    return float(result.confidence_interval.low), float(result.confidence_interval.high)


def _cliffs_delta_point(a: np.ndarray, b: np.ndarray) -> float:
    """Cliff's delta via the Mann-Whitney U statistic (ties count as one half)."""
    from scipy.stats import mannwhitneyu

    u_statistic = float(mannwhitneyu(a, b, alternative="two-sided").statistic)
    return 2.0 * u_statistic / (a.size * b.size) - 1.0


def _as_1d(values: Sequence[float] | np.ndarray, what: str) -> np.ndarray:
    """Return ``values`` as a 1-D float array, or raise naming the argument."""
    array = np.asarray(values, dtype=float).ravel()
    if array.ndim != 1:  # pragma: no cover - ravel guarantees this
        raise TkdeStatsError(f"{what} must be one-dimensional")
    return array


__all__ = [
    "Interval",
    "bca_ci",
    "cliffs_delta",
    "holm",
    "paired_family",
    "spearman_ci",
    "wilcoxon_paired",
    "wilson_ci",
]
