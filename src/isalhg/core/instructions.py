"""``Sigma_HG`` instruction tokens.

The two-tier labelled alphabet (proposal lines 169, 572):

- ``V[le;i;j;ln1,...,lnj]`` -- new hyperedge of arity ``i+j`` with edge
  label ``le``, over ``i`` existing pointed nodes ``p_1..p_i`` and ``j``
  new nodes inserted after ``p_1`` with labels ``ln1, ..., lnj``.
- ``C[le;i]`` -- new hyperedge over ``p_1..p_i`` with edge label ``le``;
  no-op if a hyperedge with the same ``(label, member-set)`` exists.
- ``P[i]`` / ``N[i]`` -- advance / retreat pointer ``p_i`` (``i in [1, k]``).
- ``W`` -- no-op (padding).

Sequence form: tokens joined by ``";"`` at the top level. Brackets enclose
each parameterised token's fields, so the parser respects bracket nesting
when splitting on ``;``.

Lex-comparison of canonical strings runs over **token tuples** (numeric
ordering on fields), never over the serialised string -- this avoids the
``"V[le;10;...]" < "V[le;2;...]"`` lexicographic pitfall.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import ClassVar

from isalhg.errors import InvalidInstructionError

# Token-kind ranks for the total order used in lex-comparison of token tuples.
# The specific assignment is deterministic; correctness does not depend on it.
_RANK_W: int = 0
_RANK_N: int = 1
_RANK_P: int = 2
_RANK_V: int = 3
_RANK_C: int = 4


@dataclass(frozen=True)
class Token:
    """Base class for all ``Sigma_HG`` tokens.

    Subclasses are immutable frozen dataclasses. Total ordering for
    lex-min comparison is provided by :meth:`sort_key`.
    """

    KIND: ClassVar[str] = ""

    def serialize(self) -> str:
        """Return the canonical surface form of this token."""
        raise NotImplementedError

    def sort_key(self) -> tuple[int, ...]:
        """Return a numeric tuple for lex-comparison of token sequences."""
        raise NotImplementedError


@dataclass(frozen=True)
class TokenW(Token):
    """``W`` -- no-op."""

    KIND: ClassVar[str] = "W"

    def serialize(self) -> str:
        return "W"

    def sort_key(self) -> tuple[int, ...]:
        return (_RANK_W,)


@dataclass(frozen=True)
class TokenN(Token):
    """``N[i]`` -- retreat pointer ``p_i``."""

    KIND: ClassVar[str] = "N"
    i: int

    def serialize(self) -> str:
        return f"N[{self.i}]"

    def sort_key(self) -> tuple[int, ...]:
        return (_RANK_N, self.i)


@dataclass(frozen=True)
class TokenP(Token):
    """``P[i]`` -- advance pointer ``p_i``."""

    KIND: ClassVar[str] = "P"
    i: int

    def serialize(self) -> str:
        return f"P[{self.i}]"

    def sort_key(self) -> tuple[int, ...]:
        return (_RANK_P, self.i)


@dataclass(frozen=True)
class TokenV(Token):
    """``V[le;i;j;ln1,...,lnj]`` -- create a hyperedge with ``j`` new nodes."""

    KIND: ClassVar[str] = "V"
    edge_label: int
    i: int
    j: int
    new_node_labels: tuple[int, ...] = field(default_factory=tuple)

    def serialize(self) -> str:
        labels = ",".join(str(ell) for ell in self.new_node_labels)
        return f"V[{self.edge_label};{self.i};{self.j};{labels}]"

    def sort_key(self) -> tuple[int, ...]:
        return (_RANK_V, self.edge_label, self.i, self.j, *self.new_node_labels)


@dataclass(frozen=True)
class TokenC(Token):
    """``C[le;i]`` -- create a hyperedge over the first ``i`` pointers."""

    KIND: ClassVar[str] = "C"
    edge_label: int
    i: int

    def serialize(self) -> str:
        return f"C[{self.edge_label};{self.i}]"

    def sort_key(self) -> tuple[int, ...]:
        return (_RANK_C, self.edge_label, self.i)


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def serialize(tokens: list[Token] | tuple[Token, ...]) -> str:
    """Render a token sequence as a ``;``-joined string."""
    return ";".join(t.serialize() for t in tokens)


def sequence_sort_key(
    tokens: list[Token] | tuple[Token, ...],
) -> tuple[object, ...]:
    """Return ``(length, *per-token sort keys)`` for lex-min comparison.

    Two sequences are first compared by length, then position by position
    using :meth:`Token.sort_key`. This mirrors IsalGraph's
    ``min(len(w), w)`` convention.
    """
    return (len(tokens),) + tuple(t.sort_key() for t in tokens)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def _split_top_level(buf: str, sep: str) -> list[str]:
    """Split ``buf`` on ``sep`` characters not inside ``[...]``."""
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    for ch in buf:
        if ch == "[":
            depth += 1
            current.append(ch)
        elif ch == "]":
            if depth == 0:
                raise InvalidInstructionError(f"unbalanced ']' in {buf!r}")
            depth -= 1
            current.append(ch)
        elif ch == sep and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    if depth != 0:
        raise InvalidInstructionError(f"unbalanced '[' in {buf!r}")
    parts.append("".join(current))
    return parts


def _parse_int(s: str, where: str) -> int:
    try:
        return int(s)
    except ValueError as exc:
        raise InvalidInstructionError(f"expected integer in {where}, got {s!r}") from exc


def _parse_one(piece: str) -> Token:
    if not piece:
        raise InvalidInstructionError("empty token")
    kind = piece[0]
    if kind == "W":
        if piece != "W":
            raise InvalidInstructionError(f"malformed W token: {piece!r}")
        return TokenW()
    if len(piece) < 4 or piece[1] != "[" or piece[-1] != "]":
        raise InvalidInstructionError(f"malformed token: {piece!r}")
    body = piece[2:-1]
    fields = body.split(";")
    if kind in ("P", "N"):
        if len(fields) != 1:
            raise InvalidInstructionError(
                f"{kind} token expects 1 field, got {len(fields)} in {piece!r}"
            )
        i = _parse_int(fields[0], f"{kind} token i")
        return TokenP(i=i) if kind == "P" else TokenN(i=i)
    if kind == "C":
        if len(fields) != 2:
            raise InvalidInstructionError(
                f"C token expects 2 fields, got {len(fields)} in {piece!r}"
            )
        return TokenC(
            edge_label=_parse_int(fields[0], "C edge label"),
            i=_parse_int(fields[1], "C i"),
        )
    if kind == "V":
        if len(fields) != 4:
            raise InvalidInstructionError(
                f"V token expects 4 fields, got {len(fields)} in {piece!r}"
            )
        edge_label = _parse_int(fields[0], "V edge label")
        i_val = _parse_int(fields[1], "V i")
        j_val = _parse_int(fields[2], "V j")
        labels_str = fields[3]
        new_labels: tuple[int, ...] = (
            ()
            if labels_str == ""
            else tuple(_parse_int(x, "V new-node label") for x in labels_str.split(","))
        )
        if len(new_labels) != j_val:
            raise InvalidInstructionError(
                f"V token j={j_val} but {len(new_labels)} new-node labels in {piece!r}"
            )
        return TokenV(
            edge_label=edge_label,
            i=i_val,
            j=j_val,
            new_node_labels=new_labels,
        )
    raise InvalidInstructionError(f"unknown token kind {kind!r} in {piece!r}")


def parse(string: str) -> list[Token]:
    """Tokenise an instruction string.

    Empty string returns the empty list.

    Raises
    ------
    isalhg.errors.InvalidInstructionError
        If a substring is not a valid token.
    """
    if string == "":
        return []
    pieces = _split_top_level(string, ";")
    return [_parse_one(p) for p in pieces]


def iter_tokens(string: str) -> Iterator[Token]:
    """Streaming variant of :func:`parse`."""
    yield from parse(string)


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------


def validate(
    tokens: list[Token] | tuple[Token, ...],
    *,
    k: int,
    n_vertex_labels: int = 1,
    n_edge_labels: int = 1,
) -> None:
    """Check every token against the alphabet's ``k``-dependent constraints.

    Parameters
    ----------
    tokens : list[Token]
        Sequence to validate.
    k : int
        Maximum hyperedge arity / pointer count of the VM.
    n_vertex_labels, n_edge_labels : int
        Vocabulary sizes; labels must lie in ``[0, n_vertex_labels)`` and
        ``[0, n_edge_labels)`` respectively (decision I45).

    Raises
    ------
    isalhg.errors.InvalidInstructionError
        On any constraint violation.
    """
    if k < 1:
        raise InvalidInstructionError(f"k must be >= 1, got {k}")
    for idx, tok in enumerate(tokens):
        if isinstance(tok, TokenW):
            continue
        if isinstance(tok, (TokenP, TokenN)):
            if not 1 <= tok.i <= k:
                raise InvalidInstructionError(
                    f"token {idx}: {type(tok).__name__} i={tok.i} not in [1, {k}]"
                )
        elif isinstance(tok, TokenC):
            if not 1 <= tok.i <= k:
                raise InvalidInstructionError(f"token {idx}: C i={tok.i} not in [1, {k}]")
            if not 0 <= tok.edge_label < n_edge_labels:
                raise InvalidInstructionError(
                    f"token {idx}: C edge_label={tok.edge_label} out of [0, {n_edge_labels})"
                )
        elif isinstance(tok, TokenV):
            if not 1 <= tok.i <= k - 1:
                raise InvalidInstructionError(f"token {idx}: V i={tok.i} not in [1, {k - 1}]")
            if not 1 <= tok.j <= k - 1:
                raise InvalidInstructionError(f"token {idx}: V j={tok.j} not in [1, {k - 1}]")
            if not 2 <= tok.i + tok.j <= k:
                raise InvalidInstructionError(f"token {idx}: V i+j={tok.i + tok.j} not in [2, {k}]")
            if len(tok.new_node_labels) != tok.j:
                raise InvalidInstructionError(
                    f"token {idx}: V j={tok.j} but {len(tok.new_node_labels)} labels"
                )
            if not 0 <= tok.edge_label < n_edge_labels:
                raise InvalidInstructionError(
                    f"token {idx}: V edge_label={tok.edge_label} out of [0, {n_edge_labels})"
                )
            for li, ell in enumerate(tok.new_node_labels):
                if not 0 <= ell < n_vertex_labels:
                    raise InvalidInstructionError(
                        f"token {idx}: V new_node_labels[{li}]={ell} out of [0, {n_vertex_labels})"
                    )
        else:
            raise InvalidInstructionError(f"token {idx}: unknown token type {type(tok)!r}")
