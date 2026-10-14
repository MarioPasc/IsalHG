#!/usr/bin/env bash
# RQ3 v2 --- the golden record from N anonymous noisy descriptions --- SLURM worker.
#
# Submit via rq3v2_launcher.sh. Do NOT submit directly.
#
# What one task does:
#   1. stages RQ3v2_golden_record from HOME onto $LOCALSCRATCH, so the runner's
#      resume logic sees what earlier attempts already wrote;
#   2. runs `python -m experiments.tkde.rq3v2 --shard i/N` once per shard in its
#      slice, with a start cutoff (first shard exempt) and a partial copy-back
#      after each one;
#   3. mirrors the whole staged tree back to $ISALHG_RESULTS_ROOT on HOME.
#
# Node family. `sd` is the login node's own family (Xeon Gold 6230R, AVX-512).
# The C++ extension is built there with -march=native; an AMD node dies with
# SIGILL in seconds. Do not relax the constraint.
#
# FSCRATCH is read-only for this campaign (file quota exhausted, grace expired,
# measured 2026-09-13). Nothing below writes there: REPO_DIR is on HOME, the
# corpora and the conda env are read from FSCRATCH and never written, the byte
# cache goes to $LOCALSCRATCH, and every result lands under $ISALHG_RESULTS_ROOT
# on HOME. Keep it that way --- a write to FSCRATCH ends the job mid-run.

#SBATCH --job-name=tkde-rq3v2
#SBATCH --time=0-08:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
# The ball enumeration holds one decoded class per distinct structure, measured
# at 19k classes on the heaviest pilot cell; 32G leaves an order of magnitude of
# headroom over that and matches what RQ3 v1 needed for its medoid matrices.
#SBATCH --mem=32G
#SBATCH --constraint=sd
#SBATCH --account=tic_163_uma

set -euo pipefail

: "${REPO_DIR:?REPO_DIR not set -- submit via rq3v2_launcher.sh}"

# Wall-clock is a reported quantity in these rows --- the cost of the two
# consensus arms is part of the H3.5 argument --- so every arm stays
# single-threaded and no BLAS thread pool can make one look faster than it is.
export TKDE_THREADS=1
# shellcheck source=/dev/null
source "${REPO_DIR}/slurm/tkde/common.sh"

TKDE_SMOKE="${TKDE_SMOKE:-0}"
TKDE_N_SHARDS="${TKDE_N_SHARDS:-1}"
TKDE_N_TASKS="${TKDE_N_TASKS:-1}"
TKDE_START_CUTOFF_S="${TKDE_START_CUTOFF_S:-21600}"
TKDE_CORPORA_ROOT="${TKDE_CORPORA_ROOT:-${ISALHG_DATA_ROOT}}"
RQ_SUBTREE="RQ3v2_golden_record"

if [[ "${TKDE_SMOKE}" == "1" ]]; then
    # A smoke and the campaign share the unit-id namespace, so the smoke gets its
    # own subtree as well as its own run tag.
    export ISALHG_RESULTS_ROOT="${ISALHG_RESULTS_ROOT}/_smoke_rq3v2"
    mkdir -p "${ISALHG_RESULTS_ROOT}"
fi

tkde_job_header "tkde-rq3v2"
tkde_stage_localscratch "."

cd "${REPO_DIR}"

# ---------------------------------------------------------------------------
# Refuse to run if anything would be written to FSCRATCH.
# ---------------------------------------------------------------------------
for GUARDED in "${ISALHG_RESULTS_ROOT}" "${OUT_DIR}" "${TKDE_LOGS_DIR:-}"; do
    if [[ -n "${GUARDED}" && "${GUARDED}" == */fscratch/* ]]; then
        echo "[FATAL] ${GUARDED} is under FSCRATCH, which is read-only for this campaign" >&2
        exit 1
    fi
done

# ---------------------------------------------------------------------------
# Stage this task's own subtree in, so the runner can resume rather than redo.
# ---------------------------------------------------------------------------
SRC="${ISALHG_RESULTS_ROOT}/${RQ_SUBTREE}"
if [[ -d "${SRC}" ]]; then
    mkdir -p "${OUT_DIR}/${RQ_SUBTREE}"
    rsync -a "${SRC}/" "${OUT_DIR}/${RQ_SUBTREE}/"
    echo "[stage-in] ${SRC} -> ${OUT_DIR}/${RQ_SUBTREE}"
fi

# ---------------------------------------------------------------------------
# This task's slice of the shard list: an even split, never fixed blocks with a
# ragged tail (the short remainder task is exactly what SCBI's floor forbids).
# ---------------------------------------------------------------------------
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

# Resume selectors. --only-cells and --resume are OPERATIONAL: they say which of
# the already-enumerated units this submission runs. --hged-timeout-s is
# MEASURED: it is folded into the configuration before the run tag is computed,
# so a shorter oracle budget carries its own tag and can never be pooled with the
# frozen one. The launcher decides which are set; the worker only relays them.
RESUME_FLAGS=()
[[ -n "${TKDE_ONLY_CELLS:-}" ]] && RESUME_FLAGS+=(--only-cells "${TKDE_ONLY_CELLS//:/,}")
[[ "${TKDE_RESUME:-0}" == "1" ]] && RESUME_FLAGS+=(--resume)
[[ -n "${TKDE_HGED_TIMEOUT_S:-}" ]] && RESUME_FLAGS+=(--hged-timeout-s "${TKDE_HGED_TIMEOUT_S}")

echo ""
echo "Task ${TASK_ID}/${TKDE_N_TASKS} -> shards ${LO}..${HI} of ${TKDE_N_SHARDS}"
echo "Corpora root: ${TKDE_CORPORA_ROOT}"
echo "Start cutoff: ${TKDE_START_CUTOFF_S} s"
echo ""

FIRST=1
for (( SHARD = LO; SHARD <= HI; SHARD++ )); do
    ELAPSED=$(( $(date +%s) - TKDE_START_TIME ))
    # The first shard is exempt: without the exemption a task whose start-up
    # alone exceeds the cutoff defers its whole slice, the sweep re-derives the
    # same slice and defers it again, and the array livelocks.
    if (( FIRST == 0 && ELAPSED >= TKDE_START_CUTOFF_S )); then
        echo "DEFERRED: shard ${SHARD}/${TKDE_N_SHARDS} (elapsed ${ELAPSED} s)"
        continue
    fi
    FIRST=0
    echo "---------- RQ3 v2 shard ${SHARD}/${TKDE_N_SHARDS} ----------"
    tkde_run_synced "${PY}" -m experiments.tkde.rq3v2 \
        --config "${REPO_DIR}/experiments/tkde/configs/rq3v2.yaml" \
        --out "${OUT_DIR}" \
        --data-root "${TKDE_CORPORA_ROOT}" \
        --shard "${SHARD}/${TKDE_N_SHARDS}" \
        --start-cutoff-s "$(( TKDE_START_CUTOFF_S - ELAPSED ))" \
        "${SMOKE_FLAG[@]}" "${RESUME_FLAGS[@]}"
done

# The analyzer merges every shard, so a task holding part of the shard list would
# write an experiment-level table from a partial view and the last task to finish
# would win. It therefore runs here only when this task holds the whole campaign;
# otherwise the authoritative pass runs after the harvest.
if [[ "${TKDE_RUN_ANALYZERS:-0}" == "1" ]]; then
    echo ""
    echo "---------- analyzer ----------"
    "${PY}" -m experiments.tkde.analyze_rq3v2 --root "${OUT_DIR}" \
        || echo "[warn] analyze_rq3v2 failed"
fi

echo ""
echo "RQ3 v2 TASK DONE"
tkde_job_footer
