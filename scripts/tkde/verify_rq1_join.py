"""Verify that several RQ1 experiments were run on identical seeded units.

The 2026-09-07 Isal RQ1 measurement is three experiments (``addressing``,
``addressing_rank``, ``addressing_cpp``) launched from the same corpus seeds so
that their rows can be merged one-source-per-arm and compared with *paired*
statistics (Wilcoxon over arms on the same edit).  That pairing is only sound
if the experiments agree on the units they measured.  This script asserts it
before the merge is trusted:

* **M1** unit key ``(collection, seed, base_id, edit_kind, edit_idx)`` -- the
  seeded single edits.  Every pair of experiments must agree on the key set,
  restricted to the collections both of them cover.
* **M0** item key ``(collection, seed, member_id)``.
* **M3** member key ``(collection, seed, member_id)``.

Only the key columns are read, so the whole check stays inside a few hundred
MB for a ~700 MB row tree.  Coverage per ``(experiment, arm)`` is reported as
well, because an arm whose rows cover fewer units than its comparison arm
would silently unbalance the paired tests.

Run it on the cluster login node (the rows live there) or against a harvested
copy on the drive.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

#: The per-table join keys.  ``arm`` is deliberately not a key: the point of
#: the merge is that different arms come from different experiments.
KEYS: dict[str, tuple[str, ...]] = {
    "m1": ("collection", "seed", "base_id", "edit_kind", "edit_idx"),
    "m0items": ("collection", "seed", "member_id"),
    "m3": ("collection", "seed", "member_id"),
}


class JoinVerificationError(Exception):
    """Raised when the experiments do not share their seeded units."""


def _tag_of(path: Path) -> str:
    """The launch tag of a ``rows_<table>__<tag>-<unit>.csv`` file."""
    return path.name.split("__", 1)[-1].split("-", 1)[0]


def _read_keys(exp_dir: Path, table: str, tags: Sequence[str] | None = None) -> pd.DataFrame:
    """Read the key columns plus ``arm`` from every row file of ``table``."""
    keys = KEYS[table]
    frames: list[pd.DataFrame] = []
    paths = sorted(exp_dir.glob(f"rows_{table}__*.csv"))
    if tags:
        allowed = set(tags)
        paths = [p for p in paths if _tag_of(p) in allowed]
    for path in paths:
        try:
            frames.append(pd.read_csv(path, usecols=[*keys, "arm"]))
        except ValueError as exc:  # a row file without the expected columns
            logger.warning("skipping %s: %s", path.name, exc)
    if not frames:
        return pd.DataFrame(columns=[*keys, "arm"])
    return pd.concat(frames, ignore_index=True)


def _unit_set(frame: pd.DataFrame, table: str) -> set[tuple]:
    keys = list(KEYS[table])
    if frame.empty:
        return set()
    return set(map(tuple, frame[keys].astype(str).itertuples(index=False, name=None)))


def _restrict(units: set[tuple], collections: set[str]) -> set[tuple]:
    return {u for u in units if u[0] in collections}


def verify_table(
    exp_dirs: dict[str, Path],
    table: str,
    tags: dict[str, Sequence[str]] | None = None,
) -> tuple[dict[str, object], list[str]]:
    """Compare one table's unit sets across experiments.

    Returns
    -------
    report : dict
        Per-experiment unit counts, per-``(experiment, arm)`` coverage, and the
        pairwise symmetric differences restricted to shared collections.
    problems : list of str
        Human-readable violations; empty when the join is sound.
    """
    problems: list[str] = []
    tags = dict(tags or {})
    frames = {name: _read_keys(path, table, tags.get(name)) for name, path in exp_dirs.items()}
    units = {name: _unit_set(frame, table) for name, frame in frames.items()}
    collections = {
        name: set(frame["collection"].astype(str).unique()) if not frame.empty else set()
        for name, frame in frames.items()
    }

    coverage: dict[str, dict[str, int]] = {}
    for name, frame in frames.items():
        if frame.empty:
            coverage[name] = {}
            continue
        keys = list(KEYS[table])
        per_arm = frame.groupby("arm")[keys[0]].size().to_dict()
        n_units_per_arm = (
            frame.astype({c: str for c in keys})
            .groupby("arm")[keys]
            .apply(lambda g: len(set(map(tuple, g.itertuples(index=False, name=None)))))
            .to_dict()
        )
        coverage[name] = {str(arm): int(n_units_per_arm[arm]) for arm in sorted(per_arm)}

    pairwise: dict[str, dict[str, int]] = {}
    names = sorted(exp_dirs)
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            shared = collections[a] & collections[b]
            if not shared:
                continue
            ua, ub = _restrict(units[a], shared), _restrict(units[b], shared)
            only_a, only_b = ua - ub, ub - ua
            pairwise[f"{a}|{b}"] = {
                "shared_collections": len(shared),
                "units_a": len(ua),
                "units_b": len(ub),
                "only_a": len(only_a),
                "only_b": len(only_b),
            }
            if only_a or only_b:
                sample_a = sorted(only_a)[:3]
                sample_b = sorted(only_b)[:3]
                problems.append(
                    f"{table}: {a} vs {b} disagree on shared collections "
                    f"{sorted(shared)}: {len(only_a)} only in {a} "
                    f"(e.g. {sample_a}), {len(only_b)} only in {b} "
                    f"(e.g. {sample_b})"
                )

    report = {
        "table": table,
        "units_per_experiment": {n: len(u) for n, u in units.items()},
        "collections_per_experiment": {n: sorted(c) for n, c in collections.items()},
        "units_per_experiment_arm": coverage,
        "pairwise": pairwise,
    }
    return report, problems


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        required=True,
        help="directory holding the experiment directories (e.g. .../RQ1_addressing)",
    )
    parser.add_argument(
        "--experiments",
        nargs="+",
        required=True,
        help="experiment directory names to compare",
    )
    parser.add_argument(
        "--tables",
        nargs="+",
        default=["m1", "m0items", "m3"],
        choices=sorted(KEYS),
    )
    parser.add_argument(
        "--only-tags",
        nargs="*",
        default=(),
        help=(
            "experiment=tag[,tag] -- restrict to these launch tags. An "
            "experiment directory can hold more than one campaign."
        ),
    )
    parser.add_argument("--out", type=Path, default=None, help="write the report JSON")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    tag_filter: dict[str, Sequence[str]] = {}
    for item in args.only_tags:
        name, sep, value = item.partition("=")
        if not sep or not name or not value:
            raise JoinVerificationError(f"--only-tags expects experiment=tag[,tag], got {item!r}")
        tag_filter[name] = [t for t in value.split(",") if t]

    exp_dirs = {name: args.root / name for name in args.experiments}
    missing = [n for n, p in exp_dirs.items() if not p.is_dir()]
    if missing:
        raise JoinVerificationError(f"missing experiment directories: {missing}")

    reports: list[dict[str, object]] = []
    all_problems: list[str] = []
    for table in args.tables:
        report, problems = verify_table(exp_dirs, table, tag_filter)
        reports.append(report)
        all_problems.extend(problems)
        logger.info("--- %s ---", table)
        logger.info("units per experiment: %s", json.dumps(report["units_per_experiment"]))
        for name, arms in report["units_per_experiment_arm"].items():  # type: ignore[union-attr]
            logger.info("  %s arms: %s", name, json.dumps(arms))
        for pair, stats in report["pairwise"].items():  # type: ignore[union-attr]
            logger.info("  %s: %s", pair, json.dumps(stats))

    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({"tables": reports, "problems": all_problems}, indent=2))
        logger.info("wrote %s", args.out)

    if all_problems:
        logger.error("JOIN NOT SOUND (%d problems):", len(all_problems))
        for p in all_problems:
            logger.error("  %s", p)
        return 1
    logger.info("JOIN SOUND: every pair agrees on its shared collections.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
