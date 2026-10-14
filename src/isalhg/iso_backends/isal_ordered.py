"""The nauty-backed entry point of the ordered walk.

:mod:`isalhg.core.algorithms.ordered_walk` is stdlib-only and takes the canonical
order as a parameter. This module supplies the order the article adopts -- nauty's
individualisation-refinement on the coloured Levi graph, via
:func:`isalhg.iso_backends.canonical_order.canonical_ranks` -- and packages the
result the three ways its consumers want it: the raw walk, the fingerprint, and the
symbol sequence a Levenshtein distance runs over.

Division of labour, which is also the sentence the paper uses: nauty decides *which*
constant comes first; the Isal language decides *what* is written, and every string of
that language decodes to a knowledge base.

``pynauty`` is imported inside ``canonical_ranks``, so importing this module never
requires it.

The rank vector nauty returns is canonical only up to an automorphism of the canonical
form (see the :mod:`~isalhg.iso_backends.canonical_order` module docstring). That does
not weaken the word: the emitter reads ``H`` only through the canonically relabelled
structure, which such an automorphism fixes, so ``(root label, word)`` is invariant
outright. Rank vectors must still never be compared across knowledge bases.
"""

from __future__ import annotations

from collections.abc import Hashable

from isalhg.core.algorithms.ordered_walk import (
    DEFAULT_POLICY,
    OrderedWalkPolicy,
    OrderedWalkResult,
    ordered_walk,
)
from isalhg.core.instructions import serialize
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.iso_backends.canonical_order import canonical_ranks
from isalhg.types import VertexLabel

#: The three pre-registered arms. ``struct`` is the default policy; ``rank`` and
#: ``rank0`` are the ablations that isolate which half of the policy buys locality.
POLICIES: dict[str, OrderedWalkPolicy] = {
    "struct": OrderedWalkPolicy(root_rule="hub", rank_first=False),
    "rank": OrderedWalkPolicy(root_rule="hub", rank_first=True),
    "rank0": OrderedWalkPolicy(root_rule="rank0", rank_first=False),
}


def ordered_word(
    H: SparseHypergraph,
    *,
    policy: OrderedWalkPolicy = DEFAULT_POLICY,
    backend: str | None = None,
) -> OrderedWalkResult:
    """Return the ordered walk of ``H`` under nauty's canonical order.

    Parameters
    ----------
    H : SparseHypergraph
        A connected labelled hypergraph.
    policy : OrderedWalkPolicy, optional
        Root rule and ``K_V`` field order. Defaults to ``ow-struct``.
    backend : {"cpp", "python"} or None, optional
        Emitter implementation. ``None`` takes the C++ extension when it is
        importable; both return the same word.

    Returns
    -------
    OrderedWalkResult
        Root, root type, program, and creation order.

    Raises
    ------
    isalhg.errors.BackendUnavailableError
        If ``pynauty`` is not installed.
    isalhg.errors.DegenerateHypergraphError
        If ``H`` has no constants.
    isalhg.errors.DisconnectedHypergraphError
        If ``H`` is not connected.
    """
    return ordered_walk(H, canonical_ranks(H), policy=policy, backend=backend)


def ordered_fingerprint(
    H: SparseHypergraph,
    *,
    policy: OrderedWalkPolicy = DEFAULT_POLICY,
    backend: str | None = None,
) -> tuple[VertexLabel, str]:
    """Return ``(root type, serialised word)`` -- the complete invariant of Theorem C.

    The root's type is carried beside the word because no token emits it: the decoder
    receives it as ``seed_label``. On a non-trivial vertex vocabulary two
    non-isomorphic knowledge bases can share a word, so the pair is the fingerprint,
    not the string.

    Parameters
    ----------
    H : SparseHypergraph
        A connected labelled hypergraph.
    policy : OrderedWalkPolicy, optional
        Root rule and ``K_V`` field order.
    backend : {"cpp", "python"} or None, optional
        Emitter implementation; ``None`` takes the C++ extension when importable.

    Returns
    -------
    tuple[VertexLabel, str]
        The root's type and the ``";"``-joined program.
    """
    result = ordered_word(H, policy=policy, backend=backend)
    return result.root_label, serialize(result.tokens)


def ordered_symbols(
    H: SparseHypergraph,
    *,
    policy: OrderedWalkPolicy = DEFAULT_POLICY,
    backend: str | None = None,
) -> tuple[Hashable, ...]:
    """Return the fingerprint as one symbol per instruction, for edit distance.

    The tokens themselves are the symbols -- a multi-digit field such as ``P[10]``
    counts once, not four times. A ``("seed", root type)`` symbol is prepended exactly
    when the vertex vocabulary is non-trivial, mirroring
    :meth:`isalhg.metric_space.distances.isalhg_levenshtein.IsalHGLevenshtein._symbols`:
    on a trivial vocabulary the root's type carries no information and the prefix would
    only add a constant to every distance.

    Parameters
    ----------
    H : SparseHypergraph
        A connected labelled hypergraph.
    policy : OrderedWalkPolicy, optional
        Root rule and ``K_V`` field order.
    backend : {"cpp", "python"} or None, optional
        Emitter implementation; ``None`` takes the C++ extension when importable.

    Returns
    -------
    tuple[Hashable, ...]
        The symbol sequence; hashable, and comparable by equality across knowledge
        bases encoded over the same vocabularies.
    """
    result = ordered_word(H, policy=policy, backend=backend)
    if H.n_vertex_labels > 1:
        return (("seed", result.root_label), *result.tokens)
    return result.tokens


__all__ = [
    "POLICIES",
    "ordered_fingerprint",
    "ordered_symbols",
    "ordered_word",
]
