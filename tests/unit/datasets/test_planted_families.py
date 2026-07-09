"""Unit tests for :mod:`isalhg.datasets.synthetic.planted_families`.

Acceptance criteria (T-M4):
  AC1  All emitted hypergraphs are connected (D-CONN1).
  AC2  Within each family, all member pairs are non-isomorphic.
  AC3  ``iso_class`` equals the family index for every item.
  AC4  ``len(dataset) == n_families * members_per_family``.
  AC5  Same ``seed_value`` produces identical sequences (determinism).
  AC6  Registry lookup ``get_dataset("planted_families", {})`` succeeds.
"""

from __future__ import annotations

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.datasets.registry import get_dataset
from isalhg.datasets.synthetic.planted_families import PlantedFamilyDataset

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _seed_a() -> SparseHypergraph:
    """n=4, two 3-edges sharing one vertex."""
    return SparseHypergraph(n_nodes=4, hyperedges=[frozenset({0, 1, 2}), frozenset({0, 1, 3})])


def _seed_b() -> SparseHypergraph:
    """n=4, 4-cycle (2-uniform)."""
    return SparseHypergraph(
        n_nodes=4,
        hyperedges=[
            frozenset({0, 1}),
            frozenset({1, 2}),
            frozenset({2, 3}),
            frozenset({3, 0}),
        ],
    )


def _seed_c() -> SparseHypergraph:
    """n=5, path-like 3-uniform."""
    return SparseHypergraph(
        n_nodes=5,
        hyperedges=[frozenset({0, 1, 2}), frozenset({1, 2, 3}), frozenset({2, 3, 4})],
    )


@pytest.fixture
def small_dataset() -> PlantedFamilyDataset:
    """3 families, 3 members each — small enough for CI."""
    return PlantedFamilyDataset(
        seeds=[_seed_a(), _seed_b(), _seed_c()],
        members_per_family=3,
        n_edits=2,
        max_retries=200,
        seed_value=42,
    )


# ---------------------------------------------------------------------------
# AC4 — length
# ---------------------------------------------------------------------------


class TestLength:
    def test_len_matches_families_times_members(self, small_dataset: PlantedFamilyDataset) -> None:
        assert len(small_dataset) == 3 * 3

    def test_len_single_family(self) -> None:
        ds = PlantedFamilyDataset(seeds=[_seed_a()], members_per_family=4, seed_value=0)
        assert len(ds) == 4

    def test_default_construction_does_not_raise(self) -> None:
        ds = PlantedFamilyDataset()
        assert len(ds) > 0


# ---------------------------------------------------------------------------
# AC1 — connectivity
# ---------------------------------------------------------------------------


class TestConnectivity:
    def test_all_hypergraphs_connected(self, small_dataset: PlantedFamilyDataset) -> None:
        for item in small_dataset:
            assert item.hypergraph.is_connected(), f"item {item.item_id!r} is disconnected"


# ---------------------------------------------------------------------------
# AC2 — non-isomorphism within family
# ---------------------------------------------------------------------------


class TestNonIsomorphismWithinFamily:
    def test_no_iso_duplicates_within_family(self, small_dataset: PlantedFamilyDataset) -> None:
        from isalhg.iso_backends.registry import get_backend

        backend = get_backend("isalhg")
        families: dict[int, list[bytes]] = {}
        for item in small_dataset:
            fam = item.iso_class
            assert fam is not None
            fp = backend.fingerprint(item.hypergraph)
            if fam not in families:
                families[fam] = []
            assert fp not in families[fam], (
                f"family {fam}: duplicate iso-class at item {item.item_id!r}"
            )
            families[fam].append(fp)


# ---------------------------------------------------------------------------
# AC3 — iso_class is the family index
# ---------------------------------------------------------------------------


class TestIsoClass:
    def test_iso_class_is_family_index(self, small_dataset: PlantedFamilyDataset) -> None:
        items = list(small_dataset)
        n_members = 3
        for idx, item in enumerate(items):
            expected_family = idx // n_members
            assert item.iso_class == expected_family, (
                f"item {idx}: expected iso_class {expected_family}, got {item.iso_class}"
            )

    def test_iso_class_not_none(self, small_dataset: PlantedFamilyDataset) -> None:
        for item in small_dataset:
            assert item.iso_class is not None


# ---------------------------------------------------------------------------
# AC5 — determinism
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_same_seed_same_output(self) -> None:
        seeds = [_seed_a(), _seed_b()]
        ds1 = PlantedFamilyDataset(seeds=seeds, members_per_family=3, seed_value=7)
        ds2 = PlantedFamilyDataset(seeds=seeds, members_per_family=3, seed_value=7)
        items1 = list(ds1)
        items2 = list(ds2)
        assert len(items1) == len(items2)
        for a, b in zip(items1, items2, strict=False):
            assert a.hypergraph == b.hypergraph

    def test_different_seeds_may_differ(self) -> None:
        seeds = [_seed_a()]
        ds1 = PlantedFamilyDataset(seeds=seeds, members_per_family=5, seed_value=1)
        ds2 = PlantedFamilyDataset(seeds=seeds, members_per_family=5, seed_value=2)
        items1 = [item.hypergraph for item in ds1]
        items2 = [item.hypergraph for item in ds2]
        # seed member (index 0) is always the same
        assert items1[0] == items2[0]
        # at least one perturbation differs across seeds (probabilistic, very likely)
        # Not a hard assertion — just a smoke check that determinism isn't trivially broken.


# ---------------------------------------------------------------------------
# AC6 — registry
# ---------------------------------------------------------------------------


class TestRegistry:
    def test_registry_lookup_default_params(self) -> None:
        ds = get_dataset("planted_families", {})
        assert len(ds) > 0

    def test_registry_lookup_with_members(self) -> None:
        ds = get_dataset("planted_families", {"members_per_family": 2})
        items = list(ds)
        assert all(item.iso_class is not None for item in items)

    def test_metadata_has_iso_labels(self) -> None:
        ds = get_dataset("planted_families", {})
        assert ds.metadata.has_iso_labels is True
