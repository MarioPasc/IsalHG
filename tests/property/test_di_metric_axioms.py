"""Property: d_I is a genuine metric on isomorphism classes (Corollary A).

Tests the four metric axioms for d_I over w*_c (algorithm="canonical"):

1. Non-negativity:         d_I(H, H') >= 0
2. Symmetry:               d_I(H, H') == d_I(H', H)
3. Triangle inequality:    d_I(H, H'') <= d_I(H, H') + d_I(H', H'')
4. Identity of
   indiscernibles:         d_I(H, H') == 0  iff  H ~ H'   (Theorem A)

The triangle inequality is *inherited* from d_Lev, so those tests are a
regression guard on the token-encoding layer (the private-use-codepoint
mapping and the (\"seed\", ell) prefix), not on the mathematics.  The identity
tests use `brute_force_iso` from `_labelled_oracle` -- NOT pynauty, which
cannot serve as a labelled oracle (see T-TAe and `_labelled_oracle.py`).

Teeth check (T-TAe pattern): `test_identity_fails_without_seed_prefix`
demonstrates that the identity-of-indiscernibles property DOES fail when the
seed-label prefix is removed, confirming that the prefix is the load-bearing
component that makes Corollary A hold on non-trivial vertex vocabularies.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

pytest.importorskip("rapidfuzz")

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.metric_space.distances.isalhg_levenshtein import IsalHGLevenshtein

from ._labelled_oracle import brute_force_iso, labelled_hypergraph_pair

pytestmark = pytest.mark.property


# ---------------------------------------------------------------------------
# Shared hypergraph strategy
# ---------------------------------------------------------------------------


@st.composite
def small_connected_hypergraph(
    draw: st.DrawFn, max_n: int = 5, max_arity: int = 3
) -> SparseHypergraph:
    """Random connected hypergraph on 2..max_n vertices (spanning tree + extras)."""
    n = draw(st.integers(min_value=2, max_value=max_n))
    perm = draw(st.permutations(list(range(n))))
    edges: list[frozenset[int]] = [
        frozenset({perm[i], perm[draw(st.integers(min_value=0, max_value=i - 1))]})
        for i in range(1, n)
    ]
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


# ---------------------------------------------------------------------------
# Axiom 1 — non-negativity
# ---------------------------------------------------------------------------


@settings(max_examples=40, deadline=None)
@given(small_connected_hypergraph(), small_connected_hypergraph())
def test_non_negativity(H1: SparseHypergraph, H2: SparseHypergraph) -> None:
    assert IsalHGLevenshtein().pairwise(H1, H2) >= 0.0


# ---------------------------------------------------------------------------
# Axiom 2 — symmetry
# ---------------------------------------------------------------------------


@settings(max_examples=40, deadline=None)
@given(small_connected_hypergraph(), small_connected_hypergraph())
def test_symmetry(H1: SparseHypergraph, H2: SparseHypergraph) -> None:
    d = IsalHGLevenshtein()
    assert d.pairwise(H1, H2) == d.pairwise(H2, H1)


@settings(max_examples=40, deadline=None)
@given(labelled_hypergraph_pair())
def test_symmetry_labelled(pair: tuple[SparseHypergraph, SparseHypergraph]) -> None:
    H1, H2 = pair
    d = IsalHGLevenshtein()
    assert d.pairwise(H1, H2) == d.pairwise(H2, H1)


# ---------------------------------------------------------------------------
# Axiom 3 — triangle inequality
# ---------------------------------------------------------------------------


@settings(max_examples=30, deadline=None)
@given(
    small_connected_hypergraph(),
    small_connected_hypergraph(),
    small_connected_hypergraph(),
)
def test_triangle_inequality(
    H1: SparseHypergraph, H2: SparseHypergraph, H3: SparseHypergraph
) -> None:
    d = IsalHGLevenshtein()
    assert d.pairwise(H1, H3) <= d.pairwise(H1, H2) + d.pairwise(H2, H3)


@settings(max_examples=20, deadline=None)
@given(labelled_hypergraph_pair(), labelled_hypergraph_pair(), labelled_hypergraph_pair())
def test_triangle_inequality_labelled(
    p12: tuple[SparseHypergraph, SparseHypergraph],
    p23: tuple[SparseHypergraph, SparseHypergraph],
    p13: tuple[SparseHypergraph, SparseHypergraph],
) -> None:
    # Each pair shares a structure but has independent labellings.
    H1, _ = p12
    _, H3 = p13
    _, H2 = p23  # H2 drawn independently
    d = IsalHGLevenshtein()
    # Rebuild a fully independent triple; triangle inequality must hold regardless.
    assert d.pairwise(H1, H3) <= d.pairwise(H1, H2) + d.pairwise(H2, H3)


# ---------------------------------------------------------------------------
# Axiom 4 — identity of indiscernibles (unlabelled)
# d_I(H1, H2) == 0  iff  brute_force_iso(H1, H2)
# ---------------------------------------------------------------------------


@settings(max_examples=40, deadline=None)
@given(small_connected_hypergraph(), small_connected_hypergraph())
def test_identity_of_indiscernibles_unlabelled(H1: SparseHypergraph, H2: SparseHypergraph) -> None:
    is_zero = IsalHGLevenshtein().pairwise(H1, H2) == 0.0
    is_iso = brute_force_iso(H1, H2)
    assert is_zero == is_iso


# ---------------------------------------------------------------------------
# Axiom 4 — identity of indiscernibles (labelled, non-trivial vocabulary)
# The biconditional holds over F(H) = (seed label, w*_c(H)), not the bare
# string alone (T-TAb / Theorem A proof §Corollary A).
# ---------------------------------------------------------------------------


@settings(max_examples=80, deadline=None)
@given(labelled_hypergraph_pair())
def test_identity_of_indiscernibles_labelled(
    pair: tuple[SparseHypergraph, SparseHypergraph],
) -> None:
    H1, H2 = pair
    is_zero = IsalHGLevenshtein().pairwise(H1, H2) == 0.0
    is_iso = brute_force_iso(H1, H2)
    assert is_zero == is_iso


# ---------------------------------------------------------------------------
# Teeth check (T-TAe pattern): identity of indiscernibles FAILS when the
# ("seed", ell) prefix is removed from the token sequence.
#
# Witness: a 2-vertex hypergraph with one edge, differing only in the seed
# vertex's label (vertex_labels=[0,0] vs vertex_labels=[1,0]).  Both emit
# the same bare w*_c (the V-token creates the non-seed vertex with label 0
# in both cases), so without the prefix d_I = 0 on a non-isomorphic pair.
# With the prefix the seed labels differ by one substitution, giving d_I = 1.
# ---------------------------------------------------------------------------


def test_identity_fails_without_seed_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    """Regression: removing the seed-label prefix breaks identity of indiscernibles.

    This test ASSERTS FAILURE on the patched version to prove that the prefix
    is the load-bearing component.  Any refactor that removes the prefix would
    cause the un-patched `test_identity_of_indiscernibles_labelled` to fail.
    """
    H_same = SparseHypergraph(
        n_nodes=2, hyperedges=[frozenset({0, 1})], n_vertex_labels=2, vertex_labels=[0, 0]
    )
    H_diff = SparseHypergraph(
        n_nodes=2, hyperedges=[frozenset({0, 1})], n_vertex_labels=2, vertex_labels=[1, 0]
    )

    # Sanity: H_same and H_diff are genuinely non-isomorphic.
    assert not brute_force_iso(H_same, H_diff)

    # With the seed-label prefix: d_I = 1 (one substitution on the prefix symbol).
    d = IsalHGLevenshtein()
    assert d.pairwise(H_same, H_diff) == 1.0

    # Without the prefix (monkeypatch seed_vertex_label to a constant so both
    # sequences become byte-identical):  d_I = 0, identity fails.
    import isalhg.metric_space.distances.isalhg_levenshtein as mod

    monkeypatch.setattr(mod, "seed_vertex_label", lambda H, w: 0)
    d_no_prefix = IsalHGLevenshtein()
    # Both sequences now encode to the same string → distance is 0 on a non-iso pair.
    assert d_no_prefix.pairwise(H_same, H_diff) == 0.0


# ---------------------------------------------------------------------------
# (d) k-pinning: fixed k gives same distance regardless of argument order
# ---------------------------------------------------------------------------


@settings(max_examples=30, deadline=None)
@given(small_connected_hypergraph(), small_connected_hypergraph())
def test_auto_k_equals_explicit_max_k(H1: SparseHypergraph, H2: SparseHypergraph) -> None:
    """Auto k (pair maximum) is identical to passing k=max explicitly.

    Verifies the k-pinning convention in :meth:`IsalHGLevenshtein.pairwise`:
    the auto ``k = max(required_k(H1), required_k(H2))`` computes the same
    distance as a constructor-fixed ``k`` set to that same value.  Two
    distance values from different ``k`` settings are **not** comparable
    (d_I is a family {d_I^{k,h}}; index (k,h) must be fixed per corpus).
    """
    from isalhg.core.canonical import required_k

    k_max = max(required_k(H1), required_k(H2))
    d_auto = IsalHGLevenshtein()
    d_fixed = IsalHGLevenshtein(k=k_max)
    assert d_auto.pairwise(H1, H2) == d_fixed.pairwise(H1, H2)
