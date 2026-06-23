"""Parallel cell driver for the algorithm-benchmark study.

Loads an :class:`ExperimentConfig`, splits its cells across a process
pool sized to ``--n-workers``, and dispatches each cell through
:func:`experiments.orchestrator.run_cell`. The orchestrator already
implements idempotent JSON-skip per cell, so re-running this driver
resumes from the first incomplete cell.

Designed for the per-algorithm Picasso job: one SLURM task per
algorithm, ``--n-workers=$SLURM_CPUS_PER_TASK``, all 91 cells inside.

Usage
-----
::

    python -m experiments.preprint.algorithms.run_parallel \\
        --config experiments/preprint/algorithms/configs/algo_greedy_min.yaml \\
        --n-workers $SLURM_CPUS_PER_TASK
"""

from __future__ import annotations

import argparse
import logging
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from experiments.orchestrator import _capture_git_sha, _capture_hardware, run_cell
from experiments.schemas import CellSpec, ExperimentConfig

logger = logging.getLogger(__name__)


def _worker(cell_args: tuple[CellSpec, Path, str, dict]) -> str:
    cell, output_root, git_sha, hardware = cell_args
    log = run_cell(cell, output_root, git_sha=git_sha, hardware=hardware)
    return f"{cell.backend} dataset={cell.dataset} seed={cell.seed} wall={log.result.wall_clock_s:.2f}s"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument(
        "--n-workers",
        type=int,
        default=int(os.environ.get("SLURM_CPUS_PER_TASK", "1")),
        help="Process pool size; default reads $SLURM_CPUS_PER_TASK.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=None,
        help="Override the YAML's output_root (useful for cross-host execution).",
    )
    parser.add_argument(
        "--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"]
    )
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    config = ExperimentConfig.from_yaml(args.config)
    if args.output_root is not None:
        config = ExperimentConfig(
            name=config.name,
            description=config.description,
            output_root=args.output_root,
            cells=config.cells,
        )
    config.output_root.mkdir(parents=True, exist_ok=True)
    git_sha = _capture_git_sha()
    hardware = _capture_hardware()

    n_workers = max(1, args.n_workers)
    logger.info(
        "config=%s cells=%d n_workers=%d output_root=%s",
        config.name,
        len(config.cells),
        n_workers,
        config.output_root,
    )

    task_inputs = [(cell, config.output_root, git_sha, hardware) for cell in config.cells]

    if n_workers == 1:
        for idx, task in enumerate(task_inputs):
            msg = _worker(task)
            logger.info("[%d/%d] %s", idx + 1, len(task_inputs), msg)
        return 0

    completed = 0
    # Recycle workers after each cell so monotonic memory growth (CDLL
    # clones held by gc, fingerprint buffers, intermediate state) cannot
    # accumulate across cells. Without this, n=1000 r=5 c=25 cells OOM
    # the node at 128 GB after a few completed cells.
    pool_kwargs: dict[str, int] = {"max_workers": n_workers}
    try:
        ProcessPoolExecutor(max_workers=1, max_tasks_per_child=1).shutdown()
        pool_kwargs["max_tasks_per_child"] = 1
    except TypeError:
        pass
    with ProcessPoolExecutor(**pool_kwargs) as pool:
        futures = {pool.submit(_worker, task): task for task in task_inputs}
        for fut in as_completed(futures):
            completed += 1
            try:
                msg = fut.result()
                logger.info("[%d/%d] %s", completed, len(task_inputs), msg)
            except Exception as exc:  # noqa: BLE001 - record-and-continue
                cell = futures[fut][0]
                logger.error(
                    "cell failed (%s/%s/%d): %s", cell.backend, cell.dataset, cell.seed, exc
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
