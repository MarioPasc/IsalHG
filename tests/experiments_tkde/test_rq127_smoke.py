"""Unit tests for the RQ1 / RQ2 / RQ7 runners, their budget helper and analyzers.

The expensive parts (a real corpus, a real pointer canonicalization) are marked
``slow`` and skipped when the frozen corpora are not on this machine; everything
that can be tested without them -- the budget's kill semantics, unit
enumeration, shard parsing, the block split, the M0 reduction, the census
counting and the analyzers' behaviour on empty and partial input -- runs
unconditionally.

The two things worth testing hardest are the ones that fail silently in
production: a budget that returns a plausible number instead of censoring, and
an aggregate reduction that counts pairs wrongly.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

from experiments.tkde import rq1, rq2, rq7  # noqa: E402
from experiments.tkde.budget import (  # noqa: E402
    TkdeBudgetError,
    encode_symbols,
    run_with_budget,
    run_with_budget_detail,
    symbol_distance,
)

CORPORA_ROOT = Path(
    os.environ.get(
        "ISALHG_RESULTS_ROOT",
        "/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE",
    )
)
HAVE_CORPORA = (CORPORA_ROOT / "corpora" / "ndc_classes" / "records.jsonl").is_file()
needs_corpora = pytest.mark.skipif(
    not HAVE_CORPORA, reason=f"frozen corpora absent under {CORPORA_ROOT}"
)


# ---------------------------------------------------------------------------
# budget.py
# ---------------------------------------------------------------------------


def _sleep_then(seconds: float, value: int) -> int:
    time.sleep(seconds)
    return value


def _boom() -> None:
    raise ValueError("deliberate")


class TestBudget:
    """The process-level budget: the only bound that holds for the C++ arms."""

    def test_returns_the_value_and_a_plausible_time(self) -> None:
        value, secs, censored = run_with_budget(_sleep_then, (0.05, 42), 5.0)
        assert value == 42
        assert not censored
        assert 0.04 <= secs < 5.0

    def test_censors_an_overrun_rather_than_waiting(self) -> None:
        started = time.monotonic()
        value, secs, censored = run_with_budget(_sleep_then, (10.0, 1), 0.4)
        elapsed = time.monotonic() - started
        assert value is None
        assert censored
        assert secs == pytest.approx(0.4)
        # The whole point: the parent returns at the budget, not at the child's
        # own duration. A budget that merely *reported* a time-out while
        # blocking for 10 s would pass a naive assertion on `censored` alone.
        assert elapsed < 5.0

    def test_an_exception_is_data_not_a_crash(self) -> None:
        result = run_with_budget_detail(_boom, (), 5.0)
        assert result.value is None
        assert not result.censored
        assert result.error is not None
        assert "ValueError" in result.error
        assert not result.ok

    @pytest.mark.parametrize("seconds", [0.0, -1.0])
    def test_a_non_positive_budget_is_refused(self, seconds: float) -> None:
        with pytest.raises(TkdeBudgetError):
            run_with_budget(_sleep_then, (0.0, 1), seconds)


class TestSymbolDistance:
    """Levenshtein over arbitrary symbols, via a per-call private alphabet."""

    def test_identical_sequences_are_at_zero(self) -> None:
        word = (("T", 0), ("F", 1, (0, 1)))
        assert symbol_distance(word, word) == 0

    def test_one_insertion_costs_one(self) -> None:
        a = (("T", 0), ("F", 1, (0, 1)))
        b = (("T", 0), ("T", 0), ("F", 1, (0, 1)))
        assert symbol_distance(a, b) == 1

    def test_the_alphabet_is_shared_across_the_sequences(self) -> None:
        # Encoding each sequence against its own alphabet would map two
        # different symbols to the same character and report distance 0.
        left, right = encode_symbols([("a", "b"), ("c", "d")])
        assert set(left).isdisjoint(set(right))
        assert symbol_distance(("a", "b"), ("c", "d")) == 2


# ---------------------------------------------------------------------------
# Unit enumeration and sharding
# ---------------------------------------------------------------------------


class TestBlockSlice:
    """The even split: never fixed blocks with a ragged tail."""

    def test_blocks_partition_the_range_exactly(self) -> None:
        covered: list[int] = []
        for block in range(7):
            covered.extend(rq1.block_slice(23, block, 7))
        assert covered == list(range(23))

    def test_block_sizes_differ_by_at_most_one(self) -> None:
        sizes = [len(rq1.block_slice(23, block, 7)) for block in range(7)]
        assert max(sizes) - min(sizes) <= 1

    def test_a_single_block_is_the_whole_range(self) -> None:
        assert list(rq1.block_slice(5, 0, 1)) == [0, 1, 2, 3, 4]


class TestShardParsing:
    def test_the_default_is_one_shard(self) -> None:
        assert rq1.parse_shard(None, 10) == (0, 1)

    def test_a_spec_is_parsed(self) -> None:
        assert rq1.parse_shard("3/8", 10) == (3, 8)

    @pytest.mark.parametrize("spec", ["8/8", "-1/4", "nonsense", "3"])
    def test_a_bad_spec_is_refused(self, spec: str) -> None:
        with pytest.raises(rq1.Rq1Error):
            rq1.parse_shard(spec, 10)


class TestUnitEnumeration:
    """Units must be deterministic and must cover every shard exactly once."""

    def test_rq1_units_are_deterministic_and_uniquely_named(self) -> None:
        config = rq1.load_yaml(_config("rq1.yaml"))
        first = rq1.enumerate_units(config)
        second = rq1.enumerate_units(config)
        assert [u.unit_id for u in first] == [u.unit_id for u in second]
        assert len({u.unit_id for u in first}) == len(first)

    def test_rq7_units_cover_the_sweep_yield_and_nscaling_kinds(self) -> None:
        units = rq7.enumerate_units(rq7.load_yaml(_config("rq7.yaml")))
        kinds = {unit.kind for unit in units}
        assert kinds == {"sweep", "yield", "nscaling"}
        assert len({u.unit_id for u in units}) == len(units)

    def test_rq2_kinds_filter_selects_only_the_census(self) -> None:
        config = rq2.load_yaml(_config("rq2.yaml"))
        every = rq2.enumerate_units(config)
        census = rq2.enumerate_units(config, ["census"])
        assert census and len(census) < len(every)
        assert {unit.kind for unit in census} == {"census"}

    def test_rq2_unit_ids_carry_no_shell_metacharacters(self) -> None:
        # The stratum labels of the design are "<=6", "7-8", "9-10"; a "<" in a
        # results file name is a shell hazard for every later reader.
        units = rq2.enumerate_units(rq2.load_yaml(_config("rq2.yaml")), ["oracle"])
        assert units
        for unit in units:
            assert not set(unit.unit_id) & set("<>|&;$ ")

    def test_shards_partition_the_units(self) -> None:
        units = rq1.enumerate_units(rq1.load_yaml(_config("rq1.yaml")))
        n_shards = 7
        seen = [unit.unit_id for shard in range(n_shards) for unit in units[shard::n_shards]]
        assert sorted(seen) == sorted(unit.unit_id for unit in units)


def _config(name: str) -> Path:
    return Path(__file__).resolve().parents[2] / "experiments" / "tkde" / "configs" / name


class TestRunTag:
    """The run tag is what stops a smoke run from being mistaken for a campaign."""

    def test_the_same_configuration_gives_the_same_tag(self) -> None:
        config = rq1.load_yaml(_config("rq1.yaml"))
        assert rq1.run_tag(config) == rq1.run_tag(dict(config))

    def test_a_smoke_configuration_gives_a_different_tag(self) -> None:
        config = rq1.load_yaml(_config("rq1.yaml"))
        assert rq1.run_tag(config) != rq1.run_tag(rq1.smoke_config(dict(config)))

    def test_changing_a_measured_parameter_changes_the_tag(self) -> None:
        config = rq1.load_yaml(_config("rq1.yaml"))
        other = dict(config)
        other["m1_edits_per_kind"] = 8
        assert rq1.run_tag(config) != rq1.run_tag(other)

    def test_resharding_does_not_change_the_tag(self) -> None:
        # Otherwise re-sharding a running campaign would recompute all of it
        # instead of resuming it.
        config = rq1.load_yaml(_config("rq1.yaml"))
        other = dict(config)
        other["n_shards"] = int(config["n_shards"]) * 2
        assert rq1.run_tag(config) == rq1.run_tag(other)

    def test_the_tag_is_eight_hex_characters(self) -> None:
        import re

        tag = rq1.run_tag(rq1.load_yaml(_config("rq7.yaml")))
        assert re.fullmatch(r"[0-9a-f]{8}", tag)


class TestUntaggedRowsAreIgnored:
    """Row files without a run tag are not campaign output and must not be read."""

    def test_an_untagged_file_is_skipped(self, tmp_path: Path) -> None:
        from experiments.tkde.analyze_rq1 import load_table

        directory = tmp_path / "RQ1_addressing" / "addressing"
        directory.mkdir(parents=True)
        header = "rq,experiment,collection,arm,d_abs\n"
        (directory / "rows_m1__m1-synthetic_rq1-000of001.csv").write_text(
            header + "1,addressing,synthetic_rq1,fact_rank,9\n", encoding="utf-8"
        )
        (directory / "rows_m1__deadbeef-m1-synthetic_rq1-000of001.csv").write_text(
            header + "1,addressing,synthetic_rq1,fact_rank,1\n", encoding="utf-8"
        )
        frame = load_table(tmp_path, "RQ1_addressing", "m1")
        assert len(frame) == 1
        assert int(frame.iloc[0]["d_abs"]) == 1

    def test_a_smoke_subtree_is_skipped(self, tmp_path: Path) -> None:
        from experiments.tkde.analyze_rq1 import load_table

        directory = tmp_path / "RQ7_envelope" / "_smoke" / "envelope"
        directory.mkdir(parents=True)
        (directory / "rows_sweep__deadbeef-sweep-x-000of001.csv").write_text(
            "rq,arm,secs\n7,fact_rank,0.1\n", encoding="utf-8"
        )
        assert load_table(tmp_path, "RQ7_envelope", "sweep").empty


# ---------------------------------------------------------------------------
# Aggregate reductions
# ---------------------------------------------------------------------------


class TestM0Reduction:
    """``rows_m0`` is computed here, so its pair arithmetic is tested here."""

    def test_a_merge_and_a_split_are_counted_separately(self) -> None:
        import pandas as pd

        from experiments.tkde.analyze_rq1 import reduce_m0

        # Members 1 and 2 share a word but not a nauty class -> one false merge.
        # Members 3 and 4 share a nauty class but not a word -> one false split.
        items = pd.DataFrame(
            [
                {
                    "collection": "c",
                    "arm": "a",
                    "word_hash": "w1",
                    "nauty_hash": "n1",
                    "invariance_ok": 1,
                    "censored": 0,
                },
                {
                    "collection": "c",
                    "arm": "a",
                    "word_hash": "w1",
                    "nauty_hash": "n2",
                    "invariance_ok": 1,
                    "censored": 0,
                },
                {
                    "collection": "c",
                    "arm": "a",
                    "word_hash": "w3",
                    "nauty_hash": "n3",
                    "invariance_ok": 1,
                    "censored": 0,
                },
                {
                    "collection": "c",
                    "arm": "a",
                    "word_hash": "w4",
                    "nauty_hash": "n3",
                    "invariance_ok": 0,
                    "censored": 0,
                },
            ]
        )
        row = reduce_m0(items).iloc[0]
        assert row["false_merges"] == 1
        assert row["false_splits"] == 1
        assert row["invariance_violations"] == 1
        assert row["n_classes_arm"] == 3
        assert row["n_classes_nauty"] == 3

    def test_a_complete_invariant_scores_zero_on_both(self) -> None:
        import pandas as pd

        from experiments.tkde.analyze_rq1 import reduce_m0

        items = pd.DataFrame(
            [
                {
                    "collection": "c",
                    "arm": "a",
                    "word_hash": f"w{i}",
                    "nauty_hash": f"n{i}",
                    "invariance_ok": 1,
                    "censored": 0,
                }
                for i in range(5)
            ]
        )
        row = reduce_m0(items).iloc[0]
        assert row["false_merges"] == 0
        assert row["false_splits"] == 0

    def test_censored_members_are_excluded_from_the_pair_counts(self) -> None:
        import pandas as pd

        from experiments.tkde.analyze_rq1 import reduce_m0

        items = pd.DataFrame(
            [
                {
                    "collection": "c",
                    "arm": "a",
                    "word_hash": "w1",
                    "nauty_hash": "n1",
                    "invariance_ok": 1,
                    "censored": 0,
                },
                {
                    "collection": "c",
                    "arm": "a",
                    "word_hash": "",
                    "nauty_hash": "n2",
                    "invariance_ok": "",
                    "censored": 1,
                },
            ]
        )
        row = reduce_m0(items).iloc[0]
        assert row["n_members"] == 2
        assert row["n_usable"] == 1
        assert row["n_censored"] == 1


class TestCensusCounts:
    """A false merge is a zero-distance pair that is genuinely non-isomorphic."""

    def test_a_complete_arm_merges_nothing(self) -> None:
        import numpy as np

        matrix = np.array([[0.0, 3.0, 5.0], [3.0, 0.0, 4.0], [5.0, 4.0, 0.0]])
        counts = rq2.census_counts(matrix, ["a", "b", "c"])
        assert counts["n_false_merges"] == 0
        assert counts["n_classes_arm"] == 3
        assert counts["n_classes_true"] == 3
        assert counts["n_pairs"] == 3
        assert counts["n_noniso_pairs"] == 3

    def test_a_zero_between_two_classes_is_a_false_merge(self) -> None:
        import numpy as np

        matrix = np.array([[0.0, 0.0, 5.0], [0.0, 0.0, 4.0], [5.0, 4.0, 0.0]])
        counts = rq2.census_counts(matrix, ["a", "b", "c"])
        assert counts["n_false_merges"] == 1
        assert counts["n_classes_arm"] == 2

    def test_a_zero_within_one_class_is_not_a_false_merge(self) -> None:
        import numpy as np

        matrix = np.array([[0.0, 0.0, 5.0], [0.0, 0.0, 4.0], [5.0, 4.0, 0.0]])
        counts = rq2.census_counts(matrix, ["a", "a", "c"])
        assert counts["n_false_merges"] == 0
        assert counts["n_noniso_pairs"] == 2

    def test_the_tolerance_is_load_bearing_for_real_valued_arms(self) -> None:
        import numpy as np

        # NetLSD lands isomorphic pairs at ~1e-14, never at exactly 0; an
        # equality test would report no merges at all.
        matrix = np.array([[0.0, 1e-14, 5.0], [1e-14, 0.0, 4.0], [5.0, 4.0, 0.0]])
        counts = rq2.census_counts(matrix, ["a", "b", "c"])
        assert counts["n_false_merges"] == 1


class TestZeroPredicate:
    @pytest.mark.parametrize("value", [0.0, 1e-15, -1e-15])
    def test_below_tolerance_counts_as_zero(self, value: float) -> None:
        assert rq2.is_zero(value)

    @pytest.mark.parametrize("value", [1e-8, 1.0, None])
    def test_above_tolerance_or_missing_does_not(self, value: float | None) -> None:
        assert not rq2.is_zero(value)


class TestBuckets:
    @pytest.mark.parametrize(
        ("n", "expected"),
        [
            (1, "<=8"),
            (8, "<=8"),
            (9, "9-12"),
            (16, "13-16"),
            (20, "17-20"),
            (24, "21-24"),
            (25, ">24"),
            (99, ">24"),
        ],
    )
    def test_bucket_boundaries(self, n: int, expected: str) -> None:
        assert rq7.bucket_of(n) == expected


# ---------------------------------------------------------------------------
# Analyzers on empty and partial input
# ---------------------------------------------------------------------------


class TestAnalyzersOnEmptyTrees:
    """An analyzer runs while the campaign is still going, so nothing may raise."""

    def test_rq1(self, tmp_path: Path) -> None:
        from experiments.tkde.analyze_rq1 import analyze

        summary = analyze(tmp_path)
        assert summary["row_counts"]["m1"] == 0
        assert (tmp_path / "RQ1_addressing" / "addressing" / "summary.json").is_file()

    def test_rq2_reports_the_certificate_section_pending(self, tmp_path: Path) -> None:
        from experiments.tkde.analyze_rq2 import analyze

        summary = analyze(tmp_path)
        # Pending, never empty: a reader must not mistake "not measured yet"
        # for "measured and null".
        assert summary["certificate"]["status"] == "pending"
        assert (tmp_path / "RQ2_wellposedness" / "wellposedness" / "tables.md").is_file()

    def test_rq7(self, tmp_path: Path) -> None:
        from experiments.tkde.analyze_rq7 import analyze

        summary = analyze(tmp_path)
        assert summary["row_counts"]["sweep"] == 0
        assert (tmp_path / "RQ7_envelope" / "envelope" / "stats.json").is_file()

    def test_rq2_reads_the_merged_certificate_file_only(self, tmp_path: Path) -> None:
        from experiments.tkde.analyze_rq2 import analyze

        directory = tmp_path / "RQ2_wellposedness" / "certificate_validity"
        (directory / "parts").mkdir(parents=True)
        header = (
            "rq,experiment,collection,seed,arm,git_sha,host_cpu,secs,censored,"
            "unit,collection_id,N,LB,medoid_cost,invalid\n"
        )
        row = "2,cert,c,0,fact_rank,sha,cpu,0.1,0,u,c1,5,1.0,2.0,0\n"
        (directory / "rows_certificate.csv").write_text(header + row, encoding="utf-8")
        # A per-shard part carrying the same row: globbing it too would double
        # the denominator of every certificate rate.
        (directory / "parts" / "rows_certificate__000.csv").write_text(
            header + row, encoding="utf-8"
        )
        summary = analyze(tmp_path)
        assert summary["certificate"]["status"] == "read"
        assert summary["certificate"]["rows"][0]["n_collections"] == 1


# ---------------------------------------------------------------------------
# End to end on the frozen corpora (slow)
# ---------------------------------------------------------------------------


@needs_corpora
@pytest.mark.slow
class TestSmokeEndToEnd:
    """The ``--smoke`` path of each runner, then its analyzer, on real corpora."""

    @pytest.mark.parametrize("module", [rq1, rq2, rq7])
    def test_runner_then_analyzer(self, module, tmp_path: Path) -> None:
        import importlib

        name = module.__name__.rsplit(".", 1)[-1]
        config = _config(f"{name}.yaml")
        exit_code = module.main(
            [
                "--config",
                str(config),
                "--out",
                str(tmp_path),
                "--data-root",
                str(CORPORA_ROOT),
                "--smoke",
            ]
        )
        assert exit_code == 0
        rows = list((tmp_path / module.RQ_FOLDER).rglob("rows_*.csv"))
        assert rows, f"{name} wrote no rows"

        analyzer = importlib.import_module(f"experiments.tkde.analyze_{name}")
        assert analyzer.main(["--root", str(tmp_path)]) == 0
        directory = tmp_path / module.RQ_FOLDER / module.EXPERIMENT
        for artefact in ("summary.json", "stats.json", "tables.md"):
            assert (directory / artefact).is_file(), f"{name} produced no {artefact}"

    def test_a_rerun_skips_the_units_already_written(self, tmp_path: Path) -> None:
        config = _config("rq7.yaml")
        args = [
            "--config",
            str(config),
            "--out",
            str(tmp_path),
            "--data-root",
            str(CORPORA_ROOT),
            "--smoke",
        ]
        assert rq7.main(args) == 0
        stamps = {
            path: path.stat().st_mtime_ns
            for path in (tmp_path / "RQ7_envelope").rglob("rows_*.csv")
        }
        assert stamps
        time.sleep(0.01)
        assert rq7.main(args) == 0
        for path, stamp in stamps.items():
            assert path.stat().st_mtime_ns == stamp, f"{path} was rewritten on a rerun"
