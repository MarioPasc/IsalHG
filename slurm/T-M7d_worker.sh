#!/usr/bin/env bash
# T-M7d multi-seed sweep — SLURM array worker.
#
# Submit via T-M7d_launcher.sh (sets all environment variables).
# Do NOT submit this script directly.
#
# Environment variables injected by the launcher:
#   CONDA_ENV_NAME       — conda env (isalhg)
#   REPO_DIR             — absolute path to the IsalHG repo root on Picasso
#   T_M7D_ENVELOPE       — path to stratum_b_feasibility_envelope.json
#   T_M7D_OUTPUT_DIR     — root output directory for all results
#   T_M7D_N_SEEDS        — seeds per cell (default 20)
#   T_M7D_N_CORPUS       — ER instances per Stratum B seed (default 60)
#   T_M7D_PAIRS_FILE     — text file: one "<cell_key> <dist_name>" per line
#
# SLURM directives:
#   CPU-only (no --gres, no GPU constraint): distance computation and canonical
#   strings are pure-Python / C++ CPU work.
#   1 h wall time: all cells finish in < 10 min; 1 h is 6× safety margin.
#   8 GB RAM: generous for the D-matrix cache (N≤60, float64 = 28 KB max).

#SBATCH --job-name=T-M7d-sweep
#SBATCH --time=0-04:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --constraint=cpu

set -euo pipefail

START_TIME=$(date +%s)

# ── Header ────────────────────────────────────────────────────────────────────
echo "=========================================="
echo "Job:          ${SLURM_JOB_ID:-local}"
echo "Array task:   ${SLURM_ARRAY_TASK_ID:-N/A}"
echo "Node:         $(hostname)"
echo "Start:        $(date)"
echo "Repo dir:     ${REPO_DIR:-UNSET}"
echo "Output dir:   ${T_M7D_OUTPUT_DIR:-UNSET}"
echo "Pairs file:   ${T_M7D_PAIRS_FILE:-UNSET}"
echo "=========================================="

# ── Validate injected variables ───────────────────────────────────────────────
: "${CONDA_ENV_NAME:?CONDA_ENV_NAME not set — submit via T-M7d_launcher.sh}"
: "${REPO_DIR:?REPO_DIR not set}"
: "${T_M7D_ENVELOPE:?T_M7D_ENVELOPE not set}"
: "${T_M7D_OUTPUT_DIR:?T_M7D_OUTPUT_DIR not set}"
: "${T_M7D_N_SEEDS:?T_M7D_N_SEEDS not set}"
: "${T_M7D_N_CORPUS:?T_M7D_N_CORPUS not set}"
: "${T_M7D_PAIRS_FILE:?T_M7D_PAIRS_FILE not set}"

# ── Resolve (cell_key, dist_name) for this array task ────────────────────────
TASK_IDX="${SLURM_ARRAY_TASK_ID:-0}"
LINE=$(sed -n "$((TASK_IDX + 1))p" "${T_M7D_PAIRS_FILE}" | tr -d '\r')
if [[ -z "${LINE}" ]]; then
    echo "[FATAL] Empty pair at array index ${TASK_IDX}" >&2
    exit 1
fi
CELL_KEY="${LINE%% *}"
DIST_NAME="${LINE##* }"
echo "Cell key:     ${CELL_KEY}"
echo "Dist name:    ${DIST_NAME}"
echo ""

# ── Environment ───────────────────────────────────────────────────────────────
module_loaded=0
for m in miniconda/3 miniconda3 Miniconda3 anaconda3 Anaconda3 miniforge mambaforge; do
    if module avail 2>&1 | grep -qiE "(^|/)${m}([[:space:]]|/|$)"; then
        module load "$m" && module_loaded=1 && break
    fi
done
[[ "$module_loaded" -eq 0 ]] && echo "[env] No conda module found; assuming conda in PATH."

if command -v conda >/dev/null 2>&1; then
    source "$(conda info --base)/etc/profile.d/conda.sh" || true
    conda activate "${CONDA_ENV_NAME}" 2>/dev/null || source activate "${CONDA_ENV_NAME}"
else
    source activate "${CONDA_ENV_NAME}"
fi

cd "${REPO_DIR}"
export PYTHONPATH="${REPO_DIR}/src:${REPO_DIR}:${PYTHONPATH:-}"
export PYTHONUNBUFFERED=1
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-4}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK:-4}"

echo "Python:       $(which python)"
echo "Git commit:   $(git -C "${REPO_DIR}" rev-parse --short HEAD 2>/dev/null || echo n/a)"
echo ""

# ── Determine which stratum to run ────────────────────────────────────────────
if [[ "${CELL_KEY}" == "stratum_a" ]]; then
    STRATUM_FLAG="--stratum a"
else
    STRATUM_FLAG="--stratum b"
fi

# ── Run the sweep for this (cell_key, dist_name) ─────────────────────────────
# --cell-key and --dist-name together narrow the sweep to exactly one (cell, rep)
# so 20 seeds of that pair are computed and cached.  The aggregation step
# (aggregate_cell_stats, _write_cell_stats) also runs inline and writes the
# per-cell stats JSON.
python -m experiments.article.analysis.sweep_multi_seed \
    --envelope "${T_M7D_ENVELOPE}" \
    --output-root "${T_M7D_OUTPUT_DIR}" \
    --n-seeds "${T_M7D_N_SEEDS}" \
    --n-corpus "${T_M7D_N_CORPUS}" \
    ${STRATUM_FLAG} \
    --cell-key "${CELL_KEY}" \
    --dist-name "${DIST_NAME}"

# ── Footer ────────────────────────────────────────────────────────────────────
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo ""
echo "=========================================="
echo "Finished:  $(date)"
echo "Duration:  $((ELAPSED / 3600))h $(((ELAPSED / 60) % 60))m $((ELAPSED % 60))s"
echo "Cell key:  ${CELL_KEY}"
echo "Dist name: ${DIST_NAME}"
echo "Output:    ${T_M7D_OUTPUT_DIR}/"
echo "=========================================="
