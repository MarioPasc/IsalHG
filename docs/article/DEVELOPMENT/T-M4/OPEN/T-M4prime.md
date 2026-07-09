# T-M4' — HIC atlas loader (real-anchor + gates T-DQ3')
**Declared:** 2026-07-08 13:40 CEST
**Status:** OPEN
**Depends on:** — (independent dataset loader)
**Context to read first:**
- `docs/article/DATA.md` §3 — the real-anchor role + scaling caveat
- `src/isalhg/datasets/hic_atlas.py` — the current stub (all methods `NotImplementedError`)
- `src/isalhg/datasets/synthetic/exhaustive_small.py` — the `HypergraphDataset` ABC + registry pattern
- `.claude/rules/coding_rules.md` — always
**Description:** Implement the `hic_atlas` loader (`github.com/iMoonLab/HIC`,
Apache-2.0) yielding whole-hypergraph instances with class labels (e.g.
IMDB→genre). Unblocks (a) T-DQ3' (`w*` timing on a real instance) and (b) the
**HGED-free** applications (MDS/clustering/kNN) on larger real hypergraphs.
**Acceptance:** loads ≥1 HIC dataset as a `HypergraphDataset` with instances +
labels; per-instance size stats (n, m, arity) reported; unit + integration test.
**Out of scope here:** the application pipeline (T-M5b–e); the `w*` timing (T-DQ3').
