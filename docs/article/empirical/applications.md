# The body — geometry measurement + applications

**Status:** ACTIVE. The paper's empirical body:
**A1 (MDS)** is dual-purpose — it measures the geometry
(`../theoretical/geometry.md`: `D̂`, non-Euclidean `ν`, distortion) and is the
flagship similarity map — the **G-profiles** measure the remaining invariants
(concentration + hubness; sensitivity + ladder), and **A2–A4** demonstrate
usefulness, each licensed by a measured invariant. Everything here is
HGED-free and scores on task metrics, so it runs at real scale; the closing
discussion (`correlation.md`) is evidence, not a prerequisite. Each application
runs on the pairwise matrix `D_I = {d_I(H_i,H_j)}` (and, for competitors, on
their `D_rep`). **None of these exist in the sibling papers** — MDS,
clustering, kNN are IsalGraph's "future work"; the geometric characterization
exists nowhere in the family. The pipeline (pairwise distance → MDS →
k-medoids → kNN/dendrogram) is not novel *per se* — it ports the graph
precedent of Neuhaus & Bunke (2007) and Bunke & Riesen (2008)
(`../RELATED_WORK.md`) to hypergraphs under `d_I`; the novelty is the
substrate (a complete-invariant string metric) plus the measured geometric
licences behind each pipeline choice.

**No HGED here — the scale decision.** These measurements validate on *task*
metrics (ARI vs planted labels, accuracy/F1/AUC, stress) and on known
perturbation budgets, **never** on the HGED oracle. Their scale is gated only by
`w*_c` (and competitor) wall-clock. The primary corpus is the planted-family
synthetic family (`../DATA.md` §1), where membership is ground truth. Real
hypergraph data enters as a **censored secondary exhibit**: on the HIC IMDB
genre atlas (`../DATA.md` §2) `w*_c` is not computable in acceptable time across
the full corpus — the canonical search explodes on high-arity, near-symmetric
instances — so the real-data measurements are reported on the subset with edge
arity ≤ 10 whose `w*_c` completes within a fixed per-instance budget, with the
per-class censoring reported alongside. Application claims are therefore
synthetic-scale claims, cross-checked on real data where `w*_c` is computable.
Competitors run the same pipeline off their own `D_rep`.

---

## Usefulness framing and the capability matrix

The section's organizing claim is not that `d_I` yields the best task-metric
scores — on A2 (clustering) the naive degree-sequence baseline and NetLSD both
lead IsalHG significantly (p_Holm < 10⁻⁷, r = 1.09 in each case), and on A3
(kNN) they lead again (degree-seq p_Holm = 2.0 × 10⁻⁶, NetLSD p_Holm = 1.3 ×
10⁻³); HPD-JSD does not differ significantly from IsalHG on either task (A2
p_Holm = 0.36, A3 p_Holm = 1.0). The design families in the primary corpus
separate cleanly on degree structure alone, so the degree-sequence baseline
captures the dominant discriminative signal on these tasks, and no degree-free
representation is expected to dominate it. Usefulness rests on three axes
jointly:

1. **Licensed.** Each application is preceded by a measured geometric invariant
   that justifies the method choice (the no-orphan-geometry rule;
   `../theoretical/geometry.md`). No application runs speculatively: A1 is
   licensed by the distortion brackets; A2 by `ν` (non-Euclidean mass makes
   medoids the correct estimator) and the G2 ladder response; A3 by the G1
   hubness profile; A4 by the G2 local sensitivity profile and the closed
   alphabet.

2. **Competitive.** On pure task metrics IsalHG places behind degree-seq and
   NetLSD on A2 and A3 (both differences Holm-significant). The naive
   degree-sequence baseline (`Deg-seq L1`, `../COMPETITORS.md` §4) leads the
   A2/A3 ranking: where degree structure alone discriminates the design families,
   no higher-order representation is expected to dominate it, and none does. HPD
   does not differ significantly from IsalHG on either task. Relative standings
   are reported with 95% bootstrap confidence intervals and one-sided Wilcoxon
   signed-rank tests, Holm-corrected across the (representations × metrics)
   family; no representation is declared dominant where the corrected p exceeds
   0.05.

3. **Uniquely capable.** The **capability matrix** (Fig. CAP; rendered by
   `experiments/article/analysis/figures/capability_matrix.py`; place adjacent
   to the A4 decoded-intermediates figure) expresses what each representation
   *cannot* do. IsalHG is the only representation that is simultaneously a
   **complete invariant**, **decodable** (S2H inverts every string in the
   closed alphabet to an actual hypergraph), and **geometrically navigable**
   (measured single-edit sensitivity IQR 3–9 tokens, median 5; 1700 edits
   across 17 designs; G2). No other representation possesses all three: nauty-edit is complete but neither
   decodable nor navigable (avalanche-everywhere G2 profile); WL, NetLSD,
   HyperCOT, and HPD are scalable embeddings but neither complete nor
   decodable; the degree-sequence baseline is a metric but has no inverse. On
   A4 the differentiator is categorical: only IsalHG exhibits intermediate
   *hypergraphs* along a path — structurally impossible for every competing
   representation (no decoder for vector fingerprints; avalanche geometry
   blocks navigation for nauty).

   **HPD and the metric axioms.** HPD uses Jensen–Shannon divergence, which
   does not satisfy the triangle inequality (its square root does). Operations
   that require a metric — classical MDS, PAM-medoids, kNN with
   `metric='precomputed'` — are therefore only approximately licensed for HPD.
   The True metric column of the capability matrix records this; every results
   table where HPD appears flags it.

---

## G1 — Concentration + hubness profile (geometry, precondition for A3)

On every corpus, before any application: the pairwise-distance histogram of
`D_I`, the diameter-to-median ratio, the length-difference floor
(`d_I` vs `||w*_c(H)|-|w*_c(H')||`), and the hubness profile (skewness of the
`k`-occurrence distribution `N_k`, Radovanović et al. 2010).

- Deliverable: a per-corpus geometry table (alongside `ν`, `D̂` from A1).
- Consumer: A3's kNN result is interpreted against this profile (high hubness /
  strong concentration predict degraded kNN); competitors get the same table —
  whose metric concentrates less is itself a head-to-head axis.

**Measured (17 design families, 85 items, 27 seeds; metric `d_I^⊥`).** The
hubness signatures separate the representations sharply. `d_I^⊥` is moderately
hub-prone (`N_10` skewness 0.91 [0.52, 1.28]) with moderate concentration
(diameter-to-median 2.72); the WL histogram distance is the most hub-prone
(skewness 2.37 [2.37, 2.37] — a narrow CI because WL skewness is nearly
deterministic on these families), while NetLSD and HPD are hubness-neutral
(skewness 0.17 and 0.10 respectively). The degree-sequence baseline has low
hubness (0.28) but very compact dimension (D̂ = 3), consistent with its strong
clustering performance. HyperCOT is hubness-neutral (0.07) but spread in the
original space (diameter-to-median 8.05). The ordering is the precondition the
A3 result is read against: the highest-hubness representation (WL) is predicted
to lose most under kNN, and the prediction holds.
The same profile recomputed on the real HIC genre corpora preserves the
contrast — WL hubness is 4.5–7.4 there, `d_I^Σ` stays moderate (1.1–1.8) — so
the prediction transfers to real data (real-data entries use the label-aware
`d_I^Σ`; the contrast with WL hubness is structural and survives the vocabulary
shift). The scalability of `w*_c` sets a hard frontier: at arity k = 3 the
encoder is feasible up to n ≈ 24 vertices at low edge density (n = 16 at
medium density, n = 8 at high density); at k = 5 only n = 8 is feasible; k = 7
and k = 10 are measured infeasible at all tested sizes. Three cells from the
random-instance sweep timed out for IsalHG while all six competitors completed;
these three cells are excluded from the comparative analysis and the exclusion
is noted in each table. The arity sweep in the comparative analysis consequently
covers k ∈ {3, 4, 5} from the design-family breakdown and k ∈ {3, 5} from the
random-instance sweep (two arity points, not three); this is a measured outcome
of the feasibility envelope, not a design choice.

## G2 — Local sensitivity + ladder response (geometry, the smoothness evidence)

- **Sensitivity:** histograms of `s(e) = d_I(H, H⊕e)` over single structural
  edits (all Qin op types) on 17 design families spanning arities 3–5 (100
  connectivity-preserving single Qin edits per design, 2 seeds; 1700 edits
  total). **Measured (metric `d_I^⊥`):** IQR of `s(e)` across all 1700 edits:
  Q1 = 3 tokens, median = 5, Q3 = 9. The three-regime prediction
  (`../theoretical/stability.md` §4.2) is confirmed for 16 of 17 families and
  **falsified** for one (the tight-path arity-4 family,
  heavy_tail_frac = 0.210 against a unimodal prediction; the candidate
  explanation is incoherent ties at the measured arity/size combination).
  GQ(2,2) is confirmed as the predicted heavy-tailed regime
  (heavy_tail_frac = 0.230). Rendered figures: sensitivity contrast per regime.
- **Ladder:** `d_I^⊥(H_0, H_t)` vs known accumulated Qin budget `t` along
  perturbation ladders built from the design fixtures. **Measured (7 design
  fixtures × 2 seeds × 4 ladders = 56 ladders, 560 steps; metric `d_I^⊥`):**
  IQR of per-step increment: Q1 = 6, median = 12, Q3 = 18 tokens. Mean
  monotone fraction per ladder = 0.71; all 56 ladders are globally increasing
  (cumulative `d_I^⊥` rises from start to end in every case). The near-monotone
  trend is the smoothness evidence for neighbourhood methods (A2/A3).
- **Contrast:** the same `s(e)` measurement on the nauty-Levi canonical-string
  distance. **Measured:** IQR_nauty Q1 = 20, Q3 = 37 tokens across all 17
  families (4–8× wider than IsalHG) — the demonstration that iso-only
  canonical labelling yields no navigable geometry (`../COMPETITORS.md` §3) is
  a measured figure. The confirmed heavy-tailed regime (GQ(2,2)) shows
  IQR_nauty = 0 vs IQR_ours = 1; the falsified family (tight-path arity-4)
  shows IQR_nauty = 16 vs IQR_ours = 0. Rendered figures: contrast histograms
  per regime.
- Consumers: licences for A2/A3 neighbourhood methods; A4's scoring baseline;
  the discussion's drift/avalanche prose points at these histograms.

## A1 — Metric MDS (FLAGSHIP; measures the geometry)

Biochemical reaction networks represent each reaction as a hyperedge over its participating molecular species; a database of module-scale reaction networks therefore forms a corpus of small hypergraphs whose structural diversity an analyst surveys before selecting candidate mechanisms for experimental validation (Klamt, Haus, and Theis 2009; Benson, Gleich, and Leskovec 2016).<!-- envelope-sensitive -->

Goal: embed hypergraph space `(·, d_I)` into `R^D`; visualize similarity;
report the **estimated intrinsic dimension** and non-Euclidean mass as
first-class descriptors.

- Method: classical (Torgerson–Gower) MDS + SMACOF for the stress-minimizing
  configuration. Because `d_I` is a (generically) non-Euclidean edit metric,
  the Gram matrix `B` will have negative eigenvalues — **report `ν` and PSD
  status per corpus** (`../theoretical/geometry.md` §2). Theory frames the
  expectation: Bourgain (1985) guarantees `O(log N)` embedding distortion (MDS
  is justified), Khot–Naor (2006) prove string-edit metrics need non-trivial
  distortion (so a residual is expected and reported) — cite both.
- **Dimension selection (primary = cross-validation on held-out
  dissimilarities):** hold out a random subset of the `C(N,2)` entries, fit on
  the rest, predict held-out, pick `D̂` minimizing out-of-sample error.
  Supporting: Mardia `P^(1)`, `P^(2)`; negative-eigenvalue floor; parallel
  analysis.
- Metrics: Kruskal stress-1 vs `D`; CV reconstruction error; Shepard diagram.
- Competitor comparison: same pipeline on each `D_rep`; whose embedding has
  lower stress at matched `D`, and whose `D̂` is smaller (a lower faithful `D̂`
  argues the representation captures structure more compactly).

**Measured (17 design families, 85 items, 27 seeds; metric `d_I^⊥`).** The
geometry table is the paper's central characterization, with 95% confidence
intervals computed by percentile bootstrap over seeds. All IsalHG entries use
`d_I^⊥` — the structural member of the metric family (trivial vocabulary;
`stability.md` §1 Remark). `d_I^⊥` is **genuinely non-Euclidean**: the
double-centred Gram matrix is indefinite (not PSD) with non-Euclidean mass
`ν = 0.097` [0.092, 0.105] and cross-validated intrinsic dimension
`D̂ = 17` [15, 20] at low residual distortion (Kruskal stress-1 = 0.046
[0.042, 0.055]). Real HIC genre hypergraphs yield `D̂ ≈ 10` under `d_I^Σ`
(label-aware member; non-trivial IMDB vocabulary; `../theoretical/geometry.md`
§3); those rows measure a different family member and are read as a separate
object. The nauty-Levi canonical-string distance is non-Euclidean but less
compressible (`ν = 0.024`, `D̂` partially censored at the search cap).
NetLSD sits in a low dimension (`D̂ = 4`); the degree-sequence baseline is
three-dimensional (`D̂ = 3`). The WL histogram and HPD distances do not
concentrate — their cross-validation error falls monotonically to the search
cap, so their `D̂` is reported as censored. HyperCOT is one-dimensional
(`D̂ = 1`, very high distortion at that dimension — stress 0.275). The
non-Euclidean verdict licenses the medoid-based clustering of A2; the
per-representation `D̂` is itself a comparison axis.

| Representation | PSD | `ν` [95% CI] | `D̂` [95% CI] | stress@`D̂` [95% CI] | diam/med | `N_10` skew [95% CI] |
|---|---|---|---|---|---|---|
| IsalHG (`d_I^⊥`) | no | 0.097 [0.092, 0.105] | 17 [15, 20] | 0.046 [0.042, 0.055] | 2.72 | 0.91 [0.52, 1.28] |
| WL histogram | yes | 0.030 [0.029, 0.031] | ≥40 (censored) | 0.310 [0.302, 0.318] | 1.88 | 2.37 [2.37, 2.37] |
| NetLSD | yes | 0.000 | 4 | 0.000 | 2.73 | 0.17 [−0.16, 0.41] |
| HPD-JSD | yes† | 0.000 | ≥40 (censored) | 0.018 [0.016, 0.021] | 1.10 | 0.10 [−0.22, 0.40] |
| nauty-Levi edit | no | 0.024 [0.022, 0.026] | ≥39 (p.c.) | 0.023 [0.021, 0.025] | 3.86 | 0.01 [−0.49, 0.40] |
| degree-seq L1 | no | 0.103 [0.093, 0.113] | 3 | 0.053 [0.050, 0.056] | 2.93 | 0.28 [−0.04, 0.50] |
| HyperCOT | no | 0.250 [0.239, 0.261] | 1 [1, 2] | 0.275 [0.256, 0.295] | 8.05 | 0.07 [−0.23, 0.33] |

†HPD-JSD: ν = 0 because JSD^{1/2} has a PSD Gram matrix on this corpus; the triangle-inequality caveat (§Usefulness) applies to the clustering and kNN steps.
p.c. = partially censored (52% of seeds hit the search cap at D = 40).
All IsalHG entries use `d_I^⊥` (trivial vocabulary; `stability.md` §1 Remark).

The theory brackets the distortion: Bourgain (1985) guarantees an `O(log N)`
embedding exists (so MDS is justified) and Khot–Naor (2006) prove string-edit
metrics require non-trivial distortion (so the measured residual is expected,
not a defect).

## A2 — Unsupervised structure (one story: clustering + hierarchy)

Databases of biological network motifs and signaling-pathway submodules catalog structurally distinct higher-order interaction patterns; grouping these module-scale hypergraphs into structural families and returning a *medoid* — an actual representative hypergraph that an analyst can directly inspect, rather than a centroid undefined in non-Euclidean space — makes the structural taxonomy actionable (Milo et al. 2002).<!-- envelope-sensitive -->

Corpus with **planted families** (seed motifs + seed-stable, non-isomorphic
perturbations ⇒ known membership; `../DATA.md` §1).

- Licence: `ν` (k-medoids/PAM needs only a metric, no coordinates —
  `../theoretical/geometry.md` §2) and the G2 smoothness evidence.
- k-medoids (PAM) on `D_I`. Internal metrics: silhouette, Dunn,
  Davies–Bouldin. External (vs planted labels): Adjusted Rand Index, NMI.
- Agglomerative dendrogram on `D_I`. Metrics: cophenetic correlation,
  silhouette at the induced cut.
- Medoid-representative (v2's standalone application) is the `k=1` degenerate —
  reported inline, not a section.
- Competitor comparison: same metrics on each `D_rep`; report metrics vs
  corpus density so the sparse/dense behaviour is visible.

**Measured (17 design families, 85 items, 27 seeds; metric `d_I^⊥`).** Recovering
17 families from structure alone is a demanding task — degree structure is the
dominant discriminative signal in these families, so degree-free representations
are not expected to lead, and none does. Adjusted Rand Index (ARI, 95% CI):
degree-seq leads at 0.451 [0.366, 0.559]; NetLSD follows at 0.479 [0.402,
0.573]; IsalHG is 0.285 [0.195, 0.368]; HPD 0.303 [0.240, 0.381]; HyperCOT
0.287 [0.225, 0.365]; nauty-Levi 0.178 [0.123, 0.236]; WL 0.016 [0.012,
0.017]. One-sided Wilcoxon signed-rank, Holm-corrected: degree-seq > IsalHG
(p_Holm = 8.2 × 10⁻⁸, r = 1.09); NetLSD > IsalHG (p_Holm = 7.5 × 10⁻⁸,
r = 1.09); HPD vs. IsalHG ns (p_Holm = 0.36); IsalHG > nauty-Levi
(p_Holm = 8.9 × 10⁻⁸); IsalHG > WL (p_Holm = 6.7 × 10⁻⁸). PAM is the
correct estimator precisely because the space is non-Euclidean (A1); no
centroid method applies. The conclusion is that IsalHG clustering is
statistically weaker than degree-seq and NetLSD on these families, statistically
stronger than nauty-Levi and WL, and indistinguishable from HPD and HyperCOT.
The paper's claim is *licensed* usefulness via the metric structure, not ARI
dominance.

**Measured (real HIC genre, censored subset; metric `d_I^Σ`).** On the two
cleanly computable IMDB genre datasets (`w*_c`-yield 92.5% and 91.7%), genre is
near-unclusterable from structure alone: **every** representation scores ARI < 0.10,
including `d_I^Σ`. No representation leads meaningfully — an honest negative result. The four
remaining IMDB genre datasets are retained at only 34–43% under the `w*_c`
budget, with label-correlated censoring (some genres below 20% retention); their
clustering numbers are reported for completeness but are not used for
representation ranking.

## A3 — kNN classification (supervised story)

In co-authorship and collaboration networks, each paper or project forms a hyperedge over its participants; assigning an incoming team-structure hypergraph to one of a set of known structural types — using only its distance to labelled examples, without retraining — is a recurring classification task in the analysis of these systems (Newman 2001; Chodrow, Veldt, and Benson 2021).<!-- envelope-sensitive -->

Needs a **labelled** hypergraph corpus with ≥2 classes: planted family ids
(synthetic) and HIC dataset labels (real; `../DATA.md` §2).

- Licence: the G1 concentration + hubness profile (reported first; the kNN
  result is read against it).
- Method: k-NN with `metric='precomputed'`, leave-one-out / stratified CV.
- Metrics: accuracy, macro-F1, AUC (one-vs-rest). Report vs `k`.
- Competitor comparison: k-NN on each `D_rep`, same folds.

**Measured (17 design families, 85 items, 27 seeds; metric `d_I^⊥`).** The G1
hubness profile predicts the kNN ordering. WL's hubness skewness is 2.37 on
this corpus and its AUC-OvR at k = 5 **collapses to chance (0.495 [0.487,
0.500])** — the primary confirmation of the licence. AUC-OvR at k = 5 (95%
CI): degree-seq 0.948 [0.927, 0.965]; NetLSD 0.934 [0.909, 0.959]; IsalHG
0.920 [0.885, 0.946]; HyperCOT 0.926 [0.894, 0.958]; HPD 0.895 [0.871,
0.921]; nauty-Levi 0.839 [0.804, 0.881]; WL 0.495 [0.487, 0.500].
One-sided Wilcoxon signed-rank, Holm-corrected: degree-seq > IsalHG
(p_Holm = 2.0 × 10⁻⁶, r = 0.949); NetLSD > IsalHG (p_Holm = 1.3 × 10⁻³,
r = 0.655); HPD vs. IsalHG ns (p_Holm = 1.0; HPD is numerically below
IsalHG); IsalHG > nauty-Levi (p_Holm = 5.2 × 10⁻⁸, r = 1.09); IsalHG > WL
(p_Holm = 6.0 × 10⁻⁸, r = 1.09). The strong-hubness→failure prediction for WL
is decisive; among the remaining representations degree-seq and NetLSD lead
significantly, which mirrors the A2 ranking and reflects the dominant role of
degree structure in discriminating the design families. HPD does not improve on
IsalHG on A3 despite its A2 numerical lead. This is the payoff of the
no-orphan-geometry rule: the G1 hubness measurement forecasts the supervised
outcome before the classifier is run.

**Measured (real HIC genre, censored subset).** The same hubness contrast recurs
on real data. On the two clean IMDB genre datasets the mean AUC-OvR at k = 9 is
0.673 for `d_I^Σ` (label-aware member; non-trivial IMDB vocabulary), followed
by NetLSD and the nauty-Levi edit distance (both 0.654), against 0.624 for the
WL histogram, which again trails in line with its elevated real-data hubness
(skewness 4.5–7.4). The agreement of the hubness→kNN prediction across synthetic
*and* real corpora is the empirical spine of the geometric characterization. (HPD
is not conclusive on the clean datasets: its vendored hyperedge-portrait
construction raises an index error on a third of the real instances, so it is
scored only on a per-instance-censored subset and flagged as such.)

## A4 — Shortest path between hypergraphs (the capability differentiator)

Temporal higher-order network datasets record a system's interaction structure at successive time points; comparing two snapshots asks not just how different the states are but which structural path connects them, with every intermediate a valid, inspectable hypergraph — a requirement that no fingerprinting method without a closed, decodable alphabet can satisfy (Holme and Saramäki 2012; Battiston et al. 2020).<!-- envelope-sensitive -->

The path `H_A → H_B` of minimal accumulated `d_I` through a pool of
intermediates. Two properties no competitor shares: (a) canonical-form
baselines are not edit-navigable (their measured `s(e)` profile is
avalanche-everywhere — G2); (b) vector fingerprints (WL, NetLSD, HyperCOT)
have **no decoder** — they cannot exhibit the intermediate *hypergraphs* along
a path. IsalHG can: the alphabet is closed, so any intermediate string decodes
to an actual hypergraph via S2H.

**HGED-free scoring (v3, replacing the v2 "vs true HGED geodesic" metric):**

- Construction: endpoints `H_A = H_0`, `H_B = H_t` from a perturbation ladder
  with known accumulated budget `t`; the pool contains the ladder's true
  intermediates plus distractors from the same corpus.
- Scores: (i) **path recovery** — does the shortest `d_I`-path re-find the
  ladder's intermediates (or same-budget equivalents) in order; (ii)
  **monotonicity** — accumulated path length vs ladder budget `t` (the G2
  ladder response read along paths); (iii) **decodability demo** — the decoded
  intermediate hypergraphs of one recovered path, shown (a figure competitors
  structurally cannot produce).
- Competitor comparison: (i)–(ii) for vector competitors where a path is
  computable at all; the capability matrix records who cannot run this.

**Measured (8 design-ladder instances spanning 7 design fixtures; metric
`d_I^⊥`).** Accumulated path length is **monotone in the ladder budget for every
representation tested** (monotone fraction 1.00 for IsalHG, WL, NetLSD, HPD) —
the ladder response of G2 read along shortest paths. Exact recovery of the
specific ladder intermediates differs substantially: WL recovery fraction = 0.000
(WL jumps directly from start to end in a two-node path, finding no
intermediates); NetLSD 0.257; HPD 0.191; IsalHG 0.125. IsalHG's lower recovery
than NetLSD and HPD reflects that the `d_I^⊥` geodesic routes through
same-budget alternatives rather than retracing the exact edit sequence — which
is a direct empirical illustration of the closing discussion's point that `d_I`
is not an edit-distance proxy. The **decodability differentiator is the
categorical result**: in all 8 instances, the IsalHG intermediate strings decode
via S2H to valid hypergraphs (8/8, all_valid = True); the path exhibits a mean
of 2.4 decoded intermediates per instance. WL, NetLSD, and HPD have no decoder —
they cannot exhibit the intermediate *hypergraphs* — and the nauty-Levi distance
cannot navigate at all (avalanche profile). The capability matrix below records
this: usefulness on A4 is not a recovery score, it is a capability that no
competing representation possesses.

## Corpora needed (→ `../DATA.md`)

| Measurement | Corpus requirement |
|---|---|
| G1/G2 profiles | every corpus (profiles are per-corpus preambles); designs for the sensitivity fixtures |
| A1 MDS | planted-family synthetic (primary) + HIC IMDB genre (censored secondary exhibit) |
| A2 clustering | planted families (known membership) + HIC IMDB genre |
| A3 kNN | labelled: planted family ids + HIC IMDB genre labels |
| A4 path | ladder endpoints + intermediate pool with distractors (synthetic only) |

## Competitor applicability (→ `../COMPETITORS.md`)

| Measurement | WL / NetLSD / HPD (vector `D_rep`) | HyperCOT | nauty-Levi edit (contrast) |
|---|---|---|---|
| G1 profile | yes | where feasible (O(n³)/pair) | yes |
| G2 sensitivity | yes (their `s(e)`) | where feasible | **yes — the contrast figure** |
| A1 MDS | yes | where feasible | yes (unstable geometry, shown) |
| A2 clustering | yes | where feasible | yes (contrast) |
| A3 kNN | yes | where feasible | yes |
| A4 path | degrades (no decoder; scores (i)–(ii) only) | degrades | **no** (differentiator) |

HyperCOT's `O(n³)`-per-pair cost restricts it to the small/mid corpora; its
rows state the limit rather than hide it (`../COMPETITORS.md` §2).

## Runtime — the cost axis (and the `d_I^⊥` compromise)

Every representation's pairwise matrix is timed (wall-clock, per the reporting
standard). On the 85-item design corpus (3,570 pairs) the `D`-matrix wall-clock
ranks: nauty-Levi and WL are fast but disqualified on quality — nauty's geometry
is avalanche-unusable (G2) and WL's hubness forces chance-level kNN (A3). Among
the geometrically capable representations, `d_I^⊥` is competitive with NetLSD
and faster than HPD, which fails on a third of real HIC instances (its vendored
portrait). HyperCOT is `O(n³)` per pair (tractable only on the small design
corpus; excluded from the random-instance cells). `d_I^⊥` is the **compromise
the other axes point to**: fast and capable on small-to-moderate instances,
decodable, geometrically characterizable, and carrying a proved completeness
guarantee that no other representation in the comparison set provides.

**Scalability frontier.** The canonical encoder's feasibility is the binding
constraint: at arity k = 3, `w*_c` completes within budget at n ≤ 24 vertices
(low edge density) and n ≤ 16 at medium density, but times out at n = 16 high
density and n = 24 medium density. At k = 5, only n = 8 low density is feasible;
k = 7 and k = 10 are measured infeasible at all tested sizes — the advertised
arity cap of 10 is not reachable at any tested vertex count. Three random cells
timed out for IsalHG while all six completing competitors finished; those cells
are excluded from the IsalHG comparative analysis and flagged in every table. The
arity axis in the random-instance sweep therefore covers k ∈ {3, 5} (two points,
not three); the design-family breakdown provides k ∈ {3, 4, 5} for A2/A3 task
metrics, but not for the geometry sweep curve.

The runtime advantage is **per-instance-size dependent**. `w*_c` cost scales
with hypergraph size and tie-symmetry, so `d_I` is fast on small-to-moderate
instances and becomes expensive on large near-symmetric inputs — the mechanism
behind the HIC censoring (`../DATA.md` §2). The cost claim is "fast and capable
on small-to-moderate instances," stated with its size dependence, not a universal
speed claim.
