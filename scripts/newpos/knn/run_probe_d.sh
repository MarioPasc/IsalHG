#!/usr/bin/env bash
# Run every Design-D job locally (pendant on the 4 collections, empirical on the 2 WD50K), then
# aggregate. Usage: run_probe_d.sh <out_dir> <S> <seed> [<seed> ...]
set -euo pipefail
OUT="$1"; S="$2"; shift 2
PY="${PY:-$HOME/.conda/envs/isalhg/bin/python}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$OUT"
for collection in wd50k66 wd50k100 ndc_classes ndc_substances; do
  "$PY" "$HERE/design_d.py" --collection "$collection" --mix pendant --seeds "$@" --out "$OUT" \
    --sources "$S" --n-jobs "${N_JOBS:-16}"
done
for collection in wd50k66 wd50k100; do
  "$PY" "$HERE/design_d.py" --collection "$collection" --mix empirical --seeds "$@" --out "$OUT" \
    --sources "$S" --n-jobs "${N_JOBS:-16}"
done
"$PY" "$HERE/aggregate_d.py" --inputs "$OUT"
