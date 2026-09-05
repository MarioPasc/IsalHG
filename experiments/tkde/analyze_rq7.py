"""RQ7 analyzer -- the operating-envelope tables of ``DESIGN.md`` §8.

Reads every ``rows_<table>__<unit>.csv`` under ``<root>/RQ7_envelope/`` and
writes ``summary.json``, ``stats.json``, ``tables.md`` and the design's
aggregate ``rows_yield.csv``.

Censored instances are excluded from every median and counted separately (G5's
censoring rule): a median that quietly included a 60 s time-out as if it were a
measurement would report the budget, not the cost.

No tests are run -- the design asks for bootstrap intervals of medians and
nothing else.
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

RQ_FOLDER = "RQ7_envelope"
EXPERIMENT = "envelope"
BUCKET_ORDER = ("<=8", "9-12", "13-16", "17-20", "21-24", ">24")


def sweep(rows: Any) -> list[dict[str, Any]]:
    """Median and p90 wall-clock, time-out fraction and tokens per cell and arm."""
    import pandas as pd

    if rows.empty:
        return []
    frame = rows.copy()
    frame["secs"] = pd.to_numeric(frame["secs"], errors="coerce")
    frame["tokens_or_bytes"] = pd.to_numeric(frame["tokens_or_bytes"], errors="coerce")

    out: list[dict[str, Any]] = []
    for (cell, arm), group in frame.groupby(["cell", "arm"], sort=True):
        completed = group[group["censored"] == 0]
        censored = int((group["censored"] != 0).sum())
        first = group.iloc[0]
        out.append(
            {
                "cell": cell,
                "m": int(first["m"]),
                "k": int(first["k"]),
                "sigma_e": int(first["sigma_e"]),
                "sigma_v": int(first["sigma_v"]),
                "density": first["density"],
                "n": int(first["n"]),
                "arm": arm,
                "n_instances": int(len(group)),
                "n_censored": censored,
                "timeout_fraction": as_dict(wilson_ci(censored, max(1, int(len(group))))),
                "median_secs": float(completed["secs"].median()) if not completed.empty else None,
                "p90_secs": (
                    float(completed["secs"].quantile(0.9)) if not completed.empty else None
                ),
                "median_secs_ci": safe_bca(completed["secs"].to_numpy(dtype=float)),
                "median_tokens": (
                    float(completed["tokens_or_bytes"].median()) if not completed.empty else None
                ),
            }
        )
    return out


def yield_table(rows: Any) -> Any:
    """Reduce the per-member yield rows to the design's ``rows_yield`` schema."""
    import pandas as pd

    if rows.empty:
        return pd.DataFrame()
    frame = rows.copy()
    frame["secs"] = pd.to_numeric(frame["secs"], errors="coerce")

    records: list[dict[str, Any]] = []
    for (collection, bucket, arm), group in frame.groupby(
        ["collection", "bucket", "arm"], sort=True
    ):
        completed = group[group["censored"] == 0]
        records.append(
            {
                "collection": collection,
                "bucket": bucket,
                "arm": arm,
                "n_members": int(len(group)),
                "n_completed": int(len(completed)),
                "median_secs": float(completed["secs"].median()) if not completed.empty else "",
                "p90_secs": (float(completed["secs"].quantile(0.9)) if not completed.empty else ""),
            }
        )
    table = pd.DataFrame(records)
    if table.empty:
        return table
    order = {name: index for index, name in enumerate(BUCKET_ORDER)}
    table["_order"] = table["bucket"].map(lambda b: order.get(b, len(order)))
    return table.sort_values(["collection", "arm", "_order"]).drop(columns="_order")


def yield_summary(table: Any) -> list[dict[str, Any]]:
    """The yield rows with a completion interval attached."""
    if table.empty:
        return []
    rows: list[dict[str, Any]] = []
    for record in table.to_dict("records"):
        rows.append(
            {
                **record,
                "completion_rate": as_dict(
                    wilson_ci(int(record["n_completed"]), max(1, int(record["n_members"])))
                ),
            }
        )
    return rows


def nscaling(rows: Any) -> list[dict[str, Any]]:
    """The ``N``-scaling curve inputs: mean seconds per ``(arm, N)`` over repetitions."""
    import pandas as pd

    if rows.empty:
        return []
    frame = rows.copy()
    for column in ("secs_canon_total", "secs_pairs_total"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    out: list[dict[str, Any]] = []
    for (collection, arm, size), group in frame.groupby(["collection", "arm", "N"], sort=True):
        completed = group[(group["censored"] == 0) & (group["skipped"] == 0)]
        out.append(
            {
                "collection": collection,
                "arm": arm,
                "N": int(size),
                "n_reps": int(len(group)),
                "n_completed": int(len(completed)),
                "n_censored": int((group["censored"] != 0).sum()),
                "n_skipped": int((group["skipped"] != 0).sum()),
                "mean_secs_canon_total": (
                    float(completed["secs_canon_total"].mean()) if not completed.empty else None
                ),
                "mean_secs_pairs_total": (
                    float(completed["secs_pairs_total"].mean()) if not completed.empty else None
                ),
                "secs_pairs_ci": safe_bca(
                    completed["secs_pairs_total"].to_numpy(dtype=float), stat="mean"
                ),
            }
        )
    return out


def frontier(sweep_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """H7a: the largest ``m`` each arm clears at every ``k``, without time-outs.

    Reported per ``(arm, k)`` because the hypothesis is about ``m`` being the
    frontier and ``k`` and the vocabularies being the tie-breakers; a cell that
    censored any of its 27 instances does not count as cleared.
    """
    best: dict[tuple[str, int], dict[str, Any]] = {}
    for row in sweep_rows:
        if row["n_censored"]:
            continue
        key = (row["arm"], row["k"])
        current = best.get(key)
        if current is None or row["m"] > current["max_m_clear"]:
            best[key] = {
                "arm": row["arm"],
                "k": row["k"],
                "max_m_clear": row["m"],
                "at_cell": row["cell"],
                "median_secs": row["median_secs"],
            }
    return [best[key] for key in sorted(best)]


def build_tables(summary: Mapping[str, Any], yield_rows: Any) -> dict[str, Any]:
    """The human-readable tables written to ``tables.md``."""
    import pandas as pd

    return {
        "Sweep -- cost per cell": pd.DataFrame(
            [
                {
                    "cell": row["cell"],
                    "m": row["m"],
                    "k": row["k"],
                    "|Sigma_E|": row["sigma_e"],
                    "|Sigma_V|": row["sigma_v"],
                    "density": row["density"],
                    "n": row["n"],
                    "arm": row["arm"],
                    "instances": row["n_instances"],
                    "timeouts": row["n_censored"],
                    "median_secs": row["median_secs"],
                    "p90_secs": row["p90_secs"],
                    "median_tokens": row["median_tokens"],
                }
                for row in summary["sweep"]
            ]
        ),
        "Frontier -- largest m cleared with no time-out": _frame(
            summary["frontier"], ["arm", "k", "max_m_clear", "at_cell", "median_secs"]
        ),
        "Yield -- real collections by size bucket": (
            yield_rows if not yield_rows.empty else pd.DataFrame()
        ),
        "N-scaling on wd50k66": _frame(
            summary["nscaling"],
            [
                "arm",
                "N",
                "n_reps",
                "n_completed",
                "n_censored",
                "n_skipped",
                "mean_secs_canon_total",
                "mean_secs_pairs_total",
            ],
        ),
    }


def analyze(root: Path) -> dict[str, Any]:
    """Read the RQ7 rows under ``root`` and write the analysis files."""
    sweep_rows = load_table(root, RQ_FOLDER, "sweep")
    yield_members = load_table(root, RQ_FOLDER, "yield_members")
    nscaling_rows = load_table(root, RQ_FOLDER, "nscaling")

    paths = RunPaths(root=root, rq=RQ_FOLDER, experiment=EXPERIMENT)
    paths.ensure()

    table = yield_table(yield_members)
    if not table.empty:
        table.to_csv(paths.dir / "rows_yield.csv", index=False)

    sweep_summary = sweep(sweep_rows)
    summary = {
        "rq": 7,
        "experiment": EXPERIMENT,
        "row_counts": {
            "sweep": int(len(sweep_rows)),
            "yield_members": int(len(yield_members)),
            "nscaling": int(len(nscaling_rows)),
        },
        "sweep": sweep_summary,
        "frontier": frontier(sweep_summary),
        "yield": yield_summary(table),
        "nscaling": nscaling(nscaling_rows),
    }
    stats = {
        "confidence": 0.95,
        "method": (
            "BCa bootstrap for medians and means; Wilson for the time-out and "
            "completion fractions; no tests"
        ),
        "sweep_medians": [
            {"cell": row["cell"], "arm": row["arm"], "median_secs_ci": row["median_secs_ci"]}
            for row in sweep_summary
        ],
        "timeout_fractions": [
            {"cell": row["cell"], "arm": row["arm"], "wilson": row["timeout_fraction"]}
            for row in sweep_summary
        ],
        "yield_completion": [
            {
                "collection": row["collection"],
                "bucket": row["bucket"],
                "arm": row["arm"],
                "wilson": row["completion_rate"],
            }
            for row in summary["yield"]
        ],
        "nscaling": summary["nscaling"],
    }
    write_summary(paths, summary)
    write_stats(paths, stats)
    write_tables_md(paths, build_tables(summary, table))
    return summary


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(prog="experiments.tkde.analyze_rq7", description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args(argv)
    summary = analyze(args.root)
    print(json.dumps(summary["row_counts"], indent=2))
    for row in summary["frontier"]:
        print(f"frontier {row['arm']:>22} k={row['k']}: largest clean m = {row['max_m_clear']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
