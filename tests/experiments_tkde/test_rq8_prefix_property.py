"""Proposition C.8 as a property test.

*Appending instructions to an ordered-walk program never removes a fact or a
constant, and never disconnects.* Every RQ8 completion rests on this: it is why
``ow_ngram``'s validity and connectivity are 1.000 by theorem rather than by
filtering (H8.3), and why a proposal can be compared with the truth at all.

The property is asserted on random continuations of real ordered-walk programs.
The continuation alphabet is the program's own token vocabulary, which is the
relevant one: those are the tokens a model fitted on such programs can emit.
"""

from __future__ import annotations

import random

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from experiments.tkde.rq8 import certificate, ow_tokens
from isalhg.core.canonical import required_k
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.string_to_hypergraph import string_to_hypergraph
from isalhg.iso_backends.isal_ordered import ordered_fingerprint

pytestmark = pytest.mark.property


def _kb(n: int, facts, types=None, n_types: int = 2, n_preds: int = 3) -> SparseHypergraph:
    return SparseHypergraph(
        n,
        [frozenset(members) for _label, members in facts],
        n_vertex_labels=n_types,
        n_edge_labels=n_preds,
        vertex_labels=list(types if types is not None else [0] * n),
        edge_labels=[label for label, _members in facts],
    )


#: Four connected knowledge bases with different shapes: a star, a chain, a
#: triangle with a pendant, and one carrying an arity-3 fact.
BASES: tuple[SparseHypergraph, ...] = (
    _kb(4, [(0, (0, 1)), (1, (0, 2)), (2, (0, 3))], [0, 1, 1, 1]),
    _kb(4, [(0, (0, 1)), (1, (1, 2)), (2, (2, 3))], [0, 1, 1, 1]),
    _kb(4, [(0, (0, 1)), (0, (1, 2)), (1, (0, 2)), (2, (2, 3))], [0, 0, 1, 1]),
    _kb(5, [(0, (0, 1, 2)), (1, (2, 3)), (2, (3, 4))], [0, 1, 1, 0, 1]),
)


def _program(H: SparseHypergraph) -> tuple[int, tuple[str, ...], int]:
    root_label, word = ordered_fingerprint(H)
    return int(root_label), ow_tokens(word), max(2, required_k(H))


def _decode(tokens, k: int, H: SparseHypergraph, root_label: int) -> SparseHypergraph:
    return string_to_hypergraph(
        ";".join(str(token) for token in tokens),
        k=k,
        n_vertex_labels=H.n_vertex_labels,
        n_edge_labels=H.n_edge_labels,
        seed_label=root_label,
        backend="python",
    )


def _facts(H: SparseHypergraph) -> set[tuple[int, frozenset[int]]]:
    return {(label, frozenset(members)) for _e, members, label in H.iter_edges()}


class TestPropositionC8:
    """The prefix property, on every base and a deterministic set of suffixes."""

    @pytest.mark.parametrize("base", BASES, ids=["star", "chain", "triangle", "arity3"])
    def test_the_prefix_alone_reproduces_the_input(self, base):
        root_label, prefix, k = _program(base)
        decoded = _decode(prefix, k, base, root_label)
        assert decoded.n_nodes == base.n_nodes
        assert decoded.n_edges == base.n_edges
        assert certificate(decoded) == certificate(base)

    @pytest.mark.parametrize("base", BASES, ids=["star", "chain", "triangle", "arity3"])
    def test_every_continuation_decodes_connected_and_extends(self, base):
        root_label, prefix, k = _program(base)
        anchor = _decode(prefix, k, base, root_label)
        vocabulary = list(dict.fromkeys(prefix))
        rng = random.Random(8)
        for _ in range(40):
            suffix = [rng.choice(vocabulary) for _ in range(rng.randint(1, 8))]
            extended = _decode([*prefix, *suffix], k, base, root_label)
            assert extended.is_connected()
            assert _facts(anchor) <= _facts(extended)
            assert extended.n_nodes >= anchor.n_nodes
            assert extended.n_edges >= anchor.n_edges


class TestPropositionC8Hypothesis:
    """The same statement over a generated distribution of continuations."""

    @settings(
        max_examples=60,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    @given(
        base_index=st.integers(min_value=0, max_value=len(BASES) - 1),
        positions=st.lists(st.integers(min_value=0, max_value=63), min_size=1, max_size=10),
    )
    def test_appending_never_removes_a_fact_or_a_constant(self, base_index, positions):
        base = BASES[base_index]
        root_label, prefix, k = _program(base)
        anchor = _decode(prefix, k, base, root_label)
        vocabulary = list(dict.fromkeys(prefix))
        suffix = [vocabulary[position % len(vocabulary)] for position in positions]
        extended = _decode([*prefix, *suffix], k, base, root_label)
        assert extended.is_connected()
        assert _facts(anchor) <= _facts(extended)
        assert extended.n_nodes >= anchor.n_nodes


class TestCertificateGuards:
    """``certificate`` answers ``None`` instead of raising on refused input."""

    def test_a_disconnected_input_has_no_certificate(self):
        disconnected = _kb(4, [(0, (0, 1)), (0, (2, 3))])
        assert certificate(disconnected) is None

    def test_a_connected_input_has_one(self):
        assert certificate(BASES[0]) is not None

    def test_isomorphic_inputs_share_a_certificate(self):
        left = _kb(3, [(0, (0, 1)), (1, (1, 2))], [0, 1, 1])
        right = _kb(3, [(0, (1, 2)), (1, (0, 1))], [1, 1, 0])
        assert certificate(left) == certificate(right)

    def test_non_isomorphic_inputs_do_not(self):
        chain = _kb(3, [(0, (0, 1)), (0, (1, 2))], [0, 0, 0])
        triangle = _kb(3, [(0, (0, 1)), (0, (1, 2)), (0, (0, 2))], [0, 0, 0])
        assert certificate(chain) != certificate(triangle)
