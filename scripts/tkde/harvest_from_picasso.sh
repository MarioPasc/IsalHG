#!/usr/bin/env bash
# Harvest the Picasso TKDE results tree onto the local drive.
#
# Runs LOCALLY.
#   bash scripts/tkde/harvest_from_picasso.sh --dry-run   # list what would come
#   bash scripts/tkde/harvest_from_picasso.sh             # copy
#   bash scripts/tkde/harvest_from_picasso.sh RQ1_addressing   # one subtree
#
# Never deletes local files: no --delete, ever. FSCRATCH is pseudo-volatile
# (files unaccessed for >2 months may be pre-deleted without notice), so the
# local drive is the durable copy and the remote is the transient one. A harvest
# that could remove a local result would invert that.

set -euo pipefail

TKDE_USER_ROOT="/mnt/home/users/tic_163_uma/mpascual"
REMOTE="${TKDE_REMOTE:-picasso}"
REMOTE_RESULTS="${TKDE_REMOTE_RESULTS:-${TKDE_USER_ROOT}/fscratch/results/IEEETKDE}"
LOCAL_RESULTS="${ISALHG_RESULTS_ROOT:-/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE}"

SSH_OPTS=(-o ServerAliveInterval=60)

DRY_RUN=0
SUBTREE=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=1; shift ;;
        -*) echo "ERROR: unknown option $1" >&2; exit 2 ;;
        *)  SUBTREE="$1"; shift ;;
    esac
done

SRC="${REMOTE}:${REMOTE_RESULTS}/"
DST="${LOCAL_RESULTS}/"
if [[ -n "${SUBTREE}" ]]; then
    SRC="${REMOTE}:${REMOTE_RESULTS}/${SUBTREE}/"
    DST="${LOCAL_RESULTS}/${SUBTREE}/"
fi

echo "=== harvest_from_picasso ==="
echo "from : ${SRC}"
echo "to   : ${DST}"
echo "date : $(date --iso-8601=seconds)"

if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo ""
    echo "--- remote tree ---"
    ssh "${SSH_OPTS[@]}" "${REMOTE}" \
        "ls -laR '${REMOTE_RESULTS}${SUBTREE:+/${SUBTREE}}' 2>&1 | head -80"
    echo ""
    echo "--- rsync dry-run ---"
    rsync -a --dry-run -v --info=stats1 -e "ssh ${SSH_OPTS[*]}" "${SRC}" "${DST}"
    exit 0
fi

mkdir -p "${DST}"
rsync -a --info=stats1 -e "ssh ${SSH_OPTS[*]}" "${SRC}" "${DST}"

echo ""
echo "=== HARVEST OK ==="
find "${DST}" -type f | wc -l | xargs echo "local files under ${DST}:"
