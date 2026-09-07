"""Merge several RQ1 experiments run on the same seeded units into one.

The 2026-09-07 RQ1 measurement of the Isal instruction word was produced by
three experiments on identical units, members and seeded edits:

* ``addressing`` -- the campaign array (``configs/rq1.yaml``): ``w*_c``
  (C++), the Python ordered walk and Python orbit engine (provisional), the
  fact arms kept as the record, the certificate arms;
* ``addressing_rank`` -- ``wstar_rank`` on the C++ engine after its port
  (``configs/rq1_rank.yaml``);
* ``addressing_cpp`` -- ``wstar_orbit`` and ``isal_ow_*`` on the C++ engines
  (``configs/rq1_cpp.yaml``), bit-identical words, C++ timing.

The analyzer (:mod:`experiments.tkde.analyze_rq1`) concatenates every tagged
row file in one experiment directory, so the experiments are merged by copying
row files into one directory with **one source experiment per arm**: an arm's
rows come from exactly one run (the first listed experiment that has the arm,
or the experiment named for it with ``--prefer``), which keeps every arm's
sample unique without deduplicating rows. Row files are filtered by arm and
keep their ``rows_<table>__<tag>-<unit>.csv`` names, so the analyzer's
campaign-file test still passes and the tags record the provenance. A
``merge_manifest.json`` records the sources and the per-arm assignment; the
first experiment's ``config.json`` and ``manifest.json`` are copied beside it.
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

RQ_FOLDER = "RQ1_addressing"
TABLES: tuple[str, ...] = ("m0items", "m1", "m2", "m3", "m4")


def _row_files(exp_dir: Path, table: str) -> list[Path]:
    return sorted(exp_dir.glob(f"rows_{table}__*.csv"))


def arms_of(exp_dir: Path) -> set[str]:
    """Every arm that has at least one row in ``exp_dir``."""
    arms: set[str] = set()
    for table in TABLES:
        for path in _row_files(exp_dir, table):
            try:
                frame = pd.read_csv(path, usecols=["arm"])
            except ValueError:
                continue
            arms.update(frame["arm"].astype(str).unique().tolist())
    return arms


def assign_sources(
    root: Path, experiments: Sequence[str], prefer: dict[str, str]
) -> dict[str, str]:
    """Map every arm to the one experiment its rows are taken from.

    Parameters
    ----------
    root : Path
        The results root holding ``RQ1_addressing/<experiment>/``.
    experiments : Sequence[str]
        Experiment names in priority order.
    prefer : dict[str, str]
        ``arm -> experiment`` overrides.

    Returns
    -------
    dict[str, str]
        ``arm -> experiment``.

    Raises
    ------
    FileNotFoundError
        If an experiment directory is missing.
    ValueError
        If a preferred experiment has no rows for that arm.
    """
    available: dict[str, set[str]] = {}
    for name in experiments:
        exp_dir = root / RQ_FOLDER / name
        if not exp_dir.is_dir():
            raise FileNotFoundError(f"no experiment directory {exp_dir}")
        available[name] = arms_of(exp_dir)
    assignment: dict[str, str] = {}
    for name in experiments:
        for arm in sorted(available[name]):
            assignment.setdefault(arm, name)
    for arm, name in prefer.items():
        if arm not in available.get(name, set()):
            raise ValueError(f"--prefer {arm}={name}: that experiment has no rows for {arm}")
        assignment[arm] = name
    return assignment


def merge(
    root: Path,
    experiments: Sequence[str],
    out_experiment: str,
    prefer: dict[str, str] | None = None,
    overwrite: bool = False,
    out_root: Path | None = None,
) -> dict[str, str]:
    """Write the merged experiment and return the arm -> source assignment.

    ``out_root`` lets the merged experiment live under another results root
    (e.g. ``.../results/IEEETKDE_isal``) under the analyzer's default
    experiment name ``addressing``, so :mod:`experiments.tkde.analyze_rq1`
    reads it with ``--root`` and no change, and the campaign's own
    ``addressing`` directory stays the frozen record.
    """
    prefer = dict(prefer or {})
    assignment = assign_sources(root, experiments, prefer)
    out_dir = (out_root or root) / RQ_FOLDER / out_experiment
    if out_dir.exists():
        if not overwrite:
            raise FileExistsError(f"{out_dir} exists; pass --overwrite to replace it")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    written = 0
    kept_rows: dict[str, int] = {}
    for name in experiments:
        arms_here = sorted(arm for arm, src in assignment.items() if src == name)
        if not arms_here:
            continue
        exp_dir = root / RQ_FOLDER / name
        for table in TABLES:
            for path in _row_files(exp_dir, table):
                frame = pd.read_csv(path)
                if "arm" not in frame.columns:
                    continue
                kept = frame[frame["arm"].astype(str).isin(arms_here)]
                if kept.empty:
                    continue
                # The experiment column names the merged experiment; the tag in
                # the file name and the manifest keep the provenance.
                kept = kept.assign(experiment=out_experiment)
                kept.to_csv(out_dir / path.name, index=False)
                written += 1
                kept_rows[table] = kept_rows.get(table, 0) + len(kept)

    first = root / RQ_FOLDER / experiments[0]
    for aux in ("config.json", "manifest.json"):
        if (first / aux).is_file():
            shutil.copy2(first / aux, out_dir / aux)
    manifest = {
        "merged_experiment": out_experiment,
        "sources": list(experiments),
        "arm_sources": assignment,
        "row_files_written": written,
        "rows_kept_per_table": kept_rows,
    }
    (out_dir / "merge_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
    logger.info("merged %d row files into %s: %s", written, out_dir, assignment)
    return assignment


def _parse_prefer(items: Sequence[str]) -> dict[str, str]:
    prefer: dict[str, str] = {}
    for item in items:
        arm, sep, name = item.partition("=")
        if not sep or not arm or not name:
            raise argparse.ArgumentTypeError(f"--prefer expects arm=experiment, got {item!r}")
        prefer[arm] = name
    return prefer


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="experiments.tkde.merge_rq1_experiments", description=__doc__
    )
    parser.add_argument("--root", required=True, type=Path, help="results root")
    parser.add_argument(
        "--experiments", nargs="+", required=True, help="source experiments, priority order"
    )
    parser.add_argument("--out", required=True, help="name of the merged experiment")
    parser.add_argument(
        "--prefer", nargs="*", default=(), help="arm=experiment overrides (one arm each)"
    )
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--out-root", type=Path, default=None, help="results root for the merged experiment"
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    assignment = merge(
        args.root,
        args.experiments,
        args.out,
        _parse_prefer(args.prefer),
        args.overwrite,
        out_root=args.out_root,
    )
    for arm, name in sorted(assignment.items()):
        print(f"{arm:24s} <- {name}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
