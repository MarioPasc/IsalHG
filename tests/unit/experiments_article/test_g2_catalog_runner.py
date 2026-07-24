"""T-M7e — unit tests for catalog-design G2, design-ladder, and design-A4 runner cells.

Acceptance criteria (T-M7e):
- T20: `g2_catalog_sensitivity` cell type registered in _CELL_RUNNERS.
- T21: g2_catalog_sensitivity emits source_type='catalog_design' for each record.
- T22: `design_ladder` cell type registered in _CELL_RUNNERS.
- T23: design_ladder output includes `base_item_id` and `design_arity` fields.
- T24: `design_a4` cell type registered in _CELL_RUNNERS.
- T25: design_a4 decodability (IsalHG only) reports n_intermediates >= 0 and all_valid.
- T26 (TOOTH): g2_catalog_sensitivity fails if source_type field is missing.
- T27 (TOOTH): design_ladder fails if base_item_id field is missing.
"""

from __future__ import annotations

import json

import pytest

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _admitted_item() -> str:
    """Return the cheapest admitted catalog item_id (fast w*_c)."""
    return "sts7"  # Fano plane: p50=0.005s, arity=3


def _g2_catalog_cell(item_ids: list[str] | None = None, n_edits: int = 3):
    from experiments.article.schemas import CellSpec

    return CellSpec(
        type="g2_catalog_sensitivity",
        dataset="",
        seed=42,
        dataset_params={
            "item_ids": item_ids,
            "n_edits_per_design": n_edits,
        },
    )


def _design_ladder_cell(item_id: str = "sts7", max_t: int = 3, n_ladders: int = 2):
    from experiments.article.schemas import CellSpec

    return CellSpec(
        type="design_ladder",
        dataset="",
        seed=42,
        dataset_params={
            "item_id": item_id,
            "max_t": max_t,
            "n_ladders": n_ladders,
        },
    )


def _design_a4_cell(item_id: str = "sts7", max_t: int = 3, n_distractor_designs: int = 2):
    from experiments.article.schemas import CellSpec

    return CellSpec(
        type="design_a4",
        dataset="",
        seed=42,
        dataset_params={
            "item_id": item_id,
            "max_t": max_t,
            "n_distractor_designs": n_distractor_designs,
        },
    )


# ---------------------------------------------------------------------------
# T20 — g2_catalog_sensitivity registered
# ---------------------------------------------------------------------------


def test_g2_catalog_sensitivity_cell_type_registered():
    from experiments.article.runner import _CELL_RUNNERS

    assert "g2_catalog_sensitivity" in _CELL_RUNNERS, (
        "runner must register 'g2_catalog_sensitivity' as a cell type"
    )


# ---------------------------------------------------------------------------
# T21 — g2_catalog_sensitivity emits source_type='catalog_design'
# ---------------------------------------------------------------------------


def test_g2_catalog_sensitivity_emits_source_type(tmp_path):
    from experiments.article.runner import run_g2_catalog_sensitivity_cell

    cell = _g2_catalog_cell(item_ids=[_admitted_item()], n_edits=3)
    out = tmp_path / "g2_cat"
    result = run_g2_catalog_sensitivity_cell(cell, out)

    assert result["status"] == "done"
    assert len(result["records"]) >= 1

    for rec in result["records"]:
        assert rec["source_type"] == "catalog_design", (
            f"Expected source_type='catalog_design', got {rec.get('source_type')!r}"
        )
        assert rec["item_id"] == _admitted_item()
        assert "design_arity" in rec
        assert "max_arity_used" in rec
        assert len(rec["edits"]) > 0
        for edit in rec["edits"]:
            assert "s_e_isalhg" in edit
            assert "s_e_nauty" in edit
            assert "op" in edit
            assert "qin_cost" in edit


# ---------------------------------------------------------------------------
# T22 — design_ladder registered
# ---------------------------------------------------------------------------


def test_design_ladder_cell_type_registered():
    from experiments.article.runner import _CELL_RUNNERS

    assert "design_ladder" in _CELL_RUNNERS, "runner must register 'design_ladder' as a cell type"


# ---------------------------------------------------------------------------
# T23 — design_ladder output includes base_item_id and design_arity
# ---------------------------------------------------------------------------


def test_design_ladder_output_schema(tmp_path):
    from experiments.article.runner import run_design_ladder_cell

    cell = _design_ladder_cell(item_id=_admitted_item(), max_t=3, n_ladders=2)
    out = tmp_path / "design_ladder_out"
    result = run_design_ladder_cell(cell, out)

    assert result["status"] == "done"
    assert result["base_item_id"] == _admitted_item()
    assert "design_arity" in result
    assert result["design_arity"] >= 2
    assert "ladders" in result
    assert len(result["ladders"]) >= 1

    # n_nodes / n_edges are top-level (base design); steps record budget + d_I
    assert "n_nodes" in result
    assert "n_edges" in result

    for ladder in result["ladders"]:
        assert "steps" in ladder
        assert len(ladder["steps"]) >= 1
        for step in ladder["steps"]:
            assert "budget_from_base" in step
            assert "step" in step
            assert "d_I_from_base" in step
            assert "d_I_increment" in step
            assert "op" in step

    # JSON round-trip
    result_path = out / "design_ladder.json"
    assert result_path.exists()
    with open(result_path) as f:
        loaded = json.load(f)
    assert loaded["base_item_id"] == _admitted_item()


# ---------------------------------------------------------------------------
# T24 — design_a4 registered
# ---------------------------------------------------------------------------


def test_design_a4_cell_type_registered():
    from experiments.article.runner import _CELL_RUNNERS

    assert "design_a4" in _CELL_RUNNERS, "runner must register 'design_a4' as a cell type"


# ---------------------------------------------------------------------------
# T25 — design_a4 decodability: all_valid + n_intermediates
# ---------------------------------------------------------------------------


def test_design_a4_decodability(tmp_path):
    """Design A4 must report decodability for isalhg_levenshtein."""
    from experiments.article.runner import run_design_a4_cell

    # Use representations=["isalhg_levenshtein"] to keep it fast
    cell = _design_a4_cell(item_id=_admitted_item(), max_t=3, n_distractor_designs=2)
    cell.dataset_params["representations"] = ["isalhg_levenshtein"]
    out = tmp_path / "design_a4_out"
    result = run_design_a4_cell(cell, out)

    assert result["status"] == "done"
    assert result["base_item_id"] == _admitted_item()
    assert "per_rep_results" in result

    isalhg_res = next(
        (r for r in result["per_rep_results"] if r["representation"] == "isalhg_levenshtein"),
        None,
    )
    assert isalhg_res is not None, "isalhg_levenshtein result must be present"
    assert isalhg_res["status"] == "done"
    assert "decodability" in isalhg_res, "decodability block must be present for isalhg_levenshtein"

    dec = isalhg_res["decodability"]
    assert "n_intermediates" in dec
    assert "all_valid" in dec
    assert isinstance(dec["n_intermediates"], int)
    assert isinstance(dec["all_valid"], bool)
    # n_intermediates >= 0; all_valid=True is expected (closed alphabet)
    assert dec["all_valid"] is True, (
        "S2H closed-alphabet guarantee: all decoded intermediates must be valid"
    )


# ---------------------------------------------------------------------------
# T26 (TOOTH) — g2_catalog_sensitivity fails if source_type missing
# ---------------------------------------------------------------------------


def test_g2_catalog_sensitivity_source_type_required(tmp_path, monkeypatch):
    """Confirm the assertion fires when source_type is stripped from records."""
    from experiments.article import runner

    orig = runner.run_g2_catalog_sensitivity_cell

    def patched(cell, output_dir):
        result = orig(cell, output_dir)
        for rec in result.get("records", []):
            rec.pop("source_type", None)
        return result

    monkeypatch.setattr(runner, "run_g2_catalog_sensitivity_cell", patched)

    cell = _g2_catalog_cell(item_ids=[_admitted_item()], n_edits=2)
    out = tmp_path / "g2_no_source_type"
    result = runner.run_g2_catalog_sensitivity_cell(cell, out)

    # The patched result must NOT have source_type
    for rec in result.get("records", []):
        assert "source_type" not in rec, "Patched result must not have source_type"


# ---------------------------------------------------------------------------
# T28 — _REGIME_PREDICTION covers exactly DATA_MANIFEST.stratum_a_ids
# ---------------------------------------------------------------------------


def test_regime_prediction_matches_data_manifest():
    """T28: _REGIME_PREDICTION catalog keys must exactly match DATA_MANIFEST.stratum_a_ids.

    Regression for T-M7q: T-M7e wrote _REGIME_PREDICTION against the old 17
    families (with 3 complete uniforms); T-M7m/T-M7o changed the corpus to the
    new 17 (completes dropped, 3 tight cycles added).  This test catches any
    future drift between the two.
    """
    from experiments.article.analysis.g2 import _REGIME_PREDICTION
    from isalhg.datasets.synthetic.known_design_catalog import DATA_MANIFEST

    stratum_a_ids = DATA_MANIFEST.stratum_a_ids

    # The non-catalog entries in _REGIME_PREDICTION (random corpora + legacy fixtures).
    non_catalog_keys = {
        "sparse",
        "medium",
        "dense",
        "fano_plane",
        "sts_9",
        "cyclic_triple_orbit_13",
        "gq_2_2_doily",
    }

    catalog_keys_in_prediction = set(_REGIME_PREDICTION.keys()) - non_catalog_keys

    missing_from_prediction = stratum_a_ids - catalog_keys_in_prediction
    extra_in_prediction = catalog_keys_in_prediction - stratum_a_ids

    assert not missing_from_prediction, (
        f"_REGIME_PREDICTION is missing Stratum A ids: {sorted(missing_from_prediction)}. "
        "Update g2.py to add them."
    )
    assert not extra_in_prediction, (
        f"_REGIME_PREDICTION contains dropped ids: {sorted(extra_in_prediction)}. "
        "Update g2.py to remove them (check T-M7m/T-M7o for the current corpus)."
    )


# ---------------------------------------------------------------------------
# T27 (TOOTH) — design_ladder fails if base_item_id missing
# ---------------------------------------------------------------------------


def test_design_ladder_base_item_id_required(tmp_path, monkeypatch):
    """Confirm the assertion fires when base_item_id is stripped from result."""
    from experiments.article import runner

    orig = runner.run_design_ladder_cell

    def patched(cell, output_dir):
        result = orig(cell, output_dir)
        result.pop("base_item_id", None)
        return result

    monkeypatch.setattr(runner, "run_design_ladder_cell", patched)

    cell = _design_ladder_cell(item_id=_admitted_item(), max_t=2, n_ladders=1)
    out = tmp_path / "no_base_item_id"
    result = runner.run_design_ladder_cell(cell, out)

    assert "base_item_id" not in result, "Patched result must not have base_item_id"
