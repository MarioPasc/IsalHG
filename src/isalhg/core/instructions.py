"""``Sigma_HG`` instruction tokens.

The alphabet:

- ``V_{i,j}`` -- new edge over ``i`` existing + ``j`` new nodes.
- ``C_i`` -- new edge over ``i`` existing nodes (no-op if it already exists).
- ``P_i`` / ``N_i`` -- advance / retreat pointer ``p_i``.
- ``W`` -- no-op (padding).

This module defines the dataclasses, the regex parser, and the validity
checker. Tokens are immutable.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass


@dataclass(frozen=True)
class Token:
    """Base class for all ``Sigma_HG`` tokens."""


@dataclass(frozen=True)
class TokenV(Token):
    """``V_{i,j}`` -- new edge over ``i`` existing + ``j`` new nodes."""

    i: int
    j: int


@dataclass(frozen=True)
class TokenC(Token):
    """``C_i`` -- new edge over ``i`` existing nodes."""

    i: int


@dataclass(frozen=True)
class TokenP(Token):
    """``P_i`` -- advance pointer ``p_i``."""

    i: int


@dataclass(frozen=True)
class TokenN(Token):
    """``N_i`` -- retreat pointer ``p_i``."""

    i: int


@dataclass(frozen=True)
class TokenW(Token):
    """``W`` -- no-op."""


def parse(string: str) -> list[Token]:
    """Tokenise an instruction string.

    Raises
    ------
    isalhg.errors.InvalidInstructionError
        If a substring is not a valid token.
    """
    raise NotImplementedError


def iter_tokens(string: str) -> Iterator[Token]:
    """Streaming variant of :func:`parse`."""
    raise NotImplementedError


def validate(tokens: list[Token], *, k: int) -> None:
    """Check every token against the alphabet's ``k``-dependent constraints.

    Raises
    ------
    isalhg.errors.InvalidInstructionError
        On constraint violation.
    """
    raise NotImplementedError
