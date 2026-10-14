#!/usr/bin/env bash
# Deploy this agent's tree to its PRIVATE Picasso repo path (wave 2026-09-13-headline-w0).
#
#   bash slurm/tkde/rq8_sync.sh            # sync experiments/ + slurm/ + tests/
#   bash slurm/tkde/rq8_sync.sh --dry-run
#
# A wrapper over scripts/tkde/sync_to_picasso.sh, which is parameterised by
# TKDE_REMOTE_REPO / TKDE_CONDA_PREFIX and needs no edit. Two deliberate
# deviations from the shared deployment, both recorded here so the next reader
# does not have to reconstruct them:
#
# 1. REMOTE REPO is ~/repos/IsalHG-rq8, not ~/fscratch/repos/IsalHG-tkde. Two
#    reasons, one of which is forced. Private, because two agents deploy in this
#    wave and the canonical checkout is a shared input to both. On HOME, because
#    FSCRATCH was measured READ-ONLY on 2026-09-13: 276.3k files against a
#    250.0k soft quota whose grace has expired, so `mkdir ~/fscratch/repos/...`
#    returns "Disk quota exceeded". This contradicts slurm/tkde/README.md
#    ("Inputs stay on FSCRATCH: repo, env, raw data and corpora"), which exists
#    because HOME's file quota is normally the scarce one; the measured state is
#    currently the reverse. Read-only inputs are unaffected and stay put: the
#    conda env and the frozen corpora are read from FSCRATCH.
#
# 2. --no-build, and the SHARED isalhg-tkde env. common.sh states the rule: the
#    editable install is a PEP 660 meta-path finder, so `isalhg.*` always
#    resolves to the tree the ENV was installed from, while PYTHONPATH decides
#    only where `experiments.*` comes from. This wave changed nothing under
#    src/**, so a rebuild would produce an identical extension, and an env
#    installed from IsalHG-rq8 would break the `"IsalHG-tkde" in
#    isalhg.__file__` assertion every worker in this directory carries. A
#    private $REPO_DIR deployment changes experiments/** and slurm/** and
#    nothing else -- exactly the shape common.sh documents.
#
#    If a future wave DOES touch src/**, this wrapper must drop --no-build and
#    the env question has to be reopened; it is not a standing licence.
#
# The results root is the wave's clean root ~/results/IEEETKDE_ow (T-KBn), with
# `matrices` symlinked at the campaign cache by each launcher.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TKDE_USER_ROOT="/mnt/home/users/tic_163_uma/mpascual"

export TKDE_REMOTE_REPO="${TKDE_REMOTE_REPO:-${TKDE_USER_ROOT}/repos/IsalHG-rq8}"
export TKDE_CONDA_PREFIX="${TKDE_CONDA_PREFIX:-${TKDE_USER_ROOT}/fscratch/conda_envs/isalhg-tkde}"

echo "=== rq8_sync ==="
echo "repo    : ${REPO_ROOT}"
echo "remote  : ${TKDE_REMOTE_REPO}"
echo "env     : ${TKDE_CONDA_PREFIX} (shared, not rebuilt)"
echo "results : ${TKDE_USER_ROOT}/results/IEEETKDE_ow"
echo ""

exec bash "${REPO_ROOT}/scripts/tkde/sync_to_picasso.sh" \
    --repo-from "${REPO_ROOT}" \
    --no-build \
    "$@"
