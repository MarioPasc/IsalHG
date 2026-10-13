"""Unit tests for the near-duplicate retrieval scorer (scripts/newpos/neardup.py)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "newpos"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from neardup import (  # noqa: E402
    block_ap,
    down_neighbours,
    holm,
    is_star,
    query_scores,
    rank_biserial,
)

from isalhg.datasets.kb.base import make_record  # noqa: E402

pytestmark = pytest.mark.unit


def _record(n: int, facts: list[tuple[int, tuple[int, ...]]]):
    rec = make_record("t", n, [0] * n, facts, require_connected=False)
    assert rec is not None
    return rec


def test_down_neighbours_counts_deletions_and_removals() -> None:
    # two binary facts sharing constant 0, one ternary fact
    rec = _record(5, [(0, (0, 1)), (1, (0, 2)), (2, (0, 3, 4))])
    kinds = [k for k, _ in down_neighbours(rec)]
    assert kinds.count("delete_fact") == 3
    assert kinds.count("remove_constant") == 2 + 2 + 3


def test_down_neighbours_skip_duplicate_facts() -> None:
    # removing 2 from (0,(0,1,2)) duplicates the fact (0,(0,1)): skipped
    rec = _record(3, [(0, (0, 1)), (0, (0, 1, 2))])
    removed = [f for k, f in down_neighbours(rec) if k == "remove_constant"]
    assert all(len(set(f)) == len(f) for f in removed)
    assert len(removed) == 2 + 2  # (0,1)->2 singletons, (0,1,2) minus 0 or 1


@pytest.mark.parametrize(
    ("facts", "star"),
    [
        ([(0, (0, 1)), (1, (0, 2))], True),
        ([(0, (0, 1)), (1, (0, 1))], False),
        ([(0, (0, 1)), (1, (1, 2))], True),
        ([(0, (0, 1)), (1, (1, 2)), (2, (2, 3))], False),
    ],
)
def test_is_star(facts: list[tuple[int, tuple[int, ...]]], star: bool) -> None:
    n = 1 + max(a for _, args in facts for a in args)
    assert is_star(_record(n, facts)) is star


def test_block_ap_perfect_and_tied() -> None:
    np.testing.assert_allclose(block_ap(np.array([0.0, 1.0, 2.0]), np.array([1, 0, 0], bool)), 1.0)
    # one positive tied with three negatives at the top: precision 1/4
    s = np.array([1.0, 1.0, 1.0, 1.0, 5.0])
    y = np.array([1, 0, 0, 0, 0], bool)
    np.testing.assert_allclose(block_ap(s, y), 0.25)


def test_query_scores_expected_rank_under_ties() -> None:
    d = np.array([1.0, 1.0, 1.0, 3.0])
    pos = np.array([True, False, False, False])
    rr, hit1, hit10, _ = query_scores(d, pos)
    # one positive among three tied at the top: expected rank 1 + 2/2 = 2
    np.testing.assert_allclose(rr, 0.5)
    np.testing.assert_allclose(hit1, 1 / 3)
    np.testing.assert_allclose(hit10, 1.0)


def test_query_scores_strict_better_counts() -> None:
    d = np.array([0.5, 2.0, 2.0])
    pos = np.array([False, True, False])
    rr, hit1, _, _ = query_scores(d, pos)
    np.testing.assert_allclose(rr, 1 / 2.5)
    assert hit1 == 0.0


def test_holm_monotone_and_capped() -> None:
    out = holm({"a": 0.01, "b": 0.04, "c": 0.5})
    assert out["a"] == pytest.approx(0.03)
    assert out["b"] == pytest.approx(0.08)
    assert out["c"] == pytest.approx(0.5)


def test_rank_biserial_extremes() -> None:
    x = np.array([1.0, 2.0, 3.0])
    assert rank_biserial(x, x - 1) == pytest.approx(1.0)
    assert rank_biserial(x, x + 1) == pytest.approx(-1.0)
    assert rank_biserial(x, x) == 0.0
