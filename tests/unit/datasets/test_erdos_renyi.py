"""Unit tests for :mod:`isalhg.datasets.synthetic.erdos_renyi`."""

from __future__ import annotations

import math

import pytest

from isalhg.datasets.registry import get_dataset
from isalhg.datasets.schemas import DatasetItem, DatasetMetadata, LabelVocabulary
from isalhg.datasets.synthetic.erdos_renyi import (
    UniformErdosRenyiHypergraphs,
    _p_from_c,
)

pytestmark = pytest.mark.unit


class TestInitValidation:
    def test_requires_exactly_one_of_p_or_c(self) -> None:
        with pytest.raises(ValueError, match="exactly one"):
            UniformErdosRenyiHypergraphs(n=10, r=3, seed=0)
        with pytest.raises(ValueError, match="exactly one"):
            UniformErdosRenyiHypergraphs(n=10, r=3, p=0.1, c=1.0, seed=0)

    def test_rejects_bad_p(self) -> None:
        with pytest.raises(ValueError, match="p must lie"):
            UniformErdosRenyiHypergraphs(n=10, r=3, p=1.5, seed=0)

    def test_rejects_bad_c(self) -> None:
        with pytest.raises(ValueError, match="c must be"):
            UniformErdosRenyiHypergraphs(n=10, r=3, c=-1.0, seed=0)

    def test_rejects_bad_n_or_r(self) -> None:
        with pytest.raises(ValueError, match="n must be"):
            UniformErdosRenyiHypergraphs(n=0, r=2, p=0.1, seed=0)
        with pytest.raises(ValueError, match="r must satisfy"):
            UniformErdosRenyiHypergraphs(n=3, r=5, p=0.1, seed=0)


class TestCToP:
    def test_preprint_table_n50_r3_c1(self) -> None:
        # PREPRINT.md table: (n=50, r=3, c=1) -> p ≈ 2.55e-3
        p = _p_from_c(c=1, n=50, r=3)
        # C(50, 3) = 19600 ; p = 50 / 19600 ≈ 2.551e-3
        assert math.isclose(p, 50 / 19600, rel_tol=1e-9)
        assert f"{p:.2e}" == "2.55e-03"

    def test_preprint_table_n200_r5_c5(self) -> None:
        # PREPRINT.md table: (n=200, r=5, c=5) -> p ≈ 2.36e-7
        p = _p_from_c(c=5, n=200, r=5)
        assert math.isclose(p, 5 * 200 / math.comb(200, 5), rel_tol=1e-12)

    def test_saturates_at_one(self) -> None:
        # Pathologically dense: c=100 on (n=4, r=2) wants p >> 1.
        # C(4,2)=6; p = 100*4/6 ≈ 66.6 -> clamp to 1.0
        p = _p_from_c(c=100, n=4, r=2)
        assert p == 1.0


class TestMaterialisation:
    def test_yields_exactly_one_item(self) -> None:
        ds = UniformErdosRenyiHypergraphs(n=10, r=3, c=2, seed=7)
        assert len(ds) == 1
        items = list(ds)
        assert len(items) == 1
        assert isinstance(items[0], DatasetItem)

    def test_determinism_same_seed(self) -> None:
        ds1 = UniformErdosRenyiHypergraphs(n=12, r=3, c=2, seed=42)
        ds2 = UniformErdosRenyiHypergraphs(n=12, r=3, c=2, seed=42)
        h1 = next(iter(ds1)).hypergraph
        h2 = next(iter(ds2)).hypergraph
        assert h1 == h2
        assert h1.n_nodes == 12
        # Every hyperedge has arity r=3.
        for _e, members, _l in h1.iter_edges():
            assert len(members) == 3

    def test_different_seed_likely_different(self) -> None:
        # Sufficiently dense regime to make collision astronomically unlikely.
        ds1 = UniformErdosRenyiHypergraphs(n=20, r=3, c=5, seed=0)
        ds2 = UniformErdosRenyiHypergraphs(n=20, r=3, c=5, seed=1)
        h1 = next(iter(ds1)).hypergraph
        h2 = next(iter(ds2)).hypergraph
        assert h1 != h2

    def test_item_extras_carry_axis_values(self) -> None:
        ds = UniformErdosRenyiHypergraphs(n=15, r=3, c=2, seed=3)
        item = next(iter(ds))
        assert item.iso_class is None
        assert item.extra["n"] == 15
        assert item.extra["r"] == 3
        assert item.extra["c"] == 2.0
        assert item.extra["seed"] == 3
        assert item.extra["n_edges"] == item.hypergraph.n_edges
        # item_id encodes the axis triple + seed for downstream addressability.
        assert item.item_id.startswith("er_n15_r3_c2_s3")

    def test_p_direct_stored_verbatim(self) -> None:
        ds = UniformErdosRenyiHypergraphs(n=10, r=3, p=0.05, seed=0)
        item = next(iter(ds))
        assert item.extra["p"] == 0.05
        assert item.extra["c"] is None


class TestMetadata:
    def test_metadata_contract(self) -> None:
        ds = UniformErdosRenyiHypergraphs(n=10, r=3, c=2, seed=0)
        md = ds.metadata
        assert isinstance(md, DatasetMetadata)
        assert md.name == "random_erdos_renyi"
        assert md.n_items == 1
        assert md.arity_range == (3, 3)
        assert md.n_nodes_range == (10, 10)
        assert md.has_iso_labels is False
        assert md.label_vocabulary == LabelVocabulary.trivial()
        assert "xgi" in md.source


class TestRegistry:
    def test_registered_under_random_erdos_renyi(self) -> None:
        ds = get_dataset(
            "random_erdos_renyi",
            {"n": 10, "r": 3, "c": 2, "seed": 0},
        )
        assert isinstance(ds, UniformErdosRenyiHypergraphs)
        assert next(iter(ds)).hypergraph.n_nodes == 10

    def test_registry_accepts_p_form(self) -> None:
        ds = get_dataset(
            "random_erdos_renyi",
            {"n": 10, "r": 3, "p": 0.05, "seed": 0},
        )
        item = next(iter(ds))
        assert item.extra["p"] == 0.05


class TestRebind:
    def test_seed_returns_new_dataset_with_new_seed(self) -> None:
        ds = UniformErdosRenyiHypergraphs(n=15, r=3, c=2, seed=0)
        rebound = ds.seed(99)
        assert isinstance(rebound, UniformErdosRenyiHypergraphs)
        assert next(iter(rebound)).extra["seed"] == 99
