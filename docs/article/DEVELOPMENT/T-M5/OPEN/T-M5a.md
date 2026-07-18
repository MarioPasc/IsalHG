# T-M5a — Discussion evidence: E1' figure + information content (rescoped at D-ART2)
**Declared:** 2026-07-08 13:40 CEST (split from T-M5) · **rescoped** 2026-07-18 17:56 CEST (D-ART2)
**Status:** OPEN
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
