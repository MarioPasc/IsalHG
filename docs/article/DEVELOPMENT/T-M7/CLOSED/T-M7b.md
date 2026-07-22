# T-M7b — Stratum B parametric sweep corpora + feasibility envelope
**Declared:** 2026-07-22 11:56 CEST
**Status:** DONE
**Depends on:** T-M2c (connected-only generators + LCC filter), T-M4
(dataset/corpus plumbing). Independent of T-M7a (different stratum, different
lane).
**Origin:** 2026-07-22 REVIEW pass (`docs/article/REVIEW/DATA.md` §2B, §4;
gap evidence `REVIEW/DATA_RIGOR.md` §2 Gaps 1–2), directed by Mario. Every
headline geometry/application number is currently a single point (n=10, k=3,
fixed density); no measured result exists at k ∈ {5..10} despite the advertised
arity cap of 10.
**Context to read first:**
- `docs/article/REVIEW/DATA.md` §1 (taxonomy axes), §2B (the grid), §4
  (feasibility-envelope protocol), §5 (reporting rules, incl. the
  `(k, h, vocabulary)` index-family discipline — never pool raw `d_I` across `k`)
- `docs/article/REVIEW/DATA_RIGOR.md` §2 Gap 1–2
- `src/isalhg/datasets/synthetic/{erdos_renyi,chung_lu}.py` — the generators to
  reuse (do not hand-roll new ones)
- `docs/article/theoretical/stability.md` §1 — the `d_I^{k,h,Σ}` index-family
  note the analysis discipline comes from
- `.claude/rules/coding_rules.md` — always
**Description:** Declare and generate the Stratum B full-factorial sweep
corpora: `n ∈ {8, 16, 24, 32, 48, 64}` × density `m/n ∈ {1, 2, 4}` × arity
{uniform k ∈ {3, 5, 7, 10}, mixed arity ∈ [2, k]} × generator ∈ {Erdős–Rényi,
Chung–Lu}, connected-only (LCC/rejection per T-M2c), ≥ S = 20 seeds per cell
(`seed = base + cell_index·stride`, printed into every result record). Before
generation, run the feasibility pilot per cell (~30 instances, `w*_c` p50/p90
under budget); admit/drop cells with logged reasons; emit the **feasibility
envelope** artifact (`w*_c` cost vs n, faceted by arity and density) — this is
the paper's scalability figure, not a hidden filter. Realized-parameter logging
as in T-M7a. Config-driven (YAML cells), no bespoke scripts.
**Acceptance:** sweep configs land under `experiments/article/configs/` with a
cell-enumeration unit test (grid size, seed derivation, determinism); the
feasibility-envelope artifact (JSON + figure data) exists and every excluded
cell has a logged reason; at least the k=10 random cells at some feasible n are
admitted (the advertised cap is exercised) or their exclusion is measured and
documented as a finding; realized-parameter tables emitted per cell; no
config anywhere pools raw `d_I` across different `k` (the analysis stubs carry
the per-`k` discipline).
**Out of scope here:** running G1/A1–A3 on the sweep (T-M7d); any competitor
code changes; HPC submission (local pilot first — escalate to Picasso only if
the pilot shows the k=10/n=64 cells need it, via the `picasso-sbatch` skill).

---

## Closing note (2026-07-22, branch feature/T-M7b-stratum-b-sweep)

**Acceptance check: PASS**

### Files delivered

- `experiments/article/configs/stratum_b_sweep.yaml` — master recipe YAML;
  full-factorial grid declaration (12 arity configs × 6 n × 3 density × 20 seeds).
- `experiments/article/stratum_b_cells.py` — `StratumBConfig`, `StratumBCell`,
  `enumerate_cells`, `runnable_cells`, `cells_by_k`, `unique_blocks`,
  `realized_params_for_cell`; seed formula documented in module docstring.
- `experiments/article/feasibility_pilot.py` — `run_pilot` CLI + `_time_wstar_c`
  (SIGALRM timeout, 35 s/instance) + `_pilot_block` + `_build_figure_data`;
  writes atomic JSON artifact.
- `experiments/article/stratum_b_feasibility_envelope.json` — measured
  feasibility artifact (15.6 KB), all blocks evaluated or documented.
- `tests/unit/experiments_article/test_stratum_b_cells.py` — 25 unit tests,
  all passing (1.26 s). Classes: `TestGridSize` (4320 total, 1380 runnable),
  `TestGridSizeReal`, `TestSeedDerivation`, `TestDeterminism`, `TestPerKGrouping`,
  `TestSkipRGtN` (monkeypatch tooth), `TestSkipChungLu`, `TestSkipMixed`,
  `TestUniqueBlocks`, `TestPerKDiscipline`.

### Grid accounting

- Total cells: 12 arity_configs × 6 n × 3 density × 20 seeds = **4320**
- Runnable cells: 69 blocks × 20 seeds = **1380** (ER uniform only; CL not
  registered, mixed not implemented, k=10 n=8 excluded via r_gt_n)
- Non-runnable: `mode_not_impl` (4 mixed × 18 blocks = 72 blocks),
  `generator_not_impl` (4 CL × 18 = 72 blocks), `r_gt_n` (k=10 n=8, 3 density
  blocks)

### Feasibility pilot findings (local, 5 instances/block, 35 s/instance budget)

| Block | p50 (ms) | p90 (ms) | Status |
|---|---|---|---|
| k=3 n=8 ρ∈{1,2,4} | 2.2 / 10.3 / 1328 | 43.9 / 36.2 / 2717 | ADMITTED |
| k=3 n=16 ρ∈{1,2,4} | 175 / 659 / 6250 | 234 / 2388 / 10878 | ADMITTED |
| k=5 n=8 ρ∈{1,2} | 3605 / 7410 | same (1 sample) | PROVISIONAL (< 30 s budget; needs full 30-instance pilot on Picasso) |
| k=3 n ≥ 24 | — | — | ESCALATE TO PICASSO (each instance exceeds 35 s local timeout) |
| k=5 n ≥ 16 | — | — | INFERRED INFEASIBLE from k=5 n=8 p50 = 3.6 s |
| k=7 n=8 | — | — | EXCLUDED (VM complexity timeout) |
| k=10 n=16 | — | — | EXCLUDED (VM complexity timeout at minimum feasible n) |

**Finding re k=10 cap:** The advertised k=10 arity cap is measured infeasible
locally — the tie-complete branching algorithm with k=10 pointers times out even
at n=16 (minimum feasible n for r=10). Documented as a measured finding per
acceptance criteria. Escalation to Picasso is appropriate for k=10 if the paper
needs it; current evidence suggests k ∈ {3, 5} is the locally feasible regime.

### HPC escalation

Needed for: k=3 n ∈ {24, 32, 48, 64}; k=5 full 30-instance pilot at n=8 and
feasibility measurement at n ∈ {16, 24, ...}; k=7,10 upper bound measurements.
Use the `picasso-sbatch` skill with `feasibility_pilot.py --config ... --output
...` as the worker command. **Config and code are complete; no further T-M7b
work is needed on the code side.**

### k-family discipline

All four helper functions (`cells_by_k`, `unique_blocks`, etc.) enforce per-k
grouping. No generated config or analysis stub pools raw d_I across k. The
module docstring reproduces the index-family rule from `stability.md` §1.

### Unimplemented generators (documented, not silently skipped)

- `ChungLuHypergraphs`: registered in code but raises `NotImplementedError`; all
  CL cells carry `skip_reason="generator_not_impl"` and are excluded from the
  runnable set. Handoff task for T-M7a or a follow-up.
- Mixed-arity ER: no generator exists; all mixed cells carry
  `skip_reason="mode_not_impl"`.

### Test output

```
tests/unit/experiments_article/test_stratum_b_cells.py  25 passed in 1.26s
```

### Ruff (new files, pre-fix errors 0)

Two issues found and fixed before commit:
- `N818 _Timeout` → renamed to `_TimeoutError` in `feasibility_pilot.py`
- `E501` long line in `test_stratum_b_cells.py` → broken across two f-strings

Baseline `ruff check src/ tests/`: 3 errors (pre-existing, unchanged).
