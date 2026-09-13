#!/usr/bin/env bash
# Submit RQ3 v2 (the golden record) to Picasso.
#
# Run this ON PICASSO's login node, from the deployed private tree:
#   bash slurm/tkde/rq3v2_launcher.sh --dry-run     # print the sbatch command
#   bash slurm/tkde/rq3v2_launcher.sh --test-only   # sbatch --test-only
#   bash slurm/tkde/rq3v2_launcher.sh --smoke       # one short task on a tiny cell
#   bash slurm/tkde/rq3v2_launcher.sh               # the full campaign
#
# Deployment, ruled by the orchestrator on 2026-09-13 after FSCRATCH was measured
# at its file quota with the grace period expired:
#   * the runner tree is PRIVATE and on HOME  (~/repos/IsalHG-rq3v2), because a
#     mkdir under ~/fscratch/repos now fails with "Disk quota exceeded";
#   * the conda environment is the SHARED isalhg-tkde on FSCRATCH, read-only and
#     never rebuilt: this campaign changes nothing under src/, so a private env
#     would rebuild a byte-identical extension for nothing;
#   * the corpora are read-only on FSCRATCH;
#   * every result lands on HOME under ~/results/IEEETKDE_ow/.
# The editable install resolves isalhg.* through the environment's finder to the
# shared IsalHG-tkde checkout while PYTHONPATH takes experiments.* from REPO_DIR,
# which is the isolation that matters between two agents sharing one env.
#
# Sizing. The default array is deliberately coarse: SCBI asks for the fewest,
# longest tasks (soporte@scbi.uma.es, 2026-08-07, two-hour floor). Set
# TKDE_N_SHARDS and TKDE_N_TASKS from the measured per-collection cost in
# RQ3V2_PILOT.md rather than from these defaults.
#
# Output lands in ${ISALHG_RESULTS_ROOT}/RQ3v2_golden_record/ on HOME; harvest
# with scripts/tkde/harvest_from_picasso.sh.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TKDE_USER_ROOT="/mnt/home/users/tic_163_uma/mpascual"

# HOME, not FSCRATCH: the quota there is exhausted and writes are refused.
REPO_DIR="${REPO_DIR:-${TKDE_USER_ROOT}/repos/IsalHG-rq3v2}"
LOGS_DIR="${TKDE_LOGS_DIR:-${TKDE_USER_ROOT}/execs/tkde/logs}"
RESULTS_ROOT="${ISALHG_RESULTS_ROOT:-${TKDE_USER_ROOT}/results/IEEETKDE_ow}"
DATA_ROOT="${ISALHG_DATA_ROOT:-${TKDE_USER_ROOT}/fscratch/datasets/isalhg_tkde}"
CONDA_ENV="${TKDE_CONDA_ENV:-isalhg-tkde}"
CONDA_PREFIX_DIR="${TKDE_CONDA_PREFIX:-${TKDE_USER_ROOT}/fscratch/conda_envs/${CONDA_ENV}}"

# experiments.tkde.corpora resolves the corpora under the RESULTS root by
# default; on Picasso they live under the DATA root, so the runner is told.
CORPORA_ROOT="${TKDE_CORPORA_ROOT:-${DATA_ROOT}}"

N_SHARDS="${TKDE_N_SHARDS:-486}"
N_TASKS="${TKDE_N_TASKS:-122}"
# 64 tasks x 4 cpus = 256 cores, well inside the 9,000-core QOS cap, and it
# halves the makespan against a throttle of 32: the campaign runs in two rounds
# of tasks rather than four.
MAX_CONCURRENT="${TKDE_MAX_CONCURRENT:-64}"
WALL="${TKDE_WALL:-0-08:00:00}"
START_CUTOFF_S="${TKDE_START_CUTOFF_S:-21600}"

WORKER="${SCRIPT_DIR}/rq3v2_worker.sh"
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

# A path under FSCRATCH here would be written to at run time and the job would
# die when the quota refused it. Refuse at submission instead.
for GUARDED in "${RESULTS_ROOT}" "${LOGS_DIR}" "${REPO_DIR}"; do
    case "${GUARDED}" in
        */fscratch/*)
            echo "ERROR: ${GUARDED} is under FSCRATCH, which is read-only for this campaign" >&2
            exit 2
            ;;
    esac
done

mkdir -p "${LOGS_DIR}" "${RESULTS_ROOT}"

# Picasso's Lua sbatch wrapper prepends ANSI codes and a multi-line warning to
# --parsable output. Take the LAST line first: a line-by-line sed leaves the
# banner's newlines in place and the guard then fires AFTER the job was
# submitted, leaving an untracked job on the cluster.
_clean_job_id() {
    tail -n 1 <<<"$1" | sed -e 's/\x1b\[[0-9;]*[a-zA-Z]//g' -e 's/[^0-9]//g'
}

COMMON_EXPORT="REPO_DIR=${REPO_DIR},ISALHG_RESULTS_ROOT=${RESULTS_ROOT}"
COMMON_EXPORT="${COMMON_EXPORT},ISALHG_DATA_ROOT=${DATA_ROOT}"
COMMON_EXPORT="${COMMON_EXPORT},TKDE_CORPORA_ROOT=${CORPORA_ROOT}"
COMMON_EXPORT="${COMMON_EXPORT},TKDE_LOGS_DIR=${LOGS_DIR}"
COMMON_EXPORT="${COMMON_EXPORT},TKDE_CONDA_ENV=${CONDA_ENV}"
COMMON_EXPORT="${COMMON_EXPORT},TKDE_CONDA_PREFIX=${CONDA_PREFIX_DIR}"

if [[ "${SMOKE}" == "1" ]]; then
    # The one job of this research question allowed under the two-hour floor: it
    # proves the deployed runner on a compute node before the campaign queues.
    ARGS=(
        --job-name=tkde-rq3v2-smoke
        --time=0-00:30:00
        --output="${LOGS_DIR}/tkde-rq3v2-smoke_%j.out"
        --error="${LOGS_DIR}/tkde-rq3v2-smoke_%j.err"
        --export="ALL,${COMMON_EXPORT},TKDE_SMOKE=1,TKDE_N_SHARDS=1,TKDE_N_TASKS=1,TKDE_RUN_ANALYZERS=1,TKDE_START_CUTOFF_S=1200"
        "${WORKER}"
    )
else
    # The analyzer rides along only when one task holds every shard; otherwise it
    # would write an experiment-level table from a partial view.
    RUN_ANALYZERS=0
    (( N_TASKS == 1 )) && RUN_ANALYZERS=1
    THROTTLE=$(( MAX_CONCURRENT < N_TASKS ? MAX_CONCURRENT : N_TASKS ))
    ARGS=(
        --array="1-${N_TASKS}%${THROTTLE}"
        --time="${WALL}"
        --output="${LOGS_DIR}/tkde-rq3v2_%A_%a.out"
        --error="${LOGS_DIR}/tkde-rq3v2_%A_%a.err"
        --export="ALL,${COMMON_EXPORT},TKDE_SMOKE=0,TKDE_N_SHARDS=${N_SHARDS},TKDE_N_TASKS=${N_TASKS},TKDE_RUN_ANALYZERS=${RUN_ANALYZERS},TKDE_START_CUTOFF_S=${START_CUTOFF_S}"
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

echo "Submitted RQ3 v2 job: ${JOB_ID}"
echo "Monitor:  sacct -j ${JOB_ID} -X -n -P -o JobID,State,Elapsed"
echo "Memory:   sacct -j ${JOB_ID} -n -P -o JobID,MaxRSS | grep '\.batch'"
echo "Logs:     ${LOGS_DIR}/tkde-rq3v2*_${JOB_ID}*.out"
echo "Results:  ${RESULTS_ROOT}/RQ3v2_golden_record/"
