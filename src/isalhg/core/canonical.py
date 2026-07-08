"""Canonical-string entry point.

Computes ``w*(H) = argmin_lex { greedy_H2S(H, v_0) : v_0 in S(H) }`` where
``S(H)`` is an *iso-invariant* seed set (invariant 4). The default seed
set is the neighbour-degree cascade ``max_neighbor_degree_nodes`` (max
label -> max degree -> lex-max sorted-desc neighbour degrees, T-M0);
``algorithm="greedy_min"`` selects the historical ``argmax_lex xi(v)``
set. Both are iso-invariant, so ``w*`` is an isomorphism invariant under
either. Returns the serialised string form for consumption by
:class:`isalhg.iso_backends.isalhg_backend.IsalHGBackend`.

Conjecture (Theorem 2 of PROPOSAL.md): ``w*(H1) == w*(H2)`` iff ``H1`` and
``H2`` are isomorphic. Empirically validated by the Tier 1 protocol;
theoretical proof deferred to the companion paper.

Disconnected hypergraphs are rejected per decision B11.

Backends
--------

The canonical-string algorithm has two implementations, both living in
``isalhg.core``:

- ``"cpp"`` (default): C++17 extension at ``isalhg.core._core``. Build
  via ``pip install -e .``.
- ``"python"``: pure-Python reference using ``_python_max_xi_nodes``,
  ``_python_wl_hash``, and ``_python_greedy_h2s`` from the sibling
  modules. Useful for differential testing and debugging.

Pick a backend per call with the ``backend=`` keyword; the default is
:data:`isalhg.core.backends.DEFAULT_BACKEND` (``"cpp"``).

Extending the algorithm pool
----------------------------

There are two extension paths:

1. **Python-side algorithm.** Subclass
   :class:`isalhg.core.algorithms.base.H2SAlgorithm`, register it via
   :func:`isalhg.core.algorithms.registry.register_algorithm`. The
   ``algorithm=`` argument of :func:`canonical_string` will route to it
   automatically via the existing registry. Note: the ``backend=`` flag
   does NOT propagate into custom Python algorithm classes; they call
   ``greedy_h2s`` with whatever its module-level default is.

2. **C++-native variant.** Add an entry to ``AlgorithmVariant`` in
   ``src/isalhg/core/_native/include/isalhg/canonical.hpp``, implement
   the filter inside ``canonical_string_compute`` in ``canonical.cpp``,
   then call :func:`register_cpp_variant` at import time. The Python
   dispatch picks the new entry up on the next call.
"""

from __future__ import annotations

from isalhg.core._core import canonical_string as _core_canonical_string
from isalhg.core.algorithms.registry import get_algorithm
from isalhg.core.backends import Backend, resolve
from isalhg.core.hypergraph_to_string import _python_greedy_h2s
from isalhg.core.hypergraph_wl import _python_wl_hash
from isalhg.core.instructions import sequence_sort_key, serialize
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.structural_tuples import (
    _python_max_neighbor_degree_nodes,
    _python_max_xi_nodes,
)
from isalhg.errors import DisconnectedHypergraphError

# Registry of C++ ``AlgorithmVariant`` ids — see
# ``src/isalhg/core/_native/include/isalhg/canonical.hpp``. Extend via
# :func:`register_cpp_variant`.
_CPP_VARIANT_IDS: dict[str, int] = {
    "greedy_min": 0,
    "greedy_single": 1,
    "greedy_min_inplace": 2,
    "greedy_min_wl_pruned": 3,
    "greedy_min_inplace_wl_pruned": 4,
    # PI 2026-06-23 — neighbour-degree seed selector. Same H2S inner loop as
    # greedy_min / greedy_single, but the seed set is computed via the
    # (max label, max degree, lex-max sorted-desc neighbour degrees) cascade
    # instead of (xi_labelled, vertex_label).
    "greedy_min_nbrdeg": 5,
    "greedy_single_nbrdeg": 6,
}


def register_cpp_variant(name: str, algorithm_id: int) -> None:
    """Register a C++ ``AlgorithmVariant`` id under a Python-visible name."""
    _CPP_VARIANT_IDS[name] = algorithm_id


def available_cpp_variants() -> tuple[str, ...]:
    """Names of the C++-native canonical-string variants currently registered."""
    return tuple(sorted(_CPP_VARIANT_IDS))


def required_k(H: SparseHypergraph) -> int:
    """Return ``max(2, max_arity(H))`` -- the smallest ``k`` admissible for ``H``."""
    if H.n_edges == 0:
        return 2
    return max(2, max(len(H.members(e)) for e in H.edges()))


# ---------------------------------------------------------------------------
# Backend-specific implementations of the five native variants.
# ---------------------------------------------------------------------------


def _python_canonical_string(
    H: SparseHypergraph, k: int, structural_depth: int, algorithm: str
) -> str:
    """Pure-Python multi-seed canonical-string for the five native variants.

    Mirrors the dispatch performed by
    ``canonical_string_compute`` in the C++ implementation but goes
    through ``_python_max_xi_nodes`` / ``_python_wl_hash`` /
    ``_python_greedy_h2s`` end-to-end.
    """
    if not H.is_connected():
        raise DisconnectedHypergraphError(
            f"{algorithm} requires a connected hypergraph (decision B11)"
        )
    # Seed selector dispatch — the PI 2026-06-23 variants replace max_xi.
    if algorithm in ("greedy_min_nbrdeg", "greedy_single_nbrdeg"):
        seeds = _python_max_neighbor_degree_nodes(H)
    else:
        seeds = _python_max_xi_nodes(H, structural_depth)
    if not seeds:
        return ""
    if algorithm in ("greedy_single", "greedy_single_nbrdeg"):
        seeds = (min(seeds),)
    elif algorithm in ("greedy_min_wl_pruned", "greedy_min_inplace_wl_pruned"):
        colours = _python_wl_hash(H)
        min_colour = min(colours[s] for s in seeds)
        seeds = tuple(s for s in seeds if colours[s] == min_colour)
    candidates = [_python_greedy_h2s(H, seed_node=s, k=k) for s in seeds]
    best = min(candidates, key=sequence_sort_key)
    return serialize(list(best))


def _cpp_canonical_string(
    H: SparseHypergraph, k: int, structural_depth: int, algorithm: str
) -> str:
    """C++-backed canonical-string for the five native variants."""
    if not H.is_connected():
        raise DisconnectedHypergraphError(
            f"{algorithm} requires a connected hypergraph (decision B11)"
        )
    return _core_canonical_string(H, k, structural_depth, _CPP_VARIANT_IDS[algorithm])


_CANONICAL_STRING_BACKENDS: dict[str, object] = {
    "python": _python_canonical_string,
    "cpp": _cpp_canonical_string,
}


def canonical_string(
    H: SparseHypergraph,
    *,
    k: int | None = None,
    structural_depth: int = 3,
    algorithm: str = "greedy_min_nbrdeg",
    backend: Backend | None = None,
) -> str:
    """Compute the canonical ``Sigma_HG*`` string of ``H``.

    Parameters
    ----------
    H : SparseHypergraph
        Connected hypergraph.
    k : int or None
        Pointer count for the VM. When ``None`` (default), defaults to
        :func:`required_k`. Two hypergraphs compared via canonical
        equality MUST be encoded with the same ``k``.
    structural_depth : int
        Depth of the structural tuples (xi/eta). Defaults to 3.
    algorithm : str
        Algorithm name. Resolved against the C++ variant registry
        (single-FFI fast path) first, then the Python algorithm registry.
        Defaults to ``"greedy_min_nbrdeg"`` -- the neighbour-degree seed
        cascade (max label -> max degree -> lex-max sorted-desc neighbour
        degrees), iso-invariant and cheaper than the ``xi`` cascade
        (T-M0). Pass ``"greedy_min"`` for the historical ``xi``-seeded
        canonical.
    backend : {"cpp", "python"}, optional
        Implementation to use for the five native variants
        (``greedy_min``, ``greedy_single``, ``greedy_min_inplace``,
        ``greedy_min_wl_pruned``, ``greedy_min_inplace_wl_pruned``).
        Defaults to ``"cpp"`` (see
        :data:`isalhg.core.backends.DEFAULT_BACKEND`). Non-native
        variants (``exhaustive``, ``pruned_exhaustive``, plus any
        user-registered Python algorithm) ignore this flag and use the
        Python algorithm registry.

    Returns
    -------
    str
        Canonical ``Sigma_HG*`` string in the bracketed-semicolon grammar.

    Raises
    ------
    DisconnectedHypergraphError
        If ``H`` is disconnected (decision B11).
    ValueError
        If ``backend`` is unknown.
    """
    if H.n_nodes == 0:
        return ""
    effective_k = required_k(H) if k is None else k
    if algorithm in _CPP_VARIANT_IDS:
        impl = resolve(backend, _CANONICAL_STRING_BACKENDS)
        return impl(H, effective_k, structural_depth, algorithm)
    # Non-native variants stay on the Python algorithm registry.
    algo = get_algorithm(algorithm, k=effective_k, structural_depth=structural_depth)
    tokens = algo.encode(H)
    return serialize(list(tokens))
