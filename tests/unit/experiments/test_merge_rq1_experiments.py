"""The RQ1 merge must not double-count an experiment measured twice.

One experiment directory can hold rows from more than one launch: on the
cluster, ``RQ1_addressing/addressing`` holds both the 2026-09-06 campaign and
the 2026-09-07 Isal campaign, and a recovery sweep re-emits units the original
array already wrote.  Concatenating them counts an arm's observations twice,
which shifts its medians and unbalances every paired test against the arms
measured once.  These tests pin the launch-tag filter and the duplicate audit
that catch it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from experiments.tkde.merge_rq1_experiments import (
    MergeIntegrityError,
    audit_duplicates,
    merge,
    tags_of,
)

pytestmark = pytest.mark.unit

RQ_FOLDER = "RQ1_addressing"


def _m1_rows(arm: str, edit_idx: range, experiment: str) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "rq": 1,
            "experiment": experiment,
            "collection": "synthetic_rq1",
            "seed": 0,
            "base_id": "b0",
            "edit_kind": "insert_fact",
            "edit_idx": list(edit_idx),
            "arm": arm,
            "d_abs": [float(i) for i in edit_idx],
        }
    )


def _write(exp_dir: Path, tag: str, unit: str, frame: pd.DataFrame) -> None:
    exp_dir.mkdir(parents=True, exist_ok=True)
    frame.to_csv(exp_dir / f"rows_m1__{tag}-{unit}.csv", index=False)


@pytest.fixture
def two_launch_root(tmp_path: Path) -> Path:
    """``addressing`` written by two launches; ``addressing_cpp`` by one."""
    root = tmp_path / "results"
    addressing = root / RQ_FOLDER / "addressing"
    # The old campaign and the new one both measured `fact_rank` on the same
    # units, under different code (the old one has no d_instr column).
    _write(
        addressing,
        "old00000",
        "m1-synthetic_rq1-000of001",
        _m1_rows("fact_rank", range(4), "addressing"),
    )
    new = _m1_rows("fact_rank", range(4), "addressing")
    new["d_instr"] = [1.0, 1.0, 2.0, 2.0]
    _write(addressing, "new11111", "m1-synthetic_rq1-000of001", new)

    cpp = root / RQ_FOLDER / "addressing_cpp"
    ow = _m1_rows("isal_ow_struct", range(4), "addressing_cpp")
    ow["d_instr"] = [1.0, 1.0, 1.0, 2.0]
    _write(cpp, "cpp22222", "m1-synthetic_rq1-000of001", ow)
    return root


class TestLaunchTags:
    def test_tags_of_lists_every_launch(self, two_launch_root: Path) -> None:
        counts = tags_of(two_launch_root / RQ_FOLDER / "addressing")
        assert counts == {"old00000": 1, "new11111": 1}

    def test_merge_without_a_filter_is_refused(self, two_launch_root: Path) -> None:
        with pytest.raises(MergeIntegrityError) as excinfo:
            merge(
                two_launch_root,
                ["addressing", "addressing_cpp"],
                "merged",
                out_root=two_launch_root / "out",
            )
        assert "duplicated observations" in str(excinfo.value)

    def test_only_tags_selects_one_launch(self, two_launch_root: Path) -> None:
        out_root = two_launch_root / "out"
        merge(
            two_launch_root,
            ["addressing", "addressing_cpp"],
            "merged",
            out_root=out_root,
            tags={"addressing": ["new11111"]},
        )
        out_dir = out_root / RQ_FOLDER / "merged"
        frame = pd.concat(
            [pd.read_csv(p) for p in out_dir.glob("rows_m1__*.csv")],
            ignore_index=True,
        )
        assert len(frame) == 8  # 4 fact_rank + 4 isal_ow_struct, each once
        assert set(frame["arm"]) == {"fact_rank", "isal_ow_struct"}
        # The surviving campaign is the one carrying the instruction column.
        assert frame["d_instr"].notna().all()

    def test_manifest_records_the_audit_and_the_tags(self, two_launch_root: Path) -> None:
        out_root = two_launch_root / "out"
        merge(
            two_launch_root,
            ["addressing", "addressing_cpp"],
            "merged",
            out_root=out_root,
            tags={"addressing": ["new11111"]},
        )
        manifest = json.loads((out_root / RQ_FOLDER / "merged" / "merge_manifest.json").read_text())
        assert manifest["source_tags_used"] == {"addressing": ["new11111"]}
        assert manifest["source_tags_available"]["addressing"] == {
            "old00000": 1,
            "new11111": 1,
        }
        assert manifest["duplicate_audit"]["m1"]["duplicate_rows"] == 0

    def test_allow_duplicates_writes_but_records_them(self, two_launch_root: Path) -> None:
        out_root = two_launch_root / "out"
        merge(
            two_launch_root,
            ["addressing", "addressing_cpp"],
            "merged",
            out_root=out_root,
            allow_duplicates=True,
        )
        manifest = json.loads((out_root / RQ_FOLDER / "merged" / "merge_manifest.json").read_text())
        assert manifest["duplicate_audit"]["m1"]["duplicate_rows"] == 4


class TestDuplicateAudit:
    def test_key_ignores_columns_a_launch_may_not_carry(self, tmp_path: Path) -> None:
        """The audit keys on the identity columns, not on the value columns."""
        exp = tmp_path / "exp"
        a = _m1_rows("fact_rank", range(2), "e")
        b = _m1_rows("fact_rank", range(2), "e")
        b["d_abs"] = [99.0, 99.0]  # same observation, different measured value
        _write(exp, "t1", "m1-synthetic_rq1-000of001", a)
        _write(exp, "t2", "m1-synthetic_rq1-000of001", b)
        report = audit_duplicates(exp)
        assert report["m1"]["rows"] == 4
        assert report["m1"]["unique_observations"] == 2
        assert report["m1"]["duplicate_rows"] == 2
