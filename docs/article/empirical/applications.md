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
`w*_c` (and competitor) wall-clock. The primary corpus is the size-controlled
swap-planted corpus (Stratum C, `../DATA.md` §1): three `(n, m)` cells, one
exact degree sequence per cell, family membership as ground truth, and both
naive baselines identically zero on every pair by construction. Real
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
scores — on the size-controlled corpus it does not, and the body reports that
plainly.

**Why the corpus is size-controlled.** The first-generation primary corpus
(17 design families × 5 members) was separable on size alone: a distance built
from `|Δn| + |Δm|` — two integers, no structure — reached ARI 0.442 and
AUC-OvR 0.932 on it, outranking five of the seven representations on the first
metric and four of seven on the second, because the seventeen families occupy
only fourteen distinct `(n, m)` cells. Those task standings measured how
directly each representation encodes size and are withdrawn
(`results/superseded/`); `../theoretical/geometry.md` §5 records the
measurement and its mechanism. The replacement corpus holds `(n, m, k)` and
the exact degree sequence constant across classes, so the withdrawn failure
mode is excluded *by construction* and verified through the same harness:
`size_l1` and `degree_seq_l1` score ARI −0.000 [−0.001, 0.000] and AUC-OvR
0.492 (the tie-degenerate chance level) at every cell.

**Measured standings on the size-controlled corpus (3 cells, 27 seeds,
95% BCa CIs, Holm-corrected Wilcoxon).** With size and degrees silenced, the
purely structural task signal ranks: the nauty-Levi canonical edit distance
first (ARI 0.235/0.399/0.614 across the three cells; AUC 0.804/0.888/0.938),
HPD second (up to ARI 0.519, AUC 0.942), NetLSD third (up to ARI 0.123);
IsalHG scores above all three floor rows with Holm-corrected significance at
every cell (p ≤ 7.5 × 10⁻³) but far below the leaders (ARI 0.016–0.028, AUC
0.545–0.569; all three leaders beat it at p ≤ 0.028, mostly ≤ 10⁻⁶), and the
WL histogram sits exactly at the floor — blind at fixed degree sequence. The
mechanism behind IsalHG's position is measured, not conjectured: a single
edit — swap or Qin op alike — moves `w*_c` by ≈30–50 % of the string on these
unanchored substrates (the tie/seed avalanche and pointer drift of the closing
discussion), so the edit-proximity class structure that the corpus plants is
largely invisible to instruction-string Levenshtein, while an
adjacency-serialized canonical form (nauty) localizes the same edit. This is
the task-level face of the completeness–stability frontier: the properties
that make `w*_c` a complete, decodable invariant are the properties that
destroy its local task geometry. Usefulness therefore rests on three axes
jointly:

1. **Licensed.** Each application is preceded by a measured geometric invariant
   that justifies the method choice (the no-orphan-geometry rule;
   `../theoretical/geometry.md`). No application runs speculatively: A1 is
   licensed by the distortion brackets; A2 by `ν` (non-Euclidean mass makes
   medoids the correct estimator) and the G2 ladder response; A3 by the G1
   hubness profile; A4 by the G2 local sensitivity profile and the closed
   alphabet.

2. **Honest on task metrics.** On the size-controlled corpus IsalHG does not
   lead A2/A3 and the paper says so: the pre-registered contract
   (`../COMPETITORS.md` §4) binds us to report the outcome in whichever
   direction it falls, and it falls against us — nauty-Levi edit, HPD, and
   NetLSD recover the planted structure significantly better, while IsalHG
   stays significantly above the naive floor that both baselines and WL sit
   on. Relative standings are reported with 95% BCa bootstrap confidence
   intervals and one-sided Wilcoxon signed-rank tests, Holm-corrected across
   the (representations × metrics) family in each direction; no representation
   is declared dominant where the corrected p exceeds 0.05. What the corpus
   buys is interpretability: every point of ARI/AUC on it is higher-order
   structure, so the ranking is a finding about representations, not about
   corpus construction.

3. **Uniquely capable.** The **capability matrix** (Fig. CAP; rendered by
   `experiments/article/analysis/figures/capability_matrix.py`; place adjacent
   to the A4 decoded-intermediates figure) expresses what each representation
   *cannot* do. IsalHG is the only representation that is simultaneously a
   **complete invariant**, **decodable** (S2H inverts every string in the
   closed alphabet to an actual hypergraph), and **geometrically navigable**
   (measured single-edit sensitivity IQR 3–9 tokens, median 5; 1700 edits
   across 17 designs; G2 — with the caveat, measured at T-M4b, that this
   absolute-token stability is a property of the anchored design fixtures:
   on random fixed-degree substrates a single edit moves ≈30–50 % of the
   string, which is what bounds IsalHG's A2/A3 scores above). No other
   representation possesses all three: nauty-edit is complete but not
   decodable (and its design-fixture sensitivity is 4–8× wider — G2); WL,
   NetLSD, HyperCOT, and HPD are scalable embeddings but neither complete nor
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

**Measured (size-controlled corpus, 3 cells × 72 items, 27 seeds; metric
`d_I^⊥`).** At fixed `(n, m, k, degree sequence)` the hubness signatures
still separate the representations. `d_I^⊥` is moderately hub-prone (`N_10`
skewness 0.92–0.94 across the cells, e.g. 0.935 [0.831, 1.063] at (12,20));
nauty-Levi edit is milder (0.39–0.58), HPD comparable to IsalHG (0.63–1.11),
and NetLSD is hubness-negative (−0.29 to −0.40). The WL histogram is
**tie-degenerate**: at a fixed degree sequence its integer L1 collapses onto
so few distinct values that neighbour ranking reduces to index order, and its
hubness (2.079) and kNN score reproduce those of the all-zero naive-baseline
matrices exactly. The highest-hubness representation again sits at chance
under kNN (A3) — the licence prediction recurs on the controlled corpus,
though for WL the mechanism is tie degeneracy rather than hub concentration.
The same profile recomputed on the real HIC genre corpora preserves the
contrast — WL hubness is 4.5–7.4 there, `d_I^Σ` stays moderate (1.1–1.8) —
so the prediction transfers to real data (real-data entries use the
label-aware `d_I^Σ`). The scalability of `w*_c` sets a hard frontier: at
arity k = 3 the encoder is feasible up to n ≈ 24 vertices at low edge density
(n = 16 at medium density, n = 8 at high density); at k = 5 only n = 8 is
feasible; k = 7 and k = 10 are measured infeasible at all tested sizes. The
size-controlled corpus is therefore 3-uniform: a k = 5 cell would need ≥ 12
families × 6 members at n = 8, which the envelope does not support — a
measured limitation of the primary corpus, stated as such. Three cells from
the geometry-vs-density sweep (Stratum B) timed out for IsalHG while all six
competitors completed; those cells are excluded from the comparative analysis
and the exclusion is noted in each table.

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

**Measured (size-controlled corpus, 3 cells × 72 items, 27 seeds; metric
`d_I^⊥`).** The geometry table is the paper's central characterization, with
95% BCa bootstrap confidence intervals over seeds. All IsalHG entries use
`d_I^⊥` — the structural member of the metric family (trivial vocabulary;
`stability.md` §1 Remark). `d_I^⊥` remains **genuinely non-Euclidean** at
every cell, and its non-Euclidean mass falls with cell size
(`ν = 0.137 [0.136, 0.140]` at (9,12), `0.061 [0.060, 0.062]` at (12,20),
`0.011 [0.010, 0.011]` at (15,35)). Its cross-validated intrinsic dimension
is measurable only at the smallest cell (`D̂ = 27.4` [26.9, 28.0] at (9,12));
at the two larger cells the CV error falls monotonically to the search cap
(`D̂ ≥ 40`, censored) — the high-dimensional signature of a space whose
distances concentrate under the avalanche. Residual distortion stays low
(stress 0.021–0.059). Real HIC genre hypergraphs yield `D̂ ≈ 10` under
`d_I^Σ` (label-aware member; non-trivial IMDB vocabulary;
`../theoretical/geometry.md` §3); those rows measure a different family
member and are read as a separate object. Representative rows at the middle
cell (12,20):

| Representation | `ν` [95% BCa CI] | `D̂` [95% BCa CI] | stress@`D̂` | `N_10` skew [95% BCa CI] |
|---|---|---|---|---|
| IsalHG (`d_I^⊥`) | 0.061 [0.060, 0.062] | ≥40 (censored) | 0.021 [0.020, 0.021] | 0.935 [0.831, 1.063] |
| nauty-Levi edit | 0.011 [0.010, 0.012] | ≥40 (censored) | 0.026 [0.024, 0.029] | 0.584 [0.478, 0.694] |
| HPD-JSD | 0.000† | 26.0 [24.8, 27.1] | 0.000 | 0.844 [0.700, 1.007] |
| NetLSD | 0.000 | 3.3 [3.1, 3.4] | 0.000 | −0.294 [−0.381, −0.201] |
| WL histogram | 0.000 | ≥40 (censored; tie-degenerate) | 0.345 | 2.079 (tie artifact) |
| degree-seq L1 / size_l1 | 0.000 | 1 (all-zero `D`) | 0.000 | 2.079 (tie artifact) |

†HPD-JSD: ν = 0 because JSD^{1/2} has a PSD Gram matrix on this corpus; the
triangle-inequality caveat (§Usefulness) applies to the clustering and kNN
steps. HyperCOT is gated out of the size-controlled cells by its corpus cap
(N = 72 > 20; `../COMPETITORS.md` §2). The two canonical-string metrics are
the only non-Euclidean rows; the naive baselines' rows are the degenerate
geometry of an identically-zero distance matrix, printed to pin the floor.
The non-Euclidean verdict licenses the medoid-based clustering of A2; the
per-representation `D̂` remains a comparison axis (NetLSD compresses to three
dimensions; the string metrics do not concentrate below the cap).

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

**Measured (size-controlled corpus, 3 cells × 12 families × 6 members,
27 seeds; metric `d_I^⊥`).** With size and degrees held constant, every point
of ARI is higher-order structure. Adjusted Rand Index (95% BCa CI over
27 seeds):

| Representation | (9,12) | (12,20) | (15,35) |
|---|---|---|---|
| nauty-Levi edit | 0.235 [0.207, 0.265] | 0.399 [0.365, 0.439] | 0.614 [0.571, 0.657] |
| HPD-JSD | 0.108 [0.096, 0.122] | 0.259 [0.238, 0.281] | 0.519 [0.481, 0.555] |
| NetLSD | 0.045 [0.039, 0.053] | 0.064 [0.054, 0.074] | 0.123 [0.104, 0.140] |
| IsalHG (`d_I^⊥`) | 0.026 [0.019, 0.038] | 0.028 [0.017, 0.040] | 0.016 [0.009, 0.025] |
| WL histogram | −0.000 [−0.001, 0.000] | −0.000 | −0.000 |
| degree-seq L1 | −0.000 [−0.001, 0.000] | −0.000 | −0.000 |
| size_l1 | −0.000 [−0.001, 0.000] | −0.000 | −0.000 |

One-sided Wilcoxon signed-rank, Holm-corrected, direction identical at all
three cells: nauty-Levi > IsalHG and HPD > IsalHG (p_Holm ≤ 1.1 × 10⁻⁶);
NetLSD > IsalHG (p_Holm ≤ 0.014); IsalHG > WL, IsalHG > degree-seq,
IsalHG > size_l1 (p_Holm ≤ 7.5 × 10⁻³). PAM is the correct estimator
precisely because the space is non-Euclidean (A1); no centroid method
applies. The conclusion is stated plainly: the planted structure is
recoverable (nauty-edit reaches ARI 0.614 at the largest cell, and the signal
grows with cell size for every above-floor representation), IsalHG's
recovery is statistically real but small, and the naive baselines sit at
exactly the floor the corpus was built to enforce. The paper's claim is
*licensed* usefulness via the metric structure and the capability axis, not
ARI dominance — and the ranking is now a finding about representations,
which the withdrawn corpus could not deliver.

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

**Measured (size-controlled corpus, 3 cells × 72 items, 27 seeds; metric
`d_I^⊥`).** AUC-OvR at k = 5 (95% BCa CI over 27 seeds):

| Representation | (9,12) | (12,20) | (15,35) |
|---|---|---|---|
| nauty-Levi edit | 0.804 [0.783, 0.827] | 0.888 [0.873, 0.903] | 0.938 [0.930, 0.946] |
| HPD-JSD | 0.677 [0.658, 0.692] | 0.828 [0.816, 0.839] | 0.942 [0.932, 0.951] |
| NetLSD | 0.589 [0.575, 0.606] | 0.626 [0.611, 0.641] | 0.714 [0.694, 0.734] |
| IsalHG (`d_I^⊥`) | 0.545 [0.530, 0.563] | 0.569 [0.554, 0.583] | 0.565 [0.550, 0.581] |
| WL / degree-seq / size_l1 | 0.492 [0.492, 0.492] | 0.492 | 0.492 |

The Holm-corrected ordering mirrors A2 at every cell: nauty-Levi, HPD, and
NetLSD > IsalHG (p_Holm ≤ 0.028, mostly ≤ 10⁻⁶); IsalHG > all three floor
rows (p_Holm ≤ 8.9 × 10⁻⁷ on AUC). The G1 licence reading recurs: the
highest-hubness representation (WL, tie-degenerate at 2.079) scores exactly
the chance level of the zero-matrix baselines — kNN needs a neighbourhood
structure, and at fixed degrees WL has none. IsalHG's AUC sits 0.05–0.08
above chance across the cells, statistically real at every cell but bounded
by the same avalanche that bounds its ARI. This is the payoff of the
no-orphan-geometry rule: the G1 profile (tie degeneracy, hubness,
concentration) forecasts the supervised outcome before the classifier is run.

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
is not an edit-distance proxy.

**The pool-based decodability score is withdrawn.** As constructed, the path
runs through a pool of pre-existing hypergraphs, and the reported
`all_valid = True` over 8/8 instances (mean 2.4 intermediates) decodes the
canonical strings of pool members — that is `S2H(w*_c(H)) ≅ H` on objects that
were hypergraphs before the experiment began, which is round-trip soundness
restated rather than a capability shown. The competitor contrast fails the same
way: the vector representations' recovered paths also visit pool members, which
are hypergraphs and are equally exhibitable, so "they cannot exhibit the
intermediate hypergraphs" is not true *of this construction*. Path recovery and
monotonicity above are unaffected.

**The capability that survives is a property of the alphabet, and it is
stronger.** Every string on a Levenshtein alignment path between two canonical
strings decodes — not only the canonical ones. Because `d_I` runs over the
token sequence, an alignment edits whole alphabet symbols, so each intermediate
is a word of `Σ_HG(k)*`, on which S2H is total; and because `V_{i,j}` attaches
its fresh vertices to an edge already containing at least one existing vertex,
every such word decodes to a *connected* hypergraph. Measured on five design
pairs spanning `d_I` from 3 to 22: **62 of 62 intermediates decode and all 62
are connected**, while only 10 of 62 are themselves canonical — exactly the two
endpoints of each path. The interior of a geodesic therefore lies outside the
canonical image, and the walk between STS(7) and the tight 3-cycle family
contracts to a three-vertex hypergraph before rebuilding rather than morphing
between the endpoints. This is the honest form of the differentiator: no vector
representation has an ambient space whose every point is a hypergraph, because
a point between two signatures in `ℝ^d` is a point in `ℝ^d` and there is no map
back; and nauty's canonical string, though decodable, is not edit-navigable
(its avalanche profile, G2). Usefulness on A4 is not a recovery score — it is
this ambient decodability.

## Corpora needed (→ `../DATA.md`)

| Measurement | Corpus requirement |
|---|---|
| G1/G2 profiles | every corpus (profiles are per-corpus preambles); designs for the sensitivity fixtures |
| A1 MDS | size-controlled Stratum C (primary) + HIC IMDB genre (censored secondary exhibit) |
| A2 clustering | size-controlled Stratum C (planted swap-families, naive floors ≡ 0) + HIC IMDB genre |
| A3 kNN | labelled: Stratum C family ids + HIC IMDB genre labels |
| A4 path | ladder endpoints + intermediate pool with distractors (synthetic only) |

The corpus policy — which corpus serves which measurement, and why — is
`../DATA.md` §7.

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
standard). On the size-controlled cells (72 items, 2,556 pairs per cell) the
`d_I^⊥` matrix costs 2–20 s per corpus seed depending on the cell; nauty-Levi
and WL are faster still, NetLSD and HPD comparable, and HyperCOT is gated out
by its `O(n³)`-per-pair corpus cap. WL's speed buys nothing here (it is
tie-degenerate at fixed degrees — G1), while nauty-Levi edit is both fast and
the strongest structure recoverer on the controlled tasks; the runtime axis
does not rescue IsalHG's task standing, and we do not claim it does. What
`d_I^⊥` uniquely carries at this cost is the combination the capability
matrix records: a proved completeness guarantee, a decodable closed alphabet,
and a characterized (non-Euclidean, licensed) geometry — properties no faster
representation in the set provides.

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
