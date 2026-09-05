"""The flat incidence-list baseline and its strict decoder.

The decoder's job is to *reject*, so the bulk of this file is one test per
rejection rule, each feeding a minimal hand-built sequence that violates exactly
one constraint. Rule coverage is asserted explicitly at the end: if a rule is
added to the grammar without a test, ``test_every_documented_rule_is_exercised``
fails.

The round-trip test pins the other half of the contract -- on a well-formed
sequence the decoder must return the *same* knowledge base, not merely an
isomorphic one, since the baseline serializes constants by id.
"""

from __future__ import annotations

import random

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.generation.incidence_baseline import (
    CONST_TAG,
    COUNT_TAG,
    END_TAG,
    FACT_TAG,
    PRED_TAG,
    TYPE_TAG,
    flatten,
    strict_decode,
    strict_decode_reason,
)

pytestmark = pytest.mark.unit

N_TYPES = 3
N_PREDS = 2


def _kb() -> SparseHypergraph:
    """A 4-constant, 2-fact labelled knowledge base."""
    return SparseHypergraph(
        4,
        [frozenset({0, 1, 2}), frozenset({2, 3})],
        n_vertex_labels=N_TYPES,
        n_edge_labels=N_PREDS,
        vertex_labels=[0, 1, 2, 0],
        edge_labels=[0, 1],
    )


def _decode(tokens: object) -> SparseHypergraph | None:
    return strict_decode(tokens, n_types=N_TYPES, n_preds=N_PREDS)  # type: ignore[arg-type]


def _reason(tokens: object) -> str | None:
    return strict_decode_reason(tokens, n_types=N_TYPES, n_preds=N_PREDS)  # type: ignore[arg-type]


def _same(a: SparseHypergraph, b: SparseHypergraph) -> bool:
    """Identity, not isomorphism: same ids, same types, same predicates."""
    if (a.n_nodes, a.n_edges) != (b.n_nodes, b.n_edges):
        return False
    if [a.vertex_label(v) for v in range(a.n_nodes)] != [
        b.vertex_label(v) for v in range(b.n_nodes)
    ]:
        return False
    return sorted((sorted(m), ell) for _, m, ell in a.iter_edges()) == sorted(
        (sorted(m), ell) for _, m, ell in b.iter_edges()
    )


# ---------------------------------------------------------------------------
# Encoding and round-trip
# ---------------------------------------------------------------------------


class TestFlatten:
    def test_layout(self) -> None:
        tokens = flatten(_kb())
        assert tokens[0] == (COUNT_TAG, 4)
        assert tokens[1:5] == ((TYPE_TAG, 0), (TYPE_TAG, 1), (TYPE_TAG, 2), (TYPE_TAG, 0))
        assert tokens[-1] == (END_TAG,)
        assert tokens.count((FACT_TAG,)) == 2

    def test_length_is_header_plus_types_plus_facts_plus_end(self) -> None:
        H = _kb()
        expected = 1 + H.n_nodes + sum(2 + len(H.members(e)) for e in H.edges()) + 1
        assert len(flatten(H)) == expected

    def test_round_trip_is_identity(self) -> None:
        H = _kb()
        decoded = _decode(flatten(H))
        assert decoded is not None
        assert _same(decoded, H)

    def test_round_trip_on_random_knowledge_bases(self) -> None:
        rng = random.Random(0)
        for _ in range(80):
            n = rng.randint(3, 9)
            edges = {frozenset(rng.sample(range(n), rng.randint(2, min(4, n)))) for _ in range(4)}
            members = sorted(edges, key=sorted)
            H = SparseHypergraph(
                n,
                members,
                n_vertex_labels=N_TYPES,
                n_edge_labels=N_PREDS,
                vertex_labels=[rng.randrange(N_TYPES) for _ in range(n)],
                edge_labels=[rng.randrange(N_PREDS) for _ in members],
            )
            decoded = _decode(flatten(H))
            assert decoded is not None
            assert _same(decoded, H)

    def test_isolated_constant_survives(self) -> None:
        """The header carries ``n``, so a constant in no fact is not lost."""
        H = SparseHypergraph(
            3,
            [frozenset({0, 1})],
            n_vertex_labels=N_TYPES,
            n_edge_labels=N_PREDS,
            vertex_labels=[0, 1, 2],
            edge_labels=[0],
        )
        decoded = _decode(flatten(H))
        assert decoded is not None
        assert decoded.n_nodes == 3
        assert decoded.degree(2) == 0


# ---------------------------------------------------------------------------
# One test per rejection rule
# ---------------------------------------------------------------------------


class TestRejectionRules:
    """Each case violates exactly one rule and must return ``None``."""

    def test_missing_header(self) -> None:
        tokens = flatten(_kb())[1:]
        assert _decode(tokens) is None
        assert _reason(tokens) == "header"

    def test_header_not_first(self) -> None:
        base = flatten(_kb())
        tokens = (base[1], base[0], *base[2:])
        assert _decode(tokens) is None
        assert _reason(tokens) == "header"

    def test_empty_sequence(self) -> None:
        assert _decode(()) is None
        assert _reason(()) == "header"

    def test_duplicate_header(self) -> None:
        base = flatten(_kb())
        tokens = (*base[:3], (COUNT_TAG, 4), *base[3:])
        assert _decode(tokens) is None
        assert _reason(tokens) == "duplicate_header"

    def test_negative_declared_count(self) -> None:
        base = flatten(_kb())
        tokens = ((COUNT_TAG, -1), *base[1:])
        assert _decode(tokens) is None
        assert _reason(tokens) == "negative_count"

    def test_out_of_range_constant_id(self) -> None:
        """The characteristic sampler failure: an id past the declared count."""
        base = list(flatten(_kb()))
        index = base.index((CONST_TAG, 0))
        base[index] = (CONST_TAG, 99)
        assert _decode(tuple(base)) is None
        assert _reason(tuple(base)) == "constant_id"

    def test_arity_below_two(self) -> None:
        tokens = (
            (COUNT_TAG, 2),
            (TYPE_TAG, 0),
            (TYPE_TAG, 0),
            (FACT_TAG,),
            (PRED_TAG, 0),
            (CONST_TAG, 0),
            (END_TAG,),
        )
        assert _decode(tokens) is None
        assert _reason(tokens) == "arity"

    def test_arity_below_two_after_duplicate_ids_collapse(self) -> None:
        """``C 0 C 0`` denotes a one-element set, so it is a unary statement."""
        tokens = (
            (COUNT_TAG, 2),
            (TYPE_TAG, 0),
            (TYPE_TAG, 0),
            (FACT_TAG,),
            (PRED_TAG, 0),
            (CONST_TAG, 0),
            (CONST_TAG, 0),
            (END_TAG,),
        )
        assert _decode(tokens) is None
        assert _reason(tokens) == "arity"

    def test_duplicate_fact(self) -> None:
        tokens = (
            (COUNT_TAG, 2),
            (TYPE_TAG, 0),
            (TYPE_TAG, 0),
            (FACT_TAG,),
            (PRED_TAG, 0),
            (CONST_TAG, 0),
            (CONST_TAG, 1),
            (FACT_TAG,),
            (PRED_TAG, 0),
            (CONST_TAG, 0),
            (CONST_TAG, 1),
            (END_TAG,),
        )
        assert _decode(tokens) is None
        assert _reason(tokens) == "duplicate_fact"

    def test_same_members_different_predicate_is_accepted(self) -> None:
        """Only a repeated ``(predicate, member set)`` is a duplicate."""
        tokens = (
            (COUNT_TAG, 2),
            (TYPE_TAG, 0),
            (TYPE_TAG, 0),
            (FACT_TAG,),
            (PRED_TAG, 0),
            (CONST_TAG, 0),
            (CONST_TAG, 1),
            (FACT_TAG,),
            (PRED_TAG, 1),
            (CONST_TAG, 0),
            (CONST_TAG, 1),
            (END_TAG,),
        )
        decoded = _decode(tokens)
        assert decoded is not None
        assert decoded.n_edges == 2

    def test_dangling_constant_outside_a_fact(self) -> None:
        tokens = (
            (COUNT_TAG, 2),
            (TYPE_TAG, 0),
            (TYPE_TAG, 0),
            (CONST_TAG, 0),
            (END_TAG,),
        )
        assert _decode(tokens) is None
        assert _reason(tokens) == "dangling"

    def test_dangling_predicate_outside_a_fact(self) -> None:
        tokens = ((COUNT_TAG, 1), (TYPE_TAG, 0), (PRED_TAG, 0), (END_TAG,))
        assert _decode(tokens) is None
        assert _reason(tokens) == "dangling"

    def test_fact_left_open_at_end(self) -> None:
        tokens = ((COUNT_TAG, 1), (TYPE_TAG, 0), (FACT_TAG,), (END_TAG,))
        assert _decode(tokens) is None
        assert _reason(tokens) == "dangling"

    def test_type_token_inside_a_fact(self) -> None:
        tokens = (
            (COUNT_TAG, 2),
            (TYPE_TAG, 0),
            (FACT_TAG,),
            (PRED_TAG, 0),
            (TYPE_TAG, 0),
            (END_TAG,),
        )
        assert _decode(tokens) is None
        assert _reason(tokens) == "dangling"

    def test_missing_terminator(self) -> None:
        tokens = flatten(_kb())[:-1]
        assert _decode(tokens) is None
        assert _reason(tokens) == "terminator"

    def test_tokens_after_terminator(self) -> None:
        tokens = (*flatten(_kb()), (TYPE_TAG, 0))
        assert _decode(tokens) is None
        assert _reason(tokens) == "terminator"

    def test_type_count_mismatch(self) -> None:
        base = flatten(_kb())
        tokens = (base[0], *base[2:])  # one T token short of the declared 4
        assert _decode(tokens) is None
        assert _reason(tokens) == "type_count"

    def test_type_id_outside_vocabulary(self) -> None:
        base = list(flatten(_kb()))
        base[1] = (TYPE_TAG, N_TYPES)
        assert _decode(tuple(base)) is None
        assert _reason(tuple(base)) == "type_id"

    def test_predicate_id_outside_vocabulary(self) -> None:
        base = list(flatten(_kb()))
        base[base.index((PRED_TAG, 0))] = (PRED_TAG, N_PREDS)
        assert _decode(tuple(base)) is None
        assert _reason(tuple(base)) == "pred_id"

    @pytest.mark.parametrize(
        "tokens",
        [
            ((COUNT_TAG, 1, 2), (END_TAG,)),
            ((COUNT_TAG, "x"), (END_TAG,)),
            ((COUNT_TAG, 1), (TYPE_TAG,), (END_TAG,)),
            ((COUNT_TAG, 1), (TYPE_TAG, -1), (END_TAG,)),
            ((COUNT_TAG, 1), ("BOGUS",), (END_TAG,)),
            ((COUNT_TAG, 1), (TYPE_TAG, 0), (END_TAG, 1)),
            ("not a tuple",),
            ((),),
        ],
    )
    def test_malformed_tokens(self, tokens: tuple[object, ...]) -> None:
        assert _decode(tokens) is None

    def test_bool_is_not_an_id(self) -> None:
        """``True`` is an ``int`` in Python; the grammar must not accept it as an id."""
        tokens = ((COUNT_TAG, 1), (TYPE_TAG, True), (END_TAG,))
        assert _decode(tokens) is None

    def test_bad_vocabulary_sizes_are_rejected(self) -> None:
        assert strict_decode(flatten(_kb()), n_types=0, n_preds=1) is None
        assert strict_decode(flatten(_kb()), n_types=1, n_preds=0) is None

    def test_every_documented_rule_is_exercised(self) -> None:
        """Guard: every rule name the decoder can emit has a test above."""
        exercised = {
            "header",
            "duplicate_header",
            "negative_count",
            "constant_id",
            "arity",
            "duplicate_fact",
            "dangling",
            "terminator",
            "type_count",
            "type_id",
            "pred_id",
            "token_shape",
        }
        import inspect

        from isalhg.generation import incidence_baseline

        source = inspect.getsource(incidence_baseline._decode)
        emitted = set(re_findall(source))
        assert emitted == exercised, f"rule set changed: {emitted ^ exercised}"


def re_findall(source: str) -> list[str]:
    """Rule names the decoder returns, read off its source.

    Two shapes occur: ``return None, "rule"`` in the main loop and a bare
    ``return "rule"`` in the nested ``close_open`` helper, which hands its rule
    name back to the loop. Both must be scanned or the guard silently under-
    reports -- which is exactly what it did on first run.
    """
    import re

    return re.findall(r'return (?:None, )?"([a-z_]+)"', source)
