#!/usr/bin/env bash
# RQ3 --- the representative record --- SLURM worker (DESIGN.md section 4).
#
# Submit via rq3_launcher.sh. Do NOT submit directly.
#
# What one task does:
#   1. stages this task's own result subtrees from HOME onto $LOCALSCRATCH, so
#      the runner's resume logic sees what earlier attempts already wrote;
#   2. runs `python -m experiments.tkde.rq3 --shard i/N` once per shard in its
#      slice, with a start cutoff (first shard exempt) and a partial copy-back
#      after each one;
#   3. optionally runs RQ6 in the same task (TKDE_RUN_RQ6=1) --- RQ6's whole
#      workload is minutes, so it is bundled here rather than submitted as a
#      job of its own (SCBI's two-hour floor, 2026-08-07);
#   4. mirrors the whole staged tree back to $ISALHG_RESULTS_ROOT on HOME.
#
# Staging note. The runner writes into three RQ folders --- RQ3_representative,
# RQ2_wellposedness/certificate_validity (DESIGN.md section 3 step 4) and, when
# bundled, RQ6_generation --- so the staging root is the results root itself and
# the copy-back mirrors only the paths this task actually wrote. A peer's files
# elsewhere under RQ2_wellposedness are never in the staged tree and so are never
# overwritten.
#
# Node family. `sd` is the login node's own family (Xeon Gold 6230R, AVX-512).
# The C++ extension is built there with -march=native; an AMD node dies with
# SIGILL in seconds. Do not relax the constraint.

#SBATCH --job-name=tkde-rq3
#SBATCH --time=0-08:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
# 24G killed job 2213221 at 20.4 GB (an unbounded memo cache in TokenNGram,
# fixed in rq6.py by refitting per unit; peak is now a measured 3.9 GB). 64G
# leaves headroom for RQ3's own peak, which the OOM never let us separate.
#SBATCH --mem=64G
#SBATCH --constraint=sd
#SBATCH --account=tic_163_uma

set -euo pipefail

: "${REPO_DIR:?REPO_DIR not set -- submit via rq3_launcher.sh}"

# Wall-clock is a reported quantity in these rows; keep every arm single-threaded
# so a BLAS thread pool cannot make one arm look faster than it is.
export TKDE_THREADS=1
# shellcheck source=/dev/null
source "${REPO_DIR}/slurm/tkde/common.sh"

TKDE_SMOKE="${TKDE_SMOKE:-0}"
TKDE_N_SHARDS="${TKDE_N_SHARDS:-1}"
TKDE_N_TASKS="${TKDE_N_TASKS:-1}"
TKDE_RUN_RQ6="${TKDE_RUN_RQ6:-0}"
TKDE_START_CUTOFF_S="${TKDE_START_CUTOFF_S:-19800}"
TKDE_CORPORA_ROOT="${TKDE_CORPORA_ROOT:-${ISALHG_DATA_ROOT}}"

if [[ "${TKDE_SMOKE}" == "1" ]]; then
    export ISALHG_RESULTS_ROOT="${ISALHG_RESULTS_ROOT}/_smoke_rq3"
    mkdir -p "${ISALHG_RESULTS_ROOT}"
fi

tkde_job_header "tkde-rq3"
tkde_stage_localscratch "."

cd "${REPO_DIR}"

# ---------------------------------------------------------------------------
# Stage this task's own subtrees in, so the runner can resume rather than redo.
# ---------------------------------------------------------------------------
for SUBTREE in RQ3_representative RQ2_wellposedness/certificate_validity RQ6_generation; do
    SRC="${ISALHG_RESULTS_ROOT}/${SUBTREE}"
    if [[ -d "${SRC}" ]]; then
        mkdir -p "${OUT_DIR}/${SUBTREE}"
        rsync -a "${SRC}/" "${OUT_DIR}/${SUBTREE}/"
        echo "[stage-in] ${SRC} -> ${OUT_DIR}/${SUBTREE}"
    fi
done

# ---------------------------------------------------------------------------
# This task's slice of the shard list: an even split, never fixed blocks with a
# ragged tail (the short remainder task is exactly what the floor forbids).
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

echo ""
echo "Task ${TASK_ID}/${TKDE_N_TASKS} -> shards ${LO}..${HI} of ${TKDE_N_SHARDS}"
echo "Corpora root: ${TKDE_CORPORA_ROOT}"
echo "Run RQ6 here: ${TKDE_RUN_RQ6}"
echo "Start cutoff: ${TKDE_START_CUTOFF_S} s"
echo ""

# ---------------------------------------------------------------------------
# tkde_run_synced -- run a payload, mirroring out/ back every SYNC_INTERVAL_S
# ---------------------------------------------------------------------------
# common.sh's copy-back runs from EXIT/TERM traps, but bash defers a trap while
# it waits on a foreground child, and on this cluster a scancel of job 2213210
# (2026-09-05) killed the step before tkde_finalize ever ran: fourteen minutes
# of rows died on the node. A long single-shard task therefore cannot rely on
# the traps alone. Running the payload in the background and syncing on a timer
# bounds the loss to one interval, and it also makes the rows visible on HOME
# while the job is still running.
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

FIRST=1
for (( SHARD = LO; SHARD <= HI; SHARD++ )); do
    ELAPSED=$(( $(date +%s) - TKDE_START_TIME ))
    if (( FIRST == 0 && ELAPSED >= TKDE_START_CUTOFF_S )); then
        echo "DEFERRED: shard ${SHARD}/${TKDE_N_SHARDS} (elapsed ${ELAPSED} s)"
        continue
    fi
    FIRST=0
    echo "---------- RQ3 shard ${SHARD}/${TKDE_N_SHARDS} ----------"
    tkde_run_synced "${PY}" -m experiments.tkde.rq3 \
        --config "${REPO_DIR}/experiments/tkde/configs/rq3.yaml" \
        --out "${OUT_DIR}" \
        --data-root "${TKDE_CORPORA_ROOT}" \
        --shard "${SHARD}/${TKDE_N_SHARDS}" \
        --start-cutoff-s "$(( TKDE_START_CUTOFF_S - ELAPSED ))" \
        "${SMOKE_FLAG[@]}"
done

if [[ "${TKDE_RUN_RQ6}" == "1" ]]; then
    echo ""
    echo "---------- RQ6 (bundled into this task) ----------"
    tkde_run_synced "${PY}" -m experiments.tkde.rq6 \
        --config "${REPO_DIR}/experiments/tkde/configs/rq6.yaml" \
        --out "${OUT_DIR}" \
        --data-root "${TKDE_CORPORA_ROOT}" \
        --shard "1/1" \
        "${SMOKE_FLAG[@]}"
fi

# The analyzers merge every shard, so a task that holds only part of the shard
# list would write an experiment-level table from a partial view and the last
# task to finish would win. They therefore run here only when this task holds
# the whole campaign; otherwise the authoritative pass is run after the harvest.
if [[ "${TKDE_RUN_ANALYZERS:-0}" == "1" ]]; then
    echo ""
    echo "---------- analyzers ----------"
    "${PY}" -m experiments.tkde.analyze_rq3 --root "${OUT_DIR}" || echo "[warn] analyze_rq3 failed"
    if [[ "${TKDE_RUN_RQ6}" == "1" ]]; then
        "${PY}" -m experiments.tkde.analyze_rq6 --root "${OUT_DIR}" \
            || echo "[warn] analyze_rq6 failed"
    fi
fi

echo ""
echo "RQ3 TASK DONE"
tkde_job_footer
