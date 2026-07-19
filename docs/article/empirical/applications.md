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

**No HGED here — the scale decision (kept from v2).** These measurements
validate on *task* metrics (ARI vs planted labels, accuracy/F1/AUC, stress) and
on known perturbation budgets, **never** on the HGED oracle. Their scale is
gated only by `w*_c` (and competitor) wall-clock, so
the real anchor (HIC, `../DATA.md` §2) is in scope at sizes the exact oracle
could never reach. Competitors run the same pipeline off their own `D_rep`.

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

## G2 — Local sensitivity + ladder response (geometry, the smoothness evidence)

- **Sensitivity:** histograms of `s(e) = d_I(H, H⊕e)` over single structural
  edits (all Qin op types), per density regime and on the four design fixtures
  (Fano, STS(9), the cyclic C13 orbit, GQ(2,2)). The C13 fixture is the cheap
  partial system, not a true STS(13): `s(e)` needs one `w*_c` per edit, and a
  true STS(13) costs ~44 s per `w*_c` — infeasible at histogram scale.
  Predictions (three regimes by tie coherence) in
  `../theoretical/stability.md` §4.2; falsification target stated there.
- **Ladder:** `d_I(H_0, H_t)` vs known accumulated Qin budget `t` along
  perturbation ladders; monotone near-linear response is the smoothness
  evidence for neighbourhood methods.
- **Contrast:** the same `s(e)` measurement on the nauty-Levi canonical-string
  distance. Expected: avalanche-everywhere — the measured demonstration that
  iso-only canonical labelling yields no navigable geometry
  (`../COMPETITORS.md` §3), replacing assertion with a figure.
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

## A3 — kNN classification (supervised story)

Needs a **labelled** hypergraph corpus with ≥2 classes: planted family ids
(synthetic) and HIC dataset labels (real; `../DATA.md` §2).

- Licence: the G1 concentration + hubness profile (reported first; the kNN
  result is read against it).
- Method: k-NN with `metric='precomputed'`, leave-one-out / stratified CV.
- Metrics: accuracy, macro-F1, AUC (one-vs-rest). Report vs `k`.
- Competitor comparison: k-NN on each `D_rep`, same folds.

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

## Corpora needed (→ `../DATA.md`)

| Measurement | Corpus requirement |
|---|---|
| G1/G2 profiles | every corpus (profiles are per-corpus preambles); designs for the sensitivity fixtures |
| A1 MDS | planted-family synthetic + real anchor (HIC, gated) |
| A2 clustering | planted families (known membership) + real anchor |
| A3 kNN | labelled: planted family ids + HIC dataset labels |
| A4 path | ladder endpoints + intermediate pool with distractors |

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
