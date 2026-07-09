# IsalHG journal article — scope proposal

**Status:** DRAFT, filled collaboratively during the scoping session opened
2026-07-08. This document supersedes the *paper scope* of `docs/preprint/PROPOSAL.md`
(the iso-benchmark validation methodology), which is retained as the spec of
the current codebase and as the preprint's methodology. The engineering docs
(`docs/engineering/CODE_DESIGN.md`, `docs/engineering/DEVELOPMENT.md`) still describe the code as
built; they will be re-oriented in a later pass once this scope is locked.

**Target venue:** *Information Sciences* (Elsevier, ISSN 0020-0255). Data-science
oriented, applied-methods CS journal.

**Point-by-point breakdown:** `theoretical/` (the theorems — completeness,
metric, **stability**) and `empirical/` (the experiments that test them —
controlled correlation/info-content, then applications). Each subfolder's
`README.md` maps back to the numbered points below. The paper's logic, per PI
2026-07: *theoretical proof → controlled empirical validation → applications
that exploit the theorem*.

**Precedent:** the IsalGraph sibling paper
(`/media/.../isalgraph/article/69b82c5859ed47c5468ca199`) already established, on
graphs, the correlation between Levenshtein-of-canonical-string and edit
distance (Spearman ρ up to 0.934) and a bits-based information-content win
(median compression 1.45–1.89×). It **proved completeness + the metric
corollary** but stated locality/stability as an *empirical claim only, with no
bound*. IsalHG's delta: (a) hypergraphs, (b) **prove the stability bound**,
(c) exploit it in applications the sibling left as future work.

---

## 1. The pivot (why this is not the preprint)

The preprint (`/media/.../preprint`) framed IsalHG as a native hypergraph
isomorphism test benchmarked on wall-clock against nauty / Traces / bliss on
the Levi reduction. **That framing loses**: the C++ port is competitive but
does not beat mature graph-iso engines on random hypergraphs (PI email
2026-06/07). Speed is not the story.

**New thesis.** The canonical H2S string `w*(H)` embeds every hypergraph into
the discrete metric space `(Σ_HG*, d)` where `d` is a string distance
(Levenshtein). Because `w*` is isomorphism-invariant, `d(w*(H_i), w*(H_j))` is
an isomorphism-invariant *dissimilarity* between hypergraphs. The paper's claim
is that this dissimilarity is a **useful, structure-faithful metric** on
hypergraph space — faithful enough to drive standard unsupervised and
supervised pipelines (MDS, medoids, clustering, kNN, dendrograms, shortest
path) — and competitive with, or complementary to, the fingerprint-distances
induced by the competing representations.

## 2. Central empirical claim (the load-bearing experiment)

For a corpus of hypergraphs with a computable ground-truth structural distance
(HyperGraph Edit Distance, HGED):

- Build `D_est = { d(w*(H_i), w*(H_j)) }` for IsalHG and
  `D_est = { d(fp(H_i), fp(H_j)) }` for each competitor `fp`.
- Build `D_true = { HGED(H_i, H_j) }`.
- Report the **correlation** (Spearman ρ / Pearson r on the scatter
  `HGED vs d_est`) and the **mutual information** `I(HGED; d_est)`.
- Higher correlation / MI ⇒ the representation's geometry is more faithful to
  true structural distance. This is the head-to-head metric against competitors.

The correlation is not the contribution — the **stability theorem**
(`theoretical/stability.md`, Theorem B: `d_I(H,H') ≤ C(k,Δ)·HGED(H,H')`) is what
*explains* it, and its `Δ`-dependence predicts that ρ decays with density. The
sibling's own ρ trend (0.934 at mean-degree 3.07 → 0.349 at 10.70) is the
signature of that `C(k,Δ)`. MI (`I(HGED; d)`) is reported alongside ρ — the
sibling reported ρ only, so MI is a novel second axis.

**Open:** HGED definition + oracle tiering (exact small-scale / BP-HGED /
perturbation-ladder). Resolved in `empirical/correlation.md` (§HGED); corpus in
DATA.md.

## 3. Information content angle (secondary competitive axis)

The preprint measured *fingerprint length in bytes*. PI (2026-07): measure
**information content in bits**. The sibling's estimator (adopted directly) is a
**uniform fixed-width code**, not Shannon self-information and not compressed
length: `B_IsalHG(w) = |w|·log2|Σ_HG(k)|`, compared against a competitor
*construction-model* bit count (incidence-list encoding), via a compression
ratio `r>1` and a one-sided Wilcoxon signed-rank test. This sidesteps the
"distribution model" problem my first framing raised. Detail in
`empirical/correlation.md` §Information content. Likely IsalHG win axis.

## 4. Applications (the "many lightweight applications" plan)

Each application is a subsection with its own natural performance metric. All
run off the same distance matrix `D_est`; competitors run the same pipeline off
their own `D_est`. **The applications do not use HGED** (decision 2026-07-08) —
they validate on task metrics, so — unlike §2's correlation study — they are not
bound by the exact-HGED ceiling and can run on larger real hypergraphs, gated
only by `w*` wall-clock (DATA.md §3, DQ3'). HGED is confined to §2 (validating
the theorem) and the stability theorem itself.

| # | Application | Method | Performance metric(s) |
|---|---|---|---|
| A1 | Visual similarity map | Metric MDS (classical / SMACOF) | Stress (Kruskal), plus dimension selection — see §5 |
| A2 | Representative hypergraph | Medoid of a set | qualitative + distance-to-medoid |
| A3 | Unsupervised grouping | k-medoids (PAM) | Silhouette, Dunn index, Davies-Bouldin |
| A4 | Hypergraph-to-hypergraph path | Shortest path in the string metric | (competitors largely cannot do this — differentiator) |
| A5 | Hierarchy | Dendrogram (agglomerative) | Cophenetic correlation, silhouette |
| A6 | Classification | k-NN in the metric | Accuracy, F1, AUC |

## 5. MDS intrinsic-dimension selection (PI note 2026-07)

Classical (Torgerson–Gower) MDS: double-center `D^(2)` → `B`; coordinates from
positive eigenpairs. Because the string metric is **not** guaranteed Euclidean,
`B` will generally have negative eigenvalues (Schoenberg). Dimension selection:

- **Chosen primary:** cross-validation on held-out dissimilarities (PI's
  preference) → reports an estimated intrinsic dimension.
- Secondary/supporting: Mardia `P^(1)`, `P^(2)` goodness-of-fit ratios;
  negative-eigenvalue floor (`λ_D ≫ |λ_min|`); parallel analysis.
- Report whether `B` is PSD per corpus (decides exact vs approximate regime).

## 6. Algorithm prerequisite (must land before experiments)

PI directive 2026-07: improve H2S **seed-node selection** to shrink the initial
set, preserving iso-invariance:
1. If labelled, restrict to nodes of maximal label.
2. Among those, restrict to nodes of maximal degree.
3. Among those, compute the decreasing-sorted neighbour-degree list; keep the
   nodes whose list is lexicographically maximal.
Verify (a) iso-invariance of `w*` is preserved, (b) wall-clock drops. This is a
refinement of `core/structural_tuples.py::max_xi_nodes` seeding.

## 7. Open scope questions (to resolve this session)

- OQ1. Corpus for the HGED-correlation study — size regime, labelled vs not,
  synthetic vs real. → DATA.md.
- OQ2. Which competitors and their fingerprint→distance maps. → COMPETITORS.md.
- OQ3. **[resolving]** HGED oracle tiering — exact (A*/ILP, n≲12) + BP-HGED
  (Riesen–Bunke bipartite, mid-scale) + perturbation-ladder (scale). See
  `empirical/correlation.md`.
- OQ4. **[resolved]** Distance = **raw Levenshtein** primary (sibling hit
  ρ=0.934 raw; matches precedent, enables direct comparison). Length-normalized
  and token-aware costs demoted to a single ablation table.
- OQ5. **[resolved]** Information-content estimator = fixed-width code + Wilcoxon
  (§3), ported from the sibling.
- OQ8. **[new, blocking]** Completeness of `w*` for IsalHG is still a
  *conjecture* (unlike the sibling, which proved it). The "metric space" claim is
  contingent on it — prove it or make the completeness section empirically
  airtight. See `theoretical/stability.md` §1.
- OQ6. Which applications become full sections vs a single "capabilities"
  figure. Six may be too many for one paper.
- OQ7. Classification (A6): what is the label? Requires a labelled hypergraph
  corpus with class structure.
