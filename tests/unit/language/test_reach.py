"""Reach' is exact, symmetric, and agrees with an independent brute force.

The definition of done for ``reach`` is three claims.  The pinned cases fix the
semantics on hand-built inputs (0 for an isomorphic pair, 1 for one inserted
fact, 2 for one substituted fact, ``None`` past the radius).  Symmetry is
checked on 300 random near-neighbour pairs, because the definition is symmetric
and an asymmetric implementation would silently break the consensus objective.
The brute-force agreement on 200 random cases is the exactness check: the
reference enumerates the same deletion pairs but adjudicates isomorphism with
nauty certificates instead of fact words, so a defect in the word path would
show up as a disagreement.

Since the remainders are compacted, a fourth block pins the properties that
change with it: a source is at reach 1 from a single-fact-deletion member even
when the deleted fact stranded a constant, two such members are at reach 2, and
a constant naming nothing is not part of the knowledge base at all.
"""

from __future__ import annotations

import random
from itertools import combinations

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.language.reach import (
    ReachError,
    RemainderIndex,
    compact_constants,
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
    """Reference reach': same enumeration, nauty certificates as the isomorphism test."""
    best: int | None = None
    for a in range(r_max + 1):
        for b in range(r_max + 1 - a):
            if best is not None and a + b >= best:
                continue
            for A in combinations(range(K.n_edges), a):
                left, _ = compact_constants(remove_facts(K, A))
                for B in combinations(range(K2.n_edges), b):
                    right, _ = compact_constants(remove_facts(K2, B))
                    if nauty_iso(left, right):
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

    def test_a_constant_naming_nothing_is_not_part_of_the_knowledge_base(self) -> None:
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
        assert compatible(H, wider, 2)
        assert reach(H, wider) == 0

    def test_disjoint_fact_profiles_are_unreachable(self) -> None:
        rng = random.Random(6)
        base = random_kb(rng, n_lo=6, n_hi=6, m_lo=5, m_hi=5, n_preds=2)
        members = [edge for _, edge in facts_of(base)]
        types = [base.vertex_label(v) for v in range(base.n_nodes)]

        def with_one_predicate(predicate: int) -> SparseHypergraph:
            return SparseHypergraph(
                n_nodes=base.n_nodes,
                hyperedges=members,
                n_vertex_labels=base.n_vertex_labels,
                n_edge_labels=2,
                vertex_labels=types,
                edge_labels=[predicate] * len(members),
            )

        assert not compatible(with_one_predicate(0), with_one_predicate(1), 2)
        assert reach(with_one_predicate(0), with_one_predicate(1)) is None

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


def deletion_member(H: SparseHypergraph, index: int) -> SparseHypergraph:
    """Return ``H`` minus one fact, compacted --- one Corpus A deletion variant."""
    core, _ = compact_constants(remove_facts(H, (index,)))
    return core


def pendant_kb(n_pendants: int) -> SparseHypergraph:
    """A hub fact plus ``n_pendants`` facts, each attaching one private constant.

    Deleting a pendant fact strands its private constant, so the deletion member
    carries one constant fewer than the source; deleting several strands
    several.  Constants ``0`` and ``1`` are the hub and are never stranded.
    Each pendant carries its own predicate, so no two of them are exchanged by
    an automorphism and the deletion members are pairwise non-isomorphic ---
    which is what a variant collection requires.
    """
    edges = [frozenset({0, 1})]
    labels = [0]
    for i in range(n_pendants):
        edges.append(frozenset({0, 2 + i}))
        labels.append(1 + i)
    return SparseHypergraph(
        n_nodes=2 + n_pendants,
        hyperedges=edges,
        n_vertex_labels=1,
        n_edge_labels=1 + n_pendants,
        vertex_labels=[0] * (2 + n_pendants),
        edge_labels=labels,
    )


class TestReachPrimeSanity:
    """The four properties `D-KBf5` pins for ``reach'`` on compacted remainders."""

    def test_source_to_its_deletion_member_is_one(self) -> None:
        source = pendant_kb(3)
        for index in range(source.n_edges):
            member = deletion_member(source, index)
            assert compatible(source, member, 2)
            assert reach(source, member) == 1

    def test_two_distinct_deletion_members_are_two_apart(self) -> None:
        source = pendant_kb(3)
        first = deletion_member(source, 0)
        second = deletion_member(source, 1)
        assert fact_key_of(first) != fact_key_of(second)
        assert reach(first, second) == 2

    def test_reach_is_symmetric_across_the_deletion_family(self) -> None:
        source = pendant_kb(3)
        family = [source, *(deletion_member(source, i) for i in range(source.n_edges))]
        for left in family:
            for right in family:
                assert reach(left, right) == reach(right, left)

    def test_reach_of_a_knowledge_base_with_itself_is_zero(self) -> None:
        rng = random.Random(101)
        for _ in range(20):
            H = random_kb(rng)
            assert reach(H, H) == 0

    @pytest.mark.parametrize("n_pendants", [1, 2, 3])
    def test_a_member_losing_several_constants_stays_in_reach(self, n_pendants: int) -> None:
        source = pendant_kb(3)
        dropped = tuple(range(1, 1 + n_pendants))
        member, _ = compact_constants(remove_facts(source, dropped))
        assert member.n_nodes == source.n_nodes - n_pendants
        assert reach(source, member, r_max=n_pendants) == n_pendants
        assert reach(source, member, r_max=n_pendants - 1) is None

    def test_an_empty_deletion_set_leaves_the_knowledge_base_alone(self) -> None:
        source = pendant_kb(2)
        core, survivors = compact_constants(remove_facts(source, ()))
        assert core == source
        assert survivors == tuple(range(source.n_nodes))

    def test_deleting_every_fact_leaves_the_empty_knowledge_base(self) -> None:
        source = pendant_kb(1)
        core, survivors = compact_constants(remove_facts(source, tuple(range(source.n_edges))))
        assert core.n_nodes == 0
        assert core.n_edges == 0
        assert survivors == ()
        assert fact_key_of(core) == ()

    def test_a_single_fact_knowledge_base(self) -> None:
        single = SparseHypergraph(
            n_nodes=2,
            hyperedges=[frozenset({0, 1})],
            n_vertex_labels=1,
            n_edge_labels=1,
            vertex_labels=[0, 0],
            edge_labels=[0],
        )
        assert reach(single, single) == 0
        empty, _ = compact_constants(remove_facts(single, (0,)))
        assert reach(single, empty, r_max=1) == 1


class TestTheGateStaysNecessary:
    """``compatible`` may over-accept; it must never reject a reachable pair.

    The pin is the tempting-but-wrong gate: comparing the type multisets of the
    constants that occur in a fact.  Compaction can *remove* an occurring
    constant, so those multisets need not agree even at reach 1.
    """

    def test_occurring_type_multisets_are_not_a_necessary_condition(self) -> None:
        K = SparseHypergraph(
            n_nodes=3,
            hyperedges=[frozenset({0, 1}), frozenset({1, 2})],
            n_vertex_labels=2,
            n_edge_labels=2,
            vertex_labels=[0, 0, 1],
            edge_labels=[0, 1],
        )
        K2 = SparseHypergraph(
            n_nodes=2,
            hyperedges=[frozenset({0, 1})],
            n_vertex_labels=2,
            n_edge_labels=2,
            vertex_labels=[0, 0],
            edge_labels=[0],
        )
        occurring = [
            sorted(H.vertex_label(v) for v in range(H.n_nodes) if H.degree(v) > 0) for H in (K, K2)
        ]
        assert occurring[0] != occurring[1]
        assert reach(K, K2) == 1
        assert compatible(K, K2, 2)

    def test_the_gate_never_rejects_a_pair_the_enumeration_can_match(self) -> None:
        rng = random.Random(313)
        checked = 0
        while checked < 150:
            H = random_kb(rng, n_lo=4, n_hi=6, m_lo=2, m_hi=4, arity_hi=3)
            other = with_inserted_fact(rng, H, arity_hi=3)
            if other is None:
                continue
            checked += 1
            for r_max in (0, 1, 2):
                if brute_force_reach(H, other, r_max) is not None:
                    assert compatible(H, other, r_max)


class TestDeletionMembersWereUnreachableBefore:
    """The gate that ``reach'`` replaces rejected exactly these pairs.

    The frozen ``compatible`` compared constant counts, so a deletion member
    that lost a constant was declared unreachable from its source and from its
    siblings.  These are the pairs the change repairs; the old test is kept in
    spirit by asserting the constant counts really do differ.
    """

    def test_source_and_member_differ_in_constant_count_yet_are_compatible(self) -> None:
        source = pendant_kb(3)
        member = deletion_member(source, 1)
        assert member.n_nodes != source.n_nodes
        assert compatible(source, member, 2)
        assert reach(source, member) == 1

    def test_two_members_differ_in_constant_count_from_the_source_yet_reach_each_other(
        self,
    ) -> None:
        source = pendant_kb(3)
        first = deletion_member(source, 1)
        second = deletion_member(source, 2)
        assert first.n_nodes == second.n_nodes == source.n_nodes - 1
        assert compatible(first, second, 2)
        assert reach(first, second) == 2


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

    def test_remainders_require_indexing_first(self) -> None:
        rng = random.Random(23)
        H = random_kb(rng)
        index = RemainderIndex(H, 1)
        with pytest.raises(ReachError):
            index.remainder((0,))
        index.level(1)
        got = index.remainder((0,))
        assert got.n_source == H.n_nodes
        assert len(got.ranks) == len(got.survivors) <= H.n_nodes
        assert sorted(got.ranks) == list(range(len(got.ranks)))

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
