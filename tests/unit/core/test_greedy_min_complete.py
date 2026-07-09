"""Unit tests for the tie-complete encoder (``greedy_min_complete``).

Pins the minimal counterexample showing that the single-branch greedy
variants are functions of the *presentation* (edge insertion order), not
of the abstract hypergraph, and asserts that the tie-complete variant
removes that dependence. Found during T-TA (Theorem A / completeness).
"""

from __future__ import annotations

import pytest

from isalhg.core.algorithms.registry import available_algorithms, get_algorithm
from isalhg.core.canonical import canonical_string
from isalhg.core.instructions import serialize
from isalhg.core.sparse_hypergraph import SparseHypergraph, permute

pytestmark = pytest.mark.unit

# Minimal counterexample (n=4, m=4): primal graph is K4, so xi = (3, 0, 0)
# for every vertex and eta ties on every arity-2 candidate; the residual
# min-edge-id tie-break then makes w* depend on edge insertion order.
_CE_EDGES: list[frozenset[int]] = [
    frozenset({1, 3}),
    frozenset({0, 1, 3}),
    frozenset({0, 2, 3}),
    frozenset({1, 2}),
]
# Rotation of the same edge list -- same abstract hypergraph.
_CE_ORDER_B: list[int] = [1, 2, 3, 0]


def _presentation_a() -> SparseHypergraph:
    return SparseHypergraph(n_nodes=4, hyperedges=_CE_EDGES)


def _presentation_b() -> SparseHypergraph:
    return SparseHypergraph(n_nodes=4, hyperedges=[_CE_EDGES[i] for i in _CE_ORDER_B])


def test_counterexample_presentations_are_the_same_hypergraph() -> None:
    assert _presentation_a() == _presentation_b()


@pytest.mark.parametrize("algorithm", ["greedy_min_nbrdeg", "greedy_min"])
def test_greedy_is_edge_order_dependent_known_limitation(algorithm: str) -> None:
    """Documents the known limitation: if this starts failing, the greedy
    tie-break changed and the completeness analysis must be revisited."""
    w_a = canonical_string(_presentation_a(), k=3, algorithm=algorithm)
    w_b = canonical_string(_presentation_b(), k=3, algorithm=algorithm)
    assert w_a != w_b


def test_complete_is_edge_order_invariant_on_counterexample() -> None:
    w_a = canonical_string(_presentation_a(), k=3, algorithm="greedy_min_complete")
    w_b = canonical_string(_presentation_b(), k=3, algorithm="greedy_min_complete")
    assert w_a == w_b


def test_complete_is_invariant_under_perm_plus_reorder() -> None:
    H = _presentation_a()
    w_ref = canonical_string(H, k=3, algorithm="greedy_min_complete")
    sigma = [2, 0, 3, 1]
    H_iso = permute(H, sigma)
    H_iso_reordered = SparseHypergraph(
        n_nodes=4,
        hyperedges=[m for _, m, _ in H_iso.iter_edges()][::-1],
    )
    assert canonical_string(H_iso_reordered, k=3, algorithm="greedy_min_complete") == w_ref


def test_complete_registered_and_encode_matches_canonical_string() -> None:
    """``encode()`` is the Python reference; ``canonical_string`` is the C++
    twin (native variant 7). This assertion is therefore a differential."""
    assert "greedy_min_complete" in available_algorithms()
    H = _presentation_a()
    algo = get_algorithm("greedy_min_complete", k=3)
    assert serialize(list(algo.encode(H))) == canonical_string(
        H, k=3, algorithm="greedy_min_complete"
    )


def test_complete_cpp_matches_python_backend_on_counterexample() -> None:
    for H in (_presentation_a(), _presentation_b()):
        cpp = canonical_string(H, k=3, algorithm="greedy_min_complete", backend="cpp")
        py = canonical_string(H, k=3, algorithm="greedy_min_complete", backend="python")
        assert cpp == py


def test_complete_on_fano_invariant_under_reorder(fano_plane: SparseHypergraph) -> None:
    w_ref = canonical_string(fano_plane, k=3, algorithm="greedy_min_complete")
    reordered = SparseHypergraph(
        n_nodes=fano_plane.n_nodes,
        hyperedges=[m for _, m, _ in fano_plane.iter_edges()][::-1],
    )
    assert canonical_string(reordered, k=3, algorithm="greedy_min_complete") == w_ref


@pytest.mark.slow
@pytest.mark.parametrize("fixture_name", ["sts_9", "gq_2_2_doily"])
def test_complete_on_designs_invariant_under_reorder(
    fixture_name: str, request: pytest.FixtureRequest
) -> None:
    H: SparseHypergraph = request.getfixturevalue(fixture_name)
    k = max(len(m) for _, m, _ in H.iter_edges())
    w_ref = canonical_string(H, k=k, algorithm="greedy_min_complete")
    reordered = SparseHypergraph(
        n_nodes=H.n_nodes,
        hyperedges=[m for _, m, _ in H.iter_edges()][::-1],
    )
    assert canonical_string(reordered, k=k, algorithm="greedy_min_complete") == w_ref


def test_complete_differs_from_greedy_on_sts13() -> None:
    """The coherent-tie regime is not universal on designs.

    Fano and STS(9) satisfy ``w*_greedy == w*_complete``: every tie reached
    along their searches is automorphism-coherent. The cyclic 13-point triple
    system reaches a tie that is not, so its greedy string is not the canonical
    one. If this starts passing, the greedy tie-break changed.
    """
    H = SparseHypergraph(
        n_nodes=13, hyperedges=[[i, (i + 1) % 13, (i + 3) % 13] for i in range(13)]
    )
    greedy = canonical_string(H, k=3, algorithm="greedy_min_nbrdeg")
    complete = canonical_string(H, k=3, algorithm="greedy_min_complete")
    assert greedy != complete


@pytest.mark.slow
def test_complete_differs_from_greedy_on_doily(gq_2_2_doily: SparseHypergraph) -> None:
    """Vertex-transitivity does not buy *recursive* tie-coherence.

    GQ(2,2) is vertex-transitive, so every tie at the root is automorphism-
    coherent, yet the stabiliser of the partial map shrinks as the search
    descends and the greedy string still misses the canonical one. Together
    with the cyclic-13 system this is the second design supporting that
    reading; the proof's Remark on recursive coherence rests on both.
    """
    greedy = canonical_string(gq_2_2_doily, k=3, algorithm="greedy_min_nbrdeg")
    complete = canonical_string(gq_2_2_doily, k=3, algorithm="greedy_min_complete")
    assert greedy != complete
