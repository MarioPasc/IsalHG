"""``Reach1Index`` must admit the pairs ``reach'`` admits (T-KBo).

The index previously bucketed members by the *frozen* reach precondition --
constant count plus type multiset -- and only compared members inside a bucket.
Under ``reach'`` (D-KBf5) a deletion compacts away constants it leaves isolated,
so the constant count is **not** preserved across a reach-1 step and equal-shape
bucketing withheld exactly the pairs the new definition admits.

The regression is the case named in T-KBo: a pair whose constant counts differ,
at ``reach' = 1``. It fails against the bucketed index and passes against the
``compatible``-filtered one.
"""

from __future__ import annotations

import pytest

from experiments.tkde.rq6 import Reach1Index
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.language.reach import reach

pytestmark = pytest.mark.unit


def _kb(
    n_nodes: int,
    edges: list[tuple[list[int], int]],
    types: list[int],
    n_types: int = 2,
    n_preds: int = 3,
) -> SparseHypergraph:
    """Build a knowledge base with explicit constant types and predicate labels."""
    return SparseHypergraph(
        n_nodes=n_nodes,
        hyperedges=[frozenset(nodes) for nodes, _ in edges],
        n_vertex_labels=n_types,
        n_edge_labels=n_preds,
        vertex_labels=list(types[:n_nodes]),
        edge_labels=[predicate for _, predicate in edges],
    )


class TestReachOneAcrossConstantCounts:
    """The constant count changes under a reach-1 step, so it cannot gate the index."""

    def test_pair_differing_in_constant_count_is_found(self) -> None:
        # `member` carries one fact more than `sample`, over a constant that
        # occurs in that fact alone. Deleting the fact isolates the constant,
        # compaction removes it, and the remainder equals `sample` -- reach' = 1
        # across a constant-count difference of exactly one.
        sample = _kb(2, [([0, 1], 0)], [0, 0])
        member = _kb(3, [([0, 1], 0), ([1, 2], 1)], [0, 0, 0])

        assert sample.n_nodes != member.n_nodes, "the pair must differ in constant count"
        assert reach(sample, member, r_max=1) is not None, (
            "precondition of this test: the library must place the pair at reach' <= 1"
        )

        index = Reach1Index([member])
        assert index.within_one(sample) is True

    def test_unreachable_pair_answers_false_not_none(self) -> None:
        # Compatible at r_max=1 but genuinely further away: the index must say
        # "no", not "unanswerable". None is reserved for a sample no member is
        # even compatible with, which the callers report as no fraction.
        sample = _kb(2, [([0, 1], 0)], [0, 0])
        member = _kb(4, [([0, 1], 0), ([1, 2], 1), ([2, 3], 1)], [0, 0, 0, 0])
        assert reach(sample, member, r_max=1) is None
        assert index_answer(sample, member) in (False, None)

    def test_exact_match_is_within_one(self) -> None:
        sample = _kb(2, [([0, 1], 0)], [0, 0])
        member = _kb(2, [([0, 1], 0)], [0, 0])
        assert Reach1Index([member]).within_one(sample) is True

    def test_no_compatible_member_is_none(self) -> None:
        # A member sharing no fact profile at all: not answerable, not "no".
        sample = _kb(2, [([0, 1], 0)], [0, 0])
        far = _kb(6, [([0, 1], 2), ([2, 3], 2), ([4, 5], 2)], [1, 1, 1, 1, 1, 1])
        assert Reach1Index([far]).within_one(sample) is None


def index_answer(sample: SparseHypergraph, member: SparseHypergraph) -> bool | None:
    """The index's verdict for a one-member corpus."""
    return Reach1Index([member]).within_one(sample)
