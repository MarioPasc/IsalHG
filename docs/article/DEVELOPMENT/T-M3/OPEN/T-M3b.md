# T-M3b — `HPDDistance` (Hyperedge Portrait Divergence, vendored MIT)
**Declared:** 2026-07-08 13:40 CEST (split from T-M3)
**Status:** OPEN
**Depends on:** T-M1a
**Context to read first:**
- `docs/article/COMPETITORS.md` §2 · `docs/article/RELATED_WORK.md` §Competitors — Agostinelli et al. 2026, `cosimoagostinelli/Hor_dissimilarity_measures`
- `docs/article/CODE_DESIGN.md` §3.2 — vendoring strategy
- `.claude/rules/coding_rules.md` — always
**Description:** Vendor the HPD function (MIT) into `representations/_hpd_vendor.py`
(provenance header); wrap as a `HypergraphDistance` (hyperedge-path tensor →
Jensen–Shannon). Register.
**Acceptance:** `matrix()` runs on the correlation corpus; numpy/scipy-only guard.
**Out of scope here:** Hyper-NetSimile (the sibling measure — skip unless needed).
