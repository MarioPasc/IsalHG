"""``greedy_min`` with Weisfeiler--Leman seed-set pruning.

Identical to :class:`~isalhg.core.algorithms.greedy_min.GreedyMin` except
that the max-xi seed set is intersected with the smallest stable WL
colour class within it. The intersection is iso-equivariant: two
isomorphic hypergraphs map their (max-xi -> WL-min) seed sets onto
each other under the isomorphism, so the lex-min over the completions
is iso-invariant.

Speedup. On graphs where the max-xi seed set is large (many
high-symmetry nodes) but breaks up into several WL orbits, this
variant skips entire orbits whose WL colour is not lex-min. On
vertex-transitive designs (Fano, STS, GQ) every vertex shares the
same WL colour, so the WL filter is a no-op -- the preprint reports
this no-speedup region explicitly.

V-branch pruning. Pruning the inner ``_label_respecting_perms`` loop
by WL orbit is NOT iso-invariant in general (the canonical
"within-orbit" tie-break would have to be iso-invariant; vertex IDs
are not), so this variant does NOT pass WL colours to
:func:`greedy_h2s`. Only the seed set is filtered.
"""

from __future__ import annotations

from isalhg.core.algorithms.base import H2SAlgorithm
from isalhg.core.algorithms.registry import register_algorithm
from isalhg.core.hypergraph_to_string import greedy_h2s
from isalhg.core.hypergraph_wl import wl_hash
from isalhg.core.instructions import sequence_sort_key
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.structural_tuples import DEFAULT_DEPTH, max_xi_nodes
from isalhg.errors import DisconnectedHypergraphError
from isalhg.types import NodeId, TokenSequence


def _wl_filtered_seeds(
    H: SparseHypergraph,
    seeds: tuple[NodeId, ...],
    colours: list[int],
) -> tuple[NodeId, ...]:
    """Return the seeds whose WL colour is lex-minimum among ``seeds``."""
    if not seeds:
        return ()
    min_colour_key = min(colours[s] for s in seeds)
    return tuple(s for s in seeds if colours[s] == min_colour_key)


class GreedyMinWLPruned(H2SAlgorithm):
    """``greedy_min`` with WL filter on seeds and on V-branch permutations."""

    def __init__(self, *, k: int, structural_depth: int = DEFAULT_DEPTH) -> None:
        self._k = k
        self._structural_depth = structural_depth

    @property
    def name(self) -> str:
        return "greedy_min_wl_pruned"

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
                "GreedyMinWLPruned requires a connected hypergraph (decision B11)"
            )
        seeds = max_xi_nodes(H, depth=self._structural_depth)
        colours = wl_hash(H)
        seeds = _wl_filtered_seeds(H, seeds, colours)
        candidates: list[TokenSequence] = [greedy_h2s(H, seed_node=s, k=self._k) for s in seeds]
        return min(candidates, key=sequence_sort_key)


register_algorithm(
    "greedy_min_wl_pruned",
    lambda k, d: GreedyMinWLPruned(k=k, structural_depth=d),
)
