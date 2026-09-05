#!/usr/bin/env bash
# Shared N x N distance matrices -- SLURM worker.
# Submit via matrices_launcher.sh. Do NOT submit directly.
#
# This is the FIRST job of wave 3 and the dependency root of three consumers:
# RQ2's false-merge census (agent rq-1-2-7), RQ4's screen and RQ5's clustering.
# All of them read the .npy files this job writes, so all of them wait on it
# with --dependency=afterok.
#
# ---------------------------------------------------------------------------
# Why this worker does NOT stage on $LOCALSCRATCH
# ---------------------------------------------------------------------------
# The many-small-files rule (manual §4.9) exists for payloads that create
# thousands of tiny files on shared GPFS. This job writes 26 files totalling
# ~1.2 GB -- wd50k66 alone is 3,988 x 3,988 float32 = 63.6 MB per arm -- which
# is the opposite pattern: few files, large, written once.
#
# More importantly, the consumers run in OTHER jobs on OTHER nodes and must
# find these matrices at the shared path. $LOCALSCRATCH is per-node and
# invisible from anywhere else, so staging here would either hide the output
# from every consumer until the copy-back, or (worse) lose it entirely if the
# copy-back failed. The job therefore writes straight into
# $ISALHG_RESULTS_ROOT, which is on HOME (permanent, quota-checked: 24 GB of
# 280 GB used, 3.3k of 35k files) and is the durable location anyway.
#
# ---------------------------------------------------------------------------
# Sizing (measured, not guessed)
# ---------------------------------------------------------------------------
# Per-pair costs measured on the 200-member audit samples and re-measured here
# on a 1,500-pair wd50k66 sample: netlsd 1.75 ms, hpd_jsd 0.62 ms,
# bipartite_ged_path 88 us, nauty_cert 58 us, nauty_cert_rows 61 us,
# wl_l1 45 us, bipartite_ged_assign 42 us, degree_seq_l1 2.6 us, size_l1 0.2 us.
# fact_rank goes through the words path (one encoding per member + one cdist)
# and is seconds, not hours.
#
#   wd50k66     7,949,178 pairs -> ~5.9 core-hours (NetLSD is 3.9 of them)
#   ndc_classes   952,890 pairs -> ~0.7 core-hours
#   wd50k100    1,686,366 pairs -> ~0.1 core-hours (five cheap arms only)
#   total                        ~6.6 core-hours
#
# At 32 cores that is well under an hour. The 12 h wall is headroom for a
# 2-3x miss on the estimate, not an expectation.
#
# ---------------------------------------------------------------------------
# On the two-hour floor (SCBI, 2026-08-07)
# ---------------------------------------------------------------------------
# This is ONE submitted job, not an array. The floor exists because thousands
# of short tasks cost the scheduler more to place than to run; a single job is
# ~1/1000 of the burden the request was about. Padding it to two hours by
# asking for fewer cores would delay RQ2, RQ4 and RQ5 -- every one of which
# waits on it -- for no scheduler benefit. Declared deliberately.

#SBATCH --job-name=tkde-matrices
#SBATCH --time=0-12:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=64G
#SBATCH --constraint=sd
#SBATCH --account=tic_163_uma

set -euo pipefail

: "${REPO_DIR:?REPO_DIR not set -- submit via matrices_launcher.sh}"
# shellcheck source=/dev/null
source "${REPO_DIR}/slurm/tkde/common.sh"

tkde_job_header "tkde-matrices"
cd "${REPO_DIR}"

CONFIG="${MATRICES_CONFIG:-experiments/tkde/configs/matrices.yaml}"
SHARD="${MATRICES_SHARD:-0/1}"

echo ""
echo "Config:        ${CONFIG}"
echo "Shard:         ${SHARD}"
echo "Writing to:    ${ISALHG_RESULTS_ROOT}/matrices/ (direct, no LOCALSCRATCH)"
echo "Unit count:    $("${PY}" -m experiments.tkde.matrices --config "${CONFIG}" --count)"
echo ""

# Prove the interpreter resolves the deployed tree before spending 32 cores on
# it. A wrong resolution is silent: the run succeeds against someone else's
# code. `experiments.*` must come from THIS checkout; `isalhg.*` legitimately
# resolves through the editable-install finder of the canonical IsalHG-tkde
# tree, which is correct because src/** is byte-identical here.
"${PY}" - <<'PYEOF'
import os
import experiments.tkde.matrices as m
import isalhg
repo = os.environ["REPO_DIR"]
assert m.__file__.startswith(repo), f"experiments resolves outside {repo}: {m.__file__}"
assert "IsalHG-tkde" in isalhg.__file__, f"isalhg resolves outside the campaign: {isalhg.__file__}"
print(f"[ok] experiments -> {m.__file__}")
print(f"[ok] isalhg      -> {isalhg.__file__}")
PYEOF

mkdir -p "${ISALHG_RESULTS_ROOT}/matrices"

"${PY}" -m experiments.tkde.matrices \
    --config "${CONFIG}" \
    --out "${ISALHG_RESULTS_ROOT}" \
    --data-root "${ISALHG_DATA_ROOT}" \
    --shard "${SHARD}"

echo ""
echo "---------- produced ----------"
find "${ISALHG_RESULTS_ROOT}/matrices" -name '*.npy' -printf '%10s  %p\n' | sort -k2

tkde_job_footer
