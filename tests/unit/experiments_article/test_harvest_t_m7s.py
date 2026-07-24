"""Unit tests for scripts/harvest_T_M7s.py — T-M7s acceptance verifiers.

Acceptance criteria
-------------------
AC-H1. parse_sacct_tsv correctly parses ``--parsable2`` sacct output and
       filters out .batch/.extern sub-steps.
AC-H2. summarise_census counts states correctly and identifies non-completed
       tasks by cell_key and dist_name.
AC-H3. verify_ac2_ci_coverage passes when every CI entry has non-NaN bounds
       and fails when any entry is missing or NaN.
AC-H4. verify_ac3_wilcoxon_coverage passes when every Wilcoxon entry has
       ``p_holm`` and ``effect_size``, and fails when those keys are absent.
AC-H5. verify_ac4_per_arity passes when all three expected arities (3, 4, 5)
       appear in a2_per_arity / a3_per_arity and fails when one is missing or
       a phantom arity appears.
AC-H6. verify_ac5_axis_coverage correctly distinguishes the three axes (n,
       density, arity), reports arity-axis shortfall without gating the pass
       on it, and fails when a cell stats file is missing.
AC-H9. verify_multi_rep_wilcoxon_populated catches the per-task aggregation
       bug: a CellStats with ≥2 representations but empty wilcoxon fails.
AC-H10. verify_excluded_cells_no_isalhg_comparison catches any exclusion
        policy violation: an excluded cell with a non-empty wilcoxon fails.
AC-H11. verify_ac3_wilcoxon_coverage catches a missing ``reverse`` sub-dict
        (forward-only entry) and a missing/wrong ``alternative`` direction label.

Teeth (tests observed failing before fix / against wrong data):
- test_ac2_fails_on_nan_ci: fails if NaN CIs are accepted as valid.
- test_ac2_fails_on_empty_cis: fails if empty CI dict returns pass=True.
- test_ac3_fails_on_missing_p_holm: fails if missing p_holm is accepted.
- test_ac3_fails_on_empty_wilcoxon: fails if empty Wilcoxon returns pass=True.
- test_ac3_fails_on_missing_reverse_direction: fails if a forward-only entry
  (no ``reverse`` sub-dict) is accepted as complete — the T-M7t/coordinator
  addition: the article must cite both directions.
- test_ac3_fails_on_missing_alternative_label: fails if an unlabelled entry
  (missing ``alternative`` field) is accepted — direction must be explicit.
- test_ac4_fails_on_missing_arity: fails if arity 4 is absent.
- test_ac4_fails_on_phantom_arity: fails if phantom arity 7 appears.
- test_ac5_arity_axis_shortfall_does_not_block_pass: k∈{3,5} alone does NOT
  trigger pass=False (the arity_axis_note records the shortfall).
- test_multi_rep_wilcoxon_populated_fails_on_empty_wilcoxon: fails if a file
  with ≥2 reps and empty wilcoxon is accepted as valid — the T-M7t regression.
- test_excluded_cell_no_isalhg_comparison_fails_when_wilcoxon_nonempty: fails
  if a wilcoxon entry is emitted for an excluded (timeout) cell.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Import the functions under test
# ---------------------------------------------------------------------------

from scripts.harvest_T_M7s import (
    compute_harvest_decision,
    parse_sacct_tsv,
    summarise_census,
    verify_ac2_ci_coverage,
    verify_ac3_wilcoxon_coverage,
    verify_ac4_per_arity,
    verify_ac5_axis_coverage,
    verify_excluded_cells_no_isalhg_comparison,
    verify_multi_rep_wilcoxon_populated,
)

# ---------------------------------------------------------------------------
# Minimal CellStats stub (avoids importing sweep_multi_seed in tests)
# ---------------------------------------------------------------------------


@dataclass
class _FakeCellStats:
    """Minimal stand-in for CellStats."""

    cell_key: str = "stratum_a"
    stratum: str = "a"
    n_seeds: int = 27
    cis: dict[str, dict[str, Any]] = field(default_factory=dict)
    wilcoxon: dict[str, dict[str, Any]] = field(default_factory=dict)
    block_meta: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# AC-H1 — parse_sacct_tsv
# ---------------------------------------------------------------------------


def _write_sacct_tsv(path: Path, rows: list[tuple[str, str]]) -> None:
    """Write a minimal sacct parsable2 TSV."""
    with open(path, "w") as fh:
        for job_id, state in rows:
            fh.write(f"{job_id}|{state}|0:0|01:00:00\n")


def test_parse_sacct_filters_batch_steps(tmp_path: Path) -> None:
    """Batch and extern sub-steps are excluded from the census."""
    tsv = tmp_path / "sacct.tsv"
    _write_sacct_tsv(
        tsv,
        [
            ("1640910_0", "COMPLETED"),
            ("1640910_0.batch", "COMPLETED"),
            ("1640910_0.extern", "COMPLETED"),
            ("1640910_1", "TIMEOUT"),
        ],
    )
    states = parse_sacct_tsv(tsv)
    assert "1640910_0" in states
    assert "1640910_1" in states
    assert "1640910_0.batch" not in states
    assert "1640910_0.extern" not in states


def test_parse_sacct_maps_states(tmp_path: Path) -> None:
    """States are mapped correctly."""
    tsv = tmp_path / "sacct.tsv"
    _write_sacct_tsv(
        tsv,
        [
            ("1640910_42", "TIMEOUT"),
            ("1640910_56", "OUT_OF_MEMORY"),
            ("1640910_70", "COMPLETED"),
        ],
    )
    states = parse_sacct_tsv(tsv)
    assert states["1640910_42"] == "TIMEOUT"
    assert states["1640910_56"] == "OUT_OF_MEMORY"
    assert states["1640910_70"] == "COMPLETED"


# ---------------------------------------------------------------------------
# AC-H2 — summarise_census
# ---------------------------------------------------------------------------


def test_summarise_census_counts(tmp_path: Path) -> None:
    """Counts COMPLETED, TIMEOUT, FAILED, OOM correctly."""
    census = [
        {
            "task_idx": 0,
            "task_id": "j_0",
            "cell_key": "stratum_a",
            "dist_name": "isalhg_levenshtein",
            "state": "COMPLETED",
        },
        {
            "task_idx": 1,
            "task_id": "j_1",
            "cell_key": "stratum_a",
            "dist_name": "hypergraph_wl_l1",
            "state": "COMPLETED",
        },
        {
            "task_idx": 2,
            "task_id": "j_2",
            "cell_key": "er_uniform_k3_n16_rho4",
            "dist_name": "isalhg_levenshtein",
            "state": "TIMEOUT",
        },
        {
            "task_idx": 3,
            "task_id": "j_3",
            "cell_key": "er_uniform_k3_n24_rho2",
            "dist_name": "isalhg_levenshtein",
            "state": "OUT_OF_MEMORY",
        },
    ]
    result = summarise_census(census)
    assert result["total"] == 4
    assert result["completed"] == 2
    assert result["timeout"] == 1
    assert result["oom"] == 1
    assert result["failed"] == 0
    assert len(result["non_completed_tasks"]) == 2


def test_summarise_census_non_completed_has_cell_and_dist() -> None:
    """Non-completed entries carry cell_key and dist_name."""
    census = [
        {
            "task_idx": 42,
            "task_id": "j_42",
            "cell_key": "er_uniform_k3_n16_rho4",
            "dist_name": "isalhg_levenshtein",
            "state": "TIMEOUT",
        },
    ]
    result = summarise_census(census)
    nc = result["non_completed_tasks"]
    assert len(nc) == 1
    assert nc[0]["cell_key"] == "er_uniform_k3_n16_rho4"
    assert nc[0]["dist_name"] == "isalhg_levenshtein"
    assert nc[0]["state"] == "TIMEOUT"


# ---------------------------------------------------------------------------
# AC-H3 — verify_ac2_ci_coverage (teeth: fails on NaN, fails on empty)
# ---------------------------------------------------------------------------


def _make_ci_entry(dist: str, metric: str, lo: float, hi: float) -> tuple[str, dict[str, Any]]:
    return (
        f"{dist}::{metric}",
        {
            "repr": dist,
            "metric": metric,
            "mean": 0.5,
            "n_valid": 27,
            "ci_lower": lo,
            "ci_upper": hi,
        },
    )


def test_ac2_passes_on_valid_cis() -> None:
    """All non-NaN CIs → pass=True."""
    cs = _FakeCellStats()
    cs.cis = dict(
        [
            _make_ci_entry("isalhg_levenshtein", "g1_a1::nu", 0.09, 0.11),
            _make_ci_entry("isalhg_levenshtein", "a2::ari", 0.30, 0.40),
            _make_ci_entry("hypergraph_wl_l1", "g1_a1::nu", 0.50, 0.60),
        ]
    )
    result = verify_ac2_ci_coverage(cs, min_reps=2)
    assert result["pass"] is True
    assert result["n_ci_valid"] == 3
    assert result["n_reps_with_ci"] == 2


def test_ac2_fails_on_nan_ci() -> None:
    """A single NaN bound makes pass=False — TOOTH."""
    cs = _FakeCellStats()
    cs.cis = dict(
        [
            _make_ci_entry("isalhg_levenshtein", "g1_a1::nu", 0.09, 0.11),
            _make_ci_entry("isalhg_levenshtein", "a2::ari", float("nan"), float("nan")),
        ]
    )
    result = verify_ac2_ci_coverage(cs, min_reps=1)
    assert result["pass"] is False
    assert result["n_ci_valid"] == 1  # only first entry is valid


def test_ac2_fails_on_empty_cis() -> None:
    """Empty CI dict → pass=False — TOOTH."""
    cs = _FakeCellStats()
    cs.cis = {}
    result = verify_ac2_ci_coverage(cs, min_reps=1)
    assert result["pass"] is False
    assert result["n_ci_entries"] == 0


def test_ac2_fails_on_missing_ci_keys() -> None:
    """CI entry without ci_lower/ci_upper is treated as NaN."""
    cs = _FakeCellStats()
    cs.cis = {
        "isalhg_levenshtein::g1_a1::nu": {
            "repr": "isalhg_levenshtein",
            "metric": "g1_a1::nu",
            "mean": 0.1,
            "n_valid": 27,
            # no ci_lower, no ci_upper
        }
    }
    result = verify_ac2_ci_coverage(cs, min_reps=1)
    assert result["pass"] is False


# ---------------------------------------------------------------------------
# AC-H4 — verify_ac3_wilcoxon_coverage (teeth: fails on missing p_holm)
# ---------------------------------------------------------------------------


def _make_wilcoxon_entry(
    dist: str,
    metric: str,
    *,
    p_holm: float | None = 0.03,
    effect_size: float | None = 0.4,
    include_alternative: bool = True,
    include_reverse: bool = True,
) -> tuple[str, dict[str, Any]]:
    """Build a wilcoxon entry for testing.

    By default produces a fully-specified entry (both directions labelled).
    Set ``include_alternative=False`` or ``include_reverse=False`` to produce
    incomplete entries for TOOTH tests.
    """
    row: dict[str, Any] = {
        "repr": dist,
        "metric": metric,
        "n_pairs": 27,
        "median_diff": 0.1,
    }
    if p_holm is not None:
        row["p_holm"] = p_holm
    if effect_size is not None:
        row["effect_size"] = effect_size
    if include_alternative:
        row["alternative"] = "isalhg_greater"
    if include_reverse:
        row["reverse"] = {
            "alternative": "competitor_greater",
            "p_holm": 1.0 - (p_holm or 0.0),
            "effect_size": -(effect_size or 0.0),
            "median_diff": -0.1,
            "n_pairs": 27,
            "family_size": 60,
        }
    return f"{dist}::{metric}", row


def test_ac3_passes_on_complete_wilcoxon() -> None:
    """All entries have p_holm, effect_size, alternative, and reverse → pass=True."""
    cs = _FakeCellStats()
    cs.wilcoxon = dict(
        [
            _make_wilcoxon_entry("hypergraph_wl_l1", "a2::ari"),
            _make_wilcoxon_entry("hpd_jsd", "a2::ari"),
        ]
    )
    result = verify_ac3_wilcoxon_coverage(cs)
    assert result["pass"] is True
    assert result["n_complete"] == 2
    assert result["missing_reverse"] == []
    assert result["mislabelled"] == []


def test_ac3_fails_on_missing_p_holm() -> None:
    """Missing p_holm makes pass=False — TOOTH."""
    cs = _FakeCellStats()
    cs.wilcoxon = dict(
        [
            _make_wilcoxon_entry("hypergraph_wl_l1", "a2::ari", p_holm=None, effect_size=0.4),
        ]
    )
    result = verify_ac3_wilcoxon_coverage(cs)
    assert result["pass"] is False
    assert result["n_complete"] == 0


def test_ac3_fails_on_missing_effect_size() -> None:
    """Missing effect_size makes pass=False — TOOTH."""
    cs = _FakeCellStats()
    cs.wilcoxon = dict(
        [
            _make_wilcoxon_entry("hypergraph_wl_l1", "a2::ari", p_holm=0.03, effect_size=None),
        ]
    )
    result = verify_ac3_wilcoxon_coverage(cs)
    assert result["pass"] is False


def test_ac3_fails_on_empty_wilcoxon() -> None:
    """Empty Wilcoxon dict → pass=False — TOOTH."""
    cs = _FakeCellStats()
    cs.wilcoxon = {}
    result = verify_ac3_wilcoxon_coverage(cs)
    assert result["pass"] is False
    assert result["n_wilcoxon_entries"] == 0


# ---------------------------------------------------------------------------
# AC-H5 — verify_ac4_per_arity (teeth: fails on missing arity, phantom)
# ---------------------------------------------------------------------------


def _write_seed_metrics_json(
    tmp_path: Path,
    a2_per_arity: dict[str, Any],
    a3_per_arity: dict[str, Any],
    a2a3_dropped: dict[str, Any] | None = None,
) -> Path:
    """Write a minimal isalhg_levenshtein.json for stratum_a/seed0."""
    p = tmp_path / "seed_metrics" / "a" / "stratum_a" / "seed0" / "isalhg_levenshtein.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "cell_key": "stratum_a",
        "stratum": "a",
        "dist_name": "isalhg_levenshtein",
        "seed": 0,
        "n_corpus": 85,
        "g1_a1": None,
        "a2": None,
        "a3": None,
        "bits": None,
        "a2_per_arity": a2_per_arity,
        "a3_per_arity": a3_per_arity,
        "realized_counts_per_family": {},
        "realized_counts_per_coarse_class": {},
        "a2a3_dropped_coarse_classes": a2a3_dropped or {},
    }
    p.write_text(json.dumps(payload))
    return tmp_path


def test_ac4_passes_on_correct_arities(tmp_path: Path) -> None:
    """All three arities present, no phantoms → pass=True."""
    root = _write_seed_metrics_json(
        tmp_path,
        a2_per_arity={"3": {"ari": 0.5}, "4": {"ari": 0.6}, "5": {"ari": 0.4}},
        a3_per_arity={"3": {"1": 0.9}, "4": {"1": 0.8}, "5": {"1": 0.7}},
        a2a3_dropped={"3": [], "4": [], "5": []},
    )
    result = verify_ac4_per_arity(root, n_seeds=27)
    assert result["pass"] is True
    assert result["a2_per_arity_keys"] == [3, 4, 5]
    assert result["missing_arities"] == []
    assert result["phantom_arities"] == []


def test_ac4_fails_on_missing_arity(tmp_path: Path) -> None:
    """Arity 4 absent → pass=False, missing_arities=[4] — TOOTH."""
    root = _write_seed_metrics_json(
        tmp_path,
        a2_per_arity={"3": {"ari": 0.5}, "5": {"ari": 0.4}},
        a3_per_arity={"3": {"1": 0.9}, "5": {"1": 0.7}},
        a2a3_dropped={"3": [], "5": []},
    )
    result = verify_ac4_per_arity(root, n_seeds=27)
    assert result["pass"] is False
    assert 4 in result["missing_arities"]


def test_ac4_fails_on_phantom_arity(tmp_path: Path) -> None:
    """Phantom arity 7 present → pass=False — TOOTH."""
    root = _write_seed_metrics_json(
        tmp_path,
        a2_per_arity={"3": {"ari": 0.5}, "4": {"ari": 0.6}, "5": {"ari": 0.4}, "7": {"ari": 0.1}},
        a3_per_arity={"3": {"1": 0.9}, "4": {"1": 0.8}, "5": {"1": 0.7}, "7": {"1": 0.5}},
        a2a3_dropped={"3": [], "4": [], "5": [], "7": []},
    )
    result = verify_ac4_per_arity(root, n_seeds=27)
    assert result["pass"] is False
    assert 7 in result["phantom_arities"]


def test_ac4_fails_when_cache_missing(tmp_path: Path) -> None:
    """Missing JSON cache → pass=False with error key."""
    result = verify_ac4_per_arity(tmp_path, n_seeds=27)
    assert result["pass"] is False
    assert "error" in result


# ---------------------------------------------------------------------------
# AC-H6 — verify_ac5_axis_coverage (teeth: arity shortfall, missing stats)
# ---------------------------------------------------------------------------


def _b_blocks_k3_k5() -> list[dict[str, Any]]:
    """Minimal block set with k∈{3,5}, n∈{8,16,24}, rho∈{1.0,2.0,4.0}."""
    return [
        {"block_key": "er_uniform_k3_n8_rho1", "n": 8, "k": 3, "density_ratio": 1.0},
        {"block_key": "er_uniform_k3_n8_rho2", "n": 8, "k": 3, "density_ratio": 2.0},
        {"block_key": "er_uniform_k3_n8_rho4", "n": 8, "k": 3, "density_ratio": 4.0},
        {"block_key": "er_uniform_k3_n16_rho1", "n": 16, "k": 3, "density_ratio": 1.0},
        {"block_key": "er_uniform_k3_n16_rho2", "n": 16, "k": 3, "density_ratio": 2.0},
        {"block_key": "er_uniform_k3_n16_rho4", "n": 16, "k": 3, "density_ratio": 4.0},
        {"block_key": "er_uniform_k3_n24_rho1", "n": 24, "k": 3, "density_ratio": 1.0},
        {"block_key": "er_uniform_k3_n24_rho2", "n": 24, "k": 3, "density_ratio": 2.0},
        {"block_key": "er_uniform_k5_n8_rho1", "n": 8, "k": 5, "density_ratio": 1.0},
        {"block_key": "er_uniform_k5_n8_rho2", "n": 8, "k": 5, "density_ratio": 2.0},
    ]


def _write_b_stats(stats_dir: Path, blocks: list[dict[str, Any]]) -> None:
    """Write minimal stats JSONs with valid CIs for each block."""
    stats_dir.mkdir(parents=True, exist_ok=True)
    for b in blocks:
        bkey = b["block_key"]
        payload = {
            "cell_key": bkey,
            "stratum": "b",
            "n_seeds": 27,
            "block_meta": {"n": b["n"], "k": b["k"], "density_ratio": b["density_ratio"]},
            "cis": {
                "isalhg_levenshtein::g1_a1::nu": {
                    "repr": "isalhg_levenshtein",
                    "metric": "g1_a1::nu",
                    "mean": 0.1,
                    "n_valid": 27,
                    "ci_lower": 0.09,
                    "ci_upper": 0.11,
                }
            },
            "wilcoxon": {},
        }
        (stats_dir / f"{bkey}_stats.json").write_text(json.dumps(payload))


def test_ac5_n_and_density_axes_ok(tmp_path: Path) -> None:
    """n-axis (3 values) and density-axis (3 values) satisfy ≥3."""
    blocks = _b_blocks_k3_k5()
    stats_dir = tmp_path / "stats"
    _write_b_stats(stats_dir, blocks)
    result = verify_ac5_axis_coverage(blocks, stats_dir)
    assert result["n_axis_ok"] is True
    assert sorted(result["n_values"]) == [8, 16, 24]
    assert result["density_axis_ok"] is True
    assert sorted(result["density_values"]) == [1.0, 2.0, 4.0]


def test_ac5_arity_axis_shortfall_does_not_block_pass(tmp_path: Path) -> None:
    """k∈{3,5} → arity_axis_ok=False, but overall pass is NOT gated on it — TOOTH.

    The task acceptance says to *state* the axis coverage.  The arity shortfall
    is a measured outcome (k=4 blocks timed out; k=7/10 were infeasible) and
    must not silently gate the harvest pass.
    """
    blocks = _b_blocks_k3_k5()
    stats_dir = tmp_path / "stats"
    _write_b_stats(stats_dir, blocks)
    result = verify_ac5_axis_coverage(blocks, stats_dir)
    # Arity axis only has k∈{3,5} = 2 distinct values.
    assert result["arity_axis_ok"] is False
    assert sorted(result["arity_values"]) == [3, 5]
    # But overall pass is True (n ≥ 3, density ≥ 3, all cells have CIs).
    assert result["pass"] is True
    # The note is populated.
    assert "Stratum B" in result["arity_axis_note"]


def test_ac5_fails_when_stats_file_missing(tmp_path: Path) -> None:
    """Missing stats file for one block → all_cells_have_ci=False, pass=False."""
    blocks = _b_blocks_k3_k5()
    stats_dir = tmp_path / "stats"
    # Write only 9 of 10 stats files.
    _write_b_stats(stats_dir, blocks[:-1])
    result = verify_ac5_axis_coverage(blocks, stats_dir)
    assert result["all_cells_have_ci"] is False
    assert result["pass"] is False


def test_ac5_fails_when_ci_nan(tmp_path: Path) -> None:
    """Stats file with NaN CIs → all_cells_have_ci=False, pass=False."""
    blocks = _b_blocks_k3_k5()
    stats_dir = tmp_path / "stats"
    # Write 9 correct + 1 NaN-CI file.
    _write_b_stats(stats_dir, blocks[:-1])
    bad_block = blocks[-1]
    bad_payload = {
        "cell_key": bad_block["block_key"],
        "stratum": "b",
        "n_seeds": 27,
        "block_meta": {},
        "cis": {
            "isalhg_levenshtein::g1_a1::nu": {
                "repr": "isalhg_levenshtein",
                "metric": "g1_a1::nu",
                "mean": float("nan"),
                "n_valid": 0,
                "ci_lower": float("nan"),
                "ci_upper": float("nan"),
            }
        },
        "wilcoxon": {},
    }
    (stats_dir / f"{bad_block['block_key']}_stats.json").write_text(json.dumps(bad_payload))
    result = verify_ac5_axis_coverage(blocks, stats_dir)
    assert result["all_cells_have_ci"] is False
    assert result["pass"] is False


# ---------------------------------------------------------------------------
# AC-H7 — summarise_census: has_non_terminal flag (Defect 1 regression)
# ---------------------------------------------------------------------------


def test_summarise_census_flags_non_terminal() -> None:
    """A RUNNING task sets has_non_terminal=True — TOOTH (Defect 1 regression).

    Before the fix, sacct was captured while task 70 was still RUNNING.
    ``summarise_census`` returned ``has_non_terminal=False`` because RUNNING is
    not in the terminal-state enumeration, causing the artifact to claim
    finality when the array had not settled.  This test fails if the non-terminal
    flag is missing or permanently False.
    """
    census_with_running = [
        {
            "task_idx": 0,
            "task_id": "j_0",
            "cell_key": "stratum_a",
            "dist_name": "isalhg_levenshtein",
            "state": "COMPLETED",
        },
        {
            "task_idx": 70,
            "task_id": "j_70",
            "cell_key": "er_uniform_k5_n8_rho2",
            "dist_name": "isalhg_levenshtein",
            "state": "RUNNING",
        },
    ]
    result = summarise_census(census_with_running)
    assert result["has_non_terminal"] is True, (
        "RUNNING task must set has_non_terminal=True; without this check the "
        "artifact falsely claims the census is terminal"
    )
    # The RUNNING task must appear in non_completed_tasks for traceability.
    assert any(e["state"] == "RUNNING" for e in result["non_completed_tasks"])


# ---------------------------------------------------------------------------
# AC-H8 — compute_harvest_decision (Defect 2 regression)
# ---------------------------------------------------------------------------


def _clean_ac(*, pass_: bool = True) -> dict:
    """Minimal passing AC dict (used for ac2/ac3/ac4 stubs)."""
    return {"pass": pass_}


def _ac5_with_arity(*, arity_axis_ok: bool) -> dict:
    """Minimal AC5 dict with controllable arity_axis_ok."""
    return {
        "pass": True,
        "n_axis_ok": True,
        "density_axis_ok": True,
        "arity_axis_ok": arity_axis_ok,
        "all_cells_have_ci": True,
        "n_values": [8, 16, 24],
        "density_values": [1.0, 2.0, 4.0],
        "arity_values": [3, 5],
        "arity_axis_note": "Stratum B arity axis has only 2 points (k∈{3,5}).",
    }


def _terminal_census() -> dict:
    """Minimal census_summary with no non-terminal tasks."""
    return {
        "total": 77,
        "completed": 74,
        "timeout": 3,
        "failed": 0,
        "oom": 0,
        "other": 0,
        "non_completed_tasks": [],
        "has_non_terminal": False,
    }


def test_compute_decision_arity_axis_shortfall() -> None:
    """arity_axis_ok=False → shortfalls=['ac5_arity_axis'], all_pass=False — TOOTH (Defect 2).

    Before the fix, ``all_acceptance_pass: true`` was written even when
    ``ac5_axis_coverage.arity_axis_ok`` was ``false``.  This test fails against
    the old ``all_pass = ac2[...] and ac3[...] and ac4[...] and ac5["pass"]``
    logic (ac5["pass"] is True even when arity_axis_ok is False).
    """
    ac5 = _ac5_with_arity(arity_axis_ok=False)
    # ac5["pass"] is True here — that is the old logic's blind spot.
    assert ac5["pass"] is True, "Precondition: ac5.pass must be True for the tooth to bite"

    all_pass, shortfalls = compute_harvest_decision(
        _clean_ac(),
        _clean_ac(),
        _clean_ac(),
        ac5,
        _terminal_census(),
    )
    assert all_pass is False, "arity_axis_ok=False must make all_acceptance_pass=False"
    assert "ac5_arity_axis" in shortfalls


def test_compute_decision_non_terminal_census() -> None:
    """has_non_terminal=True → shortfalls contain census_non_terminal — TOOTH (Defect 1)."""
    non_terminal_census = dict(_terminal_census())
    non_terminal_census["has_non_terminal"] = True

    all_pass, shortfalls = compute_harvest_decision(
        _clean_ac(),
        _clean_ac(),
        _clean_ac(),
        _ac5_with_arity(arity_axis_ok=True),
        non_terminal_census,
    )
    assert all_pass is False
    assert "census_non_terminal" in shortfalls


def test_compute_decision_clean_all_pass() -> None:
    """All sub-checks pass and no shortfalls → all_pass=True, shortfalls=[]."""
    all_pass, shortfalls = compute_harvest_decision(
        _clean_ac(),
        _clean_ac(),
        _clean_ac(),
        _ac5_with_arity(arity_axis_ok=True),
        _terminal_census(),
    )
    assert all_pass is True
    assert shortfalls == []


# ---------------------------------------------------------------------------
# AC-H9 — verify_multi_rep_wilcoxon_populated (T-M7t regression)
# ---------------------------------------------------------------------------


def _ci_row(repr_name: str, metric: str = "g1_a1::nu") -> dict[str, Any]:
    """Minimal CIs row for one (repr, metric) pair."""
    return {
        "repr": repr_name,
        "metric": metric,
        "mean": 0.1,
        "n_valid": 27,
        "ci_lower": 0.08,
        "ci_upper": 0.12,
    }


def test_multi_rep_wilcoxon_populated_fails_on_empty_wilcoxon() -> None:
    """CellStats with ≥2 representations but empty wilcoxon → pass=False — TOOTH.

    This is the pre-fix state produced by the S=27 SLURM array: each task
    processed one representation at a time, so ``aggregate_cell_stats`` never
    had both PRIMARY_REPR and a competitor in memory, and the Wilcoxon/Holm
    block never fired.  The on-disk stats files had ``cis`` populated from one
    dist but ``wilcoxon: {}``.  This test fails against that pre-fix state.
    """
    pre_fix_state = _FakeCellStats(
        cell_key="stratum_a",
        cis={
            "isalhg_levenshtein::g1_a1::nu": _ci_row("isalhg_levenshtein"),
            "hypergraph_wl_l1::g1_a1::nu": _ci_row("hypergraph_wl_l1"),
        },
        wilcoxon={},
    )
    result = verify_multi_rep_wilcoxon_populated(pre_fix_state)
    assert result["pass"] is False, (
        "≥2 representations with empty wilcoxon must fail; "
        "this is exactly the pipeline bug T-M7t was filed to fix"
    )
    assert result["wilcoxon_empty"] is True
    assert result["n_reps"] == 2


def test_multi_rep_wilcoxon_populated_passes_when_wilcoxon_present() -> None:
    """CellStats with ≥2 representations AND non-empty wilcoxon → pass=True."""
    fixed_state = _FakeCellStats(
        cell_key="stratum_a",
        cis={
            "isalhg_levenshtein::g1_a1::nu": _ci_row("isalhg_levenshtein"),
            "hypergraph_wl_l1::g1_a1::nu": _ci_row("hypergraph_wl_l1"),
        },
        wilcoxon={
            "hypergraph_wl_l1::g1_a1::nu": {
                "repr": "hypergraph_wl_l1",
                "metric": "g1_a1::nu",
                "p_holm": 0.03,
                "effect_size": 0.4,
                "median_diff": 0.05,
                "n_pairs": 27,
            }
        },
    )
    result = verify_multi_rep_wilcoxon_populated(fixed_state)
    assert result["pass"] is True
    assert result["wilcoxon_empty"] is False


def test_multi_rep_wilcoxon_populated_passes_single_rep() -> None:
    """Single-representation CellStats with empty wilcoxon is not a bug."""
    single_rep = _FakeCellStats(
        cell_key="stratum_a",
        cis={"isalhg_levenshtein::g1_a1::nu": _ci_row("isalhg_levenshtein")},
        wilcoxon={},
    )
    result = verify_multi_rep_wilcoxon_populated(single_rep)
    # One rep → wilcoxon legitimately empty (no competitor to pair against).
    assert result["pass"] is True
    assert result["n_reps"] == 1


# ---------------------------------------------------------------------------
# AC-H10 — verify_excluded_cells_no_isalhg_comparison (T-M7t regression)
# ---------------------------------------------------------------------------


def test_excluded_cell_no_isalhg_comparison_fails_when_wilcoxon_nonempty() -> None:
    """Excluded cell with non-empty wilcoxon → violations detected — TOOTH.

    The three Stratum B cells where isalhg_levenshtein timed out must carry no
    wilcoxon entries.  If PRIMARY_REPR were accidentally re-included in their
    dist_names, the aggregate would emit entries from partial (< 27 seeds) data,
    violating the whole-cell exclusion policy.  This test fails against that
    scenario.
    """
    excluded = {"er_uniform_k3_n16_rho4"}
    bug_state: dict[str, Any] = {
        "er_uniform_k3_n16_rho4": _FakeCellStats(
            cell_key="er_uniform_k3_n16_rho4",
            wilcoxon={
                "hypergraph_wl_l1::g1_a1::nu": {
                    "repr": "hypergraph_wl_l1",
                    "metric": "g1_a1::nu",
                    "p_holm": 0.04,
                    "effect_size": 0.3,
                    "median_diff": 0.1,
                    "n_pairs": 18,
                }
            },
        )
    }
    result = verify_excluded_cells_no_isalhg_comparison(bug_state, excluded)
    assert result["pass"] is False, (
        "A wilcoxon entry for an excluded (timeout) cell must be flagged; "
        "partial seed data (18/27 seeds) must not be used"
    )
    assert "er_uniform_k3_n16_rho4" in result["violations"]


def test_excluded_cell_no_isalhg_comparison_passes_when_wilcoxon_empty() -> None:
    """Excluded cell with empty wilcoxon → no violations (correct exclusion)."""
    excluded = {"er_uniform_k3_n16_rho4"}
    correct_state: dict[str, Any] = {
        "er_uniform_k3_n16_rho4": _FakeCellStats(
            cell_key="er_uniform_k3_n16_rho4",
            cis={
                "hypergraph_wl_l1::g1_a1::nu": _ci_row("hypergraph_wl_l1"),
            },
            wilcoxon={},
        )
    }
    result = verify_excluded_cells_no_isalhg_comparison(correct_state, excluded)
    assert result["pass"] is True
    assert result["violations"] == []


def test_excluded_cell_no_isalhg_comparison_non_excluded_cell_ignored() -> None:
    """Non-excluded cells with wilcoxon entries are not flagged."""
    excluded: set[str] = {"er_uniform_k3_n16_rho4"}
    non_excluded_state: dict[str, Any] = {
        "er_uniform_k3_n8_rho1": _FakeCellStats(
            cell_key="er_uniform_k3_n8_rho1",
            wilcoxon={
                "hypergraph_wl_l1::g1_a1::nu": {
                    "repr": "hypergraph_wl_l1",
                    "metric": "g1_a1::nu",
                    "p_holm": 0.01,
                    "effect_size": 0.5,
                    "median_diff": 0.2,
                    "n_pairs": 27,
                }
            },
        )
    }
    result = verify_excluded_cells_no_isalhg_comparison(non_excluded_state, excluded)
    assert result["pass"] is True
    assert result["violations"] == []


# ---------------------------------------------------------------------------
# AC-H11 — reverse direction labels (T-M7t coordinator addition)
# ---------------------------------------------------------------------------


def test_ac3_fails_on_missing_reverse_direction() -> None:
    """Entry without a ``reverse`` sub-dict → missing_reverse non-empty, pass=False — TOOTH.

    Before the coordinator addition, verify_ac3_wilcoxon_coverage only checked
    for ``p_holm`` and ``effect_size`` in the forward direction.  A forward-only
    entry was therefore accepted as complete.  But the article must cite BOTH
    directions: a ``p_holm = 1.0`` from the forward test cannot be cited to say
    the competitor beats IsalHG — that requires the reverse test's corrected p.
    This test fails against the pre-addition verifier.
    """
    cs = _FakeCellStats()
    cs.wilcoxon = dict(
        [
            _make_wilcoxon_entry(
                "degree_seq_l1",
                "a2::ari",
                include_reverse=False,  # forward-only: pre-addition bug state
            ),
        ]
    )
    result = verify_ac3_wilcoxon_coverage(cs)
    assert result["pass"] is False, (
        "Forward-only entry (no 'reverse' sub-dict) must be rejected; "
        "losses cannot be cited without the competitor_greater corrected p"
    )
    assert "degree_seq_l1::a2::ari" in result["missing_reverse"]


def test_ac3_fails_on_missing_alternative_label() -> None:
    """Entry without an ``alternative`` field → mislabelled non-empty, pass=False — TOOTH.

    Direction ambiguity: a bare ``p_holm`` with no ``alternative`` field cannot
    be attributed to either direction six months later.  This test fails against
    the pre-addition verifier (which did not require direction labels).
    """
    cs = _FakeCellStats()
    cs.wilcoxon = dict(
        [
            _make_wilcoxon_entry(
                "netlsd_l2",
                "a2::ari",
                include_alternative=False,  # no direction label: pre-addition bug state
            ),
        ]
    )
    result = verify_ac3_wilcoxon_coverage(cs)
    assert result["pass"] is False, (
        "Entry without 'alternative' field must be rejected; "
        "a bare p_holm is unattributable to a direction"
    )
    assert "netlsd_l2::a2::ari" in result["mislabelled"]
