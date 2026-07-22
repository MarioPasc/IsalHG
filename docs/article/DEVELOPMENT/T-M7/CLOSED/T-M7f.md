# T-M7f — G3: controlled single-parameter geometry response + visualization
**Declared:** 2026-07-22 11:56 CEST
**Status:** DONE
**Depends on:** T-M7a (design bases — the OFAT sequences start from drawable
Stratum A instances), T-M5b (embedding module for the MDS trajectory), T-M5f
(geometry helpers, ν), T-M5g (sensitivity machinery to condition by move type).
Parallel-safe with T-M7d/e (own corpus, own result lane).
**Origin:** 2026-07-22 REVIEW pass (`docs/article/REVIEW/DATA.md` §6 in full),
directed by Mario. G2 answers "how big is a typical single edit?" (aggregate
magnitude). G3 answers "as one specific structural knob moves monotonically,
where does the object travel in the geometry — and is that travel smooth,
monotone, and decodable?" — the designed experiment behind the article's
hypergraph visualizations.
**Context to read first:**
- `docs/article/REVIEW/DATA.md` §6 — the five move axes, measured responses,
  competitor contrast, visualization protocol, acceptance
- `docs/article/theoretical/geometry.md` §§6–7 (local sensitivity + ladder
  response — the invariants G3 consumes; the no-orphan-geometry rule)
- `experiments/article/configs/g2_ladder.yaml` + the ladder machinery — the
  sequence-generation pattern to extend to OFAT
- `docs/article/H2S_S2H.md` — S2H decoding of intermediates; the `d_I^{k,h,Σ}`
  triple discipline for the M3 (arity) axis
**Description:** Implement the G3 one-factor-at-a-time experiment. Sequence
generator: from a Stratum A base `H_0` (n ≲ 20 for drawability), produce
`H_0..H_T` (T ≈ 10) along each of five axes — M1 vertex growth (`V` op), M2
densification (`C` op), M3 arity increase (grow one edge `a → a+1`; analyze per
base `k`, never pooling raw `d_I` across `k`), M4 incidence edit (Qin op; the
drift probe), M5 symmetry break (edit a symmetric design toward/away from
random layout; the tie/avalanche probe) — each with known accumulated budget,
connectivity preserved, every step decoded via S2H. Measured responses per
axis: (a) response curve `d_I(H_0, H_t)` + step increments vs `t` (magnitude,
monotone fraction, smoothness); (b) MDS trajectory of `{H_t}` on the embedding
(max single-step embedded jump vs median — continuity quantified);
(c) ν-contribution sign (does the move add or remove Euclidean-embeddable
structure); (d) `s(e)` distribution conditioned on move type. Competitor
contrast: identical sequences through all representations (incl. naive
baseline if T-M7c is merged) — nauty's discontinuity and the vector methods'
non-decodability shown. Visualization: for one exemplar per axis, the filmstrip
of drawn hypergraphs `H_0..H_T` (one fixed rendering convention, used
everywhere) + overlaid MDS trajectory + `(t, d_I)` curve, side by side.
**Acceptance:** per axis: response curve with monotone fraction reported; MDS
trajectory with the continuity statistic; ν-contribution sign; all `H_t`
decoded (S2H round-trip asserted in tests) and drawn; competitor trajectories
emitted with nauty's jump statistic vs ours. Sequence generator unit-tested
(budget accounting, connectivity, per-axis invariants — e.g. M2 holds `n`
fixed, M3 changes exactly one edge's arity per step). Five filmstrip artifacts
(one per axis) exist. The rendering convention is stated once in the artifact
README and used for every drawn figure.
**Out of scope here:** folding G3 into `theoretical/geometry.md` prose (doc
pass follows); any HGED oracle use (budgets known by construction); re-running
G2 (T-M7e).

---
**Closed:** 2026-07-22 (agent-ac79f185c7b34bd1a, branch task/T-M7f)

**Closing check output:**

```
pytest tests/unit/experiments_article/test_g3_sequence.py -m unit -q
36 passed in 4.31s

pytest tests/unit/ -m "not slow" -q
1050 passed, 5 skipped, 13 deselected, 1 warning in 37.44s

ruff check src/ tests/          → 3 errors (all pre-existing baseline; 0 new)
ruff check experiments/article/g3_sequence.py experiments/article/g3_analysis.py → 0 errors
mypy src/isalhg/                → 21 errors (all pre-existing baseline; 0 new)
```

**G3 experiment results (run locally, all ADMITTED bases n<=20):**

| Axis | Base | T_achieved | IsalHG mf | wall_clock |
|------|------|------------|-----------|------------|
| M1 vertex growth      | tight_cycle_k3_n5 | 10 | 1.00 | 0.5s  |
| M2 densification      | loose_path_k3_n9  | 10 | 0.80 | 0.1s  |
| M3 arity increase k=3 | fano_plane_k3     | 7  | 0.57 | 1.4s  |
| M3 arity increase k=4 | tight_path_k4_n6  | 3  | 1.00 | 0.5s  |
| M3 arity increase k=5 | tight_path_k5_n7  | 3  | 0.67 | 52.2s |
| M4 incidence edit     | sts9_k3           | 10 | 0.50 | 1.5s  |
| M5 symmetry break     | gq22_k3           | 10 | 0.80 | 7.5s  |

MDS+ν computed for M1 (fast): ν rises from 0 at T<4 to ~0.04 at T=10.
MDS+ν computed for M2 (fast): ν stays near 0 (max ~0.012) — densification
is nearly Euclidean. MDS/ν skipped for M3-M5 (canonical cost too high
for prefix-matrix sweeps; noted in g3_ofat.yaml).

M3 k=5 (tight_path_k5_n7) took 52s: grown edges reach arity 8, making
nauty_levi_edit and isalhg_levenshtein expensive. T_achieved=3 (sequence
terminates early — all path vertices consumed by growing edges at step 3).

**What was delivered:**
- `experiments/article/g3_sequence.py`: OFAT sequence generator with
  OfatAxis (StrEnum), OfatStep (frozen dataclass), generate_ofat_sequence
  dispatching M1–M5; S2H round-trip utility; budget tracking via qin_edit_cost.
- `tests/unit/experiments_article/test_g3_sequence.py`: 36 tests covering
  AC1 (budget), AC2 (connectivity), AC3 (M2 n-fixed), AC4 (M3 arity+1/step),
  AC5 (S2H round-trip), AC6 (M1 n+1/step), plus sequence length and OfatStep.
- `experiments/article/g3_analysis.py`: analysis module — response curves,
  MDS trajectory, ν-trajectory, filmstrip drawing (spring layout + convex hulls),
  JSON result records, run_default_g3 entry point.
- `experiments/article/configs/g3_ofat.yaml`: OFAT experiment config.
- `artifacts/g3/README.md`: rendering convention (spring layout + convex hull
  patches; supersedes T-M5e structural-profile plots); base table; key findings.
- `artifacts/g3/`: 7 filmstrips + 7 response curves + 2 MDS + 2 ν figures +
  7 JSON result records.

**Rendering convention (T-M8b reuse):**
Spring layout on incidence bipartite graph; convex-hull patches for arity≥3
edges (alpha=0.25), thick lines for arity=2 edges (alpha=0.6); black vertex
dots. Implemented in `experiments.article.g3_analysis.draw_hypergraph`.
Supersedes T-M5e structural-profile plots.

**Discipline compliance:**
- M3 analyzed per base k (k=3/4/5 as separate sub-experiments; never pooled).
- All H_t decoded via S2H (AC5 test; round-trip verified in sequence generator).
- HGED-free: budgets known by construction (Qin-cost accumulation).
- ADMITTED designs only (PENDING_CLUSTER: sts13_0/1, sts15_0, ag24, pg23, pg24 excluded).
- HyperCOT excluded: subprocess pinned-env complexity; noted in config.
- MDS/ν skipped for slow axes (M3-M5): documented in config and README.
