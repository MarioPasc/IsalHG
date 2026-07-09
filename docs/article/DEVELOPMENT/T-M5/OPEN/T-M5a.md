# T-M5a — Correlation / density-sweep / information-content (Layer 1; NEEDS HGED)
**Declared:** 2026-07-08 13:40 CEST (split from T-M5)
**Status:** OPEN
**Depends on:** T-M1b, T-M2, T-M4 (+ any T-M3* competitors to include)
**Context to read first:**
- `docs/article/empirical/correlation.md` — E1/E2/E2b/E3 + acceptance
- `docs/article/theoretical/stability.md` §4 — the Δ-prediction the sweep tests
- `docs/article/CODE_DESIGN.md` §9 — the src/experiments boundary
- `experiments/preprint/` — the pipeline pattern; `experiments/orchestrator.py`
- `.claude/rules/coding_rules.md` — always
**Description:** `experiments/article/` runner that caches `D` matrices per
`(distance, dataset, seed)`, then: correlation (Spearman/Pearson/MI) of `d_I` and
each competitor vs HGED; the **density sweep** (n>10 on HPC) testing the `C(k,Δ)`
Δ-prediction; single-edit sensitivity histogram (E2b); information-content bits +
one-sided Wilcoxon. No `src/` changes.
**Acceptance:** reproduces `correlation.md` closing criteria; ρ-vs-Δ figure shows
the predicted decay.
**Out of scope here:** the applications (T-M5b–e); new `src/` code (`task-handoff` it).
