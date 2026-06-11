"""HypergraphX adapter.

Bridges :class:`hypergraphx.Hypergraph` and :class:`SparseHypergraph`.
HypergraphX is imported lazily inside method bodies.
"""

from __future__ import annotations

from typing import Any

from isalhg.adapters.base import HypergraphAdapter
from isalhg.core.sparse_hypergraph import SparseHypergraph


class HypergraphXAdapter(HypergraphAdapter[Any]):
    """HypergraphX bridge."""

    @property
    def name(self) -> str:
        return "hypergraphx"

    def from_external(self, obj: Any) -> SparseHypergraph:
        raise NotImplementedError

    def to_external(self, H: SparseHypergraph) -> Any:
        raise NotImplementedError
