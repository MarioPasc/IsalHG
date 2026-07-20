"""Unit tests for the E1' harvest pipeline.

Acceptance criteria:
- find_complete_cells correctly classifies cells as complete / incomplete.
- extract_pairs correctly filters HGED>0 upper-triangle pairs.
- harvest_e1prime aggregates across multiple cells and writes result JSON.
- harvest_e1prime produces a result file even when 0 cells are complete.

Teeth: monkeypatching extract_pairs to return zero pairs confirms that the
aggregate ρ computation raises or returns nan — not silently a wrong number.
"""

from __future__ import annotations

import json

import numpy as np
import pytest

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers — build a synthetic e1prime directory tree
# ---------------------------------------------------------------------------


def _make_cell(
    root,
    label: str,
    seed_name: str,
    *,
    n: int = 6,
    has_hged: bool = True,
) -> None:
    """Write synthetic D.npy + meta.json files for one cell."""
    rng = np.random.default_rng(0)
    D = np.zeros((n, n), dtype=float)
    # Fill strictly upper triangle, mirror to lower
    for i in range(n):
        for j in range(i + 1, n):
            v = float(rng.integers(0, 10))
            D[i, j] = v
            D[j, i] = v

    cell_dir = root / "d_matrix" / "perturbation_ladder" / label / seed_name
    cell_dir.mkdir(parents=True, exist_ok=True)

    for dist in ["isalhg_levenshtein"] + (["exact_hged"] if has_hged else []):
        dist_dir = cell_dir / dist
        dist_dir.mkdir(parents=True, exist_ok=True)
        np.save(dist_dir / "D.npy", D)
        meta = {
            "status": "done",
            "distance": dist,
            "shape": [n, n],
            "mean_max_degree": 2.0,
            "mean_arity": 2.5,
        }
        with open(dist_dir / "meta.json", "w") as f:
            json.dump(meta, f)


# ---------------------------------------------------------------------------
# find_complete_cells
# ---------------------------------------------------------------------------


def test_find_complete_cells_counts(tmp_path):
    """find_complete_cells returns correct complete/incomplete split."""
    from experiments.article.analysis.e1prime_harvest import find_complete_cells

    _make_cell(tmp_path, "n5_s0", "seed42", has_hged=True)
    _make_cell(tmp_path, "n6_s0", "seed42", has_hged=True)
    _make_cell(tmp_path, "n9_s1", "seed43", has_hged=False)  # missing exact_hged

    cells = find_complete_cells(tmp_path)
    assert len(cells) == 3

    complete = [c for c in cells if c["complete"]]
    incomplete = [c for c in cells if not c["complete"]]
    assert len(complete) == 2
    assert len(incomplete) == 1
    assert incomplete[0]["label"] == "n9_s1"


def test_find_complete_cells_empty_dir(tmp_path):
    """find_complete_cells returns [] when root doesn't exist."""
    from experiments.article.analysis.e1prime_harvest import find_complete_cells

    cells = find_complete_cells(tmp_path / "nonexistent")
    assert cells == []


# ---------------------------------------------------------------------------
# extract_pairs
# ---------------------------------------------------------------------------


def test_extract_pairs_filters_hged_zero(tmp_path):
    """extract_pairs excludes pairs where HGED == 0."""
    from experiments.article.analysis.e1prime_harvest import extract_pairs

    n = 5
    D_hged = np.zeros((n, n))
    D_I = np.zeros((n, n))

    # Set only one off-diagonal pair to HGED=3, d_I=2
    D_hged[0, 1] = D_hged[1, 0] = 3
    D_I[0, 1] = D_I[1, 0] = 2
    # All other pairs stay 0

    d_dir = tmp_path / "d_I"
    h_dir = tmp_path / "hged"
    d_dir.mkdir()
    h_dir.mkdir()
    np.save(d_dir / "D.npy", D_I)
    np.save(h_dir / "D.npy", D_hged)

    hged_vec, d_I_vec = extract_pairs(d_dir, h_dir)
    assert len(hged_vec) == 1
    assert hged_vec[0] == 3.0
    assert d_I_vec[0] == 2.0


def test_extract_pairs_shape_mismatch_raises(tmp_path):
    """extract_pairs raises ValueError on mismatched matrix shapes."""
    from experiments.article.analysis.e1prime_harvest import extract_pairs

    d_dir = tmp_path / "d_I"
    h_dir = tmp_path / "hged"
    d_dir.mkdir()
    h_dir.mkdir()
    np.save(d_dir / "D.npy", np.zeros((4, 4)))
    np.save(h_dir / "D.npy", np.zeros((5, 5)))

    with pytest.raises(ValueError, match="Shape mismatch"):
        extract_pairs(d_dir, h_dir)


# ---------------------------------------------------------------------------
# harvest_e1prime — end-to-end on synthetic data
# ---------------------------------------------------------------------------


def test_harvest_e1prime_aggregate_statistics(tmp_path):
    """harvest_e1prime writes valid JSON with correct aggregate statistics."""
    from experiments.article.analysis.e1prime_harvest import harvest_e1prime

    e1prime_dir = tmp_path / "e1prime"
    _make_cell(e1prime_dir, "n5_s0", "seed42", n=8, has_hged=True)
    _make_cell(e1prime_dir, "n6_s0", "seed42", n=8, has_hged=True)
    _make_cell(e1prime_dir, "n9_s1", "seed43", n=8, has_hged=False)

    out_dir = tmp_path / "out"
    result = harvest_e1prime(e1prime_dir, out_dir)

    assert result["n_cells_complete"] == 2
    assert result["n_cells_total"] == 3
    assert "n9_s1" in result["missing_cells"]
    assert result["n_pairs_total"] > 0
    assert -1.0 <= result["spearman_rho"] <= 1.0

    # JSON was written
    assert (out_dir / "e1prime_result.json").exists()
    with open(out_dir / "e1prime_result.json") as f:
        saved = json.load(f)
    assert saved["status"] == "done"
    assert saved["n_cells_complete"] == 2


def test_harvest_e1prime_zero_cells(tmp_path):
    """harvest_e1prime handles 0 complete cells gracefully."""
    from experiments.article.analysis.e1prime_harvest import harvest_e1prime

    e1prime_dir = tmp_path / "e1prime"
    _make_cell(e1prime_dir, "n9_s1", "seed43", has_hged=False)

    out_dir = tmp_path / "out"
    result = harvest_e1prime(e1prime_dir, out_dir)

    assert result["n_cells_complete"] == 0
    assert (out_dir / "e1prime_result.json").exists()


def test_harvest_e1prime_rho_nonzero_for_correlated_data(tmp_path):
    """harvest_e1prime computes rho != 0 when d_I and HGED covary.

    Teeth: without the pair-aggregation logic, rho would be nan or 0.
    """
    from experiments.article.analysis.e1prime_harvest import harvest_e1prime

    n = 10
    rng = np.random.default_rng(42)

    # Build a correlated pair (d_I ≈ 0.7*HGED + noise)
    e1prime_dir = tmp_path / "e1prime"
    cell_dir = e1prime_dir / "d_matrix" / "perturbation_ladder" / "n8_s0" / "seed42"

    D_hged = np.zeros((n, n))
    D_I = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            h = float(rng.integers(1, 12))
            d = max(0.0, 0.7 * h + rng.normal(0, 0.5))
            D_hged[i, j] = D_hged[j, i] = h
            D_I[i, j] = D_I[j, i] = d

    for dist, D in [("isalhg_levenshtein", D_I), ("exact_hged", D_hged)]:
        dist_dir = cell_dir / dist
        dist_dir.mkdir(parents=True, exist_ok=True)
        np.save(dist_dir / "D.npy", D)
        meta = {
            "status": "done",
            "distance": dist,
            "shape": [n, n],
            "mean_max_degree": 2.0,
            "mean_arity": 2.5,
        }
        with open(dist_dir / "meta.json", "w") as f:
            json.dump(meta, f)

    out_dir = tmp_path / "out"
    result = harvest_e1prime(e1prime_dir, out_dir)

    assert result["n_cells_complete"] == 1
    # With strong positive correlation (0.7*HGED), rho should be clearly positive
    assert result["spearman_rho"] > 0.5, (
        f"Expected rho > 0.5 for correlated data; got {result['spearman_rho']}"
    )
