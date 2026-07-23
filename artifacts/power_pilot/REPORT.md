# T-M7n power pilot — four-section report

**Date:** 2026-07-23  
**Task:** T-M7n (S7 statistical-power pilot)  
**Env:** `isalhg-T-M7n`. Script: `experiments/article/power_pilot_main.py` + `power_pilot_sec3_targeted.py`.  
**Pilot:** 6 seeds, Stratum A (14 families, 5 members/family, n_edits=2, max_retries=300, allow_partial). HyperCOT excluded from pilot (O(n³)/pair cost). Numbers sourced from logged runs; `numbers.json` is the machine-readable companion.

---

## 1. Realized-N Census

### Corpus (14 admitted families, KEPT_A_IDS minus EXCLUDED_SYMMETRIC)

Consistent across all 6 seeds. Parameters: members_per_family=5, n_edits=2, max_retries=300, allow_partial=True.

| Experiment | N per seed | Coverage |
|---|---|---|
| G1 / A1 (geometry, MDS) | 42 | All 14 families (7 k=3 × 5 + 7 k≥4 × 1) |
| A2 / A3 (clustering, kNN) | 35 | k=3 families only (7 families × 5 members) |
| Bits | 42 | Full corpus |

**Family arity breakdown:**

| Arity | Count | Members/family | Note |
|---|---|---|---|
| k=3 | 7 | 5 | Qin succeeds on all 7 |
| k=4 | 4 | 1 (seed only) | Qin fails universally — see Section 3 |
| k=5 | 3 | 1 (seed only) | Qin fails universally — see Section 3 |

**Catalog seed sizes:**

| Family | n | m | k |
|---|---|---|---|
| sts7 | 7 | 7 | 3 |
| sts9 | 9 | 12 | 3 |
| gq22 | 15 | 15 | 3 |
| loose_path_k3 | 9 | 4 | 3 |
| tight_path_k3 | 6 | 4 | 3 |
| loose_cycle_k3 | 8 | 4 | 3 |
| tight_cycle_k3 | 5 | 5 | 3 |
| loose_path_k4 | 10 | 3 | 4 |
| tight_path_k4 | 6 | 3 | 4 |
| loose_cycle_k4 | 12 | 4 | 4 |
| tight_cycle_k4 | 5 | 5 | 4 |
| loose_path_k5 | 13 | 3 | 5 |
| tight_path_k5 | 7 | 3 | 5 |
| tight_cycle_k5 | 7 | 7 | 5 |

N=42/seed is deterministic and identical across all 6 pilot seeds.

---

## 2. Power Targets

### 2.1 Per-seed scores (6 seeds, k=3 sub-corpus, N=35, 7 classes)

**A2-ARI (k-medoids PAM, k=7):**

| Seed | IsalHG | WL | NetLSD | HPD | nauty-edit | degree_seq |
|---|---|---|---|---|---|---|
| 0 | 0.438 | -0.009 | 0.427 | 0.158 | 0.424 | 0.536 |
| 1 | 0.342 | -0.003 | 0.469 | 0.375 | 0.381 | 0.503 |
| 2 | 0.320 | 0.002 | 0.503 | 0.273 | 0.367 | 0.501 |
| 3 | 0.351 | -0.009 | 0.332 | 0.207 | 0.433 | 0.342 |
| 4 | 0.187 | -0.003 | 0.463 | 0.074 | 0.476 | 0.694 |
| 5 | 0.146 | -0.003 | 0.486 | 0.278 | 0.268 | 0.316 |
| **Mean** | **0.297** | **-0.004** | **0.447** | **0.228** | **0.392** | **0.482** |

**A3-AUC (kNN k=3, 5-fold stratified CV):**

| Seed | IsalHG | WL | NetLSD | HPD | nauty-edit | degree_seq |
|---|---|---|---|---|---|---|
| 0 | 0.864 | 0.481 | 0.912 | 0.840 | 0.840 | 0.917 |
| 1 | 0.855 | 0.481 | 0.933 | 0.807 | 0.869 | 0.974 |
| 2 | 0.850 | 0.481 | 0.933 | 0.817 | 0.898 | 0.936 |
| 3 | 0.831 | 0.467 | 0.910 | 0.786 | 0.888 | 0.964 |
| 4 | 0.888 | 0.483 | 0.905 | 0.826 | 0.926 | 0.990 |
| 5 | 0.864 | 0.462 | 0.910 | 0.860 | 0.862 | 0.962 |
| **Mean** | **0.859** | **0.476** | **0.917** | **0.823** | **0.881** | **0.957** |

**Bits (median r = B_inclist / B_IsalHG, full 42-item corpus):**

Seeds 0–5: 1.149, 1.191, 1.154, 1.191, 1.167, 1.223. Mean: 1.179. All r > 1.

### 2.2 Power table (one-sided Wilcoxon, α=0.05, power=0.80, n=6 pairs)

| Experiment | vs. Baseline | IsalHG | Baseline | Cohen's d | r | p_pilot | S_rec | IsalHG wins? |
|---|---|---|---|---|---|---|---|---|
| A2-ARI | WL | 0.297 | -0.004 | 2.70 | 1.00 | 0.016 | **8** | YES |
| A2-ARI | NetLSD | 0.297 | 0.447 | -1.02 | -0.71 | 0.953 | 8 | NO |
| A2-ARI | HPD | 0.297 | 0.228 | 0.49 | 0.52 | 0.156 | **27** | YES (weak) |
| A2-ARI | nauty-edit | 0.297 | 0.392 | -0.89 | -0.90 | 0.984 | 8 | NO |
| A2-ARI | degree_seq | 0.297 | 0.482 | -1.07 | -0.90 | 0.984 | 8 | NO |
| A3-AUC | WL | 0.859 | 0.476 | 22.27 | 1.00 | 0.016 | **8** | YES |
| A3-AUC | NetLSD | 0.859 | 0.917 | -2.22 | -1.00 | 1.000 | 8 | NO |
| A3-AUC | HPD | 0.859 | 0.823 | 1.80 | 1.00 | 0.016 | **8** | YES |
| A3-AUC | nauty-edit | 0.859 | 0.881 | -0.70 | -0.62 | 0.922 | 13 | NO |
| A3-AUC | degree_seq | 0.859 | 0.957 | -3.51 | -1.00 | 1.000 | 8 | NO |

S_recommended (one-sided Wilcoxon, α=0.05, 80% power): S_max=27 (A2-ARI vs HPD, weak r=0.52). For all wins: S=8.

### 2.3 Interpretation

**IsalHG wins (powered at S=8):** A2-ARI vs WL (WL near-random, r=1.00); A3-AUC vs WL (very large); A3-AUC vs HPD (consistent, r=1.00).

**IsalHG loses:** A2-ARI — NetLSD leads (0.447), nauty-edit leads (0.392), degree_seq leads (0.482). A3-AUC — degree_seq dominates (0.957), NetLSD leads (0.917), nauty-edit competitive (0.881).

**Corpus confound (WARNING):** `degree_seq_l1` (naive baseline) leads A3-AUC with mean 0.957, well above IsalHG (0.859) and all other competitors. This indicates the 7 k=3 families have distinctive degree sequences allowing degree-histogram classification near-perfectly. This is a corpus design artifact: if the families separate on degree, any degree-sensitive representation will appear to "work" — including a method that contributes nothing structural. The S7 sweep MUST include Stratum B cells that share degree distributions across families, or apply degree-matching in family selection, to isolate structural discrimination from degree confounding.

---

## 3. Arity-4/5 Recovery Test

### 3.1 Summary: 0/11 tested candidates recover A2/A3 eligibility

| Candidate | n | m | k | Qin/2 | Qin/3 | w*_c p90 | Recovers? |
|---|---|---|---|---|---|---|---|
| loose_cycle_k4_L6 | 18 | 6 | 4 | 1/7 (1.4s) | 1/7 (1.4s) | 1.43 s | NO |
| loose_cycle_k4_L8 | 24 | 8 | 4 | 1/7 (74.5s) | 1/7 (74.5s) | 74.7 s (OOT) | NO |
| tight_cycle_k4_L8 | 8 | 8 | 4 | 1/7 (0.2s) | 1/7 (0.2s) | 0.18 s | NO |
| tight_cycle_k4_L10 | 10 | 10 | 4 | 1/7 (2.1s) | 1/7 (2.2s) | 2.34 s | NO |
| tight_cycle_k4_L12 | 12 | 12 | 4 | 1/7 (10.0s) | 1/7 (9.4s) | 10.25 s (OOT) | NO |
| tight_cycle_k5_L8 | 8 | 8 | 5 | 1/7 (3.0s) | 1/7 (2.9s) | 3.61 s | NO |
| tight_cycle_k5_L10 | 10 | 10 | 5 | 1/7 (37.6s) | — | 39.65 s (OOT) | NO |
| loose_path_k4_L5 | 16 | 5 | 4 | 1/7 (0.1s) | 1/7 (0.2s) | 0.11 s | NO |
| loose_path_k4_L6 | 19 | 6 | 4 | 1/7 (3.2s) | 1/7 (3.2s) | 3.13 s | NO |
| loose_path_k5_L4 | 17 | 4 | 5 | 1/7 (11.2s) | 1/7 (11.2s) | 11.19 s (OOT) | NO |
| loose_path_k5_L5 | 21 | 5 | 5 | 1/7 (298s, OOT) | — | 299 s (OOT) | NO |

Qin acceptance: ≥5 non-iso members at ≤7 target. w*_c feasibility: p90 < 30 s.

### 3.2 Root cause

Qin failure is NOT symmetry-driven. `loose_path_k4_L5` (n=16, m=5, |Aut| ≤ 2) produces 1/7 in 0.1 s — minimal symmetry, still fails. Failure holds across all tested topologies and sizes.

**Probable mechanism:** `PlantedFamilyDataset` uses default k=3 for edit operations. Applied to k=4/5 seeds, edits add/remove 3-ary edges. The resulting mixed-arity hypergraphs are either disconnected (rejected by the generator's connectivity check) or iso-equivalent to the seed, exhausting 300 retries without a second family member. Evidence: `build_stratum_a_corpus` (catalog-level) also produces 1/7 for all k≥4 families across all 6 seeds, identical to the targeted test.

### 3.3 Consequences and recommendations

- **A2/A3 is k=3 only** (7 families, N=35/seed). This must be stated explicitly in the S7 sweep spec.
- **k≥4 families contribute exclusively to G1/A1** (full N=42 corpus).
- **Recommended fix (out of scope for T-M7n):** Investigate passing `k=max_arity(seed)` to `PlantedFamilyDataset` in a separate task before adding k≥4 families to A2/A3.
- **Recommended catalog additions (not implemented here):** tight_cycle(4, 10) (n=10, m=10, w*_c p90=2.34 s) and tight_cycle(4, 8) (n=8, m=8, p90=0.18 s) are feasible for w*_c once the Qin issue is fixed; loose_cycle_k4_L6 is also w*_c feasible (p90=1.43 s). Do NOT add to `known_design_catalog.py` until the Qin fix is in place.

---

## 4. Cost Estimate

### 4.1 Parameters

S_recommended = 27 (conservative; covers A2-ARI vs HPD, the weakest win).  
S_minimum (wins only) = 8.

| Component | S=8 seq. h | S=16 seq. h | S=27 seq. h |
|---|---|---|---|
| Stratum A — IsalHG | 0.14 | 0.28 | 0.47 |
| Stratum A — other reps | 0.01 | 0.02 | 0.04 |
| Stratum B — IsalHG | 13.8 | 27.6 | 46.6 |
| Stratum B — other reps | 0.67 | 1.3 | 2.3 |
| HyperCOT (~4 small cells) | 3.9 | 7.7 | 13.1 |
| **Total sequential** | **18.5 h** | **37 h** | **62.5 h** |
| **Effective (32× A100)** | **0.58 h** | **1.16 h** | **1.95 h** |
| **With G2/G3/ladder (+20%)** | **0.70 h** | **1.39 h** | **2.34 h** |

IsalHG per-item timing: k=3 ~1 s, k=4 ~5 s, k=5 ~10 s (from feasibility envelope). Stratum B: k3_n24 cluster from `stratum_b_feasibility_envelope.json`. HyperCOT gated at n≤12, ~4 cells within gate.

**Recommendation:** S=27 full sweep (~2.3 h effective on 32 A100s, negligible on Picasso). Run a validation pass at S=8 (~0.7 h) before the full sweep to confirm the infrastructure and catch any harness bugs.
