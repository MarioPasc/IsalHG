"""``IsalOrderedLevenshtein`` -- edit distance between ordered-walk Isal words (``d_o``).

``d_o(H, H') = d_Lev(w_o(H), w_o(H'))`` over the *instruction* sequence of the ordered
walk, prefixed by the root's type when the vertex vocabulary is non-trivial. Because
``(root type, w_o)`` is a complete isomorphism invariant (Theorem C,
``theorem_c_ordered_walk.tex``), ``d_o`` is a metric on isomorphism classes: identity of
indiscernibles from completeness, symmetry and the triangle inequality from ``d_Lev``.

Three arms, one class. ``isal_ow_struct`` is the default policy; ``isal_ow_rank`` and
``isal_ow_rank0`` are the two ablations that isolate which half of the emission policy
buys locality. All three are exact -- the policy changes the word, not what the word
determines.

Distance granularity. The symbols are tokens, not characters: ``P[10]`` is one
instruction, not four bytes. Two tokens are the same symbol exactly when they are equal
as frozen dataclasses, so ``P[1]`` and ``N[1]`` -- which hash alike, being one-field
dataclasses over the same value -- are two symbols, not one. The encoder below keys a
dict by the token itself, which resolves the collision by equality.

Unlike ``d_I`` (which is a family indexed by the pointer count ``k``), ``d_o`` needs no
``k``: the ordered walk points at most ``max(2, max arity)`` pointers and never names a
higher index, so the word is the same for every admissible ``k``. Fingerprints are
therefore comparable across a corpus without pinning ``k`` first.
"""

from __future__ import annotations

from collections.abc import Hashable, Sequence
from typing import TYPE_CHECKING, Any

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.errors import DistanceComputationError, RepresentationDependencyMissingError
from isalhg.iso_backends.isal_ordered import POLICIES, ordered_symbols
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
            "rapidfuzz is required for IsalOrderedLevenshtein; install via `pip install rapidfuzz`"
        ) from exc
    return Levenshtein, process


def _encode(sequences: Sequence[tuple[Hashable, ...]]) -> list[str]:
    """Encode symbol sequences as strings under one shared symbol->char map.

    Levenshtein is invariant under any bijective symbol relabelling, so mapping each
    distinct symbol to a private code point preserves the instruction-level edit
    distance while letting rapidfuzz use its fast string path. A shared vocabulary
    across ``sequences`` keeps their pairwise distances mutually consistent. Code
    points start at ``0x100`` to avoid control characters.

    The dict is keyed by the symbol, so distinctness is decided by ``==``: ``P[1]`` and
    ``N[1]`` collide in ``hash`` but compare unequal, and receive different code points.
    """
    vocab: dict[Hashable, str] = {}
    encoded: list[str] = []
    for seq in sequences:
        buffer: list[str] = []
        for sym in seq:
            char = vocab.get(sym)
            if char is None:
                char = chr(0x100 + len(vocab))
                vocab[sym] = char
            buffer.append(char)
        encoded.append("".join(buffer))
    return encoded


class IsalOrderedLevenshtein(HypergraphDistance):
    """Levenshtein distance between ordered-walk Isal words.

    Parameters
    ----------
    policy : str, optional
        One of :data:`isalhg.iso_backends.isal_ordered.POLICIES` --
        ``"struct"`` (default), ``"rank"`` or ``"rank0"``.
    backend : {"cpp", "python"} or None, optional
        Emitter implementation. ``None`` takes the C++ extension when it is
        importable; the word, and therefore every distance, is the same either way.

    Raises
    ------
    isalhg.errors.DistanceComputationError
        If ``policy`` is not one of the three registered arms.
    """

    # Both kinds. Predicates ride in the token grammar (the ``edge_label`` field of
    # every ``V`` and ``C``); types ride in the ``new_node_labels`` of the ``V`` that
    # creates each constant. The one constant no ``V`` creates is the root, whose type
    # is supplied by the ``("seed", label)`` prefix (emitted only when the vertex
    # vocabulary is non-trivial). Between them every label of a connected input is read.
    labels_used = frozenset({"vertex", "edge"})

    def __init__(self, policy: str = "struct", backend: str | None = None) -> None:
        if policy not in POLICIES:
            raise DistanceComputationError(
                f"unknown ordered-walk policy {policy!r}; expected one of {sorted(POLICIES)}"
            )
        self._policy_name = policy
        self._policy = POLICIES[policy]
        self._backend = backend

    @property
    def name(self) -> DistanceName:
        return f"isal_ow_{self._policy_name}"

    def fingerprint(self, H: SparseHypergraph) -> tuple[Hashable, ...]:
        """Return the instruction sequence of ``H``, one symbol per instruction."""
        return ordered_symbols(H, policy=self._policy, backend=self._backend)

    def pairwise(self, H1: SparseHypergraph, H2: SparseHypergraph) -> float:
        levenshtein, _ = _import_rapidfuzz()
        encoded = _encode([self.fingerprint(H1), self.fingerprint(H2)])
        return float(levenshtein.distance(encoded[0], encoded[1]))

    def matrix(self, corpus: Sequence[SparseHypergraph]) -> NDArray[np.float64]:
        levenshtein, process = _import_rapidfuzz()
        try:
            import numpy as np
        except ImportError as exc:  # pragma: no cover - exercised only without numpy
            raise RepresentationDependencyMissingError(
                "numpy is required for IsalOrderedLevenshtein.matrix(); "
                "install via `pip install numpy`"
            ) from exc
        if not corpus:
            return np.zeros((0, 0), dtype=np.float64)
        encoded = _encode([self.fingerprint(H) for H in corpus])
        result = process.cdist(encoded, encoded, scorer=levenshtein.distance, dtype=np.float64)
        return np.asarray(result, dtype=np.float64)


register_distance("isal_ow_struct", IsalOrderedLevenshtein)
register_distance("isal_ow_rank", lambda: IsalOrderedLevenshtein("rank"))
register_distance("isal_ow_rank0", lambda: IsalOrderedLevenshtein("rank0"))
