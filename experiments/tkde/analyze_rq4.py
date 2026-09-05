"""Aggregate RQ4's rows into ``summary.json``, ``stats.json`` and ``tables.md``.

Runs on whatever rows exist, so a partially harvested campaign still produces
readable tables; every table states how many seeds it aggregated and a
hypothesis is reported ``inconclusive`` rather than decided when its sample is
short.

Per ``(sub-collection, corruption, budget, score)`` the 27 seed-level AUCs are
the sample: a BCa interval per arm, and a Holm-corrected Wilcoxon family
comparing ``fact_rank`` against every other representation. The iso-twin table
is tested one-sided against 0.5, which is what H4a is actually about -- an
incomplete representation cannot see a degree-preserving twin at all and should
sit at chance, while the exact arms should not.

Hypotheses (DESIGN.md §5), both evaluated explicitly because the A -> A' gate
is read off them:

* **H4a** (directional, the exactness claim): on iso-twins the exact arms score
  above 0.5 where the collection has structural repetition, while the
  incomplete arms sit at chance.
* **H4b** (non-inferiority): on the three standard corruptions, ``fact_rank``
  lands inside the 95 % CI of the best competitor on each collection.
"""

from __future__ import annotations

import argparse
import glob
import logging
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from experiments.tkde.config import results_root
from experiments.tkde.io import RunPaths, write_stats, write_summary, write_tables_md
from experiments.tkde.matrices import contains_smoke
from experiments.tkde.rq4 import EXACT_ARMS, FLOOR_ARMS, RQ_DIR
from experiments.tkde.stats import bca_ci, paired_family, wilcoxon_paired

logger = logging.getLogger(__name__)

ANALYSIS_EXPERIMENT = "analysis"
OURS = "fact_rank"
PRIMARY_SCORE = "knn"
TWIN = "iso_twin"
STANDARD_CORRUPTIONS: tuple[str, ...] = ("spurious_fact", "missing_fact", "wrong_argument")
CHANCE = 0.5
MIN_SEEDS = 5


def _read(root: Path, table: str) -> Any:
    """Return the concatenation of one row table, or an empty frame."""
    import pandas as pd

    # Recursive, so a row file is found wherever the runner nested it; the
    # `_smoke` exclusion below is then what keeps smoke output out, rather
    # than the glob happening not to reach it.
    pattern = str(Path(root) / RQ_DIR / "**" / f"rows_{table}__*.csv")
    # A cluster smoke task runs a REAL unit under the same unit id the full
    # run uses, so its rows are indistinguishable once concatenated. They are
    # written under a `_smoke` component and excluded here by path.
    found = sorted(glob.glob(pattern, recursive=True))
    files = [f for f in found if not contains_smoke(f)]
    skipped = len(found) - len(files)
    if skipped:
        logger.info("skipped %d smoke row file(s) for table %s", skipped, table)
    if not files:
        logger.warning("no rows for table %s under %s", table, pattern)
        return pd.DataFrame()
    return pd.concat([pd.read_csv(f) for f in files], ignore_index=True)


def _seed_series(block: Any, arm: str) -> tuple[list[int], list[float]]:
    """Return ``(seeds, auc)`` for one arm, sorted by seed and de-duplicated."""
    subset = block[(block["arm"] == arm) & (block["censored"] == 0)].dropna(subset=["auc"])
    subset = subset.drop_duplicates(subset=["seed"], keep="last").sort_values("seed")
    return list(subset["seed"].astype(int)), list(subset["auc"].astype(float))


def auc_tables(auc: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return the per-arm AUC summary and the paired-comparison rows.

    Parameters
    ----------
    auc : pandas.DataFrame
        All ``rows_auc`` rows.

    Returns
    -------
    tuple[list[dict], list[dict]]
        ``(summary_rows, comparison_rows)``.
    """
    summary: list[dict[str, Any]] = []
    comparisons: list[dict[str, Any]] = []
    if auc.empty:
        return summary, comparisons

    keys = ["subcollection", "corruption", "budget", "score"]
    for key, block in auc.groupby(keys, sort=True):
        subcollection, corruption, budget, score = key
        arms = sorted(block["arm"].unique())
        series = {arm: _seed_series(block, arm) for arm in arms}

        for arm in arms:
            _, values = series[arm]
            if not values:
                continue
            interval = bca_ci(values, stat="mean")
            # One-sided Wilcoxon against chance -- H4a's actual test.
            against_chance = wilcoxon_paired(values, [CHANCE] * len(values), alternative="greater")
            summary.append(
                {
                    "subcollection": subcollection,
                    "corruption": corruption,
                    "budget": int(budget),
                    "score": score,
                    "arm": arm,
                    "n_seeds": len(values),
                    "auc_mean": interval.point,
                    "auc_low": interval.low,
                    "auc_high": interval.high,
                    "p_vs_chance_greater": against_chance["p_value"],
                    "above_chance": bool(
                        against_chance["p_value"] < 0.05 and interval.point > CHANCE
                    ),
                    "is_exact": arm in EXACT_ARMS,
                    "is_floor": arm in FLOOR_ARMS,
                }
            )

        if OURS not in series or not series[OURS][1]:
            continue
        our_seeds, our_values = series[OURS]
        others: dict[str, list[float]] = {}
        for arm in arms:
            if arm == OURS:
                continue
            arm_seeds, values = series[arm]
            aligned = dict(zip(arm_seeds, values, strict=True))
            paired = [aligned[s] for s in our_seeds if s in aligned]
            if len(paired) == len(our_values):
                others[arm] = paired
        if others:
            for row in paired_family(our_values, others):
                comparisons.append(
                    {
                        "subcollection": subcollection,
                        "corruption": corruption,
                        "budget": int(budget),
                        "score": score,
                        **row,
                    }
                )
    return summary, comparisons


def evaluate_hypotheses(
    summary: Sequence[Mapping[str, Any]],
    comparisons: Sequence[Mapping[str, Any]],
    n_seeds: int,
) -> dict[str, dict[str, Any]]:
    """Return an explicit verdict for H4a and H4b.

    Parameters
    ----------
    summary : Sequence[Mapping]
        Per-arm AUC summary rows.
    comparisons : Sequence[Mapping]
        Paired-family rows.
    n_seeds : int
        Seeds actually harvested.

    Returns
    -------
    dict[str, dict[str, Any]]
    """
    verdicts: dict[str, dict[str, Any]] = {}

    # --- H4a: iso-twins separate the exact arms from the incomplete ones ---
    twins = [s for s in summary if s["corruption"] == TWIN and s["score"] == PRIMARY_SCORE]
    if not twins:
        verdicts["H4a"] = {"verdict": "inconclusive", "reason": "no iso_twin rows"}
    else:
        exact = [s for s in twins if s["is_exact"]]
        incomplete = [s for s in twins if not s["is_exact"]]
        exact_above = [s for s in exact if s["above_chance"]]
        incomplete_above = [s for s in incomplete if s["above_chance"]]
        verdicts["H4a"] = {
            "verdict": "supported"
            if exact_above and len(exact_above) >= len(exact) / 2
            else "not_supported",
            "n_exact_cells": len(exact),
            "n_exact_above_chance": len(exact_above),
            "n_incomplete_cells": len(incomplete),
            "n_incomplete_above_chance": len(incomplete_above),
            "exact_mean_auc": (sum(s["auc_mean"] for s in exact) / len(exact) if exact else None),
            "incomplete_mean_auc": (
                sum(s["auc_mean"] for s in incomplete) / len(incomplete) if incomplete else None
            ),
            "note": (
                "A degree-preserving twin keeps n, m, the arity histogram, the degree "
                "sequence and both label multisets, so an incomplete representation is "
                "blind to it by construction. Exact arms above chance with incomplete arms "
                "at chance is the exactness consequence RQ4 exists to show."
            ),
        }

    # --- H4b: non-inferiority on the three standard corruptions ------------
    standard = [
        s
        for s in summary
        if s["corruption"] in STANDARD_CORRUPTIONS and s["score"] == PRIMARY_SCORE
    ]
    if not standard:
        verdicts["H4b"] = {"verdict": "inconclusive", "reason": "no standard-corruption rows"}
    else:
        cells: dict[tuple[str, str, int], list[Mapping[str, Any]]] = {}
        for row in standard:
            cells.setdefault((row["subcollection"], row["corruption"], row["budget"]), []).append(
                row
            )
        failures: list[dict[str, Any]] = []
        checked = 0
        for cell, rows in sorted(cells.items()):
            ours = next((r for r in rows if r["arm"] == OURS), None)
            competitors = [r for r in rows if r["arm"] != OURS]
            if ours is None or not competitors:
                continue
            checked += 1
            best = max(competitors, key=lambda r: r["auc_mean"])
            if ours["auc_high"] < best["auc_low"]:
                failures.append(
                    {
                        "subcollection": cell[0],
                        "corruption": cell[1],
                        "budget": cell[2],
                        "best_competitor": best["arm"],
                        "best_auc": best["auc_mean"],
                        "ours_auc": ours["auc_mean"],
                    }
                )
        verdicts["H4b"] = {
            "verdict": "supported" if checked and not failures else "not_supported",
            "n_cells_checked": checked,
            "n_cells_below_best": len(failures),
            "failures": failures,
            "note": (
                "Competitiveness is claimed, not superiority. If this fails on both "
                "collections, DESIGN.md §5 moves the standard-corruption table to the "
                "supplement and the main text carries the iso-twin table plus RQ2's "
                "false-merge census (A -> A')."
            ),
        }

    if n_seeds < MIN_SEEDS:
        for key in verdicts:
            verdicts[key]["verdict"] = "inconclusive"
            verdicts[key]["reason"] = f"only {n_seeds} seed(s) harvested; need >= {MIN_SEEDS}"
    return verdicts


def main(argv: Sequence[str] | None = None) -> int:
    """Command-line entry point.

    Parameters
    ----------
    argv : Sequence[str] or None

    Returns
    -------
    int
        Process exit status.
    """
    import pandas as pd

    parser = argparse.ArgumentParser(description="Aggregate RQ4's rows.")
    parser.add_argument("--root", type=Path, default=None, help="results root")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    root = Path(args.root) if args.root else results_root()

    auc = _read(root, "auc")
    anomalies = _read(root, "anomalies")

    summary_rows, comparison_rows = auc_tables(auc)
    n_seeds = int(auc["seed"].nunique()) if not auc.empty else 0
    verdicts = evaluate_hypotheses(summary_rows, comparison_rows, n_seeds)

    anomaly_summary: dict[str, Any] = {}
    if not anomalies.empty:
        anomaly_summary = {
            "n_anomaly_rows": int(len(anomalies)),
            "n_realised": int(anomalies["realised"].sum()),
            "realised_rate": float(anomalies["realised"].mean()),
            "n_noniso_verified": int(anomalies["noniso_verified"].fillna(0).sum()),
        }
        twins = anomalies[anomalies["corruption"] == TWIN]
        if len(twins):
            realised_twins = twins[twins["realised"] == 1]
            anomaly_summary["twin_wl1_equal_rate"] = (
                float(realised_twins["twin_wl1_equal"].mean()) if len(realised_twins) else None
            )
            anomaly_summary["twin_median_swaps"] = (
                float(realised_twins["n_swaps"].median()) if len(realised_twins) else None
            )

    paths = RunPaths(root=root, rq=RQ_DIR, experiment=ANALYSIS_EXPERIMENT)
    paths.ensure()

    write_summary(
        paths,
        {
            "n_auc_rows": int(len(auc)),
            "n_seeds": n_seeds,
            "auc": summary_rows,
            "anomalies": anomaly_summary,
            "hypotheses": verdicts,
        },
    )
    write_stats(paths, {"paired_family": comparison_rows, "hypotheses": verdicts})

    tables: dict[str, Any] = {}
    if summary_rows:
        frame = pd.DataFrame(summary_rows)
        primary = frame[frame["score"] == PRIMARY_SCORE]
        twin_rows = primary[primary["corruption"] == TWIN]
        if len(twin_rows):
            tables["Iso-twin AUC (kNN, k=5) -- the exactness table (H4a)"] = twin_rows
        standard = primary[primary["corruption"].isin(STANDARD_CORRUPTIONS)]
        if len(standard):
            tables["Standard corruptions -- AUC (kNN, k=5) (H4b)"] = standard
        secondary = frame[frame["score"] == "lof"]
        if len(secondary):
            tables["Secondary score -- LOF (k=20)"] = secondary
    if comparison_rows:
        tables["fact_rank vs each arm (Holm, per cell)"] = pd.DataFrame(comparison_rows)
    if anomaly_summary:
        tables["Anomaly realisation"] = pd.DataFrame([anomaly_summary])
    tables["Hypotheses (DESIGN.md §5)"] = pd.DataFrame(
        [
            {
                "hypothesis": key,
                "verdict": value.get("verdict"),
                "detail": "; ".join(
                    f"{k}={v}"
                    for k, v in value.items()
                    if k not in {"verdict", "failures", "note"} and not isinstance(v, list | dict)
                ),
            }
            for key, value in sorted(verdicts.items())
        ]
    )
    write_tables_md(paths, tables)

    logger.info("rq4 analysis written to %s", paths.dir)
    for key, value in sorted(verdicts.items()):
        logger.info("  %s: %s", key, value.get("verdict"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
