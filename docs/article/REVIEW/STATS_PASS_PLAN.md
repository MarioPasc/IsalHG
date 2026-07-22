# Statistics pass — plan for A1/A2/A3 significance testing

**Status:** planning note (not yet a ledger task). The single acceptance-gating
item from the walkthrough assessment.

**Problem.** A1/A2/A3 currently report point estimates (stress, ARI, NMI, AUC)
with no uncertainty and no paired test. Only the bits study (Wilcoxon
`p = 1.6e-54`) and E1′ (`ρ = 0.622`, p ≈ 0) carry statistics. A statement like
"HPD 0.83 > IsalHG 0.73" on AUC is currently **unfalsifiable** — for a
data-science journal this is a top trigger for major-revision.

**Run this together with the parameter sweep (`DATA_RIGOR.md`).** Significance
testing quantifies uncertainty *at a single (n, density, arity) point*; the
sweep establishes generalization *across* those axes. They are complementary,
not substitutes. The efficient plan is one combined harness: at each sweep point,
resample over `S` seeds and emit both the CI and the paired test — so every
sweep point in every geometry/application curve carries an error band and a
competitor comparison. Do not ship the stats pass at the single n=10/k=3 point
and call generalizability done.

---

## Design

### Resampling unit = the corpus (seed-level pairing)

Generate the planted corpus under `S` independent generator seeds (recommend
`S ≥ 20`). Seeds are already pinned per the experiment standard, so this is a
sweep over the existing pipeline, not a rewrite. For each seed:

- build `D_rep` for every representation on the *same* seeded corpus,
- run A1/A2/A3, record the full metric vector per representation.

This yields a **paired** sample of size `S`: every representation is scored on
identical corpora, so competitor-vs-IsalHG differences are paired.

### Confidence intervals

- **BCa bootstrap** (bias-corrected accelerated, `scipy.stats.bootstrap`) over
  the `S` seed-level scores, per (representation, metric). Report the 95% CI in
  every table cell alongside the point estimate.

### Paired significance tests

- For each competitor vs IsalHG, **one-sided Wilcoxon signed-rank** over the `S`
  paired seed-scores (same test family already trusted in the bits study).
- Also report the **paired-difference CI** (bootstrap over `S` differences) — more
  informative to a reviewer than a bare p-value.

### Multiple comparisons

- **Holm–Bonferroni** across the full family (representations × metrics). State
  the correction and the family size explicitly.

### Effect size

- Report the **median paired difference** + **rank-biserial correlation** per
  comparison, so "significant but negligible" is visible and cannot be
  over-read.

### A3 (kNN) nested variance — do this correctly

- Per seed: stratified `k`-fold CV, repeated `R` times; the seed-level AUC is the
  **mean over folds** for that seed.
- Bootstrap / Wilcoxon over the `S` seed-level AUCs **only**. Do **not** bootstrap
  folds and seeds independently — that double-counts the CV variance and inflates
  significance.

---

## Expected outcome — plan for it, don't hope

The likely finding: IsalHG's second place to HPD on A2/A3 is **statistically
real** (small but significant gap, or CI-overlapping). The narrative must
therefore be:

> IsalHG is **competitive** (CI-overlapping or a small significant gap) on
> clustering and kNN, **and** uniquely complete + decodable.

Not "the gap is noise." Do not write any sentence that would be falsified by the
stats you are about to compute.

---

## What lands where

- **Code:** `experiments/analysis/stats.py` already exists (CODE_DESIGN §6,
  Phase 5) — extend it with the bootstrap-CI + paired-Wilcoxon + Holm helpers.
  The A1–A3 runners loop over the `S`-seed sweep; the analysis module consumes
  the per-seed JSON.
- **Docs:** the CI + p-value columns land in the `empirical/applications.md`
  measured tables; the methods paragraph (test, correction, `S`, `R`) goes in
  the same section.
- **Cost:** real compute — `S ≈ 20` full re-runs of A1–A3 across all 6
  representations at `N = 240`. The `D_rep` caches (`n240/d_matrix/`,
  `T-M5b/d_matrix/`) already exist for seed 42; the sweep adds `S − 1` more
  seeds. Budget accordingly (D-matrix wall-clock at `N = 240`: nauty 0.05 s, WL
  0.09 s, `d_I` 0.18 s, NetLSD 0.27 s, HPD 0.88 s per matrix; HyperCOT `O(n³)`
  and only on small corpora).

## Recommended ledger framing

One task (S6-adjacent, article-gating). Depends on the existing A1–A3 pipelines
(T-M5b/c/d) and the seeded planted-family generator (T-M4). Acceptance check:
every A1/A2/A3 table cell carries a 95% CI; every competitor-vs-IsalHG claim
carries a Holm-corrected paired p-value and an effect size; no prose sentence
contradicts the computed stats.
