# T-M5c — Clustering + dendrogram (HGED-free)
**Declared:** 2026-07-08 13:40 CEST (split from T-M5)
**Status:** DONE
**Depends on:** T-M1b, T-M3a–d, T-M4 (+ T-M4' for the real anchor)
**Context to read first:**
- `docs/article/empirical/applications.md` §A2 — k-medoids + dendrogram, metrics
- `.claude/rules/coding_rules.md` — always
**Description:** k-medoids (PAM) + agglomerative dendrogram on `D_I` and
competitors; silhouette/Dunn/DB + ARI/NMI vs planted labels; cophenetic
correlation; medoid-representative reported inline as the PAM `k=1`
degenerate. Report metrics vs corpus density (descriptive; the Theorem-B
Δ-validation is retired at D-ART2). **No HGED.**
**Acceptance:** reproduces `applications.md` §A2 criteria; figures render.
**Out of scope here:** MDS/kNN/path; new `src/` code.

---

## Closing note (2026-07-19)

**Executed by:** ledger-worker (T-M5c, worktree agent-ad4d83d4d83ab2ded, branch worktree-agent-ad4d83d4d83ab2ded)

**Module:** `experiments/article/analysis/clustering.py`
**Tests:** `tests/unit/analysis/test_clustering.py` (13 unit tests, 1 slow marked)

### Acceptance check output

Pipeline ran on both corpora. Figures rendered (PDF). Tables written to
`/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/T-M5c/`.

**planted_main (N=60, k=5, 5 families × 12 members, seed=42):**

```
Representation    Sil    Dunn      DB    ARI    NMI   Coph
----------------------------------------------------------
IsalHG          0.105   0.450   1.453  0.181  0.318  0.668
WL-L1           0.004   0.950   0.959 -0.000  0.112  0.684
NetLSD          0.450   0.171   0.704  0.170  0.309  0.775
HPD-JSD         0.146   0.443   1.414  0.331  0.457  0.788
NautyEdit       0.067   0.449   1.601  0.002  0.106  0.762
```

**planted_small (N=20, k=4, HyperCOT corpus, seed=42):**

```
Representation    Sil    Dunn      DB    ARI    NMI   Coph
----------------------------------------------------------
IsalHG          0.124   0.182   1.497 -0.094  0.088  0.868
HyperCOT        0.186   0.242   1.340  0.151  0.340  0.699
```

**Medoid (k=1 degenerate):** IsalHG on planted_main → point 26 (family 2);
on planted_small → point 3 (family 0).

### Design decisions

- **PAM library:** `kmedoids.fasterpam` (Schubert & Lenssen 2022, JOSS 7(75)).
  `scikit-learn-extra` had a numpy binary incompatibility; `kmedoids` is a
  superior PAM implementation (FasterPAM, same results, O(k) swap step).
- **Davies–Bouldin on precomputed D:** medoid substitutes centroid;
  s_i = mean distance from cluster points to medoid; d_ij = D[medoid_i, medoid_j].
  Documented in docstring.
- **Linkage:** UPGMA ('average') — defined for any dissimilarity, no Euclidean
  assumption. 'ward' would require coordinates.
- **n_init=10 restarts** for FasterPAM; best-loss result returned.

### Test suite

pytest: **1035 passed, 8 skipped, 16 deselected** (baseline: 1022/8/15; +13 new unit tests).
ruff: **3 errors** (baseline 3, src/isalhg/ + tests/ scope — no new issues).
mypy: **21 errors** (baseline 21 — no new issues).

### Figures produced

`/media/.../results/T-M5c/figures/planted_main/`:
  dendrogram_{isalhg_levenshtein,hypergraph_wl_l1,netlsd_l2,hpd_jsd,nauty_levi_edit}.pdf,
  dendrogram_combined.pdf, metric_comparison.pdf

`/media/.../results/T-M5c/figures/planted_small/`:
  dendrogram_{isalhg_levenshtein,hypercot}.pdf,
  dendrogram_combined.pdf, metric_comparison.pdf
