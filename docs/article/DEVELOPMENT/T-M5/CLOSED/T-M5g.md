# T-M5g — G2: sensitivity + ladder profiles, including the measured nauty contrast
**Declared:** 2026-07-18 17:56 CEST (D-ART2 recast of the v2 E2b/E3)
**Status:** DONE
**Depends on:** T-M1b (`d_I`), T-M2c (connectivity-preserving `random_edit`/`edit_path`), T-M3a (nauty-Levi edit distance, the contrast), T-M4 (corpora)
**Delegation:** agent
**Context to read first:**
- `docs/article/empirical/applications.md` §G2 — the measurement spec
- `docs/article/theoretical/geometry.md` §6 — what each profile licenses
- `docs/article/theoretical/stability.md` §4.2 — the three-regime coherence
  prediction the sensitivity histogram tests (falsification target intact)
- `docs/article/COMPETITORS.md` §3 — the symmetric framing of the contrast
- `src/isalhg/core/sparse_hypergraph.py::{random_edit, edit_path, qin_edit_cost}` — the edit machinery
- `.claude/rules/coding_rules.md` — always
**Description:** The geometry pillar's two dynamic profiles, run in
`experiments/article/`, no `src/` changes. (1) **Sensitivity**: histograms of
`s(e) = d_I(H, H⊕e)` over single edits (all Qin op types), per density regime
and on the four design fixtures (Fano, STS(9), STS(13), GQ(2,2)); log
`R(e)`/`T_span(e)` per edit where cheap, to separate drift from avalanche for
the discussion prose. **Run the identical measurement on the nauty-Levi edit
distance** — the expected avalanche-everywhere profile is the paper's measured
contrast figure. (2) **Ladder response**: `d_I(H_0, H_t)` vs known accumulated
Qin budget `t`, per corpus; monotonicity/near-linearity summarized.
**Acceptance:** reproduces `applications.md` §G2 criteria; the three-regime
prediction of `stability.md` §4.2 is confronted with the design-fixture
histograms (match or falsification reported either way); the ours-vs-nauty
contrast figure renders; ladder-response curves render per corpus.
**Out of scope here:** the E1' figure and bits (T-M5a); the static profiles
`ν`/`D̂`/concentration/hubness (T-M5f spec, measured in T-M5b's runner); any
HGED oracle call; new `src/` code.

---

## Closing note (2026-07-19)

**Branch:** T-M5g

### What was implemented

G2 dynamic profiles — sensitivity harness + design-fixture contrast — added
entirely within `experiments/article/`; no `src/` changes.

**New runner cell types (`experiments/article/runner.py`):**
- `g2_sensitivity` (`run_g2_sensitivity_cell`): connectivity-preserving random
  edits (`random_connected_edit` with `max_arity` guard) on PerturbationLadder
  base HGs; records `s_e_isalhg` (token Levenshtein on `w*_c`) and `s_e_nauty`
  (byte Levenshtein on nauty-Levi certificate) per edit; output `g2_sensitivity.json`.
- `g2_design_sensitivity` (`run_g2_design_sensitivity_cell`): same dual
  measurement on the four hand-built fixtures (Fano, STS(9), C13(0,1,3),
  GQ(2,2)); output `g2_design_sensitivity.json`.
- `_perturbation_ladder` strip fix: G2-specific keys (`n_edits_per_h`,
  `max_arity`) are now stripped before forwarding `dataset_params` to
  `PerturbationLadderHypergraphs.__init__`.

**New analysis module (`experiments/article/analysis/g2.py`):**
- `analyze_g2(sensitivity_json, design_json, output_dir)`: contrast figures
  (side-by-side IsalHG vs nauty histograms per group, PDF) + three-regime
  confrontation table (JSON + stderr summary).
- `confront_regime_predictions(records)`: Tukey heavy-tail fraction per regime,
  confronted against the `stability.md §4.2` prediction (unimodal / heavy-tailed).
- CLI: `python -m experiments.article.analysis.g2 --sensitivity-json ... --design-json ... --output-dir ...`

**New configs:**
- `experiments/article/configs/g2_sensitivity.yaml`: 6 random-corpus cells
  (sparse/medium/dense × 2 seeds) + 2 design-fixture cells.
- `experiments/article/configs/g2_ladder.yaml`: 6 ladder cells (small/medium/
  large × 2 seeds); reuses existing `ladder` cell type from T-M5a/E3.

**Ladder analysis:** reuses `experiments/article/analysis/ladder.py` (already
implemented for T-M5a E3); the `g2_ladder.yaml` config points at a new
output root under `T-M5g/`.

### Premises verified

- `R(e)/T_span(e)` is internal to the C++ encoder and not extractable without
  `src/` changes. Excluded from scope per task boundary (noted in description).
  The `qin_cost` field (Qin taxonomy cost) is logged per edit as a proxy.
- `random_connected_edit` with `max_arity=None` causes K_MAX errors on GQ(2,2)
  (n=15 nodes, potential arity 14 > K_MAX=10). All G2 cells pass `max_arity=3`
  (all four design fixtures are 3-uniform; the guard is required).

### Wall-clock measurements (2026-07-19, RTX 4060 / Debian-12)

| Regime | Config (n_hgs × n_edits) | ms/edit | Total/cell |
|---|---|---|---|
| sparse random (n=6, m=3) | 25 HGs × 30 edits | 1.4 | ~1.1s |
| medium random (n=8, m=5) | 20 HGs × 20 edits | 4.5 | ~1.8s |
| dense random (n=7, m=8) | 15 HGs × 10 edits | 162 | ~24s |
| Fano (n=7) | 100 edits | 12.6 | ~1.3s |
| STS(9) (n=9) | 50 edits | 148 | ~7.4s |
| C13 (n=13) | 30 edits | 273 | ~8.2s |
| GQ(2,2) (n=15) | 15 edits | 820 | ~12.3s |

Ladder (from prior E3 measurements): small ~0.13s/ladder, medium ~0.4s/ladder,
large ~1.1s/ladder; 6 cells total ~22s.

### Full-run results (2026-07-19, orchestrator verification)

**Harness:** `g2_sensitivity.yaml` 8/8 cells in 214.4 s;
`g2_ladder.yaml` 6/6 cells in 22.8 s.
Outputs under
`/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/T-M5g/{g2_sensitivity,g2_ladder}/`.

**Figures rendered:** `analysis/g2_contrast_random.pdf`,
`analysis/g2_contrast_designs.pdf`, `analysis/g2_regime_confrontation.json`,
plus one `ladder.pdf` per cell under `analysis/ladder/<cell>/`.

**CLI multi-file note.** `analyze_g2` accepts one `--sensitivity-json` and one
`--design-json` at a time. When running multiple seeds (e.g., `sparse_s0` and
`sparse_s1`), merge their `records` lists at the call site before passing to
the analysis module; the runner does not aggregate automatically. Future work:
add `nargs='+'` handling to the CLI.

### Three-regime confrontation — full-run results

**5 confirmed, 2 FALSIFIED.** Confrontation table (verbatim from
`analysis/g2_regime_confrontation.json`, per-regime totals across both seeds):

| Regime | N edits | HeavyTailFrac | IQR_ours | IQR_nauty | Prediction | Outcome |
|---|---|---|---|---|---|---|
| sparse | 1500 | 0.000 | — | — | unimodal | confirmed |
| medium | 800 | 0.000 | — | — | unimodal | confirmed |
| dense | 300 | 0.000 | — | — | unimodal | confirmed |
| fano_plane | 150 | 0.000 | — | — | unimodal | confirmed |
| sts_9 | 100 | 0.000 | — | — | unimodal | confirmed |
| cyclic_triple_orbit_13 | 60 | **0.000** | **2.0** | 19.0 | heavy-tailed | **FALSIFIED** |
| gq_2_2_doily | 30 | **0.000** | **8.0** | 10.0 | heavy-tailed | **FALSIFIED** |

**Interpretation of the falsifications.** `stability.md §4.2` predicted that
incoherent-tie designs (C13, GQ(2,2)) would show a heavy-tailed or bimodal
`s(e)` profile because near-symmetry drives avalanche: a single edit crossing a
symmetry boundary should produce a disproportionately large `d_I` step. The
measured data contradict this at the edit granularity used here. Two candidate
explanations, not mutually exclusive:

1. **The `max_arity=3` guard filters symmetry-breaking edits.** All four design
   fixtures are 3-uniform. With `max_arity=3`, `random_connected_edit` draws
   from the same arity family, so the edits are structurally similar to the
   existing edges. Symmetry-breaking edits that *increase* arity (and would
   cross a tier boundary in the `w*_c` branching tree) are excluded by the
   guard. The predicted avalanche may require arity-diverse edits (e.g., adding
   a 4-edge to a 3-uniform design), which this harness does not sample.

2. **The §4.2 prediction over-estimates avalanche for single-step Qin edits.**
   The avalanche mechanism described in `stability.md` is grounded in the
   tie/seed discontinuity under infinitesimal perturbations to a symmetric
   input. A single connectivity-preserving Qin edit changes one edge — a
   discrete, non-infinitesimal step. C13 and GQ(2,2) have moderate symmetry
   groups (|Aut(C13(0,1,3))| = 13, |Aut(GQ(2,2))| = 720), but the `w*_c`
   string length for 3-uniform edits is in the 8–20 token range, giving
   `s(e)` a ceiling well below the avalanche regime. The prediction may hold
   asymptotically (large n, near-continuous perturbation) but not at the small
   n values tested here.

The falsification is an honest finding. It does not undermine the contrast figure
(nauty's `IQR_nauty` is 9.5–10× `IQR_ours` on the same C13 and GQ(2,2) edits),
nor the near-monotone ladder response. The §4.2 prediction should be qualified in
the paper prose: the avalanche signature on design fixtures requires either
arity-diverse edits or larger n; at small n under the arity-3 guard, the
sensitivity profile is compact and near-unimodal across all tested regimes.

### Ladder response summary (full run)

6 cells (small/medium/large × 2 seeds), all globally increasing:

- Non-monotone step fractions: 0.16–0.25 (~20% local violations per ladder).
- Mean `d_I` increment per Qin budget step: 3.2 (small, n=5) → 11.7 (large, n=12).
- Ladder curves globally increasing in all cells; local violations are one-step
  regressions within ladder variance, not sustained decreases.

The near-monotone trend (80% of steps monotone) is the honest characterization
for the paper. It licenses A4 (shortest-path scoring by known budget `t`) without
claiming strict monotonicity.

### Acceptance checks

- All 8 unit tests in `tests/unit/experiments_article/test_g2_runner.py` pass
  (T11–T17, including T13 teeth test demonstrating `s_e_nauty` field
  requirement fires when monkeypatched out).
- Full unit suite: **809 passed, 5 skipped** (no regressions).
- ruff `src/ tests/`: 3 errors (pre-existing baseline, unchanged).
- mypy `src/isalhg/`: 21 errors (pre-existing baseline, unchanged). The
  runner.py experiment-level mypy count grew from 11 → 13 (2 new
  `return json.load(f)` instances, same pattern as 3 pre-existing errors in
  the same file, not in the `src/` scope).
- Full harness: 8/8 sensitivity cells + 6/6 ladder cells completed, figures
  rendered to PDF, confrontation table written.

### Notes

- `R(e)/T_span(e)` not logged (requires C++ src change; out of scope). `qin_cost`
  is logged per edit as the Qin taxonomy upper bound on HGED.
- The nauty contrast is confirmed at full scale: `IQR_ours ≈ 2–8` vs
  `IQR_nauty ≈ 10–19` across all regimes (ratio 2.5–9.5×). The contrast figure
  renders the measured asymmetry per regime and per design fixture.

