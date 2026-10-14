#!/usr/bin/env bash
# Deploy the RQ3 v2 runner tree to Picasso, into its own private checkout.
#
# Run this LOCALLY:
#   bash slurm/tkde/rq3v2_sync.sh --dry-run
#   bash slurm/tkde/rq3v2_sync.sh
#
# This is a thin wrapper over scripts/tkde/sync_to_picasso.sh, which is shared
# with every other agent and is therefore not edited. Everything specific to this
# campaign is an environment override set here.
#
# Why these overrides (orchestrator ruling, 2026-09-13):
#
#   TKDE_REMOTE_REPO on HOME. FSCRATCH reached its file quota with the grace
#   period expired, so it is read-only: `mkdir ~/fscratch/repos/<anything>` fails
#   with "Disk quota exceeded". The private runner tree therefore lives at
#   ~/repos/IsalHG-rq3v2. Nothing there is written at run time --- it is imported,
#   not written --- so HOME carries only the deploy itself.
#
#   The SHARED environment, with --no-build. This campaign changes nothing under
#   src/, so a private environment would rebuild a byte-identical extension and
#   spend FSCRATCH inodes that are not available. The editable install resolves
#   isalhg.* through the environment's finder to the shared IsalHG-tkde checkout
#   while PYTHONPATH takes experiments.* from the private REPO_DIR, which is the
#   isolation that matters between two agents sharing one environment.
#
#   No corpora sync. They are already frozen on FSCRATCH and are read-only.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TKDE_USER_ROOT="/mnt/home/users/tic_163_uma/mpascual"

export TKDE_REMOTE="${TKDE_REMOTE:-picasso}"
export TKDE_REMOTE_REPO="${TKDE_REMOTE_REPO:-${TKDE_USER_ROOT}/repos/IsalHG-rq3v2}"
export TKDE_CONDA_ENV="${TKDE_CONDA_ENV:-isalhg-tkde}"
export TKDE_CONDA_PREFIX="${TKDE_CONDA_PREFIX:-${TKDE_USER_ROOT}/fscratch/conda_envs/${TKDE_CONDA_ENV}}"
export ISALHG_RESULTS_ROOT="${ISALHG_RESULTS_ROOT:-/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE}"

case "${TKDE_REMOTE_REPO}" in
    */fscratch/*)
        echo "ERROR: ${TKDE_REMOTE_REPO} is under FSCRATCH, whose quota is exhausted" >&2
        exit 2
        ;;
esac

echo "Deploying to  ${TKDE_REMOTE}:${TKDE_REMOTE_REPO}"
echo "Environment   ${TKDE_CONDA_PREFIX} (shared, not rebuilt)"
echo ""

# --no-build is load-bearing: the shared environment must not be reinstalled from
# this private tree, or the other agent's isalhg.* would start resolving here.
exec bash "${REPO_ROOT}/scripts/tkde/sync_to_picasso.sh" \
    --repo-from "${REPO_ROOT}" \
    --no-build \
    "$@"
