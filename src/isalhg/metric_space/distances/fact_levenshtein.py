"""``FactRankLevenshtein`` --- the distance the article adopts.

``d_F(K, K') = Levenshtein(w(K), w(K'))`` over the token sequences of the fact
words, raw and never length-normalized.  One token is one atomic symbol, so a
fact inserted over constants that keep their addresses costs exactly one edit.

Because the address map (:func:`canonical_ranks`) is an isomorphism-invariant
injection and the fact word records every type and every fact under those
addresses, ``w`` is a complete isomorphism invariant: ``d_F = 0`` iff the two
knowledge bases are isomorphic.  Symmetry and the triangle inequality come from
``d_Lev``, so ``d_F`` is a metric on isomorphism classes.

Alphabet scoping.  Tokens carry raw type and predicate ids, so two words are
only comparable when they were written against the same ``(k_max, type
vocabulary, predicate vocabulary)``.  Distances are never compared across
collections.

Roles.  ``FactRankLevenshtein(roles=True)`` names the ablation arm
``"fact_rank_roles"``, but :meth:`~FactRankLevenshtein.pairwise` receives two
``SparseHypergraph`` objects and a ``SparseHypergraph`` does not carry roles ---
roles live on the knowledge-base record.  The roles arm therefore refuses
``pairwise`` rather than silently returning the role-free distance, which would
make the ablation secretly identical to the primary arm.  The corpus path is
:func:`fact_word` with the record's roles map, once per member, then
:func:`word_distance` on the cached words; that is what the matrix builder
does.

Layering.  :func:`canonical_ranks` lives in ``iso_backends`` and is imported
inside function bodies here.  ``metric_space`` otherwise avoids that direction
(``nauty_levi_edit`` duplicates the small ``pynauty`` graph construction rather
than import it), but the addressing is the article's central definition and
must have one source of truth; the engineering plan places the two functions in
these two packages deliberately.  ``rapidfuzz`` is likewise imported inside
method bodies.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from isalhg.core.fact_word import RolesMap, Word, encode_fact_word
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.errors import DistanceComputationError, RepresentationDependencyMissingError
from isalhg.metric_space.base import HypergraphDistance
from isalhg.metric_space.registry import register_distance
from isalhg.types import DistanceName

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray


def _import_rapidfuzz() -> Any:
    """Return ``(Levenshtein, process)`` from rapidfuzz, or raise with a hint."""
    try:
        from rapidfuzz import process
        from rapidfuzz.distance import Levenshtein
    except ImportError as exc:  # pragma: no cover - exercised only without rapidfuzz
        raise RepresentationDependencyMissingError(
            "rapidfuzz is required for FactRankLevenshtein; install via `pip install rapidfuzz`"
        ) from exc
    return Levenshtein, process


def _encode(words: Sequence[Word]) -> list[str]:
    """Encode words as strings under one shared token->code-point map.

    Levenshtein is invariant under any bijective symbol relabelling, so giving
    each distinct token a private code point preserves the token-level edit
    distance while letting rapidfuzz take its fast string path.  The vocabulary
    is shared across ``words`` so their pairwise distances stay mutually
    consistent.  Code points start at ``0x100`` to avoid control characters.
    """
    vocabulary: dict[Any, str] = {}
    encoded: list[str] = []
    for word in words:
        buffer: list[str] = []
        for token in word:
            char = vocabulary.get(token)
            if char is None:
                char = chr(0x100 + len(vocabulary))
                vocabulary[token] = char
            buffer.append(char)
        encoded.append("".join(buffer))
    return encoded


def fact_word(H: SparseHypergraph, roles: RolesMap | None = None) -> Word:
    """Return the fact word of ``H`` under the canonical addressing.

    Convenience composition of
    :func:`isalhg.iso_backends.canonical_order.canonical_ranks` and
    :func:`isalhg.core.fact_word.encode_fact_word`.  Callers holding a
    knowledge-base record pass its roles map; callers holding only a hypergraph
    pass ``None``.

    Parameters
    ----------
    H : SparseHypergraph
        The knowledge base.
    roles : RolesMap or None, optional
        ``{edge_id: {node_id: role_id}}`` aligned with ``H``'s edge ids.

    Returns
    -------
    Word
        ``n`` type tokens followed by ``m`` fact tokens.
    """
    from isalhg.iso_backends.canonical_order import canonical_ranks

    return encode_fact_word(H, canonical_ranks(H), roles)


def word_distance(w1: Word, w2: Word) -> int:
    """Return the token-level Levenshtein distance between two words.

    Parameters
    ----------
    w1, w2 : Word
        Token sequences written against the same alphabet scope.

    Returns
    -------
    int
        The unweighted edit distance, counting one token as one symbol.

    Raises
    ------
    isalhg.errors.RepresentationDependencyMissingError
        If ``rapidfuzz`` is not installed.
    """
    levenshtein, _ = _import_rapidfuzz()
    encoded = _encode([w1, w2])
    return int(levenshtein.distance(encoded[0], encoded[1]))


class FactRankLevenshtein(HypergraphDistance):
    """Levenshtein distance between fact words addressed by canonical rank.

    Parameters
    ----------
    roles : bool, optional
        Name the role-carrying ablation arm.  Defaults to ``False``, the
        primary arm of every table.  See the module docstring for why the roles
        arm refuses :meth:`pairwise`.
    """

    def __init__(self, roles: bool = False) -> None:
        self._roles = roles

    @property
    def name(self) -> DistanceName:
        return "fact_rank_roles" if self._roles else "fact_rank"

    def _require_roleless(self, method: str) -> None:
        if self._roles:
            raise DistanceComputationError(
                f"FactRankLevenshtein(roles=True).{method} cannot run: roles live "
                f"on the knowledge-base record, not on SparseHypergraph. Compute "
                f"fact_word(H, roles) once per member and call word_distance() on "
                f"the cached words."
            )

    def pairwise(self, H1: SparseHypergraph, H2: SparseHypergraph) -> float:
        """Return ``d_F(H1, H2)``.

        Raises
        ------
        isalhg.errors.DistanceComputationError
            If this instance names the roles arm.
        """
        self._require_roleless("pairwise")
        return float(word_distance(fact_word(H1), fact_word(H2)))

    def matrix(self, corpus: Sequence[SparseHypergraph]) -> NDArray[np.float64]:
        """Return the dense distance matrix, encoding each word once.

        Raises
        ------
        isalhg.errors.DistanceComputationError
            If this instance names the roles arm.
        isalhg.errors.RepresentationDependencyMissingError
            If ``numpy`` or ``rapidfuzz`` is not installed.
        """
        self._require_roleless("matrix")
        levenshtein, process = _import_rapidfuzz()
        try:
            import numpy as np
        except ImportError as exc:  # pragma: no cover - exercised only without numpy
            raise RepresentationDependencyMissingError(
                "numpy is required for FactRankLevenshtein.matrix(); "
                "install via `pip install numpy`"
            ) from exc
        if not corpus:
            return np.zeros((0, 0), dtype=np.float64)
        encoded = _encode([fact_word(H) for H in corpus])
        result = process.cdist(encoded, encoded, scorer=levenshtein.distance, dtype=np.float64)
        return np.asarray(result, dtype=np.float64)

    def fingerprint(self, H: SparseHypergraph) -> Any | None:
        """Return the fact word of ``H``, the per-member object that amortizes :meth:`matrix`."""
        self._require_roleless("fingerprint")
        return fact_word(H)


register_distance("fact_rank", FactRankLevenshtein)
register_distance("fact_rank_roles", lambda: FactRankLevenshtein(roles=True))


__all__ = [
    "FactRankLevenshtein",
    "fact_word",
    "word_distance",
]
