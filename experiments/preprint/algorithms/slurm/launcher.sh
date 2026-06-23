#!/usr/bin/env bash
# Submit one SLURM job per algorithm for the IsalHG algorithm-benchmark
# preprint study (7 jobs total). Each job uses 16 CPUs, 32 GB RAM,
# 24 h wallclock; CPU-only (no --constraint=dgx).
#
# Usage:
#   bash launcher.sh                  # submit all 7 jobs
#   bash launcher.sh --dry-run        # print sbatch commands, don't submit
#   bash launcher.sh greedy_min       # submit one specific algorithm

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---- Configurable ----------------------------------------------------------
export CONDA_ENV_NAME="isalhg"
export REPO_DIR="/mnt/home/users/tic_163_uma/mpascual/fscratch/repos/IsalHG"
export RESULTS_ROOT="/mnt/home/users/tic_163_uma/mpascual/fscratch/isalhg_results/preprint/algorithms/full"

ALL_ALGOS=(
    greedy_single
    greedy_min
    greedy_min_inplace
    greedy_min_wl_pruned
    greedy_min_inplace_wl_pruned
    exhaustive
    pruned_exhaustive
)

# ---- Argument parsing ------------------------------------------------------
DRY_RUN=false
TARGET_ALGOS=()
for arg in "$@"; do
    case "${arg}" in
        --dry-run) DRY_RUN=true ;;
        -*)        echo "[FATAL] unknown flag ${arg}"; exit 2 ;;
        *)         TARGET_ALGOS+=("${arg}") ;;
    esac
done
if [[ ${#TARGET_ALGOS[@]} -eq 0 ]]; then
    TARGET_ALGOS=("${ALL_ALGOS[@]}")
fi

# ---- Submit per algorithm --------------------------------------------------
for ALGO in "${TARGET_ALGOS[@]}"; do
    LOGS_DIR="${HOME}/execs/isalhg_preprint_algorithms/${ALGO}/logs"
    mkdir -p "${LOGS_DIR}"

    SBATCH_CMD="sbatch --parsable \
        --job-name=hg-${ALGO} \
        --output=${LOGS_DIR}/${ALGO}_%j.out \
        --error=${LOGS_DIR}/${ALGO}_%j.err \
        --export=ALL,CONDA_ENV_NAME=${CONDA_ENV_NAME},REPO_DIR=${REPO_DIR},RESULTS_ROOT=${RESULTS_ROOT},ALGORITHM_NAME=${ALGO} \
        ${SCRIPT_DIR}/worker.sh"

    if ${DRY_RUN}; then
        echo "[DRY-RUN] ${SBATCH_CMD}"
    else
        JOB_ID=$(eval "${SBATCH_CMD}")
        echo "Submitted ${ALGO} -> job ${JOB_ID}"
        echo "  Monitor:  squeue -j ${JOB_ID}"
        echo "  Logs:     ${LOGS_DIR}/${ALGO}_${JOB_ID}.out"
    fi
done
