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
