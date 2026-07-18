# Scope T-M5 — the experiments

Restructured at D-ART2 (2026-07-18) around characterize → exploit. **The body**
is HGED-free and runs at `w*_c`-wall-clock scale: the static geometric
characterization (T-M5f: `ν`, `D̂`, distortion, concentration, hubness — the
per-corpus geometry table), the dynamic profiles (T-M5g: single-edit
sensitivity `s(e)` including the measured nauty contrast, and the ladder
response), and the four applications — MDS as the flagship that also measures
the geometry (T-M5b), k-medoids + dendrogram (T-M5c), kNN read against the
hubness precondition (T-M5d), and the shortest path with ladder-based scoring
and decoded S2H intermediates (T-M5e). **The discussion evidence** (T-M5a) is
small and runs last: the single ours-only exact-HGED correlation figure E1'
plus the information-content (bits) comparison. The v2 layer-1 validation
(competitor correlation rows, MI, the density sweep) is retired — see D-ART2
in `../DECISIONS.md`. Every experiment lives in `experiments/article/`; none
adds code to `src/`.
