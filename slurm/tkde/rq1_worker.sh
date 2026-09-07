#!/usr/bin/env bash
# RQ1 -- representation design (addressing). Submit via rq1_launcher.sh.
# Do NOT submit directly: the launcher derives the array size from the runner's
# own --count, and a hard-coded size cannot disagree with a decode that changed.

#SBATCH --job-name=tkde-rq1
#SBATCH --time=1-00:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=12G
#SBATCH --constraint=sd
#SBATCH --account=tic_163_uma

set -euo pipefail

: "${REPO_DIR:?REPO_DIR not set -- submit via rq1_launcher.sh}"

# Wall-clock is a reported quantity in RQ1 (M3), so the arms must be
# single-threaded; TKDE_THREADS must be exported BEFORE common.sh is sourced.
export TKDE_THREADS=1

# shellcheck source=/dev/null
source "${REPO_DIR}/slurm/tkde/common.sh"

RQ_FOLDER="RQ1_addressing"
# RQ1_CONFIG (exported by the launcher) selects another RQ1 experiment on the
# same seeded units; the experiment name comes from that config so the staging
# subtree and the runner's own <RQ>/<experiment> path can never disagree.
CONFIG="${RQ1_CONFIG:-${REPO_DIR}/experiments/tkde/configs/rq1.yaml}"
EXPERIMENT="$(sed -n 's/^experiment:[[:space:]]*\([A-Za-z0-9_-]*\).*/\1/p' "${CONFIG}" | head -n 1)"
EXPERIMENT="${EXPERIMENT:-addressing}"

tkde_job_header "tkde-rq1"
# The smoke writes to its OWN results subtree. It must not share the real one:
# its unit ids are drawn from the same namespace, so a smoke row file sitting in
# the real directory makes the full run's idempotence check declare that unit
# already done and skip it -- silently substituting five toy members for the
# corpus. The analyzers skip any path under a _smoke directory for the same
# reason.
STAGE_SUBDIR="${RQ_FOLDER}/${EXPERIMENT}"
[[ "${TKDE_SMOKE:-0}" == "1" ]] && STAGE_SUBDIR="${RQ_FOLDER}/_smoke/${EXPERIMENT}"
tkde_stage_localscratch "${STAGE_SUBDIR}"
cd "${REPO_DIR}"

# The runner's --out is a results ROOT and it appends <RQ>/<experiment> itself,
# while tkde_stage_localscratch hands back the leaf directory. The symlink makes
# the two agree without either side learning about the other. matrices/ is
# symlinked to the durable root because it is an input shared with other jobs,
# never a per-task artefact.
STAGE_ROOT="${MYLOCALSCRATCH}/root"
mkdir -p "${STAGE_ROOT}/${RQ_FOLDER}"
ln -sfn "${OUT_DIR}" "${STAGE_ROOT}/${RQ_FOLDER}/${EXPERIMENT}"
ln -sfn "${ISALHG_RESULTS_ROOT}/matrices" "${STAGE_ROOT}/matrices"


if [[ "${TKDE_SMOKE:-0}" == "1" ]]; then
    echo "SMOKE: one shard, tiny configuration"
    "${PY}" -m experiments.tkde.rq1 \
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
# Echo the decode. A silently wrong decode produces a complete, plausible,
# WRONG result set -- the most expensive failure mode in this workflow.
echo "Task ${TASK_IDX}/${N_TASKS} -> shards [${LO}, ${HI}) of ${N_SHARDS}"

CUTOFF_EPOCH=$(( TKDE_START_TIME + START_CUTOFF_S ))

# RQ1 is the longest job in this wave and its pointer arm has a censored tail,
# so the TIMEOUT that tkde_run_synced (common.sh) guards against is expected
# here, not hypothetical.
for (( S = LO; S < HI; S++ )); do
    ELAPSED=$(( $(date +%s) - TKDE_START_TIME ))
    # The FIRST shard of a task is exempt from the cutoff: without that
    # exemption a task whose start-up alone exceeds it defers its whole chunk,
    # the recovery sweep re-derives the same chunk and defers it again, and the
    # array livelocks. A late shard is DEFERRED, never given a shorter budget.
    if (( S > LO && ELAPSED >= START_CUTOFF_S )); then
        echo "DEFERRED: shard ${S} (elapsed ${ELAPSED}s >= cutoff ${START_CUTOFF_S}s)"
        continue
    fi

    tkde_run_synced "${PY}" -m experiments.tkde.rq1 \
        --config "${CONFIG}" \
        --out "${STAGE_ROOT}" \
        --data-root "${ISALHG_DATA_ROOT}" \
        --shard "${S}/${N_SHARDS}" \
        --start-cutoff-epoch "${CUTOFF_EPOCH}"
done

tkde_job_footer
