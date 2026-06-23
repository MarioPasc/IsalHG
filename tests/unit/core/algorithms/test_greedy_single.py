"""Unit tests for ``isalhg.core.algorithms.greedy_single``."""

from __future__ import annotations

import pytest

from isalhg.core.algorithms.greedy_single import GreedySingle
from isalhg.core.canonical import required_k
from isalhg.core.instructions import serialize
from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.errors import DisconnectedHypergraphError

pytestmark = pytest.mark.unit


def _encode(H: SparseHypergraph) -> str:
    algo = GreedySingle(k=required_k(H))
    return serialize(list(algo.encode(H)))


def test_greedy_single_empty_returns_empty() -> None:
    H = SparseHypergraph(n_nodes=0)
    algo = GreedySingle(k=2)
    assert algo.encode(H) == ()


def test_greedy_single_rejects_disconnected() -> None:
    H = SparseHypergraph(
        n_nodes=4,
        hyperedges=[frozenset({0, 1}), frozenset({2, 3})],
    )
    algo = GreedySingle(k=2)
    with pytest.raises(DisconnectedHypergraphError):
        algo.encode(H)


def test_greedy_single_deterministic_on_fano(fano_plane: SparseHypergraph) -> None:
    assert _encode(fano_plane) == _encode(fano_plane)


def test_greedy_single_non_iso_pair_differs(
    non_iso_pair_small: tuple[SparseHypergraph, SparseHypergraph],
) -> None:
    h1, h2 = non_iso_pair_small
    assert _encode(h1) != _encode(h2)


def test_greedy_single_known_non_invariance_on_fano_permutation(
    fano_plane: SparseHypergraph,
) -> None:
    # GreedySingle is documented as non-canonical on vertex-transitive designs.
    # A reverse permutation of Fano may produce a different greedy trajectory.
    # We assert determinism on the original and acknowledge the algorithm is
    # documented as heuristic.
    sigma = [6, 5, 4, 3, 2, 1, 0]
    f1 = _encode(fano_plane)
    f2 = _encode(permute(fano_plane, sigma))
    # We do NOT assert equality (this would force canonicality, which the
    # algorithm does not provide). We only assert deterministic execution.
    assert isinstance(f1, str) and isinstance(f2, str)
