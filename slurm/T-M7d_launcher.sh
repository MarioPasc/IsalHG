#!/usr/bin/env bash
# T-M7d multi-seed sweep — SLURM array launcher.
#
# Submits one array task per (cell_key, dist_name) combination.
# cell_keys: "stratum_a" (17 families, T-M7m+T-M7o) + 10 admitted Stratum B
#            block keys (envelope_final=true, array 1631517) = 11 cells.
# dist_names: 7 representations (ALL_DISTANCES in sweep_multi_seed.py).
# Total: 11 × 7 = 77 array tasks.  S=27 seeds per task (T-M7n power pilot).
#
# Envelope is final (array 1631517 complete).  The launcher derives Stratum B
# block keys live from the envelope JSON; the 17-family Stratum A membership is
# read from DATA_MANIFEST.stratum_a_ids inside sweep_multi_seed.py.
#
# Usage:
#   bash slurm/T-M7d_launcher.sh [--dry-run]
#
# Prerequisites on Picasso:
#   rsync -av <local_worktree>/ \
#       /mnt/home/users/tic_163_uma/mpascual/fscratch/repos/IsalHG/
#   # Confirm the conda env is present (cloned by T-M7d ledger-worker):
#   conda env list | grep isalhg
#
# Results land at:
#   $T_M7D_OUTPUT_DIR/  (see variable below)
#
# To merge results back locally after completion:
#   rsync -av \
#       picasso:${T_M7D_OUTPUT_DIR}/ \
#       /media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/T-M7d/
#
# Runtime estimate (S=27):
#   - Stratum A × isalhg: 27 seeds × ~3s/seed ≈ 1.4 min per task
#   - Stratum A × others: 27 seeds × ~2s/seed ≈ 0.9 min per task
#   - Stratum B (n≤24) × fast dists: 27 seeds × ~2s/seed ≈ 0.9 min per task
#   - Stratum B (n=24) × isalhg: 27 seeds × ~5s/seed ≈ 2.3 min per task
#   - Wall time 4h per task is very conservative (100× safety margin).
#   - 77 tasks at max_concurrent=20: ≈ 4 array waves ≈ 3 h total.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Configurable ──────────────────────────────────────────────────────────────
export CONDA_ENV_NAME="isalhg"
export REPO_DIR="/mnt/home/users/tic_163_uma/mpascual/fscratch/repos/IsalHG"
export T_M7D_ENVELOPE="${REPO_DIR}/experiments/article/stratum_b_feasibility_envelope.json"
export T_M7D_OUTPUT_DIR="/mnt/home/users/tic_163_uma/mpascual/fscratch/results/T-M7d"
export T_M7D_N_SEEDS=27
export T_M7D_N_CORPUS=60

LOGS_DIR="/mnt/home/users/tic_163_uma/mpascual/execs/T-M7d/logs"

# ── Derive admitted Stratum B block keys from the envelope ────────────────────
# Conda env may live under fscratch (Picasso) or ~/.conda (local).
if [[ -x "${HOME}/fscratch/conda_envs/${CONDA_ENV_NAME}/bin/python" ]]; then
    PYTHON_BIN="${HOME}/fscratch/conda_envs/${CONDA_ENV_NAME}/bin/python"
elif [[ -x "${HOME}/.conda/envs/${CONDA_ENV_NAME}/bin/python" ]]; then
    PYTHON_BIN="${HOME}/.conda/envs/${CONDA_ENV_NAME}/bin/python"
else
    PYTHON_BIN="$(conda run -n ${CONDA_ENV_NAME} which python 2>/dev/null || which python)"
fi

mapfile -t B_BLOCK_KEYS < <(
    "${PYTHON_BIN}" -c "
import json, sys
with open('${T_M7D_ENVELOPE}') as f:
    env = json.load(f)
for k in env['admitted_block_keys']:
    print(k)
"
)

if [[ "${#B_BLOCK_KEYS[@]}" -eq 0 ]]; then
    echo "ERROR: no admitted Stratum B block keys found in envelope." >&2
    exit 1
fi
echo "Derived ${#B_BLOCK_KEYS[@]} admitted Stratum B blocks from envelope."

# ── Distance names (must match ALL_DISTANCES in sweep_multi_seed.py) ─────────
DIST_NAMES=(
    "isalhg_levenshtein"
    "hypergraph_wl_l1"
    "netlsd_l2"
    "hpd_jsd"
    "nauty_levi_edit"
    "degree_seq_l1"
    "hypercot"
)

# ── Build (cell_key, dist_name) pair list ─────────────────────────────────────
# Each line: "<cell_key> <dist_name>"
PAIRS_FILE="${LOGS_DIR}/T-M7d_pairs.txt"
mkdir -p "${LOGS_DIR}"

{
    for dist in "${DIST_NAMES[@]}"; do
        echo "stratum_a ${dist}"
    done
    for bkey in "${B_BLOCK_KEYS[@]}"; do
        for dist in "${DIST_NAMES[@]}"; do
            echo "${bkey} ${dist}"
        done
    done
} > "${PAIRS_FILE}"

N_PAIRS=$(wc -l < "${PAIRS_FILE}")
ARRAY_MAX="$((N_PAIRS - 1))"
MAX_CONCURRENT=20

echo "Pairs file:  ${PAIRS_FILE}  (${N_PAIRS} tasks = ${#B_BLOCK_KEYS[@]}+1 cells × ${#DIST_NAMES[@]} reps)"
echo "Array range: 0-${ARRAY_MAX} (max ${MAX_CONCURRENT} concurrent)"

# ── Preflight ──────────────────────────────────────────────────────────────────
WORKER="${SCRIPT_DIR}/T-M7d_worker.sh"
if [[ ! -f "$WORKER" ]]; then
    echo "ERROR: worker script not found: $WORKER" >&2
    exit 1
fi

DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

if ${DRY_RUN}; then
    echo "[DRY-RUN] Would submit:"
    echo "  sbatch --array=0-${ARRAY_MAX}%${MAX_CONCURRENT} ${WORKER}"
    echo ""
    echo "First 10 tasks:"
    head -10 "${PAIRS_FILE}" | awk '{printf "  task %d → cell_key=%s  dist_name=%s\n", NR-1, $1, $2}'
    echo "  ..."
    exit 0
fi

# ── Submit ─────────────────────────────────────────────────────────────────────
JOB_ID=$(sbatch --parsable \
    --array="0-${ARRAY_MAX}%${MAX_CONCURRENT}" \
    --output="${LOGS_DIR}/T-M7d_%A_%a.out" \
    --error="${LOGS_DIR}/T-M7d_%A_%a.err" \
    --export="ALL,\
CONDA_ENV_NAME=${CONDA_ENV_NAME},\
REPO_DIR=${REPO_DIR},\
T_M7D_ENVELOPE=${T_M7D_ENVELOPE},\
T_M7D_OUTPUT_DIR=${T_M7D_OUTPUT_DIR},\
T_M7D_N_SEEDS=${T_M7D_N_SEEDS},\
T_M7D_N_CORPUS=${T_M7D_N_CORPUS},\
T_M7D_PAIRS_FILE=${PAIRS_FILE}" \
    "${WORKER}")

echo "Submitted T-M7d sweep array: ${JOB_ID}"
echo "Array:   0-${ARRAY_MAX}%${MAX_CONCURRENT}  (${N_PAIRS} tasks)"
echo "Monitor: squeue -j ${JOB_ID}"
echo "Logs:    ${LOGS_DIR}/T-M7d_${JOB_ID}_*.{out,err}"
echo "Results: ${T_M7D_OUTPUT_DIR}/"
echo ""
echo "After completion, rsync results locally:"
echo "  rsync -av picasso:${T_M7D_OUTPUT_DIR}/ \\"
echo "      /media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/T-M7d/"
