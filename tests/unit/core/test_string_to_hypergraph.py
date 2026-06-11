"""Unit tests for :mod:`isalhg.core.string_to_hypergraph`."""

from __future__ import annotations

import pytest

from isalhg.core.string_to_hypergraph import StringToHypergraph, string_to_hypergraph
from isalhg.errors import InvalidInstructionError

pytestmark = pytest.mark.unit


class TestEmptyProgram:
    def test_empty_string_gives_single_node(self) -> None:
        H = string_to_hypergraph("", k=2)
        assert H.n_nodes == 1
        assert H.n_edges == 0


class TestVInstruction:
    def test_single_v_adds_one_edge(self) -> None:
        H = string_to_hypergraph("V[0;1;1;0]", k=2)
        assert H.n_nodes == 2
        assert H.n_edges == 1
        assert H.members(0) == frozenset({0, 1})

    def test_v_with_j_2(self) -> None:
        H = string_to_hypergraph("V[0;1;2;0,0]", k=3)
        assert H.n_nodes == 3
        assert H.n_edges == 1
        assert H.members(0) == frozenset({0, 1, 2})


class TestCInstruction:
    def test_c_over_pointed_nodes(self) -> None:
        H = string_to_hypergraph("V[0;1;2;0,0];P[1];C[0;2]", k=3)
        assert H.n_nodes == 3
        assert H.n_edges == 2

    def test_c_is_noop_when_edge_exists(self) -> None:
        H = string_to_hypergraph("V[0;1;1;0];C[0;2];C[0;2]", k=2)
        assert H.n_nodes == 2
        # one V edge {0,1} + one C edge {0} (deduped on second C)
        assert H.n_edges == 2


class TestPNW:
    def test_pn_movement(self) -> None:
        H1 = string_to_hypergraph("V[0;1;2;0,0]", k=3)
        H2 = string_to_hypergraph("V[0;1;2;0,0];P[1];N[1]", k=3)
        assert H1.n_nodes == H2.n_nodes
        assert H1.n_edges == H2.n_edges

    def test_w_noop(self) -> None:
        H1 = string_to_hypergraph("V[0;1;1;0]", k=2)
        H2 = string_to_hypergraph("W;V[0;1;1;0];W;W", k=2)
        assert H1.n_nodes == H2.n_nodes
        assert H1.n_edges == H2.n_edges
        assert list(H1.hyperedges()) == list(H2.hyperedges())


class TestValidation:
    def test_invalid_token_raises(self) -> None:
        with pytest.raises(InvalidInstructionError):
            string_to_hypergraph("V[0;5;1;0]", k=3)

    def test_class_form_run_with_trace(self) -> None:
        from isalhg.core.instructions import parse

        interp = StringToHypergraph(parse("V[0;1;1;0];P[1]"), k=2)
        H, trace = interp.run(trace=True)
        assert H.n_nodes == 2
        assert len(trace) == 2
