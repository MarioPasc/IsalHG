# T-M5e — Shortest path between hypergraphs (differentiator; HGED-free)
**Declared:** 2026-07-08 13:40 CEST (split from T-M5)
**Status:** OPEN
**Depends on:** T-M1b, T-M3a (contrast), T-M4
**Context to read first:**
- `docs/article/empirical/applications.md` §A4 — the differentiator competitors cannot do
- `.claude/rules/coding_rules.md` — always
**Description:** Minimal-`d_I` path `H_A→H_B` through an intermediate pool;
recovered-path length vs HGED-geodesic; show nauty-contrast cannot navigate.
**No HGED for scoring** (HGED-geodesic only on the small corpus as a reference).
**Acceptance:** reproduces `applications.md` §A4 criteria; figures render.
**Out of scope here:** MDS/clustering/kNN; new `src/` code.
