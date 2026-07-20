"""Unit tests for the bits harvest pipeline.

Acceptance criteria:
- compute_corpus_bits writes a valid info_content.json with per-H records.
- compression_ratio field = B_incidence / B_IsalHG.
- harvest_bits pools corpora and calls analyze_info_content.
- Idempotence: re-running skips already-done corpora.

Teeth: a monkeypatched alphabet_size that returns 1 (log2(1)=0 bits)
confirms that bits_isalhg yields 0 and compression_ratio becomes nan/inf —
demonstrating the ratio computation is live and not hard-coded.
"""

from __future__ import annotations

import json
from unittest.mock import patch

import numpy as np
import pytest

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Minimal corpus for unit testing (avoids full PlantedFamilyDataset)
# ---------------------------------------------------------------------------


def _fake_corpus_params() -> dict:
    """Parameters for a tiny planted-family corpus (2 families × 2 members)."""
    return {
        "n_families": 2,
        "members_per_family": 2,
        "n_nodes": 5,
        "k": 3,
        "n_edges": 3,
        "seed_value": 0,
        "n_edits": 1,
        "max_retries": 50,
    }


# ---------------------------------------------------------------------------
# compute_corpus_bits
# ---------------------------------------------------------------------------


def test_compute_corpus_bits_writes_json(tmp_path):
    """compute_corpus_bits writes info_content.json with expected keys."""
    from experiments.article.analysis.bits_harvest import compute_corpus_bits

    out_dir = tmp_path / "bits" / "test_corpus"
    data = compute_corpus_bits("test_corpus", _fake_corpus_params(), out_dir)

    assert data["status"] == "done"
    assert data["n_items"] > 0
    assert "records" in data
    assert len(data["records"]) == data["n_items"]

    # Check JSON was written
    assert (out_dir / "info_content.json").exists()
    with open(out_dir / "info_content.json") as f:
        saved = json.load(f)
    assert saved["status"] == "done"


def test_compute_corpus_bits_record_fields(tmp_path):
    """Every record has the expected fields and compression_ratio > 0."""
    from experiments.article.analysis.bits_harvest import compute_corpus_bits

    out_dir = tmp_path / "bits" / "records_test"
    data = compute_corpus_bits("records_test", _fake_corpus_params(), out_dir)

    for rec in data["records"]:
        assert "bits_isalhg" in rec
        assert "bits_incidence_list" in rec
        assert "compression_ratio" in rec
        assert rec["bits_isalhg"] > 0
        assert rec["bits_incidence_list"] > 0
        # compression_ratio = B_incidence / B_isalhg — should be positive
        expected_r = rec["bits_incidence_list"] / rec["bits_isalhg"]
        np.testing.assert_allclose(rec["compression_ratio"], expected_r, rtol=1e-6)


def test_compute_corpus_bits_idempotent(tmp_path):
    """compute_corpus_bits skips re-computation when result exists."""
    from experiments.article.analysis.bits_harvest import compute_corpus_bits

    out_dir = tmp_path / "bits" / "idempotent_test"
    data1 = compute_corpus_bits("idem_test", _fake_corpus_params(), out_dir)

    # Second call should load from disk without re-running
    with patch("isalhg.core.canonical.canonical_string") as mock_cs:
        data2 = compute_corpus_bits("idem_test", _fake_corpus_params(), out_dir)
        # canonical_string should NOT be called (skipped)
        mock_cs.assert_not_called()

    assert data2["n_items"] == data1["n_items"]


def test_compute_corpus_bits_alphabet_size_zero_yields_nan_ratio(tmp_path):
    """Teeth: patching alphabet_size to return 1 makes bits=0 → nan ratio.

    This confirms the ratio computation is live: a pre-baked ratio would
    not be nan here.
    """
    from experiments.article.analysis.bits_harvest import compute_corpus_bits
    from isalhg.metric_space.metrics import information as info_mod

    out_dir = tmp_path / "bits" / "teeth_test"

    # alphabet_size_isalhg(k) = 1 ⟹ log2(1) = 0 ⟹ bits_isalhg = 0
    with (
        patch.object(info_mod, "alphabet_size_isalhg", return_value=1),
        patch.object(info_mod, "bits_isalhg", return_value=0.0),
    ):
        data = compute_corpus_bits("teeth_test", _fake_corpus_params(), out_dir)

    # With bits_isalhg = 0, compression_ratio should be nan (division by zero path)
    ratios = [r["compression_ratio"] for r in data["records"]]
    assert all(np.isnan(r) for r in ratios), (
        f"Expected nan ratios when bits_isalhg=0; got {ratios[:3]}"
    )


# ---------------------------------------------------------------------------
# harvest_bits
# ---------------------------------------------------------------------------


def test_harvest_bits_produces_aggregate(tmp_path):
    """harvest_bits produces an aggregate result with Wilcoxon stats."""
    from experiments.article.analysis.bits_harvest import harvest_bits

    # Override BODY_CORPORA for this test with a single tiny corpus
    tiny = [
        {
            "label": "tiny_corpus",
            "dataset_params": _fake_corpus_params(),
        }
    ]
    with patch("experiments.article.analysis.bits_harvest.BODY_CORPORA", tiny):
        result = harvest_bits(tmp_path / "bits_out")

    assert result.get("n_items", 0) > 0
    assert "median_compression_ratio" in result
    assert "wilcoxon_pvalue" in result
    assert "ols_beta" in result
    # Per-corpus breakdown
    assert "per_corpus" in result
    assert result["per_corpus"][0]["label"] == "tiny_corpus"
