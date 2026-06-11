"""Shared pytest fixtures.

Canonical small hypergraph examples used across unit, integration, and
property tests. All fixtures use the trivial label vocabulary (one
vertex label, one edge label) -- decision I45's
``LabelVocabulary(("⊥",), ("⊥",))``.
"""

from __future__ import annotations

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph, permute


@pytest.fixture
def trivial_hypergraph() -> SparseHypergraph:
    """One vertex, no hyperedges."""
    return SparseHypergraph(n_nodes=1)


@pytest.fixture
def single_edge_hypergraph() -> SparseHypergraph:
    """Three vertices, one hyperedge ``{0, 1, 2}``."""
    return SparseHypergraph(n_nodes=3, hyperedges=[frozenset({0, 1, 2})])


@pytest.fixture
def fano_plane() -> SparseHypergraph:
    """Fano plane STS(7), the classical 3-uniform symmetric design.

    Lines of PG(2, 2):
        {0,1,2}, {0,3,4}, {0,5,6}, {1,3,5}, {1,4,6}, {2,3,6}, {2,4,5}.
    Each pair of points lies in exactly one line; vertex-transitive
    automorphism group ``PGL(3, 2)`` of order 168.
    """
    lines = [
        frozenset({0, 1, 2}),
        frozenset({0, 3, 4}),
        frozenset({0, 5, 6}),
        frozenset({1, 3, 5}),
        frozenset({1, 4, 6}),
        frozenset({2, 3, 6}),
        frozenset({2, 4, 5}),
    ]
    return SparseHypergraph(n_nodes=7, hyperedges=lines)


@pytest.fixture
def sts_9() -> SparseHypergraph:
    """The unique Steiner Triple System STS(9), realised as AG(2, 3).

    9 points arranged as a 3x3 affine plane; 12 blocks (rows, columns,
    main and anti-diagonal classes).
    """
    blocks = [
        # Rows
        frozenset({0, 1, 2}),
        frozenset({3, 4, 5}),
        frozenset({6, 7, 8}),
        # Columns
        frozenset({0, 3, 6}),
        frozenset({1, 4, 7}),
        frozenset({2, 5, 8}),
        # Main diagonals (3 parallel classes)
        frozenset({0, 4, 8}),
        frozenset({1, 5, 6}),
        frozenset({2, 3, 7}),
        # Anti-diagonals
        frozenset({0, 5, 7}),
        frozenset({1, 3, 8}),
        frozenset({2, 4, 6}),
    ]
    return SparseHypergraph(n_nodes=9, hyperedges=blocks)


@pytest.fixture
def iso_pair_small() -> tuple[SparseHypergraph, SparseHypergraph, list[int]]:
    """A pair ``(H1, H2, sigma)`` with ``H2 = permute(H1, sigma)``.

    H1 has 4 vertices and two hyperedges sharing a 2-element subset.
    sigma is a non-identity permutation.
    """
    h1 = SparseHypergraph(
        n_nodes=4,
        hyperedges=[frozenset({0, 1, 2}), frozenset({0, 1, 3})],
    )
    sigma = [3, 2, 1, 0]  # vertex i -> sigma[i]
    h2 = permute(h1, sigma)
    return h1, h2, sigma


@pytest.fixture
def non_iso_pair_small() -> tuple[SparseHypergraph, SparseHypergraph]:
    """A pair of 4-vertex hypergraphs with non-equal edge-arity multisets.

    H1 has two 3-edges sharing a pair; H2 has three 2-edges forming a path.
    They have matching degree-multisets ``(1, 1, 2, 2)`` but distinct
    arity profiles (``{3, 3}`` vs ``{2, 2, 2}``) -- trivially non-iso.
    """
    h1 = SparseHypergraph(
        n_nodes=4,
        hyperedges=[frozenset({0, 1, 2}), frozenset({0, 1, 3})],
    )
    h2 = SparseHypergraph(
        n_nodes=4,
        hyperedges=[frozenset({0, 1}), frozenset({1, 2}), frozenset({2, 3})],
    )
    return h1, h2
