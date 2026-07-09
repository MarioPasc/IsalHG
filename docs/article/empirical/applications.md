# Layer 2 — applications that exploit the stability theorem

**Status:** DRAFT (scoping 2026-07-08). Each application runs on the pairwise
matrix `D_I = {d_I(H_i,H_j)}` (and, for competitors, on `D_rep`). **None of these
exist in the IsalGraph paper** — MDS/clustering/kNN are its "future work",
shortest-path was an illustrative figure cut for page limits. This is the
paper's empirical novelty. Scope confirmed with the user 2026-07-08; **MDS is the
flagship** (tutor emphasis). The pipeline (pairwise distance → MDS → k-medoids →
kNN/dendrogram) is not novel *per se* — it ports the graph precedent of
Neuhaus & Bunke (2007) and Bunke & Riesen (2008) (`../RELATED_WORK.md`) to
hypergraphs under `d_I`; novelty is the substrate + the stability guarantee.

**No HGED here — the scale advantage (decided 2026-07-08).** These applications
validate usefulness on *task* metrics (ARI vs planted labels, accuracy/F1/AUC,
stress), **not** on HGED. So — unlike the Layer-1 correlation study
(`correlation.md`) — they are **not bounded by the exact-HGED ceiling**. Their
scale is gated only by `w*` (and competitor) wall-clock, measured in T-DQ3'. This
puts a real-world anchor (HIC, `../DATA.md` §3) back in scope for A1–A3 at a size
the correlation study cannot reach: run MDS/clustering/kNN on larger real
hypergraphs, report task metrics, and let the Layer-1 correlation (small, exact
HGED) supply the *why*. Competitors run the same HGED-free pipeline off their own
`D_rep`.

## A1 — Metric MDS (FLAGSHIP)

Goal: embed hypergraph space `(·, d_I)` into `R^D`; visualize similarity; report
the **estimated intrinsic dimension** as a headline result.

- Method: classical (Torgerson–Gower) MDS + SMACOF for the stress-minimizing
  configuration. Because `d_I` is a (generically) non-Euclidean edit metric, the
  Gram matrix `B` will have negative eigenvalues — **report PSD status per
  corpus** (`../theoretical/stability.md` §5). Theory frames the expectation:
  Bourgain (1985) guarantees `O(log N)` embedding distortion (MDS is justified),
  but Khot–Naor (2006) prove string-edit metrics need `(log d)^{1/2−o(1)}` L1
  distortion (so expect non-trivial residual) — cite both (`../RELATED_WORK.md`).
- **Dimension selection (PI note 2026-07, primary = cross-validation):** hold out
  a random subset of the `C(n,2)` dissimilarities, fit on the rest, predict held
  out, pick `D̂` minimizing out-of-sample error. Supporting: Mardia `P^(1)`,
  `P^(2)` goodness-of-fit ratios; negative-eigenvalue floor `λ_D ≫ |λ_min|`;
  parallel analysis. Deliverable: `D̂` for IsalHG vs each competitor — a lower
  faithful `D̂` argues the representation captures structure compactly.
- Metric: Kruskal stress-1 vs `D`; cross-validated reconstruction error;
  Shepard diagram (d_I vs embedded distance).
- Competitor comparison: same pipeline on `D_rep`; whose embedding has lower
  stress at matched `D`, and whose `D̂` is smaller.

## A2 — Unsupervised geometry (one story: clustering + hierarchy)

Corpus with **planted clusters** (families from a few seed motifs +
seed-stable perturbations ⇒ known membership + known intra/inter HGED).

- k-medoids (PAM) on `D_I`. Internal metrics: silhouette, Dunn, Davies–Bouldin.
  External (vs planted labels): Adjusted Rand Index, NMI.
- Agglomerative dendrogram on `D_I`. Metrics: cophenetic correlation,
  silhouette at the induced cut.
- Medoid (PROPOSAL A2) is the `k=1` degenerate — reported inline, not a section.
- Competitor comparison: same metrics on `D_rep`. The stability theorem predicts
  IsalHG clusters cleanest in the *sparse* regime (small `C(k,Δ)`); report
  metrics vs density to connect back to Theorem B.

## A3 — kNN classification (supervised story)

Needs a **labelled** hypergraph corpus with ≥2 classes (→ `../DATA.md` DQ3;
candidates: HIC 12-dataset origin labels, or a synthetic multi-motif corpus).

- Method: k-NN in `(·, d_I)`, leave-one-out / stratified CV.
- Metrics: accuracy, macro-F1, AUC (one-vs-rest). Report vs `k`.
- Competitor comparison: k-NN on `D_rep`.

## A4 — Shortest path between hypergraphs (the differentiator)

The path `H_A → H_B` of minimal accumulated `d_I` through a pool of
intermediates. The canonical-form competitors (nauty/bliss) **cannot** do this
meaningfully — their fingerprints are not edit-navigable (single edit ⇒ global
change; `../theoretical/stability.md` §3). IsalGraph showed this only as an
illustrative example (`d_GED = d_Lev = 5`, different intermediate sequences); we
make it **quantitative**: recovered-path length vs true HGED-geodesic length,
and intermediate-hypergraph plausibility. This is where "competitors cannot
compete" (PI 2026-07) is demonstrated, not just asserted.

## Corpora needed (→ `../DATA.md`)

| App | Corpus requirement |
|---|---|
| A1 MDS | any set of "related" hypergraphs; ideally exact/BP HGED for a Shepard cross-check |
| A2 clustering | planted-cluster synthetic (known membership) + one real anchor |
| A3 kNN | labelled real corpus, ≥2 classes |
| A4 path | two endpoints + intermediate pool |

## Competitor applicability (→ `../COMPETITORS.md`)

| App | WL / spectral / kernel (vector `D_rep`) | nauty/bliss canonical edit dist |
|---|---|---|
| A1 MDS | yes | yes (but unstable geometry) |
| A2 clustering | yes | yes (contrast) |
| A3 kNN | yes | yes |
| A4 path | degrades (not structured for geodesics) | **no** (differentiator) |
