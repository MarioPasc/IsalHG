#!/usr/bin/env bash
# Submit RQ8 -- valid completion of a record (wave 2026-09-13-headline-w0, agent rq8).
#
#   bash slurm/tkde/rq8_launcher.sh              # full run, 27 seeds
#   bash slurm/tkde/rq8_launcher.sh --smoke      # the --smoke configuration
#   bash slurm/tkde/rq8_launcher.sh --test-only
#   bash slurm/tkde/rq8_launcher.sh --dry-run
#
# No --dependency: RQ8 reads the frozen corpora and computes every word,
# certificate and model itself, so it waits on no matrices job.
#
# This launcher belongs to a PRIVATE deployment. It defaults REPO_DIR to
# ~/repos/IsalHG-rq8 so it cannot collide with the rq3v2 agent's tree or with
# the canonical IsalHG-tkde checkout, and ISALHG_RESULTS_ROOT to
# ~/results/IEEETKDE_ow, the wave's clean root (T-KBn precedent). The conda env
# stays the SHARED isalhg-tkde: this wave changes nothing under src/**, so
# `isalhg.*` must keep resolving through that env's editable install --- which
# is also what every worker in this directory asserts.
#
# The runner tree is on HOME, not FSCRATCH, against this directory's own
# convention. Measured 2026-09-13: FSCRATCH is at 276.3k files against a 250.0k
# soft quota whose GRACE HAS EXPIRED, so it is read-only --- `mkdir
# ~/fscratch/repos/...` returns "Disk quota exceeded" and no tree can be
# deployed there at all. HOME had 16.3k of 35.0k files, and a runner tree costs
# about 900. The convention exists because HOME's file quota is the scarce one;
# right now the measured state is the reverse. Inputs that are NOT written stay
# where they are: the env and the frozen corpora are read from FSCRATCH.
#
# Prints the job id on the last line.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TKDE_USER_ROOT="/mnt/home/users/tic_163_uma/mpascual"

export REPO_DIR="${REPO_DIR:-${TKDE_USER_ROOT}/repos/IsalHG-rq8}"
export ISALHG_RESULTS_ROOT="${ISALHG_RESULTS_ROOT:-${TKDE_USER_ROOT}/results/IEEETKDE_ow}"
LOGS_DIR="${TKDE_LOGS_DIR:-${TKDE_USER_ROOT}/execs/tkde/logs}"
CONFIG="${RQ8_CONFIG:-experiments/tkde/configs/rq8.yaml}"
mkdir -p "${LOGS_DIR}"

# common.sh defines PY (the env is NOT under ~/.conda on Picasso) and puts the
# deployed tree first on PYTHONPATH, so --list-units decodes THIS checkout.
# shellcheck source=/dev/null
source "${REPO_DIR}/slurm/tkde/common.sh"

MODE="submit"
SMOKE=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) MODE="dry"; shift ;;
        --test-only) MODE="test"; shift ;;
        --smoke) SMOKE=1; shift ;;
        *) echo "ERROR: unknown option $1" >&2; exit 2 ;;
    esac
done

# Picasso's Lua sbatch wrapper prepends ANSI codes and a multi-line warning to
# --parsable output. Take the LAST line FIRST: a line-by-line sed leaves the
# banner's newlines in place, and the numeric guard then fires AFTER the job was
# submitted -- leaving an untracked job running on the cluster.
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

# Ask the DECODER how many units there are, with the arguments the worker will
# use. A hard-coded count cannot disagree with the decode, so it cannot catch a
# decode that changed -- and the decode is the part most likely to change.
N_UNITS=$("${PY}" -m experiments.tkde.rq8 --config "${CONFIG}" --list-units | wc -l)
[[ "${N_UNITS}" =~ ^[0-9]+$ ]] && (( N_UNITS > 0 )) || {
    echo "FATAL: --list-units gave ${N_UNITS@Q}" >&2; exit 1
}

# One task. See the worker header: 81 units at 5.6-9.4 s each is ~12 minutes,
# and the two-hour floor forbids MANY short placements, not one short job.
N_TASKS=1
MAX_CONCURRENT=1

EXPORTS="ALL,REPO_DIR=${REPO_DIR},ISALHG_RESULTS_ROOT=${ISALHG_RESULTS_ROOT}"
EXPORTS="${EXPORTS},RQ8_CONFIG=${CONFIG},RQ8_N_TASKS=${N_TASKS}"
TIME_LIMIT="0-02:00:00"
if [[ "${SMOKE}" -eq 1 ]]; then
    EXPORTS="${EXPORTS},TKDE_SMOKE=1"
    TIME_LIMIT="0-00:30:00"
fi

SBATCH_ARGS=(
    --array="0-$((N_TASKS - 1))%${MAX_CONCURRENT}"
    --time="${TIME_LIMIT}"
    --output="${LOGS_DIR}/tkde-rq8_%A_%a.out"
    --error="${LOGS_DIR}/tkde-rq8_%A_%a.err"
    --export="${EXPORTS}"
    "${SCRIPT_DIR}/rq8_worker.sh"
)

echo "units=${N_UNITS} tasks=${N_TASKS} smoke=${SMOKE} repo=${REPO_DIR}" >&2
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
echo "Submitted tkde-rq8 as ${JOB_ID} (${N_TASKS} task over ${N_UNITS} units)" >&2
echo "  logs: ${LOGS_DIR}/tkde-rq8_${JOB_ID}_*.out" >&2
echo "${JOB_ID}"
