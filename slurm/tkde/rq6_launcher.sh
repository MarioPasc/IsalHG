#!/usr/bin/env bash
# Submit RQ6 (generation) to Picasso.
#
# Run this ON PICASSO's login node, from the deployed repo:
#   bash slurm/tkde/rq6_launcher.sh --dry-run     # print the sbatch command
#   bash slurm/tkde/rq6_launcher.sh --test-only   # sbatch --test-only
#   bash slurm/tkde/rq6_launcher.sh --smoke       # one short task on a tiny cell
#   bash slurm/tkde/rq6_launcher.sh               # standalone full RQ6
#
# The RQ6 *campaign* normally rides inside an RQ3 task (rq3_launcher.sh sets
# TKDE_RUN_RQ6=1 when one task holds every shard), because RQ6 alone is minutes
# and a job that short is what SCBI asked us to stop submitting (2026-08-07).
# Use the standalone form only to redo RQ6 without touching the RQ3 rows, and
# say so when you do.
#
# Output lands in ${ISALHG_RESULTS_ROOT}/RQ6_generation/ on HOME; harvest with
#   bash scripts/tkde/harvest_from_picasso.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TKDE_USER_ROOT="/mnt/home/users/tic_163_uma/mpascual"

REPO_DIR="${REPO_DIR:-${TKDE_USER_ROOT}/fscratch/repos/IsalHG-tkde}"
LOGS_DIR="${TKDE_LOGS_DIR:-${TKDE_USER_ROOT}/execs/tkde/logs}"
RESULTS_ROOT="${ISALHG_RESULTS_ROOT:-${TKDE_USER_ROOT}/results/IEEETKDE}"
DATA_ROOT="${ISALHG_DATA_ROOT:-${TKDE_USER_ROOT}/fscratch/datasets/isalhg_tkde}"
CORPORA_ROOT="${TKDE_CORPORA_ROOT:-${DATA_ROOT}}"

N_SHARDS="${TKDE_N_SHARDS:-1}"
N_TASKS="${TKDE_N_TASKS:-1}"
MAX_CONCURRENT="${TKDE_MAX_CONCURRENT:-2}"
WALL="${TKDE_WALL:-0-04:00:00}"
START_CUTOFF_S="${TKDE_START_CUTOFF_S:-12600}"

WORKER="${SCRIPT_DIR}/rq6_worker.sh"
[[ -f "${WORKER}" ]] || { echo "ERROR: worker not found: ${WORKER}" >&2; exit 1; }

MODE="submit"
SMOKE=0
case "${1:-}" in
    --dry-run)   MODE="dry" ;;
    --test-only) MODE="test" ;;
    --smoke)     SMOKE=1 ;;
    "")          ;;
    *)           echo "ERROR: unknown option ${1}" >&2; exit 2 ;;
esac

mkdir -p "${LOGS_DIR}" "${RESULTS_ROOT}"

_clean_job_id() {
    tail -n 1 <<<"$1" | sed -e 's/\x1b\[[0-9;]*[a-zA-Z]//g' -e 's/[^0-9]//g'
}

if [[ "${SMOKE}" == "1" ]]; then
    # %j, not %A_%a: a non-array job expands %a to SLURM's sentinel.
    ARGS=(
        --job-name=tkde-rq6-smoke
        --time=0-00:30:00
        --output="${LOGS_DIR}/tkde-rq6-smoke_%j.out"
        --error="${LOGS_DIR}/tkde-rq6-smoke_%j.err"
        --export="ALL,REPO_DIR=${REPO_DIR},ISALHG_RESULTS_ROOT=${RESULTS_ROOT},ISALHG_DATA_ROOT=${DATA_ROOT},TKDE_CORPORA_ROOT=${CORPORA_ROOT},TKDE_LOGS_DIR=${LOGS_DIR},TKDE_SMOKE=1,TKDE_N_SHARDS=1,TKDE_N_TASKS=1,TKDE_RUN_ANALYZERS=1,TKDE_START_CUTOFF_S=1200"
        "${WORKER}"
    )
elif (( N_TASKS == 1 )); then
    ARGS=(
        --job-name=tkde-rq6
        --time="${WALL}"
        --output="${LOGS_DIR}/tkde-rq6_%j.out"
        --error="${LOGS_DIR}/tkde-rq6_%j.err"
        --export="ALL,REPO_DIR=${REPO_DIR},ISALHG_RESULTS_ROOT=${RESULTS_ROOT},ISALHG_DATA_ROOT=${DATA_ROOT},TKDE_CORPORA_ROOT=${CORPORA_ROOT},TKDE_LOGS_DIR=${LOGS_DIR},TKDE_SMOKE=0,TKDE_N_SHARDS=${N_SHARDS},TKDE_N_TASKS=1,TKDE_RUN_ANALYZERS=1,TKDE_START_CUTOFF_S=${START_CUTOFF_S}"
        "${WORKER}"
    )
else
    THROTTLE=$(( MAX_CONCURRENT < N_TASKS ? MAX_CONCURRENT : N_TASKS ))
    ARGS=(
        --array="1-${N_TASKS}%${THROTTLE}"
        --job-name=tkde-rq6
        --time="${WALL}"
        --output="${LOGS_DIR}/tkde-rq6_%A_%a.out"
        --error="${LOGS_DIR}/tkde-rq6_%A_%a.err"
        --export="ALL,REPO_DIR=${REPO_DIR},ISALHG_RESULTS_ROOT=${RESULTS_ROOT},ISALHG_DATA_ROOT=${DATA_ROOT},TKDE_CORPORA_ROOT=${CORPORA_ROOT},TKDE_LOGS_DIR=${LOGS_DIR},TKDE_SMOKE=0,TKDE_N_SHARDS=${N_SHARDS},TKDE_N_TASKS=${N_TASKS},TKDE_RUN_ANALYZERS=0,TKDE_START_CUTOFF_S=${START_CUTOFF_S}"
        "${WORKER}"
    )
fi

if [[ "${MODE}" == "dry" ]]; then
    echo "[DRY-RUN] sbatch --parsable ${ARGS[*]}"
    exit 0
fi

if [[ "${MODE}" == "test" ]]; then
    sbatch --test-only "${ARGS[@]}"
    exit $?
fi

RAW=$(sbatch --parsable "${ARGS[@]}") || { echo "sbatch failed" >&2; exit 1; }
JOB_ID=$(_clean_job_id "${RAW}")
[[ "${JOB_ID}" =~ ^[0-9]+$ ]] || {
    echo "FATAL: unparsable job id: ${RAW@Q}" >&2
    echo "Run squeue NOW -- the job may already be queued." >&2
    exit 1
}

echo "Submitted RQ6 job: ${JOB_ID}"
echo "Monitor:  sacct -j ${JOB_ID} -X -n -P -o JobID,State,Elapsed"
echo "Logs:     ${LOGS_DIR}/tkde-rq6*_${JOB_ID}*.out"
echo "Results:  ${RESULTS_ROOT}/RQ6_generation/"
