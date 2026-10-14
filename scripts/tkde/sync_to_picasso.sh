#!/usr/bin/env bash
# Deploy the local IsalHG checkout to the Picasso TKDE repo and rebuild.
#
# Runs LOCALLY. Deployment is by rsync, never by git: the Picasso tree is a
# deployment target, not a checkout, and the campaign must be able to run a
# merged-but-unpushed wave.
#
#   bash scripts/tkde/sync_to_picasso.sh                     # sync + rebuild
#   bash scripts/tkde/sync_to_picasso.sh --repo-from <path>  # sync another tree
#   bash scripts/tkde/sync_to_picasso.sh --corpora           # also sync corpora/
#   bash scripts/tkde/sync_to_picasso.sh --no-build          # sync only
#   bash scripts/tkde/sync_to_picasso.sh --dry-run           # show what would move
#
# After the sync the remote reinstall runs (rm -rf build; pip install -e
# ".[dev]" --no-deps), its exit status is read DIRECTLY (never through a pipe --
# a pipe reports tail's status), and the extension's mtime is asserted to
# post-date the sync. A stale .so is the failure mode that produces wrong
# numbers with no error.

set -euo pipefail

TKDE_USER_ROOT="/mnt/home/users/tic_163_uma/mpascual"
REMOTE="${TKDE_REMOTE:-picasso}"
REMOTE_REPO="${TKDE_REMOTE_REPO:-${TKDE_USER_ROOT}/fscratch/repos/IsalHG-tkde}"
REMOTE_DATA="${TKDE_REMOTE_DATA:-${TKDE_USER_ROOT}/fscratch/datasets/isalhg_tkde}"
ENV_PREFIX="${TKDE_CONDA_PREFIX:-${TKDE_USER_ROOT}/fscratch/conda_envs/isalhg-tkde}"
LOCAL_RESULTS_ROOT="${ISALHG_RESULTS_ROOT:-/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE}"

SSH_OPTS=(-o ServerAliveInterval=60)

REPO_FROM=""
SYNC_CORPORA=0
DO_BUILD=1
DRY_RUN=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --repo-from) REPO_FROM="${2:?--repo-from needs a path}"; shift 2 ;;
        --corpora)   SYNC_CORPORA=1; shift ;;
        --no-build)  DO_BUILD=0; shift ;;
        --dry-run)   DRY_RUN=1; shift ;;
        *) echo "ERROR: unknown option $1" >&2; exit 2 ;;
    esac
done

if [[ -z "${REPO_FROM}" ]]; then
    REPO_FROM="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
fi
REPO_FROM="$(cd "${REPO_FROM}" && pwd)"
[[ -f "${REPO_FROM}/pyproject.toml" ]] || {
    echo "ERROR: ${REPO_FROM} does not look like the IsalHG repo (no pyproject.toml)" >&2
    exit 1
}

LOCAL_SHA="$(git -C "${REPO_FROM}" rev-parse --short HEAD 2>/dev/null || echo n/a)"
echo "=== sync_to_picasso ==="
echo "from   : ${REPO_FROM}  (${LOCAL_SHA})"
echo "to     : ${REMOTE}:${REMOTE_REPO}"
echo "date   : $(date --iso-8601=seconds)"

RSYNC_FLAGS=(-az --delete --info=stats1)
[[ "${DRY_RUN}" -eq 1 ]] && RSYNC_FLAGS+=(--dry-run -v)

# Directory excludes are ROOT-ANCHORED with a leading slash. An unanchored
# 'data/' matches at ANY depth: it silently dropped the packaged STS catalog
# src/isalhg/datasets/data/sts/*.txt, and smoke job 2210890 failed
# tests/unit/core/test_wstar_c_frozen.py with FileNotFoundError on sts13.txt.
# Only the cache/artefact patterns below are deliberately depth-independent.
EXCLUDES=(
    --exclude '/.git/'
    --exclude '/build/'
    --exclude '**/__pycache__/'
    --exclude '*.pyc'
    --exclude '*.so'
    --exclude '*.egg-info/'
    --exclude '/.pytest_cache/'
    --exclude '/.mypy_cache/'
    --exclude '/.ruff_cache/'
    --exclude '/.claude/worktrees/'
    --exclude '/.claude/notes/'
    --exclude '/data/'
    --exclude '/results/'
    --exclude '/outputs/'
    --exclude '/experiments/outputs/'
)

ssh "${SSH_OPTS[@]}" "${REMOTE}" "mkdir -p '${REMOTE_REPO}' '${REMOTE_DATA}/raw' '${REMOTE_DATA}/corpora'"

SYNC_EPOCH="$(date +%s)"
rsync "${RSYNC_FLAGS[@]}" "${EXCLUDES[@]}" \
    -e "ssh ${SSH_OPTS[*]}" \
    "${REPO_FROM}/" "${REMOTE}:${REMOTE_REPO}/"

# Provenance stamp: the deployed tree has no .git, so the worker's job header
# has nothing to report without this.
if [[ "${DRY_RUN}" -eq 0 ]]; then
    LOCAL_BRANCH="$(git -C "${REPO_FROM}" rev-parse --abbrev-ref HEAD 2>/dev/null || echo n/a)"
    ssh "${SSH_OPTS[@]}" "${REMOTE}" \
        "printf 'sha=%s branch=%s from=%s at=%s\n' '${LOCAL_SHA}' '${LOCAL_BRANCH}' '${REPO_FROM}' '$(date --iso-8601=seconds)' > '${REMOTE_REPO}/.tkde_deploy'"
fi

if [[ "${SYNC_CORPORA}" -eq 1 ]]; then
    if [[ -d "${LOCAL_RESULTS_ROOT}/corpora" ]]; then
        echo "[corpora] ${LOCAL_RESULTS_ROOT}/corpora -> ${REMOTE}:${REMOTE_DATA}/corpora"
        rsync -az --info=stats1 -e "ssh ${SSH_OPTS[*]}" \
            "${LOCAL_RESULTS_ROOT}/corpora/" "${REMOTE}:${REMOTE_DATA}/corpora/"
    else
        echo "[corpora] SKIP -- ${LOCAL_RESULTS_ROOT}/corpora does not exist yet"
    fi
fi

if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "[dry-run] no rebuild performed"
    exit 0
fi

if [[ "${DO_BUILD}" -eq 0 ]]; then
    echo "[build] --no-build: skipped"
    exit 0
fi

echo ""
echo "=== remote rebuild ==="
# The heredoc runs remotely; the exit status of the ssh call IS the remote
# script's status because the remote script exits non-zero on any failure.
ssh "${SSH_OPTS[@]}" "${REMOTE}" \
    "REMOTE_REPO='${REMOTE_REPO}' ENV_PREFIX='${ENV_PREFIX}' SYNC_EPOCH='${SYNC_EPOCH}' bash -s" <<'REMOTE_EOF'
set -euo pipefail
PY="${ENV_PREFIX}/bin/python"
[[ -x "${PY}" ]] || { echo "ERROR: ${PY} missing -- run picasso_env_setup.sh" >&2; exit 1; }

cd "${REMOTE_REPO}"
rm -rf build

set +e
"${PY}" -m pip install -e ".[dev]" --no-deps --no-build-isolation > /tmp/tkde_resync_build.log 2>&1
STATUS=$?
set -e
echo "PIP EXIT: ${STATUS}"
if [[ "${STATUS}" -ne 0 ]]; then
    tail -40 /tmp/tkde_resync_build.log
    exit "${STATUS}"
fi

PYTHONPATH="${REMOTE_REPO}/src:${REMOTE_REPO}" "${PY}" - "${SYNC_EPOCH}" <<'PYEOF'
import os, sys, datetime
sync_epoch = int(sys.argv[1])
import isalhg
assert "IsalHG-tkde" in isalhg.__file__, f"resolves outside IsalHG-tkde: {isalhg.__file__}"
import isalhg.core._core as native
mt = os.path.getmtime(native.__file__)
print("isalhg    :", isalhg.__file__)
print("extension :", native.__file__)
print("built at  :", datetime.datetime.fromtimestamp(mt).isoformat(timespec="seconds"))
assert mt >= sync_epoch, (
    f"STALE EXTENSION: .so mtime {mt} predates the sync at {sync_epoch}. "
    "The build did not actually rebuild it."
)
from isalhg.core.canonical import canonical_string
from isalhg.datasets.synthetic.designs import fano_plane
H = fano_plane()
assert canonical_string(H, backend="cpp") == canonical_string(H, backend="python")
print("verify    : extension fresh, cpp == python OK")
PYEOF
REMOTE_EOF

echo ""
echo "=== SYNC OK (${LOCAL_SHA}) ==="
echo "Next: ssh ${REMOTE} 'bash ${REMOTE_REPO}/slurm/tkde/smoke_launcher.sh --test-only'"
