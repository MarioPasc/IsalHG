"""Bliss-Levi backend round-trip: fingerprint stability and partition agreement.

Mirrors :mod:`tests.integration.test_pynauty_roundtrip`. ``python-igraph``
is required (skipped otherwise).
"""

from __future__ import annotations

import pytest

igraph = pytest.importorskip("igraph")  # noqa: F841

from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.iso_backends.bliss_levi import BlissLeviBackend
from isalhg.iso_backends.isalhg_backend import IsalHGBackend
from isalhg.metrics.correctness import verify_bijection_certificate

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    "fixture_name",
    ["single_edge_hypergraph", "fano_plane", "sts_9"],
)
def test_bliss_fingerprint_invariant(fixture_name: str, request: pytest.FixtureRequest) -> None:
    H = request.getfixturevalue(fixture_name)
    backend = BlissLeviBackend()
    fp_h = backend.fingerprint(H)
    for seed in range(3):
        import random

        rng = random.Random(seed)
        sigma = list(range(H.n_nodes))
        rng.shuffle(sigma)
        H2 = permute(H, sigma)
        assert backend.fingerprint(H2) == fp_h


@pytest.mark.parametrize(
    "fixture_name",
    ["single_edge_hypergraph", "fano_plane", "sts_9"],
)
def test_partition_agreement_iso(fixture_name: str, request: pytest.FixtureRequest) -> None:
    H = request.getfixturevalue(fixture_name)
    H2 = permute(H, list(range(H.n_nodes - 1, -1, -1)))
    bliss = BlissLeviBackend()
    isalhg = IsalHGBackend()
    assert bliss.are_isomorphic(H, H2)
    assert isalhg.are_isomorphic(H, H2)


def test_partition_agreement_non_iso(
    non_iso_pair_small: tuple[SparseHypergraph, SparseHypergraph],
) -> None:
    h1, h2 = non_iso_pair_small
    bliss = BlissLeviBackend()
    isalhg = IsalHGBackend()
    assert not bliss.are_isomorphic(h1, h2)
    assert not isalhg.are_isomorphic(h1, h2)


def test_bliss_bijection_certificate(
    iso_pair_small: tuple[SparseHypergraph, SparseHypergraph, list[int]],
) -> None:
    H1, H2, _sigma = iso_pair_small
    backend = BlissLeviBackend()
    bij = backend.bijection_certificate(H1, H2)
    assert bij is not None
    assert verify_bijection_certificate(H1, H2, bij)


def test_bliss_bijection_returns_none_on_non_iso(
    non_iso_pair_small: tuple[SparseHypergraph, SparseHypergraph],
) -> None:
    h1, h2 = non_iso_pair_small
    backend = BlissLeviBackend()
    assert backend.bijection_certificate(h1, h2) is None
