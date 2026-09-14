#!/usr/bin/env bash
# Submit RQ3 v2 (the golden record) to Picasso.
#
# Run this ON PICASSO's login node, from the deployed private tree:
#   bash slurm/tkde/rq3v2_launcher.sh --dry-run     # print the sbatch command
#   bash slurm/tkde/rq3v2_launcher.sh --test-only   # sbatch --test-only
#   bash slurm/tkde/rq3v2_launcher.sh --smoke       # one short task on a tiny cell
#   bash slurm/tkde/rq3v2_launcher.sh               # the full campaign
#
# Deployment, ruled by the orchestrator on 2026-09-13 after FSCRATCH was measured
# at its file quota with the grace period expired:
#   * the runner tree is PRIVATE and on HOME  (~/repos/IsalHG-rq3v2), because a
#     mkdir under ~/fscratch/repos now fails with "Disk quota exceeded";
#   * the conda environment is the SHARED isalhg-tkde on FSCRATCH, read-only and
#     never rebuilt: this campaign changes nothing under src/, so a private env
#     would rebuild a byte-identical extension for nothing;
#   * the corpora are read-only on FSCRATCH;
#   * every result lands on HOME under ~/results/IEEETKDE_ow/.
# The editable install resolves isalhg.* through the environment's finder to the
# shared IsalHG-tkde checkout while PYTHONPATH takes experiments.* from REPO_DIR,
# which is the isolation that matters between two agents sharing one env.
#
# Sizing. The default array is deliberately coarse: SCBI asks for the fewest,
# longest tasks (soporte@scbi.uma.es, 2026-08-07, two-hour floor). Set
# TKDE_N_SHARDS and TKDE_N_TASKS from the measured per-collection cost in
# RQ3V2_PILOT.md rather than from these defaults.
#
# Output lands in ${ISALHG_RESULTS_ROOT}/RQ3v2_golden_record/ on HOME; harvest
# with scripts/tkde/harvest_from_picasso.sh.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TKDE_USER_ROOT="/mnt/home/users/tic_163_uma/mpascual"

# HOME, not FSCRATCH: the quota there is exhausted and writes are refused.
REPO_DIR="${REPO_DIR:-${TKDE_USER_ROOT}/repos/IsalHG-rq3v2}"
LOGS_DIR="${TKDE_LOGS_DIR:-${TKDE_USER_ROOT}/execs/tkde/logs}"
RESULTS_ROOT="${ISALHG_RESULTS_ROOT:-${TKDE_USER_ROOT}/results/IEEETKDE_ow}"
DATA_ROOT="${ISALHG_DATA_ROOT:-${TKDE_USER_ROOT}/fscratch/datasets/isalhg_tkde}"
CONDA_ENV="${TKDE_CONDA_ENV:-isalhg-tkde}"
CONDA_PREFIX_DIR="${TKDE_CONDA_PREFIX:-${TKDE_USER_ROOT}/fscratch/conda_envs/${CONDA_ENV}}"

# experiments.tkde.corpora resolves the corpora under the RESULTS root by
# default; on Picasso they live under the DATA root, so the runner is told.
CORPORA_ROOT="${TKDE_CORPORA_ROOT:-${DATA_ROOT}}"

N_SHARDS="${TKDE_N_SHARDS:-486}"
N_TASKS="${TKDE_N_TASKS:-122}"
# 64 tasks x 4 cpus = 256 cores, well inside the 9,000-core QOS cap, and it
# halves the makespan against a throttle of 32: the campaign runs in two rounds
# of tasks rather than four.
MAX_CONCURRENT="${TKDE_MAX_CONCURRENT:-64}"
WALL="${TKDE_WALL:-0-08:00:00}"
START_CUTOFF_S="${TKDE_START_CUTOFF_S:-21600}"

WORKER="${SCRIPT_DIR}/rq3v2_worker.sh"
[[ -f "${WORKER}" ]] || { echo "ERROR: worker not found: ${WORKER}" >&2; exit 1; }

# ---------------------------------------------------------------------------
# The recovery pass after campaign 2308421 (37 of 122 tasks hit the 8 h wall).
#
# The re-price from that campaign's own logs put one unit at 0.19-3.13 h in the
# LIGHT cells and at or beyond the 8 h wall in the HEAVY ones, so the two halves
# cannot share a submission. The cause is the exact-HGED judge, not the ball: at
# N = 15 the ball is 127 s of a >= 540 s collection, and the remaining ~410 s is
# ~20 judge calls on the merges' large wrong records, which grow with N because
# align_merge_iter admits constants at >= N/2 agreement. The declared
# restricted-ball fallback would save about a fifth of that and was therefore NOT
# applied; the orchestrator ruled the oracle budget down instead (option B).
#
# LIGHT cells keep the frozen 60 s budget and the original tag: they resume.
# HEAVY cells re-run ALL 27 seeds under a shorter budget, which is a measured
# parameter and so carries its own tag. All 27, not only the missing ones,
# because the analyzer refuses a cell measured half under one oracle budget and
# half under another; the first pass's partial rows for those cells are
# superseded at analysis time with --supersede-tag.
LIGHT_CELLS="ndc_classes|non_star_N5_t1:ndc_classes|non_star_N5_t2:ndc_classes|non_star_N9_t1:wd50k66|non_star_N5_t2:wd50k66|non_star_N9_t1:wd50k66|star_N9_t2:wd50k66|star_N15_t1"
EMPTY_CELLS="ndc_classes|star_N5_t1:ndc_classes|star_N5_t2:ndc_classes|star_N9_t1:ndc_classes|star_N9_t2:ndc_classes|star_N15_t1:ndc_classes|star_N15_t2"
HEAVY_CELLS="ndc_classes|non_star_N9_t2:ndc_classes|non_star_N15_t1:ndc_classes|non_star_N15_t2:wd50k66|non_star_N9_t2:wd50k66|non_star_N15_t1:wd50k66|non_star_N15_t2:wd50k66|star_N15_t2"

# Worst case for the heavy budget, stated so the choice is checkable: at N = 15 a
# unit is 50 collections x ~20 judge calls = 1,000 calls. Every one timing out at
# 8 s is 8,000 s, plus the measured ball at 127 s x 50 = 6,350 s, plus merges and
# medoids at well under 1 s each: about 14,500 s = 4.0 h against a 6 h wall.
HEAVY_TIMEOUT_S="${TKDE_HEAVY_TIMEOUT_S:-8}"

MODE="submit"
SMOKE=0
RESUME_KIND=""
# Every argument is read, not just the first. The earlier single-`case "${1:-}"`
# form silently DROPPED a trailing flag: `--resume-heavy --dry-run` submitted a
# 189-task array while reporting a dry run (2026-09-14). A mode flag that can be
# ignored is how a campaign gets launched by someone who believes they previewed
# it, so an unknown or unreachable argument is now a refusal.
while (( $# )); do
    case "$1" in
        --dry-run)      MODE="dry" ;;
        --test-only)    MODE="test" ;;
        --smoke)        SMOKE=1 ;;
        --resume-light) RESUME_KIND="light" ;;
        --resume-empty) RESUME_KIND="empty" ;;
        --resume-heavy) RESUME_KIND="heavy" ;;
        *)              echo "ERROR: unknown option $1" >&2; exit 2 ;;
    esac
    shift
done
if [[ "${SMOKE}" == "1" && -n "${RESUME_KIND}" ]]; then
    echo "ERROR: --smoke and --resume-* are different submissions; pass one" >&2
    exit 2
fi

# A path under FSCRATCH here would be written to at run time and the job would
# die when the quota refused it. Refuse at submission instead.
for GUARDED in "${RESULTS_ROOT}" "${LOGS_DIR}" "${REPO_DIR}"; do
    case "${GUARDED}" in
        */fscratch/*)
            echo "ERROR: ${GUARDED} is under FSCRATCH, which is read-only for this campaign" >&2
            exit 2
            ;;
    esac
done

mkdir -p "${LOGS_DIR}" "${RESULTS_ROOT}"

# Picasso's Lua sbatch wrapper prepends ANSI codes and a multi-line warning to
# --parsable output. Take the LAST line first: a line-by-line sed leaves the
# banner's newlines in place and the guard then fires AFTER the job was
# submitted, leaving an untracked job on the cluster.
_clean_job_id() {
    tail -n 1 <<<"$1" | sed -e 's/\x1b\[[0-9;]*[a-zA-Z]//g' -e 's/[^0-9]//g'
}

COMMON_EXPORT="REPO_DIR=${REPO_DIR},ISALHG_RESULTS_ROOT=${RESULTS_ROOT}"
COMMON_EXPORT="${COMMON_EXPORT},ISALHG_DATA_ROOT=${DATA_ROOT}"
COMMON_EXPORT="${COMMON_EXPORT},TKDE_CORPORA_ROOT=${CORPORA_ROOT}"
COMMON_EXPORT="${COMMON_EXPORT},TKDE_LOGS_DIR=${LOGS_DIR}"
COMMON_EXPORT="${COMMON_EXPORT},TKDE_CONDA_ENV=${CONDA_ENV}"
COMMON_EXPORT="${COMMON_EXPORT},TKDE_CONDA_PREFIX=${CONDA_PREFIX_DIR}"

if [[ "${SMOKE}" == "1" ]]; then
    # The one job of this research question allowed under the two-hour floor: it
    # proves the deployed runner on a compute node before the campaign queues.
    ARGS=(
        --job-name=tkde-rq3v2-smoke
        --time=0-00:30:00
        --output="${LOGS_DIR}/tkde-rq3v2-smoke_%j.out"
        --error="${LOGS_DIR}/tkde-rq3v2-smoke_%j.err"
        --export="ALL,${COMMON_EXPORT},TKDE_SMOKE=1,TKDE_N_SHARDS=1,TKDE_N_TASKS=1,TKDE_RUN_ANALYZERS=1,TKDE_START_CUTOFF_S=1200"
        "${WORKER}"
    )
elif [[ -n "${RESUME_KIND}" ]]; then
    # One unit per task everywhere except the empty cells, so the start cutoff is
    # irrelevant (the first unit is always exempt) -- except there, where one task
    # holds them all and must be allowed to work through them.
    CUTOFF_R=1
    case "${RESUME_KIND}" in
        light)
            CELLS="${LIGHT_CELLS}"; RESUME=1; TIMEOUT_S=""
            N_UNITS="${TKDE_N_UNITS:-40}"; WALL_R="0-06:00:00"; MEM="32G"; THROTTLE_R=40 ;;
        empty)
            # Structurally empty by gate G0: one cell_empty row each, seconds of
            # work. They go in ONE task rather than 79, which is the only reading
            # of SCBI's floor that makes sense for work that cannot be lengthened.
            CELLS="${EMPTY_CELLS}"; RESUME=1; TIMEOUT_S=""
            N_UNITS=1; WALL_R="0-01:00:00"; MEM="8G"; THROTTLE_R=1; CUTOFF_R=3000 ;;
        heavy)
            # No --resume: all 27 seeds per cell must sit under the new tag.
            CELLS="${HEAVY_CELLS}"; RESUME=0; TIMEOUT_S="${HEAVY_TIMEOUT_S}"
            # 64G, not 32G: the first campaign peaked at 25.9 GB on 2308421_39,
            # a heavy task, and a 6 GB margin on the cells that grow fastest is
            # not a margin.
            N_UNITS="${TKDE_N_UNITS:-189}"; WALL_R="0-06:00:00"; MEM="64G"; THROTTLE_R=32 ;;
    esac
    THROTTLE=$(( THROTTLE_R < N_UNITS ? THROTTLE_R : N_UNITS ))
    ARGS=(
        --array="1-${N_UNITS}%${THROTTLE}"
        --time="${WALL_R}"
        --mem="${MEM}"
        --job-name="tkde-rq3v2-${RESUME_KIND}"
        --output="${LOGS_DIR}/tkde-rq3v2-${RESUME_KIND}_%A_%a.out"
        --error="${LOGS_DIR}/tkde-rq3v2-${RESUME_KIND}_%A_%a.err"
        --export="ALL,${COMMON_EXPORT},TKDE_SMOKE=0,TKDE_N_SHARDS=${N_UNITS},TKDE_N_TASKS=${N_UNITS},TKDE_RUN_ANALYZERS=0,TKDE_START_CUTOFF_S=${CUTOFF_R},TKDE_ONLY_CELLS=${CELLS},TKDE_RESUME=${RESUME},TKDE_HGED_TIMEOUT_S=${TIMEOUT_S}"
        "${WORKER}"
    )
else
    # The analyzer rides along only when one task holds every shard; otherwise it
    # would write an experiment-level table from a partial view.
    RUN_ANALYZERS=0
    (( N_TASKS == 1 )) && RUN_ANALYZERS=1
    THROTTLE=$(( MAX_CONCURRENT < N_TASKS ? MAX_CONCURRENT : N_TASKS ))
    ARGS=(
        --array="1-${N_TASKS}%${THROTTLE}"
        --time="${WALL}"
        --output="${LOGS_DIR}/tkde-rq3v2_%A_%a.out"
        --error="${LOGS_DIR}/tkde-rq3v2_%A_%a.err"
        --export="ALL,${COMMON_EXPORT},TKDE_SMOKE=0,TKDE_N_SHARDS=${N_SHARDS},TKDE_N_TASKS=${N_TASKS},TKDE_RUN_ANALYZERS=${RUN_ANALYZERS},TKDE_START_CUTOFF_S=${START_CUTOFF_S}"
        "${WORKER}"
    )
fi

if [[ "${MODE}" == "dry" ]]; then
    echo "[DRY-RUN] sbatch --parsable ${ARGS[*]}"
    exit 0
fi

if [[ "${MODE}" == "test" ]]; then
    sbatch --test-only "${ARGS[@]}"
    exit $?
fi

RAW=$(sbatch --parsable "${ARGS[@]}") || { echo "sbatch failed" >&2; exit 1; }
JOB_ID=$(_clean_job_id "${RAW}")
[[ "${JOB_ID}" =~ ^[0-9]+$ ]] || {
    echo "FATAL: unparsable job id: ${RAW@Q}" >&2
    echo "Run squeue NOW -- the job may already be queued." >&2
    exit 1
}

echo "Submitted RQ3 v2 job: ${JOB_ID}"
echo "Monitor:  sacct -j ${JOB_ID} -X -n -P -o JobID,State,Elapsed"
echo "Memory:   sacct -j ${JOB_ID} -n -P -o JobID,MaxRSS | grep '\.batch'"
echo "Logs:     ${LOGS_DIR}/tkde-rq3v2*_${JOB_ID}*.out"
echo "Results:  ${RESULTS_ROOT}/RQ3v2_golden_record/"
