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

## 3. Intrinsic dimension

The estimated intrinsic dimension `D̂` of `(·, d_I)` is a **standalone
descriptor**: "hypergraph space under `d_I` has intrinsic dimension `D̂`."

- **Primary estimator (PI note, PROPOSAL v2 §5, retained):** cross-validation
  on held-out dissimilarities — hold out a random subset of the `C(N,2)` pairs,
  fit MDS on the rest, pick `D̂` minimizing out-of-sample reconstruction error.
  Robust to the non-Euclidean residual (does not assume PSD `B`).
- **Supporting:** Mardia `P^(1)`, `P^(2)` goodness-of-fit ratios; the
  negative-eigenvalue floor `λ_D ≫ |λ_min|`; parallel analysis.
- **Consumers:** (a) the MDS target dimension in A1; (b) a competitor axis
  independent of any oracle — a *lower faithful* `D̂` than a competitor
  representation's argues `d_I` captures hypergraph structure more compactly;
  `D̂` per representation is a head-to-head result.

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

**Measured profile.** Seven regimes: sparse/medium/dense random corpora and
four design fixtures (Fano, STS(9), cyclic C13 orbit, GQ(2,2)); connectivity-
preserving single Qin edits at `max_arity = 3`. IQR of `s(e)` (IsalHG) ranges
2.0–8.0 tokens, heavy_tail_frac = 0.000 throughout — the sensitivity profile
is compact and near-unimodal across every tested configuration. The three-regime
prediction in `stability.md` §4.2 is confirmed for the random corpora and the
two coherent-tie designs (Fano, STS(9)), and **falsified** for the two
incoherent-tie designs (cyclic C13, GQ(2,2)), which show compact profiles under
single arity-3 edits rather than the predicted heavy tail; `stability.md` §4.2
records the measured numbers and the candidate explanations. Nauty-Levi contrast
confirmed: IQR_nauty = 10.0–20.0 across all regimes (ratio 1.25–9.5× ours),
rendering the per-regime and per-fixture contrast figures. **Ladder response**
(six corpora, small/medium/large base size, two seeds each): ≈80% of per-ladder
steps are monotone; mean `d_I` increment per Qin budget step grows from 3.2
(n = 5 base) to 11.7 (n = 12 base); all six ladders globally increasing, with
local one-step regressions within ladder variance.

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
