"""Analyzer for RQ3 v2 --- the golden record from N anonymous noisy descriptions.

Reads the tagged row files, aggregates to the replication unit the harness fixes
(one seed, one cell), and tests the five pre-registered hypotheses of
``HEADLINE_DESIGN_2026-09-13.md`` section 3 plus the orchestrator's H3.5, with
95 % BCa intervals, Holm-corrected paired Wilcoxon over seeds and rank-biserial
effect sizes.  Each hypothesis prints its verdict *and*, when it fails, the
fallback the design declared for it, so a reader never has to reconstruct what
was supposed to happen from what did.

Every numeric column is coerced, never string-compared.  RQ3 v1 serialized
``exact_recovery`` as ``'1'`` on one corpus and ``'1.0'`` on another --- the
second carried censored units, so pandas typed the column float --- and a
``== "1"`` test silently reported a recovery collapse to zero on the corpus it
did not match (T-KBs).
"""

from __future__ import annotations

import argparse
import json
import logging
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pandas as pd

from experiments.tkde import io
from experiments.tkde.config import TkdeError, results_root
from experiments.tkde.rq3v2 import EXPERIMENT, MEDOID_ARMS, RQ_DIR
from experiments.tkde.stats import bca_ci, paired_family, wilson_ci

logger = logging.getLogger(__name__)

OURS = "consensus_ow"
ORACLE = "majority_merge_id"
FACT_ABLATION = "consensus_fact"
MERGE_BASELINES: tuple[str, ...] = ("align_merge_ref", "align_merge_iter", "pattern_vote")
COUNTING_BASELINE = "pattern_vote"

NUMERIC_COLUMNS: tuple[str, ...] = (
    "exact_recovery",
    "fact_dist",
    "secs",
    "censored",
    "pool_size",
    "pool_secs",
    "n_ties",
    "n_decoded",
    "n_decoded_connected",
    "medoid_cost",
    "LB",
    "ratio",
    "cell_N",
    "cell_t",
    "seed",
)

#: A hypothesis is judged at this level after Holm correction across its family.
ALPHA = 0.05

#: The margin H3.3, H3.4 and H3.5 are stated with.
MARGIN = 0.05


class RQ3v2AnalysisError(TkdeError):
    """The rows could not support the pre-registered analysis."""


def load_rows(root: Path, run_tag: str | None = None) -> pd.DataFrame:
    """Read every tagged row file under the results root.

    Parameters
    ----------
    root : Path
        Results root; the rows live under ``<root>/<RQ_DIR>/<EXPERIMENT>/``.
    run_tag : str or None, optional
        Keep only rows carrying this tag.  ``None`` keeps every tag and reports
        which were seen, because mixing two configurations in one table is
        exactly the failure the tag exists to prevent.

    Returns
    -------
    pandas.DataFrame
        The rows, with every numeric column coerced.

    Raises
    ------
    RQ3v2AnalysisError
        If no row file was found, or ``run_tag`` matched nothing.
    """
    directory = Path(root) / RQ_DIR / EXPERIMENT
    files = sorted(directory.glob("rows_golden__*.csv"))
    if not files:
        raise RQ3v2AnalysisError(f"no RQ3 v2 row files under {directory}")
    frame = pd.concat([pd.read_csv(path, low_memory=False) for path in files], ignore_index=True)
    for column in NUMERIC_COLUMNS:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    if run_tag is not None:
        frame = frame[frame["run_tag"].astype(str) == run_tag]
        if frame.empty:
            raise RQ3v2AnalysisError(f"no rows carry run_tag {run_tag!r}")
    return frame


def method_label(frame: pd.DataFrame) -> pd.Series:
    """One name per arm: a medoid is named by its distance, everything else by itself."""
    return frame.apply(
        lambda row: f"medoid:{row['arm']}" if row["method"] == "medoid" else str(row["method"]),
        axis=1,
    )


def per_seed(
    frame: pd.DataFrame,
    value: str,
    *,
    keys: Sequence[str] = ("collection", "stratum", "cell_N", "cell_t"),
) -> pd.DataFrame:
    """Mean of ``value`` per (cell keys, seed, method), over that cell's collections.

    The seed is the replication unit the harness fixes, so every paired test
    below compares two methods on the same 27 numbers.  Censored rows are
    dropped from the mean and counted separately: a censoring is a measured
    outcome of an arm, not a zero.
    """
    usable = frame[(frame["censored"] != 1) & frame[value].notna()].copy()
    usable["label"] = method_label(usable)
    return (
        usable.groupby([*keys, "seed", "label"], dropna=False)[value]
        .mean()
        .reset_index()
        .rename(columns={value: "value"})
    )


def _paired(table: pd.DataFrame, ours: str, others: Sequence[str], alternative: str) -> list[dict]:
    """Holm-corrected paired family of ``ours`` against ``others`` over seeds."""
    wide = table.pivot_table(index="seed", columns="label", values="value")
    present = [name for name in others if name in wide.columns]
    if ours not in wide.columns or not present:
        return []
    wide = wide[[ours, *present]].dropna()
    if len(wide) < 3:
        return []
    return paired_family(
        wide[ours].tolist(),
        {name: wide[name].tolist() for name in present},
        alternative=alternative,
    )


def _rate(frame: pd.DataFrame, label: str, value: str = "exact_recovery") -> dict[str, Any]:
    """Point estimate, BCa interval over seeds and a Wilson interval over collections."""
    rows = frame[(frame["censored"] != 1) & frame[value].notna()].copy()
    rows["label"] = method_label(rows)
    rows = rows[rows["label"] == label]
    if rows.empty:
        return {"label": label, "n": 0}
    by_seed = rows.groupby("seed")[value].mean()
    out: dict[str, Any] = {
        "label": label,
        "n_rows": int(len(rows)),
        "n_seeds": int(by_seed.size),
        "mean": float(rows[value].mean()),
        "bca": bca_ci(by_seed.tolist()).as_dict() if by_seed.size >= 3 else None,
    }
    if value == "exact_recovery":
        successes = int(rows[value].sum())
        out["wilson"] = wilson_ci(successes, int(len(rows))).as_dict()
    return out


def hypotheses(frame: pd.DataFrame) -> dict[str, Any]:
    """Test H3.1--H3.5 exactly as pre-registered, with their declared fallbacks."""
    out: dict[str, Any] = {}
    non_star = frame[frame["stratum"] == "non_star"]
    star = frame[frame["stratum"] == "star"]

    # H3.1 --- the headline. Non-star strata, t <= 2, every N, ours above the
    # three anonymous merges, Holm-significant within the family.
    h31: dict[str, Any] = {
        "statement": (
            "on the non-star strata at t <= 2, consensus_ow exact recovery exceeds "
            "align_merge_ref, align_merge_iter and pattern_vote, Holm-significant, for every N"
        ),
        "cells": {},
    }
    recovery = per_seed(non_star, "exact_recovery")
    for (collection, n_members), cell in recovery.groupby(["collection", "cell_N"]):
        family = _paired(cell, OURS, MERGE_BASELINES, "greater")
        h31["cells"][f"{collection}|N{int(n_members)}"] = {
            "family": family,
            "held": bool(family) and all(row["reject"] and row["p_holm"] < ALPHA for row in family),
        }
    decided = [entry["held"] for entry in h31["cells"].values()]
    h31["held"] = bool(decided) and all(decided)
    if not h31["held"]:
        won = {key.split("|")[0] for key, entry in h31["cells"].items() if entry["held"]}
        h31["fallback"] = (
            f"scoped to {sorted(won)} per the design's first fallback"
            if won
            else (
                "the design's second fallback applies: the headline becomes H3.2 plus the "
                "certificate, the consensus moves to a supporting exhibit, and RQ8 becomes "
                "the second headline"
            )
        )
    out["H3.1"] = h31

    # H3.2 --- ours below every medoid on the fact-level distance. The medoid is
    # a structural floor, so this is the claim the design says survives even if
    # H3.1 does not.
    distance = per_seed(frame, "fact_dist")
    medoids = [f"medoid:{arm}" for arm in MEDOID_ARMS]
    family = _paired(distance, OURS, medoids, "less")
    out["H3.2"] = {
        "statement": "consensus_ow fact-level distance is below every medoid's",
        "family": family,
        "held": bool(family) and all(row["reject"] and row["p_holm"] < ALPHA for row in family),
    }

    # H3.3 --- the stretch: we match an oracle that has the identities.
    ours_rate = _rate(non_star, OURS)
    oracle_rate = _rate(non_star, ORACLE)
    gap = (
        ours_rate.get("mean", float("nan")) - oracle_rate.get("mean", float("nan"))
        if ours_rate.get("n_rows") and oracle_rate.get("n_rows")
        else float("nan")
    )
    out["H3.3"] = {
        "statement": "on non-stars, consensus_ow >= majority_merge_id - 0.05",
        "ours": ours_rate,
        "oracle_labelled_as_oracle": oracle_rate,
        "gap": gap,
        "held": bool(gap == gap and gap >= -MARGIN),
    }

    # H3.4 --- the control, reported as the scope statement and never hidden.
    star_ours = _rate(star, OURS)
    star_count = _rate(star, COUNTING_BASELINE)
    star_gap = (
        star_ours.get("mean", float("nan")) - star_count.get("mean", float("nan"))
        if star_ours.get("n_rows") and star_count.get("n_rows")
        else float("nan")
    )
    out["H3.4"] = {
        "statement": "on stars, pattern_vote ties consensus_ow (|delta| < 0.05)",
        "ours": star_ours,
        "counting": star_count,
        "gap": star_gap,
        "held": bool(star_gap == star_gap and abs(star_gap) < MARGIN),
        "note": (
            "measured on wd50k66 only: gate G0 found no star inside the source window in "
            "ndc_classes, so its star cells are structurally empty"
        ),
    }

    # H3.5 --- the orchestrator's ablation. Word space must not cost us the task
    # against the fact-space computation, and the cost of each is reported.
    ablation_rate = _rate(frame, FACT_ABLATION)
    all_ours = _rate(frame, OURS)
    ablation_gap = (
        all_ours.get("mean", float("nan")) - ablation_rate.get("mean", float("nan"))
        if all_ours.get("n_rows") and ablation_rate.get("n_rows")
        else float("nan")
    )
    out["H3.5"] = {
        "statement": (
            "consensus_ow exact recovery >= consensus_fact - 0.05 at matched r, at lower "
            "enumeration cost"
        ),
        "ours": all_ours,
        "fact_space": ablation_rate,
        "gap": ablation_gap,
        "held": bool(ablation_gap == ablation_gap and ablation_gap >= -MARGIN),
        "cost": cost_table(frame).to_dict(orient="records"),
        "fallback": (
            "if consensus_fact is strictly better this is reported, and RQ3's language claim "
            "reduces to the decoded output, the certificate and the cost"
        ),
    }
    return out


def cost_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Pool size and wall-clock of each consensus arm, which is part of the argument."""
    rows = frame[frame["method"].isin([OURS, FACT_ABLATION]) & (frame["censored"] != 1)]
    if rows.empty:
        return pd.DataFrame()
    return (
        rows.groupby(["method", "collection", "cell_N"])
        .agg(
            n=("secs", "size"),
            median_secs=("secs", "median"),
            max_secs=("secs", "max"),
            median_pool=("pool_size", "median"),
            median_decoded=("n_decoded", "median"),
        )
        .reset_index()
    )


def headline_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Exact recovery and fact distance per method, per corpus x stratum x N x t."""
    rows = frame.copy()
    rows["label"] = method_label(rows)
    usable = rows[rows["censored"] != 1]
    table = (
        usable.groupby(["collection", "stratum", "cell_N", "cell_t", "label"])
        .agg(
            n=("exact_recovery", "size"),
            exact_recovery=("exact_recovery", "mean"),
            fact_dist=("fact_dist", "mean"),
            median_secs=("secs", "median"),
        )
        .reset_index()
    )
    censoring = (
        rows.groupby(["collection", "stratum", "cell_N", "cell_t", "label"])["censored"]
        .mean()
        .reset_index()
        .rename(columns={"censored": "censored_rate"})
    )
    return table.merge(
        censoring, on=["collection", "stratum", "cell_N", "cell_t", "label"], how="left"
    )


def capability_table(frame: pd.DataFrame) -> pd.DataFrame:
    """What each arm can and cannot do --- the capability matrix's RQ3 v2 column."""
    rows = frame.copy()
    rows["label"] = method_label(rows)
    out = []
    for label, group in rows.groupby("label"):
        usable = group[group["censored"] != 1]
        non_member = (
            group["winner_origin"].astype(str).str.startswith("decoded").mean()
            if group["winner_origin"].notna().any()
            else float("nan")
        )
        out.append(
            {
                "label": label,
                "n_rows": int(len(group)),
                "censored_rate": float(group["censored"].mean()),
                "can_return_non_member": (
                    "yes (measured)"
                    if non_member == non_member and non_member > 0
                    else ("no (a medoid returns an input)" if label.startswith("medoid:") else "")
                ),
                "frac_non_member": non_member,
                "reads_identities": "yes (oracle)" if label == ORACLE else "no",
                "exact_recovery": float(usable["exact_recovery"].mean())
                if not usable.empty
                else float("nan"),
                "blank_reason": (
                    group.loc[group["censored"] == 1, "reason"].dropna().astype(str).iloc[0]
                    if (group["censored"] == 1).any()
                    and group.loc[group["censored"] == 1, "reason"].notna().any()
                    else ""
                ),
            }
        )
    return pd.DataFrame(out).sort_values("label").reset_index(drop=True)


def edit_mix_table(frame: pd.DataFrame) -> pd.DataFrame:
    """The realised edit mix, per corpus and stratum.

    The design's mechanism is a statement about pendant facts, so the claim is
    only testable against the mix that actually occurred; an unlogged mix would
    leave it an assumption.
    """
    rows = frame[["collection", "stratum", "cell_t", "collection_id", "edit_mix"]].dropna()
    rows = rows.drop_duplicates(subset=["collection_id"])
    counts: dict[tuple[str, str, Any], dict[str, int]] = {}
    for _, row in rows.iterrows():
        try:
            mix = json.loads(str(row["edit_mix"]).replace("'", '"'))
        except (TypeError, ValueError):
            continue
        key = (row["collection"], row["stratum"], row["cell_t"])
        bucket = counts.setdefault(key, {})
        for kind, value in mix.items():
            bucket[kind] = bucket.get(kind, 0) + int(value)
    return pd.DataFrame(
        [
            {"collection": c, "stratum": s, "cell_t": t, **bucket}
            for (c, s, t), bucket in sorted(counts.items(), key=lambda item: str(item[0]))
        ]
    )


def summarize(frame: pd.DataFrame) -> dict[str, Any]:
    """Counts, tags and censoring --- what the table was computed from."""
    rows = frame.copy()
    rows["label"] = method_label(rows)
    return {
        "n_rows": int(len(frame)),
        "run_tags": sorted(frame["run_tag"].astype(str).unique().tolist()),
        "collections": sorted(frame["collection"].astype(str).unique().tolist()),
        "strata": sorted(frame["stratum"].astype(str).unique().tolist()),
        "n_seeds": int(frame["seed"].nunique()),
        "n_collections": int(frame["collection_id"].nunique()),
        "cells": sorted(frame["cell"].astype(str).unique().tolist()),
        "censored_by_label": rows.groupby("label")["censored"].mean().round(4).to_dict(),
        "judge_by_count": frame["fact_dist_judge"].value_counts().to_dict(),
    }


def analyze(root: Path, out: Path, run_tag: str | None) -> dict[str, Any]:
    """Run the full analysis and write ``summary.json``, ``stats.json`` and ``tables.md``."""
    frame = load_rows(root, run_tag)
    if len(frame["run_tag"].astype(str).unique()) > 1 and run_tag is None:
        logger.warning(
            "rows carry %d distinct run tags; pass --run-tag to analyze one configuration",
            len(frame["run_tag"].astype(str).unique()),
        )
    paths = io.RunPaths(root=out, rq=RQ_DIR, experiment=EXPERIMENT)
    paths.ensure()
    summary = summarize(frame)
    stats = hypotheses(frame)
    tables = {
        "Headline --- exact recovery and fact distance": headline_table(frame),
        "Capability --- what each arm can do": capability_table(frame),
        "Cost of the two consensus arms (H3.5)": cost_table(frame),
        "Realised edit mix": edit_mix_table(frame),
    }
    io.write_summary(paths, summary)
    io.write_stats(paths, stats)
    io.write_tables_md(paths, {name: table for name, table in tables.items() if not table.empty})
    return {"summary": summary, "stats": stats}


def _verdicts(stats: Mapping[str, Any]) -> str:
    lines = []
    for name in ("H3.1", "H3.2", "H3.3", "H3.4", "H3.5"):
        entry = stats.get(name)
        if not entry:
            continue
        verdict = "HELD" if entry.get("held") else "NOT HELD"
        lines.append(f"{name}: {verdict} --- {entry['statement']}")
        if not entry.get("held") and entry.get("fallback"):
            lines.append(f"    fallback: {entry['fallback']}")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point of ``python -m experiments.tkde.analyze_rq3v2``."""
    parser = argparse.ArgumentParser(description="Analyze RQ3 v2")
    parser.add_argument("--root", type=Path, default=None, help="results root the rows are under")
    parser.add_argument("--out", type=Path, default=None, help="where to write the outputs")
    parser.add_argument("--run-tag", default=None)
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    root = args.root or results_root()
    result = analyze(root, args.out or root, args.run_tag)
    print(json.dumps(result["summary"], indent=2))
    print()
    print(_verdicts(result["stats"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
