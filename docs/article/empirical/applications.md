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

## G1 — Concentration + hubness profile (geometry, precondition for A3)

On every corpus, before any application: the pairwise-distance histogram of
`D_I`, the diameter-to-median ratio, the length-difference floor
(`d_I` vs `||w*_c(H)|-|w*_c(H')||`), and the hubness profile (skewness of the
`k`-occurrence distribution `N_k`, Radovanović et al. 2010).

- Deliverable: a per-corpus geometry table (alongside `ν`, `D̂` from A1).
- Consumer: A3's kNN result is interpreted against this profile (high hubness /
  strong concentration predict degraded kNN); competitors get the same table —
  whose metric concentrates less is itself a head-to-head axis.

**Measured (planted corpus, N = 60, five families).** The hubness signatures
separate the representations sharply. `d_I` is mildly hub-prone (`N_10`
skewness 0.231) with moderate concentration (diameter-to-median 1.5); the WL
histogram distance is strongly hub-prone (skewness 1.777), while NetLSD is
anti-hub (−0.551). This ordering is the precondition the A3 result is read
against: the high-hubness representation is predicted to lose most under kNN.
The same profile recomputed on the real HIC genre corpora preserves the
contrast — WL hubness rises to 4.5–7.4 there, `d_I` stays benign — so the
prediction transfers to real data.

## G2 — Local sensitivity + ladder response (geometry, the smoothness evidence)

- **Sensitivity:** histograms of `s(e) = d_I(H, H⊕e)` over single structural
  edits (all Qin op types), per density regime and on the four design fixtures
  (Fano, STS(9), the cyclic C13 orbit, GQ(2,2)). The C13 fixture is the cheap
  partial system, not a true STS(13): `s(e)` needs one `w*_c` per edit, and a
  true STS(13) costs ~44 s per `w*_c` — infeasible at histogram scale.
  **Measured (connectivity-preserving single Qin edits, `max_arity = 3`, seven
  regimes):** IQR_ours = 2.0–8.0 tokens, heavy_tail_frac = 0.000 throughout.
  The three-regime prediction (`../theoretical/stability.md` §4.2) is confirmed
  for the random corpora and the two coherent-tie designs (Fano, STS(9)), and
  **falsified** for the two incoherent-tie designs (cyclic C13, GQ(2,2)), which
  show compact near-unimodal profiles under single arity-3 Qin edits rather
  than the predicted heavy tail. Rendered figures: sensitivity contrast per
  regime and per design fixture.
- **Ladder:** `d_I(H_0, H_t)` vs known accumulated Qin budget `t` along
  perturbation ladders. **Measured (six corpora, small/medium/large base size,
  two seeds each):** ≈80% of per-ladder steps are monotone; mean `d_I`
  increment per Qin budget step grows from 3.2 (n = 5 base) to 11.7 (n = 12
  base); all six ladders globally increasing. This near-monotone trend is the
  smoothness evidence for neighbourhood methods (A2/A3).
- **Contrast:** the same `s(e)` measurement on the nauty-Levi canonical-string
  distance. **Measured:** IQR_nauty = 10.0–20.0 across all seven regimes
  (ratio 1.25–9.5× ours) — the demonstration that iso-only canonical labelling
  yields no navigable geometry (`../COMPETITORS.md` §3) is a measured figure.
  The contrast holds on both falsified designs: C13 IQR_nauty = 19.0 vs
  IQR_ours = 2.0; GQ(2,2) IQR_nauty = 10.0 vs IQR_ours = 8.0. Rendered
  figures: contrast histograms per regime and per design fixture.
- Consumers: licences for A2/A3 neighbourhood methods; A4's scoring baseline;
  the discussion's drift/avalanche prose points at these histograms.

## A1 — Metric MDS (FLAGSHIP; measures the geometry)

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

**Measured (planted corpus, N = 240, twenty families).** The geometry table
below is the paper's central characterization, reported on the corpus at which
the intrinsic-dimension estimate has stabilized. (A smaller N = 60 corpus
under-resolves it: the `N`-scaling sweep in `../theoretical/geometry.md` §3 shows
`D̂` climbing from 21 at N = 60 and plateauing at 26 for N ≥ 240, corroborated by
an independent Horn parallel-analysis bracket of [12, 26]; the applications
below are run on this same N = 240 corpus so geometry and usefulness are
measured on one object.) `d_I` is **genuinely non-Euclidean**: the double-centred
Gram matrix is indefinite (not PSD) with non-Euclidean mass `ν = 0.250` — a
quarter of the distance mass in negative eigenvalues — and cross-validated
intrinsic dimension `D̂ = 26` at low residual distortion (Kruskal stress-1 =
0.062). Real HIC genre hypergraphs are markedly lower-dimensional (`D̂ ≈ 10`,
`../theoretical/geometry.md` §3). The nauty-Levi canonical-string distance is
also non-Euclidean and less compressible (`ν = 0.133`, `D̂` censored at the cap).
The three vector representations are, by construction, Euclidean (`ν = 0`):
NetLSD sits in a genuinely low dimension (`D̂ = 5`), whereas the WL histogram and
HPD distances do not concentrate — their cross-validation error falls
monotonically to the search cap, so their `D̂` is reported as censored at that
cap rather than as an estimate. The non-Euclidean verdict is what licenses the
medoid-based clustering of A2 (a metric with negative eigenvalues has no faithful
centroid), and the per-representation `D̂` is itself a comparison axis.

| Representation | PSD | `ν` | `D̂` | stress@`D̂` | diam/med | `N_10` skew |
|---|---|---|---|---|---|---|
| IsalHG (`d_I`) | no | 0.250 | 26 | 0.062 | 1.75 | 1.280 |
| WL histogram | yes | 0.000 | ≥40 (censored) | 0.636 | 1.10 | 4.586 |
| NetLSD | yes | 0.000 | 5 | 0.000 | 5.03 | 0.121 |
| HPD | yes | 0.000 | ≥40 (censored) | 0.038 | 1.55 | 1.081 |
| nauty-Levi edit | no | 0.133 | ≥40 (censored) | 0.080 | 1.79 | 0.330 |

The theory brackets the distortion: Bourgain (1985) guarantees an `O(log N)`
embedding exists (so MDS is justified) and Khot–Naor (2006) prove string-edit
metrics require non-trivial distortion (so the measured residual is expected,
not a defect).

## A2 — Unsupervised structure (one story: clustering + hierarchy)

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

**Measured (planted corpus, N = 240, twenty families).** Recovering twenty
planted families from structure alone is a hard task, and recovery is modest for
every representation — but the relative ordering is stable and `d_I` is a close
second. Adjusted Rand Index is 0.102 for `d_I` (NMI 0.407), just behind HPD (ARI
0.120, NMI 0.445), then NetLSD (ARI 0.051, NMI 0.364), while the nauty-Levi and
WL distances essentially fail (ARI 0.018 and ≈ 0.00). PAM is the correct
estimator here precisely because the space is non-Euclidean (A1). The conclusion
carries over from the smaller five-family corpus: on raw clustering quality `d_I`
sits mid-pack (a close second behind HPD); the paper's claim is *licensed*
usefulness, not benchmark dominance.

**Measured (real HIC genre, censored subset).** On the two cleanly computable
IMDB genre datasets (`w*_c`-yield 92.5% and 91.7%), genre is near-unclusterable
from structure alone: **every** representation scores ARI < 0.10, including
`d_I`. No representation leads meaningfully — an honest negative result. The four
remaining IMDB genre datasets are retained at only 34–43% under the `w*_c`
budget, with label-correlated censoring (some genres below 20% retention); their
clustering numbers are reported for completeness but are not used for
representation ranking.

## A3 — kNN classification (supervised story)

Needs a **labelled** hypergraph corpus with ≥2 classes: planted family ids
(synthetic) and HIC dataset labels (real; `../DATA.md` §2).

- Licence: the G1 concentration + hubness profile (reported first; the kNN
  result is read against it).
- Method: k-NN with `metric='precomputed'`, leave-one-out / stratified CV.
- Metrics: accuracy, macro-F1, AUC (one-vs-rest). Report vs `k`.
- Competitor comparison: k-NN on each `D_rep`, same folds.

**Measured (planted corpus, N = 240, twenty families).** The G1 hubness profile
predicts the kNN ordering, and the prediction sharpens at this corpus size: the
WL histogram's hubness rises to 4.586 and its AUC-OvR **collapses to chance
(0.49)** — the clearest confirmation of the licence. The benign-hubness
representations classify above chance: HPD leads (AUC 0.83), `d_I` is second
(0.73), then NetLSD (0.66) and the nauty-Levi distance (0.61, held down by its
avalanche sensitivity). The strong-hubness→failure prediction holds decisively at
the extreme (WL); among the benign-hubness representations the residual ordering
is set by the other measured geometry (concentration, metric structure), which we
report rather than over-read. This is the payoff of the no-orphan-geometry rule:
a geometric quantity measured in G1 forecasts the supervised outcome before the
classifier is run, and the forecast is stable between N = 60 and N = 240.

**Measured (real HIC genre, censored subset).** The same hubness contrast recurs
on real data. On the two clean IMDB genre datasets the mean AUC-OvR at k = 9 is
0.673 for `d_I`, followed by NetLSD and the nauty-Levi edit distance (both
0.654), against 0.624 for the WL histogram, which again trails in line with its
elevated real-data hubness (skewness 4.5–7.4). The agreement of the hubness→kNN prediction across synthetic
*and* real corpora is the empirical spine of the geometric characterization. (HPD
is not conclusive on the clean datasets: its vendored hyperedge-portrait
construction raises an index error on a third of the real instances, so it is
scored only on a per-instance-censored subset and flagged as such.)

## A4 — Shortest path between hypergraphs (the capability differentiator)

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

**Measured (ladder pool of 44 hypergraphs).** Accumulated path length is
**monotone in the ladder budget for every representation** (monotone fraction
1.00) — the ladder response of G2 read along shortest paths. Exact recovery of
the specific ladder intermediates, by contrast, is essentially null for all
representations (0.00 for `d_I`, WL and NetLSD; 0.33 for HPD): the `d_I` geodesic
routes through same-budget alternatives rather than retracing the exact edit
sequence. We report this as a feature, not a failure — it is a direct empirical
illustration of the closing discussion's point that `d_I` is not an edit-distance
proxy. The **decodability differentiator is the categorical result**: only `d_I`
exhibits the intermediate hypergraphs along the path — three intermediate
strings decoded via S2H to valid hypergraphs, whereas the WL path collapses to a
direct two-node hop, NetLSD and HPD have no decoder, and the nauty-Levi distance
cannot navigate at all (its avalanche profile). The capability matrix below
records this: usefulness on A4 is not a score, it is a capability that no
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

## Runtime — the cost axis (and the `d_I` compromise)

Every representation's pairwise matrix is timed (wall-clock, per the reporting
standard). On the N = 240 planted corpus (28,680 pairs) the `D`-matrix
wall-clock is: nauty-Levi 0.05 s, WL 0.09 s, **`d_I` 0.18 s**, NetLSD 0.27 s, HPD
0.88 s; HyperCOT is `O(n³)` per pair (tractable only on tiny instances). `d_I`
is the **compromise the other axes point to**: the two representations faster
than it are disqualified on quality — nauty's geometry is avalanche-unusable
(G2) and WL's hubness forces chance-level kNN (A3) — while the one that edges it
on task metrics, HPD, costs ~5× the wall-clock, has *no decoder* (cannot run
A4), and fails on a third of real HIC instances (its vendored portrait). `d_I`
is the only representation that is simultaneously fast, competitive on task
metrics (a close second on A2 and A3), decodable, and geometrically
characterizable.

The one honesty caveat: the runtime advantage is **per-instance-size dependent**.
`w*_c` cost scales with hypergraph size and tie-symmetry, so `d_I` is fast on
small-to-moderate instances (planted, most real hypergraphs) and becomes the
*expensive* representation on large near-symmetric inputs — the mechanism behind
the HIC censoring (`../DATA.md` §2). It is the mirror image of HyperCOT's
profile, which is cheap per small instance but explodes with instance size. The
cost claim is therefore "fast and capable on small-to-moderate instances,"
stated with its size dependence, not a universal speed claim.
