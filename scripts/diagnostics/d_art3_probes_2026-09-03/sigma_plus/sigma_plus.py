"""Prototype of the conservative language extension ``Sigma^+ = Sigma_HG u {A, A+}``.

Standalone wrapper around the installed ``isalhg`` package: it imports the
package's CDLL, KPointerSet, SparseHypergraph, token classes, parser and
``canonical_string``, and re-implements only the interpreter loop so the two
new rank-addressed token families can be executed.  Nothing under ``src/`` is
touched.

Design (binding, from ``docs/article/D_ART3/prose.md`` §11.1 + coordinator brief)
--------------------------------------------------------------------------------
Ranks.  The VM numbers vertices in creation order; the seed is rank 0 and the
``j`` fresh vertices of a ``V`` token take consecutive ranks in the order the
package's S2H creates them.  Because ``SparseHypergraph.add_node`` appends,
rank == NodeId exactly.

``A[l; r_1 ... r_a]`` (1 <= a <= k).  Hyperedge labelled ``l`` over the ranked
vertices.  Total: a rank >= the current vertex count is clamped to
``count - 1`` (a negative rank is clamped to 0); repeated ranks collapse; an
already-present ``(l, support)`` is a no-op.  No CDLL and no pointer change.

``A+[l; lam; r_1 ... r_i]`` (1 <= i <= k-1).  One fresh vertex labelled ``lam``,
inserted into the CDLL exactly where ``V`` inserts a single fresh vertex (after
``p_1``), taking the next rank; plus the hyperedge labelled ``l`` over the
ranked vertices (clamped, collapsed) and the fresh vertex.  Pointers unchanged.
Assumption A1 (stated in the report): the clamp for ``A+`` uses the vertex count
*before* the fresh vertex is created, mirroring ``V``, whose ``i`` pointed
vertices are all pre-existing.

Surface syntax.  ``A[l;r1,r2,r3]`` and ``A+[l;lam;r1,r2]``; tokens are joined by
``;`` at top level exactly as in the package grammar (the extra ``+`` is inert
for the package's bracket-aware splitter).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import ClassVar

from isalhg.core.cdll import CircularDoublyLinkedList
from isalhg.core.instructions import (
    Token,
    TokenC,
    TokenN,
    TokenP,
    TokenV,
    TokenW,
    _split_top_level,
)
from isalhg.core.instructions import (
    parse as _pkg_parse,
)
from isalhg.core.pointers import KPointerSet
from isalhg.core.sparse_hypergraph import SparseHypergraph

_RANK_A = 5
_RANK_AP = 6


class SigmaPlusError(Exception):
    """Root exception of the prototype."""


class InvalidPlusTokenError(SigmaPlusError):
    """Raised when a surface form is not a well-formed ``Sigma^+`` token."""


# ---------------------------------------------------------------------------
# The two new tokens
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TokenA(Token):
    """``A[l; r_1 ... r_a]`` -- hyperedge over ranked vertices."""

    KIND: ClassVar[str] = "A"
    edge_label: int
    ranks: tuple[int, ...] = field(default_factory=tuple)

    def serialize(self) -> str:
        return f"A[{self.edge_label};{','.join(str(r) for r in self.ranks)}]"

    def sort_key(self) -> tuple[int, ...]:
        return (_RANK_A, self.edge_label, len(self.ranks), *self.ranks)


@dataclass(frozen=True)
class TokenAPlus(Token):
    """``A+[l; lam; r_1 ... r_i]`` -- fresh vertex plus hyperedge over ranks + it."""

    KIND: ClassVar[str] = "A+"
    edge_label: int
    new_label: int
    ranks: tuple[int, ...] = field(default_factory=tuple)

    def serialize(self) -> str:
        return f"A+[{self.edge_label};{self.new_label};{','.join(str(r) for r in self.ranks)}]"

    def sort_key(self) -> tuple[int, ...]:
        return (_RANK_AP, self.edge_label, self.new_label, len(self.ranks), *self.ranks)


# ---------------------------------------------------------------------------
# Parser / serializer for Sigma^+
# ---------------------------------------------------------------------------


def _parse_ranks(s: str) -> tuple[int, ...]:
    if s == "":
        raise InvalidPlusTokenError("empty rank list")
    return tuple(int(x) for x in s.split(","))


def _parse_one_plus(piece: str) -> Token:
    if piece.startswith("A+["):
        if not piece.endswith("]"):
            raise InvalidPlusTokenError(f"malformed A+ token: {piece!r}")
        fields = piece[3:-1].split(";")
        if len(fields) != 3:
            raise InvalidPlusTokenError(f"A+ expects 3 fields, got {len(fields)} in {piece!r}")
        return TokenAPlus(
            edge_label=int(fields[0]),
            new_label=int(fields[1]),
            ranks=_parse_ranks(fields[2]),
        )
    if piece.startswith("A["):
        if not piece.endswith("]"):
            raise InvalidPlusTokenError(f"malformed A token: {piece!r}")
        fields = piece[2:-1].split(";")
        if len(fields) != 2:
            raise InvalidPlusTokenError(f"A expects 2 fields, got {len(fields)} in {piece!r}")
        return TokenA(edge_label=int(fields[0]), ranks=_parse_ranks(fields[1]))
    return _pkg_parse(piece)[0]


def parse_plus(string: str) -> list[Token]:
    """Tokenise a ``Sigma^+*`` string. Conservative: pure ``Sigma_HG`` input is
    routed to the package parser piece by piece."""
    if string == "":
        return []
    return [_parse_one_plus(p) for p in _split_top_level(string, ";")]


def serialize_plus(tokens) -> str:
    """Render a ``Sigma^+`` token sequence as a ``;``-joined string."""
    return ";".join(t.serialize() for t in tokens)


def validate_plus(tokens, *, k: int, n_vertex_labels: int = 1, n_edge_labels: int = 1) -> None:
    """Alphabet-level check of a ``Sigma^+`` token sequence.

    Ranks are *not* checked against any vertex count -- rank semantics are total
    by clamping, which is the point of the extension.
    """
    from isalhg.core.instructions import validate as _pkg_validate

    plain = []
    for idx, tok in enumerate(tokens):
        if isinstance(tok, TokenA):
            if not 1 <= len(tok.ranks) <= k:
                raise InvalidPlusTokenError(f"token {idx}: A arity {len(tok.ranks)} not in [1,{k}]")
            if not 0 <= tok.edge_label < n_edge_labels:
                raise InvalidPlusTokenError(f"token {idx}: A edge_label out of range")
        elif isinstance(tok, TokenAPlus):
            if not 1 <= len(tok.ranks) <= k - 1:
                raise InvalidPlusTokenError(
                    f"token {idx}: A+ i={len(tok.ranks)} not in [1,{k - 1}]"
                )
            if not 0 <= tok.edge_label < n_edge_labels:
                raise InvalidPlusTokenError(f"token {idx}: A+ edge_label out of range")
            if not 0 <= tok.new_label < n_vertex_labels:
                raise InvalidPlusTokenError(f"token {idx}: A+ new_label out of range")
        else:
            plain.append(tok)
    _pkg_validate(plain, k=k, n_vertex_labels=n_vertex_labels, n_edge_labels=n_edge_labels)


# ---------------------------------------------------------------------------
# The S2H+ interpreter
# ---------------------------------------------------------------------------


def _capacity_for(tokens) -> int:
    cap = 1
    for tok in tokens:
        if isinstance(tok, TokenV):
            cap += tok.j
        elif isinstance(tok, TokenAPlus):
            cap += 1
    return cap


class StringToHypergraphPlus:
    """Stateful ``S2H+`` interpreter over ``Sigma^+``.

    ``V``/``C``/``P``/``N``/``W`` are executed with byte-for-byte the same
    operations as ``isalhg.core.string_to_hypergraph.StringToHypergraph._step``
    (same CDLL, same KPointerSet, same ``add_node`` / ``add_hyperedge`` calls),
    so conservativity is structural, not merely tested.
    """

    __slots__ = ("_tokens", "_k", "_H", "_cdll", "_pointers", "creators")

    def __init__(
        self,
        tokens,
        *,
        k: int,
        n_vertex_labels: int = 1,
        n_edge_labels: int = 1,
        seed_label: int = 0,
        validate: bool = False,
    ) -> None:
        self._tokens = tuple(tokens)
        self._k = k
        if validate:
            validate_plus(
                self._tokens,
                k=k,
                n_vertex_labels=n_vertex_labels,
                n_edge_labels=n_edge_labels,
            )
        self._H = SparseHypergraph(
            n_nodes=0, n_vertex_labels=n_vertex_labels, n_edge_labels=n_edge_labels
        )
        seed_id = self._H.add_node(label=seed_label)
        self._cdll = CircularDoublyLinkedList(capacity=_capacity_for(self._tokens))
        self._cdll.insert_after(0, seed_id)
        self._pointers = KPointerSet(self._cdll, k=k)
        self.creators: list = []

    def run(self, *, track_creators: bool = False) -> SparseHypergraph:
        """Execute every token; return the final hypergraph.

        With ``track_creators=True`` the attribute :attr:`creators` holds, for
        each token index, the ``(label, frozenset(members))`` of the hyperedge
        that token created *for the first time*, or ``None``.
        """
        H = self._H
        for tok in self._tokens:
            before = H.n_edges if track_creators else 0
            made = self._step(tok)
            if track_creators:
                self.creators.append(made if H.n_edges > before else None)
        return H

    # -- semantics -----------------------------------------------------
    def _clamp(self, ranks) -> frozenset:
        top = self._H.n_nodes - 1
        return frozenset(0 if r < 0 else (top if r > top else r) for r in ranks)

    def _step(self, tok):
        if isinstance(tok, TokenW):
            return None
        if isinstance(tok, TokenP):
            self._pointers.advance(tok.i)
            return None
        if isinstance(tok, TokenN):
            self._pointers.retreat(tok.i)
            return None
        if isinstance(tok, TokenC):
            members = [self._cdll.get_value(self._pointers.get(x + 1)) for x in range(tok.i)]
            self._H.add_hyperedge(members, label=tok.edge_label)
            return (tok.edge_label, frozenset(members))
        if isinstance(tok, TokenV):
            existing = [self._cdll.get_value(self._pointers.get(x + 1)) for x in range(tok.i)]
            fresh = []
            slot = self._pointers.get(1)
            for lab in tok.new_node_labels:
                v = self._H.add_node(label=lab)
                slot = self._cdll.insert_after(slot, v)
                fresh.append(v)
            self._H.add_hyperedge(existing + fresh, label=tok.edge_label)
            return (tok.edge_label, frozenset(existing + fresh))
        if isinstance(tok, TokenA):
            support = self._clamp(tok.ranks)
            self._H.add_hyperedge(support, label=tok.edge_label)
            return (tok.edge_label, support)
        if isinstance(tok, TokenAPlus):
            support = self._clamp(tok.ranks)  # assumption A1: clamp before the fresh vertex
            v = self._H.add_node(label=tok.new_label)
            self._cdll.insert_after(self._pointers.get(1), v)
            members = support | {v}
            self._H.add_hyperedge(members, label=tok.edge_label)
            return (tok.edge_label, members)
        raise InvalidPlusTokenError(f"unknown token type {type(tok)!r}")


def decode_plus(
    tokens,
    *,
    k: int,
    n_vertex_labels: int = 1,
    n_edge_labels: int = 1,
    seed_label: int = 0,
) -> SparseHypergraph:
    """Run ``S2H+`` on an already-parsed token sequence."""
    return StringToHypergraphPlus(
        tokens,
        k=k,
        n_vertex_labels=n_vertex_labels,
        n_edge_labels=n_edge_labels,
        seed_label=seed_label,
    ).run()


def string_to_hypergraph_plus(string: str, **kw) -> SparseHypergraph:
    """Parse then run: the ``Sigma^+`` analogue of the package entry point."""
    return decode_plus(parse_plus(string), **kw)


# ---------------------------------------------------------------------------
# Helpers shared by the task drivers
# ---------------------------------------------------------------------------


def structural_key(H: SparseHypergraph) -> tuple:
    """Exact (labelled, id-sensitive) key -- equality means identical objects."""
    return (
        H.n_nodes,
        tuple(sorted(H.vertex_label(v) for v in range(H.n_nodes))),
        tuple(sorted((tuple(sorted(m)), ell) for _, m, ell in H.iter_edges())),
    )


def invariant(H: SparseHypergraph) -> tuple:
    """Cheap iso-invariant prefilter (same one the 2026-09-03 reach probe used,
    plus the edge-label multiset because this prototype uses r+1 edge labels)."""
    return (
        H.n_nodes,
        H.n_edges,
        tuple(sorted(H.degree(v) for v in range(H.n_nodes))),
        tuple(sorted((len(m), ell) for _, m, ell in H.iter_edges())),
    )


def edge_set(H: SparseHypergraph) -> frozenset:
    """``{(label, frozenset(members))}`` -- the object identity modulo vertex ids."""
    return frozenset((ell, m) for _, m, ell in H.iter_edges())


def from_edge_set(n: int, edges, *, n_vertex_labels: int = 1, n_edge_labels: int = 1):
    """Rebuild a hypergraph on ``n`` vertices from ``{(label, members)}``."""
    H = SparseHypergraph(n_nodes=n, n_vertex_labels=n_vertex_labels, n_edge_labels=n_edge_labels)
    for ell, members in edges:
        H.add_hyperedge(members, label=ell)
    return H


def sigma_hg_alphabet(k: int, n_edge_labels: int = 1, n_vertex_labels: int = 1) -> list[Token]:
    """The package alphabet ``Sigma_HG(k)`` over the given vocabularies."""
    out: list[Token] = [TokenW()]
    out += [TokenP(i) for i in range(1, k + 1)]
    out += [TokenN(i) for i in range(1, k + 1)]
    out += [TokenC(le, i) for le in range(n_edge_labels) for i in range(1, k + 1)]
    out += [
        TokenV(le, i, j, tuple([lv] * j))
        for le in range(n_edge_labels)
        for i in range(1, k)
        for j in range(1, k)
        if 2 <= i + j <= k
        for lv in range(n_vertex_labels)
    ]
    return out


def _subsets_upto(n: int, a_max: int):
    from itertools import combinations

    for a in range(1, a_max + 1):
        yield from combinations(range(n), a)


def a_tokens(n: int, k: int, n_edge_labels: int) -> list[TokenA]:
    """Every canonical (ascending-rank) ``A`` token over ``n`` ranks, arity <= k."""
    return [
        TokenA(edge_label=le, ranks=S) for le in range(n_edge_labels) for S in _subsets_upto(n, k)
    ]


def aplus_tokens(n: int, k: int, n_edge_labels: int, n_vertex_labels: int = 1) -> list[TokenAPlus]:
    """Every canonical ``A+`` token over ``n`` ranks, ``i <= k-1``."""
    return [
        TokenAPlus(edge_label=le, new_label=lv, ranks=S)
        for le in range(n_edge_labels)
        for lv in range(n_vertex_labels)
        for S in _subsets_upto(n, k - 1)
    ]


def random_sigma_plus_word(
    rng: random.Random, length: int, k: int, n_edge_labels: int, n_vertex_labels: int, rank_max: int
) -> list[Token]:
    """Uniform word over ``Sigma_HG(k) u {A, A+}`` with arbitrary (possibly
    out-of-range, possibly repeated, possibly unsorted) ranks in ``[0, rank_max]``."""
    base = sigma_hg_alphabet(k, n_edge_labels, n_vertex_labels)
    toks: list[Token] = []
    for _ in range(length):
        u = rng.random()
        if u < 0.5:
            toks.append(rng.choice(base))
        elif u < 0.8:
            a = rng.randint(1, k)
            toks.append(
                TokenA(
                    edge_label=rng.randrange(n_edge_labels),
                    ranks=tuple(rng.randint(0, rank_max) for _ in range(a)),
                )
            )
        else:
            i = rng.randint(1, k - 1)
            toks.append(
                TokenAPlus(
                    edge_label=rng.randrange(n_edge_labels),
                    new_label=rng.randrange(n_vertex_labels),
                    ranks=tuple(rng.randint(0, rank_max) for _ in range(i)),
                )
            )
    return toks
