# T-M3d — `HyperCOTDistance` (pinned conda env, subprocess)
**Declared:** 2026-07-08 13:40 CEST (split from T-M3)
**Status:** OPEN
**Depends on:** T-M1a
**Context to read first:**
- `docs/article/COMPETITORS.md` §2 (dual role: theory anchor + competitor) · `RELATED_WORK.md` — Chowdhury et al. 2024, `samirchowdhury/HyperCOT` (pins `hypernetx==1.2`, `POT==0.8.0`)
- `docs/article/CODE_DESIGN.md` §3.2 — `SubprocessRepresentation`
- `src/isalhg/iso_backends/subprocess_base.py` — the subprocess pattern to mirror
- `.claude/rules/coding_rules.md` — always
**Description:** `SubprocessRepresentation` base + `HyperCOTDistance`: serialize
the corpus, shell out to a dedicated `isalhg-hypercot` conda env, parse back the
distance matrix. Register. Heaviest/most independent competitor.
**Acceptance:** `matrix()` runs on the correlation corpus via the pinned env;
distance 0 on isomorphic pairs; `SubprocessRepresentationError` with a setup hint
when the env is absent.
**Out of scope here:** the head-to-head study (T-M5a); a learned/GNN baseline (dropped).
