"""The identity-using reference: a fact survives iff a strict majority asserts it.

``majority_merge`` is the only function in the package that reads constant
identities, and RQ3 hypothesis H3c compares the identity-free coverage
consensus against it.  The tests pin the vote threshold (strictly more than
half, on both an odd and an even member count), the constant union, the type
tie-break, the node ordering, determinism, and exact recovery of the source on
insertion-only collections --- the regime the vote is expected to win outright,
since a fact inserted into one member is asserted once.
"""

from __future__ import annotations

import random

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.language.majority import MajorityMergeError, majority_merge
from isalhg.language.reach import fact_key_of
from tests.unit.language._builders import facts_of, new_fact, random_kb, rebuild

pytestmark = pytest.mark.unit

pytest.importorskip("pynauty")


def kb(n: int, facts: list[tuple[int, frozenset[int]]], types: list[int]) -> SparseHypergraph:
    """Small explicit builder for the hand-checked vote cases."""
    return SparseHypergraph(
        n_nodes=n,
        hyperedges=[members for _, members in facts],
        n_vertex_labels=3,
        n_edge_labels=2,
        vertex_labels=types,
        edge_labels=[label for label, _ in facts],
    )


class TestVote:
    def test_strict_majority_on_odd_members(self) -> None:
        shared = (0, frozenset({0, 1}))
        odd_one = (0, frozenset({1, 2}))
        members = [
            kb(3, [shared, odd_one], [0, 0, 0]),
            kb(3, [shared], [0, 0, 0]),
            kb(3, [shared], [0, 0, 0]),
        ]
        names = [["a", "b", "c"]] * 3
        merged, ordered = majority_merge(members, names)
        assert ordered == ("a", "b", "c")
        assert merged.n_edges == 1
        assert merged.members(0) == frozenset({0, 1})

    def test_exactly_half_is_not_a_majority(self) -> None:
        shared = (0, frozenset({0, 1}))
        split = (0, frozenset({1, 2}))
        members = [
            kb(3, [shared, split], [0, 0, 0]),
            kb(3, [shared, split], [0, 0, 0]),
            kb(3, [shared], [0, 0, 0]),
            kb(3, [shared], [0, 0, 0]),
        ]
        names = [["a", "b", "c"]] * 4
        merged, _ = majority_merge(members, names)
        assert merged.n_edges == 1

    def test_predicate_is_part_of_the_fact(self) -> None:
        members = [
            kb(2, [(0, frozenset({0, 1}))], [0, 0]),
            kb(2, [(1, frozenset({0, 1}))], [0, 0]),
            kb(2, [(1, frozenset({0, 1}))], [0, 0]),
        ]
        names = [["a", "b"]] * 3
        merged, _ = majority_merge(members, names)
        assert merged.n_edges == 1
        assert merged.edge_label(0) == 1


class TestConstantsAndTypes:
    def test_constants_are_the_union_ordered_by_identity(self) -> None:
        members = [
            kb(2, [(0, frozenset({0, 1}))], [0, 0]),
            kb(2, [(0, frozenset({0, 1}))], [0, 0]),
        ]
        names = [["b", "a"], ["b", "z"]]
        merged, ordered = majority_merge(members, names)
        assert ordered == ("a", "b", "z")
        assert merged.n_nodes == 3

    def test_type_majority_then_smallest_id(self) -> None:
        members = [
            kb(1, [], [0]),
            kb(1, [], [2]),
            kb(1, [], [2]),
        ]
        names = [["a"], ["a"], ["a"]]
        merged, _ = majority_merge(members, names)
        assert merged.vertex_label(0) == 2

        tied = [kb(1, [], [2]), kb(1, [], [0])]
        merged_tied, _ = majority_merge(tied, [["a"], ["a"]])
        assert merged_tied.vertex_label(0) == 0

    def test_identity_translation_is_not_the_node_id(self) -> None:
        members = [
            kb(2, [(0, frozenset({0, 1}))], [0, 1]),
            kb(2, [(0, frozenset({0, 1}))], [1, 0]),
            kb(2, [(0, frozenset({0, 1}))], [0, 1]),
        ]
        names = [["a", "b"], ["b", "a"], ["a", "b"]]
        merged, ordered = majority_merge(members, names)
        assert ordered == ("a", "b")
        assert [merged.vertex_label(0), merged.vertex_label(1)] == [0, 1]


class TestValidation:
    def test_empty_members_raise(self) -> None:
        with pytest.raises(MajorityMergeError):
            majority_merge([], [])

    def test_length_mismatch_raises(self) -> None:
        rng = random.Random(301)
        H = random_kb(rng)
        with pytest.raises(MajorityMergeError):
            majority_merge([H], [])

    def test_identity_row_must_match_constant_count(self) -> None:
        rng = random.Random(302)
        H = random_kb(rng)
        with pytest.raises(MajorityMergeError):
            majority_merge([H], [["a"]])

    def test_repeated_identity_raises(self) -> None:
        members = [kb(2, [(0, frozenset({0, 1}))], [0, 0])]
        with pytest.raises(MajorityMergeError):
            majority_merge(members, [["a", "a"]])


class TestRecoversTheSource:
    def test_insertion_only_recovers_exactly(self) -> None:
        rng = random.Random(311)
        trials = 0
        recovered = 0
        for _ in range(12):
            source = random_kb(rng, n_lo=6, n_hi=8, m_lo=5, m_hi=7, arity_hi=3)
            names = [f"c{v}" for v in range(source.n_nodes)]
            members: list[SparseHypergraph] = []
            seen = {fact_key_of(source)}
            for _ in range(5):
                fact = new_fact(rng, source, arity_hi=3)
                if fact is None:
                    break
                grown = rebuild(source, [*facts_of(source), fact])
                key = fact_key_of(grown)
                if key in seen:
                    continue
                seen.add(key)
                members.append(grown)
            if len(members) != 5:
                continue
            trials += 1
            merged, ordered = majority_merge(members, [names] * len(members))
            assert ordered == tuple(names)
            recovered += int(fact_key_of(merged) == fact_key_of(source))
        assert trials >= 8
        assert recovered == trials

    def test_output_is_deterministic(self) -> None:
        rng = random.Random(312)
        source = random_kb(rng, n_lo=7, n_hi=7, m_lo=6, m_hi=6, arity_hi=3)
        names = [f"c{v}" for v in range(source.n_nodes)]
        members = [source, source, source]
        first = majority_merge(members, [names] * 3)
        second = majority_merge(members, [names] * 3)
        assert first[1] == second[1]
        assert first[0] == second[0]
        assert [first[0].members(e) for e in first[0].edges()] == [
            second[0].members(e) for e in second[0].edges()
        ]
