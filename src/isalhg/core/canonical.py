"""Canonical-string entry point.

Computes ``w*(H) = argmin_lex { greedy_H2S(H, v_0) : v_0 in S(H) }`` where
``S(H)`` is an *iso-invariant* seed set (invariant 4). The default seed
set is the neighbour-degree cascade ``max_neighbor_degree_nodes`` (max
label -> max degree -> lex-max sorted-desc neighbour degrees, T-M0);
``algorithm="greedy_min"`` selects the historical ``argmax_lex xi(v)``
set. Both are iso-invariant, so ``w*`` is an isomorphism invariant under
either. Returns the serialised string form for consumption by
:class:`isalhg.iso_backends.isalhg_backend.IsalHGBackend`.

Completeness status (T-TA, 2026-07-08): ``w*(H1) == w*(H2)`` implies
isomorphism for every variant (round-trip soundness). The converse is FALSE
for the single-branch greedy variants -- their residual V-tie-break by raw
edge id makes ``w*`` depend on the edge insertion order -- and PROVED for
``algorithm="canonical"`` (tie-complete branching). See the
Theorem A proof in the ISAL proofs archive and
``tests/unit/core/test_canonical.py``.

The forward direction holds over the *augmented fingerprint*
``F(H) = (seed vertex label, w*(H))``, not over the bare string: ``V`` tokens
carry only the labels of the vertices they create and ``C`` tokens carry none,
so the seed's own label is never emitted. On a non-trivial vertex vocabulary
two non-isomorphic hypergraphs can therefore share ``w*``. Use
:func:`canonical_fingerprint` wherever an isomorphism decision is made;
:func:`canonical_string` alone is complete only when ``|Sigma_V| == 1``.

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

from collections import Counter

from isalhg.core._core import canonical_string as _core_canonical_string
from isalhg.core.algorithms.registry import get_algorithm
from isalhg.core.backends import Backend, resolve
from isalhg.core.hypergraph_to_string import _python_greedy_h2s
from isalhg.core.hypergraph_wl import _python_wl_hash
from isalhg.core.instructions import TokenV, parse, sequence_sort_key, serialize
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.structural_tuples import (
    _python_max_neighbor_degree_nodes,
    _python_max_xi_nodes,
)
from isalhg.errors import DegenerateHypergraphError, DisconnectedHypergraphError, InvalidLabelError
from isalhg.types import VertexLabel

# The registered name of the canonical algorithm — the only variant whose
# ``w*`` is a complete isomorphism invariant (Theorem A, D-TA2, T-TAd).
# Referenced by :class:`isalhg.metric_space.distances.IsalHGLevenshtein`
# to guard against misuse of the greedy one-sided heuristics for ``d_I``.
CANONICAL_ALGORITHM: str = "canonical"

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
    # T-TAa — neighbour-degree seeds plus tie-complete V branching. The only
    # variant whose w* is a complete isomorphism invariant (Theorem A); the
    # rest resolve the residual V tie by raw edge id. Renamed at T-TAg to
    # reflect the output (the canonical form w*_c) rather than the search strategy.
    CANONICAL_ALGORITHM: 7,
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
# Backend-specific implementations of the native variants.
# ---------------------------------------------------------------------------


def _python_canonical_string(
    H: SparseHypergraph,
    k: int,
    structural_depth: int,
    algorithm: str,
    max_expansions: int | None = None,
) -> str:
    """Pure-Python multi-seed canonical-string for the native variants.

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
    if algorithm in ("greedy_min_nbrdeg", "greedy_single_nbrdeg", CANONICAL_ALGORITHM):
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
    tie_branch = algorithm == CANONICAL_ALGORITHM
    candidates = [
        _python_greedy_h2s(
            H,
            seed_node=s,
            k=k,
            inplace=tie_branch,
            tie_branch=tie_branch,
            max_expansions=max_expansions,
        )
        for s in seeds
    ]
    best = min(candidates, key=sequence_sort_key)
    return serialize(list(best))


def _cpp_canonical_string(
    H: SparseHypergraph,
    k: int,
    structural_depth: int,
    algorithm: str,
    max_expansions: int | None = None,
) -> str:
    """C++-backed canonical-string for the native variants."""
    if not H.is_connected():
        raise DisconnectedHypergraphError(
            f"{algorithm} requires a connected hypergraph (decision B11)"
        )
    return _core_canonical_string(
        H, k, structural_depth, _CPP_VARIANT_IDS[algorithm], max_expansions or 0
    )


_CANONICAL_STRING_BACKENDS: dict[str, object] = {
    "python": _python_canonical_string,
    "cpp": _cpp_canonical_string,
}


def canonical_string(
    H: SparseHypergraph,
    *,
    k: int | None = None,
    structural_depth: int = 3,
    algorithm: str = CANONICAL_ALGORITHM,
    backend: Backend | None = None,
    max_expansions: int | None = None,
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
        Defaults to ``"canonical"`` -- the unpruned tie-complete lex-min
        ``w*_c`` over the neighbour-degree seed cascade, the only variant
        whose string is a complete isomorphism invariant (Theorem A; frozen
        at D-TA2, flipped at D-TA1/T-TAd). The greedy variants
        (``"greedy_min_nbrdeg"``, ``"greedy_min"``) are faster one-sided
        heuristics whose string depends on the edge insertion order on
        tie-degenerate inputs; they are sound (equal fingerprints certify
        isomorphism) but not complete (unequal fingerprints are inconclusive
        on tie-degenerate inputs).
    backend : {"cpp", "python"}, optional
        Implementation to use for the native variants (the names in
        :func:`available_cpp_variants`). Defaults to ``"cpp"`` (see
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
    DegenerateHypergraphError
        If ``H`` is the empty hypergraph (``n = 0``). The empty canonical
        string is identical to the one emitted by the single-vertex hypergraph,
        which breaks identity of indiscernibles for ``d_I``.  Restrict
        inputs to ``n ≥ 1``.
    DisconnectedHypergraphError
        If ``H`` is disconnected (decision B11).
    ValueError
        If ``backend`` is unknown.
    """
    if H.n_nodes == 0:
        raise DegenerateHypergraphError(
            "canonical_string requires n ≥ 1; the empty hypergraph (n=0) produces "
            "the empty string --- identical to the single-vertex case --- which "
            "breaks identity of indiscernibles for d_I. Restrict your corpus to n ≥ 1."
        )
    effective_k = required_k(H) if k is None else k
    if algorithm in _CPP_VARIANT_IDS:
        impl = resolve(backend, _CANONICAL_STRING_BACKENDS)
        return impl(H, effective_k, structural_depth, algorithm, max_expansions)
    # Non-native variants stay on the Python algorithm registry.
    algo = get_algorithm(algorithm, k=effective_k, structural_depth=structural_depth)
    tokens = algo.encode(H)
    return serialize(list(tokens))


def seed_vertex_label(H: SparseHypergraph, w: str) -> VertexLabel:
    """Return the vertex label of the seed from which ``w`` was encoded.

    Every vertex of ``H`` except the seed is created by a ``V`` token, which
    records its label; the seed pre-exists the first token and its label is
    never emitted. The seed label is therefore the single element left when the
    labels emitted by ``w`` are removed from the vertex-label multiset of ``H``.

    This derivation is independent of the seed cascade, so it holds for every
    registered variant. Under the two production cascades the answer coincides
    with the label shared by all seeds: the maximum vertex label for the
    neighbour-degree cascade, the label of the ``argmax_lex xi`` vertices for
    the ``xi`` cascade.

    Parameters
    ----------
    H : SparseHypergraph
        The hypergraph ``w`` was computed from.
    w : str
        A canonical string of ``H``, as returned by :func:`canonical_string`.

    Returns
    -------
    VertexLabel
        Label of the seed vertex. ``0`` on the empty hypergraph and on any
        trivial vocabulary (``H.n_vertex_labels == 1``), where it is the only
        admissible label.

    Raises
    ------
    InvalidLabelError
        If ``w`` emits labels that ``H`` does not carry -- i.e. ``w`` is not a
        canonical string of ``H``.
    """
    if H.n_nodes == 0 or H.n_vertex_labels == 1:
        return 0
    remaining: Counter[VertexLabel] = Counter(H.vertex_label(v) for v in H.nodes())
    for token in parse(w):
        if isinstance(token, TokenV):
            for ell in token.new_node_labels:
                remaining[ell] -= 1
    survivors = [ell for ell, count in remaining.items() if count > 0]
    if len(survivors) != 1 or remaining[survivors[0]] != 1:
        raise InvalidLabelError(
            f"canonical string emits a vertex-label multiset incompatible with H: {remaining}"
        )
    return survivors[0]


def canonical_fingerprint(
    H: SparseHypergraph,
    *,
    k: int | None = None,
    structural_depth: int = 3,
    algorithm: str = CANONICAL_ALGORITHM,
    backend: Backend | None = None,
    max_expansions: int | None = None,
) -> tuple[VertexLabel, str]:
    """Compute the augmented fingerprint ``F(H) = (seed label, w*(H))``.

    The bare canonical string is not a complete invariant on a non-trivial
    vertex vocabulary: the seed's label is the one label ``w*`` never emits, so
    two non-isomorphic hypergraphs differing only in that label share ``w*``.
    Pairing the string with the seed label restores the forward direction of
    Theorem A (equal fingerprints imply isomorphism) for every variant, and the
    biconditional for ``algorithm="canonical"``.

    Parameters
    ----------
    H : SparseHypergraph
        Connected hypergraph.
    k, structural_depth, algorithm, backend
        Forwarded verbatim to :func:`canonical_string`.
    max_expansions : int or None, optional
        V-branch expansion budget per seed run; ``None`` (default) is unlimited.
        Forwarded verbatim to :func:`canonical_string`.

    Returns
    -------
    tuple[VertexLabel, str]
        Seed vertex label and canonical ``Sigma_HG*`` string.

    Raises
    ------
    DisconnectedHypergraphError
        If ``H`` is disconnected (decision B11).
    CanonicalizationTimeoutError
        If any seed run exceeds ``max_expansions`` (when set).
    """
    w = canonical_string(
        H,
        k=k,
        structural_depth=structural_depth,
        algorithm=algorithm,
        backend=backend,
        max_expansions=max_expansions,
    )
    return seed_vertex_label(H, w), w
