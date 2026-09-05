#!/usr/bin/env bash
# Shared environment and helpers for every IEEE TKDE worker on Picasso.
#
# Contract (frozen; wave-3 launchers depend on it):
#   source "${REPO_DIR}/slurm/tkde/common.sh"   # AFTER the #SBATCH header
#
# Exports:
#   PY                    absolute python of the isalhg-tkde env
#   REPO_DIR              /mnt/.../fscratch/repos/IsalHG-tkde
#   ISALHG_DATA_ROOT      /mnt/.../fscratch/datasets/isalhg_tkde   (raw/ corpora/)
#   ISALHG_RESULTS_ROOT   /mnt/.../fscratch/results/IEEETKDE
#   TKDE_LOGS_DIR         /mnt/.../execs/tkde/logs
#   PYTHONPATH            "$REPO_DIR/src:$REPO_DIR"
#   PYTHONUNBUFFERED=1
#   OMP_NUM_THREADS / MKL_NUM_THREADS / OPENBLAS_NUM_THREADS / NUMEXPR_NUM_THREADS
#                         from SLURM_CPUS_PER_TASK (override by exporting
#                         TKDE_THREADS=1 BEFORE sourcing, for timing arms)
#   PYTHONPYCACHEPREFIX   per-task (Picasso's default is shared per-user and
#                         races across the 52 tasks on one node)
#
# Functions:
#   tkde_job_header                      reproducibility banner
#   tkde_stage_localscratch <subdir>     OUT_DIR on the node + copy-back traps
#   tkde_sync_partial                    mirror back mid-job, keep the node copy
#   tkde_finalize                        force the copy-back early (idempotent)
#   tkde_job_footer                      elapsed wall-clock
#
# Environment fixes below are inherited from the working F4 probe worker
# (scripts/diagnostics/d_art3_probes_2026-09-03/f4_topology/slurm/f4_ea_worker.sh),
# which is the only IsalHG worker measured green on this cluster. Do not drop a
# line because it looks redundant: each one was added because something failed.

# --------------------------------------------------------------------------
# Paths (frozen contract)
# --------------------------------------------------------------------------
TKDE_USER_ROOT="/mnt/home/users/tic_163_uma/mpascual"

export REPO_DIR="${REPO_DIR:-${TKDE_USER_ROOT}/fscratch/repos/IsalHG-tkde}"
export TKDE_CONDA_ENV="${TKDE_CONDA_ENV:-isalhg-tkde}"
export TKDE_CONDA_PREFIX="${TKDE_CONDA_PREFIX:-${TKDE_USER_ROOT}/fscratch/conda_envs/${TKDE_CONDA_ENV}}"
export ISALHG_DATA_ROOT="${ISALHG_DATA_ROOT:-${TKDE_USER_ROOT}/fscratch/datasets/isalhg_tkde}"
export ISALHG_RESULTS_ROOT="${ISALHG_RESULTS_ROOT:-${TKDE_USER_ROOT}/fscratch/results/IEEETKDE}"
export TKDE_LOGS_DIR="${TKDE_LOGS_DIR:-${TKDE_USER_ROOT}/execs/tkde/logs}"

# --------------------------------------------------------------------------
# Python interpreter
# --------------------------------------------------------------------------
# The env is NOT under ~/.conda/envs on Picasso (measured 2026-09-05): conda
# envs live in ~/fscratch/conda_envs. Address the interpreter absolutely rather
# than relying on `conda activate` leaving the right thing on PATH -- an
# activation that half-fails is silent, an absolute path that is wrong is not.
export PY="${TKDE_CONDA_PREFIX}/bin/python"

if [[ ! -x "${PY}" ]]; then
    echo "[FATAL] interpreter not found: ${PY}" >&2
    echo "        run scripts/tkde/picasso_env_setup.sh on the login node first" >&2
    return 1 2>/dev/null || exit 1
fi

# conda activate is still performed so that CONDA_PREFIX, LD_LIBRARY_PATH and
# the env's bin/ (pytest, ruff) are available to anything that shells out.
_tkde_module_loaded=0
for _m in miniconda/3 miniconda3 Miniconda3 anaconda3 Anaconda3 miniforge mambaforge; do
    if module avail 2>&1 | grep -qiE "(^|/)${_m}([[:space:]]|/|$)"; then
        module load "${_m}" >/dev/null 2>&1 && _tkde_module_loaded=1 && break
    fi
done
if [[ "${_tkde_module_loaded}" -eq 0 ]]; then
    if [[ -r "/mnt/home/soft/miniconda/programs/x86_64/miniconda3_py310_23.1.0/etc/profile.d/conda.sh" ]]; then
        # shellcheck disable=SC1091
        source "/mnt/home/soft/miniconda/programs/x86_64/miniconda3_py310_23.1.0/etc/profile.d/conda.sh" || true
    fi
fi
if command -v conda >/dev/null 2>&1; then
    # shellcheck disable=SC1091
    source "$(conda info --base)/etc/profile.d/conda.sh" 2>/dev/null || true
    conda activate "${TKDE_CONDA_ENV}" 2>/dev/null || source activate "${TKDE_CONDA_ENV}" 2>/dev/null || true
fi
unset _m _tkde_module_loaded

# --------------------------------------------------------------------------
# Interpreter environment
# --------------------------------------------------------------------------
# PYTHONPATH ahead of the editable-install .pth entry keeps the Python half and
# the compiled half on ONE tree. Without it a repo-relative run resolves half
# its imports from a different checkout, with no error.
export PYTHONPATH="${REPO_DIR}/src:${REPO_DIR}${PYTHONPATH:+:${PYTHONPATH}}"
export PYTHONUNBUFFERED=1

_tkde_threads="${TKDE_THREADS:-${SLURM_CPUS_PER_TASK:-1}}"
export OMP_NUM_THREADS="${_tkde_threads}"
export MKL_NUM_THREADS="${_tkde_threads}"
export OPENBLAS_NUM_THREADS="${_tkde_threads}"
export NUMEXPR_NUM_THREADS="${_tkde_threads}"
unset _tkde_threads

# Picasso exports a SHARED PYTHONPYCACHEPREFIX (/localscratch/users/<user>), so
# every task of this user on a node writes the same .pyc paths. Symptom is an
# intermittent ModuleNotFoundError on a module that is plainly present. Give
# each task its own prefix.
TKDE_TASK_TAG="${SLURM_JOB_ID:-local}_${SLURM_ARRAY_TASK_ID:-0}"
export TKDE_TASK_TAG
if [[ -n "${LOCALSCRATCH:-}" && -d "${LOCALSCRATCH}" ]]; then
    export PYTHONPYCACHEPREFIX="${LOCALSCRATCH}/${USER}/${TKDE_TASK_TAG}/pycache"
else
    export PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/${USER}/tkde_${TKDE_TASK_TAG}/pycache"
fi
mkdir -p "${PYTHONPYCACHEPREFIX}"

TKDE_START_TIME="${TKDE_START_TIME:-$(date +%s)}"
export TKDE_START_TIME

# --------------------------------------------------------------------------
# tkde_job_header -- reproducibility banner
# --------------------------------------------------------------------------
tkde_job_header() {
    echo "=========================================================="
    echo "TKDE job:      ${1:-${SLURM_JOB_NAME:-unnamed}}"
    echo "Job id:        ${SLURM_JOB_ID:-local}"
    echo "Array task:    ${SLURM_ARRAY_TASK_ID:-N/A} (job ${SLURM_ARRAY_JOB_ID:-N/A})"
    echo "Node:          $(hostname)"
    echo "CPU model:     $(lscpu 2>/dev/null | sed -n 's/^Model name: *//p' | head -1)"
    echo "CPUs/task:     ${SLURM_CPUS_PER_TASK:-?}   threads=${OMP_NUM_THREADS}"
    echo "Mem requested: ${SLURM_MEM_PER_NODE:-?} MB"
    echo "Repo:          ${REPO_DIR}"
    # The deployed tree has no .git (rsync excludes it), so the provenance SHA
    # comes from the stamp sync_to_picasso.sh writes. git is the fallback for a
    # tree that does happen to be a checkout.
    if [[ -r "${REPO_DIR}/.tkde_deploy" ]]; then
        echo "Deployed:      $(tr '\n' ' ' < "${REPO_DIR}/.tkde_deploy")"
    else
        echo "Git SHA:       $(git -C "${REPO_DIR}" rev-parse --short HEAD 2>/dev/null || echo n/a)"
    fi
    echo "Python:        ${PY}"
    echo "Data root:     ${ISALHG_DATA_ROOT}"
    echo "Results root:  ${ISALHG_RESULTS_ROOT}"
    echo "Start:         $(date --iso-8601=seconds)"
    echo "=========================================================="
}

# --------------------------------------------------------------------------
# tkde_stage_localscratch <results_subdir>
# --------------------------------------------------------------------------
# Creates ${MYLOCALSCRATCH}/out on the compute node's local disk, exports it as
# OUT_DIR, and installs EXIT/TERM/INT traps that mirror the WHOLE out/ tree into
# ${ISALHG_RESULTS_ROOT}/<results_subdir>/ and only then delete the node copy.
#
# Why the whole tree and never a file list: a copy-back that enumerates paths
# returns every file it named, so a payload artefact written outside those paths
# vanishes and nothing looks wrong until the analysis needs it.
#
# Why rsync: it writes each file to a temporary name in the destination
# directory and renames it, so a reader of a shared durable path sees the old
# file or the new one, never a truncated one. The cp fallback reproduces that
# by hand.
tkde_stage_localscratch() {
    local subdir="${1:?tkde_stage_localscratch requires a results subdirectory}"

    local root="${LOCALSCRATCH:-}"
    if [[ -z "${root}" || ! -d "${root}" ]]; then
        echo "[warn] LOCALSCRATCH unavailable; staging under ${TMPDIR:-/tmp}" >&2
        root="${TMPDIR:-/tmp}"
    fi

    MYLOCALSCRATCH="${root}/${USER}/${TKDE_TASK_TAG}"
    TKDE_DEST_DIR="${ISALHG_RESULTS_ROOT}/${subdir}"
    OUT_DIR="${MYLOCALSCRATCH}/out"
    export MYLOCALSCRATCH TKDE_DEST_DIR OUT_DIR

    mkdir -p "${OUT_DIR}" "${TKDE_DEST_DIR}"
    TKDE_FINALIZED=0

    trap 'tkde_finalize' EXIT
    # SLURM sends SIGTERM and waits KillWait before SIGKILL. Without these two
    # traps a wall-clock kill or scancel terminates the shell WITHOUT running
    # the EXIT trap, and the whole task's output dies on the node.
    trap 'exit 143' TERM
    trap 'exit 130' INT

    echo "[stage] node scratch : ${OUT_DIR}"
    echo "[stage] copy-back to : ${TKDE_DEST_DIR}"
}

# --------------------------------------------------------------------------
# tkde_finalize -- mirror out/ back; idempotent, safe to call mid-job
# --------------------------------------------------------------------------
tkde_finalize() {
    [[ "${TKDE_FINALIZED:-0}" == "1" ]] && return 0
    [[ -z "${MYLOCALSCRATCH:-}" || -z "${TKDE_DEST_DIR:-}" ]] && return 0
    [[ ! -d "${MYLOCALSCRATCH}/out" ]] && return 0

    local ok=1
    mkdir -p "${TKDE_DEST_DIR}"
    if command -v rsync >/dev/null 2>&1; then
        rsync -a "${MYLOCALSCRATCH}/out/" "${TKDE_DEST_DIR}/" || ok=0
    else
        local rel dest
        while IFS= read -r -d '' rel; do
            dest="${TKDE_DEST_DIR}/${rel}"
            mkdir -p "$(dirname "${dest}")"
            cp -a "${MYLOCALSCRATCH}/out/${rel}" "${dest}.tmp.${TKDE_TASK_TAG}" \
                && mv -f "${dest}.tmp.${TKDE_TASK_TAG}" "${dest}" || ok=0
        done < <(cd "${MYLOCALSCRATCH}/out" && find . -type f -printf '%P\0')
    fi

    if [[ "${ok}" == "1" ]]; then
        TKDE_FINALIZED=1
        echo "[stage] copy-back OK -> ${TKDE_DEST_DIR}"
        rm -rf --one-file-system "${MYLOCALSCRATCH}"
    else
        echo "[FATAL] copy-back FAILED; results remain at ${MYLOCALSCRATCH} on $(hostname)" >&2
    fi
}

# --------------------------------------------------------------------------
# tkde_sync_partial -- mirror out/ back WITHOUT deleting the node copy
# --------------------------------------------------------------------------
# Call after each unit inside a bundled job. The per-unit copy bounds the loss
# when the node dies at hour 5 of 6; the final whole-tree mirror in
# tkde_finalize is what guarantees completeness.
tkde_sync_partial() {
    [[ -z "${MYLOCALSCRATCH:-}" || -z "${TKDE_DEST_DIR:-}" ]] && return 0
    [[ ! -d "${MYLOCALSCRATCH}/out" ]] && return 0
    mkdir -p "${TKDE_DEST_DIR}"
    if command -v rsync >/dev/null 2>&1; then
        rsync -a "${MYLOCALSCRATCH}/out/" "${TKDE_DEST_DIR}/" \
            || echo "[warn] partial copy-back failed; retrying at job end" >&2
    fi
}

# --------------------------------------------------------------------------
# tkde_job_footer
# --------------------------------------------------------------------------
tkde_job_footer() {
    local elapsed=$(( $(date +%s) - TKDE_START_TIME ))
    echo "=========================================================="
    echo "Finished:  $(date --iso-8601=seconds)"
    printf 'Duration:  %dh %dm %ds\n' \
        $(( elapsed / 3600 )) $(( (elapsed / 60) % 60 )) $(( elapsed % 60 ))
    echo "=========================================================="
}
