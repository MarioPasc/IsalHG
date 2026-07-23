"""Unit tests for :mod:`isalhg.datasets.synthetic.chung_lu`."""

from __future__ import annotations

import pytest

from isalhg.datasets.registry import get_dataset
from isalhg.datasets.schemas import DatasetItem, DatasetMetadata, LabelVocabulary
from isalhg.datasets.synthetic.chung_lu import ChungLuHypergraphs

pytestmark = pytest.mark.unit


class TestInitValidation:
    def test_rejects_bad_n(self) -> None:
        with pytest.raises(ValueError, match="n must be"):
            ChungLuHypergraphs(n=0, k=3, c=2.0)

    def test_rejects_k_gt_n(self) -> None:
        with pytest.raises(ValueError, match="k must satisfy"):
            ChungLuHypergraphs(n=4, k=5, c=2.0)

    def test_rejects_k_lt_2(self) -> None:
        with pytest.raises(ValueError, match="k must satisfy"):
            ChungLuHypergraphs(n=10, k=1, c=2.0)

    def test_rejects_negative_c(self) -> None:
        with pytest.raises(ValueError, match="c must be"):
            ChungLuHypergraphs(n=10, k=3, c=-0.5)

    def test_rejects_zero_connected_max_attempts(self) -> None:
        with pytest.raises(ValueError, match="connected_max_attempts"):
            ChungLuHypergraphs(n=10, k=3, c=2.0, connected_max_attempts=0)


class TestMaterialisation:
    def test_yields_exactly_one_item(self) -> None:
        ds = ChungLuHypergraphs(n=10, k=3, c=2.0, seed=7)
        assert len(ds) == 1
        items = list(ds)
        assert len(items) == 1
        assert isinstance(items[0], DatasetItem)

    def test_determinism_same_seed(self) -> None:
        ds1 = ChungLuHypergraphs(n=12, k=3, c=2.0, seed=42)
        ds2 = ChungLuHypergraphs(n=12, k=3, c=2.0, seed=42)
        h1 = next(iter(ds1)).hypergraph
        h2 = next(iter(ds2)).hypergraph
        assert h1 == h2
        assert h1.n_nodes == 12

    def test_different_seed_likely_different(self) -> None:
        # Dense regime makes identical outcomes astronomically unlikely.
        ds1 = ChungLuHypergraphs(n=16, k=3, c=3.0, seed=0)
        ds2 = ChungLuHypergraphs(n=16, k=3, c=3.0, seed=1)
        h1 = next(iter(ds1)).hypergraph
        h2 = next(iter(ds2)).hypergraph
        assert h1 != h2

    def test_item_extras_carry_axis_values(self) -> None:
        ds = ChungLuHypergraphs(n=10, k=3, c=2.0, seed=3)
        item = next(iter(ds))
        assert item.iso_class is None
        assert item.extra["n"] == 10
        assert item.extra["k"] == 3
        assert item.extra["c"] == 2.0
        assert item.extra["seed"] == 3
        assert item.extra["n_edges"] == item.hypergraph.n_edges
        assert item.extra["n_nodes"] == item.hypergraph.n_nodes

    def test_item_id_encodes_params(self) -> None:
        ds = ChungLuHypergraphs(n=10, k=3, c=2.0, seed=5)
        item = next(iter(ds))
        assert "cl_" in item.item_id
        assert "n10" in item.item_id
        assert "k3" in item.item_id
        assert "s5" in item.item_id

    def test_generated_hypergraph_is_connected(self) -> None:
        # require_connected=True (default) must always yield connected hypergraphs.
        for seed in range(5):
            ds = ChungLuHypergraphs(n=12, k=3, c=2.0, seed=seed)
            h = next(iter(ds)).hypergraph
            assert h.is_connected(), f"seed={seed} produced disconnected hypergraph"

    def test_n_nodes_matches_request(self) -> None:
        # The generator should produce exactly n nodes.
        ds = ChungLuHypergraphs(n=16, k=3, c=2.0, seed=0)
        h = next(iter(ds)).hypergraph
        assert h.n_nodes == 16

    def test_require_connected_false_skips_check(self) -> None:
        # When require_connected=False, the first sample is accepted regardless.
        ds = ChungLuHypergraphs(n=8, k=3, c=0.1, seed=0, require_connected=False)
        item = next(iter(ds))
        assert item.extra["require_connected"] is False


class TestMetadata:
    def test_metadata_contract(self) -> None:
        ds = ChungLuHypergraphs(n=10, k=3, c=2.0, seed=0)
        md = ds.metadata
        assert isinstance(md, DatasetMetadata)
        assert md.name == "chung_lu"
        assert md.n_items == 1
        assert md.n_nodes_range == (10, 10)
        assert md.has_iso_labels is False
        assert md.label_vocabulary == LabelVocabulary.trivial()
        assert "xgi" in md.source or "chung" in md.source.lower()


class TestRegistry:
    def test_registered_under_chung_lu(self) -> None:
        ds = get_dataset("chung_lu", {"n": 10, "k": 3, "c": 2.0, "seed": 0})
        assert isinstance(ds, ChungLuHypergraphs)
        h = next(iter(ds)).hypergraph
        assert h.n_nodes == 10

    def test_registry_require_connected_param(self) -> None:
        ds = get_dataset(
            "chung_lu",
            {"n": 10, "k": 3, "c": 2.0, "seed": 0, "require_connected": False},
        )
        item = next(iter(ds))
        assert item.extra["require_connected"] is False


class TestRebind:
    def test_seed_returns_new_dataset_with_new_seed(self) -> None:
        ds = ChungLuHypergraphs(n=12, k=3, c=2.0, seed=0)
        rebound = ds.seed(99)
        assert isinstance(rebound, ChungLuHypergraphs)
        assert next(iter(rebound)).extra["seed"] == 99

    def test_seed_preserves_other_params(self) -> None:
        ds = ChungLuHypergraphs(n=12, k=3, c=2.0, seed=0)
        rebound = ds.seed(7)
        item = next(iter(rebound))
        assert item.extra["n"] == 12
        assert item.extra["k"] == 3
        assert item.extra["c"] == 2.0


# ---------------------------------------------------------------------------
# T-M7m regression: Chung-Lu arity must be capped at k (T-M7m AC-CL)
# ---------------------------------------------------------------------------


class TestArityCapRegression:
    """Edge sizes must satisfy size ∈ [2, k] after generation.

    Bug (pre-fix): k=3 generator was producing edges of size up to 6
    because the Chung-Lu bipartite model produces variable-size edges
    and the old code only filtered size < 2.
    """

    @pytest.mark.parametrize("k", [3, 4, 5])
    def test_all_edges_within_arity_cap(self, k: int) -> None:
        # Run several seeds to cover different random draws.
        for seed in range(8):
            ds = ChungLuHypergraphs(n=20, k=k, c=2.0, seed=seed, require_connected=False)
            h = next(iter(ds)).hypergraph
            for _, members, _ in h.iter_edges():
                assert len(members) <= k, f"seed={seed}, k={k}: edge size {len(members)} > k"

    @pytest.mark.parametrize("k", [3, 4, 5])
    def test_all_edges_at_least_2(self, k: int) -> None:
        for seed in range(4):
            ds = ChungLuHypergraphs(n=20, k=k, c=2.0, seed=seed, require_connected=False)
            h = next(iter(ds)).hypergraph
            for _, members, _ in h.iter_edges():
                assert len(members) >= 2, f"seed={seed}, k={k}: edge size {len(members)} < 2"

    def test_k3_never_produces_arity_above_3(self) -> None:
        """Pinned regression: k=3 was producing arity 4-6 before the fix."""
        seen_arities: set[int] = set()
        for seed in range(20):
            ds = ChungLuHypergraphs(n=24, k=3, c=3.0, seed=seed, require_connected=False)
            h = next(iter(ds)).hypergraph
            for _, members, _ in h.iter_edges():
                seen_arities.add(len(members))
        assert max(seen_arities, default=2) <= 3, f"k=3 produced arity > 3: {seen_arities}"
