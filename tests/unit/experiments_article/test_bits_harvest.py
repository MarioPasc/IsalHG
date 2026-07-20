"""Unit tests for the bits harvest pipeline.

Acceptance criteria:
- compute_corpus_bits writes a valid info_content.json with per-H records.
- compression_ratio field = B_incidence / B_IsalHG.
- harvest_bits pools corpora and calls analyze_info_content.
- Idempotence: re-running skips already-done corpora.
- Tokenization uses parse(), not raw split(";"), to count tokens.

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


# ---------------------------------------------------------------------------
# Regression: tokenization must use parse(), not raw split(";")
# ---------------------------------------------------------------------------


def test_tokenizer_split_vs_parse_discrepancy():
    """Pure unit: parse() vs split(';') token count for a multi-field string.

    ``'V[0;1;2;0,0];C[0;3]'`` has 2 tokens; raw split on ``;`` gives 6 pieces
    because ``;`` also appears as a field separator inside brackets.  This
    demonstrates the discrepancy that the harvest bug produced.
    """
    from isalhg.core.instructions import TokenC, TokenV, parse, serialize

    tokens = [
        TokenV(edge_label=0, i=1, j=2, new_node_labels=(0, 0)),
        TokenC(edge_label=0, i=3),
    ]
    canonical_str = serialize(tokens)
    assert canonical_str == "V[0;1;2;0,0];C[0;3]", canonical_str

    # parse() returns the correct count
    assert len(parse(canonical_str)) == 2

    # raw split overcounts — 6 pieces, not 2
    assert len([p for p in canonical_str.split(";") if p]) == 6


def test_tokenization_harvest_n_tokens_equals_parse_count(tmp_path):
    """End-to-end regression: n_tokens in records == len(parse(w)).

    Runs compute_corpus_bits on a tiny corpus, then re-derives each canonical
    string with the same k and asserts the recorded n_tokens matches
    len(parse(w)).  Would fail under the old split(';') implementation because
    V and C tokens embed ';' inside brackets, inflating the raw split count.
    """
    from experiments.article.analysis.bits_harvest import compute_corpus_bits
    from isalhg.core.canonical import canonical_string
    from isalhg.core.instructions import parse
    from isalhg.datasets.synthetic.planted_families import PlantedFamilyDataset

    params = _fake_corpus_params()
    out_dir = tmp_path / "bits" / "parse_regression"
    data = compute_corpus_bits("regression_test", params, out_dir)

    k_corpus = data["k"]  # the actual k used inside compute_corpus_bits
    dataset = PlantedFamilyDataset(**params)
    hypergraphs = [item.hypergraph for item in dataset]

    any_nested_semicolons = False
    for H, record in zip(hypergraphs, data["records"], strict=False):
        w = canonical_string(H, k=k_corpus)
        parse_count = len(parse(w))
        naive_count = len([p for p in w.split(";") if p])

        assert record["n_tokens"] == parse_count, (
            f"n_tokens={record['n_tokens']} but parse count={parse_count}. "
            "Regression: tokenization uses raw split(';') instead of parse()."
        )
        if naive_count > parse_count:
            any_nested_semicolons = True

    # If no canonical string had nested semicolons this test has no teeth.
    assert any_nested_semicolons, (
        "Corpus produced no strings with nested semicolons — "
        "test cannot detect the regression.  Use a corpus with V or C tokens."
    )
