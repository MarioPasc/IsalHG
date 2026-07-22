#!/usr/bin/env bash
# T-M7h Stratum A feasibility pilot — SLURM worker.
#
# Submit via T-M7h_stratum_a_launcher.sh (sets all environment variables).
# Do NOT submit this script directly.
#
# Environment variables injected by the launcher:
#   CONDA_ENV_NAME        — conda env (isalhg)
#   REPO_DIR              — absolute path to the IsalHG repo root on Picasso
#   T_M7H_A_OUTPUT_DIR    — directory for the Stratum A output JSON
#
# Runs feasibility_pilot_stratum_a.py with:
#   --budget 300     per-instance timeout (cluster ceiling)
#   --threshold 30   admission threshold (DATA.md §4 criterion)
#   --runs 3         repetitions per design (early-exit on first DNF)
#
# The 17 already-admitted designs complete in < 30 s each; the 6 PENDING_CLUSTER
# designs (sts13_0, sts13_1, sts15_0, ag24, pg23, pg24) get their first
# cluster-grade measurement at up to 300 s.  Total runtime ≈ 30 s × 17 +
# 300 s × 6 = 2 310 s ~ 39 min (worst case: all 6 DNF at 300 s).
#
# SLURM directives:
#   CPU-only: no --gres, no --constraint=dgx.
#   2 h wall time covers the worst-case runtime with generous headroom.
#   16 GB RAM is sufficient for pure-Python canonical-string computation.

#SBATCH --job-name=T-M7h-stratum-a
#SBATCH --time=0-02:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --constraint=cpu

set -euo pipefail

START_TIME=$(date +%s)

# ── Header ────────────────────────────────────────────────────────────────────
echo "=========================================="
echo "Job:          ${SLURM_JOB_ID:-local}"
echo "Node:         $(hostname)"
echo "Start:        $(date)"
echo "Repo dir:     ${REPO_DIR:-UNSET}"
echo "Output dir:   ${T_M7H_A_OUTPUT_DIR:-UNSET}"
echo "=========================================="

# ── Validate injected variables ───────────────────────────────────────────────
: "${CONDA_ENV_NAME:?CONDA_ENV_NAME not set — submit via T-M7h_stratum_a_launcher.sh}"
: "${REPO_DIR:?REPO_DIR not set}"
: "${T_M7H_A_OUTPUT_DIR:?T_M7H_A_OUTPUT_DIR not set}"

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
mkdir -p "${T_M7H_A_OUTPUT_DIR}"
echo "Output dir:   ${T_M7H_A_OUTPUT_DIR}/"
echo ""

# ── Run Stratum A feasibility pilot ───────────────────────────────────────────
# --budget 300:     per-instance SIGALRM ceiling (measurement ceiling, not admission threshold)
# --threshold 30:   admission threshold (DATA.md §4 criterion p90 ≤ 30 s + 0 DNFs)
# --runs 3:         repetitions per design; early-exit on first DNF
# --output:         where to write feasibility_pilot_stratum_a.json + admitted_catalog.txt
python scripts/feasibility_pilot_stratum_a.py \
    --budget 300 \
    --threshold 30 \
    --runs 3 \
    --output "${T_M7H_A_OUTPUT_DIR}"

# ── Footer ────────────────────────────────────────────────────────────────────
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo ""
echo "=========================================="
echo "Finished:  $(date)"
echo "Duration:  $((ELAPSED / 3600))h $(((ELAPSED / 60) % 60))m $((ELAPSED % 60))s"
echo "Output:    ${T_M7H_A_OUTPUT_DIR}/"
echo "=========================================="
