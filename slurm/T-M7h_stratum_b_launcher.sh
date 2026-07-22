#!/usr/bin/env bash
# T-M7h Stratum B feasibility pilot — SLURM array launcher.
#
# Submits one array task per pending Stratum B block (19 blocks).
# Each task runs feasibility_pilot.py for a single block with n_pilot=30
# and a 300 s per-instance timeout (admission threshold stays 30 s).
#
# Usage:
#   bash slurm/T-M7h_stratum_b_launcher.sh [--dry-run]
#
# Prerequisites on Picasso:
#   rsync -av <local_worktree>/ \
#       /mnt/home/users/tic_163_uma/mpascual/fscratch/repos/IsalHG/
#
# Results land at:
#   /mnt/home/users/tic_163_uma/mpascual/fscratch/results/T-M7h/stratum_b/per_block/
#
# To merge results back locally after completion:
#   rsync -av picasso:/mnt/home/users/tic_163_uma/mpascual/fscratch/results/T-M7h/ \
#             /media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/T-M7h/
#   python scripts/T-M7h_merge_envelope.py \
#       --stratum-b-dir /media/.../results/T-M7h/stratum_b/per_block/ \
#       --envelope experiments/article/stratum_b_feasibility_envelope.json

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Configurable ──────────────────────────────────────────────────────────────
export CONDA_ENV_NAME="isalhg"
export REPO_DIR="/mnt/home/users/tic_163_uma/mpascual/fscratch/repos/IsalHG"
export T_M7H_CONFIG="${REPO_DIR}/experiments/article/configs/stratum_b_sweep.yaml"
export T_M7H_ENVELOPE="${REPO_DIR}/experiments/article/stratum_b_feasibility_envelope.json"
export T_M7H_OUTPUT_DIR="/mnt/home/users/tic_163_uma/mpascual/fscratch/results/T-M7h/stratum_b/per_block"
LOGS_DIR="/mnt/home/users/tic_163_uma/mpascual/execs/T-M7h/logs"

# ── Derive pending block keys from the enumerator (single source of truth) ───
# feasibility_pilot.py --list-blocks --pending-envelope reads the YAML config,
# enumerates runnable blocks, and filters to those still pending in the envelope.
# This eliminates hard-coded key lists that drift from the actual enumerator naming.
PYTHON_BIN="$(conda run -n "${CONDA_ENV_NAME}" which python 2>/dev/null \
    || echo "${HOME}/.conda/envs/${CONDA_ENV_NAME}/bin/python")"

mapfile -t BLOCK_KEYS < <(
    cd "${REPO_DIR}" && "${PYTHON_BIN}" -m experiments.article.feasibility_pilot \
        --config "${T_M7H_CONFIG}" \
        --list-blocks \
        --pending-envelope "${T_M7H_ENVELOPE}"
)

if [[ "${#BLOCK_KEYS[@]}" -eq 0 ]]; then
    echo "ERROR: --list-blocks returned no pending blocks. Check envelope and config." >&2
    exit 1
fi
echo "Derived ${#BLOCK_KEYS[@]} pending block keys from the enumerator."

N_BLOCKS="${#BLOCK_KEYS[@]}"   # 19
ARRAY_MAX="$((N_BLOCKS - 1))"  # 18
MAX_CONCURRENT=10              # run at most 10 tasks simultaneously

# ── Preflight ──────────────────────────────────────────────────────────────────
WORKER="${SCRIPT_DIR}/T-M7h_stratum_b_worker.sh"
if [[ ! -f "$WORKER" ]]; then
    echo "ERROR: worker script not found: $WORKER" >&2
    exit 1
fi

DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

mkdir -p "${LOGS_DIR}"

# Write the block keys to a file so the worker can look up its key by index.
BLOCK_KEYS_FILE="${LOGS_DIR}/T-M7h_stratum_b_block_keys.txt"
printf '%s\n' "${BLOCK_KEYS[@]}" > "${BLOCK_KEYS_FILE}"
echo "Block keys written to: ${BLOCK_KEYS_FILE}"

# ── Submit ─────────────────────────────────────────────────────────────────────
SBATCH_CMD="sbatch --parsable \
    --array=0-${ARRAY_MAX}%${MAX_CONCURRENT} \
    --output=${LOGS_DIR}/T-M7h-stratum-b_%A_%a.out \
    --error=${LOGS_DIR}/T-M7h-stratum-b_%A_%a.err \
    --export=ALL,\
CONDA_ENV_NAME=${CONDA_ENV_NAME},\
REPO_DIR=${REPO_DIR},\
T_M7H_CONFIG=${T_M7H_CONFIG},\
T_M7H_OUTPUT_DIR=${T_M7H_OUTPUT_DIR},\
T_M7H_BLOCK_KEYS_FILE=${BLOCK_KEYS_FILE} \
    ${WORKER}"

if ${DRY_RUN}; then
    echo "[DRY-RUN] ${SBATCH_CMD}"
    echo ""
    echo "Array: 0-${ARRAY_MAX} (${N_BLOCKS} blocks, max ${MAX_CONCURRENT} concurrent)"
    echo "Block keys:"
    for i in "${!BLOCK_KEYS[@]}"; do
        echo "  task $i → ${BLOCK_KEYS[$i]}"
    done
    exit 0
fi

JOB_ID=$(eval "${SBATCH_CMD}")
echo "Submitted Stratum B array job: ${JOB_ID}"
echo "Array:    0-${ARRAY_MAX}%${MAX_CONCURRENT} (${N_BLOCKS} tasks)"
echo "Monitor:  squeue -j ${JOB_ID}"
echo "Logs:     ${LOGS_DIR}/T-M7h-stratum-b_${JOB_ID}_*.{out,err}"
echo "Results:  ${T_M7H_OUTPUT_DIR}/"
echo ""
echo "After completion, merge results locally:"
echo "  rsync -av picasso:${T_M7H_OUTPUT_DIR}/ /media/.../results/T-M7h/stratum_b/per_block/"
echo "  python scripts/T-M7h_merge_envelope.py \\"
echo "      --stratum-b-dir /media/.../results/T-M7h/stratum_b/per_block/ \\"
echo "      --envelope experiments/article/stratum_b_feasibility_envelope.json"
