"""HyperNetX adapter.

Bridges :class:`hypernetx.Hypergraph` and :class:`SparseHypergraph`.
HyperNetX is imported lazily inside method bodies.
"""

from __future__ import annotations

from typing import Any

from isalhg.adapters.base import HypergraphAdapter
from isalhg.core.sparse_hypergraph import SparseHypergraph


class HyperNetXAdapter(HypergraphAdapter[Any]):
    """HyperNetX bridge."""

    @property
    def name(self) -> str:
        return "hypernetx"

    def from_external(self, obj: Any) -> SparseHypergraph:
        raise NotImplementedError

    def to_external(self, H: SparseHypergraph) -> Any:
        raise NotImplementedError
