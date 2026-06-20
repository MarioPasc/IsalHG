"""Generate the 720-cell preprint sweep YAML.

Expands the (backend × n × r × c × seed) Cartesian product into one
:class:`~experiments.schemas.CellSpec` per tuple and writes the result
to ``experiments/configs/preprint_random_sweep.yaml``. The output file
is the orchestrator's source of truth; this script is the *design* of
the grid (axes + backend list + seed range) and the one place to edit
when the axes change.

PREPRINT.md §3 specifies the headline grid:

- ``n ∈ {50, 200, 1000}``
- ``r ∈ {3, 5}``
- ``c ∈ {1, 5, 25}`` (edges-per-vertex target; translated to XGI ``p``
  by the dataset class)
- seeds ``{0, ..., 9}``
- backends ``{isalhg, pynauty_levi, bliss_levi, traces_levi}``

3 × 2 × 3 × 10 × 4 = **720 cells**.

Per PREPRINT.md §4.5 the n=1000, r=5, c=25 cells get the extended
memory tier (16 GB vs the default 8 GB); the YAML carries no
SLURM-level annotation — that lives in the ``picasso-sbatch`` launcher
the orchestrator dispatches against.

Usage
-----
::

    python experiments/preprint/data/build_preprint_config.py
    # optionally:
    python experiments/preprint/data/build_preprint_config.py \
        --output experiments/configs/preprint_random_sweep.yaml
"""

from __future__ import annotations

import argparse
import logging
import math
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Grid (edit here when the axes change; rerun the script to regenerate the YAML)
# -----------------------------------------------------------------------------

N_VALUES: tuple[int, ...] = (50, 200, 1000)
R_VALUES: tuple[int, ...] = (3, 5)
C_VALUES: tuple[float, ...] = (1.0, 5.0, 25.0)
SEEDS: tuple[int, ...] = tuple(range(10))
BACKENDS: tuple[str, ...] = (
    "isalhg",
    "pynauty_levi",
    "bliss_levi",
    "traces_levi",
)

PROTOCOL_NAME: str = "fingerprint_timing"
DATASET_NAME: str = "random_erdos_renyi"

# Per PREPRINT.md §4.2 the protocol takes the median of 10 repeats per
# fingerprint to suppress per-call noise.
REPEATS: int = 10
TIMEOUT_S: float = 600.0
CHECK_POSITIVE_PAIR: bool = True

OUTPUT_ROOT: Path = Path("experiments/outputs/preprint_random_sweep")
DEFAULT_OUTPUT_YAML: Path = Path("experiments/configs/preprint_random_sweep.yaml")


def _p_from_c(c: float, n: int, r: int) -> float:
    """Mirror of :func:`isalhg.datasets.synthetic.erdos_renyi._p_from_c`.

    Used here only to log the realised ``p`` and ``E[m]`` per axis cell.
    """
    return c * n / math.comb(n, r)


def _cells() -> list[dict[str, Any]]:
    """Materialise the full Cartesian product of (backend, n, r, c, seed)."""
    cells: list[dict[str, Any]] = []
    for n in N_VALUES:
        for r in R_VALUES:
            for c in C_VALUES:
                for seed in SEEDS:
                    for backend in BACKENDS:
                        cells.append(
                            {
                                "protocol": PROTOCOL_NAME,
                                "backend": backend,
                                "dataset": DATASET_NAME,
                                "seed": int(seed),
                                "protocol_params": {
                                    "timeout_s": float(TIMEOUT_S),
                                    "repeats": int(REPEATS),
                                    "check_positive_pair": bool(CHECK_POSITIVE_PAIR),
                                },
                                "dataset_params": {
                                    "n": int(n),
                                    "r": int(r),
                                    "c": float(c),
                                    "seed": int(seed),
                                },
                                "backend_params": {},
                            }
                        )
    return cells


def _log_axis_table() -> None:
    logger.info(
        "Cohort axes (PREPRINT.md §3): n=%s r=%s c=%s seeds=%s backends=%s",
        list(N_VALUES),
        list(R_VALUES),
        list(C_VALUES),
        f"0..{SEEDS[-1]}",
        list(BACKENDS),
    )
    logger.info(
        "%-6s %-4s %-6s %-12s %-12s",
        "n",
        "r",
        "c",
        "p",
        "E[m] = c*n",
    )
    for n in N_VALUES:
        for r in R_VALUES:
            for c in C_VALUES:
                p = _p_from_c(c, n, r)
                e_m = c * n
                logger.info(
                    "%-6d %-4d %-6g %-12.4e %-12g",
                    n,
                    r,
                    c,
                    p,
                    e_m,
                )


def build_config(output_path: Path) -> int:
    cells = _cells()
    expected = len(N_VALUES) * len(R_VALUES) * len(C_VALUES) * len(SEEDS) * len(BACKENDS)
    assert len(cells) == expected, (len(cells), expected)

    payload: dict[str, Any] = {
        "name": "preprint_random_sweep",
        "description": (
            "Synthetic random-hypergraph characterisation study (preprint). "
            "Sweep across (n, r, c) = "
            f"{list(N_VALUES)} x {list(R_VALUES)} x {list(C_VALUES)}; "
            f"seeds 0..{SEEDS[-1]}; backends "
            f"{list(BACKENDS)}. Generated by "
            "experiments/preprint/data/build_preprint_config.py from PREPRINT.md §3."
        ),
        "output_root": str(OUTPUT_ROOT),
        "cells": cells,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(payload, fh, sort_keys=False, default_flow_style=False)

    logger.info("wrote %d cells to %s", len(cells), output_path)
    return len(cells)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_YAML,
        help="destination YAML path",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    _log_axis_table()
    n_cells = build_config(args.output)
    print(f"wrote {n_cells} cells to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
