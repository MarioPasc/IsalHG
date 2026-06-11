"""Unit tests for :class:`isalhg.adapters.xgi_adapter.XGIAdapter`."""

from __future__ import annotations

import pytest

xgi = pytest.importorskip("xgi")

from isalhg.adapters.xgi_adapter import XGIAdapter
from isalhg.core.sparse_hypergraph import SparseHypergraph

pytestmark = pytest.mark.unit


def _arity_multiset(H: SparseHypergraph) -> list[int]:
    return sorted(len(H.members(e)) for e in H.edges())


class TestFromExternal:
    def test_round_trip_via_xgi(self, fano_plane: SparseHypergraph) -> None:
        adapter = XGIAdapter()
        external = adapter.to_external(fano_plane)
        re_imported = adapter.from_external(external)
        assert re_imported.n_nodes == fano_plane.n_nodes
        assert re_imported.n_edges == fano_plane.n_edges
        assert _arity_multiset(re_imported) == _arity_multiset(fano_plane)

    def test_string_node_ids(self) -> None:
        h = xgi.Hypergraph([["a", "b", "c"], ["b", "c", "d"]])
        adapter = XGIAdapter()
        H = adapter.from_external(h)
        assert H.n_nodes == 4
        assert H.n_edges == 2
        assert _arity_multiset(H) == [3, 3]


class TestToExternal:
    def test_xgi_dimensions(self, single_edge_hypergraph: SparseHypergraph) -> None:
        adapter = XGIAdapter()
        h = adapter.to_external(single_edge_hypergraph)
        assert h.num_nodes == 3
        assert h.num_edges == 1
