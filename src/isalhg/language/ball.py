"""The string ball around a fact word, and the knowledge bases it decodes to.

Because the alphabet is closed and the decoder total (`DESIGN.md` G2), the
Levenshtein ball of a word is a set of *knowledge bases*, not a set of strings
some of which happen to be legal.  Two things follow, and this module is what
measures them.

**Prop 4 (fact-level ball inside the string ball).**  Adding one fact ``f`` to
``K`` over constants ``K`` already has produces a knowledge base whose class is
reached by inserting exactly one token into ``w(K)``: the token
``F[predicate; ranks of f under K's addressing]``.  Its decoded class is
``K + f`` even though ``w(K + f)`` may address the constants differently ---
the class is what matters, and it is the class this module returns.

**Position independence.**  The decoded class depends only on the type prefix
in word order and on the *multiset* of fact tokens.  :func:`decoded_classes`
uses that to canonicalize once per distinct ``(type prefix, fact-token set)``
signature rather than once per word, which is what makes a radius-1 ball of a
few thousand words affordable.  The lemma is pinned by test here and in the
encoder's own suite.

Radius.  A radius-1 ball over a vocabulary of ``V`` tokens around a word of
length ``L`` holds ``1 + L + (L + 1) V`` words (plus ``L V`` more with
substitutions), so radius 2 is already millions.  The generator is written for
small radii and says so.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence

from isalhg.core.fact_word import FACT_TAG, TYPE_TAG, Token, Word, decode_fact_word
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.language.reach import LanguageError, fact_key_of


class BallError(LanguageError):
    """Raised when a ball cannot be enumerated as asked."""


def _one_edit(word: Word, vocab: tuple[Token, ...], substitutions: bool) -> Iterator[Word]:
    """Yield every word one edit from ``word``: deletions, insertions, optional substitutions."""
    for i in range(len(word)):
        yield word[:i] + word[i + 1 :]
    for i in range(len(word) + 1):
        for token in vocab:
            yield word[:i] + (token,) + word[i:]
    if substitutions:
        for i in range(len(word)):
            for token in vocab:
                if token != word[i]:
                    yield word[:i] + (token,) + word[i + 1 :]


def string_ball(
    word: Word,
    radius: int,
    vocab: Sequence[Token],
    *,
    substitutions: bool = False,
) -> Iterator[Word]:
    """Enumerate the Levenshtein ball of ``word`` over ``vocab``, deduplicated.

    Parameters
    ----------
    word : Word
        The centre; yielded first (radius 0 is inside the ball).
    radius : int
        Ball radius in single-token edits.  Intended for 1, at most 2.
    vocab : Sequence[Token]
        Tokens available for insertion (and substitution), typically
        :func:`isalhg.core.fact_word.token_vocabulary`.
    substitutions : bool, optional
        Include one-token substitutions.  Defaults to ``False`` --- the indel
        ball, matching the reach of `DESIGN.md` RQ3.

    Yields
    ------
    Word
        Each distinct word within ``radius`` edits, centre first, then radius 1,
        then radius 2; deterministic within each shell.

    Raises
    ------
    BallError
        If ``radius`` is negative.
    """
    if radius < 0:
        raise BallError(f"radius must be non-negative; got {radius}")
    tokens = tuple(vocab)
    seen: set[Word] = {word}
    yield word
    frontier: list[Word] = [word]
    for _ in range(radius):
        following: list[Word] = []
        for current in frontier:
            for candidate in _one_edit(current, tokens, substitutions):
                if candidate not in seen:
                    seen.add(candidate)
                    following.append(candidate)
                    yield candidate
        frontier = following


def _signature(word: Word) -> tuple[tuple[Token, ...], tuple[Token, ...]]:
    """Return the decode-invariant signature of ``word``.

    The decoder reads the ``T`` tokens in word order as the type prefix and the
    ``F`` tokens as a set, so two words with equal signatures decode to equal
    knowledge bases.
    """
    prefix = tuple(token for token in word if token and token[0] == TYPE_TAG)
    facts = tuple(sorted({token for token in word if token and token[0] == FACT_TAG}))
    return prefix, facts


def decoded_classes(
    words: Iterable[Word],
    *,
    n_types: int,
    n_preds: int,
) -> dict[Word, SparseHypergraph]:
    """Decode every word and index the results by canonical key.

    Parameters
    ----------
    words : Iterable[Word]
        Words over the token vocabulary; typically the output of
        :func:`string_ball`.
    n_types : int
        Constant-type vocabulary size the decoder writes into every result.
    n_preds : int
        Predicate vocabulary size.

    Returns
    -------
    dict[Word, SparseHypergraph]
        One entry per distinct decoded class: the key is
        :func:`isalhg.language.reach.fact_key_of` of the decoded knowledge base,
        the value is that knowledge base as decoded.  Insertion order follows
        the first word of each class in ``words``.

    Raises
    ------
    isalhg.errors.FactWordError
        If a word carries a token outside the vocabulary.
    isalhg.errors.BackendUnavailableError
        If ``pynauty`` is not installed.
    """
    classes: dict[Word, SparseHypergraph] = {}
    by_signature: dict[tuple[tuple[Token, ...], tuple[Token, ...]], Word] = {}
    for word in words:
        signature = _signature(word)
        known = by_signature.get(signature)
        if known is not None:
            continue
        decoded, _ = decode_fact_word(word, n_types=n_types, n_preds=n_preds)
        key = fact_key_of(decoded)
        by_signature[signature] = key
        classes.setdefault(key, decoded)
    return classes


__all__ = [
    "BallError",
    "decoded_classes",
    "string_ball",
]
