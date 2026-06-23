"""Differential property test: C++ ``greedy_h2s`` matches Python byte-for-byte.

The Python reference (``_python_greedy_h2s``) is kept alongside the
C++-backed entry to compare both implementations on randomly generated
small hypergraphs plus the canonical hand-built designs (Fano, STS(9),
STS(13), GQ(2,2) doily).

A failure here means the C++ port has diverged from the Python
implementation — either the tie-breaking cascade, the displacement
enumeration order, or the V-branch backtracking semantics differ. Any
divergence breaks invariant 4 (canonical seed) for downstream consumers.
"""

from __future__ import annotations

import itertools

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from isalhg.core.canonical import required_k
from isalhg.core.hypergraph_to_string import _python_greedy_h2s, greedy_h2s
from isalhg.core.instructions import serialize
from isalhg.core.sparse_hypergraph import SparseHypergraph
from tests.property.test_canonical_invariance import small_connected_hypergraph

pytestmark = pytest.mark.property


def _fano() -> SparseHypergraph:
    edges = [
        [0, 1, 2],
        [0, 3, 4],
        [0, 5, 6],
        [1, 3, 5],
        [1, 4, 6],
        [2, 3, 6],
        [2, 4, 5],
    ]
    return SparseHypergraph(n_nodes=7, hyperedges=edges)


def _sts9() -> SparseHypergraph:
    edges = [
        [0, 1, 2],
        [3, 4, 5],
        [6, 7, 8],
        [0, 3, 6],
        [1, 4, 7],
        [2, 5, 8],
        [0, 4, 8],
        [1, 5, 6],
        [2, 3, 7],
        [0, 5, 7],
        [1, 3, 8],
        [2, 4, 6],
    ]
    return SparseHypergraph(n_nodes=9, hyperedges=edges)


def _sts13() -> SparseHypergraph:
    edges = [[i, (i + 1) % 13, (i + 3) % 13] for i in range(13)]
    return SparseHypergraph(n_nodes=13, hyperedges=edges)


def _doily() -> SparseHypergraph:
    pairs = list(itertools.combinations(range(1, 7), 2))
    pair_id = {p: i for i, p in enumerate(pairs)}

    def _matchings(elements: tuple[int, ...]) -> list[tuple[tuple[int, int], ...]]:
        if not elements:
            return [()]
        a = elements[0]
        rest = elements[1:]
        out: list[tuple[tuple[int, int], ...]] = []
        for i, b in enumerate(rest):
            new_rest = rest[:i] + rest[i + 1 :]
            for tail in _matchings(new_rest):
                out.append(((a, b),) + tail)
        return out

    lines = [sorted(pair_id[tuple(sorted(p))] for p in m) for m in _matchings(tuple(range(1, 7)))]
    return SparseHypergraph(n_nodes=15, hyperedges=lines)


_NAMED_FIXTURES = [
    ("fano", _fano()),
    ("sts9", _sts9()),
    ("sts13", _sts13()),
    ("doily", _doily()),
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
