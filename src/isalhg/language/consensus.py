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
two isomorphic remainders, how ``K_j``'s constants sit inside ``K_i``'s.  Every
``A' subset A`` and ``B' subset B`` with ``|A'| + |B'| <= r`` then yields the
candidate ``K_i - A' + node_map(B')``, expressed in ``K_i``'s constant space so
that the evaluation can inherit ``K_i``'s identities.  Classes are deduplicated
by canonical key.

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
    compatible,
    fact_key_of,
    node_map_from_ranks,
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
        The representative, in the constant space of ``members[anchor]``.
    anchor : int
        Index of the member whose constant space (and, for evaluation,
        identities) ``kb`` is expressed in.
    node_map : tuple[int, ...]
        ``node_map[v]`` is the constant of ``members[anchor]`` that constant
        ``v`` of ``kb`` denotes.  Always the identity, because every candidate
        is built inside its anchor's constant space; carried explicitly so a
        caller never has to assume it.
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
    node_map: tuple[int, ...]
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
                    ranks_a = left.ranks(subset_a)
                    for subset_b in table_b[word]:
                        yield Alignment(
                            deleted_from_k=subset_a,
                            deleted_from_k2=subset_b,
                            node_map=node_map_from_ranks(ranks_a, right.ranks(subset_b)),
                        )


def _transfer(
    host: SparseHypergraph,
    drop: FactSubset,
    donor: SparseHypergraph,
    take: FactSubset,
    node_map: tuple[int, ...],
) -> SparseHypergraph:
    """Return ``host - drop`` with the facts ``take`` of ``donor`` carried over by ``node_map``."""
    result = remove_facts(host, drop)
    edges = [members for _, members, _ in result.iter_edges()]
    labels = [label for _, _, label in result.iter_edges()]
    for e in take:
        edges.append(frozenset(node_map[v] for v in donor.members(e)))
        labels.append(donor.edge_label(e))
    return SparseHypergraph(
        host.n_nodes,
        edges,
        n_vertex_labels=host.n_vertex_labels,
        n_edge_labels=host.n_edge_labels,
        vertex_labels=[host.vertex_label(v) for v in range(host.n_nodes)],
        edge_labels=labels,
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
        live = [i for i, H in enumerate(self._members) if compatible(candidate, H)]
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


def _candidate_pool(
    members: Sequence[SparseHypergraph],
    r: int,
    budget: AlignmentBudget,
    scorer: _Scorer,
) -> dict[Word, tuple[SparseHypergraph, int, str]]:
    """Build the deduplicated candidate set: the members, then the alignment transfers."""
    pool: dict[Word, tuple[SparseHypergraph, int, str]] = {}
    for i, H in enumerate(members):
        pool.setdefault(scorer.key(H), (H, i, f"member:{i}"))

    indices = [RemainderIndex(H, _index_radius(r, budget)) for H in members]
    for i, host in enumerate(members):
        for j, donor in enumerate(members):
            if i == j:
                continue
            origin = f"transfer:{i},{j}"
            for alignment in _pair_alignments(indices[i], indices[j], r, budget):
                for drop in _subsets_up_to(alignment.deleted_from_k, r):
                    for take in _subsets_up_to(alignment.deleted_from_k2, r - len(drop)):
                        candidate = _transfer(host, drop, donor, take, alignment.node_map)
                        pool.setdefault(scorer.key(candidate), (candidate, i, origin))
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
    for word, (candidate, _, origin) in pool.items():
        coverage, sum_reach = scorer.score(candidate)
        scores.append(CandidateScore(word, coverage, sum_reach, origin))
        ranked.append(((-coverage, sum_reach, word), word))

    ranked.sort(key=lambda item: item[0])
    (best_neg_coverage, best_sum_reach, _), winner_word = ranked[0]
    kb, anchor, _ = pool[winner_word]
    n_ties = (
        sum(
            1
            for score in scores
            if score.coverage == -best_neg_coverage and score.sum_reach == best_sum_reach
        )
        - 1
    )

    return ConsensusResult(
        kb=kb,
        anchor=anchor,
        node_map=tuple(range(kb.n_nodes)),
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
