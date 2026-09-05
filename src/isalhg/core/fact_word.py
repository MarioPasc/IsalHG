"""The fact alphabet: a knowledge base as a word over ``Sigma_F``.

A knowledge base ``K`` is a labelled hypergraph --- constants are vertices
carrying a *type* label, facts are hyperedges carrying a *predicate* label and
are sets of constants.  This module writes ``K`` as a word and reads any word
back as a knowledge base.

Word layout (`DESIGN.md` G1)
----------------------------
Given an injective address map ``rank : constants -> {0, ..., n-1}``::

    T[tau(pi^-1(0))] ... T[tau(pi^-1(n-1))]   F[l_1; r_1 < ... < r_a] ...

The **type prefix** carries one ``T`` token per constant, emitted in increasing
rank; position in the prefix *is* the rank, so the type of a constant is never
written next to its address.  The **fact block** carries one ``F`` token per
fact, its operands the ranks of the fact's constants in increasing order, the
tokens themselves sorted by ``(predicate, operand tuple)``.  One token is one
atomic symbol: two tokens are equal iff their whole tuple is equal, and
``|w| = n + m``.

Nothing here computes ``rank``.  The module is stdlib-only and receives the
address vector from its caller
(:func:`isalhg.iso_backends.canonical_order.canonical_ranks` supplies the
isomorphism-invariant one that makes the encoding a complete invariant).

Roles
-----
A predicate with named argument positions (WD50K's subject / object /
qualifier value) carries ``(role, rank)`` pairs instead of bare ranks, sorted
by rank.  Roles are an ablation axis; the primary arm of every table is
role-free, because the competing representations see the same labelled
hypergraph and the comparison must be information-matched.

The decoder is total (`DESIGN.md` G2)
-------------------------------------
:func:`decode_fact_word` is defined on **every** finite sequence over the token
vocabulary.  It reads a word in two passes: the ``T`` tokens, in word order,
are the type prefix; the ``F`` tokens are read as a set.  The constant count is
``max(number of T tokens, 1 + largest rank mentioned by any F token)``, so an
``F`` token reaching past the prefix appends untyped constants (type ``0``) up
to that rank.  Facts form a set --- a repeated fact is a no-op --- and operands
with duplicate ranks collapse to the set they denote.  Disconnected knowledge
bases are legal.  The decoder never raises on a well-formed token sequence;
:class:`isalhg.errors.FactWordError` signals only a token that is not in the
vocabulary at all.

Two consequences the experiments use.  First, every prefix, every single-token
edit, every interior word of a Levenshtein alignment and every sample of a
sequence model decodes to a knowledge base.  Second, the decoded class depends
only on the multiset of fact tokens and on the type prefix, never on token
positions: permuting the ``F`` tokens, or moving a ``T`` token past them,
leaves the decoded knowledge base unchanged.  That lemma is what makes the
fact-level ball equal the decoded string ball, and it is pinned by test.

Reading ``T`` tokens positionally instead --- appending a constant where the
token sits --- would break it (``T F[p; 0 1] T`` would decode to three
constants and ``T T F[p; 0 1]`` to two).  The two readings agree on every word
whose ``T`` tokens precede its ``F`` tokens, hence on every encoded word.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from itertools import combinations
from typing import Any, TypeAlias

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.errors import FactWordError
from isalhg.types import EdgeId, NodeId

Rank: TypeAlias = int
RoleId: TypeAlias = int
# ("T", type_id) | ("F", pred_id, operands); operands is a tuple of ranks
# (ascending) or a tuple of (role, rank) pairs ordered by rank.
Token: TypeAlias = tuple[Any, ...]
Word: TypeAlias = tuple[Token, ...]
RolesMap: TypeAlias = Mapping[EdgeId, Mapping[NodeId, RoleId]]

TYPE_TAG = "T"
FACT_TAG = "F"
UNTYPED = 0


# ---------------------------------------------------------------------------
# Encoding
# ---------------------------------------------------------------------------


def encode_fact_word(
    H: SparseHypergraph,
    rank: Sequence[int],
    roles: RolesMap | None = None,
) -> Word:
    """Write ``H`` as a word over the fact alphabet under the address map ``rank``.

    Parameters
    ----------
    H : SparseHypergraph
        The knowledge base: vertices are constants (vertex label = type),
        hyperedges are facts (edge label = predicate).
    rank : Sequence[int]
        ``rank[v]`` is the address of constant ``v``; must be a permutation of
        ``range(H.n_nodes)``.  Pass
        :func:`isalhg.iso_backends.canonical_order.canonical_ranks` for the
        isomorphism-invariant addressing the article adopts.
    roles : RolesMap or None, optional
        ``{edge_id: {node_id: role_id}}``.  When given, every incidence of
        every fact must have a role and the operands become ``(role, rank)``
        pairs.  ``None`` (default) emits bare ranks.

    Returns
    -------
    Word
        ``n`` type tokens followed by ``m`` fact tokens; length ``n + m``.

    Raises
    ------
    isalhg.errors.FactWordError
        If ``rank`` is not a permutation of ``range(H.n_nodes)``, or if
        ``roles`` omits a fact or one of its incidences.
    """
    n = H.n_nodes
    rank_list = list(rank)
    if len(rank_list) != n or sorted(rank_list) != list(range(n)):
        raise FactWordError(
            f"rank must be a permutation of range({n}); got a sequence of length {len(rank_list)}"
        )

    inverse: list[NodeId] = [0] * n
    for v, r in enumerate(rank_list):
        inverse[r] = v

    prefix: list[Token] = [(TYPE_TAG, H.vertex_label(inverse[r])) for r in range(n)]

    facts: list[Token] = []
    for e, members, label in H.iter_edges():
        if roles is None:
            operands: tuple[Any, ...] = tuple(sorted(rank_list[v] for v in members))
        else:
            operands = _role_operands(e, members, label, rank_list, roles)
        facts.append((FACT_TAG, label, operands))
    facts.sort(key=lambda token: (token[1], token[2]))

    return (*prefix, *facts)


def _role_operands(
    e: EdgeId,
    members: frozenset[NodeId],
    label: int,
    rank_list: Sequence[int],
    roles: RolesMap,
) -> tuple[tuple[RoleId, Rank], ...]:
    """Return the ``(role, rank)`` operand tuple of fact ``e``, ordered by rank."""
    try:
        fact_roles = roles[e]
    except KeyError as exc:
        raise FactWordError(
            f"roles map has no entry for fact {e} (predicate {label}); a roles "
            f"map must cover every fact of the knowledge base"
        ) from exc
    pairs: list[tuple[RoleId, Rank]] = []
    for v in members:
        try:
            pairs.append((fact_roles[v], rank_list[v]))
        except KeyError as exc:
            raise FactWordError(
                f"roles map for fact {e} has no role for constant {v}; a roles "
                f"map must cover every incidence of every fact"
            ) from exc
    pairs.sort(key=lambda pair: pair[1])
    return tuple(pairs)


# ---------------------------------------------------------------------------
# Decoding -- total on well-formed token sequences
# ---------------------------------------------------------------------------


def decode_fact_word(
    tokens: Sequence[Token],
    *,
    n_types: int,
    n_preds: int,
) -> tuple[SparseHypergraph, RolesMap | None]:
    """Read any well-formed token sequence back as a knowledge base.

    The decoder is total: every sequence over the token vocabulary of
    :func:`token_vocabulary` --- including the empty one, sequences whose
    ``T`` tokens follow their ``F`` tokens, sequences addressing ranks beyond
    the type prefix, sequences repeating a fact, and sequences whose facts
    leave the result disconnected --- yields a knowledge base.  The module
    docstring states the semantics; the short version is that the ``T`` tokens
    in word order are the type prefix, the ``F`` tokens are a set of facts, and
    the constant count is whichever of the two demands more.

    Parameters
    ----------
    tokens : Sequence[Token]
        The word to decode.  Token positions do not affect the result.
    n_types : int
        Size of the constant-type vocabulary; becomes ``n_vertex_labels`` of
        the returned hypergraph.  Must be at least 1.
    n_preds : int
        Size of the predicate vocabulary; becomes ``n_edge_labels``.  Must be
        at least 1.

    Returns
    -------
    H : SparseHypergraph
        The decoded knowledge base.  Constant ``r`` is the constant addressed
        by rank ``r``, so ``decode_fact_word(encode_fact_word(H, rank))``
        equals ``permute(H, rank)``.
    roles : RolesMap or None
        ``{edge_id: {node_id: role_id}}`` when at least one fact token carried
        roles, else ``None``.  Facts written with bare ranks contribute no
        entry.  When a fact token repeats, the first occurrence supplies the
        roles.

    Raises
    ------
    isalhg.errors.FactWordError
        Only on a token outside the vocabulary: a tuple of the wrong shape, an
        operand list mixing bare ranks with ``(role, rank)`` pairs, a negative
        rank or role, or a type / predicate id outside ``[0, n_types)`` /
        ``[0, n_preds)``.  Well-formed input never raises.
    """
    if n_types < 1 or n_preds < 1:
        raise FactWordError(f"n_types and n_preds must be at least 1; got {n_types} and {n_preds}")

    types: list[int] = []
    parsed: list[tuple[int, tuple[Rank, ...], dict[Rank, RoleId] | None]] = []
    max_rank = -1
    saw_roles = False

    for token in tokens:
        tag = _token_tag(token)
        if tag == TYPE_TAG:
            types.append(_checked_id(token[1], n_types, "type", token))
        else:
            pred = _checked_id(token[1], n_preds, "predicate", token)
            ranks, role_of = _parse_operands(token)
            if role_of is not None:
                saw_roles = True
            if ranks:
                max_rank = max(max_rank, ranks[-1])
            parsed.append((pred, ranks, role_of))

    n = max(len(types), max_rank + 1)
    vertex_labels = [types[r] if r < len(types) else UNTYPED for r in range(n)]

    H = SparseHypergraph(
        n_nodes=n,
        hyperedges=[],
        n_vertex_labels=n_types,
        n_edge_labels=n_preds,
        vertex_labels=vertex_labels,
        edge_labels=[],
    )

    roles_map: dict[EdgeId, dict[NodeId, RoleId]] = {}
    created: set[EdgeId] = set()
    for pred, ranks, role_of in parsed:
        if not ranks:
            continue
        e = H.add_hyperedge(ranks, label=pred)
        if e not in created:
            created.add(e)
            if role_of is not None:
                roles_map[e] = dict(role_of)

    return H, (roles_map if saw_roles else None)


def _token_tag(token: Token) -> str:
    """Return ``"T"`` or ``"F"`` after checking the token's shape."""
    if not isinstance(token, tuple):
        raise FactWordError(f"token must be a tuple; got {type(token).__name__}: {token!r}")
    if len(token) == 2 and token[0] == TYPE_TAG:
        return TYPE_TAG
    if len(token) == 3 and token[0] == FACT_TAG:
        return FACT_TAG
    raise FactWordError(
        f"token {token!r} is not well formed; expected ('T', type_id) or ('F', pred_id, operands)"
    )


def _checked_id(value: Any, bound: int, what: str, token: Token) -> int:
    """Return ``value`` as an id in ``[0, bound)``, or raise."""
    if not isinstance(value, int) or isinstance(value, bool):
        raise FactWordError(f"{what} id of {token!r} must be an int; got {value!r}")
    if not 0 <= value < bound:
        raise FactWordError(f"{what} id {value} of {token!r} is outside [0, {bound})")
    return value


def _parse_operands(token: Token) -> tuple[tuple[Rank, ...], dict[Rank, RoleId] | None]:
    """Split a fact token's operands into ascending distinct ranks and roles.

    Duplicate ranks collapse to the set they denote; when the operands carry
    roles, the first pair mentioning a rank supplies that rank's role.
    """
    operands = token[2]
    if not isinstance(operands, tuple | list):
        raise FactWordError(f"operands of {token!r} must be a tuple; got {operands!r}")
    if not operands:
        return (), None

    shapes = {isinstance(item, tuple | list) for item in operands}
    if len(shapes) > 1:
        raise FactWordError(
            f"operands of {token!r} mix bare ranks with (role, rank) pairs; a "
            f"fact token uses one shape throughout"
        )

    if not shapes.pop():
        ranks = {_checked_rank(item, token) for item in operands}
        return tuple(sorted(ranks)), None

    role_of: dict[Rank, RoleId] = {}
    for item in operands:
        if len(item) != 2:
            raise FactWordError(f"role operand {item!r} of {token!r} must be a (role, rank) pair")
        role, raw_rank = item
        rank = _checked_rank(raw_rank, token)
        if not isinstance(role, int) or isinstance(role, bool) or role < 0:
            raise FactWordError(f"role {role!r} of {token!r} must be a non-negative int")
        role_of.setdefault(rank, role)
    return tuple(sorted(role_of)), role_of


def _checked_rank(value: Any, token: Token) -> Rank:
    """Return ``value`` as a non-negative rank, or raise."""
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise FactWordError(f"rank {value!r} of {token!r} must be a non-negative int")
    return value


# ---------------------------------------------------------------------------
# Derived quantities
# ---------------------------------------------------------------------------


def fact_key(word: Word) -> Word:
    """Return the hashable canonical key of ``word`` --- the identity function.

    A word is already a tuple of hashable tokens and already in canonical form
    (type prefix in rank order, fact tokens sorted), so nothing needs
    normalising.  The function exists so that callers which index knowledge
    bases by their word --- the reach computation, the consensus search, the
    ``n``-gram model --- name the key explicitly rather than relying on that
    coincidence, and so that a future normalisation has one place to live.

    Parameters
    ----------
    word : Word
        A word over the fact alphabet.

    Returns
    -------
    Word
        ``word`` itself.
    """
    return word


def word_length(H: SparseHypergraph) -> int:
    """Return ``|w| = n + m``, the length of any fact word of ``H``.

    The length does not depend on the address map: one type token per constant
    and one fact token per fact, whatever the ranks.

    Parameters
    ----------
    H : SparseHypergraph
        The knowledge base.

    Returns
    -------
    int
        ``H.n_nodes + H.n_edges``.
    """
    return H.n_nodes + H.n_edges


def token_vocabulary(n: int, k: int, n_preds: int, n_types: int) -> Iterator[Token]:
    """Enumerate the token vocabulary ``Sigma_F(n, k, n_preds, n_types)``.

    Yields every type token, then every fact token over addresses ``< n`` with
    arity between 2 and ``k``, in a deterministic order: type tokens by type
    id, then fact tokens by predicate, then by arity, then lexicographically by
    operand tuple.  Role-carrying fact tokens are **not** enumerated --- the
    role vocabulary is per-collection and the role arm is an ablation.

    Parameters
    ----------
    n : int
        Number of addresses; fact operands range over ``0 .. n-1``.
    k : int
        Maximum arity.  ``k < 2`` yields no fact tokens.
    n_preds : int
        Predicate vocabulary size.
    n_types : int
        Constant-type vocabulary size.

    Yields
    ------
    Token
        Each token of the vocabulary exactly once.

    Raises
    ------
    isalhg.errors.FactWordError
        If any argument is negative.
    """
    if min(n, k, n_preds, n_types) < 0:
        raise FactWordError(
            f"token_vocabulary arguments must be non-negative; got "
            f"n={n}, k={k}, n_preds={n_preds}, n_types={n_types}"
        )
    for type_id in range(n_types):
        yield (TYPE_TAG, type_id)
    for pred_id in range(n_preds):
        for arity in range(2, k + 1):
            for operands in combinations(range(n), arity):
                yield (FACT_TAG, pred_id, operands)


__all__ = [
    "FACT_TAG",
    "TYPE_TAG",
    "UNTYPED",
    "Rank",
    "RoleId",
    "RolesMap",
    "Token",
    "Word",
    "decode_fact_word",
    "encode_fact_word",
    "fact_key",
    "token_vocabulary",
    "word_length",
]
