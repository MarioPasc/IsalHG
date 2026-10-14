"""RQ2 analyzer -- the measured-consequences table of ``DESIGN.md`` §3.

Reads every ``rows_<table>__<unit>.csv`` under ``<root>/RQ2_wellposedness/`` and
writes ``summary.json``, ``stats.json`` and ``tables.md``. Every rate carries a
Wilson interval and its ``n``; nothing is tested, because every row of this
research question is descriptive (the design says so explicitly).

Two inputs come from outside this runner and are read, never recomputed:

* **certificate validity** (step 4) at exactly
  ``<root>/RQ2_wellposedness/certificate_validity/rows_certificate.csv`` -- the
  merged file the RQ3 analyzer writes. Per-shard parts under ``parts/`` are
  deliberately **not** globbed: reading both would double-count every row. When
  the file is absent the section is reported ``pending``, not empty, so a
  reader cannot mistake "not measured yet" for "measured and null".
* **identity timing** (step 5) from RQ7's ``rows_yield_members``.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from experiments.tkde.analyze_rq1 import _frame, as_dict, load_table, safe_bca
from experiments.tkde.io import RunPaths, write_stats, write_summary, write_tables_md
from experiments.tkde.stats import wilson_ci

logger = logging.getLogger(__name__)

RQ_FOLDER = "RQ2_wellposedness"
EXPERIMENT = "wellposedness"
CERTIFICATE_FILE = "certificate_validity/rows_certificate.csv"
RQ7_FOLDER = "RQ7_envelope"


def exactness_at_zero(exact0: Any) -> list[dict[str, Any]]:
    """Fraction of isomorphic pairs an arm places at distance 0, with a Wilson CI."""
    import pandas as pd

    if exact0.empty:
        return []
    frame = exact0.copy()
    frame["at_zero"] = pd.to_numeric(frame["at_zero"], errors="coerce")

    rows: list[dict[str, Any]] = []
    for (collection, arm), group in frame.groupby(["collection", "arm"], sort=True):
        usable = group[group["at_zero"].notna()]
        successes = int(usable["at_zero"].sum())
        rows.append(
            {
                "collection": collection,
                "arm": arm,
                "n_pairs": int(len(group)),
                "n_usable": int(len(usable)),
                "n_censored": int((group["censored"] != 0).sum()),
                "n_at_zero": successes,
                "rate": as_dict(wilson_ci(successes, max(1, int(len(usable)))))
                if len(usable)
                else None,
                "median_secs": float(group["secs"].median()),
            }
        )
    return rows


def census(rows: Any) -> list[dict[str, Any]]:
    """False-merge rate per collection and arm, over the non-isomorphic pairs."""
    import pandas as pd

    if rows.empty:
        return []
    frame = rows.copy()
    for column in ("n_false_merges", "n_noniso_pairs", "n_classes_arm", "n_classes_true"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    out: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        merges = row["n_false_merges"]
        noniso = row["n_noniso_pairs"]
        rate = None
        if merges == merges and noniso == noniso and noniso > 0:
            rate = as_dict(wilson_ci(int(merges), int(noniso)))
        out.append(
            {
                "collection": row["collection"],
                "arm": row["arm"],
                "source": row.get("source", ""),
                "n_members": row["n_members"],
                "n_noniso_pairs": None if noniso != noniso else int(noniso),
                "n_false_merges": None if merges != merges else int(merges),
                "false_merge_rate": rate,
                "n_classes_arm": None
                if row["n_classes_arm"] != row["n_classes_arm"]
                else int(row["n_classes_arm"]),
                "n_classes_true": None
                if row["n_classes_true"] != row["n_classes_true"]
                else int(row["n_classes_true"]),
                "error": row.get("error", ""),
            }
        )
    return out


def bipartite(rows: Any) -> dict[str, Any]:
    """Asymmetry, triangle-violation and false-zero rates, plus the smallest witness."""
    import pandas as pd

    if rows.empty:
        return {"rates": [], "smallest_violating_triple": None}
    frame = rows.copy()
    for column in ("d_ab", "d_ba", "d_bc", "d_ac", "violation"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    rates: list[dict[str, Any]] = []
    for (collection, kind, arm), group in frame.groupby(["collection", "kind", "arm"], sort=True):
        usable = group[group["violation"].notna()]
        successes = int(usable["violation"].sum())
        rates.append(
            {
                "collection": collection,
                "kind": kind,
                "arm": arm,
                "n": int(len(usable)),
                "n_censored": int((group["censored"] != 0).sum()),
                "n_violations": successes,
                "rate": as_dict(wilson_ci(successes, max(1, int(len(usable)))))
                if len(usable)
                else None,
            }
        )

    triples = frame[(frame["kind"] == "triple") & (frame["violation"] == 1)].copy()
    smallest = None
    if not triples.empty:
        triples["slack"] = triples["d_ac"] - (triples["d_ab"] + triples["d_bc"])
        triples["mass"] = triples["d_ab"] + triples["d_bc"] + triples["d_ac"]
        row = triples.sort_values(["mass", "ids"]).iloc[0]
        smallest = {
            "collection": row["collection"],
            "ids": row["ids"],
            "d_ab": float(row["d_ab"]),
            "d_bc": float(row["d_bc"]),
            "d_ac": float(row["d_ac"]),
            "excess": float(row["slack"]),
        }
    return {"rates": rates, "smallest_violating_triple": smallest}


def oracle(rows: Any) -> list[dict[str, Any]]:
    """Completion rate and median time of the exact oracle per ``n`` stratum."""
    import pandas as pd

    if rows.empty:
        return []
    frame = rows.copy()
    frame["secs"] = pd.to_numeric(frame["secs"], errors="coerce")

    out: list[dict[str, Any]] = []
    for (collection, stratum), group in frame.groupby(["collection", "stratum"], sort=True):
        completed = group[(group["censored"] == 0) & (group["error"].fillna("") == "")]
        out.append(
            {
                "collection": collection,
                "stratum": stratum,
                "n_pairs": int(len(group)),
                "n_completed": int(len(completed)),
                "completion_rate": as_dict(wilson_ci(int(len(completed)), max(1, int(len(group))))),
                "median_secs": float(completed["secs"].median()) if not completed.empty else None,
                "p90_secs": float(completed["secs"].quantile(0.9)) if not completed.empty else None,
                "median_secs_ci": safe_bca(completed["secs"].to_numpy(dtype=float)),
            }
        )
    return out


def hypercot(rows: Any) -> list[dict[str, Any]]:
    """The single gated HyperCOT timing row per collection."""
    import pandas as pd

    if rows.empty:
        return []
    frame = rows.copy()
    frame["secs"] = pd.to_numeric(frame["secs"], errors="coerce")
    return [
        {
            "collection": collection,
            "n_pairs": int(len(group)),
            "n_censored": int((group["censored"] != 0).sum()),
            "median_secs": float(group["secs"].median()),
            "p90_secs": float(group["secs"].quantile(0.9)),
        }
        for collection, group in frame.groupby("collection", sort=True)
    ]


def certificate(root: Path) -> dict[str, Any]:
    """Read the merged certificate-validity file, or report the section pending."""
    import pandas as pd

    target = Path(root) / RQ_FOLDER / CERTIFICATE_FILE
    if not target.is_file():
        return {"status": "pending", "path": str(target), "rows": []}
    try:
        frame = pd.read_csv(target)
    except (OSError, ValueError) as exc:
        return {"status": "unreadable", "path": str(target), "error": str(exc), "rows": []}
    if frame.empty:
        return {"status": "empty", "path": str(target), "rows": []}

    frame["invalid"] = pd.to_numeric(frame["invalid"], errors="coerce")
    rows = []
    for arm, group in frame.groupby("arm", sort=True):
        usable = group[group["invalid"].notna()]
        invalid = int(usable["invalid"].sum())
        rows.append(
            {
                "arm": arm,
                "n_collections": int(len(group)),
                "n_invalid": invalid,
                "invalid_rate": as_dict(wilson_ci(invalid, max(1, int(len(usable))))),
            }
        )
    return {"status": "read", "path": str(target), "rows": rows}


def identity_timing(root: Path) -> list[dict[str, Any]]:
    """Step 5: canonicalization time per member and arm, read off RQ7's yield rows."""
    import pandas as pd

    frame = load_table(root, RQ7_FOLDER, "yield_members")
    if frame.empty:
        return []
    frame["secs"] = pd.to_numeric(frame["secs"], errors="coerce")
    completed = frame[frame["censored"] == 0]
    return [
        {
            "collection": collection,
            "arm": arm,
            "n_members": int(len(group)),
            "n_completed": int((group["censored"] == 0).sum()),
            "median_secs": (
                float(
                    completed[(completed["collection"] == collection) & (completed["arm"] == arm)][
                        "secs"
                    ].median()
                )
                if not completed.empty
                else None
            ),
        }
        for (collection, arm), group in frame.groupby(["collection", "arm"], sort=True)
    ]


def _rate(value: Any) -> Any:
    return None if not isinstance(value, Mapping) else value.get("point")


def build_tables(summary: Mapping[str, Any]) -> dict[str, Any]:
    """The consequences table plus its supporting per-step tables."""
    import pandas as pd

    consequences = []
    zero_by_arm = {(row["collection"], row["arm"]): _rate(row["rate"]) for row in summary["exact0"]}
    for row in summary["census"]:
        consequences.append(
            {
                "collection": row["collection"],
                "arm": row["arm"],
                "iso -> 0 rate": zero_by_arm.get((row["collection"], row["arm"])),
                "false merges": row["n_false_merges"],
                "false-merge rate": _rate(row["false_merge_rate"]),
                "classes (arm)": row["n_classes_arm"],
                "classes (true)": row["n_classes_true"],
            }
        )

    return {
        "The measured consequences": pd.DataFrame(consequences),
        "Step 0 -- exactness at zero": _frame(
            summary["exact0"],
            ["collection", "arm", "n_pairs", "n_usable", "n_at_zero", "n_censored", "median_secs"],
        ),
        "Step 1 -- false-merge census": _frame(
            summary["census"],
            [
                "collection",
                "arm",
                "source",
                "n_members",
                "n_noniso_pairs",
                "n_false_merges",
                "n_classes_arm",
                "n_classes_true",
                "error",
            ],
        ),
        "Step 2 -- bipartite metricity": _frame(
            summary["bipartite"]["rates"],
            ["collection", "kind", "arm", "n", "n_violations", "n_censored"],
        ),
        "Step 3 -- oracle ceiling": _frame(
            summary["oracle"],
            ["collection", "stratum", "n_pairs", "n_completed", "median_secs", "p90_secs"],
        ),
        "Step 3 -- HyperCOT timing (gated)": _frame(
            summary["hypercot"], ["collection", "n_pairs", "n_censored", "median_secs", "p90_secs"]
        ),
        "Step 4 -- certificate validity": _frame(
            summary["certificate"]["rows"], ["arm", "n_collections", "n_invalid"]
        ),
        "Step 5 -- identity timing": _frame(
            summary["identity_timing"],
            ["collection", "arm", "n_members", "n_completed", "median_secs"],
        ),
    }


def analyze(root: Path) -> dict[str, Any]:
    """Read the RQ2 rows under ``root`` and write the three analysis files."""
    exact0_rows = load_table(root, RQ_FOLDER, "exact0")
    census_rows = load_table(root, RQ_FOLDER, "census")
    bipartite_rows = load_table(root, RQ_FOLDER, "bipartite")
    oracle_rows = load_table(root, RQ_FOLDER, "oracle")
    hypercot_rows = load_table(root, RQ_FOLDER, "hypercot_timing")

    paths = RunPaths(root=root, rq=RQ_FOLDER, experiment=EXPERIMENT)
    paths.ensure()

    summary = {
        "rq": 2,
        "experiment": EXPERIMENT,
        "row_counts": {
            "exact0": int(len(exact0_rows)),
            "census": int(len(census_rows)),
            "bipartite": int(len(bipartite_rows)),
            "oracle": int(len(oracle_rows)),
            "hypercot_timing": int(len(hypercot_rows)),
        },
        "exact0": exactness_at_zero(exact0_rows),
        "census": census(census_rows),
        "bipartite": bipartite(bipartite_rows),
        "oracle": oracle(oracle_rows),
        "hypercot": hypercot(hypercot_rows),
        "certificate": certificate(root),
        "identity_timing": identity_timing(root),
    }
    stats = {
        "confidence": 0.95,
        "method": (
            "wilson for every rate; BCa for the oracle medians; "
            "no tests (every row of this research question is descriptive)"
        ),
        "exactness_at_zero": [
            {"collection": r["collection"], "arm": r["arm"], "wilson": r["rate"]}
            for r in summary["exact0"]
        ],
        "false_merge_rate": [
            {"collection": r["collection"], "arm": r["arm"], "wilson": r["false_merge_rate"]}
            for r in summary["census"]
        ],
        "bipartite": summary["bipartite"],
        "oracle_completion": [
            {"collection": r["collection"], "stratum": r["stratum"], "wilson": r["completion_rate"]}
            for r in summary["oracle"]
        ],
        "certificate": summary["certificate"],
    }
    write_summary(paths, summary)
    write_stats(paths, stats)
    write_tables_md(paths, build_tables(summary))
    return summary


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(prog="experiments.tkde.analyze_rq2", description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args(argv)
    summary = analyze(args.root)
    print(json.dumps(summary["row_counts"], indent=2))
    print(f"certificate validity: {summary['certificate']['status']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
