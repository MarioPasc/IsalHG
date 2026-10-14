"""Exact fact-level reach between two knowledge bases, by delete-and-match.

``reach_F(K, K')`` is the fewest fact indels that carry one knowledge base onto
the other::

    reach_F(K, K') = min { |A| + |B| : A subset F(K), B subset F(K'),
                           compact(K - A) isomorphic compact(K' - B) }

Substitution is excluded on purpose (`DESIGN.md` RQ3): it is the **indel** ball,
because a substitution would collapse the ``2t`` gap between two members of a
variant collection.

A knowledge base *is* its set of ground facts, so a constant left with no fact
by a deletion has left the knowledge base: both remainders are **compacted**
before they are compared, exactly as
:func:`isalhg.datasets.kb.base.compact` does for records.  The two remainders
therefore need not carry the same constant count, and a deletion member of a
variant collection is at reach 1 from its source even when the deleted fact was
the last one naming some constant.

The computation is exact for a bounded radius and needs no isomorphism search
of its own.  Enumerate every ``A`` with ``|A| <= r_max`` and every ``B`` with
``|B| <= r_max``, canonicalize both compacted remainders with the article's
addressing (:func:`isalhg.metric_space.distances.fact_levenshtein.fact_word`)
and compare *words*: because the fact word is a complete isomorphism invariant,
word equality is isomorphism.  Scanning the total budget ``s = |A| + |B|``
upwards and returning the first ``s`` that matches gives the minimum, and the
enumeration is symmetric in its two arguments, so ``reach`` is symmetric.

Never compare rank *vectors* across two knowledge bases (`DESIGN.md` G1): a
canonical labelling is canonical only up to an automorphism of the canonical
form.  This module only ever compares words; :mod:`isalhg.language.alignment`
takes ranks from the two *isomorphic* compacted remainders, where rank equality
is a genuine isomorphism.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from itertools import combinations

from isalhg.core.fact_word import Word, encode_fact_word
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.errors import IsalHGError
from isalhg.iso_backends.canonical_order import canonical_ranks
from isalhg.metric_space.distances.fact_levenshtein import fact_word
from isalhg.types import EdgeId, NodeId

FactSubset = tuple[EdgeId, ...]


class LanguageError(IsalHGError):
    """Root of the language-layer exception hierarchy."""


class ReachError(LanguageError):
    """Raised when a reach computation is asked for something it cannot answer."""


def compact_constants(H: SparseHypergraph) -> tuple[SparseHypergraph, tuple[NodeId, ...]]:
    """Return ``H`` without the constants that occur in no fact, densely renumbered.

    A knowledge base is its set of facts, so a constant naming nothing is not
    part of it.  This is the hypergraph-level twin of
    :func:`isalhg.datasets.kb.base.compact`.

    Parameters
    ----------
    H : SparseHypergraph
        The knowledge base.

    Returns
    -------
    kb : SparseHypergraph
        Same facts, same types, same label vocabularies; only the constants of
        positive degree, renumbered ``0 .. len(survivors) - 1`` in ascending
        order of their old ids.
    survivors : tuple[NodeId, ...]
        ``survivors[u]`` is the constant of ``H`` that constant ``u`` of ``kb``
        came from.
    """
    survivors = tuple(v for v in range(H.n_nodes) if H.degree(v) > 0)
    if len(survivors) == H.n_nodes:
        return H, survivors
    remap = {v: u for u, v in enumerate(survivors)}
    edges = []
    labels = []
    for _, members, label in H.iter_edges():
        edges.append(frozenset(remap[v] for v in members))
        labels.append(label)
    kb = SparseHypergraph(
        len(survivors),
        edges,
        n_vertex_labels=H.n_vertex_labels,
        n_edge_labels=H.n_edge_labels,
        vertex_labels=[H.vertex_label(v) for v in survivors],
        edge_labels=labels,
    )
    return kb, survivors


def fact_key_of(H: SparseHypergraph) -> Word:
    """Return the canonical key of ``H`` --- the role-free fact word of its compaction.

    The key every construction in this package is indexed by.  Two knowledge
    bases share a key iff they are isomorphic as labelled hypergraphs once the
    constants naming nothing are dropped, so the key is what a "decoded class"
    means here.

    Parameters
    ----------
    H : SparseHypergraph
        The knowledge base.

    Returns
    -------
    Word
        ``fact_word(compact(H))``: one type token per occurring constant in
        canonical-rank order followed by ``m`` fact tokens sorted by
        ``(predicate, rank tuple)``.

    Raises
    ------
    isalhg.errors.BackendUnavailableError
        If ``pynauty`` is not installed.
    """
    core, _ = compact_constants(H)
    return fact_word(core)


def remove_facts(H: SparseHypergraph, drop: Iterable[EdgeId]) -> SparseHypergraph:
    """Return ``H`` with the facts in ``drop`` removed and every constant kept.

    The constants are kept here so the caller can still address them; the
    compaction that gives a remainder its identity is
    :func:`compact_constants`, applied downstream.

    Parameters
    ----------
    H : SparseHypergraph
        The knowledge base.
    drop : Iterable[EdgeId]
        Edge ids of ``H`` to remove; ids outside ``range(H.n_edges)`` are
        rejected.

    Returns
    -------
    SparseHypergraph
        Same constants, same types, same label vocabularies; the surviving
        facts in their original relative order, renumbered contiguously.

    Raises
    ------
    ReachError
        If ``drop`` names an edge id ``H`` does not have.
    """
    dropped = frozenset(drop)
    for e in dropped:
        if not 0 <= e < H.n_edges:
            raise ReachError(f"edge {e} is outside range({H.n_edges}) of the knowledge base")
    edges = []
    labels = []
    for e, members, label in H.iter_edges():
        if e in dropped:
            continue
        edges.append(members)
        labels.append(label)
    return SparseHypergraph(
        H.n_nodes,
        edges,
        n_vertex_labels=H.n_vertex_labels,
        n_edge_labels=H.n_edge_labels,
        vertex_labels=[H.vertex_label(v) for v in range(H.n_nodes)],
        edge_labels=labels,
    )


@dataclass(frozen=True)
class Remainder:
    """One compacted remainder ``compact(H - A)``, addressed back to ``H``.

    Parameters
    ----------
    word : Word
        Canonical key of the compacted remainder; the value remainders are
        matched on.
    ranks : tuple[int, ...]
        ``ranks[u]`` is the canonical rank of constant ``u`` of the *compacted*
        remainder.
    survivors : tuple[int, ...]
        ``survivors[u]`` is the constant of ``H`` that constant ``u`` of the
        compacted remainder came from.
    n_source : int
        Constant count of ``H``, so a map built from this remainder can be
        stated over the whole source constant set.
    """

    word: Word
    ranks: tuple[int, ...]
    survivors: tuple[int, ...]
    n_source: int


class RemainderIndex:
    """The canonical words of every compacted remainder of ``H`` under ``<= r_max`` deletions.

    Levels are computed on first access and cached, so a caller that can decide
    after level ``a`` never pays for level ``a + 1``.  One level costs
    ``C(m, a)`` canonicalizations.

    Parameters
    ----------
    H : SparseHypergraph
        The knowledge base whose remainders are indexed.
    r_max : int
        Largest deletion set considered.

    Raises
    ------
    ReachError
        If ``r_max`` is negative.
    """

    __slots__ = ("_H", "_levels", "_min_deletions", "_r_max", "_remainders")

    def __init__(self, H: SparseHypergraph, r_max: int) -> None:
        if r_max < 0:
            raise ReachError(f"r_max must be non-negative; got {r_max}")
        self._H = H
        self._r_max = r_max
        self._levels: list[dict[Word, list[FactSubset]] | None] = [None] * (r_max + 1)
        self._remainders: dict[FactSubset, Remainder] = {}
        self._min_deletions: dict[Word, int] | None = None

    @property
    def hypergraph(self) -> SparseHypergraph:
        """The indexed knowledge base."""
        return self._H

    @property
    def r_max(self) -> int:
        """The largest deletion set this index covers."""
        return self._r_max

    def level(self, size: int) -> dict[Word, list[FactSubset]]:
        """Return ``{canonical word: deletion sets}`` for deletion sets of ``size`` facts.

        Parameters
        ----------
        size : int
            Deletion-set size; ``0 <= size <= r_max``.

        Returns
        -------
        dict[Word, list[FactSubset]]
            Empty when ``size`` exceeds the fact count.  Deletion sets appear in
            :func:`itertools.combinations` order, so the mapping is
            deterministic.

        Raises
        ------
        ReachError
            If ``size`` is outside ``[0, r_max]``.
        """
        if not 0 <= size <= self._r_max:
            raise ReachError(f"level {size} is outside [0, {self._r_max}]")
        cached = self._levels[size]
        if cached is not None:
            return cached
        table: dict[Word, list[FactSubset]] = {}
        for subset in combinations(range(self._H.n_edges), size):
            core, survivors = compact_constants(remove_facts(self._H, subset))
            ranks = canonical_ranks(core)
            word = encode_fact_word(core, ranks)
            self._remainders[subset] = Remainder(word, ranks, survivors, self._H.n_nodes)
            table.setdefault(word, []).append(subset)
        self._levels[size] = table
        return table

    def remainder(self, subset: FactSubset) -> Remainder:
        """Return the compacted remainder ``H - subset``, with its addressing back to ``H``.

        The subset must already have been produced by :meth:`level`, which is
        where the canonicalization happens; the result is kept because
        :mod:`isalhg.language.alignment` builds its node maps from the ranks of
        the two isomorphic remainders and must not recompute them.

        Parameters
        ----------
        subset : FactSubset
            A deletion set previously returned by :meth:`level`.

        Returns
        -------
        Remainder
            Its word, canonical ranks, surviving constants, and ``H.n_nodes``.

        Raises
        ------
        ReachError
            If the subset has not been indexed.
        """
        try:
            return self._remainders[subset]
        except KeyError as exc:
            raise ReachError(f"deletion set {subset!r} has not been indexed") from exc

    def min_deletions(self) -> dict[Word, int]:
        """Return ``{canonical word: fewest deletions reaching it}``, forcing every level.

        Returns
        -------
        dict[Word, int]
            One entry per distinct remainder word, carrying the smallest
            deletion-set size that produces it.
        """
        if self._min_deletions is not None:
            return self._min_deletions
        table: dict[Word, int] = {}
        for size in range(self._r_max + 1):
            for word in self.level(size):
                table.setdefault(word, size)
        self._min_deletions = table
        return table


def _fact_profile(H: SparseHypergraph) -> Counter[tuple[int, int]]:
    """Return the multiset of ``(predicate, arity)`` over ``H``'s facts."""
    return Counter((label, len(members)) for _, members, label in H.iter_edges())


def _occurring_types(H: SparseHypergraph) -> Counter[int]:
    """Return the multiset of types over the constants of ``H`` that occur in a fact."""
    return Counter(H.vertex_label(v) for v in range(H.n_nodes) if H.degree(v) > 0)


def _stable_types(H: SparseHypergraph, r_max: int) -> Counter[int]:
    """Return the multiset of types over constants no ``<= r_max`` deletion can strand."""
    return Counter(H.vertex_label(v) for v in range(H.n_nodes) if H.degree(v) > r_max)


def compatible(K: SparseHypergraph, K2: SparseHypergraph, r_max: int) -> bool:
    """Return whether a reach of at most ``r_max`` between ``K`` and ``K2`` is possible.

    Two necessary conditions, both cheap and both stated so that compaction
    cannot break them.  Neither looks at the *total* constant count, which
    compaction no longer preserves.

    *Fact profile.*  Isomorphic knowledge bases carry the same multiset of
    ``(predicate, arity)``, and a deletion only removes elements from that
    multiset.  Writing ``P`` for the profile and ``Q`` for the common profile of
    the two remainders, ``Q`` is contained in both ``P(K)`` and ``P(K2)``, hence
    in their multiset intersection; so ``|A| = m - |Q| >= m - |P(K) & P(K2)|``
    and likewise for ``|B|``.  A budget below ``m + m2 - 2 |P(K) & P(K2)|``
    therefore cannot exist.

    *Undeletable types.*  A constant of degree greater than ``r_max`` keeps a
    fact under every deletion set the budget allows, so it survives compaction
    and its type appears in the remainder's type multiset.  The remainder's
    constants are a subset of the other side's occurring constants, so the
    types of ``K``'s high-degree constants must be contained, as a multiset, in
    the types of ``K2``'s occurring constants --- and symmetrically.

    Parameters
    ----------
    K, K2 : SparseHypergraph
        The two knowledge bases.
    r_max : int
        Total deletion budget ``|A| + |B|`` the caller will spend.

    Returns
    -------
    bool
        ``False`` when no deletion pair inside ``r_max`` can make the two
        isomorphic.  ``True`` is not a promise that one does.

    Raises
    ------
    ReachError
        If ``r_max`` is negative.
    """
    if r_max < 0:
        raise ReachError(f"r_max must be non-negative; got {r_max}")
    shared = _fact_profile(K) & _fact_profile(K2)
    if K.n_edges + K2.n_edges - 2 * sum(shared.values()) > r_max:
        return False
    return _stable_types(K, r_max) <= _occurring_types(K2) and _stable_types(
        K2, r_max
    ) <= _occurring_types(K)


def reach(K: SparseHypergraph, K2: SparseHypergraph, r_max: int = 2) -> int | None:
    """Return the exact fact-level reach between ``K`` and ``K2``, or ``None`` past ``r_max``.

    Parameters
    ----------
    K, K2 : SparseHypergraph
        The two knowledge bases, written against the same type and predicate
        vocabularies (words are only comparable inside one alphabet scope).
    r_max : int, optional
        Largest total budget ``|A| + |B|`` considered.  Default 2, the radius
        `DESIGN.md` RQ3 fixes.

    Returns
    -------
    int or None
        ``min |A| + |B|`` over deletion pairs whose compacted remainders are
        isomorphic, or ``None`` when no such pair exists within ``r_max``.
        ``0`` iff the two are isomorphic once their constants naming nothing are
        dropped.  The value is symmetric in its two arguments.

    Raises
    ------
    ReachError
        If ``r_max`` is negative.
    isalhg.errors.BackendUnavailableError
        If ``pynauty`` is not installed.
    """
    if r_max < 0:
        raise ReachError(f"r_max must be non-negative; got {r_max}")
    if not compatible(K, K2, r_max):
        return None
    left = RemainderIndex(K, r_max)
    right = RemainderIndex(K2, r_max)
    for total in range(r_max + 1):
        for a in range(total + 1):
            if left.level(a).keys() & right.level(total - a).keys():
                return total
    return None


@dataclass(frozen=True)
class Alignment:
    """One witness that two knowledge bases agree after a bounded deletion pair.

    Parameters
    ----------
    deleted_from_k : tuple[int, ...]
        Edge ids removed from the first knowledge base (``A``), ascending.
    deleted_from_k2 : tuple[int, ...]
        Edge ids removed from the second (``B``), ascending.
    node_map : tuple[int | None, ...]
        ``node_map[v]``, for a constant ``v`` of the *second* knowledge base, is
        the constant of the *first* it corresponds to, or ``None`` when ``v``
        occurs in no surviving fact of ``K2 - B`` and so has no counterpart.
        Restricted to the constants it does map, it is a genuine isomorphism
        ``compact(K2 - B) -> compact(K - A)``.
    """

    deleted_from_k: tuple[int, ...]
    deleted_from_k2: tuple[int, ...]
    node_map: tuple[int | None, ...]


def node_map_from_remainders(left: Remainder, right: Remainder) -> tuple[int | None, ...]:
    """Compose two isomorphic compacted remainders into a partial constant map.

    ``left`` addresses the constants of ``compact(K - A)``, ``right`` those of
    ``compact(K2 - B)``, and the two carry the same word.  The composition
    ``u -> rank_left^-1(rank_right(u))`` is an isomorphism
    ``compact(K2 - B) -> compact(K - A)``: equal type prefixes make it label
    preserving, and equal fact-token sequences make it fact preserving, because
    the rank map is injective so a fact and its token determine one another.
    Lifting both ends through ``survivors`` states it over ``K2``'s constants,
    where it is *partial*: a constant stranded by ``B`` has no image.

    This is the only place ranks cross between two objects, and it is legal
    precisely because the two objects are isomorphic (`DESIGN.md` G1).  The
    ranks of ``K`` and ``K2`` themselves are never composed.

    Parameters
    ----------
    left, right : Remainder
        Two remainders with equal words.

    Returns
    -------
    tuple[int | None, ...]
        Length ``right.n_source``; ``None`` where the constant did not survive.
    """
    inverse = [0] * len(left.ranks)
    for u, rank in enumerate(left.ranks):
        inverse[rank] = u
    out: list[int | None] = [None] * right.n_source
    for u, rank in enumerate(right.ranks):
        out[right.survivors[u]] = left.survivors[inverse[rank]]
    return tuple(out)


def alignments(
    K: SparseHypergraph,
    K2: SparseHypergraph,
    r_max: int = 2,
    *,
    max_per_side: int | None = None,
) -> list[Alignment]:
    """Return every bounded deletion pair whose compacted remainders are isomorphic.

    Parameters
    ----------
    K, K2 : SparseHypergraph
        The two knowledge bases.
    r_max : int, optional
        Bound on the total budget ``|A| + |B|``.  Default 2.
    max_per_side : int or None, optional
        Additional bound applied to ``|A|`` and to ``|B|`` separately.  ``None``
        (default) leaves the frozen total-budget semantics untouched.  Passing
        ``max_per_side=r`` together with ``r_max=2 * r`` enumerates the
        *per-side* family ``|A| <= r and |B| <= r``, which is the family
        `DESIGN.md` RQ3 describes as "deleting ``<= r`` of its facts and
        inserting ``<= r`` facts" and which
        :func:`isalhg.language.consensus.coverage_consensus` needs; see that
        function's notes.

    Returns
    -------
    list[Alignment]
        Sorted by ``(deleted_from_k, deleted_from_k2)``, so the result is
        deterministic.  Empty when no deletion pair inside the budget matches.

    Raises
    ------
    ReachError
        If ``r_max`` is negative or ``max_per_side`` is negative.
    isalhg.errors.BackendUnavailableError
        If ``pynauty`` is not installed.
    """
    if r_max < 0:
        raise ReachError(f"r_max must be non-negative; got {r_max}")
    if max_per_side is not None and max_per_side < 0:
        raise ReachError(f"max_per_side must be non-negative; got {max_per_side}")
    if not compatible(K, K2, r_max):
        return []
    side_cap = r_max if max_per_side is None else min(r_max, max_per_side)
    left = RemainderIndex(K, side_cap)
    right = RemainderIndex(K2, side_cap)
    found: list[Alignment] = []
    for a in range(side_cap + 1):
        table_a = left.level(a)
        for b in range(min(side_cap, r_max - a) + 1):
            table_b = right.level(b)
            for word in table_a.keys() & table_b.keys():
                for subset_a in table_a[word]:
                    remainder_a = left.remainder(subset_a)
                    for subset_b in table_b[word]:
                        found.append(
                            Alignment(
                                deleted_from_k=subset_a,
                                deleted_from_k2=subset_b,
                                node_map=node_map_from_remainders(
                                    remainder_a, right.remainder(subset_b)
                                ),
                            )
                        )
    found.sort(key=lambda item: (item.deleted_from_k, item.deleted_from_k2))
    return found


__all__ = [
    "Alignment",
    "FactSubset",
    "LanguageError",
    "ReachError",
    "Remainder",
    "RemainderIndex",
    "alignments",
    "compact_constants",
    "compatible",
    "node_map_from_remainders",
    "fact_key_of",
    "reach",
    "remove_facts",
]
