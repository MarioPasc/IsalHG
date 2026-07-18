# T-M5d — kNN classification (HGED-free)
**Declared:** 2026-07-08 13:40 CEST (split from T-M5)
**Status:** OPEN
**Depends on:** T-M1b, T-M3a–d, T-M4 (+ T-M4' for the real labelled anchor)
**Context to read first:**
- `docs/article/empirical/applications.md` §A3 — kNN, metrics
- `docs/article/DATA.md` §1–§2 — labelled corpora (planted families; HIC real)
- `.claude/rules/coding_rules.md` — always
**Description:** kNN in `(·, d_I)` and competitors, LOO/stratified CV; accuracy,
macro-F1, AUC vs `k`. Planted-family labels + (if T-M4' loaded) HIC class labels.
Results are interpreted against the G1 concentration + hubness profile
(T-M5f helpers, emitted by T-M5b's runner) — report the profile alongside the
scores. **No HGED.**
**Acceptance:** reproduces `applications.md` §A3 criteria; figures render.
**Out of scope here:** MDS/clustering/path; new `src/` code.
