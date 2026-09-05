"""RQ6 analyzer --- aggregates the generation rows into the tables.

Reads every shard under ``<root>/RQ6_generation/generation/parts/`` and writes
the merged rows plus ``summary.json``, ``stats.json`` and ``tables.md`` at the
experiment level.

The statistics follow DESIGN.md section 7: the 27 seed-level divergences go into
BCa intervals, the fact-alphabet model is compared with the baseline's accepted
samples by paired Wilcoxon (Holm-corrected across the metrics of one table), the
rejection rate carries a Wilson interval, and the validity of the fact-alphabet
model is *asserted* --- it is 1.000 by Prop 6, so anything else is a falsified
theorem and is reported as such rather than averaged away.

Every aggregate is computed on whatever rows exist, so the analyzer is
meaningful while the campaign is still running.
"""

from __future__ import annotations

import argparse
import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pandas as pd

from experiments.tkde import io, stats
from experiments.tkde.analyze_rq3 import is_smoke_path
from experiments.tkde.config import results_root
from experiments.tkde.rq3 import deploy_stamps
from experiments.tkde.rq6 import EXPERIMENT, MODEL_BASELINE, MODEL_OURS, PARTS, RQ_DIR

logger = logging.getLogger(__name__)

JSD_COLUMNS: tuple[str, ...] = ("jsd_n", "jsd_m", "jsd_arity", "jsd_pred", "jsd_type")
FIDELITY_METRICS: tuple[str, ...] = (*JSD_COLUMNS, "novelty", "reach1_frac")


def read_parts(root: Path, table: str) -> pd.DataFrame:
    """Concatenate every shard's ``rows_<table>.csv``."""
    base = root / RQ_DIR / EXPERIMENT / PARTS
    frames = [
        pd.read_csv(path)
        for path in sorted(base.glob(f"*/rows_{table}.csv"))
        if path.stat().st_size > 0 and not is_smoke_path(path, root)
    ]
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _numeric(frame: pd.DataFrame, columns: Sequence[str]) -> pd.DataFrame:
    frame = frame.copy()
    for column in columns:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def validity_table(samples: pd.DataFrame) -> pd.DataFrame:
    """Validity and rejection rate per collection and model, with Wilson intervals."""
    rows: list[dict[str, Any]] = []
    for (collection, model), group in samples.groupby(["collection", "model"], dropna=False):
        drawn = int(group["n_samples"].sum())
        valid = int(group["n_valid"].sum())
        rejected = int(group["n_rejected"].sum())
        validity = stats.wilson_ci(valid, drawn) if drawn else None
        rejection = stats.wilson_ci(rejected, drawn) if drawn else None
        rows.append(
            {
                "collection": collection,
                "model": model,
                "n_seeds": int(len(group)),
                "n_drawn": drawn,
                "n_valid": valid,
                "n_rejected": rejected,
                "validity": validity.point if validity else "",
                "validity_ci_low": validity.low if validity else "",
                "rejection_rate": rejection.point if rejection else "",
                "rejection_ci_low": rejection.low if rejection else "",
                "rejection_ci_high": rejection.high if rejection else "",
            }
        )
    return pd.DataFrame(rows)


def fidelity_table(samples: pd.DataFrame) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Seed-level fidelity metrics per collection and model, with BCa intervals."""
    rows: list[dict[str, Any]] = []
    for (collection, model), group in samples.groupby(["collection", "model"], dropna=False):
        for metric in FIDELITY_METRICS:
            values = group[metric].dropna().tolist()
            if not values:
                continue
            interval = stats.bca_ci(values, stat="mean")
            rows.append(
                {
                    "collection": collection,
                    "model": model,
                    "metric": metric,
                    "n_seeds": len(values),
                    "mean": interval.point,
                    "ci_low": interval.low,
                    "ci_high": interval.high,
                }
            )
    return pd.DataFrame(rows), rows


def paired_table(samples: pd.DataFrame) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Paired Wilcoxon of ours against the baseline's accepted samples, Holm-corrected.

    One family per collection: the metrics of that collection's table.
    """
    records: list[dict[str, Any]] = []
    for collection, group in samples.groupby("collection", dropna=False):
        tests: list[dict[str, Any]] = []
        for metric in FIDELITY_METRICS:
            wide = group.pivot_table(index="seed", columns="model", values=metric).dropna()
            if MODEL_OURS not in wide.columns or MODEL_BASELINE not in wide.columns:
                continue
            if len(wide) < 3:
                continue
            test = stats.wilcoxon_paired(wide[MODEL_OURS].tolist(), wide[MODEL_BASELINE].tolist())
            difference = stats.bca_ci(
                (wide[MODEL_OURS] - wide[MODEL_BASELINE]).tolist(), stat="mean"
            )
            tests.append(
                {
                    "collection": collection,
                    "metric": metric,
                    "n": int(len(wide)),
                    "mean_ours": float(wide[MODEL_OURS].mean()),
                    "mean_baseline": float(wide[MODEL_BASELINE].mean()),
                    "diff_low": difference.low,
                    "diff_high": difference.high,
                    "p_raw": test["p_value"],
                    "rank_biserial": test["rank_biserial"],
                }
            )
        for test, correction in zip(
            tests, stats.holm([entry["p_raw"] for entry in tests]), strict=True
        ):
            test["p_holm"] = correction["p_holm"]
            test["reject"] = correction["reject"]
        records.extend(tests)
    return pd.DataFrame(records), records


def rejection_causes(rejections: pd.DataFrame) -> pd.DataFrame:
    """Rejection counts by rule, and each rule's share of the rejections."""
    if rejections.empty:
        return pd.DataFrame()
    frame = _numeric(rejections, ["count"])
    grouped = (
        frame.groupby(["collection", "model", "reason"], dropna=False)["count"].sum().reset_index()
    )
    totals = grouped.groupby(["collection", "model"])["count"].transform("sum")
    grouped["share"] = grouped["count"] / totals
    return grouped.sort_values(["collection", "model", "count"], ascending=[True, True, False])


def alignment_table(alignment: pd.DataFrame) -> pd.DataFrame:
    """Decodability of the alignment interiors, per collection and alphabet."""
    if alignment.empty:
        return pd.DataFrame()
    frame = _numeric(alignment, ["path_len", "n_interior", "n_decoded", "n_connected", "censored"])
    rows: list[dict[str, Any]] = []
    for (collection, arm), group in frame.groupby(["collection", "arm"], dropna=False):
        usable = group[group["censored"] == 0]
        interiors = float(usable["n_interior"].sum())
        rows.append(
            {
                "collection": collection,
                "arm": arm,
                "n_pairs": int(len(group)),
                "n_censored": int((group["censored"] != 0).sum()),
                "mean_path_len": float(usable["path_len"].mean()) if len(usable) else "",
                "n_interior": int(interiors),
                "n_decoded": int(usable["n_decoded"].sum()),
                "decoded_rate": (float(usable["n_decoded"].sum() / interiors) if interiors else ""),
                "connected_rate": (
                    float(usable["n_connected"].sum() / interiors) if interiors else ""
                ),
            }
        )
    return pd.DataFrame(rows)


def completion_table(completion: pd.DataFrame) -> pd.DataFrame:
    """Validity, isomorphism to the original and reach-1 of the completions."""
    if completion.empty:
        return pd.DataFrame()
    frame = _numeric(completion, ["valid", "iso_original", "reach1"])
    rows: list[dict[str, Any]] = []
    for collection, group in frame.groupby("collection", dropna=False):
        total = int(len(group))
        entry: dict[str, Any] = {"collection": collection, "n": total}
        for name in ("valid", "iso_original", "reach1"):
            successes = int(group[name].fillna(0).sum())
            interval = stats.wilson_ci(successes, total)
            entry[f"{name}_rate"] = interval.point
            entry[f"{name}_ci_low"] = interval.low
            entry[f"{name}_ci_high"] = interval.high
        rows.append(entry)
    return pd.DataFrame(rows)


def hypothesis_table(
    validity: pd.DataFrame, alignment: pd.DataFrame, fidelity: pd.DataFrame
) -> pd.DataFrame:
    """Evaluate H6a--H6c on the measured rows."""
    rows: list[dict[str, Any]] = []
    if not validity.empty:
        ours = validity[validity["model"] == MODEL_OURS]
        baseline = validity[validity["model"] == MODEL_BASELINE]
        if not ours.empty:
            perfect = bool((ours["n_valid"] == ours["n_drawn"]).all())
            rows.append(
                {
                    "hypothesis": "H6a (validity by theorem)",
                    "claim": "every sample over the fact alphabet decodes (validity 1.000)",
                    "measured": (
                        f"{int(ours['n_valid'].sum())} of {int(ours['n_drawn'].sum())} samples"
                    ),
                    "holds": perfect,
                }
            )
        if not baseline.empty:
            drawn = int(baseline["n_drawn"].sum())
            rejected = int(baseline["n_rejected"].sum())
            interval = stats.wilson_ci(rejected, drawn) if drawn else None
            rows.append(
                {
                    "hypothesis": "H6a (baseline rejects)",
                    "claim": "the strict decoder rejects a measurable fraction of its samples",
                    "measured": (
                        f"rejection {interval.point:.4f} "
                        f"[{interval.low:.4f}, {interval.high:.4f}] on {drawn} samples"
                        if interval
                        else "no samples"
                    ),
                    "holds": bool(interval and interval.low > 0.0),
                }
            )
    if not fidelity.empty:
        ours = fidelity[(fidelity["model"] == MODEL_OURS) & fidelity["metric"].isin(JSD_COLUMNS)]
        if not ours.empty:
            worst = float(ours["mean"].max())
            rows.append(
                {
                    "hypothesis": "H6b (fidelity)",
                    "claim": "the sample profiles are close to the collection's",
                    "measured": f"largest mean JSD over the five histograms = {worst:.4f}",
                    "holds": bool(worst < 0.5),
                }
            )
    if not alignment.empty:
        for _, row in alignment.iterrows():
            if row["decoded_rate"] == "":
                continue
            rows.append(
                {
                    "hypothesis": f"H6c (interiors decode, {row['arm']})",
                    "claim": "every interior word of the alignment path decodes",
                    "measured": (
                        f"{row['n_decoded']} of {row['n_interior']} interiors on "
                        f"{row['collection']} ({row['n_censored']} pairs censored)"
                    ),
                    "holds": bool(float(row["decoded_rate"]) >= 1.0),
                }
            )
    return pd.DataFrame(rows)


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point of ``python -m experiments.tkde.analyze_rq6``."""
    parser = argparse.ArgumentParser(description="Aggregate the RQ6 rows into the tables")
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    root = Path(args.root) if args.root is not None else results_root()
    samples = read_parts(root, "samples")
    if samples.empty:
        logger.error("no RQ6 sample rows under %s", root)
        return 1
    samples = _numeric(
        samples,
        ["seed", "n_samples", "n_valid", "n_rejected", "validity", *FIDELITY_METRICS],
    )
    rejections = read_parts(root, "rejections")
    alignment = read_parts(root, "alignment")
    completion = read_parts(root, "completion")

    paths = io.RunPaths(root=root, rq=RQ_DIR, experiment=EXPERIMENT)
    validity = validity_table(samples)
    fidelity, fidelity_records = fidelity_table(samples)
    paired, paired_records = paired_table(samples)
    causes = rejection_causes(rejections)
    interiors = alignment_table(alignment)
    completions = completion_table(completion)
    hypotheses = hypothesis_table(validity, interiors, fidelity)

    ours = validity[validity["model"] == MODEL_OURS]
    if not ours.empty and not bool((ours["n_valid"] == ours["n_drawn"]).all()):
        logger.error(
            "VALIDITY IS NOT 1.000 on the fact alphabet: %d of %d samples decoded. "
            "Prop 6 says the decoder is total, so this is a defect, not a result.",
            int(ours["n_valid"].sum()),
            int(ours["n_drawn"].sum()),
        )

    target = paths.ensure()
    samples.to_csv(target / "rows_samples.csv", index=False)
    for name, frame in (
        ("rejections", rejections),
        ("alignment", alignment),
        ("completion", completion),
    ):
        if not frame.empty:
            frame.to_csv(target / f"rows_{name}.csv", index=False)

    io.write_summary(
        paths,
        {
            "n_sample_rows": int(len(samples)),
            "validity": validity.to_dict(orient="records"),
            "fidelity": fidelity_records,
            "rejection_causes": causes.to_dict(orient="records") if not causes.empty else [],
            "alignment": interiors.to_dict(orient="records") if not interiors.empty else [],
            "completion": completions.to_dict(orient="records") if not completions.empty else [],
            "hypotheses": hypotheses.to_dict(orient="records"),
        },
    )
    io.write_stats(
        paths, {"fidelity_bca": fidelity_records, "paired_ours_vs_baseline": paired_records}
    )
    io.write_tables_md(
        paths,
        {
            "G1 validity and rejection (Wilson 95%)": validity,
            "G2 fidelity, novelty and reach-1 (seed-level mean, BCa 95%)": fidelity,
            "G3 ours vs the baseline's accepted samples (Holm)": paired,
            "G4 rejection causes of the strict decoder": causes,
            "G5 alignment interiors, both alphabets": interiors,
            "G6 conditional completion (Wilson 95%)": completions,
            "G7 hypotheses": hypotheses,
        },
    )
    io.write_manifest(paths, extra={"analyzer": "analyze_rq6", **deploy_stamps()})
    logger.info("RQ6: %d sample rows, %d alignment rows", len(samples), len(alignment))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
