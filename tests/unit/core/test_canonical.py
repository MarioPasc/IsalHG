"""Unit tests for :mod:`isalhg.core.canonical`."""

from __future__ import annotations

import random

import pytest

from isalhg.core.canonical import canonical_string, required_k
from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.errors import DisconnectedHypergraphError

pytestmark = pytest.mark.unit


class TestBasics:
    def test_trivial_returns_empty_string(self) -> None:
        H = SparseHypergraph(n_nodes=1)
        assert canonical_string(H) == ""

    def test_single_edge_starts_with_v(self, single_edge_hypergraph: SparseHypergraph) -> None:
        s = canonical_string(single_edge_hypergraph)
        assert s.startswith("V[0;1;2;")


class TestIsoInvariance:
    def test_trivial_invariant(self) -> None:
        H = SparseHypergraph(n_nodes=1)
        assert canonical_string(H) == canonical_string(permute(H, [0]))

    @pytest.mark.parametrize("sigma", [[0, 1, 2], [2, 1, 0], [1, 2, 0], [0, 2, 1]])
    def test_single_edge_invariant(
        self,
        single_edge_hypergraph: SparseHypergraph,
        sigma: list[int],
    ) -> None:
        H2 = permute(single_edge_hypergraph, sigma)
        assert canonical_string(single_edge_hypergraph) == canonical_string(H2)

    def test_iso_pair_fixture(
        self,
        iso_pair_small: tuple[SparseHypergraph, SparseHypergraph, list[int]],
    ) -> None:
        h1, h2, _ = iso_pair_small
        assert canonical_string(h1) == canonical_string(h2)

    @pytest.mark.parametrize("seed", list(range(5)))
    def test_fano_random_permutation_invariance(
        self, fano_plane: SparseHypergraph, seed: int
    ) -> None:
        rng = random.Random(seed)
        sigma = list(range(7))
        rng.shuffle(sigma)
        H2 = permute(fano_plane, sigma)
        assert canonical_string(fano_plane) == canonical_string(H2)

    @pytest.mark.parametrize("seed", list(range(5)))
    def test_sts9_random_permutation_invariance(self, sts_9: SparseHypergraph, seed: int) -> None:
        rng = random.Random(seed)
        sigma = list(range(9))
        rng.shuffle(sigma)
        H2 = permute(sts_9, sigma)
        assert canonical_string(sts_9) == canonical_string(H2)


class TestDiscrimination:
    def test_non_iso_pair_differs(
        self, non_iso_pair_small: tuple[SparseHypergraph, SparseHypergraph]
    ) -> None:
        h1, h2 = non_iso_pair_small
        k = max(required_k(h1), required_k(h2))
        s1 = canonical_string(h1, k=k)
        s2 = canonical_string(h2, k=k)
        assert s1 != s2


class TestDisconnected:
    def test_rejects_disconnected(self) -> None:
        H = SparseHypergraph(
            n_nodes=4,
            hyperedges=[frozenset({0, 1}), frozenset({2, 3})],
        )
        with pytest.raises(DisconnectedHypergraphError):
            canonical_string(H)
