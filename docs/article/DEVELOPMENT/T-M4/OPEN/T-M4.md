# T-M4 — Planted-family datasets + metric-space scoring primitives
**Declared:** 2026-07-08 12:20 CEST · **retargeted** 2026-07-08 13:40 CEST
**Status:** OPEN
**Depends on:** T-M1a
**Context to read first:**
- `docs/article/DATA.md` §2 — the non-iso planted-family constraint (the iso-copy trap)
- `docs/article/CODE_DESIGN.md` §7 (datasets), §3 tree (metrics)
- `docs/article/empirical/applications.md` — what the metrics score
- `docs/article/empirical/correlation.md` §Information content — the bits estimator
- `src/isalhg/datasets/synthetic/exhaustive_small.py` — dataset ABC + registry pattern (fix its module-level iso import to lazy)
- `.claude/rules/coding_rules.md` — always
**Description:** `datasets/synthetic/planted_families.py` (non-isomorphic,
seed-stable within-family members; family = label) and
`metric_space/metrics/{association,information,embedding}` (Spearman/MI,
fixed-width-code bits, classical-MDS solve + stress + PSD check).
**Acceptance:** planted corpus verified non-isomorphic within family (dedup
check) with known labels; each metric primitive unit-tested against a
hand-computed value.
**Out of scope here:** running MDS/clustering/kNN (T-M5b–e, experiments); standard
sklearn indices (called in experiments, not re-wrapped).
