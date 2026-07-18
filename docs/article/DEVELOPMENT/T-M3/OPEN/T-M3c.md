# T-M3c — `NetLSDDistance` (spectral baseline; full member since D-ART2)
**Declared:** 2026-07-08 13:40 CEST (split from T-M3) · **promoted** 2026-07-18 17:56 CEST (D-ART2)
**Status:** OPEN
**Depends on:** T-M1a
**Context to read first:**
- `docs/article/COMPETITORS.md` §2 — full member, all corpora; the cheap
  spectral baseline that scales wherever we do
- `RELATED_WORK.md` — Tsitsulin et al. 2018, `pip install netlsd`
- `src/isalhg/core/levi_reduction.py` (post-M1a) — heat-trace on the Levi expansion
- `.claude/rules/coding_rules.md` — always
**Description:** `HypergraphDistance` = L2 between NetLSD heat-trace signatures
of the Levi expansion. Register. **Promoted from optional fifth to full
member** (D-ART2): it runs on every corpus, including the ones HyperCOT's
`O(n³)`/pair cannot reach, so it is the guaranteed at-scale fair baseline.
**Acceptance:** `matrix()` runs on the planted corpus; guarded `netlsd` import;
iso pairs → distance 0 (sanity).
**Out of scope here:** the other competitors; the applications.
