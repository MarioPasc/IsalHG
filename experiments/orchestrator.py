"""Experiment orchestrator.

Reads a YAML config (:mod:`experiments.schemas.ExperimentConfig`), enumerates
``(protocol, backend, dataset, seed)`` cells, looks each component up in its
registry, runs the cell, and persists a :class:`RunLog` per cell using the
atomic skip-if-exists pattern ported from IsalSR
``experiments/models/orchestrator.py``.

Entry point::

    python -m experiments.orchestrator --config experiments/configs/tier1_correctness.yaml
"""

from __future__ import annotations

import argparse
from pathlib import Path

from experiments.schemas import CellSpec, RunLog


def run_experiment(config_path: Path) -> None:
    """Top-level loop: load config, iterate cells, persist run logs."""
    raise NotImplementedError


def run_cell(cell: CellSpec, output_dir: Path) -> RunLog:
    """Execute one cell of the matrix; return its :class:`RunLog`.

    Idempotent: if ``output_dir / "<cell-hash>.json"`` already exists and
    JSON-validates, return the cached log without re-running.
    """
    raise NotImplementedError


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args(argv)
    run_experiment(args.config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
