"""End-to-end smoke for the RQ8 runner and analyzer, in the RQ3/RQ6 style.

Runs the real code path against a tiny in-memory collection written to a
temporary corpora root, then the analyzer over what it wrote. What is asserted
is the *contract*, not the numbers: the arm set, the tables, the theorem-backed
columns, and the stale-row guard.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.tkde import io
from experiments.tkde.rq1 import run_tag, table_file
from experiments.tkde.rq8 import (
    ARM_OURS,
    COLUMNS,
    NON_GENERATIVE_ROWS,
    RQ_FOLDER,
    Unit,
    enumerate_units,
    main,
    parse_shard,
    unit_is_done,
)

pytestmark = pytest.mark.integration

COLLECTION = "smoke_kb"


def _records() -> list[dict]:
    """Thirty small non-star knowledge bases over one shared vocabulary.

    Each is a four-fact chain-plus-hub, so every member has interior facts and a
    fact can be deleted without disconnecting the remainder.
    """
    records = []
    for index in range(30):
        predicate = index % 3
        records.append(
            {
                "kb_id": f"kb{index:03d}",
                "n": 5,
                "types": [0, 1, 1, 2, 2],
                "facts": [
                    [predicate, [0, 1]],
                    [predicate, [1, 2]],
                    [(predicate + 1) % 3, [2, 3]],
                    [(predicate + 2) % 3, [3, 4]],
                ],
                "roles": None,
                "constant_ids": None,
                "label": f"class{index % 3}",
                "meta": {},
            }
        )
    return records


@pytest.fixture
def data_root(tmp_path: Path) -> Path:
    """A corpora root holding one frozen collection."""
    directory = tmp_path / "corpora" / COLLECTION
    directory.mkdir(parents=True)
    (directory / "records.jsonl").write_text(
        "\n".join(json.dumps(record) for record in _records()) + "\n", encoding="utf-8"
    )
    (directory / "vocab.json").write_text(
        json.dumps(
            {
                "name": COLLECTION,
                "type_names": ["entity", "left", "right"],
                "pred_names": ["p", "q", "r"],
                "role_names": [],
                "k_max": 4,
                "meta": {},
                "n_records": 30,
            }
        ),
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture
def config_path(tmp_path: Path) -> Path:
    """A two-seed RQ8 configuration over the smoke collection."""
    import yaml

    payload = {
        "rq": "RQ8",
        "experiment": "completion",
        "seed_count": 2,
        "collections": [COLLECTION],
        "strata": {COLLECTION: ["non_star"]},
        "m_min": 4,
        "min_pool": 5,
        "train_frac": 0.8,
        "units_per_member": 1,
        "max_eval_units": 3,
        "k_proposals": 3,
        "resamples": 4,
        "ngram_order": 3,
        "ngram_order_ho": 6,
        "max_len": 200,
        "max_new_tokens": 40,
        "arms": [ARM_OURS, "fact_ngram", "incidence_ngram", "pattern_freq", "pattern_cooc"],
        "n_shards": 2,
    }
    path = tmp_path / "rq8_smoke.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def _run(config_path: Path, out: Path, data_root: Path, *extra: str) -> int:
    return main(
        [
            "--config",
            str(config_path),
            "--out",
            str(out),
            "--data-root",
            str(data_root),
            "--log-level",
            "WARNING",
            *extra,
        ]
    )


class TestUnitEnumeration:
    """The unit list is the stratum x seed grid, and it is unique."""

    def test_the_grid_is_collections_times_strata_times_seeds(self):
        config = {"seed_count": 4, "collections": ["a", "b"], "strata": {"b": ["non_star", "star"]}}
        units = enumerate_units(config)
        assert len(units) == 4 * 1 + 4 * 2

    def test_every_unit_id_is_unique(self):
        config = {
            "seed_count": 27,
            "collections": ["a", "b"],
            "strata": {"b": ["non_star", "star"]},
        }
        ids = [unit.unit_id for unit in enumerate_units(config)]
        assert len(set(ids)) == len(ids)

    def test_a_collection_without_declared_strata_runs_non_star(self):
        units = enumerate_units({"seed_count": 1, "collections": ["a"]})
        assert [unit.stratum for unit in units] == ["non_star"]

    @pytest.mark.parametrize(
        ("spec", "expected"), [(None, (0, 1)), ("0/3", (0, 3)), ("2/3", (2, 3))]
    )
    def test_shard_parsing(self, spec, expected):
        assert parse_shard(spec, 10) == expected

    @pytest.mark.parametrize("spec", ["3/3", "-1/3", "1/0", "nonsense"])
    def test_a_bad_shard_raises(self, spec):
        from experiments.tkde.rq8 import RQ8Error

        with pytest.raises(RQ8Error):
            parse_shard(spec, 10)


class TestRunnerEndToEnd:
    """The runner writes what the analyzer and the tables need."""

    def test_it_writes_both_tables_and_the_census(self, config_path, data_root, tmp_path):
        out = tmp_path / "results"
        assert _run(config_path, out, data_root) == 0
        directory = out / RQ_FOLDER / "completion"
        assert list(directory.glob("rows_units__*.csv"))
        assert list(directory.glob("rows_detail__*.csv"))
        assert list(directory.glob("rows_census__*.csv"))
        assert (directory / "config.json").is_file()
        assert (directory / "manifest.json").is_file()

    def test_every_row_file_carries_the_run_tag(self, config_path, data_root, tmp_path):
        out = tmp_path / "results"
        _run(config_path, out, data_root)
        directory = out / RQ_FOLDER / "completion"
        from experiments.tkde.config import load_yaml

        tag = run_tag(load_yaml(config_path))
        for path in directory.glob("rows_*.csv"):
            assert f"__{tag}-" in path.name

    def test_ours_is_scored_and_is_not_fact_ngram(self, config_path, data_root, tmp_path):
        import csv

        out = tmp_path / "results"
        _run(config_path, out, data_root)
        rows = []
        for path in (out / RQ_FOLDER / "completion").glob("rows_units__*.csv"):
            with path.open(encoding="utf-8", newline="") as handle:
                rows.extend(csv.DictReader(handle))
        arms = {row["arm"] for row in rows}
        assert ARM_OURS in arms
        assert ARM_OURS == "ow_ngram"
        assert "fact_ngram" in arms  # present as a baseline, never as ours

    def test_our_arm_is_valid_and_connected_everywhere(self, config_path, data_root, tmp_path):
        import csv

        out = tmp_path / "results"
        _run(config_path, out, data_root)
        ours = []
        for path in (out / RQ_FOLDER / "completion").glob("rows_units__*.csv"):
            with path.open(encoding="utf-8", newline="") as handle:
                ours.extend(row for row in csv.DictReader(handle) if row["arm"] == ARM_OURS)
        assert ours
        for row in ours:
            # Proposition C.8: not a filtered rate, a theorem.
            assert float(row["validity"]) == 1.0
            assert float(row["connectivity"]) == 1.0

    def test_the_incidence_baseline_rejects_some_of_its_own_samples(
        self, config_path, data_root, tmp_path
    ):
        # Regression: the prefix must drop the serialization's ("END",)
        # terminator. With the terminator kept, every continuation lands after
        # the point the strict decoder stops at, so the arm decodes its own
        # prefix every time and reports validity 1.000 --- the opposite of the
        # H8.3 contrast, and a measurement of the prefix construction rather
        # than of the flat language.
        import csv

        out = tmp_path / "results"
        _run(config_path, out, data_root)
        rows = []
        for path in (out / RQ_FOLDER / "completion").glob("rows_units__*.csv"):
            with path.open(encoding="utf-8", newline="") as handle:
                rows.extend(r for r in csv.DictReader(handle) if r["arm"] == "incidence_ngram")
        assert rows
        assert min(float(row["validity"]) for row in rows) < 1.0

    def test_a_counting_arm_never_reports_a_decode_failure(self, config_path, data_root, tmp_path):
        # Regression: an attachment that reproduces an existing fact is a wasted
        # slot, not an invalid proposal. Recording it as one put a counting
        # artefact in the validity column, which is where H8.3 is read.
        import csv

        out = tmp_path / "results"
        _run(config_path, out, data_root)
        rows = []
        for path in (out / RQ_FOLDER / "completion").glob("rows_units__*.csv"):
            with path.open(encoding="utf-8", newline="") as handle:
                rows.extend(
                    r
                    for r in csv.DictReader(handle)
                    if r["arm"] in ("pattern_freq", "pattern_cooc")
                )
        assert rows
        for row in rows:
            assert float(row["validity"]) == 1.0

    def test_the_run_is_idempotent(self, config_path, data_root, tmp_path):
        out = tmp_path / "results"
        _run(config_path, out, data_root)
        directory = out / RQ_FOLDER / "completion"
        before = {path.name: path.read_text(encoding="utf-8") for path in directory.glob("rows_*")}
        _run(config_path, out, data_root)
        after = {path.name: path.read_text(encoding="utf-8") for path in directory.glob("rows_*")}
        assert before == after

    def test_sharding_covers_the_unit_list(self, config_path, data_root, tmp_path):
        out = tmp_path / "results"
        _run(config_path, out, data_root, "--shard", "0/2")
        _run(config_path, out, data_root, "--shard", "1/2")
        directory = out / RQ_FOLDER / "completion"
        assert len(list(directory.glob("rows_units__*.csv"))) == 2

    def test_the_columns_are_the_declared_ones(self, config_path, data_root, tmp_path):
        import csv

        out = tmp_path / "results"
        _run(config_path, out, data_root)
        directory = out / RQ_FOLDER / "completion"
        for table in ("units", "detail", "census"):
            path = next(directory.glob(f"rows_{table}__*.csv"))
            with path.open(encoding="utf-8", newline="") as handle:
                assert tuple(next(csv.reader(handle))) == COLUMNS[table]

    def test_census_only_writes_the_gate_and_nothing_else(self, config_path, data_root, tmp_path):
        out = tmp_path / "results"
        assert _run(config_path, out, data_root, "--census-only") == 0
        directory = out / RQ_FOLDER / "completion"
        assert list(directory.glob("rows_census__*.csv"))
        assert not list(directory.glob("rows_units__*.csv"))


class TestStaleRowGuard:
    """A changed arm set must not be served the previous run's rows."""

    def test_the_run_tag_changes_with_the_arm_set(self):
        base = {"collections": ["a"], "arms": ["ow_ngram", "pattern_cooc"]}
        changed = {"collections": ["a"], "arms": ["ow_ngram", "pattern_cooc", "pattern_freq"]}
        assert run_tag(base) != run_tag(changed)

    def test_the_run_tag_ignores_the_shard_count(self):
        assert run_tag({"collections": ["a"], "n_shards": 4}) == run_tag(
            {"collections": ["a"], "n_shards": 81}
        )

    def test_a_done_unit_is_not_done_under_a_different_tag(self, tmp_path):
        paths = io.RunPaths(root=tmp_path, rq=RQ_FOLDER, experiment="completion")
        unit = Unit("a", "non_star", 0)
        for table in unit.tables:
            io.write_rows(
                paths,
                table_file("aaaaaaaa", table, unit.unit_id),
                [{"rq": "RQ8"}],
                columns=("rq",),
            )
        assert unit_is_done(paths, unit, "aaaaaaaa")
        assert not unit_is_done(paths, unit, "bbbbbbbb")

    def test_a_changed_arm_set_reruns_rather_than_resuming(self, config_path, data_root, tmp_path):
        import yaml

        out = tmp_path / "results"
        _run(config_path, out, data_root)
        directory = out / RQ_FOLDER / "completion"
        first = {path.name for path in directory.glob("rows_units__*.csv")}

        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        payload["arms"] = [*payload["arms"], "random_pattern"]
        config_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        _run(config_path, out, data_root)

        second = {path.name for path in directory.glob("rows_units__*.csv")} - first
        assert second, "a changed arm set must write new row files"


class TestAnalyzer:
    """The analyzer produces the four artefacts and the pre-registered verdicts."""

    def test_it_writes_summary_stats_and_tables(self, config_path, data_root, tmp_path):
        from experiments.tkde.analyze_rq8 import analyze

        out = tmp_path / "results"
        _run(config_path, out, data_root)
        analyze(out, "completion")
        directory = out / RQ_FOLDER / "completion"
        assert (directory / "summary.json").is_file()
        assert (directory / "stats.json").is_file()
        assert (directory / "tables.md").is_file()

    def test_every_hypothesis_is_reported(self, config_path, data_root, tmp_path):
        from experiments.tkde.analyze_rq8 import analyze

        out = tmp_path / "results"
        _run(config_path, out, data_root)
        result = analyze(out, "completion")
        assert set(result["hypotheses"]) == {"H8.1", "H8.2", "H8.3"}

    def test_a_failed_headline_prints_its_fallback(self, config_path, data_root, tmp_path):
        from experiments.tkde.analyze_rq8 import analyze

        out = tmp_path / "results"
        _run(config_path, out, data_root)
        block = analyze(out, "completion")["hypotheses"]["H8.1"]
        if block["verdict"] != "supported":
            assert block["fallback"], "a failed H8.1 must print its pre-registered fallback"

    def test_the_non_generative_rows_carry_their_reason(self, config_path, data_root, tmp_path):
        from experiments.tkde.analyze_rq8 import NO_COMPLETION_REASON, analyze

        out = tmp_path / "results"
        _run(config_path, out, data_root)
        analyze(out, "completion")
        text = (out / RQ_FOLDER / "completion" / "tables.md").read_text(encoding="utf-8")
        for arm in NON_GENERATIVE_ROWS:
            assert arm in text
        assert NO_COMPLETION_REASON in text

    def test_the_summary_records_whether_the_secondary_arm_ran(
        self, config_path, data_root, tmp_path
    ):
        from experiments.tkde.analyze_rq8 import analyze

        out = tmp_path / "results"
        _run(config_path, out, data_root)
        summary = analyze(out, "completion")["summary"]
        assert summary["secondary_arm_enabled"] is False
