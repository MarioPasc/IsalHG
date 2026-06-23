"""Unit tests for the WL-pruned canonical algorithm variants.

These variants are conjectured canonical (empirically validated against
``greedy_min`` here on hand-built fixtures; benchmark validates on the
ER cohort).
"""

from __future__ import annotations

import pytest

from isalhg.core.algorithms.greedy_min import GreedyMin
from isalhg.core.algorithms.greedy_min_inplace_wl_pruned import GreedyMinInplaceWLPruned
from isalhg.core.algorithms.greedy_min_wl_pruned import GreedyMinWLPruned
from isalhg.core.algorithms.pruned_exhaustive import PrunedExhaustive
from isalhg.core.canonical import required_k
from isalhg.core.instructions import serialize
from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.errors import DisconnectedHypergraphError

pytestmark = pytest.mark.unit


def _encode(algo_cls, H: SparseHypergraph) -> str:
    return serialize(list(algo_cls(k=required_k(H)).encode(H)))


VARIANTS = [GreedyMinWLPruned, GreedyMinInplaceWLPruned, PrunedExhaustive]


@pytest.mark.parametrize("cls", VARIANTS)
def test_wl_variant_empty(cls) -> None:
    H = SparseHypergraph(n_nodes=0)
    assert cls(k=2).encode(H) == ()


@pytest.mark.parametrize("cls", VARIANTS)
def test_wl_variant_rejects_disconnected(cls) -> None:
    H = SparseHypergraph(
        n_nodes=4,
        hyperedges=[frozenset({0, 1}), frozenset({2, 3})],
    )
    with pytest.raises(DisconnectedHypergraphError):
        cls(k=2).encode(H)


@pytest.mark.parametrize("cls", VARIANTS)
def test_wl_variant_matches_greedy_min_on_single_edge(cls) -> None:
    H = SparseHypergraph(n_nodes=3, hyperedges=[frozenset({0, 1, 2})])
    assert _encode(cls, H) == _encode(GreedyMin, H)


@pytest.mark.parametrize("cls", [GreedyMinWLPruned, GreedyMinInplaceWLPruned])
def test_wl_variant_matches_greedy_min_on_iso_pair_small(
    cls,
    iso_pair_small: tuple[SparseHypergraph, SparseHypergraph, list[int]],
) -> None:
    # The max-xi-then-WL-filter variants must match greedy_min exactly.
    h1, h2, _ = iso_pair_small
    assert _encode(cls, h1) == _encode(GreedyMin, h1)
    assert _encode(cls, h2) == _encode(GreedyMin, h2)
    assert _encode(cls, h1) == _encode(cls, h2)


def test_pruned_exhaustive_iso_invariant_on_iso_pair_small(
    iso_pair_small: tuple[SparseHypergraph, SparseHypergraph, list[int]],
) -> None:
    # PrunedExhaustive may pick a different seed orbit than greedy_min;
    # we only require iso-invariance, not equality with greedy_min.
    h1, h2, _ = iso_pair_small
    assert _encode(PrunedExhaustive, h1) == _encode(PrunedExhaustive, h2)


@pytest.mark.parametrize("cls", VARIANTS)
def test_wl_variant_matches_greedy_min_on_fano(cls, fano_plane: SparseHypergraph) -> None:
    # On vertex-transitive Fano the WL filter is a no-op; the variant
    # must still produce the canonical greedy_min string.
    assert _encode(cls, fano_plane) == _encode(GreedyMin, fano_plane)


@pytest.mark.parametrize("cls", VARIANTS)
def test_wl_variant_fano_permutation_invariance(cls, fano_plane: SparseHypergraph) -> None:
    sigma = [6, 5, 4, 3, 2, 1, 0]
    assert _encode(cls, fano_plane) == _encode(cls, permute(fano_plane, sigma))


@pytest.mark.parametrize("cls", VARIANTS)
def test_wl_variant_distinguishes_non_iso_pair(
    cls,
    non_iso_pair_small: tuple[SparseHypergraph, SparseHypergraph],
) -> None:
    h1, h2 = non_iso_pair_small
    assert _encode(cls, h1) != _encode(cls, h2)


@pytest.mark.parametrize("cls", VARIANTS)
def test_wl_variant_invariant_under_path_permutation(cls) -> None:
    # Path graph 0-1-2-3; reverse permutation flips endpoints.
    H = SparseHypergraph(
        n_nodes=4,
        hyperedges=[frozenset({0, 1}), frozenset({1, 2}), frozenset({2, 3})],
    )
    sigma = [3, 2, 1, 0]
    assert _encode(cls, H) == _encode(cls, permute(H, sigma))
