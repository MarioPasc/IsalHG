"""The analyzer's two-tag merge rule.

The heavy cells of campaign 2308421 were re-scored under a shorter exact-oracle
budget, which is a *measured* parameter and so carries its own run tag. Merging
those rows with the frozen-budget ones is legitimate **per cell** and fatal
**within** one: a cell averaged over two instruments is two experiments, and no
footnote repairs that. This file pins the rule in both directions.
"""

from __future__ import annotations

import pandas as pd
import pytest

from experiments.tkde import analyze_rq3v2 as an

pytestmark = pytest.mark.unit


def _rows(spec):
    """One row per (cell, tag, judge) triple given as a tuple."""
    return pd.DataFrame(
        [
            {
                "collection": collection,
                "stratum": stratum,
                "cell_N": n,
                "cell_t": t,
                "run_tag": tag,
                "judge_timeout_s": budget,
                "fact_dist_judge": judge,
                "method": "consensus_ow",
                "arm": "isal_ow_struct",
                "censored": 0,
                "exact_recovery": 1,
                "fact_dist": 0.0,
                "secs": 1.0,
            }
            for collection, stratum, n, t, tag, budget, judge in spec
        ]
    )


class TestOneTagPerCell:
    def test_two_tags_in_different_cells_are_allowed(self):
        frame = _rows(
            [
                ("ndc_classes", "non_star", 5, 1, "aaaa", 60.0, "exact_hged"),
                ("ndc_classes", "non_star", 15, 1, "bbbb", 8.0, "bipartite_ged_path"),
            ]
        )
        report = an.check_one_tag_per_cell(frame)
        assert len(report) == 2
        assert {entry["run_tag"] for entry in report.values()} == {"aaaa", "bbbb"}

    def test_two_tags_in_the_same_cell_are_refused(self):
        frame = _rows(
            [
                ("ndc_classes", "non_star", 15, 1, "aaaa", 60.0, "exact_hged"),
                ("ndc_classes", "non_star", 15, 1, "bbbb", 8.0, "bipartite_ged_path"),
            ]
        )
        with pytest.raises(an.RQ3v2AnalysisError, match="more than one run tag"):
            an.check_one_tag_per_cell(frame)

    def test_the_error_names_the_offending_cell(self):
        frame = _rows(
            [
                ("wd50k66", "star", 9, 2, "aaaa", 60.0, "exact_hged"),
                ("wd50k66", "star", 9, 2, "bbbb", 8.0, "exact_hged"),
            ]
        )
        with pytest.raises(an.RQ3v2AnalysisError) as caught:
            an.check_one_tag_per_cell(frame)
        assert "wd50k66" in str(caught.value)

    def test_a_single_tag_throughout_is_fine(self):
        frame = _rows(
            [
                ("ndc_classes", "non_star", 5, 1, "aaaa", 60.0, "exact_hged"),
                ("ndc_classes", "non_star", 9, 1, "aaaa", 60.0, "exact_hged"),
            ]
        )
        assert len(an.check_one_tag_per_cell(frame)) == 2


class TestFallbackRate:
    def test_it_reports_the_exact_and_bipartite_shares_per_cell(self):
        frame = _rows(
            [
                ("ndc_classes", "non_star", 5, 1, "aaaa", 60.0, "exact_hged"),
                ("ndc_classes", "non_star", 5, 1, "aaaa", 60.0, "exact_hged"),
                ("ndc_classes", "non_star", 5, 1, "aaaa", 60.0, "bipartite_ged_path"),
                ("ndc_classes", "non_star", 15, 1, "bbbb", 8.0, "bipartite_ged_path"),
            ]
        )
        table = an.fallback_rate_by_cell(frame)
        light = table[table["cell_N"] == 5].iloc[0]
        heavy = table[table["cell_N"] == 15].iloc[0]
        assert light["n_scored"] == 3
        assert light["frac_exact"] == pytest.approx(2 / 3)
        assert heavy["frac_bipartite"] == pytest.approx(1.0)
        assert "8.0" in str(heavy["judge_timeout_s"])

    def test_an_empty_frame_yields_an_empty_table(self):
        frame = _rows([("ndc_classes", "non_star", 5, 1, "aaaa", 60.0, "")])
        assert an.fallback_rate_by_cell(frame).empty


class TestMissingBudget:
    """The first pass wrote no ``judge_timeout_s``; the recovery pass did.

    ``load_rows`` coerces the column to float, so a cell read from both carries
    ``NaN`` beside ``60.0``.  Under pandas 3 ``astype(str)`` keeps the ``NaN`` a
    float, and sorting it with the strings raised ``TypeError`` on the real
    campaign tree (2026-10-04) before any table was written.
    """

    def test_a_row_without_a_budget_does_not_break_the_report(self):
        frame = _rows(
            [
                ("ndc_classes", "non_star", 5, 1, "aaaa", 60.0, "exact_hged"),
                ("ndc_classes", "non_star", 5, 1, "aaaa", None, "exact_hged"),
            ]
        )
        frame["judge_timeout_s"] = pd.to_numeric(frame["judge_timeout_s"], errors="coerce")
        report = an.check_one_tag_per_cell(frame)
        (entry,) = report.values()
        assert entry["judge_timeout_s"] == ["60.0"]


def _campaign(cells, recoveries):
    """Seed-level rows for several methods.

    ``cells`` holds ``(collection, stratum, N, t, tag, seeds)``; ``recoveries``
    maps ``(collection, stratum, N, t)`` to ``{label: exact_recovery}``.  Each
    (cell, seed, label) is one collection, which is all the seed-level tests
    need.
    """
    out = []
    for collection, stratum, n, t, tag, seeds in cells:
        values = recoveries[(collection, stratum, n, t)]
        for seed in seeds:
            for label, value in values.items():
                medoid = label.startswith("medoid:")
                out.append(
                    {
                        "collection": collection,
                        "stratum": stratum,
                        "cell_N": n,
                        "cell_t": t,
                        "cell": f"{stratum}_N{n}_t{t}",
                        "seed": seed,
                        "run_tag": tag,
                        "collection_id": f"{stratum}_N{n}_t{t}|s{seed}|x",
                        "method": "medoid" if medoid else label,
                        "arm": label.split(":", 1)[1] if medoid else "isal_ow_struct",
                        "censored": 0,
                        "exact_recovery": float(value),
                        "fact_dist": 1.0 - float(value),
                        "secs": 1.0,
                        "judge_timeout_s": 60.0,
                        "fact_dist_judge": "exact_hged",
                        "sub_record_drop": 0.0 if value == 1 else 1.0,
                        "ratio": 1.0,
                        "pool_size": 10.0,
                        "n_decoded": 20.0,
                    }
                )
    return pd.DataFrame(out)


def _empty_cell(collection, stratum, n, t, tag, seeds):
    return pd.DataFrame(
        [
            {
                "collection": collection,
                "stratum": stratum,
                "cell_N": n,
                "cell_t": t,
                "cell": f"{stratum}_N{n}_t{t}",
                "seed": seed,
                "run_tag": tag,
                "collection_id": None,
                "method": "cell_empty",
                "arm": None,
                "censored": 1,
                "exact_recovery": float("nan"),
                "fact_dist": float("nan"),
                "secs": float("nan"),
                "judge_timeout_s": float("nan"),
                "fact_dist_judge": None,
                "sub_record_drop": float("nan"),
                "ratio": float("nan"),
            }
            for seed in seeds
        ]
    )


WIN = {
    "consensus_ow": 1,
    "align_merge_ref": 0,
    "align_merge_iter": 0,
    "pattern_vote": 0,
    "majority_merge_id": 1,
    "consensus_fact": 1,
    "medoid:isal_ow_indel": 0,
}


class TestCoverageGate:
    """No hypothesis test runs on a partially covered cell (SESSION_LOG section 10).

    Before this gate the analyzer pooled whatever rows existed: H3.1 grouped by
    ``(collection, N)`` would have tested ``N = 15`` on two seeds, and H3.2 /
    H3.4 / H3.6 would have averaged partial cells into their pooled figures.
    """

    # Eight seeds: the smallest exact one-sided Wilcoxon p is 2**-8, which
    # survives Holm over the three merges at 0.05.
    SEEDS = list(range(1, 9))

    def _frame(self):
        complete = ("ndc_classes", "non_star", 5, 1, "aaaa", self.SEEDS)
        partial = ("ndc_classes", "non_star", 15, 1, "bbbb", [1, 2])
        frame = _campaign(
            [complete, partial],
            {
                ("ndc_classes", "non_star", 5, 1): WIN,
                ("ndc_classes", "non_star", 15, 1): {**WIN, "consensus_ow": 0},
            },
        )
        empty = _empty_cell("ndc_classes", "star", 5, 1, "aaaa", self.SEEDS)
        return pd.concat([frame, empty], ignore_index=True)

    def test_each_cell_is_complete_partial_or_empty(self):
        coverage = an.coverage_by_cell(self._frame(), expected_seeds=len(self.SEEDS))
        status = {
            (row.stratum, int(row.cell_N)): row.status for row in coverage.itertuples(index=False)
        }
        assert status == {
            ("non_star", 5): "complete",
            ("non_star", 15): "partial",
            ("star", 5): "empty",
        }
        partial = coverage[coverage["status"] == "partial"].iloc[0]
        assert partial["n_seeds"] == 2

    def test_only_complete_cells_survive_the_gate(self):
        frame = self._frame()
        kept = an.complete_cells(frame, an.coverage_by_cell(frame, expected_seeds=len(self.SEEDS)))
        assert set(kept["cell_N"].astype(int)) == {5}
        assert set(kept["stratum"]) == {"non_star"}

    def test_a_partial_cell_is_reported_not_testable_and_never_tested(self):
        frame = self._frame()
        coverage = an.coverage_by_cell(frame, expected_seeds=len(self.SEEDS))
        stats = an.hypotheses(an.complete_cells(frame, coverage), coverage=coverage)
        h31 = stats["H3.1"]
        assert set(h31["cells"]) == {"ndc_classes|N5"}
        assert "ndc_classes|N15" in h31["not_testable"]
        assert h31["held"] is True
        assert "not testable" in h31["verdict"]

    def test_a_design_cell_with_no_row_is_absent_and_not_testable(self):
        """Three heavy cells of 2311520 wrote nothing; a gate built from rows alone
        could not see them, and H3.1's "for every N" would have looked whole."""
        frame = self._frame()
        grid = [("ndc_classes", "non_star", n, t) for n in (5, 15) for t in (1, 2)]
        coverage = an.coverage_by_cell(frame, expected_seeds=len(self.SEEDS), design_cells=grid)
        absent = coverage[coverage["status"] == "absent"]
        assert {(int(r.cell_N), int(r.cell_t)) for r in absent.itertuples()} == {(5, 2), (15, 2)}
        assert (absent["n_seeds"] == 0).all()
        stats = an.hypotheses(an.complete_cells(frame, coverage), coverage=coverage)
        h31 = stats["H3.1"]
        assert "ndc_classes|N15" in h31["not_testable"]
        assert h31["cells"]["ndc_classes|N5"]["t_not_testable"] == [2]

    def test_the_two_tags_are_not_pooled_into_one_count(self):
        frame = _campaign(
            [
                ("ndc_classes", "non_star", 9, 2, "aaaa", [1, 2]),
                ("ndc_classes", "non_star", 9, 1, "aaaa", [1, 2, 3]),
            ],
            {
                ("ndc_classes", "non_star", 9, 2): WIN,
                ("ndc_classes", "non_star", 9, 1): WIN,
            },
        )
        later = _campaign(
            [("ndc_classes", "non_star", 9, 2, "bbbb", [3])],
            {("ndc_classes", "non_star", 9, 2): WIN},
        )
        merged = an.supersede_tag(pd.concat([frame, later], ignore_index=True), "aaaa")
        coverage = an.coverage_by_cell(merged, expected_seeds=3)
        row = coverage[coverage["cell_t"] == 2].iloc[0]
        assert row["status"] == "partial"
        assert row["n_seeds"] == 1


class TestH36Series:
    """H3.6 is read within a corpus x stratum x t series.

    Under partial coverage the pooled figure per ``N`` averages different cells
    at different ``N`` --- a composition change, not a change in ``N``.
    """

    def _frame(self, n5, n9):
        series = ("wd50k66", "star", 1)
        other = ("ndc_classes", "non_star", 1)
        cells = [
            (*series[:2], 5, series[2], "aaaa", [1, 2, 3, 4, 5]),
            (*series[:2], 9, series[2], "aaaa", [1, 2, 3, 4, 5]),
            (*other[:2], 5, other[2], "aaaa", [1, 2, 3, 4, 5]),
        ]
        recoveries = {
            ("wd50k66", "star", 5, 1): {"consensus_ow": n5},
            ("wd50k66", "star", 9, 1): {"consensus_ow": n9},
            ("ndc_classes", "non_star", 5, 1): {"consensus_ow": 1},
        }
        return _campaign(cells, recoveries)

    def test_a_rise_within_the_series_holds_although_the_pooled_mean_falls(self):
        stats = an.hypotheses(self._frame(n5=0, n9=1))
        h36 = stats["H3.6"]
        series = h36["by_series"]["wd50k66|star|t1"]
        assert series["monotone_in_N"] is True
        assert h36["held"] is True

    def test_a_fall_within_the_series_fails(self):
        stats = an.hypotheses(self._frame(n5=1, n9=0))
        assert stats["H3.6"]["held"] is False


class TestCertifiedRatio:
    def test_consensus_is_read_against_the_indel_medoid(self):
        frame = _campaign(
            [("wd50k66", "non_star", 5, 1, "aaaa", [1, 2, 3])],
            {("wd50k66", "non_star", 5, 1): WIN},
        )
        frame.loc[frame["method"] == "consensus_ow", "ratio"] = 1.1
        frame.loc[frame["arm"] == "isal_ow_indel", "ratio"] = 1.3
        table = an.certified_ratio_table(frame)
        row = table[table["metric"] == "indel"].iloc[0]
        assert row["n_paired"] == 3
        assert row["consensus_mean"] == pytest.approx(1.1)
        assert row["medoid_mean"] == pytest.approx(1.3)
        assert row["frac_consensus_below"] == pytest.approx(1.0)


class TestEveryMedoidInH32:
    def test_the_indel_medoid_is_in_the_h32_family(self):
        frame = _campaign(
            [("wd50k66", "non_star", 5, 1, "aaaa", [1, 2, 3, 4])],
            {("wd50k66", "non_star", 5, 1): WIN},
        )
        names = {row["name"] for row in an.hypotheses(frame)["H3.2"]["family"]}
        assert "medoid:isal_ow_indel" in names
