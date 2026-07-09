"""Property: canonical_string is invariant under node relabelling.

Uses pynauty as the iso oracle (Phase 2 onward). For every randomly
sampled connected hypergraph ``H`` and random permutation ``sigma``:
``IsalHGBackend.fingerprint(H) == IsalHGBackend.fingerprint(permute(H, sigma))``
AND ``PynautyLeviBackend`` agrees on the iso decision.

The labelled properties additionally guard the forward direction of Theorem A
over a non-trivial vertex vocabulary, where the bare canonical string is
incomplete (the seed's label is never emitted) and only the augmented
fingerprint served by ``IsalHGBackend`` separates the classes. pynauty is the
colour-aware oracle: ``levi_reduction`` lifts vertex labels into the Levi
graph's colouring.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

pynauty = pytest.importorskip("pynauty")

from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.iso_backends.isalhg_backend import IsalHGBackend
from isalhg.iso_backends.pynauty_levi import PynautyLeviBackend

from ._labelled_oracle import brute_force_iso, labelled_hypergraph_pair

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


# Both iso-invariant seed strategies are guarded: the historical xi
# cascade (``greedy_min``) and the T-M0 neighbour-degree cascade
# (``greedy_min_nbrdeg``, the default). ``greedy_single*`` is deliberately
# excluded -- it selects by raw node id and is not iso-invariant.
_ISO_INVARIANT_VARIANTS = ["greedy_min", "greedy_min_nbrdeg"]


@pytest.mark.parametrize("algorithm", _ISO_INVARIANT_VARIANTS)
@settings(max_examples=30, deadline=None)
@given(small_connected_hypergraph(), st.integers(min_value=0, max_value=2**32 - 1))
def test_isalhg_fingerprint_invariant_under_perm(
    algorithm: str, H: SparseHypergraph, seed: int
) -> None:
    import random as _r

    rng = _r.Random(seed)
    sigma = list(range(H.n_nodes))
    rng.shuffle(sigma)
    H2 = permute(H, sigma)
    backend = IsalHGBackend(algorithm=algorithm)
    assert backend.fingerprint(H) == backend.fingerprint(H2)


@pytest.mark.parametrize("algorithm", _ISO_INVARIANT_VARIANTS)
@settings(max_examples=20, deadline=None)
@given(small_connected_hypergraph(), st.integers(min_value=0, max_value=2**32 - 1))
def test_pynauty_agrees_with_isalhg_on_perm_pair(
    algorithm: str, H: SparseHypergraph, seed: int
) -> None:
    import random as _r

    rng = _r.Random(seed)
    sigma = list(range(H.n_nodes))
    rng.shuffle(sigma)
    H2 = permute(H, sigma)
    isalhg = IsalHGBackend(algorithm=algorithm)
    pyn = PynautyLeviBackend()
    assert isalhg.are_isomorphic(H, H2)
    assert pyn.are_isomorphic(H, H2)


@pytest.mark.parametrize("algorithm", _ISO_INVARIANT_VARIANTS)
@settings(max_examples=30, deadline=None)
@given(labelled_hypergraph_pair(), st.integers(min_value=0, max_value=2**32 - 1))
def test_labelled_fingerprint_invariant_under_perm(
    algorithm: str, pair: tuple[SparseHypergraph, SparseHypergraph], seed: int
) -> None:
    import random as _r

    H, _ = pair
    rng = _r.Random(seed)
    sigma = list(range(H.n_nodes))
    rng.shuffle(sigma)
    backend = IsalHGBackend(algorithm=algorithm)
    assert backend.fingerprint(H) == backend.fingerprint(permute(H, sigma))


@pytest.mark.parametrize("algorithm", _ISO_INVARIANT_VARIANTS)
@settings(max_examples=200, deadline=None)
@given(labelled_hypergraph_pair())
def test_labelled_fingerprint_equality_implies_iso(
    algorithm: str, pair: tuple[SparseHypergraph, SparseHypergraph]
) -> None:
    """Forward direction of Theorem A on a non-trivial vertex vocabulary.

    The greedy variants are only one-sided (equal fingerprints certify
    isomorphism; the converse needs ``greedy_min_complete``), so this asserts
    the implication, not the biconditional. Before the seed-label augmentation
    the implication failed -- labels ``(0, 0)`` and ``(1, 0)`` over one edge
    shared a fingerprint.

    The oracle is the exhaustive bijection search, not pynauty: the Levi
    colouring loses absolute label identity (see ``_labelled_oracle``).
    """
    H1, H2 = pair
    if IsalHGBackend(algorithm=algorithm).are_isomorphic(H1, H2):
        assert brute_force_iso(H1, H2)
