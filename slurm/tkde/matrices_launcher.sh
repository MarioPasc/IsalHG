#!/usr/bin/env bash
# Submit the shared distance-matrices job (wave 3, agent rq-4-5).
#
#   bash slurm/tkde/matrices_launcher.sh              # submit
#   bash slurm/tkde/matrices_launcher.sh --dry-run    # print, do not submit
#   bash slurm/tkde/matrices_launcher.sh --test-only  # sbatch --test-only
#
# Prints the job id on the last line so the dependent RQ launchers (and the
# peer agent's RQ2 census) can consume it:
#
#   MATRICES_JOB=$(bash slurm/tkde/matrices_launcher.sh | tail -1)
#   bash slurm/tkde/rq5_launcher.sh --dependency "${MATRICES_JOB}"

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TKDE_USER_ROOT="/mnt/home/users/tic_163_uma/mpascual"

# rq-4-5 deploys to its OWN remote tree so that three wave-3 agents can run
# concurrently without overwriting each other's checkouts.
REPO_DIR="${REPO_DIR:-${TKDE_USER_ROOT}/fscratch/repos/IsalHG-tkde-rq45}"
LOGS_DIR="${TKDE_LOGS_DIR:-${TKDE_USER_ROOT}/execs/tkde/logs}"
CONFIG="${MATRICES_CONFIG:-experiments/tkde/configs/matrices.yaml}"
mkdir -p "${LOGS_DIR}"

MODE="submit"
case "${1:-}" in
    --dry-run) MODE="dry" ;;
    --test-only) MODE="test" ;;
    "") ;;
    *) echo "ERROR: unknown option $1" >&2; exit 2 ;;
esac

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

SBATCH_ARGS=(
    --output="${LOGS_DIR}/tkde-matrices_%j.out"
    --error="${LOGS_DIR}/tkde-matrices_%j.err"
    --export="ALL,REPO_DIR=${REPO_DIR},MATRICES_CONFIG=${CONFIG},MATRICES_SHARD=0/1"
    "${SCRIPT_DIR}/matrices_worker.sh"
)

if [[ "${MODE}" == "dry" ]]; then
    echo "[DRY-RUN] sbatch --parsable ${SBATCH_ARGS[*]}"
    exit 0
fi
if [[ "${MODE}" == "test" ]]; then
    sbatch --test-only "${SBATCH_ARGS[@]}"
    exit $?
fi

JOB_ID=$(submit "${SBATCH_ARGS[@]}") || exit 1
echo "Submitted tkde-matrices as ${JOB_ID}" >&2
echo "  logs:    ${LOGS_DIR}/tkde-matrices_${JOB_ID}.out" >&2
echo "  monitor: sacct -j ${JOB_ID} -X -o JobID,State,Elapsed,NodeList" >&2
echo "${JOB_ID}"
