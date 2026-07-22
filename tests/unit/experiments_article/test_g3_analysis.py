"""Unit tests for G3 OFAT analysis module — new numeric fields (T-M7f review round 2).

Tests cover the four review items:
  R1: full pairwise d_I matrix in JSON (compute_full_pairwise_matrix,
      compute_nu_from_matrix, compute_mds_from_matrix)
  R2: nauty jump statistic (mds_jump_stat, G3AxisResult.continuity_nauty)
  R3: M3 depth — loose_path_k5_n13 in default_g3_config
  R4: artifact fields match new G3AxisResult schema

Each test is designed to FAIL against the pre-fix behaviour (old g3_analysis.py
lacked these functions; the new schema adds fields not present before).
"""

from __future__ import annotations

import numpy as np
import pytest

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def small_steps():
    """A short M1 OFAT sequence (T=3) from a tight 3-cycle base."""
    import random

    from experiments.article.g3_sequence import OfatAxis, generate_ofat_sequence
    from isalhg.datasets.synthetic.known_design_catalog import tight_cycle

    H0 = tight_cycle(3, 5)
    rng = random.Random(7)
    return generate_ofat_sequence(H0, OfatAxis.M1, T=3, rng=rng)


@pytest.fixture()
def tiny_steps():
    """A minimal sequence of length 2 (H_0 and H_1) for edge-case testing."""
    import random

    from experiments.article.g3_sequence import OfatAxis, generate_ofat_sequence
    from isalhg.datasets.synthetic.known_design_catalog import tight_cycle

    H0 = tight_cycle(3, 5)
    rng = random.Random(3)
    return generate_ofat_sequence(H0, OfatAxis.M1, T=1, rng=rng)


# ---------------------------------------------------------------------------
# R1a — compute_full_pairwise_matrix
# ---------------------------------------------------------------------------


class TestComputeFullPairwiseMatrix:
    def test_returns_square_matrix(self, small_steps):
        from experiments.article.g3_analysis import compute_full_pairwise_matrix

        D, _ = compute_full_pairwise_matrix(small_steps, "isalhg_levenshtein")
        n = len(small_steps)
        assert len(D) == n
        for row in D:
            assert len(row) == n

    def test_diagonal_is_zero(self, small_steps):
        from experiments.article.g3_analysis import compute_full_pairwise_matrix

        D, _ = compute_full_pairwise_matrix(small_steps, "isalhg_levenshtein")
        for i in range(len(D)):
            assert D[i][i] == 0.0

    def test_symmetric(self, small_steps):
        from experiments.article.g3_analysis import compute_full_pairwise_matrix

        D, _ = compute_full_pairwise_matrix(small_steps, "isalhg_levenshtein")
        n = len(D)
        for i in range(n):
            for j in range(n):
                v_ij = D[i][j]
                v_ji = D[j][i]
                if v_ij is None or v_ji is None:
                    assert v_ij is None and v_ji is None
                else:
                    assert abs(v_ij - v_ji) < 1e-9, f"D[{i}][{j}]={v_ij} != D[{j}][{i}]={v_ji}"

    def test_off_diagonal_nonnegative(self, small_steps):
        from experiments.article.g3_analysis import compute_full_pairwise_matrix

        D, _ = compute_full_pairwise_matrix(small_steps, "isalhg_levenshtein")
        n = len(D)
        for i in range(n):
            for j in range(n):
                if i != j and D[i][j] is not None:
                    assert D[i][j] >= 0.0

    def test_d_matrix_row0_matches_sequence_distances(self, small_steps):
        """Row 0 of the full matrix equals d(H_0, H_t) for all t."""
        from experiments.article.g3_analysis import (
            compute_full_pairwise_matrix,
            compute_sequence_distances,
        )

        D, _ = compute_full_pairwise_matrix(small_steps, "isalhg_levenshtein")
        d_from_base = compute_sequence_distances(small_steps, ["isalhg_levenshtein"])[
            "isalhg_levenshtein"
        ]
        for t, expected in enumerate(d_from_base):
            assert D[0][t] == expected, f"Step {t}: full matrix row0={D[0][t]}, expected={expected}"


# ---------------------------------------------------------------------------
# R1b — compute_nu_from_matrix
# ---------------------------------------------------------------------------


class TestComputeNuFromMatrix:
    def test_returns_same_length_as_steps(self, small_steps):
        from experiments.article.g3_analysis import (
            compute_full_pairwise_matrix,
            compute_nu_from_matrix,
        )

        D, _ = compute_full_pairwise_matrix(small_steps, "isalhg_levenshtein")
        nus = compute_nu_from_matrix(D)
        assert len(nus) == len(small_steps)

    def test_first_entry_is_zero(self, small_steps):
        """Single-point prefix: nu is 0 by definition."""
        from experiments.article.g3_analysis import (
            compute_full_pairwise_matrix,
            compute_nu_from_matrix,
        )

        D, _ = compute_full_pairwise_matrix(small_steps, "isalhg_levenshtein")
        nus = compute_nu_from_matrix(D)
        assert nus[0] == 0.0

    def test_entries_in_unit_interval(self, small_steps):
        from experiments.article.g3_analysis import (
            compute_full_pairwise_matrix,
            compute_nu_from_matrix,
        )

        D, _ = compute_full_pairwise_matrix(small_steps, "isalhg_levenshtein")
        nus = compute_nu_from_matrix(D)
        for v in nus:
            if v is not None:
                assert 0.0 <= v <= 1.0, f"nu={v} outside [0,1]"

    def test_agrees_with_point_wise_computation(self, small_steps):
        """compute_nu_from_matrix must give same results as compute_nu_trajectory."""
        from experiments.article.g3_analysis import (
            compute_full_pairwise_matrix,
            compute_nu_from_matrix,
            compute_nu_trajectory,
        )

        D, _ = compute_full_pairwise_matrix(small_steps, "isalhg_levenshtein")
        nus_matrix = compute_nu_from_matrix(D)
        nus_pointwise = compute_nu_trajectory(small_steps, "isalhg_levenshtein")

        assert len(nus_matrix) == len(nus_pointwise)
        for i, (a, b) in enumerate(zip(nus_matrix, nus_pointwise, strict=False)):
            if a is None and b is None:
                continue
            assert a is not None and b is not None, f"Mismatch at index {i}: {a} vs {b}"
            np.testing.assert_allclose(a, b, rtol=1e-6, err_msg=f"nu mismatch at index {i}")


# ---------------------------------------------------------------------------
# R1c — compute_mds_from_matrix
# ---------------------------------------------------------------------------


class TestComputeMdsFromMatrix:
    def test_returns_ndarray_with_correct_shape(self, small_steps):
        from experiments.article.g3_analysis import (
            compute_full_pairwise_matrix,
            compute_mds_from_matrix,
        )

        D, _ = compute_full_pairwise_matrix(small_steps, "isalhg_levenshtein")
        coords = compute_mds_from_matrix(D, n_dims=2)
        assert coords is not None
        assert coords.shape == (len(small_steps), 2)

    def test_returns_none_when_matrix_has_none(self, tiny_steps):
        """If any matrix entry is None, embedding returns None."""
        from experiments.article.g3_analysis import compute_mds_from_matrix

        D: list[list[float | None]] = [[0.0, None], [None, 0.0]]
        coords = compute_mds_from_matrix(D)
        assert coords is None


# ---------------------------------------------------------------------------
# R2 — mds_jump_stat and nu_sign_summary
# ---------------------------------------------------------------------------


class TestMdsJumpStat:
    def test_returns_dict_with_expected_keys(self, small_steps):
        from experiments.article.g3_analysis import (
            compute_full_pairwise_matrix,
            compute_mds_from_matrix,
            mds_jump_stat,
        )

        D, _ = compute_full_pairwise_matrix(small_steps, "isalhg_levenshtein")
        coords = compute_mds_from_matrix(D)
        stat = mds_jump_stat(coords)
        assert "max_jump" in stat
        assert "median_step" in stat
        assert "ratio" in stat

    def test_max_jump_is_nonneg(self, small_steps):
        from experiments.article.g3_analysis import (
            compute_full_pairwise_matrix,
            compute_mds_from_matrix,
            mds_jump_stat,
        )

        D, _ = compute_full_pairwise_matrix(small_steps, "isalhg_levenshtein")
        coords = compute_mds_from_matrix(D)
        stat = mds_jump_stat(coords)
        if stat["max_jump"] is not None:
            assert stat["max_jump"] >= 0.0

    def test_none_on_none_coords(self):
        from experiments.article.g3_analysis import mds_jump_stat

        stat = mds_jump_stat(None)
        assert stat["max_jump"] is None
        assert stat["median_step"] is None
        assert stat["ratio"] is None

    def test_known_coords(self):
        """Coords on a straight line: all steps equal, ratio=1."""
        from experiments.article.g3_analysis import mds_jump_stat

        coords = np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0], [3.0, 0.0]])
        stat = mds_jump_stat(coords)
        np.testing.assert_allclose(stat["max_jump"], 1.0, atol=1e-9)
        np.testing.assert_allclose(stat["median_step"], 1.0, atol=1e-9)
        np.testing.assert_allclose(stat["ratio"], 1.0, atol=1e-9)


class TestNuSignSummary:
    def test_all_none_returns_none(self):
        from experiments.article.g3_analysis import nu_sign_summary

        assert nu_sign_summary([None, None, None]) is None

    def test_near_zero_detected(self):
        from experiments.article.g3_analysis import nu_sign_summary

        assert nu_sign_summary([0.0, 0.0, 0.0]) == "near_zero"

    def test_monotone_increase(self):
        from experiments.article.g3_analysis import nu_sign_summary

        assert nu_sign_summary([0.0, 0.01, 0.02, 0.03, 0.04]) == "increases"

    def test_monotone_decrease(self):
        from experiments.article.g3_analysis import nu_sign_summary

        assert nu_sign_summary([0.05, 0.03, 0.01, 0.0]) == "decreases"

    def test_mixed_label(self):
        from experiments.article.g3_analysis import nu_sign_summary

        # Alternating: 2 increases, 2 decreases in 4 transitions
        vals = [0.01, 0.05, 0.02, 0.06, 0.03]
        result = nu_sign_summary(vals)
        assert result == "mixed"


# ---------------------------------------------------------------------------
# R3 — M3 depth: loose_path_k5_n13 in default config and _build_base
# ---------------------------------------------------------------------------


class TestM3LoosePath:
    def test_loose_path_k5_n13_in_default_config(self):
        """Review item R3: loose_path_k5_n13 must appear in default_g3_config."""
        from experiments.article.g3_analysis import default_g3_config

        configs = default_g3_config()
        m3_bases = [c["base_name"] for c in configs if c["axis"] == "M3"]
        assert "loose_path_k5_n13" in m3_bases, (
            f"R3 FAIL: loose_path_k5_n13 not in M3 configs; found: {m3_bases}"
        )

    def test_loose_path_k5_n13_builds_correctly(self):
        """The base hypergraph has n=13, m=3, uniform arity=5."""
        from experiments.article.g3_analysis import _build_base

        H = _build_base("loose_path_k5_n13")
        assert H.n_nodes == 13, f"Expected n=13, got {H.n_nodes}"
        assert H.n_edges == 3, f"Expected m=3, got {H.n_edges}"
        for e in range(H.n_edges):
            assert len(H.members(e)) == 5, f"Edge {e} has arity {len(H.members(e))}, expected 5"

    def test_m3_configs_all_have_vm_k(self):
        """All M3 configs must declare vm_k (the fixed VM k for the sequence)."""
        from experiments.article.g3_analysis import default_g3_config

        configs = default_g3_config()
        for cfg in configs:
            if cfg["axis"] == "M3":
                assert "vm_k" in cfg, f"M3 config {cfg['base_name']} missing vm_k"
                assert isinstance(cfg["vm_k"], int), (
                    f"M3 config {cfg['base_name']} vm_k is not int: {cfg['vm_k']}"
                )


# ---------------------------------------------------------------------------
# R4 — G3AxisResult has all required new fields
# ---------------------------------------------------------------------------


class TestG3AxisResultSchema:
    """Review item R4: G3AxisResult must carry d_matrix_isalhg, d_matrix_nauty,
    mds_coords_isalhg, mds_coords_nauty, continuity_isalhg, continuity_nauty,
    nu_sign, vm_k."""

    @pytest.fixture()
    def sample_result(self, small_steps, tmp_path):
        """Run one M1 axis and return the G3AxisResult."""
        import random

        from experiments.article.g3_analysis import (
            OfatAxis,  # re-exported
            run_ofat_axis,
        )
        from isalhg.datasets.synthetic.known_design_catalog import tight_cycle

        H0 = tight_cycle(3, 5)
        rng = random.Random(42)
        return run_ofat_axis(
            H_0=H0,
            axis=OfatAxis.M1,
            base_design_name="tight_cycle_k3_n5",
            T=3,
            rng=rng,
            output_dir=tmp_path,
            distance_names=["isalhg_levenshtein", "nauty_levi_edit"],
            vm_k=None,
        )

    def test_has_d_matrix_isalhg(self, sample_result):
        assert hasattr(sample_result, "d_matrix_isalhg")
        D = sample_result.d_matrix_isalhg
        n = sample_result.T_achieved + 1
        assert len(D) == n
        assert all(len(row) == n for row in D)

    def test_has_d_matrix_nauty(self, sample_result):
        assert hasattr(sample_result, "d_matrix_nauty")
        D = sample_result.d_matrix_nauty
        n = sample_result.T_achieved + 1
        assert len(D) == n

    def test_has_mds_coords_isalhg(self, sample_result):
        assert hasattr(sample_result, "mds_coords_isalhg")
        coords = sample_result.mds_coords_isalhg
        if coords is not None:
            assert len(coords) == sample_result.T_achieved + 1
            assert all(len(row) == 2 for row in coords)

    def test_has_mds_coords_nauty(self, sample_result):
        assert hasattr(sample_result, "mds_coords_nauty")

    def test_has_continuity_isalhg(self, sample_result):
        assert hasattr(sample_result, "continuity_isalhg")
        stat = sample_result.continuity_isalhg
        assert "max_jump" in stat
        assert "median_step" in stat
        assert "ratio" in stat

    def test_has_continuity_nauty(self, sample_result):
        assert hasattr(sample_result, "continuity_nauty")
        stat = sample_result.continuity_nauty
        assert "max_jump" in stat
        assert "median_step" in stat

    def test_has_nu_sign(self, sample_result):
        assert hasattr(sample_result, "nu_sign")
        # nu_sign must be one of the valid strings or None
        valid = {"increases", "decreases", "near_zero", "mixed", None}
        assert sample_result.nu_sign in valid, f"Invalid nu_sign: {sample_result.nu_sign!r}"

    def test_has_vm_k(self, sample_result):
        assert hasattr(sample_result, "vm_k")
        # For M1, vm_k is None
        assert sample_result.vm_k is None

    def test_nu_trajectory_not_all_none(self, sample_result):
        """Review item R1: nu_trajectory must have real values (not all-None)."""
        nus = sample_result.nu_trajectory
        assert any(v is not None for v in nus), (
            "R1 FAIL: nu_trajectory is all-None; MDS/ν computation must be run for all axes"
        )

    def test_json_serializable(self, sample_result, tmp_path):
        """to_dict() must produce JSON-serializable output with all new keys."""
        import json

        d = sample_result.to_dict()
        # Round-trip through JSON
        json_str = json.dumps(d, default=str)
        d2 = json.loads(json_str)
        assert "d_matrix_isalhg" in d2
        assert "d_matrix_nauty" in d2
        assert "mds_coords_isalhg" in d2
        assert "mds_coords_nauty" in d2
        assert "continuity_isalhg" in d2
        assert "continuity_nauty" in d2
        assert "nu_sign" in d2
        assert "vm_k" in d2


# ---------------------------------------------------------------------------
# Regression: old nu_trajectory = all-None must now have values (R1)
# ---------------------------------------------------------------------------


class TestNuNotAllNone:
    """Regression: before the fix, M3/M4/M5 axes had nu_trajectory = [null, null, ...].
    After the fix, compute_nu_from_matrix uses the precomputed d_matrix_isalhg,
    so real values must appear.

    This test demonstrates the failure against old behavior by verifying that
    compute_nu_from_matrix on a valid distance matrix produces non-None values."""

    def test_nu_from_non_null_matrix_is_not_all_none(self, small_steps):
        from experiments.article.g3_analysis import (
            compute_full_pairwise_matrix,
            compute_nu_from_matrix,
        )

        D, _ = compute_full_pairwise_matrix(small_steps, "isalhg_levenshtein")
        nus = compute_nu_from_matrix(D)
        # At least some entries must be non-None (the whole-matrix case)
        non_none = [v for v in nus if v is not None]
        assert len(non_none) > 0, "All nu values are None — precomputed matrix is not being used"

    def test_old_skip_mds_nu_path_no_longer_exists(self):
        """The old run_ofat_axis had a skip_mds_nu parameter that caused all-None.
        After the fix, this parameter must not exist (R1: always compute)."""
        import inspect

        from experiments.article.g3_analysis import run_ofat_axis

        sig = inspect.signature(run_ofat_axis)
        assert "skip_mds_nu" not in sig.parameters, (
            "R1 FAIL: run_ofat_axis still has skip_mds_nu parameter; MDS/ν must always be computed"
        )
