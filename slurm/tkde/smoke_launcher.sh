#!/usr/bin/env bash
# Submit the TKDE environment smoke test to Picasso.
#
# Run this ON PICASSO's login node, from the deployed repo:
#   bash slurm/tkde/smoke_launcher.sh --dry-run     # print the sbatch command
#   bash slurm/tkde/smoke_launcher.sh --test-only   # sbatch --test-only
#   bash slurm/tkde/smoke_launcher.sh               # submit
#
# Output lands in ${ISALHG_RESULTS_ROOT}/_smoke/ ; harvest it with
#   bash scripts/tkde/harvest_from_picasso.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TKDE_USER_ROOT="/mnt/home/users/tic_163_uma/mpascual"

REPO_DIR="${REPO_DIR:-${TKDE_USER_ROOT}/fscratch/repos/IsalHG-tkde}"
LOGS_DIR="${TKDE_LOGS_DIR:-${TKDE_USER_ROOT}/execs/tkde/logs}"
RESULTS_ROOT="${ISALHG_RESULTS_ROOT:-${TKDE_USER_ROOT}/fscratch/results/IEEETKDE}"

WORKER="${SCRIPT_DIR}/smoke_worker.sh"
[[ -f "${WORKER}" ]] || { echo "ERROR: worker not found: ${WORKER}" >&2; exit 1; }

MODE="submit"
case "${1:-}" in
    --dry-run)   MODE="dry" ;;
    --test-only) MODE="test" ;;
    "")          ;;
    *)           echo "ERROR: unknown option ${1}" >&2; exit 2 ;;
esac

mkdir -p "${LOGS_DIR}" "${RESULTS_ROOT}"

# Picasso's Lua sbatch wrapper prepends ANSI codes and a multi-line warning to
# --parsable output. Take the LAST line first: a line-by-line sed leaves the
# banner's newlines in place and the guard then fires AFTER the job was
# submitted, leaving an untracked job on the cluster.
_clean_job_id() {
    tail -n 1 <<<"$1" | sed -e 's/\x1b\[[0-9;]*[a-zA-Z]//g' -e 's/[^0-9]//g'
}

# %j, not %A_%a: this is a single job, and on a non-array job %a expands to
# SLURM's "no array task" sentinel 4294967294 (measured, job 2210890).
# Array launchers use %A_%a.
ARGS=(
    --output="${LOGS_DIR}/tkde-smoke_%j.out"
    --error="${LOGS_DIR}/tkde-smoke_%j.err"
    --export="ALL,REPO_DIR=${REPO_DIR},ISALHG_RESULTS_ROOT=${RESULTS_ROOT},TKDE_LOGS_DIR=${LOGS_DIR}"
    "${WORKER}"
)

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

echo "Submitted TKDE smoke job: ${JOB_ID}"
echo "Monitor:  squeue -j ${JOB_ID}"
echo "Log:      ${LOGS_DIR}/tkde-smoke_${JOB_ID}.out"
echo "Results:  ${RESULTS_ROOT}/_smoke/"
