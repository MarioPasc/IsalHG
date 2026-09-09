# T-KBn — RQ3's idempotent skip serves stale rows under a changed arm set
**Declared:** 2026-09-09 13:00 CEST
**Status:** OPEN
**Delegation:** agent
**Why out of scope:** caught by the D-ART4 note (b) RQ3 pilot during T-KBf's
submission run. Worked around operationally (the campaign runs into a clean
results root), so it does not block RQ3–RQ7; the runner defect itself remains.

**Context to read first:**
- `experiments/tkde/rq3.py::_done_units` and its call in `run_shard`
  (`rows_variants.csv` / `rows_natural.csv` are read to decide what to skip)
- `experiments/tkde/rq3.py::write_rows` call sites — the tables are aggregated
  under a **fixed, untagged** name, unlike RQ2's `rows_census__<tag>-<unit>.csv`
- `experiments/tkde/rq1.py::run_tag` — the tag RQ2 and RQ7 use and RQ3 does not
- `docs/article/DEVELOPMENT/T-KB/OPEN/T-KBh.md` — the analyzers pooling launch
  tags; this is the same disease one level earlier, in the *runner*
- `docs/article/DEVELOPMENT/T-KB/IN-PROGRESS/T-KBe.md` §"Defect 1" — the
  2,506,837-row double count from two campaigns in one directory
- `.claude/rules/coding_rules.md` — always

**Description:** RQ3 decides which units to skip by reading its own aggregated,
**untagged** row files. When the arm set changes, every unit is still "done", so
the runner skips all of them, re-aggregates the previous campaign's rows, and
writes a **fresh `config.json` advertising the new arms beside rows that contain
none of them**. Measured 2026-09-09 on the pilot (job 2265308):

| | cluster pilot (dirty tree) | fresh local run |
|---|---|---|
| rows | 44 variants / 20 natural | **58 / 27** |
| wall-clock | 0.3 s | **80 s** |
| `wstar_orbit` rows | **0** | present (matrix n=20, 1.32 s) |
| `nauty_cert_rows`, `bipartite_ged_assign` | **0** | present |
| `config.json` `medoid_arms` | the **new** 11-arm list | the new list |

So the config claimed the paper's representation was measured and the rows
contained no such arm. On the real `RQ3_representative/` tree — 49,027 rows from
2026-09-05, pre-D-ART5 arm set — the full RQ3 would have produced a complete,
plausible table **with no Isal row at all**.

RQ4, RQ5, RQ6 and RQ7 do **not** use `_done_units` and so do not serve stale
rows; RQ4/RQ5/RQ6 do not tag either, so they would instead *overwrite* the
pre-D-ART5 rows that D-ART4 (1) requires be kept ("nothing on disk is deleted;
`results/IEEETKDE/` keeps every row as the record").

**Workaround in force (not a fix):** the D-ART5 campaign runs into a clean root
`~/results/IEEETKDE_isal/`, with `matrices` symlinked to the shared build, which
follows the RQ1 Isal campaign's own precedent (`results/IEEETKDE_isal/
RQ1_addressing/`). Job 2265353 is the first RQ3 under it.

**Acceptance:** RQ3's row files carry the launch tag as RQ2's do, so a new
launch cannot be skipped as an old one; `_done_units` keys on `(tag, unit)`;
a test writes rows under one arm set, re-runs under a different one, and asserts
the new arms are computed rather than skipped; and a run whose persisted
`config.json` names an arm absent from its rows fails a self-check rather than
being written.

**Out of scope here:** the analyzers' tag pooling (T-KBh); moving or deleting
any pre-D-ART5 rows; RQ2's layout, which is already tagged and correct.
