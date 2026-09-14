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
