#!/usr/bin/env bash
# Submit the KNN_2026-10-15 full run (LOG.md section 8; agent probe-engineer).
#
#   bash slurm/tkde/knn_launcher.sh --smoke        # seed 0 of one unit per design CLI
#   bash slurm/tkde/knn_launcher.sh --test-only    # sbatch --test-only of the array
#   bash slurm/tkde/knn_launcher.sh --dry-run
#   bash slurm/tkde/knn_launcher.sh                # the array (every task)
#   bash slurm/tkde/knn_launcher.sh --tasks 3,7    # a subset of array indices
#
# Private deployment, as rq8_launcher.sh: REPO_DIR defaults to
# ~/fscratch/repos/IsalHG-knn (scripts/ and experiments/ of this wave, deployed
# with `TKDE_REMOTE_REPO=<it> scripts/tkde/sync_to_picasso.sh --no-build`), and
# the results root to ~/results/KNN_2026-10-15 on HOME, mirroring the local
# drive's KNN_2026-10-15/ so the harvest is one rsync. The conda env and isalhg
# stay the SHARED isalhg-tkde / IsalHG-tkde (src/** unchanged by this wave).
#
# Prints the job id on the last line.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TKDE_USER_ROOT="/mnt/home/users/tic_163_uma/mpascual"

export REPO_DIR="${REPO_DIR:-${TKDE_USER_ROOT}/fscratch/repos/IsalHG-knn}"
export ISALHG_RESULTS_ROOT="${ISALHG_RESULTS_ROOT:-${TKDE_USER_ROOT}/results/KNN_2026-10-15}"
LOGS_DIR="${TKDE_LOGS_DIR:-${TKDE_USER_ROOT}/execs/tkde/logs}"
mkdir -p "${LOGS_DIR}" "${ISALHG_RESULTS_ROOT}"

# shellcheck source=/dev/null
source "${REPO_DIR}/slurm/tkde/common.sh"

MODE="submit"
SMOKE=0
TASKS=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) MODE="dry"; shift ;;
        --test-only) MODE="test"; shift ;;
        --smoke) SMOKE=1; shift ;;
        --tasks) TASKS="${2:?--tasks needs a comma-separated list}"; shift 2 ;;
        *) echo "ERROR: unknown option $1" >&2; exit 2 ;;
    esac
done

# Picasso's Lua sbatch wrapper prepends ANSI codes and a multi-line warning to
# --parsable output. Take the LAST line FIRST (README.md, rq8_launcher.sh).
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

# Ask the DECODER how many tasks there are; a hard-coded count cannot catch a
# decode that changed.
N_TASKS=$("${PY}" scripts/newpos/knn/full_run.py --list-tasks | wc -l)
[[ "${N_TASKS}" =~ ^[0-9]+$ ]] && (( N_TASKS > 0 )) || {
    echo "FATAL: --list-tasks gave ${N_TASKS@Q}" >&2; exit 1
}
"${PY}" scripts/newpos/knn/full_run.py --list-tasks >&2

MAX_CONCURRENT="${N_TASKS}"
ARRAY="0-$((N_TASKS - 1))%${MAX_CONCURRENT}"
[[ -n "${TASKS}" ]] && ARRAY="${TASKS}"
TIME_LIMIT="0-12:00:00"
WALL_S=43200
EXPORTS="ALL,REPO_DIR=${REPO_DIR},ISALHG_RESULTS_ROOT=${ISALHG_RESULTS_ROOT},KNN_WALL_S=${WALL_S}"
NAME="tkde-knn"
if [[ "${SMOKE}" -eq 1 ]]; then
    ARRAY="0"
    TIME_LIMIT="0-01:00:00"
    EXPORTS="${EXPORTS},KNN_SMOKE=1,KNN_WALL_S=3600"
    NAME="tkde-knn-smoke"
fi

SBATCH_ARGS=(
    --job-name="${NAME}"
    --array="${ARRAY}"
    --time="${TIME_LIMIT}"
    --output="${LOGS_DIR}/${NAME}_%A_%a.out"
    --error="${LOGS_DIR}/${NAME}_%A_%a.err"
    --export="${EXPORTS}"
    "${SCRIPT_DIR}/knn_worker.sh"
)

echo "tasks=${N_TASKS} array=${ARRAY} smoke=${SMOKE} repo=${REPO_DIR}" >&2
echo "results=${ISALHG_RESULTS_ROOT}" >&2

if [[ "${MODE}" == "dry" ]]; then
    echo "[DRY-RUN] sbatch --parsable ${SBATCH_ARGS[*]}"
    exit 0
fi
if [[ "${MODE}" == "test" ]]; then
    sbatch --test-only "${SBATCH_ARGS[@]}"
    exit $?
fi

JOB_ID=$(submit "${SBATCH_ARGS[@]}") || exit 1
echo "Submitted ${NAME} as ${JOB_ID} (array ${ARRAY})" >&2
echo "  logs: ${LOGS_DIR}/${NAME}_${JOB_ID}_*.out" >&2
echo "${JOB_ID}"
