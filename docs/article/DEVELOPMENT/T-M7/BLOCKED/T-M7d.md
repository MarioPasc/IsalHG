# T-M7d — Combined sweep + statistics harness: body re-run with CIs and paired tests
**Declared:** 2026-07-22 11:56 CEST
**Status:** BLOCKED
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

---

## Blocking note — 2026-07-23 CEST (ledger-worker T-M7d)

**Blocking reason:** DO NOT SUBMIT until SLURM array 1631517 (T-M7h Stratum B
pilot) finalizes the admitted block set in
`experiments/article/stratum_b_feasibility_envelope.json`.  The launcher
derives block keys live from the envelope at submit time, so the admitted set
must be frozen first.

**What was built:**
- `experiments/article/analysis/sweep_multi_seed.py` (~1875 lines): full
  multi-seed sweep harness. Runs G1 + A1 + A2 + A3 + bits for all 7
  representations (isalhg_levenshtein, hypergraph_wl_l1, netlsd_l2,
  hpd_jsd, nauty_levi_edit, degree_seq_l1, hypercot) over Stratum A and
  every admitted Stratum B cell. BCa 95% CIs (scipy.stats.bootstrap),
  one-sided Wilcoxon signed-rank vs IsalHG, Holm–Bonferroni across
  (representations × metrics), median paired diff + rank-biserial. A3
  nested correctly (per seed = stratified k-fold mean AUC; bootstrap and
  Wilcoxon only over S seed-level scores). Bits via
  `isalhg.core.instructions.parse()` — not `w.split(";")`. D.npy caches
  with atomic temp-rename writes. CLI flags: `--cell-key` and `--dist-name`
  for SLURM array mode.
- `slurm/T-M7d_launcher.sh`: derives admitted Stratum B block keys live from
  the envelope; builds (cell_key, dist_name) pairs; submits array
  `0-76%20` (77 tasks = 11 cells × 7 reps). Config: `T_M7D_N_SEEDS=20`,
  `T_M7D_N_CORPUS=60`. Results at
  `/mnt/home/users/tic_163_uma/mpascual/fscratch/results/T-M7d/`.
- `slurm/T-M7d_worker.sh`: CPU-only (`--constraint=cpu`), 4 CPUs, 8 GB RAM,
  4-hour wall time per task.

**Local smoke results (commit on branch worktree-T-M7d):**

*Stratum A (20 seeds, n_corpus=15):* seeds 0–14 all completed; all 7
representations including HyperCOT flow through on every seed. Per-seed
timing: isalhg_levenshtein 1.8–3.3 s for N=40; hypercot 1.3–1.5 s. BCa
CIs, Wilcoxon, and Holm p-values emitted correctly; A3 (5-fold × 8
classes) runs.

*Stratum B (3 seeds, n_corpus=12):* k3_n8_rho1 and k3_n8_rho2 verified;
all 7 representations including HyperCOT (1–3 s per matrix) flow through.
rho4 cells time out locally at ~20 s/seed for n=8, but remain within the
4-hour Picasso wall time (n=8 rho4: ~35 min/task at n_corpus=60, 20 seeds;
n=16 rho4: up to ~2.3 h estimated).

**Arity-4/5 design finding (PI-level observation):**
Nine of the 17 admitted Stratum A designs have only m=3 hyperedges
(loose_path_k4, tight_path_k4, loose_path_k5, tight_path_k5, and
5 k≥4 designs). The Qin-edit perturbation space for m=3 is too small to
yield non-isomorphic members under the 300-retry budget. The runner falls
back to the 8 arity-3 designs (`ADMITTED_A_IDS_ARITY3`: sts7, sts9, gq22,
loose_path_k3, tight_path_k3, loose_cycle_k3, tight_cycle_k3,
complete_k3_n5) consistently across all 20 seeds. This fallback fires on
every seed in the smoke; the 8-design fallback is therefore the effective
Stratum A corpus. The PI may want to either (a) accept the arity-3
fallback as the de-facto Stratum A corpus, or (b) fix `PlantedFamilyDataset`
in `src/isalhg/` to use a smaller n_edits or a different edit strategy for
low-m designs (out of scope for T-M7d per the security boundary).

**Unit tests:** 171 passed, 5 deselected (slow) in
`tests/unit/experiments_article/` on env `isalhg-T-M7d`.
ruff: 3 errors (baseline unchanged). mypy: 21 errors (baseline unchanged).

**Sbatch paths:**
- Launcher: `slurm/T-M7d_launcher.sh`
- Worker:   `slurm/T-M7d_worker.sh`
- Runtime estimate: 77 tasks × max 20 concurrent ≈ 4 array waves ≈ 2 h total
  wall time on Picasso (worst-case task: isalhg_levenshtein on n=16 rho4,
  ~2.3 h; 4-hour per-task wall covers it). Most tasks finish in < 10 min.

**Waiting on:** array 1631517 finalization → orchestrator submits.
