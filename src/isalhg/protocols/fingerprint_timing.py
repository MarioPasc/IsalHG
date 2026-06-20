"""Fingerprint + timing protocol -- Tier 2 / preprint.

Per ``(backend, dataset, seed)`` triple, the protocol iterates over every
``DatasetItem`` in the dataset and:

1. Computes ``backend.fingerprint(H)`` ``repeats`` times under a
   :func:`signal.alarm` watchdog (POSIX). The median wall-clock + IQR
   summarises the per-item runtime; the maximum ``peak_rss`` is the
   per-item memory cost.
2. Captures ``len(fingerprint_bytes)`` from one non-timing call to
   produce the per-backend fingerprint-length distribution.
3. Optionally runs a positive-pair correctness check
   (``check_positive_pair=True``): builds a random permutation ``σ``
   seeded by the cell seed + item position, applies
   :func:`isalhg.core.sparse_hypergraph.permute`, and asserts
   ``backend.are_isomorphic(H, σ(H)) is True``. Failures are recorded
   in the ``positive_pair_failures`` list and do NOT raise — the
   protocol is a measurement, not an assertion.
4. Items that exceed ``timeout_s`` (or raise) are recorded as DNF in
   ``dnf_items`` rather than aborting the cell.

Measurement schema (``ProtocolResult.measurements``)
----------------------------------------------------

::

    {
      "n_items": int,
      "n_dnf": int,
      "n_positive_pair_checked": int,
      "median_time_s": float | None,        # None iff every item DNF
      "iqr_time_s": float | None,
      "peak_rss_bytes": int | None,
      "fp_bytes_length": int | None,        # of the first non-DNF item
      "repeats": int,
      "timeout_s": float,
      "positive_pair_passes": int,
      "positive_pair_failures": list[dict], # [{item_id, reason}]
      "dnf_items": list[dict],              # [{item_id, exception, wall_s}]
      "per_item": [
        {"item_id": str, "median_time_s": float | None,
         "iqr_time_s": float | None, "peak_rss_bytes": int | None,
         "fp_bytes_length": int | None, "positive_pair_ok": bool | None,
         "dnf": bool, "dnf_reason": str | None}
      ],
    }

This shape is stable across the preprint cohort (``n_items = 1`` per
cell) and the full-paper datasets that yield many items per cell;
analysis code keys on these names regardless of ``n_items``.
"""

from __future__ import annotations

import logging
import random
import signal
import time
from typing import Any

from isalhg.core.sparse_hypergraph import permute
from isalhg.datasets.base import HypergraphDataset
from isalhg.iso_backends.base import IsoBackend
from isalhg.metrics.runtime import (
    iqr_wall_clock_s,
    median_wall_clock_s,
    peak_rss,
    time_call_repeated,
)
from isalhg.protocols.base import BenchmarkProtocol, ProtocolResult
from isalhg.protocols.registry import register_protocol
from isalhg.types import ProtocolName, Seed

logger = logging.getLogger(__name__)


class _TimeoutError(Exception):
    """Internal sentinel for the signal.alarm watchdog."""


def _raise_timeout(signum: int, frame: Any) -> None:  # noqa: ARG001
    raise _TimeoutError()


class FingerprintTimingProtocol(BenchmarkProtocol):
    """Wall-clock + memory + correctness measurement of fingerprint computation."""

    def __init__(
        self,
        *,
        timeout_s: float = 600.0,
        repeats: int = 10,
        check_positive_pair: bool = True,
    ) -> None:
        if timeout_s <= 0:
            raise ValueError(f"timeout_s must be > 0; got {timeout_s}")
        if repeats < 1:
            raise ValueError(f"repeats must be >= 1; got {repeats}")
        self._timeout_s = float(timeout_s)
        self._repeats = int(repeats)
        self._check_positive_pair = bool(check_positive_pair)

    @property
    def name(self) -> ProtocolName:
        return "fingerprint_timing"

    def measure(
        self,
        backend: IsoBackend,
        dataset: HypergraphDataset,
        seed: Seed,
    ) -> ProtocolResult:
        items = list(dataset.seed(seed))
        per_item: list[dict[str, Any]] = []
        positive_pair_failures: list[dict[str, Any]] = []
        dnf_items: list[dict[str, Any]] = []
        positive_pair_checked = 0
        first_fp_len: int | None = None

        total_start = time.perf_counter()
        for idx, item in enumerate(items):
            H = item.hypergraph
            row: dict[str, Any] = {
                "item_id": item.item_id,
                "median_time_s": None,
                "iqr_time_s": None,
                "peak_rss_bytes": None,
                "fp_bytes_length": None,
                "positive_pair_ok": None,
                "dnf": False,
                "dnf_reason": None,
            }

            # ---- timing block (under signal.alarm watchdog) ----
            timing_results = None
            timing_wall = 0.0
            timing_start = time.perf_counter()
            old_handler = signal.signal(signal.SIGALRM, _raise_timeout)
            try:
                signal.alarm(int(max(1.0, self._timeout_s)))
                try:
                    H_local = H

                    def _call() -> Any:
                        return backend.fingerprint(H_local)  # noqa: B023 - invoked synchronously within this iteration

                    timing_results = time_call_repeated(_call, repeats=self._repeats)
                finally:
                    signal.alarm(0)
            except _TimeoutError:
                timing_wall = time.perf_counter() - timing_start
                row["dnf"] = True
                row["dnf_reason"] = "TimeoutError"
                dnf_items.append(
                    {
                        "item_id": item.item_id,
                        "exception": "TimeoutError",
                        "wall_s": timing_wall,
                    }
                )
                logger.warning(
                    "DNF: %s on %s (timeout=%.1fs)",
                    backend.name,
                    item.item_id,
                    self._timeout_s,
                )
            except Exception as exc:  # noqa: BLE001 - protocol records, never raises
                timing_wall = time.perf_counter() - timing_start
                row["dnf"] = True
                row["dnf_reason"] = type(exc).__name__
                dnf_items.append(
                    {
                        "item_id": item.item_id,
                        "exception": type(exc).__name__,
                        "wall_s": timing_wall,
                        "message": str(exc)[:200],
                    }
                )
                logger.warning(
                    "DNF: %s on %s (%s: %s)",
                    backend.name,
                    item.item_id,
                    type(exc).__name__,
                    exc,
                )
            finally:
                signal.signal(signal.SIGALRM, old_handler)

            if timing_results is not None:
                row["median_time_s"] = median_wall_clock_s(timing_results)
                row["iqr_time_s"] = iqr_wall_clock_s(timing_results)
                row["peak_rss_bytes"] = peak_rss(timing_results)
                fp_len = len(timing_results[0].value)
                row["fp_bytes_length"] = fp_len
                if first_fp_len is None:
                    first_fp_len = fp_len

            # ---- positive-pair correctness ----
            if self._check_positive_pair and not row["dnf"]:
                positive_pair_checked += 1
                ok = self._check_pair(backend, H, seed=seed, item_index=idx)
                row["positive_pair_ok"] = ok
                if not ok:
                    positive_pair_failures.append(
                        {
                            "item_id": item.item_id,
                            "reason": "are_isomorphic(H, sigma(H)) returned non-True",
                        }
                    )
                    logger.warning(
                        "positive-pair failure: %s on %s",
                        backend.name,
                        item.item_id,
                    )

            per_item.append(row)

        wall_clock_s = time.perf_counter() - total_start

        # ---- aggregate across items ----
        good_medians = [r["median_time_s"] for r in per_item if r["median_time_s"] is not None]
        good_iqrs = [r["iqr_time_s"] for r in per_item if r["iqr_time_s"] is not None]
        good_rss = [r["peak_rss_bytes"] for r in per_item if r["peak_rss_bytes"] is not None]
        agg_median = float(median_of_floats(good_medians)) if good_medians else None
        agg_iqr = float(median_of_floats(good_iqrs)) if good_iqrs else None
        agg_rss = int(max(good_rss)) if good_rss else None

        positive_pair_passes = positive_pair_checked - len(positive_pair_failures)

        measurements: dict[str, Any] = {
            "n_items": len(items),
            "n_dnf": len(dnf_items),
            "n_positive_pair_checked": positive_pair_checked,
            "median_time_s": agg_median,
            "iqr_time_s": agg_iqr,
            "peak_rss_bytes": agg_rss,
            "fp_bytes_length": first_fp_len,
            "repeats": self._repeats,
            "timeout_s": self._timeout_s,
            "positive_pair_passes": positive_pair_passes,
            "positive_pair_failures": positive_pair_failures,
            "dnf_items": dnf_items,
            "per_item": per_item,
        }

        logger.info(
            "fingerprint_timing %s/%s seed=%d: items=%d dnf=%d pos_pass=%d/%d median=%s wall=%.3fs",
            backend.name,
            dataset.name,
            seed,
            len(items),
            len(dnf_items),
            positive_pair_passes,
            positive_pair_checked,
            f"{agg_median:.4g}" if agg_median is not None else "NA",
            wall_clock_s,
        )

        return ProtocolResult(
            protocol=self.name,
            backend=backend.name,
            dataset=dataset.name,
            seed=seed,
            wall_clock_s=wall_clock_s,
            measurements=measurements,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _check_pair(
        self,
        backend: IsoBackend,
        H: Any,
        *,
        seed: Seed,
        item_index: int,
    ) -> bool:
        """Generate sigma, build H_pi, call ``backend.are_isomorphic``."""
        rng = random.Random((int(seed) << 16) ^ item_index)
        sigma = list(range(H.n_nodes))
        rng.shuffle(sigma)
        H_pi = permute(H, sigma)
        try:
            return bool(backend.are_isomorphic(H, H_pi))
        except Exception as exc:  # noqa: BLE001 - record-and-continue
            logger.warning("are_isomorphic raised on positive pair (%s): %s", backend.name, exc)
            return False


def median_of_floats(values: list[float]) -> float:
    """Median over a list of floats (single-use shim so the protocol stays stdlib)."""
    import statistics

    return float(statistics.median(values))


def _factory(params: dict[str, Any]) -> BenchmarkProtocol:
    return FingerprintTimingProtocol(
        timeout_s=float(params.get("timeout_s", 600.0)),
        repeats=int(params.get("repeats", 10)),
        check_positive_pair=bool(params.get("check_positive_pair", True)),
    )


register_protocol("fingerprint_timing", _factory)
