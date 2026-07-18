"""Unit tests for the perturbation-ladder dataset.

The ladder is the scale tier of the HGED oracle: each snapshot ``t`` is a
known distance ``HGED(base, snapshot_t) <= t`` from its base. The tests check
determinism, the item/metadata contract, the registry wiring, and -- the
load-bearing property -- that the exact oracle honours every ladder budget
(``ExactHGED(base, snapshot_t) <= t``, T-M2 acceptance).

T-M2c additions: connectivity checks (acceptance criteria a/b).
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
        base_extra = items[0].extra
        assert base_extra["ladder"] == 0
        assert base_extra["step"] == 0
        assert base_extra["budget_from_base"] == 0
        assert base_extra["op"] == "base"
        assert "acceptance_attempts" in base_extra
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


class TestArityBound:
    """T-M2c amendment: ladder snapshots must not exceed arity_range[1].

    Pre-fix (before max_arity filter): add_incidence and insert_hyperedge were
    uncapped, so a base-arity-4 edge could reach arity 6+ after a single step
    (observed at seed=0, item=L0_t1) and arity 14+ over 10 steps (Picasso
    crash job 1547134_4: arity_range=[2,4], max_t=10, IsalHGError k>K_MAX).
    """

    def test_pre_fix_arity_overflow_is_observable(self) -> None:
        """Documents the bug: random_connected_edit without max_arity can exceed arity."""
        import random

        from isalhg.core.sparse_hypergraph import _sample_new_hyperedge
        from isalhg.datasets.synthetic._random_hg import random_connected_hypergraph

        rng = random.Random(0)
        H, _ = random_connected_hypergraph(n_nodes=6, n_edges=4, arity_range=(2, 4), rng=rng)
        # Without max_arity, insert_hyperedge can create edges up to n_nodes arity.
        # Confirm _sample_new_hyperedge would produce arity > 4 given a large-enough n.
        found_oversized = False
        for _ in range(200):
            fresh = _sample_new_hyperedge(H, rng)
            if fresh is not None and len(fresh[0]) > 4:
                found_oversized = True
                break
        assert found_oversized, (
            "Expected _sample_new_hyperedge to produce arity > 4 on a 6-node base"
        )

    def test_all_snapshots_within_arity_range(self) -> None:
        """All ladder snapshots respect arity_range[1] after the fix."""
        ds = PerturbationLadderHypergraphs(
            n_nodes=6, n_edges=4, n_ladders=5, max_t=10, arity_range=(2, 4), seed=0
        )
        for it in ds:
            H = it.hypergraph
            for members in H.hyperedges():
                assert len(members) <= 4, f"item={it.item_id}: arity {len(members)} > 4"

    def test_arity_bound_across_seeds(self) -> None:
        """Arity bound holds across multiple seeds and long ladders."""
        for seed in range(10):
            ds = PerturbationLadderHypergraphs(
                n_nodes=8, n_edges=6, n_ladders=3, max_t=10, arity_range=(2, 4), seed=seed
            )
            for it in ds:
                H = it.hypergraph
                for members in H.hyperedges():
                    assert len(members) <= 4, (
                        f"seed={seed}, item={it.item_id}: arity {len(members)} > 4"
                    )


class TestConnectivity:
    """T-M2c acceptance (a): all ladder snapshots are connected.

    Pre-fix regression: the raw ``random_hypergraph`` + ``random_edit``
    pipeline could produce disconnected snapshots — ``insert_vertex`` always
    materialises an isolated vertex, and ``delete_hyperedge`` can disconnect.
    The test below first shows the pre-fix behaviour is observable, then
    verifies the new pipeline is always connected.
    """

    def test_raw_random_hypergraph_can_be_disconnected(self) -> None:
        """Pre-fix: raw random_hypergraph produces disconnected outputs."""
        import random

        from isalhg.datasets.synthetic._random_hg import random_hypergraph

        rng = random.Random(0)
        # n=5, 1 edge of arity 2: at most 2 out of 5 nodes covered → disconnected
        H = random_hypergraph(n_nodes=5, n_edges=1, arity_range=(2, 2), rng=rng)
        assert not H.is_connected(), (
            "This test documents the pre-fix behaviour: raw random_hypergraph "
            "with insufficient edges produces disconnected hypergraphs."
        )

    def test_all_items_connected(self) -> None:
        """T-M2c acceptance (a): all snapshots in the ladder are connected."""
        ds = PerturbationLadderHypergraphs(n_ladders=5, max_t=8, seed=0)
        for it in ds:
            assert it.hypergraph.is_connected(), (
                f"Ladder snapshot {it.item_id} is disconnected (T-M2c violation)"
            )

    def test_connected_across_seeds(self) -> None:
        """Connectivity holds across multiple seeds (sampling coverage)."""
        for seed in range(10):
            ds = PerturbationLadderHypergraphs(n_ladders=3, max_t=6, seed=seed)
            for it in ds:
                assert it.hypergraph.is_connected(), (
                    f"seed={seed}, item={it.item_id} is disconnected"
                )


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
