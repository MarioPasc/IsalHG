"""Property tests for connected corpus generators (T-M2c acceptance a).

Every hypergraph emitted by ``CorrelationCorpusHypergraphs`` and every
snapshot in ``PerturbationLadderHypergraphs`` must be connected, across all
seeds sampled by Hypothesis.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from isalhg.datasets.synthetic.correlation_corpus import CorrelationCorpusHypergraphs
from isalhg.datasets.synthetic.perturbation_ladder import PerturbationLadderHypergraphs

pytestmark = pytest.mark.property


@given(seed=st.integers(min_value=0, max_value=99999))
@settings(max_examples=30, deadline=10_000)
def test_correlation_corpus_all_connected(seed: int) -> None:
    """All corpus items are connected under Hypothesis-sampled seeds."""
    ds = CorrelationCorpusHypergraphs(n_items=15, seed=seed)
    for it in ds:
        assert it.hypergraph.is_connected(), f"seed={seed}, item={it.item_id} is disconnected"


@given(seed=st.integers(min_value=0, max_value=99999))
@settings(max_examples=20, deadline=15_000)
def test_perturbation_ladder_all_connected(seed: int) -> None:
    """All ladder snapshots are connected under Hypothesis-sampled seeds."""
    ds = PerturbationLadderHypergraphs(n_ladders=3, max_t=6, seed=seed)
    for it in ds:
        assert it.hypergraph.is_connected(), f"seed={seed}, item={it.item_id} is disconnected"


@given(seed=st.integers(min_value=0, max_value=99999))
@settings(max_examples=20, deadline=30_000)
def test_perturbation_ladder_arity_bounded(seed: int) -> None:
    """Ladder snapshots never exceed arity_range[1], even with max_t >= 10.

    Reproduces the Picasso crash (job 1547134_4): arity_range=[2,4], max_t=10.
    add_incidence grew a base-arity-4 edge to arity 14 over 10 steps, pushing
    past K_MAX and raising IsalHGError in _cpp_canonical_string.
    """
    max_k = 4
    ds = PerturbationLadderHypergraphs(n_ladders=2, max_t=10, arity_range=(2, max_k), seed=seed)
    for it in ds:
        H = it.hypergraph
        for members in H.hyperedges():
            assert len(members) <= max_k, (
                f"seed={seed}, item={it.item_id}: hyperedge arity {len(members)} > {max_k} "
                f"(Picasso crash: add_incidence unbounded without max_arity filter)"
            )
