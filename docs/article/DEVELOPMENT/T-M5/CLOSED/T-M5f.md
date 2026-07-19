# T-M5f — Geometric characterization of `(w*_c, d_Lev)`: the static invariants
**Declared:** 2026-07-17 20:30 CEST · **extended** 2026-07-18 17:56 CEST (D-ART2)
**Status:** DONE
**Depends on:** T-M1b (`d_I`), T-M4 (`metric_space/metrics/` home); feeds T-M5b (MDS flagship) and T-M5d (kNN precondition)
**Delegation:** agent
**Why out of scope:** Surfaced in the 2026-07-17 way-forward analysis; promoted by D-ART2 to the article's characterization leg (characterize → exploit).
**Context to read first:**
- `docs/article/theoretical/geometry.md` — the six invariants + the no-orphan-geometry rule (the spec this task realizes; the two *dynamic* invariants are T-M5g's)
- `docs/article/PROPOSAL.md` §2 — the invariant→consumer table
- `docs/article/DEVELOPMENT/T-M5/OPEN/T-M5b.md` — the flagship MDS run that consumes this spec
- `docs/article/RELATED_WORK.md` §Geometry diagnostics — Radovanović et al. 2010 (hubness)
- `docs/article/CODE_DESIGN.md` §2 tree (`metrics/{embedding,geometry}.py`) — where the helpers land
- `.claude/rules/coding_rules.md` — always
**Note (2026-07-17):** the theory half is drafted as
`theoretical/geometry.md`; refine it only if the measurement forces it.
**Description:** Implement and spec the **static** geometric invariants. (a)
`metric_space/metrics/embedding.py`: classical-MDS solve (double-centre → eig),
eigenvalue spectrum, negative-eigenvalue mass `ν = Σλ⁻/Σ|λ|`, PSD flag,
stress-1, Shepard data, CV-reconstruction-error harness input (`D̂` selection
runs in experiments). (b) `metric_space/metrics/geometry.py`: concentration
stats (pairwise histogram summary, diameter/median ratio, length-difference
floor) and **hubness** (`k`-occurrence `N_k` skewness). (c) The **per-corpus
geometry table** spec consumed by T-M5b's runner: one row per (corpus,
representation) with `ν`, PSD, `D̂`, stress@`D̂`, concentration, hubness — the
paper's characterization table, also the competitor-geometry axis.
**Acceptance:** `theoretical/geometry.md` consistent with the measured
invariants (refined if the measurement surfaces gaps); helpers unit-tested
(pinned spectra on a small fixture; PSD vs non-PSD corpus flagged correctly;
hubness skewness against a hand-computed value); the geometry-table spec
recorded in T-M5b before its run.
**Out of scope here:** the dynamic profiles (sensitivity/ladder — T-M5g);
running MDS end-to-end (T-M5b owns the run); any HGED call; changes to `w*_c`
or the distance.

---

## Closing note (2026-07-19)

**Acceptance check passed.**

### What was implemented

(a) `src/isalhg/metric_space/metrics/embedding.py` — two new functions:
- `neg_eigenvalue_mass(eigenvalues, tol=1e-10) -> float`: ν = Σ_{λ<−tol}|λ| / Σ|λ|.
  Uses same tolerance as `is_psd` for consistency; returns 0.0 when total |λ| = 0.
- `shepard_data(D_original, D_embedded) -> (ndarray, ndarray)`: upper-triangle
  pairs for a Shepard diagram.

(b) `src/isalhg/metric_space/metrics/geometry.py` (new, 4 functions):
- `concentration_stats(D) -> dict`: diameter, median, q25, q75, iqr,
  diameter_to_median — all from upper-triangle pairwise distances.
- `length_difference_floor(lengths) -> ndarray`: |L_i − L_j| lower-bound matrix.
- `k_occurrence_counts(D, k) -> ndarray[int64]`: N_k for each point
  (stable argsort; sum = N*k guaranteed).
- `hubness_skewness(D, k) -> float`: scipy.stats.skew on N_k counts;
  returns 0.0 on NaN (constant distribution).

(c) `src/isalhg/metric_space/metrics/__init__.py` — updated to document `geometry`.

(d) Geometry table spec appended to `T-M5b.md` — 12-column schema with source
primitives mapped per column.

### Test results

```
pytest tests/unit/metric_space/test_metrics_embedding.py
       tests/unit/metric_space/test_metrics_geometry.py — 44 passed, 1 warning
pytest tests/unit/ (full)                               — 832 passed, 5 skipped, 1 warning
ruff check src/isalhg/metric_space/metrics/            — 0 errors
mypy src/isalhg/ --ignore-missing-imports              — 21 errors (baseline matched)
```

### Pre-fix failure evidence

Tests were written before implementation:
- `test_metrics_geometry.py`: `ModuleNotFoundError: No module named
  'isalhg.metric_space.metrics.geometry'` — all 20 tests collected as errors.
- `test_metrics_embedding.py` (new TestNegEigenvalueMass + TestShepardData):
  10 tests failed with `ImportError` on the two missing names.

### Premises checked

- `embedding.py` already had `classical_mds`, `is_psd`, `embed_classical`,
  `kruskal_stress_1` — confirmed, no duplication needed.
- `geometry.py` was genuinely absent (greenfield) — confirmed.
- The `D_edit` fixture (`d("ab","ba")=2`, others=1) has eigenvalues
  [2.0, 0.5, ~0, −0.25] — non-PSD confirmed, ν ≈ 0.0909 pinned in test.
- Hubness skewness returns 0.0 for constant N_k (NaN from scipy handled
  by `math.isnan` guard) — tested in `test_uniform_counts_no_hubness`.
- `geometry.md` is consistent with the implemented invariants; no refinement
  needed (the theory doc already matched the implementation plan).
