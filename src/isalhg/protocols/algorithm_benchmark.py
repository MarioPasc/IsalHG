"""Algorithm-comparison protocol -- algorithm-benchmark.

Per ``(backend, dataset, seed)`` triple, iterates every
:class:`DatasetItem` and records, for each item:

- raw wall-clock samples (``repeats`` calls) plus their median + IQR;
- peak RSS delta;
- the canonical fingerprint string (hex-encoded UTF-8) for cross-algorithm
  equality joins downstream;
- a token-kind count breakdown (``V``, ``C``, ``N``, ``P``, ``W``);
- ``roundtrip_ok`` -- did ``S2H(serialize(H2S(H))) ~ H`` hold;
- ``iso_invariance_ok`` -- did ``fingerprint(H) == fingerprint(permute(H, sigma))``
  for a deterministically seeded sigma;
- DNF flag and reason on timeout/exception.

Measurement schema (``ProtocolResult.measurements``)
----------------------------------------------------

::

    {
      "n_items": int,
      "n_dnf": int,
      "repeats": int,
      "timeout_s": float,
      "median_time_s": float | None,        # median of per-item medians
      "iqr_time_s": float | None,           # median of per-item IQRs
      "peak_rss_bytes": int | None,         # max over items
      "n_roundtrip_checked": int,
      "n_roundtrip_failures": int,
      "n_iso_invariance_checked": int,
      "n_iso_invariance_failures": int,
      "dnf_items": list[dict],
      "per_item": [
        {"item_id": str, "n_nodes": int, "n_edges": int, "max_arity": int,
         "wall_times_s": list[float], "median_time_s": float | None,
         "iqr_time_s": float | None, "peak_rss_bytes": int | None,
         "fingerprint_hex": str | None, "fp_bytes_length": int | None,
         "token_counts": dict[str, int] | None,
         "roundtrip_ok": bool | None, "iso_invariance_ok": bool | None,
         "dnf": bool, "dnf_reason": str | None}
      ],
    }

The downstream aggregator joins per-item records on
``(dataset_params, seed, item_id)`` across the per-algorithm output
subfolders to compute the cross-algorithm canonical-equivalence table.
"""

from __future__ import annotations

import logging
import random
import signal
import statistics
import time
from typing import Any

from isalhg.core.instructions import TokenC, TokenN, TokenP, TokenV, TokenW, parse, serialize
from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.core.string_to_hypergraph import StringToHypergraph
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


_TOKEN_NAME_BY_TYPE = {
    TokenV: "V",
    TokenC: "C",
    TokenN: "N",
    TokenP: "P",
    TokenW: "W",
}


def _count_tokens(fingerprint_str: str) -> dict[str, int]:
    """Parse ``fingerprint_str`` and return ``{kind: count}`` over V/C/N/P/W."""
    counts = {"V": 0, "C": 0, "N": 0, "P": 0, "W": 0}
    tokens = parse(fingerprint_str)
    for t in tokens:
        for cls, kind in _TOKEN_NAME_BY_TYPE.items():
            if isinstance(t, cls):
                counts[kind] += 1
                break
    return counts


def _roundtrip_ok(
    H: SparseHypergraph,
    fingerprint_str: str,
    k_value: int,
    backend: IsoBackend,
) -> bool:
    """Parse the fingerprint, replay through S2H, compare to ``H`` via backend.

    Returns ``False`` on any parse / replay / iso failure.
    """
    try:
        tokens = parse(fingerprint_str)
        interp = StringToHypergraph(
            tuple(tokens),
            k=k_value,
            n_vertex_labels=H.n_vertex_labels,
            n_edge_labels=H.n_edge_labels,
        )
        H_round, _ = interp.run()
        return bool(backend.are_isomorphic(H, H_round))
    except Exception as exc:  # noqa: BLE001 - record-and-return
        logger.debug("roundtrip check failed: %s", exc)
        return False


def _iso_invariance_ok(
    H: SparseHypergraph,
    fingerprint_bytes: bytes,
    seed: Seed,
    item_index: int,
    backend: IsoBackend,
) -> bool:
    """Permute H with a deterministic sigma, fingerprint it, compare bytes."""
    try:
        rng = random.Random((int(seed) << 16) ^ item_index)
        sigma = list(range(H.n_nodes))
        rng.shuffle(sigma)
        H_pi = permute(H, sigma)
        fp_pi = backend.fingerprint(H_pi)
        return fp_pi == fingerprint_bytes
    except Exception as exc:  # noqa: BLE001 - record-and-return
        logger.debug("iso-invariance check failed: %s", exc)
        return False


class AlgorithmBenchmarkProtocol(BenchmarkProtocol):
    """Per-item algorithm comparison: speed + memory + canonicality."""

    def __init__(
        self,
        *,
        timeout_s: float = 600.0,
        repeats: int = 5,
        check_roundtrip: bool = True,
        check_iso_invariance: bool = True,
        store_fingerprint_bytes: bool = True,
        n_workers: int = 1,  # noqa: ARG002 - reserved for future parallelism
    ) -> None:
        if timeout_s <= 0:
            raise ValueError(f"timeout_s must be > 0; got {timeout_s}")
        if repeats < 1:
            raise ValueError(f"repeats must be >= 1; got {repeats}")
        self._timeout_s = float(timeout_s)
        self._repeats = int(repeats)
        self._check_roundtrip = bool(check_roundtrip)
        self._check_iso_invariance = bool(check_iso_invariance)
        self._store_fingerprint_bytes = bool(store_fingerprint_bytes)
        self._n_workers = max(1, int(n_workers))

    @property
    def name(self) -> ProtocolName:
        return "algorithm_benchmark"

    def measure(
        self,
        backend: IsoBackend,
        dataset: HypergraphDataset,
        seed: Seed,
    ) -> ProtocolResult:
        items = list(dataset.seed(seed))
        per_item: list[dict[str, Any]] = []
        dnf_items: list[dict[str, Any]] = []
        roundtrip_checked = 0
        roundtrip_failures = 0
        iso_checked = 0
        iso_failures = 0

        total_start = time.perf_counter()
        for idx, item in enumerate(items):
            row = self._measure_item(backend, item, idx, seed)
            per_item.append(row)
            if row["dnf"]:
                dnf_items.append(
                    {
                        "item_id": item.item_id,
                        "exception": row["dnf_reason"],
                    }
                )
            if row["roundtrip_ok"] is not None:
                roundtrip_checked += 1
                if not row["roundtrip_ok"]:
                    roundtrip_failures += 1
            if row["iso_invariance_ok"] is not None:
                iso_checked += 1
                if not row["iso_invariance_ok"]:
                    iso_failures += 1

        wall_clock_s = time.perf_counter() - total_start

        good_medians = [r["median_time_s"] for r in per_item if r["median_time_s"] is not None]
        good_iqrs = [r["iqr_time_s"] for r in per_item if r["iqr_time_s"] is not None]
        good_rss = [r["peak_rss_bytes"] for r in per_item if r["peak_rss_bytes"] is not None]
        agg_median = float(statistics.median(good_medians)) if good_medians else None
        agg_iqr = float(statistics.median(good_iqrs)) if good_iqrs else None
        agg_rss = int(max(good_rss)) if good_rss else None

        measurements: dict[str, Any] = {
            "n_items": len(items),
            "n_dnf": len(dnf_items),
            "repeats": self._repeats,
            "timeout_s": self._timeout_s,
            "median_time_s": agg_median,
            "iqr_time_s": agg_iqr,
            "peak_rss_bytes": agg_rss,
            "n_roundtrip_checked": roundtrip_checked,
            "n_roundtrip_failures": roundtrip_failures,
            "n_iso_invariance_checked": iso_checked,
            "n_iso_invariance_failures": iso_failures,
            "dnf_items": dnf_items,
            "per_item": per_item,
        }

        logger.info(
            "algorithm_benchmark %s/%s seed=%d: items=%d dnf=%d rt_fail=%d/%d "
            "iso_fail=%d/%d median=%s wall=%.3fs",
            backend.name,
            dataset.name,
            seed,
            len(items),
            len(dnf_items),
            roundtrip_failures,
            roundtrip_checked,
            iso_failures,
            iso_checked,
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
    # Per-item measurement
    # ------------------------------------------------------------------

    def _measure_item(
        self,
        backend: IsoBackend,
        item: Any,
        idx: int,
        seed: Seed,
    ) -> dict[str, Any]:
        H = item.hypergraph
        max_arity = max((len(H.members(e)) for e in H.edges()), default=0) if H.n_edges else 0
        row: dict[str, Any] = {
            "item_id": item.item_id,
            "n_nodes": H.n_nodes,
            "n_edges": H.n_edges,
            "max_arity": max_arity,
            "wall_times_s": [],
            "median_time_s": None,
            "iqr_time_s": None,
            "peak_rss_bytes": None,
            "fingerprint_hex": None,
            "fp_bytes_length": None,
            "token_counts": None,
            "roundtrip_ok": None,
            "iso_invariance_ok": None,
            "dnf": False,
            "dnf_reason": None,
        }

        timing_results = None
        old_handler = signal.signal(signal.SIGALRM, _raise_timeout)
        try:
            signal.alarm(int(max(1.0, self._timeout_s)))
            try:
                H_local = H

                def _call() -> Any:
                    return backend.fingerprint(H_local)  # noqa: B023 - one-shot

                timing_results = time_call_repeated(_call, repeats=self._repeats)
            finally:
                signal.alarm(0)
        except _TimeoutError:
            row["dnf"] = True
            row["dnf_reason"] = "TimeoutError"
            logger.warning(
                "DNF: %s on %s (timeout=%.1fs)",
                backend.name,
                item.item_id,
                self._timeout_s,
            )
            return row
        except Exception as exc:  # noqa: BLE001
            row["dnf"] = True
            row["dnf_reason"] = type(exc).__name__
            logger.warning(
                "DNF: %s on %s (%s: %s)",
                backend.name,
                item.item_id,
                type(exc).__name__,
                exc,
            )
            return row
        finally:
            signal.signal(signal.SIGALRM, old_handler)

        if timing_results is None:
            row["dnf"] = True
            row["dnf_reason"] = "NoTimingResults"
            return row

        row["wall_times_s"] = [r.wall_clock_s for r in timing_results]
        row["median_time_s"] = median_wall_clock_s(timing_results)
        row["iqr_time_s"] = iqr_wall_clock_s(timing_results)
        row["peak_rss_bytes"] = peak_rss(timing_results)
        fp_bytes: bytes = timing_results[0].value
        row["fp_bytes_length"] = len(fp_bytes)
        try:
            fp_str = fp_bytes.decode("utf-8")
        except UnicodeDecodeError:
            fp_str = ""
        if self._store_fingerprint_bytes:
            row["fingerprint_hex"] = fp_bytes.hex()
        if fp_str:
            try:
                row["token_counts"] = _count_tokens(fp_str)
            except Exception as exc:  # noqa: BLE001
                logger.debug("token count parse failed on %s: %s", item.item_id, exc)
                row["token_counts"] = None

        # Roundtrip + iso-invariance checks.
        k_value = max(2, max_arity)
        if self._check_roundtrip and fp_str:
            row["roundtrip_ok"] = _roundtrip_ok(H, fp_str, k_value, backend)
        if self._check_iso_invariance:
            row["iso_invariance_ok"] = _iso_invariance_ok(H, fp_bytes, seed, idx, backend)
        return row


def _factory(params: dict[str, Any]) -> BenchmarkProtocol:
    return AlgorithmBenchmarkProtocol(
        timeout_s=float(params.get("timeout_s", 600.0)),
        repeats=int(params.get("repeats", 5)),
        check_roundtrip=bool(params.get("check_roundtrip", True)),
        check_iso_invariance=bool(params.get("check_iso_invariance", True)),
        store_fingerprint_bytes=bool(params.get("store_fingerprint_bytes", True)),
        n_workers=int(params.get("n_workers", 1)),
    )


register_protocol("algorithm_benchmark", _factory)


# Suppress unused-import warning for `serialize`; it is referenced in the
# docstring as the canonical replay path even though we only use `parse`.
_ = serialize
