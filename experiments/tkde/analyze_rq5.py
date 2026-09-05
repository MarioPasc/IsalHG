"""Aggregate RQ5's rows into ``summary.json``, ``stats.json`` and ``tables.md``.

Runs on whatever rows exist, so a partially harvested campaign still produces
readable tables; every table states the number of seeds it aggregated, and a
hypothesis is reported as ``inconclusive`` rather than decided when its sample
is short.

The primary comparison is the **balanced** design: one ARI per seed per arm,
27 paired observations, ``fact_rank`` against every other arm with a
Holm-corrected Wilcoxon family and matched-pairs rank-biserial effect sizes.
The **full** design contributes one value per arm with its member-level
interval, and the geometry table carries the licences (``nu``, hubness) that
DESIGN.md §6 requires before PAM and metric MDS may be used at all.

The four pre-registered hypotheses of DESIGN.md §6 are each evaluated
explicitly, because the A -> A' gate is read off them:

* **H5a** licences: ``nu(fact_rank) > 0`` with a non-trivial negative Gram
  spectrum, and ``k = 10`` hubness skewness below 1.5.
* **H5b** directional: ``fact_rank`` beats **both** naive floors.
* **H5c** non-inferiority: ``fact_rank`` within the CI of the best labelled
  competitor.
* **H5d** ``fact_rank_roles`` does not lower ARI relative to ``fact_rank``.
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
from experiments.tkde.rq5 import FLOOR_ARMS, RQ_DIR
from experiments.tkde.stats import bca_ci, paired_family

logger = logging.getLogger(__name__)

ANALYSIS_EXPERIMENT = "analysis"
OURS = "fact_rank"
ROLES_ARM = "fact_rank_roles"
LABELLED_COMPETITORS: tuple[str, ...] = ("wl_l1", "nauty_cert", "hpd_jsd", "nauty_cert_rows")
HUBNESS_CEILING = 1.5
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
    frames = [pd.read_csv(f) for f in files]
    return pd.concat(frames, ignore_index=True)


def _seed_series(frame: Any, arm: str) -> tuple[list[int], list[float]]:
    """Return ``(seeds, ari)`` for one arm, sorted by seed and de-duplicated."""
    subset = frame[frame["arm"] == arm].dropna(subset=["ari"])
    subset = subset.drop_duplicates(subset=["seed"], keep="last").sort_values("seed")
    return list(subset["seed"].astype(int)), list(subset["ari"].astype(float))


def balanced_tables(clustering: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return the per-arm balanced summary and the paired-comparison rows.

    Parameters
    ----------
    clustering : pandas.DataFrame
        All ``rows_clustering`` rows.

    Returns
    -------
    tuple[list[dict], list[dict]]
        ``(summary_rows, comparison_rows)``.
    """
    summary: list[dict[str, Any]] = []
    comparisons: list[dict[str, Any]] = []
    if clustering.empty:
        return summary, comparisons

    balanced = clustering[clustering["design"] == "balanced"]
    for (experiment, method), block in balanced.groupby(["experiment", "method"], sort=True):
        arms = sorted(block["arm"].unique())
        series = {arm: _seed_series(block, arm) for arm in arms}
        for arm in arms:
            arm_seeds, values = series[arm]
            if not values:
                continue
            interval = bca_ci(values, stat="mean")
            summary.append(
                {
                    "experiment": experiment,
                    "method": method,
                    "arm": arm,
                    "n_seeds": len(values),
                    "ari_mean": interval.point,
                    "ari_low": interval.low,
                    "ari_high": interval.high,
                    "nmi_mean": float(block[block["arm"] == arm]["nmi"].mean()),
                    "cophenetic_mean": float(block[block["arm"] == arm]["cophenetic"].mean()),
                    "silhouette_mean": float(block[block["arm"] == arm]["silhouette"].mean()),
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
                comparisons.append({"experiment": experiment, "method": method, **row})
    return summary, comparisons


def geometry_table(geometry: Any) -> list[dict[str, Any]]:
    """Return the geometry rows, one per ``(experiment, arm)``."""
    if geometry.empty:
        return []
    columns = [
        "experiment",
        "collection",
        "arm",
        "N",
        "nu",
        "n_negative_eigen",
        "largest_negative",
        "hubness_skew_k10",
        "hubness_max_occurrence",
        "diameter_over_median",
    ]
    present = [c for c in columns if c in geometry.columns]
    return geometry[present].sort_values(["experiment", "arm"]).to_dict("records")


def evaluate_hypotheses(
    summary: Sequence[Mapping[str, Any]],
    comparisons: Sequence[Mapping[str, Any]],
    geometry: Sequence[Mapping[str, Any]],
    clustering: Any,
) -> dict[str, dict[str, Any]]:
    """Return an explicit verdict per pre-registered hypothesis.

    A verdict is ``supported``, ``not_supported`` or ``inconclusive``; the last
    is used whenever the evidence needed is absent or the seed count is too
    short to test, so a missing measurement never reads as a negative result.

    Parameters
    ----------
    summary : Sequence[Mapping]
        Balanced per-arm summary rows.
    comparisons : Sequence[Mapping]
        Paired-family rows.
    geometry : Sequence[Mapping]
        Geometry rows.
    clustering : pandas.DataFrame
        All clustering rows (for the full design's values).

    Returns
    -------
    dict[str, dict[str, Any]]
        Keyed by hypothesis id.
    """
    verdicts: dict[str, dict[str, Any]] = {}

    # --- H5a: the licences ------------------------------------------------
    ours_geometry = [g for g in geometry if g.get("arm") == OURS]
    if not ours_geometry:
        verdicts["H5a"] = {"verdict": "inconclusive", "reason": "no geometry rows for fact_rank"}
    else:
        row = ours_geometry[0]
        nu_positive = float(row["nu"]) > 0.0
        spectrum = int(row["n_negative_eigen"]) > 0
        hub = float(row["hubness_skew_k10"])
        verdicts["H5a"] = {
            "verdict": "supported"
            if (nu_positive and spectrum and hub < HUBNESS_CEILING)
            else "not_supported",
            "nu": float(row["nu"]),
            "n_negative_eigen": int(row["n_negative_eigen"]),
            "hubness_skew_k10": hub,
            "hubness_ceiling": HUBNESS_CEILING,
            "nu_positive": nu_positive,
            "non_trivial_negative_spectrum": spectrum,
            "hubness_moderate": hub < HUBNESS_CEILING,
            "note": (
                "nu > 0 licenses PAM over centroid methods and metric MDS over classical MDS; "
                "the hubness clause is the kNN precondition and is reported separately, so a "
                "failure of the hubness half does not withdraw the PAM licence."
            ),
        }

    # --- H5b: directional, against BOTH naive floors ----------------------
    floor_rows = [
        c for c in comparisons if c.get("name") in FLOOR_ARMS and c.get("method") == "pam"
    ]
    if not floor_rows:
        verdicts["H5b"] = {"verdict": "inconclusive", "reason": "no paired floor comparisons"}
    else:
        beaten = [
            c
            for c in floor_rows
            if float(c["mean_ours"]) > float(c["mean_other"]) and bool(c["reject"])
        ]
        verdicts["H5b"] = {
            "verdict": "supported" if len(beaten) == len(floor_rows) else "not_supported",
            "n_floor_comparisons": len(floor_rows),
            "n_significantly_beaten": len(beaten),
            "detail": [
                {
                    "experiment": c["experiment"],
                    "floor": c["name"],
                    "mean_ours": c["mean_ours"],
                    "mean_floor": c["mean_other"],
                    "p_holm": c["p_holm"],
                    "reject": c["reject"],
                    "rank_biserial": c["rank_biserial"],
                }
                for c in floor_rows
            ],
            "note": (
                "A floor inside our CI means the type signal on this collection is largely a "
                "size signal; DESIGN.md §6 then moves the ARI table to the supplement and the "
                "main text carries the unsupervised exhibit (A -> A')."
            ),
        }

    # --- H5c: non-inferiority to the best labelled competitor -------------
    labelled = [s for s in summary if s["arm"] in LABELLED_COMPETITORS and s["method"] == "pam"]
    ours_rows = [s for s in summary if s["arm"] == OURS and s["method"] == "pam"]
    if not labelled or not ours_rows:
        verdicts["H5c"] = {"verdict": "inconclusive", "reason": "missing labelled competitors"}
    else:
        best = max(labelled, key=lambda s: s["ari_mean"])
        ours = ours_rows[0]
        within = ours["ari_high"] >= best["ari_low"]
        verdicts["H5c"] = {
            "verdict": "supported" if within else "not_supported",
            "best_competitor": best["arm"],
            "best_ari": best["ari_mean"],
            "best_ci": [best["ari_low"], best["ari_high"]],
            "ours_ari": ours["ari_mean"],
            "ours_ci": [ours["ari_low"], ours["ari_high"]],
        }

    # --- H5d: the roles ablation ------------------------------------------
    roles_rows = [c for c in comparisons if c.get("name") == ROLES_ARM and c.get("method") == "pam"]
    if not roles_rows:
        verdicts["H5d"] = {"verdict": "inconclusive", "reason": "no fact_rank_roles comparison"}
    else:
        row = roles_rows[0]
        lowered = float(row["mean_other"]) < float(row["mean_ours"]) and bool(row["reject"])
        verdicts["H5d"] = {
            "verdict": "not_supported" if lowered else "supported",
            "mean_fact_rank": row["mean_ours"],
            "mean_fact_rank_roles": row["mean_other"],
            "p_holm": row["p_holm"],
            "reject": row["reject"],
        }

    n_seeds = int(clustering["seed"].nunique()) if not clustering.empty else 0
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

    parser = argparse.ArgumentParser(description="Aggregate RQ5's rows.")
    parser.add_argument("--root", type=Path, default=None, help="results root")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    root = Path(args.root) if args.root else results_root()

    clustering = _read(root, "clustering")
    geometry_rows_frame = _read(root, "geometry")
    per_class = _read(root, "per_class")
    mds = _read(root, "mds")

    summary_rows, comparison_rows = balanced_tables(clustering)
    geometry_rows = geometry_table(geometry_rows_frame)
    verdicts = evaluate_hypotheses(summary_rows, comparison_rows, geometry_rows, clustering)

    full_rows: list[dict[str, Any]] = []
    if not clustering.empty:
        full = clustering[clustering["design"] == "full"]
        keep = [
            c
            for c in (
                "experiment",
                "arm",
                "method",
                "k",
                "n_members",
                "ari",
                "nmi",
                "cophenetic",
                "silhouette",
                "ari_boot_low",
                "ari_boot_high",
            )
            if c in full.columns
        ]
        full_rows = full[keep].sort_values(["experiment", "method", "arm"]).to_dict("records")

    paths = RunPaths(root=root, rq=RQ_DIR, experiment=ANALYSIS_EXPERIMENT)
    paths.ensure()

    summary = {
        "n_clustering_rows": int(len(clustering)),
        "n_seeds": int(clustering["seed"].nunique()) if not clustering.empty else 0,
        "n_mds_rows": int(len(mds)),
        "n_per_class_rows": int(len(per_class)),
        "balanced": summary_rows,
        "full": full_rows,
        "geometry": geometry_rows,
        "hypotheses": verdicts,
        "mds_stress1": (float(mds["stress1"].iloc[0]) if not mds.empty else None),
    }
    write_summary(paths, summary)
    write_stats(paths, {"paired_family": comparison_rows, "hypotheses": verdicts})

    tables: dict[str, Any] = {}
    if summary_rows:
        tables["Balanced design -- ARI per arm (BCa 95 %)"] = pd.DataFrame(summary_rows)
    if comparison_rows:
        tables["Balanced design -- fact_rank vs each arm (Holm)"] = pd.DataFrame(comparison_rows)
    if full_rows:
        tables["Full design -- one value per arm"] = pd.DataFrame(full_rows)
    if geometry_rows:
        tables["Geometry -- the measured licences"] = pd.DataFrame(geometry_rows)
    tables["Hypotheses (DESIGN.md §6)"] = pd.DataFrame(
        [
            {
                "hypothesis": key,
                "verdict": value.get("verdict"),
                "detail": "; ".join(
                    f"{k}={v}"
                    for k, v in value.items()
                    if k not in {"verdict", "detail", "note"} and not isinstance(v, list | dict)
                ),
            }
            for key, value in sorted(verdicts.items())
        ]
    )
    if not per_class.empty:
        columns = [
            c
            for c in ("experiment", "arm", "method", "class", "support", "recall", "precision")
            if c in per_class.columns
        ]
        grouped = (
            per_class[per_class["design"] == "full"][columns]
            .groupby(
                [c for c in ("experiment", "arm", "method", "class") if c in columns],
                as_index=False,
            )
            .mean(numeric_only=True)
            if "design" in per_class.columns
            else per_class[columns]
        )
        if len(grouped):
            tables["Full design -- per-class recall / precision"] = grouped
    write_tables_md(paths, tables)

    logger.info("rq5 analysis written to %s", paths.dir)
    for key, value in sorted(verdicts.items()):
        logger.info("  %s: %s", key, value.get("verdict"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
