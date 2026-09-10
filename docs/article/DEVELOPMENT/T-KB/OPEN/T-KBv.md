# T-KBv — the start-cutoff deadline is measured from submit, not from task start
**Declared:** 2026-09-11 00:15 CEST
**Status:** OPEN
**Delegation:** agent
**Why out of scope:** found while auditing RQ4's deferrals under T-KBq. It is the
*proximate* cause of those deferrals; T-KBq's subject (no idempotent skip) is
what makes them unrecoverable. Two separate defects.

**Context to read first:**
- `slurm/tkde/common.sh:128` — `TKDE_START_TIME="${TKDE_START_TIME:-$(date +%s)}"`
- `slurm/tkde/rq4_launcher.sh:30` — `source .../common.sh`, and line 91's `--export=ALL`
- `slurm/tkde/rq4_worker.sh:68` — `DEADLINE=$(( TKDE_START_TIME + WALL_S - TEARDOWN_S ))`
- `experiments/tkde/rq4.py:1576` — the start-cutoff branch
- `docs/article/DEVELOPMENT/T-KB/OPEN/T-KBq.md` §2026-09-11

**Description.** `common.sh` **inherits** `TKDE_START_TIME` when it is already
set. `rq4_launcher.sh` **sources `common.sh`** (for `PY`), which sets that
variable in the launcher's own shell, and then submits with `--export=ALL`. So
every array task inherits the **array's submission time** and computes its
deadline from it, rather than from when the task actually started.

A throttled task that starts late therefore gets a correspondingly shortened
usable wall. Measured on job 2273337 — **perfectly monotonic in start delay**:

| task | started | delay after submit (15:56) | deferred |
|---|---|---|---|
| 0, 1, 2 | 15:58–16:04 | ~0 h | **0** |
| 3 | 20:00 | 4 h 04 | 42 |
| 4, 5 | 20:18 | 4 h 22 | 47, 47 |
| 6, 7, 8 | 23:30–23:33 | ~7 h 35 | **146 each** |

574 units deferred; 217 units have no row at all.

**Scope — audited, and it is only RQ4.** The inheritance requires the *launcher*
to source `common.sh`:

| launcher | sources `common.sh` | affected |
|---|---|---|
| **rq4** | **yes (line 30)** | **YES** |
| rq7 | no | no |
| rq6 | no | no |
| rq3 | no | no |
| tail600 | no | no |

Every other worker sets `TKDE_START_TIME` itself when it sources `common.sh`
on the node, which is the intended behaviour. **tail600 confirms this
empirically**: submitted 21:11, its latest tasks started 22:22, and it still
produced **130 of 130** calls.

**Censoring counts are NOT affected — checked, because this reaches the census.**
A past-deadline unit is **deferred, never run on a trimmed budget**;
`rq4.py:1576` says so in as many words: *"Refuse to START a unit whose full
budget no longer fits inside the wall, and **NEVER trim its budget to make it
fit**: a unit that got a fraction of its time is not comparable with its paired
units."* So truncation produces **no row**, not a censored row, and censoring
counts are not a function of queue position. **The M3 census (77 / 53) and
D-ART5's R2 sentence are safe from this mechanism**, and T-KBu's
"exceeded the budget" vs "never got the budget" collapse does **not** arrive by
this second route.

**Acceptance:**
1. Each array task computes its deadline from **its own start**. Either
   `common.sh` stops honouring an inherited value (`TKDE_START_TIME=$(date +%s)`
   unconditionally on the node), or the launchers stop exporting it —
   whichever keeps the single-task and multi-task paths identical.
2. A test asserts that two tasks of the same array starting an hour apart compute
   deadlines an hour apart.
3. The other four launchers are left alone; they are correct today **by accident
   of not sourcing `common.sh`**, so the fix must not depend on that.

**Out of scope here:** the missing idempotent skip (T-KBq); whether the deferred
set is cost-biased (T-KBq's profile obligation); re-running RQ4.
