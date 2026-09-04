# Knowledge bases as words — the article's storyline (v6.1)

*This document is the narrative of the IsalHG journal article, target IEEE
Transactions on Knowledge and Data Engineering. It states the premise, the
research questions and the hypothesis each one tests, the theory the paper
proves, the algorithms it ships, the data it runs on, the competitors it
faces, and the one evaluation each application receives. Every proof,
experiment and figure in the paper serves one research question; anything
that serves none is cut. Engineering (tasks, gates, statuses) lives in
`../DEVELOPMENT/`; the verified fact base behind every number quoted here is
in `foundation/`. Version 6.1, 2026-09-03, written for the PI meeting.*

**Two standing rules.** (i) Experiments start from zero: no result of the
previous iteration is load-bearing unless re-measured on the collections of
§7; prior measurements enter only as the feasibility envelope and as design
lessons. (ii) The paper tells one story on one evaluation axis per
application: every experiment answers a question *about knowledge bases*,
and the metric that answers it is the only metric reported for it.

---

## 0. The paper in six sentences

A knowledge base over a function-free signature is a finite set of ground
facts — a labelled hypergraph — and two knowledge bases that differ only by
renaming their constants are the same knowledge base. Comparing, aggregating,
organizing and generating *collections* of such knowledge bases therefore
requires a distance on isomorphism classes, and every existing candidate
lacks at least one of four prerequisites: exactness at zero, the metric
axioms, polynomial per-pair cost, or a closed language in which every string
is a knowledge base. Writing each knowledge base as its canonical instruction
word supplies all four: exact identity (Theorem A), a metric with computable
optimality certificates (Corollary A and the pairwise bound), polynomial
pairwise cost after one canonicalization per knowledge base, and a language
whose every word — every prefix, every edit, every alignment interior, every
sample of a generative model — decodes to a connected knowledge base. The
space has two scales: the metric organizes distinct structures and certifies
consensus, and the language resolves fact-level neighbourhoods around any
knowledge base; we prove what each scale guarantees and, with a conservative
extension of the language, that the string neighbourhood of radius `r`
contains every knowledge base within `r` fact insertions. On that basis we
deliver consensus, outlier filtering, hierarchical clustering, k-medoids, a
metric map and a generative model for collections of knowledge bases, each
tied to a question a knowledge engineer asks and each evaluated on real
collections: entity descriptions of a hyper-relational knowledge graph and
time series of real interaction knowledge bases whose fact-level changes are
known exactly. Canonical-labelling engines decide identity faster and we say
so first; what they do not give is a language, and the last three
contributions are impossible without one.

## 1. Premise — collections of knowledge bases are metric-space problems

**Where collections of knowledge bases come from.** The one-hop description
of an entity in a knowledge graph — its statements, with qualifiers, hence
n-ary facts; the fact set extracted from one document, one source or one run
of an extractor; the anonymized or blank-node fragment of an RDF store; the
finite models a generator or a model finder emits; successive snapshots of an
entity's description as a graph evolves. In each case the analyst holds `N`
knowledge bases over one signature and asks: *which one best represents the
collection?* (consensus) *which ones do not belong?* (outliers) *how do they
group, and what patterns of description exist?* (dendrogram, k-medoids)
*what does the collection look like?* (map) *what does a new, plausible
member look like?* (generation). And in each case the identity of the
constants is unavailable, untrusted or irrelevant — the *pattern* of facts is
the object — so isomorphic knowledge bases must be treated as equal. Model
theory says this is the right equivalence: isomorphic structures satisfy the
same sentences.

**Every one of those questions is a metric-space question,** and each is well
posed, and inherits a guarantee, only if the dissimilarity is a metric on
isomorphism classes: identity of indiscernibles gives exact duplicate
handling; the triangle inequality gives the medoid its approximation ratio and
the analyst a certificate; polynomial evaluation gives an `N × N` matrix at
all. The generative question adds a fifth requirement no metric supplies: a
representation in which *every string is an object*.

**No existing distance has the prerequisites together** (§6 has the full
matrix). Exact structure edit distance is NP-hard per pair. Its bipartite
(Hungarian) approximation is polynomial but not a metric — Serratosa (2019)
in print, and measured here: the reported edit-path cost is asymmetric on
38 % of random pairs and violates the triangle inequality on 1.4 % of
triples, with an explicit ten-vertex counterexample; its raw assignment value
is a pseudometric that cannot separate non-isomorphic knowledge bases.
Weisfeiler–Leman, spectral and portrait embeddings are vector metrics but
incomplete: they merge non-isomorphic knowledge bases, at a rate we count on
real collections. Hypergraph optimal transport is a metric in theory whose
computed value is a local optimum of a non-convex problem, needs an external
measure, and has no decoder. A canonical labelling certificate (nauty on the
Levi graph) plus Levenshtein *is* an exact polynomial metric — it is the
certificate member of the family we introduce, faster to compute, and it is
compared on every table — but a certificate is not a language: an edited
certificate is not a certificate, a prefix of one is nothing, and no
generative model can be defined on the set of certificates.

## 2. The premise formalized — a knowledge base is a word

**Knowledge bases as labelled hypergraphs.** Signature `σ = (P_1,…,P_r)`,
function-free; a knowledge base `K` is a finite `σ`-structure read as its set
of ground facts. Encoding E1 (symmetric relations): vertices are the
constants, labelled by the unary predicates true at them; each fact
`P_i(d_1,…,d_a)` with `a ≥ 2` is a hyperedge `{d_1,…,d_a}` labelled `i`;
`k = max_i a_i`. Encoding E1⊤ adds an anchor constant `⊤` joined to every
constant by a binary `dom` edge, which makes every knowledge base connected
and makes constant insertion a fact. Encoding E2 (general relations, argument
order, repeated arguments) is the anchored incidence hypergraph of arity 2.
Under each, `K ≅ K' ⇔ E(K) ≅ E(K')` as labelled hypergraphs, so every
statement below about hypergraphs is a statement about knowledge bases (the
bridge corollary). Facts of arity ≥ 3 — qualifier-bearing statements, group
interactions — are what makes the object a hypergraph rather than a graph.

**The word.** The instruction alphabet `Σ_HG(k)` — `V` (new edge over `i`
pointed vertices plus `j` fresh ones), `C` (new edge over pointed vertices),
`P`/`N` (pointer moves), `W` — is executed by a virtual machine that builds a
hypergraph; the interpreter S2H is total on the alphabet and every decoded
hypergraph is connected. The tie-complete canonical word `w*_c(H)` is the
lexicographically least word over an isomorphism-invariant seed set and all
tie branches; the augmented fingerprint `F_c(H) = (seed label, w*_c(H))`
carries the one label the word omits. The language extension `Σ⁺` of §11
adds rank-addressed fact tokens on the decoder side only. Algorithms:
`../H2S_S2H.md`.

**The four properties, each a theorem.**

1. *Exactness.* `F_c(H_1) = F_c(H_2) ⇔ H_1 ≅ H_2` for connected labelled
   hypergraphs under one `(k, depth, vocabulary)` (Theorem A, proved,
   labelled case included).
2. *Metric.* `d_I(H_1,H_2) = d_Lev(F_c(H_1), F_c(H_2))` over the
   seed-label-prefixed token sequence is a metric on isomorphism classes
   (Corollary A, proved). Raw token Levenshtein; never the normalized
   variant, which is not a metric.
3. *Polynomial pairwise cost.* One canonicalization per knowledge base, then
   `O(L²)` per pair with `L = |w*_c|` in tokens (13 tokens at six vertices to
   59 at fifteen on 3-uniform substrates; `L² ≈ n³`, the cost of one
   Hungarian assignment). Canonicalization is worst-case exponential; on
   labelled knowledge bases it is measured in milliseconds (§7), and labels
   are what makes it so.
4. *A closed language.* Every word of `Σ_HG(k)*` and of `Σ⁺*` decodes to a
   connected hypergraph: every prefix, every single-token edit (24,000/24,000
   measured), every interior word of a Levenshtein alignment between two
   canonical words (62/62), every sample of any distribution over words
   (Propositions 2 and 2⁺).

**Compactness** rides along: the canonical word is shorter than the
incidence list under a fixed-width code (compression ratio > 1 on every item
measured previously; re-measured on the labelled collections of §7).

**Two scales.** `d_I` compares construction *programs*. Because a canonical
word is produced by deterministic symmetry breaking and a pointer traversal
whose layout depends on every earlier choice, one structural edit typically
rewrites about half of the word (measured 0.51–0.54 of the word per edit on
random substrates). Consequently the metric is exact and graded *across
distinct structures* — identity is exact, distinct classes are far apart,
certificates hold — while *within a structure's fact-level neighbourhood* it
is the language, not the metric, that resolves: a one-fact variant of a
knowledge base `K` is reachable from `w*_c(K)` by one or two token edits
through a non-canonical word in 52–55 % of cases under `Σ_HG` (measured) and
in 100 % of insertion cases under `Σ⁺` (Proposition 4). The paper is
organized on this two-scale reading: the **metric scale** organizes and
certifies (consensus, outliers, clustering, map); the **language scale**
resolves neighbourhoods, interpolates and generates.

## 3. Research questions

Each question names the knowledge-base problem it answers, the hypothesis, the
evidence, and the single evaluation it receives. They are the paper's
sections, in order.

### RQ1 — Well-posedness. *Which distances on isomorphism classes of knowledge bases satisfy the prerequisites that consensus, outlier filtering, clustering and generation need, and what does each missing prerequisite do to a real collection?*

- **Hypothesis.** Only canonical-word metrics satisfy exactness, the metric
  axioms and polynomial pairwise cost together; only the constructive member
  adds a closed language. Each missing prerequisite has a measurable effect
  on a real collection: false merges for incomplete embeddings, metric
  violations for the bipartite pipeline, time-outs for exact oracles.
- **Evidence.** Theorems 1–2 and Propositions 1–5 for ours; the counterexample
  and violation rates for the bipartite pipeline; the false-merge census on
  the real collections (the fraction of non-isomorphic pairs at distance 0
  under each embedding, against the exact key); the oracle ceiling.
- **Evaluation.** The capability matrix, filled by theorem or counterexample,
  and one table of measured consequences on the real collections.

### RQ2 — Consensus without identity. *Given `N` knowledge bases whose constants cannot be aligned, which one best represents the collection, with what guarantee, and how well does the representative summarize the collection when the truth is known?*

- **Hypothesis.** (a) For any metric, the medoid satisfies
  `cost ≤ (2 − 2/N)·OPT`, and the pairwise lower bound
  `LB = Σ_{i<j} d(K_i,K_j)/(N−1) ≤ OPT` gives every candidate a certified
  ratio; measured ≤ 1.63 on all pilot profiles. (b) For collections whose
  members are fact-level variants of a common source — extractions,
  annotations, or successive snapshots of one knowledge base — the
  **ball-coverage consensus** in the language (the candidate whose radius-`r`
  string ball decodes to the most inputs) identifies the source: measured
  maximiser in 11/12 one-edit profiles (unique in 9/12) under `Σ_HG`, and
  provably covering every insertion variant under `Σ⁺` (Propositions 4–5).
  The `d_I`-medoid, or any metric's medoid, cannot: it must return an input.
- **Real ground truth without planting.** Time series of interaction
  knowledge bases (§7) supply real variant collections in which the
  fact-level change between consecutive members is *known exactly* because
  node identities persist across time; the methods see only the anonymized
  members.
- **Evaluation (one metric).** The exact fact-level distance from the
  returned consensus to the held-out next member of the series, compared with
  the certified medoid and with the fact-level majority-vote merge computed
  *with* identities (the Konieczny–Pino Pérez operator, which our methods must
  approach without identities). Synthetic-free.

### RQ3 — Outliers that statistics cannot see. *Which members of a collection of knowledge bases are structurally atypical, and does exactness change the answer?*

- **Hypothesis.** Distance-based outlier scores over a metric on isomorphism
  classes rank atypical descriptions correctly; incomplete representations
  assign distance 0 to non-isomorphic knowledge bases and therefore hide
  outliers whose statistics (size, degree sequence, WL colouring) match the
  inliers.
- **Evidence.** The false-merge census (RQ1) turned into outlier terms: how
  many rare structures each representation absorbs into a frequent class;
  and a detection test on real substrates with controlled corruptions
  (semi-synthetic: real knowledge bases, injected fact-level errors of stated
  type and budget, the standard practice of anomaly-detection benchmarks).
- **Evaluation (one metric).** Area under the ROC curve for recovering the
  corrupted members, per corruption type, for every representation.

### RQ4 — What patterns of description exist. *Do the structural classes found by k-medoids and hierarchical clustering of entity descriptions correspond to known entity types, and what geometry licenses those algorithms?*

- **Hypothesis.** `ν > 0` (the space is non-Euclidean, so medoid-type
  estimators and metric MDS, not centroids and classical MDS); hubness is
  moderate; the intrinsic dimension is high. Under those licences, PAM
  k-medoids and average-linkage dendrograms over `d_I` recover entity types
  (the Wikidata `instance of` classes of the entities) from structure alone.
- **Evaluation (one metric family).** Adjusted Rand index against entity
  types for k-medoids; cophenetic correlation and the same index at the
  type level for the dendrogram; the map is a figure with its stress, not an
  evaluation.

### RQ5 — Generation and interpolation: what a language gives that a certificate cannot. *Can the collection be extended with new, valid, plausible knowledge bases, and can two knowledge bases be joined by a path of valid intermediates?*

- **Hypothesis.** Because every word decodes, any generative model over
  words is a generative model over knowledge bases with validity 1 and no
  rejection step; a certificate-based representation admits no such model.
  The alignment path between two canonical words is a sequence of valid
  knowledge bases (the decodability figure); the alignment interior of two
  certificates decodes to nothing.
- **Evidence.** Proposition 6 (generative closure; prefix validity);
  Proposition 7 (certificate sets are not languages); a small sequence model
  (token n-gram, order 3–4, or a small recurrent model) fitted on the words
  of a real collection and sampled; the incidence-list generator as baseline.
- **Evaluation (one metric).** Validity rate of generated objects (1.000 by
  theorem for ours; measured for the baseline) and structural fidelity —
  the distance between the size/arity/label profile of the samples and that
  of the collection — with the interpolation figure as the qualitative
  exhibit.

### RQ6 — Operating envelope. *For which knowledge-base sizes, arities and label vocabularies does the pipeline run, and how does cost scale with the collection size?*

- **Hypothesis.** Cost is `N` canonicalizations plus `N²` string
  comparisons; the canonicalization frontier is the number of facts, not of
  constants (measured: `m ≤ 111` completes in ~0.03 s, `m ≥ 253` never);
  labels are the tie-breaker (measured: labelled milliseconds where unlabelled
  fails at thirteen vertices).
- **Evaluation.** One envelope figure over `(m, k, |Σ|)` on synthetic random
  knowledge bases (the one place synthetic data is indispensable: real
  collections do not span sizes systematically) and the yield table of every
  real collection.

## 4. Theory delivered

| # | Statement | Status | Serves |
|---|---|---|---|
| Thm 1 | Theorem A for knowledge bases via the bridge: `F_c(E(K)) = F_c(E(K')) ⇔ K ≅ K'` | proved | RQ1, RQ3 |
| Thm 2 | Corollary A: `d_I` is a metric on isomorphism classes of connected knowledge bases with one `(k, depth, Σ)` | proved | RQ1, RQ2, RQ4 |
| Prop 1 | Length and key size: `\|w*_c\| ≤ m(1+kn)`; fixed-width bits against the incidence list | proved + re-measured | RQ1, RQ6 |
| Prop 2 | Closure and connectivity: S2H is total on `Σ_HG(k)*` and every decoded word is connected; hence every prefix, edit and alignment interior is a knowledge base | closure proved; connectivity written in this paper (prefix induction) | RQ2, RQ5 |
| Prop 2⁺ | The same for `Σ⁺` (§11): the rank-addressed tokens add no vertex without attaching it inside an edge | to be written (immediate) | RQ2, RQ5 |
| Prop 3 | Certificates: medoid `≤ (2 − 2/N)·OPT`; `LB ≤ OPT`; for any decoded candidate `M`, `LB ≤ OPT ≤ Σ_i d_I(M, K_i)` | proved (Jiang–Münger–Bunke 2001 for the medoid) | RQ2 |
| Prop 4 | Fact-level simulation under `Σ⁺` (anchored encodings): a fact insertion is one token; a fact deletion is one token if the fact is `C`-encoded (each edge of a canonical word has exactly one creator, by the termination lemma) and exactly `j` tokens if it is `V`-encoded with `j` fresh constants (a run of `j` chained anchor re-attachments, exact equality); hence every knowledge base within `r` fact insertions of `K` lies in `S2H⁺(B_r(w*_c(K)))`, and within `r` arbitrary fact edits in `B_{(k−1)r}` | proof sketch checked 2026-09-03; measured 1,200/1,200 insertions and 717/717 deletions | RQ2 |
| Prop 5 | Source identifiability on the indel ball: if `K_1..K_N` are obtained from `M` by `t` fact insertions each (distinct), then `cov_t^indel(M) = N`, while a copy reaches another copy only by at least `2t` indel edits; hence `M` is the unique maximiser of `cov_t^indel` among inputs | to be written (from Prop 4); measured: source unique maximiser 12/12 at `t = 1` and 12/12 at `t = 2`, copy-to-copy reach 0.00–0.02 | RQ2 |
| Prop 6 | Generative closure: any distribution on `Σ⁺*` pushes forward to a distribution on connected knowledge bases; autoregressive generation is valid at every prefix | immediate from Prop 2/2⁺ | RQ5 |
| Prop 7 | Certificate sets are not languages: the set of canonical-labelling certificates is not closed under single-symbol edits, has no total decoder and no prefix property; hence no ball, reach, interpolation or generative model is defined on it | to be written (short) | RQ1, RQ5 |
| Prop 8 | The bipartite edit-path cost is not a metric (counterexample `d(A,B) = 2, d(B,C) = 4, d(A,C) = 7` on 3+3+4 vertices); its raw assignment value is a pseudometric with false zeros | proved by counterexample; rates measured | RQ1 |
| Prop 9 | Incompleteness of WL-type keys on hypergraphs | cited (CFI 1992; UniGNN 2021) + measured merges | RQ1, RQ3 |

What the paper does **not** claim: a faster isomorphism test; an
edit-distance proxy; scaling to large knowledge bases.

## 5. The toolkit — one algorithm per question, one guarantee each

**Metric scale.** Canonicalize once per knowledge base (C++ engine; keys
`F_c`); census (distinct classes, frequencies, exact duplicates); `N × N`
token-Levenshtein matrix (rapidfuzz, seed-label prefix). Then: **consensus** =
medoid with its certified ratio (Prop 3); **outlier scores** = k-nearest
distance and LOF over the precomputed metric (licensed by Thm 2 and the
hubness measurement), plus rare-class scores from the census; **organization**
= PAM k-medoids (licensed by Thm 2 and `ν > 0`) and agglomerative dendrogram
with cophenetic correlation; **map** = metric MDS (SMACOF) with stress-1 and
the Schoenberg spectrum that says why classical MDS is excluded.

**Language scale.** *Reach*: `K'` is within reach `r` of `K` if some word in
`B_r(w*_c(K))` decodes to `K'`'s class; computed by enumerating the ball
(`|B_1| ≈ 570–740` words, `|B_2| ≈ 1.6–2.7 × 10⁵` at 22–29 tokens under
`Σ_HG`), decoding, canonicalizing and hashing — under `Σ⁺` with the
fact-level enumeration that Prop 4 licenses. On top of it: the **ball-coverage
consensus** (candidates: the inputs and their radius-1 neighbourhoods;
objective: inputs covered at `r`, then the truncated reach sum);
**reach-isolation** outlier scores (no input within reach `r` in either
direction) for the corruption test; the **interpolation path** (the alignment
between two canonical words, each interior word decoded); and the
**generative model** (a token sequence model over the collection's words,
sampled and decoded). Every object produced at this scale is a decoded
knowledge base; nothing at this scale exists for a certificate (Prop 7).

Complexity per step is stated with each algorithm; the language-scale
operations are exponential in `r` and are run at `r ≤ 2`.

## 6. Competitors and the capability matrix

**Distances on knowledge bases.** Exact HGED/SED oracle (`n ≤ 10`);
bipartite GED (edit-path cost and raw value, hypergraph-adapted with Qin's
costs); fact-level majority-vote merge with identities (the belief-merging
operator; the reference for RQ2, since it uses information our methods do not
have); WL histogram; NetLSD on the Levi graph; hyperedge portrait divergence;
HyperCOT where `N ≤ 20`; the certificate member (nauty-Levi canonical
labelling + Levenshtein, tokenized per canonical adjacency row); the two naive
floors `size_l1` and `degree_seq_l1`.

**Capability matrix** (columns filled by theorem or counterexample): *exact
at 0 · metric · polynomial pair · closed language · consensus is a decoded
object · certificate available · neighbourhood enumerable · generative model
definable*. The constructive and certificate members differ in exactly the
last four columns, and RQ2 and RQ5 are the experiments that show the
difference is real: the ball-coverage consensus on real variant series
(certificate: not computable), and the generative model with validity 1
(certificate: undefined). Both are small, both have a proposition behind
them, and both are tied to a knowledge-base task.

**The concession, stated once in the introduction.** For deciding
isomorphism and deduplicating a collection, the certificate member is
faster and equally exact; the paper does not compete on that and reports the
timing.

## 7. Data — real collections chosen to expose the hypotheses

*Selection rule.* Few collections, each carrying one research question with
a ground truth that is real or, where ground truth cannot exist without
intervention, obtained by controlled intervention on real substrates. The
synthetic suite of the previous iteration is retired except for the envelope
sweep (RQ6), where real data cannot span sizes. A self-contained
supplementary section (`supplementary_data.md`) documents every collection:
source, derivation, sizes, arity histogram, envelope yield, structural
repetition, and canonicalization timing.

| Collection | Derivation | Ground truth | Serves |
|---|---|---|---|
| **Entity knowledge bases of a hyper-relational knowledge graph** | **WD50K(66)** (Galkin et al. 2020): one knowledge base per entity = its statements with qualifiers, a hyperedge per statement over subject, object and qualifier values, labelled by the relation; constants anonymized. Probe (`foundation/probes_2026-09.md` §7): 3,994 entity KBs inside the envelope, 3,167 of them genuinely n-ary (55 % of hyperedges of arity ≥ 3; 79 % of KBs hyper-relational), median 8 constants, labelled canonicalization sub-second below ~17 constants, 13 % time-outs at 30 s in the largest buckets (reported as yield). WD50K(100) — 1,847 KBs, 99.8 % n-ary edges — is the purity control in the supplement; JF17K and WikiPeople were probed and rejected (33 % time-outs from label degeneracy; 88 % plain triples) | Wikidata `instance of` types, fetched for every in-envelope entity (100 % coverage); one label per entity by the most frequent type; 14 classes with ≥ 20 members cover 87.5 % of the collection (`human` 1,830, `film` 1,092, `big city` 171, …) — imbalance stated, per-class support reported, a super-class coarsening as the fallback | RQ1, RQ3, RQ4, RQ5, RQ6 |
| **Quarterly co-formulation knowledge bases of pharmacologic classes** | **NDC-classes** (FDA National Drug Code directory, ARB release; Benson et al. 2018): nodes are pharmacologic classes, each marketed product is a fact over the classes it belongs to, timestamped by first marketing; the knowledge base of class `c` in quarter `t` is its set of co-formulation facts that quarter; consecutive quarters of one class are real variants and the fact-level change between them is exact because node identities persist. Probe (`foundation/probes_2026-09.md` §6): of twelve temporal datasets the only one with a usable one-edit rate — 1,432 encodable members, 555 consecutive pairs, 120 one-edit (21.6 %), 85 identical, 14 classes with ≥ 3 one-edit pairs; 67 % of facts n-ary; constants anonymous but typed by the FDA class type carried in the name (`[epc]` 514, `[moa]` 278, `[pe]` 113, untyped 256). NDC-substances (2,222 members, 3.2 % one-edit, full unlabelled feasibility) is the control in the supplement | the exact fact-level difference between consecutive members; the held-out next quarter | RQ2 (consensus without identity), RQ1 (false merges), RQ6 |
| **Semi-synthetic corruptions of real knowledge bases** | real members of the two collections above with injected fact-level errors of stated type (spurious fact, missing fact, wrong argument) and budget; the iso-twin construction (a WL-preserving swap applied to a real member) as the exactness probe | injected labels | RQ3 |
| **Envelope sweep** | random connected labelled knowledge bases over `(m, k, \|Σ_V\|, \|Σ_E\|)` | — | RQ6 only |

Retired: the contact-network induced ego-networks (too dense: 26 usable
knowledge bases; kept only as a row of the envelope table), the planted
families and Stratum C of the previous iteration, the HIC atlas.

## 8. Scope statement

The claims are scoped to knowledge bases inside the measured envelope (facts
in the low hundreds, arity ≤ 5, labelled), to collections of any size `N`, and
to fact-level neighbourhoods of radius ≤ 2 at the language scale. The
Limitations section of the paper is written last, from the measurements,
and states the envelope, the two-scale resolution, and the concession on
identity speed; nothing else is pre-committed.

## 9. Risks and pre-agreed fallbacks

| Risk | Fallback |
|---|---|
| The temporal probe finds no dataset with enough in-envelope one-edit series | use the qualifier-rich entity collection with successive Wikidata revisions of the same entities (real variants, fetched) or, failing that, controlled fact edits on real entity knowledge bases |
| Entity types are too coarse or too sparse for RQ4 | use relation profiles as the class label and say so; the census and the dendrogram remain unsupervised exhibits |
| `Σ⁺` engineering (decoder + C++ + tests) does not fit the schedule | run the language scale under `Σ_HG` with the measured 52–55 % coverage and state Prop 4 as the extension's promise for the follow-up |
| The generative model's fidelity is poor | validity 1 and the certificate impossibility (Prop 7) still hold; report fidelity as measured and keep the exhibit short |
| Reviewer: "why not just the certificate member?" | the last four matrix columns, RQ2 and RQ5, and the timing concession |

## 10. Future work (named, not done)

The search-space program — enumeration by cost level, minimal countermodels,
black-box structural optimization — and the repair and entailment problems
(nearest model of a sentence by ball enumeration, which Prop 4 makes
well-founded at radius ≤ 2); sequence models beyond n-grams over the
language; a per-component encoding lifting the connectedness assumption.

## 11. Vocabulary — the two things the word means, and why both change

The project uses "vocabulary" in two senses, and this section treats both
because the PI's question concerns the first.

### 11.1 The instruction alphabet: a conservative language extension `Σ⁺`

**Why touch the alphabet at all.** The preprint fixed `Σ_HG` and the metric
space article inherited it unchanged. Two facts measured on 2026-09-03 say
the language, not the metric, is where the ambient claims live: (i) one
structural edit moves the canonical word by half its length, so `d_I` cannot
resolve fact-level neighbourhoods; (ii) a one-fact variant is nonetheless
reachable from the canonical word by one or two token edits in only 52–55 %
of cases — the other cases need pointer moves to bring a pointer onto the
fact's constants, and the number of moves is a layout artefact. The
extension removes exactly that artefact. It is a shift from the preprint of
the kind the venue values — a new language over the same machine — and it
makes a class of statements provable that are only measurable today.

**What is added (decoder side only).** Ranks: the virtual machine numbers
vertices in creation order (the seed is rank 0). Two token families:

- `A[ℓ; r_1 … r_a]` — hyperedge labelled `ℓ` over the vertices of ranks
  `r_1 < … < r_a`, `1 ≤ a ≤ k`. No pointer or list change. Total: ranks
  beyond the current vertex count are clamped to the last vertex, repeated
  ranks collapse, an existing `(ℓ, support)` is a no-op.
- `A⁺[ℓ; λ; r_1 … r_i]` — one fresh vertex with label `λ` and the hyperedge
  labelled `ℓ` over the `i` ranked vertices plus the fresh one,
  `1 ≤ i ≤ k−1`; ranks are clamped before the fresh vertex is created. List
  placement follows `V`: the first `A⁺` of a run inserts after `p_1`, and
  each further consecutive `A⁺` inserts after the vertex the previous one
  created, so a run of `j` such tokens lays out and numbers its vertices
  exactly as one `V` with `j` fresh vertices would.

Three pins fixed by the prototype (2026-09-03, `foundation/probes_2026-09.md`
§8): `a ≥ 1` and `i ≥ 1` are what carries connectivity; in the anchored
encoding the anchor carries the *maximum* vertex label, so it is the
canonical seed (rank 0) by the seed cascade's first rung (300/300 measured);
and the run-chaining placement above — the prototype showed that neither
emission order under a plain "insert after `p_1`" rule reproduces both `V`'s
layout and `V`'s ranks, so the chaining is part of the token's semantics.

**What is not touched.** The canonical encoder emits only `V`, `C`, `P`,
`N`; the canonical word `w*_c`, Theorem A, Corollary A, the length lemma, the
compactness result and every frozen number are unchanged, because `Σ⁺` only
enlarges the set of *decodable* words. The extension is conservative in the
strict sense: `Σ_HG ⊂ Σ⁺`, `S2H⁺` restricted to `Σ_HG*` is `S2H`.

**What it costs.** One proposition (2⁺: totality and connectivity, an
immediate extension of the prefix induction); the decoder cases for `A` and
`A⁺` in Python and C++ (small; the VM already has ranks implicitly as
creation order); the `Σ⁺` token enumerator for balls; tests pinning that
canonical words are unchanged.

**What it buys, as theorems.** Proposition 4: on anchored encodings a fact
insertion is one token and a fact deletion one token unless the fact's token
created fresh constants, in which case at most as many tokens as constants
it created; hence the string ball of radius `r` around `w*_c(K)` contains
every knowledge base within `r` fact insertions of `K`, and the ball of
radius `(k−1)r` every knowledge base within `r` fact edits. Proposition 5
then makes the ball-coverage consensus provably complete for insertion
variants. Proposition 6 makes single-token moves of a generative model
fact-level moves. None of these is available under `Σ_HG`, where the
pointer displacement puts an `O(kn)` factor in every bound — the same factor
that makes the old HGED envelope vacuous.

**What it does not buy, said now.** Reach is not equivalent to fact-level
distance: a pointer-token edit inside a word changes the decoded knowledge
base globally, so words at small token distance may decode to structurally
distant objects. Balls are supersets of fact-level neighbourhoods, never
equal to them; the paper states the inclusion, not an equivalence. The full
`Σ⁺` ball is `Θ(n^k)` per origin (measured 15,000–46,000 words at radius 1
against 460–800 under `Σ_HG`), so coverage is computed by the targeted
witnesses of Proposition 4, not by enumeration. And because a token
*substitution* replaces one fact by another — two fact-level operations in
one token — the consensus coverage is defined on the **indel ball**
(insertions and deletions only): with substitutions every copy of a variant
collection covers every other copy at radius 1 (measured), whereas on the
indel ball the source covers all `N` at radius `t` and no copy reaches
another in fewer than two edits. The metric `d_I` keeps its two-scale
character; the extension changes the language scale only.

**How it will be justified in the paper.** As the second contribution of the
representation: the preprint gave the machine and its complete canonical
form; this article gives the *language* — closure (Prop 2), the
fact-level-complete extension (Prop 4) and the generative closure (Prop 6) —
and shows what each licenses on knowledge bases.

### 11.2 The paper's glossary (additions to `logic_models/vocabulary.md`)

Each term is added because a claim needs it and no existing name says it.

- **Canonical-word metric.** `d_φ(A,B) = d_Lev(φ(A), φ(B))` for a complete
  invariant `φ` into words; a metric on isomorphism classes. *Constructive
  member*: `φ = F_c`. *Certificate member*: `φ` = canonical-labelling
  certificate. Needed to state the family and place nauty-edit in it.
- **Language.** A set of words closed under the alphabet with a total
  decoder into objects. Needed for the distinction that carries RQ5 and
  Prop 7.
- **Certificate (of a consensus).** `cost(M)/LB` with
  `LB = Σ_{i<j} d(K_i,K_j)/(N−1)`; an upper bound on `cost(M)/OPT`. Needed
  because the medoid's guarantee is otherwise only asymptotic.
- **Reach.** `reach(K → K') = min{ r : class(K') ∈ classes(S2H(B_r(w*_c(K)))) }`;
  directed; `reach ≤ d_I`. Needed to name the language-scale distance.
- **Ball coverage.** `cov_r(M) = #{ i : reach(M → K_i) ≤ r }`. Needed to
  define the language-scale consensus.
- **Variant series.** A sequence of knowledge bases of one subject over
  time or over sources, whose consecutive members differ by few facts.
  Needed to name the real ground-truth collections.
- **Iso-twin.** A non-isomorphic knowledge base with the same size, degree
  sequence and WL colouring as another. Needed for the exactness probe.

## 12. Section plan of the paper

1. Introduction — the problem, the four prerequisites and the fifth
   (language), the concession, the contributions.
2. Related work — distances on structures and their metricity; median graphs
   and strings; belief merging; canonical forms in mining; metric-space
   analytics; molecular string languages as the closed-alphabet precedent.
3. Knowledge bases as hypergraphs; the machine, the alphabet, the canonical
   word, the language extension.
4. The metric space — Theorems 1–2, Propositions 1–3, 8–9.
5. The language — Propositions 2, 2⁺, 4–7; the two-scale geometry with its
   measurement.
6. The toolkit — algorithms and guarantees at both scales.
7. Experiments — RQ1–RQ6, one evaluation each, on the collections of §7;
   the decodability figure in RQ5.
8. Limitations, written from the measurements.
9. Conclusion and future work.
