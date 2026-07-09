"""Tie-complete H2S over the neighbour-degree seed set; lex-min over results.

The single-branch greedy encoder resolves V candidates that tie through the
full iso-invariant cascade key ``(i, j, edge_label, new_node_labels, eta)``
by raw edge id (insertion order), so its output is a function of the
*presentation* (vertex ids + edge insertion order), not of the abstract
hypergraph: two edge orderings of the same hypergraph can yield different
canonical strings (counterexample pinned in
``tests/unit/core/test_canonical.py``). This variant instead recurses over
every tied candidate (``tie_branch=True``) and keeps the lex-min completion,
which removes edge ids from observable behaviour: the resulting ``w*`` is
invariant under vertex relabelling *and* edge reordering, and is a complete
isomorphism invariant (Theorem A of the metric-space article; proof archived
under the ISAL proofs directory).

Seed set: the neighbour-degree cascade :func:`max_neighbor_degree_nodes`
(iso-invariant, matching the ``greedy_min_nbrdeg`` default). Cost: the
branching factor multiplies by the tie-set size at every V step; worst case
exponential on eta-degenerate inputs (designs).

This class is the pure-Python reference. Production callers should reach the
same algorithm through ``canonical_string(algorithm="canonical")``, which
routes to the C++ ``AlgorithmVariant::GreedyMinComplete`` single-FFI fast path
(multi-seed fan-out across the thread pool). Both produce byte-identical output;
keeping the reference reachable makes ``encode()`` vs ``canonical_string()``
a live differential assertion.
"""

from __future__ import annotations

from isalhg.core.algorithms.base import H2SAlgorithm
from isalhg.core.algorithms.registry import register_algorithm
from isalhg.core.hypergraph_to_string import _python_greedy_h2s
from isalhg.core.instructions import sequence_sort_key
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.structural_tuples import DEFAULT_DEPTH, max_neighbor_degree_nodes
from isalhg.errors import DisconnectedHypergraphError
from isalhg.types import TokenSequence


class CanonicalEncoder(H2SAlgorithm):
    """Tie-complete greedy H2S from every neighbour-degree seed; lex-min result.

    Parameters
    ----------
    k : int
        VM pointer count; must be >= max hyperedge arity.
    structural_depth : int, optional
        Structural-tuple depth (not used by the encoder itself but required
        by the :class:`H2SAlgorithm` interface). Defaults to
        :data:`DEFAULT_DEPTH`.
    max_expansions : int or None, optional
        Maximum number of V-branch expansions across the entire search tree.
        ``None`` (default) means unlimited. When exceeded,
        :class:`isalhg.errors.CanonicalizationTimeoutError` is raised. Useful
        to bound the exponential worst-case on eta-degenerate designs.
    """

    def __init__(
        self,
        *,
        k: int,
        structural_depth: int = DEFAULT_DEPTH,
        max_expansions: int | None = None,
    ) -> None:
        self._k = k
        self._structural_depth = structural_depth
        self._max_expansions = max_expansions

    @property
    def name(self) -> str:
        return "canonical"

    @property
    def k(self) -> int:
        return self._k

    @property
    def structural_depth(self) -> int:
        return self._structural_depth

    def encode(self, H: SparseHypergraph) -> TokenSequence:
        if H.n_nodes == 0:
            return ()
        if not H.is_connected():
            raise DisconnectedHypergraphError(
                "CanonicalEncoder requires a connected hypergraph (decision B11)"
            )
        seeds = max_neighbor_degree_nodes(H)
        candidates: list[TokenSequence] = [
            _python_greedy_h2s(
                H,
                seed_node=s,
                k=self._k,
                inplace=True,
                tie_branch=True,
                max_expansions=self._max_expansions,
            )
            for s in seeds
        ]
        return min(candidates, key=sequence_sort_key)


register_algorithm(
    "canonical",
    lambda k, d: CanonicalEncoder(k=k, structural_depth=d),
)
