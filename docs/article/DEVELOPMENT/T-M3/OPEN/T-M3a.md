# T-M3a — `NautyLeviEditDistance` (contrast baseline)
**Declared:** 2026-07-08 13:40 CEST (split from T-M3)
**Status:** OPEN
**Depends on:** T-M1a
**Context to read first:**
- `docs/article/COMPETITORS.md` §2–§3 — the *contrast* role (iso-only, no navigable geometry)
- `src/isalhg/iso_backends/pynauty_levi.py` + `src/isalhg/core/levi_reduction.py` (post-M1a)
- `.claude/rules/coding_rules.md` — always
**Description:** `HypergraphDistance` computing string-edit distance between the
nauty canonical forms of the Levi graphs. The deliberate contrast that *fails*
A4 (shortest path). Register in `metric_space/registry.py`.
**Acceptance:** `matrix()` runs on the correlation corpus; distance 0 on
isomorphic pairs; guarded `pynauty` import raises `RepresentationDependencyMissingError`.
**Out of scope here:** the head-to-head study (T-M5a).
