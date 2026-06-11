"""Paired statistical tests over backend comparisons.

Used for the runtime sweep: ``IsalHG`` versus each baseline, per
``(dataset, n, r, m/n)`` cell, with Wilcoxon signed-rank by default
(Shapiro-Wilk gate) and bootstrap CIs on the speedup ratio.

Imports SciPy lazily.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class PairedTestResult:
    """Outcome of one paired comparison."""

    statistic: float
    p_value: float
    effect_size: float
    test_used: str  # "wilcoxon" or "paired_t"


def paired_test(
    isalhg_samples: Sequence[float],
    baseline_samples: Sequence[float],
) -> PairedTestResult:
    """Wilcoxon if Shapiro-Wilk rejects, paired-t otherwise."""
    raise NotImplementedError


def bootstrap_ci(samples: Sequence[float], *, n_resamples: int = 10_000) -> tuple[float, float]:
    """Percentile bootstrap 95% CI of the mean."""
    raise NotImplementedError
