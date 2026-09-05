"""RQ3 analyzer --- aggregates the representative-record rows into the tables.

Reads every shard under ``<root>/RQ3_representative/<corpus>/parts/`` and writes
the merged rows plus ``summary.json``, ``stats.json`` and ``tables.md`` at the
experiment level. The RQ2 certificate rows are merged in the same pass to
``<root>/RQ2_wellposedness/certificate_validity/rows_certificate.csv``, which is
the file RQ2's own analyzer reads.

The statistics follow DESIGN.md section 4: seed-level means per cell into a BCa
interval, a Holm-corrected paired family of the coverage consensus against every
medoid arm and against ``majority_merge``, exact-recovery rates with Wilson
intervals, and the medoid ratios against the ``2 - 2/N`` bound of Prop 3. The
four hypotheses H3a--H3d are evaluated explicitly and land in ``tables.md``.

Every aggregate is computed on whatever rows exist, so the analyzer is
meaningful while the campaign is still running.
"""

from __future__ import annotations

import argparse
import logging
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pandas as pd

from experiments.tkde import io, stats
from experiments.tkde.config import results_root
from experiments.tkde.rq3 import (
    CERT_EXPERIMENT,
    CERT_RQ_DIR,
    EXPERIMENT_A,
    EXPERIMENT_B,
    MEDOID_ARMS,
    PARTS,
    RQ_DIR,
)

logger = logging.getLogger(__name__)

COVERAGE_PRIMARY = "coverage_r2"
COVERAGE_KNOWN = "coverage_rt"
MAJORITY = "majority_merge"
RATIO_TOLERANCE = 1e-9
# DESIGN.md section 4, H3a / H3d.
H3A_THRESHOLD_PURE = 0.95
H3A_THRESHOLD_MIX = 0.80
H3C_TOLERANCE = 0.05
H3D_RATIO_CEILING = 1.7


def read_parts(root: Path, rq_dir: str, experiment: str, table: str) -> pd.DataFrame:
    """Concatenate every shard's ``rows_<table>.csv`` under one experiment."""
    base = root / rq_dir / experiment / PARTS
    frames = [
        pd.read_csv(path)
        for path in sorted(base.glob(f"*/rows_{table}.csv"))
        if path.stat().st_size > 0
    ]
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def method_label(row: Mapping[str, Any]) -> str:
    """Name one method for the tables: the medoid's arm, or the consensus radius."""
    method = str(row["method"])
    if method == "medoid":
        return f"medoid[{row['arm']}]"
    if method == "coverage":
        return COVERAGE_PRIMARY if str(row["radius"]) == "2" else COVERAGE_KNOWN
    return MAJORITY


def prepare(frame: pd.DataFrame) -> pd.DataFrame:
    """Add the method label and drop censored or unscored rows."""
    if frame.empty:
        return frame
    frame = frame.copy()
    frame["label"] = frame.apply(method_label, axis=1)
    frame["censored"] = pd.to_numeric(frame["censored"], errors="coerce").fillna(0)
    frame["fact_dist"] = pd.to_numeric(frame["fact_dist"], errors="coerce")
    frame["exact_recovery"] = pd.to_numeric(frame["exact_recovery"], errors="coerce")
    frame["ratio"] = pd.to_numeric(frame["ratio"], errors="coerce")
    return frame


def scored(frame: pd.DataFrame) -> pd.DataFrame:
    """The rows that carry a score: uncensored, with a finite fact distance."""
    if frame.empty:
        return frame
    return frame[(frame["censored"] == 0) & frame["fact_dist"].notna()]


# ---------------------------------------------------------------------------
# Corpus A
# ---------------------------------------------------------------------------


def seed_level(frame: pd.DataFrame, by: Sequence[str]) -> pd.DataFrame:
    """Mean fact distance per replication: the sample every test is run on."""
    return frame.groupby([*by, "seed"], dropna=False)["fact_dist"].mean().reset_index(name="score")


def distance_table(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Seed-level mean fact distance per cell and method, with a BCa interval."""
    rows: list[dict[str, Any]] = []
    if frame.empty:
        return pd.DataFrame(), rows
    means = seed_level(frame, ["collection", "cell", "label"])
    for (collection, cell, label), group in means.groupby(
        ["collection", "cell", "label"], dropna=False
    ):
        interval = stats.bca_ci(group["score"].tolist(), stat="mean")
        rows.append(
            {
                "collection": collection,
                "cell": cell,
                "method": label,
                "n_seeds": int(len(group)),
                "mean_fact_dist": interval.point,
                "ci_low": interval.low,
                "ci_high": interval.high,
            }
        )
    return pd.DataFrame(rows), rows


def recovery_table(frame: pd.DataFrame, by: Sequence[str]) -> pd.DataFrame:
    """Exact-recovery rate per group, with a Wilson interval."""
    rows: list[dict[str, Any]] = []
    if frame.empty:
        return pd.DataFrame(rows)
    for keys, group in frame.groupby(list(by), dropna=False):
        successes = int(group["exact_recovery"].sum())
        total = int(len(group))
        interval = stats.wilson_ci(successes, total)
        entry = dict(zip(by, keys if isinstance(keys, tuple) else (keys,), strict=True))
        entry.update(
            {
                "n": total,
                "n_recovered": successes,
                "recovery": interval.point,
                "ci_low": interval.low,
                "ci_high": interval.high,
            }
        )
        rows.append(entry)
    return pd.DataFrame(rows)


def paired_tables(
    frame: pd.DataFrame, by: Sequence[str], unit: str
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Holm-corrected Wilcoxon of the coverage consensus against every competitor.

    Parameters
    ----------
    frame : DataFrame
        Scored rows.
    by : Sequence of str
        Grouping that defines one family of tests (one table).
    unit : str
        Column identifying the paired replication (``"seed"`` or ``"collection_id"``).

    Returns
    -------
    tuple
        The rendered table and the same rows as JSON-ready records.
    """
    records: list[dict[str, Any]] = []
    if frame.empty:
        return pd.DataFrame(), records
    aggregated = (
        frame.groupby([*by, "label", unit], dropna=False)["fact_dist"]
        .mean()
        .reset_index(name="score")
    )
    for keys, group in aggregated.groupby(list(by), dropna=False):
        wide = group.pivot_table(index=unit, columns="label", values="score").dropna()
        if COVERAGE_PRIMARY not in wide.columns or len(wide) < 3:
            continue
        others = {
            column: wide[column].tolist() for column in wide.columns if column != COVERAGE_PRIMARY
        }
        if not others:
            continue
        entry_keys = dict(zip(by, keys if isinstance(keys, tuple) else (keys,), strict=True))
        for row in stats.paired_family(wide[COVERAGE_PRIMARY].tolist(), others):
            records.append({**entry_keys, "unit": unit, **row})
    if not records:
        return pd.DataFrame(), records
    table = pd.DataFrame(
        [
            {
                **{key: value for key, value in record.items() if key not in ("diff_ci",)},
                "diff_low": record["diff_ci"]["low"],
                "diff_high": record["diff_ci"]["high"],
            }
            for record in records
        ]
    )
    return table, records


def ratio_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Medoid ratios per arm against the ``2 - 2/N`` bound of Prop 3."""
    rows: list[dict[str, Any]] = []
    if frame.empty:
        return pd.DataFrame(rows)
    medoids = frame[frame["method"] == "medoid"].dropna(subset=["ratio"])
    if medoids.empty:
        return pd.DataFrame(rows)
    medoids = medoids.copy()
    medoids["N"] = pd.to_numeric(medoids["N"], errors="coerce")
    medoids["bound"] = 2.0 - 2.0 / medoids["N"]
    medoids["exceeds"] = medoids["ratio"] > medoids["bound"] + RATIO_TOLERANCE
    for arm, group in medoids.groupby("arm", dropna=False):
        rows.append(
            {
                "arm": arm,
                "n": int(len(group)),
                "ratio_max": float(group["ratio"].max()),
                "ratio_median": float(group["ratio"].median()),
                "ratio_mean": float(group["ratio"].mean()),
                "ratio_p90": float(group["ratio"].quantile(0.9)),
                "n_exceeding_bound": int(group["exceeds"].sum()),
            }
        )
    return pd.DataFrame(rows)


def hypothesis_table(
    frame: pd.DataFrame,
    recovery: pd.DataFrame,
    ratios: pd.DataFrame,
    certificates: pd.DataFrame,
) -> pd.DataFrame:
    """Evaluate H3a--H3d on the measured rows and say which hold."""
    rows: list[dict[str, Any]] = []

    if not recovery.empty:
        per_kind = recovery[recovery["label"] == COVERAGE_PRIMARY]
        for kind, threshold in (
            ("ins", H3A_THRESHOLD_PURE),
            ("del", H3A_THRESHOLD_PURE),
            ("mix", H3A_THRESHOLD_MIX),
        ):
            subset = per_kind[per_kind["cell_kind"] == kind]
            if subset.empty:
                continue
            worst = float(subset["recovery"].min())
            rows.append(
                {
                    "hypothesis": f"H3a ({kind}, coverage r=2)",
                    "claim": f"exact recovery >= {threshold:.2f} in every cell",
                    "measured": f"min over cells = {worst:.3f} (n cells = {len(subset)})",
                    "holds": bool(worst >= threshold),
                }
            )

    medoids = scored(frame)
    medoids = medoids[medoids["method"] == "medoid"] if not medoids.empty else medoids
    if not medoids.empty and "cell_t" in medoids.columns:
        budget = pd.to_numeric(medoids["cell_t"], errors="coerce")
        at_least_t = (medoids["fact_dist"] >= budget).mean()
        rows.append(
            {
                "hypothesis": "H3b (medoid floor)",
                "claim": "a medoid returns an input, so its distance to the source is >= t",
                "measured": f"fraction of medoid rows with fact_dist >= t = {at_least_t:.4f}",
                "holds": bool(at_least_t >= 1.0 - 1e-12),
            }
        )

    if not recovery.empty:
        coverage = recovery[recovery["label"] == COVERAGE_PRIMARY]["recovery"]
        majority = recovery[recovery["label"] == MAJORITY]["recovery"]
        if not coverage.empty and not majority.empty:
            gap = float(abs(coverage.mean() - majority.mean()))
            rows.append(
                {
                    "hypothesis": "H3c (vs majority_merge)",
                    "claim": f"recovery within {H3C_TOLERANCE:.2f} of the identity-reading merge",
                    "measured": f"|mean recovery gap| = {gap:.4f}",
                    "holds": bool(gap <= H3C_TOLERANCE),
                }
            )

    if not ratios.empty:
        ours = ratios[ratios["arm"] == "fact_rank"]
        if not ours.empty:
            exceeding = int(ours["n_exceeding_bound"].iloc[0])
            maximum = float(ours["ratio_max"].iloc[0])
            rows.append(
                {
                    "hypothesis": "H3d (certified ratio)",
                    "claim": "every fact_rank ratio <= 2 - 2/N, and the max is <= "
                    f"{H3D_RATIO_CEILING}",
                    "measured": f"{exceeding} of {int(ours['n'].iloc[0])} exceed the bound; "
                    f"max = {maximum:.4f}",
                    "holds": bool(exceeding == 0 and maximum <= H3D_RATIO_CEILING),
                }
            )

    if not certificates.empty:
        invalid = pd.to_numeric(certificates["invalid"], errors="coerce").fillna(0)
        by_arm = certificates.assign(invalid=invalid).groupby("arm")["invalid"].sum()
        offenders = ", ".join(f"{arm}={int(count)}" for arm, count in by_arm.items() if count)
        rows.append(
            {
                "hypothesis": "H2d (certificate validity, RQ2 step 4)",
                "claim": "LB <= cost under a metric; a non-metric arm can violate it",
                "measured": offenders or "no arm produced LB > cost",
                "holds": bool(by_arm.get("fact_rank", 0) == 0),
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Drivers
# ---------------------------------------------------------------------------


def analyze_corpus_a(root: Path, certificates: pd.DataFrame) -> dict[str, Any]:
    """Aggregate Corpus A and write its six files."""
    paths = io.RunPaths(root=root, rq=RQ_DIR, experiment=EXPERIMENT_A)
    raw = read_parts(root, RQ_DIR, EXPERIMENT_A, "variants")
    if raw.empty:
        logger.warning("no Corpus A rows under %s", root)
        return {}
    frame = prepare(raw)
    good = scored(frame)

    distances, distance_records = distance_table(good)
    recovery_by_cell = recovery_table(good, ["collection", "cell", "cell_kind", "cell_t", "label"])
    recovery_by_kind = recovery_table(good, ["collection", "cell_kind", "cell_t", "label"])
    paired_cell, paired_cell_records = paired_tables(good, ["collection", "cell"], "seed")
    paired_pooled, paired_pooled_records = paired_tables(good, ["collection"], "seed")
    ratios = ratio_table(good)
    hypotheses = hypothesis_table(frame, recovery_by_cell, ratios, certificates)

    drops = merge_drop_counts(root, EXPERIMENT_A)
    summary = {
        "n_rows": int(len(frame)),
        "n_scored": int(len(good)),
        "n_censored": int((frame["censored"] != 0).sum()),
        "n_collections": int(good["collection_id"].nunique()),
        "dropped_total": drops["dropped_total"],
        "dropped_by_cell": drops["dropped_by_cell"],
        "source_pools": drops["source_pools"],
        "recovery_by_kind": recovery_by_kind.to_dict(orient="records"),
        "ratio_by_arm": ratios.to_dict(orient="records"),
        "hypotheses": hypotheses.to_dict(orient="records"),
    }
    statistics = {
        "distance_bca": distance_records,
        "paired_by_cell": paired_cell_records,
        "paired_pooled": paired_pooled_records,
    }
    frame.drop(columns=["label"]).to_csv(paths.ensure() / "rows_variants.csv", index=False)
    io.write_summary(paths, summary)
    io.write_stats(paths, statistics)
    io.write_tables_md(
        paths,
        {
            "A1 fact distance to the source (seed-level mean, BCa 95%)": distances,
            "A2 exact recovery by cell (Wilson 95%)": recovery_by_cell,
            "A3 exact recovery by kind and budget": recovery_by_kind,
            "A4 coverage(r=2) vs every competitor, per cell (Holm)": paired_cell,
            "A5 coverage(r=2) vs every competitor, pooled per collection (Holm)": paired_pooled,
            "A6 medoid ratio against 2 - 2/N": ratios,
            "A7 hypotheses": hypotheses,
            "A8 dropped collections": pd.DataFrame(
                sorted(
                    (
                        {"cell": key, "dropped": value}
                        for key, value in drops["dropped_by_cell"].items()
                    ),
                    key=lambda entry: entry["cell"],
                )
            ),
            "A9 source pools per cell": pd.DataFrame(
                sorted(
                    drops["source_pools"].values(),
                    key=lambda entry: (entry["collection"], entry["kind"], entry["N"]),
                )
            ),
        },
    )
    io.write_manifest(paths, extra={"analyzer": "analyze_rq3", "corpus": "A"})
    return summary


def analyze_corpus_b(root: Path) -> dict[str, Any]:
    """Aggregate Corpus B and write its six files."""
    paths = io.RunPaths(root=root, rq=RQ_DIR, experiment=EXPERIMENT_B)
    raw = read_parts(root, RQ_DIR, EXPERIMENT_B, "natural")
    if raw.empty:
        logger.warning("no Corpus B rows under %s", root)
        return {}
    frame = prepare(raw)
    good = scored(frame)

    rows: list[dict[str, Any]] = []
    for (collection, regime, label), group in good.groupby(
        ["collection", "regime_preserving", "label"], dropna=False
    ):
        interval = stats.bca_ci(group["fact_dist"].tolist(), stat="mean")
        rows.append(
            {
                "collection": collection,
                "regime_preserving": regime,
                "method": label,
                "n_runs": int(len(group)),
                "mean_fact_dist": interval.point,
                "ci_low": interval.low,
                "ci_high": interval.high,
            }
        )
    distances = pd.DataFrame(rows)
    recovery = recovery_table(good, ["collection", "regime_preserving", "label"])
    paired, paired_records = paired_tables(good, ["collection"], "collection_id")
    ratios = ratio_table(good)

    summary = {
        "n_rows": int(len(frame)),
        "n_scored": int(len(good)),
        "n_censored": int((frame["censored"] != 0).sum()),
        "n_runs": int(good["collection_id"].nunique()),
        "distance_by_regime": rows,
        "recovery": recovery.to_dict(orient="records"),
        "ratio_by_arm": ratios.to_dict(orient="records"),
    }
    frame.drop(columns=["label"]).to_csv(paths.ensure() / "rows_natural.csv", index=False)
    io.write_summary(paths, summary)
    io.write_stats(paths, {"paired": paired_records})
    io.write_tables_md(
        paths,
        {
            "B1 fact distance to quarter T (BCa 95% over runs)": distances,
            "B2 exact recovery (Wilson 95%)": recovery,
            "B3 coverage(r=2) vs every competitor (Holm, paired on the run)": paired,
            "B4 medoid ratio against 2 - 2/N": ratios,
        },
    )
    io.write_manifest(paths, extra={"analyzer": "analyze_rq3", "corpus": "B"})
    return summary


def merge_certificates(root: Path) -> pd.DataFrame:
    """Merge the shard certificate rows to the path RQ2's analyzer reads."""
    frame = read_parts(root, CERT_RQ_DIR, CERT_EXPERIMENT, "certificate")
    if frame.empty:
        logger.warning("no certificate rows under %s", root)
        return frame
    paths = io.RunPaths(root=root, rq=CERT_RQ_DIR, experiment=CERT_EXPERIMENT)
    frame.to_csv(paths.ensure() / "rows_certificate.csv", index=False)
    invalid = pd.to_numeric(frame["invalid"], errors="coerce").fillna(0)
    by_arm = frame.assign(invalid=invalid).groupby("arm")["invalid"].agg(["sum", "count"])
    io.write_summary(
        paths,
        {
            "n_rows": int(len(frame)),
            "n_collections": int(frame["collection_id"].nunique()),
            "invalid_by_arm": {
                str(arm): {
                    "n_invalid": int(row["sum"]),
                    "n": int(row["count"]),
                    "rate": stats.wilson_ci(int(row["sum"]), int(row["count"])).as_dict(),
                }
                for arm, row in by_arm.iterrows()
            },
            "note": "produced by analyze_rq3 from RQ3's matrices (DESIGN.md section 3 step 4)",
        },
    )
    return frame


def merge_drop_counts(root: Path, experiment: str) -> dict[str, Any]:
    """Merge the per-shard drop counts and source-pool records.

    The source pools are a property of the design, so every shard writes the
    same record for a given cell; the merge keeps the last one seen rather than
    summing.
    """
    import json

    total = 0
    by_cell: dict[str, int] = {}
    pools: dict[str, Any] = {}
    base = root / RQ_DIR / experiment / PARTS
    for path in sorted(base.glob("*/summary.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        total += int(payload.get("dropped_total", 0))
        for key, value in (payload.get("dropped_by_cell") or {}).items():
            by_cell[key] = by_cell.get(key, 0) + int(value)
        pools.update(payload.get("source_pools") or {})
    return {"dropped_total": total, "dropped_by_cell": by_cell, "source_pools": pools}


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point of ``python -m experiments.tkde.analyze_rq3``."""
    parser = argparse.ArgumentParser(description="Aggregate the RQ3 rows into the tables")
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    root = Path(args.root) if args.root is not None else results_root()
    certificates = merge_certificates(root)
    summary_a = analyze_corpus_a(root, certificates)
    summary_b = analyze_corpus_b(root)
    logger.info(
        "RQ3: %d Corpus A rows, %d Corpus B rows, %d certificate rows",
        summary_a.get("n_rows", 0),
        summary_b.get("n_rows", 0),
        0 if certificates.empty else len(certificates),
    )
    if not summary_a and not summary_b:
        logger.error("nothing to analyze under %s", root)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["main", "MEDOID_ARMS"]
