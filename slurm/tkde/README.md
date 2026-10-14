# `slurm/tkde/` — the TKDE campaign's SLURM layer

Every IEEE TKDE experiment runs on Picasso through this directory. `common.sh`
is the frozen contract: a worker sources it and gets the interpreter, the paths,
the thread settings, the job banner, and `$LOCALSCRATCH` staging with a
copy-back that cannot silently lose a file.

The measured cluster facts behind every rule here — node families, the AVX-512
trap, quota headroom, package versions, the smoke job — are in
[`docs/article/D_ART3/experiments/PICASSO.md`](../../docs/article/D_ART3/experiments/PICASSO.md).
Read that before changing anything in this directory.

---

## Before you write a launcher

1. **The environment already exists.** Do not create an env, do not `pip
   install`, do not rebuild the extension. `scripts/tkde/picasso_env_setup.sh`
   owns that, and `scripts/tkde/sync_to_picasso.sh` re-runs the build after
   every merged wave.
2. **Read the live cluster state.** Quota headroom is account state, not a
   constant, and this account is close to its FSCRATCH file limit:

   ```bash
   ssh picasso 'quota'                                   # space AND file count
   ssh picasso 'cd <your output dir> && count_files'
   ssh picasso 'squeue'                                  # -u is REJECTED by the Lua wrapper
   ```

   Compare `N_tasks × (artefacts_per_task + 2 log files)` against the headroom
   *before* submitting. A hard file quota blocks writes mid-campaign while every
   task keeps burning wallclock.
3. **`sbatch --test-only` first, then one real task, then the array.** Passing
   environment self-checks is not evidence a job will run.

---

## Minimal launcher / worker skeleton

### `rqN_worker.sh`

```bash
#!/usr/bin/env bash
# Submit via rqN_launcher.sh. Do NOT submit directly.

#SBATCH --job-name=tkde-rqN
#SBATCH --time=0-06:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --constraint=sd
#SBATCH --account=tic_163_uma

set -euo pipefail

: "${REPO_DIR:?REPO_DIR not set -- submit via rqN_launcher.sh}"
# shellcheck source=/dev/null
source "${REPO_DIR}/slurm/tkde/common.sh"

tkde_job_header "tkde-rqN"
tkde_stage_localscratch "RQN_<name>"       # -> $ISALHG_RESULTS_ROOT/RQN_<name>/
cd "${REPO_DIR}"

# Decode the flat array index into your grid, and ECHO IT.
# A silently wrong decode produces a complete, plausible, WRONG result set.
TASK_IDX="${SLURM_ARRAY_TASK_ID:-0}"
Q=$(( N_UNITS / N_TASKS )); R=$(( N_UNITS % N_TASKS )); I="${TASK_IDX}"
LO=$(( I * Q + (I < R ? I : R) )); HI=$(( LO + Q + (I < R ? 1 : 0) ))
echo "Task ${TASK_IDX} -> units [${LO}, ${HI})"

for (( U = LO; U < HI; U++ )); do
    # Start-cutoff: refuse to START a unit whose full budget no longer fits.
    # The FIRST unit is exempt -- without that exemption a task whose start-up
    # alone exceeds the cutoff defers its whole chunk, the sweep re-derives the
    # same chunk and defers it again, and the array LIVELOCKS.
    ELAPSED=$(( $(date +%s) - TKDE_START_TIME ))
    if (( U > LO && ELAPSED >= START_CUTOFF_S )); then
        echo "DEFERRED: unit ${U}"; continue
    fi
    # NEVER trim a late unit's budget to make it fit -- defer it. A unit that
    # got 1 h instead of 6 h is not comparable with its paired units, and if
    # wall-clock is reported you have silently corrupted the measurement.

    # NEVER run the payload in the foreground: bash defers the EXIT/TERM traps
    # while it waits on a foreground child, so a scancel or a TIMEOUT kills the
    # step with the copy-back never having run. tkde_run_synced backgrounds it
    # and syncs on a timer.
    tkde_run_synced "${PY}" -m experiments.tkde.rqN --unit "${U}" --out "${OUT_DIR}"
done

tkde_job_footer
```

### `rqN_launcher.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TKDE_USER_ROOT="/mnt/home/users/tic_163_uma/mpascual"
REPO_DIR="${REPO_DIR:-${TKDE_USER_ROOT}/fscratch/repos/IsalHG-tkde}"
LOGS_DIR="${TKDE_USER_ROOT}/execs/tkde/logs"
mkdir -p "${LOGS_DIR}"

# Picasso's Lua sbatch wrapper prepends ANSI codes and a multi-line warning to
# --parsable output. Take the LAST line FIRST: a line-by-line sed leaves the
# banner's newlines in place, and the numeric guard then fires AFTER the job was
# submitted -- leaving an untracked job running on the cluster.
_clean_job_id() {
    tail -n 1 <<<"$1" | sed -e 's/\x1b\[[0-9;]*[a-zA-Z]//g' -e 's/[^0-9]//g'
}
submit() {
    local raw id
    raw=$(sbatch --parsable "$@") || { echo "sbatch failed" >&2; return 1; }
    id=$(_clean_job_id "${raw}")
    [[ "${id}" =~ ^[0-9]+$ ]] || {
        echo "FATAL: unparsable job id: ${raw@Q}" >&2
        echo "Run squeue NOW -- the job may already exist." >&2
        return 1
    }
    echo "${id}"
}

# Size the array in TASKS, never in units, and derive the count from the
# decoder rather than hard-coding it: a hard-coded count cannot disagree with
# the decode, so it cannot catch a decode that changed.
N_UNITS=$("${PY}" -m experiments.tkde.rqN --count)
BUNDLE=12                                    # ceil(2h / per-unit time)
N_TASKS=$(( (N_UNITS + BUNDLE - 1) / BUNDLE ))
MAX_CONCURRENT=16

JOB_ID=$(submit \
    --array="0-$((N_TASKS - 1))%${MAX_CONCURRENT}" \
    --output="${LOGS_DIR}/tkde-rqN_%A_%a.out" \
    --error="${LOGS_DIR}/tkde-rqN_%A_%a.err" \
    --export="ALL,REPO_DIR=${REPO_DIR},N_UNITS=${N_UNITS},N_TASKS=${N_TASKS},START_CUTOFF_S=18000" \
    "${SCRIPT_DIR}/rqN_worker.sh") || exit 1
echo "Submitted ${JOB_ID} (${N_TASKS} tasks over ${N_UNITS} units)"
```

---

## The rules, and why each exists

### Every job header

`--account=tic_163_uma --constraint=sd`, explicit `--output`/`--error` under
`~/execs/tkde/logs` with `%A_%a`, a throttle `%K` on every array.

Use `%A_%a` for arrays and `%j` for a single job. On a **non**-array job `%a`
expands to SLURM's "no array task" sentinel `4294967294` — measured on smoke job
2210890, whose log landed at `tkde-smoke_2210890_4294967294.out`.

**`--constraint=sd` is not negotiable without a rebuild.** The C++ extension is
built on the login node (Xeon Gold 6230R, `sd` family, AVX-512) with the
project's `-march=native`. Array `2206615` pinned to `sr` (AMD EPYC, no
AVX-512) died with SIGILL on every task in 8 s. `sd` is the login node's own
family. Pinning also keeps every timing arm on one machine type — a mixed
Intel/AMD pool turns a wall-clock comparison into a measurement of the
scheduler. The `-march=haswell` → `--constraint=cpu` fallback is in `PICASSO.md`.

Picasso's `sbatch` wrapper prints a banner recommending `cpu`/`avx512` over
`sd`. Ignore it for this campaign; the reasoning above is measured, the banner
is generic.

### The 2 h floor, and bundling

**No submitted task may run under two hours** (SCBI, 2026-08-07: short jobs cost
the scheduler more to place than to run and saturate the queue for every user).
The smoke job is the single documented exception.

Keep the array topology and change what one *task* does: if a unit takes `T`,
put `B = ceil(2h / T)` units in each task and submit `ceil(N/B)` tasks. This is
makespan-neutral — an array of `N` units under throttle `K` finishes at `N·T/K`
either way — provided you keep at least `K` tasks after bundling (cap the
throttle at the post-bundling task count) and keep the last round's residue
small.

Split the units **evenly** (the `Q`/`R` form above), never in fixed blocks with
a ragged tail: the short remainder task is exactly what bundling is meant to
eliminate.

### The start-cutoff

`START_CUTOFF_S = wall − per_unit_budget − teardown`. Three rules, all
load-bearing:

- **Exempt the first unit** or the array livelocks (see the skeleton comment).
- **Never trim a late unit's budget** to make it fit — defer it.
- **Write results per unit**, so a node loss, a TIMEOUT or a deferral costs one
  unit and a resume pass skips what is done.

Submit the recovery sweep at launch time with `--dependency=afterany`, not by
hand. A recovery step that depends on someone remembering does not happen.

### Row files carry a run tag; smokes stage apart

A row file is named `rows_<table>__<8hex>-<unit>.csv`. The `8hex` prefix is
`experiments.tkde.rq1.run_tag(config)` — a hash of the parameters that decide
*what* a unit measures, with the distribution keys (`n_shards`, `smoke`)
excluded so re-sharding resumes a campaign instead of recomputing it. Without
the tag, two runs whose unit ids coincide but whose parameters differ are
indistinguishable on disk and the second inherits the first's rows.

`load_table` (`analyze_rq1.py`, shared by the RQ2 and RQ7 analyzers) skips **an
untagged file** and **any path with a `_smoke` component**. Both failure shapes
happened: a smoke staged into `_smoke/`, and untagged files left in the real
directory by the 2026-09-05 cluster smokes. The RQ3/RQ4/RQ5 analyzers exclude by
`_smoke` path only.

So: a smoke **must** stage under a `_smoke*` subtree
(`STAGE_SUBDIR="${RQ_FOLDER}/_smoke/${EXPERIMENT}"`), because it shares the
campaign's unit-id namespace — `exact0-ndc_classes-fact_rank` is a unit of both,
and five toy members would otherwise stand in for the corpus and mark the unit
done.

### Depending on a job that Slurm has already forgotten

Slurm purges job records after a while, and `--dependency=afterok:<old id>`
against a purged job is **rejected** with `Job dependency problem` — the
submission fails, it does not silently run. Confirm the record still exists
before depending on it:

```bash
sacct -j <ID> -n -X -o JobID,State     # empty output = purged, pick another anchor
```

### `$LOCALSCRATCH` staging

`tkde_stage_localscratch <subdir>` gives you `$OUT_DIR` on the node's local disk
and installs the copy-back. Write everything there; write nothing directly to
`$ISALHG_RESULTS_ROOT`.

- The copy-back **mirrors the whole `out/` tree** and never a list of expected
  files. A copy-back that names paths returns every file it named, so an
  artefact written at the root of the output tree vanishes and nothing looks
  wrong until the analysis needs it.
- `EXIT`, `TERM` **and** `INT` traps are installed. SLURM sends SIGTERM and
  waits `KillWait` before SIGKILL; without the `TERM` trap a wall-clock kill
  runs no EXIT trap and the whole task's output dies on the node.
- The node copy is deleted **only after** the copy-back succeeded, and the
  failure is announced loudly if it did not.
- Files are renamed into place, so a concurrent reader sees the old file or the
  new one, never a truncated one.
- **Prove it rather than reasoning about it**: run the payload once staged and
  once direct, then `comm -23` the two `find . -type f | sort` listings. That
  diff — not a count of the artefact you happen to remember — is what catches a
  lost file.

### Never run the payload in the foreground — `tkde_run_synced`

The traps above only fire if the shell can run them. **Bash defers a trap while
it waits on a foreground child**, so a `scancel` or a wall-clock kill terminates
the step with `tkde_finalize` never having run. Measured on job `2213210`
(2026-09-05): fourteen minutes of rows died on the node.

`common.sh` therefore provides `tkde_run_synced <command> [args...]` — it
backgrounds the payload, calls `tkde_sync_partial` every
`TKDE_SYNC_INTERVAL_S` (default 300 s), then waits and returns the payload's
status. Every worker's payload goes through it. Two things it buys: the TERM
trap can run at all, and the loss on a TIMEOUT or an OOM kill is bounded to one
interval instead of the whole task. Rows also become visible on HOME mid-run,
which is how a long job is monitored.

A job that writes straight to `$ISALHG_RESULTS_ROOT` (the matrices job) keeps
the wrapper anyway: there the sync is a no-op and the trap is the whole point.

### Shared matrices: the runner's `--out` is the node, the cache is on HOME

`--out` points at the **node-local stage root**, which starts empty. Anything
that reads the cached `N × N` distance matrices must therefore resolve them
from `$ISALHG_RESULTS_ROOT/matrices` on HOME, or it silently rebuilds every
matrix the shared `tkde-matrices` job already produced. Two mechanisms are in
use and both are correct:

- **Symlink** (`rq1`, `rq2`, `rq7`): `ln -sfn "${ISALHG_RESULTS_ROOT}/matrices"
  "${STAGE_ROOT}/matrices"`. Reads resolve to HOME, and a job that also *writes*
  a matrix (rq2's `ndc_substances` census) writes it straight into the shared
  cache through the link. The smoke run is the exception and gets its own
  `${STAGE_ROOT}/matrices` directory on the node — its 20-member subset would
  otherwise overwrite a several-hour real cache with a toy.
- **Flag** (`rq4`, `rq5`): `--matrices-root "${ISALHG_RESULTS_ROOT}"`, with
  `--out` still on the node.

**The copy-back never follows that symlink into HOME's `matrices/`, and must not
start doing so.** The reason is the layout, not the link: `tkde_finalize` and
`tkde_sync_partial` mirror `${MYLOCALSCRATCH}/out/` only, while `STAGE_ROOT` is
`${MYLOCALSCRATCH}/root` — a *sibling* of `out/`. The `matrices` link lives at
`${STAGE_ROOT}/matrices`, outside the mirrored tree; what is inside it is the
per-experiment link `${STAGE_ROOT}/<RQ>/<experiment>` pointing back at
`$OUT_DIR`. A change that mirrored `STAGE_ROOT` instead of `out/` would rsync
HOME's `matrices/` onto itself through the link — the one edit to refuse here.

### Threads

`common.sh` sets `OMP/MKL/OPENBLAS/NUMEXPR_NUM_THREADS` from
`SLURM_CPUS_PER_TASK`. **Timing arms must export `TKDE_THREADS=1` before
sourcing** so a measured wall-clock is not a measurement of thread count.

### `--export` is comma-separated

`--export=ALL,SEEDS=0,101,102` delivers `SEEDS=0` and two junk variables.
Nothing errors: low task indices return plausible results and high ones die
"index out of range". Ship list-valued variables colon-separated
(`${SEEDS//,/:}`) and translate back in the worker (`${SEEDS//:/,}`).

### Arrays

`MaxArraySize = 4096` (largest index 4095), `MaxJobCount = 15000`,
`cpu=9000` concurrent cores per user. Above 1000 tasks, mail
`soporte@scbi.uma.es` before the first submission — say what you measured
(arrays, tasks, cores/mem/wall per task, expected duration, core-hours, output
file count). They shape the submission rather than throttle it.

Exceeding `MaxArraySize` is handled by **offsetting the range**, never by
renumbering each chunk from 0 — renumbering silently remaps every task to the
wrong unit of work.

Re-run only what failed:

```bash
FAILED=$(sacct -j "${JOB_ID}" -n -X -o JobID,State \
         | awk '$2!="COMPLETED"{split($1,a,"_"); print a[2]}' | paste -sd, -)
[[ -n "${FAILED}" ]] && submit --array="${FAILED}%${MAX_CONCURRENT}" ... worker.sh
```

### Sizing

Resource limits are hard: exceeding RAM or wallclock kills the job. Measure a
short array first, take `MaxRSS` at p99, add ~50 % headroom.

`sacct -X` reports an **empty `MaxRSS`** — accounting records memory on the
`.batch` step and `-X` shows allocation lines only. Drop `-X` for memory:

```bash
sacct -j <ID> -n -P -o JobID,State,Elapsed,MaxRSS,ReqMem | awk -F'|' '$1 ~ /\.batch$/'
sacct -j <ID> -X -n -P -o JobID,State,Elapsed,NodeList   # states: this IS what -X is for
seff <ID>_<TASK>                                          # completed jobs only
```

Measured peaks in wave 3, for sizing anything of the same shape:

| Job | MaxRSS | What drives it |
|---|---|---|
| `tkde-matrices` (2213202) | 34.2 GB | the corpus plus every full-collection matrix resident at once |
| RQ3+RQ6 bundle | 20.4 GB | RQ6's per-shard cache grew across units; fixed by refitting per unit |

Both were read off the `.batch` step, not off `-X`. A bundled task that
memoizes across units is the shape to watch: the peak is the *last* unit's
footprint plus everything the earlier ones left behind, so a cache that is not
reset per unit turns a flat profile into a rising one.

### Results go to HOME, not FSCRATCH

**`ISALHG_RESULTS_ROOT = /mnt/home/users/tic_163_uma/mpascual/results/IEEETKDE`**
— on HOME (decision 2026-09-05). Inputs stay on FSCRATCH: repo, env, raw data
and `corpora/`.

`$FSCRATCH` is pseudo-volatile (files unaccessed for over two months may be
pre-deleted without notice, and `fscratch_files` is **not installed** here, so
do not plan around recovering them) *and* the account is currently over its
FSCRATCH file soft quota. HOME is permanent and nearly empty (3.3k/35.0k files,
24 GB/280 GB). The asymmetry that decides it: every input on FSCRATCH is
reproducible — re-sync the repo, re-run the setup, re-stage the data — and a
result is not.

Consequences you get for free: `tkde_stage_localscratch`'s copy-back is now
*also* the durable-storage step, so no separate FSCRATCH-to-HOME rescue job is
needed, and the campaign's output no longer consumes the exhausted FSCRATCH file
quota. What still applies: HOME's own file quota is 35.0k, so a launcher that
would write tens of thousands of small artefacts must still consolidate them.

Harvest with `scripts/tkde/harvest_from_picasso.sh` as soon as a job completes —
it reads the HOME root, and never deletes local files. The local drive remains
the copy a paper cites.

---

## Files

| File | What it is |
|---|---|
| `common.sh` | the frozen contract every worker sources |
| `smoke_worker.sh` | the environment proof: extension import, `cpp == python`, pynauty, rapidfuzz, unit tests |
| `smoke_launcher.sh` | submits the smoke job (the one job allowed under 2 h) |

Re-run the smoke job after any environment change:

```bash
bash scripts/tkde/sync_to_picasso.sh
ssh picasso 'bash ~/fscratch/repos/IsalHG-tkde/slurm/tkde/smoke_launcher.sh --test-only'
ssh picasso 'bash ~/fscratch/repos/IsalHG-tkde/slurm/tkde/smoke_launcher.sh'
```
