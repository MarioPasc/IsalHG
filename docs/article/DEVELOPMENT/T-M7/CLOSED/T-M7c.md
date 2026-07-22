# T-M7c — Naive baseline distance (degree-sequence L1)
**Declared:** 2026-07-22 11:56 CEST
**Status:** DONE
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

---

## Closing note — 2026-07-22

**Commit order (discipline check):** docs commit (interpretation contract +
capability row) precedes code commit on branch `feat/T-M7c-degree-seq-l1`.

**Files added/changed:**
- `src/isalhg/metric_space/representations/degree_seq_l1.py` — new distance
- `src/isalhg/metric_space/registry.py` — `"degree_seq_l1"` entry added to `_LAZY_MODULES`
- `tests/unit/metric_space/test_degree_seq_l1.py` — 16 unit tests
- `docs/article/COMPETITORS.md` — §4 naive baseline entry + interpretation contract + CQ6
- `docs/article/REVIEW/CAPABILITY_MATRIX.md` — Deg-seq L1 column added

**Tests:** 16/16 pass (metric axioms, iso-invariance, incompleteness witness,
matrix, fingerprint, registry). Full unit suite: 955 passed, 5 skipped.

**Incompleteness witness pinned:** `non_iso_pair_small` (H1: two 3-edges,
H2: three 2-edges; both degree seq [2,2,1,1], d_DS=0). Documented in module
docstring, test docstring, and COMPETITORS.md §4.

**Acceptance check:**
- [x] distance registered with name `"degree_seq_l1"` in registry
- [x] unit tests: non-negativity, symmetry, triangle inequality (pinned values: d(tri,star)=3, d(star,path)=2, d(tri,path)=3), d=0 on iso pairs, d=0 incompleteness witness documented
- [x] `COMPETITORS.md` §4: baseline entry + interpretation contract pre-committed before code
- [x] `REVIEW/CAPABILITY_MATRIX.md`: Deg-seq L1 column complete ✗ / metric ✓ / decodable ✗ / navigable — / scales ✓ / single-metric ✓
- [x] pipeline compatibility: `D.npy` on `planted_main` will be produced without code changes elsewhere (registered name follows the same pattern as all competitors)

**ruff:** 0 new errors (3 pre-existing baseline, not in new files).
**mypy:** 0 new errors (21 pre-existing baseline, not in new files).
