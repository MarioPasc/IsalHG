"""Empirical complexity-fit regression.

Given runtime samples ``(n_i, m_i, r_i, t_i)`` from
:class:`FingerprintTimingProtocol`, fits the log-linear model
``log t = log c + alpha log n + beta log m + gamma log r`` and returns the
fitted coefficients with confidence intervals.

Imports SciPy lazily inside the function body to keep ``isalhg.metrics``
import-light.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class ComplexityFit:
    """Output of the ``T ~ n^alpha m^beta r^gamma`` fit."""

    alpha: float
    beta: float
    gamma: float
    log_c: float
    r_squared: float
    alpha_ci: tuple[float, float]
    beta_ci: tuple[float, float]
    gamma_ci: tuple[float, float]


def fit_power_law(
    n: Sequence[int],
    m: Sequence[int],
    r: Sequence[int],
    t: Sequence[float],
) -> ComplexityFit:
    """Fit ``log t = log c + alpha log n + beta log m + gamma log r`` by OLS."""
    raise NotImplementedError
