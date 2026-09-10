#!/usr/bin/env bash
# Submit the 600 s tail characterisation (T-KBp) to Picasso.
#
#   bash tail600_launcher.sh --test-only
#   bash tail600_launcher.sh --smoke
#   bash tail600_launcher.sh
#   bash tail600_launcher.sh --no-sweep
#
# This is NOT an RQ job. D-ART5 decision 2: the published budget stays 60 s and
# the 600 s pass is "a re-run *of the censored tail*, i.e. characterisation by
# definition, never a row". Rows land in TAIL600_characterisation/, outside every
# RQ tree, and carry kind="tail_characterisation".
#
# ---------------------------------------------------------------------------
# Shard arithmetic
# ---------------------------------------------------------------------------
# Work list (RQ1 merged M3 census, measured 2026-09-10):
#     wstar_orbit   77 censored members  (70 ndc_classes + 7 wd50k66)
#     wstar_rank    53 censored members  (all ndc_classes; a strict SUBSET of
#                                         the 77 -- the union is 77 members)
#     total        130 (member, arm) calls
#
# Worst case is every call hitting the ceiling, which is the case to size for:
#     130 calls x 600 s                          = 78,000 s = 21.7 h sequential
#
# With n_shards = 16 (SHARDS below, mirrored in configs/tail600.yaml):
#     ceil(130 / 16)                             = 9 calls in the largest shard
#     9 x (600 s budget + ~10 s fork/join)       = 5,490 s = 1.53 h of payload
#   + corpus load: ndc_classes is 1,381 members and wd50k66 is 3,988; a shard
#     touches at most both, and a stride shard over a collection-major work list
#     loads each once                            ~   900 s = 0.25 h
#     -----------------------------------------------------------------------
#     worst case per task                        = 6,390 s = 1.78 h
#
# WALL is 4 h, so the worst-case task uses 44 % of its wall -- no task
# approaches it, which is the point: a task killed at the wall loses whatever
# rows the copy-back has not yet mirrored, and a 600 s budget makes each lost
# call expensive. Sixteen tasks at MAX_CONCURRENT = 16 finish the whole
# measurement inside one wall.
#
# BUNDLE is 1 by design: unlike RQ7's minute-scale cells, one shard here is
# already 1.5 h of payload, so bundling would push a task towards its wall for
# no scheduling gain.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TKDE_USER_ROOT="/mnt/home/users/tic_163_uma/mpascual"
REPO_DIR="${REPO_DIR:-${TKDE_USER_ROOT}/fscratch/repos/IsalHG-tkde}"
LOGS_DIR="${TKDE_USER_ROOT}/execs/tkde/logs"
PY="${PY:-${TKDE_USER_ROOT}/fscratch/conda_envs/isalhg-tkde/bin/python}"
CONFIG="${REPO_DIR}/experiments/tkde/configs/tail600.yaml"
mkdir -p "${LOGS_DIR}"

BUNDLE="${BUNDLE:-1}"
MAX_CONCURRENT="${MAX_CONCURRENT:-16}"
WALL="${WALL:-0-04:00:00}"
START_CUTOFF_S="${START_CUTOFF_S:-12600}"

# sbatch --parsable can emit ANSI colour on this cluster, so the id is stripped
# to digits before it is used as a dependency (RQ7 launcher, same guard).
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
        --job-name=tkde-tail600-smoke \
        --time=0-00:30:00 \
        --output="${LOGS_DIR}/tkde-tail600-smoke_%j.out" \
        --error="${LOGS_DIR}/tkde-tail600-smoke_%j.err" \
        --export="${COMMON_EXPORT},TKDE_SMOKE=1" \
        "${SCRIPT_DIR}/tail600_worker.sh") || exit 1
    echo "Submitted tail600 smoke ${JOB_ID}"
    echo "Log: ${LOGS_DIR}/tkde-tail600-smoke_${JOB_ID}.out"
    exit 0
fi

# The runner is a package module of the DEPLOYED tree, not of slurm/tkde, so
# --count must run from REPO_DIR or it dies with ModuleNotFoundError and the
# array size is never derived (RQ7 launcher, same failure).
N_SHARDS=$(cd "${REPO_DIR}" && "${PY}" -m experiments.tkde.tail600 --config "${CONFIG}" --count)
[[ "${N_SHARDS}" =~ ^[0-9]+$ ]] || { echo "FATAL: --count returned ${N_SHARDS@Q}" >&2; exit 1; }
N_TASKS=$(( (N_SHARDS + BUNDLE - 1) / BUNDLE ))
(( MAX_CONCURRENT > N_TASKS )) && MAX_CONCURRENT="${N_TASKS}"

ARGS=(
    --array="0-$((N_TASKS - 1))%${MAX_CONCURRENT}"
    --output="${LOGS_DIR}/tkde-tail600_%A_%a.out"
    --error="${LOGS_DIR}/tkde-tail600_%A_%a.err"
    --export="${COMMON_EXPORT},N_SHARDS=${N_SHARDS},N_TASKS=${N_TASKS},START_CUTOFF_S=${START_CUTOFF_S}"
    --time="${WALL}"
    "${SCRIPT_DIR}/tail600_worker.sh"
)

echo "tail600: ${N_SHARDS} shards -> ${N_TASKS} tasks (bundle ${BUNDLE}, throttle ${MAX_CONCURRENT}, wall ${WALL})"

if [[ "${MODE}" == "test" ]]; then
    sbatch --test-only "${ARGS[@]}"
    exit 0
fi

JOB_ID=$(submit "${ARGS[@]}") || exit 1
echo "Submitted tail600 array ${JOB_ID} (${N_TASKS} tasks)"

if [[ "${NO_SWEEP}" -eq 0 ]]; then
    SWEEP_ID=$(submit --dependency=afterany:"${JOB_ID}" "${ARGS[@]}") || exit 1
    scontrol show job "${SWEEP_ID}" | grep -q 'Dependency=(null)' && {
        echo "FATAL: dependency dropped on the sweep; cancelling it" >&2
        scancel "${SWEEP_ID}"; exit 1
    }
    echo "Submitted tail600 recovery sweep ${SWEEP_ID} (afterany:${JOB_ID})"
fi

echo "Monitor: sacct -j ${JOB_ID} -X -n -P -o JobID,State,Elapsed"
echo "Score:   ${PY} -m experiments.tkde.analyze_tail600 --root \${ISALHG_RESULTS_ROOT}"
