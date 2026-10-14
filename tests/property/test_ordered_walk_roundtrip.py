"""Property: the ordered walk round-trips and is relabelling-invariant.

Hypothesis generates connected labelled knowledge bases; for each one and each of the
three policies:

- ``S2H`` of the emitted word is isomorphic to the input, decided by pynauty on the
  coloured Levi graph (Lemma C.3);
- relabelling the constants and reordering the facts leaves ``(root type, word)``
  untouched (the invariance half of Theorem C);
- the program validates at ``required_k`` and contains no ``W``.

The generator draws a spanning set of facts along a random permutation, which makes
connectivity a property of the construction rather than a filter, and then adds free
facts of arity up to 3. Labels are drawn independently so the non-trivial-vocabulary
path -- where the root's type must ride outside the word -- is exercised.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

pynauty = pytest.importorskip("pynauty")

from isalhg.core.canonical import required_k
from isalhg.core.instructions import TokenW, serialize, validate
from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.core.string_to_hypergraph import string_to_hypergraph
from isalhg.iso_backends.isal_ordered import POLICIES, ordered_fingerprint, ordered_word
from isalhg.iso_backends.pynauty_levi import PynautyLeviBackend

pytestmark = pytest.mark.property

_POLICY_NAMES = ("struct", "rank", "rank0")


@st.composite
def connected_labelled_kb(draw, max_n: int = 6, max_arity: int = 3) -> SparseHypergraph:
    n = draw(st.integers(min_value=1, max_value=max_n))
    perm = draw(st.permutations(list(range(n))))
    members: list[frozenset[int]] = []
    for i in range(1, n):
        parent = draw(st.integers(min_value=0, max_value=i - 1))
        members.append(frozenset({perm[i], perm[parent]}))
    for _ in range(draw(st.integers(min_value=0, max_value=2))):
        arity = draw(st.integers(min_value=2, max_value=min(max_arity, max(2, n))))
        if arity > n:
            continue
        members.append(
            frozenset(
                draw(
                    st.sets(
                        st.integers(min_value=0, max_value=n - 1),
                        min_size=arity,
                        max_size=arity,
                    )
                )
            )
        )
    deduped = sorted(set(members), key=sorted)
    edge_labels = [draw(st.integers(min_value=0, max_value=2)) for _ in deduped]
    vertex_labels = [draw(st.integers(min_value=0, max_value=2)) for _ in range(n)]
    return SparseHypergraph(
        n,
        deduped,
        n_vertex_labels=3,
        n_edge_labels=3,
        vertex_labels=vertex_labels,
        edge_labels=edge_labels,
    )


def _reordered(H: SparseHypergraph, sigma: list[int], rotation: int) -> SparseHypergraph:
    """Relabel the constants by ``sigma`` and rotate the fact insertion order."""
    P = permute(H, sigma)
    facts = [(P.members(e), P.edge_label(e)) for e in P.edges()]
    if facts:
        shift = rotation % len(facts)
        facts = facts[shift:] + facts[:shift]
    return SparseHypergraph(
        P.n_nodes,
        [m for m, _ in facts],
        n_vertex_labels=P.n_vertex_labels,
        n_edge_labels=P.n_edge_labels,
        vertex_labels=[P.vertex_label(v) for v in range(P.n_nodes)],
        edge_labels=[label for _, label in facts],
    )


@pytest.mark.parametrize("policy_name", _POLICY_NAMES)
@settings(max_examples=60, deadline=None)
@given(connected_labelled_kb())
def test_round_trip_is_isomorphic(policy_name: str, H: SparseHypergraph) -> None:
    policy = POLICIES[policy_name]
    result = ordered_word(H, policy=policy)
    decoded = string_to_hypergraph(
        serialize(result.tokens),
        k=required_k(H),
        n_vertex_labels=H.n_vertex_labels,
        n_edge_labels=H.n_edge_labels,
        seed_label=result.root_label,
    )
    assert PynautyLeviBackend().are_isomorphic(H, decoded)


@pytest.mark.parametrize("policy_name", _POLICY_NAMES)
@settings(max_examples=60, deadline=None)
@given(connected_labelled_kb(), st.integers(min_value=0, max_value=7), st.data())
def test_fingerprint_is_invariant(
    policy_name: str, H: SparseHypergraph, rotation: int, data: st.DataObject
) -> None:
    policy = POLICIES[policy_name]
    sigma = data.draw(st.permutations(list(range(H.n_nodes))))
    assert ordered_fingerprint(_reordered(H, sigma, rotation), policy=policy) == (
        ordered_fingerprint(H, policy=policy)
    )


@pytest.mark.parametrize("policy_name", _POLICY_NAMES)
@settings(max_examples=60, deadline=None)
@given(connected_labelled_kb())
def test_program_validates_and_never_pads(policy_name: str, H: SparseHypergraph) -> None:
    tokens = ordered_word(H, policy=POLICIES[policy_name]).tokens
    validate(
        list(tokens),
        k=required_k(H),
        n_vertex_labels=H.n_vertex_labels,
        n_edge_labels=H.n_edge_labels,
    )
    assert not any(isinstance(t, TokenW) for t in tokens)
