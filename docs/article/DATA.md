# IsalHG journal article — data plan

**Status:** DRAFT (scoping session 2026-07-08). Companion to
`docs/article/PROPOSAL.md`. Supersedes the *paper* data scope of `docs/preprint/DATA.md`
(the iso-benchmark cohort spec), which remains the authoritative record of what
the current data layer implements. Reuse from that cohort is expected; this
document records only what the metric-space paper needs.

The paper needs data for **three distinct purposes**, each with different
constraints:

## 1. HGED-correlation corpus (the load-bearing experiment)

Requirement: a set of hypergraphs on which a ground-truth structural distance
(HGED) is *computable*. HGED is NP-hard in general, so this pins the size.

- Size regime: bounded by exact-HGED cost — but this runs on **HPC with high
  parallelism**, so the ceiling is larger than the sibling's ≤12 (T-M2 benchmarks
  where exact HGED falls over). **Open:** target |corpus| and max (n, m). Pairwise
  scales O(N²) in HGED calls, which the HPC also parallelizes.
- Composition: should span a controlled range of structural similarity so the
  `HGED vs d_est` scatter is populated across its whole range — not just near-0
  (isomorphic) and near-max (unrelated). Candidate generators: perturbation
  ladders (apply k random edge/vertex edits to a seed H, so HGED ≤ k is known
  by construction — gives a *supervised* distance axis for free).
- Labelled vs unlabelled: run both; labelled exercises the new seed-selection
  step (PROPOSAL §6) and the label-aware distance.
- **Open:** is a perturbation-ladder (known upper-bound HGED) acceptable as the
  ground truth, or do we need exact HGED via an ILP/A* solver on a genuinely
  independent corpus?

## 2. Application corpora (per §4 of PROPOSAL)

### ⚠ Critical design constraint — classes must be non-isomorphic

The obvious shortcut (take STS iso-class representatives, generate `permute()`
copies as class members) is **invalid for classification/clustering**. Permuted
copies are *isomorphic*, so `w*` is identical and `d_I = 0` within class by
construction. Any clustering/kNN on such a corpus scores perfectly for a trivial
reason (it re-tests iso-invariance, §1's job) and says nothing about the metric
*geometry*. **Class members must be non-isomorphic but structurally coherent.**
Permuted copies are retained only as (a) the `HGED=0` anchor of the correlation
scatter and (b) an invariance sanity check.

### The planted-family corpus (serves A1, A2, and A3 from one generator)

A synthetic generator: `F` seed motifs; each family = a seed + `r` independent
**seed-stable perturbations** (each a few random incidence/edge edits that do
*not* flip the top-`ξ` seed — `../theoretical/stability.md` §3). Yields:
- non-isomorphic within-family members at small, controllable HGED;
- known family membership ⇒ **class label for A3 (kNN)** and **planted labels
  for A2** (ARI/NMI vs planted; silhouette/Dunn/DB internal);
- small `n` ⇒ exact/BP HGED feasible, so within/between-family HGED is known;
- a direct tie to Theorem B: within-family (seed-stable, small `C(k,Δ)`) should
  cluster tightly; the clustering quality vs density *is* a Theorem-B readout.
This is **new code** (`datasets/synthetic/planted_families.py`) — the cohort has
no equivalent. Seeds: the design fixtures already shipped (Fano n=7, STS(9) n=9,
STS(13) n=13, GQ(2,2) n=15) plus SageMath PG(2,q) small designs.

- A4 shortest path: any two endpoint hypergraphs + a pool of intermediates
  (reuse the planted-family pool).

### Cohort survey verdict (2026-07-08)

A survey of the existing cohort (`docs/preprint/DATA.md`) found **no ready corpus with
all three of: n ≤ 15, whole-hypergraph class label, ≥2 instances/class.**
Small-instance sources (Kaski–Östergård STS n=13/15 3-uniform; design fixtures
n=7–15; LLM4Hypergraph n≤19) exist but give 1 instance per iso-class or
pair-level labels only. Hence the planted-family generator above is required.

## 3. Real-world anchor (credibility)

Survey result: the **HIC atlas (12 datasets)** is the only cohort member with
genuine whole-hypergraph class labels *and* many instances/class (e.g.
IMDB→genre, Steam→category), Apache-2.0, `github.com/iMoonLab/HIC`. **But** its
instances are real networks (n in the hundreds–thousands): HGED is infeasible,
and — the sharper risk — **IsalHG's canonical string may not scale to that
size** given the backtracking avalanche on large/symmetric inputs
(`docs/engineering/DEVELOPMENT.md` open Q1). **HGED being infeasible on HIC no
longer matters** (decision 2026-07-08): the applications are HGED-free, so HIC is
a full at-scale anchor for **both** unsupervised (MDS/k-medoids on `d_I`) **and**
supervised (kNN on genre labels) demos — the *only* remaining gate is whether
`w*` (post T-M0 + C++) is computable at HIC's size (T-DQ3'). ARB / XGI-DATA /
Hypergraphx entries are each **one giant network** — no set of instances to
classify — so unsuitable for A1–A3.

**Honest scope note (two constraints, now separated).** The **Layer-1
correlation** study is bounded by exact HGED — small–medium `n`, though HPC
parallelism raises the ceiling past 10 (`../empirical/correlation.md` §HGED). The
**Layer-2 applications** are HGED-free, so their scale is bounded only by `w*`
(and competitor) wall-clock — they can run on **larger** real hypergraphs than
the correlation corpus. So the paper is no longer strictly a "small hypergraph"
story: the *validation* is small (HGED-bound), the *applications* can be larger
(w*-bound, T-DQ3' decides). If HIC's `w*` does not scale, applications fall back
to the synthetic planted-family corpus + small real designs.

**Open (DQ3'):** measure whether `w*` (post seed-optimization, C++) is
computable in seconds on a HIC IMDB instance. That single measurement decides
whether a real anchor is in scope.

## 4. Reuse from the existing data layer

The current `isalhg.datasets` layer (exhaustive_small, permute-based iso pairs,
STS/design fixtures) is directly reusable for the correlation corpus and the
synthetic application corpora. The perturbation-ladder generator (known-HGED)
is **new** and needs a `datasets/synthetic/` module. → track in engineering docs
once scope locks.

## 5. Open data questions

- DQ1. Corpus size + (n, m) ceiling for computable exact HGED (§1). Empirical:
  benchmark A* HGED on the HPC parallel regime across n = 8, 12, 16, 20, … to
  find where the exact oracle actually falls over (no longer assume ≤12).
- DQ2. **[resolving]** Both — exact HGED (small ground truth) + perturbation
  ladder (scale, upper bound), cross-checked by BP-HGED (`../empirical/
  correlation.md`).
- DQ3. **[resolved]** No cohort corpus fits labelled small-instance
  classification. Use the **planted-family synthetic generator** (§2) for
  A1/A2/A3; class = family. Real anchor (HIC) is secondary and scaling-gated.
- DQ3'. **[new, blocking the real anchor]** Measure whether `w*` is computable
  in seconds on a HIC IMDB instance (post seed-opt + C++). Decides real-anchor
  scope (§3).
- DQ4. **[resolved]** Two corpora: (i) small synthetic + exact HGED for the
  Layer-1 correlation study; (ii) the planted-family corpus for Layer-2
  applications. They differ in purpose and cannot be merged (correlation needs
  exact HGED ⇒ tiny; applications need planted structure ⇒ family design).
