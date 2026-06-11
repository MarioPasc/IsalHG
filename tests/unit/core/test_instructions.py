"""Unit tests for :mod:`isalhg.core.instructions`."""

from __future__ import annotations

import pytest

from isalhg.core.instructions import (
    TokenC,
    TokenN,
    TokenP,
    TokenV,
    TokenW,
    parse,
    sequence_sort_key,
    serialize,
    validate,
)
from isalhg.errors import InvalidInstructionError

pytestmark = pytest.mark.unit


class TestSerialization:
    @pytest.mark.parametrize(
        "tok, expected",
        [
            (TokenW(), "W"),
            (TokenP(i=1), "P[1]"),
            (TokenN(i=3), "N[3]"),
            (TokenC(edge_label=0, i=2), "C[0;2]"),
            (TokenV(edge_label=0, i=1, j=2, new_node_labels=(0, 0)), "V[0;1;2;0,0]"),
            (TokenV(edge_label=2, i=2, j=1, new_node_labels=(5,)), "V[2;2;1;5]"),
        ],
    )
    def test_serialize_token(self, tok, expected: str) -> None:
        assert tok.serialize() == expected

    def test_serialize_sequence_empty(self) -> None:
        assert serialize([]) == ""

    def test_serialize_sequence_mixed(self) -> None:
        seq = [TokenN(i=1), TokenP(i=2), TokenV(edge_label=0, i=1, j=1, new_node_labels=(0,))]
        assert serialize(seq) == "N[1];P[2];V[0;1;1;0]"


class TestParse:
    @pytest.mark.parametrize(
        "s",
        [
            "W",
            "P[1]",
            "N[2]",
            "C[0;3]",
            "V[0;1;2;0,0]",
            "V[2;2;1;5]",
        ],
    )
    def test_single_token_round_trip(self, s: str) -> None:
        toks = parse(s)
        assert len(toks) == 1
        assert toks[0].serialize() == s

    def test_empty_string(self) -> None:
        assert parse("") == []

    def test_sequence_round_trip(self) -> None:
        s = "N[1];V[0;1;1;0];C[0;2];W"
        toks = parse(s)
        assert serialize(toks) == s

    @pytest.mark.parametrize(
        "bad",
        [
            "X",
            "V",
            "P[]",
            "V[0;1;1;0,0,0]",
            "C[0]",
            "V[0;1]",
            "P[1;2]",
            "P[abc]",
            "V[0;1;1;0",
        ],
    )
    def test_invalid(self, bad: str) -> None:
        with pytest.raises(InvalidInstructionError):
            parse(bad)


class TestValidate:
    def test_valid_program(self) -> None:
        toks = parse("V[0;1;2;0,0];C[0;3];P[1]")
        validate(toks, k=4)

    def test_v_out_of_range_i(self) -> None:
        toks = [TokenV(edge_label=0, i=4, j=1, new_node_labels=(0,))]
        with pytest.raises(InvalidInstructionError):
            validate(toks, k=4)

    def test_p_out_of_range(self) -> None:
        toks = [TokenP(i=5)]
        with pytest.raises(InvalidInstructionError):
            validate(toks, k=4)

    def test_v_arity_overflow(self) -> None:
        toks = [TokenV(edge_label=0, i=2, j=3, new_node_labels=(0, 0, 0))]
        with pytest.raises(InvalidInstructionError):
            validate(toks, k=4)

    def test_edge_label_out_of_range(self) -> None:
        toks = [TokenC(edge_label=2, i=2)]
        with pytest.raises(InvalidInstructionError):
            validate(toks, k=4, n_edge_labels=2)


class TestSortKey:
    def test_sequence_sort_key_length_first(self) -> None:
        s_short = [TokenW()]
        s_long = [TokenW(), TokenW()]
        assert sequence_sort_key(s_short) < sequence_sort_key(s_long)

    def test_v_over_c_within_same_cost(self) -> None:
        v = TokenV(edge_label=0, i=1, j=1, new_node_labels=(0,))
        c = TokenC(edge_label=0, i=1)
        assert v.sort_key() < c.sort_key()
