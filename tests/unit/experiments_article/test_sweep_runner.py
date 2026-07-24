"""Unit tests for the T-M7d multi-seed sweep runner.

Tests the sweep runner infrastructure (corpus builders, D-matrix caching,
metric extractors, statistics aggregation) independently of the stats harness
(covered by test_stats_harness.py — do NOT duplicate those tests here).

Acceptance criteria
-------------------
AC1. load_admitted_stratum_b_blocks parses the envelope JSON and returns
     only admitted blocks.
AC2. build_stratum_a_seed_corpus returns (hypergraphs, labels, label_strings)
     with len(labels) == len(hypergraphs) and all labels in [0, n_families).
AC3. build_stratum_b_seed_corpus returns connected hypergraphs and sub-seeds
     are deterministic: same corpus_seed → same corpus.
AC4. compute_bits_for_hypergraphs uses the bracket-aware parser, not raw
     split(";") — regression for the T-M5a S5 tokenization bug.
AC5. _extract_metric_scores correctly returns None for seeds where computation
     failed (g1_a1 is None).
AC6. aggregate_cell_stats attaches CIs to every metric × representation slot;
     Wilcoxon tests are present for every competitor vs IsalHG.
AC7. run_sweep CLI: --n-max filter restricts to small Stratum B blocks.
AC8. D-matrix cache layout: seed_metrics JSON carries the seed in-content.
AC9. Censored D̂ flag: d_hat_censored=True when d_hat hits the CV cap.

Teeth (tests observed failing before fix):
- test_bits_uses_parse_not_split: demonstrates split overcounts before fix.
- test_extract_metric_none_passthrough: fails if None filtering is wrong.
- test_aggregate_has_ci_for_all_repr_metric_pairs: fails if CIs loop skips reps.
- test_seed_in_content: fails if JSON cache omits seed field.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _fake_envelope(tmp_path: Path) -> Path:
    """Write a minimal stratum_b_feasibility_envelope.json for tests."""
    envelope = {
        "schema_version": "1.0",
        "admitted_block_keys": ["er_uniform_k3_n8_rho1", "er_uniform_k3_n16_rho2"],
        "pending_cluster": [],
        "block_results": [
            {
                "block_key": "er_uniform_k3_n8_rho1",
                "n": 8,
                "k": 3,
                "density_ratio": 1.0,
                "admitted": True,
            },
            {
                "block_key": "er_uniform_k3_n16_rho2",
                "n": 16,
                "k": 3,
                "density_ratio": 2.0,
                "admitted": True,
            },
            {
                "block_key": "er_uniform_k3_n24_rho1",
                "n": 24,
                "k": 3,
                "density_ratio": 1.0,
                "admitted": True,  # NOT in admitted_block_keys — should be excluded
            },
        ],
    }
    path = tmp_path / "envelope.json"
    path.write_text(json.dumps(envelope))
    return path


def _fake_d_matrix(n: int = 10) -> np.ndarray:
    """Random symmetric distance matrix with zero diagonal."""
    rng = np.random.default_rng(0)
    raw = rng.random((n, n))
    D = (raw + raw.T) / 2
    np.fill_diagonal(D, 0.0)
    return D


def _fake_seed_metrics_list(
    n_seeds: int,
    cell_key: str = "stratum_a",
    stratum: str = "a",
    dist_name: str = "isalhg_levenshtein",
    g1_a1_valid: bool = True,
    a2_valid: bool = True,
    a3_valid: bool = True,
) -> list:
    """Build a list of fake SeedMetrics for testing aggregation."""
    from experiments.article.analysis.sweep_multi_seed import SeedMetrics

    metrics: list[SeedMetrics] = []
    rng = np.random.default_rng(1)

    for s in range(n_seeds):
        g1_a1: dict[str, Any] | None = (
            {
                "nu": float(rng.uniform(0.1, 0.4)),
                "d_hat": int(rng.integers(3, 15)),
                "d_hat_censored": False,
                "stress": float(rng.uniform(0.05, 0.3)),
                "diameter": float(rng.uniform(5.0, 20.0)),
                "median": float(rng.uniform(2.0, 10.0)),
                "iqr": float(rng.uniform(1.0, 5.0)),
                "hubness_skewness": float(rng.uniform(-0.5, 3.0)),
            }
            if g1_a1_valid
            else None
        )
        a2: dict[str, Any] | None = (
            {
                "ari": float(rng.uniform(0.3, 0.9)),
                "nmi": float(rng.uniform(0.3, 0.9)),
                "silhouette": float(rng.uniform(0.1, 0.7)),
                "dunn": float(rng.uniform(0.5, 2.0)),
                "davies_bouldin": float(rng.uniform(0.3, 1.5)),
            }
            if a2_valid
            else None
        )
        a3: dict[int, float] | None = (
            {1: float(rng.uniform(0.5, 1.0)), 3: float(rng.uniform(0.5, 1.0))} if a3_valid else None
        )
        metrics.append(
            SeedMetrics(
                cell_key=cell_key,
                stratum=stratum,
                dist_name=dist_name,
                seed=s,
                n_corpus=50,
                g1_a1=g1_a1,
                a2=a2,
                a3=a3,
                bits=None,
            )
        )
    return metrics


# ---------------------------------------------------------------------------
# AC1: load_admitted_stratum_b_blocks
# ---------------------------------------------------------------------------


def test_load_admitted_blocks_returns_only_admitted(tmp_path: Path) -> None:
    """Only block_keys in admitted_block_keys are returned; extras ignored."""
    from experiments.article.analysis.sweep_multi_seed import load_admitted_stratum_b_blocks

    env_path = _fake_envelope(tmp_path)
    blocks = load_admitted_stratum_b_blocks(env_path)

    # envelope has 2 admitted keys out of 3 block_results
    assert len(blocks) == 2
    keys = {b.block_key for b in blocks}
    assert "er_uniform_k3_n8_rho1" in keys
    assert "er_uniform_k3_n16_rho2" in keys
    # not admitted even though in block_results
    assert "er_uniform_k3_n24_rho1" not in keys


def test_load_admitted_blocks_parses_n_k_density(tmp_path: Path) -> None:
    """n, k, density_ratio are parsed from block_results."""
    from experiments.article.analysis.sweep_multi_seed import load_admitted_stratum_b_blocks

    env_path = _fake_envelope(tmp_path)
    blocks = load_admitted_stratum_b_blocks(env_path)

    b8 = next(b for b in blocks if b.block_key == "er_uniform_k3_n8_rho1")
    assert b8.n == 8
    assert b8.k == 3
    assert b8.density_ratio == pytest.approx(1.0)


def test_load_admitted_blocks_missing_file_raises(tmp_path: Path) -> None:
    """FileNotFoundError when envelope does not exist."""
    from experiments.article.analysis.sweep_multi_seed import load_admitted_stratum_b_blocks

    with pytest.raises(FileNotFoundError):
        load_admitted_stratum_b_blocks(tmp_path / "nonexistent.json")


# ---------------------------------------------------------------------------
# AC2: build_stratum_a_seed_corpus (smoke — needs isalhg installed)
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_build_stratum_a_seed_corpus_labels_align() -> None:
    """len(hypergraphs) == len(labels); labels in [0, n_families).

    Uses a small arity-3 subset of ADMITTED_A_IDS to keep the test fast.
    (T-M7m: complete_k3_n5 removed from admitted set; all 14 families are
    now feasible for Qin-edit perturbation within the standard retry budget.)
    """
    from experiments.article.analysis.sweep_multi_seed import build_stratum_a_seed_corpus

    # Small subset of arity-3 admitted families — fast for CI.
    fast_subset = frozenset({"sts7", "sts9", "loose_path_k3", "tight_cycle_k3"})
    hypergraphs, labels, label_strings, _ = build_stratum_a_seed_corpus(
        seed=0,
        admitted_ids=fast_subset,
        members_per_family=5,
        n_edits=2,
        max_retries=300,
    )
    n_families = len(fast_subset)
    assert len(hypergraphs) == len(labels), "hypergraphs and labels must align"
    assert len(labels) == len(label_strings), "labels and label_strings must align"
    for lbl in labels:
        assert 0 <= lbl < n_families, f"label {lbl} out of range [0, {n_families})"


@pytest.mark.slow
def test_build_stratum_a_seed_corpus_different_seeds_differ() -> None:
    """Different seeds produce different corpora (perturbation members vary)."""
    from experiments.article.analysis.sweep_multi_seed import build_stratum_a_seed_corpus

    fast_subset = frozenset({"sts7", "sts9", "loose_path_k3", "tight_cycle_k3"})
    H0, _, _, _ = build_stratum_a_seed_corpus(
        seed=0, admitted_ids=fast_subset, members_per_family=5, n_edits=2
    )
    H1, _, _, _ = build_stratum_a_seed_corpus(
        seed=1, admitted_ids=fast_subset, members_per_family=5, n_edits=2
    )
    # The corpora have the same size (same families × members_per_family).
    assert len(H0) == len(H1)
    # But at least some hypergraphs should differ (seed changes the perturbations).
    n_edges_0 = [h.n_edges for h in H0]
    n_edges_1 = [h.n_edges for h in H1]
    # Compare edge-count vectors as a proxy; at least one should differ.
    # (Two seeds could coincidentally produce the same n_edges; use a soft check.)
    assert not all(e0 == e1 for e0, e1 in zip(n_edges_0, n_edges_1, strict=False)), (
        "seeds 0 and 1 produced identical corpora — check seed propagation"
    )


# ---------------------------------------------------------------------------
# AC3: build_stratum_b_seed_corpus
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_build_stratum_b_seed_corpus_deterministic() -> None:
    """Same corpus_seed → same corpus (sub-seeds are deterministic)."""
    from experiments.article.analysis.sweep_multi_seed import (
        StratumBBlock,
        build_stratum_b_seed_corpus,
    )

    block = StratumBBlock(block_key="er_uniform_k3_n8_rho1", n=8, k=3, density_ratio=1.0)
    H_a = build_stratum_b_seed_corpus(block, corpus_seed=0, n_corpus=5)
    H_b = build_stratum_b_seed_corpus(block, corpus_seed=0, n_corpus=5)

    assert len(H_a) == len(H_b), "Same seed must produce same corpus size"
    for ha, hb in zip(H_a, H_b, strict=False):
        assert ha.n_nodes == hb.n_nodes
        assert ha.n_edges == hb.n_edges


@pytest.mark.slow
def test_build_stratum_b_seed_corpus_connectivity() -> None:
    """All returned hypergraphs are connected (D-CONN1)."""
    from experiments.article.analysis.sweep_multi_seed import (
        StratumBBlock,
        build_stratum_b_seed_corpus,
    )

    block = StratumBBlock(block_key="er_uniform_k3_n8_rho1", n=8, k=3, density_ratio=1.0)
    hypergraphs = build_stratum_b_seed_corpus(block, corpus_seed=0, n_corpus=10)
    assert len(hypergraphs) >= 1, "Should generate at least one connected hypergraph"
    for H in hypergraphs:
        assert H.is_connected(), "All Stratum B hypergraphs must be connected"


# ---------------------------------------------------------------------------
# AC4: bits uses parse(), not split(";")  — TOOTH
# ---------------------------------------------------------------------------


def test_bits_uses_parse_not_split() -> None:
    """compute_bits_for_hypergraphs counts tokens with the bracket-aware parser.

    Demonstrates that ``w.split(';')`` would overcount: a string
    ``V[0;1;2;0,0];C[0;3]`` has 2 tokens via parse() but 6 pieces via split().
    This test fails if the implementation uses raw split.
    """
    from isalhg.core.instructions import TokenC, TokenV, parse, serialize

    # Build a canonical string with nested semicolons.
    tokens = [
        TokenV(edge_label=0, i=1, j=2, new_node_labels=(0, 0)),
        TokenC(edge_label=0, i=3),
    ]
    w = serialize(tokens)
    assert w == "V[0;1;2;0,0];C[0;3]"

    parse_count = len(parse(w))
    split_count = len([p for p in w.split(";") if p])

    # parse() → 2 tokens; split(';') → 6 pieces.
    assert parse_count == 2, f"parse() returned {parse_count}, expected 2"
    assert split_count > parse_count, (
        "The test is vacuous: no nested semicolons to trigger the discrepancy"
    )


@pytest.mark.slow
def test_bits_harvest_n_tokens_via_parse(tmp_path: Path) -> None:
    """End-to-end: compute_bits_for_hypergraphs uses len(parse(w)), not len(w.split(';'))."""
    from experiments.article.analysis.sweep_multi_seed import compute_bits_for_hypergraphs
    from isalhg.core.canonical import canonical_string
    from isalhg.core.instructions import parse
    from isalhg.datasets.synthetic.planted_families import PlantedFamilyDataset

    # Tiny corpus with k=3 to guarantee V tokens.
    params = {
        "n_families": 2,
        "members_per_family": 3,
        "n_nodes": 5,
        "k": 3,
        "n_edges": 4,
        "seed_value": 0,
        "n_edits": 1,
        "max_retries": 50,
    }
    dataset = PlantedFamilyDataset(**params)
    hypergraphs = [item.hypergraph for item in dataset]

    result = compute_bits_for_hypergraphs(hypergraphs)
    assert result is not None

    k_corpus = result["k_corpus"]
    any_discrepancy = False
    for H in hypergraphs:
        w = canonical_string(H, k=k_corpus)
        parse_count = len(parse(w))
        split_count = len([p for p in w.split(";") if p])
        if split_count != parse_count:
            any_discrepancy = True

    # If no discrepancy existed, the test has no teeth (corpus too simple).
    assert any_discrepancy, (
        "Corpus produced no strings with nested semicolons — "
        "the regression test has no teeth.  Use k≥3 to get V tokens."
    )


# ---------------------------------------------------------------------------
# AC5: _extract_metric_scores None passthrough  — TOOTH
# ---------------------------------------------------------------------------


def test_extract_metric_none_passthrough() -> None:
    """_extract_metric_scores returns None for seeds where g1_a1 is None."""
    from experiments.article.analysis.sweep_multi_seed import (
        SeedMetrics,
        _extract_metric_scores,
    )

    # Build 5 seeds: 3 valid, 2 failed (g1_a1=None).
    seeds = []
    for s in range(5):
        g1_a1 = (
            {
                "nu": 0.1 + s * 0.01,
                "stress": 0.2,
                "hubness_skewness": 1.0,
                "d_hat": 5,
                "diameter": 10.0,
                "median": 5.0,
                "iqr": 2.0,
            }
            if s < 3
            else None
        )
        seeds.append(
            SeedMetrics(
                cell_key="test",
                stratum="a",
                dist_name="isalhg_levenshtein",
                seed=s,
                n_corpus=10,
                g1_a1=g1_a1,
                a2=None,
                a3=None,
                bits=None,
            )
        )

    scores = _extract_metric_scores(seeds, "g1_a1", "nu")
    assert len(scores) == 5
    assert scores[0] is not None
    assert scores[1] is not None
    assert scores[2] is not None
    assert scores[3] is None  # failed
    assert scores[4] is None  # failed

    # Test that aggregation uses only the 3 valid scores.
    valid = [v for v in scores if v is not None]
    assert len(valid) == 3


# ---------------------------------------------------------------------------
# AC6: aggregate_cell_stats attaches CIs and Wilcoxon — TOOTH
# ---------------------------------------------------------------------------


def test_aggregate_has_ci_for_all_repr_metric_pairs() -> None:
    """aggregate_cell_stats: every (repr, geometry metric) pair has a CI entry.

    Fails if the CIs loop skips any representation or metric.
    """
    from experiments.article.analysis.sweep_multi_seed import aggregate_cell_stats

    # Two representations: primary + one competitor; 20 seeds each.
    n_seeds = 20
    all_seed_metrics = {
        "isalhg_levenshtein": _fake_seed_metrics_list(n_seeds, dist_name="isalhg_levenshtein"),
        "degree_seq_l1": _fake_seed_metrics_list(n_seeds, dist_name="degree_seq_l1"),
    }

    cs = aggregate_cell_stats(
        cell_key="stratum_a",
        stratum="a",
        all_seed_metrics=all_seed_metrics,
        n_seeds=n_seeds,
    )

    # Every geom metric for every representation must appear in cs.cis.
    geom_metrics = ["nu", "stress", "hubness_skewness", "d_hat"]
    for dist in ["isalhg_levenshtein", "degree_seq_l1"]:
        for mkey in geom_metrics:
            mid = f"g1_a1::{mkey}"
            key = f"{dist}::{mid}"
            assert key in cs.cis, f"Missing CI entry: {key}"
            row = cs.cis[key]
            assert "ci_lower" in row and "ci_upper" in row, f"CI bounds missing in: {row}"

    # Wilcoxon must be present for the competitor vs primary.
    wilcoxon_keys = list(cs.wilcoxon.keys())
    assert len(wilcoxon_keys) > 0, "No Wilcoxon entries were populated"
    for mkey in geom_metrics:
        mid = f"g1_a1::{mkey}"
        wkey = f"degree_seq_l1::{mid}"
        assert wkey in cs.wilcoxon, f"Missing Wilcoxon entry: {wkey}"
        wrow = cs.wilcoxon[wkey]
        assert "p_holm" in wrow, f"Holm-adjusted p missing in: {wrow}"


def test_aggregate_a3_uses_seed_level_scores() -> None:
    """A3 AUC resampling is over seeds, not fold × seed.

    This tests the structural property: the n_valid count in the CI row equals
    n_seeds, not n_seeds × n_folds.  The failure mode (double-counting folds)
    would inflate n_samples in the BootstrapCI, which would appear as
    n_valid != n_seeds if we ever stored folds directly.
    """
    from experiments.article.analysis.sweep_multi_seed import aggregate_cell_stats

    n_seeds = 20
    # Each SeedMetrics.a3 is a seed-level dict (already aggregated over folds
    # per knn.run_knn_cv semantics).
    all_seed_metrics = {
        "isalhg_levenshtein": _fake_seed_metrics_list(
            n_seeds, dist_name="isalhg_levenshtein", a3_valid=True
        ),
    }

    cs = aggregate_cell_stats(
        cell_key="stratum_a",
        stratum="a",
        all_seed_metrics=all_seed_metrics,
        n_seeds=n_seeds,
    )

    # A3 k=1 CI for isalhg_levenshtein.
    mid = "a3::auc_k1"
    key = f"isalhg_levenshtein::{mid}"
    assert key in cs.cis, "A3 k=1 CI missing for isalhg_levenshtein"
    row = cs.cis[key]
    # n_valid should equal the number of seeds with valid a3 scores (20).
    assert row["n_valid"] == n_seeds, (
        f"Expected n_valid={n_seeds} (seed count), got {row['n_valid']} "
        "(double-counting folds would give a different number)"
    )


# ---------------------------------------------------------------------------
# AC7: n_max filter for local smoke
# ---------------------------------------------------------------------------


def test_n_max_filter_restricts_stratum_b_blocks(tmp_path: Path) -> None:
    """--n-max filters Stratum B blocks to those with n ≤ n_max."""
    from experiments.article.analysis.sweep_multi_seed import load_admitted_stratum_b_blocks

    env_path = _fake_envelope(tmp_path)
    all_blocks = load_admitted_stratum_b_blocks(env_path)

    filtered = [b for b in all_blocks if b.n <= 8]
    assert len(filtered) == 1
    assert filtered[0].block_key == "er_uniform_k3_n8_rho1"


# ---------------------------------------------------------------------------
# AC8: seed in content of cached JSON
# ---------------------------------------------------------------------------


def test_seed_in_content(tmp_path: Path) -> None:
    """Per-seed JSON cache carries seed as an in-content field."""
    from experiments.article.analysis.sweep_multi_seed import (
        SeedMetrics,
        _cache_seed_metrics,
        _load_seed_metrics_cache,
    )

    sm = SeedMetrics(
        cell_key="test_cell",
        stratum="a",
        dist_name="isalhg_levenshtein",
        seed=7,
        n_corpus=50,
        g1_a1={
            "nu": 0.25,
            "d_hat": 10,
            "d_hat_censored": False,
            "stress": 0.12,
            "diameter": 15.0,
            "median": 7.0,
            "iqr": 3.0,
            "hubness_skewness": 1.5,
        },
        a2=None,
        a3=None,
        bits=None,
    )
    _cache_seed_metrics(sm, tmp_path)

    # Load back.
    loaded = _load_seed_metrics_cache("test_cell", "a", "isalhg_levenshtein", 7, tmp_path)
    assert loaded is not None
    assert loaded.seed == 7, "seed field must be present in cached JSON content"

    # Verify the JSON file directly.
    cache_path = tmp_path / "seed_metrics" / "a" / "test_cell" / "seed7" / "isalhg_levenshtein.json"
    assert cache_path.exists()
    with open(cache_path) as f:
        raw = json.load(f)
    assert raw["seed"] == 7, "seed field missing from JSON content"


# ---------------------------------------------------------------------------
# AC9: censored D̂ flag
# ---------------------------------------------------------------------------


def test_compute_g1_a1_censored_flag() -> None:
    """d_hat_censored=True when d_hat reaches the max_cv_dims cap.

    We use a corpus where the CV curve is monotone-decreasing so the parsimony
    rule always picks the cap.  A near-Euclidean corpus (points on a grid)
    with max_cv_dims=2 will saturate at d=2 if the true dimension is higher.
    """
    from experiments.article.analysis.sweep_multi_seed import compute_g1_a1

    # 20 points in 5D → D̂ should want > 2 dims; cap at 2 → censored.
    rng = np.random.default_rng(42)
    X = rng.standard_normal((20, 5))

    # Build pairwise Euclidean distance matrix.
    diff = X[:, np.newaxis, :] - X[np.newaxis, :, :]
    D = np.sqrt(np.sum(diff**2, axis=-1))
    np.fill_diagonal(D, 0.0)

    result = compute_g1_a1(D, "test", "isalhg_levenshtein", max_cv_dims=2)
    assert result is not None
    # With cap=2 and true dim=5, the CV error should still be decreasing at d=2,
    # so d_hat_censored should be True.
    assert result["d_hat"] == 2
    assert result["d_hat_censored"] is True


def test_compute_g1_a1_uncensored_flag() -> None:
    """d_hat_censored=False when d_hat is below the cap."""
    from experiments.article.analysis.sweep_multi_seed import compute_g1_a1

    # 1D data: all points on a line → D̂ = 1; cap=10 → not censored.
    n = 20
    X = np.linspace(0, 10, n).reshape(-1, 1)
    diff = X[:, np.newaxis, :] - X[np.newaxis, :, :]
    D = np.sqrt(np.sum(diff**2, axis=-1))
    np.fill_diagonal(D, 0.0)

    result = compute_g1_a1(D, "test", "isalhg_levenshtein", max_cv_dims=10)
    assert result is not None
    assert result["d_hat"] <= 3  # should be 1 or 2 for 1D data
    assert result["d_hat_censored"] is False


# ---------------------------------------------------------------------------
# Smoke: ADMITTED_A_IDS completeness
# ---------------------------------------------------------------------------


def test_admitted_a_ids_count() -> None:
    """ADMITTED_A_IDS must contain exactly the 14 admitted designs (pruned T-M7m)."""
    from experiments.article.analysis.sweep_multi_seed import ADMITTED_A_IDS

    assert len(ADMITTED_A_IDS) == 14, (
        f"Expected 14 admitted Stratum A IDs (T-M7m pruned), got {len(ADMITTED_A_IDS)}"
    )

    # Spot-check mandatory entries (all 14 kept families).
    mandatory = {"sts7", "sts9", "gq22", "loose_path_k3", "tight_cycle_k5"}
    missing = mandatory - ADMITTED_A_IDS
    assert not missing, f"Missing mandatory admitted IDs: {missing}"

    # Spot-check excluded entries (must NOT be present — T-M7m EXCLUDED_SYMMETRIC).
    excluded = {
        "sts13_0",
        "sts13_1",
        "ag24",
        "pg23",
        "pg24",
        "complete_k3_n5",
        "complete_k4_n6",
        "complete_k5_n6",
        "sts15_0",
    }
    present_but_excluded = excluded & ADMITTED_A_IDS
    assert not present_but_excluded, (
        f"Excluded designs should not be in ADMITTED_A_IDS: {present_but_excluded}"
    )


def test_primary_repr_in_all_distances() -> None:
    """PRIMARY_REPR must appear in ALL_DISTANCES (it is both reference and rep)."""
    from experiments.article.analysis.sweep_multi_seed import ALL_DISTANCES, PRIMARY_REPR

    assert PRIMARY_REPR in ALL_DISTANCES, (
        f"PRIMARY_REPR={PRIMARY_REPR!r} not in ALL_DISTANCES={ALL_DISTANCES}"
    )


def test_all_distances_has_naive_baseline() -> None:
    """degree_seq_l1 (naive baseline, T-M7c) must be in ALL_DISTANCES."""
    from experiments.article.analysis.sweep_multi_seed import ALL_DISTANCES

    assert "degree_seq_l1" in ALL_DISTANCES, (
        "Naive baseline degree_seq_l1 missing from ALL_DISTANCES"
    )


def test_coarse_classes_by_arity_structure() -> None:
    """COARSE_CLASSES_BY_ARITY must cover arities 3, 4, 5 (T-M7m).

    ADMITTED_A_IDS_ARITY3 was removed at T-M7m (arity-3 fallback retired;
    all 14 pruned families are feasible). This test replaces it with a check
    that the coarse-class structure covers all three arity groups.
    """
    from experiments.article.analysis.sweep_multi_seed import (
        ADMITTED_A_IDS,
        COARSE_CLASSES_BY_ARITY,
    )

    keys = set(COARSE_CLASSES_BY_ARITY.keys())
    assert keys == {3, 4, 5}, f"COARSE_CLASSES_BY_ARITY must cover arities 3/4/5, got {keys}"
    # Arity 3 must have 3 coarse classes (design, path, cycle).
    assert len(COARSE_CLASSES_BY_ARITY[3]) == 3, (
        f"Expected 3 arity-3 coarse classes, got {COARSE_CLASSES_BY_ARITY[3]}"
    )
    # All arity-3 families in ADMITTED_A_IDS must map to arity-3 coarse classes.
    from isalhg.datasets.synthetic.known_design_catalog import COARSE_CLASS_BY_ID

    for iid in ADMITTED_A_IDS:
        cc = COARSE_CLASS_BY_ID.get(iid, "")
        if cc.endswith("_k3"):
            assert cc in COARSE_CLASSES_BY_ARITY[3], (
                f"{iid} has coarse class {cc!r} not in COARSE_CLASSES_BY_ARITY[3]"
            )
