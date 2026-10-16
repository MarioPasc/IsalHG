"""Units and tasks of the KNN_2026-10-15 full run (LOG.md §8), and their dispatch.

A *unit* is one ``(design, collection, condition or stratum)`` job over the 27
seeds, run by that design's own CLI (``probe_knn.py`` for A / B / mix,
``design_c.py``, ``design_d.py``) into its own directory ``<out>/<unit>/``. Every
CLI resumes from what is already in that directory, so a re-run after a
TIMEOUT recomputes only the missing seeds.

A *task* (one SLURM array index) runs a fixed group of units in sequence. The
heavy units (Design B and the mix condition) are one task each; the Design-D
units and the short Design-A and Design-C units are grouped so that no task
runs under the cluster's two-hour floor (slurm/tkde/README.md, "The 2 h
floor"). The grouping is a scheduling decision only: it changes no unit's
parameters or seeds.

``--list-units`` and ``--list-tasks`` are what the launcher and the worker
decode, so the array size can never disagree with the decode. ``--smoke``
runs seed 0 of one unit per design CLI (the cluster smoke, staged apart).
"""

from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("full_run")

HERE = Path(__file__).resolve().parent
SEEDS: tuple[int, ...] = tuple(range(27))
COLLECTIONS: tuple[str, ...] = ("wd50k66", "wd50k100", "ndc_classes", "ndc_substances")
MIX_COLLECTIONS: tuple[str, ...] = ("wd50k66", "wd50k100")
LINEAGE_COLLECTIONS: tuple[str, ...] = ("ndc_classes", "ndc_substances")
STRATA: tuple[str, ...] = ("C-all", "C-int", "C-pend")
B_SOURCES, B_COPIES = 200, 6
A_LINEAGES = 30
D_SOURCES = 200
SMOKE_UNITS: tuple[str, ...] = (
    "D_ndc_classes_pendant",
    "C3_ndc_classes_C-all",
    "A_ndc_classes",
    "B_ndc_classes",
)


@dataclass(frozen=True)
class Unit:
    """One design job; the seeds are appended by :meth:`command`."""

    name: str
    script: str
    args: tuple[str, ...]

    def command(self, out: Path, n_jobs: int, seeds: Sequence[int] = SEEDS) -> list[str]:
        """The CLI invocation writing into ``out / name``."""
        return [
            sys.executable,
            str(HERE / self.script),
            *self.args,
            "--seeds",
            *(str(s) for s in seeds),
            "--out",
            str(out / self.name),
            "--n-jobs",
            str(n_jobs),
        ]


def units() -> list[Unit]:
    """Every unit of the full run, in a fixed order."""
    out: list[Unit] = []
    common_b = ("--S", str(B_SOURCES), "--c", str(B_COPIES), "--r", "1", "2", "3")
    tail = ("--arm-set", "full", "--no-summary")
    for col in COLLECTIONS:
        out.append(
            Unit(
                f"B_{col}",
                "probe_knn.py",
                ("--designs", "B", "--collections", col, *common_b, *tail),
            )
        )
    for col in MIX_COLLECTIONS:
        args = ("--designs", "mix", "--collections", col, "--mix-collections", col)
        out.append(Unit(f"Bmix_{col}", "probe_knn.py", (*args, *common_b, *tail)))
    for col in COLLECTIONS:
        for mix in ("pendant", "empirical"):
            if mix == "empirical" and col not in MIX_COLLECTIONS:
                continue
            args = ("--collection", col, "--mix", mix, "--sources", str(D_SOURCES))
            out.append(Unit(f"D_{col}_{mix}", "design_d.py", args))
    for col in LINEAGE_COLLECTIONS:
        args = ("--designs", "A", "Afull", "--collections", col, "--lineages", str(A_LINEAGES))
        out.append(Unit(f"A_{col}", "probe_knn.py", (*args, *tail)))
    for copies in (3, 6):
        for col in COLLECTIONS:
            for stratum in STRATA:
                args = ("--collection", col, "--stratum", stratum, "--copies", str(copies))
                out.append(
                    Unit(f"C{copies}_{col}_{stratum}", "design_c.py", (*args, "--arm-set", "full"))
                )
    return out


def tasks() -> list[list[str]]:
    """Unit names per array task.

    Measured locally at 16 jobs (2026-10-15): one Design-B seed at S = 200,
    c = 6 is about 6 min (27 seeds: ~2.7 h); a Design-D job is 19-54 min
    (``probe_d/SUMMARY_D.md`` cost table, S = 200 extrapolation); a Design-C
    job is 1-6 min and a Design-A job a few minutes. So each B / mix unit is
    one task, the two WD50K(66) D units one task, the other four D units one
    task, and every A and C unit one task.
    """
    names = [u.name for u in units()]
    heavy = [[n] for n in names if n.startswith(("B_", "Bmix_"))]
    d66 = [n for n in names if n.startswith("D_wd50k66_")]
    d_rest = [n for n in names if n.startswith("D_") and n not in d66]
    short = [n for n in names if n.startswith(("A_", "C3_", "C6_"))]
    return [*heavy, d66, d_rest, short]


def _run(unit: Unit, out: Path, n_jobs: int, seeds: Sequence[int]) -> int:
    cmd = unit.command(out, n_jobs, seeds)
    logger.info("unit %s: %s", unit.name, " ".join(cmd))
    t0 = time.perf_counter()
    status = subprocess.run(cmd, check=False).returncode
    logger.info("unit %s: exit %d after %.0f s", unit.name, status, time.perf_counter() - t0)
    return status


def run_task(task: int, out: Path, n_jobs: int, start_cutoff_epoch: float | None) -> int:
    """Run every unit of ``task`` in order; returns the number of failed units."""
    by_name = {u.name: u for u in units()}
    group = tasks()[task]
    logger.info("task %d -> %d unit(s): %s", task, len(group), ", ".join(group))
    failed = 0
    for k, name in enumerate(group):
        # The first unit is exempt, or a task whose start-up passed the cutoff livelocks.
        if k > 0 and start_cutoff_epoch is not None and time.time() >= start_cutoff_epoch:
            logger.warning("DEFERRED: unit %s (start cutoff reached)", name)
            continue
        failed += _run(by_name[name], out, n_jobs, SEEDS) != 0
    return failed


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--list-units", action="store_true")
    ap.add_argument("--list-tasks", action="store_true")
    ap.add_argument("--task", type=int)
    ap.add_argument("--smoke", action="store_true", help="seed 0 of SMOKE_UNITS")
    ap.add_argument("--out", type=Path)
    ap.add_argument(
        "--n-jobs",
        type=int,
        default=int(os.environ.get("SLURM_CPUS_PER_TASK", os.cpu_count() or 1)),
    )
    ap.add_argument("--start-cutoff-epoch", type=float, default=None)
    args = ap.parse_args()
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(name)s %(message)s", datefmt="%H:%M:%S"
    )
    if args.list_units:
        for i, u in enumerate(units()):
            print(f"{i} {u.name}")
        return
    if args.list_tasks:
        for i, group in enumerate(tasks()):
            print(f"{i} {','.join(group)}")
        return
    if args.out is None:
        ap.error("--out is required to run")
    if args.smoke:
        by_name = {u.name: u for u in units()}
        failed = sum(_run(by_name[n], args.out, args.n_jobs, (0,)) != 0 for n in SMOKE_UNITS)
        sys.exit(1 if failed else 0)
    if args.task is None:
        ap.error("--task (or --smoke) is required to run")
    sys.exit(1 if run_task(args.task, args.out, args.n_jobs, args.start_cutoff_epoch) else 0)


if __name__ == "__main__":
    main()
