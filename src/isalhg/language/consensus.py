"""The coverage consensus --- a representative that need not be one of the inputs.

A medoid can only return a member, so when every member is ``t`` edits from the
source, the medoid is ``t`` edits from the source too.  The language removes
that ceiling: a candidate is a *word*, it decodes to a knowledge base whether or
not anyone wrote it down, and the objective can therefore select the source
itself.  That contrast is what RQ3 of `DESIGN.md` measures, and this module is
the method it measures.

The objective (frozen, `DESIGN.md` RQ3)
---------------------------------------
Over a candidate set ``C``, return the lexicographic argmax of

* ``cov_r(c) = #{ i : reach_F(c, K_i) <= r }`` --- maximised;
* ``sum_i min(reach_F(c, K_i), r + 1)`` --- minimised, with an unreachable
  member charged ``r + 1``;
* the word of ``c`` in tuple order --- minimised, as the final tie break.

Nothing here is tuned: the objective is fixed in advance and the measured
recovery rate is whatever it is.

The candidate set
-----------------
The members, plus the *alignment-transfer* set: for an ordered pair
``(i, j)``, an alignment ``(A, B, node_map)`` between ``K_i`` and ``K_j`` says
which facts of each are unmatched and, through the canonical labellings of the
two isomorphic compacted remainders, how ``K_j``'s constants sit inside
``K_i``'s.  Every ``A' subset A`` and ``B' subset B`` with ``|A'| + |B'| <= r``
then yields the candidate ``K_i - A' + node_map(B')``.  ``node_map`` is
*partial*: a constant of ``K_j`` stranded by ``B`` has no counterpart in
``K_i``, so a transferred fact naming it **creates** the constant, carrying the
donor's type and (for evaluation only) the donor's identity.  That is
``insert_fact_new_constant``, the one insertion kind the Isal word owns
outright.  The candidate is then compacted --- a knowledge base is its facts, so
a constant that ``A'`` stranded is gone --- and the classes are deduplicated by
canonical key.  Because of both steps a candidate is no longer literally inside
the anchor's constant space, and
:attr:`ConsensusResult.constant_origin` records where each of its constants came
from.

The alignment budget: why ``2r``
-------------------------------
How much of ``K_i`` and ``K_j`` an alignment is allowed to delete decides which
candidates exist at all, and the answer follows from the objective rather than
from taste.  A candidate ``c`` that covers both members satisfies
``reach(c, K_i) <= r`` and ``reach(c, K_j) <= r``, so by the triangle
inequality ``reach(K_i, K_j) <= 2r``: the deletion pair that exposes such a
candidate is *always* inside the total budget ``|A| + |B| <= 2r``.  Enumerating
that family --- ``alignment_budget="triangle"``, the default --- is therefore
**complete** for the objective, while the subsets ``A' subset A``,
``B' subset B`` stay bounded by ``|A'| + |B'| <= r`` because a candidate is
built with a budget of ``r``.

The two narrower readings are kept as recorded variants, and each misses
something measurable:

* ``"per_side"`` (``|A| <= r`` and ``|B| <= r``) misses candidates that sit
  between two members at unequal distances.  With ``K_i = S + 2`` facts,
  ``K_j = S`` and ``r = 1``, the candidate ``S + 1`` fact covers both members,
  and it comes from the alignment ``(|A|, |B|) = (2, 0)`` --- outside the
  per-side family, inside the triangle one.
* ``"sum"`` (``|A| + |B| <= r``) misses the source itself: two insertion-only
  members at ``t = 2`` are at reach 4, so no alignment survives at all and the
  candidate set collapses to the members.

Ruling of 2026-09-05 (orchestrator, amending `DESIGN.md` RQ3): the triangle
family is the default; the runners report only the default.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from itertools import combinations
from typing import Literal

from isalhg.core.fact_word import Word
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.language.majority import majority_merge
from isalhg.language.reach import (
    Alignment,
    FactSubset,
    LanguageError,
    RemainderIndex,
    compact_constants,
    compatible,
    fact_key_of,
    node_map_from_remainders,
    remove_facts,
)

AlignmentBudget = Literal["triangle", "per_side", "sum"]
BUDGETS: tuple[AlignmentBudget, ...] = ("triangle", "per_side", "sum")


def _index_radius(r: int, budget: AlignmentBudget) -> int:
    """Return how deep the per-member remainder indices must go for ``budget``."""
    return 2 * r if budget == "triangle" else r


class ConsensusError(LanguageError):
    """Raised when a consensus cannot be computed as asked."""


@dataclass(frozen=True)
class CandidateScore:
    """One candidate's score under the frozen objective.

    Parameters
    ----------
    word : Word
        The candidate's canonical key; also the final tie-break value.
    coverage : int
        Number of members within reach ``r``.
    sum_reach : int
        ``sum_i min(reach(c, K_i), r + 1)``.
    origin : str
        ``"member:<i>"`` for a member, ``"transfer:<i>,<j>"`` for a candidate
        built from ``K_i`` with facts transferred from ``K_j``.  A class first
        produced as a member keeps the member origin.
    """

    word: Word
    coverage: int
    sum_reach: int
    origin: str


@dataclass(frozen=True)
class ConsensusResult:
    """The winning candidate and the numbers RQ3's rows need.

    Parameters
    ----------
    kb : SparseHypergraph
        The representative, built on the constant space of ``members[anchor]``.
    anchor : int
        Index of the member the representative was built from.
    node_map : tuple[int | None, ...]
        ``node_map[v]`` is the constant of ``members[anchor]`` that constant
        ``v`` of ``kb`` denotes, or ``None`` when there is none.  It is *not*
        the identity: compacting the candidate drops the constants its deletions
        stranded and renumbers what is left, and a transferred fact can create a
        constant the anchor never had.  Use :attr:`constant_origin` when the
        created constants matter.
    constant_origin : tuple[tuple[int, int], ...]
        ``constant_origin[v] = (member index, constant of that member)`` for
        every constant of ``kb``: where the constant --- and therefore, for
        evaluation only, its identity --- came from.  Every entry names
        ``anchor`` except those created by a transferred fact, which name the
        donor.
    word : Word
        ``kb``'s canonical key.
    coverage, sum_reach : int
        The winning objective values.
    n_candidates : int
        Size of the deduplicated candidate set.
    n_ties : int
        How many other candidates matched the winner on
        ``(coverage, sum_reach)`` and were separated only by the word rule.
    candidates : tuple[CandidateScore, ...]
        Every candidate's score, in generation order.
    """

    kb: SparseHypergraph
    anchor: int
    node_map: tuple[int | None, ...]
    constant_origin: tuple[tuple[int, int], ...]
    word: Word
    coverage: int
    sum_reach: int
    n_candidates: int
    n_ties: int
    candidates: tuple[CandidateScore, ...]


def _pair_alignments(
    left: RemainderIndex,
    right: RemainderIndex,
    r: int,
    budget: AlignmentBudget,
) -> Iterator[Alignment]:
    """Yield the alignments between two members from indices shared across all pairs."""
    top_a = _index_radius(r, budget)
    for a in range(top_a + 1):
        table_a = left.level(a)
        if not table_a:
            continue
        if budget == "triangle":
            top_b = 2 * r - a
        elif budget == "per_side":
            top_b = r
        else:
            top_b = r - a
        for b in range(top_b + 1):
            table_b = right.level(b)
            for word in sorted(table_a.keys() & table_b.keys()):
                for subset_a in table_a[word]:
                    remainder_a = left.remainder(subset_a)
                    for subset_b in table_b[word]:
                        yield Alignment(
                            deleted_from_k=subset_a,
                            deleted_from_k2=subset_b,
                            node_map=node_map_from_remainders(
                                remainder_a, right.remainder(subset_b)
                            ),
                        )


@dataclass(frozen=True)
class _Candidate:
    """One decoded candidate together with the provenance of each of its constants.

    Parameters
    ----------
    kb : SparseHypergraph
        The candidate, compacted.
    host_of : tuple[int | None, ...]
        Per candidate constant, the host constant it came from, or ``None``.
    donor_of : tuple[int | None, ...]
        Per candidate constant, the donor constant that created it, or ``None``.
        Exactly one of the two entries is set for every constant.
    """

    kb: SparseHypergraph
    host_of: tuple[int | None, ...]
    donor_of: tuple[int | None, ...]


def _transfer(
    host: SparseHypergraph,
    drop: FactSubset,
    donor: SparseHypergraph,
    take: FactSubset,
    node_map: tuple[int | None, ...],
) -> _Candidate:
    """Return ``host - drop`` with the facts ``take`` of ``donor`` carried over by ``node_map``.

    A donor constant with no image under the partial ``node_map`` is *created*
    in the host's space with the donor's type, which is the
    ``insert_fact_new_constant`` edit of the language.  The result is compacted,
    because a constant that ``drop`` stranded is no longer part of the knowledge
    base.

    Parameters
    ----------
    host, donor : SparseHypergraph
        The two members.
    drop, take : FactSubset
        Facts removed from ``host`` and carried over from ``donor``.
    node_map : tuple[int | None, ...]
        Partial map from ``donor``'s constants to ``host``'s.

    Returns
    -------
    _Candidate
        The compacted candidate and the origin of each of its constants.
    """
    result = remove_facts(host, drop)
    edges = [members for _, members, _ in result.iter_edges()]
    labels = [label for _, _, label in result.iter_edges()]
    types = [host.vertex_label(v) for v in range(host.n_nodes)]
    created: dict[int, int] = {}
    for e in take:
        members = []
        for v in donor.members(e):
            image = node_map[v]
            if image is None:
                image = created.get(v)
                if image is None:
                    image = len(types)
                    created[v] = image
                    types.append(donor.vertex_label(v))
            members.append(image)
        edges.append(frozenset(members))
        labels.append(donor.edge_label(e))
    extended = SparseHypergraph(
        len(types),
        edges,
        n_vertex_labels=host.n_vertex_labels,
        n_edge_labels=host.n_edge_labels,
        vertex_labels=types,
        edge_labels=labels,
    )
    kb, survivors = compact_constants(extended)
    donor_by_slot = {slot: v for v, slot in created.items()}
    return _Candidate(
        kb=kb,
        host_of=tuple(v if v < host.n_nodes else None for v in survivors),
        donor_of=tuple(donor_by_slot.get(v) for v in survivors),
    )


def _subsets_up_to(items: FactSubset, bound: int) -> Iterator[FactSubset]:
    """Yield every subset of ``items`` of size at most ``bound``, smallest first."""
    for size in range(min(bound, len(items)) + 1):
        yield from combinations(items, size)


class _Scorer:
    """Scores candidates against the members, sharing every canonicalization.

    Each member is indexed once as ``{remainder word: fewest deletions}``.  A
    candidate is then expanded one deletion level at a time; a member settles as
    soon as the level index reaches its best total, because a level ``a``
    contributes at least ``a`` to the sum.  On the RQ3 cells this stops at level
    1 and the candidate costs ``1 + m`` canonicalizations instead of
    ``1 + m + C(m, 2)``.
    """

    __slots__ = ("_cache", "_members", "_r", "_reachable")

    def __init__(self, members: Sequence[SparseHypergraph], r: int) -> None:
        self._r = r
        self._members = list(members)
        self._reachable = [RemainderIndex(H, r).min_deletions() for H in self._members]
        self._cache: dict[SparseHypergraph, Word] = {}

    def key(self, H: SparseHypergraph) -> Word:
        """Return the canonical key of ``H``, memoized across every candidate."""
        cached = self._cache.get(H)
        if cached is None:
            cached = fact_key_of(H)
            self._cache[H] = cached
        return cached

    def _level_keys(self, candidate: SparseHypergraph, size: int) -> set[Word]:
        """Return the canonical keys of the candidate's remainders under ``size`` deletions."""
        return {
            self.key(remove_facts(candidate, subset))
            for subset in combinations(range(candidate.n_edges), size)
        }

    def score(self, candidate: SparseHypergraph) -> tuple[int, int]:
        """Return ``(coverage, sum_reach)`` of ``candidate`` against the members.

        Unreached members carry ``r + 1``, which is both the objective's charge
        for them and the sentinel the loop settles on.
        """
        unreached = self._r + 1
        best = [unreached] * len(self._members)
        live = [i for i, H in enumerate(self._members) if compatible(candidate, H, self._r)]
        for a in range(self._r + 1):
            live = [i for i in live if best[i] > a]
            if not live:
                break
            keys = self._level_keys(candidate, a)
            if not keys:
                break
            for i in live:
                table = self._reachable[i]
                for key in keys:
                    b = table.get(key)
                    if b is not None and a + b < best[i]:
                        best[i] = a + b
        coverage = sum(1 for value in best if value <= self._r)
        return coverage, sum(best)


def _provenance(
    built: _Candidate, host_index: int, donor_index: int
) -> tuple[tuple[int, int], ...]:
    """Return, per constant of ``built.kb``, the member and constant it came from.

    Parameters
    ----------
    built : _Candidate
        The candidate and its two per-constant origin vectors.
    host_index, donor_index : int
        Positions of the host and the donor in the member sequence.

    Returns
    -------
    tuple[tuple[int, int], ...]
        Index-aligned with the candidate's constants.

    Raises
    ------
    ConsensusError
        If a constant claims neither a host nor a donor origin, which would mean
        the transfer lost track of an identity.
    """
    out: list[tuple[int, int]] = []
    for host_constant, donor_constant in zip(built.host_of, built.donor_of, strict=True):
        if host_constant is not None:
            out.append((host_index, host_constant))
        elif donor_constant is not None:
            out.append((donor_index, donor_constant))
        else:
            raise ConsensusError("a transferred candidate carries a constant with no origin")
    return tuple(out)


@dataclass(frozen=True)
class _PoolEntry:
    """A deduplicated candidate class: the object, its anchor, its provenance, its origin tag."""

    kb: SparseHypergraph
    anchor: int
    constant_origin: tuple[tuple[int, int], ...]
    origin: str


def _candidate_pool(
    members: Sequence[SparseHypergraph],
    r: int,
    budget: AlignmentBudget,
    scorer: _Scorer,
) -> dict[Word, _PoolEntry]:
    """Build the deduplicated candidate set: the members, then the alignment transfers."""
    pool: dict[Word, _PoolEntry] = {}
    for i, H in enumerate(members):
        core, survivors = compact_constants(H)
        pool.setdefault(
            scorer.key(core),
            _PoolEntry(core, i, tuple((i, v) for v in survivors), f"member:{i}"),
        )

    indices = [RemainderIndex(H, _index_radius(r, budget)) for H in members]
    for i, host in enumerate(members):
        for j, donor in enumerate(members):
            if i == j:
                continue
            origin = f"transfer:{i},{j}"
            for alignment in _pair_alignments(indices[i], indices[j], r, budget):
                for drop in _subsets_up_to(alignment.deleted_from_k, r):
                    for take in _subsets_up_to(alignment.deleted_from_k2, r - len(drop)):
                        built = _transfer(host, drop, donor, take, alignment.node_map)
                        pool.setdefault(
                            scorer.key(built.kb),
                            _PoolEntry(built.kb, i, _provenance(built, i, j), origin),
                        )
    return pool


def coverage_consensus(
    members: Sequence[SparseHypergraph],
    r: int = 2,
    *,
    alignment_budget: AlignmentBudget = "triangle",
) -> ConsensusResult:
    """Return the coverage consensus of ``members`` at radius ``r``.

    Parameters
    ----------
    members : Sequence[SparseHypergraph]
        The disagreeing descriptions; at least one, all over the same constant
        set for the candidate transfers to mean anything.
    r : int, optional
        Reach radius of the objective and budget of the candidate generation.
        Default 2, the radius `DESIGN.md` RQ3 fixes as the unknown-budget
        setting.
    alignment_budget : {"triangle", "per_side", "sum"}, optional
        Which alignments generate candidates.  ``"triangle"`` (default) takes
        ``|A| + |B| <= 2r``, the family the triangle inequality shows is
        complete for the objective; ``"per_side"`` takes ``|A| <= r`` and
        ``|B| <= r``; ``"sum"`` takes ``|A| + |B| <= r``.  The subset budget
        ``|A'| + |B'| <= r`` is the same in all three.  See the module
        docstring for what the two narrower readings miss.

    Returns
    -------
    ConsensusResult
        The winner and its provenance, plus every candidate's score.

    Raises
    ------
    ConsensusError
        If ``members`` is empty, ``r`` is negative, or ``alignment_budget`` is
        not one of the three readings.
    isalhg.errors.BackendUnavailableError
        If ``pynauty`` is not installed.
    """
    if not members:
        raise ConsensusError("coverage_consensus needs at least one member")
    if r < 0:
        raise ConsensusError(f"r must be non-negative; got {r}")
    if alignment_budget not in BUDGETS:
        raise ConsensusError(f"alignment_budget must be one of {BUDGETS}; got {alignment_budget!r}")

    scorer = _Scorer(members, r)
    pool = _candidate_pool(members, r, alignment_budget, scorer)

    scores: list[CandidateScore] = []
    ranked: list[tuple[tuple[int, int, Word], Word]] = []
    for word, entry in pool.items():
        coverage, sum_reach = scorer.score(entry.kb)
        scores.append(CandidateScore(word, coverage, sum_reach, entry.origin))
        ranked.append(((-coverage, sum_reach, word), word))

    ranked.sort(key=lambda item: item[0])
    (best_neg_coverage, best_sum_reach, _), winner_word = ranked[0]
    winner = pool[winner_word]
    n_ties = (
        sum(
            1
            for score in scores
            if score.coverage == -best_neg_coverage and score.sum_reach == best_sum_reach
        )
        - 1
    )

    return ConsensusResult(
        kb=winner.kb,
        anchor=winner.anchor,
        node_map=tuple(
            constant if member == winner.anchor else None
            for member, constant in winner.constant_origin
        ),
        constant_origin=winner.constant_origin,
        word=winner_word,
        coverage=-best_neg_coverage,
        sum_reach=best_sum_reach,
        n_candidates=len(pool),
        n_ties=n_ties,
        candidates=tuple(scores),
    )


__all__ = [
    "BUDGETS",
    "AlignmentBudget",
    "CandidateScore",
    "ConsensusError",
    "ConsensusResult",
    "coverage_consensus",
    "majority_merge",
]
