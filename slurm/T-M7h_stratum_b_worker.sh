#!/usr/bin/env bash
# T-M7h Stratum B feasibility pilot — SLURM array worker.
#
# Submit via T-M7h_stratum_b_launcher.sh (sets all environment variables).
# Do NOT submit this script directly.
#
# Environment variables injected by the launcher:
#   CONDA_ENV_NAME           — conda env (isalhg)
#   REPO_DIR                 — absolute path to the IsalHG repo root on Picasso
#   T_M7H_CONFIG             — absolute path to stratum_b_sweep.yaml
#   T_M7H_OUTPUT_DIR         — directory for per-block result JSONs
#   T_M7H_BLOCK_KEYS_FILE    — text file with one block key per line (0-indexed)
#
# SLURM directives:
#   CPU-only: no --gres, no --constraint=dgx.
#   3 h wall time per task (30 instances × 300 s timeout = 9 000 s max; 3 h
#   covers normal cases and gives headroom for cluster-slower edges).
#   16 GB RAM: generous for pure-Python canonical-string + Levenshtein work.

#SBATCH --job-name=T-M7h-stratum-b
#SBATCH --time=0-03:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
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
echo "Config:       ${T_M7H_CONFIG:-UNSET}"
echo "Output dir:   ${T_M7H_OUTPUT_DIR:-UNSET}"
echo "Block keys:   ${T_M7H_BLOCK_KEYS_FILE:-UNSET}"
echo "=========================================="

# ── Validate injected variables ───────────────────────────────────────────────
: "${CONDA_ENV_NAME:?CONDA_ENV_NAME not set — submit via T-M7h_stratum_b_launcher.sh}"
: "${REPO_DIR:?REPO_DIR not set}"
: "${T_M7H_CONFIG:?T_M7H_CONFIG not set}"
: "${T_M7H_OUTPUT_DIR:?T_M7H_OUTPUT_DIR not set}"
: "${T_M7H_BLOCK_KEYS_FILE:?T_M7H_BLOCK_KEYS_FILE not set}"

# ── Resolve block key for this array task ─────────────────────────────────────
TASK_IDX="${SLURM_ARRAY_TASK_ID:-0}"
BLOCK_KEY=$(sed -n "$((TASK_IDX + 1))p" "${T_M7H_BLOCK_KEYS_FILE}" | tr -d '[:space:]')
if [[ -z "${BLOCK_KEY}" ]]; then
    echo "[FATAL] Empty block key at array index ${TASK_IDX}" >&2
    exit 1
fi
echo "Block key:    ${BLOCK_KEY}"

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

# ── Output setup ──────────────────────────────────────────────────────────────
mkdir -p "${T_M7H_OUTPUT_DIR}"
OUTPUT_PATH="${T_M7H_OUTPUT_DIR}/block_${BLOCK_KEY}.json"
echo "Output:       ${OUTPUT_PATH}"
echo ""

# ── Run feasibility pilot for this block ──────────────────────────────────────
# --budget 30:   admission threshold (p90 ≤ 30 s + 0 timeouts → ADMITTED)
# --timeout 300: per-instance SIGALRM ceiling (measurement ceiling)
# --n-pilot 30:  30 instances per block (DATA.md §4 requirement)
# --block-key:   restrict to this single block (SLURM array task mode)
python -m experiments.article.feasibility_pilot \
    --config "${T_M7H_CONFIG}" \
    --output "${OUTPUT_PATH}" \
    --block-key "${BLOCK_KEY}" \
    --n-pilot 30 \
    --budget 30.0 \
    --timeout 300.0 \
    --verbose

# ── Footer ────────────────────────────────────────────────────────────────────
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo ""
echo "=========================================="
echo "Finished:  $(date)"
echo "Duration:  $((ELAPSED / 3600))h $(((ELAPSED / 60) % 60))m $((ELAPSED % 60))s"
echo "Block:     ${BLOCK_KEY}"
echo "Output:    ${OUTPUT_PATH}"
echo "=========================================="
