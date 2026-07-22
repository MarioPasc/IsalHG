# T-M7d — Combined sweep + statistics harness: body re-run with CIs and paired tests
**Declared:** 2026-07-22 11:56 CEST
**Status:** OPEN
**Depends on:** T-M7a (Stratum A corpus), T-M7b (Stratum B sweep + envelope),
T-M7c (naive baseline registered), T-M5b/c/d (the existing A1/A2/A3 pipelines
this re-drives), T-M5f (geometry helpers).
**Origin:** 2026-07-22 REVIEW pass (`docs/article/REVIEW/STATS_PASS_PLAN.md`
in full; `REVIEW/DATA.md` §3, §7.7), directed by Mario. The two co-equal top
gaps close together here: uncertainty quantification (no A1–A3 result carries a
CI or test today) and generalization (every headline number is a single
(n, density, arity) point).
**Context to read first:**
- `docs/article/REVIEW/STATS_PASS_PLAN.md` — the full design (seed-level
  pairing, BCa bootstrap, one-sided Wilcoxon, Holm, effect sizes, nested-CV
  rule for A3)
- `docs/article/REVIEW/DATA.md` §3 (per-experiment slice map), §5 (reporting
  rules)
- `experiments/analysis/stats.py` — the module to extend (CODE_DESIGN Phase 5)
- `experiments/article/analysis/{mds,clustering,knn,bits_harvest}.py` — the
  pipelines to loop; T-M5i's registry-fallback fix governs dataset construction
- `docs/article/DEVELOPMENT/T-M5/CLOSED/T-M5b.md` — the D.npy cache layout
  A2/A3 share
- **Landmine:** all bits counting through the bracket-aware parser (the
  `w.split(";")` bug reversed the conclusion twice in S5; regression tests T15
  exist — reuse them)
**Description:** One harness, two jobs. (1) **Sweep:** run G1 + A1 (geometry
table) + A2 + A3 + bits over the Stratum A corpus and every admitted Stratum B
cell, all seven representations (five competitors + naive baseline + d_I),
shared `D.npy` caches per (cell, seed, representation). Emit the
geometry-vs-axis curves (ν, D̂, stress-1, hubness skew vs n / density / arity)
and per-axis application metrics. Analysis discipline: across `k` compare only
dimensionless descriptors and within-`k` rankings — never pooled raw `d_I`.
(2) **Statistics, at every point:** S ≥ 20 seeds per cell as the paired
resampling unit; BCa bootstrap 95% CIs per (representation, metric, cell);
one-sided Wilcoxon signed-rank vs IsalHG per competitor with Holm–Bonferroni
across the (representations × metrics) family; median paired difference +
rank-biserial effect size; A3 nested correctly (per seed: repeated stratified
k-fold; seed-level score = fold mean; resample seeds only). All D̂ values for
censored representations carry the `≥ cap` flag in the emitted tables.
**Acceptance:** every emitted A1/A2/A3/G1/bits table cell carries a 95% CI;
every competitor-vs-IsalHG claim carries a Holm-corrected p and an effect size;
the geometry-vs-axis curves exist for ≥ 3 values on each of the n, density, and
arity axes with error bands; the naive-baseline row present on every surface;
bits reproduced through the pinned parser tests on the new corpora; stats
module unit-tested (pinned BCa interval on a known sample; Holm ordering; the
nested-CV rule asserted — a test fails if folds and seeds are resampled
independently); result JSONs carry their seeds in-content.
**Out of scope here:** ladder/A4/G2 re-runs (T-M7e), G3 (T-M7f), real-data
(T-M7g), E1′ (closed at S5 — the existing figure stands), prose folding into
`empirical/applications.md` (a follow-up doc pass owns it; only the artifact
tables/curves are produced here).
