"""Runtime measurement helpers.

Thin wrappers over :func:`time.perf_counter` and
:func:`resource.getrusage` that isolate the timing + memory boilerplate
from the protocol bodies. The same primitives are reused by every
protocol that needs wall-clock or peak-RSS data
(``fingerprint_timing``, future ``partition_agreement`` scaling
extensions, etc.).

Caveats
-------
``resource.getrusage(RUSAGE_SELF).ru_maxrss`` reports the *parent*
process's high-water mark only. Subprocess-based backends
(``traces_levi`` -> ``dreadnaut``) therefore under-report peak memory;
the parent's RSS captures only the Levi serialisation buffer and the
b6 parsing, not the child solver. ``docs/preprint/PREPRINT.md`` §11 + the
preprint figure caption flag this limitation; a production fix using
``psutil`` child-polling is a follow-up.

On Linux ``ru_maxrss`` is reported in kilobytes; on macOS/BSD it is in
bytes. We detect the platform and normalise to bytes so downstream
consumers see a single unit.
"""

from __future__ import annotations

import platform
import resource
import statistics
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

T = TypeVar("T")

# Linux reports ru_maxrss in KiB; *BSD / macOS report bytes. The Python
# resource docs document this divergence and getconf PAGESIZE does not
# disambiguate.
_RUSAGE_FACTOR: int = 1024 if platform.system() == "Linux" else 1


def _peak_rss_bytes() -> int:
    """Return the current process's peak resident-set size in bytes."""
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * _RUSAGE_FACTOR


@dataclass(frozen=True)
class TimedResult(Generic[T]):
    """One timing sample.

    Attributes
    ----------
    value : T
        The return value of the timed callable.
    wall_clock_s : float
        Elapsed wall-clock time, from :func:`time.perf_counter` deltas.
    peak_rss_bytes : int
        Peak resident-set growth (``after - before``, clamped to
        ``>= 0``) of the parent process during the call. See module
        docstring for the subprocess caveat.
    """

    value: T
    wall_clock_s: float
    peak_rss_bytes: int


def time_call(fn: Callable[[], T]) -> TimedResult[T]:
    """Invoke ``fn`` once and record its wall-clock + peak-RSS delta.

    Parameters
    ----------
    fn : Callable[[], T]
        Zero-argument callable to measure.

    Returns
    -------
    TimedResult[T]
        ``value`` is ``fn()``'s return value verbatim.
    """
    rss_before = _peak_rss_bytes()
    t0 = time.perf_counter()
    value = fn()
    wall = time.perf_counter() - t0
    rss_after = _peak_rss_bytes()
    return TimedResult(
        value=value,
        wall_clock_s=wall,
        peak_rss_bytes=max(0, rss_after - rss_before),
    )


def time_call_repeated(fn: Callable[[], T], *, repeats: int) -> list[TimedResult[T]]:
    """Run ``fn`` ``repeats`` times, returning one :class:`TimedResult` per call.

    The protocol layer takes the median of ``wall_clock_s`` to suppress
    per-call noise and the maximum of ``peak_rss_bytes`` as the
    representative memory cost.
    """
    if repeats < 1:
        raise ValueError(f"repeats must be >= 1, got {repeats}")
    return [time_call(fn) for _ in range(repeats)]


def median_wall_clock_s(results: Sequence[TimedResult[Any]]) -> float:
    """Median of ``wall_clock_s`` across ``results``.

    Raises
    ------
    ValueError
        If ``results`` is empty.
    """
    if not results:
        raise ValueError("median_wall_clock_s requires at least one result")
    return float(statistics.median(r.wall_clock_s for r in results))


def iqr_wall_clock_s(results: Sequence[TimedResult[Any]]) -> float:
    """Interquartile range (Q3 - Q1) of ``wall_clock_s`` across ``results``.

    Returns 0.0 for fewer than two samples.
    """
    if len(results) < 2:
        return 0.0
    quartiles = statistics.quantiles((r.wall_clock_s for r in results), n=4, method="inclusive")
    return float(quartiles[2] - quartiles[0])


def peak_rss(results: Sequence[TimedResult[Any]]) -> int:
    """Maximum of ``peak_rss_bytes`` across ``results``.

    Raises
    ------
    ValueError
        If ``results`` is empty.
    """
    if not results:
        raise ValueError("peak_rss requires at least one result")
    return int(max(r.peak_rss_bytes for r in results))


__all__ = [
    "TimedResult",
    "iqr_wall_clock_s",
    "median_wall_clock_s",
    "peak_rss",
    "time_call",
    "time_call_repeated",
]
