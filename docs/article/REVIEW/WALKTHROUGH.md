# IsalHG metric-space article — a reader's walkthrough

**Purpose.** A plain-language pass through the finished article for an
unfamiliar reader: which studies are included, why, what each measures, how,
and the outcomes — followed by a straight publishability assessment. Written
from the v3 scope (`docs/article/PROPOSAL.md`, characterize → exploit).

**Data provenance.** Every quantitative claim below traces to a result file on
the results drive
(`/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/`, indexed by
`RESULTS_MANIFEST.md`). The body — geometry, MDS, clustering, kNN, bits — is
measured on **one primary corpus**: 17 known-design hypergraph families × 5
members = **85 items**, arities 3/4/5, across **27 seeds**, with 95% BCa
bootstrap confidence intervals and Holm-corrected one-sided Wilcoxon tests
(`T-M7d/stats/stratum_a_stats.json`). The sensitivity/ladder profiles and the
shortest-path study are design-seeded (`T-M7q/`); the edit-distance correlation
figure and the compactness bits study are frozen (`T-M5a/`). This supersedes an
earlier point-estimate draft measured on a single random-seed corpus with no
confidence intervals; where a number here disagrees with that draft, the number
here is the one to trust.

This is author-facing prep, not article prose and not a ledger task.

---

## Part I — The premise (everything hangs off this)

**"A hypergraph is a word."**

IsalHG has a small virtual machine — a circular doubly-linked list (CDLL) of
vertices plus `k` pointers — and a five-token instruction alphabet `Σ_HG`:

- `V` — add a hyperedge over some existing + some new vertices,
- `C` — add a hyperedge over existing vertices,
- `P` / `N` — move a pointer forward / back one step,
- `W` — no-op (padding / alphabet closure).

Feed the machine a string and it builds a hypergraph (**S2H**). Take a
hypergraph and an encoder (**H2S**) walks it back into a string. The alphabet is
*closed*: every well-formed string decodes to a valid hypergraph; S2H never
rejects.

The move that makes this a research object rather than a serialization format:
for each hypergraph one computes a **canonical** string `w*_c(H)` — the
shortlex-minimum over an isomorphism-invariant set of starting vertices, with a
*tie-complete* branching search so it is fixed by the isomorphism class alone.
Two hypergraphs are isomorphic **iff** their canonical strings (plus a
seed-label prefix `F(H) = (ℓ_V(seed), w*_c(H))`) are equal. That is
**Theorem A**.

With that, one line does all the work:

```
d_I(H, H') = d_Lev( w*_c(H), w*_c(H') )
```

Raw Levenshtein distance on the canonical strings. Because `w*_c` is a
*complete* invariant, `d_I` satisfies identity of indiscernibles
(`d_I = 0 ⇔ isomorphic`); symmetry and the triangle inequality come free from
Levenshtein. So **`d_I` is a metric on isomorphism classes of connected
hypergraphs** (Corollary A). Hypergraphs are now embedded, exactly and without
loss, into a metric space.

The metric comes in two members of one family. On unlabelled (structural)
inputs the alphabet carries a trivial vocabulary and the metric is `d_I^⊥`; on
labelled inputs (real data with vertex/edge labels) it is `d_I^Σ`. Same
construction, different domain — the synthetic body uses `d_I^⊥`, the real-data
cross-check uses `d_I^Σ`, and the two are read as separate objects rather than
one continuous series.

The rest of the paper answers one question: *now that hypergraphs live in a
metric space, what does that space look like, and what can you do with it?* The
spine is **foundation → compactness → geometry → usefulness → discussion**.

---

## Part II — The five studies, in reading order

### 1. Foundation — "it's really a metric" (Theorem A + Corollary A)

**What / why.** The non-negotiable core. If `w*_c` were not complete, `d_I`
would only be a pseudometric and every downstream application would rest on
sand.

**How.** Two halves:
- **Soundness** (`w*_c` equal ⇒ isomorphic): proved unconditionally from the
  round-trip property, for *every* encoder variant.
- **Completeness** (isomorphic ⇒ `w*_c` equal): the genuinely-new-for-hypergraphs
  part. It holds **only for the tie-complete encoder**. The cheaper greedy
  encoders are *provably incomplete* — a pinned `n = 4` counterexample (primal
  `K4`, constant structural tuples) where the greedy string depends on
  edge-insertion order. The paper therefore must, and does, use the expensive
  tie-complete form.

**Outcome.** Backed by a written proof
(`proofs/theorem_a_completeness.{tex,pdf}`) plus empirical pins: 150/150
shuffle+relabel invariance, biconditional agreement with pynauty under
Hypothesis fuzzing, and frozen regression pins on the Fano plane, STS(9), a
cyclic 13-point orbit, the `n = 4` counterexample, and both true STS(13)
systems.

**Subtlety to know.** `w*_c` is *frozen* as the **unpruned** tie-complete
lex-min. One may not "clean it up" with a smarter tie-break — that changes the
canonical form (lex-min over a subset ≠ lex-min over the full set). The only
permitted speed-up is stabiliser-orbit pruning. This is why the encoder is
worst-case exponential on highly symmetric designs — owned, not hidden, and
quantified in the scalability frontier (Part IV).

### 2. Compactness — "it's a *short* word" (the bits study)

**What / why.** Substantiates "a hypergraph is a *compact* word." Small but
rhetorically important: it is where the representation is introduced and shown
economical against the natural incidence-list baseline.

**How.** A uniform fixed-width code — deliberately *not* Shannon entropy and
*not* gzip; the estimator is the sibling graph paper's reviewer-tested one:

```
B_IsalHG(w) = |w| · log2 |Σ_HG(k)|
```

compared against an incidence-list construction model (per edge: a type bit +
arity·⌈log2 n⌉ address bits, plus vertex-insertion bits). Compression ratio
`r = B_comp / B_IsalHG`; `r > 1` favours IsalHG. One-sided Wilcoxon signed-rank
on `r − 1`.

**Outcome (frozen, three planted corpora, N = 320 pooled;
`T-M5a/bits/pooled_info_content.json`).** `r > 1` on **320/320**; pooled median
`r = 1.441`; Wilcoxon `p = 1.6 × 10⁻⁵⁴`; OLS slope `β = 0.749 < 1` (systematic
compression). Median canonical-string length 22 tokens at `n = 10` (81.4 bits at
`log2 13 ≈ 3.70` bits/token) against an incidence-list code of 114.0 bits. The
ratio sits at the low edge of the sibling's `[1.45, 1.89]` band — expected, since
hypergraphs pack more structure per vertex. The S7 design corpus reproduces the
sign of the result independently (`T-M7d`, `bits::median_ratio = 1.30`,
92.4% of items shorter), so the compactness claim is not an artifact of one
corpus.

**War story.** An early tokenizer bug (`split(";")` fragmenting bracketed
`V[...]` tokens, ~2× overcount) had *reversed* this to `r ≈ 0.51`. It was caught
and regression-pinned. The bits result is fragile to tokenization and rests on
one estimator choice — worth stating plainly in the paper.

### 3. Geometry — "what does the space look like?" (Pillar 1, the characterization)

The paper's central *contribution* in the authors' framing: no
hypergraph-dissimilarity space has been characterized this way. Six measured
invariants, under a strict **no-orphan-geometry rule** — every invariant is
measured because a specific downstream application or competitor contrast
consumes it. Primary corpus: 17 design families, 85 items, 27 seeds, all IsalHG
entries in the structural metric `d_I^⊥`; 95% BCa confidence intervals over
seeds.

| Invariant | What it measures | IsalHG (`d_I^⊥`) | Licenses |
|---|---|---|---|
| Non-Euclidean mass `ν` | `Σ_{λ<0}|λ| / Σ|λ|` of the double-centred Gram (Schoenberg) | `ν = 0.097` [0.096, 0.099], not PSD | metric methods (k-medoids) over centroid methods |
| Intrinsic dimension `D̂` | cross-validation on held-out dissimilarities (Gower placement) | `D̂ = 17` [16, 17] | MDS target dim; per-representation competitor axis |
| Distortion | Kruskal stress-1 at matched `D`, Shepard | stress `= 0.046` [0.045, 0.048] | qualifies every MDS map |
| Concentration + hubness | diam/median; skewness of `N_10` (Radovanović 2010) | diam/med 2.72; hub skew 0.907 [0.825, 0.990] | kNN precondition (A3) |
| Local sensitivity `s(e)` | `d_I(H, H⊕e)` per single edit | IQR 3–9 tokens, median 5 | neighbourhood methods; nauty contrast |
| Ladder response | `d_I` vs known accumulated edit budget `t` | increment IQR 6–18; monotone frac 0.71; 56/56 globally increasing | A4 scoring; smoothness evidence |

All values from `T-M7d/stats/stratum_a_stats.json` (geometry, hubness) and
`T-M7q/` (sensitivity, ladder).

**Why the numbers matter — the per-representation fingerprint.** The full
geometry table (all seven representations) is the paper's central
characterization, because the competitors contrast sharply and those contrasts
are what the applications then confirm:

| Representation | PSD | `ν` | `D̂` | stress | diam/med | `N_10` skew |
|---|---|---|---|---|---|---|
| IsalHG (`d_I^⊥`) | no | 0.097 | 17 | 0.046 | 2.72 | 0.907 |
| WL histogram | yes | 0.030 | ≥40 (censored) | 0.310 | 1.88 | 2.37 |
| NetLSD | yes | 0.000 | 4 | 0.000 | 2.73 | 0.17 |
| HPD-JSD | yes† | 0.000 | ≥40 (censored) | 0.018 | 1.10 | 0.10 |
| nauty-Levi edit | no | 0.024 | ≥39 (part. censored) | 0.023 | 3.86 | 0.01 |
| degree-seq L1 | no | 0.103 | 3 | 0.053 | 2.93 | 0.28 |
| HyperCOT | no | 0.250 | 1.1 | 0.275 | 8.05 | 0.07 |

IsalHG lands in a *moderately-dimensional, non-Euclidean, low-distortion,
mildly-hubby* space. WL and HPD are Euclidean by construction (`ν = 0`) but
their `D̂` is **censored** — their cross-validation error rides monotonically to
the search cap, so no finite estimate exists — and WL is *pathologically*
hub-prone (skew 2.37 against IsalHG's 0.907). NetLSD is compact (`D̂ = 4`) and
degree-seq lower still (`D̂ = 3`); HyperCOT is essentially one-dimensional at
high distortion. The censored cells are a legitimate contrast, not a pipeline
bug, and are labelled "censored" wherever they appear.

**Index-family discipline.** Raw `d_I` is never pooled across arities `k` (the
string length scales with incidence mass, which scales with `k`). Every geometry
comparison above is a dimensionless descriptor (`ν`, `D̂`, stress, skewness) or a
within-`k` ranking — never a raw-distance comparison across `k`.

**A structural-faithfulness check without the edit-distance oracle.** Along
perturbation ladders built from the design fixtures the accumulated edit budget
`t` is known by construction, and `d_I^⊥` rises with it: Spearman
`ρ(t, d_I^⊥) = 0.39` over 56 ladders / 560 steps (`p < 10⁻²⁰`,
`T-M7q/g2_design_ladder/`). The moderate `ρ` is expected — equal-budget edits on
distinct design families produce unequal `d_I` increments — and it is a
statement about *known* edits, not an edit-distance-proxy claim.

**Honesty flag inside the section.** The local-sensitivity study made a
three-regime prediction (from the stability analysis); it is confirmed for
**16 of 17** design families and **falsified for one** — the tight-path arity-4
family, which shows a heavier-than-predicted tail (heavy_tail_frac = 0.21
against a unimodal prediction; `T-M7q/g2_catalog_sensitivity/regime_confrontation.json`).
GQ(2,2) is confirmed as the predicted heavy-tailed regime (heavy_tail_frac =
0.23). The single falsification is reported as a partial falsification, with the
candidate mechanism (incoherent ties at that arity/size), rather than buried.

### 4. Usefulness — "what can you do with it?" (Pillar 2, four applications)

All four run off the *same* pairwise matrix `D_I` (competitors: their own
`D_rep`); each cites the geometric property that licenses it and each answers a
real analyst question named in the application's motivation.

- **A1 — Similarity map (MDS).** *Motivation:* surveying a database of
  module-scale reaction networks before selecting mechanisms to test.
  Classical + SMACOF. Dual-purpose: an application *and* how `ν`, `D̂`,
  distortion are produced. Licensed by Bourgain (`O(log N)` distortion exists,
  so MDS is justified) and Khot–Naor (string-edit metrics need non-trivial
  distortion, so a residual is expected and reported). Outcome: the IsalHG map
  sits at stress 0.046, genuinely non-Euclidean; the vector competitors are
  Euclidean but high- or censored-dimensional.

- **A2 — Clustering (k-medoids + dendrogram).** *Motivation:* grouping network
  motifs into structural families and returning an actual *medoid* an analyst
  can inspect. Licensed by `ν` — PAM needs only a metric, no coordinates, which
  is *why* k-means is unavailable in a non-Euclidean space. Adjusted Rand Index
  against the 17 planted families (95% BCa CI):

  | Rep | ARI | vs IsalHG (Holm) |
  |---|---|---|
  | NetLSD | 0.479 [0.460, 0.500] | **beats** IsalHG, `p = 4.5×10⁻⁷`, rb 1.00 |
  | degree-seq L1 | 0.451 [0.433, 0.472] | **beats** IsalHG, `p = 4.5×10⁻⁷`, rb 1.00 |
  | HPD-JSD | 0.303 [0.289, 0.319] | ties IsalHG (`p = 1.0`) |
  | HyperCOT | 0.287 [0.272, 0.304] | ties IsalHG (`p = 1.0`) |
  | **IsalHG** | **0.285 [0.268, 0.303]** | — |
  | nauty-Levi | 0.178 [0.166, 0.191] | IsalHG beats it, `p = 6.1×10⁻⁷`, rb 0.99 |
  | WL | 0.016 [0.015, 0.016] | IsalHG beats it, `p = 4.5×10⁻⁷`, rb 1.00 |

  **IsalHG loses A2 clustering to a naive degree-sequence baseline and to
  NetLSD, both Holm-significant.** That is the honest headline and it has a
  clean explanation: the design families separate cleanly on degree structure
  alone, so a first-order degree signal captures the dominant discriminative
  information and no degree-free representation is expected to dominate it. The
  baseline was *pre-registered* — its interpretation contract was written before
  any result was seen — so this is a designed finding, not a post-hoc excuse.

- **A3 — Classification (kNN, precomputed metric).** *Motivation:* assigning an
  incoming collaboration/team-structure hypergraph to a known structural type
  from its distances to labelled examples. Licensed by the G1 hubness profile,
  *measured first* so the result is a confirmed prediction. AUC-OvR at `k = 5`
  (95% BCa CI):

  | Rep | AUC@k=5 | vs IsalHG (Holm) |
  |---|---|---|
  | degree-seq L1 | 0.948 [0.943, 0.951] | **beats** IsalHG, `p = 1.9×10⁻⁵`, rb 0.94 |
  | NetLSD | 0.934 [0.929, 0.939] | **beats** IsalHG, `p = 1.2×10⁻²`, rb 0.71 |
  | HyperCOT | 0.926 [0.920, 0.933] | ties IsalHG |
  | **IsalHG** | **0.920 [0.913, 0.925]** | — |
  | HPD-JSD | 0.895 [0.891, 0.900] | IsalHG **beats** it, `p = 4.2×10⁻⁶`, rb 0.97 |
  | nauty-Levi | 0.839 [0.831, 0.848] | IsalHG beats it, `p = 4.5×10⁻⁷`, rb 1.00 |
  | WL | 0.495 [0.494, 0.497] | IsalHG beats it, `p = 4.5×10⁻⁷`, rb 1.00 |

  The **licence lands decisively**: WL's hubness skewness of 2.37 is the highest
  in the corpus, and its kNN AUC **collapses to chance, 0.495** — the geometry
  measured before the classifier predicted the classifier's failure. Among the
  rest the ordering again follows the degree signal (degree-seq and NetLSD
  ahead), but IsalHG now beats HPD significantly despite tying it on A2.

- **A4 — Hypergraph-to-hypergraph shortest path (the capability differentiator).**
  *Motivation:* comparing two snapshots of a temporal higher-order network by
  the structural *path* between them, with every intermediate a valid,
  inspectable hypergraph. Shortest accumulated-`d_I` path through a pool of
  intermediates + distractors, over 8 design-ladder instances
  (`T-M7q/a4_design/`). Scored without the edit-distance oracle: budget
  monotonicity, path recovery, and a decodability demonstration. Outcome:
  accumulated path length is **monotone in the ladder budget for every
  representation** (monotone fraction 1.00 for IsalHG, WL, NetLSD, HPD); exact
  recovery of the specific ladder intermediates is IsalHG 0.125, WL 0.000,
  NetLSD 0.257, HPD 0.191 — IsalHG's lower recovery is a *feature*, the geodesic
  routes through same-budget alternatives, which is precisely why `d_I` is not
  an edit-distance proxy. The **categorical result is decodability**: in all 8
  instances the IsalHG intermediate strings decode via S2H to valid hypergraphs
  (8/8, mean 2.4 decoded intermediates per path). WL collapses to a two-node hop
  (no intermediates); NetLSD and HPD have no decoder; nauty cannot navigate at
  all (its avalanche geometry). **No competitor can exhibit the intermediate
  hypergraphs along a path.**

**Honest summary of Pillar 2.** On pure task metrics IsalHG is **mid-table on
these degree-separable families**: it loses A2 and A3 to a naive
degree-sequence baseline and to NetLSD, ties HPD on A2, and beats HPD on A3.
Usefulness therefore does **not** rest on task-metric dominance. It rests on
three axes stated jointly: (i) each application is *licensed* by a measured
invariant (no orphan geometry); (ii) IsalHG is *competitive* (indistinguishable
from HPD/HyperCOT, ahead of nauty and WL); and (iii) IsalHG is *uniquely
capable* — the only representation that is simultaneously a **complete
invariant**, **decodable**, and **geometrically navigable** (A4). That
capability, not a clustering score, is the defensible value proposition, and the
paper does not claim otherwise.

**Real-data cross-check (HIC IMDB genre, censored).** The intended real anchor
failed a feasibility gate: real IMDB hypergraphs carry corpus-level arity far
beyond the arity cap, and near-symmetric instances make `w*_c` blow up, so `w*_c`
is not computable across the full corpus. The feasible subset censors by
structural symmetry (which correlates with labels), so it cannot be a primary
anchor. On the two cleanly computable datasets (`w*_c` yield 92.5% and 91.7%),
genre is **near-unclusterable from structure for every representation** (all
ARI < 0.10 under `d_I^Σ` — an honest negative), while the kNN hubness story
reproduces: mean AUC-OvR at `k = 9` is 0.673 for `d_I^Σ`, ahead of NetLSD and
nauty (0.654) and WL (0.624), whose real-data hubness (skewness 4.5–7.4) again
trails. Real-data intrinsic dimension is markedly lower than synthetic
(`D̂ ≈ 10–11` on two IMDB corpora vs `D̂ = 17` synthetic). Application claims are
therefore explicitly **synthetic-scale claims, cross-checked on real data where
`w*_c` is computable.**

### 5. Discussion — the relation to edit distance (retired capstone, compressed)

Deliberately *last* and *small*: it is the paper's weakest axis, and leading
with it would invite the reviewer to read the work as "a mediocre
edit-distance-approximation paper." The logic, in order:

1. **Length lemma:** `|w*_c| ≤ m(1+kn)` (string linear in incidence mass).
2. **Envelope proposition:** `d_I ≤ m(1+kn)·HGED` — *unconditional*, presented
   honestly as an envelope (its whole content is the length lemma), **not** a
   stability bound.
3. **Impossibility (the key move):** a two-sided bi-Lipschitz relation
   `c·HGED ≤ d_I ≤ C·HGED` is **provably out of reach**. The lower direction
   fails generically for *any* complete canonical-form / WL-type invariant
   (FSW-GNN, LoG 2025; Chen et al. 2023). The upper direction fails through two
   named, measured mechanisms: **drift** (unit-step pointer runs cost `Θ(n)` in
   adversarial layouts) and **avalanche** (near-symmetric inputs — the price
   *any* complete invariant pays, because deterministic symmetry-breaking is
   discontinuous exactly where objects are nearly symmetric). Framed as a
   *frontier*: stability-by-construction (WL, spectra, transport) is bought by
   *giving up completeness*; IsalHG sits on the completeness side.
4. **One figure (E1′):** Spearman `ρ` between `d_I` and *exact* edit distance on
   a small connected mini-corpus, ours only. Outcome (frozen,
   `T-M5a/e1prime/`): **`ρ = 0.622`, `N = 6,921` pairs**, per-cell 0.48–0.81,
   and `HGED = 0 ⇔ d_I = 0` confirmed. Offered as honest characterization, not
   a proxy claim.
5. **Consequence:** because no bound can certify usefulness, usefulness was
   established *directly* (Pillars 1–2). The discussion closes the loop on the
   paper's own methodology.

**E1′ reader note.** The corpus is 11 of 12 planned blocks — the 12th (`n = 10`,
second seed) exceeded 100 GB after 18 h on the exact-HGED oracle and was
excluded *whole-block* (per-pair exclusion would bias `ρ`). This is documented
as the measured practical ceiling of exact HGED, which is NP-hard and barely
computable at `n = 10`. The frozen oracle is not to be re-run.

---

## Part III — The cast of competitors

| Competitor | Representation | Role | Standing on the primary corpus |
|---|---|---|---|
| **IsalHG** (ours) | canonical string, Levenshtein | — | complete + decodable + navigable; mid-table task metrics; slow on near-symmetric / high-arity inputs |
| **degree-seq L1** | sorted degree vector, L1 | naive structural baseline (pre-registered) | **A2/A3 leader** — the families are degree-separable |
| **NetLSD** | spectral heat-trace, L2 | full member | **A2/A3 leader**; compact (`D̂ = 4`); no decoder; not complete |
| **HPD** (portrait divergence) | hyperedge-path tensor, JSD | paper+code member | ties IsalHG on A2, loses A3; no decoder; JSD not a metric; index error on ~⅓ of real instances |
| **HyperCOT** | optimal-transport coupling | paper+code member | ties IsalHG; `O(n³)`/pair — small corpora only |
| **Hypergraph-WL histogram** | count vector, L1 | standard baseline | pathological hubness (skew 2.37) → kNN dies (AUC 0.495); no decoder |
| **nauty-Levi canonical + edit** | canonical string, edit | **contrast, not "beaten"** | complete but avalanche-everywhere (sensitivity IQR 20–37 vs ours 3–9); cannot navigate paths |

Two of these carry the honest story. The **degree-sequence baseline** exists to
answer "does any richer representation beat a trivially cheap structural
signal?" — on these families the answer is *no*, and reporting that plainly (a
pre-registered outcome) is stronger than hiding it. **nauty** is the sharpest
device: it is *also* a complete canonical form, so it isolates what IsalHG's
specific encoder design buys — a *navigable* geometry (sensitivity IQR 3–9 vs
nauty's 20–37, a 4–8× contrast measured over 1700 single edits) that a hash-like
canonical form does not have. IsalHG's own profile is not avalanche-free
everywhere (the GQ(2,2) heavy-tailed regime), but it is compact *outside* a
characterized regime, where nauty's is avalanche *everywhere*.

---

## Part IV — Is it publishable? Straight assessment against the current data

**Short answer.** A publishable, genuinely solid paper for a good applied venue
(*Information Sciences*, the target). It is *not* a "we beat SOTA on tasks"
result and must not be framed as one — on the primary corpus IsalHG is
mid-table on clustering and kNN. The defensible claim is narrower and real: **a
complete, decodable metric representation of hypergraphs with a characterized
geometry and a unique navigation capability.** The S7 re-run *closed* the two
largest holes of the previous draft (no significance testing; a single-point
study), and in doing so surfaced three new, smaller, defensible ones.

### Genuinely strong (the load-bearing case)

1. **The foundation is airtight.** Theorem A + Corollary A is a real, proved
   theorem with a written proof, empirical pins, and a correctly-handled
   subtlety (greedy incomplete; only tie-complete works).
2. **The characterize → exploit narrative is disciplined.** The
   no-orphan-geometry rule is a strong organizing principle most representation
   papers lack — every geometry number in the table is consumed by an
   application licence or a competitor contrast.
3. **The A4 decodability differentiator is real and unique.** "Only our
   representation can produce the intermediate hypergraphs along a path" (8/8
   instances, mean 2.4 decoded intermediates) is a clean, categorical,
   non-cherry-pickable claim. This is the headline the paper should lead the
   usefulness section with.
4. **The statistics are now in place.** Every headline task-metric number
   carries a 95% BCa confidence interval over 27 seeds and a Holm-corrected
   one-sided Wilcoxon test in both directions (60-test family). The comparisons
   are falsifiable, which the previous draft's point estimates were not.
5. **Intellectual honesty is a feature.** Pre-registered naive baseline, a
   reported single-regime falsification, the real-data NO-GO, the tokenizer bug
   caught, and the impossibility argument that turns "no bound" into a
   *principled* completeness–stability frontier.

### Holes a reviewer *will* find (and how the paper defends each)

1. **On pure task metrics IsalHG loses A2 and A3 to a naive degree-sequence
   baseline and to NetLSD** (Holm-significant, rb 0.94–1.00). This is the
   sharpest hole and it must be met head-on, not smoothed. *Defense:* the design
   families are separable on degree alone, a degree-controlled corpus was proved
   infeasible to build, and the degree baseline was *pre-registered* to detect
   exactly this. Usefulness is reframed onto A4 + the capability matrix
   (complete ∧ decodable ∧ navigable), where no competitor stands. The framing
   must be airtight that usefulness = "licensed, competitive, uniquely capable,"
   never "best-in-class clustering/kNN." **Promote the capability matrix to a
   main figure, beside the A4 decoded-intermediates figure.**

2. **The arity axis is short of plan** — the random-instance sweep admitted only
   `k ∈ {3, 5}` (two points), not the three the design called for
   (`harvest_summary.json`: `all_acceptance_pass = false`,
   `acceptance_shortfalls = ["ac5_arity_axis"]`). *Defense:* this is a *measured
   outcome of the feasibility envelope*, not an omission — `k = 4` random blocks
   timed out and `k ∈ {7, 10}` are infeasible at every tested size. State it as
   an honest scope statement. The Stratum A per-arity breakdown does cover
   `k ∈ {3, 4, 5}` for the A2/A3 task metrics; it is a different object from the
   geometry sweep curve and should be labelled as such.

3. **Three cells timed out for IsalHG while all six competitors finished**
   (`er_uniform_k3_n16_rho4`, `k3_n24_rho2`, `k5_n8_rho2`; 4-hour wall,
   partial seed coverage). *Defense:* whole-cell exclusion — not per-pair, which
   would bias the comparison — reported in every affected table as the measured
   compute boundary of a complete invariant. This is the honest face of the
   scalability frontier (next item).

4. **The scalability frontier caps well below the advertised arity.** `w*_c` is
   feasible at `k = 3` up to `n ≈ 24` (low density) and at `k = 5` only at
   `n = 8`; `k = 7` and `k = 10` are measured infeasible at every tested size,
   so the advertised arity cap of 10 is not reachable. *Defense:* state it
   plainly with the runtime table; note that nauty is *also* worst-case
   exponential, so the frontier is a property of complete invariants, not a
   defect unique to IsalHG. Own the worst-case cost (GQ(2,2), the HIC blow-up)
   in the discussion rather than an appendix.

5. **The real-data anchor is the design catalog, not a real corpus.** The
   real-world gate returned NO-GO on all 10 candidate corpora — each is one large
   network, not a labelled collection of comparable instances — and the HIC IMDB
   exhibit is censored (2 clean + 4 heavily-censored datasets) with a *negative*
   clean result (genre near-unclusterable). *Defense:* the designs *are* the real
   anchor (they are genuine combinatorial objects, not random seeds), and the
   application claims are stated as synthetic-scale claims cross-checked on real
   data where computable. Honest, but a reviewer may still want one in-cap real
   corpus; if a cheap one exists it is worth adding.

6. **`D̂` censoring must be labelled everywhere.** WL, HPD, and nauty report
   `D̂ ≥ 39–40` "censored at the cap" — a legitimate contrast (their metrics do
   not concentrate), but every such cell needs the caveat or it reads as a bug
   in *our* pipeline rather than a property of theirs.

7. **The single-regime falsification (tight-path arity-4) needs a clean
   landing** — explained (incoherent ties under single arity-≤3-dominated edits)
   and bounded (16/17 confirmed), not left as an unresolved crack.

8. **The bits result rests on one estimator and is tokenization-fragile.** The
   reversed-conclusion tokenizer bug should be mentioned as the reason the
   estimator choice and the bracket-aware parser are pinned by regression tests.

### Best way to arrange everything

- **Lead with the theorem and the picture; close with the caveat.** Keep the
  spine (foundation → compactness → geometry → usefulness → discussion). Do
  **not** move the edit-distance discussion earlier — burying it is correct.
- **Headline: "a complete, decodable metric representation of hypergraphs with a
  characterized geometry"** — not "a better clustering method." The uniqueness
  claims (complete + decodable + navigable) are what no competitor has;
  competitive-but-not-dominant task metrics are enough *given* the uniqueness.
- **Make the degree-confound explicit, early, and once.** A single clear
  paragraph — "these families are degree-separable, the naive baseline is
  therefore expected to lead, and it does" — disarms the biggest reviewer
  objection better than any amount of A2/A3 spin.
- **Promote the capability matrix to a main figure**, with the A4 decoded-
  intermediates figure beside it (the matrix claims decodable; the figure shows
  it).
- **State the two big limitations up front in the discussion:**
  worst-case-exponential `w*_c` with its measured frontier, and synthetic-scale
  claims with a real-data cross-check. Owning these disarms the reviewer.
- **Ship the reproducibility artifact.** `REPRODUCING.md` +
  `scripts/reproduce_tables.py` regenerate the headline numbers from the cached
  distance matrices; cite it — reproducibility is cheap credibility for a
  data-science venue.

**Bottom line.** The science is sound, the foundation is proved, the narrative
is unusually disciplined, and decodability/completeness is a real unique
contribution. The evidence is now a *powered* study — 85 design items across
27 seeds, BCa intervals, Holm-corrected tests — not the single-point study the
previous draft was. The cost is honesty about where IsalHG *does not* win: it is
mid-table on degree-separable clustering and kNN, its arity reach is capped by a
measured feasibility frontier, and its real anchor is a design catalog rather
than a real corpus. Sold correctly — complete + decodable + characterized
geometry, competitive on tasks, uniquely capable on A4, and forthright about the
degree confound and the frontier — this is a clean, honest contribution that
will survive review at *Information Sciences*.
