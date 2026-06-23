"""Canonical-string entry point.

Computes ``w*(H) = argmin_lex { greedy_H2S(H, v_0) : v_0 in argmax_lex xi(v) }``
(invariant 4). Returns the serialised string form for consumption by
:class:`isalhg.iso_backends.isalhg_backend.IsalHGBackend`.

Conjecture (Theorem 2 of PROPOSAL.md): ``w*(H1) == w*(H2)`` iff ``H1`` and
``H2`` are isomorphic. Empirically validated by the Tier 1 protocol;
theoretical proof deferred to the companion paper.

Disconnected hypergraphs are rejected per decision B11.

Extending the algorithm pool
----------------------------

There are two extension paths:

1. **Python-side algorithm.** Subclass
   :class:`isalhg.core.algorithms.base.H2SAlgorithm`, register it via
   :func:`isalhg.core.algorithms.registry.register_algorithm`. The
   ``algorithm=`` argument of :func:`canonical_string` will route to it
   automatically — no edit to this module is needed. Use this path for
   anything that is not already a thin variant of greedy_h2s.

2. **C++-native variant.** Add an entry to the ``AlgorithmVariant`` enum
   in ``src/isalhg/_core/include/isalhg/canonical.hpp``, implement the
   filter / pre-processing inside ``canonical_string_compute`` in
   ``canonical.cpp``, then register the (name, integer id) mapping at
   import time via :func:`register_cpp_variant` below. The Python
   dispatch picks it up automatically.

Both forms coexist; :func:`canonical_string` checks the C++ registry
first (single-FFI hot path) and falls back to the Python registry.
"""

from __future__ import annotations

from isalhg._core import canonical_string as _cpp_canonical_string
from isalhg.core.algorithms.registry import get_algorithm
from isalhg.core.instructions import serialize
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.errors import DisconnectedHypergraphError

# Registry of C++ AlgorithmVariant ids. See
# ``src/isalhg/_core/include/isalhg/canonical.hpp`` for the enum values
# and ``canonical.cpp`` for their semantics. New native variants extend
# this dict via :func:`register_cpp_variant`.
_CPP_VARIANT_IDS: dict[str, int] = {
    "greedy_min": 0,
    "greedy_single": 1,
    "greedy_min_inplace": 2,
    "greedy_min_wl_pruned": 3,
    "greedy_min_inplace_wl_pruned": 4,
}


def register_cpp_variant(name: str, algorithm_id: int) -> None:
    """Register a C++ ``AlgorithmVariant`` id under a Python-visible name.

    Use after extending the C++ ``AlgorithmVariant`` enum and
    ``canonical_string_compute`` in ``canonical.cpp``. The
    :func:`canonical_string` dispatch picks the entry up at the next call.

    Parameters
    ----------
    name : str
        Algorithm name as passed to ``canonical_string(..., algorithm=...)``.
    algorithm_id : int
        Integer value of the ``AlgorithmVariant`` enum entry.
    """
    _CPP_VARIANT_IDS[name] = algorithm_id


def available_cpp_variants() -> tuple[str, ...]:
    """Names of the C++-native canonical-string variants currently registered."""
    return tuple(sorted(_CPP_VARIANT_IDS))


def required_k(H: SparseHypergraph) -> int:
    """Return ``max(2, max_arity(H))`` -- the smallest ``k`` admissible for ``H``."""
    if H.n_edges == 0:
        return 2
    return max(2, max(len(H.members(e)) for e in H.edges()))


def canonical_string(
    H: SparseHypergraph,
    *,
    k: int | None = None,
    structural_depth: int = 3,
    algorithm: str = "greedy_min",
) -> str:
    """Compute the canonical ``Sigma_HG*`` string of ``H``.

    Parameters
    ----------
    H : SparseHypergraph
        Connected hypergraph.
    k : int or None
        Pointer count for the VM. When ``None`` (default), defaults to
        :func:`required_k` which is the smallest ``k`` compatible with the
        alphabet's arity constraints. Two hypergraphs compared via canonical
        equality MUST be encoded with the same ``k``.
    structural_depth : int
        Depth of the structural tuples (xi/eta). Defaults to 3 (invariant 8).
    algorithm : str
        Algorithm name. Resolved against the C++ variant registry
        (single-FFI fast path) first, then the Python algorithm registry.
        Defaults to ``"greedy_min"`` -- the production canonical algorithm.

    Returns
    -------
    str
        Canonical ``Sigma_HG*`` string in the bracketed-semicolon grammar.

    Raises
    ------
    DisconnectedHypergraphError
        If ``H`` is disconnected (decision B11).
    """
    if H.n_nodes == 0:
        return ""
    effective_k = required_k(H) if k is None else k
    cpp_variant_id = _CPP_VARIANT_IDS.get(algorithm)
    if cpp_variant_id is not None:
        if not H.is_connected():
            raise DisconnectedHypergraphError(
                f"{algorithm} requires a connected hypergraph (decision B11)"
            )
        return _cpp_canonical_string(H, effective_k, structural_depth, cpp_variant_id)
    algo = get_algorithm(algorithm, k=effective_k, structural_depth=structural_depth)
    tokens = algo.encode(H)
    return serialize(list(tokens))
