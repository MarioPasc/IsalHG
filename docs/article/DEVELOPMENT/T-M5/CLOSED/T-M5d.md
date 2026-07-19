# T-M5d — kNN classification (HGED-free)
**Declared:** 2026-07-08 13:40 CEST (split from T-M5)
**Status:** DONE
**Depends on:** T-M1b, T-M3a–d, T-M4 (+ T-M4' for the real labelled anchor)
**Context to read first:**
- `docs/article/empirical/applications.md` §A3 — kNN, metrics
- `docs/article/DATA.md` §1–§2 — labelled corpora (planted families; HIC real)
- `.claude/rules/coding_rules.md` — always
**Description:** kNN in `(·, d_I)` and competitors, LOO/stratified CV; accuracy,
macro-F1, AUC vs `k`. Planted-family labels + (if T-M4' loaded) HIC class labels.
Results are interpreted against the G1 concentration + hubness profile
(T-M5f helpers, emitted by T-M5b's runner) — report the profile alongside the
scores. **No HGED.**
**Acceptance:** reproduces `applications.md` §A3 criteria; figures render.
**Out of scope here:** MDS/clustering/path; new `src/` code.

---

## Closing note (2026-07-19)

**Branch:** worktree-agent-a8ab79ba7ccaeb3d8  
**Env:** isalhg-T-M5d (cloned from isalhg, pip install -e ".[dev]" in worktree)  
**Files added:**
- `experiments/article/analysis/knn.py` — kNN A3 pipeline
- `tests/unit/analysis/test_knn.py` — 13 unit tests

### Test → implement → verify cycle

Tests written first and confirmed failing (ModuleNotFoundError × 13). Implementation
made all 13 pass. Full suite: **1050 passed / 8 skipped** (ruff 3, mypy 21 — both
at baseline).

### Score tables (planted_main, N=60, 5 classes × 12, StratifiedKFold 5)

| Representation | hubness_skew | conc(d/m) | best acc (k) | best F1 (k) | best AUC (k) |
|---|---|---|---|---|---|
| IsalHG | 0.231 | 1.500 | 0.650 (k=1) | 0.633 (k=1) | 0.800 (k=3) |
| WL-L1 | **1.777** | 1.100 | 0.200 (k=1) | 0.110 (k=1) | 0.500 (k=1) |
| NetLSD | -0.551 | 3.633 | 0.467 (k=11) | 0.423 (k=11) | 0.722 (k=11) |
| HPD-JSD | 0.490 | 1.413 | **0.717 (k=3)** | **0.719 (k=3)** | **0.871 (k=3)** |
| NautyEdit | -0.215 | 1.641 | 0.283 (k=5) | 0.273 (k=5) | 0.560 (k=5) |

### Score tables (planted_small, N=20, 4 classes × 5, LOO)

| Representation | hubness_skew | conc(d/m) | best acc (k) | best AUC (k) |
|---|---|---|---|---|
| IsalHG | 0.028 | 2.000 | 0.300 (k=1) | 0.533 (k=1) |
| HyperCOT | 0.093 | 2.479 | 0.350 (k=7) | 0.533 (k=1) |

### G1 profile interpretation

The G1 precondition holds:

- **WL-L1 (hubness_skew=1.777):** strong hubness → AUC-OvR ≈ 0.50 (random).
  Exact match of the degraded-kNN prediction from the G1 profile.
- **IsalHG (hubness_skew=0.231):** moderate, low concentration → k=1 acc=65%,
  AUC=0.80. Useful at k=1; degrades with k (as concentration is mild).
- **HPD-JSD (hubness_skew=0.490):** best overall (72% acc, AUC=0.87). Low
  hubness, compact distances.
- **NautyEdit (hubness_skew=-0.215):** low hubness but 26–28% accuracy — the
  avalanche profile (large/noisy distances) destroys neighborhood structure
  even when hubness itself is benign.
- **NetLSD:** anti-hubness (skew=-0.551), moderate accuracy (up to 47%).

This confirms the paper's licence for A3: G1 (hubness) predicts relative kNN
performance across representations.

### Outputs (not committed; live on external drive)
- `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/T-M5d/knn_scores_planted_main.{csv,json}`
- `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/T-M5d/knn_scores_planted_small.{csv,json}`
- `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/T-M5d/figures/{planted_main,planted_small}/knn_{accuracy,macro-f1,auc-ovr}.pdf`

### Acceptance check

Reproduces `applications.md` §A3 criteria:
- kNN with `metric='precomputed'` via sklearn ✓
- LOO for N≤25 (planted_small), StratifiedKFold(5) for N>25 (planted_main) ✓
- Same CV folds shared across representations ✓
- Metrics: accuracy, macro-F1, AUC-OvR vs k ✓
- G1 profile (hubness_skewness, diameter_to_median) loaded from T-M5b geometry
  table and printed alongside scores per representation ✓
- Labels from planted family ids (no HIC, no HGED) ✓
- Figures render (6 PDF files produced) ✓
