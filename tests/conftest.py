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


def _cyclic_sts_13(base: tuple[int, int, int]) -> SparseHypergraph:
    """Build an STS(13) via the cyclic difference-set construction.

    Each block is the rotate ``{(b + i) mod 13 : b in base}`` for
    ``i in 0..12``. Two STS(13) variants exist up to isomorphism; the
    full classification is due to Heinlein 2023 (arXiv:2303.01207).
    """
    n = 13
    edges = [frozenset((b + i) % n for b in base) for i in range(n)]
    return SparseHypergraph(n_nodes=n, hyperedges=edges)


@pytest.fixture
def sts_13_pair() -> tuple[SparseHypergraph, SparseHypergraph]:
    """The two non-isomorphic STS(13).

    First system: cyclic on base ``{0, 1, 4}`` (Bose 1939).
    Second system: cyclic on base ``{0, 1, 6}`` — a starter inequivalent
    to ``{0, 1, 4}`` under PGL action on Z/13Z. The complete STS(13)
    classification (Heinlein 2023) reports exactly two iso-classes; the
    Phase 3 closing check verifies non-isomorphism empirically against
    pynauty.
    """
    return _cyclic_sts_13((0, 1, 4)), _cyclic_sts_13((0, 1, 6))


@pytest.fixture
def gq_2_2_doily() -> SparseHypergraph:
    """Generalised quadrangle GQ(2, 2) — the "doily".

    15 points, 15 lines, automorphism group of order 720. Standard
    symplectic realisation W(2) over GF(2) (Payne & Thas, *Finite
    Generalized Quadrangles*, §1.2).
    """
    edges = [
        frozenset({0, 1, 2}),
        frozenset({0, 3, 4}),
        frozenset({0, 5, 6}),
        frozenset({1, 3, 7}),
        frozenset({1, 5, 8}),
        frozenset({2, 4, 9}),
        frozenset({2, 6, 10}),
        frozenset({3, 8, 11}),
        frozenset({4, 7, 12}),
        frozenset({5, 10, 13}),
        frozenset({6, 9, 14}),
        frozenset({7, 11, 13}),
        frozenset({8, 12, 14}),
        frozenset({9, 11, 12}),
        frozenset({10, 13, 14}),
    ]
    return SparseHypergraph(n_nodes=15, hyperedges=edges)
