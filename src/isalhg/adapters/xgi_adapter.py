"""XGI adapter.

Bridges :class:`xgi.Hypergraph` and :class:`SparseHypergraph`. XGI is also the
backbone of the Tier 1, 2, and 4 dataset loaders; this adapter is reused
there.
"""

from __future__ import annotations

from typing import Any

from isalhg.adapters.base import HypergraphAdapter
from isalhg.core.sparse_hypergraph import SparseHypergraph


class XGIAdapter(HypergraphAdapter[Any]):
    """XGI bridge."""

    @property
    def name(self) -> str:
        return "xgi"

    def from_external(self, obj: Any) -> SparseHypergraph:
        raise NotImplementedError

    def to_external(self, H: SparseHypergraph) -> Any:
        raise NotImplementedError
