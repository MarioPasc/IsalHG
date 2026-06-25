#!/usr/bin/env bash
# Submit the IsalHG preprint random-hypergraph sweep on Picasso.
#
# Pattern: one SLURM array, one task per (backend, n, r, c, seed) cell
# (PREPRINT.md §4.5). Submitted as TWO arrays split by memory tier:
#
#   fast tier (n < 1000 OR c < 25):
#       --time=01:30:00  --mem-per-cpu=8G   --array=0-<N-1>%128
#   slow tier (n = 1000 AND c = 25):
#       --time=04:00:00  --mem-per-cpu=32G  --array=0-<N-1>%32
#
# The orchestrator's idempotent JSON-skip makes resubmission a no-op
# for completed cells, so partial failures replay cleanly.
#
# Usage:
#   bash launcher.sh                  # submit both arrays (full sweep)
#   bash launcher.sh --dry-run        # print sbatch commands, don't submit
#   bash launcher.sh --tier fast      # submit only the fast tier
#   bash launcher.sh --tier slow      # submit only the slow tier
#   bash launcher.sh --smoke          # 4-cell preprint_smoke.yaml (one array)
#   bash launcher.sh --config <path>  # alternate YAML

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---- Configurable ----------------------------------------------------------
export CONDA_ENV_NAME="${CONDA_ENV_NAME:-isalhg}"
export REPO_DIR="${REPO_DIR:-/mnt/home/users/tic_163_uma/mpascual/fscratch/repos/IsalHG}"
export RESULTS_ROOT="${RESULTS_ROOT:-/mnt/home/users/tic_163_uma/mpascual/fscratch/isalhg_results/preprint/pipeline}"

DEFAULT_CONFIG="${REPO_DIR}/experiments/configs/preprint_random_sweep.yaml"
SMOKE_CONFIG="${REPO_DIR}/experiments/configs/preprint_smoke.yaml"

# ---- Argument parsing ------------------------------------------------------
DRY_RUN=false
TIER_FILTER="both"   # both | fast | slow
CONFIG_PATH="${DEFAULT_CONFIG}"
SWEEP_NAME="random_sweep"

while [[ $# -gt 0 ]]; do
    case "${1}" in
        --dry-run)
            DRY_RUN=true; shift ;;
        --smoke)
            CONFIG_PATH="${SMOKE_CONFIG}"
            SWEEP_NAME="smoke"
            TIER_FILTER="all"
            shift ;;
        --tier)
            TIER_FILTER="${2}"; shift 2 ;;
        --config)
            CONFIG_PATH="${2}"; shift 2 ;;
        -h|--help)
            sed -n '2,30p' "${BASH_SOURCE[0]}"; exit 0 ;;
        *)
            echo "[FATAL] unknown flag ${1}" >&2; exit 2 ;;
    esac
done

LOGS_ROOT="${HOME}/execs/isalhg_preprint_pipeline/${SWEEP_NAME}/logs"
OUTPUT_ROOT="${RESULTS_ROOT}/${SWEEP_NAME}"
mkdir -p "${LOGS_ROOT}" "${OUTPUT_ROOT}"

# ---- Count cells per tier --------------------------------------------------
# Use the pipeline's own filter so the launcher and the array task body
# agree on the cell ordering bit-for-bit. Need conda activated to pull
# in PyYAML; the worker re-activates it inside the SLURM job too.
_activate_conda_once() {
    if [[ -n "${_CONDA_READY:-}" ]]; then return; fi
    if command -v module >/dev/null 2>&1; then
        for m in miniconda3 Miniconda3 anaconda3 Anaconda3 miniforge mambaforge; do
            if module avail 2>/dev/null | grep -qi "^${m}[[:space:]]"; then
                module load "$m" >/dev/null 2>&1 && break
            fi
        done
    fi
    if command -v conda >/dev/null 2>&1; then
        # shellcheck disable=SC1091
        source "$(conda info --base)/etc/profile.d/conda.sh" >/dev/null 2>&1 || true
        conda activate "${CONDA_ENV_NAME}" 2>/dev/null || source activate "${CONDA_ENV_NAME}" 2>/dev/null || true
    fi
    export _CONDA_READY=1
}

count_cells() {
    local tier="${1}"
    _activate_conda_once
    ( cd "${REPO_DIR}" && \
      PYTHONPATH="${REPO_DIR}/src:${REPO_DIR}:${PYTHONPATH:-}" \
      python -m experiments.preprint.pipeline.run_cell \
          --config "${CONFIG_PATH}" --tier "${tier}" --count )
}

submit_array() {
    local tier="${1}" n_cells="${2}" wall_time="${3}" mem_per_cpu="${4}" concurrency="${5}"

    if [[ "${n_cells}" -eq 0 ]]; then
        echo "[skip] tier=${tier} has zero cells; nothing to submit"
        return
    fi

    local array_spec="0-$((n_cells - 1))%${concurrency}"
    local job_name="hg-preprint-${tier}"
    # NODE_CONSTRAINT: defaults to avx512 — the isalhg conda env's compiled
    # extensions (pynauty, isalhg.core._core) were built on Intel sd*
    # nodes with AVX-512; AMD sr* nodes hit "Illegal instruction (core
    # dumped)" on import. Override via env if you rebuild for portability.
    local node_constraint="${NODE_CONSTRAINT:-avx512}"
    local sbatch_cmd
    sbatch_cmd=$(cat <<EOF
sbatch --parsable \
    --job-name=${job_name} \
    --output=${LOGS_ROOT}/${tier}_%A_%a.out \
    --error=${LOGS_ROOT}/${tier}_%A_%a.err \
    --array=${array_spec} \
    --time=${wall_time} \
    --mem-per-cpu=${mem_per_cpu} \
    --cpus-per-task=1 \
    --ntasks=1 \
    --constraint=${node_constraint} \
    --export=ALL,CONDA_ENV_NAME=${CONDA_ENV_NAME},REPO_DIR=${REPO_DIR},CONFIG_PATH=${CONFIG_PATH},OUTPUT_ROOT=${OUTPUT_ROOT},TIER=${tier} \
    ${SCRIPT_DIR}/worker.sh
EOF
)

    echo "Tier:        ${tier}"
    echo "Cells:       ${n_cells}"
    echo "Array spec:  ${array_spec}"
    echo "Wall time:   ${wall_time}"
    echo "Mem/CPU:     ${mem_per_cpu}"
    echo "Constraint:  ${node_constraint}"
    echo "Logs:        ${LOGS_ROOT}/${tier}_<jobid>_<task>.out"
    echo "Output:      ${OUTPUT_ROOT}"
    echo ""

    if ${DRY_RUN}; then
        echo "[DRY-RUN] ${sbatch_cmd}"
    else
        JOB_ID=$(eval "${sbatch_cmd}")
        echo "Submitted ${tier} tier -> job ${JOB_ID} (array ${array_spec})"
        echo "  Monitor:  squeue -j ${JOB_ID}"
    fi
    echo "----"
}

# ---- Dispatch --------------------------------------------------------------
echo "=========================================="
echo "Sweep:       ${SWEEP_NAME}"
echo "Config:      ${CONFIG_PATH}"
echo "Tier filter: ${TIER_FILTER}"
echo "Dry run:     ${DRY_RUN}"
echo "Repo dir:    ${REPO_DIR}"
echo "Output root: ${OUTPUT_ROOT}"
echo "=========================================="
echo ""

case "${TIER_FILTER}" in
    both)
        N_FAST=$(count_cells fast)
        N_SLOW=$(count_cells slow)
        submit_array fast "${N_FAST}" "01:30:00" "8G"  "128"
        submit_array slow "${N_SLOW}" "04:00:00" "32G" "32"
        ;;
    fast)
        N_FAST=$(count_cells fast)
        submit_array fast "${N_FAST}" "01:30:00" "8G" "128"
        ;;
    slow)
        N_SLOW=$(count_cells slow)
        submit_array slow "${N_SLOW}" "04:00:00" "32G" "32"
        ;;
    all)
        # Smoke / arbitrary YAML: single array, conservative settings.
        N_ALL=$(count_cells all)
        submit_array all "${N_ALL}" "01:30:00" "8G" "64"
        ;;
    *)
        echo "[FATAL] --tier must be one of: both | fast | slow | all" >&2
        exit 2 ;;
esac

echo "Done."
