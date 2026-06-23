"""Unit tests for ``isalhg.core.hypergraph_wl``."""

from __future__ import annotations

import pytest

from isalhg.core.hypergraph_wl import wl_hash, wl_partition
from isalhg.core.sparse_hypergraph import SparseHypergraph, permute

pytestmark = pytest.mark.unit


def test_wl_hash_empty_hypergraph() -> None:
    H = SparseHypergraph(n_nodes=0)
    assert wl_hash(H) == []


def test_wl_hash_isolated_vertices_have_equal_colour() -> None:
    H = SparseHypergraph(n_nodes=3)
    h = wl_hash(H)
    assert h[0] == h[1] == h[2]


def test_wl_hash_single_edge_three_vertices_all_equal() -> None:
    H = SparseHypergraph(n_nodes=3, hyperedges=[frozenset({0, 1, 2})])
    h = wl_hash(H)
    assert h[0] == h[1] == h[2]


def test_wl_hash_permutation_invariance_on_fano(fano_plane: SparseHypergraph) -> None:
    # Fano is vertex-transitive: every vertex has the same WL colour.
    h = wl_hash(fano_plane)
    assert len(set(h)) == 1

    sigma = [6, 5, 4, 3, 2, 1, 0]
    h_perm = wl_hash(permute(fano_plane, sigma))
    # Sets of colours must be equal (the labelling is permutation-invariant up to relabelling).
    assert sorted(h) == sorted(h_perm)


def test_wl_hash_permutation_invariance_on_sts_9(sts_9: SparseHypergraph) -> None:
    h = wl_hash(sts_9)
    assert len(set(h)) == 1  # STS(9) is vertex-transitive

    sigma = [8, 7, 6, 5, 4, 3, 2, 1, 0]
    h_perm = wl_hash(permute(sts_9, sigma))
    assert sorted(h) == sorted(h_perm)


def test_wl_hash_distinguishes_non_iso_pair(
    non_iso_pair_small: tuple[SparseHypergraph, SparseHypergraph],
) -> None:
    h1_obj, h2_obj = non_iso_pair_small
    h1 = wl_hash(h1_obj)
    h2 = wl_hash(h2_obj)
    # Different arity profiles -> WL must produce different colour multisets.
    assert sorted(h1) != sorted(h2)


def test_wl_partition_groups_by_colour(fano_plane: SparseHypergraph) -> None:
    part = wl_partition(fano_plane)
    # Vertex-transitive -> exactly one orbit.
    assert len(part) == 1
    only_class = next(iter(part.values()))
    assert sorted(only_class) == list(range(fano_plane.n_nodes))


def test_wl_hash_path_distinguishes_endpoints_from_middle() -> None:
    # Path 0 - 1 - 2 - 3 via three 2-edges. Endpoints (0, 3) should
    # share a colour distinct from the middle (1, 2).
    H = SparseHypergraph(
        n_nodes=4,
        hyperedges=[
            frozenset({0, 1}),
            frozenset({1, 2}),
            frozenset({2, 3}),
        ],
    )
    h = wl_hash(H)
    assert h[0] == h[3]
    assert h[1] == h[2]
    assert h[0] != h[1]


def test_wl_hash_uses_vertex_labels() -> None:
    H_unlabelled = SparseHypergraph(
        n_nodes=3,
        hyperedges=[frozenset({0, 1, 2})],
    )
    H_labelled = SparseHypergraph(
        n_nodes=3,
        hyperedges=[frozenset({0, 1, 2})],
        n_vertex_labels=2,
        vertex_labels=[0, 1, 1],
    )
    h_un = wl_hash(H_unlabelled)
    h_lab = wl_hash(H_labelled)
    assert h_un[0] == h_un[1] == h_un[2]
    assert h_lab[0] != h_lab[1]
    assert h_lab[1] == h_lab[2]
