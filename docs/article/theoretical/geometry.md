# The geometry of the IsalHG hypergraph metric space

**Status:** ACTIVE. **The article's central theoretical
object**: the characterization the paper leads with and the licence system the
applications cite. The companion `stability.md` holds the foundation (§1) and
the HGED-relation analysis the closing discussion compresses (§2–4);
`README.md` fixes the logical spine. Non-normative where it and the proof
volume disagree; the proofs win.

Notation follows `stability.md`: `H` connected labelled hypergraph, `w*_c(H)` the
frozen tie-complete canonical string, `d_I(H,H') := d_Lev(w*_c(H), w*_c(H'))`,
`n=|V|`, `m=|E|`, `k` max arity, `Δ` max degree.

---

## 1. The object, the rule, and the claim structure

`w*_c` maps each isomorphism class of connected hypergraph to a point of the
discrete metric space `(Σ_HG*, d_Lev)`. Theorem A (completeness) makes the map
**injective on isomorphism classes**, so `d_I` is a genuine metric (Corollary A,
`stability.md` §1). We establish this foundation for hypergraphs from first
principles: the graph-case sibling (IsalGraph) is under review and not citable
as published work, so the paper stands alone and re-derives the completeness →
metric chain in the hypergraph setting — *non-trivially*, since hypergraph
completeness required the tie-complete encoder, the greedy encoder being
provably incomplete (a pinned counterexample). On that foundation the article's
thesis is **characterize → exploit**: measure the induced geometry, then let
each measured property license an application.

**The no-orphan-geometry rule.** Every invariant this document defines is
measured *because* a specific downstream consumer needs it — an application
licence or a competitor contrast. An invariant with no consumer is cut. This is
the discipline that keeps the geometric exploration motivated rather than
decorative, and it is the answer to the overextension risk: the geometry
program is exactly as large as the applications require, no larger.

The claim structure is deliberately *not* "we prove a clean bound." It is: the
embedding lands hypergraphs in a measurable geometry — six invariants, §§2–7 —
whose usefulness is demonstrated on standard pipelines against competitors, and
whose relation to structural edit distance is honestly characterized in the
closing discussion (envelope + impossibility + mechanisms; `stability.md`),
not claimed as a bound.

## 2. Curvature / non-Euclideanness (Schoenberg)

Classical (Torgerson–Gower) MDS double-centres the squared-distance matrix
`D^(2)` into a Gram matrix `B = -½ J D^(2) J`. The metric is exactly Euclidean
iff `B` is positive semidefinite (Schoenberg 1938). Edit metrics are
**generically non-Euclidean**: `B` carries negative eigenvalues, so `d_I` does
not embed isometrically into any `R^D`.

- **Reported invariant:** the negative-eigenvalue mass ratio
  `ν := Σ_{λ<0}|λ| / Σ_i |λ_i| ∈ [0,1)` per corpus, plus the PSD status.
- **Consumers:** (a) the MDS regime decision in A1 (`ν ≈ 0` ⇒ classical MDS
  near-isometric; `ν` large ⇒ approximate regime, SMACOF, residual owned);
  (b) the *method licence* for A2 — k-medoids/PAM operate on the metric
  directly and need no Euclidean coordinates, which is why they are chosen
  over centroid methods.
- This is a *characterization*, not a defect: many workhorse metrics (edit,
  shortest-path, Wasserstein-on-non-Euclidean-ground) are non-Euclidean and
  still drive MDS/clustering. The paper reports `ν`, it does not apologize for
  it.

## 3. Intrinsic dimension — the estimation procedure

The estimated intrinsic dimension `D̂` of `(·, d_I)` is a **standalone
descriptor**: "hypergraph space under `d_I` has intrinsic dimension `D̂`."
Choosing `D̂` is not a free parameter but a modelling decision, and the correct
decision depends on whether `B` is positive semidefinite.

**The exact case does not apply here.** Schoenberg's criterion gives a unique,
non-arbitrary answer *only* when `B` is PSD: then the minimal isometric
dimension is `D = rank(B) = #{λ > 0}`. The three metric axioms do not guarantee
this, and `d_I` is one of the metrics they fail for — its `B` is indefinite
(`ν > 0`, §2), so no exact Euclidean embedding exists at any `D`. Dimension
selection is therefore an **approximation problem**, and the negative
eigenvalues become the instrument rather than the obstruction.

**Primary estimator — cross-validation on held-out dissimilarities.** This is
the most defensible general-purpose choice and it makes no PSD assumption. The
one subtlety that must be honoured: "hold out a subset of pairs, fit on the
rest, predict the held-out" only measures generalization if the held-out pairs
are genuinely *out of sample*. Masking matrix entries while still embedding the
full matrix is secretly in-sample — its reconstruction error falls
monotonically in `D` and drives the estimate to the search ceiling. The correct
realization is **leave-out-points** with an out-of-sample placement: embed the
training points by classical MDS, position each held-out point from its
distances to the training set via the Gower (1968) landmark formula, and score
the predicted held-out↔train distances. This yields a genuine minimum.

**Corroborating estimator — Horn parallel analysis.** Independently of CV, we
build a null spectrum by permuting the off-diagonal dissimilarities, symmetrizing,
double-centring and eigendecomposing over many permutations, and retain the
dimensions whose observed eigenvalue exceeds the 95th-percentile null at their
rank (Horn 1965, adapted to a dissimilarity matrix). On a PSD input it recovers
the true rank (a rank-3 Euclidean cloud returns 3); on a non-PSD input it is
deliberately **conservative** — the permutation null retains large positive
eigenvalues, so only the clearly-dominant observed dimensions survive, and the
95th-percentile threshold carries a nominal `≈0.05·N` false-retention floor.
Horn therefore reports the lower end of a bracket, CV the reconstruction-optimal
upper end.

**Supporting:** Mardia `P^(1)`, `P^(2)` goodness-of-fit ratios (the squared
version preferred, as it downweights the small mixed-sign eigenvalues); the
negative-eigenvalue floor `λ_D ≫ |λ_min|`. An alternative notion — a *distortion
budget* rather than a spectral one — is available if isometry is not required
(Bourgain's `O(log N)` embedding and Johnson–Lindenstrauss reduction, §4); the
paper reports the spectral `D̂` and cites the distortion bracket rather than
selecting `D` from it.

**Measured — `D̂` is corpus-dependent.** The current measurement uses the
size-controlled primary corpus (Stratum C, `../DATA.md` §1): three
`(n, m)` cells, 12 swap-planted families × 6 members = 72 items per cell, one
exact degree sequence per cell; metric `d_I^⊥`, trivial vocabulary; 27
independent corpus seeds, 95% BCa CIs. The real-data cross-check uses two HIC
genre corpora (metric `d_I^Σ`; non-trivial IMDB vocabulary — see the Remark
in `stability.md` §1), reported as a censored secondary exhibit
(`../DATA.md` §2):

| corpus | metric | `N` | `ν` [95% CI] | `D̂` (CV) [95% CI] | `D̂` (Horn) |
|---|---|---|---|---|---|
| Stratum C (9,12) | `d_I^⊥` | 72 | 0.137 [0.136, 0.140] | 27.4 [26.9, 28.0] | — |
| Stratum C (12,20) | `d_I^⊥` | 72 | 0.061 [0.060, 0.062] | ≥40 (censored) | — |
| Stratum C (15,35) | `d_I^⊥` | 72 | 0.011 [0.010, 0.011] | ≥40 (censored) | — |
| HIC IMDB-Wri-Genre-M | `d_I^Σ` | 266 | 0.160 | 10 | 1 |
| HIC IMDB-Wri-Genre | `d_I^Σ` | 833 | 0.200 | 11 | 1 |

`d_I^⊥` is **genuinely non-Euclidean at every cell**, and both invariants move
systematically with cell size: the non-Euclidean mass falls
(0.137 → 0.061 → 0.011) while the CV dimension leaves the measurable range —
well-determined at 27.4 [26.9, 28.0] on the smallest cell, censored at the
search cap (40) on the two larger ones, where the CV error falls
monotonically without turning. The censoring is informative: at fixed size
and degrees the pairwise `d_I^⊥` distribution concentrates (the avalanche
moves every edited object a near-constant fraction of the string length, §6),
and a concentrated metric has no low-dimensional structure for the estimator
to find. **Real genre hypergraphs are markedly lower-dimensional**
(`D̂ ≈ 10–11`, Horn ≈ 1) — a substantive finding, reported as a
censored-subset measurement. The Stratum C rows use the structural member
`d_I^⊥`; the HIC rows use the label-aware member `d_I^Σ`. These are members
of different families (the Remark in `stability.md` §1) and are read as two
objects rather than one continuous series. Estimates are reported as
bracketed ranges (BCa 95% CI on the CV optimum), never a bare number, and a
censored estimate is reported as censored.

- **Consumers:** (a) the MDS target dimension in A1; (b) a competitor axis
  independent of any oracle — `D̂` per representation is a head-to-head result
  (the Euclidean vector competitors WL and HPD do not concentrate at all —
  their CV error rides to the search cap, so their `D̂` is reported as censored,
  itself a contrast).

**`D̂` is a descriptor, not a quality score — and a complete invariant cannot be
low-dimensional.** The intuitive reading, that a smaller `D̂` shows a
representation captures structure more compactly, points the wrong way here and
is not adopted. Intrinsic dimension counts the structural degrees of freedom a
representation retains, and retaining few is what incompleteness *is*: on the
size-controlled cells NetLSD sits at `D̂ ≈ 3.0–3.5` and is incomplete, the
naive baselines' identically-zero matrices degenerate to `D̂ = 1`, and the WL
histogram is censored *and* tie-degenerate (hubness 2.079, chance-level kNN).
Read in that order, `D̂` ranks the representations by information retained,
and the string metrics' high dimensions (IsalHG 27.4 at the smallest cell;
nauty-Levi 38.6 [37.5, 39.3] there) are the signature of separating every
isomorphism class. The genuine costs of a high `D̂` are two, both measured: a
two-dimensional map is lossy (§4), and high intrinsic dimension is the
standard precondition for hubness and concentration. On the size-controlled
corpus the second cost *does* materialise for `d_I^⊥` at the larger cells —
the censored `D̂` and the near-constant single-edit response (§6) are two
faces of the same concentration, and A2/A3 pay for it — which is exactly what
a descriptor is for: it forecast the task outcome before the classifier ran.

**The estimator is calibrated.** On noiseless Euclidean clouds at the corpus
sizes used here the cross-validated estimator recovers true ranks 2–25
exactly, and adding 10% distance noise inflates rather than deflates the
estimate, so CV readings are if anything upper readings; the leave-out-points
protocol with Gower out-of-sample placement is required (entry-masking is
in-sample and rides to the cap). The N-convergence and subsampling analyses
of the superseded design corpus (plateau at its `D̂` well before full size)
are retained in `results/superseded/` as estimator validation; they are
statements about the estimator, and the calibration transfers, but their
corpus-specific values are no longer cited.

**Structural-faithfulness check (HGED-free; metric `d_I^⊥`).** Because the
intrinsic dimension and the embedding are only as meaningful as the distances
they preserve, we verify that the `d_I^⊥`-MDS map tracks *true* structural
distance without the HGED oracle: along perturbation ladders built from the
design fixtures, the accumulated Qin edit budget `t` is known by construction,
and `d_I^⊥` increases with it — Spearman `ρ(t, d_I^⊥) = 0.39` (56 ladders,
560 steps; 7 design fixtures × 2 seeds × 4 ladders each; p < 10⁻²⁰). The
budget-coloured Shepard panel renders this. It is a faithfulness statement about
known edits, not an HGED-proxy claim; the moderate ρ reflects that equal-budget
edits on distinct design families produce unequal `d_I` increments, as expected
from the varying structural complexity of the designs.

## 4. Embeddability and distortion

Even when non-Euclidean, the geometry is not wild — it is bracketed on both
sides:

- **Upper (existence):** Bourgain (1985) — any `N`-point metric embeds into
  `L2` with `O(log N)` distortion. MDS is therefore justified with a worst-case
  distortion guarantee; JL gives cheap approximate dimension reduction when
  isometry is not required.
- **Lower (obstruction):** Khot–Naor (2006) — string-edit metrics require
  `(log d)^{1/2−o(1)}` `L1` distortion, so a non-trivial residual is expected
  and must be reported, not hidden.
- **Reported invariant:** measured distortion — Kruskal stress-1 at matched `D`,
  the Shepard diagram (`d_I` vs embedded distance), and the CV reconstruction
  error of §3.
- **Consumer:** A1 — every similarity map ships with its distortion figures;
  competitors' maps are compared at matched `D`.

**Measured — residual distortion on the size-controlled corpus (3 cells × 72
items, 27 seeds).** At its (possibly censored) `D̂`, `d_I^⊥`'s residual
distortion stays low across the cells: Kruskal stress-1 = 0.055
[0.054, 0.057] at (9,12), 0.021 [0.020, 0.021] at (12,20), 0.059
[0.057, 0.060] at (15,35); nauty-Levi edit is comparable (0.019–0.043).
Distortion at a display dimension `D = 2` is not the distortion at `D̂`, and
the gap is representation-dependent, so a shared-`D = 2` panel compares
compressibility rather than fidelity; similarity maps are therefore reported
with their own stress-at-display-dimension, and the representation comparison
is carried by the CV-error-versus-`D` curves of §3 rather than by a common
two-dimensional projection. (The shared-`D = 2` panel measured on the
superseded design corpus, which quantified that artifact — a 10.7× stress
ratio between `d_I^⊥` and NetLSD at `D = 2` against comparable fidelity at
matched `D̂` — is archived with that corpus in `results/superseded/`.)

**What the first axis measured — and how the corpus silenced it.** On the
superseded design corpus the leading MDS coordinate of `d_I^⊥` was almost
exactly canonical-string length: `|r(PC1, |w*_c|)| = 0.960` (Spearman 0.948),
equally `|r(PC1, m)| = 0.956`, with length confined to the first axis. That
corpus's families differed widely in incidence mass (mean `|w*_c| = 16.1`
tokens, CV 0.64), so its maps displayed a size gradient before they displayed
structure — one of the three measurements that motivated the size-controlled
redesign (§5). On Stratum C the axis is silenced by construction: incidence
mass is constant within a cell and `|w*_c|` varies by only a few percent
(e.g. 562–642 characters at (15,35)), so no size axis exists for PC1 to
find.

## 5. Concentration, spread, and hubness

The distribution of pairwise `d_I` (median, IQR, diameter, its scaling with
`|w*_c|`) determines whether the metric **concentrates** — a concentrated metric
weakens kNN (all points look equidistant, the curse of dimensionality).

- **Reported invariants:** the pairwise-distance histogram per corpus; the
  diameter-to-median ratio; the relation `d_I` vs `||w*_c(H)|-|w*_c(H')||`
  (the length-difference floor); and the **hubness profile** — the skewness of
  the `k`-occurrence distribution `N_k(x)` (how often `x` appears among other
  points' `k` nearest neighbours), the standard diagnostic for
  nearest-neighbour reliability in high-dimensional metric data (Radovanović
  et al. 2010).
- **Consumer:** A3 — the kNN application's precondition report. High hubness or
  strong concentration predict degraded kNN; measuring them first makes the
  kNN result (good or bad) interpretable instead of anecdotal.

**Measured — the length-difference floor (superseded design corpus).**
Levenshtein distance satisfies `d_Lev(a,b) ≥ ||a|−|b||`, so some coupling
between `d_I^⊥` and the length gap is mandatory for any string metric. On the
superseded design corpus its magnitude was large: Spearman
`ρ(d_I^⊥, ||w*_c(H)|−|w*_c(H')||) = 0.867` over all 3,570 pairs per seed —
most of the ordering `d_I^⊥` imposed there was ordering by size difference,
the pairwise counterpart of the PC1 result in §4.

**The size contribution was not merely substantial — on that corpus it was
sufficient, and this is what forced the corpus redesign.** A distance built
from two integers per hypergraph, `d_size(H,H') = |n−n'| + |m−m'|`, carrying
no structural information whatsoever, scored ARI 0.442 [±0.040] on the A2
clustering task and AUC-OvR 0.932 [±0.008] on A3 — outranking five of the
seven measured representations on the first and four of seven on the second,
because the seventeen design families occupy only fourteen distinct `(n,m)`
cells. Neither size axis alone achieves this (incidence mass alone: ARI
0.101; edge count alone: 0.111); the pair resolves the families. Three
measurements agree on the mechanism: the 0.867 length coupling, the 0.960
PC1–`|w*_c|` correlation of §4, and the mutual redundancy of the then-leading
representations (`d_I^⊥` against degree-sequence L1, Spearman 0.799; NetLSD
against degree-sequence L1, 0.707) are three views of a corpus whose class
structure is recoverable from size. Those task standings are withdrawn and
archived (`results/superseded/`).

**The resolution is the size-controlled corpus, with the substrate choice
itself measured.** The natural-looking substrate — Steiner triple systems of
one order, e.g. the eighty STS(15) at `n = 15`, `m = 35`, 3-uniform,
7-regular — fails on both axes it was meant to win: pristine `w*_c` cost is
driven by the Steiner pair-coverage tie structure, not by `|Aut|` (617 s on
PG(3,2), the most symmetric of the eighty; > 900 s on every rigid or
median-symmetry instance probed, and > 900 s on a rigid STS(19)), and near
the Steiner manifold the canonical form is maximally unstable — a two-swap
perturbation moves `d_I` as far as switching to a different Steiner system,
so STS-seeded families carry no recoverable class structure. The adopted
corpus (Stratum C, `../DATA.md` §1) instead fixes `(n, m, k)` and an
irregular degree sequence per cell and plants families by degree-preserving
incidence swaps. On it both naive baselines are identically zero on every
pair — measured through the full harness at ARI −0.000 [−0.001, 0.000] and
AUC 0.492 at all three cells — and within a cell `|w*_c|` varies by only a
few percent, so the length floor of this section has no room to order
anything. A2 and A3 now carry comparative weight, and what they show is
reported in `../empirical/applications.md`: the planted structure is
recoverable (nauty-Levi edit reaches ARI 0.614 [0.571, 0.657] at the largest
cell), and `d_I^⊥` recovers only a small, statistically real part of it —
the concentration measured in §3 and the single-edit response of §6 are the
mechanism, and the closing discussion owns it.

## 6. Local sensitivity and ladder response

The two *dynamic* invariants: how the embedding responds to controlled
structural perturbation. Both are HGED-free — the perturbation budget is known
because we apply the edits (Qin-cost accounting on the generator side).

- **Local sensitivity profile:** the histogram of `s(e) = d_I(H, H⊕e)` over
  single structural edits `e` (all edit types), per corpus and on the design
  fixtures. The profile's shape is the *local roughness* of the embedding:
  a compact unimodal profile means small structural edits move the point a
  short string distance; heavy tails locate the avalanche regime (near-symmetric
  inputs with incoherent ties — `stability.md` §3 supplies the mechanism
  vocabulary).
- **Ladder response:** `d_I(H, H_t)` vs the known accumulated edit budget `t`
  along perturbation ladders `H = H_0 → H_1 → ⋯`. Monotone, near-linear
  response at corpus scale is the smoothness evidence that neighbourhood
  methods (A2/A3) implicitly rely on.
- **Consumers:** (a) the **contrast baseline**: the same `s(e)` measurement on
  the nauty-Levi canonical string shows avalanche-everywhere — the claim
  "canonical labelling yields no navigable geometry" becomes a measured figure,
  not an assertion (`COMPETITORS.md` §3); (b) A4's scoring: path-length
  monotonicity vs `t` is the ladder response read along recovered paths;
  (c) the discussion's mechanism prose (drift/avalanche) points at these
  measured profiles instead of hypothetical worst cases.

**Measured profile.** Seventeen regimes covering the full 17-family design
corpus (STS7, STS9, GQ(2,2), loose/tight path families, loose/tight cycle
families; arities 3, 4, 5; each regime 100 connectivity-preserving single Qin
edits × 2 seeds = 1700 edits total). IQR of `s(e)` (IsalHG): Q1 = 3 tokens,
median = 5, Q3 = 9 — the sensitivity profile is compact and near-unimodal
across the tested configurations. The three-regime prediction in `stability.md`
§4.2 is confirmed for 16 of 17 regimes and **falsified** for one (tight\_path
arity-4, heavy_tail_frac = 0.210 against a unimodal prediction);
`stability.md` §4.2 records the candidate explanation (incoherent ties in
arity-4 tight-path families at the measured sizes). GQ(2,2) is now
**confirmed** as the predicted heavy-tailed regime (heavy_tail_frac = 0.230,
prediction = heavy-tailed, outcome = confirmed) — in agreement with the
theoretical analysis. Nauty-Levi contrast confirmed: IQR_nauty ranges Q1 = 20
to Q3 = 37 tokens across all regimes (overall 4–8× wider than IsalHG),
rendering the per-regime and per-fixture contrast figures. **Ladder response**
(7 design fixtures × 2 seeds × 4 ladders = 56 ladders, 560 steps): mean
monotone fraction per ladder = 0.71 (local one-step regressions occur within
ladder variance); mean `d_I^⊥` increment per Qin budget step: Q1 = 6,
median = 12, Q3 = 18 tokens. All 56 ladders are globally increasing
(cumulative `d_I^⊥` increases from start to end).

**Scope of the profile — absolute versus relative response (measured at the
corpus redesign).** The compact absolute profile above is a property of the
anchored design fixtures, whose short strings and heterogeneous local
structure localize an edit. On random fixed-degree substrates — the
size-controlled corpus's regime — a single edit (incidence swap or Qin op;
the two are indistinguishable in response) moves `d_I^⊥` by ≈30–50 % of the
string at every cell probed from (9,12) to (15,35), and in relative terms
even the design-fixture medians sit near 30 % of their short strings. There
is no measured regime in which the single-edit response is a small *fraction*
of the string: this is the avalanche/drift of the closing discussion measured
directly, it is why edit-proximity class structure is largely invisible to
`d_I^⊥` on the size-controlled tasks, and it bounds what "navigable" may
claim — decodable interpolation (A4's ambient decodability) survives it;
small-perturbation task geometry does not. The nauty contrast, conversely, is
a statement about these fixtures' absolute token counts, not a task
prediction: on the size-controlled corpus the nauty-Levi edit distance is the
strongest structure recoverer (`../empirical/applications.md`), its
adjacency-serialized canonical form localizing the same edits that the
instruction string's positional coupling amplifies.

## 7. Mapping to experiments

| Geometric invariant | Where measured | Consumer |
|---|---|---|
| Non-Euclidean mass `ν`, PSD status | classical-MDS Gram spectrum | A1 regime; A2 method licence |
| Intrinsic dimension `D̂` | CV-MDS | A1 dimension; competitor axis |
| Distortion (stress, Shepard, CV error) | MDS at matched `D` | A1; competitor maps at matched `D` |
| Concentration + hubness | pairwise-distance profile, `N_k` skewness | A3 precondition |
| Local sensitivity `s(e)` | single-edit histograms | contrast vs nauty; discussion mechanisms |
| Ladder response | `d_I` vs budget `t` | smoothness evidence; A4 scoring |

The measurement code (Gram spectrum, `ν`, distortion, hubness, sensitivity
harness) lands in `metric_space/metrics/`; its implementation is tracked in
`DEVELOPMENT/`. This document is the theory.

## 8. Relationship to the other theory documents

- **`stability.md` §1 — Theorem A (completeness):** *why it is a metric.* The
  foundation this document stands on; the paper's formal core.
- **`geometry.md` (here) — the intrinsic geometry:** *what shape the metric
  space has, and which application each measurement licenses.*
- **`stability.md` §2–4 — the HGED-relation analysis:** *what the closing
  discussion may honestly say about `d_I` vs HGED* (envelope, impossibility,
  drift/avalanche mechanisms). Analysis record; only the compressed PROPOSAL §5
  subset reaches the paper.

## 9. References (beyond the project canon)

- I.J. Schoenberg. *Metric spaces and positive definite functions.* Trans. AMS
  44(3), 1938. doi:10.2307/1989894
- J. Bourgain. *On Lipschitz embedding of finite metric spaces in Hilbert
  space.* Israel J. Math. 52, 1985. doi:10.1007/BF02776078
- S. Khot, A. Naor. *Nonembeddability theorems via Fourier analysis.* Math. Ann.
  334, 2006. doi:10.1007/s00208-005-0745-0
- W.S. Torgerson. *Multidimensional scaling: I. Theory and method.*
  Psychometrika 17, 1952. doi:10.1007/BF02288916
- K.V. Mardia. *Some properties of classical multi-dimensional scaling.* Comm.
  Stat. Theory Methods 7(13), 1978. doi:10.1080/03610927808827707
- M. Radovanović, A. Nanopoulos, M. Ivanović. *Hubs in Space: Popular Nearest
  Neighbors in High-Dimensional Data.* JMLR 11, 2010.
  (jmlr.org/papers/v11/radovanovic10a.html)
