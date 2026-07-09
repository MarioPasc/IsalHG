#!/usr/bin/env bash
# T-M5a SLURM worker — execute one cell from the config.
#
# Submit via T-M5a_launcher.sh (sets all necessary environment variables).
# Do NOT submit this script directly.
#
# Environment variables injected by the launcher:
#   T_M5A_CONFIG  — absolute path to the experiment YAML config
#   T_M5A_REPO    — absolute path to the IsalHG repo root
#   T_M5A_PYTHON  — absolute path to the conda Python binary
#
# SLURM directives (adjust to Picasso queue availability):
#   - CPU-only: no GPU requested, no --constraint=dgx
#   - 4 CPUs per task (ExactHGED branch-and-bound is single-threaded;
#     4 CPUs gives headroom for parallelism inside scipy / rapidfuzz)
#   - 16 GB RAM per task (safe for n ≤ 12 hypergraphs)
#   - 6-hour wall clock (exact-HGED pairs at n=9 can take tens of seconds
#     each; 30 pairs × 30 items = 900 pairs; budget generously)

#SBATCH --partition=batch
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=06:00:00

# ── Safeguards ────────────────────────────────────────────────────────────────

set -euo pipefail

echo "=============================="
echo "Job:        $SLURM_JOB_ID"
echo "Array task: $SLURM_ARRAY_TASK_ID"
echo "Node:       $(hostname)"
echo "Config:     ${T_M5A_CONFIG:-UNSET}"
echo "Repo:       ${T_M5A_REPO:-UNSET}"
echo "Python:     ${T_M5A_PYTHON:-UNSET}"
echo "Start:      $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "=============================="

# ── Validate injected variables ───────────────────────────────────────────────

: "${T_M5A_CONFIG:?T_M5A_CONFIG not set — submit via T-M5a_launcher.sh}"
: "${T_M5A_REPO:?T_M5A_REPO not set}"
: "${T_M5A_PYTHON:?T_M5A_PYTHON not set}"

# ── Change to repo root (required for experiments.article package discovery) ──

cd "$T_M5A_REPO"

# ── Run one cell ──────────────────────────────────────────────────────────────

"$T_M5A_PYTHON" -m experiments.article.runner \
    --config "$T_M5A_CONFIG" \
    --cell-index "$SLURM_ARRAY_TASK_ID"

echo "=============================="
echo "Done:  $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "=============================="
