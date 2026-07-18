# T-M5e — Shortest path between hypergraphs (differentiator; HGED-free scoring)
**Declared:** 2026-07-08 13:40 CEST (split from T-M5) · **rescored** 2026-07-18 17:56 CEST (D-ART2)
**Status:** OPEN
**Depends on:** T-M1b, T-M2c (connected ladder generators), T-M3a (contrast), T-M4, T-M5g (ladder-response baseline)
**Context to read first:**
- `docs/article/empirical/applications.md` §A4 — the v3 scoring spec (ladder-based)
- `docs/article/DATA.md` §3 — ladder corpora + distractor pools
- `src/isalhg/core/string_to_hypergraph.py` — S2H (decodes intermediates)
- `.claude/rules/coding_rules.md` — always
**Description:** Minimal-`d_I` path `H_A → H_B` through an intermediate pool.
**v3 scoring (HGED-free, replacing the v2 "vs HGED-geodesic" metric):**
endpoints from perturbation ladders with known accumulated Qin budget `t`;
pool = the ladder's true intermediates + same-corpus distractors. Scores:
(i) path recovery (does the shortest path re-find the ladder intermediates or
same-budget equivalents, in order); (ii) monotonicity of accumulated path
length vs `t`; (iii) the decodability figure — S2H-decode the intermediates of
one recovered path and render the hypergraph sequence (the capability no
competitor has: vector fingerprints have no decoder; nauty's string is not
edit-navigable, shown by its G2 avalanche profile).
**Acceptance:** reproduces `applications.md` §A4 criteria; scores (i)–(ii)
reported for ours + vector competitors where computable; the capability matrix
row filled; the decoded-intermediates figure renders.
**Out of scope here:** MDS/clustering/kNN; new `src/` code; any HGED call.
