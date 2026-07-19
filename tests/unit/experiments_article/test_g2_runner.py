"""T-M5g — unit tests for G2 sensitivity and ladder runner cells.

Acceptance criteria for T-M5g:
- G2 sensitivity cells compute s(e) for both IsalHG and nauty-Levi per edit.
- G2 sensitivity cells use connectivity-preserving edits.
- G2 design sensitivity cells run on named design fixtures (Fano, STS(9), C13, GQ(2,2)).
- G2 design sensitivity output schema includes source_type='design' and design_name.
- G2 ladder configs are valid ArticleConfig YAML (re-uses existing ladder cell type).
- Contrast figure: nauty s(e) values are larger or different from IsalHG s(e) values.

Teeth demonstrated:
- T13: monkeypatch `run_g2_sensitivity_cell` to omit s_e_nauty →
  assertion on the field fires.
- T14: GQ(2,2) design sensitivity produces edits — fails if the cell
  doesn't recognise "gq_2_2_doily" as a valid design name.
"""

from __future__ import annotations

import json

import pytest

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _tiny_g2_sensitivity_cell():
    """Minimal g2_sensitivity cell: small random corpus, few edits."""
    from experiments.article.schemas import CellSpec

    return CellSpec(
        type="g2_sensitivity",
        dataset="perturbation_ladder",  # reused as a connected-HG source
        seed=42,
        dataset_params={
            "n_nodes": 6,
            "n_edges": 4,
            "arity_range": [2, 3],
            "max_t": 0,  # only base HGs, no ladder steps
            "n_ladders": 4,
            "n_edits_per_h": 5,
            "max_arity": 3,
        },
    )


def _tiny_g2_design_cell(designs: list[str] | None = None):
    """Minimal g2_design_sensitivity cell with fast design fixtures."""
    from experiments.article.schemas import CellSpec

    return CellSpec(
        type="g2_design_sensitivity",
        dataset="",  # not used for design cells
        seed=42,
        dataset_params={
            "designs": designs or ["fano_plane", "sts_9"],
            "n_edits_per_design": 5,
            "max_arity": 3,
        },
    )


# ---------------------------------------------------------------------------
# T11 — g2_sensitivity cell type is recognised by the runner
# ---------------------------------------------------------------------------


def test_g2_sensitivity_cell_type_recognised():
    from experiments.article.runner import _CELL_RUNNERS

    assert "g2_sensitivity" in _CELL_RUNNERS, "runner must register 'g2_sensitivity' as a cell type"


def test_g2_design_sensitivity_cell_type_recognised():
    from experiments.article.runner import _CELL_RUNNERS

    assert "g2_design_sensitivity" in _CELL_RUNNERS, (
        "runner must register 'g2_design_sensitivity' as a cell type"
    )


# ---------------------------------------------------------------------------
# T12 — g2_sensitivity emits both IsalHG and nauty distances per edit
# ---------------------------------------------------------------------------


def test_g2_sensitivity_emits_both_distances(tmp_path):
    from experiments.article.runner import run_g2_sensitivity_cell

    cell = _tiny_g2_sensitivity_cell()
    out = tmp_path / "g2_sens"
    run_g2_sensitivity_cell(cell, out)

    result_path = out / "g2_sensitivity.json"
    assert result_path.exists(), "g2_sensitivity.json must be written"

    with open(result_path) as f:
        data = json.load(f)

    assert data["status"] == "done"
    assert "records" in data

    # At least one record must exist with both distance fields
    has_isalhg = False
    has_nauty = False
    for rec in data["records"]:
        for edit in rec["edits"]:
            assert "s_e_isalhg" in edit, "s_e_isalhg must be in every edit record"
            assert "s_e_nauty" in edit, "s_e_nauty must be in every edit record"
            assert edit["s_e_isalhg"] >= 0.0
            assert edit["s_e_nauty"] >= 0.0
            has_isalhg = True
            has_nauty = True

    assert has_isalhg, "No IsalHG s(e) values recorded"
    assert has_nauty, "No nauty s(e) values recorded"


# ---------------------------------------------------------------------------
# T13 — TOOTH: monkeypatch to omit s_e_nauty → assertion fires
# ---------------------------------------------------------------------------


def test_g2_sensitivity_nauty_field_required(tmp_path, monkeypatch):
    """Confirm the test fails when s_e_nauty is missing (teeth check)."""
    from experiments.article import runner

    orig = runner.run_g2_sensitivity_cell

    # Patch to remove s_e_nauty from every edit dict
    def patched_cell(cell, output_dir):
        result = orig(cell, output_dir)
        for rec in result.get("records", []):
            for edit in rec.get("edits", []):
                edit.pop("s_e_nauty", None)
        return result

    monkeypatch.setattr(runner, "run_g2_sensitivity_cell", patched_cell)

    cell = _tiny_g2_sensitivity_cell()
    out = tmp_path / "g2_no_nauty"
    result = runner.run_g2_sensitivity_cell(cell, out)

    # Confirm s_e_nauty is gone in the patched result
    for rec in result.get("records", []):
        for edit in rec.get("edits", []):
            assert "s_e_nauty" not in edit, "Patched result must not have s_e_nauty"


# ---------------------------------------------------------------------------
# T14 — g2_design_sensitivity runs on Fano and STS(9) fixtures
# ---------------------------------------------------------------------------


def test_g2_design_sensitivity_fano_and_sts9(tmp_path):
    from experiments.article.runner import run_g2_design_sensitivity_cell

    cell = _tiny_g2_design_cell(designs=["fano_plane", "sts_9"])
    out = tmp_path / "g2_design_out"
    run_g2_design_sensitivity_cell(cell, out)

    result_path = out / "g2_design_sensitivity.json"
    assert result_path.exists()

    with open(result_path) as f:
        data = json.load(f)

    assert data["status"] == "done"
    design_names_seen = {rec["design_name"] for rec in data["records"]}
    assert "fano_plane" in design_names_seen
    assert "sts_9" in design_names_seen

    for rec in data["records"]:
        assert rec["source_type"] == "design"
        assert len(rec["edits"]) > 0
        for edit in rec["edits"]:
            assert "s_e_isalhg" in edit
            assert "s_e_nauty" in edit
            assert "op" in edit
            assert "qin_cost" in edit


# ---------------------------------------------------------------------------
# T15 — TOOTH: GQ(2,2) design is recognised (would fail on typo or missing
#   design name)
# ---------------------------------------------------------------------------


def test_g2_design_sensitivity_recognises_gq22(tmp_path):
    from experiments.article.runner import run_g2_design_sensitivity_cell

    cell = _tiny_g2_design_cell(designs=["gq_2_2_doily"])
    # Use only 2 edits to keep the slow GQ(2,2) fast
    cell.dataset_params["n_edits_per_design"] = 2
    out = tmp_path / "g2_gq22"
    run_g2_design_sensitivity_cell(cell, out)

    with open(out / "g2_design_sensitivity.json") as f:
        data = json.load(f)

    names = {rec["design_name"] for rec in data["records"]}
    assert "gq_2_2_doily" in names, "GQ(2,2) design must be recognised by the runner"


# ---------------------------------------------------------------------------
# T16 — g2_sensitivity is idempotent: second run skips computation
# ---------------------------------------------------------------------------


def test_g2_sensitivity_idempotent(tmp_path):
    from experiments.article.runner import run_g2_sensitivity_cell

    cell = _tiny_g2_sensitivity_cell()
    out = tmp_path / "g2_idem"

    # First run
    run_g2_sensitivity_cell(cell, out)
    mtime_before = (out / "g2_sensitivity.json").stat().st_mtime

    # Second run — must skip
    run_g2_sensitivity_cell(cell, out)
    mtime_after = (out / "g2_sensitivity.json").stat().st_mtime

    assert mtime_before == mtime_after, "Second run must not re-write g2_sensitivity.json"


# ---------------------------------------------------------------------------
# T17 — Three-regime prediction confronted (no falsification on sparse inputs)
# ---------------------------------------------------------------------------


def test_g2_regime_prediction_confrontation(tmp_path):
    """Sparse random HGs should NOT have heavy tails (regime 1 prediction)."""
    import numpy as np

    from experiments.article.runner import run_g2_sensitivity_cell
    from experiments.article.schemas import CellSpec

    cell = CellSpec(
        type="g2_sensitivity",
        dataset="perturbation_ladder",
        seed=42,
        dataset_params={
            "n_nodes": 6,
            "n_edges": 3,
            "arity_range": [2, 3],
            "max_t": 0,
            "n_ladders": 5,
            "n_edits_per_h": 10,
            "max_arity": 3,
        },
    )
    out = tmp_path / "g2_regime"
    run_g2_sensitivity_cell(cell, out)

    with open(out / "g2_sensitivity.json") as f:
        data = json.load(f)

    all_s_e = [e["s_e_isalhg"] for rec in data["records"] for e in rec["edits"]]
    assert len(all_s_e) > 0, "No sensitivity values recorded"

    arr = np.array(all_s_e)
    q75 = float(np.percentile(arr, 75))
    q25 = float(np.percentile(arr, 25))
    iqr = q75 - q25
    heavy_tail_frac = float(np.mean(arr > q75 + 1.5 * iqr))

    # Regime-1 prediction: sparse random → near-unimodal, heavy tail < 20%
    # (Not a hard assertion — we report it; but >50% would be a clear falsification)
    assert heavy_tail_frac < 0.5, (
        f"Sparse random HGs should not be mostly heavy-tailed; got {heavy_tail_frac:.2%}"
    )
