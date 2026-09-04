#!/usr/bin/env bash
# F4 topology probe -- full-scale E-A (w*_c) arm on Picasso.
#
# The local probe subsamples the E-A arm (it is the expensive encoding). This
# array computes the complete list -- 32,920 canonicalizations covering every
# M1 base and single-edit neighbour, every M2 NDC consecutive pair, and every
# WD50K ladder -- in contiguous blocks, one block per array task.
#
# Usage:
#   bash slurm/f4_ea_launcher.sh --dry-run     # print the sbatch command
#   bash slurm/f4_ea_launcher.sh --test-only   # sbatch --test-only
#   bash slurm/f4_ea_launcher.sh               # submit
#
# Prerequisites already deployed (2026-09-04):
#   probe modules -> ${PROBE_DIR}
#   datasets      -> ${F4_DATA_ROOT}/{arb_benson/temporal/NDC-classes,wd50k_66}
#
# Merge back locally when the array completes:
#   rsync -a picasso:${F4_OUT_DIR}/ <local f4_topology>/ea_shards/
#   python merge_ea_shards.py --shards <local f4_topology>/ea_shards

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export CONDA_ENV_NAME="isalhg"
export REPO_DIR="/mnt/home/users/tic_163_uma/mpascual/fscratch/repos/IsalHG"
export PROBE_DIR="${REPO_DIR}/scripts/diagnostics/d_art3_probes_2026-09-03/f4_topology"
export F4_DATA_ROOT="/mnt/home/users/tic_163_uma/mpascual/fscratch/datasets/isalhg_f4"
export F4_OUT_DIR="/mnt/home/users/tic_163_uma/mpascual/fscratch/results/f4_topology/ea"
export N_SHARDS=4
export EA_BUDGET=60
LOGS_DIR="/mnt/home/users/tic_163_uma/mpascual/execs/f4_topology/logs"

WORKER="${SCRIPT_DIR}/f4_ea_worker.sh"
[[ -f "${WORKER}" ]] || { echo "ERROR: worker not found: ${WORKER}" >&2; exit 1; }

MODE="submit"
case "${1:-}" in
    --dry-run)   MODE="dry" ;;
    --test-only) MODE="test" ;;
esac

mkdir -p "${LOGS_DIR}" "${F4_OUT_DIR}"

_clean_job_id() {
    tail -n 1 <<<"$1" | sed -e 's/\x1b\[[0-9;]*[a-zA-Z]//g' -e 's/[^0-9]//g'
}

ARRAY_SPEC="0-$((N_SHARDS - 1))%${N_SHARDS}"
COMMON=(
    --array="${ARRAY_SPEC}"
    --output="${LOGS_DIR}/f4-ea_%A_%a.out"
    --error="${LOGS_DIR}/f4-ea_%A_%a.err"
    --export="ALL,CONDA_ENV_NAME=${CONDA_ENV_NAME},REPO_DIR=${REPO_DIR},PROBE_DIR=${PROBE_DIR},F4_DATA_ROOT=${F4_DATA_ROOT},F4_OUT_DIR=${F4_OUT_DIR},N_SHARDS=${N_SHARDS},EA_BUDGET=${EA_BUDGET}"
    "${WORKER}"
)

if [[ "${MODE}" == "dry" ]]; then
    echo "[DRY-RUN] sbatch --parsable ${COMMON[*]}"
    exit 0
fi

if [[ "${MODE}" == "test" ]]; then
    sbatch --test-only "${COMMON[@]}"
    exit $?
fi

RAW=$(sbatch --parsable "${COMMON[@]}") || { echo "sbatch failed" >&2; exit 1; }
JOB_ID=$(_clean_job_id "${RAW}")
[[ "${JOB_ID}" =~ ^[0-9]+$ ]] || {
    echo "FATAL: unparsable job id: ${RAW@Q}" >&2
    echo "Check squeue immediately -- the job may already be queued." >&2
    exit 1
}

echo "Submitted F4 E-A array: ${JOB_ID} (${N_SHARDS} tasks, ${ARRAY_SPEC})"
echo "Monitor:  squeue -j ${JOB_ID}"
echo "Logs:     ${LOGS_DIR}/f4-ea_${JOB_ID}_<task>.{out,err}"
echo "Results:  ${F4_OUT_DIR}/ea_shard_<task>.json"
