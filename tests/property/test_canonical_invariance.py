"""Property: canonical_string is invariant under node relabelling.

Uses pynauty as the iso oracle (Phase 2 onward). For every randomly
sampled connected hypergraph ``H`` and random permutation ``sigma``:
``IsalHGBackend.fingerprint(H) == IsalHGBackend.fingerprint(permute(H, sigma))``
AND ``PynautyLeviBackend`` agrees on the iso decision.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

pynauty = pytest.importorskip("pynauty")

from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.iso_backends.isalhg_backend import IsalHGBackend
from isalhg.iso_backends.pynauty_levi import PynautyLeviBackend

pytestmark = pytest.mark.property


@st.composite
def small_connected_hypergraph(draw, max_n: int = 5, max_arity: int = 3) -> SparseHypergraph:
    n = draw(st.integers(min_value=2, max_value=max_n))
    perm = draw(st.permutations(list(range(n))))
    spanning_edges: list[frozenset[int]] = []
    for i in range(1, n):
        parent_idx = draw(st.integers(min_value=0, max_value=i - 1))
        spanning_edges.append(frozenset({perm[i], perm[parent_idx]}))
    n_extra = draw(st.integers(min_value=0, max_value=2))
    extra: list[frozenset[int]] = []
    for _ in range(n_extra):
        arity = draw(st.integers(min_value=2, max_value=min(max_arity, n)))
        members = draw(
            st.sets(
                st.integers(min_value=0, max_value=n - 1),
                min_size=arity,
                max_size=arity,
            )
        )
        extra.append(frozenset(members))
    return SparseHypergraph(n_nodes=n, hyperedges=spanning_edges + extra)


@settings(max_examples=30, deadline=None)
@given(small_connected_hypergraph(), st.integers(min_value=0, max_value=2**32 - 1))
def test_isalhg_fingerprint_invariant_under_perm(H: SparseHypergraph, seed: int) -> None:
    import random as _r

    rng = _r.Random(seed)
    sigma = list(range(H.n_nodes))
    rng.shuffle(sigma)
    H2 = permute(H, sigma)
    backend = IsalHGBackend()
    assert backend.fingerprint(H) == backend.fingerprint(H2)


@settings(max_examples=20, deadline=None)
@given(small_connected_hypergraph(), st.integers(min_value=0, max_value=2**32 - 1))
def test_pynauty_agrees_with_isalhg_on_perm_pair(H: SparseHypergraph, seed: int) -> None:
    import random as _r

    rng = _r.Random(seed)
    sigma = list(range(H.n_nodes))
    rng.shuffle(sigma)
    H2 = permute(H, sigma)
    isalhg = IsalHGBackend()
    pyn = PynautyLeviBackend()
    assert isalhg.are_isomorphic(H, H2)
    assert pyn.are_isomorphic(H, H2)
