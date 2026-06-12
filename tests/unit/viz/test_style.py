"""Tests for :mod:`isalhg.viz.style`."""

from __future__ import annotations

import re

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.viz.style import (
    build_edge_palette,
    build_vertex_palette,
    color_for_edge,
    color_for_vertex,
)

pytestmark = pytest.mark.unit

_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _fano() -> SparseHypergraph:
    return SparseHypergraph(
        n_nodes=7,
        hyperedges=[
            frozenset({0, 1, 2}),
            frozenset({0, 3, 4}),
            frozenset({0, 5, 6}),
            frozenset({1, 3, 5}),
            frozenset({1, 4, 6}),
            frozenset({2, 3, 6}),
            frozenset({2, 4, 5}),
        ],
    )


def test_vertex_palette_covers_every_node() -> None:
    H = _fano()
    palette = build_vertex_palette(H)
    assert set(palette.keys()) == set(H.nodes())
    for hex_color in palette.values():
        assert _HEX_RE.match(hex_color), f"not a hex colour: {hex_color}"


def test_edge_palette_covers_every_edge() -> None:
    H = _fano()
    palette = build_edge_palette(H)
    assert set(palette.keys()) == set(H.edges())
    for hex_color in palette.values():
        assert _HEX_RE.match(hex_color), f"not a hex colour: {hex_color}"


def test_color_lookup_deterministic() -> None:
    H = _fano()
    a = [color_for_vertex(v, H) for v in H.nodes()]
    b = [color_for_vertex(v, H) for v in H.nodes()]
    assert a == b
    c = [color_for_edge(e, H) for e in H.edges()]
    d = [color_for_edge(e, H) for e in H.edges()]
    assert c == d


def test_id_based_fallback_when_vocab_trivial() -> None:
    # Trivial vocab -> ID-based palette must still be valid hex.
    H = _fano()
    assert H.n_vertex_labels == 1
    assert H.n_edge_labels == 1
    palette_v = build_vertex_palette(H)
    palette_e = build_edge_palette(H)
    # Different IDs should generally yield different colours (not strictly
    # required, but the palette would be useless otherwise).
    assert len(set(palette_v.values())) >= H.n_nodes - 1
    assert len(set(palette_e.values())) >= H.n_edges - 1
