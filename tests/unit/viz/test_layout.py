"""Unit tests for :mod:`isalhg.viz.layout`."""

from __future__ import annotations

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.viz.layout import cdll_ring_positions, compact_primal_layout

pytestmark = pytest.mark.unit

pytest.importorskip("networkx")


class TestCDLLRing:
    def test_empty(self) -> None:
        assert cdll_ring_positions(()) == {}

    def test_single(self) -> None:
        assert cdll_ring_positions((7,)) == {7: (0.0, 0.0)}

    def test_three_on_unit_circle(self) -> None:
        pos = cdll_ring_positions((0, 1, 2), radius=1.0)
        for x, y in pos.values():
            assert abs(x * x + y * y - 1.0) < 1e-9


class TestCompactPrimalLayout:
    def test_covers_every_vertex(self) -> None:
        H = SparseHypergraph(
            n_nodes=5,
            hyperedges=[
                frozenset({0, 1, 2}),
                frozenset({2, 3, 4}),
            ],
        )
        pos = compact_primal_layout(H, seed=0)
        assert set(pos.keys()) == set(H.nodes())
        # Connected: all vertices land inside the normalised box.
        for x, y in pos.values():
            assert -1.05 <= x <= 1.05
            assert -1.05 <= y <= 1.05

    def test_isolated_vertex_pulled_in(self) -> None:
        # Vertex 4 is isolated (no hyperedge touches it).
        H = SparseHypergraph(
            n_nodes=5,
            hyperedges=[
                frozenset({0, 1, 2}),
                frozenset({1, 2, 3}),
            ],
        )
        pos = compact_primal_layout(H, seed=0, margin=0.2)
        x, _ = pos[4]
        # Stray must sit *just outside* the [-1, 1] main box at x = 1 + margin
        # (NOT far away as the backend auto-layouts would place it).
        assert abs(x - 1.2) < 1e-9, f"stray at x={x}, expected ~1.2"

    def test_two_isolated_vertices_stacked(self) -> None:
        H = SparseHypergraph(
            n_nodes=6,
            hyperedges=[
                frozenset({0, 1, 2}),
                frozenset({1, 2, 3}),
            ],
        )
        pos = compact_primal_layout(H, seed=0, margin=0.2)
        # Strays 4 and 5 stack vertically at the same x.
        assert abs(pos[4][0] - pos[5][0]) < 1e-9
        assert pos[4][1] != pos[5][1]

    def test_no_edges_falls_back_to_ring(self) -> None:
        H = SparseHypergraph(n_nodes=4, hyperedges=[])
        pos = compact_primal_layout(H, seed=0)
        # Ring layout: all on the unit circle.
        for x, y in pos.values():
            assert abs(x * x + y * y - 1.0) < 1e-9
