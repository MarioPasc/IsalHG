"""Three encodings of a labelled knowledge base as a word, plus their distances.

Probe module for the D-ART3 alphabet decision (`docs/article/D_ART3/
logic_models/encoding.md` §3.1, absolute vs relative addressing). Nothing here
is imported by the installable package; it lives beside the other 2026-09-03
diagnostics.

A knowledge base ``K`` is a labelled hypergraph: constants are vertices carrying
a type label, facts are hyperedges carrying a predicate label and are *sets* of
constants.

E-A  status quo. ``w*_c`` over ``Sigma_HG`` (relative / pointer addressing),
     distance = token-level Levenshtein over ``parse(w*_c)`` with the
     seed-label prefix when the vertex vocabulary is non-trivial. Mirrors
     :mod:`isalhg.metric_space.distances.isalhg_levenshtein`.

E-B  F4 with GLOBAL canonical ranks. Constants are addressed by their position
     in nauty's canonical order of the Levi graph.

E-C  F4 with LOCAL addresses. Constants are addressed by
     ``(WL colour at depth 3, index among same-coloured constants under the
     E-B order)``.

Both F4 words are sequences of atomic symbols; the distance is the unweighted
Levenshtein distance over those symbols (one token = one symbol).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypeAlias

from isalhg.core.canonical import canonical_string, required_k, seed_vertex_label
from isalhg.core.hypergraph_wl import wl_hash
from isalhg.core.instructions import parse
from isalhg.core.levi_reduction import LeviGraph, to_levi
from isalhg.core.sparse_hypergraph import SparseHypergraph

Symbol: TypeAlias = Any
Word: TypeAlias = tuple[Symbol, ...]

WL_DEPTH = 3


# ---------------------------------------------------------------------------
# Knowledge-base value type (the corpora speak this; SparseHypergraph is built
# from it on demand so that edits never depend on id renumbering).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class KB:
    """A labelled knowledge base.

    Parameters
    ----------
    n : int
        Number of constants; ids are ``0 .. n-1``.
    types : tuple[int, ...]
        Per-constant type id, in ``range(n_types)``.
    facts : tuple[tuple[int, frozenset[int]], ...]
        Each fact is ``(predicate id, member set)``; member sets are distinct
        per predicate (no multi-facts).
    n_types : int
        Constant-type vocabulary size.
    n_preds : int
        Predicate vocabulary size.
    """

    n: int
    types: tuple[int, ...]
    facts: tuple[tuple[int, frozenset[int]], ...]
    n_types: int
    n_preds: int

    @property
    def m(self) -> int:
        return len(self.facts)

    @property
    def max_arity(self) -> int:
        return max((len(mem) for _, mem in self.facts), default=0)

    def to_hypergraph(self) -> SparseHypergraph:
        return SparseHypergraph(
            n_nodes=self.n,
            hyperedges=[mem for _, mem in self.facts],
            n_vertex_labels=self.n_types,
            n_edge_labels=self.n_preds,
            vertex_labels=list(self.types),
            edge_labels=[lab for lab, _ in self.facts],
        )

    def fact_set(self) -> frozenset[tuple[int, frozenset[int]]]:
        return frozenset(self.facts)


def kb_from_hypergraph(H: SparseHypergraph) -> KB:
    return KB(
        n=H.n_nodes,
        types=tuple(H.vertex_label(v) for v in range(H.n_nodes)),
        facts=tuple((lab, mem) for _, mem, lab in H.iter_edges()),
        n_types=H.n_vertex_labels,
        n_preds=H.n_edge_labels,
    )


# ---------------------------------------------------------------------------
# Shared machinery: nauty canonical order on the constants
# ---------------------------------------------------------------------------


def _import_pynauty() -> Any:
    import pynauty

    return pynauty


def _to_pynauty(levi: LeviGraph) -> Any:
    """Mirror of ``isalhg.iso_backends.pynauty_levi._to_pynauty``."""
    pynauty = _import_pynauty()
    adjacency: dict[int, list[int]] = {node: [] for node in range(levi.n_nodes)}
    for u, v in levi.edges:
        adjacency[u].append(v)
        adjacency[v].append(u)
    return pynauty.Graph(
        number_of_vertices=levi.n_nodes,
        directed=False,
        adjacency_dict=adjacency,
        vertex_coloring=levi.color_classes(),
    )


def canonical_ranks(H: SparseHypergraph) -> tuple[int, ...]:
    """Return the isomorphism-invariant total order ``pi`` on the constants.

    ``pynauty.canon_label(g)`` returns ``pi`` with ``pi[i]`` the *original*
    Levi node sitting at canonical position ``i``. Filtering that sequence to
    the constant-side nodes (ids ``< n_vertex_nodes``) and keeping the order
    yields a total order on the constants; a canonical labelling commutes with
    every isomorphism, so the induced ranks are isomorphism-invariant. There
    are no residual ties: ``canon_label`` is a permutation.

    Parameters
    ----------
    H : SparseHypergraph
        The knowledge base.

    Returns
    -------
    tuple[int, ...]
        ``rank[v]`` is the canonical rank of constant ``v`` in ``0 .. n-1``.
    """
    pynauty = _import_pynauty()
    levi = to_levi(H)
    pi = pynauty.canon_label(_to_pynauty(levi))
    rank: list[int] = [-1] * levi.n_vertex_nodes
    r = 0
    for node in pi:
        if node < levi.n_vertex_nodes:
            rank[node] = r
            r += 1
    return tuple(rank)


def nauty_fingerprint(H: SparseHypergraph) -> bytes:
    """``color_signature ++ pynauty certificate`` (the M4 reference form)."""
    if H.n_nodes == 0:
        return b""
    pynauty = _import_pynauty()
    levi = to_levi(H)
    return levi.color_signature() + bytes(pynauty.certificate(_to_pynauty(levi)))


# ---------------------------------------------------------------------------
# E-A -- status quo, relative (pointer) addressing
# ---------------------------------------------------------------------------


def word_A(H: SparseHypergraph, *, k: int | None = None, augment: bool | None = None) -> Word:
    """Token sequence of ``w*_c`` with the seed-label prefix.

    Parameters
    ----------
    H : SparseHypergraph
        Connected knowledge base.
    k : int or None, optional
        Pointer count. ``None`` uses ``required_k(H)``; a *pair* comparison
        must pass the pair maximum (Critical Invariant #7).
    augment : bool or None, optional
        Emit the ``("seed", label)`` prefix. ``None`` decides from
        ``H.n_vertex_labels > 1``.
    """
    kk = required_k(H) if k is None else k
    w = canonical_string(H, k=kk, algorithm="canonical", backend="cpp")
    tokens: Word = tuple(parse(w))
    aug = (H.n_vertex_labels > 1) if augment is None else augment
    if aug:
        return (("seed", seed_vertex_label(H, w)), *tokens)
    return tokens


# ---------------------------------------------------------------------------
# E-B -- F4 with global canonical ranks
# ---------------------------------------------------------------------------


def word_B(H: SparseHypergraph, rank: tuple[int, ...] | None = None) -> Word:
    """F4 word with absolute addresses = canonical ranks.

    Layout: a type prefix ``T[type(pi^-1(r))]`` for ``r = 0 .. n-1`` (position
    in the prefix *is* the rank), then one ``F[l; r_1 < ... < r_a]`` per fact,
    the fact tokens sorted lexicographically by ``(l, rank tuple)``.
    """
    if rank is None:
        rank = canonical_ranks(H)
    n = H.n_nodes
    inv: list[int] = [0] * n
    for v, r in enumerate(rank):
        inv[r] = v
    prefix: list[Symbol] = [("T", H.vertex_label(inv[r])) for r in range(n)]
    facts: list[Symbol] = []
    for _, members, lab in H.iter_edges():
        facts.append(("F", lab, tuple(sorted(rank[v] for v in members))))
    facts.sort(key=lambda t: (t[1], t[2]))
    return (*prefix, *facts)


# ---------------------------------------------------------------------------
# E-C -- F4 with local (WL-colour) addresses
# ---------------------------------------------------------------------------


def local_addresses(
    H: SparseHypergraph, rank: tuple[int, ...] | None = None
) -> tuple[tuple[int, int], ...]:
    """Return ``addr[v] = (WL colour at depth 3, index within that colour)``.

    The index orders same-coloured constants by their E-B canonical rank, so
    the address map is isomorphism-invariant and injective.
    """
    if rank is None:
        rank = canonical_ranks(H)
    colours = wl_hash(H, max_rounds=WL_DEPTH, backend="cpp")
    by_colour: dict[int, list[int]] = {}
    for v in range(H.n_nodes):
        by_colour.setdefault(colours[v], []).append(v)
    addr: list[tuple[int, int]] = [(0, 0)] * H.n_nodes
    for colour, members in by_colour.items():
        for idx, v in enumerate(sorted(members, key=lambda u: rank[u])):
            addr[v] = (colour, idx)
    return tuple(addr)


def word_C(H: SparseHypergraph, rank: tuple[int, ...] | None = None) -> Word:
    """F4 word with local addresses.

    Layout: a type prefix keyed by address, ``T[(col, idx); type]``, emitted in
    increasing address order, then one ``F[l; (col, idx)_1 ... (col, idx)_a]``
    per fact with the operands sorted by address, the fact tokens sorted
    lexicographically.
    """
    addr = local_addresses(H, rank)
    order = sorted(range(H.n_nodes), key=lambda v: addr[v])
    prefix: list[Symbol] = [("T", addr[v], H.vertex_label(v)) for v in order]
    facts: list[Symbol] = []
    for _, members, lab in H.iter_edges():
        facts.append(("F", lab, tuple(sorted(addr[v] for v in members))))
    facts.sort(key=lambda t: (t[1], t[2]))
    return (*prefix, *facts)


# ---------------------------------------------------------------------------
# Distances
# ---------------------------------------------------------------------------


def _levenshtein() -> Any:
    from rapidfuzz.distance import Levenshtein

    return Levenshtein


def token_levenshtein(w1: Word, w2: Word) -> int:
    """Unweighted Levenshtein over atomic symbols."""
    return int(_levenshtein().distance(w1, w2))


def byte_levenshtein(b1: bytes, b2: bytes) -> int:
    return int(_levenshtein().distance(b1, b2))


def words_all(H: SparseHypergraph, *, k: int | None = None) -> dict[str, Word]:
    """Compute all three words for one knowledge base (E-A is the slow arm)."""
    rank = canonical_ranks(H)
    return {"A": word_A(H, k=k), "B": word_B(H, rank), "C": word_C(H, rank)}


def words_BC(H: SparseHypergraph) -> dict[str, Word]:
    rank = canonical_ranks(H)
    return {"B": word_B(H, rank), "C": word_C(H, rank)}
