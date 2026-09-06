#!/usr/bin/env bash
# RQ4 -- refill of the censored `hpd_jsd` arm. SLURM worker.
#
# Why this job exists. The vendored hyperedge-portrait code allocated the
# portrait's last axis with extent `N`, while the histogram it fills is indexed
# up to `max(1, N - 1)`; on a 3-fact record (N = 1) that is an out-of-bounds
# write and the arm raised. RQ4's `_row_worker` recorded `censored=1` rather
# than a number, on 266 AUC rows -- `hpd_jsd` x `missing_fact` x budget 2,
# across all seven sub-collections (133 units, two scores each). The library
# fix (`max(N, 2)`, src/isalhg/metric_space/representations/_hpd_vendor.py) is
# merged; this job re-scores THAT ARM ONLY, in THOSE UNITS ONLY, leaving the
# seven arms whose numbers are already frozen byte-identical.
#
# Submit (from a login node), with the PRIVATE deployment and env:
#   sbatch --export=ALL,REPO_DIR=...,TKDE_CONDA_ENV=...,TKDE_CONDA_PREFIX=... \
#          --output=... --error=... rq4_refill_worker.sh
#
# --------------------------------------------------------------------------
# No $LOCALSCRATCH staging -- deliberately.
# --------------------------------------------------------------------------
# `rq4.refill_unit` READS `<out>/RQ4_screen/rows/rows_auc__<unit>.csv`, drops
# the arm's rows, re-scores it and REWRITES the same file. Staged on a node's
# empty scratch it would find no AUC files, refill nothing, report success and
# copy an empty tree back. `--out` is therefore the real results root on HOME
# and the runner writes in place. `tkde_run_synced` is kept anyway: it
# backgrounds the payload so the shell can service SIGTERM, and its
# `tkde_sync_partial` is a documented no-op when nothing was staged.
#
# --------------------------------------------------------------------------
# Sizing (measured)
# --------------------------------------------------------------------------
# 133 censored units (shard 0/3: 45, 1/3: 44, 2/3: 44), one arm each. HPD costs
# ~0.62 ms/pair and a unit is n_anomalies x N pairs (ndc_classes 70 x 1381,
# wd50k66_Q5 92 x 1830, the rest smaller) -> ~2-3 core-h in total, i.e. well
# under an hour of wall on 8 cores including the per-shard corpus load and the
# kNN/LOF re-scoring. 4 h is >= 4x headroom. A single recovery job is exempt
# from the campaign's 2 h task floor.
#
# Memory: 48 G, the RQ4 request measured sufficient over the same corpora and
# the same 8-worker pool.
#
# --------------------------------------------------------------------------
# One process per shard, not one per unit
# --------------------------------------------------------------------------
# The shard split is not for parallelism here (one task runs all three) but for
# PROVENANCE: `refill_unit`'s manifest records `refilled_from`, the `src_deploy`
# stamp of `RQ4_screen/shard_<i>_3/manifest.json` -- the tree that produced the
# seven arms it did not touch. Run un-sharded, that lookup misses
# (`shard_all/manifest.json` does not exist) and the two halves of every
# refilled table lose their second provenance.

#SBATCH --job-name=tkde-rq4-refill
#SBATCH --time=0-04:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --constraint=sd
#SBATCH --account=tic_163_uma

set -euo pipefail

: "${REPO_DIR:?REPO_DIR not set -- submit with --export=ALL,REPO_DIR=...}"
# shellcheck source=/dev/null
source "${REPO_DIR}/slurm/tkde/common.sh"

tkde_job_header "tkde-rq4-refill"
cd "${REPO_DIR}"

CONFIG="${RQ4_CONFIG:-${REPO_DIR}/experiments/tkde/configs/rq4.yaml}"
ARM="${RQ4_REFILL_ARM:-hpd_jsd}"
N_SHARDS="${RQ4_REFILL_SHARDS:-3}"

echo "Arm:           ${ARM}"
echo "Shards:        ${N_SHARDS}"
echo "Writes into:   ${ISALHG_RESULTS_ROOT}/RQ4_screen/rows  (IN PLACE)"

# --------------------------------------------------------------------------
# Compute-node import chain. The login node carries modules the compute nodes
# do not, and the env was cloned rather than built here, so passing on the
# login node is not evidence. A wrong `isalhg` here would silently re-score the
# arm with the UNFIXED vendor and write plausible, wrong numbers over the
# censored ones -- which is worse than the censoring.
# --------------------------------------------------------------------------
"${PY}" - "${REPO_DIR}" <<'PYEOF'
import datetime, inspect, os, sys

repo = sys.argv[1]
tail = os.path.basename(repo)

import isalhg
print("isalhg     :", isalhg.__file__)
# ~/fscratch is a symlink to /mnt2/..., so a correct install reports the /mnt2
# spelling: assert the DIRECTORY NAME, never a prefix match on $REPO_DIR.
assert f"/{tail}/" in isalhg.__file__, f"isalhg resolves outside {tail}: {isalhg.__file__}"

import isalhg.core._core as native
print("extension  :", native.__file__)
print("built at   :", datetime.datetime.fromtimestamp(
    os.path.getmtime(native.__file__)).isoformat(timespec="seconds"))

from isalhg.metric_space.representations import _hpd_vendor as hv
assert "max(N, 2)" in inspect.getsource(hv.hyperedge_portrait), (
    "HPD FIX ABSENT: this deployment would re-censor or mis-score the arm"
)
print("hpd fix    : max(N, 2) present in hyperedge_portrait")
PYEOF

# --------------------------------------------------------------------------
# Smoke: prove the chain above plus the vendor's own regression suite and the
# runner's refill code path, WITHOUT touching the real tables. `--tag` puts the
# probe's rows_paths under `_smoke_refill/`, which holds no AUC files, so every
# unit is skipped and only a manifest is written there.
# --------------------------------------------------------------------------
if [[ -n "${TKDE_REFILL_SMOKE:-}" ]]; then
    echo "[smoke] hpd regression suite"
    "${PY}" -m pytest -q \
        tests/unit/metric_space/test_hpd_single_hyperedge.py \
        tests/unit/metric_space/test_hpd.py
    echo "[smoke] refill dry pass under _smoke_refill (expects 0 units rewritten)"
    tkde_run_synced "${PY}" -m experiments.tkde.rq4 \
        --config "${CONFIG}" \
        --out "${ISALHG_RESULTS_ROOT}" \
        --data-root "${ISALHG_DATA_ROOT}" \
        --matrices-root "${ISALHG_RESULTS_ROOT}" \
        --tag _smoke_refill \
        --refill-censored-arm "${ARM}" \
        --shard "0/${N_SHARDS}"
    tkde_job_footer
    exit 0
fi

for (( I = 0; I < N_SHARDS; I++ )); do
    echo ""
    echo "---------- refill shard ${I}/${N_SHARDS} ----------"
    tkde_run_synced "${PY}" -m experiments.tkde.rq4 \
        --config "${CONFIG}" \
        --out "${ISALHG_RESULTS_ROOT}" \
        --data-root "${ISALHG_DATA_ROOT}" \
        --matrices-root "${ISALHG_RESULTS_ROOT}" \
        --refill-censored-arm "${ARM}" \
        --shard "${I}/${N_SHARDS}"
done

echo ""
echo "---------- census of the rewritten tables ----------"
"${PY}" - "${ISALHG_RESULTS_ROOT}/RQ4_screen/rows" "${ARM}" <<'PYEOF'
import collections, csv, glob, os, sys

rows_dir, arm = sys.argv[1], sys.argv[2]
per_arm = collections.Counter()
censored = collections.Counter()
for path in glob.glob(os.path.join(rows_dir, "rows_auc__*.csv")):
    with open(path, encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            per_arm[row["arm"]] += 1
            if str(row.get("censored")) == "1":
                censored[row["arm"]] += 1
print("rows per arm :", dict(per_arm))
print("censored     :", dict(censored) or "none")
print(f"censored {arm}:", censored[arm])
PYEOF

tkde_job_footer
