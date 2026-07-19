# T-M5a — Discussion evidence: E1' figure + information content (rescoped at D-ART2)
**Declared:** 2026-07-08 13:40 CEST (split from T-M5) · **rescoped** 2026-07-18 17:56 CEST (D-ART2)
**Status:** IN-PROGRESS (part 1 — DQ1' probe + Picasso E1' submission — started 2026-07-19 at S3; part 2 harvests at S5)
**Depends on:** T-M1b, T-M2 (DONE — oracle), T-M2c (connected mini-corpus generators), T-M4 (association + information primitives)
**Context to read first:**
- `docs/article/empirical/correlation.md` — E1' spec + the bits estimator + what is retired
- `docs/article/PROPOSAL.md` §4–§5 — where each deliverable lands in the paper
- `docs/article/DATA.md` §4 — the exact-HGED mini-corpus
- `docs/article/CODE_DESIGN.md` §9 — the src/experiments boundary
- `experiments/preprint/` — the pipeline pattern; `experiments/orchestrator.py`
- `.claude/rules/coding_rules.md` — always
**Description:** Two deliverables, both `experiments/article/`, no `src/`
changes. (1) **E1' — the discussion figure**: exact HGED (HPC parallel) on the
connected mini-corpus, all pairs; Spearman ρ + scatter/joint-density figure,
**ours only** — no competitor rows, no density sweep, no MI. (2) **Information
content**: fixed-width-code bits vs incidence-list construction-model bits on
the body corpora; compression-ratio table, one-sided Wilcoxon, OLS β.
**Rescope note (D-ART2):** the v2 contents of this task — the full correlation
study with competitor rows + MI, and the density sweep testing the `C(k,Δ)`
Δ-prediction — are retired from the article (recorded in
`theoretical/stability.md` §4 as follow-up material). The v2 E2b/E3
(sensitivity histograms, ladder scaling) are **not here**: they moved to the
geometry pillar as G2 (T-M5g).
**Acceptance:** reproduces `correlation.md` E1' + §Information content
criteria; the E1' figure and the bits table render; mini-corpus size pinned by
an oracle wall-clock probe (DQ1', logged in DATA.md).
**Out of scope here:** the applications (T-M5b–e); the G2 profiles (T-M5g);
new `src/` code (`task-handoff` it); any competitor HGED computation.

---
**Reconciliation note (S1 merge, 2026-07-18).** The v2 contents of this task
were executed and closed on the pre-rescope `main` (commits `6d92271` +
`c680588`: the `experiments/article/` Layer-1 pipeline — correlation, density
sweep, E2b/E3 — with the Picasso submission recorded in T-M5a', jobs
1547131/32/33). That closure is **superseded by this rescope**: the v2
closure record was dropped from `CLOSED/` at the reconciliation merge and
T-M5a' is parked under `BLOCKED/` (D-ART2). The v2 pipeline code remains in
`experiments/article/` and should be cannibalized for the E1' + bits runner.

---
**Part-1 record (orchestrator, 2026-07-19 16:51 CEST — S3).** DQ1' probe +
mini-corpus pin + Picasso submission; part 2 (harvest + figure + bits) runs
at S5.

- **DQ1' probe** (local RTX-4060 workstation, `isalhg` env, 30 s/pair cap,
  seed 42): exact HGED on `perturbation_ladder` pairs, arity ≤ 3 —
  per-(n, m_attempts): (5,3) med 4 ms / max 0.28 s; (6,4) med 1 ms;
  (7,5) med 8 ms / max 4.8 s; (8,6) med 19 ms; (9,7) med 92 ms / p90 2.5 s;
  (10,8) med 9 ms / max 0.87 s. **0 DNFs** across all 60 timed pairs.
  Ceiling pinned at (n, m) = (10, 8). Logged in `DATA.md` §6 (DQ1').
- **Mini-corpus pinned** (`experiments/article/configs/e1prime_mini_corpus.yaml`):
  12 cells = base n ∈ {5..10} × seeds {42, 43}; each cell 4 ladders × 9
  snapshots = 36 items → 630 all-pairs; ≈ 7,560 (d_I, HGED) pairs total.
  Distances per cell: `isalhg_levenshtein`, `exact_hged` (no per-pair
  timeout — E1' needs exact values; the 6 h SLURM wallclock bounds a cell).
- **Local smoke** (cell 0, n=5): `d_matrix` end-to-end — d_I 0.01 s,
  exact-HGED 630 pairs in 15.8 s; `D.npy` + `meta.json` written. Sanity:
  Spearman ρ = 0.633 (p = 1.7e-71, 626 HGED>0 pairs), HGED range 1–29,
  d_I range 1–18, and all 4 HGED=0 pairs have d_I = 0 (metric consistency).
- **Picasso submission**: repo rsynced to
  `fscratch/repos/IsalHG` (post-S3-merge tree), editable install rebuilt with
  `fscratch/conda_envs/isalhg` python, runner `--count` = 12 verified on the
  login node. Submitted via `slurm/T-M5a_launcher.sh` (v2 pair reused;
  CPU-only, 4 CPU / 16 GB / 6 h per task; Lua wrapper applied
  `--constraint=cpu`). **Job 1616143**, array 0–11, all 12 tasks RUNNING at
  submit+1 min on sd[015,051,108,110]. Output root:
  `/mnt/home/users/tic_163_uma/mpascual/fscratch/isalhg_results/T-M5a/e1prime`.
  Logs: `~/execs/T-M5a/logs/T-M5a-e1prime_mini_corpus_1616143_*.{out,err}`.
- **Remaining (part 2, S5):** harvest `D.npy` pairs, ours-only ρ + scatter
  figure, bits/Wilcoxon table on the body corpora, close the task.
