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

    "${PY}" -m experiments.tkde.rqN --unit "${U}" --out "${OUT_DIR}"

    tkde_sync_partial          # bound the loss if the node dies mid-bundle
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
