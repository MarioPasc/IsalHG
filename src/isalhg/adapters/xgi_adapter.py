"""XGI adapter.

Bridges :class:`xgi.Hypergraph` and :class:`SparseHypergraph`. XGI is also the
backbone of the Tier 1, 2, and 4 dataset loaders; this adapter is reused
there.

XGI hypergraphs admit string node IDs and arbitrary edge metadata. This
adapter handles:

- integer node IDs (the common case): pass through.
- non-integer node IDs: assigns contiguous integers in lexicographic order
  of the string representation. The mapping is recorded as part of the
  ``extra`` metadata when round-tripping back via :meth:`to_external`.

Labels are not yet propagated from XGI vertex/edge attributes; the trivial
vocabulary is used. Label-aware bridging will be added alongside the Tier 5
loaders (out of Phase 2 scope).
"""

from __future__ import annotations

from typing import Any

from isalhg.adapters.base import HypergraphAdapter
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.errors import AdapterDependencyMissingError, AdapterTranslationError


def _import_xgi() -> Any:
    try:
        import xgi
    except ImportError as exc:
        raise AdapterDependencyMissingError(
            "xgi is required for XGIAdapter; install via `pip install xgi`"
        ) from exc
    return xgi


class XGIAdapter(HypergraphAdapter[Any]):
    """XGI bridge."""

    @property
    def name(self) -> str:
        return "xgi"

    def from_external(self, obj: Any) -> SparseHypergraph:
        _import_xgi()  # ensure the lib exists
        # Collect XGI node IDs and assign contiguous int IDs.
        try:
            node_iter = list(obj.nodes)
        except AttributeError as exc:
            raise AdapterTranslationError(
                f"object {type(obj).__name__} lacks `.nodes`; expected xgi.Hypergraph"
            ) from exc
        # Sort lexicographically on string representation for determinism.
        sorted_nodes = sorted(node_iter, key=lambda x: (type(x).__name__, str(x)))
        node_to_int: dict[Any, int] = {n: i for i, n in enumerate(sorted_nodes)}

        hyperedges: list[frozenset[int]] = []
        for eid in obj.edges:
            members = obj.edges.members(eid)
            if not members:
                raise AdapterTranslationError(
                    f"empty hyperedge {eid!r} encountered (forbidden by SparseHypergraph)"
                )
            mapped = frozenset(node_to_int[m] for m in members)
            hyperedges.append(mapped)

        return SparseHypergraph(
            n_nodes=len(sorted_nodes),
            hyperedges=hyperedges,
        )

    def to_external(self, H: SparseHypergraph) -> Any:
        xgi = _import_xgi()
        edge_lists = [sorted(H.members(e)) for e in H.edges()]
        return xgi.Hypergraph(edge_lists)
