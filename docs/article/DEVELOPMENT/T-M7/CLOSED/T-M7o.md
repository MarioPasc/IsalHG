# T-M7o — Fix PlantedFamilyDataset arity-cap bug + add longer arity-4/5 cycles

**Scope:** T-M7 (pre-writing revision — strict data, baselines, sweep/stats)
**Declared:** 2026-07-23 15:44 CEST
**Status:** DONE
**Depends on:** T-M7n ✔ (diagnosed the bug; REPORT.md §3 is the primary source)
**Blocks:** S7 A2/A3 labeled experiments on arity-4/5 families

## Context

`artifacts/power_pilot/REPORT.md §3` confirmed that all k≥4 families collapse to
a single member (the seed only) in `PlantedFamilyDataset` because the arity-cap
check at `planted_families.py:265` compares every perturbed member's max edge
arity against `self._k`, which defaults to 3.  `build_stratum_a_corpus` never
passes a per-seed `k`, so every k=4/5 seed's perturbations are rejected before
the iso-dedup step.

Pilot also identified feasible longer designs:
- `tight_cycle(4, 8)`: n=8, m=8, w*_c p90=0.18 s
- `tight_cycle(4, 10)`: n=10, m=10, w*_c p90=2.34 s
- `tight_cycle(5, 8)`: n=8, m=8, w*_c p90=3.61 s
- `tight_cycle(5, 10)`: n=10, m=10, w*_c p90=39.65 s → OOT, DROPPED

## What to do

1. **Fix the arity cap** in `PlantedFamilyDataset._build()`: the per-family
   effective `k` must be the seed's max arity.  Compute `self._family_k:
   list[int]` from seeds at `__init__` time; replace the static `self._k`
   comparison in the arity-gate with `self._family_k[fam_idx]`.  Keep
   `K_MAX=10` as the alphabet ceiling; do not allow perturbations to exceed the
   seed's arity (members stay within the family's arity band).

2. **Add longer designs** to `known_design_catalog.py`:
   - `tight_cycle_k4_n8` = `tight_cycle(4, 8)`, coarse class `cycle_k4`
   - `tight_cycle_k4_n10` = `tight_cycle(4, 10)`, coarse class `cycle_k4`
   - `tight_cycle_k5_n8` = `tight_cycle(5, 8)`, coarse class `cycle_k5`
   Drop `tight_cycle(5, 10)` (39.65 s OOT).  Keep short cycles as potential
   geometry anchors; the coarse classes end up multi-member.

3. **Re-verify census**: after fix + additions, report multi-member coarse
   classes at k=4 and k=5 with ≥2 members each.

## Files owned

- `src/isalhg/datasets/synthetic/planted_families.py`
- `src/isalhg/datasets/synthetic/known_design_catalog.py`
- `tests/unit/datasets/test_planted_families_arity_fix.py` (new)

## Out of scope here

- `experiments/article/analysis/sweep_multi_seed.py` (owned by T-M7p)
- Stratum B envelope, HIC real anchor, degree-matched generator (T-M7p)
- Any experiment re-run or REPORT.md update

## Acceptance

- [ ] A-1: `test_k5_seed_yields_two_noniso_members` FAILS on unpatched code.
- [ ] A-2: After patch, all k=4 cycle coarse-class members ≥ 2.
- [ ] A-3: After patch, all k=5 cycle coarse-class members ≥ 2.
- [ ] A-4: w*_c feasibility confirmed (< 30 s p90) for each added design.
- [ ] A-5: `pytest tests/unit/datasets/test_planted_families_arity_fix.py -m unit` green.
- [ ] A-6: ruff 3 / mypy 21 (baselines unchanged).

## Closing note

**Closed 2026-07-23. Branch:** `fix/T-M7o-arity-cap`

**Bug confirmed and fixed.** `planted_families.py:265` compared all perturbed
members' max arity against `self._k` (default 3). Added `self._family_k:
list[int]` at `__init__` time (max arity per seed), replaced the static
comparison with `self._family_k[fam_idx]`. Also updated `_make_metadata()` to
report the correct realized max arity.

**Catalog additions** (3 new entries, all in `KEPT_A_IDS`):
- `tight_cycle_k4_n8` = tight_cycle(4, 8) [n=8, m=8], coarse class `cycle_k4`
- `tight_cycle_k4_n10` = tight_cycle(4, 10) [n=10, m=10], coarse class `cycle_k4`
- `tight_cycle_k5_n8` = tight_cycle(5, 8) [n=8, m=8], coarse class `cycle_k5`

`KEPT_A_IDS` grows from 14 → 17. `TOTAL_ENTRIES` grows from 23 → 26.

**Realized census (5 members/family target, 300 retries, seed=0):**
All 17 families fully realized at 5 members each (5.0 avg). Surprise: the
arity-cap fix also recovered path_k4 and path_k5 (those were also stuck at 1
member pre-fix). Every coarse class is now multi-member for A2/A3:
- cycle_k4: 4 families × 5 members = 20 items ✓
- cycle_k5: 2 families × 5 members = 10 items ✓
- path_k4: 2 families × 5 members = 10 items ✓ (was 1/family pre-fix)
- path_k5: 2 families × 5 members = 10 items ✓ (was 1/family pre-fix)
- All k=3 coarse classes: unchanged, 5/family ✓

**Tests:**
- `test_planted_families_arity_fix.py`: 15 tests (unit, not slow)
  — A-1: test_k5_seed_yields_at_least_two_noniso_members FAILED pre-fix, PASSES post-fix ✓
  — A-2/A-3: cycle_k4/k5 multi-membership verified ✓
  — A-4: slow w*_c feasibility tests declared (not run in default suite) ✓
- Updated `test_stratum_a_pruning.py`: KEPT_14 → KEPT_17, path-family
  test updated to >= 1 (was == 1, which was testing the bug), corpus size
  updated to >= 17
- Updated `test_known_design_catalog.py`: TOTAL_ENTRIES 23 → 26

**Checks:** pytest 1249 passed / 0 failed (unit, not slow); ruff 3 (baseline);
mypy 21 (baseline).
