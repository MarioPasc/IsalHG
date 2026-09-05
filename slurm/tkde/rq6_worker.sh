#!/usr/bin/env bash
# RQ6 --- generation --- SLURM worker (DESIGN.md section 7).
#
# Submit via rq6_launcher.sh. Do NOT submit directly.
#
# RQ6's whole workload is minutes (measured 2026-09-05: 10,000 samples on
# wd50k66 take 7.8 s, so the 27-seed campaign over both collections and both
# models is well under half an hour), which is why the *campaign* runs bundled
# inside an RQ3 task (TKDE_RUN_RQ6=1 in rq3_worker.sh) rather than as a job of
# its own: SCBI asked for the fewest, longest tasks, 2026-08-07.
#
# This worker exists for two things:
#   * the one cluster smoke task this research question is allowed below the
#     two-hour floor, which proves the deployed runner on a compute node;
#   * a standalone re-run of RQ6 alone when the RQ3 rows must not be touched.
#
# Node family. `sd` is the login node's own family (Xeon Gold 6230R, AVX-512),
# and the pointer-alphabet panel of the decodability figure calls the C++
# canonical-string engine built there with -march=native. An AMD node dies with
# SIGILL in seconds. Do not relax the constraint.

#SBATCH --job-name=tkde-rq6
#SBATCH --time=0-04:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
# Sized with rq3_worker.sh; the sampling peak is a measured 3.9 GB per unit.
#SBATCH --mem=64G
#SBATCH --constraint=sd
#SBATCH --account=tic_163_uma

set -euo pipefail

: "${REPO_DIR:?REPO_DIR not set -- submit via rq6_launcher.sh}"

export TKDE_THREADS=1
# shellcheck source=/dev/null
source "${REPO_DIR}/slurm/tkde/common.sh"

TKDE_SMOKE="${TKDE_SMOKE:-0}"
TKDE_N_SHARDS="${TKDE_N_SHARDS:-1}"
TKDE_N_TASKS="${TKDE_N_TASKS:-1}"
TKDE_START_CUTOFF_S="${TKDE_START_CUTOFF_S:-12600}"
TKDE_CORPORA_ROOT="${TKDE_CORPORA_ROOT:-${ISALHG_DATA_ROOT}}"

if [[ "${TKDE_SMOKE}" == "1" ]]; then
    export ISALHG_RESULTS_ROOT="${ISALHG_RESULTS_ROOT}/_smoke_rq6"
    mkdir -p "${ISALHG_RESULTS_ROOT}"
fi

tkde_job_header "tkde-rq6"
tkde_stage_localscratch "."

cd "${REPO_DIR}"

if [[ -d "${ISALHG_RESULTS_ROOT}/RQ6_generation" ]]; then
    mkdir -p "${OUT_DIR}/RQ6_generation"
    rsync -a "${ISALHG_RESULTS_ROOT}/RQ6_generation/" "${OUT_DIR}/RQ6_generation/"
    echo "[stage-in] RQ6_generation staged for resume"
fi

TASK_ID="${SLURM_ARRAY_TASK_ID:-1}"
Q=$(( TKDE_N_SHARDS / TKDE_N_TASKS ))
R=$(( TKDE_N_SHARDS % TKDE_N_TASKS ))
I=$(( TASK_ID - 1 ))
if (( I < R )); then
    LO=$(( I * Q + I + 1 ))
    HI=$(( LO + Q ))
else
    LO=$(( I * Q + R + 1 ))
    HI=$(( LO + Q - 1 ))
fi

SMOKE_FLAG=()
[[ "${TKDE_SMOKE}" == "1" ]] && SMOKE_FLAG=(--smoke)

echo ""
echo "Task ${TASK_ID}/${TKDE_N_TASKS} -> shards ${LO}..${HI} of ${TKDE_N_SHARDS}"
echo "Corpora root: ${TKDE_CORPORA_ROOT}"
echo ""

FIRST=1
for (( SHARD = LO; SHARD <= HI; SHARD++ )); do
    ELAPSED=$(( $(date +%s) - TKDE_START_TIME ))
    if (( FIRST == 0 && ELAPSED >= TKDE_START_CUTOFF_S )); then
        echo "DEFERRED: shard ${SHARD}/${TKDE_N_SHARDS} (elapsed ${ELAPSED} s)"
        continue
    fi
    FIRST=0
    echo "---------- RQ6 shard ${SHARD}/${TKDE_N_SHARDS} ----------"
    tkde_run_synced "${PY}" -m experiments.tkde.rq6 \
        --config "${REPO_DIR}/experiments/tkde/configs/rq6.yaml" \
        --out "${OUT_DIR}" \
        --data-root "${TKDE_CORPORA_ROOT}" \
        --shard "${SHARD}/${TKDE_N_SHARDS}" \
        --start-cutoff-s "$(( TKDE_START_CUTOFF_S - ELAPSED ))" \
        "${SMOKE_FLAG[@]}"
done

if [[ "${TKDE_RUN_ANALYZERS:-1}" == "1" ]]; then
    echo ""
    echo "---------- analyzer ----------"
    "${PY}" -m experiments.tkde.analyze_rq6 --root "${OUT_DIR}" || echo "[warn] analyze_rq6 failed"
fi

echo ""
echo "RQ6 TASK DONE"
tkde_job_footer
