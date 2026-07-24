"""Gate tests for real-world corpus candidates (T-M7g).

Validates three things:

(A) Structural pre-gate: ARBBensonDataset yields exactly 1 item per dataset
    (a single large network), not a labeled instance collection.

(B) Gate artifact: after ``scripts/gate_real_corpus_candidates.py`` runs, the
    JSON artifact must exist, be well-formed, and record every candidate as
    NO_GO (none promoted).

(C) Stratum A designs corpus: 17 families × 5 members = 85 items, max arity ≤ 5,
    all items carry family labels.  This is the guaranteed-computable real anchor
    that passes the feasibility gate by construction.

Test ordering: (A) and (C) pass immediately; (B) FAILS until the gate script is
executed (``python scripts/gate_real_corpus_candidates.py``).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# (A) Structural pre-gate: ARB datasets always yield 1 item
# ---------------------------------------------------------------------------


def test_arb_benson_single_network_pre_gate_fail() -> None:
    """ARBBensonDataset.__len__() == 1 for any dataset name.

    The gate requires ≥ 2 labeled instances; a single-network loader fails
    at pre-gate.  The assertion is structural — no file download needed.
    """
    from isalhg.datasets.arb_benson import ARBBensonDataset

    # Use a non-existent root — __len__ must return 1 without touching the FS
    ds = ARBBensonDataset(root=Path("/nonexistent"), name="dummy")
    assert len(ds) == 1, (
        "ARBBensonDataset must always return len=1 "
        "(one large network, not a labeled instance collection)"
    )


# ---------------------------------------------------------------------------
# (B) Gate artifact — FAILS until gate_real_corpus_candidates.py has run
# ---------------------------------------------------------------------------

_ARTIFACT = (
    Path(__file__).parents[3] / "artifacts" / "real_anchor_gate" / "candidate_gate_results.json"
)


@pytest.mark.slow
def test_gate_artifact_exists() -> None:
    """Gate artifact must exist after gate_real_corpus_candidates.py runs."""
    assert _ARTIFACT.is_file(), (
        f"Gate artifact not found at {_ARTIFACT}. "
        "Run: python scripts/gate_real_corpus_candidates.py"
    )


@pytest.mark.slow
def test_gate_artifact_schema() -> None:
    """Gate artifact must be valid JSON with required top-level keys."""
    if not _ARTIFACT.is_file():
        pytest.skip("Gate artifact not yet produced — run gate script first")
    data = json.loads(_ARTIFACT.read_text())
    required = {"gate_protocol_version", "run_date", "candidates", "promoted", "conclusion"}
    missing = required - data.keys()
    assert not missing, f"Gate artifact missing keys: {missing}"


@pytest.mark.slow
def test_gate_artifact_no_promotions() -> None:
    """No candidate may have been promoted (all should be NO_GO)."""
    if not _ARTIFACT.is_file():
        pytest.skip("Gate artifact not yet produced — run gate script first")
    data = json.loads(_ARTIFACT.read_text())
    assert data["promoted"] == [], f"Expected zero promotions; found {data['promoted']}"
    for cand in data["candidates"]:
        assert cand["verdict"] == "NO_GO", (
            f"Candidate {cand['name']} has unexpected verdict {cand['verdict']!r}"
        )


@pytest.mark.slow
def test_gate_artifact_all_pre_gate_reason() -> None:
    """Every candidate fails at pre-gate (single network, not a corpus)."""
    if not _ARTIFACT.is_file():
        pytest.skip("Gate artifact not yet produced — run gate script first")
    data = json.loads(_ARTIFACT.read_text())
    for cand in data["candidates"]:
        pre = cand.get("pre_gate", {})
        assert pre.get("status") == "FAIL", (
            f"Candidate {cand['name']}: expected pre_gate.status='FAIL', got {pre.get('status')!r}"
        )
        assert (
            "single" in pre.get("reason", "").lower() or "one" in pre.get("reason", "").lower()
        ), (
            f"Candidate {cand['name']}: reason should mention single/one-network structure; "
            f"got: {pre.get('reason')!r}"
        )


# ---------------------------------------------------------------------------
# (C) Stratum A designs corpus passes feasibility by construction
# ---------------------------------------------------------------------------


def test_stratum_a_gate_n_families() -> None:
    """DATA_MANIFEST reports exactly 17 admitted design ids."""
    from isalhg.datasets.synthetic.known_design_catalog import DATA_MANIFEST

    n = len(DATA_MANIFEST.stratum_a_ids)
    assert n == 17, f"Expected 17 admitted Stratum A ids; got {n}"


def test_stratum_a_gate_corpus_size() -> None:
    """build_stratum_a_corpus() yields 85 items across 17 distinct families."""
    from experiments.article.analysis.sweep_multi_seed import build_stratum_a_seed_corpus

    hypergraphs, int_labels, fam_labels, coarse_labels = build_stratum_a_seed_corpus(seed=0)
    n_items = len(hypergraphs)
    n_families = len(set(fam_labels))
    assert n_items == 85, f"Expected 85 items (17 × 5); got {n_items}"
    assert n_families == 17, f"Expected 17 families; got {n_families}"


def test_stratum_a_gate_arity_within_cap() -> None:
    """All Stratum A designs have max arity ≤ k_max=10 (enforced at T-M7a/h)."""
    from experiments.article.analysis.sweep_multi_seed import build_stratum_a_seed_corpus

    hypergraphs, _int_labels, _fam_labels, _coarse = build_stratum_a_seed_corpus(seed=0)
    k_max = 10
    for h in hypergraphs:
        max_arity = max((len(e) for e in h.hyperedges()), default=0)
        assert max_arity <= k_max, f"Stratum A item has max_arity={max_arity} > k_max={k_max}"
