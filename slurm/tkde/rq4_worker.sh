#!/usr/bin/env bash
# RQ4 -- the data-quality screen (DESIGN.md §5). SLURM worker.
# Submit via rq4_launcher.sh. Do NOT submit directly.
#
# Depends on tkde-matrices (--dependency=afterok): the inlier-inlier block of
# every scored matrix is a submatrix of a cached full-collection matrix. Only
# the 5 % anomaly rows are computed here. If the cache is absent the runner
# raises MatrixCacheMissingError rather than recomputing a 7.95 M-pair matrix
# inside an eight-hour wall.
#
# ---------------------------------------------------------------------------
# Sizing (measured)
# ---------------------------------------------------------------------------
# 1,323 units = 27 seeds x 7 sub-collections x 7 (corruption, budget) cells.
# Per unit the cost is n_anomalies x N pairs across eight arms; the eight arms
# together cost ~2.56 ms per pair (netlsd 1.75 ms and hpd_jsd 0.62 ms are 93 %
# of it). By sub-collection:
#
#   ndc_classes  N=1381, 70 anomalies -> ~248 core-s/unit -> 13.0 core-h total
#   Q5 human     N=1830, 92 anomalies -> ~432 core-s/unit -> 22.7 core-h
#   Q11424 film  N=1092, 55 anomalies -> ~154 core-s/unit ->  8.1 core-h
#   the four small types (171/74/49/47)                   ->  0.3 core-h
#   scoring overhead (kNN + LOF on N x N, 8 arms)         ->  3.7 core-h
#   total                                                 -> ~48 core-hours
#
# At 8 cores and 3 tasks that is ~2 h per task, which is the floor, reached by
# choosing the task count from the measurement rather than by padding.
#
# Units are enumerated SEED-MAJOR, so each contiguous bundle holds every
# sub-collection the same number of times and all three tasks cost the same.
# A collection-major order would give one multi-hour task and one four-minute
# one out of the same even split.

# Memory. No RQ4/RQ5 MaxRSS was ever measured -- the two cluster smokes
# (2213203/2213204) were cancelled before they were assigned a node. The
# nearest measurement is the matrices job (2213202): 34.2 GB of a 64 G request
# with 32 fork-pool workers over the same corpora. The pool here is 8 workers,
# but the corpus and the memoized matrices are resident per fork rather than
# shared, so a linear scale-down is not safe: 48 G is >= 50 % headroom over a
# 30 GB worst case and still schedules on every sd node.

#SBATCH --job-name=tkde-rq4
#SBATCH --time=0-08:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --constraint=sd
#SBATCH --account=tic_163_uma

set -euo pipefail

: "${REPO_DIR:?REPO_DIR not set -- submit via rq4_launcher.sh}"
# shellcheck source=/dev/null
source "${REPO_DIR}/slurm/tkde/common.sh"

tkde_job_header "tkde-rq4"
tkde_stage_localscratch "."
cd "${REPO_DIR}"

CONFIG="${RQ4_CONFIG:-experiments/tkde/configs/rq4.yaml}"
N_TASKS="${RQ4_N_TASKS:-3}"
TASK_IDX="${SLURM_ARRAY_TASK_ID:-0}"
WALL_S="${RQ4_WALL_S:-28800}"
UNIT_BUDGET_S="${RQ4_UNIT_BUDGET_S:-1200}"
TEARDOWN_S=600

N_UNITS=$("${PY}" -m experiments.tkde.rq4 --config "${CONFIG}" --count)
DEADLINE=$(( TKDE_START_TIME + WALL_S - TEARDOWN_S ))

# Echo the decoded assignment. A silently wrong decode produces a complete,
# plausible, WRONG result set.
echo ""
echo "Config:        ${CONFIG}"
echo "Units:         ${N_UNITS}"
echo "Shard:         ${TASK_IDX}/${N_TASKS}"
echo "Deadline:      $(date -d "@${DEADLINE}" --iso-8601=seconds) (unit budget ${UNIT_BUDGET_S}s)"
echo "Out (staged):  ${OUT_DIR}"
echo ""

"${PY}" - <<'PYEOF'
import os
import experiments.tkde.rq4 as m
import isalhg

# Assert the DIRECTORY NAME, never equality with $REPO_DIR. ~/fscratch is a
# symlink to /mnt2/fscratch/users/..., so a correct install reports the /mnt2
# spelling and a startswith($REPO_DIR) check fails on it (PICASSO.md §1).
name = os.path.basename(os.environ["REPO_DIR"])
assert f"/{name}/" in m.__file__, f"experiments resolves outside {name}: {m.__file__}"
# isalhg legitimately resolves through the editable-install finder of the
# canonical IsalHG-tkde tree; that is correct because src/** is unchanged here.
assert "IsalHG-tkde" in isalhg.__file__, f"isalhg resolves outside the campaign: {isalhg.__file__}"
print(f"[ok] experiments -> {m.__file__}")
print(f"[ok] isalhg      -> {isalhg.__file__}")
PYEOF

# One process per task, not one per unit: the runner memoizes the loaded
# collections, their hypergraphs, their fact words and the eight cached
# matrices. Re-deriving those per unit made an ndc_classes unit 24 s instead of
# 1.2 s (measured). The start-cutoff, with its first-unit exemption, lives
# inside that loop; deferred units are listed in the shard manifest and a
# resume pass picks them up because every unit's rows are addressed by unit id.
# That one long-lived process is exactly what tkde_run_synced (common.sh) is
# for: the EXIT/TERM traps cannot fire while the shell waits on it in the
# foreground.

if [[ -n "${TKDE_SMOKE_UNIT:-}" ]]; then
    # The one cluster smoke task allowed below the two-hour floor: a single
    # named unit, chosen small, proving the deployed tree, the interpreter, the
    # matrix cache and the copy-back before the real array is queued. Passing
    # environment self-checks is not evidence that a job will run.
    echo "[smoke] running unit ${TKDE_SMOKE_UNIT} only"
    # --tag _smoke keeps the smoke's rows OUT of the real experiment folder.
    # The smoke runs a REAL unit (same config, same unit id), so its rows are
    # byte-shaped exactly like the campaign's: written alongside them, the
    # idempotent full run would see the unit as done and ship the smoke's
    # output as the result. The analyzers also exclude any `_smoke` path.
    tkde_run_synced "${PY}" -m experiments.tkde.rq4 \
        --config "${CONFIG}" \
        --out "${OUT_DIR}" \
        --data-root "${ISALHG_DATA_ROOT}" \
        --matrices-root "${ISALHG_RESULTS_ROOT}" \
        --tag _smoke \
        --unit "${TKDE_SMOKE_UNIT}"
else
    tkde_run_synced "${PY}" -m experiments.tkde.rq4 \
        --config "${CONFIG}" \
        --out "${OUT_DIR}" \
        --data-root "${ISALHG_DATA_ROOT}" \
        --matrices-root "${ISALHG_RESULTS_ROOT}" \
        --shard "${TASK_IDX}/${N_TASKS}" \
        --deadline "${DEADLINE}" \
        --unit-budget "${UNIT_BUDGET_S}"
fi

tkde_sync_partial

echo ""
echo "---------- rows produced ----------"
find "${OUT_DIR}" -name 'rows_*.csv' | wc -l | xargs echo "row files:"

tkde_job_footer
