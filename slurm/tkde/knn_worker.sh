#!/usr/bin/env bash
# KNN_2026-10-15 full run (LOG.md section 8) -- SLURM worker.
# Submit via knn_launcher.sh. Do NOT submit directly.
#
# One array task runs one group of units of scripts/newpos/knn/full_run.py
# (`--list-tasks` is the decode). A unit is one (design, collection,
# condition/stratum) job over the 27 seeds; the heavy units (Design B, the mix
# condition, Design D) are one task each, and the short ones (Designs A and C)
# are bundled into two tasks so that no task runs under the two-hour floor
# (README.md, "The 2 h floor"). The grouping changes no parameter of any unit.
#
# Staging. OUT_DIR is on $LOCALSCRATCH and mirrors back to
# $ISALHG_RESULTS_ROOT/full/ on HOME. Each unit writes only under its own
# directory <unit>/, so the tasks of the array never write the same file and the
# copy-back (rsync, no --delete) cannot clobber another task's unit. Before the
# payload, each unit's directory already on HOME is copied onto the node: every
# design CLI resumes from what is on disk, so a resubmitted task recomputes only
# the missing seeds.
#
# isalhg resolves through the editable install of the canonical IsalHG-tkde tree
# (common.sh, "PYTHONPATH does NOT decide where isalhg comes from"). This wave
# changes nothing under src/** (checksum-identical to that tree, 2026-10-15), so
# the private $REPO_DIR deploys scripts/ and experiments/ only.

#SBATCH --job-name=tkde-knn
#SBATCH --time=0-12:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --constraint=sd
#SBATCH --account=tic_163_uma

set -euo pipefail

: "${REPO_DIR:?REPO_DIR not set -- submit via knn_launcher.sh}"
# shellcheck source=/dev/null
source "${REPO_DIR}/slurm/tkde/common.sh"
export ISALHG_CORPORA_ROOT="${ISALHG_CORPORA_ROOT:-${ISALHG_DATA_ROOT}/corpora}"

tkde_job_header "tkde-knn"
tkde_stage_localscratch "full"
cd "${REPO_DIR}"

TASK_IDX="${SLURM_ARRAY_TASK_ID:-0}"
WALL_S="${KNN_WALL_S:-43200}"
UNIT_BUDGET_S="${KNN_UNIT_BUDGET_S:-3600}"
TEARDOWN_S=600
CUTOFF_EPOCH=$(( TKDE_START_TIME + WALL_S - TEARDOWN_S - UNIT_BUDGET_S ))
RUNNER="scripts/newpos/knn/full_run.py"

N_TASKS=$("${PY}" "${RUNNER}" --list-tasks | wc -l)
GROUP=$("${PY}" "${RUNNER}" --list-tasks | awk -v t="${TASK_IDX}" '$1 == t {print $2}')
[[ -n "${GROUP}" ]] || { echo "[FATAL] task ${TASK_IDX} not in --list-tasks (${N_TASKS} tasks)" >&2; exit 1; }

# Echo the decoded assignment: a silently wrong decode produces a complete,
# plausible, WRONG result set.
echo ""
echo "Task:          ${TASK_IDX} of ${N_TASKS}"
echo "Units:         ${GROUP}"
echo "Start cutoff:  $(date -d "@${CUTOFF_EPOCH}" --iso-8601=seconds)"
echo "Out (staged):  ${OUT_DIR}"
echo "Copy-back:     ${TKDE_DEST_DIR}"
echo ""

"${PY}" - <<'PYEOF'
import os
import sys

sys.path.insert(0, os.path.join(os.environ["REPO_DIR"], "scripts", "newpos", "knn"))
import isalhg
import knn_lib
from experiments.tkde import corpora

# Assert the DIRECTORY NAME, never equality with $REPO_DIR: ~/fscratch is a
# symlink to /mnt2/fscratch/users/..., so a correct path reports the /mnt2
# spelling and a startswith($REPO_DIR) check fails on it (PICASSO.md section 1).
name = os.path.basename(os.environ["REPO_DIR"])
for mod in (knn_lib, corpora):
    assert f"/{name}/" in mod.__file__, f"{mod.__name__} resolves outside {name}: {mod.__file__}"
assert "IsalHG-tkde" in isalhg.__file__, f"isalhg resolves outside the campaign: {isalhg.__file__}"
root = corpora.corpora_root()
assert (root / "wd50k66" / "records.jsonl").is_file(), f"no frozen corpora under {root}"
print(f"[ok] knn_lib     -> {knn_lib.__file__}")
print(f"[ok] experiments -> {corpora.__file__}")
print(f"[ok] isalhg      -> {isalhg.__file__}")
print(f"[ok] corpora     -> {root}")
PYEOF

# Resume: bring each unit's directory already on HOME onto the node.
IFS=',' read -r -a UNITS <<< "${GROUP}"
for U in "${UNITS[@]}"; do
    if [[ -d "${TKDE_DEST_DIR}/${U}" ]]; then
        mkdir -p "${OUT_DIR}/${U}"
        rsync -a "${TKDE_DEST_DIR}/${U}/" "${OUT_DIR}/${U}/"
        echo "[resume] ${U}: $(find "${OUT_DIR}/${U}" -type f | wc -l) file(s) on the node"
    fi
done

if [[ -n "${KNN_SMOKE:-}" ]]; then
    # The one placement allowed under the floor: seed 0 of one unit per design CLI
    # (full_run.SMOKE_UNITS), staged under _smoke/ so it shares no path with the
    # campaign's units and the idempotent full run cannot mistake it for done work.
    echo "[smoke] seed 0 of full_run.SMOKE_UNITS into _smoke/"
    tkde_run_synced "${PY}" "${RUNNER}" --smoke \
        --out "${OUT_DIR}/_smoke" --n-jobs "${SLURM_CPUS_PER_TASK:-1}"
else
    tkde_run_synced "${PY}" "${RUNNER}" --task "${TASK_IDX}" --out "${OUT_DIR}" \
        --n-jobs "${SLURM_CPUS_PER_TASK:-1}" --start-cutoff-epoch "${CUTOFF_EPOCH}"
fi

# A mirror of an empty tree reports "copy-back OK" too (rq8_worker.sh); refuse it.
N_JSON=$(find "${OUT_DIR}" -name '*.json' | wc -l)
if [[ "${N_JSON}" -eq 0 ]]; then
    echo "[FATAL] ${OUT_DIR} holds no JSON after the payload ran" >&2
    exit 1
fi
echo "[ok] ${N_JSON} JSON file(s) staged"
tkde_sync_partial

tkde_job_footer
