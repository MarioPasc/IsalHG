#!/usr/bin/env bash
# Run every Design-C job (4 collections x 3 strata) locally, one after another, then aggregate.
# Usage: run_probe_c.sh <out_dir> <copies: 3|6> <seed> [<seed> ...]
set -euo pipefail
OUT="$1"; COPIES="$2"; shift 2
PY="${PY:-$HOME/.conda/envs/isalhg/bin/python}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$OUT"
for collection in wd50k66 wd50k100 ndc_classes ndc_substances; do
  for stratum in C-all C-int C-pend; do
    "$PY" "$HERE/design_c.py" --collection "$collection" --stratum "$stratum" \
      --seeds "$@" --out "$OUT" --copies "$COPIES" --n-jobs "${N_JOBS:-16}"
  done
done
"$PY" "$HERE/aggregate_c.py" --inputs "$OUT"
