#!/usr/bin/env bash
# Submit RQ5 on the ordered walk -- the D-ART6 swap (T-KBab).
#
#   bash slurm/tkde/rq5_ow_launcher.sh
#   bash slurm/tkde/rq5_ow_launcher.sh --smoke
#   bash slurm/tkde/rq5_ow_launcher.sh --test-only
#
# A thin wrapper, deliberately. RQ5's arm set is entirely config-driven (each
# experiment block carries its own `arms:` list), so the swap needs no Python
# change and no second worker: it is rq5_launcher.sh with RQ5_CONFIG pointed at
# configs/rq5_ow.yaml, a private REPO_DIR and the wave's results root.
#
# No --dependency is passed. The `isal_ow_struct` matrices for wd50k66 and
# wd50k100 were built by the campaign's matrices job and are already cached; the
# launcher asserts they are present rather than trusting that, because a missing
# cache makes the runner raise MatrixCacheMissingError halfway through a job
# that has already burned its placement.
#
# Prints the job id on the last line.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TKDE_USER_ROOT="/mnt/home/users/tic_163_uma/mpascual"

export REPO_DIR="${REPO_DIR:-${TKDE_USER_ROOT}/fscratch/repos/IsalHG-rq8}"
export ISALHG_RESULTS_ROOT="${ISALHG_RESULTS_ROOT:-${TKDE_USER_ROOT}/results/IEEETKDE_ow}"
export RQ5_CONFIG="${RQ5_CONFIG:-experiments/tkde/configs/rq5_ow.yaml}"

# The cached matrices live under the CAMPAIGN's results root and are shared
# read-only. The wave's root symlinks `matrices` at them (T-KBn precedent), so
# --matrices-root "${ISALHG_RESULTS_ROOT}" in the shared worker resolves there.
MATRICES_SRC="${TKDE_MATRICES_SRC:-${TKDE_USER_ROOT}/results/IEEETKDE/matrices}"
mkdir -p "${ISALHG_RESULTS_ROOT}"
if [[ ! -e "${ISALHG_RESULTS_ROOT}/matrices" ]]; then
    ln -sfn "${MATRICES_SRC}" "${ISALHG_RESULTS_ROOT}/matrices"
    echo "linked ${ISALHG_RESULTS_ROOT}/matrices -> ${MATRICES_SRC}" >&2
fi

# Assert the arm the swap is FOR is actually cached, on every collection the
# config names. A missing .npy is the one failure that looks like queue time.
for collection in wd50k66 wd50k100; do
    target="${ISALHG_RESULTS_ROOT}/matrices/${collection}/isal_ow_struct.npy"
    [[ -f "${target}" ]] || {
        echo "FATAL: no cached isal_ow_struct matrix at ${target}" >&2
        echo "       run the matrices job for ${collection} before this swap." >&2
        exit 1
    }
    echo "  [ok] ${target}" >&2
done

exec bash "${SCRIPT_DIR}/rq5_launcher.sh" "$@"
