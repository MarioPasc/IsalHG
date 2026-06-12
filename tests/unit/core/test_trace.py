"""Tests for :mod:`isalhg.core.trace`."""

from __future__ import annotations

import pytest

from isalhg.core.algorithms.greedy_min import GreedyMin
from isalhg.core.canonical import required_k
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.string_to_hypergraph import StringToHypergraph
from isalhg.core.trace import (
    AlgorithmTrace,
    StepSnapshot,
    dump_trace,
    hypergraph_to_hif,
    load_trace,
)

pytestmark = pytest.mark.unit


def _fano() -> SparseHypergraph:
    return SparseHypergraph(
        n_nodes=7,
        hyperedges=[
            frozenset({0, 1, 2}),
            frozenset({0, 3, 4}),
            frozenset({0, 5, 6}),
            frozenset({1, 3, 5}),
            frozenset({1, 4, 6}),
            frozenset({2, 3, 6}),
            frozenset({2, 4, 5}),
        ],
    )


def test_hypergraph_to_hif_schema() -> None:
    H = _fano()
    hif = hypergraph_to_hif(H)
    assert hif["network-type"] == "undirected"
    assert hif["metadata"]["n_nodes"] == 7
    assert hif["metadata"]["n_edges"] == 7
    assert len(hif["nodes"]) == 7
    assert len(hif["edges"]) == 7
    # Every hyperedge contributes |members| incidences.
    assert len(hif["incidences"]) == sum(len(H.members(e)) for e in H.edges())


def test_step_snapshot_round_trip() -> None:
    snap = StepSnapshot(
        step_idx=3,
        token="P[1]",
        token_kind="P",
        cdll_node_order=(0, 1, 2),
        pointer_node_values=(1, 0, 2),
        active_nodes=(0, 1, 2),
        active_edges=(0,),
        partial_string="V[0;1;1;0];P[1];C[0;1]",
    )
    obj = snap.to_json()
    snap2 = StepSnapshot.from_json(obj)
    assert snap == snap2


def test_algorithm_trace_round_trip(tmp_path) -> None:
    H = _fano()
    algo = GreedyMin(k=required_k(H))
    tokens, trace = algo.encode_with_trace(H)
    # |snapshots| = |tokens| + 1
    assert len(trace.snapshots) == len(tokens) + 1
    assert trace.direction == "h2s"
    # Initial snapshot has the seed only.
    assert trace.snapshots[0].active_nodes == (0,)
    assert trace.snapshots[0].active_edges == ()
    # Final snapshot covers the full hypergraph.
    assert set(trace.snapshots[-1].active_nodes) == set(H.nodes())
    assert set(trace.snapshots[-1].active_edges) == set(H.edges())
    # JSON round-trip.
    path = tmp_path / "fano_trace.json"
    dump_trace(trace, path)
    loaded = load_trace(path)
    assert loaded.direction == trace.direction
    assert loaded.k == trace.k
    assert loaded.snapshots == trace.snapshots
    assert loaded.final_hif == trace.final_hif


def test_s2h_trace_consistency_with_h2s() -> None:
    H = _fano()
    k = required_k(H)
    algo = GreedyMin(k=k)
    tokens, h2s_trace = algo.encode_with_trace(H)
    interpreter = StringToHypergraph(tokens, k=k)
    _, s2h_trace = interpreter.run_with_trace(direction="s2h")
    # Same canonical string -> identical state trajectories.
    assert (
        s2h_trace.snapshots
        == AlgorithmTrace(
            direction="s2h",
            k=h2s_trace.k,
            n_vertex_labels=h2s_trace.n_vertex_labels,
            n_edge_labels=h2s_trace.n_edge_labels,
            final_hif=h2s_trace.final_hif,
            snapshots=h2s_trace.snapshots,
        ).snapshots
    )


def test_active_sets_monotonic() -> None:
    H = _fano()
    algo = GreedyMin(k=required_k(H))
    _, trace = algo.encode_with_trace(H)
    prev_v: frozenset[int] = frozenset()
    prev_e: frozenset[int] = frozenset()
    for snap in trace.snapshots:
        v = frozenset(snap.active_nodes)
        e = frozenset(snap.active_edges)
        assert prev_v.issubset(v), f"vertex set regressed at step {snap.step_idx}"
        assert prev_e.issubset(e), f"edge set regressed at step {snap.step_idx}"
        prev_v, prev_e = v, e
