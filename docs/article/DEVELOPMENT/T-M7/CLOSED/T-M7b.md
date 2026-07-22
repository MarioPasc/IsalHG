# T-M7b — Stratum B parametric sweep corpora + feasibility envelope
**Declared:** 2026-07-22 11:56 CEST
**Status:** OPEN
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
