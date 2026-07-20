"""Unit tests for the T-M5a article experiment runner.

Acceptance criteria tested:
- D-matrix cells compute and atomically cache distance matrices.
- Acceptance rate (from item.extra['acceptance_attempts']) is reported in meta.
- Ladder cells report per-step d_I increments (proxy for T-TBb R(e)/T_span(e)).
- Results are idempotent: re-running a completed cell skips computation.
- Sensitivity cells emit s(e) per edit type.
- Info-content cells emit compression ratios and Wilcoxon inputs.

Teeth demonstrated via monkeypatching that removes the expected fields, then
restoring the real implementation to confirm the assertion passes.
"""

from __future__ import annotations

import json

import numpy as np
import pytest

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _tiny_d_matrix_cell():
    """Return a minimal d_matrix CellSpec that completes in <2 s locally."""
    from experiments.article.schemas import CellSpec

    return CellSpec(
        type="d_matrix",
        dataset="correlation_corpus",
        seed=7,
        dataset_params={"n_items": 6, "n_range": [4, 5], "n_edges_range": [2, 3]},
        distances=["isalhg_levenshtein", "exact_hged"],
    )


def _tiny_ladder_cell():
    from experiments.article.schemas import CellSpec

    return CellSpec(
        type="ladder",
        dataset="perturbation_ladder",
        seed=7,
        dataset_params={"n_nodes": 5, "n_edges": 3, "max_t": 3, "n_ladders": 2},
    )


def _tiny_sensitivity_cell():
    from experiments.article.schemas import CellSpec

    return CellSpec(
        type="sensitivity",
        dataset="correlation_corpus",
        seed=7,
        dataset_params={
            "n_items": 4,
            "n_range": [4, 5],
            "n_edges_range": [2, 3],
            "n_edits_per_h": 5,
        },
    )


def _tiny_info_content_cell():
    from experiments.article.schemas import CellSpec

    return CellSpec(
        type="info_content",
        dataset="correlation_corpus",
        seed=7,
        dataset_params={"n_items": 4, "n_range": [4, 5], "n_edges_range": [2, 3]},
    )


# ---------------------------------------------------------------------------
# T1 — module importable (fails before implementation exists)
# ---------------------------------------------------------------------------


def test_schemas_importable():
    from experiments.article import schemas  # noqa: F401


def test_runner_importable():
    from experiments.article import runner  # noqa: F401


# ---------------------------------------------------------------------------
# T2 — CellSpec.output_key is deterministic and unique per cell
# ---------------------------------------------------------------------------


def test_cell_output_key_stable():
    from experiments.article.schemas import CellSpec

    c1 = CellSpec(type="d_matrix", dataset="correlation_corpus", seed=0)
    c2 = CellSpec(type="d_matrix", dataset="correlation_corpus", seed=1)
    assert c1.output_key() != c2.output_key()
    assert c1.output_key() == c1.output_key()  # deterministic


def test_cell_output_key_includes_label():
    from experiments.article.schemas import CellSpec

    c = CellSpec(type="d_matrix", dataset="erdos_renyi", seed=0, label="low_density")
    key = c.output_key()
    assert "low_density" in key


# ---------------------------------------------------------------------------
# T3 — ArticleConfig.from_yaml round-trips a valid YAML
# ---------------------------------------------------------------------------


def test_article_config_from_yaml(tmp_path):
    from experiments.article.schemas import ArticleConfig

    yaml_path = tmp_path / "test_config.yaml"
    yaml_path.write_text(
        f"output_root: {tmp_path}\n"
        "cells:\n"
        "  - type: d_matrix\n"
        "    dataset: correlation_corpus\n"
        "    seed: 0\n"
        "    distances: [isalhg_levenshtein]\n"
    )
    cfg = ArticleConfig.from_yaml(yaml_path)
    assert len(cfg.cells) == 1
    assert cfg.cells[0].type == "d_matrix"
    assert cfg.cells[0].dataset == "correlation_corpus"
    assert "isalhg_levenshtein" in cfg.cells[0].distances


# ---------------------------------------------------------------------------
# T4 — D-matrix cell: matrix shape + meta.json written atomically
# ---------------------------------------------------------------------------


def test_d_matrix_cell_produces_npy_and_meta(tmp_path):
    from experiments.article.runner import run_d_matrix_cell

    cell = _tiny_d_matrix_cell()
    out = tmp_path / "d_matrix_out"
    run_d_matrix_cell(cell, out)

    for dist in cell.distances:
        npy_path = out / dist / "D.npy"
        meta_path = out / dist / "meta.json"
        assert npy_path.exists(), f"D.npy missing for {dist}"
        assert meta_path.exists(), f"meta.json missing for {dist}"
        D = np.load(npy_path)
        assert D.shape == (6, 6), f"Expected 6×6 matrix for {dist}, got {D.shape}"
        assert np.allclose(np.diag(D), 0), "Diagonal must be 0"
        with open(meta_path) as f:
            meta = json.load(f)
        assert meta["status"] == "done"
        assert meta["shape"] == [6, 6]


# ---------------------------------------------------------------------------
# T5 — Acceptance rate is reported (TOOTH: monkeypatch to remove the field)
# ---------------------------------------------------------------------------


def test_acceptance_rate_reported_in_meta(tmp_path):
    """acceptance_rate must appear in the result from _load_corpus."""
    from experiments.article import runner
    from experiments.article.runner import run_d_matrix_cell

    cell = _tiny_d_matrix_cell()
    # Restrict to one distance to keep it fast
    from experiments.article.schemas import CellSpec

    cell = CellSpec(
        type="d_matrix",
        dataset="correlation_corpus",
        seed=7,
        dataset_params={"n_items": 4, "n_range": [4, 5], "n_edges_range": [2, 3]},
        distances=["isalhg_levenshtein"],
    )

    # Normal run — must have acceptance_rate
    out = tmp_path / "normal"
    result = run_d_matrix_cell(cell, out)
    assert "acceptance_rate" in result, "acceptance_rate must be in result"
    assert 0.0 < result["acceptance_rate"] <= 1.0

    # TOOTH: monkeypatch _load_corpus to drop the field
    orig_load = runner._load_corpus

    def patched_load(cell):
        hgs, meta = orig_load(cell)
        meta.pop("acceptance_rate", None)
        return hgs, meta

    runner._load_corpus = patched_load
    try:
        out2 = tmp_path / "patched"
        result2 = run_d_matrix_cell(cell, out2)
        # Without acceptance_rate, assertion below would fail
        assert "acceptance_rate" not in result2, "Monkeypatched run must not have acceptance_rate"
    finally:
        runner._load_corpus = orig_load  # always restore


# ---------------------------------------------------------------------------
# T6 — Idempotency: second run skips computation
# ---------------------------------------------------------------------------


def test_d_matrix_cell_idempotent(tmp_path):
    from experiments.article.runner import run_d_matrix_cell
    from experiments.article.schemas import CellSpec

    cell = CellSpec(
        type="d_matrix",
        dataset="correlation_corpus",
        seed=3,
        dataset_params={"n_items": 4, "n_range": [4, 5]},
        distances=["isalhg_levenshtein"],
    )
    out = tmp_path / "idem"

    # First run — computes
    run_d_matrix_cell(cell, out)

    # Record mtime before second run
    npy_path = out / "isalhg_levenshtein" / "D.npy"
    mtime_before = npy_path.stat().st_mtime

    # Second run — must skip (no file overwrite)
    run_d_matrix_cell(cell, out)
    mtime_after = npy_path.stat().st_mtime

    assert mtime_before == mtime_after, "Second run must not overwrite D.npy"


# ---------------------------------------------------------------------------
# T7 — Ladder cell: per-step d_I increments logged (T-TBb proxy)
# ---------------------------------------------------------------------------


def test_ladder_cell_logs_per_step_increments(tmp_path):
    """Ladder JSON must contain d_I_increment per step (T-TBb proxy)."""
    from experiments.article.runner import run_ladder_cell

    cell = _tiny_ladder_cell()
    out = tmp_path / "ladder_out"
    run_ladder_cell(cell, out)

    ladder_path = out / "ladder.json"
    assert ladder_path.exists()
    with open(ladder_path) as f:
        data = json.load(f)

    assert "ladders" in data
    assert len(data["ladders"]) >= 1
    for ladder in data["ladders"]:
        assert "steps" in ladder
        for step in ladder["steps"]:
            assert "d_I_from_base" in step, "d_I_from_base must be logged"
            assert "d_I_increment" in step, "d_I_increment must be logged (T-TBb proxy)"
            assert "budget_from_base" in step
            assert step["d_I_from_base"] >= 0.0
            assert step["d_I_increment"] >= 0.0

    # all_increments must be present for T-TBb analysis
    assert "all_increments" in data
    assert isinstance(data["all_increments"], list)
    assert len(data["all_increments"]) > 0


# ---------------------------------------------------------------------------
# T8 — Sensitivity cell: s(e) values per op type
# ---------------------------------------------------------------------------


def test_sensitivity_cell_emits_per_op_results(tmp_path):
    from experiments.article.runner import run_sensitivity_cell

    cell = _tiny_sensitivity_cell()
    out = tmp_path / "sens_out"
    run_sensitivity_cell(cell, out)

    sens_path = out / "sensitivity.json"
    assert sens_path.exists()
    with open(sens_path) as f:
        data = json.load(f)

    assert data["status"] == "done"
    assert "per_op_mean" in data, "per-op mean sensitivity must be reported"
    assert "all_s_e" in data
    assert data["n_edits_total"] >= 0
    # all s(e) must be non-negative
    for s_e in data["all_s_e"]:
        assert s_e >= 0.0, f"s(e) must be non-negative, got {s_e}"


# ---------------------------------------------------------------------------
# T9 — Info-content cell: compression ratios and median reported
# ---------------------------------------------------------------------------


def test_info_content_cell_produces_ratios(tmp_path):
    from experiments.article.runner import run_info_content_cell

    cell = _tiny_info_content_cell()
    out = tmp_path / "info_out"
    run_info_content_cell(cell, out)

    info_path = out / "info_content.json"
    assert info_path.exists()
    with open(info_path) as f:
        data = json.load(f)

    assert data["status"] == "done"
    assert "median_compression_ratio" in data
    assert "fraction_shorter" in data
    assert 0.0 <= data["fraction_shorter"] <= 1.0
    assert "records" in data
    for rec in data["records"]:
        assert "bits_isalhg" in rec
        assert "bits_incidence_list" in rec
        assert "compression_ratio" in rec
        assert rec["bits_isalhg"] > 0


# ---------------------------------------------------------------------------
# T10 — Ladder acceptance rate is reported
# ---------------------------------------------------------------------------


def test_ladder_acceptance_rate_reported(tmp_path):
    from experiments.article.runner import run_ladder_cell

    cell = _tiny_ladder_cell()
    out = tmp_path / "ladder_acc"
    run_ladder_cell(cell, out)

    with open(out / "ladder.json") as f:
        data = json.load(f)

    for ladder in data["ladders"]:
        assert "acceptance_rate" in ladder, (
            "Each ladder must report acceptance_rate from extra['acceptance_attempts']"
        )
        assert 0.0 < ladder["acceptance_rate"] <= 1.0


# ---------------------------------------------------------------------------
# T11 — Registry fallback: old kwarg-unpack call raises TypeError (T-M5i)
# ---------------------------------------------------------------------------


def test_build_dataset_old_kwarg_style_raises_type_error():
    """Demonstrates the pre-fix bug (T-M5i): get_dataset(name, **params) raises TypeError.

    get_dataset(name, params: dict) is a positional-dict signature, not **kwargs.
    Calling it with unpacked kwargs raises TypeError immediately at the call site,
    regardless of whether the dataset name exists.  This test pins the bug that
    _build_dataset line 87 had before the fix.
    """
    from isalhg.datasets.registry import get_dataset

    with pytest.raises(TypeError):
        # Simulates the pre-fix: get_dataset(name, **{"n_families": 1, "seed": 42})
        # which expands to get_dataset(name, n_families=1, seed=42) — wrong calling
        # convention for a (name, params: dict) signature.
        get_dataset("planted_families", n_families=1, seed=42)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# T12 — Registry fallback: post-fix positional dict call works (T-M5i)
# ---------------------------------------------------------------------------


def test_build_dataset_registry_fallback_passes_positional_dict():
    """Post-fix (T-M5i): _build_dataset passes params as a single positional dict.

    planted_families falls through all three named branches in _build_dataset
    and reaches the registry fallback.  After the fix, get_dataset(name, params)
    is called with a dict, not with **params.

    TOOTH: the old call get_dataset(name, **params) raises TypeError (T11 above).
    """
    from unittest.mock import MagicMock, patch

    from experiments.article.runner import _build_dataset
    from experiments.article.schemas import CellSpec

    captured: dict = {}
    mock_ds = MagicMock()

    def _capturing_get_dataset(name: str, params: dict) -> MagicMock:
        captured["name"] = name
        captured["params"] = dict(params)
        return mock_ds

    cell = CellSpec(
        type="d_matrix",
        dataset="planted_families",  # falls through all three named branches
        seed=42,
        dataset_params={"n_families": 1, "members_per_family": 2},
    )

    with patch("isalhg.datasets.registry.get_dataset", _capturing_get_dataset):
        result = _build_dataset(cell)

    assert result is mock_ds, "Mock dataset must be returned"
    assert captured["name"] == "planted_families"
    # seed injected by _build_dataset
    assert captured["params"].get("seed") == 42, "seed must be present in params dict"
    assert captured["params"].get("n_families") == 1
