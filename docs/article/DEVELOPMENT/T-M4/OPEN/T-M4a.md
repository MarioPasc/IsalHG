# T-M4a — Entropy-coded information-content estimator (arithmetic / universal integer codes)
**Declared:** 2026-07-17 19:56 CEST
**Status:** OPEN
**Note (D-ART2, 2026-07-18):** optional, non-blocking. The article's bits
subsection (PROPOSAL §4) uses the fixed-width estimator; this task is the
entropy-coded upgrade, run only if time permits or the PI asks.
**Depends on:** T-M4 (scoring primitives; the fixed-width estimator this extends). Shares the movement-block parser with T-TBc — coordinate, do not duplicate.
**Why out of scope:** PI email 2026-07-17 (Ezequiel): replace pointer-movement runs by arithmetic coding of the per-pointer displacement tuple, frequencies trained on a held-out random corpus; sign-bit + Gray-coded magnitude as the topology-preserving variant. Filed from the 2026-07-17 stability discussion; the metric-substrate half of the idea is T-TBc.
**Context to read first:**
- `docs/article/theoretical/stability_reformulations.md` §4 — why AC is compression-only (code-level avalanche makes AC bitstreams unusable as the `d_I` substrate)
- `docs/article/PROPOSAL.md` §4 — the current fixed-width estimator `B(w) = |w|·log2|Σ_HG(k)|` and the Wilcoxon protocol (v3 numbering)
- `docs/article/empirical/correlation.md` §Information content — the comparison this extends
- `docs/article/DEVELOPMENT/T-M4/OPEN/T-M4.md` — the scoring-primitive home this lands in
- `.claude/rules/coding_rules.md` — always
**Description:** Implement two alternative bit estimators for `w*_c`: (1) static arithmetic coding of displacement tuples with frequency tables trained on a dedicated random-hypergraph corpus **disjoint from every experiment corpus** (document it in DATA.md); (2) a model-free universal-code variant (sign bit + Elias-γ or Gray magnitude, ≈ `1 + O(log|δ|)` bits per displacement). Both replace the unary `Θ(|δ|)`-token accounting that makes bits scale with layout distance rather than structure. Report the PROPOSAL-§4 compression-ratio table under all three estimators (fixed-width / AC / universal). Extensibility to IsalGraph/IsalSR/IsalChem is noted only — no sibling-repo work.
**Acceptance:** estimators in `metric_space/metrics/` with unit tests (known-string bit counts pinned; AC decode round-trip); frequency-table corpus generation seeded, pinned, and documented in `docs/article/DATA.md`; the PROPOSAL-§4 comparison table produced on the pinned corpus with the Wilcoxon test rerun per estimator.
**Out of scope here:** any use of coded bitstreams as a distance substrate (T-TBc owns the metric axis); changes to `w*_c` or the encoder; sibling repositories.
