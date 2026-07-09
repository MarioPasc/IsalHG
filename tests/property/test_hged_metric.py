"""Property: ExactHGED is a genuine metric consistent with the ladder and iso.

Over a Hypothesis distribution of small connected hypergraphs the exact oracle
must satisfy the edit-distance metric identities (self-distance 0, symmetry,
permutation-invariance, triangle inequality), the perturbation-ladder guarantee
(``ExactHGED(H, edit_path(H, t)) <= t``), and the isomorphism equivalence
(``ExactHGED(H1, H2) == 0`` iff pynauty says ``H1 ~ H2``). The last one is the
independent cross-check that our bespoke solver agrees with a mature iso engine
on the zero set.

Small sizes (``n <= 5``, arity ``<= 3``) keep the NP-hard exact solve fast.
"""

from __future__ import annotations

import random

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

scipy = pytest.importorskip("scipy")
numpy = pytest.importorskip("numpy")

from isalhg.core.sparse_hypergraph import SparseHypergraph, edit_path, permute
from isalhg.metric_space.distances.hged import ExactHGED

pytestmark = pytest.mark.property


@st.composite
def small_connected_hypergraph(
    draw: st.DrawFn, max_n: int = 5, max_arity: int = 3
) -> SparseHypergraph:
    """A random connected hypergraph on ``2..max_n`` vertices (spanning tree + extras)."""
    n = draw(st.integers(min_value=2, max_value=max_n))
    perm = draw(st.permutations(list(range(n))))
    edges: list[frozenset[int]] = []
    for i in range(1, n):
        parent = draw(st.integers(min_value=0, max_value=i - 1))
        edges.append(frozenset({perm[i], perm[parent]}))
    for _ in range(draw(st.integers(min_value=0, max_value=2))):
        arity = draw(st.integers(min_value=2, max_value=min(max_arity, n)))
        members = draw(
            st.sets(
                st.integers(min_value=0, max_value=n - 1),
                min_size=arity,
                max_size=arity,
            )
        )
        edges.append(frozenset(members))
    return SparseHypergraph(n_nodes=n, hyperedges=edges)


@settings(max_examples=30, deadline=None)
@given(small_connected_hypergraph())
def test_self_distance_zero(H: SparseHypergraph) -> None:
    assert ExactHGED().pairwise(H, H) == 0.0


@settings(max_examples=25, deadline=None)
@given(small_connected_hypergraph(), st.integers(min_value=0, max_value=2**32 - 1))
def test_permutation_invariance(H: SparseHypergraph, seed: int) -> None:
    rng = random.Random(seed)
    sigma = list(range(H.n_nodes))
    rng.shuffle(sigma)
    assert ExactHGED().pairwise(H, permute(H, sigma)) == 0.0


@settings(max_examples=25, deadline=None)
@given(
    small_connected_hypergraph(),
    small_connected_hypergraph(),
)
def test_symmetry(h1: SparseHypergraph, h2: SparseHypergraph) -> None:
    exact = ExactHGED()
    assert exact.pairwise(h1, h2) == exact.pairwise(h2, h1)


@settings(max_examples=25, deadline=None)
@given(
    small_connected_hypergraph(),
    st.integers(min_value=0, max_value=8),
    st.integers(min_value=0, max_value=2**32 - 1),
)
def test_ladder_budget_upper_bounds_hged(H: SparseHypergraph, t: int, seed: int) -> None:
    rng = random.Random(seed)
    pert, budget = edit_path(H, t, rng)
    assert ExactHGED().pairwise(H, pert) <= budget


@settings(max_examples=20, deadline=None)
@given(
    small_connected_hypergraph(),
    small_connected_hypergraph(),
    small_connected_hypergraph(),
)
def test_triangle_inequality(a: SparseHypergraph, b: SparseHypergraph, c: SparseHypergraph) -> None:
    exact = ExactHGED()
    assert exact.pairwise(a, c) <= exact.pairwise(a, b) + exact.pairwise(b, c)


@settings(max_examples=25, deadline=None)
@given(
    small_connected_hypergraph(),
    small_connected_hypergraph(),
)
def test_zero_iff_isomorphic(h1: SparseHypergraph, h2: SparseHypergraph) -> None:
    pynauty = pytest.importorskip("pynauty")  # noqa: F841
    from isalhg.iso_backends.pynauty_levi import PynautyLeviBackend

    is_zero = ExactHGED().pairwise(h1, h2) == 0.0
    is_iso = PynautyLeviBackend().are_isomorphic(h1, h2)
    assert is_zero == is_iso
