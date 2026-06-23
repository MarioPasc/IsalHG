#!/usr/bin/env bash
#SBATCH -J isalhg-algo
#SBATCH --time=2-00:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=128G

set -euo pipefail

START_TIME=$(date +%s)

# ============================================================================
# JOB HEADER (reproducibility)
# ============================================================================
echo "=========================================="
echo "Job:          ${SLURM_JOB_ID:-local}"
echo "Algorithm:    ${ALGORITHM_NAME:-unset}"
echo "Node:         $(hostname)"
echo "Start:        $(date)"
echo "Working dir:  $(pwd)"
echo "Git commit:   $(git -C "${REPO_DIR:-.}" rev-parse --short HEAD 2>/dev/null || echo n/a)"
echo "CPUs:         ${SLURM_CPUS_PER_TASK:-unset}"
echo "=========================================="

# ============================================================================
# ENVIRONMENT
# ============================================================================
module_loaded=0
for m in miniconda3 Miniconda3 anaconda3 Anaconda3 miniforge mambaforge; do
    if module avail 2>/dev/null | grep -qi "^${m}[[:space:]]"; then
        module load "$m" && module_loaded=1 && break
    fi
done
[ "$module_loaded" -eq 0 ] && echo "[env] No conda module; assuming conda in PATH."

if command -v conda >/dev/null 2>&1; then
    source "$(conda info --base)/etc/profile.d/conda.sh" || true
    conda activate "${CONDA_ENV_NAME}" 2>/dev/null || source activate "${CONDA_ENV_NAME}"
else
    source activate "${CONDA_ENV_NAME}"
fi

cd "${REPO_DIR}"
export PYTHONPATH="${REPO_DIR}/src:${REPO_DIR}:${PYTHONPATH:-}"
export PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

# ============================================================================
# COMMAND
# ============================================================================
CONFIG_PATH="${REPO_DIR}/experiments/preprint/algorithms/configs/algo_${ALGORITHM_NAME}.yaml"
OUTPUT_ROOT="${RESULTS_ROOT}/${ALGORITHM_NAME}"
mkdir -p "${OUTPUT_ROOT}"

echo "Config:       ${CONFIG_PATH}"
echo "Output root:  ${OUTPUT_ROOT}"
echo ""

python -m experiments.preprint.algorithms.run_parallel \
    --config "${CONFIG_PATH}" \
    --n-workers "${SLURM_CPUS_PER_TASK}" \
    --output-root "${OUTPUT_ROOT}"

# ============================================================================
# CLEANUP
# ============================================================================
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo ""
echo "Finished:  $(date)"
echo "Duration:  $(($ELAPSED / 3600))h $((($ELAPSED / 60) % 60))m $(($ELAPSED % 60))s"
