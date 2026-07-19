"""Property tests for the S2H/H2S round-trip."""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from isalhg.core.canonical import canonical_string, required_k
from isalhg.core.hypergraph_to_string import greedy_h2s
from isalhg.core.instructions import serialize
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.string_to_hypergraph import string_to_hypergraph

pytestmark = pytest.mark.property


def _arity_multiset(H: SparseHypergraph) -> list[int]:
    return sorted(len(H.members(e)) for e in H.edges())


@st.composite
def small_connected_hypergraph(draw, max_n: int = 6, max_arity: int = 3) -> SparseHypergraph:
    """Sample a small connected hypergraph by building a random spanning tree
    of 2-edges plus 0--2 extra hyperedges of arity 2..max_arity.
    """
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


@settings(max_examples=40, deadline=None)
@given(small_connected_hypergraph())
def test_round_trip_preserves_arity_profile(H: SparseHypergraph) -> None:
    k = required_k(H)
    tokens = greedy_h2s(H, seed_node=0, k=k)
    H_decoded = string_to_hypergraph(serialize(list(tokens)), k=k)
    assert H_decoded.n_nodes == H.n_nodes
    assert H_decoded.n_edges == H.n_edges
    assert _arity_multiset(H_decoded) == _arity_multiset(H)


@settings(max_examples=30, deadline=None)
@given(small_connected_hypergraph(max_n=5, max_arity=3))
def test_canonical_round_trip(H: SparseHypergraph) -> None:
    """``canonical(S2H(serialise(H2S(H)))) == canonical(H)``."""
    k = required_k(H)
    tokens = greedy_h2s(H, seed_node=0, k=k)
    H_decoded = string_to_hypergraph(serialize(list(tokens)), k=k)
    assert canonical_string(H_decoded, k=k) == canonical_string(H, k=k)


# ---------------------------------------------------------------------------
# Explicit backend-parity property tests (T-OPTb AC1c)
# ---------------------------------------------------------------------------


@settings(max_examples=40, deadline=None)
@given(small_connected_hypergraph(max_n=5, max_arity=3))
def test_python_backend_round_trip(H: SparseHypergraph) -> None:
    """Python backend: S2H(H2S(H)) ~ H (fingerprint equality)."""
    k = required_k(H)
    tokens = greedy_h2s(H, seed_node=0, k=k)
    H_decoded = string_to_hypergraph(serialize(list(tokens)), k=k, backend="python")
    assert canonical_string(H_decoded, k=k) == canonical_string(H, k=k)


@settings(max_examples=40, deadline=None)
@given(small_connected_hypergraph(max_n=5, max_arity=3))
def test_cpp_backend_round_trip(H: SparseHypergraph) -> None:
    """C++ backend: S2H(H2S(H)) ~ H (fingerprint equality, T-OPTb AC1)."""
    k = required_k(H)
    tokens = greedy_h2s(H, seed_node=0, k=k)
    H_decoded = string_to_hypergraph(serialize(list(tokens)), k=k, backend="cpp")
    assert canonical_string(H_decoded, k=k) == canonical_string(H, k=k)


@settings(max_examples=30, deadline=None)
@given(small_connected_hypergraph(max_n=5, max_arity=3))
def test_cpp_python_s2h_parity(H: SparseHypergraph) -> None:
    """C++ and Python S2H produce fingerprint-identical hypergraphs from the
    same encoded string (T-OPTb AC1 — parity on Hypothesis-random strings)."""
    k = required_k(H)
    tokens = greedy_h2s(H, seed_node=0, k=k)
    s = serialize(list(tokens))
    H_cpp = string_to_hypergraph(s, k=k, backend="cpp")
    H_py = string_to_hypergraph(s, k=k, backend="python")
    assert canonical_string(H_cpp, k=k) == canonical_string(H_py, k=k)
