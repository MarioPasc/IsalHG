#!/usr/bin/env bash
# RQ7 -- the operating envelope. Submit via rq7_launcher.sh. Do NOT submit directly.

#SBATCH --job-name=tkde-rq7
#SBATCH --time=1-00:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --constraint=sd
#SBATCH --account=tic_163_uma

set -euo pipefail

: "${REPO_DIR:?REPO_DIR not set -- submit via rq7_launcher.sh}"

# RQ7 IS the timing measurement, so every arm runs single-threaded: a wall-clock
# compared across arms must not be a measurement of how many threads each one
# happened to spawn. TKDE_THREADS must be set BEFORE common.sh is sourced.
export TKDE_THREADS=1

# shellcheck source=/dev/null
source "${REPO_DIR}/slurm/tkde/common.sh"

RQ_FOLDER="RQ7_envelope"
EXPERIMENT="envelope"
CONFIG="${REPO_DIR}/experiments/tkde/configs/rq7.yaml"

tkde_job_header "tkde-rq7"
# The smoke gets its own results subtree: its unit ids come from the same
# namespace as the real run's, so a smoke row file in the real directory would
# make the full run skip that unit as already done.
STAGE_SUBDIR="${RQ_FOLDER}/${EXPERIMENT}"
[[ "${TKDE_SMOKE:-0}" == "1" ]] && STAGE_SUBDIR="${RQ_FOLDER}/_smoke/${EXPERIMENT}"
tkde_stage_localscratch "${STAGE_SUBDIR}"
cd "${REPO_DIR}"

STAGE_ROOT="${MYLOCALSCRATCH}/root"
mkdir -p "${STAGE_ROOT}/${RQ_FOLDER}"
ln -sfn "${OUT_DIR}" "${STAGE_ROOT}/${RQ_FOLDER}/${EXPERIMENT}"
# The N-scaling pass builds its matrices with the cache DISABLED (it is timing
# them), so matrices/ is linked only so a stray read resolves to the real tree
# rather than to an empty staged one.
ln -sfn "${ISALHG_RESULTS_ROOT}/matrices" "${STAGE_ROOT}/matrices"

if [[ "${TKDE_SMOKE:-0}" == "1" ]]; then
    echo "SMOKE: one shard, tiny configuration"
    "${PY}" -m experiments.tkde.rq7 \
        --config "${CONFIG}" \
        --out "${STAGE_ROOT}" \
        --data-root "${ISALHG_DATA_ROOT}" \
        --smoke
    tkde_finalize
    tkde_job_footer
    exit 0
fi

: "${N_SHARDS:?N_SHARDS not set}"
: "${N_TASKS:?N_TASKS not set}"
: "${START_CUTOFF_S:?START_CUTOFF_S not set}"

TASK_IDX="${SLURM_ARRAY_TASK_ID:-0}"
Q=$(( N_SHARDS / N_TASKS )); R=$(( N_SHARDS % N_TASKS )); I="${TASK_IDX}"
LO=$(( I * Q + (I < R ? I : R) )); HI=$(( LO + Q + (I < R ? 1 : 0) ))
echo "Task ${TASK_IDX}/${N_TASKS} -> shards [${LO}, ${HI}) of ${N_SHARDS}"

CUTOFF_EPOCH=$(( TKDE_START_TIME + START_CUTOFF_S ))

# ---------------------------------------------------------------------------
# tkde_run_synced -- run a payload, mirroring the staged tree back on a timer.
# ---------------------------------------------------------------------------
# common.sh's copy-back runs from EXIT/TERM traps, but bash defers a trap while
# it waits on a FOREGROUND child. Measured on job 2213210 (2026-09-05): a
# scancel killed the step before tkde_finalize ever ran and fourteen minutes of
# rows died on the node. Backgrounding the payload lets the trap fire, and the
# timed sync bounds the loss to one interval.
tkde_run_synced() {
    "$@" &
    local pid=$!
    local status=0
    while kill -0 "${pid}" 2>/dev/null; do
        sleep "${TKDE_SYNC_INTERVAL_S:-300}"
        kill -0 "${pid}" 2>/dev/null && tkde_sync_partial
    done
    wait "${pid}" || status=$?
    tkde_sync_partial
    return "${status}"
}

for (( S = LO; S < HI; S++ )); do
    ELAPSED=$(( $(date +%s) - TKDE_START_TIME ))
    if (( S > LO && ELAPSED >= START_CUTOFF_S )); then
        echo "DEFERRED: shard ${S} (elapsed ${ELAPSED}s >= cutoff ${START_CUTOFF_S}s)"
        continue
    fi

    tkde_run_synced "${PY}" -m experiments.tkde.rq7 \
        --config "${CONFIG}" \
        --out "${STAGE_ROOT}" \
        --data-root "${ISALHG_DATA_ROOT}" \
        --shard "${S}/${N_SHARDS}" \
        --start-cutoff-epoch "${CUTOFF_EPOCH}"
done

tkde_job_footer
