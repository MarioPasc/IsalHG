#!/usr/bin/env bash
# Submit RQ4 -- the data-quality screen (wave 3, agent rq-4-5).
#
#   bash slurm/tkde/rq4_launcher.sh --dependency 1234567   # full array
#   bash slurm/tkde/rq4_launcher.sh --smoke --dependency 1234567
#   bash slurm/tkde/rq4_launcher.sh --test-only
#   bash slurm/tkde/rq4_launcher.sh --dry-run
#
# --dependency is the tkde-matrices job id: RQ4 reads the inlier-inlier block
# from its cached matrices and computes only the anomaly rows. The dependency is
# VERIFIED after submission -- sbatch accepts a malformed one and records
# Dependency=(null), which starts the array immediately against a half-built
# cache and produces a complete, plausible, wrong result set.
#
# Prints the job id on the last line.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TKDE_USER_ROOT="/mnt/home/users/tic_163_uma/mpascual"

export REPO_DIR="${REPO_DIR:-${TKDE_USER_ROOT}/fscratch/repos/IsalHG-tkde}"
LOGS_DIR="${TKDE_LOGS_DIR:-${TKDE_USER_ROOT}/execs/tkde/logs}"
CONFIG="${RQ4_CONFIG:-experiments/tkde/configs/rq4.yaml}"
mkdir -p "${LOGS_DIR}"

# common.sh defines PY (the env is NOT under ~/.conda on Picasso) and puts the
# deployed tree first on PYTHONPATH, so --count decodes THIS checkout's units.
# shellcheck source=/dev/null
source "${REPO_DIR}/slurm/tkde/common.sh"

MODE="submit"
DEPENDENCY=""
SMOKE=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) MODE="dry"; shift ;;
        --test-only) MODE="test"; shift ;;
        --smoke) SMOKE=1; shift ;;
        --dependency) DEPENDENCY="${2:?--dependency needs a job id}"; shift 2 ;;
        *) echo "ERROR: unknown option $1" >&2; exit 2 ;;
    esac
done

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

cd "${REPO_DIR}"
# Derive the task count from the decoder, with the same arguments the worker
# uses. A hard-coded count cannot disagree with the decode, so it cannot catch
# a decode that changed -- and the decode is the part most likely to change.
N_UNITS=$("${PY}" -m experiments.tkde.rq4 --config "${CONFIG}" --count)
[[ "${N_UNITS}" =~ ^[0-9]+$ ]] || { echo "FATAL: --count gave ${N_UNITS@Q}" >&2; exit 1; }

# ~48 core-hours over 1,323 units (see rq4_worker.sh for the per-sub-collection
# breakdown). At 8 cores per task, 3 tasks is ~2 h each -- the floor reached by
# measurement rather than by padding. Units are seed-major, so an even split
# gives three equal-cost tasks.
BUNDLE="${RQ4_BUNDLE:-441}"
N_TASKS=$(( (N_UNITS + BUNDLE - 1) / BUNDLE ))
MAX_CONCURRENT="${RQ4_MAX_CONCURRENT:-3}"

EXPORTS="ALL,REPO_DIR=${REPO_DIR},RQ4_CONFIG=${CONFIG},RQ4_N_TASKS=${N_TASKS}"
TIME_LIMIT="0-08:00:00"
if [[ "${SMOKE}" -eq 1 ]]; then
    # Unit 0 is (ndc_classes, spurious_fact, budget 1, first seed): the
    # smallest real unit, ~4 minutes on eight cores across all eight arms.
    EXPORTS="${EXPORTS},TKDE_SMOKE_UNIT=${RQ4_SMOKE_UNIT:-0}"
    TIME_LIMIT="0-00:30:00"
    N_TASKS=1
    MAX_CONCURRENT=1
fi

SBATCH_ARGS=(
    --array="0-$((N_TASKS - 1))%${MAX_CONCURRENT}"
    --time="${TIME_LIMIT}"
    --output="${LOGS_DIR}/tkde-rq4_%A_%a.out"
    --error="${LOGS_DIR}/tkde-rq4_%A_%a.err"
    --export="${EXPORTS}"
)
[[ -n "${DEPENDENCY}" ]] && SBATCH_ARGS+=(--dependency="afterok:${DEPENDENCY}")
SBATCH_ARGS+=("${SCRIPT_DIR}/rq4_worker.sh")

echo "units=${N_UNITS} bundle=${BUNDLE} tasks=${N_TASKS} smoke=${SMOKE} dep=${DEPENDENCY:-none}" >&2

if [[ "${MODE}" == "dry" ]]; then
    echo "[DRY-RUN] sbatch --parsable ${SBATCH_ARGS[*]}"
    exit 0
fi
if [[ "${MODE}" == "test" ]]; then
    sbatch --test-only "${SBATCH_ARGS[@]}"
    exit $?
fi

JOB_ID=$(submit "${SBATCH_ARGS[@]}") || exit 1

if [[ -n "${DEPENDENCY}" ]]; then
    if scontrol show job "${JOB_ID}" | grep -q 'Dependency=(null)'; then
        echo "FATAL: dependency on ${DEPENDENCY} was dropped; cancelling ${JOB_ID}" >&2
        scancel "${JOB_ID}"
        exit 1
    fi
    echo "  dependency afterok:${DEPENDENCY} verified" >&2
fi

echo "Submitted tkde-rq4 as ${JOB_ID} (${N_TASKS} task(s) over ${N_UNITS} units)" >&2
echo "  logs: ${LOGS_DIR}/tkde-rq4_${JOB_ID}_*.out" >&2
echo "${JOB_ID}"
