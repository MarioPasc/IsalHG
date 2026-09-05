#!/usr/bin/env bash
# Submit RQ7 (the operating envelope) to Picasso.
#
#   bash rq7_launcher.sh --test-only
#   bash rq7_launcher.sh --smoke
#   bash rq7_launcher.sh
#   bash rq7_launcher.sh --no-sweep
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TKDE_USER_ROOT="/mnt/home/users/tic_163_uma/mpascual"
REPO_DIR="${REPO_DIR:-${TKDE_USER_ROOT}/fscratch/repos/IsalHG-tkde-rq127}"
LOGS_DIR="${TKDE_USER_ROOT}/execs/tkde/logs"
PY="${PY:-${TKDE_USER_ROOT}/fscratch/conda_envs/isalhg-tkde/bin/python}"
CONFIG="${REPO_DIR}/experiments/tkde/configs/rq7.yaml"
mkdir -p "${LOGS_DIR}"

# A sweep cell is at most 27 x 60 s for the pointer arm; a yield block is about
# an hour; an N-scaling unit is at most three repetitions under a one-hour
# budget. Five shards per task clears the two-hour floor in the common case.
BUNDLE="${BUNDLE:-5}"
MAX_CONCURRENT="${MAX_CONCURRENT:-16}"
WALL="${WALL:-1-00:00:00}"
START_CUTOFF_S="${START_CUTOFF_S:-54000}"

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
    JOB_ID=$(submit \
        --job-name=tkde-rq7-smoke \
        --time=0-00:30:00 \
        --output="${LOGS_DIR}/tkde-rq7-smoke_%j.out" \
        --error="${LOGS_DIR}/tkde-rq7-smoke_%j.err" \
        --export="${COMMON_EXPORT},TKDE_SMOKE=1" \
        "${SCRIPT_DIR}/rq7_worker.sh") || exit 1
    echo "Submitted RQ7 smoke ${JOB_ID}"
    echo "Log: ${LOGS_DIR}/tkde-rq7-smoke_${JOB_ID}.out"
    exit 0
fi

# The runner is a package module of the DEPLOYED tree, not of slurm/tkde,
# so --count must run from REPO_DIR. Without the cd this dies with
# ModuleNotFoundError and the array size is never derived.
N_SHARDS=$(cd "${REPO_DIR}" && "${PY}" -m experiments.tkde.rq7 --config "${CONFIG}" --count)
[[ "${N_SHARDS}" =~ ^[0-9]+$ ]] || { echo "FATAL: --count returned ${N_SHARDS@Q}" >&2; exit 1; }
N_TASKS=$(( (N_SHARDS + BUNDLE - 1) / BUNDLE ))
(( MAX_CONCURRENT > N_TASKS )) && MAX_CONCURRENT="${N_TASKS}"

ARGS=(
    --array="0-$((N_TASKS - 1))%${MAX_CONCURRENT}"
    --output="${LOGS_DIR}/tkde-rq7_%A_%a.out"
    --error="${LOGS_DIR}/tkde-rq7_%A_%a.err"
    --export="${COMMON_EXPORT},N_SHARDS=${N_SHARDS},N_TASKS=${N_TASKS},START_CUTOFF_S=${START_CUTOFF_S}"
    --time="${WALL}"
    "${SCRIPT_DIR}/rq7_worker.sh"
)

echo "RQ7: ${N_SHARDS} shards -> ${N_TASKS} tasks (bundle ${BUNDLE}, throttle ${MAX_CONCURRENT}, wall ${WALL})"

if [[ "${MODE}" == "test" ]]; then
    sbatch --test-only "${ARGS[@]}"
    exit 0
fi

JOB_ID=$(submit "${ARGS[@]}") || exit 1
echo "Submitted RQ7 array ${JOB_ID} (${N_TASKS} tasks)"

if [[ "${NO_SWEEP}" -eq 0 ]]; then
    SWEEP_ID=$(submit --dependency=afterany:"${JOB_ID}" "${ARGS[@]}") || exit 1
    scontrol show job "${SWEEP_ID}" | grep -q 'Dependency=(null)' && {
        echo "FATAL: dependency dropped on the sweep; cancelling it" >&2
        scancel "${SWEEP_ID}"; exit 1
    }
    echo "Submitted RQ7 recovery sweep ${SWEEP_ID} (afterany:${JOB_ID})"
fi

echo "Monitor: sacct -j ${JOB_ID} -X -n -P -o JobID,State,Elapsed"
