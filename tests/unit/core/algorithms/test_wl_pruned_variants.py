"""Unit tests for the WL-pruned H2S algorithm variants.

Invariance status, established here by pinned counterexample:

- ``GreedyMinWLPruned`` / ``GreedyMinInplaceWLPruned`` filter the seed set by
  the iso-invariant argmin WL colour and keep the whole class. They are
  invariant under vertex relabelling. They still inherit greedy's raw-edge-id
  V-tie-break, so they are not canonical forms on isomorphism classes.
- ``PrunedExhaustive`` picks the min-id vertex per WL colour class. Raw ids are
  not transported by an isomorphism, so it is **not** invariant under vertex
  relabelling and defines no canonical form.
- The ``wl_colors`` V-branch pruning inside ``greedy_h2s`` discards the lex-min
  completion. No registered algorithm passes it.
"""

from __future__ import annotations

import random

import pytest

from isalhg.core.algorithms.exhaustive import Exhaustive
from isalhg.core.algorithms.greedy_min import GreedyMin
from isalhg.core.algorithms.greedy_min_inplace_wl_pruned import GreedyMinInplaceWLPruned
from isalhg.core.algorithms.greedy_min_wl_pruned import GreedyMinWLPruned
from isalhg.core.algorithms.pruned_exhaustive import PrunedExhaustive
from isalhg.core.canonical import required_k
from isalhg.core.hypergraph_wl import wl_hash
from isalhg.core.instructions import serialize
from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.errors import DisconnectedHypergraphError

pytestmark = pytest.mark.unit


def _encode(algo_cls, H: SparseHypergraph) -> str:
    return serialize(list(algo_cls(k=required_k(H)).encode(H)))


def _build(n: int, edges) -> SparseHypergraph:
    """Fixed hyperedge insertion order, so a relabel isolates the seed key."""
    H = SparseHypergraph(n)
    for e in edges:
        H.add_hyperedge(frozenset(e))
    return H


VARIANTS = [GreedyMinWLPruned, GreedyMinInplaceWLPruned, PrunedExhaustive]
SEED_INVARIANT_VARIANTS = [GreedyMinWLPruned, GreedyMinInplaceWLPruned]

# Triangular prism: 3-regular, one WL colour class, vertex-transitive.
PRISM_EDGES = [(0, 2), (0, 3), (0, 4), (1, 2), (1, 4), (1, 5), (2, 3), (3, 5), (4, 5)]
PRISM_SIGMA = [2, 4, 0, 1, 5, 3]

# 4-regular, one WL colour class, six primal automorphism orbits (rigid).
RIGID_EDGES = [
    (0, 5),
    (0, 6),
    (0, 7),
    (0, 9),
    (1, 2),
    (1, 4),
    (1, 6),
    (1, 8),
    (2, 3),
    (2, 6),
    (2, 9),
    (3, 4),
    (3, 5),
    (3, 9),
    (4, 5),
    (4, 7),
    (5, 8),
    (6, 8),
    (7, 8),
    (7, 9),
]
RIGID_SIGMA = [1, 9, 3, 6, 0, 4, 7, 5, 8, 2]


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


# ---------------------------------------------------------------------------
# Pinned counterexamples: the raw-id pruning keys are inadmissible.
#
# ``permute`` preserves hyperedge insertion order, so a relabel isolates the
# seed/branch key from greedy's separate raw-edge-id V-tie-break.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("n", "edges", "sigma", "label"),
    [
        (6, PRISM_EDGES, PRISM_SIGMA, "triangular prism (vertex-transitive)"),
        (10, RIGID_EDGES, RIGID_SIGMA, "4-regular rigid"),
    ],
)
def test_pruned_exhaustive_is_not_relabel_invariant(n, edges, sigma, label) -> None:
    H = _build(n, edges)
    assert len(set(wl_hash(H))) == 1, f"{label}: precondition, one WL colour class"
    Hp = permute(H, dict(enumerate(sigma)))
    assert _encode(PrunedExhaustive, H) != _encode(PrunedExhaustive, Hp), label


@pytest.mark.parametrize(
    ("n", "edges", "sigma"),
    [(6, PRISM_EDGES, PRISM_SIGMA), (10, RIGID_EDGES, RIGID_SIGMA)],
)
def test_exhaustive_is_relabel_invariant_on_the_same_fixtures(n, edges, sigma) -> None:
    # Control for the counterexample above: taking the lex-min over *every*
    # seed is relabel-invariant, so the failure is the min-id representative,
    # not the fixture or the edge order.
    H = _build(n, edges)
    assert _encode(Exhaustive, H) == _encode(Exhaustive, permute(H, dict(enumerate(sigma))))


def test_pruned_exhaustive_differs_from_exhaustive_on_vertex_transitive() -> None:
    # One WL colour class == one automorphism orbit, yet the min-id
    # representative does not reach the lex-min: greedy H2S is not constant on
    # an orbit, because its residual V-tie-break reads raw edge ids.
    H = _build(6, PRISM_EDGES)
    assert _encode(PrunedExhaustive, H) != _encode(Exhaustive, H)


@pytest.mark.parametrize("cls", SEED_INVARIANT_VARIANTS)
@pytest.mark.parametrize(("n", "edges"), [(6, PRISM_EDGES), (10, RIGID_EDGES)])
def test_seed_filtered_wl_variants_are_relabel_invariant(cls, n, edges) -> None:
    # The contrast with PrunedExhaustive: the argmin-WL-colour filter keeps the
    # whole class and reads no vertex id, so it is an admissible pruning key.
    H = _build(n, edges)
    base = _encode(cls, H)
    rng = random.Random(0)
    for _ in range(25):
        sigma = list(range(n))
        rng.shuffle(sigma)
        assert _encode(cls, permute(H, dict(enumerate(sigma)))) == base
