# Geometry v5 — the synthesis

*Proposed replacement for `../theoretical/geometry.md`. Status: pending PI.*

> **PI, 2026-08-12.** *"La parte de geometría es muy amplia, y haces bien en
> limitarte a lo que luego haga falta en las aplicaciones. Debes intentar
> sintetizarla un poco, porque se pierde uno leyendo."*

The instruction is not "cut the geometry" — it is "make it readable by keeping
what the applications need." The v3 document already had the right rule
(**no orphan geometry**); it grew large because it accumulated *methodology*
(estimator design, calibration, corpus forensics) alongside *results*. The
synthesis is therefore structural: **results in the main text, methodology in an
appendix, forensics compressed to a paragraph** — and the consumers are
re-pointed from ML pipelines to engineering decisions.

---

## 1. The new consumer table (this replaces the six-invariant table)

**The geometry of the metric space is the geometry of the search space.** That
is the sentence that repairs the v3 program's weakest joint: under v3 the
invariants licensed *method choices in an ML pipeline* (a weak licence, since
the pipelines ran either way); under v5.1 they are *parameters of a search
algorithm* — branching factor, move-operator choice, heuristic power, pruning
licence. Each row below states what a reader **does differently** because of the
number.

| Invariant | Measured | Search-design consumer |
|---|---|---|
| **Ball growth and collapse** — `\|B_r(w)\|` in string space, and the number of distinct isomorphism classes it contains | **not yet measured — new (gate G-B1)** | **The branching factor of C1 and the redundancy of the move operator**: how much duplicate work one expansion level does, and therefore how much the frontier key has to absorb. It is also what makes "enumerate every object within radius `r`" (C2's neighbourhood query) cost-predictable |
| **Local sensitivity + ladder response** | `s(e)` IQR 3–9 tokens on anchored design fixtures vs nauty 20–37; **≈30–50 % of the string per structural edit on unanchored substrates**; 56/56 ladders globally increasing, monotone fraction 0.71 | **Which move operator the search uses.** A structure-space move is incoherent in string space, so the search moves in **string space** and orders by **cost**, never by distance-to-target. The same measurement that bounded v3's classification scores is here a design conclusion — and it is the sharpest argument for testing a semantics-aligned alphabet (`logic_models/encoding.md` §3) |
| **Concentration + hubness** | `N_10` skew 0.92–0.94 (`d_I^⊥`), nauty 0.39–0.58, HPD 0.63–1.11, NetLSD −0.29 to −0.40, WL 2.079 (tie artifact) | **The discriminating power of a distance heuristic** — predicted weak, and reported as the reason C1 has no distance-guided variant. Retained also as the prediction that forecast the kNN outcome on both synthetic and real corpora |
| **Intrinsic dimension `D̂`** | 27.4 [26.9, 28.0] at the smallest cell, censored (≥ 40) at the larger two; NetLSD 3.0–3.5; WL censored *and* tie-degenerate; real HIC data 10–11 | **How much any index or heuristic can compress the space.** Intrinsic dimensionality is the standard predictor of pruning power in metric search (Chávez et al., ACM CSUR 2001). Also the honest reading that a *complete* invariant cannot be low-dimensional: retaining few degrees of freedom is what incompleteness is |
| **Non-Euclidean mass `ν`** (Schoenberg) | `ν = 0.137 / 0.061 / 0.011` across the Stratum C cells; the only non-Euclidean rows are the two canonical-string metrics | **Which pruning is licensed.** `d_I` is a metric but not Euclidean ⇒ triangle-inequality pruning and metric-space indexing apply; Euclidean methods over embedded coordinates do not without distortion. Also why PAM, not centroids, is the correct estimator wherever clustering appears |

**Ball growth is the one genuinely new measurement**, and it is cheap: enumerate
`B_r(w)` for small `r` on a sample of corpus strings, decode each (P1), canonize,
count distinct classes. It closes the loop between the metric geometry and the
search cost in a way no v3 invariant did, and it belongs to gate G-B1.

**Two invariants demoted from the v3 six.** *Distortion* (stress, Shepard, CV
error) survives as a qualifier on the one MDS figure, not as an invariant with a
consumer. *The intrinsic-dimension estimation procedure* is methodology, not a
result.

## 2. What each invariant licenses, stated as sentences the paper can use

- Because the ball around a canonical string collapses onto far fewer
  isomorphism classes than it contains words, the move operator is redundant by
  a measurable factor, and the frontier key is what pays for that redundancy —
  which is exactly why the key is a *pluggable component* of C1 and why a
  faster one (nauty) is welcome inside our own loop.
- Because a single structural edit costs ≈30–50 % of the string on unanchored
  substrates, distance-to-target is not a search heuristic; the search moves in
  string space and orders by cost, and the metric is used for *neighbourhoods,
  navigation and diffing*, not for guidance.
- Because hubness is moderate for `d_I` and severe for WL, nearest-neighbour
  workloads behave in the order the profile predicts — measured twice,
  synthetic and real.
- Because `D̂` is high (27+ where measurable, censored above), no index or
  heuristic will compress this space much; that is reported, not worked around.
- Because `ν > 0` at every cell, no isometric Euclidean embedding exists;
  triangle-inequality pruning is licensed and Euclidean methods are not.

The second bullet is the honest reconciliation of the geometry with the v5.1
thesis and should appear near-verbatim in the paper: **the avalanche is a fact
about the direction structure → string, and the search runs in the direction
string → structure.**

## 3. Structure of the section in the paper

Target: **two to three pages**, in this order.

1. *One paragraph* — the object: `w*_c` maps iso-classes into `(Σ_HG*, d_Lev)`;
   Theorem A makes it injective; Corollary A makes `d_I` a metric.
2. *The measurement table* — one table, four invariants, per representation,
   with BCa CIs, on the corpora the applications use.
3. *Four short paragraphs* — one per invariant, each ending in its engineering
   consequence (the sentences of §2).
4. *One figure* — the similarity map with its stress, captioned as a
   visualization and not as a result.
5. *One paragraph* — the theory bracket: Bourgain's `O(log N)` upper and
   Khot–Naor's string-edit lower, cited, not restated.

## 4. What moves to the appendix / supplement

- The intrinsic-dimension estimator design: leave-out-points CV with Gower
  out-of-sample placement, why entry-masking is in-sample and rides to the cap,
  Horn parallel analysis as the conservative lower bracket, Mardia ratios, the
  negative-eigenvalue floor.
- The estimator calibration (exact recovery of ranks 2–25; noise inflates rather
  than deflates; N-convergence and subsampling).
- The full distortion analysis, the shared-`D = 2` artifact (10.7× stress ratio
  against NetLSD), and the Shepard panels.
- The budget-Shepard faithfulness check (`ρ(t, d_I^⊥) = 0.39` over 56 ladders).
- The per-regime sensitivity histograms (17 regimes, 1700 edits) — the summary
  IQRs stay in the main text, the histograms go to the supplement.

## 5. What compresses to one paragraph

The corpus forensics. The v3 document spends roughly a page and a half on: the
PC1–`|w*_c|` correlation of 0.960 on the superseded corpus, the length-difference
floor ρ = 0.867, the `d_size` baseline reaching ARI 0.442 / AUC 0.932, the mutual
redundancy of the leading representations, and the STS-substrate autopsy
(pristine `w*_c` > 900 s on rigid instances; 2-swap families avalanche to
ARI ≈ 0.03). All of it is good work and it is what justifies the Stratum C
design. In the paper it becomes:

> The first-generation corpus was separable on size alone — a distance built from
> `|Δn| + |Δm|` reached ARI 0.442 and AUC 0.932 on it — so its task standings
> measured how directly each representation encodes size. The replacement corpus
> fixes `(n, m, k)` and the exact degree sequence across classes, which drives
> both naive baselines to exactly zero on every pair by construction; Steiner
> systems were measured and rejected as a substrate on both cost and signal
> grounds. Details in Appendix X.

## 6. What is cut

- δ-hyperbolicity (already cut at D-ART2; stays cut).
- The MDS regime-decision apparatus (classical vs SMACOF selection rules) —
  one sentence, not a subsection.
- The competitor `D̂` head-to-head as a standalone axis; it collapses into the
  measurement table.

## 7. New geometry work, if any

Only one candidate, and it is small: **the intrinsic dimensionality statistic of
the metric-search literature** — `ρ = μ²/(2σ²)` computed from the pairwise
distance histogram (Chávez et al., 2001) — reported alongside `D̂`. It costs one
line of code, it is the number that community reads, and it makes the
index-applicability argument in the venue's own vocabulary. Everything else in
this document is re-use of measurements already frozen.
