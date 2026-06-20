"""Unit tests for :mod:`isalhg.metrics.runtime`."""

from __future__ import annotations

import math
import time

import pytest

from isalhg.metrics.runtime import (
    TimedResult,
    iqr_wall_clock_s,
    median_wall_clock_s,
    peak_rss,
    time_call,
    time_call_repeated,
)

pytestmark = pytest.mark.unit


class TestTimeCall:
    def test_returns_value(self) -> None:
        r = time_call(lambda: 42)
        assert r.value == 42

    def test_wall_clock_non_negative_and_sane(self) -> None:
        def sleeper() -> None:
            time.sleep(0.01)

        r = time_call(sleeper)
        assert r.wall_clock_s >= 0.005  # generous lower bound for jitter
        assert r.wall_clock_s < 5.0

    def test_peak_rss_non_negative(self) -> None:
        r = time_call(lambda: [0] * 1000)
        assert r.peak_rss_bytes >= 0


class TestTimeCallRepeated:
    def test_repeats_count(self) -> None:
        results = time_call_repeated(lambda: 1, repeats=5)
        assert len(results) == 5
        assert all(isinstance(r, TimedResult) for r in results)
        assert all(r.value == 1 for r in results)

    def test_rejects_non_positive_repeats(self) -> None:
        with pytest.raises(ValueError, match="repeats must be"):
            time_call_repeated(lambda: 1, repeats=0)


def _stub_results(walls: list[float], rsses: list[int]) -> list[TimedResult[None]]:
    return [
        TimedResult(value=None, wall_clock_s=w, peak_rss_bytes=r)
        for w, r in zip(walls, rsses, strict=True)
    ]


class TestAggregates:
    def test_median(self) -> None:
        results = _stub_results([1.0, 2.0, 3.0, 4.0, 5.0], [0, 0, 0, 0, 0])
        assert median_wall_clock_s(results) == 3.0

    def test_iqr_inclusive(self) -> None:
        # statistics.quantiles([1..5], n=4, method='inclusive') -> [2.0, 3.0, 4.0]
        # IQR = Q3 - Q1 = 4.0 - 2.0 = 2.0
        results = _stub_results([1.0, 2.0, 3.0, 4.0, 5.0], [0] * 5)
        assert math.isclose(iqr_wall_clock_s(results), 2.0)

    def test_iqr_single_sample_returns_zero(self) -> None:
        results = _stub_results([7.0], [0])
        assert iqr_wall_clock_s(results) == 0.0

    def test_peak_rss_max(self) -> None:
        results = _stub_results([0.1] * 3, [10, 50, 30])
        assert peak_rss(results) == 50

    def test_median_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="at least one"):
            median_wall_clock_s([])

    def test_peak_rss_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="at least one"):
            peak_rss([])
