#!/usr/bin/env bash
# Submit RQ1 (addressing) to Picasso.
#
#   bash rq1_launcher.sh --test-only    # sbatch --test-only, submits nothing
#   bash rq1_launcher.sh --smoke        # ONE short task (the documented
#                                       # exception to the 2 h floor)
#   bash rq1_launcher.sh                # the array + its recovery sweep
#   bash rq1_launcher.sh --no-sweep     # the array only
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TKDE_USER_ROOT="/mnt/home/users/tic_163_uma/mpascual"
REPO_DIR="${REPO_DIR:-${TKDE_USER_ROOT}/fscratch/repos/IsalHG-tkde}"
LOGS_DIR="${TKDE_USER_ROOT}/execs/tkde/logs"
PY="${PY:-${TKDE_USER_ROOT}/fscratch/conda_envs/isalhg-tkde/bin/python}"
CONFIG="${REPO_DIR}/experiments/tkde/configs/rq1.yaml"
mkdir -p "${LOGS_DIR}"

# One shard is about one core-hour (measured pointer profile, see rq1.yaml), so
# three shards per task clears SCBI's two-hour floor with margin.
BUNDLE="${BUNDLE:-3}"
MAX_CONCURRENT="${MAX_CONCURRENT:-16}"
WALL="${WALL:-1-00:00:00}"
START_CUTOFF_S="${START_CUTOFF_S:-54000}"   # 15 h: leaves 9 h for a started shard

# Picasso's Lua sbatch wrapper prepends ANSI codes and a multi-line warning to
# --parsable output. Take the LAST line FIRST: a line-by-line sed leaves the
# banner's newlines in place and the numeric guard then fires AFTER the job was
# submitted, leaving an untracked job on the cluster.
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

MODE="array"
[[ "${1:-}" == "--smoke" ]] && MODE="smoke"
[[ "${1:-}" == "--test-only" ]] && MODE="test"
NO_SWEEP=0
[[ "${1:-}" == "--no-sweep" || "${2:-}" == "--no-sweep" ]] && NO_SWEEP=1

COMMON_EXPORT="ALL,REPO_DIR=${REPO_DIR}"

if [[ "${MODE}" == "smoke" ]]; then
    # %j, not %A_%a: on a non-array job %a expands to SLURM's sentinel
    # 4294967294 (measured on smoke job 2210890).
    JOB_ID=$(submit \
        --job-name=tkde-rq1-smoke \
        --time=0-00:30:00 \
        --output="${LOGS_DIR}/tkde-rq1-smoke_%j.out" \
        --error="${LOGS_DIR}/tkde-rq1-smoke_%j.err" \
        --export="${COMMON_EXPORT},TKDE_SMOKE=1" \
        "${SCRIPT_DIR}/rq1_worker.sh") || exit 1
    echo "Submitted RQ1 smoke ${JOB_ID}"
    echo "Log: ${LOGS_DIR}/tkde-rq1-smoke_${JOB_ID}.out"
    exit 0
fi

# Size the array in TASKS and derive the shard count from the runner itself: a
# hard-coded count cannot disagree with a decode that changed, so it cannot
# catch one.
# The runner is a package module of the DEPLOYED tree, not of slurm/tkde,
# so --count must run from REPO_DIR. Without the cd this dies with
# ModuleNotFoundError and the array size is never derived.
N_SHARDS=$(cd "${REPO_DIR}" && "${PY}" -m experiments.tkde.rq1 --config "${CONFIG}" --count)
[[ "${N_SHARDS}" =~ ^[0-9]+$ ]] || { echo "FATAL: --count returned ${N_SHARDS@Q}" >&2; exit 1; }
N_TASKS=$(( (N_SHARDS + BUNDLE - 1) / BUNDLE ))
(( MAX_CONCURRENT > N_TASKS )) && MAX_CONCURRENT="${N_TASKS}"

ARGS=(
    --array="0-$((N_TASKS - 1))%${MAX_CONCURRENT}"
    --output="${LOGS_DIR}/tkde-rq1_%A_%a.out"
    --error="${LOGS_DIR}/tkde-rq1_%A_%a.err"
    --export="${COMMON_EXPORT},N_SHARDS=${N_SHARDS},N_TASKS=${N_TASKS},START_CUTOFF_S=${START_CUTOFF_S}"
    --time="${WALL}"
    "${SCRIPT_DIR}/rq1_worker.sh"
)

echo "RQ1: ${N_SHARDS} shards -> ${N_TASKS} tasks (bundle ${BUNDLE}, throttle ${MAX_CONCURRENT}, wall ${WALL})"

if [[ "${MODE}" == "test" ]]; then
    sbatch --test-only "${ARGS[@]}"
    exit 0
fi

JOB_ID=$(submit "${ARGS[@]}") || exit 1
echo "Submitted RQ1 array ${JOB_ID} (${N_TASKS} tasks)"

if [[ "${NO_SWEEP}" -eq 0 ]]; then
    # The recovery sweep is submitted NOW, not by hand later: a recovery step
    # that depends on someone remembering does not happen. It is free when
    # nothing spilled, because every unit whose rows exist is skipped in
    # seconds.
    SWEEP_ID=$(submit --dependency=afterany:"${JOB_ID}" "${ARGS[@]}") || exit 1
    scontrol show job "${SWEEP_ID}" | grep -q 'Dependency=(null)' && {
        echo "FATAL: dependency dropped on the sweep; cancelling it" >&2
        scancel "${SWEEP_ID}"; exit 1
    }
    echo "Submitted RQ1 recovery sweep ${SWEEP_ID} (afterany:${JOB_ID})"
fi

echo "Monitor: sacct -j ${JOB_ID} -X -n -P -o JobID,State,Elapsed"
echo "Logs:    ${LOGS_DIR}/tkde-rq1_${JOB_ID}_*.out"
