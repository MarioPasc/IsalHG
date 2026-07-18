# IsalHG journal article — scope proposal

**Status:** ACTIVE scope, v3 (2026-07-18 rescope). This document supersedes the
*paper scope* of `docs/preprint/PROPOSAL.md` (the iso-benchmark validation
methodology), which is retained as the spec of the current codebase and as the
preprint's methodology. The engineering docs (`docs/engineering/CODE_DESIGN.md`,
`docs/engineering/DEVELOPMENT.md`) still describe the code as built. The v3
rescope replaces the earlier framing in which HGED-faithfulness (Theorem B) was
a load-bearing pillar; the rationale is in §1 and the decision record in
`DEVELOPMENT/DECISIONS.md`.

**Target venue:** *Information Sciences* (Elsevier, ISSN 0020-0255). Data-science
oriented, applied-methods CS journal.

**Point-by-point breakdown.** `theoretical/` holds the foundation, the geometry,
and the source material for the closing discussion (`stability.md` §1
completeness→metric; `geometry.md` the geometric characterization; `stability.md`
§2–4 the HGED-relation analysis the discussion draws on). `empirical/` holds the
experiments (`applications.md` the geometry measurement + the applications;
`correlation.md` the discussion evidence: the single HGED-relation figure and
the information-content comparison). `H2S_S2H.md` is the self-contained
algorithm specification (S2H interpreter, H2S encoder) the methods section is
written from. Each subfolder's `README.md` maps to the spine in §0.

**Self-contained for hypergraphs (the siblings are under review, not
published).** The IsalGraph sibling established, on graphs, the completeness
theorem + metric corollary (proved) and an HGED-correlation + information-content
result (measured). It is under review and **not citable as published prior
work**, so this paper is self-contained: we re-prove completeness and the metric
corollary for hypergraphs (*non-trivially* — hypergraph completeness needs the
tie-complete encoder; the greedy one is provably incomplete), and we re-measure
what we still use (information content). This is also an advantage: we can
leverage IsalGraph's ideas and lessons (raw Levenshtein works; fixed-width bit
accounting is reviewer-tested) without being bound by its framing. IsalHG's
genuinely new contributions — in neither sibling — are: (a) the **geometric
characterization** of the induced metric space; (b) the **geometry-licensed
applications**; (c) the honest **relation-to-HGED analysis** (envelope +
impossibility + mechanisms) replacing the naive proxy claim.

---

## 0. Premise and thesis

*This document, and the whole `docs/article/` knowledge base, is written to read
as the article — a premise, a foundation, and a reasoned build-up. The
engineering that backs it (implement, test, run, optimise) lives separately in
`DEVELOPMENT/`; this is the reasoning, not the task log.*

**Premise.** *A hypergraph is a word.* The IsalHG instruction language encodes
any connected hypergraph as a string over `Σ_HG`, and the complete canonical
form `w*_c` makes that encoding a fingerprint: `w*_c(H) = w*_c(H') ⇔ H ≅ H'`
(Theorem A — `w*_c` is a **complete isomorphism invariant**). Levenshtein
distance on these words is therefore a **metric on isomorphism classes** of
hypergraphs, `d_I` (Corollary A: identity of indiscernibles from completeness;
symmetry and triangle inequality from `d_Lev`).

**Thesis (characterize → exploit).** The article **characterizes the geometry**
of the metric space `(Σ_HG*, d_Lev)` restricted to the image of `w*_c` — its
intrinsic dimension, its deviation from Euclidean geometry, its concentration
and neighbourhood structure, its local sensitivity to structural edits — and
then **exploits that geometry**: every application (MDS, k-medoids + dendrogram,
kNN, shortest path) is licensed by a measured geometric property and scored on
its own task metric against competing hypergraph representations. Usefulness is
the claim; the geometric characterization is both a contribution in itself (no
hypergraph-dissimilarity space has been characterized this way) and the
instrument that makes the applications principled rather than ad hoc.

**What the article does *not* claim.** `d_I` is **not** presented as a proxy or
estimator for hypergraph edit distance. A bi-Lipschitz equivalence
`c·HGED ≤ d_I ≤ C·HGED` is provably out of reach — the lower direction fails for
canonical-form/WL-type representations generically, and our own analysis shows
the clean upper Lipschitz bound fails in adversarial layouts (drift) and near
symmetric inputs (avalanche). The paper states what *is* true (a metric; an
unconditional envelope; named, measured deviation mechanisms), shows one
honest correlation figure, and draws the methodological conclusion: **usefulness
must be, and is, established directly on task metrics** — which is exactly the
program of this paper. The former "faithfulness capstone" framing is retired
(v3); Theorem B's surviving content lives in the closing discussion (§5).

**Narrative spine (the paper's section logic); each step motivated by the
previous.**

0. **Foundation.** `w*_c` is a complete invariant ⇒ `d_I` is a metric on
   isomorphism classes. Stated formally (Theorem A + Corollary A).
   *`theoretical/stability.md` §1; algorithms in `H2S_S2H.md`.*
1. **Compactness.** The word is short: fixed-width-code information content vs
   an incidence-list construction model, compression ratio + Wilcoxon. A short
   subsection substantiating the premise ("a hypergraph is a *compact* word").
   *`empirical/correlation.md` §Information content.*
2. **Geometry (characterize).** The measured shape of the space: non-Euclidean
   mass `ν` + Gram spectrum, intrinsic dimension `D̂` (CV-MDS), distortion
   (stress, Shepard), concentration + hubness, and the local sensitivity +
   ladder profile. Rule: **no orphan geometry** — every invariant measured is
   consumed by an application licence or a competitor contrast.
   *`theoretical/geometry.md`; measured via the A1 pipeline
   (`empirical/applications.md`).*
3. **Usefulness (exploit).** Four applications, each citing the geometric
   property that licenses it, each scored on task metrics against the
   competitor representations, plus the capability matrix (what each
   representation can and cannot do). *`empirical/applications.md`;
   `COMPETITORS.md`.*
4. **Discussion (relation to HGED + limits).** Two short propositions (length
   lemma; unconditional envelope `d_I ≤ m(1+kn)·HGED`), the impossibility of a
   bi-Lipschitz proxy for any complete invariant (literature + our mechanisms:
   drift, avalanche), and **one** exact-HGED correlation figure (ours only) as
   an honest empirical characterization. Future work.
   *`theoretical/stability.md` §2–4; `empirical/correlation.md`.*

**Why this order.** The paper leads with what is proved (the metric), then with
what is measured (the geometry), then with what the measurement buys
(applications with competitors). The HGED relation comes last because it is a
*limit statement*, not a pillar: leading with it — as earlier drafts did —
aimed the paper at its weakest link and invited the reviewer reading "this is
an HGED approximation paper" that we cannot defend. The `§`-numbering below is
this scoping doc's layout, **not** the paper's section order.

---

## 1. The two pivots (why this is not the preprint, and not the v2 scope)

**Pivot 1 — away from the iso-benchmark (2026-07).** The preprint
(`docs/preprint/`) framed IsalHG as a native hypergraph isomorphism test
benchmarked on wall-clock against nauty / Traces / bliss on the Levi reduction.
That framing loses: the C++ core is competitive but does not beat mature
graph-iso engines on speed. Speed is not the story; the string *representation*
is.

**Pivot 2 — away from the HGED-proxy framing (2026-07-18, v3).** The v2 scope
made HGED-faithfulness the capstone: a correlation study, a density sweep
validating a Lipschitz bound `d_I ≤ C(k,Δ)·HGED` (Theorem B), and an
HGED-correlation head-to-head against competitors. The stability analysis then
showed the clean bound is **conditional on five hypotheses, two of which fail
generically** (pointer-run drift in adversarial layouts; tie/seed avalanche near
symmetry). Continuing to build the paper on that axis would overstate what the
theory delivers and re-import the proxy claim we cannot make. The v3 scope
inverts the dependency: the geometry and the applications carry the paper on
their own (HGED-free) evidence, and the HGED relation is compressed into the
closing discussion, where its honest content — envelope, impossibility,
mechanisms, one figure — *strengthens* the paper instead of gating it.

## 2. Geometry — the characterization (pillar 1)

*Reasoning in `theoretical/geometry.md`; measured through the A1 (MDS) pipeline
and the corpus distance matrices (`empirical/applications.md`).*

The measured invariants, each with its consumer (the no-orphan-geometry rule):

| Invariant | What it is | Consumed by |
|---|---|---|
| Non-Euclidean mass `ν` + Gram spectrum | `Σ_{λ<0}|λ| / Σ|λ|` of the double-centred Gram matrix (Schoenberg) | licenses k-medoids/PAM over centroid methods; decides classical-MDS regime (A1) |
| Intrinsic dimension `D̂` | cross-validated MDS dimension selection (primary); Mardia ratios, eigenvalue floor (supporting) | headline descriptor; sets the MDS target dimension (A1); per-representation `D̂` is a competitor axis |
| Distortion | Kruskal stress-1 at matched `D`, Shepard diagram, CV reconstruction error | qualifies every MDS map (A1); Bourgain upper / Khot–Naor lower brackets cited |
| Concentration + hubness | pairwise-distance histogram, diameter/median ratio, `k`-occurrence skewness (Radovanović et al. 2010) | precondition report for kNN (A3) |
| Local sensitivity profile | `s(e) = d_I(H, H⊕e)` histograms per structural edit type | licenses neighbourhood methods; the measured contrast vs nauty-edit (whose profile is avalanche-everywhere) |
| Ladder response | `d_I` vs known accumulated edit budget `t` (perturbation ladders) | monotone-response evidence at scale; scores A4's path recovery |

The last two are HGED-free by construction (the edit budget is known because we
apply the edits); they were formerly misfiled under the HGED-validation layer.

## 3. Usefulness — the applications (pillar 2)

*Detail in `empirical/applications.md`; competitor policy in `COMPETITORS.md`.*

Four applications, all driven by the same pairwise matrix `D_I` (competitors:
their own `D_rep`), each licensed by a measured geometric property:

| # | Application | Method | Licensed by | Task metric(s) |
|---|---|---|---|---|
| A1 | Similarity map + geometry measurement | classical MDS + SMACOF | distortion brackets; `D̂` selects the dimension | stress-1, CV reconstruction error (also *produces* `ν`, `D̂`) |
| A2 | Unsupervised structure | k-medoids (PAM) + agglomerative dendrogram | `ν` (medoids need only a metric); concentration | silhouette, Dunn, Davies–Bouldin; ARI/NMI vs planted labels; cophenetic corr. |
| A3 | Classification | kNN, `metric='precomputed'` | concentration + hubness profile | accuracy, macro-F1, AUC vs `k` |
| A4 | Hypergraph-to-hypergraph path | shortest path through an intermediate pool in `(·, d_I)` | local sensitivity profile; closed alphabet (decodability) | HGED-free: endpoints from perturbation ladders (known budget `t`); path-length monotonicity vs `t`; decoded intermediates (S2H) shown |

The medoid-representative use (v2's A2) is the `k=1` degenerate of PAM,
reported inline. A4 is the capability differentiator: canonical-form
competitors cannot navigate their fingerprint space (a single structural edit
relabels the whole string — the measured avalanche profile), and vector
fingerprints have no decoder — no competitor can exhibit the intermediate
*hypergraphs* along a path. Every intermediate string on an edit path decodes
to an actual hypergraph because the alphabet is closed (S2H never rejects).

**Competitors** (full rationale in `COMPETITORS.md`): hypergraph-WL histogram,
NetLSD on the Levi expansion (full member), HyperCOT (run where its `O(n³)`/pair
cost is feasible, its scale limit stated), Hyperedge Portrait Divergence, and
the nauty-Levi canonical-string edit distance as the *contrast* baseline. The
comparison axes are task metrics, per-representation geometry (`D̂`, `ν`), and
the capability matrix — **not** HGED correlation.

## 4. Compactness — information content in bits

A short subsection where the representation is introduced, substantiating "a
hypergraph is a *compact* word". Estimator ported from the sibling (uniform
fixed-width code, reviewer-tested; *not* Shannon self-information, *not*
compressed length): `B_IsalHG(w) = |w|·log2|Σ_HG(k)|` vs an incidence-list
construction-model bit count; compression ratio `r > 1` favours IsalHG;
one-sided Wilcoxon signed-rank. Detail in `empirical/correlation.md`
§Information content. An entropy-coded refinement is optional future work, not
load-bearing.

## 5. Discussion — relation to HGED (the retired capstone, compressed)

*Source material: `theoretical/stability.md` §2–4 and
`theoretical/stability_reformulations.md`; the figure's methodology in
`empirical/correlation.md`.*

What the discussion states, in order:

1. **Proposition (length).** `|w*_c| ≤ m(1+kn)` — the string is linearly
   bounded in incidence mass.
2. **Proposition (envelope).** `d_I ≤ m(1+kn)·HGED` unconditionally — an
   envelope, presented as such, *not* a stability result.
3. **Impossibility (prose, cited).** No bi-Lipschitz relation to HGED is
   achievable: the lower direction fails generically for complete
   canonical-form/WL-type invariants (FSW-GNN, LoG 2025; Chen et al. 2023), and
   the upper Lipschitz direction fails in the raw metric through two named,
   measured mechanisms — pointer-run **drift** (layout-dependent, `Θ(n)` in
   adversarial layouts) and tie/seed **avalanche** (near-symmetric inputs; the
   price *any* complete invariant pays, since deterministic symmetry breaking
   is discontinuous exactly where objects are nearly symmetric). Stability by
   construction (WL vectors, spectra, transport couplings) is bought by giving
   up completeness — IsalHG sits on the other side of that frontier.
4. **One figure.** Spearman ρ between `d_I` and exact HGED on a small connected
   corpus (ours only — no density sweep, no competitor head-to-head): the
   honest empirical footprint of the relation, offered as characterization,
   not claim.
5. **Consequence.** Because no bound can certify task usefulness, usefulness
   was established directly (§§2–3) — the discussion closes the loop on the
   paper's own methodology.

This is the surviving role of Theorem B. The conditional bound (`B-cond`, five
hypotheses), the density-sweep validation, and the HGED head-to-head are out of
the article's scope; their analysis is preserved in `theoretical/` for the
record and for follow-up work.

## 6. Open scope questions

- OQ-A [open]. Exact-HGED mini-corpus for the §5 figure: size and (n, m)
  ceiling under the HPC-parallel exact oracle; connected-domain generators
  gate it. → `DATA.md`, `DEVELOPMENT/`.
- OQ-B [open]. The real-anchor gate: is `w*_c` computable in acceptable time on
  HIC-scale instances? A single measurement decides whether the applications'
  real anchor is HIC or falls back to synthetic + small designs. → `DATA.md`
  DQ3'.
- OQ-C [open]. kNN label source confirmed as HIC dataset labels (real) +
  planted family ids (synthetic); final choice of which HIC datasets clear the
  OQ-B gate.
- OQ-D [resolved, v3]. Distance = **raw Levenshtein** primary (sibling
  precedent; matches the frozen `w*_c` + `d_Lev` decisions).
  Length-normalized / token-weighted variants: one ablation table at most.
- OQ-E [resolved, v3]. Applications = the four of §3; six-application sprawl
  cut. Medoid folds into A2; interpolation beyond A4's decoded intermediates
  is future work.
- OQ-F [resolved, v3; PI-ratified 2026-07-18]. Mutual information `I(HGED; d)`
  is dropped along with the HGED head-to-head axis (it existed to compare
  competitors on that axis). The §5 figure reports ρ only. Decision record:
  `DEVELOPMENT/DECISIONS.md` (D-ART2).
