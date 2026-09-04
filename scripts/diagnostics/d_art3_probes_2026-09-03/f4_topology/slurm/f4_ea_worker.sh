#!/usr/bin/env bash
# F4 topology probe -- full-scale E-A (w*_c) arm, SLURM array worker.
#
# Submit via f4_ea_launcher.sh (sets every environment variable).
# Do NOT submit this script directly.
#
# Environment variables injected by the launcher:
#   CONDA_ENV_NAME   -- conda env (isalhg)
#   REPO_DIR         -- IsalHG repo root on Picasso
#   PROBE_DIR        -- scripts/diagnostics/d_art3_probes_2026-09-03/f4_topology
#   F4_DATA_ROOT     -- data root holding arb_benson/temporal/NDC-classes and wd50k_66
#   F4_OUT_DIR       -- where ea_shard_<i>.json is written
#   N_SHARDS         -- number of array tasks
#   EA_BUDGET        -- per-instance wall-clock budget in seconds (censoring)
#
# Work unit. run_ea_full.py enumerates the complete E-A task list -- 32,920
# canonicalizations, measured on the login node 2026-09-04 -- and this task
# computes the contiguous block [lo, hi) belonging to its array index. Each
# instance is canonicalized in a forked child killed at EA_BUDGET seconds, so a
# hard instance censors instead of stalling the block.
#
# Node family. The isalhg C++ extension on Picasso was built on the login node
# (Xeon Gold 6230R, AVX-512). Array 2206615 pinned to `sr` died with SIGILL on
# every task in 8 s: `sr` is AMD EPYC without AVX-512. `sd` is the login node's
# own family, so the existing build runs and all shards are timed on one machine
# type. Do NOT relax this to `cpu` without rebuilding with a portable baseline.
#
# Duration. The local pilot measured ~1e5 core-seconds for the whole list
# (synthetic near-free, NDC ~6 core-s/instance, WD50K ~2.4 core-s/instance), so
# one quarter of it on 4 cores is ~1.7 h -- above SCBI's two-hour floor once the
# heavier edited instances are counted. The 12 h wall is ~7x headroom; the
# per-instance budget bounds the tail.
#
# Output is one JSON per array task (a handful of files, each a few MB), so this
# worker writes straight to FSCRATCH rather than staging through $LOCALSCRATCH:
# the many-small-files rule does not apply here.

#SBATCH --job-name=f4-ea
#SBATCH --time=0-12:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --constraint=sd
#SBATCH --account=tic_163_uma

set -euo pipefail

START_TIME=$(date +%s)

echo "=========================================="
echo "Job:          ${SLURM_JOB_ID:-local}"
echo "Array task:   ${SLURM_ARRAY_TASK_ID:-N/A} of ${N_SHARDS:-?}"
echo "Node:         $(hostname)"
echo "CPU model:    $(lscpu | sed -n 's/^Model name: *//p' | head -1)"
echo "Start:        $(date)"
echo "=========================================="

: "${CONDA_ENV_NAME:?CONDA_ENV_NAME not set -- submit via f4_ea_launcher.sh}"
: "${REPO_DIR:?REPO_DIR not set}"
: "${PROBE_DIR:?PROBE_DIR not set}"
: "${F4_DATA_ROOT:?F4_DATA_ROOT not set}"
: "${F4_OUT_DIR:?F4_OUT_DIR not set}"
: "${N_SHARDS:?N_SHARDS not set}"

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

cd "${PROBE_DIR}"
export PYTHONPATH="${REPO_DIR}/src:${REPO_DIR}:${PYTHONPATH:-}"
export PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export F4_DATA_ROOT

echo "Python:       $(which python)"
echo "Git commit:   $(git -C "${REPO_DIR}" rev-parse --short HEAD 2>/dev/null || echo n/a)"
python -c "import isalhg, pynauty, rapidfuzz; print('isalhg:', isalhg.__file__)"
echo ""

mkdir -p "${F4_OUT_DIR}"

python run_ea_full.py \
    --shard "${SLURM_ARRAY_TASK_ID:-0}" \
    --nshards "${N_SHARDS}" \
    --workers "${SLURM_CPUS_PER_TASK:-4}" \
    --budget "${EA_BUDGET:-60}" \
    --out "${F4_OUT_DIR}"

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo ""
echo "=========================================="
echo "Finished:  $(date)"
echo "Duration:  $((ELAPSED / 3600))h $(((ELAPSED / 60) % 60))m $((ELAPSED % 60))s"
echo "Output:    ${F4_OUT_DIR}/ea_shard_$(printf '%04d' "${SLURM_ARRAY_TASK_ID:-0}").json"
echo "=========================================="
