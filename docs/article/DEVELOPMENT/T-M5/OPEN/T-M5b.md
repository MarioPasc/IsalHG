# T-M5b — MDS (flagship application; HGED-FREE)
**Declared:** 2026-07-08 13:40 CEST (split from T-M5)
**Status:** OPEN
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
