#!/usr/bin/env bash
# RQ2 on the ordered walk -- the D-ART6 swap (T-KBab). SLURM worker.
# Submit via rq2_ow_launcher.sh. Do NOT submit directly.
#
# Why this file exists at all, since the swap is a config change. RQ2's ARM SET
# is config-driven, but the CONFIG PATH is not: rq2_worker.sh line 25 and
# rq2_launcher.sh line 19 both hard-code configs/rq2.yaml with no environment
# override. Reusing them would therefore have run the swap against the
# `wstar_orbit` arm list. Editing the shared pair is out of this agent's scope
# (another agent is running RQ3 v2 off the same directory this wave), so the ow
# variant is a copy of rq2_worker.sh differing in exactly three places:
#
#   1. CONFIG is read from ${RQ2_CONFIG}, defaulting to configs/rq2_ow.yaml;
#   2. the job name is tkde-rq2-ow.
#
# EXPERIMENT is deliberately "wellposedness", the SAME as the shared worker's.
# It is not a free choice. `experiments/tkde/rq2.py` builds its output path from
# a MODULE CONSTANT --
#
#     paths = RunPaths(root=results_root, rq=RQ_FOLDER, experiment=EXPERIMENT)
#
# -- and never reads the config's `experiment:` key, so naming this variable
# anything else points the symlink at a directory the runner will not write to.
# Measured 2026-09-13 (jobs 2308342 / 2308343): with EXPERIMENT="wellposedness_ow"
# every one of 22 tasks ran its units, logged "copy-back OK", and delivered ZERO
# rows -- the runner wrote to ${STAGE_ROOT}/RQ2_wellposedness/wellposedness, a
# plain directory outside the mirrored out/ tree, and the whole night's work died
# with the nodes. This is the same defect slurm/tkde/README.md records for the
# 2026-09-07 rank run.
#
# Separation from the `wstar_orbit` census does not need a directory rename and
# never did: the results ROOT already differs (~/results/IEEETKDE_ow against the
# campaign's ~/results/IEEETKDE), and the run tag differs because the arm list
# does. The assertion below makes the coupling explicit so it cannot rot.
#
# Everything else is byte-for-byte the shared worker's, including the smoke's
# private matrices directory -- which is not cosmetic: the smoke configuration
# puts ndc_classes in census_own_collections over a 20-member subset, so through
# the shared symlink it would overwrite the real ndc_classes cache with a toy.

# Memory, measured rather than inherited. The shared worker asks for 32 G; on
# this arm set that is too tight. Jobs 2308342_*, MaxRSS off the .batch step:
# the bipartite units dominate, task 3 completed at 26.1 GB and task 10 was
# OUT_OF_MEMORY at 31.4 GB after 5 h 55 m -- still climbing, so its true peak is
# unknown and 32 G cannot be shown to be enough for any of them. 96 G is ~3x the
# only observed floor, schedules on every sd node (182 GB usable) and costs
# queue time rather than a lost run.
#SBATCH --job-name=tkde-rq2-ow
#SBATCH --time=1-00:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=96G
#SBATCH --constraint=sd
#SBATCH --account=tic_163_uma

set -euo pipefail

: "${REPO_DIR:?REPO_DIR not set -- submit via rq2_ow_launcher.sh}"

# The oracle-ceiling rows report wall-clock, so every arm is single-threaded;
# the census's parallelism is process-level (n_jobs), not thread-level.
export TKDE_THREADS=1

# shellcheck source=/dev/null
source "${REPO_DIR}/slurm/tkde/common.sh"

RQ_FOLDER="RQ2_wellposedness"
EXPERIMENT="wellposedness"
CONFIG="${RQ2_CONFIG:-${REPO_DIR}/experiments/tkde/configs/rq2_ow.yaml}"

# The generic half of the 2026-09-13 lesson. `tkde_finalize` prints "copy-back
# OK" whenever the mirror command succeeds, and mirroring an EMPTY tree succeeds,
# so a run that produced nothing is indistinguishable in the log from one that
# worked. This refuses to reach the copy-back at all when the staged tree holds
# no row file -- a loud non-zero exit instead of a successful-looking empty run.
#
# It lives here rather than in common.sh only because common.sh is read-only to
# this agent; it belongs there, and T-KBac proposes the move.
tkde_assert_out_dir_not_empty() {
    local n
    n=$(find "${OUT_DIR}" -name 'rows_*.csv' 2>/dev/null | wc -l)
    if [[ "${n}" -eq 0 ]]; then
        echo "" >&2
        echo "[FATAL] ${OUT_DIR} holds no rows_*.csv after the payload ran." >&2
        echo "        The copy-back would mirror an empty tree and report OK." >&2
        echo "        Usual cause: the runner wrote outside the mirrored out/" >&2
        echo "        tree -- check the experiment/folder names against the" >&2
        echo "        runner's own constants." >&2
        find "${MYLOCALSCRATCH}" -name 'rows_*.csv' 2>/dev/null | head -5 >&2
        exit 1
    fi
    echo "[ok] ${n} row file(s) staged in ${OUT_DIR}"
}

tkde_job_header "tkde-rq2-ow"
# The smoke gets its own results subtree: its unit ids come from the same
# namespace as the real run's (exact0-ndc_classes-fact_rank is BOTH a smoke unit
# and a full-run unit), so a smoke row file in the real directory would make the
# full run skip that unit as already done and substitute 5 pairs for 100.
STAGE_SUBDIR="${RQ_FOLDER}/${EXPERIMENT}"
[[ "${TKDE_SMOKE:-0}" == "1" ]] && STAGE_SUBDIR="${RQ_FOLDER}/_smoke/${EXPERIMENT}"
tkde_stage_localscratch "${STAGE_SUBDIR}"
cd "${REPO_DIR}"

echo ""
echo "Config:     ${CONFIG}"
echo "Experiment: ${EXPERIMENT}"
echo "Results:    ${ISALHG_RESULTS_ROOT}"
echo ""

STAGE_ROOT="${MYLOCALSCRATCH}/root"
mkdir -p "${STAGE_ROOT}/${RQ_FOLDER}"
ln -sfn "${OUT_DIR}" "${STAGE_ROOT}/${RQ_FOLDER}/${EXPERIMENT}"

# The rows reach HOME only if the directory the RUNNER writes to is the one this
# worker symlinked into the mirrored out/ tree. That is an assumption about
# another module's constants, so it is asserted rather than trusted: a mismatch
# here produced 22 successful-looking tasks and zero rows (2026-09-13). Checked
# before any unit runs, so the cost of being wrong is a failed job instead of a
# lost night.
"${PY}" - "${RQ_FOLDER}" "${EXPERIMENT}" <<'PYEOF'
import sys

import experiments.tkde.rq2 as runner

want_folder, want_experiment = sys.argv[1], sys.argv[2]
assert runner.RQ_FOLDER == want_folder, (
    f"worker RQ_FOLDER={want_folder!r} but rq2.py writes to {runner.RQ_FOLDER!r}"
)
assert runner.EXPERIMENT == want_experiment, (
    f"worker EXPERIMENT={want_experiment!r} but rq2.py writes to "
    f"{runner.EXPERIMENT!r} -- rq2.py takes this from a module constant, NOT from "
    "the config's `experiment:` key, so the symlink would point at a directory "
    "the runner never writes to and every row would die on the node"
)
print(f"[ok] runner writes to {runner.RQ_FOLDER}/{runner.EXPERIMENT}")
PYEOF

# ... and that the link really lands inside the tree tkde_finalize mirrors.
# BOTH sides are canonicalised. Picasso exports LOCALSCRATCH with a trailing
# slash, so MYLOCALSCRATCH is `/localscratch/users//mpascual/<job>`; `readlink
# -f` collapses the double slash on the left-hand side only, and comparing a
# canonical path against a raw one failed 22 tasks on a correct layout
# (job 2311493). `-m` is used because it canonicalises a path that need not
# exist yet.
LINK_TARGET="$(readlink -f "${STAGE_ROOT}/${RQ_FOLDER}/${EXPERIMENT}")"
MIRRORED_ROOT="$(readlink -m "${MYLOCALSCRATCH}/out")"
case "${LINK_TARGET}" in
    "${MIRRORED_ROOT}"*) echo "[ok] rows land in ${LINK_TARGET} (mirrored)" ;;
    *)
        echo "[FATAL] ${STAGE_ROOT}/${RQ_FOLDER}/${EXPERIMENT} resolves to" >&2
        echo "        ${LINK_TARGET}, which is outside ${MIRRORED_ROOT} -- " >&2
        echo "        the copy-back would report success and deliver nothing." >&2
        exit 1
        ;;
esac
# matrices/ is a SHARED input (and, for ndc_substances, a shared output), so in
# a real run it points at the durable root rather than at the node: staging it
# would hide the cache the shared matrices job wrote and rebuild every arm.
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

tkde_assert_out_dir_not_empty
tkde_job_footer
