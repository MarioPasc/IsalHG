#!/usr/bin/env bash
# The 600 s tail characterisation (T-KBp). Submit via tail600_launcher.sh.
# Do NOT submit directly.

#SBATCH --job-name=tkde-tail600
#SBATCH --time=0-04:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --constraint=sd
#SBATCH --account=tic_163_uma

set -euo pipefail

: "${REPO_DIR:?REPO_DIR not set -- submit via tail600_launcher.sh}"

# The whole measurement is a wall-clock comparison against the 60 s rows, and
# those were measured single-threaded (RQ7's rule). A tail row taken with a
# different thread count would not be comparable with the row it characterises.
# TKDE_THREADS must be set BEFORE common.sh is sourced.
export TKDE_THREADS=1

# shellcheck source=/dev/null
source "${REPO_DIR}/slurm/tkde/common.sh"

# NOT an RQ folder: no analyzer or merge tool of the campaign globs this name,
# which is what keeps D-ART5 decision 2 ("never a row") a property of the
# filesystem rather than of a convention.
RQ_FOLDER="TAIL600_characterisation"
EXPERIMENT="tail_600s"
CONFIG="${REPO_DIR}/experiments/tkde/configs/tail600.yaml"

tkde_job_header "tkde-tail600"
# The smoke shares the shard-id namespace with the real run, so its rows go to
# their own subtree or the real run would skip those shards as already done.
STAGE_SUBDIR="${RQ_FOLDER}/${EXPERIMENT}"
[[ "${TKDE_SMOKE:-0}" == "1" ]] && STAGE_SUBDIR="${RQ_FOLDER}/_smoke/${EXPERIMENT}"
tkde_stage_localscratch "${STAGE_SUBDIR}"
cd "${REPO_DIR}"

STAGE_ROOT="${MYLOCALSCRATCH}/root"
mkdir -p "${STAGE_ROOT}/${RQ_FOLDER}"
if [[ "${TKDE_SMOKE:-0}" == "1" ]]; then
    mkdir -p "${STAGE_ROOT}/${RQ_FOLDER}/_smoke"
    ln -sfn "${OUT_DIR}" "${STAGE_ROOT}/${RQ_FOLDER}/_smoke/${EXPERIMENT}"
else
    ln -sfn "${OUT_DIR}" "${STAGE_ROOT}/${RQ_FOLDER}/${EXPERIMENT}"
fi

# The census is READ from the durable results root, never from the staged tree:
# --out is a node-local scratch directory holding no RQ1 rows at all.
CENSUS_ROOT="${ISALHG_RESULTS_ROOT}"

if [[ "${TKDE_SMOKE:-0}" == "1" ]]; then
    echo "SMOKE: four members at the smoke budget, one shard"
    "${PY}" -m experiments.tkde.tail600 \
        --config "${CONFIG}" \
        --out "${STAGE_ROOT}" \
        --census-root "${CENSUS_ROOT}" \
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

for (( S = LO; S < HI; S++ )); do
    ELAPSED=$(( $(date +%s) - TKDE_START_TIME ))
    if (( S > LO && ELAPSED >= START_CUTOFF_S )); then
        echo "DEFERRED: shard ${S} (elapsed ${ELAPSED}s >= cutoff ${START_CUTOFF_S}s)"
        continue
    fi

    tkde_run_synced "${PY}" -m experiments.tkde.tail600 \
        --config "${CONFIG}" \
        --out "${STAGE_ROOT}" \
        --census-root "${CENSUS_ROOT}" \
        --data-root "${ISALHG_DATA_ROOT}" \
        --shard "${S}/${N_SHARDS}" \
        --start-cutoff-epoch "${CUTOFF_EPOCH}"
done

tkde_job_footer
