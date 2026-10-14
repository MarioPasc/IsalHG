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

import random

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
        assert index_answer(sample, member) is False

    def test_exact_match_is_within_one(self) -> None:
        sample = _kb(2, [([0, 1], 0)], [0, 0])
        member = _kb(2, [([0, 1], 0)], [0, 0])
        assert Reach1Index([member]).within_one(sample) is True

    def test_an_empty_fact_count_window_is_False_not_None(self) -> None:
        """An empty window is a proof of "no", never an inability to answer.

        The fact-count window is a *necessary* condition for ``reach' <= 1``, so
        no member inside it means no member within reach 1. Returning ``None``
        here excluded such samples from the ``reach1_eligible`` denominator and
        inflated the rate 2.18x on wd50k66/incidence_ngram.
        """
        sample = _kb(2, [([0, 1], 0)], [0, 0])
        far = _kb(6, [([0, 1], 2), ([2, 3], 2), ([4, 5], 2)], [1, 1, 1, 1, 1, 1])
        assert far.n_edges - sample.n_edges > 1, "the window must really be empty"
        assert Reach1Index([far]).within_one(sample) is False
        assert reach(sample, far, r_max=1) is None, "and the answer is genuinely no"


def index_answer(sample: SparseHypergraph, member: SparseHypergraph) -> bool:
    """The index's verdict for a one-member corpus."""
    return Reach1Index([member]).within_one(sample)


class TestFactCountBucketIsExact:
    """The bucket key must never exclude a pair the definition admits.

    ``Reach1Index`` scans only members whose fact count is within one of the
    sample's. The argument: isomorphic compacted remainders carry equally many
    facts, so ``m - |A| = m2 - |B|`` with ``|A| + |B| <= 1`` forces
    ``|m - m2| <= 1``. The proof is short enough to be wrong, so it is also
    measured over random pairs.
    """

    @staticmethod
    def _random_kb(rng: random.Random, n_nodes: int, n_facts: int) -> SparseHypergraph:
        edges: set[frozenset[int]] = set()
        guard = 0
        while len(edges) < n_facts and guard < 200:
            guard += 1
            size = rng.choice((2, 2, 3))
            if size > n_nodes:
                continue
            edges.add(frozenset(rng.sample(range(n_nodes), size)))
        ordered = sorted(edges, key=sorted)
        return SparseHypergraph(
            n_nodes=n_nodes,
            hyperedges=ordered,
            n_vertex_labels=2,
            n_edge_labels=2,
            vertex_labels=[rng.randrange(2) for _ in range(n_nodes)],
            edge_labels=[rng.randrange(2) for _ in ordered],
        )

    def test_no_reachable_pair_is_outside_the_bucket(self) -> None:
        rng = random.Random(20260910)
        checked = admitted = 0
        for _ in range(300):
            a = self._random_kb(rng, rng.randint(3, 6), rng.randint(2, 5))
            b = self._random_kb(rng, rng.randint(3, 6), rng.randint(2, 5))
            if a.n_edges == 0 or b.n_edges == 0:
                continue
            checked += 1
            if reach(a, b, r_max=1) is not None:
                admitted += 1
                assert abs(a.n_edges - b.n_edges) <= 1, (
                    f"reach' <= 1 across a fact-count gap of "
                    f"{abs(a.n_edges - b.n_edges)}; the bucket key is unsound"
                )
        assert checked > 100, f"only {checked} pairs exercised"
        assert admitted > 0, "no pair was within reach 1; the test asserts nothing"

    def test_index_agrees_with_a_brute_force_scan(self) -> None:
        rng = random.Random(4242)
        members = [self._random_kb(rng, rng.randint(3, 5), rng.randint(2, 4)) for _ in range(12)]
        members = [H for H in members if H.n_edges > 0]
        index = Reach1Index(members)
        disagreements = 0
        for _ in range(60):
            sample = self._random_kb(rng, rng.randint(3, 5), rng.randint(2, 4))
            if sample.n_edges == 0:
                continue
            brute = any(reach(sample, H, r_max=1) is not None for H in members)
            answer = index.within_one(sample)
            if brute and answer is not True:
                disagreements += 1
        assert disagreements == 0, f"{disagreements} reachable samples were missed by the index"
