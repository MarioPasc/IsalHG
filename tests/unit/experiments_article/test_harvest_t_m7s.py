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

Teeth (tests observed failing before fix / against wrong data):
- test_ac2_fails_on_nan_ci: fails if NaN CIs are accepted as valid.
- test_ac2_fails_on_empty_cis: fails if empty CI dict returns pass=True.
- test_ac3_fails_on_missing_p_holm: fails if missing p_holm is accepted.
- test_ac3_fails_on_empty_wilcoxon: fails if empty Wilcoxon returns pass=True.
- test_ac4_fails_on_missing_arity: fails if arity 4 is absent.
- test_ac4_fails_on_phantom_arity: fails if phantom arity 7 appears.
- test_ac5_arity_axis_shortfall_does_not_block_pass: k∈{3,5} alone does NOT
  trigger pass=False (the arity_axis_note records the shortfall).
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
    parse_sacct_tsv,
    summarise_census,
    verify_ac2_ci_coverage,
    verify_ac3_wilcoxon_coverage,
    verify_ac4_per_arity,
    verify_ac5_axis_coverage,
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
    dist: str, metric: str, *, p_holm: float | None = 0.03, effect_size: float | None = 0.4
) -> tuple[str, dict[str, Any]]:
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
    return f"{dist}::{metric}", row


def test_ac3_passes_on_complete_wilcoxon() -> None:
    """All entries have p_holm and effect_size → pass=True."""
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
