"""Exact fact-level reach between two knowledge bases, by delete-and-match.

``reach_F(K, K')`` is the fewest fact indels that carry one knowledge base onto
the other with its constants held fixed::

    reach_F(K, K') = min { |A| + |B| : A subset F(K), B subset F(K'),
                                       (K - A) isomorphic (K' - B) }

Substitution is excluded on purpose (`DESIGN.md` RQ3): it is the **indel** ball,
because a substitution would collapse the ``2t`` gap between two members of a
variant collection.  Constants are never deleted, so an isolated constant left
behind by a removed fact is legal and the two remainders always carry the same
constant count.

The computation is exact for a bounded radius and needs no isomorphism search
of its own.  Enumerate every ``A`` with ``|A| <= r_max`` and every ``B`` with
``|B| <= r_max``, canonicalize both remainders with the article's addressing
(:func:`isalhg.metric_space.distances.fact_levenshtein.fact_word`) and compare
*words*: because the fact word is a complete isomorphism invariant, word
equality is isomorphism.  Scanning the total budget ``s = |A| + |B|`` upwards
and returning the first ``s`` that matches gives the minimum, and the
enumeration is symmetric in its two arguments, so ``reach`` is symmetric.

Never compare rank *vectors* across two knowledge bases (`DESIGN.md` G1): a
canonical labelling is canonical only up to an automorphism of the canonical
form.  This module only ever compares words; :mod:`isalhg.language.alignment`
takes ranks from the two *isomorphic* remainders, where rank equality is a
genuine isomorphism.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from itertools import combinations

from isalhg.core.fact_word import Word, encode_fact_word
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.errors import IsalHGError
from isalhg.iso_backends.canonical_order import canonical_ranks
from isalhg.metric_space.distances.fact_levenshtein import fact_word
from isalhg.types import EdgeId

FactSubset = tuple[EdgeId, ...]


class LanguageError(IsalHGError):
    """Root of the language-layer exception hierarchy."""


class ReachError(LanguageError):
    """Raised when a reach computation is asked for something it cannot answer."""


def fact_key_of(H: SparseHypergraph) -> Word:
    """Return the canonical key of ``H`` --- its role-free fact word.

    The key every construction in this package is indexed by.  Two knowledge
    bases share a key iff they are isomorphic as labelled hypergraphs, so the
    key is what a "decoded class" means here.

    Parameters
    ----------
    H : SparseHypergraph
        The knowledge base.

    Returns
    -------
    Word
        ``fact_word(H)``: ``n`` type tokens in canonical-rank order followed by
        ``m`` fact tokens sorted by ``(predicate, rank tuple)``.

    Raises
    ------
    isalhg.errors.BackendUnavailableError
        If ``pynauty`` is not installed.
    """
    return fact_word(H)


def remove_facts(H: SparseHypergraph, drop: Iterable[EdgeId]) -> SparseHypergraph:
    """Return ``H`` with the facts in ``drop`` removed and every constant kept.

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


class RemainderIndex:
    """The canonical words of every remainder of ``H`` under ``<= r_max`` deletions.

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

    __slots__ = ("_H", "_levels", "_min_deletions", "_r_max", "_ranks")

    def __init__(self, H: SparseHypergraph, r_max: int) -> None:
        if r_max < 0:
            raise ReachError(f"r_max must be non-negative; got {r_max}")
        self._H = H
        self._r_max = r_max
        self._levels: list[dict[Word, list[FactSubset]] | None] = [None] * (r_max + 1)
        self._ranks: dict[FactSubset, tuple[int, ...]] = {}
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
            remainder = remove_facts(self._H, subset)
            ranks = canonical_ranks(remainder)
            word = encode_fact_word(remainder, ranks)
            self._ranks[subset] = ranks
            table.setdefault(word, []).append(subset)
        self._levels[size] = table
        return table

    def ranks(self, subset: FactSubset) -> tuple[int, ...]:
        """Return the canonical ranks of the remainder ``H - subset``.

        The subset must already have been produced by :meth:`level`, which is
        where the ranks are computed; they are kept because
        :mod:`isalhg.language.alignment` builds its node maps from the ranks of
        the two isomorphic remainders and must not recompute them.

        Parameters
        ----------
        subset : FactSubset
            A deletion set previously returned by :meth:`level`.

        Returns
        -------
        tuple[int, ...]
            ``rank[v]`` for every constant ``v`` of ``H``.

        Raises
        ------
        ReachError
            If the subset has not been indexed.
        """
        try:
            return self._ranks[subset]
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


def compatible(K: SparseHypergraph, K2: SparseHypergraph) -> bool:
    """Return whether a finite reach between ``K`` and ``K2`` is possible at all.

    Deleting facts never deletes a constant, so isomorphic remainders force
    equal constant counts and equal type multisets.  The test is exact as a
    *necessary* condition and costs no canonicalization.

    Parameters
    ----------
    K, K2 : SparseHypergraph
        The two knowledge bases.

    Returns
    -------
    bool
        ``False`` when no deletion pair can make the two isomorphic.
    """
    if K.n_nodes != K2.n_nodes:
        return False
    left = sorted(K.vertex_label(v) for v in range(K.n_nodes))
    right = sorted(K2.vertex_label(v) for v in range(K2.n_nodes))
    return left == right


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
        ``min |A| + |B|`` over deletion pairs whose remainders are isomorphic,
        or ``None`` when no such pair exists within ``r_max``.  ``0`` iff the
        two are isomorphic.  The value is symmetric in its two arguments.

    Raises
    ------
    ReachError
        If ``r_max`` is negative.
    isalhg.errors.BackendUnavailableError
        If ``pynauty`` is not installed.
    """
    if r_max < 0:
        raise ReachError(f"r_max must be non-negative; got {r_max}")
    if not compatible(K, K2):
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
    node_map : tuple[int, ...]
        ``node_map[v]``, for a constant ``v`` of the *second* knowledge base, is
        the constant of the *first* it corresponds to.  A genuine isomorphism
        ``(K2 - B) -> (K - A)``: applying it with
        :func:`isalhg.core.sparse_hypergraph.permute` reproduces ``K - A``
        exactly.
    """

    deleted_from_k: tuple[int, ...]
    deleted_from_k2: tuple[int, ...]
    node_map: tuple[int, ...]


def node_map_from_ranks(
    ranks_left: tuple[int, ...], ranks_right: tuple[int, ...]
) -> tuple[int, ...]:
    """Compose the two remainders' canonical labellings into an isomorphism.

    ``ranks_left`` addresses the constants of ``K - A``, ``ranks_right`` those
    of ``K2 - B``, and the two remainders have equal words.  The composition
    ``v -> rank_left^-1(rank_right(v))`` is then an isomorphism
    ``(K2 - B) -> (K - A)``: equal type prefixes make it label preserving, and
    equal fact-token sequences make it fact preserving, because the rank map is
    injective so a fact and its token determine one another.

    This is the only place ranks cross between two objects, and it is legal
    precisely because the two objects are isomorphic (`DESIGN.md` G1).  The
    ranks of ``K`` and ``K2`` themselves are never composed.
    """
    inverse = [0] * len(ranks_left)
    for v, r in enumerate(ranks_left):
        inverse[r] = v
    return tuple(inverse[r] for r in ranks_right)


def alignments(
    K: SparseHypergraph,
    K2: SparseHypergraph,
    r_max: int = 2,
    *,
    max_per_side: int | None = None,
) -> list[Alignment]:
    """Return every bounded deletion pair whose remainders are isomorphic.

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
        deterministic.  Empty when the two constant sets or type multisets
        differ.

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
    if not compatible(K, K2):
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
                    ranks_a = left.ranks(subset_a)
                    for subset_b in table_b[word]:
                        found.append(
                            Alignment(
                                deleted_from_k=subset_a,
                                deleted_from_k2=subset_b,
                                node_map=node_map_from_ranks(ranks_a, right.ranks(subset_b)),
                            )
                        )
    found.sort(key=lambda item: (item.deleted_from_k, item.deleted_from_k2))
    return found


__all__ = [
    "Alignment",
    "FactSubset",
    "LanguageError",
    "ReachError",
    "RemainderIndex",
    "alignments",
    "compatible",
    "node_map_from_ranks",
    "fact_key_of",
    "reach",
    "remove_facts",
]
