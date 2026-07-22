"""Unit tests for :mod:`isalhg.datasets.synthetic.mixed_arity_erdos_renyi`."""

from __future__ import annotations

from collections import Counter

import pytest

from isalhg.datasets.registry import get_dataset
from isalhg.datasets.schemas import DatasetItem, DatasetMetadata, LabelVocabulary
from isalhg.datasets.synthetic.mixed_arity_erdos_renyi import (
    MixedArityErdosRenyiHypergraphs,
)

pytestmark = pytest.mark.unit


class TestInitValidation:
    def test_rejects_bad_n(self) -> None:
        with pytest.raises(ValueError, match="n must be"):
            MixedArityErdosRenyiHypergraphs(n=0, k=5, c=2.0)

    def test_rejects_k_lt_2(self) -> None:
        with pytest.raises(ValueError, match="k must be"):
            MixedArityErdosRenyiHypergraphs(n=10, k=1, c=2.0)

    def test_rejects_k_gt_n(self) -> None:
        with pytest.raises(ValueError, match="k must be"):
            MixedArityErdosRenyiHypergraphs(n=4, k=5, c=2.0)

    def test_rejects_negative_c(self) -> None:
        with pytest.raises(ValueError, match="c must be"):
            MixedArityErdosRenyiHypergraphs(n=10, k=5, c=-1.0)

    def test_rejects_zero_connected_max_attempts(self) -> None:
        with pytest.raises(ValueError, match="connected_max_attempts"):
            MixedArityErdosRenyiHypergraphs(n=10, k=5, c=2.0, connected_max_attempts=0)


class TestMaterialisation:
    def test_yields_exactly_one_item(self) -> None:
        ds = MixedArityErdosRenyiHypergraphs(n=12, k=5, c=2.0, seed=7)
        assert len(ds) == 1
        items = list(ds)
        assert len(items) == 1
        assert isinstance(items[0], DatasetItem)

    def test_determinism_same_seed(self) -> None:
        ds1 = MixedArityErdosRenyiHypergraphs(n=12, k=5, c=2.0, seed=42)
        ds2 = MixedArityErdosRenyiHypergraphs(n=12, k=5, c=2.0, seed=42)
        h1 = next(iter(ds1)).hypergraph
        h2 = next(iter(ds2)).hypergraph
        assert h1 == h2

    def test_different_seed_likely_different(self) -> None:
        ds1 = MixedArityErdosRenyiHypergraphs(n=20, k=5, c=3.0, seed=0)
        ds2 = MixedArityErdosRenyiHypergraphs(n=20, k=5, c=3.0, seed=1)
        h1 = next(iter(ds1)).hypergraph
        h2 = next(iter(ds2)).hypergraph
        assert h1 != h2

    def test_edges_have_mixed_arities(self) -> None:
        # With k=5 and moderate density, multiple distinct arities should appear.
        # Run 3 seeds and pool edges; at least 2 distinct arities must appear.
        arities: set[int] = set()
        for seed in range(3):
            ds = MixedArityErdosRenyiHypergraphs(n=20, k=5, c=2.0, seed=seed)
            h = next(iter(ds)).hypergraph
            for _, members, _ in h.iter_edges():
                arities.add(len(members))
        assert len(arities) >= 2, f"expected multiple arities, got {sorted(arities)}"

    def test_arities_within_range(self) -> None:
        # All edge arities must lie in [2, k].
        k = 5
        ds = MixedArityErdosRenyiHypergraphs(n=20, k=k, c=2.0, seed=0)
        h = next(iter(ds)).hypergraph
        for _, members, _ in h.iter_edges():
            a = len(members)
            assert 2 <= a <= k, f"arity {a} out of range [2, {k}]"

    def test_generated_hypergraph_is_connected(self) -> None:
        for seed in range(5):
            ds = MixedArityErdosRenyiHypergraphs(n=12, k=5, c=2.0, seed=seed)
            h = next(iter(ds)).hypergraph
            assert h.is_connected(), f"seed={seed} produced disconnected hypergraph"

    def test_n_nodes_matches_request(self) -> None:
        ds = MixedArityErdosRenyiHypergraphs(n=16, k=5, c=2.0, seed=0)
        h = next(iter(ds)).hypergraph
        assert h.n_nodes == 16

    def test_item_extras_carry_axis_values(self) -> None:
        ds = MixedArityErdosRenyiHypergraphs(n=12, k=5, c=2.0, seed=9)
        item = next(iter(ds))
        assert item.iso_class is None
        assert item.extra["n"] == 12
        assert item.extra["k"] == 5
        assert item.extra["c"] == 2.0
        assert item.extra["seed"] == 9
        assert item.extra["n_edges"] == item.hypergraph.n_edges

    def test_item_id_encodes_params(self) -> None:
        ds = MixedArityErdosRenyiHypergraphs(n=12, k=5, c=2.0, seed=3)
        item = next(iter(ds))
        assert "mixed" in item.item_id
        assert "n12" in item.item_id
        assert "k5" in item.item_id
        assert "s3" in item.item_id

    def test_require_connected_false(self) -> None:
        ds = MixedArityErdosRenyiHypergraphs(n=8, k=3, c=0.1, seed=0, require_connected=False)
        item = next(iter(ds))
        assert item.extra["require_connected"] is False


class TestMetadata:
    def test_metadata_contract(self) -> None:
        ds = MixedArityErdosRenyiHypergraphs(n=12, k=5, c=2.0, seed=0)
        md = ds.metadata
        assert isinstance(md, DatasetMetadata)
        assert md.name == "random_erdos_renyi_mixed"
        assert md.n_items == 1
        assert md.n_nodes_range == (12, 12)
        assert md.has_iso_labels is False
        assert md.label_vocabulary == LabelVocabulary.trivial()
        # arity range must include 2 (min) and k (max)
        lo, hi = md.arity_range
        assert lo <= 2
        assert hi >= 5  # k=5

    def test_arity_range_bottom_is_2(self) -> None:
        ds = MixedArityErdosRenyiHypergraphs(n=12, k=7, c=2.0, seed=0)
        md = ds.metadata
        assert md.arity_range[0] == 2

    def test_arity_range_top_matches_k(self) -> None:
        ds = MixedArityErdosRenyiHypergraphs(n=12, k=7, c=2.0, seed=0)
        md = ds.metadata
        assert md.arity_range[1] == 7


class TestRegistry:
    def test_registered_under_random_erdos_renyi_mixed(self) -> None:
        ds = get_dataset("random_erdos_renyi_mixed", {"n": 12, "k": 5, "c": 2.0, "seed": 0})
        assert isinstance(ds, MixedArityErdosRenyiHypergraphs)
        h = next(iter(ds)).hypergraph
        assert h.n_nodes == 12

    def test_registry_require_connected_param(self) -> None:
        ds = get_dataset(
            "random_erdos_renyi_mixed",
            {"n": 10, "k": 5, "c": 2.0, "seed": 0, "require_connected": False},
        )
        item = next(iter(ds))
        assert item.extra["require_connected"] is False


class TestRebind:
    def test_seed_returns_new_dataset_with_new_seed(self) -> None:
        ds = MixedArityErdosRenyiHypergraphs(n=12, k=5, c=2.0, seed=0)
        rebound = ds.seed(99)
        assert isinstance(rebound, MixedArityErdosRenyiHypergraphs)
        assert next(iter(rebound)).extra["seed"] == 99

    def test_seed_preserves_other_params(self) -> None:
        ds = MixedArityErdosRenyiHypergraphs(n=12, k=5, c=2.0, seed=0)
        rebound = ds.seed(7)
        item = next(iter(rebound))
        assert item.extra["n"] == 12
        assert item.extra["k"] == 5
        assert item.extra["c"] == 2.0


class TestArityDistribution:
    def test_all_arities_reachable(self) -> None:
        """With enough density and samples, all arities in [2,k] should appear."""
        k = 5
        seen_arities: Counter[int] = Counter()
        # 10 seeds at moderate density on n=20 should exercise all arities in [2,5].
        for seed in range(10):
            ds = MixedArityErdosRenyiHypergraphs(n=20, k=k, c=3.0, seed=seed)
            h = next(iter(ds)).hypergraph
            for _, members, _ in h.iter_edges():
                seen_arities[len(members)] += 1
        for a in range(2, k + 1):
            assert seen_arities[a] > 0, f"arity {a} never appeared in 10 seeds at c=3"
