# Measured facts — what the previous iteration actually established

*Foundation fact sheet for the D-ART3 re-scope. Produced 2026-09-03 by a
read-only survey of the drive results tree
(`/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/`) and the ledger
closing notes, re-computing aggregates from the data files rather than trusting
prose. Every number carries its provenance path. Read this before quoting any
prior number in the new article.*

**Two corrections this survey forces on the existing docs.**

1. The "S7 measured headlines" still quoted in
   `docs/article/DEVELOPMENT/README.md` (ν = 0.097, D̂ = 17, degree-seq ARI
   0.451 vs IsalHG 0.285, AUC 0.948 vs 0.920) come from the **size-confounded
   Stratum A corpus retracted on 2026-08-09**. The FINAL corpus is Stratum C
   (§B.1 below), on which IsalHG *loses* clustering and kNN to nauty-Levi edit,
   HPD and NetLSD. Never quote the S7 numbers as current.
2. "k = 7 and k = 10 measured infeasible" has **no timing record on the drive**;
   every such block is `not_runnable` (generator not implemented, or arity >
   node count). The measured envelope is k = 3 to n ≈ 24 at low density and
   k = 5 at n = 8. Do not repeat the k = 7/10 claim without re-measuring.

---

# Survey of prior IsalHG (v3 "characterize → exploit") measured results

Read-only survey, 2026-09-03. Drive root `D = /media/mpascual/Sandisk2TB/research/ISAL/isalhg`.
Repo root `P = /home/mpascual/research/code/IsalHG`. Every number below was read from the
data file named, not from prose, unless the row says "prose".

Authoritative index: `D/results/RESULTS_MANIFEST.md` (last reconciled 2026-08-09).

---

## A. Inventory

| Results dir | Task | Corpus (families / n,m,k / N / seeds) | Measured | Status | Provenance |
|---|---|---|---|---|---|
| `D/results/T-M4b/` | T-M4b | **Stratum C**: 3 size-controlled cells (n,m)=(9,12),(12,20),(15,35), k=3, 12 swap-planted families × 6 members = **72 items/cell**; one exact degree sequence per (cell,seed) ⇒ `size_l1`,`degree_seq_l1` ≡ 0 by construction | G1 geometry (ν, D̂, stress, hubness) + A1 MDS + A2 clustering + A3 kNN + bits, 8 reps | **FINAL 2026-08-09** | `T-M4b/stats/stratum_c_{n9m12,n12m20,n15m35}_stats.json`; `sweep_summary.json`; `d_matrix/…/D.npy` |
| `D/results/T-M7d/` | T-M7d/s/t | **Stratum B**: 10 admitted ER cells (`k3_n{8,16,24}`, `k5_n8`, ρ∈{1,2,4}); 6 reps | geometry-vs-density trends only (no A2/A3 keys present) | **FINAL**, S=27; 3 cells void | `T-M7d/stats/er_uniform_*_stats.json` (10 files; 3 have `wilcoxon:{}`) |
| `D/results/T-M7q/` | T-M7q | 17 admitted design families (arity 3/4/5, n=5–15, m=3–15), 2 seeds; ladders + A4 pools (n_pool=29, n_ladder=21) | G2 single-edit sensitivity (1700 edits), ladder response (56 ladders/560 steps), A4 path (8 instances, 4 reps) | **FINAL** | `T-M7q/g2_catalog_sensitivity/**/g2_catalog_sensitivity.json`, `…/regime_confrontation.json`, `g2_design_ladder/**/design_ladder.json`, `a4_design/**/a4_result.json` |
| `D/results/T-M5a/` | T-M5a | 11-block connected mini-corpus n5–n10 (630 pairs/block); bits pooled N=320, n=5–11, m=3–12, k=3 | E1′ ρ(d_I, exact HGED); bits compression | **FROZEN — do not re-run oracle** | `T-M5a/figures/e1prime_result.json`; `T-M5a/bits/{info_content_result,pooled_info_content}.json` |
| `D/results/T-M7h/` | T-M7h | 23 designs (Stratum A pilot, 3 runs, 300 s timeout, 30 s admit) + 148 Stratum B blocks (30-instance pilots) | **feasibility envelope for `w*_c`** | **FINAL** | `T-M7h/stratum_a/{admitted_catalog.txt,feasibility_pilot_stratum_a.json}`; `T-M7h/stratum_b/per_block/*.json` |
| `D/results/T-M7d-validation{,-v2}/` | — | same corpus, S=8 shakeout | 1 rep / 7 reps | **archived, not cited** | `*/sweep_summary.json` |
| `D/results/superseded/T-M7d_stratum_a/` | T-M7d | **Stratum A**: 17 design families × 5 = 85 items, only **14 distinct (n,m)** ⇒ size-confounded | the "S7 headlines" still quoted in the ledger README | **SUPERSEDED 2026-08-09** | `superseded/T-M7d_stratum_a/stats/stratum_a_stats.json` |
| `D/results/superseded/{n240,T-M5b,c,d,e,g,j,l,T-M7f}` | T-M5* | N=60 / N=240 planted lineage; pre-prune G2/G3; HIC OD6 tables | historical only — **no article claim reads from here** | superseded | `superseded/T-M5j/tables/*.{csv,json}` etc. |
| `D/results/preprint/` | — | iso-benchmark (nauty/Traces/bliss), 1967 JSON | separate paper | separate | `preprint/experiment/analysis_output/` |

Other drive folders (one line each):
`D/data/HIC` 17 MB — iMoonLab HIC repo clone (loaders/generators, IMDB hypergraph atlas).
`D/data/arb_benson` 3.6 GB — ARB/Benson archives (`labeled/`, `temporal/`, `raw_archives/`, `MANIFEST.md`); **all 10 real candidates NO-GO** (single giant networks, not instance collections; T-M7g).
`D/misc/HGED` 3.2 MB — bespoke HGED solver fidelity study (`results/table2_*_{exact,clamp10}_*.json`, `docs/T-M2a_fidelity_report.md`).
`D/docs` — `isalhg_idea.pdf` (seed proposal), `variable_length_gray_code.pdf`.
`D/proofs/completeness` — Theorem A `.tex/.pdf` (+ `.bak-t-m0c`). `D/proofs/stability` — Theorem B, Lemma B1, pointer-run amortization `.tex/.pdf`.
`D/article/{journal,preprint}` — Overleaf-style project snapshots.

---

## B. Headline numbers per exhibit

### B.1 Geometry + A2 + A3 — the FINAL body (Stratum C, S=27, 95 % BCa)
Source: `D/results/T-M4b/stats/stratum_c_*_stats.json`. HyperCOT **absent** from all three cells
(gated out at N=72 > 20). A3 reported at k=5. Sign convention below: **bold** = best.

| metric | cell | IsalHG | nauty-Levi edit | HPD-JSD | NetLSD | HyperWL | degree-seq / size |
|---|---|---|---|---|---|---|---|
| ν | (9,12) | **0.137** [.136,.140] | 0.041 [.036,.045] | 0.000 | 0.000 | 0.000 | 0.000 |
| ν | (12,20) | **0.061** [.060,.062] | 0.011 | 0.000 | 0.000 | 0.000 | 0.000 |
| ν | (15,35) | **0.011** [.010,.011] | 0.003 | 0.000 | 0.000 | 0.000 | 0.000 |
| D̂ (CV-MDS) | (9,12) | 27.4 [26.9,28.0] | 38.6 [37.5,39.3] | 15.7 [15.1,16.2] | 3.5 [3.3,3.7] | 40 (cap) | 1.0 |
| D̂ | (12,20)/(15,35) | 40 (**censored at cap**) | 40 (cap) | 26.0 / 33.1 | 3.3 / 3.0 | 40 (cap) | 1.0 |
| stress-1 | (9,12)/(12,20)/(15,35) | 0.055 / 0.021 / 0.059 | 0.019 / 0.026 / 0.043 | 0.000 | 0.000 | 0.275–0.345 | 0.000 |
| hubness skew | all 3 cells | 0.919 / 0.935 / 0.943 | 0.385 / 0.584 / 0.574 | 0.634 / 0.844 / 1.106 | −0.403 / −0.294 / −0.349 | **2.079** (tie artifact) | **2.079** |
| **A2 ARI** | (9,12) | 0.026 [.019,.038] | **0.235** [.207,.265] | 0.108 | 0.045 | −0.000 | −0.000 |
| **A2 ARI** | (12,20) | 0.028 [.017,.040] | **0.399** [.365,.439] | 0.259 | 0.064 | −0.000 | −0.000 |
| **A2 ARI** | (15,35) | 0.016 [.009,.025] | **0.614** [.571,.657] | 0.519 | 0.123 | −0.000 | −0.000 |
| A2 NMI | (15,35) | 0.380 | **0.802** | 0.760 | 0.482 | 0.238 | 0.238 |
| A2 silhouette | (15,35) | 0.015 | 0.209 | 0.188 | **0.437** | 0.000 | 0.000 |
| **A3 AUC k=5** | (9,12) | 0.545 [.530,.563] | **0.804** [.783,.827] | 0.677 | 0.589 | 0.492 | 0.492 |
| **A3 AUC k=5** | (12,20) | 0.569 [.554,.583] | **0.888** [.873,.903] | 0.828 | 0.626 | 0.492 | 0.492 |
| **A3 AUC k=5** | (15,35) | 0.565 [.550,.581] | 0.938 [.930,.946] | **0.942** [.932,.951] | 0.714 | 0.492 | 0.492 |

Exact Holm-corrected one-sided Wilcoxon (27 paired seeds, family size 60, `…::a2::ari` /
`…::a3::auc_k5`, same file):
- **Competitor > IsalHG**: nauty p_Holm = 4.47e-7 (all 3 cells, both tasks, effect size −1.00);
  HPD p_Holm = 4.47e-7 to 1.05e-6; NetLSD p_Holm = 4.7e-3 / 1.4e-3 (9,12 & 12,20) down to 4.47e-7 (15,35).
- **IsalHG > floor** (WL, degree-seq, size): p_Holm = 4.5e-4 … 7.5e-3 (ARI), 4.1e-6 … 8.9e-7 (AUC);
  median_diff only **+0.019 to +0.022 ARI**, +0.040 to +0.085 AUC.

### B.2 Geometry-vs-density (Stratum B, IsalHG only, S=27) — `T-M7d/stats/er_uniform_*_stats.json`
| cell | ν | D̂ | stress | hubness |
|---|---|---|---|---|
| k3 n8 ρ1 / ρ2 / ρ4 | 0.140 / 0.101 / 0.066 | 18.6 / 27.3 / 33.9 | 0.063 / 0.045 / 0.028 | 0.61 / 0.67 / 0.85 |
| k3 n16 ρ1 / ρ2 | 0.047 / 0.008 | 36.0 / 40 (cap) | 0.021 / 0.025 | 0.63 / 0.67 |
| k3 n24 ρ1 | 0.016 | 40 (cap) | 0.013 | 0.67 |
| k5 n8 ρ1 | 0.141 | 17.7 | 0.065 | 0.62 |
| k3 n16 ρ4, k3 n24 ρ2, k5 n8 ρ2 | **VOID** — IsalHG DNF at 4 h wall; `wilcoxon:{}`, no CIs | | | |
Trend: **ν falls monotonically and D̂ rises with n and with density** — the space becomes more
Euclidean and higher-dimensional as instances grow.

### B.3 G2 sensitivity + ladder — `T-M7q/`
Single-edit response `s(e)` pooled over **1700 edits** (17 designs × 100 edits × 2 seeds),
recomputed from `g2_catalog_sensitivity/**/*.json`:
- **IsalHG: Q1 = 3, median = 5, Q3 = 9 tokens** (mean 7.32/7.46, max 25).
- **nauty-Levi canonical string: Q1 = 20, median = 30, Q3 = 37 tokens** (mean 29.2/29.7, max 72).
  ⇒ IsalHG's interquartile response is **3× narrower**; per-regime IQR ratio 2–19× (`regime_confrontation.json`).
- Regime confrontation: **16/17 confirmed, 1 falsified** — `tight_path_k4` (heavy_tail_frac 0.210
  where "unimodal" was predicted); acceptance_frac = 0.941. GQ(2,2) heavy-tail confirmed (0.230)
  but there IQR_ours = 1 vs IQR_nauty = 0 (the one regime where nauty is tighter).
- Ladder (`g2_design_ladder/`, 56 ladders × 10 steps = 560 steps, 7 fixtures × 2 seeds):
  increment **Q1 = 6, median = 12, Q3 = 18 tokens**; per-ladder monotone fraction **0.706**;
  **55/56 ladders globally increasing**; ρ_Spearman(budget t, d_I) = **0.385** (p = 3.2e-21), Pearson 0.402.

### B.4 A4 shortest path — `T-M7q/a4_design/**/a4_result.json` (8 instances, pool 29, 19 true intermediates)
| rep | mean recovery | monotone frac | mean path nodes | decodability |
|---|---|---|---|---|
| IsalHG | 0.125 | 1.000 | 4.38 | **8/8 all_valid, mean 2.38 intermediates** |
| NetLSD | **0.257** | 1.000 | 7.00 | none (no decoder) |
| HPD-JSD | 0.191 | 1.000 | 6.12 | none |
| HyperWL | 0.000 | 1.000 | 2.12 | none |
IsalHG **loses recovery to NetLSD and HPD**; its only unique property here is decodability.
That decodability score is itself **vacuous** (see D-4); the genuine replacement measurement is
**62/62 ambient intermediates decode and are connected, only 10/62 (the endpoints) canonical**
(`P/docs/article/DEVELOPMENT/T-M5/OPEN/T-M5m.md`; probe `scripts/diagnostics/ambient_decodability_probe.py`).

### B.5 E1′ — `d_I` vs exact HGED (`T-M5a/figures/e1prime_result.json`, FROZEN)
Spearman **ρ = 0.6222** (p ≈ 0), Pearson r = 0.6634, OLS β = 0.5682, **N = 6,921 pairs**,
11/12 blocks (630 pairs each). Per-cell ρ: n5 0.633/0.657, n6 **0.809**/0.556, n7 0.524/0.670,
n8 **0.481**/0.506, n9 0.617/0.721, n10 0.685 — range **0.481–0.809**, median 0.633.
Excluded whole-block: `n10_s1` at the oracle ceiling (> 100 GB / 18 h, PI-decided).

### B.6 Bits / compactness (`T-M5a/bits/`, FROZEN)
N = 320 items (n = 5–11, m = 3–12, k = 3). **compression ratio r > 1 on 320/320 (fraction 1.000)**;
median r = **1.4413**, mean 1.4622, range 1.072–2.365; one-sided Wilcoxon W = 51360,
**p = 1.62e-54**; median 81.41 bits (IsalHG) vs 114.0 bits (incidence list); OLS β = 0.7485.
Per-cell inside Stratum C (`T-M4b/stats/`): median r = **1.5625 / 1.3343 / 1.1904** at
(9,12)/(12,20)/(15,35), gt1_fraction = 1.000 in all three ⇒ **the advantage decays as m grows**.
String length: median `|w*_c|` = 22 tokens (range 4–31). Checked here: the bound
**`|w*_c| ≤ m(1+kn)` holds on 320/320**, and is extremely loose — actual/bound ratio
median **0.073** (range 0.054–0.114).

### B.7 HIC real-data exhibit (superseded dir, T-M5j/k)
`D/results/superseded/T-M5j/tables/*.{csv,json}`. `w*_c` yield: Wri-Genre **92.5 %**,
Wri-Genre-M **91.7 %** (clean); Dir-Genre 43.0 %, Dir-Genre-M 38.7 %, Dir-Form 38.6 %,
Wri-Form 34.4 % (heavily censored). On the two clean sets: **A2 ARI < 0.10 for every
representation** (genre is near-unclusterable); A3 AUC@k=9 — IsalHG 0.673, NetLSD ≈ nauty 0.654,
WL 0.624 (WL hubness skew 4.5–7.4). Geometry on real data: ν = 0.160/0.200, D̂_CV = 10–11,
D̂_Horn = 1 — **much lower-dimensional than the synthetic corpora**.
Gate verdict T-DQ3′: **NO-GO** — corpus-level k = 110 ≫ K_MAX = 10; arity-capped sub-corpus
retains 1471/1869 (78.7 %); 27/100 budgeted DNF, *not* size-concentrated (symmetry-driven).

### B.8 Scalability frontier for `w*_c` — `T-M7h/` (30-instance pilots, 300 s timeout, admit p90 ≤ 30 s)
| block | n | k | ρ | p50 | p90 | verdict |
|---|---|---|---|---|---|---|
| er k3 n24 ρ1 | 24 | 3 | 1 | 1.74 s | 4.27 s | ADMITTED |
| er k3 n24 ρ2 | 24 | 3 | 2 | 4.22 s | 9.92 s | ADMITTED (but DNF at 4 h at S=27 scale) |
| er k3 n24 ρ4 | 24 | 3 | 4 | 42.1 s | 164.8 s | EXCLUDED (3/30 > 300 s) |
| er k3 n32 ρ1 | 32 | 3 | 1 | 34.3 s | 146.2 s | EXCLUDED |
| er k3 n32 ρ2 | 32 | 3 | 2 | 97.3 s | 188.9 s | EXCLUDED (6/30 > 300 s) |
| er k5 n8 ρ1 / ρ2 | 8 | 5 | 1 / 2 | 3.30 / 8.95 s | 5.39 / 12.80 s | ADMITTED (ρ2 DNF at 4 h at S=27) |

Design instances (`stratum_a/admitted_catalog.txt`, 17/23 admitted): sts7 0.024 s, sts9 0.299 s,
gq22 3.045 s, tight_cycle_k5 0.356 s, complete_k5_n6 0.141 s — all ≤ 3.1 s.
**Excluded designs**: sts13_0 p90 = **165.6 s**, sts13_1 = **158.9 s**; sts15_0, ag24, pg23, pg24
**DNF at 300 s**. Additional (T-M4b note): STS(15) PG(3,2) (|Aut| = 20160) pristine `w*_c` = **617 s**;
rigid STS(15) and STS(19) instances **> 900 s**. Cost driver measured to be **Steiner
pair-coverage tie structure, not |Aut|** (single-edit cost ≈ 30–39 s regardless of |Aut|).

---

## C. Properties of IsalHG exhibited

### C.1 Favourable (each = fact + number + file)
1. `w*_c` is a **complete isomorphism invariant** (Theorem A, proved) so `d_I` is a genuine metric on iso-classes — `D/proofs/completeness/theorem_a_completeness.pdf`.
2. **Every string decodes**: 62/62 intermediates on Levenshtein alignment paths decode to *connected* hypergraphs, and only the 10 endpoints are canonical — `P/docs/article/DEVELOPMENT/T-M5/OPEN/T-M5m.md`. No competitor has a decoder at all (`T-M7q/a4_design/**/a4_result.json`: `decodability` key exists only for `isalhg_levenshtein`).
3. **The word is short**: compression ratio r > 1 on **320/320** items, median 1.441, Wilcoxon p = 1.62e-54 — `T-M5a/bits/info_content_result.json`.
4. **The length bound is real and very loose**: `|w*_c| ≤ m(1+kn)` holds 320/320, actual/bound median 0.073 — computed from `T-M5a/bits/pooled_info_content.json`.
5. **Local, non-avalanching edit response**: single edit moves Q1=3 / median=5 / Q3=9 tokens vs nauty's 20/30/37 over 1700 edits — `T-M7q/g2_catalog_sensitivity/`. Confirmed in 16/17 regimes (`regime_confrontation.json`).
6. **Monotone response to accumulated edits**: 55/56 ladders globally increasing, mean per-ladder monotone fraction 0.706, ρ(t, d_I) = 0.385 — recomputed from `T-M7q/g2_design_ladder/`.
7. **Correlates with exact HGED**: ρ = 0.622 over 6,921 pairs, per-cell 0.481–0.809, and **HGED = 0 ⇔ d_I = 0** on every block — `T-M5a/figures/e1prime_result.json`.
8. **Measurably non-Euclidean**: ν = 0.137/0.061/0.011 across Stratum C, the **largest ν of any representation tested** (nauty 0.041 → 0.003; WL/HPD/NetLSD/naive all ν = 0.000) — `T-M4b/stats/`. This is the empirical licence for medoid/PAM over centroid methods.
9. **Benign hubness**: k-occurrence skew ≈ 0.92–0.94, vs WL and both naive baselines pinned at the 2.079 tie artifact — `T-M4b/stats/`.
10. **Fast on small designs**: sts7 24 ms, sts9 299 ms, GQ(2,2) 3.0 s; ER k3 n24 ρ1 p50 = 1.74 s — `T-M7h/stratum_a/admitted_catalog.txt`, `T-M7h/stratum_b/per_block/`.

### C.2 Unfavourable — the new article must not assume these away
1. **IsalHG loses A2 clustering to three of five competitors on the FINAL corpus**: ARI 0.016–0.028 vs nauty 0.235–0.614, HPD 0.108–0.519, NetLSD 0.045–0.123; every loss Holm-significant at p ≤ 1.4e-3 — `T-M4b/stats/stratum_c_*_stats.json`.
2. **IsalHG loses A3 kNN likewise**: AUC@k5 0.545–0.569 vs nauty 0.804–0.938, HPD 0.677–0.942, NetLSD 0.589–0.714 — same files. Its margin over the structural floor is only +0.04 to +0.09 AUC.
3. **A4 path recovery is worse than two competitors**: 0.125 vs NetLSD 0.257, HPD 0.191 — `T-M7q/a4_design/`.
4. **The shipped A4 decodability score was vacuous** (it decoded pool members that were already hypergraphs) — `P/docs/article/DEVELOPMENT/T-M5/OPEN/T-M5m.md`, still OPEN.
5. **Single-edit avalanche on unanchored substrates**: an incidence swap moves ≈ 30–50 % of the string; on d-regular trivially-labelled hypergraphs a 2-edge swap changes ≈ 30–35 of ≈ 50 tokens, drowning the class signal (max achievable ARI 0.234 over 4 constructions) — T-M7p impossibility record, `P/docs/article/DEVELOPMENT/T-M7/CLOSED/T-M7p.md`.
6. **Hard feasibility ceiling**: k=3 only to n ≈ 24 at low density; k=5 only at n=8; three admitted cells still DNF at a 4-hour wall at S=27 — `D/results/RESULTS_MANIFEST.md`, `T-M7d/stats/` (three files with `wilcoxon:{}`).
7. **Symmetric/rigid designs are effectively uncomputable**: STS(13) p90 ≈ 159–166 s; STS(15)/AG(2,4)/PG(2,3)/PG(2,4) DNF at 300 s; STS(15) rigid and STS(19) > 900 s — `T-M7h/stratum_a/admitted_catalog.txt`, T-M4b note.
8. **Real data fails the gate**: HIC corpus k = 110 vs K_MAX = 10; 4 of 6 IMDB datasets retain only 34–43 % of items — T-DQ3′ NO-GO, `superseded/T-M5j/tables/`.
9. **D̂ censors at the estimator cap (40) on 2 of 3 FINAL cells**, so intrinsic dimension is only a lower bound there — `T-M4b/stats/`.
10. **Compactness decays with size**: median r 1.5625 → 1.3343 → 1.1904 as (n,m) grows from (9,12) to (15,35) — `T-M4b/stats/`.
11. **d_I is strongly length-coupled**: MDS PC1 correlates 0.960 with `|w*_c|` and 0.956 with `m`; `d_I` correlates ρ = 0.867 with the canonical-length gap — the confound that killed Stratum A (T-M4b).

---

## D. Pitfalls: bugs, supersessions, prose-vs-data checks

### D.1 Bugs found and fixed (from the ledger closing notes)
1. **Bits tokenization** (T-M5a): `w.split(";")` overcounted ≈ 2.7×, twice reversing the compactness conclusion; fixed via `instructions.parse()`, regression-pinned.
2. **Leaky CV in D̂** (T-M5b): in-sample RMSE monotone-decreasing ⇒ D̂ rode to the cap; fixed with Gower out-of-sample extension.
3. **`runner._build_dataset` kwarg/seed mismatch** (T-M5i): 2 defects, 16 new tests.
4. **HIC table truncation** (T-M5k): an HPD patch dropped non-HPD rows from 2 clean-dataset tables.
5. **`PlantedFamilyDataset` arity cap** (T-M7o): static `k=3` rejected all k≥4 perturbations, collapsing arity-4/5 families to a single member; kept-family count 14 → 17.
6. **Chung-Lu arity cap** (T-M7m) and **mixed-arity ER shared-p** (T-M7i, ≈ 86 % of edges at max arity).
7. **Wilcoxon never persisted at S=27** (T-M7t): the array ran one task per (cell, rep) so no task held two reps; `harvest_summary.json` reported 60 entries computed in memory and never written. Bidirectional Holm families added on the fix.
8. **Orbit-pruning invariant false** (T-OPTa): the per-node-fingerprint orbit-membership hypothesis was falsified; pruning reverted, no speedup delivered.
9. `T-M7d/stats/` is **locally authoritative** — the Picasso copy still has empty `wilcoxon` dicts; never mirror Picasso→local over it (`RESULTS_MANIFEST.md`).

### D.2 Supersessions
- **Stratum A → Stratum C (D-M4b, 2026-08-09).** Stratum A had 17 families over only 14 distinct (n,m) cells; the naive `size_l1` baseline alone scored **ARI 0.442 / AUC 0.932**, beating 5/7 and 4/7 representations. Archived to `superseded/T-M7d_stratum_a/`. Guard added: `tests/integration/test_corpus_confound_guard.py`.
- **N=60 → N=240 → Stratum C** planted lineage retained under `superseded/{n240,T-M5b..l}/`; no article claim reads from there.
- **v2 HGED pillar retired at D-ART2**: density sweep, competitor HGED head-to-head, mutual information, BP-HGED cross-check all dropped.
- **T-M5g's G2 verdict (5 confirmed / 2 falsified) superseded by T-M7q (16/17 confirmed, 1 falsified)** after the arity-cap fix.

### D.3 Prose ↔ data cross-checks (11 checked; 10 match, 1 mismatch, 1 unverifiable)
| # | Claim (prose) | Data file | Verdict |
|---|---|---|---|
| 1 | ν = 0.137 / 0.061 / 0.011 (`applications.md:230`) | `T-M4b/stats/*` → 0.137[.136,.140], 0.061, 0.011 | **MATCH** |
| 2 | D̂ = 27.4 [26.9,28.0] at (9,12) (`applications.md:232`) | → 27.444 [26.889, 27.963] | **MATCH** |
| 3 | A2 ARI nauty 0.614 [.571,.657] at (15,35) (`applications.md:284-297`) | → identical | **MATCH** |
| 4 | A3 AUC@k5 IsalHG 0.565 [.550,.581] at (15,35) | → identical | **MATCH** |
| 5 | E1′ ρ = 0.622, N = 6,921, per-cell 0.48–0.81 (`correlation.md:120-133`) | `e1prime_result.json` → 0.6222, 6921, 0.481–0.809 | **MATCH** |
| 6 | bits r > 1 on 320/320, median 1.441, p = 1.6e-54 (`correlation.md:159-172`) | `info_content_result.json` → 1.000, 1.4413, 1.62e-54 | **MATCH** |
| 7 | G2 IQR ours 3–9 median 5; nauty Q1 20 / Q3 37 (`applications.md:171-180`) | recomputed pooled over both seeds → 3/5/9 and 20/30/37 | **MATCH** (single-seed s0 gives nauty Q1 = 19; prose pools 2 seeds) |
| 8 | Ladder Q1 6 / median 12 / Q3 18, monotone 0.71 (`applications.md:182-186`) | recomputed → 6/12/18, 0.706 | **MATCH** |
| 9 | ρ(t, d_I) = 0.39 over 560 steps (`geometry.md:187-188`) | recomputed → 0.385, p = 3.2e-21 | **MATCH** |
| 10 | A4 recovery IsalHG 0.125 / NetLSD 0.257 / HPD 0.191 / WL 0.000; decodability 8/8, mean 2.4 (`applications.md:394-409`) | `a4_result.json` → identical; 2.38 | **MATCH** |
| 11 | **Ledger README "S7 measured headlines": ν = 0.097, D̂ = 17, stress = 0.046, degree-seq ARI 0.451 vs IsalHG 0.285, AUC 0.948 vs 0.920** | these are exactly `superseded/T-M7d_stratum_a/stats/stratum_a_stats.json` (ν 0.097[.096,.099], D̂ 16.8, stress 0.046, degree 0.451, isalhg 0.285, AUC 0.948/0.920) | **MISMATCH IN STATUS** — the numbers are real but come from the **size-confounded corpus superseded on 2026-08-09**. `P/docs/article/DEVELOPMENT/README.md` still presents them as the current headline while `applications.md`/`geometry.md` have moved to Stratum C. Anyone reading the ledger first will quote retracted numbers. |

### D.4 One claim I could not verify from the data
**"k = 7 and k = 10 measured infeasible."** Repeated in `RESULTS_MANIFEST.md`, the ledger README,
and `applications.md:479-489`; T-M7h's closing note says "12 blocks (incl. all k=7/k=10) TIMEOUT at 8 h".
On the drive, **no timing record for any k=7 or k=10 block exists**. In
`T-M7h/stratum_b/per_block/*.json` every such block is `not_runnable`:
k=7 → `generator_not_impl` (chung_lu, ×18) or `mode_not_impl` (mixed ER, ×18);
k=10 → same, plus `r_gt_n` ×3 for uniform ER at n=8 (arity 10 > 8 nodes is definitionally impossible,
not a timing result). The only measured timeouts on the drive are k=3 at n=24 ρ4 and n=32.
Either the 8-hour envelope run's outputs were never synced to this drive, or the claim
over-reads `not_runnable` as "timed out". **The new article must not repeat it unchecked.**

---

## E. Reusable for the new (median/consensus of N knowledge bases) article

Facts that survive the supersessions and remain directly usable:

1. **Closed alphabet / total decodability — the strongest asset.** 62/62 intermediates on
   Levenshtein alignment paths decode to *connected* hypergraphs while only the 2 endpoints are
   canonical (T-M5m). For a median/consensus paper this is exactly the property that makes a
   *computed* median string meaningful: the consensus word decodes to an actual knowledge base
   even though it is not any input's canonical form. Reuse the ambient probe, not the retracted
   pool-based score.
2. **Compactness with a proved bound.** r > 1 on 320/320, median 1.441, p = 1.62e-54; and
   `|w*_c| ≤ m(1+kn)` verified with median slack 0.073. Usable as-is for a cost argument over N
   knowledge bases. Caveat: the ratio decays with m (1.56 → 1.19 from (9,12) to (15,35)).
3. **Non-Euclidean mass ν licenses k-medoids/PAM.** IsalHG carries the largest ν measured
   (0.137 at (9,12)); WL, HPD, NetLSD and both naive baselines are ν = 0.000. Since a *median* is
   a medoid-type object, this is a direct, already-measured licence — and the strongest surviving
   geometry result. Note ν → 0.011 by (15,35): the licence weakens as instances grow.
4. **Sensitivity profile vs nauty avalanche.** 3/5/9 vs 20/30/37 tokens over 1700 edits, 16/17
   regimes confirmed. A consensus/median over strings needs edits to be *local*; this is the
   evidence that they are for IsalHG and are not for the canonical-string competitor. Pair it with
   the honest counterweight: on unanchored/regular substrates the response rises to 30–50 % of
   the string (T-M7p), so any median must be built on anchored or labelled substrates.
5. **E1′ correlation ρ = 0.622 with exact HGED, and HGED = 0 ⇔ d_I = 0.** Reusable as a
   characterization (a median under `d_I` is not a median under HGED, but the two agree on
   identity and correlate moderately). Frozen — do not re-run the oracle.
6. **Feasibility frontier for realistic sizing.** Plan corpora at k = 3, n ≤ 24 low density
   (p50 1.7 s / p90 4.3 s) or k = 5 at n = 8; expect DNF past that; avoid Steiner-like
   pair-coverage substrates entirely (STS(13) ≈ 160 s, STS(15) rigid > 900 s). For N knowledge
   bases the per-item `w*_c` cost, not the pairwise Levenshtein, is the binding constraint.
7. **Ladder monotonicity (55/56 increasing, ρ = 0.385)** supports "distance grows with
   accumulated divergence", which is the ordering a consensus/outlier filter needs — but ρ = 0.385
   is weak, so it licenses ranking, not calibration.
8. **Infrastructure that transfers unchanged**: the S=27 / BCa / bidirectional-Holm stats harness
   (`T-M4b/stats/` format), the size-controlled corpus construction and its confound guard
   (`tests/integration/test_corpus_confound_guard.py`), and the naive `degree_seq_l1` / `size_l1`
   baselines — the last of which is mandatory, since it alone beat 5/7 representations on the
   previous corpus.

Facts that must **not** be reused as favourable: A2/A3 task wins (IsalHG loses on the FINAL
corpus), A4 path recovery (loses to NetLSD/HPD), the pool-based decodability score (vacuous),
and any Stratum A number (superseded).

---

## F. Open questions I could not resolve from the files

1. **The k=7 / k=10 infeasibility evidence** (D.4). Was the 8-hour envelope run's output ever
   synced? Only `T-M7h/stratum_b/per_block/*.json` exists here and it records `not_runnable`.
2. **Where the ledger README's S7 headline should now point.** It still quotes
   `superseded/T-M7d_stratum_a/stats/stratum_a_stats.json`; whether that is a deliberate historical
   note or stale text is not stated in either the README or `RESULTS_MANIFEST.md`.
3. **HyperCOT was never run on the FINAL corpus** (absent from all three `stratum_c_*_stats.json`;
   gated out at N = 72 > 20). Its only numbers are on superseded corpora, so the capability
   matrix's HyperCOT column has no FINAL backing.
4. **G3 OFAT geometry response**: `RESULTS_MANIFEST.md` points to repo `artifacts/` plus
   `superseded/T-M7f/`; I did not locate a consolidated G3 summary file on the drive.
5. **Stratum B holds no A2/A3 keys** — only geometry. Whether task metrics were intended there
   and dropped, or never scoped, is not recorded in the files I read.
6. **`d_I^⊥` vs `d_I^Σ`** (label-free vs label-prefixed fingerprint) are used in different
   exhibits (synthetic vs HIC). No file gives a conversion or comparison; T-M8a explicitly
   declined to state one. For labelled knowledge bases this distinction will matter.
7. **`misc/HGED/results/table2_*`** (exact vs clamp10 solver fidelity, n=20 vs n=1000) was listed
   but not opened; if the new article needs an HGED oracle at larger n, that is where the
   accuracy/cost trade-off was measured.
