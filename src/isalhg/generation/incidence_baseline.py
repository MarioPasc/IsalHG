"""The flat incidence-list serialization, and the strict decoder that rejects.

This is RQ6's control arm. The same knowledge base is written as a flat
incidence list instead of a fact word, and the same n-gram is fitted over the
result. The two serializations carry the same information; what differs is that
the fact alphabet is *closed* -- every token sequence names a knowledge base --
while this grammar is not, so a sequence model sampling from it produces
sequences that name nothing.

Grammar
-------
::

    ("N", n)  ("T", tau)^n   [ ("FACT",) ("P", pred) ("C", id)^a ]^m   ("END",)

The header declares the constant count, the ``T`` tokens give their types in
order, each fact opens with ``("FACT",)`` and carries its predicate then its
member ids, and ``("END",)`` terminates. The layout mirrors the fact word --
sizes first, then types, then facts -- so the comparison isolates the grammar's
*closedness* rather than confounding it with a different information order.

What the decoder rejects (each one a way a sampled sequence goes wrong)
----------------------------------------------------------------------
1. **No header**, or a header that is not the first token.
2. **A repeated header** anywhere in the sequence.
3. **A negative declared count.**
4. **An out-of-range constant id** -- ``id < 0`` or ``id >= n``. This is the
   characteristic failure: nothing stops a sampler from emitting an id it saw
   in a larger knowledge base.
5. **A fact of arity below 2**, after duplicate ids inside one fact collapse.
   A unary statement carries no relational structure and the corpora exclude
   it, so a model that emits one has left the collection's language.
6. **A duplicate fact** -- the same ``(predicate, member set)`` twice.
   ``SparseHypergraph`` does not carry multi-hyperedges, so this is genuinely
   undecodable rather than merely redundant.
7. **A dangling token** -- a ``("P", ...)`` or ``("C", ...)`` outside a fact, or
   a fact left open at ``END``.
8. **A missing terminator**, or tokens after ``END``.
9. **Wrong token shape**, or a type / predicate id outside its vocabulary.
10. **More or fewer ``T`` tokens than the header declared.**

Rules 4-6 have no counterpart in the fact alphabet at all: an out-of-range rank
*extends* the constant set, a collapsed operand tuple yields whatever set it
denotes, and a repeated fact is a no-op. That is the asymmetry RQ6 measures.

The decoder returns ``None`` rather than raising, because a rejection is the
arm's measurement and not a failure of the caller;
:func:`strict_decode_reason` names the rule for the diagnostics table.

Stdlib only.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from isalhg.core.sparse_hypergraph import SparseHypergraph

COUNT_TAG = "N"
TYPE_TAG = "T"
FACT_TAG = "FACT"
PRED_TAG = "P"
CONST_TAG = "C"
END_TAG = "END"

MIN_ARITY = 2


def flatten(H: SparseHypergraph) -> tuple[tuple[Any, ...], ...]:
    """Write ``H`` as a flat incidence-list token sequence.

    Facts are emitted in the order of ``H.iter_edges()`` and their member ids in
    increasing order, so the encoding is deterministic and
    ``strict_decode(flatten(H))`` reproduces ``H`` exactly (same ids, same
    types, same predicates) rather than merely something isomorphic to it.

    Parameters
    ----------
    H : SparseHypergraph
        The knowledge base to serialize.

    Returns
    -------
    tuple[tuple, ...]
        ``("N", n)``, then one ``("T", type)`` per constant in id order, then
        per fact ``("FACT",) ("P", pred) ("C", id)...``, then ``("END",)``.
        Length ``2 + n + sum(2 + arity)``.
    """
    tokens: list[tuple[Any, ...]] = [(COUNT_TAG, H.n_nodes)]
    tokens.extend((TYPE_TAG, H.vertex_label(v)) for v in range(H.n_nodes))
    for _, members, label in H.iter_edges():
        tokens.append((FACT_TAG,))
        tokens.append((PRED_TAG, label))
        tokens.extend((CONST_TAG, v) for v in sorted(members))
    tokens.append((END_TAG,))
    return tuple(tokens)


def _is_id(value: Any) -> bool:
    """True for a genuine non-negative int (``bool`` is not an id)."""
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def strict_decode_reason(
    tokens: Sequence[tuple[Any, ...]],
    *,
    n_types: int,
    n_preds: int,
) -> str | None:
    """Return the name of the rule that rejects ``tokens``, or ``None`` if it decodes.

    The rule names are stable strings suitable for a rejection-cause histogram:
    ``"header"``, ``"duplicate_header"``, ``"negative_count"``, ``"type_count"``,
    ``"type_id"``, ``"pred_id"``, ``"constant_id"``, ``"arity"``,
    ``"duplicate_fact"``, ``"dangling"``, ``"terminator"``, ``"token_shape"``.

    Parameters
    ----------
    tokens : Sequence[tuple]
        The candidate sequence.
    n_types, n_preds : int
        Vocabulary sizes the ids must fall inside. Both must be at least 1.

    Returns
    -------
    str or None
        The failing rule, or ``None`` when the sequence is well formed.
    """
    return _decode(tokens, n_types=n_types, n_preds=n_preds)[1]


def strict_decode(
    tokens: Sequence[tuple[Any, ...]],
    *,
    n_types: int,
    n_preds: int,
) -> SparseHypergraph | None:
    """Read a flat incidence-list sequence back, or return ``None`` if ill formed.

    Unlike :func:`isalhg.core.fact_word.decode_fact_word`, this decoder is
    **partial**: the grammar it implements has constraints (declared count,
    id range, arity floor, fact uniqueness, balanced facts, terminator) that a
    sequence can violate, and every violation is a rejection. The module
    docstring enumerates them.

    Parameters
    ----------
    tokens : Sequence[tuple]
        The candidate sequence.
    n_types : int
        Constant-type vocabulary size; becomes ``n_vertex_labels``. At least 1.
    n_preds : int
        Predicate vocabulary size; becomes ``n_edge_labels``. At least 1.

    Returns
    -------
    SparseHypergraph or None
        The decoded knowledge base, or ``None`` on any violation. A decoded
        result carries exactly the declared constants, so an isolated constant
        survives and the result may be disconnected.
    """
    return _decode(tokens, n_types=n_types, n_preds=n_preds)[0]


def _decode(
    tokens: Sequence[tuple[Any, ...]],
    *,
    n_types: int,
    n_preds: int,
) -> tuple[SparseHypergraph | None, str | None]:
    """Shared body of :func:`strict_decode` and :func:`strict_decode_reason`."""
    if n_types < 1 or n_preds < 1:
        return None, "token_shape"
    if not tokens:
        return None, "header"

    for token in tokens:
        if not isinstance(token, tuple) or not token:
            return None, "token_shape"

    head = tokens[0]
    if head[0] != COUNT_TAG or len(head) != 2:
        return None, "header"
    if not isinstance(head[1], int) or isinstance(head[1], bool):
        return None, "token_shape"
    if head[1] < 0:
        return None, "negative_count"
    n = head[1]

    types: list[int] = []
    facts: list[tuple[int, frozenset[int]]] = []
    seen_facts: set[tuple[int, frozenset[int]]] = set()

    open_pred: int | None = None
    open_members: set[int] | None = None
    in_fact = False
    terminated = False

    def close_open() -> str | None:
        """Validate and file the fact currently being read."""
        nonlocal open_pred, open_members, in_fact
        if not in_fact:
            return None
        if open_pred is None:
            return "dangling"
        members = frozenset(open_members or ())
        if len(members) < MIN_ARITY:
            return "arity"
        key = (open_pred, members)
        if key in seen_facts:
            return "duplicate_fact"
        seen_facts.add(key)
        facts.append(key)
        open_pred, open_members, in_fact = None, None, False
        return None

    for token in tokens[1:]:
        if terminated:
            return None, "terminator"
        tag = token[0]

        if tag == COUNT_TAG:
            return None, "duplicate_header"

        if tag == TYPE_TAG:
            if in_fact:
                return None, "dangling"
            if len(token) != 2 or not _is_id(token[1]):
                return None, "token_shape"
            if token[1] >= n_types:
                return None, "type_id"
            types.append(token[1])
            continue

        if tag == FACT_TAG:
            if len(token) != 1:
                return None, "token_shape"
            reason = close_open()
            if reason is not None:
                return None, reason
            in_fact = True
            open_pred, open_members = None, set()
            continue

        if tag == PRED_TAG:
            if not in_fact or open_pred is not None:
                return None, "dangling"
            if len(token) != 2 or not _is_id(token[1]):
                return None, "token_shape"
            if token[1] >= n_preds:
                return None, "pred_id"
            open_pred = token[1]
            continue

        if tag == CONST_TAG:
            if not in_fact or open_pred is None:
                return None, "dangling"
            if len(token) != 2 or not _is_id(token[1]):
                return None, "token_shape"
            if token[1] >= n:
                return None, "constant_id"
            assert open_members is not None
            open_members.add(token[1])
            continue

        if tag == END_TAG:
            if len(token) != 1:
                return None, "token_shape"
            reason = close_open()
            if reason is not None:
                return None, reason
            terminated = True
            continue

        return None, "token_shape"

    if not terminated:
        return None, "terminator"
    if len(types) != n:
        return None, "type_count"

    return (
        SparseHypergraph(
            n_nodes=n,
            hyperedges=[members for _, members in facts],
            n_vertex_labels=n_types,
            n_edge_labels=n_preds,
            vertex_labels=types,
            edge_labels=[pred for pred, _ in facts],
        ),
        None,
    )


__all__ = [
    "CONST_TAG",
    "COUNT_TAG",
    "END_TAG",
    "FACT_TAG",
    "MIN_ARITY",
    "PRED_TAG",
    "TYPE_TAG",
    "flatten",
    "strict_decode",
    "strict_decode_reason",
]
