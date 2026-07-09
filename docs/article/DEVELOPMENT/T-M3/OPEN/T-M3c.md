# T-M3c — `NetLSDDistance` (optional spectral, pip)
**Declared:** 2026-07-08 13:40 CEST (split from T-M3)
**Status:** OPEN
**Depends on:** T-M1a
**Context to read first:**
- `docs/article/COMPETITORS.md` §2 (optional spectral) · `RELATED_WORK.md` — Tsitsulin et al. 2018, `pip install netlsd`
- `src/isalhg/core/levi_reduction.py` (post-M1a) — heat-trace on the Levi/clique expansion
- `.claude/rules/coding_rules.md` — always
**Description:** `HypergraphDistance` = L2 between NetLSD heat-trace signatures of
the Levi expansion. Register. (Optional fifth competitor.)
**Acceptance:** `matrix()` runs; guarded `netlsd` import.
**Out of scope here:** promoting it to a headline baseline (it is the spectral aside).
