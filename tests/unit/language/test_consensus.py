"""The coverage consensus returns a decoded word, and returns the right one.

The pinned behaviour here is the part of RQ3 that does not need a corpus: the
objective's shape (lexicographic, with the word as the final tie break), the
provenance fields the rows need, determinism, and the two failure modes of the
alignment budget.  The measured recovery rates over many random sources live in
``test_consensus_recovery.py``, which is marked ``slow``.

The budget test is the one to read first.  With a *total* alignment budget of
``r``, two members that are each ``t = 2`` insertions from the source have no
alignment at all, so the candidate set is the members and the consensus cannot
beat a medoid; with the *per-side* budget the deletion pair that exposes the
source is in the family and the source is recovered.  That is why
``coverage_consensus`` defaults to the per-side reading.
"""

from __future__ import annotations

import random

import pytest

from isalhg.core.canonical import canonical_string
from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.core.string_to_hypergraph import string_to_hypergraph
from isalhg.iso_backends.canonical_order import nauty_certificate_bytes
from isalhg.language.consensus import (
    ConsensusError,
    ConsensusResult,
    coverage_consensus,
    in_language_domain,
)
from isalhg.language.reach import compact_constants, fact_key_of, reach, remove_facts
from tests.unit.language._builders import (
    facts_of,
    new_fact,
    random_kb,
    rebuild,
)

pytestmark = pytest.mark.unit

pytest.importorskip("pynauty")


def insertion_collection(
    rng: random.Random, source: SparseHypergraph, n_members: int, t: int
) -> list[SparseHypergraph] | None:
    """Return ``n_members`` copies of ``source``, each with ``t`` distinct new facts."""
    members: list[SparseHypergraph] = []
    keys = {fact_key_of(source)}
    for _ in range(n_members):
        member: SparseHypergraph | None = None
        for _ in range(60):
            grown: SparseHypergraph | None = source
            for _ in range(t):
                assert grown is not None
                fact = new_fact(rng, grown, arity_hi=3)
                if fact is None:
                    grown = None
                    break
                grown = rebuild(grown, [*facts_of(grown), fact])
            if grown is None:
                continue
            key = fact_key_of(grown)
            if key in keys:
                continue
            keys.add(key)
            member = grown
            break
        if member is None:
            return None
        members.append(member)
    return members


def deletion_collection(
    rng: random.Random, source: SparseHypergraph, n_members: int, t: int
) -> list[SparseHypergraph] | None:
    """Return ``n_members`` copies of ``source``, each with ``t`` distinct facts removed."""
    if source.n_edges <= t:
        return None
    members: list[SparseHypergraph] = []
    keys = {fact_key_of(source)}
    for _ in range(n_members):
        member: SparseHypergraph | None = None
        for _ in range(60):
            kept = facts_of(source)
            for _ in range(t):
                del kept[rng.randrange(len(kept))]
            shrunk = rebuild(source, kept)
            key = fact_key_of(shrunk)
            if key in keys:
                continue
            keys.add(key)
            member = shrunk
            break
        if member is None:
            return None
        members.append(member)
    return members


class TestDegenerateInputs:
    def test_single_member_returns_it(self) -> None:
        rng = random.Random(201)
        H = random_kb(rng)
        result = coverage_consensus([H], r=2)
        assert result.word == fact_key_of(H)
        assert result.coverage == 1
        assert result.sum_reach == 0
        assert result.anchor == 0
        assert result.node_map == tuple(range(H.n_nodes))
        assert result.n_candidates >= 1

    def test_identical_members_collapse_to_one_candidate(self) -> None:
        rng = random.Random(202)
        H = random_kb(rng)
        sigma = list(range(H.n_nodes))
        rng.shuffle(sigma)
        result = coverage_consensus([H, permute(H, sigma), H], r=2)
        assert result.word == fact_key_of(H)
        assert result.coverage == 3
        assert result.sum_reach == 0
        assert result.n_ties == 0
        member_scores = [score for score in result.candidates if score.origin.startswith("member:")]
        # the three copies are one class, so exactly one candidate carries a member origin
        assert len(member_scores) == 1

    def test_empty_members_raise(self) -> None:
        with pytest.raises(ConsensusError):
            coverage_consensus([], r=2)

    def test_negative_radius_raises(self) -> None:
        rng = random.Random(203)
        with pytest.raises(ConsensusError):
            coverage_consensus([random_kb(rng)], r=-1)

    def test_unknown_budget_raises(self) -> None:
        rng = random.Random(204)
        with pytest.raises(ConsensusError):
            coverage_consensus([random_kb(rng)], r=2, alignment_budget="both")  # type: ignore[arg-type]


def source_is_writable(source: SparseHypergraph) -> bool:
    """True when the source is something the consensus is allowed to return.

    The candidate set admits only knowledge bases with an Isal string (R3,
    Prop. C.4), so a source whose compaction is disconnected cannot be
    recovered however good the objective is --- ``random_kb`` produces one about
    one time in eight, and the recovery rates below are about the objective, not
    about the generator.  Corpus A enforces the same restriction.
    """
    core, _ = compact_constants(source)
    return in_language_domain(core)


class TestRecoversTheSource:
    def test_insertion_only_t1(self) -> None:
        rng = random.Random(211)
        recovered = 0
        trials = 0
        for _ in range(8):
            source = random_kb(rng, n_lo=6, n_hi=8, m_lo=5, m_hi=7, arity_hi=3)
            members = insertion_collection(rng, source, 5, 1)
            if members is None or not source_is_writable(source):
                continue
            trials += 1
            result = coverage_consensus(members, r=2)
            recovered += int(result.word == fact_key_of(source))
        assert trials >= 6
        assert recovered == trials

    def test_insertion_only_t2(self) -> None:
        rng = random.Random(212)
        recovered = 0
        trials = 0
        for _ in range(8):
            source = random_kb(rng, n_lo=6, n_hi=8, m_lo=5, m_hi=7, arity_hi=3)
            members = insertion_collection(rng, source, 5, 2)
            if members is None or not source_is_writable(source):
                continue
            trials += 1
            result = coverage_consensus(members, r=2)
            recovered += int(result.word == fact_key_of(source))
        assert trials >= 6
        assert recovered == trials

    def test_deletion_only_t1(self) -> None:
        rng = random.Random(213)
        recovered = 0
        trials = 0
        for _ in range(8):
            source = random_kb(rng, n_lo=6, n_hi=8, m_lo=6, m_hi=8, arity_hi=3)
            members = deletion_collection(rng, source, 5, 1)
            if members is None or not source_is_writable(source):
                continue
            trials += 1
            result = coverage_consensus(members, r=2)
            recovered += int(result.word == fact_key_of(source))
        assert trials >= 6
        assert recovered >= trials - 1

    def test_source_beats_every_member_on_the_objective(self) -> None:
        rng = random.Random(214)
        source = random_kb(rng, n_lo=7, n_hi=7, m_lo=6, m_hi=6, arity_hi=3)
        members = insertion_collection(rng, source, 5, 2)
        assert members is not None
        result = coverage_consensus(members, r=2)
        assert result.coverage == len(members)
        member_scores = [score for score in result.candidates if score.origin.startswith("member:")]
        assert len(member_scores) == len(members)
        assert all(score.coverage < result.coverage for score in member_scores)


class TestAlignmentBudget:
    def test_total_budget_cannot_see_the_source_at_t2(self) -> None:
        rng = random.Random(221)
        source = random_kb(rng, n_lo=7, n_hi=7, m_lo=6, m_hi=6, arity_hi=3)
        members = insertion_collection(rng, source, 5, 2)
        assert members is not None
        if any(
            reach(a, b, r_max=2) is not None
            for i, a in enumerate(members)
            for b in members[i + 1 :]
        ):
            pytest.skip("two members happened to land within radius 2 of each other")
        target = fact_key_of(source)
        assert coverage_consensus(members, r=2, alignment_budget="triangle").word == target
        assert coverage_consensus(members, r=2, alignment_budget="per_side").word == target
        total = coverage_consensus(members, r=2, alignment_budget="sum")
        assert total.word != target
        assert total.n_candidates == len(members)

    def test_total_budget_still_recovers_at_t1(self) -> None:
        rng = random.Random(222)
        source = random_kb(rng, n_lo=7, n_hi=7, m_lo=6, m_hi=6, arity_hi=3)
        members = insertion_collection(rng, source, 5, 1)
        assert members is not None
        assert coverage_consensus(members, r=2, alignment_budget="sum").word == fact_key_of(source)

    def test_per_side_misses_a_midpoint_that_triangle_finds(self) -> None:
        """The unequal-distance case that makes ``2r`` the complete family.

        Members are ``S + 2`` facts and ``S`` itself, at radius 1.  Neither is
        within reach 1 of the other, but ``S + 1`` fact is within reach 1 of
        both, so it is the unique candidate with coverage 2.  It comes from the
        alignment ``(|A|, |B|) = (2, 0)``, which the per-side family (``|A| <= 1``)
        excludes and the triangle family (``|A| + |B| <= 2``) contains.
        """
        rng = random.Random(223)
        for _ in range(20):
            source = random_kb(rng, n_lo=6, n_hi=7, m_lo=4, m_hi=5, arity_hi=3)
            grown = insertion_collection(rng, source, 1, 2)
            if grown is None:
                continue
            members = [grown[0], source]
            if reach(members[0], members[1], r_max=1) is not None:
                continue

            triangle = coverage_consensus(members, r=1, alignment_budget="triangle")
            assert triangle.coverage == 2
            assert triangle.word not in {fact_key_of(H) for H in members}
            assert reach(triangle.kb, members[0], r_max=1) == 1
            assert reach(triangle.kb, members[1], r_max=1) == 1

            narrow = coverage_consensus(members, r=1, alignment_budget="per_side")
            assert narrow.n_candidates == 2
            assert narrow.coverage == 1
            return
        pytest.fail("no usable instance was generated")


class TestResultShape:
    def test_deterministic(self) -> None:
        rng = random.Random(231)
        source = random_kb(rng, n_lo=7, n_hi=7, m_lo=6, m_hi=6, arity_hi=3)
        members = insertion_collection(rng, source, 5, 1)
        assert members is not None
        first = coverage_consensus(members, r=2)
        second = coverage_consensus(members, r=2)
        assert first.word == second.word
        assert first.anchor == second.anchor
        assert first.n_candidates == second.n_candidates
        assert first.n_ties == second.n_ties
        assert first.candidates == second.candidates

    def test_candidates_are_distinct_and_scored(self) -> None:
        rng = random.Random(232)
        source = random_kb(rng, n_lo=6, n_hi=6, m_lo=5, m_hi=5, arity_hi=3)
        members = insertion_collection(rng, source, 4, 1)
        assert members is not None
        result = coverage_consensus(members, r=2)
        words = [score.word for score in result.candidates]
        assert len(words) == len(set(words)) == result.n_candidates
        assert all(0 <= score.coverage <= len(members) for score in result.candidates)
        assert all(score.sum_reach <= 3 * len(members) for score in result.candidates)
        assert all(score.origin.startswith(("member:", "transfer:")) for score in result.candidates)

    def test_winner_is_the_lexicographic_argmax(self) -> None:
        rng = random.Random(233)
        source = random_kb(rng, n_lo=6, n_hi=6, m_lo=5, m_hi=5, arity_hi=3)
        members = insertion_collection(rng, source, 4, 2)
        assert members is not None
        result = coverage_consensus(members, r=2)
        best = min((-score.coverage, score.sum_reach, score.word) for score in result.candidates)
        assert (-result.coverage, result.sum_reach, result.word) == best

    def test_anchor_and_node_map_describe_the_constant_space(self) -> None:
        rng = random.Random(234)
        source = random_kb(rng, n_lo=6, n_hi=6, m_lo=5, m_hi=5, arity_hi=3)
        members = insertion_collection(rng, source, 4, 1)
        assert members is not None
        result = coverage_consensus(members, r=2)
        assert 0 <= result.anchor < len(members)
        assert len(result.constant_origin) == result.kb.n_nodes
        assert len(result.node_map) == result.kb.n_nodes
        assert fact_key_of(result.kb) == result.word
        for constant, (member, source_constant) in enumerate(result.constant_origin):
            assert 0 <= member < len(members)
            assert 0 <= source_constant < members[member].n_nodes
            expected = source_constant if member == result.anchor else None
            assert result.node_map[constant] == expected


def deleted_member(source: SparseHypergraph, index: int) -> SparseHypergraph:
    """Return ``source`` minus fact ``index``, compacted --- one deletion variant."""
    core, _ = compact_constants(remove_facts(source, (index,)))
    return core


def winning_origin(result: ConsensusResult) -> str:
    """Return the ``origin`` tag of the candidate that won."""
    return next(score.origin for score in result.candidates if score.word == result.word)


def hub_and_pendants(n_pendants: int) -> SparseHypergraph:
    """A hub fact ``{0,1}`` plus one private-constant fact per pendant.

    Each pendant carries its own predicate, so the deletion members are pairwise
    non-isomorphic; deleting a pendant fact strands that pendant's constant, so
    the member is a knowledge base with one constant fewer.
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


class TestTransferCreatesAConstant:
    """A donor fact may name a constant the host lost; the transfer creates it.

    Every member here is the source minus one pendant fact, so every member is
    missing exactly the constant that fact named.  Recovering the source
    therefore *requires* an insertion that brings a constant back, which is the
    ``insert_fact_new_constant`` edit.  The recovered candidate is checked to be
    a genuine connected knowledge base by round-tripping it through the Isal
    word: ``S2H(H2S(kb))`` reproduces it (`DESIGN.md` Prop. C.4).
    """

    def test_the_consensus_recovers_a_source_no_member_can_express(self) -> None:
        source = hub_and_pendants(3)
        members = [deleted_member(source, index) for index in range(1, source.n_edges)]
        assert all(member.n_nodes == source.n_nodes - 1 for member in members)

        result = coverage_consensus(members, r=2)

        assert result.word == fact_key_of(source)
        assert result.kb.n_nodes == source.n_nodes
        assert result.coverage == len(members)
        assert winning_origin(result).startswith("transfer:")

    def test_the_recovered_candidate_carries_the_donor_identity(self) -> None:
        source = hub_and_pendants(3)
        members = [deleted_member(source, index) for index in range(1, source.n_edges)]
        result = coverage_consensus(members, r=2)

        donors = {member for member, _ in result.constant_origin if member != result.anchor}
        assert donors, result.constant_origin
        for member, constant in result.constant_origin:
            assert 0 <= constant < members[member].n_nodes

    def test_the_recovered_candidate_is_a_connected_knowledge_base_that_decodes(self) -> None:
        source = hub_and_pendants(3)
        members = [deleted_member(source, index) for index in range(1, source.n_edges)]
        result = coverage_consensus(members, r=2)

        kb = result.kb
        assert kb.is_connected()
        word = canonical_string(kb, k=kb.n_nodes)
        decoded = string_to_hypergraph(
            word,
            k=kb.n_nodes,
            n_vertex_labels=kb.n_vertex_labels,
            n_edge_labels=kb.n_edge_labels,
        )
        assert nauty_certificate_bytes(decoded) == nauty_certificate_bytes(kb)
