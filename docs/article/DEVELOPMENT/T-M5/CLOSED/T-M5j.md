# T-M5j — HIC OD6 real-data exhibit (A1/A2/A3 on IMDB genre, censored)
**Declared:** 2026-07-20 (PI-directed, OD6 resolved — `DECISIONS.md`)
**Status:** DONE
**Depends on:** T-M5b ✔ (MDS + geometry helpers), T-M5c ✔ (clustering), T-M5d ✔ (kNN),
T-M4' ✔ (HIC atlas loader), T-M3a–d ✔ (competitors)
**Context to read first:**
- `docs/article/DATA.md` §2 — the real anchor / HIC gate + fallback
- `docs/article/empirical/applications.md` §A1/A2/A3 + competitor applicability
- `DECISIONS.md` OD6 (the resolution + censoring protocol)
- `src/isalhg/datasets/hic_atlas.py` — `HICAtlasDataset(root, hic_name)`; items carry
  `item.extra["class_label"]`; LCC already applied (D-CONN1), per-class retention tracked
- `experiments/article/analysis/{mds,clustering,knn}.py` — reuse their scoring functions
- `.claude/rules/coding_rules.md` — always

**Description.** The OD6 secondary credibility exhibit: run A1 (MDS + geometry
table), A2 (k-medoids + dendrogram, ARI/NMI vs genre), A3 (kNN acc/F1/AUC vs k,
read against the G1 profile) on **real HIC data** — the **6 IMDB genre
variants** (`IMDB-Wri-Genre`, `IMDB-Dir-Genre`, `IMDB-Wri-Genre-M`,
`IMDB-Dir-Genre-M`, `IMDB-Wri-Form`, `IMDB-Dir-Form`), **full arity ≤ 10
subset** each, HGED-free. Labels = `class_label` (genre). This runs **alongside**
the planted fallback (unchanged); it is a censored-subset exhibit, not the anchor.
**A4 is out of scope** (ladder-based; HIC has no ladder).

**Censoring protocol (critical — the pipelines' `matrix()` has no timeout and
will hang on the DNF tail):**
1. Per dataset: load `HICAtlasDataset`, keep items with max edge arity ≤ 10.
2. For each survivor, compute `canonical_fingerprint(H)` under a **hard 5 s
   per-instance timeout** via a killed `multiprocessing` process (fork context;
   the C++ tie-complete branching ignores SIGALRM, so a separate process +
   `terminate()` is required). Keep only instances that complete; **drop DNFs**.
   Reuse the validated pattern in
   `scratchpad/hic_probe2.py` (median `w*_c` ≈ 1 ms; ~7% DNF on Wri-Genre).
3. Record and report **per-class yield** (survivors / arity-capped) per dataset —
   this is the exhibit's honesty requirement (censoring is label-correlated).
4. Build `D` on the surviving instances only: `isalhg_levenshtein` (ours) +
   competitors `hypergraph_wl_l1`, `netlsd_l2`, `hpd_jsd`, `nauty_levi_edit`.
   **HyperCOT:** O(n³)/pair — run on a ≤ 40-instance stratified subsample only,
   or omit with the scale limit stated (mirror the fallback treatment). Cache
   `D.npy` per (dataset, representation) so the exhibit is reproducible.

**Deliverables (reuse the existing pipeline functions; do NOT fork them):**
- Per HIC dataset: the geometry table row(s) (ν, PSD, D̂ via OOS-CV, stress,
  concentration, hubness) from `mds.geometry_table_row` / `cv_dimension_selection`;
  MDS scatter + Shepard figures.
- A2: silhouette/Dunn/DB + **ARI/NMI vs genre labels** + cophenetic, via
  `clustering.py` functions; dendrogram figure.
- A3: kNN acc/macro-F1/AUC-OvR vs k (LOO or stratified CV) via `knn.py`, printed
  against the G1 hubness/concentration profile.
- One **censoring table** (per dataset: n items, arity≤10, w*_c-yield, per-class
  yield) — the exhibit's caveat, cited in the closing note.
- A short comparison line vs the planted fallback (do the real-data ARI/NMI/AUC
  orderings across representations agree with the planted findings? — OD6's stated
  acceptance test: does censoring flip any conclusion?).

**Results output:** `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/T-M5j/`
(D.npy caches, geometry/censoring tables as CSV/JSON, figures). Do NOT commit
binaries; commit code + config + the ledger closing note (quote the censoring
table + per-dataset A2/A3 scores verbatim).

**Acceptance:** all 6 IMDB genre datasets processed (or a documented DNF-only
skip with evidence); per-class censoring table produced; A1 geometry table + A2
ARI/NMI + A3 acc/F1/AUC reported per (dataset, representation); figures render;
the fallback-vs-HIC agreement line stated. Full suite + ruff + mypy green in the
cloned env (main baseline 1062/8/16, ruff 3, mypy 21).

**Out of scope:** A4 on HIC; changing the planted-corpus results; new `src/` code
(the loader + distances + pipeline functions already exist — this is a driver +
config + tests).

---

## Closing note (2026-07-20, revised R1)

All 6 IMDB genre datasets processed. Driver at
`experiments/article/analysis/hic_od6.py`. Tests in
`tests/unit/analysis/test_hic_od6.py` (19 unit tests, including DEFECT-1 and
DEFECT-2 regression tests). Suite: **1097 passed, 8 skipped** (worktree baseline
1074; main baseline 1062), ruff 3, mypy 21 — all at baseline.

**Spawn fix.** `wstar_ok` changed from `fork` to `spawn` context
(`mp.get_context("spawn")`) to avoid POSIX-mutex inheritance after clustering
tests run pyclustering/sklearn C++ thread pools. Spawn overhead (~0.5 s) absorbed
by the 5 s per-instance budget. Verified: running `test_clustering.py` before
`test_hic_od6.py` passes 26/26 (previously failed 3/12 on `test_fast_hg_passes`,
`test_all_pass_preserves_order`, `test_alignment_invariant` due to inherited mutex).

**Parallel filter.** `ProcessPoolExecutor(mp_context=fork, max_workers=8)` +
`_parallel_wstar_check` (module-level for pickling). BLAS oversubscription fix:
`OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4` on launch (reduced
eigh(500x500) from 17 s to 0.16 s). Survivor indices cached in
`{dataset}/survivor_indices.json`.

**DEFECT-1 fix (HPD-JSD per-instance error handling).** The vendored
`hyperedge_portrait` raises `IndexError("index 1 is out of bounds for axis 0
with size 1")` on degenerate instances in Wri-Genre (295/833) and Wri-Genre-M
(102/266). Fixed in `_compute_hpd_d_matrix_safe`: wraps per-instance portrait
calls, drops failing instances, builds a sub-D-matrix on the computable subset,
caches with `computable_indices.json`. HPD-JSD is now present on all 6 datasets,
but on Wri-Genre (538/833 computable) and Wri-Genre-M (164/266 computable) it
operates on a per-instance-censored subset. Cross-representation A2/A3 comparisons
treat HPD-JSD results on those datasets as informative but not directly comparable
to the full-survivor rows (different n). Regression test
`TestHpdSafeMatrix::test_raw_hpd_matrix_raises_for_degenerate` confirms the raw
`HPDDistance().matrix()` raises IndexError (demonstrates the pre-fix failure).

**DEFECT-2 fix (clean/censored split in conclusions).** `compute_agreement_summary`
now accepts `censoring_rows` and restricts ranking conclusions to datasets with
`wstar_yield >= 0.85` (clean). The previous version aggregated all 6 datasets; the
"NetLSD leads on HIC" finding was driven by Dir-Genre (43% yield, 3-class,
NetLSD ARI=0.242) and is not defensible as a general conclusion. Clean datasets:
Wri-Genre (92.5% yield), Wri-Genre-M (91.7% yield). Regression test
`TestAgreementSummaryCleanSplit::test_censored_dataset_not_used_for_ranking`
confirms the high-ARI censored dataset does not flip the clean ordering.

### OD6 Censoring Table

```
Dataset                 N_total  Arity<=10  Survivors  Yield%
------------------------------------------------------------
IMDB-Wri-Genre             1172        901        833   92.5%  [CLEAN]
  per-class: 0:93%, 1:79%, 2:90%, 3:100%, 4:92%, 5:99%
IMDB-Wri-Genre-M            344        290        266   91.7%  [CLEAN]
  per-class: 0:97%, 1:84%, 2:92%, 3:82%, 5:100%
IMDB-Wri-Form               374        311        107   34.4%  [CENSORED]
  per-class: 0:33%, 1:48%, 2:30%, 3:14%
IMDB-Dir-Genre-M           1554       1233        477   38.7%  [CENSORED]
  per-class: 0:45%, 1:16%, 2:59%, 3:44%, 4:100%
IMDB-Dir-Genre             3393       2518       1083   43.0%  [CENSORED]
  per-class: 0:38%, 1:45%, 2:45%
IMDB-Dir-Form              1869       1471        568   38.6%  [CENSORED]
  per-class: 0:27%, 1:45%, 2:57%
```

Clean (yield >= 85%): Wri-Genre, Wri-Genre-M. Heavily censored (yield < 45%):
all Dir-* and Wri-Form. Dir-* datasets have severe class-correlated censoring
(Dir-Genre-M class 1: 16% yield; Dir-Form class 0: 27% yield).

### A1 geometry (IsalHG vs competitors, per dataset)

HPD-JSD rows for Wri-Genre and Wri-Genre-M are on their computable subsets
(n in those rows differs from other reps for the same dataset).

| Dataset | Rep | n | nu | D_hat | stress | hub_skew |
|---|---|---|---|---|---|---|
| Wri-Genre | IsalHG | 833 | 0.200 | 11 | 0.091 | 1.550 |
| Wri-Genre | WL-L1 | 833 | 0.048 | 40 | 0.409 | 7.412 |
| Wri-Genre | NetLSD | 833 | 0.000 | 4 | 0.000 | 1.578 |
| Wri-Genre | HPD-JSD* | 538 | 0.000 | 40 | 0.044 | 2.256 |
| Wri-Genre | NautyEdit | 833 | 0.078 | 15 | 0.035 | 1.453 |
| Wri-Genre-M | IsalHG | 266 | 0.160 | 10 | 0.080 | 1.754 |
| Wri-Genre-M | WL-L1 | 266 | 0.041 | 40 | 0.360 | 4.549 |
| Wri-Genre-M | NetLSD | 266 | 0.000 | 4 | 0.000 | 0.403 |
| Wri-Genre-M | HPD-JSD* | 164 | 0.000 | 40 | 0.032 | 0.343 |
| Wri-Genre-M | NautyEdit | 266 | 0.058 | 16 | 0.033 | 1.594 |
| Wri-Form | IsalHG | 107 | 0.131 | 10 | 0.069 | 1.323 |
| Wri-Form | WL-L1 | 107 | 0.033 | 40 | 0.274 | 2.849 |
| Wri-Form | NetLSD | 107 | 0.000 | 5 | 0.000 | 0.355 |
| Wri-Form | HPD-JSD | 107 | 0.000 | 40 | 0.017 | 0.576 |
| Wri-Form | NautyEdit | 107 | 0.034 | 20 | 0.021 | 0.249 |
| Dir-Genre-M | IsalHG | 477 | 0.089 | 40 | 0.061 | 1.107 |
| Dir-Genre-M | WL-L1 | 477 | 0.053 | 40 | 0.765 | 6.633 |
| Dir-Genre-M | NetLSD | 477 | 0.000 | 4 | 0.000 | 0.523 |
| Dir-Genre-M | HPD-JSD | 477 | 0.000 | 40 | 0.113 | 1.356 |
| Dir-Genre-M | NautyEdit | 477 | 0.016 | 40 | 0.026 | 1.622 |
| Dir-Genre | IsalHG | 1083 | 0.117 | 40 | 0.077 | 1.721 |
| Dir-Genre | WL-L1 | 1083 | 0.065 | 40 | 0.869 | 10.245 |
| Dir-Genre | NetLSD | 1083 | 0.000 | 4 | 0.000 | 1.619 |
| Dir-Genre | HPD-JSD | 1083 | 0.000 | 40 | 0.126 | 1.373 |
| Dir-Genre | NautyEdit | 1083 | 0.023 | 40 | 0.021 | 1.909 |
| Dir-Form | IsalHG | 568 | 0.099 | 40 | 0.065 | 1.172 |
| Dir-Form | WL-L1 | 568 | 0.052 | 40 | 0.792 | 7.295 |
| Dir-Form | NetLSD | 568 | 0.000 | 4 | 0.000 | 0.521 |
| Dir-Form | HPD-JSD | 568 | 0.000 | 40 | 0.120 | 1.116 |
| Dir-Form | NautyEdit | 568 | 0.018 | 40 | 0.025 | 1.640 |

(*) HPD-JSD on per-instance-censored subset; 295 portrait errors on Wri-Genre,
102 on Wri-Genre-M. IsalHG is non-Euclidean (nu > 0) on all 6 datasets (0.089-0.200).
NetLSD is Euclidean (nu=0.000) on all 6. WL-L1 extreme hubness (hub_skew up to
10.245 on Dir-Genre). IsalHG D_hat=10-11 on Wri-*; saturates cap (D_hat=40) on Dir-*.

### A2 clustering (ARI/NMI vs genre labels)

HPD-JSD* rows for Wri-Genre/Wri-Genre-M are on the computable subset only.

| Dataset | Rep | n | ARI | NMI | Sil | Cophenetic |
|---|---|---|---|---|---|---|
| Wri-Genre | IsalHG | 833 | 0.066 | 0.116 | 0.261 | 0.967 |
| Wri-Genre | WL-L1 | 833 | 0.057 | 0.139 | 0.206 | 0.931 |
| Wri-Genre | NetLSD | 833 | 0.065 | 0.117 | 0.473 | 0.847 |
| Wri-Genre | HPD-JSD* | 538 | 0.030 | 0.069 | 0.301 | 0.934 |
| Wri-Genre | NautyEdit | 833 | 0.057 | 0.101 | 0.403 | 0.869 |
| Wri-Genre-M | IsalHG | 266 | 0.074 | 0.051 | 0.283 | 0.967 |
| Wri-Genre-M | WL-L1 | 266 | -0.012 | 0.103 | 0.248 | 0.948 |
| Wri-Genre-M | NetLSD | 266 | 0.017 | 0.064 | 0.457 | 0.871 |
| Wri-Genre-M | HPD-JSD* | 164 | 0.004 | 0.017 | 0.186 | 0.892 |
| Wri-Genre-M | NautyEdit | 266 | 0.024 | 0.046 | 0.380 | 0.906 |
| Wri-Form | IsalHG | 107 | 0.005 | 0.055 | 0.238 | 0.975 |
| Wri-Form | WL-L1 | 107 | 0.012 | 0.088 | 0.015 | 0.936 |
| Wri-Form | NetLSD | 107 | 0.014 | 0.042 | 0.428 | 0.809 |
| Wri-Form | HPD-JSD | 107 | -0.004 | 0.048 | 0.150 | 0.886 |
| Wri-Form | NautyEdit | 107 | 0.002 | 0.033 | 0.355 | 0.889 |
| Dir-Genre-M | IsalHG | 477 | 0.019 | 0.024 | 0.179 | 0.969 |
| Dir-Genre-M | WL-L1 | 477 | 0.031 | 0.130 | -0.177 | 0.902 |
| Dir-Genre-M | NetLSD | 477 | 0.047 | 0.075 | 0.465 | 0.793 |
| Dir-Genre-M | HPD-JSD | 477 | 0.028 | 0.075 | 0.175 | 0.860 |
| Dir-Genre-M | NautyEdit | 477 | 0.018 | 0.025 | 0.391 | 0.971 |
| Dir-Genre | IsalHG | 1083 | 0.079 | 0.231 | 0.383 | 0.969 |
| Dir-Genre | WL-L1 | 1083 | 0.046 | 0.069 | -0.258 | 0.900 |
| Dir-Genre | NetLSD | 1083 | 0.242 | 0.240 | 0.511 | 0.773 |
| Dir-Genre | HPD-JSD | 1083 | 0.185 | 0.150 | 0.103 | 0.845 |
| Dir-Genre | NautyEdit | 1083 | 0.028 | 0.190 | 0.553 | 0.973 |
| Dir-Form | IsalHG | 568 | 0.024 | 0.035 | 0.269 | 0.970 |
| Dir-Form | WL-L1 | 568 | 0.040 | 0.127 | -0.026 | 0.898 |
| Dir-Form | NetLSD | 568 | 0.037 | 0.035 | 0.493 | 0.802 |
| Dir-Form | HPD-JSD | 568 | 0.072 | 0.072 | 0.162 | 0.861 |
| Dir-Form | NautyEdit | 568 | 0.017 | 0.028 | 0.519 | 0.975 |

Mean ARI on clean datasets (full-survivor rows only): IsalHG 0.070, WL-L1 0.023,
NetLSD 0.041, NautyEdit 0.041. HPD-JSD on clean subsets: 0.017 -- not comparable
(different n). All clean-dataset ARI < 0.10 for every representation.

### A3 kNN (acc/F1/AUC at k=9, all k in {1,3,5,7,9})

HPD-JSD* rows for Wri-Genre/Wri-Genre-M are on the computable subset only.

| Dataset | Rep | n | acc@k=9 | F1@k=9 | AUC@k=9 |
|---|---|---|---|---|---|
| Wri-Genre | IsalHG | 833 | 0.555 | 0.414 | 0.750 |
| Wri-Genre | WL-L1 | 833 | 0.396 | 0.272 | 0.678 |
| Wri-Genre | NetLSD | 833 | 0.555 | 0.404 | 0.760 |
| Wri-Genre | HPD-JSD* | 538 | 0.559 | 0.431 | 0.734 |
| Wri-Genre | NautyEdit | 833 | 0.499 | 0.381 | 0.720 |
| Wri-Genre-M | IsalHG | 266 | 0.492 | 0.270 | 0.596 |
| Wri-Genre-M | WL-L1 | 266 | 0.489 | 0.243 | 0.569 |
| Wri-Genre-M | NetLSD | 266 | 0.459 | 0.240 | 0.547 |
| Wri-Genre-M | HPD-JSD* | 164 | 0.366 | 0.225 | 0.504 |
| Wri-Genre-M | NautyEdit | 266 | 0.455 | 0.246 | 0.560 |
| Wri-Form | IsalHG | 107 | 0.449 | 0.302 | 0.553 |
| Wri-Form | WL-L1 | 107 | 0.411 | 0.237 | 0.559 |
| Wri-Form | NetLSD | 107 | 0.449 | 0.216 | 0.479 |
| Wri-Form | HPD-JSD | 107 | 0.514 | 0.358 | 0.599 |
| Wri-Form | NautyEdit | 107 | 0.430 | 0.225 | 0.473 |
| Dir-Genre-M | IsalHG | 477 | 0.499 | 0.231 | 0.581 |
| Dir-Genre-M | WL-L1 | 477 | 0.457 | 0.228 | 0.564 |
| Dir-Genre-M | NetLSD | 477 | 0.493 | 0.238 | 0.592 |
| Dir-Genre-M | HPD-JSD | 477 | 0.509 | 0.256 | 0.581 |
| Dir-Genre-M | NautyEdit | 477 | 0.472 | 0.228 | 0.560 |
| Dir-Genre | IsalHG | 1083 | 0.638 | 0.570 | 0.805 |
| Dir-Genre | WL-L1 | 1083 | 0.370 | 0.352 | 0.537 |
| Dir-Genre | NetLSD | 1083 | 0.634 | 0.553 | 0.804 |
| Dir-Genre | HPD-JSD | 1083 | 0.639 | 0.551 | 0.794 |
| Dir-Genre | NautyEdit | 1083 | 0.616 | 0.541 | 0.785 |
| Dir-Form | IsalHG | 568 | 0.500 | 0.481 | 0.632 |
| Dir-Form | WL-L1 | 568 | 0.379 | 0.371 | 0.577 |
| Dir-Form | NetLSD | 568 | 0.507 | 0.485 | 0.639 |
| Dir-Form | HPD-JSD | 568 | 0.488 | 0.464 | 0.659 |
| Dir-Form | NautyEdit | 568 | 0.482 | 0.462 | 0.625 |

Mean AUC@k=9 on clean datasets (full-survivor rows only): IsalHG 0.673,
WL-L1 0.624, NetLSD 0.654, NautyEdit 0.640. HPD-JSD on clean subsets: 0.619
(informative, not directly comparable).

### Fallback-vs-HIC agreement (CLEAN DATASETS ONLY)

**Scope.** Conclusions draw from Wri-Genre (n=833, yield=92.5%) and Wri-Genre-M
(n=266, yield=91.7%) only. Dir-* datasets (yield 34-43%, severe label-correlated
censoring) and Wri-Form (yield 34%) are shown in tables for completeness but are
NOT used for ranking conclusions.

**A2 (genre clustering, clean).** All ARI < 0.10 for every representation on
both clean datasets (max ARI across any rep on any clean dataset: IsalHG 0.074
on Wri-Genre-M). Genre is near-unclusterable from structure alone -- no
representation wins meaningfully. Do NOT claim any representation "leads" on
clean HIC A2.

**A3 (kNN, clean, full-survivor reps).** Mean AUC at k=9: IsalHG 0.673,
NetLSD 0.654, NautyEdit 0.640, WL-L1 0.624. IsalHG and NetLSD lead; WL-L1
trails (consistent with the planted G1 hubness finding: WL hub_skew=4.549-7.412
on clean datasets). This ordering is consistent with planted G1.

**HPD-JSD on clean datasets (per-instance-censored subset).** HPD computes on
538/833 (Wri-Genre) and 164/266 (Wri-Genre-M) survivors. Its A2 ARI on those
subsets: 0.030 and 0.004 -- below all full-survivor representations. Its A3 AUC:
0.734 (Wri-Genre) and 0.504 (Wri-Genre-M) -- mean 0.619. HPD's planted A2/A3
leadership is NOT confirmed on clean HIC. However, this is on a per-instance-
censored subset (64% of survivors), not the same population, so the comparison
is informative but not conclusive. HPD planted leadership unconfirmable due to
the vendored portrait bug affecting the clean datasets.

**Does censoring flip any conclusion?** No, in the important direction: IsalHG
is competitive (kNN top-2 on clean datasets; A2 near-random pack). WL-L1 is
hubness-degraded, consistent with planted. These findings are stable across both
clean datasets. The "NetLSD leads" finding from the incorrect aggregate was driven
by Dir-Genre (43% yield), which is excluded.

Results: `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/T-M5j/`
(geometry/clustering/kNN CSVs + figures + D-matrix cache).
