"""Unit tests for :class:`isalhg.metric_space.representations.wl`.

The WL baseline is iso-invariant (distance 0 on isomorphic pairs) but not a
complete invariant, so distance 0 on a *non*-isomorphic pair is not asserted.
"""

from __future__ import annotations

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.metric_space import registry
from isalhg.metric_space.representations.wl import HypergraphWLDistance

pytestmark = pytest.mark.unit


def _path_hypergraph() -> SparseHypergraph:
    return SparseHypergraph(
        n_nodes=4, hyperedges=[frozenset({0, 1}), frozenset({1, 2}), frozenset({2, 3})]
    )


class TestPairwise:
    def test_zero_on_iso_pair(
        self, iso_pair_small: tuple[SparseHypergraph, SparseHypergraph, list[int]]
    ) -> None:
        h1, h2, _ = iso_pair_small
        assert HypergraphWLDistance().pairwise(h1, h2) == 0.0

    def test_zero_on_permuted_design_fixture(self, fano_plane: SparseHypergraph) -> None:
        d = HypergraphWLDistance()
        assert d.pairwise(fano_plane, permute(fano_plane, [6, 5, 4, 3, 2, 1, 0])) == 0.0

    def test_self_distance_zero(self, sts_9: SparseHypergraph) -> None:
        assert HypergraphWLDistance().pairwise(sts_9, sts_9) == 0.0

    def test_positive_on_distinct_designs(
        self, fano_plane: SparseHypergraph, sts_9: SparseHypergraph
    ) -> None:
        # Fano vertices have degree 3, STS(9) degree 4 -> distinct WL colours.
        assert HypergraphWLDistance().pairwise(fano_plane, sts_9) > 0.0

    def test_chi2_metric(self, fano_plane: SparseHypergraph, sts_9: SparseHypergraph) -> None:
        d = HypergraphWLDistance(metric="chi2")
        assert d.pairwise(fano_plane, fano_plane) == 0.0
        assert d.pairwise(fano_plane, sts_9) > 0.0

    def test_invalid_metric_raises(self) -> None:
        with pytest.raises(ValueError):
            HypergraphWLDistance(metric="cosine")

    def test_name(self) -> None:
        assert HypergraphWLDistance().name == "hypergraph_wl_l1"
        assert HypergraphWLDistance(metric="chi2").name == "hypergraph_wl_chi2"


class TestMatrix:
    def test_matrix_runs_on_ten_item_corpus(
        self,
        fano_plane: SparseHypergraph,
        sts_9: SparseHypergraph,
        single_edge_hypergraph: SparseHypergraph,
        iso_pair_small: tuple[SparseHypergraph, SparseHypergraph, list[int]],
        non_iso_pair_small: tuple[SparseHypergraph, SparseHypergraph],
    ) -> None:
        np = pytest.importorskip("numpy")
        i1, i2, _ = iso_pair_small
        h1, h2 = non_iso_pair_small
        corpus = [
            fano_plane,
            permute(fano_plane, [1, 2, 3, 4, 5, 6, 0]),
            sts_9,
            permute(sts_9, [1, 2, 3, 4, 5, 6, 7, 8, 0]),
            i1,
            i2,
            h1,
            h2,
            single_edge_hypergraph,
            _path_hypergraph(),
        ]
        matrix = HypergraphWLDistance().matrix(corpus)
        assert matrix.shape == (10, 10)
        assert np.allclose(matrix, matrix.T)
        assert np.allclose(np.diag(matrix), 0.0)
        # Isomorphic members: schedule-consistent WL keeps them at distance 0.
        assert matrix[0, 1] == 0.0  # fano vs permuted fano
        assert matrix[2, 3] == 0.0  # sts9 vs permuted sts9
        assert matrix[4, 5] == 0.0  # iso pair

    def test_empty_corpus(self) -> None:
        pytest.importorskip("numpy")
        matrix = HypergraphWLDistance().matrix([])
        assert matrix.shape == (0, 0)


class TestRegistry:
    def test_registered_and_retrievable(self) -> None:
        d = registry.get_distance("hypergraph_wl_l1")
        assert isinstance(d, HypergraphWLDistance)
        assert d.name == "hypergraph_wl_l1"
        assert "hypergraph_wl_chi2" in registry.available_distances()
