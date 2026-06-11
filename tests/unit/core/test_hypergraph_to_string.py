"""Unit tests for :mod:`isalhg.core.hypergraph_to_string`."""

from __future__ import annotations

import pytest

from isalhg.core.canonical import required_k
from isalhg.core.hypergraph_to_string import greedy_h2s
from isalhg.core.instructions import serialize
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.string_to_hypergraph import string_to_hypergraph

pytestmark = pytest.mark.unit


def _arity_multiset(H: SparseHypergraph) -> list[int]:
    return sorted(len(H.members(e)) for e in H.edges())


@pytest.mark.parametrize(
    "fixture_name,seed_node",
    [
        ("trivial_hypergraph", 0),
        ("single_edge_hypergraph", 0),
        ("fano_plane", 0),
        ("sts_9", 0),
    ],
)
def test_round_trip_to_isomorphic_decoded(
    request: pytest.FixtureRequest,
    fixture_name: str,
    seed_node: int,
) -> None:
    H: SparseHypergraph = request.getfixturevalue(fixture_name)
    k = required_k(H)
    tokens = greedy_h2s(H, seed_node=seed_node, k=k)
    s = serialize(list(tokens))
    H_decoded = string_to_hypergraph(s, k=k)
    assert H_decoded.n_nodes == H.n_nodes
    assert H_decoded.n_edges == H.n_edges
    assert _arity_multiset(H_decoded) == _arity_multiset(H)


def test_seed_invariance_on_vertex_transitive(
    fano_plane: SparseHypergraph,
) -> None:
    """On a vertex-transitive structure, every seed yields the same token sequence."""
    k = required_k(fano_plane)
    sequences = [greedy_h2s(fano_plane, seed_node=v, k=k) for v in fano_plane.nodes()]
    serialised = [serialize(list(seq)) for seq in sequences]
    assert len(set(serialised)) == 1, f"Fano seeds disagree: {set(serialised)}"
