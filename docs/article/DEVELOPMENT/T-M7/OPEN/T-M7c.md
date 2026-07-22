# T-M7c — Naive baseline distance (degree-sequence L1)
**Declared:** 2026-07-22 11:56 CEST
**Status:** OPEN
**Depends on:** T-M1a (`metric_space/` distance ABC + registry).
**Origin:** 2026-07-22 REVIEW pass (`docs/article/REVIEW/APPROACH_RIGOR.md`
§1), directed by Mario. All five competitors are sophisticated; no comparison
surface currently answers "does anyone beat a trivial structural distance?".
Must land **before** T-M7d so its row is produced by the same harness with the
same CIs — retrofitting later doubles the compute.
**Context to read first:**
- `docs/article/REVIEW/APPROACH_RIGOR.md` §1 — candidates, the interpretation
  contract, the capability-matrix row
- `src/isalhg/metric_space/` distances + registry — the pattern to follow (one
  more `D_rep`, cached as `D.npy` like every competitor)
- `docs/article/COMPETITORS.md` — where the baseline gets its one-paragraph
  entry
- `.claude/rules/coding_rules.md` — always
**Description:** Implement the naive structural baseline: **degree-sequence L1**
— L1 distance between sorted primal-degree sequences, zero-padded to equal
length. Register it as a distance alongside the five competitors so it flows
through every comparison surface (geometry table, A2, A3, A4 capability row,
real-data exhibit) via the standard `D.npy` cache path. Write the
interpretation contract into `COMPETITORS.md` *before* any result is seen (both
outcomes reported plainly; neither suppressed). Add its capability-matrix row
values to `REVIEW/CAPABILITY_MATRIX.md` (complete ✗, metric ✓, decodable ✗,
navigable —, scales ✓).
**Acceptance:** distance registered with unit tests (metric axioms on small
fixtures — non-negativity, symmetry, triangle on a pinned triple, and
`d = 0` for isomorphic pairs with equal degree sequences; plus a pinned
non-isomorphic degree-equal pair showing `d = 0` — the incompleteness witness,
documented); produces a `D.npy` on `planted_main` in the existing pipeline
without code changes elsewhere; `COMPETITORS.md` carries the entry + the
interpretation contract; `REVIEW/CAPABILITY_MATRIX.md` row added.
**Out of scope here:** running the full comparisons (T-M7d does that with the
harness); the alternative naive candidates (size signature, incidence-Jaccard)
— one primary baseline only, per the REVIEW decision.
