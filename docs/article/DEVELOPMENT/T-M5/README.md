# Scope T-M5 — the experiments

Two layers, deliberately separated by whether they need HGED. **Layer 1**
(T-M5a) is the controlled validation of the stability theorem: correlation of
`d_I` against exact HGED, the density sweep that tests Theorem B's falsifiable
`Δ`-dependence, the single-edit sensitivity histogram that tests the avalanche
story, and the information-content comparison in bits. It is bounded by the exact
HGED ceiling, so it runs small. **Layer 2** (T-M5b–e) is the applications — MDS
as the flagship, clustering with a dendrogram, kNN, and the shortest path between
hypergraphs that the canonical-form competitors structurally cannot compute. These
self-validate on task metrics and never call HGED, so their scale is gated only by
`w*` wall-clock. Every experiment lives in `experiments/article/`; none of them
adds code to `src/`.
