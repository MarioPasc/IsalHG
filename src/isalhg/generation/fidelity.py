"""Fidelity and novelty of a generated sample set -- RQ6's second axis.

Validity says a sample *is* a knowledge base; it says nothing about whether it
looks like one from the collection. These are the measures that do: the
Jensen-Shannon divergence between the sample's structural histograms and the
collection's, and the fraction of samples that are new.

Five histograms, chosen because they are exactly the quantities the encoding
commits to: the constant count ``n``, the fact count ``m``, the arity of each
fact, the predicate of each fact, and the type of each constant. A generator
that matched all five and still produced implausible knowledge bases would be
failing at something no histogram can see, and RQ6 says so rather than
pretending otherwise.

Divergence, not distance. :func:`jsd` returns the Jensen-Shannon *divergence*
in bits, which lies in ``[0, 1]``: 0 for identical distributions and exactly 1
for distributions with disjoint support. Its square root is the metric; the
divergence is reported because the design names JSD and because the ``[0, 1]``
reading is the legible one for a fidelity table.

Support alignment. ``n`` and ``m`` and arity are counts, so their histograms are
indexed by value and padded to the longer of the two. Predicate and type
histograms are indexed by vocabulary id. In both cases sample and collection are
aligned before comparison, so a value the sample never produced contributes a
zero rather than shifting every later bin.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, TypeAlias, cast

from isalhg.core.fact_word import Word
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.generation.errors import GenerationError

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray

    # Local alias so no annotation has to name ``np``: every function here binds
    # ``np`` as a local from the guarded import, which would shadow the module
    # the annotation means.
    FloatArray: TypeAlias = NDArray[np.float64]

PROFILE_KEYS: tuple[str, ...] = ("n", "m", "arity", "pred", "type")


def _import_numpy() -> Any:
    try:
        import numpy as np
    except ImportError as exc:  # pragma: no cover - exercised only without numpy
        raise GenerationError(
            "numpy is required for the fidelity measures; install via `pip install numpy`"
        ) from exc
    return np


def _counts_to_array(counter: Counter[int], length: int) -> FloatArray:
    """Dense normalized vector of ``counter`` over ``range(length)``."""
    np = _import_numpy()
    vector = np.zeros(max(length, 1), dtype=np.float64)
    for key, value in counter.items():
        if 0 <= key < len(vector):
            vector[key] = float(value)
    total = vector.sum()
    if total > 0:
        vector /= total
    return cast("FloatArray", vector)


def profile(hs: Sequence[SparseHypergraph]) -> dict[str, FloatArray]:
    """Return the five normalized structural histograms of ``hs``.

    Every histogram is indexed by value from 0, so two profiles are aligned by
    :func:`_align` before comparison and no bin ever shifts.

    Parameters
    ----------
    hs : Sequence[SparseHypergraph]
        The knowledge bases to profile. May be empty, in which case every
        histogram is a single zero bin.

    Returns
    -------
    dict[str, numpy.ndarray]
        Keys ``"n"``, ``"m"``, ``"arity"``, ``"pred"``, ``"type"``. Shapes:
        ``"n"`` is ``(max n + 1,)``, ``"m"`` is ``(max m + 1,)``, ``"arity"`` is
        ``(max arity + 1,)``, ``"pred"`` is ``(n_edge_labels,)``, ``"type"`` is
        ``(n_vertex_labels,)`` -- the vocabulary sizes taken as the maximum over
        ``hs``. Each vector sums to 1, or is all-zero when the corresponding
        population is empty (no members, or no facts).

    Raises
    ------
    isalhg.errors.IsalHGError
        If numpy is not installed.
    """
    n_counts: Counter[int] = Counter()
    m_counts: Counter[int] = Counter()
    arity_counts: Counter[int] = Counter()
    pred_counts: Counter[int] = Counter()
    type_counts: Counter[int] = Counter()

    n_types = 1
    n_preds = 1
    for H in hs:
        n_counts[H.n_nodes] += 1
        m_counts[H.n_edges] += 1
        n_types = max(n_types, H.n_vertex_labels)
        n_preds = max(n_preds, H.n_edge_labels)
        for v in range(H.n_nodes):
            type_counts[H.vertex_label(v)] += 1
        for _, members, label in H.iter_edges():
            arity_counts[len(members)] += 1
            pred_counts[label] += 1

    return {
        "n": _counts_to_array(n_counts, max(n_counts, default=0) + 1),
        "m": _counts_to_array(m_counts, max(m_counts, default=0) + 1),
        "arity": _counts_to_array(arity_counts, max(arity_counts, default=0) + 1),
        "pred": _counts_to_array(pred_counts, max(n_preds, max(pred_counts, default=0) + 1)),
        "type": _counts_to_array(type_counts, max(n_types, max(type_counts, default=0) + 1)),
    }


def _align(
    p: FloatArray, q: FloatArray
) -> tuple[FloatArray, FloatArray]:
    """Zero-pad the shorter of two histograms so both index the same support."""
    np = _import_numpy()
    length = max(len(p), len(q))
    p_padded = np.zeros(length, dtype=np.float64)
    q_padded = np.zeros(length, dtype=np.float64)
    p_padded[: len(p)] = p
    q_padded[: len(q)] = q
    return p_padded, q_padded


def _entropy(vector: FloatArray) -> float:
    """Shannon entropy of a normalized histogram, in bits (zero bins skipped)."""
    np = _import_numpy()
    nonzero = vector[vector > 0]
    return float(-(nonzero * np.log2(nonzero)).sum())


def jsd(p: FloatArray, q: FloatArray) -> float:
    """Jensen-Shannon divergence between two histograms, in bits.

    ``JSD(p, q) = H((p + q) / 2) - (H(p) + H(q)) / 2`` with ``H`` the Shannon
    entropy in base 2. Inputs are aligned by zero-padding and renormalized, so
    unnormalized counts are accepted.

    Parameters
    ----------
    p, q : numpy.ndarray
        Non-negative 1-D vectors. Lengths may differ.

    Returns
    -------
    float
        A value in ``[0, 1]``: 0 iff the two normalized histograms are equal,
        1 iff their supports are disjoint. Returns 0.0 when both are all-zero
        (two empty populations agree vacuously) and 1.0 when exactly one is.

    Raises
    ------
    isalhg.errors.IsalHGError
        If numpy is not installed, or either input is negative or not 1-D.
    """
    np = _import_numpy()
    p_arr = np.asarray(p, dtype=np.float64)
    q_arr = np.asarray(q, dtype=np.float64)
    if p_arr.ndim != 1 or q_arr.ndim != 1:
        raise GenerationError("jsd expects 1-D histograms")
    if (p_arr < 0).any() or (q_arr < 0).any():
        raise GenerationError("jsd expects non-negative histograms")

    p_sum = float(p_arr.sum())
    q_sum = float(q_arr.sum())
    if p_sum == 0.0 and q_sum == 0.0:
        return 0.0
    if p_sum == 0.0 or q_sum == 0.0:
        return 1.0

    p_arr, q_arr = _align(p_arr / p_sum, q_arr / q_sum)
    mixture = 0.5 * (p_arr + q_arr)

    value = _entropy(mixture) - 0.5 * (_entropy(p_arr) + _entropy(q_arr))
    # Clamp the float noise: the quantity is provably in [0, 1].
    return float(min(max(value, 0.0), 1.0))


def fidelity(
    samples: Sequence[SparseHypergraph],
    collection: Sequence[SparseHypergraph],
) -> dict[str, float]:
    """Return the five Jensen-Shannon divergences between ``samples`` and ``collection``.

    Parameters
    ----------
    samples : Sequence[SparseHypergraph]
        The decoded samples of one seed.
    collection : Sequence[SparseHypergraph]
        The members the model was fitted on.

    Returns
    -------
    dict[str, float]
        Keys ``"jsd_n"``, ``"jsd_m"``, ``"jsd_arity"``, ``"jsd_pred"``,
        ``"jsd_type"``, each in ``[0, 1]`` and lower-is-closer.

    Raises
    ------
    isalhg.errors.IsalHGError
        If numpy is not installed.
    """
    sample_profile = profile(samples)
    collection_profile = profile(collection)
    return {f"jsd_{key}": jsd(sample_profile[key], collection_profile[key]) for key in PROFILE_KEYS}


def novelty(sample_keys: Sequence[Word], collection_keys: Sequence[Word]) -> float:
    """Fraction of ``sample_keys`` that do not appear in ``collection_keys``.

    The key of a knowledge base is its fact word under the canonical addressing,
    which is a complete isomorphism invariant -- so "not in the collection"
    means "not isomorphic to any member", not merely "not identical to one".
    Pass role-free keys (``fact_word(H)`` with no roles map) so that a sample
    reproducing a member up to argument roles still counts as a reproduction.

    Parameters
    ----------
    sample_keys : Sequence[Word]
        Fact words of the decoded samples.
    collection_keys : Sequence[Word]
        Fact words of the collection members.

    Returns
    -------
    float
        A value in ``[0, 1]``; ``0.0`` for an empty sample set (nothing was
        generated, so nothing is new).
    """
    if not sample_keys:
        return 0.0
    known = set(collection_keys)
    return sum(1 for key in sample_keys if key not in known) / len(sample_keys)


__all__ = ["PROFILE_KEYS", "fidelity", "jsd", "novelty", "profile"]
