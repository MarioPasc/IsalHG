"""Algorithm trace recording for IsalHG.

A ``StepSnapshot`` captures the VM state after one ``Sigma_HG`` token has
been processed: which node IDs sit in the CDLL ring (in forward circular
order), which node IDs the ``k`` pointers carry, which vertices and which
hyperedges are currently materialised in ``H``, and the partial token
string emitted so far. An ``AlgorithmTrace`` is the ordered sequence of
snapshots for one algorithm run (either ``"s2h"`` direction, produced by
:class:`StringToHypergraph`, or ``"h2s"`` direction, produced by
replaying a canonical string through S2H).

The on-disk format is JSON. The hypergraph payload is encoded in the
Hypergraph Interchange Format (HIF v0.1, https://github.com/pszufe/HIF-standard);
the per-snapshot "is this node / edge currently visible?" flag is carried
in ``attrs.grayed`` on each HIF entry at load time
(``isalhg.viz.trace_io``). The dump path stays stdlib-only.

Restriction: Python stdlib only. No numpy, no xgi, no matplotlib.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.types import EdgeId, NodeId

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StepSnapshot:
    """State of the VM after one ``Sigma_HG`` step.

    Parameters
    ----------
    step_idx : int
        ``0`` for the initial state (no token yet processed); ``i`` for the
        state immediately after consuming token ``tokens[i - 1]``.
    token : str | None
        Serialised form of the token that produced this state. ``None`` for
        the initial state (``step_idx == 0``).
    token_kind : str | None
        ``"V" / "C" / "P" / "N" / "W"`` or ``None`` (initial state).
    cdll_node_order : tuple[NodeId, ...]
        Node IDs in forward circular order starting at the CDLL head.
    pointer_node_values : tuple[NodeId, ...]
        Node ID carried by each of the ``k`` pointers (``p_1, ..., p_k``).
    active_nodes : tuple[NodeId, ...]
        Sorted tuple of node IDs present in the hypergraph at this step.
    active_edges : tuple[EdgeId, ...]
        Sorted tuple of edge IDs present in the hypergraph at this step.
    partial_string : str
        Serialised token sequence consumed so far (``";"``-joined).
    """

    step_idx: int
    token: str | None
    token_kind: str | None
    cdll_node_order: tuple[NodeId, ...]
    pointer_node_values: tuple[NodeId, ...]
    active_nodes: tuple[NodeId, ...]
    active_edges: tuple[EdgeId, ...]
    partial_string: str

    def to_json(self) -> dict[str, Any]:
        return {
            "step_idx": self.step_idx,
            "token": self.token,
            "token_kind": self.token_kind,
            "cdll_node_order": list(self.cdll_node_order),
            "pointer_node_values": list(self.pointer_node_values),
            "active_nodes": list(self.active_nodes),
            "active_edges": list(self.active_edges),
            "partial_string": self.partial_string,
        }

    @classmethod
    def from_json(cls, obj: dict[str, Any]) -> StepSnapshot:
        return cls(
            step_idx=int(obj["step_idx"]),
            token=obj["token"],
            token_kind=obj["token_kind"],
            cdll_node_order=tuple(int(v) for v in obj["cdll_node_order"]),
            pointer_node_values=tuple(int(v) for v in obj["pointer_node_values"]),
            active_nodes=tuple(int(v) for v in obj["active_nodes"]),
            active_edges=tuple(int(v) for v in obj["active_edges"]),
            partial_string=str(obj["partial_string"]),
        )


@dataclass(frozen=True)
class AlgorithmTrace:
    """Ordered snapshots for one S2H or H2S run.

    Parameters
    ----------
    direction : str
        ``"s2h"`` or ``"h2s"``. Distinguishes the framing in the
        visualisation layer; the snapshot content is identical for both
        directions of the round trip.
    k : int
        Pointer count of the VM.
    n_vertex_labels, n_edge_labels : int
        Vocabulary sizes (decision I45).
    final_hif : dict
        HIF v0.1 dict of the final hypergraph. Hand-built; no xgi import.
    snapshots : tuple[StepSnapshot, ...]
        The trace itself. Length is ``len(tokens) + 1`` (one initial state +
        one snapshot per token).
    """

    direction: str
    k: int
    n_vertex_labels: int
    n_edge_labels: int
    final_hif: dict[str, Any]
    snapshots: tuple[StepSnapshot, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.direction not in ("s2h", "h2s"):
            raise ValueError(f"direction must be 's2h' or 'h2s', got {self.direction!r}")

    def to_json(self) -> dict[str, Any]:
        return {
            "schema": "isalhg.trace.v1",
            "direction": self.direction,
            "k": self.k,
            "n_vertex_labels": self.n_vertex_labels,
            "n_edge_labels": self.n_edge_labels,
            "final_hif": self.final_hif,
            "snapshots": [s.to_json() for s in self.snapshots],
        }

    @classmethod
    def from_json(cls, obj: dict[str, Any]) -> AlgorithmTrace:
        return cls(
            direction=str(obj["direction"]),
            k=int(obj["k"]),
            n_vertex_labels=int(obj["n_vertex_labels"]),
            n_edge_labels=int(obj["n_edge_labels"]),
            final_hif=dict(obj["final_hif"]),
            snapshots=tuple(StepSnapshot.from_json(s) for s in obj["snapshots"]),
        )


# ---------------------------------------------------------------------------
# HIF (Hypergraph Interchange Format) builder — hand-built, stdlib-only
# ---------------------------------------------------------------------------


def hypergraph_to_hif(H: SparseHypergraph) -> dict[str, Any]:
    """Serialise ``H`` to a HIF v0.1 dict.

    Per-node and per-edge ``attrs.label`` carry the integer label IDs;
    semantic label strings live in the dataset layer and are not embedded
    here. ``attrs.grayed`` is left unset; the viz layer sets it at load
    time according to each snapshot's active sets.

    Returns
    -------
    dict
        Mapping with the keys ``"network-type"``, ``"metadata"``,
        ``"nodes"``, ``"edges"``, ``"incidences"``.
    """
    return {
        "network-type": "undirected",
        "metadata": {
            "n_vertex_labels": int(H.n_vertex_labels),
            "n_edge_labels": int(H.n_edge_labels),
            "n_nodes": int(H.n_nodes),
            "n_edges": int(H.n_edges),
        },
        "nodes": [{"node": int(v), "attrs": {"label": int(H.vertex_label(v))}} for v in H.nodes()],
        "edges": [{"edge": int(e), "attrs": {"label": int(H.edge_label(e))}} for e in H.edges()],
        "incidences": [
            {"node": int(v), "edge": int(e)} for e in H.edges() for v in sorted(H.members(e))
        ],
    }


# ---------------------------------------------------------------------------
# Snapshot builders
# ---------------------------------------------------------------------------


def initial_snapshot(
    H: SparseHypergraph,
    cdll_node_order: tuple[NodeId, ...],
    pointer_node_values: tuple[NodeId, ...],
) -> StepSnapshot:
    """Build the ``step_idx=0`` snapshot for an S2H run."""
    return StepSnapshot(
        step_idx=0,
        token=None,
        token_kind=None,
        cdll_node_order=cdll_node_order,
        pointer_node_values=pointer_node_values,
        active_nodes=tuple(sorted(H.nodes())),
        active_edges=tuple(sorted(H.edges())),
        partial_string="",
    )


def post_step_snapshot(
    *,
    step_idx: int,
    token_serialised: str,
    token_kind: str,
    H: SparseHypergraph,
    cdll_node_order: tuple[NodeId, ...],
    pointer_node_values: tuple[NodeId, ...],
    partial_string: str,
) -> StepSnapshot:
    """Build a snapshot for the state after token ``step_idx - 1`` has been processed."""
    return StepSnapshot(
        step_idx=step_idx,
        token=token_serialised,
        token_kind=token_kind,
        cdll_node_order=cdll_node_order,
        pointer_node_values=pointer_node_values,
        active_nodes=tuple(sorted(H.nodes())),
        active_edges=tuple(sorted(H.edges())),
        partial_string=partial_string,
    )


# ---------------------------------------------------------------------------
# JSON I/O
# ---------------------------------------------------------------------------


def dump_trace(trace: AlgorithmTrace, path: str | Path) -> None:
    """Write ``trace`` to ``path`` as JSON (UTF-8, ``indent=2``)."""
    Path(path).write_text(json.dumps(trace.to_json(), indent=2), encoding="utf-8")


def load_trace(path: str | Path) -> AlgorithmTrace:
    """Read an :class:`AlgorithmTrace` previously written by :func:`dump_trace`."""
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    return AlgorithmTrace.from_json(obj)


__all__ = [
    "AlgorithmTrace",
    "StepSnapshot",
    "dump_trace",
    "hypergraph_to_hif",
    "initial_snapshot",
    "load_trace",
    "post_step_snapshot",
]


# Silence the unused-import warning from `asdict` -- kept on hand for
# downstream debugging tools but not used in to_json paths.
_ = asdict
