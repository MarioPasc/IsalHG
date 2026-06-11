"""H2S greedy encoder.

Greedy traversal of the input hypergraph that emits the ``Sigma_HG*`` string
which, under :func:`string_to_hypergraph`, reproduces an isomorphic
hypergraph. The tie-breaking cascade (sum of pointer deltas, ``V`` over
``C``, ``(i, j)`` lex, eta tuple lex) is mandatory -- see CLAUDE.md
"Critical Invariants" for the rationale.
"""

from __future__ import annotations

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.types import NodeId


def hypergraph_to_string(
    H: SparseHypergraph,
    *,
    seed_node: NodeId,
    k: int,
) -> str:
    """Greedy encode ``H`` starting at ``seed_node``.

    Parameters
    ----------
    H : SparseHypergraph
        Connected hypergraph to encode.
    seed_node : NodeId
        First node placed at slot 0 of the CDLL. The canonical wrapper
        chooses this via the max-xi rule.
    k : int
        Pointer count of the VM (= maximum hyperedge arity).

    Returns
    -------
    str
        Instruction string over ``Sigma_HG``.
    """
    raise NotImplementedError
