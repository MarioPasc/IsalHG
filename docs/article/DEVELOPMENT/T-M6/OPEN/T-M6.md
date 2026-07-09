# T-M6 — (optional) reparent iso packages under `isomorphisms/`
**Declared:** 2026-07-08 12:20 CEST
**Status:** OPEN
**Depends on:** T-M1a..T-M5e (do last; cosmetic)
**Context to read first:**
- `docs/article/CODE_DESIGN.md` §2 (target tree), §8 (dependency direction)
- `.claude/rules/coding_rules.md` §2 (refactor protocol)
**Description:** Move `iso_backends/`, iso `protocols/`, iso `metrics/`
(correctness, partition) under `isalhg/isomorphisms/`; update registries,
experiments, tests. Pure move + import rewrite.
**Acceptance:** full test suite + ruff + mypy green; no behaviour change.
**Out of scope here:** any functional change; the shared `metrics/{runtime,
complexity_fit}` stay top-level.
