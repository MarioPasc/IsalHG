# T-KBq — RQ4 has no resume, so a deferred unit is never reached by resubmission
**Declared:** 2026-09-10 16:00 CEST
**Status:** OPEN
**Delegation:** agent
**Why out of scope:** found while completing RQ4 under T-KBf. Worked around by
re-bundling (job 2273337, `RQ4_BUNDLE=150` → 9 tasks), so it does not block the
campaign; the runner defect remains.

**Context to read first:**
- `slurm/tkde/rq4_launcher.sh:71` — `BUNDLE="${RQ4_BUNDLE:-441}"` and
  `N_TASKS = ceil(N_UNITS / BUNDLE)`
- `experiments/tkde/rq4.py` — the unit loop and the start-cutoff; `n_skipped`
  counts *members* skipped inside a unit, not units already done
- `experiments/tkde/rq3.py::_done_units` — the pattern RQ4 lacks (and whose own
  defect is T-KBn: it keys on untagged aggregates)
- `docs/article/DEVELOPMENT/T-KB/IN-PROGRESS/T-KBf.md` §"The RQ4 smoke is a
  structurally invalid gate" — why one unit is expensive and the rest are cheap
- `.claude/rules/coding_rules.md` §5.2 "Idempotent runs"

**Description:** RQ4's start-cutoff correctly **defers** a unit whose full
budget no longer fits the wall rather than trimming it, and reports the deferred
list. But the runner has no idempotent skip: on the next submission each task
starts at the first unit of its slice again. Measured on job 2269721, the
continuation of 2267420:

| | first run (2267420) | continuation (2269721) |
|---|---|---|
| units run | 246 + 246 + 345 | 197 + 197 + 207 |
| `rows_auc` files after | 819 | **819 — unchanged** |
| deferred | 195 + 96 + … | 234 |

So the continuation re-ran the same prefix and the deferred units were never
reached. Resubmission alone can never complete RQ4.

`coding_rules.md` §5.2 states the convention the runner is missing: *"The
orchestrator skips cells whose result JSON already exists and JSON-validates."*
RQ2, RQ5, RQ6 and RQ7 are not affected in the same way — they complete inside
their walls — but none of them skips either, so the same trap is waiting for any
of them whose cost grows.

**Workaround in force:** `RQ4_BUNDLE=150` gives 9 tasks of 150 units, and ~200
units per task is achievable in the 8 h wall, so every unit falls inside some
task's reachable prefix. Job 2273337.

**Acceptance:** RQ4 skips a unit whose rows already exist and validate, so a
resubmission advances rather than repeats; a test writes rows for a unit, re-runs
the shard, and asserts the unit is skipped and the next one runs; the deferred
list from a previous run is honoured on resume. Do **not** copy RQ3's
`_done_units` verbatim — it keys on untagged aggregates and is itself defective
(T-KBn); key on the per-unit row files RQ4 already writes.

**Out of scope here:** the start-cutoff itself, which is correct and must not
start a unit it cannot finish; the word-path memoisation; RQ3's own skip defect
(T-KBn).

---

## Measured on job 2273337 (the `RQ4_BUNDLE=150` workaround), 2026-09-10 23:35

**The workaround is not sufficient.** It was sized on "~200 units per task
achievable in the 8 h wall", so that every unit would fall inside some task's
reachable prefix. Measured, the first three tasks clear their slice and the next
three do not:

| task | units in slice | deferred by the start-cutoff |
|---|---|---|
| 0, 1, 2 | 147 each | **0** |
| 3 | 147 | **42** |
| 4 | 147 | **47** |
| 5 | 147 | **47** |
| 6, 7, 8 | 147 each | still running |

**1,323 units total; 1,106 per-unit row files exist** (`IEEETKDE_isal/RQ4_screen/
rows/`, the union of every RQ4 job so far, since the runner overwrites by unit
name). **217 units have never produced a row**, and 136 of them were deferred by
this job alone.

Because the runner has no idempotent skip (this task's subject), those deferred
units are **not reachable by resubmission**: the next job starts each task at the
first unit of its slice again and will defer the same tail. The bundle size
changes which units are deferred, not whether some are.

**Consequence for the acceptance:** a resume is not an optimisation here, it is
the only way RQ4 completes. Sizing the bundle differently cannot fix it, because
the deferral is caused by per-unit cost variance within a slice rather than by
the slice being too long on average — tasks 0–2 finished 147 units in the same
wall in which tasks 3–5 managed ~105.
