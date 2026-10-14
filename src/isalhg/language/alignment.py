"""The interior of a Levenshtein alignment between two fact words.

``d_F`` is a Levenshtein distance between token sequences, so an optimal
alignment is a sequence of ``d_F`` single-token edits carrying ``w1`` to
``w2``.  The words *between* the endpoints are the alignment's interior, and
this module produces them for one optimal alignment (``rapidfuzz`` returns one;
there is in general more than one).

The interior is the exhibit of RQ6 step 4: because the decoder is total
(`DESIGN.md` G2), **every** interior word is a knowledge base, with no
reconstruction step and no validity filter.  A nauty certificate's interior
decodes to nothing at all --- that is the capability contrast the figure draws.
Totality is a theorem, so the tests assert it rather than measure it; what the
figure measures is the *shape* of the interior (sizes, connectivity).

Deletion, insertion and substitution all cost one, matching
:func:`isalhg.metric_space.distances.fact_levenshtein.word_distance`, so the
path length is exactly ``d_F(w1, w2)`` and the interior holds ``d_F - 1`` words.

:class:`Alignment` and :func:`alignments` --- the *structural* alignment between
two knowledge bases --- live in :mod:`isalhg.language.reach` beside the
delete-and-match machinery they are computed from; they are re-exported here
for callers that expect them under this name.
"""

from __future__ import annotations

from typing import Any

from isalhg.core.fact_word import Token, Word
from isalhg.language.reach import Alignment, LanguageError, alignments


class AlignmentError(LanguageError):
    """Raised when an alignment path cannot be built."""


def _import_rapidfuzz() -> Any:
    """Return ``rapidfuzz.distance.Levenshtein``, or raise with an install hint."""
    try:
        from rapidfuzz.distance import Levenshtein
    except ImportError as exc:  # pragma: no cover - exercised only without rapidfuzz
        raise AlignmentError(
            "rapidfuzz is required for alignment_path; install via `pip install rapidfuzz`"
        ) from exc
    return Levenshtein


def _codes(w1: Word, w2: Word) -> tuple[str, str]:
    """Encode both words over one shared token-to-code-point map.

    Levenshtein is invariant under a bijective relabelling of symbols, so a
    private code point per distinct token preserves the token-level alignment
    while letting ``rapidfuzz`` take its fast string path.  Code points start at
    ``0x100`` to avoid control characters.
    """
    vocabulary: dict[Token, str] = {}
    encoded: list[str] = []
    for word in (w1, w2):
        buffer: list[str] = []
        for token in word:
            char = vocabulary.get(token)
            if char is None:
                char = chr(0x100 + len(vocabulary))
                vocabulary[token] = char
            buffer.append(char)
        encoded.append("".join(buffer))
    return encoded[0], encoded[1]


def _apply_prefix(ops: list[Any], count: int, w1: Word, w2: Word) -> Word:
    """Return ``w1`` with the first ``count`` edit operations applied.

    Mirrors ``rapidfuzz.distance.Editops.apply`` but stops after ``count``
    operations and copies the untouched tail of ``w1``, so ``count = 0`` gives
    ``w1`` and ``count = len(ops)`` gives ``w2``.
    """
    out: list[Token] = []
    src = 0
    for op in ops[:count]:
        out.extend(w1[src : op.src_pos])
        if op.tag == "delete":
            src = op.src_pos + 1
        elif op.tag == "insert":
            out.append(w2[op.dest_pos])
            src = op.src_pos
        else:
            out.append(w2[op.dest_pos])
            src = op.src_pos + 1
    out.extend(w1[src:])
    return tuple(out)


def alignment_path(w1: Word, w2: Word) -> list[Word]:
    """Return the interior words of one optimal Levenshtein alignment.

    Parameters
    ----------
    w1, w2 : Word
        Token sequences written against the same alphabet scope.

    Returns
    -------
    list[Word]
        The ``d_F(w1, w2) - 1`` words strictly between the endpoints, in path
        order; empty when the two words are equal or one edit apart.  Word
        ``i`` differs from word ``i + 1`` by exactly one token edit.

    Raises
    ------
    AlignmentError
        If ``rapidfuzz`` is not installed.
    """
    levenshtein = _import_rapidfuzz()
    code1, code2 = _codes(w1, w2)
    ops = list(levenshtein.editops(code1, code2))
    return [_apply_prefix(ops, step, w1, w2) for step in range(1, len(ops))]


__all__ = [
    "Alignment",
    "AlignmentError",
    "alignment_path",
    "alignments",
]
