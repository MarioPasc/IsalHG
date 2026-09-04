# Knowledge bases as words — the article's storyline (v7, PI-ratified scope)

*This document is the narrative of the IsalHG journal article, target IEEE
Transactions on Knowledge and Data Engineering. It states the premise, the
research questions and the hypothesis each one tests, the theory the paper
proves, the algorithms it ships, the data it runs on, the competitors it
faces, and the one evaluation each application receives. Every proof,
experiment and figure serves one research question; anything that serves none
is cut. Engineering (tasks, gates, statuses) lives in `../DEVELOPMENT/`; the
verified fact base behind every number quoted here is in `foundation/`.
Version 7, 2026-09-04, rewritten after the PI ratified the scope
(`START_HERE.md` §6.0 records his answers verbatim and their consequences).*

**Three standing rules.** (i) Experiments start from zero: no result of the
previous iteration is load-bearing unless re-measured on the collections of
§7. (ii) One story, one evaluation axis per application: every experiment
answers a question *about knowledge bases*, and the metric that answers it is
the only metric reported for it. (iii) The logical machinery stays out of
this manuscript — knowledge bases are treated as data, not as models of
sentences; the logic program is the follow-up paper (§10).

**The alphabet gate, and its answer.** The PI ratified changing the
instruction alphabet and set the criterion: *similar knowledge bases must
encode to strings at small Levenshtein distance*. It has been measured
(§2.3, RQ1, `foundation/probes_2026-09.md` §9): fact tokens addressed by
**global canonical rank** meet it — one token per fact insertion against half
the word under the inherited pointer alphabet — local colour-based addressing
is refuted, and the residual boundary is a change of the constant set. The
adopted encoding carries §§3–7.

---

## 0. The paper in six sentences

A knowledge base is a finite set of facts over constants whose identities are
anonymous, untrusted or irrelevant, so two knowledge bases that differ only by
renaming their constants are the same knowledge base; facts of arity three and
above — a statement with qualifiers, a product over the classes it belongs to —
make the object a hypergraph rather than a graph. Comparing, aggregating,
organizing and generating *collections* of such knowledge bases therefore
requires a distance on isomorphism classes, and every existing candidate lacks
at least one of five prerequisites: exactness at zero, the metric axioms,
polynomial per-pair cost, a closed language in which every string is a
knowledge base, and local stability — similar knowledge bases at small
distance. We write each knowledge base as a word over an instruction alphabet
and give the first four by construction: exact identity, a metric with
computable optimality certificates, polynomial pairwise cost after one
canonicalization, and a language whose every prefix, edit and sample decodes
to a knowledge base. The fifth is a design problem in the alphabet itself, and
this paper's second contribution is to solve it: we show that the pointer-
addressed alphabet of our earlier work is locally unstable — one fact rewrites
half the word — and we design and measure fact-addressed alternatives against
that criterion. On the resulting representation we build the operations a
knowledge engineer actually performs on a collection — a representative
record, a data-quality screen, a description-pattern hierarchy, a map, and a
generator — each with the guarantee it needs, on two real collections:
qualifier-bearing entity descriptions from a hyper-relational knowledge graph,
and quarterly drug-class co-formulation records whose true fact-level changes
are known. Canonical-labelling engines decide identity faster and we say so
first; what they do not give is a language, and the last two contributions are
impossible without one.

## 1. Premise — collections of knowledge bases, and what people do with them

**Where collections come from.** The one-hop description of an entity in a
knowledge graph — its statements with qualifiers, hence n-ary facts; the fact
set extracted from one document, one source or one extraction run; the
anonymized or blank-node fragment of an RDF store; the record of which
categories a product belongs to in one reporting period. In each case an
engineer holds `N` knowledge bases over one schema, and in each case the
constants' identities are unavailable, untrusted or beside the point — the
*pattern* of facts is the object — so knowledge bases that differ by a
renaming must be treated as equal.

**What is done with them, and why each is a real task (PI's requirement).**

| Operation | The engineer's question | Where it is already done |
|---|---|---|
| **Representative** (medianoid) | *`N` descriptions of the same thing from different sources, runs or periods disagree — which one do I keep as the reference record?* | golden-record construction in master data management; consensus of extraction runs; the reference co-formulation pattern of a drug class in a period |
| **Outliers** | *Which descriptions in this collection are structurally anomalous — extraction errors, schema violations, vandalism, mis-typed entities?* | knowledge-graph error detection and data-quality screening, where the anomaly is the *shape* of the description, not a value |
| **Hierarchy** (dendrogram) and **k-medoids** | *Which description patterns exist in my collection, how many, and which are underpopulated?* | schema and pattern induction over a knowledge graph; audit of coverage; stratified sampling for annotation |
| **Map** (metric MDS) | *What does this collection look like — where are the dense regions and the strays?* | exploratory audit of a collection before any of the above |
| **Generation** | *Give me more knowledge bases like these* | benchmark construction; synthetic stand-ins for records that cannot be shared; completion suggestions |

Every one of these is a metric-space operation, and each is well posed, and
inherits a guarantee, only if the dissimilarity is a metric on isomorphism
classes: identity of indiscernibles gives exact duplicate handling, the
triangle inequality gives the representative its approximation ratio and the
engineer a certificate, and polynomial evaluation gives an `N × N` matrix at
all. Generation adds a requirement no metric supplies: a representation in
which *every string is an object*. And all of them, in practice, need the
fifth prerequisite — that near-identical inputs sit close — or the numbers
they produce describe the encoding rather than the data.

**No existing distance has the five together** (§6 has the matrix). Exact
structure edit distance is NP-hard per pair. Its bipartite (Hungarian)
approximation is polynomial but not a metric — in print (Serratosa 2019) and
measured here: the reported edit-path cost is asymmetric on 38 % of random
pairs and violates the triangle inequality on 1.4 % of triples, with an
explicit ten-vertex counterexample; its raw assignment value is a pseudometric
that cannot separate non-isomorphic knowledge bases. Weisfeiler–Leman,
spectral and portrait embeddings are vector metrics, and stable, but
incomplete: they merge non-isomorphic knowledge bases, at a rate we count on
real collections. Hypergraph optimal transport is a metric in theory whose
computed value is a local optimum of a non-convex problem, needs an external
measure, and has no decoder. A canonical-labelling certificate plus
Levenshtein is an exact polynomial metric — the certificate member of the
family we introduce, faster to compute, compared on every table — but a
certificate is not a language: an edited certificate is not a certificate, a
prefix of one is nothing, and no generative model is definable on the set of
certificates.

## 2. The representation

### 2.1 Knowledge bases as labelled hypergraphs

A knowledge base `K` is a finite set of facts; a fact is a predicate applied
to constants. Constants carry a type (the unary predicates true of them, where
the data provides them); facts carry their predicate as a label. Encoding E1:
constants are vertices labelled by type, each fact of arity `a ≥ 2` is a
hyperedge over its constants labelled by predicate, `k` is the maximum arity.
Encoding E1⊤ adds an anchor constant joined to every constant, which makes
constant insertion a fact and every knowledge base connected.

**Argument roles ride inside the fact token** (author decision, 2026-09-04).
A relation with named argument positions — a statement's subject, object and
qualifier values — is encoded as the labelled set of `(role, constant)` pairs,
so nothing is abstracted away and arity stays native. Under a fact-addressed
alphabet the role is one extra field per operand and costs nothing
structural; under the pointer alphabet, whose tokens have no role field, the
fallback is encoding E2 (an arity-2 incidence hypergraph with
position-labelled incidences), fully general but inflating the constant count
to `1 + |constants| + |facts|` and pushing members out of the feasibility
envelope. This is one more reason the alphabet decision of §2.3 matters. Under
each, `K ≅ K' ⇔ E(K) ≅ E(K')`, so every statement about hypergraphs below is
a statement about knowledge bases. *The paper does not develop the model
theory of this correspondence* (rule iii): it states the encoding, notes that
isomorphic knowledge bases are indistinguishable by any property that does not
name a constant, and moves on.

### 2.2 The word, and what is proved of it

An instruction alphabet is executed by a small machine that builds a
knowledge base; the encoder writes a knowledge base as a word, the interpreter
reads a word back. For the pointer alphabet `Σ_HG` inherited from our earlier
work, the tie-complete canonical word `w*_c(K)` and the augmented fingerprint
`F_c(K) = (seed type, w*_c(K))` give:

1. *Exactness.* `F_c(K) = F_c(K') ⇔ K ≅ K'` (Theorem A, proved, labelled case
   included).
2. *Metric.* `d_I(K,K') = d_Lev(F_c(K), F_c(K'))` over the token sequence is a
   metric on isomorphism classes (Corollary A, proved). Raw token
   Levenshtein; never the length-normalized variant, which is not a metric.
3. *Polynomial pairwise cost.* One canonicalization per knowledge base, then
   `O(L²)` per pair in tokens; measured in milliseconds on labelled real
   knowledge bases, with the frontier at the fact count, not the constant
   count.
4. *A closed language.* Every word decodes to a knowledge base: every prefix,
   every single-token edit (24,000/24,000 measured), every interior word of an
   alignment between two canonical words (62/62), every sample of any
   distribution over words.

**Compactness** rides along: the word is shorter than the incidence list under
a fixed-width code.

### 2.3 The fifth prerequisite, and the alphabet decision (RQ1)

`Σ_HG` addresses the constants of a fact *relatively*, by where a set of
pointers happens to stand after every earlier instruction. The canonical word
is therefore a layout as much as a content, and a single new fact perturbs the
layout: measured, one structural edit rewrites **0.51–0.54 of the word** on
random substrates. Similar knowledge bases are not close. That is a defect of
the alphabet, not of the idea — and the PI's ratified criterion is exactly
this property, so the paper's second contribution is to fix it.

**The design space** is how a fact names its constants:

| | Addressing | One new fact costs | Risk |
|---|---|---|---|
| **A — pointer (inherited)** | relative to a moving pointer state | a token plus every downstream layout shift | measured: half the word |
| **B — global canonical rank** | the constant's position in an isomorphism-invariant total order | one token *if* the order is unchanged | a new fact can permute the order, rewriting every token that mentions a re-ranked constant |
| **C — local address** | `(structural colour, index within colour)`, the colour from a bounded-depth refinement | one token *if* the colours are unchanged | refinement is local, so damage should be bounded — untested |

All three are complete invariants under an isomorphism-invariant ordering, so
exactness and the metric survive any choice; what differs is the topology. The
selection rule was **pre-registered before the measurement**: adopt the scheme
with the best measured local stability, whichever it is, keep the others with
their numbers in the supplement, and explain why the winner wins.

**Measured (`foundation/probes_2026-09.md` §9; 31,279 single-edit pairs over
synthetic, NDC and WD50K members). C is falsified outright; B is adopted for
the regime it wins, which is not every regime — see the trade-off below.**

| | A pointer | **B global rank** | C local colour |
|---|---|---|---|
| single-edit response, normalized median (synth / NDC / WD50K) | 0.500 / 0.500 / 0.500 | **0.188 / 0.211 / 0.300** | 1.000 / 1.000 / 1.000 |
| one fact inserted over existing constants | 15 / 7 / 5 tokens | **1 / 1 / 1 token** | 25 / 14 / 14 tokens |
| canonicalization | 1.1–1.7 ms median, p90 2.2–8.3 s, 6 % censored | **20–60 µs, none censored** | 20–60 µs |
| completeness and iso-invariance (3,000 instances) | 0 violations | 0 violations | 0 violations |

The result that generalizes beyond this paper is *why* C fails. A refinement
colour is a hash of the whole refinement history, so one fact edit moves
92–98 % of the colours — no edit among 5,724 left the colour multiset intact,
and even depth 1 moves 36–52 % — whereas the canonical rank order is untouched
by 68–85 % of edits. Putting a colour *identity* inside an address makes every
symbol change at once. **Address symbols must be positional, not
content-hashed**, and that is a statement about canonical forms in general,
not about our alphabet.

**The boundary is a trade-off, not a caveat, and it is the more interesting
result.** B's locality holds for edits that leave the constant set alone and
**inverts** when an edit adds or strands a constant, because any
isomorphism-invariant total order renumbers when the set it orders changes.
Measured on the real NDC series, split by regime (140 constant-preserving
pairs, 415 changing):

| | pointer (A) | rank (B) |
|---|---|---|
| preserving: median distance at Δ = 1 | 5 tokens | **1 token** |
| preserving: pairs within 2 tokens | 0.167 | **0.771** |
| changing: median distance at Δ = 1 | **4 tokens** | 7 tokens |
| changing: pairs within 2 tokens | **0.400** | 0.000 |
| changing: ρ(constants moved, distance) | 0.430 | 0.503 |

So the pooled figures above are an average over a mix that is 1:3 against B on
this corpus, and the honest statement is a **trade-off with a mechanism**: a
content-addressed encoding pays for every *fact* edit, a position-addressed one
pays for every *constant* edit.

**The trade-off is an obstruction, not an unexplored gap.** The missing third
point — positional addressing *within* a locally determined class, which
should have inherited the virtues of both — was built and measured, in a fine
and a coarse variant. It is worse than either: it **never** lands within two
tokens of a one-edit neighbour (0 of 31,279 pairs), where B is within *one*
token on 38–52 % of constant-preserving pairs. The reason is the sentence the
paper should keep: in every constant-preserving row the fraction of edits that
leave the address map entirely intact is **0.000** — no edit among 21,528 —
because a fact insertion *is* a change to the incidence data such a key reads,
whereas B's profile is bimodal and nothing moves at all on 57 / 43 / 22 % of
those edits. **Locality is won by the mass of zero-cost edits, not by a low
average damage.**

**Frontier (Prop 13).** For an isomorphism-invariant address map `A` on
constants: if `A` is content-determined, every fact edit changes it at the
edit site, so its cost is never zero; if `A` is position-determined, it is
untouched with probability `p` under fact edits (measured 0.22–0.57) but
renumbers `Θ(|w|)` whenever the constant set changes; a hybrid inherits both
costs. An addressing that is `O(1)`-local under both would require an
identifier that is not a function of the isomorphism class — extrinsic naming,
which invariance forbids. B is adopted because it maximizes the zero-cost
fraction, and the article reports the frontier as a result.

**The consequence the paper states itself, rather than leaving to a
reviewer.** B is, in substance, a canonical labelling serialized to a sorted
fact list, and its distance correlates with the canonical-labelling
certificate distance at ρ = 0.62–0.96. The article's distinctiveness therefore
rests on what a certificate does not have — the closed language, total
decoding, the certified ball-coverage representative, and generation with
validity 1 — and that argument is made explicitly in §6 and tested in RQ3 and
RQ6, not implied by a claim of novelty in the addressing.

## 3. Research questions

Each question names the knowledge-base problem it answers, the hypothesis, the
evidence, and the single evaluation it receives. They are the paper's
sections, in order.

### RQ1 — Representation design. *Which addressing scheme makes similar knowledge bases close, and at what cost in exactness, compactness and time?*

- **Hypothesis (falsified twice, and the paper says so).** Pointer addressing
  is locally unstable — confirmed, one fact ≈ half the word on every corpus.
  Local `(colour, index)` addressing was predicted to be the stable one —
  **refuted**: it is the worst, because a refinement colour is a global hash
  (one edit moves 92–98 % of colours). Its repair, positional addressing
  within a *locally determined* class, was then built and is **also
  refuted** — 0 of 31,279 pairs within two tokens. Global canonical ranks,
  predicted to sit in between, are the best, at one token per fact insertion,
  with a characterized inversion when the constant set changes. The three
  failures together give the frontier proposition (Prop 13), which is a
  stronger result than any single encoding would have been.
- **Evidence.** The three encodings on the same instances: single-edit
  response per edit kind on synthetic and on both real collections; the
  correlation with the *known* fact-level difference on the real variant
  series; a locality measurement of the refinement colouring that explains the
  refutation; empirical completeness and iso-invariance; token counts;
  wall-clock.
- **Evaluation.** Median and interquartile single-edit response, absolute and
  as a fraction of the word, and Spearman correlation with the true fact-level
  difference — the PI's criterion, stated as a number.
- **Reading (contract, pre-registered and honoured).** The encoding with the
  best measured local stability carries the rest of the paper, whatever its
  relation to the certificate baseline; the others are reported in the
  supplement with their numbers. The selection was made on the measurement
  (`foundation/probes_2026-09.md` §9) and the losing arms are documented, not
  discarded.

### RQ2 — Well-posedness. *Which distances on isomorphism classes satisfy the prerequisites the five operations need, and what does each missing one do to a real collection?*

- **Hypothesis.** Only canonical-word metrics satisfy exactness, the metric
  axioms and polynomial cost together; only ours adds a closed language. Each
  missing prerequisite has a measurable effect: false merges for incomplete
  embeddings, metric violations for the bipartite pipeline, time-outs for
  exact oracles.
- **Evidence.** Theorems and propositions for ours; the counterexample and
  violation rates for the bipartite pipeline; the false-merge census on the
  real collections; the oracle ceiling.
- **Evaluation.** The capability matrix, filled by theorem or counterexample,
  and one table of measured consequences.

### RQ3 — The representative record. *Given `N` descriptions of one thing that disagree, which is the reference, and with what guarantee?*

- **Hypothesis.** The medoid satisfies `cost ≤ (2 − 2/N)·OPT` in any metric,
  and the pairwise bound `LB = Σ_{i<j} d(K_i,K_j)/(N−1) ≤ OPT` gives every
  candidate a certified ratio (measured ≤ 1.63). Where the collection's
  members are fact-level variants of one source, a consensus computed in the
  language — the candidate whose radius-`r` string ball decodes to the most
  members — identifies the source, which no method restricted to returning an
  input can do.
- **Evidence.** Quarterly co-formulation records: consecutive quarters of one
  drug class are real variants with a known fact-level difference; the methods
  see only anonymized members.
- **Evaluation.** The exact fact-level distance from the returned
  representative to the held-out next quarter, against the certified medoid
  and against the identity-using majority merge (which uses information our
  methods do not have).

### RQ4 — The data-quality screen. *Which descriptions are structurally anomalous, and does exactness change the answer?*

- **Hypothesis.** Distance-based scores over a metric on isomorphism classes
  rank anomalous descriptions correctly; incomplete representations put
  non-isomorphic knowledge bases at distance zero and therefore hide anomalies
  whose statistics match the inliers.
- **Evidence.** Injected fact-level errors of stated type and budget on real
  members (spurious fact, missing fact, wrong argument), and the *iso-twin*
  construction — a non-isomorphic twin matching size, degree sequence and
  refinement colouring.
- **Evaluation.** Area under the ROC curve for recovering the corrupted
  members, per corruption type, per representation.

### RQ5 — Description patterns. *Which patterns of description exist in a collection, and does the structure recover known kinds?*

- **Hypothesis.** The space is non-Euclidean (`ν > 0`), which licenses
  medoid-type estimators and metric MDS rather than centroids and classical
  MDS; hubness is moderate; under those licences k-medoids and average-linkage
  hierarchies over the chosen encoding recover entity kinds from structure
  alone.
- **Evaluation.** Adjusted Rand index against Wikidata entity types with
  per-class support (the label set is imbalanced and this is stated);
  cophenetic correlation for the hierarchy. The map is a figure with its
  stress, not an evaluation.

### RQ6 — Generation. *Can a collection be extended with new, valid, plausible knowledge bases?*

- **Hypothesis.** Because every word decodes, any distribution over words is a
  distribution over knowledge bases with validity 1 and no rejection step; a
  certificate-based representation admits no such model. The alignment path
  between two canonical words is a sequence of valid knowledge bases; between
  two certificates it is nothing.
- **Evidence.** A token sequence model (order-3/4 n-gram or a small recurrent
  model) fitted on a real collection's words and sampled, against an
  incidence-list generator that must reject invalid outputs; the decodability
  figure.
- **Evaluation.** Validity rate (1.000 by theorem for ours; measured for the
  baseline) and structural fidelity — the divergence between the size, arity
  and label profile of the samples and of the collection.

### RQ7 — Operating envelope. *For which knowledge-base sizes, arities and vocabularies does this run, and how does cost scale with `N`?*

- **Hypothesis.** Cost is `N` canonicalizations plus `N²` string comparisons;
  the canonicalization frontier is the fact count, not the constant count
  (measured: `m ≤ 111` in ~0.03 s, `m ≥ 253` never); labels are the
  tie-breaker (labelled milliseconds where the unlabelled form fails at
  thirteen constants). Fact-addressed encodings should be dominated by the
  canonical-ordering call and be markedly cheaper.
- **Evaluation.** One envelope figure over `(m, k, |Σ|)` on random knowledge
  bases — the single place synthetic data is indispensable, since real
  collections do not span sizes — with the real collections placed on it, and
  the yield table per collection.

## 4. Theory delivered

| # | Statement | Status | Serves |
|---|---|---|---|
| Thm 1 | Exactness: the canonical word is a complete isomorphism invariant of labelled knowledge bases, for any isomorphism-invariant addressing (pointer, global rank, local address) | proved for `Σ_HG` (Theorem A); the fact-addressed case is a short argument via invariance of the address map — to be written with RQ1's choice | RQ1, RQ2, RQ4 |
| Thm 2 | Metric: `d(K,K') = d_Lev` on the canonical token sequences is a metric on isomorphism classes, one `(alphabet, depth, vocabulary)` per comparison | proved (Corollary A); ports verbatim | all |
| Prop 1 | Length and key size: `\|w\| ≤ m(1+kn)` for the pointer alphabet, `\|w\| = n + m` for the fact alphabets; fixed-width bits against the incidence list | proved / immediate | RQ1, RQ7 |
| Prop 2 | Closure: the interpreter is total, so every word — prefix, edit, alignment interior, generated sample — decodes to a knowledge base (and, for `Σ_HG`, a connected one) | closure proved; connectivity written here | RQ3, RQ6 |
| Prop 3 | Certificates: medoid `≤ (2 − 2/N)·OPT`; `LB ≤ OPT`; hence `LB ≤ OPT ≤ Σ_i d(M, K_i)` certifies any candidate | proved (Jiang–Münger–Bunke 2001 for the medoid) | RQ3 |
| Prop 4 | Fact-level simulation: under a fact-addressed alphabet a fact insertion is exactly one token, so the ball of radius `r` contains every knowledge base within `r` fact insertions; under the pointer alphabet the same holds only through non-canonical words, with the pointer displacement as an additive cost | measured for the pointer case (1,200/1,200 insertion witnesses, 717/717 deletions); immediate for the fact case | RQ1, RQ3 |
| Prop 5 | Source identifiability on the indel ball: if the members are `t` fact insertions from a common source, the source covers all `N` at radius `t` while no member reaches another in fewer than `2t` | measured (source unique maximiser 12/12 at both noise levels; member-to-member reach 0.00–0.02) | RQ3 |
| Prop 6 | Generative closure: any distribution over words pushes forward to a distribution over knowledge bases; autoregressive generation is valid at every prefix | immediate from Prop 2 | RQ6 |
| Prop 7 | Certificate sets are not languages: not closed under any edit, no total decoder, no prefix property; hence no ball, path or generative model exists on them | to be written (short) | RQ2, RQ6 |
| Prop 8 | The bipartite edit-path cost is not a metric (counterexample `d(A,B)=2, d(B,C)=4, d(A,C)=7` on 3+3+4 vertices); its raw assignment value is a pseudometric with false zeros | proved by counterexample; rates measured | RQ2 |
| Prop 9 | Incompleteness of refinement-based keys on hypergraphs | cited + measured merges | RQ2, RQ4 |
| Obs 10 | Instability of pointer addressing: one fact edit moves the canonical word by a constant fraction (measured 0.500 normalized median on all three corpora), with the two mechanisms named | measured; the lower-bound construction is time-boxed with a pre-agreed fallback to the measurement | RQ1 |
| Obs 11 | Address symbols must be positional, not content-hashed: a refinement colour is a global function of the knowledge base (one fact edit moves 92–98 % of depth-3 colours; 36–52 % at depth 1), so a colour-identity address rewrites the whole word, while a canonical rank order survives 68–85 % of edits | measured (5,724 edits) | RQ1 |
| Obs 12 | **The addressing trade-off.** Any isomorphism-invariant total order renumbers when the constant set changes, so a position-addressed encoding is one-token-local under fact edits and pays globally under constant edits, while a content-addressed one pays under fact edits: measured inversion on the real series (rank encoding 1 token vs 5 at Δ=1 when constants are preserved; 7 vs 4 when they are not, its distance tracking constants moved at ρ = 0.503) | measured on both regimes, four encodings | RQ1, RQ3 |
| **Prop 13** | **Addressing frontier.** For an isomorphism-invariant address map: content-determined addresses change at the edit site of every fact edit (measured: 0 of 21,528 edits left such a map intact); position-determined addresses are untouched with probability 0.22–0.57 under fact edits but renumber `Θ(\|w\|)` when the constant set changes; hybrids inherit both. `O(1)`-locality under both edit kinds requires an extrinsic identifier, which invariance forbids. Corollary of practice: locality is won by the mass of zero-cost edits, not by low average damage | measured over four encodings and 31,279 pairs; the proposition is to be written from it | RQ1 |

Not claimed: a faster isomorphism test; an edit-distance proxy; scaling to
large knowledge bases.

## 5. The toolkit

Canonicalize once per knowledge base; census (distinct classes, frequencies,
exact duplicates); `N × N` token-Levenshtein matrix. On the matrix:
**representative** = medoid with its certified ratio, refined in the language
by ball coverage where the collection is a variant series; **anomaly scores** =
k-nearest-neighbour distance and local outlier factor over the precomputed
metric, plus rare-class scores from the census; **patterns** = k-medoids and
average-linkage hierarchy with cophenetic correlation; **map** = metric MDS
with stress and the spectrum that excludes classical MDS; **generation** = a
token sequence model over the collection's words, sampled and decoded.
Complexity is stated with each algorithm; the language-scale operations are
exponential in the radius and run at `r ≤ 2`.

## 6. Competitors and the capability matrix

Exact structure edit distance (small instances only); bipartite GED in both
readings; the identity-using majority merge (the reference for RQ3, since it
uses information we deny ourselves); WL histogram; NetLSD; hyperedge portrait
divergence; hypergraph optimal transport where it is affordable; the
certificate member (canonical labelling plus Levenshtein); the two naive
floors. Columns: *exact at 0 · metric · polynomial pair · closed language ·
locally stable · consensus is a decoded object · certificate available ·
generative model definable*. The **locally stable** column is new and is what
RQ1 fills; the last three are where the certificate member differs from us,
and RQ3 and RQ6 are the experiments that make the difference visible.

**Conceded once, in the introduction.** For deciding isomorphism and
deduplicating a collection, the certificate engines are faster and equally
exact; we do not compete there and we report the timing.

## 7. Data

Unchanged from the ratified plan and documented in full in
[`supplementary_data.md`](supplementary_data.md): **WD50K(66)** entity
knowledge bases (3,167 genuinely n-ary members in the envelope; Wikidata types
as class labels, imbalance stated; WD50K(100) as purity control) and
**NDC-classes** quarterly co-formulation knowledge bases (1,432 members, 21.6 %
of consecutive quarters one-edit variants with exact fact-level truth;
NDC-substances as control); controlled corruptions of real members for RQ4;
one synthetic envelope sweep for RQ7. Retired after probing: the planted
families and size-controlled strata of the previous iteration, the contact
induced ego-networks, the HIC atlas, JF17K, WikiPeople, and ten of the twelve
temporal datasets.

## 8. Scope

Claims are scoped to knowledge bases inside the measured envelope (facts in
the low hundreds, arity ≤ 10, labelled), to collections of any size `N`, and —
for the language-scale operations — to neighbourhoods of radius ≤ 2. The
Limitations section is written last, from the measurements, and carries the
envelope, whatever instability RQ1 leaves standing, and the concession on
identity speed.

## 9. Risks and pre-agreed fallbacks

| Risk | Fallback |
|---|---|
| ~~No fact-addressed encoding is locally stable~~ | **resolved**: global-rank addressing gives one token per fact insertion (`foundation/probes_2026-09.md` §9) |
| **Global-rank addressing won its regime and correlates with the certificate distance at ρ = 0.62–0.96** (materialized) | adopted for that regime under the pre-registered rule, and **said in the paper**: the distinctiveness is the closed language — total decoding, the ball-coverage representative, generation with validity 1 — carried by RQ3, RQ6 and the decodability figure; the certificate engine becomes a family member we cite rather than a competitor we beat. Losing encodings and their numbers are in the supplement |
| **The consensus substrate sits in the weak regime** (materialized and quantified): 74.8 % of natural NDC consecutive pairs change the constant set, and restricting to the preserving regime leaves **15 drug classes with a run of ≥ 3 quarters and 2 with ≥ 5** — too small to carry RQ3 alone | RQ3 runs on constant-preserving ladders over *real* members (injected fact edits on real knowledge bases, constant set held) with the natural series reported beside them as the harder case; the alternative — moving the substrate — is an open scoping decision recorded in `foundation/probes_2026-09.md` §9 |
| Roles cost stability under the adopted encoding (unmeasured — the roles arm was run only on the falsified encoding) | measure before the experiments; the fallback is to carry roles as an edge-label refinement instead of a token field |
| A new alphabet costs more engineering than the schedule holds | the pointer alphabet remains available for every experiment except RQ1, whose comparison is the contribution either way |
| Entity types too imbalanced for RQ5 | per-class support with macro-averaging, or a super-class coarsening; the hierarchy remains an unsupervised exhibit |
| Generation fidelity poor | validity 1 and the certificate impossibility still hold; the exhibit stays short |

## 10. Future work (named, not done)

**The logic paper.** Every finite model of a first-order sentence is a
labelled hypergraph, so the representation supports minimal countermodel
search, nearest-model repair and entailment forcing as metric queries on model
space. The PI's decision is that this is a second manuscript, not a section of
this one; the material is developed in [`logic_models/`](logic_models/) and is
not drawn on here beyond the encoding. Also future: sequence models beyond
n-grams over the language; a per-component encoding lifting connectedness;
ordered and repeated arguments natively rather than through E2.

## 11. Vocabulary

The word means two things in this project. §11.1 is the instruction alphabet —
the PI's D3′ decision. §11.2 is the paper's glossary.

### 11.1 The alphabet: from a pointer language to a fact language

**Why this is on the table.** The preprint fixed the pointer alphabet, and the
metric-space work inherited it. The PI's ruling is that we are not bound by
it, that a change increases the distance from the preprint (which the venue
values), and that the criterion is topological: *KBs parecidas deben
codificarse en cadenas cuyas distancias de Levenshtein sean pequeñas*.

**What is inherited and what changes.** The machine, the closed alphabet, the
total decoder, the completeness argument and the metric corollary are
alphabet-parametric: they depend on the address map being isomorphism-
invariant and on every construction token attaching to something already
present, not on *how* a token names its operands. What changes is the
addressing, and with it the topology. Concretely, a fact-addressed word is a
type prefix plus one token per fact, sorted — length exactly `n + m` against
the pointer alphabet's `m(1+kn)` bound — with the constants addressed as in
§2.3 B or C.

**An earlier, weaker proposal, and why it is not enough.** A previous draft
proposed adding fact tokens to the *decoder* only, leaving the canonical
encoder untouched: this makes a one-fact variant *reachable* in one token edit
through a non-canonical word (measured: insertion witnesses 1,200/1,200,
deletion witnesses 717/717, source identification 12/12) while leaving the
distance between canonical words at half the string. That satisfies the
neighbourhood queries but **not** the PI's criterion, which is about the
distance itself. The decoder-side tokens remain useful — they are what makes
Props 4–5 constructive — but the encoder must change too, and RQ1 decides how.

**The honest price, now paid.** A new canonical encoder means re-proving
completeness for it (short, since the address map carries it — and measured
clean over 3,000 instances), re-implementing the encoder, and re-scoping every
frozen `Σ_HG` measurement as a statement about the pointer alphabet: nothing
is invalidated, things are labelled. The gains, measured rather than hoped:
one token per fact insertion instead of half the word; canonicalization from
milliseconds-to-seconds with a 6 % censor rate down to tens of microseconds
with none; word length `n + m`; and the connectedness restriction lifted,
since a fact language can express a disconnected knowledge base and the
pointer language cannot. The cost is compactness on sparse knowledge bases
(one type token per constant, where the pointer encoding amortizes constants
into the tokens that create them) and the renumbering boundary of §2.3.

### 11.2 Glossary (additions to `logic_models/vocabulary.md`)

Each term earns its place by a claim that needs it.

- **Canonical-word metric.** `d_φ(A,B) = d_Lev(φ(A), φ(B))` for a complete
  invariant `φ` into words. *Constructive member*: ours. *Certificate
  member*: canonical labelling plus serialization. Needed to state the family
  and place the competitor inside it.
- **Language.** A set of words closed under the alphabet with a total decoder
  into objects. Needed for RQ6 and Prop 7.
- **Addressing.** How a fact token names its constants: pointer, global rank,
  or local `(colour, index)`. Needed to state RQ1.
- **Local stability.** The distribution of `d(K, K ⊕ f)` over single fact
  edits. Needed because "similar KBs are close" must be a measured quantity,
  not an impression.
- **Certificate (of a representative).** `cost(M)/LB` with
  `LB = Σ_{i<j} d(K_i,K_j)/(N−1)`. Needed because the medoid's guarantee is
  otherwise only asymptotic.
- **Reach** and **ball coverage.** `reach(K → K')` is the fewest token edits
  to a word decoding to `K'`; `cov_r(M)` counts the members within reach `r`.
  Needed for the language-scale representative.
- **Variant series.** Knowledge bases of one subject over periods or sources
  whose consecutive members differ by few facts. Needed to name the real
  ground truth.
- **Iso-twin.** A non-isomorphic knowledge base matching another's size,
  degree sequence and refinement colouring. Needed for the exactness probe.

## 12. Section plan of the paper

1. Introduction — the collection-level operations and their real settings, the
   five prerequisites, the concession, the contributions.
2. Related work — distances on structures and their metricity; median graphs
   and strings; canonical forms in mining; metric-space analytics; closed
   string languages as precedent.
3. Knowledge bases as hypergraphs; the machine and the alphabet; the
   addressing design space.
4. The metric space — Thm 1, Thm 2, Props 1, 3, 8, 9.
5. The language and its topology — Props 2, 4–7; RQ1's measurement.
6. The toolkit — algorithms and guarantees.
7. Experiments — RQ1–RQ7, one evaluation each, on the collections of §7; the
   decodability figure in RQ6.
8. Limitations.
9. Conclusion and future work (the logic paper named).
