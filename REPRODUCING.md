# Reproducing the IsalHG metric-space article

This document reproduces the article's quantitative claims from the shipped
artifact. The reproduction driver reads the small per-seed caches and
re-runs the published statistics pipeline; it needs no HPC access and no
recomputation of the pairwise distance matrices.

## 1. Environment

```bash
conda create -n isalhg --file artifacts/reproducibility/isalhg_env.lock.txt
conda activate isalhg
pip install -e ".[dev]"
```

The HyperCOT competitor runs in a separate pinned env (`hypernetx==1.2` + POT,
incompatible with the main env's `hypernetx==2.4`); it is only needed to
regenerate HyperCOT's distance matrices, not to reproduce the tables below:

```bash
conda create -n isalhg-hypercot --file artifacts/reproducibility/isalhg_hypercot_env.lock.txt
```

Exact versions and licenses: `artifacts/reproducibility/VERSIONS_LICENSES.md`.

## 2. Data

Every result is mapped to its corpus in the results-drive manifest
(`RESULTS_MANIFEST.md` at the results root). In brief, the article body is the
S=27 sweep over **Stratum A** (17 known-design families × 5 members = 85 items,
arities 3/4/5) and the 10 admitted **Stratum B** Erdős–Rényi cells; three
Stratum B cells are excluded whole-cell because `w*_c` exceeded a 4-hour wall
there (the measured feasibility frontier — see §5).

The reproduction reads only the shipped per-seed caches:
`<results>/T-M7d/seed_metrics/` (KB–MB scale, included). The full pairwise
`D.npy` matrices (`<results>/T-M7d/d_matrix/`, ~64 MB) ship too but are not
required for the tables.

## 3. Reproduce the geometry table, bits, and a paired test

```bash
PYTHONPATH=. python scripts/reproduce_tables.py \
    --results-root <results>/T-M7d
```

Expected output (matches `<results>/T-M7d/stats/stratum_a_stats.json` to full
precision; these are the published Stratum A / IsalHG values):

| check | expected |
|---|---|
| geometry ν | 0.0974229 |
| geometry D̂ | 16.8148 |
| geometry stress-1 | 0.0461492 |
| geometry hubness skewness | 0.907314 |
| bits median ratio | 1.3048 |
| Wilcoxon: degree-seq > IsalHG on A2-ARI, Holm p (reverse) | 4.47035×10⁻⁷ |

The script exits 0 on full agreement. The last row is the reverse-direction
test (a competitor beating IsalHG); the forward direction for the same pair is
`p_holm = 1.0` — the two directions are separate Holm families and the artifact
labels each with its `alternative`.

## 4. Application figures

The kNN (A3) and clustering (A2) figures are read from the same
`stats/*_stats.json`. AUC-OvR at k=5 with WL's chance-level collapse (0.495
[0.494, 0.497]) is the headline A3 exhibit; the values and their 95% BCa CIs
are in `stratum_a_stats.json` under `<repr>::a3::auc_k5`. The capability matrix
figure is rendered by `render_capability_matrix(output_path=...)` in
`experiments/article/analysis/figures/capability_matrix.py` (its cells are
proved/measured capabilities, not corpus-dependent); the unit test
`tests/unit/experiments_article/test_capability_matrix.py` exercises it.

## 5. HPC-only steps (stated honestly, caches shipped)

Two measurements were produced on the Picasso cluster and are **not** part of
the clean-machine dry run; their caches ship so downstream numbers reproduce
without re-running them:

- **E1′ (exact-HGED correlation).** The exact HGED oracle is expensive: the
  hardest completed block ran ~8.5 h at 55 GB, and the excluded 12th block hit
  a 100 GB / 72 h ceiling. The frozen result (Spearman ρ = 0.622 on the
  11-block corpus, N = 6,921 pairs) and its inputs are in `<results>/T-M5a/`.
  Do not re-run the oracle.
- **The S=27 sweep itself** (array 1640910, 77 tasks) produced the `D.npy` and
  `seed_metrics` caches this artifact ships. Regenerating them from scratch
  needs the cluster; the shipped caches make §3 reproducible without it.

## 6. Known limitation carried in the artifact

The Stratum B arity axis has two points (k ∈ {3, 5}); the ≥3-value criterion is
not met there because k=4 blocks timed out and k=7/10 are measured infeasible.
The harvest artifact records this honestly
(`artifacts/T-M7d-harvest/harvest_summary.json`: `all_acceptance_pass: false`,
`acceptance_shortfalls: ["ac5_arity_axis"]`). The per-arity A2/A3 breakdown on
Stratum A does cover k ∈ {3, 4, 5}, but that is an application-metric object,
not the geometry sweep curve.

## 7. Supplement

The completeness proof (Theorem A) is the supplement:
`proofs/completeness/theorem_a_completeness.{tex,pdf}` on the results drive.

## 8. Deposit

DOI: **deposit pending** (Zenodo, at PI direction on submission). The tagged
repository state and this artifact are the deposit contents.
