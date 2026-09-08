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

**One launch per experiment.** An experiment directory is a *name*, not a run:
``addressing`` on the cluster holds the 2026-09-06 campaign (launch tag
``c3fb21de``, before the Isal arms and before the instruction-granularity
columns ``d_instr``/``n_instr``/``aut_bucket`` existed) *and* the 2026-09-07
Isal campaign (tag ``47c8a42c``, jobs 2247394 + 2247395), which re-measures
every unit.  Both write the fact and certificate arms, so concatenating them
counts those arms twice while the Isal arms are counted once -- shifted
medians and unbalanced paired tests.  ``--only-tags addressing=47c8a42c``
selects one launch, and the duplicate audit refuses the merge if any
observation key survives twice.  ``--list-tags`` prints what is there.
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

#: Columns that identify one measured observation, per table.  A table's key is
#: the subset of these that its files actually carry, plus ``arm``; two rows
#: sharing a key are the same measurement written twice.  Used by the duplicate
#: audit, which is the guard against merging two launches of one experiment.
KEY_CANDIDATES: dict[str, tuple[str, ...]] = {
    "m0items": ("collection", "seed", "member_id"),
    "m1": ("collection", "seed", "base_id", "edit_kind", "edit_idx"),
    "m2": ("collection", "seed", "series", "pair_id"),
    "m3": ("collection", "seed", "member_id"),
    "m4": ("collection", "seed", "series", "pair_id"),
}


class MergeIntegrityError(Exception):
    """Raised when the merged experiment would carry duplicated observations."""


def _tag_of(path: Path) -> str:
    """The launch tag of a ``rows_<table>__<tag>-<unit>.csv`` file.

    One experiment directory can hold rows from several launches: the campaign
    of 2026-09-06 and the Isal campaign of 2026-09-07 both wrote to
    ``addressing``.  The tag is the only thing in the file name that separates
    them, so it is what a filter selects on.
    """
    stem = path.name.split("__", 1)[-1]
    return stem.split("-", 1)[0]


def _row_files(exp_dir: Path, table: str, tags: Sequence[str] | None = None) -> list[Path]:
    paths = sorted(exp_dir.glob(f"rows_{table}__*.csv"))
    if tags:
        allowed = set(tags)
        paths = [p for p in paths if _tag_of(p) in allowed]
    return paths


def tags_of(exp_dir: Path) -> dict[str, int]:
    """Launch tag -> number of row files carrying it, over every table."""
    counts: dict[str, int] = {}
    for table in TABLES:
        for path in _row_files(exp_dir, table):
            tag = _tag_of(path)
            counts[tag] = counts.get(tag, 0) + 1
    return counts


def arms_of(exp_dir: Path, tags: Sequence[str] | None = None) -> set[str]:
    """Every arm that has at least one row in ``exp_dir``."""
    arms: set[str] = set()
    for table in TABLES:
        for path in _row_files(exp_dir, table, tags):
            try:
                frame = pd.read_csv(path, usecols=["arm"])
            except ValueError:
                continue
            arms.update(frame["arm"].astype(str).unique().tolist())
    return arms


def audit_duplicates(out_dir: Path) -> dict[str, dict[str, int]]:
    """Count rows sharing an observation key in the merged experiment.

    Returns
    -------
    dict
        ``table -> {"rows": n, "unique": u, "duplicate_rows": n - u}`` for every
        table that has rows.  A non-zero ``duplicate_rows`` means one
        observation was written twice -- two launches merged, or a recovery
        sweep re-emitting units the original array already wrote -- which would
        double-count that arm and unbalance every paired test.
    """
    report: dict[str, dict[str, int]] = {}
    for table in TABLES:
        paths = _row_files(out_dir, table)
        if not paths:
            continue
        frames = [pd.read_csv(p) for p in paths]
        frame = pd.concat(frames, ignore_index=True)
        keys = [c for c in (*KEY_CANDIDATES[table], "arm") if c in frame.columns]
        if not keys:
            continue
        unique = len(frame.drop_duplicates(subset=keys))
        report[table] = {
            "rows": int(len(frame)),
            "unique_observations": int(unique),
            "duplicate_rows": int(len(frame) - unique),
            "key": ",".join(keys),
        }  # type: ignore[dict-item]
    return report


def assign_sources(
    root: Path,
    experiments: Sequence[str],
    prefer: dict[str, str],
    tags: dict[str, Sequence[str]] | None = None,
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
    tags = dict(tags or {})
    available: dict[str, set[str]] = {}
    for name in experiments:
        exp_dir = root / RQ_FOLDER / name
        if not exp_dir.is_dir():
            raise FileNotFoundError(f"no experiment directory {exp_dir}")
        available[name] = arms_of(exp_dir, tags.get(name))
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
    tags: dict[str, Sequence[str]] | None = None,
    allow_duplicates: bool = False,
) -> dict[str, str]:
    """Write the merged experiment and return the arm -> source assignment.

    ``out_root`` lets the merged experiment live under another results root
    (e.g. ``.../results/IEEETKDE_isal``) under the analyzer's default
    experiment name ``addressing``, so :mod:`experiments.tkde.analyze_rq1`
    reads it with ``--root`` and no change, and the campaign's own
    ``addressing`` directory stays the frozen record.
    """
    prefer = dict(prefer or {})
    tags = dict(tags or {})
    assignment = assign_sources(root, experiments, prefer, tags)
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
            for path in _row_files(exp_dir, table, tags.get(name)):
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
    duplicates = audit_duplicates(out_dir)
    manifest = {
        "merged_experiment": out_experiment,
        "sources": list(experiments),
        "source_tags_available": {name: tags_of(root / RQ_FOLDER / name) for name in experiments},
        "source_tags_used": {name: list(sel) for name, sel in tags.items()},
        "arm_sources": assignment,
        "row_files_written": written,
        "rows_kept_per_table": kept_rows,
        "duplicate_audit": duplicates,
    }
    (out_dir / "merge_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
    offending = {t: r for t, r in duplicates.items() if r["duplicate_rows"]}
    if offending and not allow_duplicates:
        raise MergeIntegrityError(
            "the merged experiment carries duplicated observations "
            f"{offending}; restrict the sources with --only-tags "
            "(one launch per experiment) or pass --allow-duplicates knowingly. "
            f"Available tags: {manifest['source_tags_available']}"
        )
    if offending:
        logger.warning("merged with duplicated observations: %s", offending)
    logger.info("merged %d row files into %s: %s", written, out_dir, assignment)
    return assignment


def _parse_tags(items: Sequence[str]) -> dict[str, list[str]]:
    """``experiment=tag[,tag]`` pairs -> ``{experiment: [tag, ...]}``."""
    tags: dict[str, list[str]] = {}
    for item in items:
        name, sep, value = item.partition("=")
        if not sep or not name or not value:
            raise argparse.ArgumentTypeError(
                f"--only-tags expects experiment=tag[,tag], got {item!r}"
            )
        tags[name] = [t for t in value.split(",") if t]
    return tags


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
        "--only-tags",
        nargs="*",
        default=(),
        help=(
            "experiment=tag[,tag] -- keep only the row files of these launch "
            "tags for that experiment. One experiment directory can hold two "
            "campaigns; without this the merged table double-counts the arms "
            "they share."
        ),
    )
    parser.add_argument(
        "--list-tags",
        action="store_true",
        help="print the launch tags present in each source experiment and exit",
    )
    parser.add_argument(
        "--allow-duplicates",
        action="store_true",
        help="write the merge even though it carries duplicated observations",
    )
    parser.add_argument(
        "--out-root", type=Path, default=None, help="results root for the merged experiment"
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if args.list_tags:
        for name in args.experiments:
            exp_dir = args.root / RQ_FOLDER / name
            print(f"{name}: {json.dumps(tags_of(exp_dir), sort_keys=True)}")
        return 0
    assignment = merge(
        args.root,
        args.experiments,
        args.out,
        _parse_prefer(args.prefer),
        args.overwrite,
        out_root=args.out_root,
        tags=_parse_tags(args.only_tags),
        allow_duplicates=args.allow_duplicates,
    )
    for arm, name in sorted(assignment.items()):
        print(f"{arm:24s} <- {name}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
