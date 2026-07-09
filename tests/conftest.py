"""Shared pytest fixtures.

Canonical small hypergraph examples used across unit, integration, and
property tests. All fixtures use the trivial label vocabulary (one
vertex label, one edge label) -- decision I45's
``LabelVocabulary(("⊥",), ("⊥",))``.

The named designs are built by ``isalhg.datasets.synthetic.designs``, which
is the single source of truth for them; ``tests/unit/datasets/test_designs.py``
asserts their defining incidence axioms.
"""

from __future__ import annotations

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.datasets.synthetic import designs


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
    """Fano plane STS(7), the classical 3-uniform symmetric design."""
    return designs.fano_plane()


@pytest.fixture
def sts_9() -> SparseHypergraph:
    """The unique Steiner Triple System STS(9), realised as AG(2, 3)."""
    return designs.sts_9()


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


@pytest.fixture
def sts_13_pair() -> tuple[SparseHypergraph, SparseHypergraph]:
    """A non-isomorphic pair of cyclic triple systems on 13 points.

    Cyclic on the starters ``{0, 1, 4}`` and ``{0, 1, 6}``. Each is a single
    orbit of 13 blocks, so neither is an STS(13) despite the fixture name --
    see ``isalhg.datasets.synthetic.designs.cyclic_sts_13``. Non-isomorphism
    is verified empirically against pynauty by the Phase 3 closing check.
    """
    return designs.cyclic_sts_13((0, 1, 4)), designs.cyclic_sts_13((0, 1, 6))


@pytest.fixture
def gq_2_2_doily() -> SparseHypergraph:
    """Generalised quadrangle GQ(2, 2) -- the "doily"."""
    return designs.gq_2_2_doily()


@pytest.fixture
def qin_fig1_hypergraph() -> SparseHypergraph:
    """The labelled hypergraph of Qin et al. (ICDE 2023), Fig. 1.

    8 nodes ``u1..u8 -> 0..7``; vertex labels ``0`` = square (u1-u3),
    ``1`` = triangle (u4, u5), ``2`` = circle (u6-u8); edge labels
    ``0`` = orange, ``1`` = star/grey. Memberships read off Fig. 1(b)
    (visually verified 2026-07-08) and consistent with every textual
    anchor: ``NEI(u4)``/``NEI(u5)`` of Example 1, the ``E2`` deletion
    cost 4 of p. 248, Example 6's cardinality-sorted re-ranking, and
    ``HGED(EGO(u4), EGO(u5)) = 6`` of Examples 2/7.
    """
    return SparseHypergraph(
        n_nodes=8,
        hyperedges=[
            frozenset({0, 1, 3}),  # E1 = {u1, u2, u4}
            frozenset({3, 5, 6}),  # E2 = {u4, u6, u7}
            frozenset({1, 2, 4}),  # E3 = {u2, u3, u5}
            frozenset({3, 4, 6, 7}),  # E4 = {u4, u5, u7, u8}
        ],
        n_vertex_labels=3,
        n_edge_labels=2,
        vertex_labels=[0, 0, 0, 1, 1, 2, 2, 2],
        edge_labels=[0, 0, 1, 1],
    )
