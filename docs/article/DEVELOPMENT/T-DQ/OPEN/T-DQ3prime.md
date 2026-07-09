# T-DQ3' — Measure `w*` wall-clock on a HIC instance (real-anchor gate)
**Declared:** 2026-07-08 12:20 CEST
**Status:** OPEN
**Depends on:** T-M0 (DONE — seed-optimized `w*`), T-M4' (HIC loader)
**Note (2026-07-08):** raised in value — since applications are now HGED-free,
`w*` wall-clock is the *only* gate on running MDS/clustering/kNN at real scale,
so this one measurement decides how large the application corpora can be.
**Context to read first:**
- `docs/article/DATA.md` §3 (DQ3') — why this decides the real anchor
- `src/isalhg/datasets/hic_atlas.py` — the (stubbed) loader
- `src/isalhg/core/canonical.py` — the `w*` entry point to time
- `.claude/rules/coding_rules.md` — always
**Description:** Time `canonical_string` on one real HIC IMDB instance (post
T-M0 + C++). One number decides whether a real-world anchor (A1/A2 at scale) is
in scope or the paper stays on synthetic + small designs.
**Acceptance:** a reported wall-clock (seconds/minutes/DNF) on a named HIC
instance, with a go/no-go recommendation for the real anchor.
**Out of scope here:** building the full HIC application pipeline (deferred to T-M5b–e).
