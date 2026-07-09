"""``greedy_min`` with both in-place mutation and WL branch pruning.

Composition of the two optimisations in
:mod:`~isalhg.core.algorithms.greedy_min_inplace` and
:mod:`~isalhg.core.algorithms.greedy_min_wl_pruned`.

Like its non-inplace twin, it filters the max-xi seed set by the iso-invariant
argmin WL colour (admissible, keeps the whole class) and does **not** pass WL
colours into the V-branch permutation loop. It inherits greedy's raw-edge-id
V-tie-break, so it is invariant under vertex relabelling but depends on the
hyperedge insertion order: a speed heuristic, not a canonical form. Only
``canonical`` is.
"""

from __future__ import annotations

from isalhg.core.algorithms.base import H2SAlgorithm
from isalhg.core.algorithms.greedy_min_wl_pruned import _wl_filtered_seeds
from isalhg.core.algorithms.registry import register_algorithm
from isalhg.core.hypergraph_to_string import greedy_h2s
from isalhg.core.hypergraph_wl import wl_hash
from isalhg.core.instructions import sequence_sort_key
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.structural_tuples import DEFAULT_DEPTH, max_xi_nodes
from isalhg.errors import DisconnectedHypergraphError
from isalhg.types import TokenSequence


class GreedyMinInplaceWLPruned(H2SAlgorithm):
    """``greedy_min`` with a WL-filtered seed set and in-place state mutation."""

    def __init__(self, *, k: int, structural_depth: int = DEFAULT_DEPTH) -> None:
        self._k = k
        self._structural_depth = structural_depth

    @property
    def name(self) -> str:
        return "greedy_min_inplace_wl_pruned"

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
                "GreedyMinInplaceWLPruned requires a connected hypergraph (decision B11)"
            )
        seeds = max_xi_nodes(H, depth=self._structural_depth)
        colours = wl_hash(H)
        seeds = _wl_filtered_seeds(H, seeds, colours)
        candidates: list[TokenSequence] = [
            greedy_h2s(H, seed_node=s, k=self._k, inplace=True) for s in seeds
        ]
        return min(candidates, key=sequence_sort_key)


register_algorithm(
    "greedy_min_inplace_wl_pruned",
    lambda k, d: GreedyMinInplaceWLPruned(k=k, structural_depth=d),
)
