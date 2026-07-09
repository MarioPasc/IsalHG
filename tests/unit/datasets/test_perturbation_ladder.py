"""Unit tests for the perturbation-ladder dataset.

The ladder is the scale tier of the HGED oracle: each snapshot ``t`` is a
known distance ``HGED(base, snapshot_t) <= t`` from its base. The tests check
determinism, the item/metadata contract, the registry wiring, and -- the
load-bearing property -- that the exact oracle honours every ladder budget
(``ExactHGED(base, snapshot_t) <= t``, T-M2 acceptance).
"""

from __future__ import annotations

import pytest

from isalhg.datasets import registry
from isalhg.datasets.synthetic.perturbation_ladder import PerturbationLadderHypergraphs

pytestmark = pytest.mark.unit


class TestStructure:
    def test_length_is_ladders_times_steps(self) -> None:
        ds = PerturbationLadderHypergraphs(n_ladders=4, max_t=7, seed=0)
        assert len(ds) == 4 * (7 + 1)
        assert len(list(ds)) == len(ds)

    def test_deterministic_under_seed(self) -> None:
        a = PerturbationLadderHypergraphs(n_ladders=3, max_t=5, seed=11)
        b = PerturbationLadderHypergraphs(n_ladders=3, max_t=5, seed=11)
        ids_a = [it.item_id for it in a]
        ids_b = [it.item_id for it in b]
        assert ids_a == ids_b
        # Structural identity across the two builds, item by item.
        for x, y in zip(list(a), list(b), strict=True):
            assert x.hypergraph == y.hypergraph
            assert x.extra == y.extra

    def test_extra_records_budget_and_op(self) -> None:
        ds = PerturbationLadderHypergraphs(n_ladders=1, max_t=4, seed=3)
        items = list(ds)
        assert items[0].extra == {"ladder": 0, "step": 0, "budget_from_base": 0, "op": "base"}
        previous_budget = 0
        for step, it in enumerate(items):
            assert it.extra["step"] == step
            # Qin-cost budget: >= the op count, strictly increasing per step.
            assert it.extra["budget_from_base"] >= step
            if step >= 1:
                assert it.extra["budget_from_base"] > previous_budget
            previous_budget = it.extra["budget_from_base"]
            assert it.iso_class is None

    def test_metadata(self) -> None:
        ds = PerturbationLadderHypergraphs(n_ladders=2, max_t=3, seed=1)
        meta = ds.metadata
        assert meta.name == "perturbation_ladder"
        assert meta.n_items == len(ds)
        assert meta.has_iso_labels is False
        assert meta.n_nodes_range[0] <= meta.n_nodes_range[1]

    def test_seed_returns_new_instance(self) -> None:
        ds = PerturbationLadderHypergraphs(n_ladders=2, max_t=3, seed=0)
        other = ds.seed(999)
        assert isinstance(other, PerturbationLadderHypergraphs)
        assert other is not ds
        # Same item ids (structure), but the bases differ under a new seed.
        assert [it.item_id for it in other] == [it.item_id for it in ds]
        base_a = next(iter(ds)).hypergraph
        base_b = next(iter(other)).hypergraph
        assert base_a != base_b


class TestRegistry:
    def test_registered_and_retrievable(self) -> None:
        ds = registry.get_dataset("perturbation_ladder", {"n_ladders": 2, "max_t": 3})
        assert isinstance(ds, PerturbationLadderHypergraphs)
        assert "perturbation_ladder" in registry.available_datasets()


class TestBudgetIsHGEDUpperBound:
    """T-M2 acceptance: the ladder budget upper-bounds the exact oracle."""

    def test_exact_hged_at_most_budget(self) -> None:
        pytest.importorskip("scipy")
        pytest.importorskip("numpy")
        from isalhg.metric_space.distances.hged import ExactHGED

        exact = ExactHGED()
        ds = PerturbationLadderHypergraphs(n_nodes=6, n_edges=4, n_ladders=4, max_t=6, seed=7)
        pairs = ds.ladder_pairs()
        assert pairs, "ladder_pairs must be non-empty"
        for base, snapshot, budget in pairs:
            assert exact.pairwise(base, snapshot) <= budget
