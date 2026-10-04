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
from experiments.tkde.config import DEFAULT_SEED_COUNT, TkdeError, load_yaml, results_root
from experiments.tkde.rq3v2 import EXPERIMENT, RQ_DIR
from experiments.tkde.stats import bca_ci, paired_family, wilson_ci

logger = logging.getLogger(__name__)

OURS = "consensus_ow"
ORACLE = "majority_merge_id"
FACT_ABLATION = "consensus_fact"
MERGE_BASELINES: tuple[str, ...] = ("align_merge_ref", "align_merge_iter", "pattern_vote")
COUNTING_BASELINE = "pattern_vote"

#: The row a structurally empty cell writes instead of collections (gate G0).
EMPTY_METHOD = "cell_empty"

#: One cell of the design: corpus x stratum x N x t.
CELL_KEY: tuple[str, ...] = ("collection", "stratum", "cell_N", "cell_t")

#: The campaign configuration, whose design grid names every cell.
DEFAULT_CONFIG = Path(__file__).resolve().parent / "configs" / "rq3v2.yaml"

#: Certified ratios are comparable only within one metric, so each consensus arm
#: is read against the members' medoid under its own metric.
RATIO_PAIRS: tuple[tuple[str, str, str], ...] = (
    ("indel", OURS, "medoid:isal_ow_indel"),
    ("levenshtein", "consensus_ow_lev", "medoid:isal_ow_struct"),
)

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
    "judge_timeout_s",
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


def supersede_tag(frame: pd.DataFrame, tag: str) -> pd.DataFrame:
    """Drop ``tag``'s rows in any cell another tag also measured.

    The heavy cells were re-scored under a shorter exact-oracle budget, so they
    carry a second tag; the partial rows the first pass had written for those
    cells are superseded and must not be pooled with the re-score.  Naming the
    superseded tag explicitly, rather than letting the analyzer prefer whichever
    tag has more seeds, keeps the decision in the command line and in the doc
    where a reader can see it.

    Cells that only ``tag`` measured are untouched --- superseding is per cell,
    not wholesale.

    Parameters
    ----------
    frame : pandas.DataFrame
        The loaded rows.
    tag : str
        The tag to yield where another tag also covers the cell.

    Returns
    -------
    pandas.DataFrame
        The surviving rows.
    """
    key = ["collection", "stratum", "cell_N", "cell_t"]
    tags = frame.groupby(key)["run_tag"].agg(lambda s: set(s.astype(str)))
    contested = {cell for cell, found in tags.items() if len(found) > 1 and tag in found}
    if not contested:
        return frame
    cells = frame[key].apply(tuple, axis=1)
    drop = cells.isin(contested) & (frame["run_tag"].astype(str) == tag)
    logger.info(
        "superseding tag %s in %d contested cells; %d rows dropped",
        tag,
        len(contested),
        int(drop.sum()),
    )
    return frame[~drop]


def check_one_tag_per_cell(frame: pd.DataFrame) -> dict[str, Any]:
    """Refuse a table whose cells are not each measured under a single tag.

    Two tags may legitimately coexist in one campaign --- the heavy cells were
    re-scored under a shorter exact-oracle budget, which is a measured parameter
    and therefore a different tag --- but a *cell* measured partly under one
    budget and partly under another is two experiments averaged together, and no
    footnote repairs that.  The merge is therefore by cell, and a cell carrying
    two tags is an error rather than a warning.

    Parameters
    ----------
    frame : pandas.DataFrame
        The loaded rows.

    Returns
    -------
    dict
        Per cell, its tag and the oracle budget that scored it.

    Raises
    ------
    RQ3v2AnalysisError
        If any cell carries more than one run tag.
    """
    key = ["collection", "stratum", "cell_N", "cell_t"]
    tags = frame.groupby(key)["run_tag"].agg(lambda s: sorted(set(s.astype(str))))
    offenders = {str(cell): found for cell, found in tags.items() if len(found) > 1}
    if offenders:
        raise RQ3v2AnalysisError(
            "these cells carry more than one run tag, so they mix two oracle budgets "
            f"and cannot be pooled: {offenders}"
        )
    # Per element, not ``astype(str)``: pandas 3 keeps a missing value a float
    # NaN there, and the first pass wrote no budget at all.
    budgets = frame.groupby(key)["judge_timeout_s"].agg(
        lambda s: sorted({str(v) for v in s if pd.notna(v) and str(v) not in ("", "nan")})
    )
    return {
        str(cell): {"run_tag": tags.loc[cell][0], "judge_timeout_s": budgets.loc[cell]}
        for cell in tags.index
    }


def fallback_rate_by_cell(frame: pd.DataFrame) -> pd.DataFrame:
    """Per cell, how often the exact oracle gave way to the bipartite judge.

    The footnote every table carrying a fact distance needs: a cell scored under
    a short oracle budget reports more bipartite readings, and the reader is
    entitled to know which cells those are rather than being told the axis is
    "exact HGED" and left to assume it everywhere.
    """
    rows = frame[frame["fact_dist_judge"].notna() & (frame["fact_dist_judge"] != "")]
    if rows.empty:
        return pd.DataFrame()
    grouped = rows.groupby(["collection", "stratum", "cell_N", "cell_t"])
    return (
        pd.DataFrame(
            {
                "n_scored": grouped.size(),
                "frac_exact": grouped["fact_dist_judge"].apply(
                    lambda s: float((s == "exact_hged").mean())
                ),
                "frac_bipartite": grouped["fact_dist_judge"].apply(
                    lambda s: float((s == "bipartite_ged_path").mean())
                ),
                "judge_timeout_s": grouped["judge_timeout_s"].apply(
                    lambda s: ",".join(sorted({str(v) for v in s if str(v) not in ("", "nan")}))
                ),
                "run_tag": grouped["run_tag"].apply(lambda s: ",".join(sorted(set(s.astype(str))))),
            }
        )
        .reset_index()
        .sort_values(["collection", "stratum", "cell_N", "cell_t"])
    )


def design_cells(config: Mapping[str, Any]) -> list[tuple[str, str, int, int]]:
    """Every corpus x stratum x N x t cell the configuration enumerates."""
    design = config["design"]
    return [
        (str(collection), str(stratum), int(n_members), int(t))
        for collection in design["collections"]
        for stratum in design["strata"]
        for n_members in design["n_values"]
        for t in design["t_values"]
    ]


def coverage_by_cell(
    frame: pd.DataFrame,
    expected_seeds: int,
    design_cells: Sequence[tuple[str, str, int, int]] = (),
) -> pd.DataFrame:
    """Seeds present per cell, and whether the cell may enter a hypothesis test.

    A cell is ``complete`` when it carries ``expected_seeds`` seeds under one run
    tag, ``empty`` when it holds only the structural-emptiness row of gate G0,
    ``absent`` when the design enumerates it and no row exists, and ``partial``
    otherwise.  Only complete cells are tested: a partial cell's seeds are the
    ones that happened to finish inside the wall, which is not the sample the
    harness fixes, so its numbers are descriptive and censored.

    Parameters
    ----------
    frame : pandas.DataFrame
        The loaded rows, after any supersession.
    expected_seeds : int
        Seeds a complete cell carries (``seed_count`` of the configuration).
    design_cells : Sequence of tuple, optional
        The cells the design enumerates (:func:`design_cells`); a cell with no
        row at all is otherwise invisible to a gate built from the rows.

    Returns
    -------
    pandas.DataFrame
        One row per cell with ``run_tag``, ``n_seeds``, ``expected_seeds``,
        ``n_collections`` and ``status``.
    """
    out = []
    seen = {
        (str(c), str(s), int(n), int(t))
        for c, s, n, t in frame[list(CELL_KEY)].drop_duplicates().itertuples(index=False)
    }
    for cell in design_cells:
        if tuple(cell) not in seen:
            out.append(
                {
                    **dict(zip(CELL_KEY, cell, strict=True)),
                    "run_tag": "",
                    "n_seeds": 0,
                    "expected_seeds": int(expected_seeds),
                    "n_collections": 0,
                    "status": "absent",
                }
            )
    for cell, group in frame.groupby(list(CELL_KEY)):
        measured = group[group["method"].astype(str) != EMPTY_METHOD]
        tags = sorted(set(group["run_tag"].astype(str)))
        n_seeds = int(group["seed"].nunique())
        if measured.empty:
            status = "empty"
        elif n_seeds >= expected_seeds and len(tags) == 1:
            status = "complete"
        else:
            status = "partial"
        out.append(
            {
                **dict(zip(CELL_KEY, cell, strict=True)),
                "run_tag": ",".join(tags),
                "n_seeds": n_seeds,
                "expected_seeds": int(expected_seeds),
                "n_collections": int(measured["collection_id"].nunique()),
                "status": status,
            }
        )
    return pd.DataFrame(out).sort_values(list(CELL_KEY)).reset_index(drop=True)


def complete_cells(frame: pd.DataFrame, coverage: pd.DataFrame) -> pd.DataFrame:
    """The rows of the cells ``coverage`` marks complete, and nothing else."""
    keep = {
        tuple(row) for row in coverage.loc[coverage["status"] == "complete", list(CELL_KEY)].values
    }
    cells = frame[list(CELL_KEY)].apply(tuple, axis=1)
    return frame[cells.isin(keep)]


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


def _untested_t(coverage: pd.DataFrame | None) -> tuple[list[str], dict[str, dict[str, list[int]]]]:
    """Non-star ``(collection, N)`` keys with no complete cell, and the t split of the rest."""
    if coverage is None or coverage.empty:
        return [], {}
    non_star = coverage[coverage["stratum"] == "non_star"]
    not_testable: list[str] = []
    split: dict[str, dict[str, list[int]]] = {}
    for (collection, n_members), group in non_star.groupby(["collection", "cell_N"]):
        key = f"{collection}|N{int(n_members)}"
        tested = sorted(int(t) for t in group.loc[group["status"] == "complete", "cell_t"])
        untested = sorted(
            int(t) for t in group.loc[group["status"].isin(["partial", "absent"]), "cell_t"]
        )
        if tested:
            split[key] = {"t_tested": tested, "t_not_testable": untested}
        elif untested:
            not_testable.append(key)
    return not_testable, split


def hypotheses(frame: pd.DataFrame, coverage: pd.DataFrame | None = None) -> dict[str, Any]:
    """Test H3.1--H3.6 as pre-registered, with their declared fallbacks.

    Parameters
    ----------
    frame : pandas.DataFrame
        The rows to test --- the complete cells only (:func:`complete_cells`).
    coverage : pandas.DataFrame or None, optional
        The per-cell coverage of the whole campaign, so H3.1 can name the
        ``(collection, N)`` it could not test instead of silently narrowing
        "for every N".

    Returns
    -------
    dict
        One entry per hypothesis, each with ``held`` and, where the scope was
        narrowed by coverage, a ``verdict`` string that says so.
    """
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
    not_testable, t_split = _untested_t(coverage)
    recovery = per_seed(non_star, "exact_recovery")
    for (collection, n_members), cell in recovery.groupby(["collection", "cell_N"]):
        key = f"{collection}|N{int(n_members)}"
        family = _paired(cell, OURS, MERGE_BASELINES, "greater")
        h31["cells"][key] = {
            "family": family,
            "held": bool(family) and all(row["reject"] and row["p_holm"] < ALPHA for row in family),
            **t_split.get(key, {}),
        }
    decided = [entry["held"] for entry in h31["cells"].values()]
    h31["held"] = bool(decided) and all(decided)
    h31["not_testable"] = not_testable
    narrowed = not_testable + [
        f"{key} t={entry['t_not_testable']}"
        for key, entry in t_split.items()
        if entry["t_not_testable"]
    ]
    if not decided:
        h31["verdict"] = "not testable: no complete non-star cell"
    elif h31["held"] and not narrowed:
        h31["verdict"] = "supported"
    elif h31["held"]:
        h31["verdict"] = f"supported on the tested cells; not testable at {narrowed}"
    else:
        h31["verdict"] = "not supported" + (f"; not testable at {narrowed}" if narrowed else "")
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
    # Every medoid the rows carry, the like-for-like indel medoid included; an arm
    # whose every row is censored (hypercot without its environment) has no
    # score to compare and is named rather than dropped silently.
    distance = per_seed(frame, "fact_dist")
    labelled = frame.assign(label=method_label(frame)) if not frame.empty else frame
    medoids = sorted(
        str(name) for name in distance["label"].unique() if str(name).startswith("medoid:")
    )
    unscored = sorted(
        str(name)
        for name in (labelled["label"].unique() if not labelled.empty else [])
        if str(name).startswith("medoid:") and str(name) not in medoids
    )
    family = _paired(distance, OURS, medoids, "less")
    out["H3.2"] = {
        "statement": "consensus_ow fact-level distance is below every medoid's",
        "family": family,
        "medoids_not_scored": unscored,
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
    # The margin hypotheses are judged on the point estimate as registered; the
    # seed-paired interval, p and effect size are printed beside it so a reader
    # sees how far from the margin the estimate sits.
    out["H3.3"] = {
        "statement": "on non-stars, consensus_ow >= majority_merge_id - 0.05",
        "ours": ours_rate,
        "oracle_labelled_as_oracle": oracle_rate,
        "gap": gap,
        "paired": _paired(per_seed(non_star, "exact_recovery"), OURS, [ORACLE], "two-sided"),
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
        "paired": _paired(per_seed(star, "exact_recovery"), OURS, [COUNTING_BASELINE], "two-sided"),
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
        "paired": _paired(per_seed(frame, "exact_recovery"), OURS, [FACT_ABLATION], "two-sided"),
        "held": bool(ablation_gap == ablation_gap and ablation_gap >= -MARGIN),
        "cost": cost_table(frame).to_dict(orient="records"),
        "fallback": (
            "if consensus_fact is strictly better this is reported, and RQ3's language claim "
            "reduces to the decoded output, the certificate and the cost"
        ),
    }

    # H3.6 --- the small-N prediction, and whether the shortfall is legible. Read
    # within each corpus x stratum x t series: under partial coverage the pooled
    # mean per N averages different cells at different N, which is a change of
    # composition and not of N.
    ours_rows = frame[(frame["method"] == OURS) & (frame["censored"] != 1)]
    pooled, _ = _by_n(ours_rows)
    by_series: dict[str, Any] = {}
    for (collection, stratum, t), series in ours_rows.groupby(["collection", "stratum", "cell_t"]):
        entries, monotone = _by_n(series)
        by_series[f"{collection}|{stratum}|t{int(t)}"] = {
            "by_N": entries,
            "monotone_in_N": monotone,
            "n_values": len(entries),
        }
    comparable = [entry for entry in by_series.values() if entry["n_values"] >= 2]
    out["H3.6"] = {
        "statement": (
            "consensus_ow exact recovery rises with N, and the small-N shortfall is a "
            "sub-record of the source rather than an arbitrary object"
        ),
        "by_series": by_series,
        "by_N_pooled": pooled,
        "pooled_note": (
            "pooled over every tested cell at each N; the cells differ across N when coverage "
            "is partial, so this figure is not used for the verdict"
        ),
        "n_series_compared": len(comparable),
        "held": bool(comparable) and all(entry["monotone_in_N"] for entry in comparable),
        "note": (
            "the mechanism: dropping a fact one member lacks saves that member an insertion "
            "(5-10 tokens) and costs the other N-1 a deletion (about 1 each), so the word "
            "median can prefer a sub-record at small N and should not at large N. The verdict "
            "reads the monotonicity clause; the sub-record clause carries no registered "
            "threshold and is reported as the share of misses"
        ),
    }
    return out


def _by_n(rows: pd.DataFrame) -> tuple[dict[str, Any], bool]:
    """Recovery per N with its seed-level BCa interval, the miss anatomy, and monotonicity."""
    entries: dict[str, Any] = {}
    monotone = True
    previous: float | None = None
    for n_members in sorted(rows["cell_N"].dropna().unique()):
        cell = rows[rows["cell_N"] == n_members]
        recovery = float(cell["exact_recovery"].mean())
        by_seed = cell.groupby("seed")["exact_recovery"].mean()
        missed = cell[cell["exact_recovery"] != 1]
        drops = (
            pd.to_numeric(missed["sub_record_drop"], errors="coerce")
            if "sub_record_drop" in missed.columns
            else pd.Series(dtype=float)
        )
        entries[f"N{int(n_members)}"] = {
            "n": int(len(cell)),
            "n_seeds": int(by_seed.size),
            "exact_recovery": recovery,
            "bca": bca_ci(by_seed.tolist()).as_dict() if by_seed.size >= 3 else None,
            "n_missed": int(len(missed)),
            "sub_record_frac_of_missed": float((drops > 0).mean()) if len(drops) else None,
            "not_sub_record_frac_of_missed": float((drops == -1).mean()) if len(drops) else None,
        }
        if previous is not None and recovery + 1e-12 < previous:
            monotone = False
        previous = recovery
    return entries, monotone


def cost_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Pool size and wall-clock of each consensus arm, which is part of the argument."""
    rows = frame[frame["method"].isin([OURS, FACT_ABLATION]) & (frame["censored"] != 1)]
    if rows.empty:
        return pd.DataFrame()
    return (
        rows.groupby(["method", *CELL_KEY])
        .agg(
            n=("secs", "size"),
            median_secs=("secs", "median"),
            max_secs=("secs", "max"),
            median_pool=("pool_size", "median"),
            median_decoded=("n_decoded", "median"),
        )
        .reset_index()
    )


def certified_ratio_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Per cell, each consensus arm's certified ratio beside its same-metric medoid's.

    ``ratio = cost / LB`` with Prop 3's pairwise bound.  The consensus searches
    the pool *and* the members, so its cost can never exceed the medoid's under
    the same metric; ``frac_consensus_at_or_below`` is therefore 1 by
    construction and is printed as a check on the rows, not as a finding.
    """
    rows = frame[(frame["censored"] != 1) & frame["ratio"].notna()].copy()
    if rows.empty:
        return pd.DataFrame()
    rows["label"] = method_label(rows)
    out = []
    for metric, ours, medoid in RATIO_PAIRS:
        subset = rows[rows["label"].isin([ours, medoid])]
        if subset.empty:
            continue
        wide = subset.pivot_table(
            index=[*CELL_KEY, "collection_id"], columns="label", values="ratio"
        )
        if ours not in wide.columns or medoid not in wide.columns:
            continue
        wide = wide[[ours, medoid]].dropna()
        for cell, group in wide.groupby(level=list(CELL_KEY)):
            out.append(
                {
                    **dict(zip(CELL_KEY, cell, strict=True)),
                    "metric": metric,
                    "consensus": ours,
                    "medoid": medoid,
                    "n_paired": int(len(group)),
                    "consensus_mean": float(group[ours].mean()),
                    "consensus_median": float(group[ours].median()),
                    "medoid_mean": float(group[medoid].mean()),
                    "medoid_median": float(group[medoid].median()),
                    "frac_consensus_below": float((group[ours] < group[medoid]).mean()),
                    "frac_consensus_at_or_below": float((group[ours] <= group[medoid]).mean()),
                }
            )
    return pd.DataFrame(out)


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


def analyze(
    root: Path,
    out: Path,
    run_tag: str | None,
    superseded: str | None = None,
    expected_seeds: int = DEFAULT_SEED_COUNT,
    config_path: Path | None = None,
) -> dict[str, Any]:
    """Run the full analysis and write ``summary.json``, ``stats.json`` and ``tables.md``.

    Every table is written over all cells, each row carrying its cell's coverage
    status; the hypotheses read the complete cells only (:func:`coverage_by_cell`).
    ``config_path`` supplies the design grid, so a cell that wrote no row at all
    is reported absent rather than missed.
    """
    grid = design_cells(load_yaml(config_path)) if config_path is not None else []
    frame = load_rows(root, run_tag)
    if superseded:
        frame = supersede_tag(frame, superseded)
    tags = sorted(frame["run_tag"].astype(str).unique())
    if len(tags) > 1 and run_tag is None:
        # Expected in this campaign: the heavy cells were re-scored under a
        # shorter oracle budget. Legitimate per cell, fatal within one --- which
        # check_one_tag_per_cell enforces below.
        logger.info("merging %d run tags cell by cell: %s", len(tags), tags)
    paths = io.RunPaths(root=out, rq=RQ_DIR, experiment=EXPERIMENT)
    paths.ensure()
    # Raises rather than warns: a cell averaged over two oracle budgets is two
    # experiments, and no footnote repairs that.
    per_cell_tags = check_one_tag_per_cell(frame)
    coverage = coverage_by_cell(frame, expected_seeds, design_cells=grid)
    tested = complete_cells(frame, coverage)
    summary = summarize(frame)
    summary["tag_by_cell"] = per_cell_tags
    summary["coverage_gate"] = {
        "expected_seeds": int(expected_seeds),
        "design_grid_from": str(config_path) if config_path is not None else None,
        **{
            status: [
                "|".join(str(row[key]) for key in CELL_KEY) + f" ({row['n_seeds']} seeds)"
                for _, row in coverage[coverage["status"] == status].iterrows()
            ]
            for status in ("complete", "partial", "absent", "empty")
        },
    }
    # No hypothesis test runs on a partial table: a cell's finished seeds are the
    # ones that fit inside the wall, not the sample the harness fixes.
    stats = (
        hypotheses(tested, coverage=coverage)
        if not tested.empty
        else {"note": "no cell is complete; no hypothesis is testable"}
    )
    stats["coverage_gate"] = summary["coverage_gate"]
    status = coverage[[*CELL_KEY, "status", "n_seeds"]]

    def with_status(table: pd.DataFrame) -> pd.DataFrame:
        return table.merge(status, on=list(CELL_KEY), how="left") if not table.empty else table

    tables = {
        "Coverage per cell (hypothesis tests read the complete cells only)": coverage,
        "Headline --- exact recovery and fact distance (partial cells: descriptive, censored)": (
            with_status(headline_table(frame))
        ),
        "Certified ratio --- each consensus arm against its same-metric medoid": with_status(
            certified_ratio_table(frame)
        ),
        "Capability --- what each arm can do": capability_table(frame),
        "Cost of the two consensus arms (H3.5)": with_status(cost_table(frame)),
        "Judge fallback rate per cell (footnote to every fact-distance column)": with_status(
            fallback_rate_by_cell(frame)
        ),
        "Realised edit mix": edit_mix_table(frame),
    }
    io.write_summary(paths, summary)
    io.write_stats(paths, stats)
    io.write_tables_md(paths, {name: table for name, table in tables.items() if not table.empty})
    return {"summary": summary, "stats": stats}


def _verdicts(stats: Mapping[str, Any]) -> str:
    lines = []
    for name in ("H3.1", "H3.2", "H3.3", "H3.4", "H3.5", "H3.6"):
        entry = stats.get(name)
        if not entry:
            continue
        verdict = "HELD" if entry.get("held") else "NOT HELD"
        if entry.get("verdict"):
            verdict = f"{verdict} ({entry['verdict']})"
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
    parser.add_argument(
        "--supersede-tag",
        default=None,
        help=(
            "drop this tag's rows in any cell another tag also measured; the heavy cells "
            "were re-scored under a shorter oracle budget and their partial first-pass rows "
            "are superseded"
        ),
    )
    parser.add_argument(
        "--expected-seeds",
        type=int,
        default=DEFAULT_SEED_COUNT,
        help=(
            "seeds a complete cell carries (the configuration's seed_count); hypothesis "
            "tests read only cells with this many seeds under one tag"
        ),
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="the campaign configuration whose design grid names every cell",
    )
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    root = args.root or results_root()
    result = analyze(
        root,
        args.out or root,
        args.run_tag,
        args.supersede_tag,
        args.expected_seeds,
        args.config,
    )
    print(json.dumps(result["summary"], indent=2))
    print()
    print(_verdicts(result["stats"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
