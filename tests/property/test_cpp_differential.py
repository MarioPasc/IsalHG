"""Differential property test: C++ ``greedy_h2s`` matches Python byte-for-byte.

The Python reference (``_python_greedy_h2s``) is kept alongside the
C++-backed entry to compare both implementations on randomly generated
small hypergraphs plus the canonical hand-built designs (Fano, STS(9),
a cyclic triple system on 13 points, GQ(2,2) doily).

A failure here means the C++ port has diverged from the Python
implementation — either the tie-breaking cascade, the displacement
enumeration order, or the V-branch backtracking semantics differ. Any
divergence breaks invariant 4 (canonical seed) for downstream consumers.

Both encoder modes are covered: the single-branch default and the
tie-complete search (``tie_branch=True``), whose per-seed output is the
one Theorem A's completeness biconditional is stated over.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from isalhg.core.canonical import required_k
from isalhg.core.hypergraph_to_string import _python_greedy_h2s, greedy_h2s
from isalhg.core.instructions import serialize
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.datasets.synthetic.designs import (
    cyclic_triple_orbit_13,
    fano_plane,
    gq_2_2_doily,
    sts_9,
)
from tests.property.test_canonical_invariance import small_connected_hypergraph

pytestmark = pytest.mark.property

_NAMED_FIXTURES = [
    ("fano", fano_plane()),
    ("sts9", sts_9()),
    ("c13_013", cyclic_triple_orbit_13((0, 1, 3))),
    ("doily", gq_2_2_doily()),
]


@pytest.mark.parametrize("name,H", _NAMED_FIXTURES)
def test_named_designs_byte_equal(name: str, H: SparseHypergraph) -> None:
    k = required_k(H)
    py = serialize(list(_python_greedy_h2s(H, seed_node=0, k=k)))
    cpp = serialize(list(greedy_h2s(H, seed_node=0, k=k)))
    assert py == cpp, f"{name}: C++ differs from Python"


@settings(max_examples=100, deadline=None)
@given(small_connected_hypergraph(max_n=6, max_arity=3))
def test_hypothesis_byte_equal(H: SparseHypergraph) -> None:
    k = required_k(H)
    py = serialize(list(_python_greedy_h2s(H, seed_node=0, k=k)))
    cpp = serialize(list(greedy_h2s(H, seed_node=0, k=k)))
    assert py == cpp


@settings(max_examples=40, deadline=None)
@given(
    small_connected_hypergraph(max_n=6, max_arity=3),
    st.integers(min_value=0, max_value=5),
)
def test_hypothesis_seed_byte_equal(H: SparseHypergraph, seed_node: int) -> None:
    if seed_node >= H.n_nodes:
        return
    k = required_k(H)
    py = serialize(list(_python_greedy_h2s(H, seed_node=seed_node, k=k)))
    cpp = serialize(list(greedy_h2s(H, seed_node=seed_node, k=k)))
    assert py == cpp


# ---------------------------------------------------------------------------
# Tie-complete mode (``tie_branch=True``) — the encoder Theorem A applies to.
# The Python reference costs ~0.5 s per Fano seed and ~19 s per STS(9) seed,
# so the designs are covered one seed at a time and STS(9) is marked slow.
# ---------------------------------------------------------------------------


def test_tie_complete_fano_byte_equal() -> None:
    H = fano_plane()
    k = required_k(H)
    py = serialize(list(_python_greedy_h2s(H, seed_node=0, k=k, inplace=True, tie_branch=True)))
    cpp = serialize(list(greedy_h2s(H, seed_node=0, k=k, tie_branch=True)))
    assert py == cpp


@pytest.mark.slow
def test_tie_complete_sts9_byte_equal() -> None:
    H = sts_9()
    k = required_k(H)
    py = serialize(list(_python_greedy_h2s(H, seed_node=0, k=k, inplace=True, tie_branch=True)))
    cpp = serialize(list(greedy_h2s(H, seed_node=0, k=k, tie_branch=True)))
    assert py == cpp


def test_tie_complete_counterexample_byte_equal() -> None:
    """The n=4 instance whose two edge orderings split the greedy encoder."""
    edges = [frozenset({1, 3}), frozenset({0, 1, 3}), frozenset({0, 2, 3}), frozenset({1, 2})]
    for order in ([0, 1, 2, 3], [1, 2, 3, 0]):
        H = SparseHypergraph(n_nodes=4, hyperedges=[edges[i] for i in order])
        for seed_node in range(H.n_nodes):
            py = serialize(
                list(_python_greedy_h2s(H, seed_node=seed_node, k=3, inplace=True, tie_branch=True))
            )
            cpp = serialize(list(greedy_h2s(H, seed_node=seed_node, k=3, tie_branch=True)))
            assert py == cpp, f"order={order} seed={seed_node}"


@settings(max_examples=50, deadline=None)
@given(small_connected_hypergraph(max_n=5, max_arity=3))
def test_tie_complete_hypothesis_byte_equal(H: SparseHypergraph) -> None:
    k = required_k(H)
    py = serialize(list(_python_greedy_h2s(H, seed_node=0, k=k, inplace=True, tie_branch=True)))
    cpp = serialize(list(greedy_h2s(H, seed_node=0, k=k, tie_branch=True)))
    assert py == cpp


@settings(max_examples=30, deadline=None)
@given(
    small_connected_hypergraph(max_n=5, max_arity=3),
    st.integers(min_value=0, max_value=4),
)
def test_tie_complete_hypothesis_seed_byte_equal(H: SparseHypergraph, seed_node: int) -> None:
    if seed_node >= H.n_nodes:
        return
    k = required_k(H)
    py = serialize(
        list(_python_greedy_h2s(H, seed_node=seed_node, k=k, inplace=True, tie_branch=True))
    )
    cpp = serialize(list(greedy_h2s(H, seed_node=seed_node, k=k, tie_branch=True)))
    assert py == cpp
