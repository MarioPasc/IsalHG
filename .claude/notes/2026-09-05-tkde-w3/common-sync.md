# `common-sync` — post-wave consolidation, wave `2026-09-05-tkde-w3`

## Identity

| Field | Value |
|---|---|
| Agent | `common-sync` (post-wave consolidation) |
| Orchestrator | `main` |
| Worktree | `/home/mpascual/research/code/IsalHG/.claude/worktrees/agent-a4654a7c8320da94d` |
| BASE_SHA | `21da071e9cc7333fbb61550fc690c644c3fa2893` (`merge(hpd-fix): size the HPD portrait k-axis for single-hyperedge inputs`) |
| Branch | `integration/2026-09-05-tkde-w1` |
| Conda env | none needed — shell and Markdown only, no pytest run |

## Plan

1. Move `tkde_run_synced` from the eight workers into `common.sh`, body
   byte-identical, keeping the rationale comment in one place.
2. Replace the false PYTHONPATH claim in `common.sh` with the PEP 660 truth
   and its operational consequence.
3. Document the matrices-root contract in `slurm/tkde/README.md`, after
   reading what the copy-back actually does with the stage-root symlink.
4. Document run tags, smoke staging, purged job dependencies, memory sizing
   and the wave-3 job table in `README.md` / `PICASSO.md`.
5. `bash -n` everything; run a local functional probe of the centralised
   helper under a real SIGTERM.
6. Two conventional commits + this log.

## Changes

### 1. `tkde_run_synced` centralised

The helper existed **eight times**, once per worker (`matrices`, `rq1`–`rq7`),
with identical bodies and eight differently-worded rationale comments. It now
lives once in `slurm/tkde/common.sh` (line 264), between `tkde_sync_partial`
and `tkde_job_footer`, with the merged rationale: bash defers EXIT/TERM traps
while it waits on a foreground child; measured on job `2213210` (2026-09-05),
where a `scancel` killed the step before `tkde_finalize` ran and fourteen
minutes of rows died on the node; backgrounding lets the trap fire and the
timed `tkde_sync_partial` bounds the loss to one `TKDE_SYNC_INTERVAL_S`
(default 300 s) while also making rows visible on HOME mid-run.

The function body is **unchanged** (`"$@" &`, `kill -0` poll with
`sleep "${TKDE_SYNC_INTERVAL_S:-300}"`, `wait` capturing status, final
`tkde_sync_partial`, `return "${status}"`), so no worker changes behaviour.
`common.sh`'s header "Functions:" list gained the entry.

Each worker keeps only the sentence that is specific to it — RQ1's expected
censored-tail TIMEOUT, RQ2's 600 s oracle units plus census memory, RQ3's long
single-shard task, RQ4/RQ5's one long-lived memoizing process, matrices'
write-straight-to-HOME no-op sync. RQ6 and RQ7 had nothing worker-specific to
say, so their blocks went entirely.

**Source ordering verified**: every worker sources `common.sh` well before its
first call site — earliest source is `rq7_worker.sh:22`, earliest surviving
call is `rq7_worker.sh:75`; the latest source line is `matrices_worker.sh:65`
against its call at line 107.

### 2. PYTHONPATH comment corrected

The old comment claimed PYTHONPATH sits "ahead of the editable-install `.pth`
entry" and so keeps the Python half and the compiled half on one tree. That is
wrong for this layout. The editable install is a **PEP 660 meta-path finder**,
and finders run before path entries, so on the cluster `isalhg.*` always
resolves to the **shared** checkout `~/fscratch/repos/IsalHG-tkde` — the tree
`scripts/tkde/sync_to_picasso.sh` targets — while `experiments.*` resolves from
`$REPO_DIR` on PYTHONPATH. Independently confirmed by
`experiments/tkde/rq1.py:215-219`, whose `deploy_stamps` docstring states the
same mechanism, and by `sync_to_picasso.sh:24,149`
(`REMOTE_REPO=…/repos/IsalHG-tkde`, assert `"IsalHG-tkde" in isalhg.__file__`).

The rewritten comment states the consequence: a change under `src/**` reaches
the cluster only through `sync_to_picasso.sh` (which also rebuilds the
extension), a private deployment moves `experiments/**` and `slurm/**` alone,
and the manifests record both trees as `src_deploy` and `runner_deploy`. The
`export PYTHONPATH=…` line itself is untouched.

### 3. Matrices-root contract — measured, not assumed

`slurm/tkde/README.md` gains a section. Both mechanisms are in use and both are
correct:

- **symlink** — `rq1_worker.sh:49`, `rq2_worker.sh:52`, `rq7_worker.sh:43`:
  `ln -sfn "${ISALHG_RESULTS_ROOT}/matrices" "${STAGE_ROOT}/matrices"`. rq2's
  `ndc_substances` census also *writes* through it into the shared cache. The
  smoke is the exception and gets `mkdir -p "${STAGE_ROOT}/matrices"` on the
  node (`rq2_worker.sh:50`).
- **flag** — `rq4_worker.sh:122,130` and `rq5_worker.sh:117,125`:
  `--matrices-root "${ISALHG_RESULTS_ROOT}"`, with `--out` still node-local.

**Actual copy-back behaviour with that symlink — no fix needed.**
`tkde_finalize` and `tkde_sync_partial` both mirror `${MYLOCALSCRATCH}/out/`
(`common.sh:215` and `:246`, `rsync -a "${MYLOCALSCRATCH}/out/" …`). The
workers set `STAGE_ROOT="${MYLOCALSCRATCH}/root"` — a **sibling** of `out/`,
not a parent and not a child. The `matrices` link therefore sits at
`${MYLOCALSCRATCH}/root/matrices`, outside the mirrored tree, and is never
walked. What *is* inside `STAGE_ROOT` and points into the mirrored tree is the
per-experiment link `${STAGE_ROOT}/<RQ>/<experiment>` → `$OUT_DIR`, which is
the intended arrangement. `common.sh` is left unmodified on this point; the
README instead records the invariant that must not be broken — mirroring
`STAGE_ROOT` instead of `out/` would rsync HOME's `matrices/` onto itself
through the link.

### 4. Documented facts (all verified in-repo before writing)

- **Run tags.** `rows_<table>__<8hex>-<unit>.csv`; tag from
  `experiments/tkde/rq1.py::run_tag` (sha1 of the config minus
  `OPERATIONAL_KEYS`, 8 hex chars). `analyze_rq1.py::load_table` skips a path
  with a `_smoke` component **or** one failing `_is_tagged`
  (`^[0-9a-f]{8}-`). `analyze_rq2.py:29` and `analyze_rq7.py:25` import that
  same `load_table`; RQ3/RQ4/RQ5 analyzers exclude by `_smoke` path only
  (`analyze_rq3.py::is_smoke_path`, `matrices.contains_smoke`). The README says
  exactly this rather than claiming all analyzers enforce the tag.
- **Smoke staging.** `rq2_worker.sh:32-33` —
  `STAGE_SUBDIR="${RQ_FOLDER}/_smoke/${EXPERIMENT}"` under `TKDE_SMOKE=1`,
  because `exact0-ndc_classes-fact_rank` is a unit id of both the smoke and the
  campaign.
- **Purged job records.** `--dependency=afterok:<purged id>` is rejected at
  submission (`Job dependency problem`); check `sacct -j <id>` first.
- **Memory.** `sacct -X` hides `MaxRSS` (recorded on `.batch`). Peaks:
  matrices job `2213202` 34.2 GB; RQ3+RQ6 bundle 20.4 GB, driven by RQ6 cache
  growth across the bundled units and fixed by refitting per unit.
- **Wave-3 job table** (PICASSO.md §6.2): RQ7 `2215078`, RQ2 main `2215097`,
  RQ2 census `2215136`, RQ1 `2215137`, RQ3+RQ6 `2215096`, RQ5 `2215162`,
  RQ4 `2215168`.

The README skeleton's payload line was also switched from a foreground
`"${PY}" -m … ; tkde_sync_partial` to `tkde_run_synced "${PY}" -m …`, so a new
worker copied from the template does not reintroduce the defect.

## Verification

### Grep proof — one definition, every worker still calls it

```
$ /usr/bin/grep -rn 'tkde_run_synced()' slurm/tkde/
slurm/tkde/common.sh:264:tkde_run_synced() {

$ /usr/bin/grep -cE '^[[:space:]]*tkde_run_synced "' slurm/tkde/*_worker.sh
slurm/tkde/matrices_worker.sh:1
slurm/tkde/rq1_worker.sh:1
slurm/tkde/rq2_worker.sh:1
slurm/tkde/rq3_worker.sh:2
slurm/tkde/rq4_worker.sh:2
slurm/tkde/rq5_worker.sh:2
slurm/tkde/rq6_worker.sh:1
slurm/tkde/rq7_worker.sh:1
```

11 call sites, matching the 11 counted before the refactor.

### `bash -n`

All 19 files under `slurm/tkde/` (`common.sh`, 8 launchers, 9 workers,
`smoke_*`) parse clean:

```
$ bash -n slurm/tkde/common.sh; bash -n slurm/tkde/matrices_launcher.sh; … ; \
  echo "ALL 19 FILES: bash -n clean"
ALL 19 FILES: bash -n clean
```

### Functional probe of the centralised helper

`common.sh` **cannot** be sourced with a bare environment: it hard-exits at
line 60 unless `${TKDE_CONDA_PREFIX}/bin/python` is executable. The probe
therefore sets exactly one thing — `TKDE_CONDA_PREFIX` at a scratch directory
whose `bin/python` is a symlink to `/usr/bin/env` — plus `ISALHG_RESULTS_ROOT`
and `TMPDIR` so the staging has somewhere to go. Everything else (the module
loop, the conda activate, the pycache prefix) degrades silently as designed.

The probe sources the real `common.sh`, stubs `tkde_sync_partial` /
`tkde_finalize` to print a timestamped marker, calls the real
`tkde_stage_localscratch` (so the real EXIT/TERM/INT traps are installed), sets
`TKDE_SYNC_INTERVAL_S=1`, starts a 30 s payload, and takes a `kill -TERM` two
seconds in. Both arms run: through `tkde_run_synced`, and in the foreground for
contrast.

Scripts: `scratchpad/probe_outer.sh`, `scratchpad/probe_inner.sh` (session
scratchpad, not committed).

```
================ arm: synced ================
[warn] LOCALSCRATCH unavailable; staging under …/results_synced/tmp
[stage] node scratch : …/results_synced/tmp/mpascual/local_0/out
[stage] copy-back to : …/results_synced/probe
arm=synced: starting 30 s payload
MARKER copy-back fired (t=1s)
>>> kill -TERM 196992 (payload still running)
MARKER finalize fired   (t=2s)
<<< inner shell exit status: 143

================ arm: foreground ================
[warn] LOCALSCRATCH unavailable; staging under …/results_foreground/tmp
[stage] node scratch : …/results_foreground/tmp/mpascual/local_0/out
[stage] copy-back to : …/results_foreground/probe
arm=foreground: starting 30 s payload
>>> kill -TERM 197049 (payload still running)
MARKER finalize fired   (t=30s)
<<< inner shell exit status: 143
```

Read: with `tkde_run_synced`, the periodic copy-back fires at t = 1 s and the
TERM-driven finalize at t = 2 s, immediately on the signal. In the foreground
arm the identical trap is deferred for the **full 30 s** of the payload — on
Picasso, SIGKILL arrives after `KillWait` and the trap never runs at all. That
is the 2213210 failure, reproduced locally, and the fix confirmed.

No pytest run: nothing under `src/**`, `experiments/**`, `scripts/**` or
`tests/**` was touched.

## Deliberately not done

- **No behaviour change to any payload.** The function body was copied
  verbatim; the diff is comment prose plus the move.
- **`common.sh` copy-back left alone.** The stage-root symlink is outside the
  mirrored tree (see §3), so there is nothing to fix; the invariant is recorded
  in the README instead of being enforced by a new guard.
- **No shellcheck run.** Not installed here, and not part of the brief.
- **`smoke_worker.sh` untouched.** It never had a copy of the helper and its
  payload is the pytest suite, not a unit loop.
- **PICASSO.md §4 untouched** beyond the new §6.2, even though it discusses the
  editable install: the brief scoped the PEP 660 correction to `common.sh`.
- **No push, rebase or merge; no Picasso contact.**

## Risks / notes for the orchestrator

- `tkde_run_synced` is now part of the frozen `common.sh` contract. Per
  PICASSO.md, **any change to `common.sh` requires re-running the smoke job**
  before the next campaign submission. This change qualifies.
- The helper's `local` keyword means it must stay a function in a sourced
  file — it cannot be inlined into a `bash -c` payload.
- `TKDE_SYNC_INTERVAL_S` is read at call time, so a worker may still override
  it per payload; nothing in the tree does today.
- A worker that overrides `tkde_sync_partial` after sourcing would change what
  `tkde_run_synced` does. None does; worth knowing if one ever needs to.
