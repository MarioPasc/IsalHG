"""End-to-end: SparseHypergraph -> IsalHGBackend.are_isomorphic.

Drives :class:`IsalHGBackend` over every Phase 1 fixture and asserts
FP = FN = 0 against the ground truth (iso pairs and non-iso pairs).
"""

from __future__ import annotations

import random

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.iso_backends.isalhg_backend import IsalHGBackend

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    "fixture_name",
    ["trivial_hypergraph", "single_edge_hypergraph", "fano_plane", "sts_9"],
)
def test_fingerprint_invariant_under_permutation(
    request: pytest.FixtureRequest,
    fixture_name: str,
) -> None:
    H: SparseHypergraph = request.getfixturevalue(fixture_name)
    backend = IsalHGBackend()
    fp_h = backend.fingerprint(H)
    for seed in range(3):
        rng = random.Random(seed)
        sigma = list(range(H.n_nodes))
        rng.shuffle(sigma)
        H2 = permute(H, sigma)
        assert backend.fingerprint(H2) == fp_h
        assert backend.are_isomorphic(H, H2)


def test_fp_fn_zero_on_non_iso(
    non_iso_pair_small: tuple[SparseHypergraph, SparseHypergraph],
) -> None:
    h1, h2 = non_iso_pair_small
    backend = IsalHGBackend()
    assert not backend.are_isomorphic(h1, h2)


def test_iso_pair_zero_fn(
    iso_pair_small: tuple[SparseHypergraph, SparseHypergraph, list[int]],
) -> None:
    h1, h2, _ = iso_pair_small
    assert IsalHGBackend().are_isomorphic(h1, h2)
