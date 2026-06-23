"""Aggregate per-algorithm run logs into a single long-format DataFrame.

Reads every ``*.json`` orchestrator output across the per-algorithm
output subfolders (one folder per algorithm under ``--results-root``),
extracts the per-item rows, and writes:

- ``items.parquet`` (or ``.csv`` fallback) -- one row per
  ``(algorithm, dataset, seed, item_id)``.
- ``cells.parquet`` -- one row per ``(algorithm, dataset, seed)``.

Includes the cross-algorithm ``canonical_equivalent_with_greedy_min``
column: True iff this row's ``fingerprint_hex`` equals
``greedy_min``'s on the same ``(dataset_params, seed, item_id)``.

Usage
-----
::

    python -m experiments.preprint.algorithms.analysis.aggregate \\
        --results-root /media/.../algorithms/full \\
        --output-dir /media/.../algorithms/analysis_full
"""

from __future__ import annotations

import argparse
import json
import logging
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _iter_run_logs(results_root: Path) -> Iterator[tuple[str, Path, dict[str, Any]]]:
    """Yield ``(algorithm, json_path, payload)`` for every run log under ``results_root``."""
    for algo_dir in sorted(p for p in results_root.iterdir() if p.is_dir()):
        algorithm = algo_dir.name
        for path in sorted(algo_dir.rglob("*.json")):
            try:
                with path.open("r", encoding="utf-8") as fh:
                    payload = json.load(fh)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("skip unreadable %s: %s", path, exc)
                continue
            yield algorithm, path, payload


def _per_item_rows(
    algorithm: str,
    path: Path,
    payload: dict[str, Any],
) -> Iterator[dict[str, Any]]:
    measurements: dict[str, Any] = (payload.get("result") or {}).get("measurements", {}) or {}
    per_item: list[dict[str, Any]] = measurements.get("per_item", []) or []
    cell = payload.get("cell", {}) or {}
    result = payload.get("result", {}) or {}
    ds_params: dict[str, Any] = cell.get("dataset_params", {}) or {}
    seed = cell.get("seed", result.get("seed"))
    dataset = cell.get("dataset") or result.get("dataset")
    backend = cell.get("backend") or result.get("backend")
    for row in per_item:
        item_id = row.get("item_id")
        out = {
            "algorithm": algorithm,
            "backend": backend,
            "dataset": dataset,
            "seed": seed,
            "item_id": item_id,
            "json_path": str(path),
            "ds_n": ds_params.get("n"),
            "ds_r": ds_params.get("r"),
            "ds_c": ds_params.get("c"),
            "ds_seed": ds_params.get("seed"),
            **{
                k: row.get(k)
                for k in (
                    "n_nodes",
                    "n_edges",
                    "max_arity",
                    "median_time_s",
                    "iqr_time_s",
                    "peak_rss_bytes",
                    "fp_bytes_length",
                    "fingerprint_hex",
                    "roundtrip_ok",
                    "iso_invariance_ok",
                    "dnf",
                    "dnf_reason",
                )
            },
        }
        tc = row.get("token_counts") or {}
        for k in ("V", "C", "N", "P", "W"):
            out[f"token_{k}"] = tc.get(k)
        yield out


def _cell_rows(
    algorithm: str,
    path: Path,
    payload: dict[str, Any],
) -> dict[str, Any]:
    measurements: dict[str, Any] = (payload.get("result") or {}).get("measurements", {}) or {}
    cell = payload.get("cell", {}) or {}
    result = payload.get("result", {}) or {}
    ds_params: dict[str, Any] = cell.get("dataset_params", {}) or {}
    return {
        "algorithm": algorithm,
        "backend": cell.get("backend", result.get("backend")),
        "dataset": cell.get("dataset", result.get("dataset")),
        "seed": cell.get("seed", result.get("seed")),
        "json_path": str(path),
        "ds_n": ds_params.get("n"),
        "ds_r": ds_params.get("r"),
        "ds_c": ds_params.get("c"),
        "ds_seed": ds_params.get("seed"),
        "n_items": measurements.get("n_items"),
        "n_dnf": measurements.get("n_dnf"),
        "median_time_s": measurements.get("median_time_s"),
        "iqr_time_s": measurements.get("iqr_time_s"),
        "peak_rss_bytes": measurements.get("peak_rss_bytes"),
        "n_roundtrip_checked": measurements.get("n_roundtrip_checked"),
        "n_roundtrip_failures": measurements.get("n_roundtrip_failures"),
        "n_iso_invariance_checked": measurements.get("n_iso_invariance_checked"),
        "n_iso_invariance_failures": measurements.get("n_iso_invariance_failures"),
        "wall_clock_s": result.get("wall_clock_s", payload.get("wall_clock_s")),
        "git_sha": payload.get("git_sha"),
    }


def _add_canonical_equivalence(rows: list[dict[str, Any]]) -> None:
    """Add ``canonical_equivalent_with_greedy_min`` column in place."""
    key_to_baseline: dict[tuple[Any, ...], str | None] = {}
    for r in rows:
        if r["algorithm"] == "greedy_min":
            key = (r["dataset"], r["ds_n"], r["ds_r"], r["ds_c"], r["ds_seed"], r["item_id"])
            key_to_baseline[key] = r["fingerprint_hex"]
    for r in rows:
        key = (r["dataset"], r["ds_n"], r["ds_r"], r["ds_c"], r["ds_seed"], r["item_id"])
        baseline = key_to_baseline.get(key)
        if baseline is None or r["fingerprint_hex"] is None:
            r["canonical_equivalent_with_greedy_min"] = None
        else:
            r["canonical_equivalent_with_greedy_min"] = bool(r["fingerprint_hex"] == baseline)


def _save_table(rows: Iterable[dict[str, Any]], dest: Path) -> None:
    rows_list = list(rows)
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        import pandas as pd

        df = pd.DataFrame(rows_list)
        try:
            df.to_parquet(dest.with_suffix(".parquet"), index=False)
            logger.info("wrote %s (%d rows)", dest.with_suffix(".parquet"), len(df))
        except (ImportError, ValueError) as exc:
            logger.warning("parquet write failed (%s); falling back to CSV", exc)
            df.to_csv(dest.with_suffix(".csv"), index=False)
            logger.info("wrote %s (%d rows)", dest.with_suffix(".csv"), len(df))
    except ImportError:
        import csv

        dest_csv = dest.with_suffix(".csv")
        if rows_list:
            fields = sorted({k for r in rows_list for k in r.keys()})
            with dest_csv.open("w", encoding="utf-8", newline="") as fh:
                writer = csv.DictWriter(fh, fieldnames=fields)
                writer.writeheader()
                for r in rows_list:
                    writer.writerow(r)
        logger.info("wrote %s (%d rows, pandas not installed)", dest_csv, len(rows_list))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"]
    )
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    item_rows: list[dict[str, Any]] = []
    cell_rows: list[dict[str, Any]] = []
    n_logs = 0
    for algorithm, path, payload in _iter_run_logs(args.results_root):
        n_logs += 1
        item_rows.extend(_per_item_rows(algorithm, path, payload))
        cell_rows.append(_cell_rows(algorithm, path, payload))

    _add_canonical_equivalence(item_rows)
    _save_table(item_rows, args.output_dir / "items")
    _save_table(cell_rows, args.output_dir / "cells")

    logger.info(
        "aggregated %d run logs -> %d item rows, %d cell rows",
        n_logs,
        len(item_rows),
        len(cell_rows),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
