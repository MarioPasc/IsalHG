"""Regression tests for PlantedFamilyDataset arity-cap bug fix (T-M7o).

The bug: PlantedFamilyDataset._build() compared every perturbed member's max
hyperedge arity against self._k (the dataset-level parameter, defaulting to 3).
When a k=4 or k=5 seed is passed via build_stratum_a_corpus, self._k is still 3,
so EVERY perturbation of a k=4/5 seed is rejected ("arity > k=3") and those
families collapse to a single member (the seed itself).

Fix: use per-family k = max arity of seed, stored as self._family_k[fam_idx].

Acceptance:
  A-1  test_k5_seed_yields_two_noniso_members FAILS on unpatched code.
  A-2  k=4 cycle coarse class is multi-member after fix + catalog additions.
  A-3  k=5 cycle coarse class is multi-member after fix + catalog additions.
  A-4  w*_c feasibility for new designs (< 30 s p90; marked slow).
  A-5  ruff 3 / mypy 21 unchanged.
"""

from __future__ import annotations

import pytest

from isalhg.datasets.synthetic.known_design_catalog import (
    COARSE_CLASS_BY_ID,
    KEPT_A_IDS,
    build_stratum_a_corpus,
    tight_cycle,
)
from isalhg.datasets.synthetic.planted_families import PlantedFamilyDataset

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _member_count(seed, *, members_per_family: int = 5, n_edits: int = 2) -> int:
    """Return the number of non-iso members generated from a single seed."""
    ds = PlantedFamilyDataset(
        seeds=[seed],
        members_per_family=members_per_family,
        n_edits=n_edits,
        max_retries=300,
        seed_value=0,
        dedup_backend="isalhg",
        allow_partial=True,
    )
    return len(list(ds))


# ---------------------------------------------------------------------------
# A-1: Regression — the test that MUST fail against the unpatched code
#
# This test is the canonical proof that the bug existed.  It was verified to
# fail on the pre-fix code (T-M7o 2026-07-23): PlantedFamilyDataset with
# self._k=3 rejects all perturbations of a k=5 seed, yielding only the seed
# itself (1 member).  The test asserts >= 2 members.
# ---------------------------------------------------------------------------


class TestArityCapFix:
    def test_k4_seed_yields_at_least_two_noniso_members(self) -> None:
        """A k=4 seed must produce >=2 non-iso members (was 1 before fix)."""
        seed = tight_cycle(4, 5)  # n=5, m=5, k=4 — smallest k=4 tight cycle
        count = _member_count(seed, members_per_family=5, n_edits=2)
        assert count >= 2, (
            f"Expected >=2 members from k=4 tight_cycle(4,5) seed, got {count}. "
            "The arity-cap bug (self._k=3 rejection) is not fixed."
        )

    def test_k5_seed_yields_at_least_two_noniso_members(self) -> None:
        """A k=5 seed must produce >=2 non-iso members (was 1 before fix).

        This test MUST FAIL against the pre-fix PlantedFamilyDataset
        (self._k defaults to 3; every arity-5 edge triggers the rejection gate).
        """
        seed = tight_cycle(5, 7)  # n=7, m=7, k=5 — existing catalog entry
        count = _member_count(seed, members_per_family=5, n_edits=2)
        assert count >= 2, (
            f"Expected >=2 members from k=5 tight_cycle(5,7) seed, got {count}. "
            "The arity-cap bug (self._k=3 rejection) is not fixed."
        )

    def test_family_k_attribute_matches_seed_max_arity(self) -> None:
        """PlantedFamilyDataset stores per-family k = seed's max arity."""
        seed_k4 = tight_cycle(4, 5)  # k=4
        seed_k3 = tight_cycle(3, 5)  # k=3
        ds = PlantedFamilyDataset(
            seeds=[seed_k3, seed_k4],
            members_per_family=2,
            n_edits=1,
            max_retries=100,
            seed_value=0,
            dedup_backend="isalhg",
            allow_partial=True,
        )
        assert hasattr(ds, "_family_k"), "PlantedFamilyDataset must have _family_k attribute"
        assert ds._family_k[0] == 3, f"Expected family_k[0]=3, got {ds._family_k[0]}"
        assert ds._family_k[1] == 4, f"Expected family_k[1]=4, got {ds._family_k[1]}"


# ---------------------------------------------------------------------------
# A-2: k=4 cycle coarse class is multi-member in the Stratum A corpus
# ---------------------------------------------------------------------------


class TestCycleK4MultiMember:
    def test_cycle_k4_coarse_class_has_multiple_entries_in_catalog(self) -> None:
        """cycle_k4 coarse class must have >=2 entries in KEPT_A_IDS."""
        cycle_k4_ids = [iid for iid in KEPT_A_IDS if COARSE_CLASS_BY_ID.get(iid) == "cycle_k4"]
        assert len(cycle_k4_ids) >= 2, (
            f"cycle_k4 coarse class has only {len(cycle_k4_ids)} entries: {cycle_k4_ids}. "
            "Need >=2 for A2/A3 multi-member eligibility."
        )

    def test_tight_cycle_k4_n8_in_catalog(self) -> None:
        """tight_cycle_k4_n8 must be a kept entry in the catalog."""
        assert "tight_cycle_k4_n8" in KEPT_A_IDS, (
            "tight_cycle_k4_n8 not found in KEPT_A_IDS. "
            "It must be added to the known_design_catalog."
        )

    def test_tight_cycle_k4_n10_in_catalog(self) -> None:
        """tight_cycle_k4_n10 must be a kept entry in the catalog."""
        assert "tight_cycle_k4_n10" in KEPT_A_IDS, (
            "tight_cycle_k4_n10 not found in KEPT_A_IDS. "
            "It must be added to the known_design_catalog."
        )

    def test_cycle_k4_seeds_each_yield_multiple_members(self) -> None:
        """Every cycle_k4 catalog seed must yield >=2 non-iso members after fix."""
        from isalhg.datasets.synthetic.known_design_catalog import _ENTRY_BY_ID

        cycle_k4_ids = [iid for iid in KEPT_A_IDS if COARSE_CLASS_BY_ID.get(iid) == "cycle_k4"]
        for iid in cycle_k4_ids:
            _, H = _ENTRY_BY_ID[iid]
            count = _member_count(H, members_per_family=5, n_edits=2)
            assert count >= 2, (
                f"cycle_k4 entry '{iid}' yields only {count} member(s). "
                "Expected >=2 after arity-cap fix."
            )


# ---------------------------------------------------------------------------
# A-3: k=5 cycle coarse class is multi-member in the Stratum A corpus
# ---------------------------------------------------------------------------


class TestCycleK5MultiMember:
    def test_cycle_k5_coarse_class_has_multiple_entries_in_catalog(self) -> None:
        """cycle_k5 coarse class must have >=2 entries in KEPT_A_IDS."""
        cycle_k5_ids = [iid for iid in KEPT_A_IDS if COARSE_CLASS_BY_ID.get(iid) == "cycle_k5"]
        assert len(cycle_k5_ids) >= 2, (
            f"cycle_k5 coarse class has only {len(cycle_k5_ids)} entries: {cycle_k5_ids}. "
            "Need >=2 for A2/A3 multi-member eligibility."
        )

    def test_tight_cycle_k5_n8_in_catalog(self) -> None:
        """tight_cycle_k5_n8 must be a kept entry in the catalog."""
        assert "tight_cycle_k5_n8" in KEPT_A_IDS, (
            "tight_cycle_k5_n8 not found in KEPT_A_IDS. "
            "It must be added to the known_design_catalog."
        )

    def test_cycle_k5_seeds_each_yield_multiple_members(self) -> None:
        """Every cycle_k5 catalog seed must yield >=2 non-iso members after fix."""
        from isalhg.datasets.synthetic.known_design_catalog import _ENTRY_BY_ID

        cycle_k5_ids = [iid for iid in KEPT_A_IDS if COARSE_CLASS_BY_ID.get(iid) == "cycle_k5"]
        for iid in cycle_k5_ids:
            _, H = _ENTRY_BY_ID[iid]
            count = _member_count(H, members_per_family=5, n_edits=2)
            assert count >= 2, (
                f"cycle_k5 entry '{iid}' yields only {count} member(s). "
                "Expected >=2 after arity-cap fix."
            )


# ---------------------------------------------------------------------------
# A-4: w*_c feasibility for new designs (slow — real timing)
# ---------------------------------------------------------------------------


@pytest.mark.slow
class TestWstarFeasibility:
    """w*_c p90 < 30 s over ~15 instances for each new design.

    These tests instantiate PlantedFamilyDataset with 15 members to sample
    the instance distribution and time the canonical fingerprint computation.
    Marked @pytest.mark.slow — not run in the default suite.
    """

    def _p90_seconds(self, seed, n_instances: int = 15) -> float:
        import time

        from isalhg.iso_backends.isalhg_backend import IsalHGBackend

        backend = IsalHGBackend()
        ds = PlantedFamilyDataset(
            seeds=[seed],
            members_per_family=n_instances,
            n_edits=2,
            max_retries=500,
            seed_value=0,
            dedup_backend="isalhg",
            allow_partial=True,
        )
        times: list[float] = []
        for item in ds:
            t0 = time.perf_counter()
            backend.fingerprint(item.hypergraph)
            times.append(time.perf_counter() - t0)

        times_sorted = sorted(times)
        idx = min(int(0.90 * len(times_sorted)), len(times_sorted) - 1)
        return times_sorted[idx]

    def test_tight_cycle_k4_n8_feasible(self) -> None:
        p90 = self._p90_seconds(tight_cycle(4, 8))
        assert p90 < 30.0, f"tight_cycle(4,8) p90={p90:.2f}s exceeds 30 s limit"

    def test_tight_cycle_k4_n10_feasible(self) -> None:
        p90 = self._p90_seconds(tight_cycle(4, 10))
        assert p90 < 30.0, f"tight_cycle(4,10) p90={p90:.2f}s exceeds 30 s limit"

    def test_tight_cycle_k5_n8_feasible(self) -> None:
        p90 = self._p90_seconds(tight_cycle(5, 8))
        assert p90 < 30.0, f"tight_cycle(5,8) p90={p90:.2f}s exceeds 30 s limit"


# ---------------------------------------------------------------------------
# A-5: Stratum A corpus build with k=4/5 families succeeds
# ---------------------------------------------------------------------------


class TestStratumACorpusWithArityFix:
    def test_stratum_a_cycle_k4_families_have_multiple_members(self) -> None:
        """build_stratum_a_corpus with cycle_k4 seeds yields >1 member per family."""
        cycle_k4_ids = frozenset(
            iid for iid in KEPT_A_IDS if COARSE_CLASS_BY_ID.get(iid) == "cycle_k4"
        )
        corpus = build_stratum_a_corpus(
            admitted_ids=cycle_k4_ids,
            members_per_family=5,
            n_edits=2,
            max_retries=300,
            seed_value=0,
            dedup_backend="isalhg",
            allow_partial=True,
        )
        items = list(corpus)
        families: dict[int, int] = {}
        for item in items:
            fam = item.extra["family_index"]
            families[fam] = families.get(fam, 0) + 1

        for fam_idx, count in families.items():
            assert count >= 2, (
                f"Stratum A cycle_k4 family {fam_idx} has only {count} member(s). "
                "Expected >=2 after arity-cap fix."
            )

    def test_stratum_a_cycle_k5_families_have_multiple_members(self) -> None:
        """build_stratum_a_corpus with cycle_k5 seeds yields >1 member per family."""
        cycle_k5_ids = frozenset(
            iid for iid in KEPT_A_IDS if COARSE_CLASS_BY_ID.get(iid) == "cycle_k5"
        )
        corpus = build_stratum_a_corpus(
            admitted_ids=cycle_k5_ids,
            members_per_family=5,
            n_edits=2,
            max_retries=300,
            seed_value=0,
            dedup_backend="isalhg",
            allow_partial=True,
        )
        items = list(corpus)
        families: dict[int, int] = {}
        for item in items:
            fam = item.extra["family_index"]
            families[fam] = families.get(fam, 0) + 1

        for fam_idx, count in families.items():
            assert count >= 2, (
                f"Stratum A cycle_k5 family {fam_idx} has only {count} member(s). "
                "Expected >=2 after arity-cap fix."
            )
