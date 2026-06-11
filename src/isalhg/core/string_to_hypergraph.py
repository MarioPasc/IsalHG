"""S2H interpreter.

Executes a ``Sigma_HG*`` string against the virtual machine
``S = (H, L, p_1, ..., p_k)`` and returns the resulting hypergraph.

Closed-alphabet invariant: every well-formed string decodes to a valid
hypergraph; the interpreter must not raise on alphabet-valid input.
"""

from __future__ import annotations

from isalhg.core.sparse_hypergraph import SparseHypergraph


def string_to_hypergraph(string: str, *, k: int) -> SparseHypergraph:
    """Execute ``string`` against an initial VM state and return the partial hypergraph.

    Parameters
    ----------
    string : str
        Instruction sequence over ``Sigma_HG``.
    k : int
        Maximum hyperedge arity supported (pointer count of the VM).

    Returns
    -------
    SparseHypergraph
        Final hypergraph state after executing every instruction.
    """
    raise NotImplementedError
