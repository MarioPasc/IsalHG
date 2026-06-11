"""Aggregate per-cell ``RunLog`` JSONs into per-condition summary rows.

For each ``(protocol, backend, dataset)`` triple, collects the seeds and
computes median, IQR, and geometric-mean speedup against the reference
backend (defaults to ``pynauty_levi``).
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from experiments.schemas import RunLog


def collect_run_logs(output_root: Path) -> list[RunLog]:
    """Walk ``output_root`` and load every ``RunLog`` JSON found."""
    raise NotImplementedError


def aggregate_by_cell(logs: Iterable[RunLog]) -> dict[tuple[str, str, str], dict[str, float]]:
    """Group by ``(protocol, backend, dataset)`` and summarise."""
    raise NotImplementedError
