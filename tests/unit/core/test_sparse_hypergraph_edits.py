"""Unit tests for the six structural edit operations on ``SparseHypergraph``.

Covers each unit edit (vertex/hyperedge insert-delete, incidence add-remove),
its preconditions, purity (the argument is never mutated), and the
``random_edit`` / ``edit_path`` samplers used by the perturbation ladder.
"""

from __future__ import annotations

import random

import pytest

from isalhg.core.sparse_hypergraph import (
    SparseHypergraph,
    add_incidence,
    delete_hyperedge,
    delete_vertex,
    edit_path,
    insert_hyperedge,
    insert_vertex,
    random_edit,
    remove_incidence,
)
from isalhg.errors import HypergraphEditError, InvalidLabelError

pytestmark = pytest.mark.unit

_OP_NAMES = {
    "insert_vertex",
    "delete_vertex",
    "insert_hyperedge",
    "delete_hyperedge",
    "add_incidence",
    "remove_incidence",
}


def _base() -> SparseHypergraph:
    """4 vertices, edges ``e0={0,1,2}``, ``e1={2,3}``; no isolated vertex."""
    return SparseHypergraph(n_nodes=4, hyperedges=[frozenset({0, 1, 2}), frozenset({2, 3})])


class TestInsertVertex:
    def test_appends_isolated_vertex(self) -> None:
        H = _base()
        out = insert_vertex(H)
        assert out.n_nodes == H.n_nodes + 1
        assert out.n_edges == H.n_edges
        assert out.degree(H.n_nodes) == 0
        # purity
        assert H.n_nodes == 4

    def test_label_is_applied(self) -> None:
        H = SparseHypergraph(
            n_nodes=2, hyperedges=[frozenset({0, 1})], n_vertex_labels=3, vertex_labels=[0, 1]
        )
        out = insert_vertex(H, label=2)
        assert out.vertex_label(2) == 2

    def test_out_of_range_label_raises(self) -> None:
        with pytest.raises(InvalidLabelError):
            insert_vertex(_base(), label=5)


class TestDeleteVertex:
    def test_delete_isolated(self) -> None:
        H = SparseHypergraph(n_nodes=3, hyperedges=[frozenset({0, 1})])
        assert H.degree(2) == 0
        out = delete_vertex(H, 2)
        assert out.n_nodes == 2
        assert out.n_edges == 1
        assert out.has_edge(frozenset({0, 1}))

    def test_renumbers_after_gap(self) -> None:
        H = SparseHypergraph(n_nodes=4, hyperedges=[frozenset({1, 2}), frozenset({2, 3})])
        assert H.degree(0) == 0
        out = delete_vertex(H, 0)
        assert out.n_nodes == 3
        # old {1,2} -> {0,1}; old {2,3} -> {1,2}
        assert out.has_edge(frozenset({0, 1}))
        assert out.has_edge(frozenset({1, 2}))
        # purity
        assert H.n_nodes == 4

    def test_non_isolated_raises(self) -> None:
        with pytest.raises(HypergraphEditError):
            delete_vertex(_base(), 0)

    def test_out_of_range_raises(self) -> None:
        with pytest.raises(HypergraphEditError):
            delete_vertex(_base(), 99)


class TestInsertHyperedge:
    def test_adds_edge(self) -> None:
        H = _base()
        out = insert_hyperedge(H, frozenset({0, 3}))
        assert out.n_edges == H.n_edges + 1
        assert out.has_edge(frozenset({0, 3}))
        # purity
        assert H.n_edges == 2

    def test_duplicate_raises(self) -> None:
        with pytest.raises(HypergraphEditError):
            insert_hyperedge(_base(), frozenset({0, 1, 2}))

    def test_empty_raises(self) -> None:
        with pytest.raises(HypergraphEditError):
            insert_hyperedge(_base(), frozenset())

    def test_out_of_range_vertex_raises(self) -> None:
        with pytest.raises(HypergraphEditError):
            insert_hyperedge(_base(), frozenset({0, 99}))

    def test_out_of_range_label_raises(self) -> None:
        with pytest.raises(HypergraphEditError):
            insert_hyperedge(_base(), frozenset({0, 3}), label=4)

    def test_label_distinguishes_same_memberset(self) -> None:
        H = SparseHypergraph(
            n_nodes=2, hyperedges=[frozenset({0, 1})], n_edge_labels=2, edge_labels=[0]
        )
        # Same member-set, different label -> not a duplicate.
        out = insert_hyperedge(H, frozenset({0, 1}), label=1)
        assert out.n_edges == 2


class TestDeleteHyperedge:
    def test_removes_edge(self) -> None:
        H = _base()
        out = delete_hyperedge(H, 0)
        assert out.n_edges == 1
        assert out.has_edge(frozenset({2, 3}))
        assert not out.has_edge(frozenset({0, 1, 2}))
        # purity
        assert H.n_edges == 2

    def test_out_of_range_raises(self) -> None:
        with pytest.raises(HypergraphEditError):
            delete_hyperedge(_base(), 5)


class TestAddIncidence:
    def test_grows_edge(self) -> None:
        H = _base()
        out = add_incidence(H, 0, 1)  # e1={2,3} gains v0
        assert out.members(1) == frozenset({0, 2, 3})
        # purity
        assert H.members(1) == frozenset({2, 3})

    def test_existing_member_raises(self) -> None:
        with pytest.raises(HypergraphEditError):
            add_incidence(_base(), 2, 0)  # v2 already in e0

    def test_would_duplicate_raises(self) -> None:
        H = SparseHypergraph(n_nodes=3, hyperedges=[frozenset({0, 1}), frozenset({0, 1, 2})])
        with pytest.raises(HypergraphEditError):
            add_incidence(H, 2, 0)  # {0,1}+2 == e1

    def test_out_of_range_raises(self) -> None:
        with pytest.raises(HypergraphEditError):
            add_incidence(_base(), 99, 0)


class TestRemoveIncidence:
    def test_shrinks_edge(self) -> None:
        H = _base()
        out = remove_incidence(H, 2, 0)  # e0={0,1,2} loses v2
        assert out.members(0) == frozenset({0, 1})
        # purity
        assert H.members(0) == frozenset({0, 1, 2})

    def test_not_member_raises(self) -> None:
        with pytest.raises(HypergraphEditError):
            remove_incidence(_base(), 3, 0)  # v3 not in e0

    def test_would_empty_raises(self) -> None:
        H = SparseHypergraph(n_nodes=2, hyperedges=[frozenset({0})])
        with pytest.raises(HypergraphEditError):
            remove_incidence(H, 0, 0)

    def test_would_duplicate_raises(self) -> None:
        H = SparseHypergraph(n_nodes=3, hyperedges=[frozenset({0, 1, 2}), frozenset({0, 1})])
        with pytest.raises(HypergraphEditError):
            remove_incidence(H, 2, 0)  # {0,1,2}-2 == e1


class TestRandomEditAndPath:
    def test_random_edit_returns_named_op(self) -> None:
        out, op = random_edit(_base(), random.Random(0))
        assert isinstance(out, SparseHypergraph)
        assert op in _OP_NAMES

    def test_random_edit_is_deterministic(self) -> None:
        a, op_a = random_edit(_base(), random.Random(7))
        b, op_b = random_edit(_base(), random.Random(7))
        assert op_a == op_b
        assert a == b

    def test_edit_path_reports_qin_budget(self) -> None:
        # The budget is the accumulated Qin-taxonomy cost: >= the op count,
        # equal only when no whole-hyperedge insert/delete occurred.
        out, budget = edit_path(_base(), 5, random.Random(1))
        assert budget >= 5
        assert isinstance(out, SparseHypergraph)

    def test_edit_path_is_deterministic(self) -> None:
        a, _ = edit_path(_base(), 8, random.Random(123))
        b, _ = edit_path(_base(), 8, random.Random(123))
        assert a == b

    def test_edit_path_zero_is_identity(self) -> None:
        H = _base()
        out, t = edit_path(H, 0, random.Random(0))
        assert t == 0
        assert out == H

    def test_edit_path_negative_raises(self) -> None:
        with pytest.raises(HypergraphEditError):
            edit_path(_base(), -1, random.Random(0))

    def test_edit_path_produces_valid_hypergraphs(self) -> None:
        # Every intermediate must remain a well-formed hypergraph (no crash,
        # contiguous IDs enforced by the constructor).
        rng = random.Random(2024)
        current = _base()
        for _ in range(25):
            current, op = random_edit(current, rng)
            assert op in _OP_NAMES
            assert current.n_nodes >= 0
            for e in range(current.n_edges):
                assert len(current.members(e)) >= 1
