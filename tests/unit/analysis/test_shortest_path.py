"""Unit tests for experiments.article.analysis.shortest_path (T-M5e).

Acceptance criteria:
- score_path_recovery: correctly identifies true intermediates in a recovered path.
- score_monotonicity: correctly counts path steps with increasing accumulated d_I.
- shortest_path_in_pool: finds the shortest weighted path via Dijkstra.
- decode_path_intermediates: S2H never rejects a canonical string (closed alphabet).

Tests are independent of disk I/O and of the full A4 experiment pipeline.
Each test is designed to fail before the implementation module exists.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers to make synthetic pool metadata (no actual hypergraphs needed)
# ---------------------------------------------------------------------------


def _pool_meta(specs: list[tuple[int, int, int]]) -> list[dict[str, Any]]:
    """Build minimal pool-metadata dicts from (ladder_id, step, budget) tuples."""
    return [
        {
            "idx": i,
            "ladder_id": lid,
            "step": step,
            "budget_from_base": budget,
            "item_id": f"L{lid}_t{step}",
        }
        for i, (lid, step, budget) in enumerate(specs)
    ]


# ---------------------------------------------------------------------------
# score_path_recovery
# ---------------------------------------------------------------------------


class TestScorePathRecovery:
    """Tests for score_path_recovery(path_idxs, pool_meta, target_ladder_id, start_idx, end_idx)."""

    def test_perfect_recovery(self) -> None:
        """Found path passes through all true intermediates in the correct order."""
        from experiments.article.analysis.shortest_path import score_path_recovery

        # Pool: 4 items on ladder 0 (steps 0-3) + 2 distractors on ladder 1
        meta = _pool_meta(
            [
                (0, 0, 0),  # idx 0 — H_A
                (0, 1, 3),  # idx 1 — true intermediate
                (0, 2, 7),  # idx 2 — true intermediate
                (0, 3, 10),  # idx 3 — H_B
                (1, 0, 0),  # idx 4 — distractor base
                (1, 1, 4),  # idx 5 — distractor step
            ]
        )
        # Found path goes through all true intermediates in order
        path_idxs = [0, 1, 2, 3]
        frac = score_path_recovery(path_idxs, meta, target_ladder_id=0, start_idx=0, end_idx=3)
        assert frac == pytest.approx(1.0), f"Expected 1.0, got {frac}"

    def test_no_recovery(self) -> None:
        """Found path goes through only distractors — zero true intermediates recovered."""
        from experiments.article.analysis.shortest_path import score_path_recovery

        meta = _pool_meta(
            [
                (0, 0, 0),
                (0, 1, 3),
                (0, 2, 7),
                (0, 3, 10),
                (1, 0, 0),
                (1, 1, 4),
            ]
        )
        # Path skips the true intermediates (goes through distractors 4, 5)
        path_idxs = [0, 4, 5, 3]
        frac = score_path_recovery(path_idxs, meta, target_ladder_id=0, start_idx=0, end_idx=3)
        assert frac == pytest.approx(0.0), f"Expected 0.0, got {frac}"

    def test_partial_recovery(self) -> None:
        """Found path passes through only one of two true intermediates."""
        from experiments.article.analysis.shortest_path import score_path_recovery

        meta = _pool_meta(
            [
                (0, 0, 0),
                (0, 1, 3),
                (0, 2, 7),
                (0, 3, 10),
                (1, 0, 0),
                (1, 1, 4),
            ]
        )
        path_idxs = [0, 1, 3]  # recovers idx=1 but misses idx=2
        frac = score_path_recovery(path_idxs, meta, target_ladder_id=0, start_idx=0, end_idx=3)
        assert frac == pytest.approx(0.5), f"Expected 0.5, got {frac}"

    def test_direct_path_no_intermediates(self) -> None:
        """Direct path H_A → H_B with no intermediate nodes: 0 recovered."""
        from experiments.article.analysis.shortest_path import score_path_recovery

        meta = _pool_meta([(0, 0, 0), (0, 1, 5), (0, 2, 10)])
        # Direct jump — no intermediates visited
        path_idxs = [0, 2]
        frac = score_path_recovery(path_idxs, meta, target_ladder_id=0, start_idx=0, end_idx=2)
        # true_intermediates = {idx 1}; recovered = {}
        assert frac == pytest.approx(0.0), f"Expected 0.0, got {frac}"

    def test_one_step_ladder_no_intermediates(self) -> None:
        """Ladder with t=1: no true intermediates exist; recovery is vacuously 1.0."""
        from experiments.article.analysis.shortest_path import score_path_recovery

        meta = _pool_meta([(0, 0, 0), (0, 1, 5)])
        path_idxs = [0, 1]
        frac = score_path_recovery(path_idxs, meta, target_ladder_id=0, start_idx=0, end_idx=1)
        # No true intermediates → vacuous 1.0
        assert frac == pytest.approx(1.0), f"Expected 1.0 (vacuous), got {frac}"


# ---------------------------------------------------------------------------
# score_monotonicity
# ---------------------------------------------------------------------------


class TestScoreMonotonicity:
    """Tests for score_monotonicity(path_idxs, D) -> float."""

    def test_all_positive_steps_fully_monotone(self) -> None:
        """All edge weights > 0 → every step strictly increases accumulated length."""
        from experiments.article.analysis.shortest_path import score_monotonicity

        # 4-node path: 0→1→2→3, all weights 1.0
        D = np.array(
            [
                [0.0, 1.0, 5.0, 10.0],
                [1.0, 0.0, 1.0, 5.0],
                [5.0, 1.0, 0.0, 1.0],
                [10.0, 5.0, 1.0, 0.0],
            ]
        )
        path = [0, 1, 2, 3]
        frac = score_monotonicity(path, D)
        assert frac == pytest.approx(1.0), f"Expected 1.0, got {frac}"

    def test_zero_weight_edge_reduces_monotonicity(self) -> None:
        """One zero-weight edge breaks strict monotonicity for that step."""
        from experiments.article.analysis.shortest_path import score_monotonicity

        D = np.array(
            [
                [0.0, 1.0, 1.0, 2.0],
                [1.0, 0.0, 0.0, 1.0],  # D[1,2] = 0
                [1.0, 0.0, 0.0, 1.0],
                [2.0, 1.0, 1.0, 0.0],
            ]
        )
        path = [0, 1, 2, 3]  # step 1→2 has weight 0 → not strictly increasing
        frac = score_monotonicity(path, D)
        # 3 steps total; 1 zero-weight step → 2 strictly increasing → frac = 2/3
        assert frac == pytest.approx(2.0 / 3.0, abs=1e-9), f"Expected 2/3, got {frac}"

    def test_single_step_path(self) -> None:
        """Path with one step (two nodes) is trivially fully monotone."""
        from experiments.article.analysis.shortest_path import score_monotonicity

        D = np.array([[0.0, 5.0], [5.0, 0.0]])
        frac = score_monotonicity([0, 1], D)
        assert frac == pytest.approx(1.0)

    def test_singleton_path_returns_one(self) -> None:
        """Path with single node has 0 steps — return 1.0 (vacuously monotone)."""
        from experiments.article.analysis.shortest_path import score_monotonicity

        D = np.zeros((1, 1))
        frac = score_monotonicity([0], D)
        assert frac == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# shortest_path_in_pool
# ---------------------------------------------------------------------------


class TestShortestPathInPool:
    """Tests for shortest_path_in_pool(D, start_idx, end_idx) -> list[int]."""

    def test_triangle_shortcut(self) -> None:
        """In a 3-node pool, takes the shortcut if it's cheaper."""
        from experiments.article.analysis.shortest_path import shortest_path_in_pool

        # Direct 0→2 costs 3; via 1 costs 1+1=2 → prefer via 1
        D = np.array([[0.0, 1.0, 3.0], [1.0, 0.0, 1.0], [3.0, 1.0, 0.0]], dtype=float)
        path = shortest_path_in_pool(D, 0, 2)
        assert path == [0, 1, 2], f"Expected [0,1,2], got {path}"

    def test_direct_preferred(self) -> None:
        """Direct 0→2 is cheaper than any intermediate."""
        from experiments.article.analysis.shortest_path import shortest_path_in_pool

        D = np.array([[0.0, 10.0, 1.0], [10.0, 0.0, 10.0], [1.0, 10.0, 0.0]], dtype=float)
        path = shortest_path_in_pool(D, 0, 2)
        assert path == [0, 2], f"Expected [0,2], got {path}"

    def test_start_equals_end(self) -> None:
        """Path from a node to itself is just [start_idx]."""
        from experiments.article.analysis.shortest_path import shortest_path_in_pool

        D = np.zeros((3, 3))
        path = shortest_path_in_pool(D, 1, 1)
        assert path == [1], f"Expected [1], got {path}"


# ---------------------------------------------------------------------------
# decode_path_intermediates (closed-alphabet check)
# ---------------------------------------------------------------------------


class TestDecodePathIntermediates:
    """Tests for decode_path_intermediates(canonical_strings, k) -> list[SparseHypergraph]."""

    def test_canonical_strings_always_decode(self) -> None:
        """Every canonical string of a pool item decodes to a valid hypergraph.

        Verifies the closed-alphabet invariant: S2H never rejects.
        """
        from experiments.article.analysis.shortest_path import decode_path_intermediates
        from isalhg.core.canonical import canonical_string, required_k
        from isalhg.datasets.synthetic.perturbation_ladder import PerturbationLadderHypergraphs

        ds = PerturbationLadderHypergraphs(
            n_nodes=5, n_edges=3, arity_range=(2, 3), max_t=5, n_ladders=2, seed=99
        )
        items = list(ds)
        hypergraphs = [it.hypergraph for it in items]
        k = max(required_k(H) for H in hypergraphs)
        w_stars = [canonical_string(H, k=k) for H in hypergraphs]

        decoded = decode_path_intermediates(w_stars, k)
        assert len(decoded) == len(hypergraphs), "Should decode all strings"
        for i, H in enumerate(decoded):
            assert H.n_nodes >= 1, f"item {i}: decoded n_nodes={H.n_nodes} < 1"
            assert H.n_edges >= 0, f"item {i}: decoded n_edges={H.n_edges} < 0"

    def test_empty_list(self) -> None:
        """Empty input returns empty list."""
        from experiments.article.analysis.shortest_path import decode_path_intermediates

        result = decode_path_intermediates([], k=2)
        assert result == []
