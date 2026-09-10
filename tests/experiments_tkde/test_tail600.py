"""Unit tests for the 600 s tail characterisation (T-KBp).

Three things are worth pinning and nothing else is: the census readers (a
missing sidecar is data, a malformed one is a defect), the shard split (it must
partition, because a lost shard is a member silently absent from a completion
count), and the verdict logic against inputs whose answer is known by
construction -- the point of a pre-stated expectation is that the scoring cannot
drift towards the data.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import pytest

from experiments.tkde import tail600
from experiments.tkde.analyze_tail600 import (
    CONFIRMED,
    INDETERMINATE,
    MATERIAL_FRACTION,
    MOST_FRACTION,
    REFUTED,
    ArmTally,
    Tail600AnalysisError,
    budgets,
    read_rows,
    render,
    score,
    tally,
    verdict_material,
    verdict_mechanism,
    verdict_most_censored,
)
from experiments.tkde.tail600 import (
    Tail600Error,
    Tail600SourceError,
    TailMember,
    parse_shard,
    read_m3_census,
    read_sidecar_census,
    shard_slice,
    worklist,
)

pytestmark = pytest.mark.unit


M3_COLUMNS = (
    "rq",
    "experiment",
    "git_sha",
    "host_cpu",
    "collection",
    "seed",
    "member_id",
    "n",
    "m",
    "k",
    "aut_bucket",
    "arm",
    "tokens",
    "n_instr",
    "secs",
    "censored",
)


def _write_m3(path: Path, rows: list[dict[str, Any]], columns=M3_COLUMNS) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns), restval="")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _m3_row(member_id: str, arm: str, censored: int, **kwargs: Any) -> dict[str, Any]:
    row = {
        "rq": 1,
        "experiment": "merged",
        "git_sha": "abc1234",
        "host_cpu": "test",
        "collection": "ndc_classes",
        "seed": 1,
        "member_id": member_id,
        "n": 12,
        "m": 30,
        "k": 10,
        "aut_bucket": "<1e3",
        "arm": arm,
        "tokens": 0,
        "n_instr": 0,
        "secs": 60.0,
        "censored": censored,
    }
    row.update(kwargs)
    return row


# ---------------------------------------------------------------------------
# The M3 census reader
# ---------------------------------------------------------------------------


class TestReadM3Census:
    def test_keeps_only_censored_rows_of_requested_arms(self, tmp_path: Path) -> None:
        _write_m3(
            tmp_path / "RQ1_addressing" / "merged" / "rows_m3__tag-000.csv",
            [
                _m3_row("a", "wstar_orbit", 1),
                _m3_row("b", "wstar_orbit", 0),
                _m3_row("c", "wstar_rank", 1),
                _m3_row("d", "nauty_cert", 1),
            ],
        )
        members = read_m3_census(tmp_path, ("wstar_orbit", "wstar_rank"))
        assert [(m.member_id, m.arm) for m in members] == [
            ("a", "wstar_orbit"),
            ("c", "wstar_rank"),
        ]

    def test_carries_the_baseline_fields(self, tmp_path: Path) -> None:
        _write_m3(
            tmp_path / "RQ1_addressing" / "merged" / "rows_m3__tag-000.csv",
            [_m3_row("a", "wstar_orbit", 1, n=9, m=14, k=7, aut_bucket="1e3-1e6", secs=60.0)],
        )
        (member,) = read_m3_census(tmp_path, ("wstar_orbit",))
        assert (member.n, member.m, member.k) == (9, 14, 7)
        assert member.aut_bucket == "1e3-1e6"
        assert member.baseline_secs == pytest.approx(60.0)

    def test_deduplicates_across_shard_files(self, tmp_path: Path) -> None:
        base = tmp_path / "RQ1_addressing" / "merged"
        _write_m3(base / "rows_m3__tag-000.csv", [_m3_row("a", "wstar_orbit", 1)])
        _write_m3(base / "rows_m3__tag-001.csv", [_m3_row("a", "wstar_orbit", 1)])
        assert len(read_m3_census(tmp_path, ("wstar_orbit",))) == 1

    def test_no_census_raises(self, tmp_path: Path) -> None:
        with pytest.raises(Tail600SourceError, match="no RQ1 M3 census"):
            read_m3_census(tmp_path, ("wstar_orbit",))

    def test_census_without_the_defining_columns_raises(self, tmp_path: Path) -> None:
        _write_m3(
            tmp_path / "RQ1_addressing" / "merged" / "rows_m3__tag-000.csv",
            [{"collection": "ndc_classes", "member_id": "a"}],
            columns=("collection", "member_id"),
        )
        with pytest.raises(Tail600SourceError, match="missing columns"):
            read_m3_census(tmp_path, ("wstar_orbit",))

    def test_an_arm_absent_from_the_census_yields_nothing(self, tmp_path: Path) -> None:
        _write_m3(
            tmp_path / "RQ1_addressing" / "merged" / "rows_m3__tag-000.csv",
            [_m3_row("a", "wstar_orbit", 1)],
        )
        members = read_m3_census(tmp_path, ("wstar_orbit", "wstar_rank"))
        assert {m.arm for m in members} == {"wstar_orbit"}


# ---------------------------------------------------------------------------
# The sidecar reader
# ---------------------------------------------------------------------------


def _write_sidecar(root: Path, collection: str, arm: str, payload: Any) -> Path:
    directory = root / "matrices" / collection
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{arm}.censored.json"
    path.write_text(payload if isinstance(payload, str) else json.dumps(payload), encoding="utf-8")
    return path


class TestReadSidecarCensus:
    def test_reads_the_censored_ids(self, tmp_path: Path) -> None:
        _write_sidecar(
            tmp_path,
            "ndc_classes",
            "wstar_orbit",
            {"arm": "wstar_orbit", "n_requested": 3, "censored_ids": ["x", "y"]},
        )
        members, present = read_sidecar_census(tmp_path, ("wstar_orbit",))
        assert [m.member_id for m in members] == ["x", "y"]
        assert present == {"wstar_orbit": ["ndc_classes"]}

    def test_a_missing_sidecar_is_data_not_an_error(self, tmp_path: Path) -> None:
        _write_sidecar(tmp_path, "ndc_classes", "wstar_orbit", {"censored_ids": ["x"]})
        members, present = read_sidecar_census(tmp_path, ("wstar_orbit", "wstar_rank"))
        assert [m.arm for m in members] == ["wstar_orbit"]
        assert present["wstar_rank"] == []

    def test_no_matrices_directory_at_all(self, tmp_path: Path) -> None:
        members, present = read_sidecar_census(tmp_path, ("wstar_orbit",))
        assert members == []
        assert present == {"wstar_orbit": []}

    @pytest.mark.parametrize(
        "payload",
        [
            pytest.param("{not json", id="not-json"),
            pytest.param([1, 2, 3], id="not-a-mapping"),
            pytest.param({"arm": "wstar_orbit"}, id="no-censored-ids"),
            pytest.param({"censored_ids": "x"}, id="censored-ids-not-a-list"),
            pytest.param({"censored_ids": ["x", 7]}, id="censored-ids-not-strings"),
        ],
    )
    def test_a_malformed_sidecar_raises(self, tmp_path: Path, payload: Any) -> None:
        _write_sidecar(tmp_path, "ndc_classes", "wstar_orbit", payload)
        with pytest.raises(Tail600SourceError):
            read_sidecar_census(tmp_path, ("wstar_orbit",))

    def test_build_and_smoke_components_are_skipped(self, tmp_path: Path) -> None:
        _write_sidecar(tmp_path, "_smoke", "wstar_orbit", {"censored_ids": ["ghost"]})
        _write_sidecar(tmp_path, "ndc_classes", "wstar_orbit", {"censored_ids": ["real"]})
        members, _ = read_sidecar_census(tmp_path, ("wstar_orbit",))
        assert [m.member_id for m in members] == ["real"]


# ---------------------------------------------------------------------------
# Work list and sharding
# ---------------------------------------------------------------------------


class TestWorklist:
    def test_is_collection_then_arm_then_member_major(self) -> None:
        unsorted = [
            TailMember("wd50k66", "b", "wstar_orbit"),
            TailMember("ndc_classes", "z", "wstar_rank"),
            TailMember("ndc_classes", "a", "wstar_orbit"),
            TailMember("ndc_classes", "a", "wstar_rank"),
        ]
        assert [m.key for m in worklist(unsorted)] == [
            ("ndc_classes", "a", "wstar_orbit"),
            ("ndc_classes", "a", "wstar_rank"),
            ("ndc_classes", "z", "wstar_rank"),
            ("wd50k66", "b", "wstar_orbit"),
        ]


class TestShardSlice:
    @pytest.mark.parametrize("n_items", [0, 1, 5, 13, 130])
    @pytest.mark.parametrize("n_shards", [1, 2, 3, 16])
    def test_shards_partition_the_work(self, n_items: int, n_shards: int) -> None:
        items = list(range(n_items))
        shards = [shard_slice(items, i, n_shards) for i in range(n_shards)]
        assert sorted(x for shard in shards for x in shard) == items

    @pytest.mark.parametrize("n_items,n_shards", [(130, 16), (77, 16), (5, 3)])
    def test_shards_are_balanced_within_one(self, n_items: int, n_shards: int) -> None:
        sizes = [len(shard_slice(list(range(n_items)), i, n_shards)) for i in range(n_shards)]
        assert max(sizes) - min(sizes) <= 1

    def test_the_campaign_worst_case_shard_is_nine_calls(self) -> None:
        """130 calls over 16 shards: the launcher's arithmetic, pinned."""
        sizes = [len(shard_slice(list(range(130)), i, 16)) for i in range(16)]
        assert max(sizes) == 9

    @pytest.mark.parametrize("shard,n_shards", [(-1, 4), (4, 4), (0, 0)])
    def test_out_of_range_raises(self, shard: int, n_shards: int) -> None:
        with pytest.raises(Tail600Error):
            shard_slice([1, 2, 3], shard, n_shards)


class TestParseShard:
    def test_default_is_the_single_shard(self) -> None:
        assert parse_shard(None, 10) == (0, 1)

    @pytest.mark.parametrize("spec", ["3/16", "0/1"])
    def test_valid_specs(self, spec: str) -> None:
        index, total = parse_shard(spec, 130)
        assert (index, total) == tuple(int(p) for p in spec.split("/"))

    @pytest.mark.parametrize("spec", ["nonsense", "1", "4/4", "-1/4", "0/0"])
    def test_invalid_specs_raise(self, spec: str) -> None:
        with pytest.raises(Tail600Error):
            parse_shard(spec, 130)


# ---------------------------------------------------------------------------
# collect_work
# ---------------------------------------------------------------------------


class TestCollectWork:
    def test_reports_which_arms_are_measurable(self, tmp_path: Path) -> None:
        _write_m3(
            tmp_path / "RQ1_addressing" / "merged" / "rows_m3__tag-000.csv",
            [_m3_row("a", "wstar_orbit", 1)],
        )
        members, report = tail600.collect_work(
            {"source": "m3", "arms": ["wstar_orbit", "wstar_rank"]}, tmp_path
        )
        assert len(members) == 1
        assert report["arms_measurable"] == ["wstar_orbit"]
        assert report["arms_unmeasurable"] == ["wstar_rank"]

    def test_max_items_truncates(self, tmp_path: Path) -> None:
        _write_m3(
            tmp_path / "RQ1_addressing" / "merged" / "rows_m3__tag-000.csv",
            [_m3_row(f"m{i}", "wstar_orbit", 1) for i in range(9)],
        )
        members, report = tail600.collect_work(
            {"source": "m3", "arms": ["wstar_orbit"], "max_items": 4}, tmp_path
        )
        assert len(members) == 4 and report["n_members"] == 4

    def test_unknown_source_raises(self, tmp_path: Path) -> None:
        with pytest.raises(Tail600Error, match="unknown source"):
            tail600.collect_work({"source": "guesswork"}, tmp_path)


class TestRunTag:
    def test_operational_keys_do_not_change_the_tag(self) -> None:
        base = {"budget_s": 600.0, "arms": ["wstar_orbit"]}
        assert tail600.run_tag(base) == tail600.run_tag({**base, "n_shards": 32, "smoke": {}})

    def test_the_budget_does_change_the_tag(self) -> None:
        base = {"budget_s": 600.0, "arms": ["wstar_orbit"]}
        assert tail600.run_tag(base) != tail600.run_tag({**base, "budget_s": 60.0})


class TestOutputLocation:
    def test_rows_land_outside_every_rq_tree(self, tmp_path: Path) -> None:
        """D-ART5 decision 2: never a row. The folder name is the guarantee."""
        paths = tail600.resolve_paths(tmp_path, smoke=False)
        assert not tail600.RQ_FOLDER.startswith("RQ")
        assert paths.dir == tmp_path / tail600.RQ_FOLDER / tail600.EXPERIMENT

    def test_the_smoke_gets_its_own_subtree(self, tmp_path: Path) -> None:
        real = tail600.resolve_paths(tmp_path, smoke=False).dir
        smoke = tail600.resolve_paths(tmp_path, smoke=True).dir
        assert smoke != real and smoke.is_relative_to(tmp_path / tail600.RQ_FOLDER)

    def test_the_row_file_name_is_not_an_rq_table(self) -> None:
        name = tail600.table_file("deadbeef", 3, 16)
        assert name.startswith("tail600__") and "m3" not in name


# ---------------------------------------------------------------------------
# The verdict logic -- inputs whose answer is known by construction
# ---------------------------------------------------------------------------


def _rows(arm: str, completed: int, censored: int) -> list[dict[str, Any]]:
    return [
        {"arm": arm, "censored": "0", "collection": "c", "member_id": f"ok{i}"}
        for i in range(completed)
    ] + [
        {"arm": arm, "censored": "1", "collection": "c", "member_id": f"no{i}"}
        for i in range(censored)
    ]


class TestTally:
    def test_counts_completed_and_censored(self) -> None:
        result = tally(_rows("wstar_orbit", 30, 47), "wstar_orbit")
        assert (result.total, result.completed, result.censored) == (77, 30, 47)
        assert result.completion_fraction == pytest.approx(30 / 77)

    def test_ignores_other_arms(self) -> None:
        rows = _rows("wstar_orbit", 1, 1) + _rows("wstar_rank", 5, 0)
        assert tally(rows, "wstar_rank").total == 5

    def test_an_empty_tally_has_a_zero_fraction(self) -> None:
        assert ArmTally("x", 0, 0, 0).completion_fraction == 0.0


class TestVerdictMaterial:
    @pytest.mark.parametrize(
        "completed,expected",
        [
            pytest.param(0, REFUTED, id="none-complete"),
            pytest.param(19, REFUTED, id="just-under-25pc"),
            pytest.param(20, CONFIRMED, id="exactly-25pc"),
            pytest.param(77, CONFIRMED, id="all-complete"),
        ],
    )
    def test_the_threshold_is_the_pre_registered_one(self, completed: int, expected: str) -> None:
        """77 members: 19/77 = 24.7 % is under 0.25, 20/77 = 26.0 % is over."""
        result = verdict_material(
            tally(_rows("wstar_orbit", completed, 77 - completed), "wstar_orbit")
        )
        assert result.outcome == expected
        assert str(completed) in result.detail

    def test_no_rows_is_indeterminate_not_refuted(self) -> None:
        assert verdict_material(ArmTally("wstar_orbit", 0, 0, 0)).outcome == INDETERMINATE

    def test_the_pre_registered_threshold_has_not_drifted(self) -> None:
        assert MATERIAL_FRACTION == 0.25


class TestVerdictMostCensored:
    @pytest.mark.parametrize(
        "completed,expected",
        [
            pytest.param(0, CONFIRMED, id="none-complete"),
            pytest.param(26, CONFIRMED, id="just-under-half"),
            pytest.param(27, REFUTED, id="just-over-half"),
            pytest.param(53, REFUTED, id="all-complete"),
        ],
    )
    def test_most_means_more_than_half(self, completed: int, expected: str) -> None:
        """53 members: 26/53 = 49.1 % is under 0.50, 27/53 = 50.9 % is over."""
        result = verdict_most_censored(
            tally(_rows("wstar_rank", completed, 53 - completed), "wstar_rank")
        )
        assert result.outcome == expected

    def test_no_rows_is_indeterminate(self) -> None:
        assert verdict_most_censored(ArmTally("wstar_rank", 0, 0, 0)).outcome == INDETERMINATE

    def test_the_pre_registered_threshold_has_not_drifted(self) -> None:
        assert MOST_FRACTION == 0.50


class TestVerdictMechanism:
    def test_a_mostly_censored_tail_confirms_displacement(self) -> None:
        result = verdict_mechanism(tally(_rows("wstar_rank", 3, 50), "wstar_rank"))
        assert result.outcome == CONFIRMED
        assert "D-ART5 stands" in result.detail

    def test_a_mostly_completed_tail_refutes_it_and_says_what_must_change(self) -> None:
        result = verdict_mechanism(tally(_rows("wstar_rank", 40, 13), "wstar_rank"))
        assert result.outcome == REFUTED
        assert "needs rewriting" in result.detail
        assert "artefact of the 60 s budget" in result.detail

    def test_no_rows_is_indeterminate(self) -> None:
        assert verdict_mechanism(ArmTally("wstar_rank", 0, 0, 0)).outcome == INDETERMINATE


class TestScore:
    def test_scores_all_three_clauses(self) -> None:
        rows = _rows("wstar_orbit", 40, 37) + _rows("wstar_rank", 2, 51)
        tallies, verdicts = score(rows)
        assert [t.arm for t in tallies] == ["wstar_orbit", "wstar_rank"]
        assert [v.outcome for v in verdicts] == [CONFIRMED, CONFIRMED, CONFIRMED]

    def test_an_arm_with_no_rows_is_indeterminate_across_its_clauses(self) -> None:
        _, verdicts = score(_rows("wstar_orbit", 40, 37))
        assert [v.outcome for v in verdicts] == [CONFIRMED, INDETERMINATE, INDETERMINATE]

    def test_the_refutation_case_end_to_end(self) -> None:
        """If most of the 53 complete, the mechanism clause must say so."""
        rows = _rows("wstar_orbit", 70, 7) + _rows("wstar_rank", 45, 8)
        _, verdicts = score(rows)
        assert [v.outcome for v in verdicts] == [CONFIRMED, REFUTED, REFUTED]

    def test_the_report_names_every_outcome(self) -> None:
        tallies, verdicts = score(_rows("wstar_orbit", 1, 76) + _rows("wstar_rank", 0, 53))
        report = render(tallies, verdicts, [600.0])
        assert "REFUTED" in report and "CONFIRMED" in report
        assert "never a published row" in report


class TestReportBudget:
    """The heading must name the budget the rows were taken at, not a constant."""

    def test_the_heading_carries_the_measured_budget(self) -> None:
        tallies, verdicts = score(_rows("wstar_orbit", 1, 1))
        assert "# 600 s tail" in render(tallies, verdicts, [600.0])
        assert "# 5 s tail" in render(tallies, verdicts, [5.0])

    def test_mixed_budgets_are_named_as_mixed(self) -> None:
        tallies, verdicts = score(_rows("wstar_orbit", 1, 1))
        assert "# 5/600 s tail" in render(tallies, verdicts, [5.0, 600.0])

    def test_budgets_are_read_from_the_rows(self) -> None:
        rows = [
            {"arm": "wstar_orbit", "censored": "1", "budget_s": "600.0"},
            {"arm": "wstar_rank", "censored": "0", "budget_s": "600.0"},
            {"arm": "wstar_rank", "censored": "0", "budget_s": ""},
        ]
        assert budgets(rows) == [600.0]

    def test_no_budget_column_yields_a_question_mark(self) -> None:
        tallies, verdicts = score(_rows("wstar_orbit", 1, 1))
        assert "# ? s tail" in render(tallies, verdicts, [])


# ---------------------------------------------------------------------------
# read_rows -- the guard that keeps foreign rows out of the score
# ---------------------------------------------------------------------------


def _write_tail_rows(root: Path, rows: list[dict[str, Any]], *, smoke: bool = False) -> Path:
    component = f"{tail600.RQ_FOLDER}/_smoke" if smoke else tail600.RQ_FOLDER
    directory = root / component / tail600.EXPERIMENT
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "rows_tail600__tag-000of001.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(tail600.COLUMNS_TAIL), restval="")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return path


def _tail_row(member_id: str, arm: str, censored: int, kind: str = tail600.KIND) -> dict[str, Any]:
    return {
        "kind": kind,
        "source": "m3",
        "collection": "ndc_classes",
        "member_id": member_id,
        "arm": arm,
        "censored": censored,
        "secs": 600.0 if censored else 123.4,
        "budget_s": 600.0,
    }


class TestReadRows:
    def test_reads_and_deduplicates(self, tmp_path: Path) -> None:
        _write_tail_rows(
            tmp_path,
            [_tail_row("a", "wstar_orbit", 0), _tail_row("a", "wstar_orbit", 0)],
        )
        assert len(read_rows(tmp_path)) == 1

    def test_no_rows_raises(self, tmp_path: Path) -> None:
        with pytest.raises(Tail600AnalysisError, match="no tail rows"):
            read_rows(tmp_path)

    def test_a_row_that_is_not_tail_characterisation_raises(self, tmp_path: Path) -> None:
        _write_tail_rows(tmp_path, [_tail_row("a", "wstar_orbit", 0, kind="published")])
        with pytest.raises(Tail600AnalysisError, match="only 'tail_characterisation'"):
            read_rows(tmp_path)

    def test_the_smoke_subtree_is_read_only_on_request(self, tmp_path: Path) -> None:
        _write_tail_rows(tmp_path, [_tail_row("a", "wstar_orbit", 0)], smoke=True)
        with pytest.raises(Tail600AnalysisError):
            read_rows(tmp_path, smoke=False)
        assert len(read_rows(tmp_path, smoke=True)) == 1


# ---------------------------------------------------------------------------
# measure_member -- the arm guard
# ---------------------------------------------------------------------------


class TestMeasureMember:
    def test_a_non_budgeted_arm_is_refused(self) -> None:
        member = TailMember("ndc_classes", "a", "nauty_cert", k=3)
        with pytest.raises(Tail600Error, match="not a budgeted engine arm"):
            measure = tail600.measure_member
            measure(member, object(), 1.0)
