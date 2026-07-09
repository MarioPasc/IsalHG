"""Property: ``greedy_min_complete`` is a complete isomorphism invariant.

Theorem A (metric-space article) empirical arm. Unlike
``test_canonical_invariance.py`` -- whose ``permute`` oracle preserves edge
insertion order and therefore never exercises the greedy edge-id tie-break
-- these properties shuffle the edge list too, testing invariance over the
full presentation class of each hypergraph:

1. invariance: ``w*(H)`` equals ``w*`` of any vertex-relabelled,
   edge-reordered copy;
2. completeness biconditional: ``w*`` equality agrees with the pynauty
   iso decision on independently drawn pairs.

Over a non-trivial vertex vocabulary the biconditional attaches to the
*augmented* fingerprint ``F(H) = (seed label, w*(H))`` served by
``IsalHGBackend``: the canonical string never emits the label of its own seed
vertex, so the bare string is incomplete there (T-TAb).
"""

from __future__ import annotations

import random as _random

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

pynauty = pytest.importorskip("pynauty")

from isalhg.core.canonical import canonical_string, required_k
from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.iso_backends.isalhg_backend import IsalHGBackend
from isalhg.iso_backends.pynauty_levi import PynautyLeviBackend

from ._labelled_oracle import brute_force_iso, labelled_hypergraph_pair

pytestmark = pytest.mark.property

_ALGO = "canonical"


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


def _reordered_iso_copy(H: SparseHypergraph, rng: _random.Random) -> SparseHypergraph:
    sigma = list(range(H.n_nodes))
    rng.shuffle(sigma)
    H_iso = permute(H, sigma)
    edges = [(m, ell) for _, m, ell in H_iso.iter_edges()]
    rng.shuffle(edges)
    return SparseHypergraph(
        n_nodes=H.n_nodes,
        hyperedges=[m for m, _ in edges],
        n_vertex_labels=H.n_vertex_labels,
        n_edge_labels=H.n_edge_labels,
        vertex_labels=[H_iso.vertex_label(v) for v in range(H.n_nodes)],
        edge_labels=[ell for _, ell in edges],
    )


@settings(max_examples=30, deadline=None)
@given(small_connected_hypergraph(), st.integers(min_value=0, max_value=2**32 - 1))
def test_complete_invariant_under_relabel_and_reorder(H: SparseHypergraph, seed: int) -> None:
    rng = _random.Random(seed)
    H2 = _reordered_iso_copy(H, rng)
    k = required_k(H)
    assert canonical_string(H, k=k, algorithm=_ALGO) == canonical_string(H2, k=k, algorithm=_ALGO)


@settings(max_examples=25, deadline=None)
@given(small_connected_hypergraph(), small_connected_hypergraph())
def test_complete_equality_matches_pynauty_iso(H1: SparseHypergraph, H2: SparseHypergraph) -> None:
    k = max(required_k(H1), required_k(H2))
    same_string = canonical_string(H1, k=k, algorithm=_ALGO) == canonical_string(
        H2, k=k, algorithm=_ALGO
    )
    iso = H1.n_nodes == H2.n_nodes and PynautyLeviBackend().are_isomorphic(H1, H2)
    assert same_string == iso


# ---------------------------------------------------------------------------
# Labelled vocabularies: the biconditional holds over the augmented
# fingerprint ``F(H) = (seed label, w*_c(H))``, not over the bare string --
# ``w*`` never emits the seed's own label (T-TAb). The oracle is the exhaustive
# bijection search, not pynauty (see ``_labelled_oracle``).
# ---------------------------------------------------------------------------


@settings(max_examples=30, deadline=None)
@given(labelled_hypergraph_pair(), st.integers(min_value=0, max_value=2**32 - 1))
def test_labelled_complete_fingerprint_invariant_under_relabel_and_reorder(
    pair: tuple[SparseHypergraph, SparseHypergraph], seed: int
) -> None:
    H, _ = pair
    backend = IsalHGBackend(algorithm=_ALGO)
    assert backend.fingerprint(H) == backend.fingerprint(
        _reordered_iso_copy(H, _random.Random(seed))
    )


@settings(max_examples=100, deadline=None)
@given(labelled_hypergraph_pair())
def test_labelled_complete_fingerprint_equality_matches_iso_oracle(
    pair: tuple[SparseHypergraph, SparseHypergraph],
) -> None:
    H1, H2 = pair
    backend = IsalHGBackend(algorithm=_ALGO)
    same_fp = backend.fingerprint(H1) == backend.fingerprint(H2)
    assert same_fp == brute_force_iso(H1, H2)
