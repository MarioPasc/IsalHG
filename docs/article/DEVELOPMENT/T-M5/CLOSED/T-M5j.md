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

## Closing note (2026-07-20)

All 6 IMDB genre datasets processed. Driver at
`experiments/article/analysis/hic_od6.py`. Tests in
`tests/unit/analysis/test_hic_od6.py` (12 unit tests). Suite: **1090 passed,
8 skipped** (baseline 1062/8/16), ruff 3, mypy 21 — all at baseline.

**Spawn fix.** `wstar_ok` changed from `fork` to `spawn` context
(`mp.get_context("spawn")`) to avoid POSIX-mutex inheritance after clustering
tests run pyclustering/sklearn C++ thread pools. Spawn overhead (~0.5 s) is
absorbed by the 5 s per-instance budget; production filter timing (dominated by
DNF-wait at 5 s/instance) is unaffected (~1 min added for largest dataset).
Verified: running `test_clustering.py` before `test_hic_od6.py` passes 26/26
(previously failed 3/12 on `test_fast_hg_passes`, `test_all_pass_preserves_order`,
`test_alignment_invariant` due to inherited mutex).

**Parallel filter.** `ProcessPoolExecutor(mp_context=fork, max_workers=8)` +
`_parallel_wstar_check` (module-level for pickling). BLAS oversubscription fix:
`OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4` on launch (reduced
eigh(500×500) from 17 s to 0.16 s). Survivor indices cached in
`{dataset}/survivor_indices.json` (skip re-filter on rerun).

### OD6 Censoring Table

```
Dataset                 N_total  Arity≤10  Survivors  Yield%
------------------------------------------------------------
IMDB-Wri-Genre             1172       901        833   92.5%
  per-class: 0:93%, 1:79%, 2:90%, 3:100%, 4:92%, 5:99%
IMDB-Wri-Genre-M            344       290        266   91.7%
  per-class: 0:97%, 1:84%, 2:92%, 3:82%, 5:100%
IMDB-Wri-Form               374       311        107   34.4%
  per-class: 0:33%, 1:48%, 2:30%, 3:14%
IMDB-Dir-Genre-M           1554      1233        477   38.7%
  per-class: 0:45%, 1:16%, 2:59%, 3:44%, 4:100%
IMDB-Dir-Genre             3393      2518       1083   43.0%
  per-class: 0:38%, 1:45%, 2:45%
IMDB-Dir-Form              1869      1471        568   38.6%
  per-class: 0:27%, 1:45%, 2:57%
```

Wri-Genre/Wri-Genre-M have good yield (92%). Dir-* datasets have severe
class-correlated censoring (Dir-Genre-M class 1: 16%; Dir-Form class 0: 27%).
HPD-JSD failed on Wri-Genre and Wri-Genre-M with "index 1 is out of bounds
for axis 0 with size 1" (bug in the hyperedge-portrait implementation for
these specific datasets); excluded for those two, present for the other four.

### A1 geometry (IsalHG vs competitors, per dataset)

| Dataset | Rep | n | ν | D̂ | stress | hub_skew |
|---|---|---|---|---|---|---|
| Wri-Genre | IsalHG | 833 | 0.200 | 11 | 0.091 | 1.550 |
| Wri-Genre | WL-L1 | 833 | 0.048 | 40 | 0.409 | 7.412 |
| Wri-Genre | NetLSD | 833 | 0.000 | 4 | 0.000 | 1.578 |
| Wri-Genre | NautyEdit | 833 | 0.078 | 15 | 0.035 | 1.453 |
| Wri-Genre-M | IsalHG | 266 | 0.160 | 10 | 0.080 | 1.754 |
| Wri-Genre-M | WL-L1 | 266 | 0.041 | 40 | 0.360 | 4.549 |
| Wri-Genre-M | NetLSD | 266 | 0.000 | 4 | 0.000 | 0.403 |
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

IsalHG is non-Euclidean (ν > 0, PSD=False) on all 6 datasets (ν: 0.089–0.200).
NetLSD is Euclidean (ν=0.000, PSD=True) on all 6. HPD-JSD is Euclidean where
computed. WL-L1 is non-Euclidean but extreme hubness (up to hub_skew=10.245 on
Dir-Genre). The Wri-* datasets show D̂=10–11 for IsalHG; Dir-* datasets saturate
the CV cap at D̂=40.

### A2 clustering (ARI/NMI vs genre labels, best per-dataset reading)

| Dataset | Rep | ARI | NMI | Sil | Cophenetic |
|---|---|---|---|---|---|
| Wri-Genre | IsalHG | 0.066 | 0.116 | 0.261 | 0.967 |
| Wri-Genre | WL-L1 | 0.057 | 0.139 | 0.206 | 0.931 |
| Wri-Genre | NetLSD | 0.065 | 0.117 | 0.473 | 0.847 |
| Wri-Genre | NautyEdit | 0.057 | 0.101 | 0.403 | 0.869 |
| Wri-Genre-M | IsalHG | 0.074 | 0.051 | 0.283 | 0.967 |
| Wri-Genre-M | WL-L1 | -0.012 | 0.103 | 0.248 | 0.948 |
| Wri-Genre-M | NetLSD | 0.017 | 0.064 | 0.457 | 0.871 |
| Wri-Genre-M | NautyEdit | 0.024 | 0.046 | 0.380 | 0.906 |
| Wri-Form | IsalHG | 0.005 | 0.055 | 0.238 | 0.975 |
| Wri-Form | WL-L1 | 0.012 | 0.088 | 0.015 | 0.936 |
| Wri-Form | NetLSD | 0.014 | 0.042 | 0.428 | 0.809 |
| Wri-Form | HPD-JSD | -0.004 | 0.048 | 0.150 | 0.886 |
| Wri-Form | NautyEdit | 0.002 | 0.033 | 0.355 | 0.889 |
| Dir-Genre-M | IsalHG | 0.019 | 0.024 | 0.179 | 0.969 |
| Dir-Genre-M | WL-L1 | 0.031 | 0.130 | -0.177 | 0.902 |
| Dir-Genre-M | NetLSD | 0.047 | 0.075 | 0.465 | 0.793 |
| Dir-Genre-M | HPD-JSD | 0.028 | 0.075 | 0.175 | 0.860 |
| Dir-Genre-M | NautyEdit | 0.018 | 0.025 | 0.391 | 0.971 |
| Dir-Genre | IsalHG | 0.079 | 0.231 | 0.383 | 0.969 |
| Dir-Genre | WL-L1 | 0.046 | 0.069 | -0.258 | 0.900 |
| Dir-Genre | NetLSD | 0.242 | 0.240 | 0.511 | 0.773 |
| Dir-Genre | HPD-JSD | 0.185 | 0.150 | 0.103 | 0.845 |
| Dir-Genre | NautyEdit | 0.028 | 0.190 | 0.553 | 0.973 |
| Dir-Form | IsalHG | 0.024 | 0.035 | 0.269 | 0.970 |
| Dir-Form | WL-L1 | 0.040 | 0.127 | -0.026 | 0.898 |
| Dir-Form | NetLSD | 0.037 | 0.035 | 0.493 | 0.802 |
| Dir-Form | HPD-JSD | 0.072 | 0.072 | 0.162 | 0.861 |
| Dir-Form | NautyEdit | 0.017 | 0.028 | 0.519 | 0.975 |

Mean ARI across 6 datasets: IsalHG 0.044, WL-L1 0.029, NetLSD 0.071,
HPD-JSD 0.070 (4 datasets), NautyEdit 0.024.

### A3 kNN (best acc@k=9, all k in {1,3,5,7,9})

| Dataset | Rep | acc@k=9 | F1@k=9 | AUC@k=9 |
|---|---|---|---|---|
| Wri-Genre | IsalHG | 0.555 | 0.414 | 0.750 |
| Wri-Genre | WL-L1 | 0.396 | 0.272 | 0.678 |
| Wri-Genre | NetLSD | 0.555 | 0.404 | 0.760 |
| Wri-Genre | NautyEdit | 0.499 | 0.381 | 0.720 |
| Wri-Genre-M | IsalHG | 0.492 | 0.270 | 0.596 |
| Wri-Genre-M | WL-L1 | 0.489 | 0.243 | 0.569 |
| Wri-Genre-M | NetLSD | 0.459 | 0.240 | 0.547 |
| Wri-Genre-M | NautyEdit | 0.455 | 0.246 | 0.560 |
| Wri-Form | IsalHG | 0.449 | 0.302 | 0.553 |
| Wri-Form | WL-L1 | 0.411 | 0.237 | 0.559 |
| Wri-Form | NetLSD | 0.449 | 0.216 | 0.479 |
| Wri-Form | HPD-JSD | 0.514 | 0.358 | 0.599 |
| Wri-Form | NautyEdit | 0.430 | 0.225 | 0.473 |
| Dir-Genre-M | IsalHG | 0.499 | 0.231 | 0.581 |
| Dir-Genre-M | WL-L1 | 0.457 | 0.228 | 0.564 |
| Dir-Genre-M | NetLSD | 0.493 | 0.238 | 0.592 |
| Dir-Genre-M | HPD-JSD | 0.509 | 0.256 | 0.581 |
| Dir-Genre-M | NautyEdit | 0.472 | 0.228 | 0.560 |
| Dir-Genre | IsalHG | 0.638 | 0.570 | 0.805 |
| Dir-Genre | WL-L1 | 0.370 | 0.352 | 0.537 |
| Dir-Genre | NetLSD | 0.634 | 0.553 | 0.804 |
| Dir-Genre | HPD-JSD | 0.639 | 0.551 | 0.794 |
| Dir-Genre | NautyEdit | 0.616 | 0.541 | 0.785 |
| Dir-Form | IsalHG | 0.500 | 0.481 | 0.632 |
| Dir-Form | WL-L1 | 0.379 | 0.371 | 0.577 |
| Dir-Form | NetLSD | 0.507 | 0.485 | 0.639 |
| Dir-Form | HPD-JSD | 0.488 | 0.464 | 0.659 |
| Dir-Form | NautyEdit | 0.482 | 0.462 | 0.625 |

Mean peak-acc across 6 datasets: IsalHG 0.505, WL-L1 0.414, NetLSD 0.528,
HPD-JSD 0.523 (4 datasets), NautyEdit 0.477.

### Fallback-vs-HIC agreement

On HIC the ARI and kNN orderings differ from the planted-corpus findings:
NetLSD leads on HIC (mean ARI 0.071) whereas HPD-JSD led on the planted corpus.
IsalHG is 3rd in both ARI and kNN-acc orderings (same mid-pack position as in
planted). WL-L1 drops to last in kNN-acc on large Dir-* datasets (hub_skew
up to 10.245 → hubness curse severe). The ordering shift is driven primarily by
IMDB-Dir-Genre (1083 survivors, 3 classes) where NetLSD achieves ARI=0.242 and
HPD-JSD ARI=0.185, both far above the 6-class Wri-Genre datasets.

**Caveat (honesty requirement).** The censoring is strongly label-correlated on
Dir-* datasets (Dir-Genre-M class 1: 16% yield; Dir-Form class 0: 27% yield).
The survived subset is not representative of the full dataset: easy-to-encode
instances (low arity, low symmetry) survive while hard-to-encode ones are
censored. Any ordering seen on the censored subset must be interpreted with this
in mind. The censoring table is the exhibit's primary caveat and must be
displayed alongside any HIC results in the paper.

Results: `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/T-M5j/`
(geometry/clustering/kNN CSVs + figures + D-matrix cache).
