"""``IsalEngineLevenshtein`` -- edit distance between the nauty-assisted Isal words.

Two arms, one class, and both are ``Sigma_HG`` words produced by the family's own
walk -- not by the ordered walk of ``isal_ordered``:

* ``wstar_rank`` -- the greedy displacement search with the residual tie set and the
  new-vertex order resolved by nauty's canonical rank. nauty supplies the order used
  *inside* the Isal search; the value is a new canonical form, not ``w*_c``.
* ``wstar_orbit`` -- the tie-complete search with every residual branch set reduced to
  one representative per orbit of the relevant stabiliser. nauty is an automorphism
  oracle only, so the value **is** the frozen ``w*_c``, bit-identical to the C++
  engine (value-preserving pruning).

Both engines live in :mod:`isalhg.iso_backends.orbit_oracle` and are imported inside
method bodies, so this module imports (and registers its two names) even while that
module is still landing; the failure then surfaces at the first call, with the arm
name in the message, rather than at registry import.

Granularity and the seed prefix mirror
:class:`isalhg.metric_space.distances.isalhg_levenshtein.IsalHGLevenshtein` exactly:
one symbol per ``Sigma_HG`` token, prefixed by ``("seed", label)`` when the vertex
vocabulary is non-trivial, so the sequence renders the augmented fingerprint
``F = (seed label, w)`` that Corollary A needs for identity of indiscernibles.

Unlike ``d_I``, which is a family indexed by the pointer count ``k``, neither word
here changes with ``k`` above the maximum arity: the walk points at most as many
pointers as the widest edge needs and never names a higher index. ``fingerprint`` is
therefore well defined without pinning ``k`` first, and ``k`` defaults to
``required_k(H)`` per member.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, TypeAlias

from isalhg.core.canonical import required_k
from isalhg.core.instructions import parse
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.errors import DistanceComputationError, RepresentationDependencyMissingError
from isalhg.metric_space.base import HypergraphDistance
from isalhg.metric_space.registry import register_distance
from isalhg.types import DistanceName

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray

    from isalhg.core.instructions import Token

Symbol: TypeAlias = "Token | tuple[str, int]"

#: Engine name -> ``(arm name, entry-point function name in orbit_oracle)``.
ENGINES: dict[str, tuple[str, str]] = {
    "rank": ("wstar_rank", "canonical_fingerprint_rank"),
    "orbit": ("wstar_orbit", "canonical_fingerprint_orbit"),
}


def _import_rapidfuzz() -> Any:
    """Return ``(Levenshtein, process)`` from rapidfuzz, or raise with a hint."""
    try:
        from rapidfuzz import process
        from rapidfuzz.distance import Levenshtein
    except ImportError as exc:  # pragma: no cover - exercised only without rapidfuzz
        raise RepresentationDependencyMissingError(
            "rapidfuzz is required for IsalEngineLevenshtein; install via `pip install rapidfuzz`"
        ) from exc
    return Levenshtein, process


def _encode(sequences: Sequence[tuple[Symbol, ...]]) -> list[str]:
    """Encode symbol sequences as strings under one shared symbol->char map.

    Levenshtein is invariant under any bijective symbol relabelling, so a private
    code point per distinct symbol preserves the token-level edit distance while
    letting rapidfuzz use its fast string path. The dict is keyed by the symbol, so
    distinctness is decided by ``==``: ``P[1]`` and ``N[1]`` hash alike (one-field
    dataclasses over the same value) but compare unequal, and receive different code
    points. Code points start at ``0x100`` to avoid control characters.
    """
    vocab: dict[Symbol, str] = {}
    encoded: list[str] = []
    for sequence in sequences:
        buffer: list[str] = []
        for symbol in sequence:
            char = vocab.get(symbol)
            if char is None:
                char = chr(0x100 + len(vocab))
                vocab[symbol] = char
            buffer.append(char)
        encoded.append("".join(buffer))
    return encoded


class IsalEngineLevenshtein(HypergraphDistance):
    """Levenshtein distance between ``Sigma_HG`` words of a nauty-assisted engine.

    Parameters
    ----------
    engine : str, optional
        ``"rank"`` (default) or ``"orbit"``; see :data:`ENGINES`.
    k : int or None, optional
        Fixed pointer count. ``None`` (default) uses ``required_k`` of each member;
        both words are invariant to any ``k`` at least the maximum arity, so this
        never makes two members incomparable.
    structural_depth : int, optional
        Structural-tuple depth passed to the engine. Defaults to 3.

    Raises
    ------
    isalhg.errors.DistanceComputationError
        If ``engine`` is not a key of :data:`ENGINES`.
    """

    # Both kinds, exactly as IsalHGLevenshtein: edge labels ride in the token grammar
    # (a V token carries the edge label and the new vertices' labels), and the one
    # vertex no V introduces is the seed, whose label the ("seed", label) prefix
    # supplies on a non-trivial vocabulary.
    labels_used = frozenset({"vertex", "edge"})

    def __init__(
        self,
        engine: str = "rank",
        *,
        k: int | None = None,
        structural_depth: int = 3,
    ) -> None:
        if engine not in ENGINES:
            raise DistanceComputationError(
                f"unknown Isal engine {engine!r}; expected one of {sorted(ENGINES)}"
            )
        self._engine = engine
        self._k = k
        self._structural_depth = structural_depth

    @property
    def name(self) -> DistanceName:
        return ENGINES[self._engine][0]

    @property
    def engine(self) -> str:
        """The engine selector this instance was built with."""
        return self._engine

    def _entry_point(self) -> Any:
        # importlib, not a `from ... import`, so this module type-checks and
        # imports against a tree where orbit_oracle has not landed yet: the two
        # arms then fail at their first call, naming themselves, instead of
        # taking the whole distance registry down at import time.
        import importlib

        arm, function = ENGINES[self._engine]
        try:
            module = importlib.import_module("isalhg.iso_backends.orbit_oracle")
        except ImportError as exc:
            raise DistanceComputationError(
                f"arm {arm!r} needs isalhg.iso_backends.orbit_oracle, which is not "
                f"importable: {exc}"
            ) from exc
        entry = getattr(module, function, None)
        if entry is None:
            raise DistanceComputationError(
                f"arm {arm!r} needs isalhg.iso_backends.orbit_oracle.{function}, "
                "which is not defined in the installed tree"
            )
        return entry

    def _symbols(self, H: SparseHypergraph, k: int, *, augment: bool) -> tuple[Symbol, ...]:
        seed_label, word = self._entry_point()(H, k=k, structural_depth=self._structural_depth)
        tokens: tuple[Symbol, ...] = tuple(parse(word))
        if not augment:
            return tokens
        return (("seed", int(seed_label)), *tokens)

    def _resolve_corpus_k(self, corpus: Sequence[SparseHypergraph]) -> int:
        if self._k is not None:
            return self._k
        return max((required_k(H) for H in corpus), default=2)

    def fingerprint(self, H: SparseHypergraph) -> tuple[Symbol, ...]:
        """Return the seed-prefixed token sequence of ``H``, one symbol per token."""
        k = self._k if self._k is not None else required_k(H)
        return self._symbols(H, k, augment=H.n_vertex_labels > 1)

    def pairwise(self, H1: SparseHypergraph, H2: SparseHypergraph) -> float:
        levenshtein, _ = _import_rapidfuzz()
        k = self._k if self._k is not None else max(required_k(H1), required_k(H2))
        augment = max(H1.n_vertex_labels, H2.n_vertex_labels) > 1
        encoded = _encode(
            [self._symbols(H1, k, augment=augment), self._symbols(H2, k, augment=augment)]
        )
        return float(levenshtein.distance(encoded[0], encoded[1]))

    def matrix(self, corpus: Sequence[SparseHypergraph]) -> NDArray[np.float64]:
        levenshtein, process = _import_rapidfuzz()
        try:
            import numpy as np
        except ImportError as exc:  # pragma: no cover - exercised only without numpy
            raise RepresentationDependencyMissingError(
                "numpy is required for IsalEngineLevenshtein.matrix(); "
                "install via `pip install numpy`"
            ) from exc
        if not corpus:
            return np.zeros((0, 0), dtype=np.float64)
        k = self._resolve_corpus_k(corpus)
        augment = any(H.n_vertex_labels > 1 for H in corpus)
        encoded = _encode([self._symbols(H, k, augment=augment) for H in corpus])
        result = process.cdist(encoded, encoded, scorer=levenshtein.distance, dtype=np.float64)
        return np.asarray(result, dtype=np.float64)


register_distance("wstar_rank", lambda: IsalEngineLevenshtein("rank"))
register_distance("wstar_orbit", lambda: IsalEngineLevenshtein("orbit"))
