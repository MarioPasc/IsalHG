#!/usr/bin/env bash
# Submit RQ2 on the ordered walk -- the D-ART6 swap (T-KBab), as TWO arrays.
#
# The census units read the N x N matrices the shared matrices job wrote, so
# they carry --dependency=afterok on it when one is named; everything else
# (exactness at zero, bipartite metricity, the oracle ceiling, the HyperCOT
# timing row) depends on nothing and starts immediately.
#
#   bash slurm/tkde/rq2_ow_launcher.sh --test-only
#   bash slurm/tkde/rq2_ow_launcher.sh --smoke
#   MATRICES_JOB_ID=2213202 bash slurm/tkde/rq2_ow_launcher.sh
#
# This is rq2_launcher.sh with three changes and no others: the config is
# configs/rq2_ow.yaml (the shared launcher hard-codes rq2.yaml at line 19 with
# no environment override, which is why a thin wrapper was not possible), the
# worker is rq2_ow_worker.sh, and REPO_DIR / ISALHG_RESULTS_ROOT default to this
# agent's private deployment so nothing collides with the rq3v2 tree or with the
# canonical IsalHG-tkde checkout.
#
# The conda env stays the SHARED isalhg-tkde. This wave changes nothing under
# src/**, so `isalhg.*` must keep resolving through that env's editable install;
# a private env would rebuild an identical extension and break the canonical-tree
# assertion every worker here carries.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TKDE_USER_ROOT="/mnt/home/users/tic_163_uma/mpascual"
REPO_DIR="${REPO_DIR:-${TKDE_USER_ROOT}/fscratch/repos/IsalHG-rq8}"
ISALHG_RESULTS_ROOT="${ISALHG_RESULTS_ROOT:-${TKDE_USER_ROOT}/results/IEEETKDE_ow}"
LOGS_DIR="${TKDE_LOGS_DIR:-${TKDE_USER_ROOT}/execs/tkde/logs}"
PY="${PY:-${TKDE_USER_ROOT}/fscratch/conda_envs/isalhg-tkde/bin/python}"
CONFIG="${RQ2_CONFIG:-${REPO_DIR}/experiments/tkde/configs/rq2_ow.yaml}"
mkdir -p "${LOGS_DIR}" "${ISALHG_RESULTS_ROOT}"

# The cached matrices are a shared read-only input; the wave's clean root links
# at them rather than copying (T-KBn precedent). RQ2 also WRITES one through
# this link -- the ndc_substances census it builds itself -- which is intended:
# that matrix belongs in the shared cache, where the next consumer will find it.
MATRICES_SRC="${TKDE_MATRICES_SRC:-${TKDE_USER_ROOT}/results/IEEETKDE/matrices}"
if [[ ! -e "${ISALHG_RESULTS_ROOT}/matrices" ]]; then
    ln -sfn "${MATRICES_SRC}" "${ISALHG_RESULTS_ROOT}/matrices"
    echo "linked ${ISALHG_RESULTS_ROOT}/matrices -> ${MATRICES_SRC}" >&2
fi
for collection in wd50k66 ndc_classes; do
    target="${ISALHG_RESULTS_ROOT}/matrices/${collection}/isal_ow_struct.npy"
    [[ -f "${target}" ]] || {
        echo "FATAL: no cached isal_ow_struct matrix at ${target}" >&2
        echo "       the census cannot run the swap without it." >&2
        exit 1
    }
    echo "  [ok] ${target}" >&2
done

BUNDLE="${BUNDLE:-4}"
MAX_CONCURRENT="${MAX_CONCURRENT:-10}"
WALL="${WALL:-1-00:00:00}"
START_CUTOFF_S="${START_CUTOFF_S:-54000}"
MATRICES_JOB_ID="${MATRICES_JOB_ID:-}"

# Colon-separated on purpose: --export splits on commas and would deliver only
# the first kind, with the rest becoming junk variables and no error.
IMMEDIATE_KINDS="exact0:bipartite:oracle:hypercot"
CENSUS_KINDS="census"

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

COMMON_EXPORT="ALL,REPO_DIR=${REPO_DIR},ISALHG_RESULTS_ROOT=${ISALHG_RESULTS_ROOT},RQ2_CONFIG=${CONFIG}"

if [[ "${MODE}" == "smoke" ]]; then
    JOB_ID=$(submit \
        --job-name=tkde-rq2-ow-smoke \
        --time=0-00:30:00 \
        --output="${LOGS_DIR}/tkde-rq2-ow-smoke_%j.out" \
        --error="${LOGS_DIR}/tkde-rq2-ow-smoke_%j.err" \
        --export="${COMMON_EXPORT},TKDE_SMOKE=1" \
        "${SCRIPT_DIR}/rq2_ow_worker.sh") || exit 1
    echo "Submitted RQ2_ow smoke ${JOB_ID}"
    echo "Log: ${LOGS_DIR}/tkde-rq2-ow-smoke_${JOB_ID}.out"
    exit 0
fi

build_args() { # $1 = colon-separated kinds, $2 = tag
    local kinds="$1" tag="$2" shards tasks throttle
    # --count must run from REPO_DIR: the runner is a package module of the
    # deployed tree, not of slurm/tkde.
    shards=$(cd "${REPO_DIR}" && "${PY}" -m experiments.tkde.rq2 --config "${CONFIG}" \
        --kinds "${kinds//:/,}" --count)
    [[ "${shards}" =~ ^[0-9]+$ ]] || { echo "FATAL: --count returned ${shards@Q}" >&2; return 1; }
    tasks=$(((shards + BUNDLE - 1) / BUNDLE))
    throttle="${MAX_CONCURRENT}"
    ((throttle > tasks)) && throttle="${tasks}"
    ARRAY_ARGS=(
        --array="0-$((tasks - 1))%${throttle}"
        --job-name="tkde-rq2-ow-${tag}"
        --output="${LOGS_DIR}/tkde-rq2-ow-${tag}_%A_%a.out"
        --error="${LOGS_DIR}/tkde-rq2-ow-${tag}_%A_%a.err"
        --export="${COMMON_EXPORT},RQ2_KINDS=${kinds},N_SHARDS=${shards},N_TASKS=${tasks},START_CUTOFF_S=${START_CUTOFF_S}"
        --time="${WALL}"
    )
    echo "RQ2_ow ${tag}: ${shards} shards -> ${tasks} tasks (bundle ${BUNDLE}, throttle ${throttle})" >&2
}

build_args "${IMMEDIATE_KINDS}" "main" || exit 1
MAIN_ARGS=("${ARRAY_ARGS[@]}")
build_args "${CENSUS_KINDS}" "census" || exit 1
CENSUS_ARGS=("${ARRAY_ARGS[@]}")

if [[ "${MODE}" == "test" ]]; then
    sbatch --test-only "${MAIN_ARGS[@]}" "${SCRIPT_DIR}/rq2_ow_worker.sh"
    sbatch --test-only "${CENSUS_ARGS[@]}" "${SCRIPT_DIR}/rq2_ow_worker.sh"
    exit 0
fi

MAIN_ID=$(submit "${MAIN_ARGS[@]}" "${SCRIPT_DIR}/rq2_ow_worker.sh") || exit 1
echo "Submitted RQ2_ow main array ${MAIN_ID}"

DEP_ARGS=()
if [[ -n "${MATRICES_JOB_ID}" ]]; then
    DEP_ARGS=(--dependency="afterok:${MATRICES_JOB_ID}")
else
    echo "NOTE: MATRICES_JOB_ID unset. The isal_ow_struct matrices this census" >&2
    echo "      reads were asserted present above and no matrices job is running," >&2
    echo "      so the census starts against a complete, frozen cache." >&2
fi
CENSUS_ID=$(submit "${CENSUS_ARGS[@]}" "${DEP_ARGS[@]}" "${SCRIPT_DIR}/rq2_ow_worker.sh") || exit 1

if [[ -n "${MATRICES_JOB_ID}" ]]; then
    # sbatch ACCEPTS a malformed dependency and records Dependency=(null), then
    # starts immediately against a half-built cache. The only way to know the
    # dependency took is to read it back.
    if scontrol show job "${CENSUS_ID}" | grep -q 'Dependency=(null)'; then
        echo "FATAL: dependency dropped on the census array; cancelling ${CENSUS_ID}" >&2
        scancel "${CENSUS_ID}"
        exit 1
    fi
    echo "Submitted RQ2_ow census array ${CENSUS_ID} (afterok:${MATRICES_JOB_ID}, verified)"
else
    echo "Submitted RQ2_ow census array ${CENSUS_ID} (no dependency; cache asserted present)"
fi

echo "Monitor: sacct -j ${MAIN_ID},${CENSUS_ID} -X -n -P -o JobID,State,Elapsed"
