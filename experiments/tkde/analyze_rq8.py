"""RQ8 analyzer --- the completion tables and the pre-registered tests.

Reads the ``rows_units`` and ``rows_census`` files of one RQ8 run and writes the
four G6 artefacts a table rests on: ``summary.json``, ``stats.json``,
``tables.md`` and (unchanged) the rows beside them.

The three hypotheses are tested exactly as ``HEADLINE_DESIGN_2026-09-13.md``
section 4 pre-registers them, and the fallback is printed whenever one fails
rather than quietly dropped:

**H8.1** (headline) hit@10 of ``ow_ngram`` is above every baseline's on the
interior units of both corpora, Holm-significant. One-sided paired Wilcoxon over
the 27 seeds, ours ``greater``; the family for the Holm correction is the
baselines of one ``(corpus, stratum)`` table.

**H8.2** (control) on star units ``pattern_cooc >= ow_ngram`` is expected. It is
reported as the scope statement, two-sided, never hidden.

**H8.3** proposals valid and connected: ours 1.000 by theorem (Proposition C.8),
``fact_ngram`` below 1, ``incidence_ngram`` below 0.05. The third clause was
measured **false** at gate G8.1 (0.17 / 0.14) and is reported failed with its
reason rather than relaxed: the ceiling was ported from RQ6, where sampling is
*unconditional*, and here the prefix is itself a well-formed serialization, so a
truncated continuation decodes far more often. The threshold measures a
different experiment.

**hit@10 is already usable@10.** A proposal counts only if it decoded, is
connected, and carries the truth's certificate --- the runner's ``score`` takes
the ``accepted`` set, which requires a decode and a certificate, and then tests
``connected`` explicitly. There is therefore no separate corrected column:
``fact_ngram``'s disconnected samples never reach a hit. The table header says
so, so no reader has to reconstruct it.

Every representation that defines a distance and no completion operation appears
in the tables with the cell ``"no completion definable"`` --- the spec's rule
that a row which cannot be scored states why (section 1 rule 2), so a reader
never mistakes an absent row for an unfavourable one.
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from experiments.tkde import corpora as corpora_io
from experiments.tkde import io, stats
from experiments.tkde.config import TkdeError
from experiments.tkde.rq8 import (
    ARM_OURS,
    ARM_OURS_1F,
    ARM_OURS_HO,
    ARM_OURS_HO_1F,
    EXPERIMENT,
    KIND_INTERIOR,
    KIND_PENDANT,
    NO_COMPLETION_REASON,
    NON_GENERATIVE_ROWS,
    RQ_FOLDER,
    STRATUM_STAR,
)

logger = logging.getLogger(__name__)

#: ``fact_ngram`` must fall below 1 and ``incidence_ngram`` below this, per H8.3.
INCIDENCE_CEILING = 0.05

#: Every arm that is *ours*. None of these may enter another's Holm family: a
#: family is ours against the baselines, and scoring our own matched twin as a
#: competitor would both inflate the correction and answer a question the
#: pre-registration never asked.
OURS_FAMILY: frozenset[str] = frozenset({ARM_OURS, ARM_OURS_1F, ARM_OURS_HO, ARM_OURS_HO_1F})


class RQ8AnalysisError(TkdeError):
    """The RQ8 rows are absent or do not carry what a table needs."""


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def seed_scores(frame: Any, column: str) -> dict[tuple[str, str, str, str], dict[int, float]]:
    """``{(collection, stratum, kind, arm): {seed: score}}`` for one metric."""
    out: dict[tuple[str, str, str, str], dict[int, float]] = {}
    for row in frame.to_dict("records"):
        value = row.get(column)
        if value is None or value == "" or value != value:
            continue
        key = (
            str(row["collection"]),
            str(row["stratum"]),
            str(row["hidden_kind"]),
            str(row["arm"]),
        )
        out.setdefault(key, {})[int(row["seed"])] = float(value)
    return out


def paired(
    scores: Mapping[tuple[str, str, str, str], Mapping[int, float]],
    cell: tuple[str, str, str],
    ours: str,
) -> tuple[list[float], dict[str, list[float]]]:
    """Ours and every competitor of one cell, aligned on the seeds all share.

    Aligning rather than zipping matters: a stratum whose pool was too small in
    one seed contributes no row for that seed, and a silent zip would then pair
    seed 3 of one arm with seed 4 of another.
    """
    collection, stratum, kind = cell
    present = {
        arm: dict(values)
        for (c, s, k, arm), values in scores.items()
        if (c, s, k) == (collection, stratum, kind)
    }
    if ours not in present:
        return [], {}
    common = set(present[ours])
    for values in present.values():
        common &= set(values)
    order = sorted(common)
    return (
        [present[ours][seed] for seed in order],
        {
            arm: [values[seed] for seed in order]
            for arm, values in sorted(present.items())
            if arm != ours
        },
    )


def interval_table(
    scores: Mapping[tuple[str, str, str, str], Mapping[int, float]],
) -> list[dict[str, Any]]:
    """A 95 % BCa interval of every cell's mean, one row per arm."""
    rows: list[dict[str, Any]] = []
    for (collection, stratum, kind, arm), values in sorted(scores.items()):
        if not values:
            continue
        interval = stats.bca_ci([values[seed] for seed in sorted(values)], stat="mean")
        rows.append(
            {
                "collection": collection,
                "stratum": stratum,
                "hidden_kind": kind,
                "arm": arm,
                **interval.as_dict(),
            }
        )
    return rows


# ---------------------------------------------------------------------------
# The hypotheses
# ---------------------------------------------------------------------------


def test_h81(
    scores: Mapping[tuple[str, str, str, str], Mapping[int, float]],
) -> dict[str, Any]:
    """H8.1: ours above every baseline on the interior units of both corpora.

    The Holm family is ours against the **baselines**, not against the other
    ordered-walk arms. `ow_ngram_1f`, `ow_ngram_ho` and `ow_ngram_ho_1f` are all
    ours: including them would inflate the family, correct the p-values for
    comparisons the hypothesis never made, and score our own arms as if they
    were competitors. Each of them is instead tested against the same baseline
    family in its own right, which is what Amendment A1 needs answering --- in
    particular whether the matched arm's `wd50k66` lead survives Holm.
    """
    cells = sorted(
        {
            (collection, stratum)
            for (collection, stratum, kind, _arm) in scores
            if kind == KIND_INTERIOR and stratum != STRATUM_STAR
        }
    )
    candidates = [
        arm
        for arm in (ARM_OURS, ARM_OURS_1F, ARM_OURS_HO, ARM_OURS_HO_1F)
        if any(key[3] == arm for key in scores)
    ]
    per_cell: list[dict[str, Any]] = []
    for collection, stratum in cells:
        for candidate in candidates:
            ours, others = paired(scores, (collection, stratum, KIND_INTERIOR), candidate)
            others = {name: values for name, values in others.items() if name not in OURS_FAMILY}
            if not ours or not others:
                per_cell.append(
                    {
                        "collection": collection,
                        "stratum": stratum,
                        "arm": candidate,
                        "primary": candidate == ARM_OURS,
                        "verdict": "not testable",
                        "reason": "no paired seeds against any baseline",
                    }
                )
                continue
            family = stats.paired_family(ours, others, alternative="greater")
            per_cell.append(
                {
                    "collection": collection,
                    "stratum": stratum,
                    "arm": candidate,
                    "primary": candidate == ARM_OURS,
                    "n_seeds": len(ours),
                    "mean_ours": sum(ours) / len(ours),
                    "family": family,
                    "verdict": (
                        "supported"
                        if all(
                            row["reject"] and row["mean_ours"] > row["mean_other"] for row in family
                        )
                        else "not supported"
                    ),
                }
            )
    # The pre-registered hypothesis is about ARM_OURS; the other rows are the
    # amendment's evidence and are reported beside it without changing the verdict.
    primary = [cell for cell in per_cell if cell.get("primary")]
    supported = [cell for cell in primary if cell.get("verdict") == "supported"]
    per_cell_all, per_cell = per_cell, primary
    if len(supported) == len(per_cell) and per_cell:
        verdict, fallback = "supported", ""
    elif supported:
        verdict = "partially supported"
        fallback = (
            "The headline is scoped to "
            + ", ".join(f"{cell['collection']}/{cell['stratum']}" for cell in supported)
            + "; on the remaining cells the claim reduces to H8.3 plus the measured "
            "gap to the recommender."
        )
    else:
        verdict = "not supported"
        fallback = (
            "Pre-registered fallback: the claim reduces to H8.3 (proposals valid and "
            "connected by theorem) plus the measured gap to the recommender, and RQ8 "
            "becomes a supporting exhibit rather than a headline."
        )
    return {
        "hypothesis": "H8.1",
        "statement": (
            "hit@10 of ow_ngram exceeds every baseline on the interior units of both "
            "corpora, Holm-corrected one-sided paired Wilcoxon over seeds"
        ),
        "verdict": verdict,
        "fallback": fallback,
        "cells": per_cell,
        "amendment_a1_arms": [cell for cell in per_cell_all if not cell.get("primary")],
    }


def test_h82(
    scores: Mapping[tuple[str, str, str, str], Mapping[int, float]],
) -> dict[str, Any]:
    """H8.2: on star units ``pattern_cooc >= ow_ngram`` is expected; scope only."""
    cells = sorted(
        {
            (collection, stratum, kind)
            for (collection, stratum, kind, _arm) in scores
            if stratum == STRATUM_STAR
        }
    )
    rows: list[dict[str, Any]] = []
    for collection, stratum, kind in cells:
        ours, others = paired(scores, (collection, stratum, kind), ARM_OURS)
        recommender = others.get("pattern_cooc")
        if not ours or not recommender:
            continue
        test = stats.wilcoxon_paired(ours, recommender, alternative="two-sided")
        mean_ours = sum(ours) / len(ours)
        mean_them = sum(recommender) / len(recommender)
        rows.append(
            {
                "collection": collection,
                "stratum": stratum,
                "hidden_kind": kind,
                "n_seeds": len(ours),
                "mean_ours": mean_ours,
                "mean_pattern_cooc": mean_them,
                "delta": mean_ours - mean_them,
                **test,
                "expected": "pattern_cooc >= ow_ngram",
                "observed": (
                    "as expected" if mean_them >= mean_ours else "ours ahead on the control"
                ),
            }
        )
    return {
        "hypothesis": "H8.2",
        "statement": (
            "on star units pattern_cooc ties or beats ow_ngram; reported as the scope "
            "statement of the headline, not as a result to be avoided"
        ),
        "cells": rows,
    }


def test_h83(
    validity: Mapping[tuple[str, str, str, str], Mapping[int, float]],
    connectivity: Mapping[tuple[str, str, str, str], Mapping[int, float]],
) -> dict[str, Any]:
    """H8.3: ours valid and connected at 1.000; the two word baselines below."""

    def pooled(source: Mapping[tuple[str, str, str, str], Mapping[int, float]], arm: str) -> Any:
        values = [
            value
            for (_c, _s, _k, name), series in source.items()
            if name == arm
            for value in series.values()
        ]
        return stats.bca_ci(values, stat="mean").as_dict() if values else None

    ours_valid = pooled(validity, ARM_OURS)
    ours_connected = pooled(connectivity, ARM_OURS)
    fact_valid = pooled(validity, "fact_ngram")
    fact_connected = pooled(connectivity, "fact_ngram")
    incidence_valid = pooled(validity, "incidence_ngram")

    checks = {
        "ours_valid_is_one": bool(ours_valid and ours_valid["point"] >= 1.0),
        "ours_connected_is_one": bool(ours_connected and ours_connected["point"] >= 1.0),
        "fact_ngram_below_one": bool(fact_connected is not None and fact_connected["point"] < 1.0),
        "incidence_below_ceiling": bool(
            incidence_valid is not None and incidence_valid["point"] < INCIDENCE_CEILING
        ),
    }
    return {
        "hypothesis": "H8.3",
        "statement": (
            "every ow_ngram proposal is valid and connected (1.000, Proposition C.8); "
            f"fact_ngram below 1; incidence_ngram validity below {INCIDENCE_CEILING}"
        ),
        "ow_ngram_validity": ours_valid,
        "ow_ngram_connectivity": ours_connected,
        "fact_ngram_validity": fact_valid,
        "fact_ngram_connectivity": fact_connected,
        "incidence_ngram_validity": incidence_valid,
        "checks": checks,
        "verdict": "supported" if all(checks.values()) else "not supported",
    }


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------


def _frame(rows: Sequence[Mapping[str, Any]]) -> Any:
    import pandas as pd

    return pd.DataFrame(list(rows))


def capability_rows(metric: str) -> list[dict[str, Any]]:
    """The non-generative rows, each carrying its reason instead of a number."""
    return [
        {"arm": arm, metric: NO_COMPLETION_REASON, "note": NO_COMPLETION_REASON}
        for arm in NON_GENERATIVE_ROWS
    ]


def build_tables(
    units: Any,
    census: Any,
    intervals: Mapping[str, Sequence[Mapping[str, Any]]],
    hypotheses: Mapping[str, Any],
) -> dict[str, Any]:
    """Assemble every markdown table, non-generative rows included."""
    import pandas as pd

    tables: dict[str, Any] = {}
    if census is not None and not census.empty:
        tables["G0 --- star census"] = census[
            [
                "collection",
                "n_members",
                "n_star",
                "frac_star",
                "n_non_star",
                "shared_constants_mean",
                "shared_facts_mean",
                "n_pool",
                "n_pool_star",
                "n_pool_non_star",
            ]
        ]

    for metric, label in (
        ("hit_at_10", "hit@10 (= usable@10)"),
        ("pattern_at_10", "pattern@10"),
        ("validity", "validity"),
        ("connectivity", "connectivity"),
    ):
        frame = _frame(intervals[metric])
        if frame.empty:
            continue
        frame = frame.rename(columns={"point": label, "low": "ci_low", "high": "ci_high"})
        frame["note"] = "scored"
        blank = _frame(capability_rows(label))
        tables[f"{label} --- mean over seeds, 95 % BCa"] = pd.concat(
            [frame, blank], ignore_index=True
        )

    # Amendment A1: numerator AND denominator are restricted to proposals adding
    # exactly one fact. On the unrestricted denominator an extra-fact miss was
    # scored as an attachment miss, which reversed the sign of the reported
    # effect. The column name now carries its own denominator, and the fact-count
    # profile sits beside it so a reader can see how matched the arms were.
    # A pre-Amendment-A1 table carries none of the one-fact columns, because the
    # run that wrote it did not record the fact delta. That is a fact about the
    # run, not a defect: the mechanism table is emitted without the matched
    # statistic and says so, rather than the analyzer refusing to read an older
    # campaign or, worse, inventing a denominator for it.
    wanted = [
        "n_units",
        "n_hit",
        "n_pattern_hit",
        "n_pattern_hit_1f",
        "n_pattern_hit_1f_attach_miss",
        "n_accepted",
        "n_accepted_1f",
        "delta_facts_sum",
    ]
    present = [column for column in wanted if column in units.columns]
    matched = "n_pattern_hit_1f" in present and "n_pattern_hit_1f_attach_miss" in present
    mechanism = units.groupby(["collection", "stratum", "hidden_kind", "arm"], as_index=False)[
        present
    ].sum()
    if matched:
        mechanism = mechanism.assign(
            attach_miss_given_pattern_hit_on_a_one_fact_proposal=lambda f: (
                f["n_pattern_hit_1f_attach_miss"]
                / f["n_pattern_hit_1f"].where(f["n_pattern_hit_1f"] > 0)
            ),
            frac_accepted_1f=lambda f: (
                f["n_accepted_1f"] / f["n_accepted"].where(f["n_accepted"] > 0)
            ),
            delta_facts_mean=lambda f: (
                f["delta_facts_sum"] / f["n_accepted"].where(f["n_accepted"] > 0)
            ),
        )
        title = "Mechanism --- attachment miss, over one-fact proposals only"
    else:
        mechanism = mechanism.assign(note="pre-Amendment-A1 run: no fact-delta recorded")
        title = "Mechanism --- attachment miss NOT computable (pre-Amendment-A1 run)"
    tables[title] = mechanism

    verdicts = _frame(
        [
            {
                "hypothesis": name,
                "verdict": block.get("verdict", "reported as scope"),
                "fallback": block.get("fallback", ""),
            }
            for name, block in hypotheses.items()
        ]
    )
    tables["Pre-registered hypotheses"] = verdicts
    return tables


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def load_tagged(root: Path, table: str, run_tag: str | None) -> Any:
    """``load_table`` restricted to one run tag.

    Two RQ8 campaigns share a results directory --- the free-running arms and
    the Amendment A1 matched arms --- and they are *different measurements* of
    overlapping arms. ``load_table`` concatenates every tagged file it finds, so
    reading them together would silently pool two runs: an arm present in both
    would contribute twice to what the Wilcoxon believes are 27 seed-level
    replications. Passing ``run_tag`` keeps a table to one run; passing ``None``
    reproduces the old behaviour and is refused when more than one tag is
    present.

    Parameters
    ----------
    root : Path
        The results root.
    table : str
        Table name without the ``rows_`` prefix.
    run_tag : str or None
        The eight-hex run tag, or ``None`` for "whatever is there".

    Returns
    -------
    pandas.DataFrame
        The rows of that run.

    Raises
    ------
    RQ8AnalysisError
        If ``run_tag`` is ``None`` and the directory holds more than one tag.
    """
    import pandas as pd

    base = Path(root) / RQ_FOLDER
    paths = sorted(base.rglob(f"rows_{table}__*.csv"))
    paths = [p for p in paths if "_smoke" not in p.parts]
    tags = {p.name.split(f"rows_{table}__")[1].split("-")[0] for p in paths}
    if run_tag is None and len(tags) > 1:
        raise RQ8AnalysisError(
            f"{base} holds {len(tags)} run tags ({sorted(tags)}); pass --run-tag to "
            "pick one. Pooling them would mix two measurements of the same arms."
        )
    if run_tag is not None:
        paths = [p for p in paths if f"__{run_tag}-" in p.name]
    frames = []
    for path in paths:
        try:
            frames.append(pd.read_csv(path))
        except (OSError, ValueError) as exc:
            logger.warning("unreadable rows file %s: %s", path, exc)
    frames = [f for f in frames if not f.empty]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def analyze(root: Path, experiment: str, run_tag: str | None = None) -> dict[str, Any]:
    """Read one RQ8 run and write ``summary.json`` / ``stats.json`` / ``tables.md``."""
    units = load_tagged(Path(root), "units", run_tag)
    if units.empty:
        raise RQ8AnalysisError(f"no RQ8 unit rows under {Path(root) / RQ_FOLDER}")
    census = load_tagged(Path(root), "census", run_tag)

    metrics = ("hit_at_10", "pattern_at_10", "validity", "connectivity")
    scores = {metric: seed_scores(units, metric) for metric in metrics}
    intervals = {metric: interval_table(scores[metric]) for metric in metrics}

    hypotheses = {
        "H8.1": test_h81(scores["hit_at_10"]),
        "H8.2": test_h82(scores["hit_at_10"]),
        "H8.3": test_h83(scores["validity"], scores["connectivity"]),
    }

    summary = {
        "rq": "RQ8",
        "experiment": experiment,
        "run_tag": run_tag,
        "n_unit_rows": int(len(units)),
        "arms_scored": sorted(str(a) for a in units["arm"].unique()),
        "secondary_arm_enabled": ARM_OURS_HO in set(units["arm"].unique()),
        "matched_arms_enabled": sorted(
            arm for arm in (ARM_OURS_1F, ARM_OURS_HO_1F) if arm in set(units["arm"].unique())
        ),
        "non_generative_rows": {arm: NO_COMPLETION_REASON for arm in NON_GENERATIVE_ROWS},
        "census": census.to_dict("records") if census is not None and not census.empty else [],
        "intervals": intervals,
        "kinds": sorted(str(k) for k in units["hidden_kind"].unique()),
        "expected_kinds": [KIND_INTERIOR, KIND_PENDANT],
    }

    # Each run tag gets its own artefact directory, so the two campaigns'
    # summaries and tables cannot overwrite one another.
    folder = experiment if run_tag is None else f"{experiment}/_tag_{run_tag}"
    paths = io.RunPaths(root=Path(root), rq=RQ_FOLDER, experiment=folder)
    io.write_summary(paths, summary)
    io.write_stats(paths, {"hypotheses": hypotheses, "intervals": intervals})
    io.write_tables_md(paths, build_tables(units, census, intervals, hypotheses))
    return {"summary": summary, "hypotheses": hypotheses}


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point of ``python -m experiments.tkde.analyze_rq8``."""
    parser = argparse.ArgumentParser(prog="experiments.tkde.analyze_rq8")
    parser.add_argument("--root", type=Path, default=None, help="the results root")
    parser.add_argument("--experiment", default=EXPERIMENT)
    parser.add_argument(
        "--run-tag",
        default=None,
        help=(
            "eight-hex run tag to analyse. Required when the results directory "
            "holds more than one campaign, because pooling two runs of "
            "overlapping arms would corrupt the paired statistics."
        ),
    )
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    root = args.root if args.root is not None else corpora_io.results_root()
    result = analyze(Path(root), str(args.experiment), args.run_tag)
    for name, block in result["hypotheses"].items():
        logger.info("%s: %s", name, block.get("verdict", "reported as scope"))
        if block.get("fallback"):
            logger.info("%s fallback: %s", name, block["fallback"])
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
