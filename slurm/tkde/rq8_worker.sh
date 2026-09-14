#!/usr/bin/env bash
# RQ8 -- valid completion of a record. SLURM worker.
# Submit via rq8_launcher.sh. Do NOT submit directly.
#
# Depends on nothing. RQ8 reads the frozen corpora and computes every word,
# certificate and model itself, so it needs no matrices job and no dependency.
#
# ---------------------------------------------------------------------------
# Job shape: ONE task, and why
# ---------------------------------------------------------------------------
# RQ8 is 81 units (27 seeds x {ndc_classes/non_star, wd50k66/non_star,
# wd50k66/star}). Measured locally on this workstation at the full pilot size
# (200 evaluation units per unit, six arms): 5.6-7.6 s per ndc_classes unit and
# 8.3-9.4 s per wd50k66 unit, so the whole campaign is about 12 minutes of CPU.
#
# That is below the two-hour floor and it is submitted as ONE task anyway, for
# the reason the floor exists: the floor forbids MANY short placements, and a
# single twelve-minute job is one placement. Splitting 81 units across an array
# would turn one short job into eight, which is exactly the multiplication SCBI
# asked this account to stop (soporte@scbi.uma.es, 2026-08-07). The RQ5 worker
# made the same call for the same reason and records it the same way.
#
# The array machinery (--count, --shard, the start cutoff) is exercised at
# N_TASKS = 1, so widening the design later needs no change to this file.
#
# $LOCALSCRATCH staging is used: RQ8 writes ~165 small CSV files (two tables per
# unit plus the census), which is the many-small-files pattern the manual asks
# to keep off shared GPFS. The stage subdirectory is "." so that OUT_DIR mirrors
# onto the results ROOT and the runner creates RQ8_completion/ beneath it --
# staging "RQ8_completion" would produce RQ8_completion/RQ8_completion/.
#
# Memory. No RQ8 MaxRSS exists yet. The resident set is one collection
# (wd50k66: 3,988 records), its ordered-walk word memo, and three TokenNGram
# models over the training split. The nearest measured shape is RQ6, whose
# shard reached 20.4 GB only because it shared one model across units and never
# reset the memo; RQ8 fits its models per unit and drops them with the unit, so
# the profile is flat rather than rising. 32 G is ample headroom over a
# worst-case single unit and schedules on every sd node.

#SBATCH --job-name=tkde-rq8
#SBATCH --time=0-02:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --constraint=sd
#SBATCH --account=tic_163_uma

set -euo pipefail

: "${REPO_DIR:?REPO_DIR not set -- submit via rq8_launcher.sh}"
# shellcheck source=/dev/null
source "${REPO_DIR}/slurm/tkde/common.sh"

# `tkde_finalize` prints "copy-back OK" whenever the mirror succeeds, and
# mirroring an EMPTY tree succeeds -- so a run that produced nothing reads in the
# log exactly like one that worked. Measured 2026-09-13 on RQ2_ow: 22 tasks, all
# "copy-back OK", zero rows. This refuses to reach the copy-back when no row file
# was staged. It belongs in common.sh, which is read-only here; T-KBac proposes
# the move.
tkde_assert_out_dir_not_empty() {
    local n
    n=$(find "${OUT_DIR}" -name 'rows_*.csv' 2>/dev/null | wc -l)
    if [[ "${n}" -eq 0 ]]; then
        echo "" >&2
        echo "[FATAL] ${OUT_DIR} holds no rows_*.csv after the payload ran." >&2
        echo "        The copy-back would mirror an empty tree and report OK." >&2
        find "${MYLOCALSCRATCH}" -name 'rows_*.csv' 2>/dev/null | head -5 >&2
        exit 1
    fi
    echo "[ok] ${n} row file(s) staged in ${OUT_DIR}"
}

tkde_job_header "tkde-rq8"
tkde_stage_localscratch "."
cd "${REPO_DIR}"

CONFIG="${RQ8_CONFIG:-experiments/tkde/configs/rq8.yaml}"
N_TASKS="${RQ8_N_TASKS:-1}"
TASK_IDX="${SLURM_ARRAY_TASK_ID:-0}"
WALL_S="${RQ8_WALL_S:-7200}"
UNIT_BUDGET_S="${RQ8_UNIT_BUDGET_S:-300}"
TEARDOWN_S=300

N_UNITS=$("${PY}" -m experiments.tkde.rq8 --config "${CONFIG}" --list-units | wc -l)
CUTOFF_EPOCH=$(( TKDE_START_TIME + WALL_S - TEARDOWN_S - UNIT_BUDGET_S ))

# Echo the decoded assignment. A silently wrong decode produces a complete,
# plausible, WRONG result set -- the most expensive failure available here.
echo ""
echo "Config:        ${CONFIG}"
echo "Units:         ${N_UNITS}"
echo "Shard:         ${TASK_IDX}/${N_TASKS}"
echo "Start cutoff:  $(date -d "@${CUTOFF_EPOCH}" --iso-8601=seconds)"
echo "Out (staged):  ${OUT_DIR}"
echo ""

"${PY}" - <<'PYEOF'
import os
import isalhg
import experiments.tkde.rq8 as m

# Assert the DIRECTORY NAME, never equality with $REPO_DIR: ~/fscratch is a
# symlink to /mnt2/fscratch/users/..., so a correct install reports the /mnt2
# spelling and a startswith($REPO_DIR) check fails on it (PICASSO.md section 1).
name = os.path.basename(os.environ["REPO_DIR"])
assert f"/{name}/" in m.__file__, f"experiments resolves outside {name}: {m.__file__}"
# isalhg resolves through the editable-install finder of the canonical
# IsalHG-tkde tree. That is correct and deliberate: this wave changed nothing
# under src/**, so a private env would rebuild an identical extension while
# breaking every worker that asserts the canonical tree.
assert "IsalHG-tkde" in isalhg.__file__, f"isalhg resolves outside the campaign: {isalhg.__file__}"
print(f"[ok] experiments -> {m.__file__}")
print(f"[ok] isalhg      -> {isalhg.__file__}")
PYEOF

# The runner owns the unit loop so that one process serves every unit: it
# memoizes the loaded collection and its ordered-walk words, which a per-unit
# subprocess would recompute for all 3,988 wd50k66 members 27 times over. The
# start cutoff and its first-unit exemption live inside that loop.
# That one long-lived process is exactly what tkde_run_synced (common.sh) is
# for: the EXIT/TERM traps cannot fire while the shell waits on it in the
# foreground, and a wall-clock kill would take the whole task's rows with it.

if [[ -n "${TKDE_SMOKE:-}" ]]; then
    # The one cluster smoke allowed below the two-hour floor: the --smoke
    # configuration, staged under a _smoke subtree so its rows share no path
    # with the campaign's. The smoke runs REAL unit ids, so written beside the
    # campaign's rows the idempotent full run would see those units as done and
    # ship five toy members as the result. The analyzers also exclude any
    # `_smoke` path.
    echo "[smoke] running the --smoke configuration only"
    tkde_run_synced "${PY}" -m experiments.tkde.rq8 \
        --config "${CONFIG}" \
        --smoke \
        --out "${OUT_DIR}/_smoke" \
        --data-root "${ISALHG_DATA_ROOT}"
else
    tkde_run_synced "${PY}" -m experiments.tkde.rq8 \
        --config "${CONFIG}" \
        --out "${OUT_DIR}" \
        --data-root "${ISALHG_DATA_ROOT}" \
        --shard "${TASK_IDX}/${N_TASKS}" \
        --start-cutoff-epoch "${CUTOFF_EPOCH}"

    # The analyzer runs in the same task: it reads only the rows just written,
    # costs seconds, and its absence is how a campaign ends with rows nobody
    # turned into a table. It reads OUT_DIR, so it sees this task's rows before
    # the copy-back rather than a half-mirrored tree.
    "${PY}" -m experiments.tkde.analyze_rq8 \
        --root "${OUT_DIR}" \
        --experiment "$("${PY}" -c "
import sys
from experiments.tkde.config import load_yaml
print(load_yaml(sys.argv[1]).get('experiment', 'completion'))
" "${CONFIG}")" || echo "[warn] analyzer failed; the rows are still staged"
fi

tkde_assert_out_dir_not_empty
tkde_sync_partial

echo ""
echo "---------- rows produced ----------"
find "${OUT_DIR}" -name 'rows_*.csv' | wc -l | xargs echo "row files:"

tkde_job_footer
