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
import dataclasses
import hashlib
import json
import logging
import os
import platform
import subprocess
from pathlib import Path
from typing import Any

from experiments.schemas import CellSpec, ExperimentConfig, RunLog
from isalhg.datasets.registry import get_dataset
from isalhg.iso_backends.registry import get_backend
from isalhg.protocols.registry import get_protocol

logger = logging.getLogger(__name__)


def run_experiment(config_path: Path) -> list[RunLog]:
    """Top-level loop: load config, iterate cells, persist run logs.

    Returns the list of :class:`RunLog` instances (cached or freshly
    computed) for downstream programmatic inspection.
    """
    config = ExperimentConfig.from_yaml(config_path)
    config.output_root.mkdir(parents=True, exist_ok=True)
    logger.info("loaded config %r with %d cells", config.name, len(config.cells))

    git_sha = _capture_git_sha()
    hardware = _capture_hardware()

    logs: list[RunLog] = []
    for idx, cell in enumerate(config.cells):
        logger.info(
            "[%d/%d] cell protocol=%s backend=%s dataset=%s seed=%d",
            idx + 1,
            len(config.cells),
            cell.protocol,
            cell.backend,
            cell.dataset,
            cell.seed,
        )
        log = run_cell(cell, config.output_root, git_sha=git_sha, hardware=hardware)
        logs.append(log)
    return logs


def run_cell(
    cell: CellSpec,
    output_dir: Path,
    *,
    git_sha: str = "",
    hardware: dict[str, Any] | None = None,
) -> RunLog:
    """Execute one cell of the matrix; return its :class:`RunLog`.

    Idempotent: if ``output_dir / "<filename>.json"`` already exists and
    JSON-validates against :meth:`RunLog.load_json`, return the cached
    log without re-running.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / _cell_filename(cell)

    if out_path.exists():
        try:
            cached = RunLog.load_json(out_path)
            logger.info("cached -> %s", out_path.name)
            return cached
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            logger.warning("re-running %s; cached log corrupt: %s", out_path.name, exc)

    dataset = get_dataset(cell.dataset, cell.dataset_params)
    protocol = get_protocol(cell.protocol, cell.protocol_params)
    backend = get_backend(cell.backend)

    result = protocol.measure(backend, dataset, cell.seed)
    log = RunLog(
        cell=cell,
        result=result,
        hardware=hardware or _capture_hardware(),
        git_sha=git_sha or _capture_git_sha(),
    )
    log.save_json(out_path)
    logger.info("wrote %s (wall=%.3fs)", out_path.name, result.wall_clock_s)
    return log


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _cell_filename(cell: CellSpec) -> str:
    """Stable, human-readable filename including a content hash.

    The hash key is normalised so tuples and lists collapse to a single
    JSON representation; otherwise a programmatic caller passing
    ``{"n_range": (3, 4)}`` would hash differently from a YAML caller
    that produces ``[3, 4]``, breaking idempotent skip-if-exists.
    """
    digest = hashlib.sha256(
        json.dumps(
            _normalise_for_hash(dataclasses.asdict(cell)),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()[:16]
    return f"{cell.protocol}__{cell.backend}__{cell.dataset}__seed{cell.seed}__{digest}.json"


def _normalise_for_hash(value: Any) -> Any:
    """Recursively collapse tuples -> lists and sets -> sorted lists.

    Used as a pre-pass before ``json.dumps`` so the hash key is
    invariant to the container type produced by the caller (PyYAML
    emits lists; Python literals may emit tuples).
    """
    if isinstance(value, dict):
        return {str(k): _normalise_for_hash(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalise_for_hash(v) for v in value]
    if isinstance(value, (set, frozenset)):
        return sorted(_normalise_for_hash(v) for v in value)
    return value


def _capture_hardware() -> dict[str, Any]:
    info: dict[str, Any] = {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "conda_env": os.environ.get("CONDA_DEFAULT_ENV", ""),
        "processor": platform.processor(),
    }
    for mod_name in ("pynauty", "igraph"):
        try:
            mod = __import__(mod_name)
            info[f"{mod_name}_version"] = getattr(mod, "__version__", "unknown")
        except ImportError:
            info[f"{mod_name}_version"] = None
    return info


def _capture_git_sha() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5.0,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""
    if out.returncode != 0:
        return ""
    return out.stdout.strip()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="root logger level (default: INFO)",
    )
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    run_experiment(args.config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
