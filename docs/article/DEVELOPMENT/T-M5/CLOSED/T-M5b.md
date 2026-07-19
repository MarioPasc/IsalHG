# T-M5b — MDS (flagship application; HGED-FREE)
**Declared:** 2026-07-08 13:40 CEST (split from T-M5)
**Status:** DONE
**Depends on:** T-M1b, T-M3a–d, T-M4 (+ T-M4' for the real anchor)
**Context to read first:**
- `docs/article/empirical/applications.md` §A1 — method + CV dimension selection
- `docs/article/CODE_DESIGN.md` §9 — boundary (classical-MDS solve is a `src` primitive; CV/SMACOF/figures in experiments)
- `.claude/rules/coding_rules.md` — always
**Description:** Classical + SMACOF MDS on `D_I` and each competitor
(incl. NetLSD, full member since D-ART2; HyperCOT where feasible, limit
stated); CV dimension selection (primary), Mardia ratios, negative-eigenvalue
floor; stress; PSD report; Shepard diagram. The runner also emits the
**per-corpus geometry table** (`ν`, PSD, `D̂`, stress@`D̂`, concentration,
hubness — spec from T-M5f). Runs on the planted corpus and — if T-DQ3' is
green — a larger real HIC corpus. **No HGED.**
**Acceptance:** reproduces `applications.md` §A1 criteria; `D̂` reported per
representation; the geometry table produced per corpus; figures render.
**Out of scope here:** clustering/kNN/path (M5c–e); new `src/` code.

---

## Geometry table spec (from T-M5f, 2026-07-19)

The MDS runner emits one row per `(corpus, representation)`. Column schema:

| Column | Source primitive | Notes |
|---|---|---|
| `corpus` | — | e.g. `"planted_k3_n8"` |
| `representation` | — | e.g. `"IsalHG"`, `"WL"`, `"NetLSD"` |
| `n_points` | — | number of hypergraphs in corpus |
| `psd` | `embedding.is_psd(eigenvalues)` | bool; False = non-Euclidean |
| `nu` | `embedding.neg_eigenvalue_mass(eigenvalues)` | ν ∈ [0,1); 0 means Euclidean |
| `d_hat` | CV-MDS loop (experiments) | `D̂` minimising held-out reconstruction error |
| `stress_at_d_hat` | `embedding.kruskal_stress_1(D, D_embedded_at_d_hat)` | Kruskal S₁ at matched `D̂` |
| `diameter` | `geometry.concentration_stats(D)["diameter"]` | max pairwise distance |
| `median` | `geometry.concentration_stats(D)["median"]` | median pairwise distance |
| `diameter_to_median` | `geometry.concentration_stats(D)["diameter_to_median"]` | spread ratio |
| `iqr` | `geometry.concentration_stats(D)["iqr"]` | 75th − 25th pairwise percentile |
| `hubness_skewness` | `geometry.hubness_skewness(D, k=10)` | skewness of N_10; k=10 matches Radovanović et al. 2010 default |

`eigenvalues` are the descending array returned by `embedding.classical_mds(D)`.
`D_embedded_at_d_hat` is computed by `embedding.embed_classical(D, n_dims=d_hat)` then
pairwise L2 distance. All primitives are in `src/isalhg/metric_space/metrics/`.

---

## Closing note (2026-07-19)

**Implementation.** New files:
- `experiments/article/analysis/mds.py` (~990 lines): `cv_dimension_selection`,
  `mardia_ratios`, `negative_eigenvalue_floor`, `geometry_table_row`,
  `compute_and_cache_d_matrix`, `run_mds_pipeline`, figure functions,
  `pairwise_l2`, `smacof_stress_at_dim`, `main()` CLI.
- `experiments/article/configs/mds_planted.yaml`: two cells (planted_main N=60,
  planted_small N=20); documents the runner-bug workaround (T-M5i).
- `tests/unit/analysis/__init__.py` (empty init).
- `tests/unit/analysis/test_mds_cv.py`: 11 unit tests covering
  `cv_dimension_selection`, `mardia_ratios`, `pairwise_l2`, `geometry_table_row`.

**Key decision — CV parsimony rule.** For near-Euclidean distance matrices, all
CV errors above the true dimension are machine-epsilon noise; `argmin` picks an
arbitrary index. Fix: parsimony rule — choose the smallest `d` within
`max(1e-8, range_err * 1e-3)` of the global minimum, where
`range_err = cv_errors[0] - min_err`. Test `test_cv_dimension_selection_2d_euclidean`
was observed to fail (d_hat=5) before the fix and passes after (d_hat=2, CV error
at d=2 ≈ 1.4e-15 < 1e-6).

**Runner bug (→ T-M5i).** `runner._build_dataset` calls `get_dataset(name, **params)`;
the registry signature is `get_dataset(name, params: dict)`. Workaround: `mds.py`
computes D matrices directly with the identical cache layout. T-M5c/d/e load
precomputed `D.npy` caches and are not immediately blocked.

**Wall-clock probe (N=60, n=10, seed=42):**
- corpus gen: 0.09s; isalhg_levenshtein: 0.04s; hypergraph_wl_l1: 0.01s;
  netlsd_l2: 0.06s; hpd_jsd: 0.10s; nauty_levi_edit: 0.00s
- planted_small (N=20, n=6): hypercot: 0.72s; total < 1s all representations

**Geometry table — planted_main (N=60, seed=42):**

```
Repr             N   PSD      ν   D̂     S@D̂     diam      med    D/M      IQR     hub
IsalHG          60     F  0.123   10   0.1336    24.00    16.00   1.50     4.00   0.231
WL-L1           60     T  0.000   10   0.6432    22.00    20.00   1.10     0.00   1.777
NetLSD          60     T  0.000    5   0.0000     0.49     0.13   3.63     0.15  -0.551
HPD-JSD         60     T  0.000   10   0.1696     0.84     0.59   1.41     0.13   0.490
NautyEdit       60     F  0.029   10   0.2423    64.00    39.00   1.64     8.00  -0.215
```

**Geometry table — planted_small (N=20, seed=42):**

```
Repr             N   PSD      ν   D̂     S@D̂     diam      med    D/M      IQR     hub
IsalHG          20     F  0.102    7   0.0700    12.00     6.00   2.00     3.00   0.028
HyperCOT        20     F  0.234    3   0.2178     8.24     3.32   2.48     1.99   0.093
```

**Figures** rendered to `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/T-M5b/figures/`:
`mds_scatter_*.pdf`, `shepard_*.pdf`, `stress_vs_dim_*.pdf`, `mds_combined.pdf`
per corpus. Not committed (binary outputs).

**D.npy caches** at:
`/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/T-M5b/d_matrix/planted_families/{planted_main,planted_small}/seed42/{dist}/D.npy`.
Not committed (experiment outputs). T-M5c/d/e read these directly.

**Test suite (isalhg-T-M5b env, 2026-07-19):**

```
pytest tests/ -q -m unit
851 passed, 6 skipped, 187 deselected, 1 warning in 117.35s

ruff check src/ tests/
Found 3 errors.  ← all pre-existing (ANN001 isalhg_backend, SIM108 instruction_view, E731 test_registry)

mypy src/isalhg/
Found 21 errors in 7 files  ← all pre-existing
```

Baselines matched: ruff 3 / mypy 21.
