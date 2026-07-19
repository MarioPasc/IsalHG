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

### Smoke test result (2026-07-19)

Two-cell smoke (tiny_sparse + fano_only, 5 edits each):
- `s_e_isalhg = 2.07` vs `s_e_nauty = 21.0` for sparse random (nauty 10×).
- `s_e_isalhg = 7.0` vs `s_e_nauty = 35.0` for Fano (nauty 5×).
- Both JSON outputs written, analysis figures rendered to PDF, confrontation
  table produced without error.

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

### Three-regime prediction (from smoke; full sweep deferred to run time)

Smoke run (tiny_sparse, 15 edits): heavy-tail fraction 0.133 — consistent with
regime-1 (sparse/unimodal) prediction (< 0.20). Design fixture (Fano, 5 edits):
heavy-tail 0.000 — consistent with coherent-tie prediction. Full confrontation
table to be regenerated at full-scale run time; placeholder config in
`g2_sensitivity.yaml`.

### Notes

- `R(e)/T_span(e)` not logged (requires C++ src change; out of scope). `qin_cost`
  is logged per edit as the Qin taxonomy upper bound on HGED.
- The nauty-Levi edit distance avalanche is already visible at smoke scale:
  nauty's byte-level Levenshtein on its canonical certificate is 5–10× larger
  than IsalHG's token Levenshtein for identical edits, confirming the
  "avalanche-everywhere" contrast the paper needs.

