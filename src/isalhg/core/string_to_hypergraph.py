"""S2H interpreter.

Executes a ``Sigma_HG*`` token sequence against the virtual machine
``S = (H, L, p_1, ..., p_k)`` and returns the resulting hypergraph.

Closed-alphabet invariant: every well-formed string decodes to a valid
hypergraph; the interpreter must not raise on alphabet-valid input
(rejection happens earlier, in :func:`isalhg.core.instructions.validate`).

VM semantics (PROPOSAL.md "Virtual machine state"):

- Initial state: one vertex with label ``seed_label`` at slot ``0``; CDLL
  has one slot; all ``k`` pointers point to slot ``0``.
- ``V[le;i;j;ln1..lnj]``: insert ``j`` new vertices with labels
  ``ln1..lnj`` into the hypergraph; insert them in order as new CDLL slots
  *after slot ``p_1``*; add a hyperedge of arity ``i + j`` with label
  ``le`` over ``{cdll.get_value(p_1), ..., cdll.get_value(p_i),
  new_vertex_1, ..., new_vertex_j}``. Pointers do **not** move.
- ``C[le;i]``: add a hyperedge of arity ``i`` with label ``le`` over
  ``{cdll.get_value(p_1), ..., cdll.get_value(p_i)}``; no-op if such a
  hyperedge already exists.
- ``P[i]`` / ``N[i]``: advance / retreat pointer ``p_i``.
- ``W``: no-op.
"""

from __future__ import annotations

from collections.abc import Iterable

from isalhg.core.cdll import CircularDoublyLinkedList
from isalhg.core.instructions import (
    Token,
    TokenC,
    TokenN,
    TokenP,
    TokenV,
    TokenW,
    parse,
    serialize,
    validate,
)
from isalhg.core.pointers import KPointerSet
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.trace import (
    AlgorithmTrace,
    StepSnapshot,
    hypergraph_to_hif,
    initial_snapshot,
    post_step_snapshot,
)
from isalhg.types import NodeId

_TOKEN_KIND: dict[type, str] = {
    TokenW: "W",
    TokenN: "N",
    TokenP: "P",
    TokenV: "V",
    TokenC: "C",
}


def _kind_of(tok: Token) -> str:
    return _TOKEN_KIND[type(tok)]


def _capacity_for(tokens: Iterable[Token]) -> int:
    """Return ``1 + sum(j for V tokens)`` -- the maximum vertex count reachable."""
    cap = 1
    for tok in tokens:
        if isinstance(tok, TokenV):
            cap += tok.j
    return cap


class StringToHypergraph:
    """Stateful S2H interpreter.

    Parameters
    ----------
    tokens : list[Token]
        Pre-parsed token sequence. The constructor pre-allocates a CDLL
        large enough to hold every vertex that may be introduced.
    k : int
        Pointer count of the VM.
    n_vertex_labels, n_edge_labels : int, optional
        Vocabulary sizes (decision I45). Default ``1`` (trivial vocabulary).
    seed_label : int, optional
        Label of the initial vertex. Defaults to ``0``.
    """

    def __init__(
        self,
        tokens: list[Token] | tuple[Token, ...],
        *,
        k: int,
        n_vertex_labels: int = 1,
        n_edge_labels: int = 1,
        seed_label: int = 0,
    ) -> None:
        self._tokens: tuple[Token, ...] = tuple(tokens)
        self._k = k
        self._n_vertex_labels = n_vertex_labels
        self._n_edge_labels = n_edge_labels
        validate(
            list(self._tokens),
            k=k,
            n_vertex_labels=n_vertex_labels,
            n_edge_labels=n_edge_labels,
        )

        # Output hypergraph: starts with one vertex (the seed).
        self._H: SparseHypergraph = SparseHypergraph(
            n_nodes=0,
            n_vertex_labels=n_vertex_labels,
            n_edge_labels=n_edge_labels,
        )
        seed_id: NodeId = self._H.add_node(label=seed_label)

        # CDLL: pre-allocated to the worst-case vertex count.
        cap = _capacity_for(self._tokens)
        self._cdll = CircularDoublyLinkedList(capacity=cap)
        self._cdll.insert_after(0, seed_id)
        self._pointers = KPointerSet(self._cdll, k=k)

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def run(self, *, trace: bool = False) -> tuple[SparseHypergraph, list[str]]:
        """Execute every token in sequence and return ``(H, trace_lines)``.

        ``trace_lines`` is a per-token log when ``trace=True``; otherwise
        an empty list.
        """
        trace_log: list[str] = []
        for idx, tok in enumerate(self._tokens):
            self._step(tok)
            if trace:
                trace_log.append(
                    f"step {idx}: {tok.serialize()} -> "
                    f"n={self._H.n_nodes} m={self._H.n_edges} "
                    f"pointers={self._pointers.snapshot()}"
                )
        return self._H, trace_log

    def run_with_trace(
        self,
        *,
        direction: str = "s2h",
    ) -> tuple[SparseHypergraph, AlgorithmTrace]:
        """Execute every token and return the final hypergraph plus an :class:`AlgorithmTrace`.

        Parameters
        ----------
        direction : str, optional
            ``"s2h"`` (default) or ``"h2s"``. Labels the trace for the
            visualisation layer; the snapshot content is identical for
            either direction of the round trip.

        Returns
        -------
        (SparseHypergraph, AlgorithmTrace)
            The fully-decoded hypergraph and the ordered snapshot list.
            The trace contains ``len(tokens) + 1`` snapshots (one initial
            state followed by one snapshot per token).
        """
        snapshots: list[StepSnapshot] = [
            initial_snapshot(
                self._H,
                cdll_node_order=tuple(self._cdll.values()),
                pointer_node_values=self._current_pointer_values(),
            )
        ]
        emitted: list[Token] = []
        for idx, tok in enumerate(self._tokens):
            self._step(tok)
            emitted.append(tok)
            snapshots.append(
                post_step_snapshot(
                    step_idx=idx + 1,
                    token_serialised=tok.serialize(),
                    token_kind=_kind_of(tok),
                    H=self._H,
                    cdll_node_order=tuple(self._cdll.values()),
                    pointer_node_values=self._current_pointer_values(),
                    partial_string=serialize(emitted),
                )
            )
        trace = AlgorithmTrace(
            direction=direction,
            k=self._k,
            n_vertex_labels=self._n_vertex_labels,
            n_edge_labels=self._n_edge_labels,
            final_hif=hypergraph_to_hif(self._H),
            snapshots=tuple(snapshots),
        )
        return self._H, trace

    def _current_pointer_values(self) -> tuple[NodeId, ...]:
        """Return the node IDs each ``p_i`` currently points to."""
        return tuple(self._cdll.get_value(self._pointers.get(i)) for i in range(1, self._k + 1))

    def _step(self, tok: Token) -> None:
        if isinstance(tok, TokenW):
            return
        if isinstance(tok, TokenP):
            self._pointers.advance(tok.i)
            return
        if isinstance(tok, TokenN):
            self._pointers.retreat(tok.i)
            return
        if isinstance(tok, TokenC):
            members = [self._cdll.get_value(self._pointers.get(idx + 1)) for idx in range(tok.i)]
            self._H.add_hyperedge(members, label=tok.edge_label)
            return
        if isinstance(tok, TokenV):
            existing_members = [
                self._cdll.get_value(self._pointers.get(idx + 1)) for idx in range(tok.i)
            ]
            new_node_ids: list[NodeId] = []
            insert_after_slot = self._pointers.get(1)
            for new_label in tok.new_node_labels:
                v = self._H.add_node(label=new_label)
                new_slot = self._cdll.insert_after(insert_after_slot, v)
                new_node_ids.append(v)
                insert_after_slot = new_slot
            self._H.add_hyperedge(existing_members + new_node_ids, label=tok.edge_label)
            return
        raise TypeError(f"unknown token type: {type(tok)!r}")


# ---------------------------------------------------------------------------
# Convenience entry point
# ---------------------------------------------------------------------------


def string_to_hypergraph(
    string: str,
    *,
    k: int,
    n_vertex_labels: int = 1,
    n_edge_labels: int = 1,
    seed_label: int = 0,
) -> SparseHypergraph:
    """Parse ``string`` and run the resulting program on a fresh VM.

    Returns
    -------
    SparseHypergraph
        Final hypergraph state.
    """
    tokens = parse(string)
    interpreter = StringToHypergraph(
        tokens,
        k=k,
        n_vertex_labels=n_vertex_labels,
        n_edge_labels=n_edge_labels,
        seed_label=seed_label,
    )
    H, _ = interpreter.run(trace=False)
    return H
