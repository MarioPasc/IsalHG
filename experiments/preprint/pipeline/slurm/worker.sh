#!/usr/bin/env bash
# Array-task body for the IsalHG preprint random-hypergraph sweep.
#
# Each task runs ONE (backend, n, r, c, seed) cell through
# experiments.preprint.pipeline.run_cell. The SBATCH headers below are
# defaults — launcher.sh overrides --time / --mem-per-cpu / --array per
# memory tier (fast vs slow). The orchestrator's idempotent JSON-skip
# makes resubmission a no-op for completed cells.
#
# Required exported env (set by launcher.sh):
#   CONDA_ENV_NAME   conda env to activate (default: isalhg)
#   REPO_DIR         repo root on the node
#   CONFIG_PATH      path to the preprint YAML
#   OUTPUT_ROOT      cell-JSON output directory
#   TIER             fast | slow | all

#SBATCH -J isalhg-preprint
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=01:30:00
#SBATCH --mem-per-cpu=8G

set -euo pipefail
START_TIME=$(date +%s)

# ============================================================================
# JOB HEADER (reproducibility)
# ============================================================================
echo "=========================================="
echo "Job:          ${SLURM_JOB_ID:-local}"
echo "Array task:   ${SLURM_ARRAY_TASK_ID:-unset} / ${SLURM_ARRAY_TASK_COUNT:-unset}"
echo "Tier:         ${TIER:-unset}"
echo "Node:         $(hostname)"
echo "Start:        $(date)"
echo "Working dir:  $(pwd)"
echo "Git commit:   $(git -C "${REPO_DIR:-.}" rev-parse --short HEAD 2>/dev/null || echo n/a)"
echo "CPUs:         ${SLURM_CPUS_PER_TASK:-unset}"
echo "Memory:       ${SLURM_MEM_PER_CPU:-unset} MB/CPU"
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
mkdir -p "${OUTPUT_ROOT}"

echo "Config:       ${CONFIG_PATH}"
echo "Output root:  ${OUTPUT_ROOT}"
echo "Cell index:   ${SLURM_ARRAY_TASK_ID}"
echo ""

# Wrap python in `timeout --kill-after=10` so the entire process tree
# (including any orphaned multiprocessing children with stuck C++
# worker threads) gets SIGKILL'd. Without this, SLURM keeps the task
# slot busy until the wall-clock limit because the cgroup is non-empty
# even after the Python parent exits. PIPELINE_TASK_TIMEOUT defaults to
# 1300 s (=22 min) — comfortably above the 600 s per-call IsalHG budget
# but short enough to free slots quickly when work is done.
TASK_TIMEOUT="${PIPELINE_TASK_TIMEOUT:-1300}"
timeout --kill-after=10 "${TASK_TIMEOUT}" python -m experiments.preprint.pipeline.run_cell \
    --config "${CONFIG_PATH}" \
    --tier "${TIER}" \
    --cell-index "${SLURM_ARRAY_TASK_ID}" \
    --output-root "${OUTPUT_ROOT}" \
    || EXITCODE=$?
echo "python exit: ${EXITCODE:-0}"

# ============================================================================
# CLEANUP
# ============================================================================
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo ""
echo "Finished:  $(date)"
echo "Duration:  $(($ELAPSED / 3600))h $((($ELAPSED / 60) % 60))m $(($ELAPSED % 60))s"
