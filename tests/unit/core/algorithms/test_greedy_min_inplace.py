"""Unit tests for ``isalhg.core.algorithms.greedy_min_inplace``.

The in-place variant MUST produce the same token sequence as the
clone-based ``greedy_min`` on every fixture; only the per-branch state
mechanism differs.
"""

from __future__ import annotations

import pytest

from isalhg.core.algorithms.greedy_min import GreedyMin
from isalhg.core.algorithms.greedy_min_inplace import GreedyMinInplace
from isalhg.core.canonical import required_k
from isalhg.core.instructions import serialize
from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.errors import DisconnectedHypergraphError

pytestmark = pytest.mark.unit


def _encode_ip(H: SparseHypergraph) -> str:
    return serialize(list(GreedyMinInplace(k=required_k(H)).encode(H)))


def _encode_gm(H: SparseHypergraph) -> str:
    return serialize(list(GreedyMin(k=required_k(H)).encode(H)))


def test_inplace_empty() -> None:
    H = SparseHypergraph(n_nodes=0)
    assert GreedyMinInplace(k=2).encode(H) == ()


def test_inplace_rejects_disconnected() -> None:
    H = SparseHypergraph(
        n_nodes=4,
        hyperedges=[frozenset({0, 1}), frozenset({2, 3})],
    )
    with pytest.raises(DisconnectedHypergraphError):
        GreedyMinInplace(k=2).encode(H)


def test_inplace_matches_clone_on_single_edge() -> None:
    H = SparseHypergraph(n_nodes=3, hyperedges=[frozenset({0, 1, 2})])
    assert _encode_ip(H) == _encode_gm(H)


def test_inplace_matches_clone_on_fano(fano_plane: SparseHypergraph) -> None:
    assert _encode_ip(fano_plane) == _encode_gm(fano_plane)


def test_inplace_matches_clone_on_sts9(sts_9: SparseHypergraph) -> None:
    assert _encode_ip(sts_9) == _encode_gm(sts_9)


def test_inplace_fano_permutation_invariance(fano_plane: SparseHypergraph) -> None:
    sigma = [6, 5, 4, 3, 2, 1, 0]
    assert _encode_ip(fano_plane) == _encode_ip(permute(fano_plane, sigma))


def test_inplace_sts9_permutation_invariance(sts_9: SparseHypergraph) -> None:
    sigma = [8, 7, 6, 5, 4, 3, 2, 1, 0]
    assert _encode_ip(sts_9) == _encode_ip(permute(sts_9, sigma))


def test_inplace_distinguishes_non_iso_pair(
    non_iso_pair_small: tuple[SparseHypergraph, SparseHypergraph],
) -> None:
    h1, h2 = non_iso_pair_small
    assert _encode_ip(h1) != _encode_ip(h2)


def test_inplace_matches_clone_on_iso_pair_small(
    iso_pair_small: tuple[SparseHypergraph, SparseHypergraph, list[int]],
) -> None:
    h1, h2, _ = iso_pair_small
    assert _encode_ip(h1) == _encode_gm(h1)
    assert _encode_ip(h2) == _encode_gm(h2)
    assert _encode_ip(h1) == _encode_ip(h2)
