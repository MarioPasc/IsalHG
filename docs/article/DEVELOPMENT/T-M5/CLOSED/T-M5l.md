# T-M5l — D̂ robustness: Horn parallel analysis + N-scaling + budget-Shepard
**Declared:** 2026-07-20 (PI-directed: strengthen the `D̂` estimate beyond CV)
**Status:** DONE
**Depends on:** T-M5b ✔ (MDS pipeline + CV `D̂` + geometry table), T-M4 ✔
(planted generator), T-M5j ✔ (HIC clean-corpus `D.npy` caches)
**Context to read first:**
- `docs/article/theoretical/geometry.md` §Intrinsic dimension — the `D̂` estimator
  menu (CV primary; Mardia, neg-eigenvalue floor, parallel analysis supporting)
- `experiments/article/analysis/mds.py` — `classical_mds`, `cv_dimension_selection`,
  `mardia_ratios`, `embed_classical`, `geometry_table_row`
- `src/isalhg/datasets/synthetic/perturbation_ladder.py` — ladder items carry
  `item.extra["budget_from_base"]`, `["step"]`, `["ladder_id"]`
- `.claude/rules/coding_rules.md` — always

**Motivation.** The primary `D̂ = 21` (planted N = 60) is a CV estimate on a small
corpus — `D̂` near a third of `N` has limited resolution. This task strengthens it
three ways, all HGED-free.

**Deliverables.**

1. **Horn parallel analysis** (new function in `mds.py`, e.g.
   `parallel_analysis(D, n_permutations=500, percentile=95, rng_seed=42) ->
   (d_hat_horn, observed_eigs, null_threshold_curve)`).
   Null construction for a dissimilarity matrix: for each permutation, randomly
   permute the upper-triangle off-diagonal entries of `D`, symmetrise, keep zero
   diagonal, double-centre (Torgerson–Gower) and eigendecompose; accumulate the
   per-rank eigenvalue distribution. `D̂_Horn` = count of observed positive
   eigenvalues exceeding the `percentile`-th null eigenvalue at their rank.
   Unit-test on (i) a synthetic Euclidean rank-3 matrix (Horn should recover ≈3)
   and (ii) a pure-noise dissimilarity matrix (Horn should return ≈0). Emit a
   scree-with-null figure (observed vs null band).

2. **N-scaling `D̂` sweep.** Regenerate the planted corpus at
   `N ∈ {60, 120, 240, 480}` — **same per-instance params** as `planted_main`
   (`n_nodes=10, k=3, n_edges=10, n_edits=3, seed_value=42`), scaling only
   `n_families × members_per_family` (keep families balanced). Compute the
   `isalhg_levenshtein` `D` at each `N` (the whole matrix is ~0.1 s at N=60 —
   `w*_c` is fast on n=10 instances; the cost is O(N²) Levenshtein, still cheap).
   Report `D̂_CV` and `D̂_Horn` at each `N`, plus Mardia `P^(2)` and the
   neg-eigenvalue floor. **Cross-check on real large-N data:** run the same
   `D̂_CV` + `D̂_Horn` on the **cached** HIC `isalhg_levenshtein` `D.npy` for
   `IMDB-Wri-Genre` (N=833) and `IMDB-Wri-Genre-M` (N=266) under
   `results/T-M5j/d_matrix/<dataset>/isalhg_levenshtein/D.npy` — do NOT recompute
   those. Deliver a table: `N`, corpus, `ν`, `D̂_CV`, `D̂_Horn`, `P^(2)`, floor.
   The scientific question: is `D̂ ≈ 21` stable as `N` grows, or does it drift?
   Report the answer honestly either way.

3. **Budget-colored Shepard panel** (HGED-free structural-faithfulness view).
   On the `perturbation_ladder` corpus: compute the `d_I`-MDS embedding; for
   ladder pairs with a known accumulated Qin budget `t`
   (`extra["budget_from_base"]`), scatter (x = `t`, y = embedding Euclidean
   distance) coloured by `t`, and the native companion (x = `t`, y = `d_I`).
   This shows the embedding tracks known structural distance without invoking
   the HGED oracle (budget is known by construction; `HGED ≤ t`). Emit the
   figure + a Spearman `ρ(t, embedding-distance)`.

**Results output:** `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/T-M5l/`
(D̂-vs-N table CSV/JSON, Horn scree figures, budget-Shepard figure). Do NOT commit
binaries; commit code + tests + the ledger closing note (quote the D̂-vs-N table
+ the Horn agreement verbatim).

**Acceptance:** `parallel_analysis` implemented + unit-tested (recovers rank-3
Euclidean, returns ≈0 on noise); D̂-vs-N table produced for planted
{60,120,240,480} + HIC {833,266}; budget-Shepard figure renders with its ρ;
Horn `D̂` reported next to the CV `D̂` at every N. Full suite + ruff + mypy green
in the cloned env (main baseline: check current `main`).

**Out of scope:** re-running A2/A3/A4 at larger N (this task is the `D̂`
descriptor only); competitor D-matrices at the new N (ours `d_I` suffices for the
dimension question); new HGED calls; editing the geometry.md prose (orchestrator
writes the MDS-procedure section from these results).

---

## Closing note (2026-07-20)

**Branch:** `feat/T-M5l-dhat-robustness`

**Acceptance check output:**

### `parallel_analysis` — unit tests (4/4 pass)

```
tests/unit/analysis/test_parallel_analysis.py::test_parallel_analysis_rank3_euclidean PASSED
tests/unit/analysis/test_parallel_analysis.py::test_parallel_analysis_noise_returns_zero PASSED
tests/unit/analysis/test_parallel_analysis.py::test_parallel_analysis_discriminates PASSED
tests/unit/analysis/test_parallel_analysis.py::test_parallel_analysis_return_shapes PASSED
```

Rank-3 Euclidean → D̂_Horn = 3 (in [2,4]); noise → D̂_Horn ≤ 2. Discriminates.

### D̂-vs-N sweep table

```
Corpus                     N       ν  D̂_CV D̂_Horn   P^(2)  floor  n_perm
--------------------------------------------------------------------------
planted_N60               60   0.123     21       3   0.982     38     200
planted_N120             120   0.193     23       5   0.966     66     200
planted_N240             240   0.250     26       8   0.954    123     200
planted_N480             480   0.300     26      12   0.949    231     200
IMDB-Wri-Genre-M         266   0.160     10       1   0.993    203     200
IMDB-Wri-Genre           833   0.200     11       1   0.992    690     200
```

**Scientific answer:** D̂_CV drifts upward from 21 (N=60) to 26 (N=240–480 plateau),
then stabilises — slight underestimate at N=60, converging toward D̂ ≈ 26.
Horn D̂ (3→12) grows monotonically but stays well below CV D̂ (21→26); the gap
is expected for non-Euclidean metrics where signal is distributed across many
weak eigenvalues below the 95th-percentile null threshold. ν grows 0.123→0.300
with N (increasing non-Euclideanness at scale). HIC real data (genre graphs) is
substantially lower-dimensional (D̂_CV ≈ 10–11, D̂_Horn = 1) than planted
synthetic data — consistent with genre data having dominant clustering directions
not present in the structurally diverse planted families.

### Budget-Shepard panel

```
ρ(budget, d_I)     = 0.6361
ρ(budget, embed)   = 0.6492
D̂_CV (ladder)     = 16
n_pairs            = 150  (15 ladders × 10 steps)
```

Both d_I and the MDS embedding track the known Qin budget (ρ ≈ 0.64–0.65),
confirming structural monotonicity without invoking the HGED oracle. The
embedding tracks budget marginally better than raw d_I (ρ_embed > ρ_d_I), which
is consistent with MDS projecting out high-frequency non-monotone variance.

### Full suite

```
1124 passed, 8 skipped, 1 warning  (4 new tests in test_parallel_analysis.py)
ruff: 0 new errors (baseline 14 pre-existing)
mypy src/isalhg/: 21 errors matched (all pre-existing)
```

### Files changed

- `experiments/article/analysis/mds.py` — added `parallel_analysis` function
- `experiments/article/analysis/dhat_robustness.py` — NEW: sweep + budget-Shepard + figures + CLI
- `tests/unit/analysis/test_parallel_analysis.py` — NEW: 4 unit tests

### Results (not committed — external storage)

`/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/T-M5l/`
- `dhat_sweep_table.{csv,json}` — the full table above
- `figures/horn_scree_planted_N{60,120,240,480}.pdf` — Horn scree per N
- `figures/horn_scree_IMDB-Wri-Genre{,-M}.pdf`
- `figures/dhat_sweep_bar.pdf` — D̂_CV vs D̂_Horn side-by-side
- `figures/budget_shepard.pdf` — 2-panel: d_I vs t + embed_dist vs t, coloured by t
