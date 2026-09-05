#!/usr/bin/env bash
# Submit RQ5 -- description patterns (wave 3, agent rq-4-5).
#
#   bash slurm/tkde/rq5_launcher.sh --dependency 1234567   # full run
#   bash slurm/tkde/rq5_launcher.sh --smoke --dependency 1234567
#   bash slurm/tkde/rq5_launcher.sh --test-only
#   bash slurm/tkde/rq5_launcher.sh --dry-run
#
# --dependency is the tkde-matrices job id: RQ5 reads its cached matrices and
# computes no distance itself. The dependency is VERIFIED after submission --
# sbatch accepts a malformed one and records Dependency=(null), which starts the
# job immediately against a half-built cache.
#
# Prints the job id on the last line.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TKDE_USER_ROOT="/mnt/home/users/tic_163_uma/mpascual"

export REPO_DIR="${REPO_DIR:-${TKDE_USER_ROOT}/fscratch/repos/IsalHG-tkde-rq45}"
LOGS_DIR="${TKDE_LOGS_DIR:-${TKDE_USER_ROOT}/execs/tkde/logs}"
CONFIG="${RQ5_CONFIG:-experiments/tkde/configs/rq5.yaml}"
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
N_UNITS=$("${PY}" -m experiments.tkde.rq5 --config "${CONFIG}" --count)
[[ "${N_UNITS}" =~ ^[0-9]+$ ]] || { echo "FATAL: --count gave ${N_UNITS@Q}" >&2; exit 1; }

# RQ5 is ~25 minutes of work in total (measured at the real N = 3,492: the
# eigendecomposition for nu is 62 s per arm, metric MDS 159 s once, PAM and
# average-linkage 0.2 s each). One task; see the worker header for why an array
# would be worse rather than better.
BUNDLE="${RQ5_BUNDLE:-${N_UNITS}}"
N_TASKS=$(( (N_UNITS + BUNDLE - 1) / BUNDLE ))
MAX_CONCURRENT="${RQ5_MAX_CONCURRENT:-${N_TASKS}}"

EXPORTS="ALL,REPO_DIR=${REPO_DIR},RQ5_CONFIG=${CONFIG},RQ5_N_TASKS=${N_TASKS}"
TIME_LIMIT="0-06:00:00"
if [[ "${SMOKE}" -eq 1 ]]; then
    # Unit 11 is the first BALANCED unit (units 0..10 are the eleven heavy
    # full-design arms). A balanced unit is a 280-member submatrix across every
    # arm: seconds, and it still exercises the matrix cache, the deployed tree
    # and the copy-back.
    EXPORTS="${EXPORTS},TKDE_SMOKE_UNIT=${RQ5_SMOKE_UNIT:-11}"
    TIME_LIMIT="0-00:30:00"
    N_TASKS=1
    MAX_CONCURRENT=1
fi

SBATCH_ARGS=(
    --array="0-$((N_TASKS - 1))%${MAX_CONCURRENT}"
    --time="${TIME_LIMIT}"
    --output="${LOGS_DIR}/tkde-rq5_%A_%a.out"
    --error="${LOGS_DIR}/tkde-rq5_%A_%a.err"
    --export="${EXPORTS}"
)
[[ -n "${DEPENDENCY}" ]] && SBATCH_ARGS+=(--dependency="afterok:${DEPENDENCY}")
SBATCH_ARGS+=("${SCRIPT_DIR}/rq5_worker.sh")

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

# sbatch ACCEPTS a garbage dependency and records Dependency=(null); the job
# then starts immediately against partial input. Verify, and cancel if dropped.
if [[ -n "${DEPENDENCY}" ]]; then
    if scontrol show job "${JOB_ID}" | grep -q 'Dependency=(null)'; then
        echo "FATAL: dependency on ${DEPENDENCY} was dropped; cancelling ${JOB_ID}" >&2
        scancel "${JOB_ID}"
        exit 1
    fi
    echo "  dependency afterok:${DEPENDENCY} verified" >&2
fi

echo "Submitted tkde-rq5 as ${JOB_ID} (${N_TASKS} task(s) over ${N_UNITS} units)" >&2
echo "  logs: ${LOGS_DIR}/tkde-rq5_${JOB_ID}_*.out" >&2
echo "${JOB_ID}"
