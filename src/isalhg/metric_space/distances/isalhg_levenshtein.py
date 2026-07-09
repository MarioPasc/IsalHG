"""``IsalHGLevenshtein`` -- the IsalHG distance ``d_I`` (our method).

``d_I(H, H') = d_Lev(w*(H), w*(H'))`` -- the Levenshtein distance between the two
canonical H2S strings. The distance runs over the **token sequence** of the
canonical string, not over its serialised ASCII form: the ``Sigma_HG`` alphabet
is a sequence of structured tokens, and (as ``core.instructions`` documents) a
multi-digit field such as ``P[10]`` must count as one symbol, not as the four
characters ``P``, ``[``, ``1``, ``0``. The stability theorem (T-TB) likewise
reasons per token. Tokens are recovered from ``w*`` via
:func:`isalhg.core.instructions.parse`.

Because ``w*`` depends on the pointer count ``k`` (Critical Invariant #7), every
hypergraph in one comparison is encoded with the **same** ``k``:
:meth:`matrix` uses the corpus maximum, :meth:`pairwise` the pair maximum, unless
a fixed ``k`` is passed to the constructor.

Raw edit distance is primary (the IsalGraph sibling reached Spearman rho=0.934
raw); ``normalize=True`` selects the length-normalized ablation. rapidfuzz's
C++ Levenshtein is imported inside method bodies (guarded), because the
Layer-1 correlation study issues millions of pairwise calls.

Labelled inputs
---------------
``w*`` never emits the label of its own seed vertex, so on a non-trivial vertex
vocabulary two non-isomorphic hypergraphs can share it and ``d_Lev`` alone
would read ``0`` on them -- identity of indiscernibles fails. Corollary A of
the Theorem A proof therefore takes the distance over the *seed-label-prefixed*
sequence: one extra symbol carrying
:func:`isalhg.core.canonical.seed_vertex_label` is prepended to each token
sequence, which costs a single substitution exactly when the seed labels
differ. The prefix is emitted only when ``n_vertex_labels > 1``, where the seed
label carries information; on a trivial vocabulary every distance is unchanged.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, TypeAlias

from isalhg.core.backends import Backend
from isalhg.core.canonical import (
    CANONICAL_ALGORITHM,
    canonical_string,
    required_k,
    seed_vertex_label,
)
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

# A canonical-string token, or the ``("seed", label)`` prefix symbol that makes
# the sequence a faithful rendering of the augmented fingerprint.
Symbol: TypeAlias = "Token | tuple[str, int]"


def _import_rapidfuzz() -> Any:
    """Return ``(Levenshtein, process)`` from rapidfuzz, or raise with a hint."""
    try:
        from rapidfuzz import process
        from rapidfuzz.distance import Levenshtein
    except ImportError as exc:  # pragma: no cover - exercised only without rapidfuzz
        raise RepresentationDependencyMissingError(
            "rapidfuzz is required for IsalHGLevenshtein; install via `pip install rapidfuzz`"
        ) from exc
    return Levenshtein, process


def _encode(sequences: Sequence[tuple[Symbol, ...]]) -> list[str]:
    """Encode symbol sequences as strings under one shared symbol->char map.

    Levenshtein is invariant under any bijective symbol relabelling, so mapping
    each distinct symbol to a private code point preserves the token-level edit
    distance while letting rapidfuzz use its fast string path. A shared
    vocabulary across ``sequences`` keeps their pairwise distances mutually
    consistent. Code points start at ``0x100`` to avoid control characters.
    """
    vocab: dict[Symbol, str] = {}
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


class IsalHGLevenshtein(HypergraphDistance):
    """Levenshtein distance between canonical H2S strings ``w*`` (``d_I``).

    Parameters
    ----------
    k : int or None, optional
        Fixed pointer count for every ``w*``. ``None`` (default) resolves ``k``
        per comparison (pair maximum for :meth:`pairwise`, corpus maximum for
        :meth:`matrix`) so the two strings under comparison always share ``k``.
    algorithm : str, optional
        Canonical-string algorithm; must be ``"canonical"`` (``w*_c``,
        the tie-complete lex-min) -- the only variant under which ``d_I``
        is a metric on isomorphism classes (Corollary A). Passing any
        other name raises :class:`isalhg.errors.DistanceComputationError`
        at construction time.
    structural_depth : int, optional
        Structural-tuple depth passed to :func:`canonical_string`. Defaults to 3.
    normalize : bool, optional
        If ``True``, use length-normalized edit distance in ``[0, 1]`` (ablation).
        Defaults to ``False`` (raw distance, primary).
    backend : {"cpp", "python"} or None, optional
        Canonical-string implementation. ``None`` uses the package default.
    """

    def __init__(
        self,
        *,
        k: int | None = None,
        algorithm: str = CANONICAL_ALGORITHM,
        structural_depth: int = 3,
        normalize: bool = False,
        backend: Backend | None = None,
        max_expansions: int | None = None,
    ) -> None:
        if algorithm != CANONICAL_ALGORITHM:
            raise DistanceComputationError(
                f"IsalHGLevenshtein requires algorithm={CANONICAL_ALGORITHM!r} "
                f"(the only variant under which d_I is a metric); "
                f"got {algorithm!r}. "
                f"To compute non-metric fingerprint distances for ablation, "
                f"call canonical_string() directly."
            )
        self._k = k
        self._algorithm = algorithm
        self._structural_depth = structural_depth
        self._normalize = normalize
        self._backend = backend
        self._max_expansions = max_expansions

    @property
    def name(self) -> DistanceName:
        return "isalhg_levenshtein_normalized" if self._normalize else "isalhg_levenshtein"

    def _symbols(self, H: SparseHypergraph, k: int, *, augment: bool) -> tuple[Symbol, ...]:
        w_star = canonical_string(
            H,
            k=k,
            structural_depth=self._structural_depth,
            algorithm=self._algorithm,
            backend=self._backend,
            max_expansions=self._max_expansions,
        )
        tokens: tuple[Symbol, ...] = tuple(parse(w_star))
        if not augment:
            return tokens
        return (("seed", seed_vertex_label(H, w_star)), *tokens)

    def _resolve_corpus_k(self, corpus: Sequence[SparseHypergraph]) -> int:
        if self._k is not None:
            return self._k
        return max((required_k(H) for H in corpus), default=2)

    def pairwise(self, H1: SparseHypergraph, H2: SparseHypergraph) -> float:
        levenshtein, _ = _import_rapidfuzz()
        k = self._k if self._k is not None else max(required_k(H1), required_k(H2))
        augment = max(H1.n_vertex_labels, H2.n_vertex_labels) > 1
        encoded = _encode(
            [self._symbols(H1, k, augment=augment), self._symbols(H2, k, augment=augment)]
        )
        if self._normalize:
            return float(levenshtein.normalized_distance(encoded[0], encoded[1]))
        return float(levenshtein.distance(encoded[0], encoded[1]))

    def matrix(self, corpus: Sequence[SparseHypergraph]) -> NDArray[np.float64]:
        levenshtein, process = _import_rapidfuzz()
        try:
            import numpy as np
        except ImportError as exc:  # pragma: no cover - exercised only without numpy
            raise RepresentationDependencyMissingError(
                "numpy is required for IsalHGLevenshtein.matrix(); install via `pip install numpy`"
            ) from exc
        if not corpus:
            return np.zeros((0, 0), dtype=np.float64)
        k = self._resolve_corpus_k(corpus)
        augment = any(H.n_vertex_labels > 1 for H in corpus)
        encoded = _encode([self._symbols(H, k, augment=augment) for H in corpus])
        scorer = levenshtein.normalized_distance if self._normalize else levenshtein.distance
        result = process.cdist(encoded, encoded, scorer=scorer, dtype=np.float64)
        return np.asarray(result, dtype=np.float64)

    def fingerprint(self, H: SparseHypergraph) -> Any | None:
        # Amortizable only when k is fixed; otherwise it depends on the corpus.
        if self._k is None:
            return None
        return self._symbols(H, self._k, augment=H.n_vertex_labels > 1)


register_distance("isalhg_levenshtein", IsalHGLevenshtein)
