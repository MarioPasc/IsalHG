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

### WITHDRAWN: "no choice of bundle size fixes it"

That claim, written above an hour earlier, was **asserted without measurement**
and is wrong. `[IsalHG-Fable]` challenged it; measured from the row files:

| per-unit cost, 1,106 completed units | |
|---|---|
| median | 4.3 s |
| mean | 62.7 s |
| p90 / p99 | 221.3 s / **271.1 s** |
| max | **513.2 s** |

| bundle | slice cost at p99 | fits the 8 h wall? |
|---|---|---|
| **147** (current) | **11.07 h** | **no** — this is the deferral |
| 100 | 7.53 h | yes |
| 75 | 5.65 h | yes, with margin |
| 50 | 3.77 h | yes |

**No single unit can exhaust the wall** (max 513 s ≈ 8.5 min), so nothing
structurally defeats a resize. A bundle of 75 would fit at p99 with 2.3 h spare.

**But the estimate is from a biased sample, and the bias runs the wrong way.**
These are the *completed* units. Deferral tracks per-unit cost, so the deferred
217 are disproportionately the expensive ones and the true p99 is **higher than
271 s**. A bundle chosen from this distribution is chosen from the cheap half.

**The resume remains the fix, for a better reason than the one I gave.** Not
because a resize cannot work — it can — but because a resize requires guessing a
bundle against a distribution we cannot observe without first completing the
units we are trying to reach, and it costs a full re-run to use. The resume is
robust without guessing. The decisive argument is the one already in this task:
resubmission restarts each task at the head of its slice and defers the same
tail, so the deferred units are unreachable by any number of resubmissions.

### The deferred set is a VALIDITY problem, not only a throughput one

Raised by `[IsalHG-Fable]`, and it reframes this task. Deferral tracks per-unit
cost; cost tracks size, arity and symmetry; and in RQ4 those are the same
properties that decide **how detectable a structural corruption is**. So a screen
analysed with 217 units absent is not analysed on a random subsample — it is
analysed on the **cheap half**, conditioned on a property correlated with the
thing being measured.

This is L15's clause arriving by a second route: the earlier concern was
censoring correlated with the corrupted-vs-clean label; this is the same defect
produced by wall-clock **deferral** instead of a per-unit budget.

**Analysis obligation, whatever is done about completing the run:** the deferred
set is reported with its `(m, max arity, |Aut|)` profile beside the censored set,
and if that profile is non-random the AUC carries the caveat. **Deferral must not
enter the pipeline as absence** — it is a third variety of the state that looks
like nothing happened, alongside `censored` (T-KBu) and a blank column.
