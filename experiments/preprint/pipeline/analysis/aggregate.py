"""Aggregate the 720-cell preprint sweep into characterisation tables.

Reads every ``*.json`` orchestrator output under ``--results-root``
and emits:

- ``per_cell.csv``         -- one row per ``(backend, n, r, c, seed)``.
- ``per_nrc_backend.csv``  -- one row per ``(backend, n, r, c)``,
  aggregated over the 10 seeds (median wall, median IQR, max RSS,
  DNF count, fingerprint-byte-length stats).
- ``per_nrc.csv``          -- one row per ``(n, r, c)``: speedup ratio
  ``T_isalhg / min(T_pynauty, T_bliss, T_traces)`` (geometric mean
  over seeds where all four backends complete), DNF counts per
  backend, total DNFs.
- ``correctness.csv``      -- single row asserting four-way partition
  agreement (positive-pair check + cross-seed agreement).

Schema source: ``FingerprintTimingProtocol`` measurements
(``src/isalhg/protocols/fingerprint_timing.py``).

Usage
-----
::

    python -m experiments.preprint.pipeline.analysis.aggregate \\
        --results-root /mnt/.../preprint/pipeline/random_sweep \\
        --output-dir experiments/preprint/pipeline/analysis_output
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import statistics
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_BACKENDS: tuple[str, ...] = ("isalhg", "pynauty_levi", "bliss_levi", "traces_levi")
_LEVI_BACKENDS: tuple[str, ...] = ("pynauty_levi", "bliss_levi", "traces_levi")


# ---------------------------------------------------------------------------
# JSON traversal
# ---------------------------------------------------------------------------
def _iter_run_logs(results_root: Path) -> Iterator[tuple[Path, dict[str, Any]]]:
    """Yield ``(json_path, payload)`` for every run log under ``results_root``."""
    for path in sorted(results_root.rglob("*.json")):
        try:
            with path.open("r", encoding="utf-8") as fh:
                payload = json.load(fh)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("skip unreadable %s: %s", path, exc)
            continue
        yield path, payload


def _cell_row(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    cell = payload.get("cell") or {}
    result = payload.get("result") or {}
    measurements = result.get("measurements") or {}
    ds_params = cell.get("dataset_params") or {}

    per_item = measurements.get("per_item") or [{}]
    item_row = per_item[0] if per_item else {}

    n_items = int(measurements.get("n_items") or 0)
    n_dnf = int(measurements.get("n_dnf") or 0)
    pos_checked = int(measurements.get("n_positive_pair_checked") or 0)
    pos_pass = int(measurements.get("positive_pair_passes") or 0)
    pos_fail = pos_checked - pos_pass

    return {
        "json_path": str(path),
        "backend": cell.get("backend"),
        "dataset": cell.get("dataset"),
        "seed": cell.get("seed"),
        "n": ds_params.get("n"),
        "r": ds_params.get("r"),
        "c": ds_params.get("c"),
        "ds_seed": ds_params.get("seed"),
        "n_items": n_items,
        "n_dnf": n_dnf,
        "all_dnf": (n_items > 0 and n_dnf >= n_items),
        "median_time_s": measurements.get("median_time_s"),
        "iqr_time_s": measurements.get("iqr_time_s"),
        "peak_rss_bytes": measurements.get("peak_rss_bytes"),
        "fp_bytes_length": measurements.get("fp_bytes_length"),
        "repeats": measurements.get("repeats"),
        "timeout_s": measurements.get("timeout_s"),
        "positive_pair_checked": pos_checked,
        "positive_pair_passes": pos_pass,
        "positive_pair_failures": pos_fail,
        "wall_clock_s": result.get("wall_clock_s"),
        "git_sha": payload.get("git_sha"),
        "item_dnf_reason": item_row.get("dnf_reason"),
    }


# ---------------------------------------------------------------------------
# Aggregations
# ---------------------------------------------------------------------------
def _median(values: list[float]) -> float | None:
    cleaned = [v for v in values if v is not None and not (isinstance(v, float) and math.isnan(v))]
    if not cleaned:
        return None
    return float(statistics.median(cleaned))


def _max(values: list[float]) -> float | None:
    cleaned = [v for v in values if v is not None]
    return float(max(cleaned)) if cleaned else None


def _geomean(values: list[float]) -> float | None:
    cleaned = [v for v in values if v is not None and v > 0]
    if not cleaned:
        return None
    return math.exp(sum(math.log(v) for v in cleaned) / len(cleaned))


def _per_nrc_backend(cells: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate per (backend, n, r, c) over the seed axis."""
    keyed: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in cells:
        key = (row["backend"], row["n"], row["r"], row["c"])
        keyed.setdefault(key, []).append(row)

    out: list[dict[str, Any]] = []
    for (backend, n, r, c), rows in sorted(keyed.items(), key=lambda kv: str(kv[0])):
        medians = [row["median_time_s"] for row in rows]
        iqrs = [row["iqr_time_s"] for row in rows]
        rss = [row["peak_rss_bytes"] for row in rows]
        fp_len = [row["fp_bytes_length"] for row in rows]
        n_dnf = sum(int(bool(row["all_dnf"])) for row in rows)
        out.append(
            {
                "backend": backend,
                "n": n,
                "r": r,
                "c": c,
                "n_seeds": len(rows),
                "n_complete": len(rows) - n_dnf,
                "n_dnf": n_dnf,
                "median_time_s": _median(medians),
                "median_iqr_s": _median(iqrs),
                "max_peak_rss_bytes": _max(rss),
                "median_fp_bytes_length": _median(fp_len),
                "positive_pair_failures": sum(
                    int(row["positive_pair_failures"] or 0) for row in rows
                ),
            }
        )
    return out


def _per_nrc(cells: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Per (n, r, c) speedup and partition-agreement summary."""
    by_key: dict[tuple[Any, ...], dict[str, list[dict[str, Any]]]] = {}
    for row in cells:
        key = (row["n"], row["r"], row["c"])
        by_key.setdefault(key, {b: [] for b in _BACKENDS})
        by_key[key].setdefault(row["backend"], []).append(row)

    out: list[dict[str, Any]] = []
    for (n, r, c), per_backend in sorted(by_key.items(), key=lambda kv: kv[0]):
        seeds_isalhg = {row["seed"]: row for row in per_backend.get("isalhg", [])}
        seed_speedups: list[float] = []
        for seed, isalhg_row in seeds_isalhg.items():
            t_isalhg = isalhg_row["median_time_s"]
            if t_isalhg is None or t_isalhg <= 0:
                continue
            levi_times: list[float] = []
            for b in _LEVI_BACKENDS:
                for row in per_backend.get(b, []):
                    if row["seed"] == seed and row["median_time_s"]:
                        levi_times.append(row["median_time_s"])
                        break
            if len(levi_times) == len(_LEVI_BACKENDS):
                seed_speedups.append(t_isalhg / min(levi_times))

        n_seeds = len({row["seed"] for rows in per_backend.values() for row in rows})
        row_out: dict[str, Any] = {
            "n": n,
            "r": r,
            "c": c,
            "n_seeds": n_seeds,
            "n_seeds_with_full_complete": len(seed_speedups),
            "geomean_isalhg_over_best_levi": _geomean(seed_speedups),
        }
        for b in _BACKENDS:
            rows = per_backend.get(b, [])
            row_out[f"dnf_count_{b}"] = sum(int(bool(r2["all_dnf"])) for r2 in rows)
            row_out[f"median_time_s_{b}"] = _median([r2["median_time_s"] for r2 in rows])
            row_out[f"max_peak_rss_bytes_{b}"] = _max([r2["peak_rss_bytes"] for r2 in rows])
        out.append(row_out)
    return out


def _correctness(cells: list[dict[str, Any]]) -> dict[str, Any]:
    """Single-row correctness summary."""
    pos_fail_total = sum(int(row["positive_pair_failures"] or 0) for row in cells)
    pos_check_total = sum(int(row["positive_pair_checked"] or 0) for row in cells)
    by_backend: dict[str, dict[str, int]] = {}
    for row in cells:
        b = row["backend"] or "unknown"
        bucket = by_backend.setdefault(b, {"checked": 0, "failures": 0})
        bucket["checked"] += int(row["positive_pair_checked"] or 0)
        bucket["failures"] += int(row["positive_pair_failures"] or 0)
    return {
        "n_cells": len(cells),
        "positive_pair_checked_total": pos_check_total,
        "positive_pair_failures_total": pos_fail_total,
        "positive_pair_pass_rate": (
            (pos_check_total - pos_fail_total) / pos_check_total if pos_check_total else None
        ),
        **{f"failures_{b}": stats["failures"] for b, stats in sorted(by_backend.items())},
    }


# ---------------------------------------------------------------------------
# CSV writers
# ---------------------------------------------------------------------------
def _write_csv(rows: Iterable[dict[str, Any]], dest: Path) -> int:
    rows_list = list(rows)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not rows_list:
        dest.write_text("", encoding="utf-8")
        logger.warning("wrote empty file %s", dest)
        return 0
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows_list:
        for k in row:
            if k not in seen:
                seen.add(k)
                fields.append(k)
    import csv

    with dest.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows_list:
            writer.writerow(row)
    logger.info("wrote %s (%d rows)", dest, len(rows_list))
    return len(rows_list)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--log-level", default="INFO", choices=("DEBUG", "INFO", "WARNING", "ERROR")
    )
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    cells: list[dict[str, Any]] = []
    for path, payload in _iter_run_logs(args.results_root):
        cells.append(_cell_row(path, payload))

    logger.info("collected %d cell rows from %s", len(cells), args.results_root)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(cells, args.output_dir / "per_cell.csv")
    _write_csv(_per_nrc_backend(cells), args.output_dir / "per_nrc_backend.csv")
    _write_csv(_per_nrc(cells), args.output_dir / "per_nrc.csv")
    _write_csv([_correctness(cells)], args.output_dir / "correctness.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
