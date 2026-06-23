"""Canonical-string entry point.

Computes ``w*(H) = argmin_lex { greedy_H2S(H, v_0) : v_0 in argmax_lex xi(v) }``
(invariant 4). Returns the serialised string form for consumption by
:class:`isalhg.iso_backends.isalhg_backend.IsalHGBackend`.

Conjecture (Theorem 2 of PROPOSAL.md): ``w*(H1) == w*(H2)`` iff ``H1`` and
``H2`` are isomorphic. Empirically validated by the Tier 1 protocol;
theoretical proof deferred to the companion paper.

Disconnected hypergraphs are rejected per decision B11.
"""

from __future__ import annotations

from isalhg.core.algorithms.greedy_min import GreedyMin
from isalhg.core.algorithms.registry import get_algorithm
from isalhg.core.instructions import serialize
from isalhg.core.sparse_hypergraph import SparseHypergraph


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
        Name of a registered :class:`~isalhg.core.algorithms.base.H2SAlgorithm`
        variant. Defaults to ``"greedy_min"`` -- the production canonical
        algorithm. Other registered variants (``"greedy_single"``,
        ``"greedy_min_inplace"``, ``"greedy_min_wl_pruned"``,
        ``"greedy_min_inplace_wl_pruned"``, ``"exhaustive"``,
        ``"pruned_exhaustive"``) are exposed for the preprint
        algorithm-comparison study.

    Returns
    -------
    str
        Canonical ``Sigma_HG*`` string in the bracketed-semicolon grammar.

    Raises
    ------
    DisconnectedHypergraphError
        If ``H`` is disconnected (decision B11).
    """
    effective_k = required_k(H) if k is None else k
    if algorithm == "greedy_min":
        algo = GreedyMin(k=effective_k, structural_depth=structural_depth)
    else:
        algo = get_algorithm(algorithm, k=effective_k, structural_depth=structural_depth)
    tokens = algo.encode(H)
    return serialize(list(tokens))
