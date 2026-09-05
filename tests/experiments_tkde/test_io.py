"""Unit tests for the results writers and the configuration helpers.

The file set of ``DESIGN.md`` G6 is asserted exactly -- an experiment that
silently omits ``stats.json`` or writes ``rows.csv`` under another name is not
harvestable -- and both provenance paths are exercised: a real git checkout and
a deployed tree whose only record is the ``.tkde_deploy`` stamp.
"""

from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path

import pandas as pd
import pytest

from experiments.tkde.config import (
    DEFAULT_DATA_ROOT,
    DEFAULT_RESULTS_ROOT,
    TkdeConfigError,
    TkdeIOError,
    data_root,
    load_yaml,
    results_root,
    seeds,
)
from experiments.tkde.io import (
    RunPaths,
    repo_root,
    write_config,
    write_manifest,
    write_rows,
    write_stats,
    write_summary,
    write_tables_md,
)

pytestmark = pytest.mark.unit

EXPECTED_FILES = {
    "rows_main.csv",
    "config.json",
    "manifest.json",
    "summary.json",
    "stats.json",
    "tables.md",
}


@pytest.fixture
def paths(tmp_path: Path) -> RunPaths:
    return RunPaths(root=tmp_path, rq="RQ5_patterns", experiment="balanced")


class TestRunPaths:
    def test_dir_layout(self, tmp_path: Path, paths: RunPaths) -> None:
        assert paths.dir == tmp_path / "RQ5_patterns" / "balanced"

    def test_ensure_creates_the_tree(self, paths: RunPaths) -> None:
        assert paths.ensure().is_dir()


class TestWriteRows:
    def test_columns_keep_their_order(self, paths: RunPaths) -> None:
        rows = [{"b": 2, "a": 1}, {"a": 3, "b": 4}]
        target = write_rows(paths, "main", rows, columns=["a", "b"])
        assert target.name == "rows_main.csv"
        with target.open(encoding="utf-8", newline="") as handle:
            parsed = list(csv.reader(handle))
        assert parsed[0] == ["a", "b"]
        assert parsed[1] == ["1", "2"]
        assert parsed[2] == ["3", "4"]

    def test_missing_key_becomes_an_empty_field(self, paths: RunPaths) -> None:
        target = write_rows(paths, "main", [{"a": 1}], columns=["a", "b"])
        assert target.read_text(encoding="utf-8").splitlines()[1] == "1,"

    def test_rewrite_overwrites_rather_than_appends(self, paths: RunPaths) -> None:
        write_rows(paths, "main", [{"a": 1}, {"a": 2}], columns=["a"])
        target = write_rows(paths, "main", [{"a": 9}], columns=["a"])
        assert target.read_text(encoding="utf-8").splitlines() == ["a", "9"]

    def test_booleans_and_containers_are_rendered(self, paths: RunPaths) -> None:
        target = write_rows(
            paths, "main", [{"flag": True, "cell": [1, 2]}], columns=["flag", "cell"]
        )
        assert target.read_text(encoding="utf-8").splitlines()[1] == '1,"[1,2]"'

    def test_undeclared_column_raises(self, paths: RunPaths) -> None:
        with pytest.raises(TkdeIOError, match="undeclared columns"):
            write_rows(paths, "main", [{"a": 1, "sneaky": 2}], columns=["a"])

    def test_empty_columns_raise(self, paths: RunPaths) -> None:
        with pytest.raises(TkdeIOError, match="columns must not be empty"):
            write_rows(paths, "main", [], columns=[])

    def test_no_rows_still_writes_the_header(self, paths: RunPaths) -> None:
        target = write_rows(paths, "main", [], columns=["a", "b"])
        assert target.read_text(encoding="utf-8").strip() == "a,b"


class TestJsonWriters:
    def test_config_summary_and_stats(self, paths: RunPaths) -> None:
        write_config(paths, {"seed": 5, "path": Path("/tmp/x")})
        write_summary(paths, {"ari": 0.5})
        write_stats(paths, {"interval": {"point": 1.0}})
        assert json.loads((paths.dir / "config.json").read_text())["path"] == "/tmp/x"
        assert json.loads((paths.dir / "summary.json").read_text())["ari"] == 0.5
        assert json.loads((paths.dir / "stats.json").read_text())["interval"]["point"] == 1.0

    def test_numpy_values_are_coerced(self, paths: RunPaths) -> None:
        import numpy as np

        write_summary(
            paths, {"scalar": np.float64(1.5), "array": np.arange(3), "flag": np.bool_(True)}
        )
        payload = json.loads((paths.dir / "summary.json").read_text())
        assert payload == {"scalar": 1.5, "array": [0, 1, 2], "flag": True}

    def test_interval_dataclass_is_coerced(self, paths: RunPaths) -> None:
        from experiments.tkde.stats import Interval

        write_stats(paths, {"ci": Interval(0.5, 0.4, 0.6, "wilson", 10)})
        payload = json.loads((paths.dir / "stats.json").read_text())
        assert payload["ci"]["method"] == "wilson"


class TestManifest:
    def test_git_path_in_a_real_checkout(self, paths: RunPaths) -> None:
        write_manifest(paths)
        manifest = json.loads((paths.dir / "manifest.json").read_text())
        assert manifest["git_source"] == "git"
        assert manifest["git_sha"] is not None
        assert len(manifest["git_sha"]) == 40
        assert manifest["hostname"]
        assert manifest["cpu_model"]
        assert manifest["python_version"]
        for package in ("numpy", "scipy", "scikit-learn", "rapidfuzz", "pynauty"):
            assert package in manifest["package_versions"]
        assert set(manifest["slurm"]) >= {"SLURM_JOB_ID", "SLURM_ARRAY_TASK_ID"}
        assert manifest["start_iso"] <= manifest["end_iso"]

    def test_deploy_stamp_path_when_git_is_absent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        deployed = tmp_path / "deployed"
        deployed.mkdir()
        (deployed / ".tkde_deploy").write_text(
            "sha=abc123 branch=integration/w1 from=/home/x/IsalHG at=2026-09-05T10:00:00+02:00\n",
            encoding="utf-8",
        )
        monkeypatch.setenv("ISALHG_REPO_ROOT", str(deployed))
        assert repo_root() == deployed

        paths = RunPaths(root=tmp_path / "results", rq="RQ1", experiment="e")
        write_manifest(paths)
        manifest = json.loads((paths.dir / "manifest.json").read_text())
        assert manifest["git_sha"] == "abc123"
        assert manifest["git_branch"] == "integration/w1"
        assert manifest["git_source"].startswith(".tkde_deploy:")

    def test_neither_git_nor_stamp(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        bare = tmp_path / "bare"
        bare.mkdir()
        monkeypatch.setenv("ISALHG_REPO_ROOT", str(bare))
        paths = RunPaths(root=tmp_path / "results", rq="RQ1", experiment="e")
        write_manifest(paths)
        manifest = json.loads((paths.dir / "manifest.json").read_text())
        assert manifest["git_sha"] is None
        assert manifest["git_source"] == "unavailable"

    def test_records_slurm_ids_when_set(
        self, paths: RunPaths, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SLURM_JOB_ID", "2210893")
        monkeypatch.setenv("SLURM_ARRAY_TASK_ID", "7")
        write_manifest(paths)
        manifest = json.loads((paths.dir / "manifest.json").read_text())
        assert manifest["slurm"]["SLURM_JOB_ID"] == "2210893"
        assert manifest["slurm"]["SLURM_ARRAY_TASK_ID"] == "7"

    def test_counts_the_rows_already_written(self, paths: RunPaths) -> None:
        write_rows(paths, "main", [{"a": 1}, {"a": 2}, {"a": 3}], columns=["a"])
        write_rows(paths, "aux", [], columns=["b"])
        write_manifest(paths)
        counts = json.loads((paths.dir / "manifest.json").read_text())["row_counts"]
        assert counts == {"main": 3, "aux": 0}

    def test_extra_overrides_defaults(self, paths: RunPaths) -> None:
        write_manifest(paths, extra={"start_iso": "2026-01-01T00:00:00+00:00", "note": "smoke"})
        manifest = json.loads((paths.dir / "manifest.json").read_text())
        assert manifest["start_iso"] == "2026-01-01T00:00:00+00:00"
        assert manifest["note"] == "smoke"

    def test_git_sha_matches_the_repository(self, paths: RunPaths) -> None:
        write_manifest(paths)
        manifest = json.loads((paths.dir / "manifest.json").read_text())
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root(),
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        assert manifest["git_sha"] == head


class TestTablesMd:
    def test_one_section_per_table(self, paths: RunPaths) -> None:
        tables = {
            "geometry": pd.DataFrame({"arm": ["fact_rank"], "nu": [0.097]}),
            "clustering": pd.DataFrame({"arm": ["fact_rank"], "ari": [0.285]}),
        }
        target = write_tables_md(paths, tables)
        text = target.read_text(encoding="utf-8")
        assert target.name == "tables.md"
        assert "## geometry" in text
        assert "## clustering" in text
        assert "| arm | nu |" in text
        assert "0.097" in text

    def test_empty_frame(self, paths: RunPaths) -> None:
        write_tables_md(paths, {"nothing": pd.DataFrame()})
        assert "*(empty table)*" in (paths.dir / "tables.md").read_text(encoding="utf-8")

    def test_pipes_in_values_are_escaped(self, paths: RunPaths) -> None:
        write_tables_md(paths, {"t": pd.DataFrame({"c": ["a|b"]})})
        assert "a\\|b" in (paths.dir / "tables.md").read_text(encoding="utf-8")


class TestFullFileSet:
    def test_the_six_g6_files_and_nothing_else(self, paths: RunPaths) -> None:
        write_rows(paths, "main", [{"a": 1}], columns=["a"])
        write_config(paths, {"seed": 1})
        write_summary(paths, {"x": 1})
        write_stats(paths, {"y": 2})
        write_tables_md(paths, {"t": pd.DataFrame({"a": [1]})})
        write_manifest(paths)
        assert {path.name for path in paths.dir.iterdir()} == EXPECTED_FILES


class TestConfig:
    def test_seed_schedule(self) -> None:
        assert seeds(1) == list(range(10_000, 10_027))
        assert seeds(7, S=3) == [70_000, 70_001, 70_002]
        assert len(seeds(4)) == 27
        assert set(seeds(1)).isdisjoint(seeds(2))

    @pytest.mark.parametrize(("rq_index", "S"), [(-1, 27), (1, 0)])
    def test_invalid_seed_arguments_raise(self, rq_index: int, S: int) -> None:
        with pytest.raises(TkdeConfigError):
            seeds(rq_index, S)

    def test_roots_read_the_environment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ISALHG_RESULTS_ROOT", "/x/results")
        monkeypatch.setenv("ISALHG_DATA_ROOT", "/x/data")
        assert results_root() == Path("/x/results")
        assert data_root() == Path("/x/data")

    def test_roots_fall_back_to_the_design_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ISALHG_RESULTS_ROOT", raising=False)
        monkeypatch.delenv("ISALHG_DATA_ROOT", raising=False)
        assert results_root() == DEFAULT_RESULTS_ROOT
        assert data_root() == DEFAULT_DATA_ROOT

    def test_results_root_agrees_with_the_corpora_loader(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from experiments.tkde import corpora

        monkeypatch.setenv("ISALHG_RESULTS_ROOT", "/x/results")
        assert results_root() == corpora.results_root()

    def test_load_yaml(self, tmp_path: Path) -> None:
        config = tmp_path / "c.yaml"
        config.write_text("a: 1\nb: [1, 2]\n", encoding="utf-8")
        assert load_yaml(config) == {"a": 1, "b": [1, 2]}

    def test_empty_yaml_is_an_empty_mapping(self, tmp_path: Path) -> None:
        config = tmp_path / "c.yaml"
        config.write_text("", encoding="utf-8")
        assert load_yaml(config) == {}

    def test_missing_and_non_mapping_yaml_raise(self, tmp_path: Path) -> None:
        with pytest.raises(TkdeConfigError, match="no configuration file"):
            load_yaml(tmp_path / "absent.yaml")
        listing = tmp_path / "list.yaml"
        listing.write_text("- 1\n- 2\n", encoding="utf-8")
        with pytest.raises(TkdeConfigError, match="must hold a mapping"):
            load_yaml(listing)
