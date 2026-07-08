"""Unit tests for :class:`isalhg.iso_backends.isalhg_backend.IsalHGBackend`."""

from __future__ import annotations

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.iso_backends.isalhg_backend import IsalHGBackend

pytestmark = pytest.mark.unit


class TestFingerprint:
    def test_trivial(self) -> None:
        backend = IsalHGBackend()
        H = SparseHypergraph(n_nodes=1)
        assert backend.fingerprint(H) == b""

    def test_returns_bytes(self, fano_plane: SparseHypergraph) -> None:
        backend = IsalHGBackend()
        fp = backend.fingerprint(fano_plane)
        assert isinstance(fp, bytes)
        assert len(fp) > 0


class TestAreIsomorphic:
    def test_iso_pair(
        self,
        iso_pair_small: tuple[SparseHypergraph, SparseHypergraph, list[int]],
    ) -> None:
        h1, h2, _ = iso_pair_small
        assert IsalHGBackend().are_isomorphic(h1, h2)

    def test_non_iso_pair(
        self,
        non_iso_pair_small: tuple[SparseHypergraph, SparseHypergraph],
    ) -> None:
        h1, h2 = non_iso_pair_small
        assert not IsalHGBackend().are_isomorphic(h1, h2)

    def test_fano_vs_permutation(self, fano_plane: SparseHypergraph) -> None:
        sigma = [3, 1, 4, 0, 5, 6, 2]
        H2 = permute(fano_plane, sigma)
        assert IsalHGBackend().are_isomorphic(fano_plane, H2)

    def test_different_vocab_returns_false(self) -> None:
        h1 = SparseHypergraph(n_nodes=2, n_vertex_labels=1)
        h2 = SparseHypergraph(n_nodes=2, n_vertex_labels=2)
        assert not IsalHGBackend().are_isomorphic(h1, h2)


class TestName:
    def test_name_reflects_algorithm(self) -> None:
        # ``name`` is the per-algorithm identifier ``isalhg_<algorithm>``
        # used to disambiguate the variant-comparison study.
        assert IsalHGBackend(algorithm="greedy_min").name == "isalhg_greedy_min"
        assert IsalHGBackend(algorithm="greedy_single").name == "isalhg_greedy_single"

    def test_default_name_is_nbrdeg(self) -> None:
        # T-M0 default: the neighbour-degree seed cascade.
        assert IsalHGBackend().name == "isalhg_greedy_min_nbrdeg"
