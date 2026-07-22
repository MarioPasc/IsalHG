#!/usr/bin/env bash
# T-M7h Stratum A feasibility pilot — SLURM launcher.
#
# Submits a single CPU job that re-runs all 23 Stratum A designs with a
# 300 s per-instance timeout and a 30 s admission threshold.  The 6
# PENDING_CLUSTER designs (sts13_0, sts13_1, sts15_0, ag24, pg23, pg24)
# get their first cluster-grade measurement; the 17 already-admitted designs
# finish in < 30 s each and are re-confirmed.
#
# Usage:
#   bash slurm/T-M7h_stratum_a_launcher.sh [--dry-run]
#
# Prerequisites on Picasso:
#   rsync -av <local_worktree>/ \
#       /mnt/home/users/tic_163_uma/mpascual/fscratch/repos/IsalHG/
#
# Results land at:
#   /mnt/home/users/tic_163_uma/mpascual/fscratch/results/T-M7h/stratum_a/
#
# To merge results back locally after completion:
#   rsync -av picasso:/mnt/home/users/tic_163_uma/mpascual/fscratch/results/T-M7h/stratum_a/ \
#             /media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/T-M7h/stratum_a/
#   python scripts/T-M7h_merge_envelope.py \
#       --stratum-a-json /media/.../results/T-M7h/stratum_a/feasibility_pilot_stratum_a.json \
#       --stratum-a-artifacts artifacts/feasibility_pilot/

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Configurable ──────────────────────────────────────────────────────────────
export CONDA_ENV_NAME="isalhg"
export REPO_DIR="/mnt/home/users/tic_163_uma/mpascual/fscratch/repos/IsalHG"
export T_M7H_A_OUTPUT_DIR="/mnt/home/users/tic_163_uma/mpascual/fscratch/results/T-M7h/stratum_a"
LOGS_DIR="/mnt/home/users/tic_163_uma/mpascual/execs/T-M7h/logs"

# ── Preflight ──────────────────────────────────────────────────────────────────
WORKER="${SCRIPT_DIR}/T-M7h_stratum_a_worker.sh"
if [[ ! -f "$WORKER" ]]; then
    echo "ERROR: worker script not found: $WORKER" >&2
    exit 1
fi

DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

mkdir -p "${LOGS_DIR}"

# ── Submit ─────────────────────────────────────────────────────────────────────
SBATCH_CMD="sbatch --parsable \
    --output=${LOGS_DIR}/T-M7h-stratum-a_%j.out \
    --error=${LOGS_DIR}/T-M7h-stratum-a_%j.err \
    --export=ALL,\
CONDA_ENV_NAME=${CONDA_ENV_NAME},\
REPO_DIR=${REPO_DIR},\
T_M7H_A_OUTPUT_DIR=${T_M7H_A_OUTPUT_DIR} \
    ${WORKER}"

if ${DRY_RUN}; then
    echo "[DRY-RUN] ${SBATCH_CMD}"
    exit 0
fi

JOB_ID=$(eval "${SBATCH_CMD}")
echo "Submitted Stratum A job: ${JOB_ID}"
echo "Monitor:  squeue -j ${JOB_ID}"
echo "Logs:     ${LOGS_DIR}/T-M7h-stratum-a_${JOB_ID}.{out,err}"
echo "Results:  ${T_M7H_A_OUTPUT_DIR}/"
echo ""
echo "After completion, merge results locally:"
echo "  rsync -av picasso:${T_M7H_A_OUTPUT_DIR}/ /media/.../results/T-M7h/stratum_a/"
echo "  python scripts/T-M7h_merge_envelope.py \\"
echo "      --stratum-a-json /media/.../results/T-M7h/stratum_a/feasibility_pilot_stratum_a.json \\"
echo "      --stratum-a-artifacts artifacts/feasibility_pilot/"
