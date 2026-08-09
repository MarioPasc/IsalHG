# F7 — Task metrics under a size control

**Spine position:** Usefulness (A2 clustering, A3 kNN).
**Status:** to build. **Blocked on a corpus decision** — see §2. This figure
cannot be drawn honestly from the current Stratum A corpus alone.

---

## 1. What the figure is for

A2 and A3 are the paper's "does the metric do useful work" evidence. The figure
must let a reader see, at a glance, (i) where each representation lands, (ii)
how far above the trivial floor anyone is, and (iii) whether the ranking
survives a control for the confound the corpus carries.

## 2. The measurement that forces the redesign (2026-08-09)

A distance built from **two integers per hypergraph** — `d_size(H,H') =
|n−n'| + |m−m'|`, no structure whatsoever — was run through the same A2/A3
pipeline as the seven representations, on the same Stratum A corpus, 5 seeds
(`scratchpad/size_confound.py`):

| representation | A2 ARI | A3 AUC@5 | ρ(D, D_size) | ρ(D, D_{|w*_c|}) |
|---|---|---|---|---|
| NetLSD | 0.475 ± 0.040 | 0.932 ± 0.007 | 0.746 | 0.575 |
| **`|Δn| + |Δm|` (size only)** | **0.442 ± 0.040** | **0.932 ± 0.008** | — | — |
| degree-seq L1 | 0.437 ± 0.038 | 0.945 ± 0.008 | 0.850 | 0.777 |
| HPD-JSD | 0.285 ± 0.038 | 0.892 ± 0.012 | 0.063 | 0.033 |
| IsalHG `d_I^⊥` | 0.274 ± 0.028 | 0.915 ± 0.011 | 0.715 | 0.857 |
| HyperCOT | 0.264 ± 0.020 | 0.928 ± 0.011 | −0.029 | 0.008 |
| nauty-Levi edit | 0.178 ± 0.015 | 0.848 ± 0.023 | 0.526 | 0.737 |
| WL histogram | 0.015 ± 0.002 | 0.492 ± 0.002 | 0.160 | 0.332 |

**The two-integer baseline outranks five of the seven representations on ARI
and four of seven on AUC.** It ties NetLSD on AUC and is within noise of
degree-seq on ARI.

The mechanism is in the corpus. The 17 design families span `n ∈ [5,15]`,
`m ∈ [3,15]`, incidence mass 12–45 (CV 0.499), `|w*_c|` 49–276 (CV 0.561), and
they occupy **14 distinct `(n,m)` cells** — so family identity is nearly a
lookup on two integers, and only three collisions
(TightCycle3/TightCycle4 at (5,5), STS7/TightCycle5 at (7,7),
TightCycle4-8/TightCycle5-8 at (8,8)) require any structural discrimination at
all. Three independent measurements agree: `d_I` correlates 0.867 with the
canonical-length gap (`theoretical/geometry.md` §5), MDS PC1 correlates 0.960
with `|w*_c|` and 0.956 with `m` (§4), and the leading representations are
mutually redundant (IsalHG↔degree-seq ρ = 0.799, NetLSD↔degree-seq ρ = 0.707).

Note that neither size axis alone does the work — incidence mass alone gives
ARI 0.101 and edge count alone 0.111. It is the **pair** `(n, m)` that resolves
the families, which is precisely what a degree sequence (length `n`, sum
`Σ deg = Σ|e|`) and a heat trace (whose small-`t` expansion is dominated by
graph order and size) both encode almost directly.

**Consequence.** On this corpus, A2 and A3 do not measure representation
quality. Reporting the current ranking as a representation comparison — in
either direction, whether IsalHG wins or loses — is not defensible, and the
falsifying check is one line of code that any reviewer can run.

## 3. The fix, and why it is the fix

Add a **size-controlled corpus** in which `(n, m, k)` and the degree sequence
are held constant across classes, so the only remaining signal is higher-order
structure. The vendored Steiner catalog
(`datasets/synthetic/sts_catalog.py`, T-M0c) already contains the ideal
instance: **the 80 non-isomorphic STS(15)**, every one with `n = 15`, `m = 35`,
arity 3, and every vertex of degree 7. On that corpus, by construction:

- `d_size ≡ 0` and `d_degseq ≡ 0` for every pair — both baselines collapse to
  a single point and score ARI = 0 exactly, which is the cleanest possible
  demonstration of what "incomplete invariant" means;
- WL is expected to be weak (Steiner systems are a classical hard family for
  colour-refinement);
- IsalHG separates all 80 by Theorem A.

This converts the paper's weakest table into its strongest: a task where the
naive floor is provably zero and completeness is the only way through.

**Feasibility (measured 2026-08-09):** `w*_c` costs 0.00 s at STS(7), 0.08 s at
STS(9), **29.6 s at STS(13)**, and STS(15) had not returned after several
minutes — consistent with the known symmetry-driven blow-up (the manifest's
scalability frontier, and STS(13) already carries a slow-marked pin). **STS(15)
may be out of reach**; the measurement is in progress and its outcome decides
between:

| option | corpus | cost | what it buys |
|---|---|---|---|
| A | 80 × STS(15) | unknown; likely prohibitive | the ideal control, degree-regular |
| B | size-matched sub-corpus of the existing designs, `(n,m)` held fixed | free | only 3 usable pairs — underpowered |
| C | new generator: fixed `(n, m, k)` + fixed degree sequence, non-isomorphic by rejection | one generator + one sweep | controllable size *and* degree; scale set by feasibility |
| D | keep the current corpus, report the size floor as a row, and state the confound | free | honest but concedes A2/A3 measure little |

**Recommended: C, with D as the fallback**, and the size-only row present in
every table regardless of which is chosen.

## 4. Panel specification (assuming C or A lands)

**Panel (a) — size-heterogeneous corpus (the current one).** Grouped bars, ARI
and AUC@5 per representation, 95% BCa CIs over seeds, with a **horizontal
reference line at the `|Δn|+|Δm|` score** and the region below it shaded. The
caption states plainly that most of the spread here is size.

**Panel (b) — size-controlled corpus.** The same bars on the controlled corpus,
where the reference line sits at ARI = 0 by construction. The contrast between
(a) and (b) *is* the scientific content: it separates "recovers the families"
from "recovers the families for the right reason".

**Panel (c) — the confound, quantified.** Scatter of each representation's
ρ(D, D_size) against its A2 ARI on the heterogeneous corpus. A rising trend is
the diagnostic; representations off the trend (HPD, HyperCOT — near-zero size
coupling) are the ones doing structural work.

## 5. Data provenance

- Current corpus: `results/T-M7d/stats/stratum_a_stats.json` (BCa CIs,
  Holm-corrected Wilcoxon) and `results/T-M7d/d_matrix/stratum_a/seed*/`.
- Size-only baseline: recomputed in-figure from the corpus descriptors; to be
  registered as a distance (`size_l1`) alongside `degree_seq_l1` so it flows
  through the same harness and carries the same CIs.
- Controlled corpus: pending the §3 decision.
- Generating code: `experiments/analysis/figures/task_metrics.py`.

## 6. Acceptance check

1. A `|Δn|+|Δm|` row appears in every A2/A3 surface, with CIs from the same
   harness as every other row.
2. No sentence ranks representations on the heterogeneous corpus without the
   size floor visible in the same figure.
3. If option C or A lands, panel (b) exists and the naive baselines score at
   the structural floor there.
4. `COMPETITORS.md` §4's pre-registered interpretation contract is honoured
   verbatim: the outcome is reported, not suppressed, in whichever direction it
   falls.

## 7. Resolution (2026-08-09, T-M4b — this section supersedes §3's "pending")

Option C landed, with the substrate decision itself measured: option A
(STS(15)) failed both feasibility (pristine `w*_c` > 900 s on rigid
instances; 617 s on PG(3,2)) and signal (2-swap families avalanche —
within-family `d_I` ≈ between-family; ARI ≈ 0.03). The adopted corpus is
Stratum C (`../DATA.md` §1): 3 size-controlled cells, 12 swap-planted
families × 6, one degree sequence per cell. Measured through the S=27
harness (`results/T-M4b/stats/`): both naive baselines at ARI −0.000
[−0.001, 0.000] / AUC 0.492 at every cell (check 3 ✓); `size_l1` in every
surface with the same CIs and tests (check 1 ✓); the outcome reported in the
direction it fell — nauty-Levi edit leads (ARI up to 0.614), HPD and NetLSD
follow, IsalHG is significantly above the floor and significantly below the
leaders, WL is tie-degenerate at the floor (check 4 ✓). The figure's panel
(b) is generated from `results/T-M4b/`; the panel-(a) heterogeneous-corpus
numbers are archived under `results/superseded/T-M7d_stratum_a/`. Ledger
record: `../DEVELOPMENT/T-M4/CLOSED/T-M4b.md`; decision record: D-M4b in
`../DEVELOPMENT/DECISIONS.md`.
