"""Tests for T-M7m: symmetric-family pruning, coarse class labels, and pooling guard.

Acceptance criteria (T-M7m):
  AC-1  Built Stratum A corpus is exactly the 14 kept families.
  AC-2  EXCLUDED_SYMMETRIC names are absent from the built corpus.
  AC-3  Coarse-class assignment is correct for every kept family.
  AC-4  Per-arity partition covers the expected coarse classes.
  AC-5  Arity pooling guard raises when hypergraphs span multiple k values.
  AC-6  Members-cap graceful degradation: logs and uses max feasible, no crash.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Expected data
# ---------------------------------------------------------------------------

EXCLUDED_9 = frozenset(
    {
        "ag24",
        "pg23",
        "pg24",
        "sts13_0",
        "sts13_1",
        "sts15_0",
        "complete_k3_n5",
        "complete_k4_n6",
        "complete_k5_n6",
    }
)

KEPT_14 = frozenset(
    {
        "sts7",
        "sts9",
        "gq22",
        "loose_path_k3",
        "tight_path_k3",
        "loose_cycle_k3",
        "tight_cycle_k3",
        "loose_path_k4",
        "tight_path_k4",
        "loose_cycle_k4",
        "tight_cycle_k4",
        "loose_path_k5",
        "tight_path_k5",
        "tight_cycle_k5",
    }
)

# T-M7o (2026-07-23) added 3 longer arity-4/5 cycles to make cycle_k4 and
# cycle_k5 coarse classes multi-member for A2/A3.
KEPT_17 = KEPT_14 | frozenset(
    {
        "tight_cycle_k4_n8",  # tight_cycle(4, 8), n=8, m=8
        "tight_cycle_k4_n10",  # tight_cycle(4, 10), n=10, m=10
        "tight_cycle_k5_n8",  # tight_cycle(5, 8), n=8, m=8
    }
)

# Coarse class mapping for the 14 kept families.
EXPECTED_COARSE: dict[str, str] = {
    "sts7": "design_k3",
    "sts9": "design_k3",
    "gq22": "design_k3",
    "loose_path_k3": "path_k3",
    "tight_path_k3": "path_k3",
    "loose_cycle_k3": "cycle_k3",
    "tight_cycle_k3": "cycle_k3",
    "loose_path_k4": "path_k4",
    "tight_path_k4": "path_k4",
    "loose_cycle_k4": "cycle_k4",
    "tight_cycle_k4": "cycle_k4",
    "loose_path_k5": "path_k5",
    "tight_path_k5": "path_k5",
    "tight_cycle_k5": "cycle_k5",
}

# Coarse classes per arity.
COARSE_BY_ARITY: dict[int, frozenset[str]] = {
    3: frozenset({"design_k3", "path_k3", "cycle_k3"}),
    4: frozenset({"path_k4", "cycle_k4"}),
    5: frozenset({"path_k5", "cycle_k5"}),
}


# ---------------------------------------------------------------------------
# AC-1 + AC-2: EXCLUDED_SYMMETRIC constant, built corpus membership
# ---------------------------------------------------------------------------


class TestExcludedSymmetric:
    def test_excluded_symmetric_constant_exists(self) -> None:
        from isalhg.datasets.synthetic.known_design_catalog import EXCLUDED_SYMMETRIC

        assert isinstance(EXCLUDED_SYMMETRIC, frozenset)
        assert EXCLUDED_SYMMETRIC == EXCLUDED_9

    def test_kept_a_ids_constant_exists(self) -> None:
        from isalhg.datasets.synthetic.known_design_catalog import KEPT_A_IDS

        assert isinstance(KEPT_A_IDS, frozenset)
        # T-M7o added 3 longer arity-4/5 cycles; KEPT_A_IDS is now 17.
        assert KEPT_A_IDS == KEPT_17

    def test_built_corpus_is_exactly_17_families(self) -> None:
        """build_stratum_a_corpus() with default admitted_ids uses exactly KEPT_17."""
        from isalhg.datasets.synthetic.known_design_catalog import build_stratum_a_corpus

        corpus = build_stratum_a_corpus(
            members_per_family=1,
            n_edits=1,
            seed_value=0,
            dedup_backend="isalhg",
            # admitted_ids=None → default pruned set
        )
        family_labels = {item.extra.get("family_label") for item in corpus}
        # Map family label back to item_id via catalog.
        from isalhg.datasets.synthetic.known_design_catalog import (
            _ALL_ENTRIES,
        )

        id_by_label = {e.family_label: e.item_id for e, _ in _ALL_ENTRIES}
        actual_ids = frozenset(id_by_label.get(lbl, lbl) for lbl in family_labels)
        assert actual_ids == KEPT_17, f"Expected {KEPT_17}, got {actual_ids}"

    def test_excluded_families_absent_from_built_corpus(self) -> None:
        from isalhg.datasets.synthetic.known_design_catalog import (
            _ALL_ENTRIES,
            build_stratum_a_corpus,
        )

        corpus = build_stratum_a_corpus(
            members_per_family=1,
            n_edits=1,
            seed_value=0,
            dedup_backend="isalhg",
        )
        id_by_label = {e.family_label: e.item_id for e, _ in _ALL_ENTRIES}
        family_ids_in_corpus = frozenset(
            id_by_label.get(item.extra.get("family_label"), "") for item in corpus
        )
        overlap = family_ids_in_corpus & EXCLUDED_9
        assert not overlap, f"Excluded families appeared in corpus: {overlap}"

    def test_excluded_constructors_still_importable(self) -> None:
        """Raw constructors stay importable even after exclusion."""
        from isalhg.datasets.synthetic.known_design_catalog import (
            affine_plane_ag24,
            complete_uniform,
        )

        H = affine_plane_ag24()
        assert H.n_nodes == 16
        K = complete_uniform(5, 3)
        assert K.n_nodes == 5


# ---------------------------------------------------------------------------
# AC-3: Coarse-class assignment
# ---------------------------------------------------------------------------


class TestCoarseClassAssignment:
    def test_coarse_class_by_id_constant(self) -> None:
        from isalhg.datasets.synthetic.known_design_catalog import COARSE_CLASS_BY_ID

        for item_id, expected_cc in EXPECTED_COARSE.items():
            assert COARSE_CLASS_BY_ID.get(item_id) == expected_cc, (
                f"{item_id}: expected {expected_cc!r}, got {COARSE_CLASS_BY_ID.get(item_id)!r}"
            )

    def test_known_design_catalog_items_carry_coarse_class(self) -> None:
        from isalhg.datasets.synthetic.known_design_catalog import KnownDesignCatalog

        catalog = KnownDesignCatalog(arities=(3,))
        for item in catalog:
            assert "coarse_class" in item.extra, f"item {item.item_id!r} missing coarse_class"

    def test_coarse_class_values_match_expected(self) -> None:
        from isalhg.datasets.synthetic.known_design_catalog import KnownDesignCatalog

        catalog = KnownDesignCatalog()
        for item in catalog:
            iid = item.item_id
            if iid in EXPECTED_COARSE:
                cc = item.extra.get("coarse_class")
                assert cc == EXPECTED_COARSE[iid], (
                    f"{iid}: expected {EXPECTED_COARSE[iid]!r}, got {cc!r}"
                )

    def test_stratum_a_corpus_items_carry_coarse_class(self) -> None:
        """Coarse class propagates through build_stratum_a_corpus."""
        from isalhg.datasets.synthetic.known_design_catalog import build_stratum_a_corpus

        corpus = build_stratum_a_corpus(
            members_per_family=1,
            n_edits=1,
            seed_value=0,
            dedup_backend="isalhg",
        )
        for item in corpus:
            assert "coarse_class" in item.extra, (
                f"item {item.item_id!r} missing coarse_class in Stratum A corpus"
            )


# ---------------------------------------------------------------------------
# AC-4: Per-arity partition
# ---------------------------------------------------------------------------


class TestPerArityPartition:
    def test_arity3_coarse_classes(self) -> None:
        from isalhg.datasets.synthetic.known_design_catalog import KnownDesignCatalog

        catalog = KnownDesignCatalog(arities=(3,))
        # Exclude symmetric families from the expected set.
        from isalhg.datasets.synthetic.known_design_catalog import EXCLUDED_SYMMETRIC

        cc_set = frozenset(
            item.extra["coarse_class"] for item in catalog if item.item_id not in EXCLUDED_SYMMETRIC
        )
        assert cc_set == COARSE_BY_ARITY[3], f"k3 coarse classes: {cc_set}"

    def test_arity4_coarse_classes(self) -> None:
        from isalhg.datasets.synthetic.known_design_catalog import (
            EXCLUDED_SYMMETRIC,
            KnownDesignCatalog,
        )

        catalog = KnownDesignCatalog(arities=(4,))
        cc_set = frozenset(
            item.extra["coarse_class"] for item in catalog if item.item_id not in EXCLUDED_SYMMETRIC
        )
        assert cc_set == COARSE_BY_ARITY[4], f"k4 coarse classes: {cc_set}"

    def test_arity5_coarse_classes(self) -> None:
        from isalhg.datasets.synthetic.known_design_catalog import (
            EXCLUDED_SYMMETRIC,
            KnownDesignCatalog,
        )

        catalog = KnownDesignCatalog(arities=(5,))
        cc_set = frozenset(
            item.extra["coarse_class"] for item in catalog if item.item_id not in EXCLUDED_SYMMETRIC
        )
        assert cc_set == COARSE_BY_ARITY[5], f"k5 coarse classes: {cc_set}"


# ---------------------------------------------------------------------------
# AC-5: Arity pooling guard
# ---------------------------------------------------------------------------


class TestArityPoolingGuard:
    def test_guard_passes_single_arity(self) -> None:
        from isalhg.datasets.synthetic.known_design_catalog import (
            assert_single_arity_group,
            catalog_seeds,
        )

        hgs_k3 = catalog_seeds(arities=(3,), exclude_symmetric=True)
        # Should not raise.
        assert_single_arity_group(hgs_k3)

    def test_guard_fires_on_mixed_arity(self) -> None:
        from isalhg.datasets.synthetic.known_design_catalog import (
            assert_single_arity_group,
            catalog_seeds,
        )

        hgs_k3 = catalog_seeds(arities=(3,), exclude_symmetric=True)
        hgs_k4 = catalog_seeds(arities=(4,), exclude_symmetric=True)
        mixed = hgs_k3 + hgs_k4
        with pytest.raises(ValueError, match="[Aa]rity"):
            assert_single_arity_group(mixed)

    def test_guard_fires_on_k3_k5_mix(self) -> None:
        from isalhg.datasets.synthetic.known_design_catalog import (
            assert_single_arity_group,
            catalog_seeds,
        )

        hgs_k3 = catalog_seeds(arities=(3,), exclude_symmetric=True)
        hgs_k5 = catalog_seeds(arities=(5,), exclude_symmetric=True)
        with pytest.raises(ValueError, match="[Aa]rity"):
            assert_single_arity_group(hgs_k3 + hgs_k5)

    def test_guard_empty_list_ok(self) -> None:
        from isalhg.datasets.synthetic.known_design_catalog import assert_single_arity_group

        # Empty list is fine (no pooling possible).
        assert_single_arity_group([])


# ---------------------------------------------------------------------------
# AC-6: Members-cap graceful degradation
# ---------------------------------------------------------------------------


class TestMembersCapGraceful:
    def test_partial_family_does_not_crash(self) -> None:
        """PlantedFamilyDataset with allow_partial=True logs instead of crashing."""
        from isalhg.datasets.synthetic.known_design_catalog import fano_plane
        from isalhg.datasets.synthetic.planted_families import PlantedFamilyDataset

        seed = fano_plane()
        # Fano plane has only 1 iso-class among its small arity=3 perturbations
        # in extremely tiny edit budget. Use allow_partial=True.
        ds = PlantedFamilyDataset(
            seeds=[seed],
            members_per_family=10,  # intentionally high
            n_edits=1,
            max_retries=3,  # very few retries — will exhaust
            seed_value=0,
            dedup_backend="isalhg",
            allow_partial=True,
        )
        # Should not raise; should yield at least the seed itself.
        items = list(ds)
        assert len(items) >= 1, "Expected at least the seed item"

    def test_partial_yields_seed_minimum(self) -> None:
        """When retries exhausted with allow_partial=True, at least the seed is kept."""
        from isalhg.datasets.synthetic.known_design_catalog import fano_plane
        from isalhg.datasets.synthetic.planted_families import PlantedFamilyDataset

        seed = fano_plane()
        ds = PlantedFamilyDataset(
            seeds=[seed],
            members_per_family=5,
            n_edits=1,
            max_retries=2,
            seed_value=0,
            dedup_backend="isalhg",
            allow_partial=True,
        )
        items = list(ds)
        # At minimum the seed (member_index=0) must be present.
        assert any(item.extra.get("is_seed") for item in items)

    def test_without_allow_partial_still_raises(self) -> None:
        """Default allow_partial=False keeps the old crashing behavior."""
        from isalhg.datasets.synthetic.known_design_catalog import (
            complete_uniform,
        )
        from isalhg.datasets.synthetic.planted_families import PlantedFamilyDataset

        # K_5^(3) has exactly 1 iso-class; exhausting retries with 3-edit budget
        # at max_retries=2 should crash.
        seed = complete_uniform(5, 3)
        with pytest.raises(RuntimeError, match="exhausted"):
            PlantedFamilyDataset(
                seeds=[seed],
                members_per_family=5,
                n_edits=1,
                max_retries=2,
                seed_value=0,
                dedup_backend="isalhg",
                allow_partial=False,
            )


# ---------------------------------------------------------------------------
# DATA_MANIFEST
# ---------------------------------------------------------------------------


class TestDataManifest:
    def test_data_manifest_exists(self) -> None:
        from isalhg.datasets.synthetic.known_design_catalog import DATA_MANIFEST

        assert DATA_MANIFEST is not None

    def test_data_manifest_has_stratum_a_ids(self) -> None:
        from isalhg.datasets.synthetic.known_design_catalog import DATA_MANIFEST

        assert hasattr(DATA_MANIFEST, "stratum_a_ids") or isinstance(DATA_MANIFEST, dict), (
            "DATA_MANIFEST must expose stratum_a_ids"
        )
        if isinstance(DATA_MANIFEST, dict):
            ids = DATA_MANIFEST.get("stratum_a_ids") or DATA_MANIFEST.get("stratum_a")
        else:
            ids = DATA_MANIFEST.stratum_a_ids
        # T-M7o: KEPT_A_IDS is now 17 (14 original + 3 arity-4/5 cycle additions).
        assert frozenset(ids) == KEPT_17, f"Expected 17 ids, got {frozenset(ids)}"


# ---------------------------------------------------------------------------
# Graceful build + realized-count report (T-M7m fix)
# ---------------------------------------------------------------------------
# These tests FAIL against the pre-fix commit (build_stratum_a_corpus without
# allow_partial → RuntimeError on high-symmetry k4/k5 families) and PASS
# after the fix (allow_partial=True default).
# ---------------------------------------------------------------------------


class TestGracefulBuildAndRealizedCounts:
    """Verify that the Stratum A corpus builds without crashing and that
    realized member counts are reported correctly.

    T-M7m fix: allow_partial=True prevents RuntimeError for high-symmetry
    k4/k5 families.  T-M7o fix: per-family arity cap allows k=4/5 edges,
    so cycle families now generate multiple members; path families may too.
    The corpus now has 17 families (was 14 before T-M7o catalog additions).
    """

    def test_full_17family_corpus_no_crash(self) -> None:
        """build_stratum_a_corpus at default params must not raise."""
        from isalhg.datasets.synthetic.known_design_catalog import build_stratum_a_corpus

        # T-M7m fix: RuntimeError was raised for k4/k5 families.
        # T-M7o: +3 arity-4/5 cycle entries → 17 families total.
        items = list(build_stratum_a_corpus(members_per_family=3, seed_value=0))
        assert len(items) >= 17, f"Expected at least 17 items (1 per family), got {len(items)}"

    def test_k3_families_reach_members_per_family(self) -> None:
        """k=3 families (design/path/cycle) should all reach members_per_family=3."""
        from collections import Counter

        from isalhg.datasets.synthetic.known_design_catalog import build_stratum_a_corpus

        items = list(build_stratum_a_corpus(members_per_family=3, seed_value=0))
        counts = Counter(item.extra["family_label"] for item in items)
        k3_labels = {
            "STS7",
            "STS9",
            "GQ22",
            "LoosePath3",
            "TightPath3",
            "LooseCycle3",
            "TightCycle3",
        }
        for lbl in k3_labels:
            assert counts[lbl] == 3, (
                f"k=3 family {lbl!r} should have 3 realized members, got {counts[lbl]}"
            )

    def test_path_families_k4_k5_realize_at_least_one_member(self) -> None:
        """k=4/5 path families must yield at least 1 member (the seed).

        Pre T-M7o: these families were stuck at 1 member because the arity-cap
        bug rejected all perturbations (arity > self._k=3).  Post T-M7o: the
        per-family k fix allows k=4/5 edges; families may now generate additional
        members.  The invariant is at least 1 (the seed is always included).
        """
        from collections import Counter

        from isalhg.datasets.synthetic.known_design_catalog import build_stratum_a_corpus

        items = list(build_stratum_a_corpus(members_per_family=3, seed_value=0))
        counts = Counter(item.extra["family_label"] for item in items)
        path_labels = {"LoosePath4", "TightPath4", "LoosePath5", "TightPath5"}
        for lbl in path_labels:
            assert counts[lbl] >= 1, (
                f"Path family {lbl!r} expected >= 1 realized member, got {counts[lbl]}"
            )

    def test_runner_path_no_crash(self) -> None:
        """build_stratum_a_seed_corpus (runner helper) must not raise."""
        from experiments.article.analysis.sweep_multi_seed import (
            ADMITTED_A_IDS,
            build_stratum_a_seed_corpus,
        )

        hypergraphs, labels, label_strings, coarse_class_strings = build_stratum_a_seed_corpus(
            seed=0,
            admitted_ids=ADMITTED_A_IDS,
            members_per_family=3,
        )
        assert len(hypergraphs) >= 14
        assert len(hypergraphs) == len(labels) == len(label_strings) == len(coarse_class_strings)

    def test_runner_path_returns_four_elements(self) -> None:
        """build_stratum_a_seed_corpus must return (hgs, labels, fam_labels, cc_labels)."""
        from experiments.article.analysis.sweep_multi_seed import (
            ADMITTED_A_IDS,
            build_stratum_a_seed_corpus,
        )

        result = build_stratum_a_seed_corpus(
            seed=0,
            admitted_ids=ADMITTED_A_IDS,
            members_per_family=3,
        )
        assert len(result) == 4, (
            "build_stratum_a_seed_corpus must return 4-tuple "
            "(hypergraphs, labels, label_strings, coarse_class_strings)"
        )

    def test_coarse_class_strings_non_empty(self) -> None:
        """Every item must carry a non-empty coarse_class string."""
        from experiments.article.analysis.sweep_multi_seed import (
            ADMITTED_A_IDS,
            build_stratum_a_seed_corpus,
        )

        _, _, _, coarse_class_strings = build_stratum_a_seed_corpus(
            seed=0,
            admitted_ids=ADMITTED_A_IDS,
            members_per_family=3,
        )
        assert all(cc != "" for cc in coarse_class_strings), (
            "Every item must have a non-empty coarse_class string"
        )

    def test_realized_counts_per_family_structure(self) -> None:
        """Realized counts per family must cover all 14 admitted families."""
        from collections import Counter

        from experiments.article.analysis.sweep_multi_seed import (
            ADMITTED_A_IDS,
            build_stratum_a_seed_corpus,
        )

        _, _, label_strings, _ = build_stratum_a_seed_corpus(
            seed=0,
            admitted_ids=ADMITTED_A_IDS,
            members_per_family=3,
        )
        from isalhg.datasets.synthetic.known_design_catalog import DATA_MANIFEST

        realized = dict(Counter(label_strings))
        # Expected count comes from the manifest — never hardcode (predates T-M7o).
        expected_n = len(DATA_MANIFEST.stratum_a_ids)
        assert len(realized) == expected_n, (
            f"Expected {expected_n} family labels in realized counts, got {len(realized)}"
        )
        # All values must be >= 1 (the seed is always accepted).
        assert all(v >= 1 for v in realized.values()), (
            "Every admitted family must have at least 1 realized member"
        )

    def test_realized_counts_per_coarse_class_structure(self) -> None:
        """Realized counts per coarse class must cover all 9 admitted coarse classes."""

        from experiments.article.analysis.sweep_multi_seed import (
            ADMITTED_A_IDS,
            build_stratum_a_seed_corpus,
        )

        _, _, label_strings, coarse_class_strings = build_stratum_a_seed_corpus(
            seed=0,
            admitted_ids=ADMITTED_A_IDS,
            members_per_family=3,
        )
        realized_cc: dict[str, int] = {}
        for _lbl, cc in zip(label_strings, coarse_class_strings, strict=False):
            realized_cc[cc] = realized_cc.get(cc, 0) + 1
        # Expected coarse classes for the 14 kept families:
        # k3: design_k3, path_k3, cycle_k3  (3 classes)
        # k4: path_k4, cycle_k4             (2 classes)
        # k5: path_k5, cycle_k5             (2 classes)
        # Total: 7 coarse classes (excluded_* classes are not in kept families).
        assert len(realized_cc) >= 7, (
            f"Expected >= 7 coarse classes in realized counts, got {len(realized_cc)}: "
            f"{list(realized_cc)}"
        )

    def test_seedmetrics_realized_count_fields_serializable(self, tmp_path) -> None:
        """SeedMetrics with realized count fields round-trips through the cache."""
        from experiments.article.analysis.sweep_multi_seed import (
            SeedMetrics,
            _cache_seed_metrics,
            _load_seed_metrics_cache,
        )

        sm = SeedMetrics(
            cell_key="stratum_a",
            stratum="a",
            dist_name="isalhg_levenshtein",
            seed=0,
            n_corpus=28,
            g1_a1=None,
            a2=None,
            a3=None,
            bits=None,
            realized_counts_per_family={"STS7": 3, "LoosePath4": 1},
            realized_counts_per_coarse_class={"design_k3": 3, "path_k4": 1},
            a2a3_dropped_coarse_classes={4: ["path_k4"], 5: ["path_k5", "cycle_k5"]},
        )
        _cache_seed_metrics(sm, tmp_path)
        loaded = _load_seed_metrics_cache("stratum_a", "a", "isalhg_levenshtein", 0, tmp_path)
        assert loaded is not None
        assert loaded.realized_counts_per_family == {"STS7": 3, "LoosePath4": 1}
        assert loaded.realized_counts_per_coarse_class == {"design_k3": 3, "path_k4": 1}
        assert loaded.a2a3_dropped_coarse_classes == {4: ["path_k4"], 5: ["path_k5", "cycle_k5"]}
