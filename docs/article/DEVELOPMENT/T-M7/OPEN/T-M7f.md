# T-M7f — G3: controlled single-parameter geometry response + visualization
**Declared:** 2026-07-22 11:56 CEST
**Status:** OPEN
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
