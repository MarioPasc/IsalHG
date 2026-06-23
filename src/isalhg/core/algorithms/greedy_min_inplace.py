"""``greedy_min`` with in-place mutation + undo at branch points.

Same canonical output as :class:`~isalhg.core.algorithms.greedy_min.GreedyMin`
by construction: only the per-branch state-management strategy differs.
The clone-based variant copies the full ``_State`` (including the
``O(n)`` CDLL) at every V/C branch; this variant mutates the state
forward, recurses, and undoes the mutation on return.

Optimisation imported from IsalSR's canonical-string implementation
(``IsalSR/src/isalsr/core/canonical.py::_step`` undo block,
lines 537--542 in the IsalSR repository at the time of porting). The
reduction is from ``O(j * n)`` per V step to ``O(j)`` per V step.
"""

from __future__ import annotations

from isalhg.core.algorithms.base import H2SAlgorithm
from isalhg.core.algorithms.registry import register_algorithm
from isalhg.core.hypergraph_to_string import greedy_h2s
from isalhg.core.instructions import sequence_sort_key
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.structural_tuples import DEFAULT_DEPTH, max_xi_nodes
from isalhg.errors import DisconnectedHypergraphError
from isalhg.types import TokenSequence


class GreedyMinInplace(H2SAlgorithm):
    """``greedy_min`` with in-place mutation + undo at V/C branches."""

    def __init__(self, *, k: int, structural_depth: int = DEFAULT_DEPTH) -> None:
        self._k = k
        self._structural_depth = structural_depth

    @property
    def name(self) -> str:
        return "greedy_min_inplace"

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
                "GreedyMinInplace requires a connected hypergraph (decision B11)"
            )
        seeds = max_xi_nodes(H, depth=self._structural_depth)
        candidates: list[TokenSequence] = [
            greedy_h2s(H, seed_node=s, k=self._k, inplace=True) for s in seeds
        ]
        return min(candidates, key=sequence_sort_key)


register_algorithm(
    "greedy_min_inplace",
    lambda k, d: GreedyMinInplace(k=k, structural_depth=d),
)
