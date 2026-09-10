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

---

## 2026-09-11 — the deferral mechanism, measured (and two of my explanations withdrawn)

Job 2273337 finished. **574 units deferred**, and the cause is neither of the two
things I wrote earlier.

### The cause: the deadline is measured from SUBMIT, not from task start

| task | started | delay after submit (15:56) | deferred |
|---|---|---|---|
| 0, 1, 2 | 15:58–16:04 | ~0 h | **0** |
| 3 | 20:00 | 4 h 04 | 42 |
| 4, 5 | 20:18 | 4 h 22 | 47, 47 |
| 6 | 23:30 | 7 h 34 | **146** |
| 7, 8 | 23:33 | 7 h 37 | **146, 146** |

**Perfectly monotonic in start delay.** `common.sh:128` reads
`TKDE_START_TIME="${TKDE_START_TIME:-$(date +%s)}"` — it **inherits** an existing
value, and the launcher exports the submitting shell's environment. So every
array task computes `DEADLINE = TKDE_START_TIME + WALL_S − TEARDOWN_S`
(`rq4_worker.sh:68`) from the **array's submission time**. A throttled task that
starts 7½ h late gets ~0 usable wall and defers everything after its first unit.

**This is a distinct defect from this task's subject** (no idempotent skip) and
it is the *proximate* cause of the deferrals; the missing skip is what makes them
unrecoverable.

### WITHDRAWN, again: "deferral tracks per-unit cost"

That premise was mine, and `[IsalHG-Fable]` built the validity argument on it —
that the deferred set is the *expensive* half, correlated with corruption
detectability. **It is not**: deferral tracks *start delay*, and within a task it
truncates a contiguous slice. Cost is not the selector.

(My earlier "no bundle size fixes it" was withdrawn before this for the same
reason — an unmeasured causal claim. This is the second explanation of the same
observation that I asserted and had to retract.)

### What is actually missing — measured, not explained

Slices are **seed-major**: 27 seeds × 49 units = 1,323. But the loss is **not**
clean whole seeds either:

| | |
|---|---|
| distinct seeds with any rows | **26 of 27** |
| seeds with the **full 49** units | **7** |
| seeds with 45–47 units | most of the remainder |
| seeds with **2** units | **3** (40014, 40017, 40025) |
| total rows | 1,106 of 1,323 — **217 missing** |

So the missing set is *ragged*: three nearly-empty seeds from the late tasks, plus
one to four units absent from most other seeds. **The second component could
still be cost-selected** — those are units missing from otherwise-complete seeds —
and nothing measured so far decides that.

**I am not offering a third explanation.** The analysis obligation already in
this task stands and is now the way to settle it: report the missing set's
`(m, max arity, |Aut|)` profile beside the censored set, and let the profile say
whether it is random. Three explanations in twenty minutes is the signal to stop
theorising and measure the thing the obligation already asks for.

## The profile obligation, discharged: the missing set is NOT random

RQ4's array is complete (9/9), so the missing set is final at **217 units**.
Profiled by cell — each `(collection, corruption kind)` should appear once per
seed, i.e. **27 times**:

**Baseline:** 43 of the 49 cells are missing **exactly 4** (23 of 27) — the
uniform loss of ~4 seeds to the late tasks (T-KBv). That component *is* flat.

**Six cells deviate, and the deviation is structured:**

| cell | present | missing |
|---|---|---|
| `wd50k66_Q3624078__iso_twin_b1` | 13 | **14** |
| `wd50k66_Q202866__iso_twin_b1` | 14 | **13** |
| `wd50k66_Q1549591__iso_twin_b1` | 19 | **8** |
| `wd50k66_Q5398426__iso_twin_b1` | 19 | **8** |
| `ndc_classes__spurious_fact_b1` | 26 | 1 |
| `ndc_classes__spurious_fact_b2` | 26 | 1 |

**Every over-loss cell is `iso_twin_b1`** — four of the seven collections carry
excess loss on that corruption kind and nothing else does. Excess over the
baseline-4 totals **27 units**, all of it `iso_twin`.

**This is the validity concern, confirmed — by corruption kind rather than by
cost.** `iso_twin` is the corruption an isomorphism-complete representation
should detect *best*; it is the discriminating case for RQ4's claim, and it is
the cell the campaign is missing most of. A detection score computed over the
survivors is computed over a sample **depleted in exactly the corruption type
that most favours the paper's method.**

**Consequences, and none of them is a fourth explanation of the cause:**

1. The AUC **carries the caveat**, per L15 and the obligation as written: the
   missing count is reported **per cell**, not pooled, so the `iso_twin`
   depletion is visible rather than averaged away.
2. The direction is **against** the paper on its face — fewer `iso_twin` units
   means less of the case the method wins — but it is a *sampling* change, not a
   measured effect, and must not be reported as either a penalty or a bonus.
3. Whether the `iso_twin` excess is cost-driven (those units are the expensive
   ones and hit budgets) or deadline-driven is **not established**, and this task
   does not need it to be: the reporting obligation is discharged by the profile
   itself.

---

## 2026-09-11 — this task's title is wrong: the skip EXISTS and is inert

RQ4 **does** have an idempotent skip, and it has had one since the runner's first
commit (`c83d212`):

```python
if not args.force and _unit_done(rows_paths, unit):
    logger.info("unit %d (%s) already done; skipping", unit_index, unit.unit_id)
```

**It fired zero times across all nine tasks of job 2273337.** Not rarely — never.

The reason is the same class as everything else tonight: `_unit_done` checks
`rows_paths.dir / f"rows_auc__{unit.unit_id}.csv"`, and the worker runs with
`--out "${OUT_DIR}"` where `OUT_DIR` is **node-local staging**, confirmed from
the live log: `out=/localscratch/users/mpascual/2279519_6/out`. That directory is
per-task and starts empty, and results are copied to the durable root only at
teardown. **So the predicate is evaluated against a directory that cannot contain
prior results.** A correct operation on the wrong object, for the fourth time
today.

**So the observation that opened this task is right and its diagnosis is wrong.**
Resubmission genuinely does not advance — but not because no skip exists. It is
because the skip is asked a question the staging directory can never answer yes
to.

**The fix changes accordingly:** point the skip at the **durable results root**,
not at `--out`. That is a smaller change than writing a resume, and it makes the
existing `--force` flag meaningful (today it guards a branch that is already
always taken).

**Relationship to T-KBv.** Two independent defects, both required for the
observed damage:

| defect | effect |
|---|---|
| **T-KBv** — deadline from the array's submit time | late tasks defer everything after their first unit |
| **this task** — skip evaluated against empty staging | a resubmission re-runs the reachable prefix instead of advancing past it |

Fixing either alone leaves RQ4 incomplete: without T-KBv late tasks still defer;
without this, a resubmission still cannot reach what they deferred.

### The skip predicate must be "a complete, valid row", not "a file exists"

Raised by `[IsalHG-Fable]` against the obvious fix. Pointing `_unit_done` at the
durable root is necessary but not sufficient: a teardown interrupted mid-copy
leaves a **truncated file**, which a presence check treats as done **forever**.
The unit then becomes permanently unreachable by any number of resubmissions —
**the same failure this task documents, arriving from the other direction.**

So the predicate reads the file and requires a complete, valid row set, not
`Path.exists()`. This is the count-versus-liveness distinction again: **a file's
existence is not evidence that the work behind it finished.**

### The restore is the acceptance test for this task and T-KBv

The `iso_twin` re-run has to happen anyway, so it costs nothing to adopt as the
criterion, and it is sharper than what either task carries today:

> Resubmitting the `iso_twin` cells through the **ordinary launcher** must touch
> **exactly** the missing units and nothing else.
> **If it re-runs units that already have rows, the skip fix is wrong. If late
> tasks still defer, the deadline fix (T-KBv) is wrong.**

### Why the restore waits on the fixes rather than merely may

The restored units **must come from the same code path as the surviving 1,106.**
Hand-built `--unit` invocations routed around two unfixed defects use a different
entry point, different deadline handling and different skip behaviour — they
would produce units of **unknown comparability inside the one cell whose
comparability carries RQ4's claim.**

That is this session's own lesson in its exact form: *a reproduction that does
not reproduce the configuration is not a reproduction*, which already cost a
WD50K number faithful to a pipeline nobody runs. **This is a stronger reason to
wait than the hour was.**

### On this task's title

Left as written. "RQ4 has no resume" names a fix that was never the fix — the
observation was right and the diagnosis wrong — and the ledger should **show**
that pattern rather than hide it behind a rename.
