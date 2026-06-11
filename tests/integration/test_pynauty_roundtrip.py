"""End-to-end: SparseHypergraph -> PynautyLeviBackend.fingerprint.

Pynauty serves as the iso oracle. For every Phase 1 fixture, the
PynautyLeviBackend and the IsalHGBackend MUST induce the same partition
(i.e. agree on which inputs are iso). Phase 2's closing check.
"""

from __future__ import annotations

import random

import pytest

pynauty = pytest.importorskip("pynauty")

from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.iso_backends.isalhg_backend import IsalHGBackend
from isalhg.iso_backends.pynauty_levi import PynautyLeviBackend

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    "fixture_name",
    ["single_edge_hypergraph", "fano_plane", "sts_9"],
)
def test_pynauty_fingerprint_invariant(
    request: pytest.FixtureRequest,
    fixture_name: str,
) -> None:
    """Pynauty fingerprint stable under node permutation."""
    H: SparseHypergraph = request.getfixturevalue(fixture_name)
    backend = PynautyLeviBackend()
    fp_h = backend.fingerprint(H)
    for seed in range(3):
        rng = random.Random(seed)
        sigma = list(range(H.n_nodes))
        rng.shuffle(sigma)
        H2 = permute(H, sigma)
        assert backend.fingerprint(H2) == fp_h


@pytest.mark.parametrize(
    "fixture_name",
    ["single_edge_hypergraph", "fano_plane", "sts_9"],
)
def test_partition_agreement_iso(
    request: pytest.FixtureRequest,
    fixture_name: str,
) -> None:
    """IsalHG and pynauty agree: permuted copies are iso."""
    H: SparseHypergraph = request.getfixturevalue(fixture_name)
    pyn = PynautyLeviBackend()
    isalhg = IsalHGBackend()
    rng = random.Random(0)
    sigma = list(range(H.n_nodes))
    rng.shuffle(sigma)
    H2 = permute(H, sigma)
    assert pyn.are_isomorphic(H, H2)
    assert isalhg.are_isomorphic(H, H2)


def test_partition_agreement_non_iso(
    non_iso_pair_small: tuple[SparseHypergraph, SparseHypergraph],
) -> None:
    """Both backends agree the non-iso pair is non-iso."""
    h1, h2 = non_iso_pair_small
    assert not PynautyLeviBackend().are_isomorphic(h1, h2)
    assert not IsalHGBackend().are_isomorphic(h1, h2)


def test_pynauty_bijection_certificate(
    fano_plane: SparseHypergraph,
) -> None:
    """Pynauty produces a valid vertex bijection for iso fixtures."""
    sigma = [3, 1, 4, 0, 5, 6, 2]
    H2 = permute(fano_plane, sigma)
    bij = PynautyLeviBackend().bijection_certificate(fano_plane, H2)
    assert bij is not None
    assert sorted(bij.keys()) == list(range(7))
    assert sorted(bij.values()) == list(range(7))
