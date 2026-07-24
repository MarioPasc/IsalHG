# T-M7q — G2/A4 re-run on the corrected Stratum A corpus
**Declared:** 2026-07-24 12:18 CEST
**Status:** OPEN
**Depends on:** T-M7e (the pipelines and configs this re-executes — CLOSED),
T-M7m (prune), T-M7o (arity-cap fix), T-M7h (envelope FINAL).
**Origin:** 2026-07-24 S7 re-run handoff
(`docs/article/DEVELOPMENT/HANDOFF_S7_RERUN.md` §4.3), directed by Mario.
T-M7e closed on 2026-07-22 against a Stratum A membership that has since
changed: T-M7m removed `complete_k3_n5`, `complete_k4_n6`, `complete_k5_n6`
(perturbation-failing complete uniforms) and six feasibility-DNF
planes/large-Steiner designs; T-M7o added `tight_cycle_k4_n8`,
`tight_cycle_k4_n10`, `tight_cycle_k5_n8` and fixed the arity cap so every
family realizes 5 members. T-M7e's G2 ladder and A4 cells are built on
families that no longer exist in the corpus (7 of its 14 ladder cells and 6 of
its 11 A4 cells name the three dropped completes), so its result dirs are
archived as superseded. This task re-executes the same pipelines against the
current corpus. **The corpus itself is FINAL — do not re-derive, re-prune, or
re-litigate it.**
**Context to read first:**
- `docs/article/DEVELOPMENT/HANDOFF_S7_RERUN.md` — §2 the final envelope,
  §3 the two claim-constraining findings, §5 the landmines
- `docs/article/DEVELOPMENT/T-M7/CLOSED/T-M7e.md` — the full spec being
  re-executed and the superseded measured baseline to compare against
- `src/isalhg/datasets/synthetic/known_design_catalog.py` — `DATA_MANIFEST`
  is the single source of truth for Stratum A membership (17 ids); read it,
  never a hardcoded list
- `experiments/article/configs/{g2_catalog_sensitivity,g2_design_ladder,a4_design}.yaml`
- `experiments/article/analysis/g2.py` — `_REGIME_PREDICTION` still maps the
  *old* 17 ids; reconcile against `DATA_MANIFEST.stratum_a_ids`
- `docs/article/theoretical/stability.md` §4.2 — the three-regime prediction
  being re-scored
**Description:** Re-point the three configs at `DATA_MANIFEST.stratum_a_ids`
(current 17) and re-execute, on the corrected corpus: (1) **G2 catalog
sensitivity** with the nauty contrast and acceptance-rate reporting;
(2) **G2 design-seeded ladder response**; (3) **A4 design-seeded shortest
path** with decoded S2H intermediates. Re-score the §4.2 three-regime
confrontation on the new membership and emit the updated
`regime_confrontation.json`. Report the delta against T-M7e's superseded
numbers explicitly (which per-regime verdicts moved, and whether the
`tight_path_k4` falsification survives). Realized-parameter logging
throughout. Local compute (T-M7e ran locally); nothing here goes to Picasso.
**Also in this lane — G3 verification (no re-run).** A T-M7r re-run of the
T-M7f G3 experiment was declared and then **withdrawn on evidence**
(2026-07-24): G3's six bases (`tight_cycle_k3_n5`, `loose_path_k3_n9`,
`tight_path_k4_n6`, `tight_path_k5_n7`, `sts9_k3`, `gq22_k3`) all derive from
families still in `DATA_MANIFEST`, and `g3_sequence.py` calls
`random_connected_edit(..., max_arity=...)` directly rather than through
`PlantedFamilyDataset`, so the T-M7o arity-cap bug never reached it. Confirm
that mechanically — assert each G3 base's family is a member of
`DATA_MANIFEST.stratum_a_ids`, and confirm no G3 code path constructs a
`PlantedFamilyDataset` or a `PerturbationLadderHypergraphs` with a defaulted
`arity_range=(2, 3)` — and record the result in the closing note. If either
check fails, **stop and report**; do not re-run G3 inside this task.
**Acceptance:** every G2/A4 cell id present in the emitted artifacts is a
member of `DATA_MANIFEST.stratum_a_ids` and no dropped family appears
anywhere; `_REGIME_PREDICTION` covers exactly the current 17; G2 profiles +
nauty contrast + ladder response re-emitted with acceptance rates; the §4.2
confrontation re-scored with a stated confirm/falsify count and an explicit
diff vs T-M7e's 16/17; A4 re-emits monotonicity, recovery, and ≥3 decoded
intermediates on a design-seeded path spanning arities 3/4/5; superseded
T-M7e result dirs moved under the `results/superseded/` convention, not
deleted; all prior G2/A4 pins that still apply stay green; the G3 verification
above is recorded with its two checks and their outcomes; suite matches the
session baselines (1430 passed / 9 skipped / 25 deselected, ruff 3, mypy 21).
**Out of scope here:** the sweep/stats harness (T-M7d), G3 (T-M7r), E1′ (frozen
— do not re-open the oracle), prose folding into `theoretical/stability.md`
§4.2 or `empirical/applications.md` (a doc pass follows the measurement),
any change to `src/isalhg/datasets/synthetic/` corpus definitions.
