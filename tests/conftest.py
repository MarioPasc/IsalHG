"""Shared pytest fixtures.

Canonical small hypergraph examples used across unit, integration, and
property tests. To be populated by the coding agent once
:class:`isalhg.core.sparse_hypergraph.SparseHypergraph` has a concrete
implementation.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def trivial_hypergraph() -> None:
    """One node, no hyperedges."""
    pytest.skip("not implemented yet")


@pytest.fixture
def fano_plane() -> None:
    """Fano plane STS(7); the canonical 3-uniform symmetric design."""
    pytest.skip("not implemented yet")


@pytest.fixture
def iso_pair_small() -> None:
    """A pair (H1, H2) with H1 ~ H2 by an explicit known permutation."""
    pytest.skip("not implemented yet")


@pytest.fixture
def non_iso_pair_small() -> None:
    """A pair (H1, H2) of the same degree sequence that are NOT isomorphic."""
    pytest.skip("not implemented yet")
