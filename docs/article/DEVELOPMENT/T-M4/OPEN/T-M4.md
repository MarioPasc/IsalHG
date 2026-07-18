# T-M4 — Planted-family datasets + metric-space scoring primitives
**Declared:** 2026-07-08 12:20 CEST · **retargeted** 2026-07-08 13:40 CEST
**Status:** OPEN
**Depends on:** T-M1a
**Context to read first:**
- `docs/article/DATA.md` §1 — the non-iso planted-family constraint (the iso-copy trap) + the geometry-sweep parameterization
- `docs/article/CODE_DESIGN.md` §7 (datasets), §3 tree (metrics)
- `docs/article/empirical/applications.md` — what the metrics score
- `docs/article/empirical/correlation.md` §Information content — the bits estimator
- `src/isalhg/datasets/synthetic/exhaustive_small.py` — dataset ABC + registry pattern (fix its module-level iso import to lazy)
- `.claude/rules/coding_rules.md` — always
**Description:** `datasets/synthetic/planted_families.py` (non-isomorphic,
seed-stable within-family members; family = label; connected by construction —
D-CONN1; parameterized for the D-ART2 geometry sweeps: density, arity mix,
size) and `metric_space/metrics/{association,information,embedding,geometry}`
(Spearman/Pearson — MI retired at D-ART2; fixed-width-code bits; classical-MDS
solve + stress + PSD + `ν`; concentration stats + hubness skewness — the
static-invariant helpers T-M5f specs).
**Acceptance:** planted corpus verified non-isomorphic within family (dedup
check) with known labels; each metric primitive unit-tested against a
hand-computed value.
**Out of scope here:** running MDS/clustering/kNN (T-M5b–e, experiments); standard
sklearn indices (called in experiments, not re-wrapped).
