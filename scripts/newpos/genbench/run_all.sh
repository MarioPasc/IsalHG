#!/usr/bin/env bash
# Full 27-seed pipeline: sample the three n-gram generators, evaluate (with the LCC repair
# arm), analyse, draw the figure. Idempotent: existing sample files are kept.
set -euo pipefail

PY="${PY:-$HOME/.conda/envs/isalhg/bin/python}"
RESULTS="${RESULTS:-/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/NEWPOS_2026-10-13/genbench_ngram}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORCE="${FORCE:-}"

"$PY" "$HERE/sample_ngram.py" --out "$RESULTS/samples" --workers 6 > "$RESULTS/sample_full.log" 2>&1
"$PY" "$HERE/evaluate.py" --samples "$RESULTS/samples" \
    --collection wd50k66 --collection ndc_classes --out "$RESULTS/scores" \
    --repair-lcc-of fact_ngram --write-repaired "$RESULTS/samples_repaired" \
    --workers 6 $FORCE > "$RESULTS/evaluate_full.log" 2>&1
"$PY" "$HERE/analyze.py" --eval "$RESULTS/scores" --out "$RESULTS" > "$RESULTS/analyze_full.log" 2>&1
"$PY" "$HERE/fig_rejection_bias.py" --eval "$RESULTS/scores" \
    --out "$RESULTS/fig_rejection_bias.pdf" > "$RESULTS/fig_full.log" 2>&1
echo "finished $(date -Iseconds)" > "$RESULTS/full_pipeline.done"
