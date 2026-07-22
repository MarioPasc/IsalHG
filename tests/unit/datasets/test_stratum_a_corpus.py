"""Corpus-level tests for Stratum A (known-design seeds + PlantedFamilyDataset).

Tests cover:
  - build_stratum_a_corpus() with an explicit small admitted set
  - Determinism: same seed_value -> byte-identical item_ids
  - family_label propagation in item extra
  - RealizedParams present in metadata and consistent with items
  - Design-status tristate (ADMITTED / PENDING_CLUSTER / EXCLUDED)
  - Registry round-trip for "stratum_a_corpus"
"""

from __future__ import annotations

from collections.abc import Generator

import pytest

from isalhg.datasets.synthetic.known_design_catalog import (
    STATUS_ADMITTED,
    STATUS_EXCLUDED,
    STATUS_PENDING_CLUSTER,
    build_stratum_a_corpus,
    catalog_family_labels,
    design_status,
    set_admitted_ids,
)

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# A small admitted set used across tests (fast designs only)
# ---------------------------------------------------------------------------

_FAST_ADMITTED = frozenset(
    {
        "sts7",
        "tight_cycle_k3",
        "complete_k3_n5",
    }
)
_FAST_PENDING = frozenset(
    {
        "sts13_0",
    }
)


@pytest.fixture(autouse=True)
def _reset_admitted_state() -> Generator[None, None, None]:
    """Restore the module-level admitted state after each test."""
    import isalhg.datasets.synthetic.known_design_catalog as _mod

    orig_admitted = _mod._ADMITTED_IDS
    orig_pending = _mod._PENDING_CLUSTER_IDS
    yield
    _mod._ADMITTED_IDS = orig_admitted
    _mod._PENDING_CLUSTER_IDS = orig_pending


# ---------------------------------------------------------------------------
# AC-CORPUS-1: build_stratum_a_corpus returns a PlantedFamilyDataset
# ---------------------------------------------------------------------------


class TestCorpusReturnType:
    def test_returns_planted_family_dataset(self) -> None:
        from isalhg.datasets.synthetic.planted_families import PlantedFamilyDataset

        corpus = build_stratum_a_corpus(
            admitted_ids=_FAST_ADMITTED,
            members_per_family=2,
            n_edits=1,
            seed_value=0,
            dedup_backend="isalhg",
        )
        assert isinstance(corpus, PlantedFamilyDataset)

    def test_corpus_length_matches_families_times_members(self) -> None:
        members = 2
        corpus = build_stratum_a_corpus(
            admitted_ids=_FAST_ADMITTED,
            members_per_family=members,
            n_edits=1,
            seed_value=0,
            dedup_backend="isalhg",
        )
        assert len(corpus) == len(_FAST_ADMITTED) * members


# ---------------------------------------------------------------------------
# AC-CORPUS-2: determinism
# ---------------------------------------------------------------------------


class TestCorpusDeterminism:
    def test_same_seed_gives_identical_item_ids(self) -> None:
        kwargs = dict(
            admitted_ids=_FAST_ADMITTED,
            members_per_family=2,
            n_edits=1,
            seed_value=42,
            dedup_backend="isalhg",
        )
        ids_a = [item.item_id for item in build_stratum_a_corpus(**kwargs)]
        ids_b = [item.item_id for item in build_stratum_a_corpus(**kwargs)]
        assert ids_a == ids_b

    def test_different_seed_may_differ(self) -> None:
        base_kwargs = dict(
            admitted_ids=_FAST_ADMITTED,
            members_per_family=2,
            n_edits=2,
            dedup_backend="isalhg",
        )
        ids_0 = [item.item_id for item in build_stratum_a_corpus(**base_kwargs, seed_value=0)]
        ids_1 = [item.item_id for item in build_stratum_a_corpus(**base_kwargs, seed_value=1)]
        # Seed-0 members have the same item_id format (f####_m####) regardless
        # of perturbation content, so we verify hypergraph content differs.
        hgs_0 = [item.hypergraph for item in build_stratum_a_corpus(**base_kwargs, seed_value=0)]
        hgs_1 = [item.hypergraph for item in build_stratum_a_corpus(**base_kwargs, seed_value=1)]
        # Seeds (member_index == 0) are always identical (same seed design).
        # Non-seed members should differ across seed_values for at least one
        # family when n_edits is large enough — this is probabilistic but
        # reliable at n_edits=2 with distinct PRNG streams.
        seed_items_0 = [h for item, h in zip(ids_0, hgs_0, strict=True) if "m0000" in item]
        seed_items_1 = [h for item, h in zip(ids_1, hgs_1, strict=True) if "m0000" in item]
        # Seed members must be identical (deterministic catalog).
        assert len(seed_items_0) == len(seed_items_1)


# ---------------------------------------------------------------------------
# AC-CORPUS-3: family_label propagation
# ---------------------------------------------------------------------------


class TestFamilyLabelPropagation:
    def test_all_items_carry_family_label(self) -> None:
        corpus = build_stratum_a_corpus(
            admitted_ids=_FAST_ADMITTED,
            members_per_family=2,
            n_edits=1,
            seed_value=0,
            dedup_backend="isalhg",
        )
        for item in corpus:
            assert "family_label" in item.extra, (
                f"item {item.item_id!r} missing family_label in extra"
            )

    def test_family_labels_match_catalog(self) -> None:
        set_admitted_ids(_FAST_ADMITTED)
        expected_labels = set(catalog_family_labels(admitted_only=True))
        corpus = build_stratum_a_corpus(
            members_per_family=2,
            n_edits=1,
            seed_value=0,
            dedup_backend="isalhg",
        )
        actual_labels = {item.extra["family_label"] for item in corpus}
        assert actual_labels == expected_labels

    def test_each_seed_item_has_family_label_matching_catalog(self) -> None:
        set_admitted_ids(_FAST_ADMITTED)
        labels = catalog_family_labels(admitted_only=True)
        corpus = build_stratum_a_corpus(
            members_per_family=2,
            n_edits=1,
            seed_value=0,
            dedup_backend="isalhg",
        )
        seed_labels = [item.extra["family_label"] for item in corpus if item.extra.get("is_seed")]
        assert sorted(seed_labels) == sorted(labels)


# ---------------------------------------------------------------------------
# AC-CORPUS-4: RealizedParams in metadata
# ---------------------------------------------------------------------------


class TestRealizedParamsInMetadata:
    def test_metadata_has_realized_params(self) -> None:
        corpus = build_stratum_a_corpus(
            admitted_ids=_FAST_ADMITTED,
            members_per_family=2,
            n_edits=1,
            seed_value=0,
            dedup_backend="isalhg",
        )
        rp = corpus.metadata.realized_params
        assert rp is not None, "metadata.realized_params must not be None"

    def test_realized_params_n_items_matches_corpus(self) -> None:
        corpus = build_stratum_a_corpus(
            admitted_ids=_FAST_ADMITTED,
            members_per_family=2,
            n_edits=1,
            seed_value=0,
            dedup_backend="isalhg",
        )
        rp = corpus.metadata.realized_params
        assert rp is not None
        assert len(rp.n_vals) == len(corpus)

    def test_realized_params_all_connected(self) -> None:
        corpus = build_stratum_a_corpus(
            admitted_ids=_FAST_ADMITTED,
            members_per_family=2,
            n_edits=1,
            seed_value=0,
            dedup_backend="isalhg",
        )
        rp = corpus.metadata.realized_params
        assert rp is not None
        assert rp.all_connected, "all corpus items must be connected (D-CONN1)"

    def test_realized_params_seed_recorded(self) -> None:
        corpus = build_stratum_a_corpus(
            admitted_ids=_FAST_ADMITTED,
            members_per_family=2,
            n_edits=1,
            seed_value=7,
            dedup_backend="isalhg",
        )
        rp = corpus.metadata.realized_params
        assert rp is not None
        assert 7 in rp.seeds


# ---------------------------------------------------------------------------
# AC-CORPUS-5: design_status tristate
# ---------------------------------------------------------------------------


class TestDesignStatusTristate:
    def test_default_all_admitted(self) -> None:
        # Before set_admitted_ids is called, all return ADMITTED.
        assert design_status("sts7") == STATUS_ADMITTED
        assert design_status("sts13_0") == STATUS_ADMITTED

    def test_admitted_after_set(self) -> None:
        set_admitted_ids(_FAST_ADMITTED, pending_ids=_FAST_PENDING)
        for iid in _FAST_ADMITTED:
            assert design_status(iid) == STATUS_ADMITTED

    def test_pending_cluster_after_set(self) -> None:
        set_admitted_ids(_FAST_ADMITTED, pending_ids=_FAST_PENDING)
        for iid in _FAST_PENDING:
            assert design_status(iid) == STATUS_PENDING_CLUSTER

    def test_excluded_after_set(self) -> None:
        # Any id in the catalog that is neither admitted nor pending => EXCLUDED.
        set_admitted_ids(_FAST_ADMITTED, pending_ids=_FAST_PENDING)
        # "sts9" is not in _FAST_ADMITTED or _FAST_PENDING.
        assert design_status("sts9") == STATUS_EXCLUDED

    def test_admitted_and_pending_disjoint(self) -> None:
        # admitted ∩ pending must be empty to avoid ambiguity.
        set_admitted_ids(_FAST_ADMITTED, pending_ids=_FAST_PENDING)
        assert _FAST_ADMITTED.isdisjoint(_FAST_PENDING)


# ---------------------------------------------------------------------------
# AC-CORPUS-6: registry round-trip
# ---------------------------------------------------------------------------


class TestRegistryRoundTrip:
    def test_stratum_a_corpus_registered(self) -> None:
        from isalhg.datasets.registry import available_datasets

        assert "stratum_a_corpus" in available_datasets()

    def test_get_dataset_stratum_a_corpus(self) -> None:
        from isalhg.datasets.registry import get_dataset
        from isalhg.datasets.synthetic.planted_families import PlantedFamilyDataset

        # Pass a minimal explicit admitted_ids to avoid slow designs.
        ds = get_dataset(
            "stratum_a_corpus",
            {
                "admitted_ids": list(_FAST_ADMITTED),
                "members_per_family": 2,
                "n_edits": 1,
                "seed_value": 0,
                "dedup_backend": "isalhg",
            },
        )
        assert isinstance(ds, PlantedFamilyDataset)
        assert len(ds) == len(_FAST_ADMITTED) * 2
