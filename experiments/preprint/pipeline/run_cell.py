"""Single-cell entry point for the preprint Picasso array sweep.

Reads one ``CellSpec`` out of an :class:`ExperimentConfig` by integer
index (or by ``$SLURM_ARRAY_TASK_ID``) and dispatches it through
:func:`experiments.orchestrator.run_cell`. The orchestrator already
implements atomic skip-if-exists per-cell JSON, so re-running the same
array task is a no-op once the result is on disk.

Memory tiers
------------

The launcher (``slurm/launcher.sh``) submits two SLURM arrays — a
``fast`` tier covering every cell with ``n < 1000 OR c < 25`` and a
``slow`` tier covering the dense ``n = 1000 AND c = 25`` corner. The
``--tier`` flag below filters the YAML's cells into the matching
deterministic subset BEFORE indexing, so the same task index always
addresses the same cell on resubmission.

Usage
-----
::

    # Single cell from the full sweep, indexed inside its tier subset:
    python -m experiments.preprint.pipeline.run_cell \\
        --config experiments/configs/preprint_random_sweep.yaml \\
        --tier fast \\
        --cell-index 0

    # SLURM array body picks up the task id automatically:
    python -m experiments.preprint.pipeline.run_cell \\
        --config experiments/configs/preprint_random_sweep.yaml \\
        --tier fast  # --cell-index defaults to $SLURM_ARRAY_TASK_ID
"""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

from experiments.orchestrator import _capture_git_sha, _capture_hardware, run_cell
from experiments.schemas import CellSpec, ExperimentConfig

logger = logging.getLogger(__name__)

_SLOW_N: int = 1000
_SLOW_C: float = 25.0


def _is_slow_cell(cell: CellSpec) -> bool:
    """Return True for the high-memory tier (``n = 1000 AND c = 25``)."""
    n = cell.dataset_params.get("n")
    c = cell.dataset_params.get("c")
    return n == _SLOW_N and float(c) == _SLOW_C


def filter_by_tier(cells: tuple[CellSpec, ...], tier: str) -> list[CellSpec]:
    """Filter cells deterministically by memory tier.

    Parameters
    ----------
    cells
        Cells in YAML order (the launcher relies on this order).
    tier
        ``"fast"``, ``"slow"``, or ``"all"``.

    Returns
    -------
    list[CellSpec]
        YAML-ordered subset matching the tier.
    """
    if tier == "all":
        return list(cells)
    if tier == "fast":
        return [c for c in cells if not _is_slow_cell(c)]
    if tier == "slow":
        return [c for c in cells if _is_slow_cell(c)]
    raise ValueError(f"unknown tier {tier!r}; expected fast|slow|all")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument(
        "--tier",
        choices=("fast", "slow", "all"),
        default="all",
        help=(
            "Memory tier filter. 'fast' selects every cell except the "
            "n=1000 AND c=25 corner; 'slow' selects only that corner; "
            "'all' takes the YAML in full."
        ),
    )
    parser.add_argument(
        "--cell-index",
        type=int,
        default=None,
        help=(
            "Index into the post-filter cell list. Defaults to "
            "$SLURM_ARRAY_TASK_ID when running under SLURM."
        ),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=None,
        help="Override the YAML's output_root (cross-host execution).",
    )
    parser.add_argument(
        "--count",
        action="store_true",
        help=(
            "Print the cell count for the selected --tier on stdout and "
            "exit. Used by launcher.sh to size the SLURM array."
        ),
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
    )
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    if args.count:
        config = ExperimentConfig.from_yaml(args.config)
        print(len(filter_by_tier(config.cells, args.tier)))
        return 0

    if args.cell_index is None:
        env_idx = os.environ.get("SLURM_ARRAY_TASK_ID")
        if env_idx is None:
            parser.error(
                "--cell-index is required when $SLURM_ARRAY_TASK_ID is unset",
            )
        args.cell_index = int(env_idx)

    config = ExperimentConfig.from_yaml(args.config)
    output_root = args.output_root if args.output_root is not None else config.output_root
    output_root.mkdir(parents=True, exist_ok=True)

    tier_cells = filter_by_tier(config.cells, args.tier)
    if not 0 <= args.cell_index < len(tier_cells):
        parser.error(
            f"--cell-index {args.cell_index} out of range "
            f"[0, {len(tier_cells)}) for tier={args.tier!r}",
        )
    cell = tier_cells[args.cell_index]

    logger.info(
        "tier=%s cell_index=%d/%d backend=%s n=%s r=%s c=%s seed=%s",
        args.tier,
        args.cell_index,
        len(tier_cells),
        cell.backend,
        cell.dataset_params.get("n"),
        cell.dataset_params.get("r"),
        cell.dataset_params.get("c"),
        cell.seed,
    )

    log = run_cell(
        cell,
        output_root,
        git_sha=_capture_git_sha(),
        hardware=_capture_hardware(),
    )
    logger.info(
        "done backend=%s seed=%d wall=%.3fs",
        cell.backend,
        cell.seed,
        log.result.wall_clock_s,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
