"""Cross-solver property tests for the official (Qin) HGED.

Qin's empty-shell taxonomy is the article's single HGED cost model (PI
decision 2026-07-08). Two independent solvers compute it:
``ExactHGED`` (LSAP branch-and-bound, the experiments' oracle) and ``QinHGED``
(the paper's HGED-BFS, the fidelity anchor). Their **exact agreement** on
random pairs is the strongest correctness evidence available -- two very
different search strategies over the same cost model must return the same
minimum -- alongside the shared zero set on isomorphic pairs.
"""

from __future__ import annotations

import random

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

scipy = pytest.importorskip("scipy")
numpy = pytest.importorskip("numpy")

from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.metric_space.distances.hged import ExactHGED
from isalhg.metric_space.distances.qin_hged import QinHGED

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


@settings(max_examples=25, deadline=None)
@given(small_connected_hypergraph(), small_connected_hypergraph())
def test_bnb_oracle_equals_paper_bfs(H1: SparseHypergraph, H2: SparseHypergraph) -> None:
    assert ExactHGED().pairwise(H1, H2) == QinHGED().pairwise(H1, H2)


@settings(max_examples=25, deadline=None)
@given(small_connected_hypergraph(), st.integers(min_value=0, max_value=2**32 - 1))
def test_both_vanish_on_isomorphic_pairs(H: SparseHypergraph, seed: int) -> None:
    rng = random.Random(seed)
    sigma = list(range(H.n_nodes))
    rng.shuffle(sigma)
    Hp = permute(H, sigma)
    assert QinHGED().pairwise(H, Hp) == 0.0
    assert ExactHGED().pairwise(H, Hp) == 0.0
