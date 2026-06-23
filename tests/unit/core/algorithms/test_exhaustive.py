"""Unit tests for ``isalhg.core.algorithms.exhaustive``."""

from __future__ import annotations

import pytest

from isalhg.core.algorithms.exhaustive import Exhaustive
from isalhg.core.algorithms.greedy_min import GreedyMin
from isalhg.core.canonical import required_k
from isalhg.core.instructions import serialize
from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.errors import DisconnectedHypergraphError

pytestmark = pytest.mark.unit


def _encode(algo_cls, H: SparseHypergraph) -> str:
    algo = algo_cls(k=required_k(H))
    return serialize(list(algo.encode(H)))


def test_exhaustive_empty_returns_empty() -> None:
    H = SparseHypergraph(n_nodes=0)
    algo = Exhaustive(k=2)
    assert algo.encode(H) == ()


def test_exhaustive_rejects_disconnected() -> None:
    H = SparseHypergraph(
        n_nodes=4,
        hyperedges=[frozenset({0, 1}), frozenset({2, 3})],
    )
    algo = Exhaustive(k=2)
    with pytest.raises(DisconnectedHypergraphError):
        algo.encode(H)


def test_exhaustive_matches_greedy_min_on_single_edge() -> None:
    H = SparseHypergraph(n_nodes=3, hyperedges=[frozenset({0, 1, 2})])
    assert _encode(Exhaustive, H) == _encode(GreedyMin, H)


def test_exhaustive_invariant_under_permutation_on_iso_pair_small() -> None:
    h1 = SparseHypergraph(
        n_nodes=4,
        hyperedges=[frozenset({0, 1, 2}), frozenset({0, 1, 3})],
    )
    h2 = permute(h1, [3, 2, 1, 0])
    assert _encode(Exhaustive, h1) == _encode(Exhaustive, h2)


def test_exhaustive_distinguishes_non_iso_pair(
    non_iso_pair_small: tuple[SparseHypergraph, SparseHypergraph],
) -> None:
    h1, h2 = non_iso_pair_small
    assert _encode(Exhaustive, h1) != _encode(Exhaustive, h2)


def test_exhaustive_fano_permutation_invariance(fano_plane: SparseHypergraph) -> None:
    sigma = [6, 5, 4, 3, 2, 1, 0]
    assert _encode(Exhaustive, fano_plane) == _encode(Exhaustive, permute(fano_plane, sigma))
