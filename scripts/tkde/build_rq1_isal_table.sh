#!/usr/bin/env bash
# Build the RQ1 table of the Isal instruction word from the three experiments
# that measured it on identical seeded units (T-KBe).
#
#   addressing       the campaign array (configs/rq1.yaml, jobs 2247394 +
#                    2247395) -- w*_c (`isalhg_levenshtein`), the fact arms,
#                    the certificate arms.  Launch tag 47c8a42c.
#   addressing_rank  wstar_rank on the C++ engine (configs/rq1_rank.yaml,
#                    job 2248782).
#   addressing_cpp   wstar_orbit and isal_ow_* on the C++ engines
#                    (configs/rq1_cpp.yaml, jobs 2248907 + 2248908).
#
# Two things this script exists to get right:
#
# 1. `RQ1_addressing/addressing` on the cluster holds TWO campaigns.  Launch
#    tag c3fb21de is the 2026-09-05 fact-rank campaign (job 2215137, rows
#    written 09-06 13:50 -> 09-07 04:08, before the instruction-granularity
#    columns d_instr/n_instr/aut_bucket existed); tag 47c8a42c is the Isal
#    campaign.  Both wrote the fact and certificate arms, so merging the
#    directory as a whole double-counts them.  --only-tags picks one launch and
#    the merge's duplicate audit refuses the job if any observation survives
#    twice.
# 2. `fact_rank_roles` fails the M0 relabelling-invariance gate (2,104
#    violations / 247 false splits on wd50k66) and must not reach a published
#    table (T-KBf).  It stays in the source experiments as the census that
#    condemns it.
#
# Run it on the Picasso login node (the rows live in ~/results there) or on a
# harvested copy.  The analyzer hardcodes the experiment name `addressing`, so
# the merged experiment keeps that name under a separate results root.
#
# Usage:
#   bash scripts/tkde/build_rq1_isal_table.sh [SRC_ROOT] [OUT_ROOT]

set -euo pipefail

SRC_ROOT="${1:-$HOME/results/IEEETKDE}"
OUT_ROOT="${2:-$HOME/results/IEEETKDE_isal_merged}"
ADDRESSING_TAG="${ADDRESSING_TAG:-47c8a42c}"

REPO_DIR="${REPO_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
PYTHON="${PYTHON:-$HOME/fscratch/conda_envs/isalhg-tkde/bin/python}"

export PYTHONPATH="${REPO_DIR}/src:${REPO_DIR}${PYTHONPATH:+:${PYTHONPATH}}"
cd "$REPO_DIR"

echo "== launch tags present in each source experiment =="
"$PYTHON" -m experiments.tkde.merge_rq1_experiments \
    --root "$SRC_ROOT" \
    --experiments addressing addressing_rank addressing_cpp \
    --out addressing --list-tags

# The gate: paired statistics over arms are only sound if the three
# experiments measured the same seeded units.  A non-zero exit here means an
# experiment is still incomplete -- do not build the table on it.
echo "== join check (identical seeded units) =="
"$PYTHON" scripts/tkde/verify_rq1_join.py \
    --root "$SRC_ROOT/RQ1_addressing" \
    --experiments addressing addressing_rank addressing_cpp \
    --only-tags "addressing=${ADDRESSING_TAG}" \
    --tables m1 m0items m3 \
    --out "$OUT_ROOT/RQ1_addressing/join_report.json"

echo "== merge, one source per arm =="
"$PYTHON" -m experiments.tkde.merge_rq1_experiments \
    --root "$SRC_ROOT" \
    --experiments addressing addressing_rank addressing_cpp \
    --only-tags "addressing=${ADDRESSING_TAG}" \
    --prefer wstar_rank=addressing_rank \
             wstar_orbit=addressing_cpp \
             isal_ow_struct=addressing_cpp \
             isal_ow_rank=addressing_cpp \
             isal_ow_rank0=addressing_cpp \
    --drop-arms fact_rank_roles \
    --out addressing --out-root "$OUT_ROOT" --overwrite

echo "== analyze =="
"$PYTHON" -m experiments.tkde.analyze_rq1 --root "$OUT_ROOT"

echo "== outputs =="
ls -la "$OUT_ROOT/RQ1_addressing/addressing/"*.md "$OUT_ROOT/RQ1_addressing/addressing/"*.json
