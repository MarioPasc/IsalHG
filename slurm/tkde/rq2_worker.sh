#!/usr/bin/env bash
# RQ2 -- well-posedness. Submit via rq2_launcher.sh. Do NOT submit directly.

#SBATCH --job-name=tkde-rq2
#SBATCH --time=1-00:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --constraint=sd
#SBATCH --account=tic_163_uma

set -euo pipefail

: "${REPO_DIR:?REPO_DIR not set -- submit via rq2_launcher.sh}"

# The oracle-ceiling rows report wall-clock, so every arm is single-threaded;
# the census's parallelism is process-level (n_jobs), not thread-level.
export TKDE_THREADS=1

# shellcheck source=/dev/null
source "${REPO_DIR}/slurm/tkde/common.sh"

RQ_FOLDER="RQ2_wellposedness"
EXPERIMENT="wellposedness"
CONFIG="${REPO_DIR}/experiments/tkde/configs/rq2.yaml"

tkde_job_header "tkde-rq2"
# The smoke gets its own results subtree: its unit ids come from the same
# namespace as the real run's (exact0-ndc_classes-fact_rank is BOTH a smoke unit
# and a full-run unit), so a smoke row file in the real directory would make the
# full run skip that unit as already done and substitute 5 pairs for 100.
STAGE_SUBDIR="${RQ_FOLDER}/${EXPERIMENT}"
[[ "${TKDE_SMOKE:-0}" == "1" ]] && STAGE_SUBDIR="${RQ_FOLDER}/_smoke/${EXPERIMENT}"
tkde_stage_localscratch "${STAGE_SUBDIR}"
cd "${REPO_DIR}"

STAGE_ROOT="${MYLOCALSCRATCH}/root"
mkdir -p "${STAGE_ROOT}/${RQ_FOLDER}"
ln -sfn "${OUT_DIR}" "${STAGE_ROOT}/${RQ_FOLDER}/${EXPERIMENT}"
# matrices/ is a SHARED input (and, for ndc_substances, a shared output), so in
# a real run it points at the durable root rather than at the node: staging it
# would hide the cache the shared matrices job wrote and rebuild every arm.
#
# The smoke run is the exception and it is not cosmetic. Its configuration puts
# ndc_classes in census_own_collections over a 20-member subset, so through the
# symlink it would write a 20x20 matrix over the real ndc_classes cache the
# shared matrices job builds -- destroying a several-hour input with a toy.
# The smoke therefore gets its own matrices directory on the node.
if [[ "${TKDE_SMOKE:-0}" == "1" ]]; then
    mkdir -p "${STAGE_ROOT}/matrices"
else
    ln -sfn "${ISALHG_RESULTS_ROOT}/matrices" "${STAGE_ROOT}/matrices"
fi

# --export splits on commas, so a list-valued variable must travel
# colon-separated or it is truncated to its first element with no error.
KINDS_ARG=()
if [[ -n "${RQ2_KINDS:-}" ]]; then
    KINDS_ARG=(--kinds "${RQ2_KINDS//:/,}")
    echo "Unit kinds: ${RQ2_KINDS//:/,}"
fi

if [[ "${TKDE_SMOKE:-0}" == "1" ]]; then
    echo "SMOKE: one shard, tiny configuration"
    "${PY}" -m experiments.tkde.rq2 \
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

# The oracle units here are 600 s apiece and the census holds a whole
# collection's matrices in memory, so both the TIMEOUT and the OOM kill that
# tkde_run_synced (common.sh) guards against are live risks.
for (( S = LO; S < HI; S++ )); do
    ELAPSED=$(( $(date +%s) - TKDE_START_TIME ))
    if (( S > LO && ELAPSED >= START_CUTOFF_S )); then
        echo "DEFERRED: shard ${S} (elapsed ${ELAPSED}s >= cutoff ${START_CUTOFF_S}s)"
        continue
    fi

    tkde_run_synced "${PY}" -m experiments.tkde.rq2 \
        --config "${CONFIG}" \
        --out "${STAGE_ROOT}" \
        --data-root "${ISALHG_DATA_ROOT}" \
        --shard "${S}/${N_SHARDS}" \
        --start-cutoff-epoch "${CUTOFF_EPOCH}" \
        "${KINDS_ARG[@]}"
done

tkde_job_footer
