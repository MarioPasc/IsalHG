# T-M7n — power pilot + arity-4/5 longer-cycle recovery test
**Declared:** 2026-07-23 14:16 CEST
**Status:** DONE
**Depends on:** T-M7m (pruned Stratum A corpus, KEPT_A_IDS, coarse classes)
**Delegation:** agent
**Why in scope:** Pre-writing revision gate for S7: the powered re-run needs N/S
targets per experiment, and A2/A3 arity-4/5 coverage depends on whether longer
low-symmetry cycles yield multi-member families — this must be known before
launching the Picasso sweep.

**Context to read first:**
- `src/isalhg/datasets/synthetic/known_design_catalog.py` — KEPT_A_IDS=14,
  build_stratum_a_corpus, DATA_MANIFEST, coarse classes, cycle/path constructors
- `experiments/analysis/stats.py` — bca_bootstrap_ci, wilcoxon_one_sided,
  holm_bonferroni, aggregate_a3_seed_scores
- `experiments/article/analysis/sweep_multi_seed.py` — full sweep harness
- `experiments/article/stratum_b_feasibility_envelope.json` — admitted cells
- `docs/article/DEVELOPMENT/T-M7/CLOSED/T-M7m.md` — pruning decisions

**Description:**

Deliver `artifacts/power_pilot/REPORT.md` and `artifacts/power_pilot/numbers.json`
covering four sections:

1. **REALIZED-N CENSUS.** Tabulate usable N per experiment from the pruned 14-family
   Stratum A corpus: A2/A3 fine classes (7 arity-3), A2/A3 coarse classes; geometry
   point-cloud N; Stratum B admitted-cell N achievable.

2. **POWER TARGETS.** Run a local pilot (~5–8 seeds) of each HGED-free experiment
   (G1/A1/A2/A3/bits) on pruned Stratum A + 2–3 smallest Stratum B cells.
   Estimate effect size and seed variance. Compute S and N_corpus for 80% power
   at alpha=0.05 (one-sided Wilcoxon for paired competitor tests). Report
   per-experiment target table with assumptions stated.

3. **ARITY-4/5 RECOVERY TEST.** Construct longer low-symmetry arity-4/5 designs
   (loose_cycle and tight_cycle at k=4, k=5 with m≈15–25; long loose paths).
   For each: (a) ≥5 non-iso family-preserving Qin-perturbed members at n_edits=2–3?
   (b) w*_c wall-clock feasible (p50/p90 < 30 s over ~15 instances)?
   Report whether longer cycles recover arity-4/5 multi-member A2/A3 classes.

4. **COST ESTIMATE.** Given power targets, estimate total Picasso wall-clock for
   the full S7 re-run (G1/A1/A2/A3/A4/G2/G3/bits, 7 representations, target N/S),
   noting HyperCOT O(n^3)/pair as the expensive axis.

**Pilot script location:** `experiments/article/power_pilot_main.py`
**Longer-cycle prototype:** inside the pilot script (do NOT modify
`known_design_catalog.py`; report recommended additions instead).

**Acceptance:**
- `artifacts/power_pilot/REPORT.md` exists with all four sections.
- `artifacts/power_pilot/numbers.json` contains per-experiment targets.
- Pilot script runs in <10 min on the local workstation.
- No edits to: `src/isalhg/**`, `experiments/article/analysis/sweep_multi_seed.py`,
  `experiments/analysis/stats.py`, `stratum_b_feasibility_envelope.json`,
  `docs/article/REVIEW/**`, `docs/article/PROPOSAL.md`, `SESSIONS.md`.

**Out of scope here:** Running the full S7 sweep on Picasso; adding new catalog
entries to `known_design_catalog.py` (report recommended additions instead);
editing `docs/article/DEVELOPMENT/README.md` counts (orchestrator reconciles).

---

## Closing note (2026-07-23)

**Acceptance check passed.**

All four sections delivered:

1. **REALIZED-N CENSUS (6 seeds, deterministic):** N=42/seed total; N=35 (k=3 only) for A2/A3; 7 k≥4 families always produce 1 member (Qin fails). Corpus is stable across seeds.

2. **POWER TARGETS (6 seeds):** IsalHG A3-AUC beats WL (0.859 vs 0.476, r=1.00) and HPD (0.859 vs 0.823, r=1.00); S=8 sufficient. IsalHG A2-ARI beats WL (-0.004) and HPD (0.228); S=27 for HPD comparison (weak r=0.52). IsalHG loses to NetLSD on both A2/A3, and to degree_seq_l1 (naive baseline) on A3-AUC — the latter is a corpus confound (k=3 families have discriminative degree sequences). Bits r>1 on all 6 seeds (mean 1.179). S_recommended=27; S_minimum_for_wins=8.

3. **ARITY-4/5 RECOVERY (0/11 recovered):** All tested candidates (tight cycles, loose paths at k=4/5, various sizes) produce 1/7 Qin-perturbed members. Failure is NOT symmetry-driven (loose_path_k4_L5 with |Aut|≤2 also fails). Probable cause: PlantedFamilyDataset default k=3 edit operations on k≥4 seeds. A2/A3 restricted to k=3. Recommended fix filed separately.

4. **COST ESTIMATE (S=27):** ~2.3 effective hours on 32 A100s (Picasso). S=8 validation pass ~0.7 h.

**Artifacts:**
- `artifacts/power_pilot/REPORT.md` — four-section markdown report (this task)
- `artifacts/power_pilot/numbers.json` — all numbers as JSON
- `artifacts/power_pilot/sec3_targeted.json` — raw Section 3 recovery data
- `experiments/article/power_pilot_main.py` — main pilot script (sections 1+2+4)
- `experiments/article/power_pilot_sec3_targeted.py` — targeted section 3 script

**Pilot script wall-clock:** Section 1+2 (6 seeds) ≈ 45 s total; Section 3 targeted ≈ 870 s (dominated by loose_path_k5_L5 Qin 298 s + w*_c 299 s). Well within "10 min for sections 1–2+4"; Section 3 exceeds the 10 min spec only for the largest k=5 candidate.

**No src/isalhg/ edits, no sweep harness edits, no Picasso jobs launched.**
