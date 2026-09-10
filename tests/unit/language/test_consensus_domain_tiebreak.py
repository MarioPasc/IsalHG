"""The consensus returns an object the Isal language can write, chosen by that language.

Two changes are pinned here and they must be read together.

The **domain exclusion** is a correctness fix: ``K_i - A' + pi(B')`` can be
disconnected, and it can be empty, and neither has an Isal string (R3, Prop.
C.4).  Where such a candidate *won*, the reported representative was not a
decoded program, so the row was already invalid --- which is also why the fix is
cheap: dropping losing candidates from an argmax changes nothing.  The two
pinned collections below are exactly the two ways it goes wrong: a disconnected
winner, and the empty knowledge base winning outright because it is within reach
``r`` of every member.

The **tie break** is a coherence fix.  Deduplicating by a canonical key is
invariant-neutral, but a tie break *selects* among candidates the objective
cannot separate, so it is a choice of representation, and D-ART4 (3) ruled that
representation to be the Isal string.  The pinned collection is one where the
retired fact word and the Isal fingerprint disagree; the test attributes the
change to the tie break rather than to the exclusion by running the intermediate
objective as well.

``old_objective`` and ``mid_objective`` reproduce the two earlier behaviours by
substituting the module-level hooks, so the "before" side of every comparison is
the code as it stood at 44c48e3 rather than a description of it.
"""

from __future__ import annotations

import random
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager

import pytest

from isalhg.core.canonical import canonical_string, required_k
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.string_to_hypergraph import string_to_hypergraph
from isalhg.language import consensus as consensus_module
from isalhg.language.consensus import (
    ConsensusDomainError,
    ConsensusResult,
    coverage_consensus,
    in_language_domain,
    isal_fingerprint,
)
from isalhg.language.reach import fact_key_of
from tests.unit.language._builders import facts_of, new_fact, random_kb, rebuild

pytestmark = pytest.mark.unit

pytest.importorskip("pynauty")

N_TYPES = 2
N_PREDS = 2

Fact = tuple[int, list[int]]


def build(n: int, types: Sequence[int], facts: Sequence[Fact]) -> SparseHypergraph:
    """Return the knowledge base with ``n`` typed constants and the given facts."""
    return SparseHypergraph(
        n_nodes=n,
        hyperedges=[frozenset(members) for _, members in facts],
        n_vertex_labels=N_TYPES,
        n_edge_labels=N_PREDS,
        vertex_labels=list(types),
        edge_labels=[label for label, _ in facts],
    )


@contextmanager
def _hooks(
    *,
    domain: Callable[[SparseHypergraph], bool],
    word: Callable[[SparseHypergraph], object],
) -> Iterator[None]:
    """Run the consensus with its domain test and tie-break word substituted."""
    saved_domain = consensus_module.in_language_domain
    saved_word = consensus_module.isal_fingerprint
    consensus_module.in_language_domain = domain  # type: ignore[assignment]
    consensus_module.isal_fingerprint = word  # type: ignore[assignment]
    try:
        yield
    finally:
        consensus_module.in_language_domain = saved_domain  # type: ignore[assignment]
        consensus_module.isal_fingerprint = saved_word  # type: ignore[assignment]


def old_objective(members: Sequence[SparseHypergraph], r: int) -> ConsensusResult:
    """The objective as it stood before this change: no exclusion, fact-word tie break.

    The pool is keyed by ``fact_key_of``, so substituting the tie break with the
    same function reproduces the previous ``min`` over pool keys exactly.
    """
    with _hooks(domain=lambda _H: True, word=fact_key_of):
        return coverage_consensus(members, r)


def mid_objective(members: Sequence[SparseHypergraph], r: int) -> ConsensusResult:
    """The exclusion alone: in-domain candidates, still with the fact-word tie break."""
    with _hooks(domain=in_language_domain, word=fact_key_of):
        return coverage_consensus(members, r)


# ---------------------------------------------------------------------------
# The pinned collections, found by a search over random variant collections
# (seed 20260910) and recorded here so the behaviour is fixed rather than
# resampled.
# ---------------------------------------------------------------------------

#: Two deletion members whose best candidate under the old objective is
#: disconnected --- it keeps all six constants but splits into components.
DISCONNECTED_WINNER: tuple[list[SparseHypergraph], int] = (
    [
        build(
            6,
            [1, 1, 0, 1, 0, 1],
            [(0, [0, 2, 4]), (0, [1, 3]), (0, [1, 3, 5]), (1, [1, 4, 5])],
        ),
        build(
            6,
            [1, 1, 0, 1, 0, 1],
            [(0, [0, 2, 4]), (0, [1, 3, 5]), (0, [1, 5]), (1, [1, 4, 5])],
        ),
    ],
    2,
)

#: Two two-fact members for which the *empty* knowledge base is within reach 2
#: of both, so under the old objective it wins on coverage outright.
EMPTY_WINNER: tuple[list[SparseHypergraph], int] = (
    [
        build(4, [1, 0, 1, 1], [(0, [0, 1, 2]), (0, [0, 2, 3])]),
        build(4, [1, 0, 1, 1], [(0, [1, 2]), (1, [0, 2, 3])]),
    ],
    2,
)

#: Two insertion members whose optimum is a three-way tie the fact word and the
#: Isal fingerprint resolve differently.
TIE_BREAK_DISAGREES: tuple[list[SparseHypergraph], int] = (
    [
        build(
            6,
            [0, 0, 0, 0, 1, 0],
            [(0, [0, 2, 3]), (0, [0, 2, 5]), (0, [2, 3]), (1, [0, 1, 4]), (1, [2, 3])],
        ),
        build(
            6,
            [0, 0, 0, 0, 1, 0],
            [(0, [0, 2, 3]), (0, [0, 2, 5]), (1, [0, 1]), (1, [0, 1, 4]), (1, [2, 3])],
        ),
    ],
    2,
)


class TestDomainExclusion:
    """A representative with no Isal string is not a result the method may report."""

    @pytest.mark.parametrize(
        ("collection", "label"),
        [(DISCONNECTED_WINNER, "disconnected"), (EMPTY_WINNER, "empty")],
        ids=["disconnected_winner", "empty_winner"],
    )
    def test_out_of_domain_winner_is_replaced(
        self, collection: tuple[list[SparseHypergraph], int], label: str
    ) -> None:
        members, r = collection
        old = old_objective(members, r)
        assert not in_language_domain(old.kb), (
            f"the {label} fixture no longer reproduces an out-of-domain winner"
        )

        result = coverage_consensus(members, r)
        assert in_language_domain(result.kb)
        assert result.connected is True
        assert result.n_disconnected > 0
        assert result.n_excluded == result.n_disconnected
        assert result.word != old.word

    def test_the_excluded_count_is_reported(self) -> None:
        members, r = DISCONNECTED_WINNER
        old = old_objective(members, r)
        result = coverage_consensus(members, r)
        # Every class the old pool held and the new one does not is out of
        # domain, so the two censuses must agree exactly.
        assert result.n_candidates + result.n_excluded == old.n_candidates

    def test_members_outside_the_domain_are_not_candidates(self) -> None:
        # A disconnected member cannot be returned as a representative even
        # though it is a perfectly good scoring target.
        disconnected = build(4, [0, 1, 0, 1], [(0, [0, 1]), (1, [2, 3])])
        connected = build(4, [0, 1, 0, 1], [(0, [0, 1]), (1, [1, 2]), (0, [2, 3])])
        assert not in_language_domain(disconnected)

        result = coverage_consensus([disconnected, connected], r=1)
        assert in_language_domain(result.kb)
        assert result.n_excluded >= 1

    def test_every_candidate_out_of_domain_raises(self) -> None:
        disconnected = build(4, [0, 1, 0, 1], [(0, [0, 1]), (1, [2, 3])])
        with pytest.raises(ConsensusDomainError, match="outside the language's domain"):
            coverage_consensus([disconnected], r=0)

    def test_single_candidate_needs_no_tie_break(self) -> None:
        H = build(3, [0, 1, 0], [(0, [0, 1]), (1, [1, 2])])
        result = coverage_consensus([H], r=0)
        assert result.n_candidates == 1
        assert result.n_ties == 0
        assert result.origin == "member:0"
        assert result.connected is True


class TestTieBreak:
    """The candidates the objective cannot separate are ordered by the Isal string."""

    def test_the_two_words_pick_different_winners(self) -> None:
        members, r = TIE_BREAK_DISAGREES
        mid = mid_objective(members, r)
        result = coverage_consensus(members, r)

        assert result.n_ties > 0
        assert (result.coverage, result.sum_reach) == (mid.coverage, mid.sum_reach)
        # Same pool, same first two criteria: whatever differs is the tie break.
        assert result.n_candidates == mid.n_candidates
        assert result.word != mid.word

    def test_every_candidate_tied_is_decided_by_the_isal_word(self) -> None:
        # At r = 0 no alignment survives, so the pool is the two members, each
        # covering only itself at the same summed reach: a total tie.
        left = build(2, [0, 1], [(0, [0, 1])])
        right = build(2, [0, 1], [(1, [0, 1])])
        result = coverage_consensus([left, right], r=0)

        assert result.n_candidates == 2
        assert result.n_ties == 1
        assert result.word == min(
            (fact_key_of(left), fact_key_of(right)),
            key=lambda w: isal_fingerprint(left if w == fact_key_of(left) else right),
        )

    def test_no_tie_means_no_change(self) -> None:
        """A run with ``n_ties == 0`` is bit-identical to the pre-change result.

        The tie break is evaluated only over the candidates the first two
        criteria could not separate, so a unique optimum cannot depend on which
        complete invariant orders words.  Measured over a sample rather than
        pinned to one collection, and the sample is asserted non-empty so the
        test cannot pass vacuously.
        """
        rng = random.Random(4242)
        checked = 0
        for _ in range(30):
            source = random_kb(rng, n_lo=4, n_hi=6, m_lo=3, m_hi=5, arity_hi=3)
            if not in_language_domain(source):
                continue
            # Four members, not two: with two, the objective's first two
            # criteria leave three or more candidates tied on every collection
            # sampled, so a two-member sweep would never reach the case this
            # test is about. The campaign's own N is 5 or 9.
            members = _insertion_members(rng, source, n_members=4)
            if members is None:
                continue
            result = coverage_consensus(members, r=2)
            if result.n_ties != 0 or result.n_excluded != 0:
                continue
            before = mid_objective(members, r=2)
            assert result.word == before.word
            assert result.kb == before.kb
            assert (result.coverage, result.sum_reach) == (before.coverage, before.sum_reach)
            assert result.candidates == before.candidates
            checked += 1
        assert checked >= 5, f"only {checked} tie-free collections sampled; the test is too weak"


class TestRepresentativeIsAProgram:
    """Prop. C.4: what the consensus returns round-trips through the language."""

    @pytest.mark.parametrize(
        "collection",
        [DISCONNECTED_WINNER, EMPTY_WINNER, TIE_BREAK_DISAGREES],
        ids=["disconnected", "empty", "tie_break"],
    )
    def test_the_winner_decodes(self, collection: tuple[list[SparseHypergraph], int]) -> None:
        members, r = collection
        kb = coverage_consensus(members, r).kb
        seed_label, word = isal_fingerprint(kb)
        decoded = string_to_hypergraph(
            word,
            k=required_k(kb),
            n_vertex_labels=kb.n_vertex_labels,
            n_edge_labels=kb.n_edge_labels,
            seed_label=seed_label,
        )
        assert fact_key_of(decoded) == fact_key_of(kb)

    def test_the_winner_decodes_over_a_sample(self) -> None:
        rng = random.Random(90210)
        checked = 0
        for _ in range(25):
            source = random_kb(rng, n_lo=4, n_hi=6, m_lo=3, m_hi=5, arity_hi=3)
            if not in_language_domain(source):
                continue
            members = _insertion_members(rng, source, n_members=2)
            if members is None:
                continue
            kb = coverage_consensus(members, r=2).kb
            # canonical_string is the domain gate; it raises on anything the
            # language cannot write, so reaching the round trip is the assertion.
            word = canonical_string(kb, k=required_k(kb), algorithm="canonical")
            decoded = string_to_hypergraph(
                word,
                k=required_k(kb),
                n_vertex_labels=kb.n_vertex_labels,
                n_edge_labels=kb.n_edge_labels,
                seed_label=isal_fingerprint(kb)[0],
            )
            assert fact_key_of(decoded) == fact_key_of(kb)
            checked += 1
        assert checked >= 5


def _insertion_members(
    rng: random.Random, source: SparseHypergraph, n_members: int
) -> list[SparseHypergraph] | None:
    """Return ``n_members`` pairwise non-isomorphic single-insertion variants of ``source``."""
    members: list[SparseHypergraph] = []
    keys = {fact_key_of(source)}
    for _ in range(n_members):
        for _ in range(60):
            fact = new_fact(rng, source, arity_hi=3)
            if fact is None:
                return None
            grown = rebuild(source, [*facts_of(source), fact])
            key = fact_key_of(grown)
            if key in keys:
                continue
            keys.add(key)
            members.append(grown)
            break
        else:
            return None
    return members
