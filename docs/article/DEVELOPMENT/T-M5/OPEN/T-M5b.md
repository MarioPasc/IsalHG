# T-M5b — MDS (flagship application; HGED-FREE)
**Declared:** 2026-07-08 13:40 CEST (split from T-M5)
**Status:** OPEN
**Depends on:** T-M1b, T-M3a–d, T-M4 (+ T-M4' for the real anchor)
**Context to read first:**
- `docs/article/empirical/applications.md` §A1 — method + CV dimension selection
- `docs/article/CODE_DESIGN.md` §9 — boundary (classical-MDS solve is a `src` primitive; CV/SMACOF/figures in experiments)
- `.claude/rules/coding_rules.md` — always
**Description:** Classical + SMACOF MDS on `D_I` and each competitor
(incl. NetLSD, full member since D-ART2; HyperCOT where feasible, limit
stated); CV dimension selection (primary), Mardia ratios, negative-eigenvalue
floor; stress; PSD report; Shepard diagram. The runner also emits the
**per-corpus geometry table** (`ν`, PSD, `D̂`, stress@`D̂`, concentration,
hubness — spec from T-M5f). Runs on the planted corpus and — if T-DQ3' is
green — a larger real HIC corpus. **No HGED.**
**Acceptance:** reproduces `applications.md` §A1 criteria; `D̂` reported per
representation; the geometry table produced per corpus; figures render.
**Out of scope here:** clustering/kNN/path (M5c–e); new `src/` code.
