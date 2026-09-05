#!/usr/bin/env bash
# RQ5 -- description patterns (DESIGN.md §6). SLURM worker.
# Submit via rq5_launcher.sh. Do NOT submit directly.
#
# Depends on tkde-matrices (--dependency=afterok): every unit reads submatrices
# of the cached full-collection matrices and computes no distance itself. If the
# cache is absent the runner raises MatrixCacheMissingError rather than
# recomputing, so a dropped dependency fails fast instead of timing out.
#
# ---------------------------------------------------------------------------
# Job shape: ONE task, and why
# ---------------------------------------------------------------------------
# RQ5 is 65 units: 11 full-design units (one per arm: PAM x 27 initializations,
# average-linkage, an eigendecomposition for nu, and the SMACOF map on
# fact_rank) and 54 balanced-design units (a 280-member submatrix across every
# arm -- sub-second each). Measured locally, the whole set is well under an
# hour. Splitting it across an array would submit several sub-hour tasks where
# one job does; the two-hour floor exists to stop exactly that multiplication,
# so RQ5 is submitted as a single task and the reasoning is recorded here
# rather than left implicit. The array machinery (--count, even split,
# start-cutoff) is still exercised, at N_TASKS = 1, so widening the design
# later needs no change to this file.
#
# $LOCALSCRATCH staging is used: RQ5 writes ~200 small row files (one CSV per
# unit per table), which is the many-small-files pattern the manual asks to
# keep off shared GPFS. The stage subdirectory is "." so that OUT_DIR mirrors
# onto the results ROOT and the runner can create RQ5_patterns/ beneath it --
# staging "RQ5_patterns" instead would produce RQ5_patterns/RQ5_patterns/.

#SBATCH --job-name=tkde-rq5
#SBATCH --time=0-06:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --constraint=sd
#SBATCH --account=tic_163_uma

set -euo pipefail

: "${REPO_DIR:?REPO_DIR not set -- submit via rq5_launcher.sh}"
# shellcheck source=/dev/null
source "${REPO_DIR}/slurm/tkde/common.sh"

tkde_job_header "tkde-rq5"
tkde_stage_localscratch "."
cd "${REPO_DIR}"

CONFIG="${RQ5_CONFIG:-experiments/tkde/configs/rq5.yaml}"
N_TASKS="${RQ5_N_TASKS:-1}"
TASK_IDX="${SLURM_ARRAY_TASK_ID:-0}"
WALL_S="${RQ5_WALL_S:-21600}"
UNIT_BUDGET_S="${RQ5_UNIT_BUDGET_S:-1800}"
TEARDOWN_S=600

N_UNITS=$("${PY}" -m experiments.tkde.rq5 --config "${CONFIG}" --count)
DEADLINE=$(( TKDE_START_TIME + WALL_S - TEARDOWN_S ))

# Echo the decoded assignment. A silently wrong decode produces a complete,
# plausible, WRONG result set -- the most expensive failure available here.
echo ""
echo "Config:        ${CONFIG}"
echo "Units:         ${N_UNITS}"
echo "Shard:         ${TASK_IDX}/${N_TASKS}"
echo "Deadline:      $(date -d "@${DEADLINE}" --iso-8601=seconds) (unit budget ${UNIT_BUDGET_S}s)"
echo "Out (staged):  ${OUT_DIR}"
echo ""

"${PY}" - <<'PYEOF'
import os
import experiments.tkde.rq5 as m
import isalhg
repo = os.environ["REPO_DIR"]
assert m.__file__.startswith(repo), f"experiments resolves outside {repo}: {m.__file__}"
assert "IsalHG-tkde" in isalhg.__file__, f"isalhg resolves outside the campaign: {isalhg.__file__}"
print(f"[ok] experiments -> {m.__file__}")
print(f"[ok] isalhg      -> {isalhg.__file__}")
PYEOF

# The runner owns the unit loop so that one process serves every unit: it
# memoizes the loaded collection and the 11 cached matrices (64 MB each on
# wd50k66), which a per-unit subprocess would re-read ~300 times. The
# start-cutoff and its first-unit exemption live inside that loop.
if [[ -n "${TKDE_SMOKE_UNIT:-}" ]]; then
    # The one cluster smoke task allowed below the two-hour floor: a single
    # named unit -- a cheap balanced one, not a full-design one -- proving the
    # deployed tree, the interpreter, the matrix cache and the copy-back before
    # the real job is queued. Passing environment self-checks is not evidence
    # that a job will run.
    echo "[smoke] running unit ${TKDE_SMOKE_UNIT} only"
    "${PY}" -m experiments.tkde.rq5 \
        --config "${CONFIG}" \
        --out "${OUT_DIR}" \
        --data-root "${ISALHG_DATA_ROOT}" \
        --unit "${TKDE_SMOKE_UNIT}"
else
    "${PY}" -m experiments.tkde.rq5 \
        --config "${CONFIG}" \
        --out "${OUT_DIR}" \
        --data-root "${ISALHG_DATA_ROOT}" \
        --shard "${TASK_IDX}/${N_TASKS}" \
        --deadline "${DEADLINE}" \
        --unit-budget "${UNIT_BUDGET_S}"
fi

tkde_sync_partial

echo ""
echo "---------- rows produced ----------"
find "${OUT_DIR}" -name 'rows_*.csv' | wc -l | xargs echo "row files:"

tkde_job_footer
