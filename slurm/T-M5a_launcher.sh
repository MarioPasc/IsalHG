#!/usr/bin/env bash
# T-M5a SLURM launcher — submit an array job for one experiment config.
#
# Usage:
#   bash slurm/T-M5a_launcher.sh experiments/article/configs/e1_correlation.yaml
#   bash slurm/T-M5a_launcher.sh experiments/article/configs/e2_density_sweep.yaml
#   bash slurm/T-M5a_launcher.sh experiments/article/configs/e2b_sensitivity.yaml
#   bash slurm/T-M5a_launcher.sh experiments/article/configs/e3_ladder.yaml
#
# Each cell maps to one SLURM array task; --cell-index $SLURM_ARRAY_TASK_ID
# in the worker selects the correct cell.  Results go to the output_root
# declared in the config YAML (never into the git tree).
#
# Picasso notes:
#   - This job is CPU-only (canonical strings + Levenshtein + ExactHGED).
#     No --gres=gpu, no --constraint=dgx.
#   - Logs land in ~/execs/T-M5a/logs/ following the project convention.
#   - Repo path on Picasso:
#       /mnt/home/users/tic_163_uma/mpascual/fscratch/repos/IsalHG
#   - conda env is isalhg (editable install already present on Picasso).
#
# If Picasso login nodes have internet access, sync the worktree first:
#   rsync -av --exclude='.git' <worktree>/ picasso:fscratch/repos/IsalHG/

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────

CONFIG="${1:?Usage: $0 <config.yaml>}"
CONFIG="$(realpath "$CONFIG")"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${PYTHON:-~/.conda/envs/isalhg/bin/python}"
LOG_DIR="$HOME/execs/T-M5a/logs"
WORKER="$REPO_ROOT/slurm/T-M5a_worker.sh"

# ── Preflight ──────────────────────────────────────────────────────────────────

if [[ ! -f "$CONFIG" ]]; then
    echo "ERROR: config not found: $CONFIG" >&2
    exit 1
fi

if [[ ! -x "$WORKER" ]]; then
    echo "ERROR: worker script not executable: $WORKER" >&2
    echo "       Run: chmod +x $WORKER" >&2
    exit 1
fi

mkdir -p "$LOG_DIR"

# ── Count cells ────────────────────────────────────────────────────────────────

N=$("$PYTHON" -m experiments.article.runner --config "$CONFIG" --count)
if [[ "$N" -lt 1 ]]; then
    echo "ERROR: config has no cells: $CONFIG" >&2
    exit 1
fi
ARRAY_SPEC="0-$((N - 1))"
echo "Submitting ${N} cells from: $(basename "$CONFIG")"

# ── Derive a short job name from the config filename ──────────────────────────

JOB_NAME="T-M5a-$(basename "${CONFIG%.yaml}")"

# ── Submit ────────────────────────────────────────────────────────────────────

sbatch \
    --job-name="$JOB_NAME" \
    --array="$ARRAY_SPEC" \
    --output="$LOG_DIR/${JOB_NAME}_%A_%a.out" \
    --error="$LOG_DIR/${JOB_NAME}_%A_%a.err" \
    --export=ALL,T_M5A_CONFIG="$CONFIG",T_M5A_REPO="$REPO_ROOT",T_M5A_PYTHON="$PYTHON" \
    "$WORKER"

echo "Logs in: $LOG_DIR"
