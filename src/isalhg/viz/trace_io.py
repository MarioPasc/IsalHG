"""Trace reconstruction for the visualisation layer.

Reads a JSON trace dumped by :func:`isalhg.core.trace.dump_trace` and
re-hydrates the final :class:`SparseHypergraph` (so callers do not have
to re-run the algorithm to obtain the drawing target).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.trace import AlgorithmTrace, load_trace


def hypergraph_from_hif(hif: dict[str, Any]) -> SparseHypergraph:
    """Reconstruct a :class:`SparseHypergraph` from a HIF v0.1 dict.

    Reads ``metadata.n_vertex_labels`` and ``metadata.n_edge_labels``
    (defaulting to ``1`` if absent) so the canonical-algorithm-side
    contract is preserved end-to-end.
    """
    meta = hif.get("metadata", {})
    n_vertex_labels = int(meta.get("n_vertex_labels", 1))
    n_edge_labels = int(meta.get("n_edge_labels", 1))
    nodes_entries = hif.get("nodes", [])
    edges_entries = hif.get("edges", [])
    incidences = hif.get("incidences", [])

    n_nodes = len(nodes_entries)
    vertex_labels: list[int] = [0] * n_nodes
    node_pos: dict[int, int] = {}
    for slot, entry in enumerate(nodes_entries):
        node_id = int(entry["node"])
        attrs = entry.get("attrs", {})
        node_pos[node_id] = slot
        vertex_labels[slot] = int(attrs.get("label", 0))

    edge_members: dict[int, set[int]] = {}
    edge_labels_map: dict[int, int] = {}
    for entry in edges_entries:
        eid = int(entry["edge"])
        attrs = entry.get("attrs", {})
        edge_labels_map[eid] = int(attrs.get("label", 0))
        edge_members.setdefault(eid, set())
    for inc in incidences:
        eid = int(inc["edge"])
        nid = int(inc["node"])
        edge_members.setdefault(eid, set()).add(node_pos[nid])

    sorted_edge_ids = sorted(edge_members.keys())
    hyperedges = [frozenset(edge_members[e]) for e in sorted_edge_ids]
    edge_labels = [edge_labels_map.get(e, 0) for e in sorted_edge_ids]

    return SparseHypergraph(
        n_nodes=n_nodes,
        hyperedges=hyperedges,
        n_vertex_labels=n_vertex_labels,
        n_edge_labels=n_edge_labels,
        vertex_labels=vertex_labels,
        edge_labels=edge_labels,
    )


def load_trace_for_viz(path: str | Path) -> tuple[AlgorithmTrace, SparseHypergraph]:
    """Load ``path`` and return both the trace and the reconstructed final hypergraph."""
    trace = load_trace(path)
    H = hypergraph_from_hif(trace.final_hif)
    return trace, H
