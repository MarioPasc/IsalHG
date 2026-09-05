#!/usr/bin/env bash
# Submit RQ3 (the representative record) to Picasso.
#
# Run this ON PICASSO's login node, from the deployed repo:
#   bash slurm/tkde/rq3_launcher.sh --dry-run     # print the sbatch command
#   bash slurm/tkde/rq3_launcher.sh --test-only   # sbatch --test-only
#   bash slurm/tkde/rq3_launcher.sh --smoke       # one short task on a tiny cell
#   bash slurm/tkde/rq3_launcher.sh               # the full campaign
#
# Sizing, measured rather than assumed (2026-09-05, i7-13700KF, single core):
# one seed of the whole 24-cell Corpus A matrix plus all 69 Corpus B runs takes
# 53 s, so the 27-seed campaign is about 17 minutes locally and roughly 40-60
# minutes on an `sd` node. DESIGN.md's "a few core-hours" over-estimated it.
# SCBI's floor asks for the *fewest, longest* tasks, so the default is a single
# array task carrying every shard, with RQ6 (minutes) bundled into it. Raising
# TKDE_N_TASKS splits the shards further and makes each task shorter --- the
# wrong direction for the floor, and it also switches the analyzers off inside
# the job, because a task holding part of the shard list cannot aggregate.
#
# Output lands in ${ISALHG_RESULTS_ROOT}/{RQ3_representative,
# RQ2_wellposedness/certificate_validity,RQ6_generation}/ on HOME; harvest with
#   bash scripts/tkde/harvest_from_picasso.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TKDE_USER_ROOT="/mnt/home/users/tic_163_uma/mpascual"

REPO_DIR="${REPO_DIR:-${TKDE_USER_ROOT}/fscratch/repos/IsalHG-tkde}"
LOGS_DIR="${TKDE_LOGS_DIR:-${TKDE_USER_ROOT}/execs/tkde/logs}"
RESULTS_ROOT="${ISALHG_RESULTS_ROOT:-${TKDE_USER_ROOT}/results/IEEETKDE}"
DATA_ROOT="${ISALHG_DATA_ROOT:-${TKDE_USER_ROOT}/fscratch/datasets/isalhg_tkde}"

# The frozen corpora live under the DATA root on Picasso, while
# experiments.tkde.corpora resolves them under the RESULTS root by default. The
# runners take the base directory explicitly for exactly this reason.
CORPORA_ROOT="${TKDE_CORPORA_ROOT:-${DATA_ROOT}}"

N_SHARDS="${TKDE_N_SHARDS:-1}"
N_TASKS="${TKDE_N_TASKS:-1}"
MAX_CONCURRENT="${TKDE_MAX_CONCURRENT:-2}"
WALL="${TKDE_WALL:-0-08:00:00}"
START_CUTOFF_S="${TKDE_START_CUTOFF_S:-19800}"

WORKER="${SCRIPT_DIR}/rq3_worker.sh"
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

# Picasso's Lua sbatch wrapper prepends ANSI codes and a multi-line warning to
# --parsable output. Take the LAST line first: a line-by-line sed leaves the
# banner's newlines in place and the guard then fires AFTER the job was
# submitted, leaving an untracked job on the cluster.
_clean_job_id() {
    tail -n 1 <<<"$1" | sed -e 's/\x1b\[[0-9;]*[a-zA-Z]//g' -e 's/[^0-9]//g'
}

if [[ "${SMOKE}" == "1" ]]; then
    # The one job of this research question allowed under the two-hour floor:
    # it proves the deployed runner on a compute node before the campaign queues.
    ARGS=(
        --job-name=tkde-rq3-smoke
        --time=0-00:30:00
        --output="${LOGS_DIR}/tkde-rq3-smoke_%j.out"
        --error="${LOGS_DIR}/tkde-rq3-smoke_%j.err"
        --export="ALL,REPO_DIR=${REPO_DIR},ISALHG_RESULTS_ROOT=${RESULTS_ROOT},ISALHG_DATA_ROOT=${DATA_ROOT},TKDE_CORPORA_ROOT=${CORPORA_ROOT},TKDE_LOGS_DIR=${LOGS_DIR},TKDE_SMOKE=1,TKDE_N_SHARDS=1,TKDE_N_TASKS=1,TKDE_RUN_RQ6=0,TKDE_RUN_ANALYZERS=1,TKDE_START_CUTOFF_S=1200"
        "${WORKER}"
    )
else
    # RQ6 and the analyzers ride along only when one task holds every shard.
    RUN_RQ6=0
    RUN_ANALYZERS=0
    if (( N_TASKS == 1 )); then
        RUN_RQ6=1
        RUN_ANALYZERS=1
    fi
    THROTTLE=$(( MAX_CONCURRENT < N_TASKS ? MAX_CONCURRENT : N_TASKS ))
    ARGS=(
        --array="1-${N_TASKS}%${THROTTLE}"
        --time="${WALL}"
        --output="${LOGS_DIR}/tkde-rq3_%A_%a.out"
        --error="${LOGS_DIR}/tkde-rq3_%A_%a.err"
        --export="ALL,REPO_DIR=${REPO_DIR},ISALHG_RESULTS_ROOT=${RESULTS_ROOT},ISALHG_DATA_ROOT=${DATA_ROOT},TKDE_CORPORA_ROOT=${CORPORA_ROOT},TKDE_LOGS_DIR=${LOGS_DIR},TKDE_SMOKE=0,TKDE_N_SHARDS=${N_SHARDS},TKDE_N_TASKS=${N_TASKS},TKDE_RUN_RQ6=${RUN_RQ6},TKDE_RUN_ANALYZERS=${RUN_ANALYZERS},TKDE_START_CUTOFF_S=${START_CUTOFF_S}"
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

echo "Submitted RQ3 job: ${JOB_ID}"
echo "Monitor:  sacct -j ${JOB_ID} -X -n -P -o JobID,State,Elapsed"
echo "Logs:     ${LOGS_DIR}/tkde-rq3_${JOB_ID}_*.out"
echo "Results:  ${RESULTS_ROOT}/RQ3_representative/"
