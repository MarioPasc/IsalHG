"""Reach is exact, symmetric, and agrees with an independent brute force.

The definition of done for ``reach`` is three claims.  The pinned cases fix the
semantics on hand-built inputs (0 for an isomorphic pair, 1 for one inserted
fact, 2 for one substituted fact, ``None`` past the radius).  Symmetry is
checked on 300 random near-neighbour pairs, because the definition is symmetric
and an asymmetric implementation would silently break the consensus objective.
The brute-force agreement on 200 random cases is the exactness check: the
reference enumerates the same deletion pairs but adjudicates isomorphism with
nauty certificates instead of fact words, so a defect in the word path would
show up as a disagreement.
"""

from __future__ import annotations

import random
from itertools import combinations

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.language.reach import (
    ReachError,
    RemainderIndex,
    compatible,
    fact_key_of,
    reach,
    remove_facts,
)
from tests.unit.language._builders import (
    facts_of,
    nauty_iso,
    random_kb,
    rebuild,
    with_inserted_fact,
    with_substituted_fact,
)

pytestmark = pytest.mark.unit

pytest.importorskip("pynauty")


def brute_force_reach(K: SparseHypergraph, K2: SparseHypergraph, r_max: int) -> int | None:
    """Reference reach: same enumeration, nauty certificates as the isomorphism test."""
    best: int | None = None
    for a in range(r_max + 1):
        for b in range(r_max + 1 - a):
            if best is not None and a + b >= best:
                continue
            for A in combinations(range(K.n_edges), a):
                left = remove_facts(K, A)
                for B in combinations(range(K2.n_edges), b):
                    if nauty_iso(left, remove_facts(K2, B)):
                        best = a + b
                        break
                else:
                    continue
                break
    return best


class TestPinnedCases:
    def test_identical_is_zero(self) -> None:
        rng = random.Random(1)
        H = random_kb(rng)
        assert reach(H, H) == 0

    def test_isomorphic_copy_is_zero(self) -> None:
        rng = random.Random(2)
        for _ in range(25):
            H = random_kb(rng)
            sigma = list(range(H.n_nodes))
            rng.shuffle(sigma)
            assert reach(H, permute(H, sigma)) == 0

    def test_one_inserted_fact_is_one(self) -> None:
        rng = random.Random(3)
        checked = 0
        for _ in range(40):
            H = random_kb(rng)
            grown = with_inserted_fact(rng, H)
            if grown is None:
                continue
            checked += 1
            assert reach(H, grown) == 1
            assert reach(grown, H) == 1
        assert checked >= 30

    def test_one_substituted_fact_is_two(self) -> None:
        rng = random.Random(4)
        checked = 0
        for _ in range(60):
            H = random_kb(rng)
            swapped = with_substituted_fact(rng, H)
            if swapped is None or fact_key_of(H) == fact_key_of(swapped):
                continue
            checked += 1
            assert reach(H, swapped) == 2
        assert checked >= 30

    def test_three_insertions_exceed_radius_two(self) -> None:
        rng = random.Random(5)
        H = random_kb(rng, n_lo=7, n_hi=7, m_lo=5, m_hi=5)
        grown: SparseHypergraph | None = H
        for _ in range(3):
            assert grown is not None
            grown = with_inserted_fact(rng, grown)
        assert grown is not None
        assert reach(H, grown, r_max=2) is None
        assert reach(H, grown, r_max=3) == 3

    def test_different_constant_count_is_unreachable(self) -> None:
        rng = random.Random(6)
        H = random_kb(rng, n_lo=6, n_hi=6)
        wider = SparseHypergraph(
            n_nodes=H.n_nodes + 1,
            hyperedges=[members for _, members in facts_of(H)],
            n_vertex_labels=H.n_vertex_labels,
            n_edge_labels=H.n_edge_labels,
            vertex_labels=[H.vertex_label(v) for v in range(H.n_nodes)] + [0],
            edge_labels=[label for label, _ in facts_of(H)],
        )
        assert not compatible(H, wider)
        assert reach(H, wider) is None

    def test_type_multiset_gates_reach(self) -> None:
        rng = random.Random(7)
        H = random_kb(rng, n_lo=6, n_hi=6, n_types=3)
        recoloured = SparseHypergraph(
            n_nodes=H.n_nodes,
            hyperedges=[members for _, members in facts_of(H)],
            n_vertex_labels=H.n_vertex_labels,
            n_edge_labels=H.n_edge_labels,
            vertex_labels=[(H.vertex_label(0) + 1) % 3] + [H.vertex_label(v) for v in range(1, 6)],
            edge_labels=[label for label, _ in facts_of(H)],
        )
        if sorted(H.vertex_label(v) for v in range(6)) != sorted(
            recoloured.vertex_label(v) for v in range(6)
        ):
            assert reach(H, recoloured) is None

    def test_radius_zero_is_isomorphism(self) -> None:
        rng = random.Random(8)
        H = random_kb(rng)
        grown = with_inserted_fact(rng, H)
        assert grown is not None
        assert reach(H, H, r_max=0) == 0
        assert reach(H, grown, r_max=0) is None

    def test_negative_radius_raises(self) -> None:
        rng = random.Random(9)
        H = random_kb(rng)
        with pytest.raises(ReachError):
            reach(H, H, r_max=-1)


class TestSymmetry:
    N_PAIRS = 300

    def test_symmetric_on_near_neighbours(self) -> None:
        rng = random.Random(11)
        checked = 0
        distribution: dict[int | None, int] = {}
        while checked < self.N_PAIRS:
            H = random_kb(rng, n_lo=5, n_hi=8, m_lo=3, m_hi=6)
            other: SparseHypergraph | None
            choice = rng.randrange(3)
            if choice == 0:
                other = with_inserted_fact(rng, H)
            elif choice == 1:
                other = with_substituted_fact(rng, H)
            else:
                sigma = list(range(H.n_nodes))
                rng.shuffle(sigma)
                other = permute(H, sigma)
            if other is None:
                continue
            checked += 1
            forward = reach(H, other)
            backward = reach(other, H)
            assert forward == backward, (forward, backward)
            distribution[forward] = distribution.get(forward, 0) + 1
        # the three generators must actually exercise more than one outcome
        assert len(distribution) >= 3, distribution


class TestBruteForceAgreement:
    N_CASES = 200

    def test_matches_independent_reference(self) -> None:
        rng = random.Random(13)
        checked = 0
        finite = 0
        while checked < self.N_CASES:
            H = random_kb(rng, n_lo=4, n_hi=6, m_lo=2, m_hi=4, arity_hi=3)
            other: SparseHypergraph | None
            choice = rng.randrange(4)
            if choice == 0:
                other = with_inserted_fact(rng, H, arity_hi=3)
            elif choice == 1:
                other = with_substituted_fact(rng, H, arity_hi=3)
            elif choice == 2:
                other = random_kb(rng, n_lo=H.n_nodes, n_hi=H.n_nodes, m_lo=2, m_hi=4, arity_hi=3)
            else:
                kept = facts_of(H)
                if not kept:
                    continue
                del kept[rng.randrange(len(kept))]
                other = rebuild(H, kept)
            if other is None:
                continue
            checked += 1
            mine = reach(H, other, r_max=2)
            theirs = brute_force_reach(H, other, r_max=2)
            assert mine == theirs, (mine, theirs)
            finite += int(mine is not None)
        assert finite >= self.N_CASES // 4


class TestRemainderIndex:
    def test_levels_are_lazy_and_cached(self) -> None:
        rng = random.Random(17)
        H = random_kb(rng, n_lo=6, n_hi=6, m_lo=5, m_hi=5)
        index = RemainderIndex(H, 2)
        first = index.level(1)
        assert index.level(1) is first
        assert sum(len(subsets) for subsets in first.values()) == H.n_edges
        assert sum(len(subsets) for subsets in index.level(2).values()) == 10

    def test_min_deletions_takes_the_smallest(self) -> None:
        rng = random.Random(19)
        H = random_kb(rng, n_lo=6, n_hi=6, m_lo=4, m_hi=4)
        table = RemainderIndex(H, 2).min_deletions()
        assert table[fact_key_of(H)] == 0
        assert all(0 <= value <= 2 for value in table.values())

    def test_ranks_require_indexing_first(self) -> None:
        rng = random.Random(23)
        H = random_kb(rng)
        index = RemainderIndex(H, 1)
        with pytest.raises(ReachError):
            index.ranks((0,))
        index.level(1)
        assert len(index.ranks((0,))) == H.n_nodes

    def test_remove_facts_keeps_every_constant(self) -> None:
        rng = random.Random(29)
        H = random_kb(rng, m_lo=3, m_hi=3)
        stripped = remove_facts(H, (0, 1, 2))
        assert stripped.n_nodes == H.n_nodes
        assert stripped.n_edges == 0
        assert [stripped.vertex_label(v) for v in range(stripped.n_nodes)] == [
            H.vertex_label(v) for v in range(H.n_nodes)
        ]

    def test_remove_facts_rejects_unknown_edge(self) -> None:
        rng = random.Random(31)
        H = random_kb(rng)
        with pytest.raises(ReachError):
            remove_facts(H, (H.n_edges,))
