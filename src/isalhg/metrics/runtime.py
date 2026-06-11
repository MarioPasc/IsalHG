"""Runtime measurement helpers.

Thin wrappers over ``time.perf_counter`` and ``resource.getrusage`` that
isolate the measurement boilerplate from the protocol bodies.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class TimedResult(Generic[T]):
    """Pair ``(return_value, wall_clock_s, peak_rss_bytes)``."""

    value: T
    wall_clock_s: float
    peak_rss_bytes: int


def time_call(fn: Callable[[], T]) -> TimedResult[T]:
    """Invoke ``fn`` once, recording wall clock and peak RSS delta."""
    raise NotImplementedError


def time_call_repeated(fn: Callable[[], T], *, repeats: int) -> list[TimedResult[T]]:
    """Invoke ``fn`` ``repeats`` times, returning one ``TimedResult`` per call."""
    raise NotImplementedError
