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

**Argument roles** (subject, object, qualifier) are not carried in this
paper: facts are sets, as in every representation compared. The lift that
keeps the alphabet — a per-slot role pattern folded into the fact label, with
the roles in the incidence graph's colouring so the canonical labelling
respects them — is specified and filed (ledger T-KBa) and is future work;
the fact-rank variant that carried roles without the colouring failed
invariance and is the cautionary measurement. Under E1,
`K ≅ K' ⇔ E(K) ≅ E(K')`, so every statement about hypergraphs below is
a statement about knowledge bases. *The paper does not develop the model
theory of this correspondence* (rule iii): it states the encoding, notes that
isomorphic knowledge bases are indistinguishable by any property that does not
name a constant, and moves on.

### 2.2 The word, and what is proved of it

The instruction alphabet `Σ_HG = {V, C, P, N, W}` is executed by a small
machine — a circular list of constants and `k` pointers — that builds a
knowledge base; an encoder writes a knowledge base as a program, the
interpreter `S2H` runs a program back into one. **The paper's representation
is that program** (D-ART4, 2026-09-06). The machine admits more than one
*canonical* program, and the paper uses that:

1. `w*_c(K)`, the tie-complete shortlex minimum over all programs from an
   isomorphism-invariant seed set — the family's search-based form. With the
   augmented fingerprint `F_c(K) = (seed type, w*_c(K))`: *exactness*
   `F_c(K) = F_c(K') ⇔ K ≅ K'` (Theorem A, proved, labelled case included)
   and the *metric* `d_I = d_Lev` on the token sequences (Corollary A). Its
   search is made polynomial on symmetric inputs by stabiliser-orbit pruning
   without changing its value (Prop. C.7, proved; implemented in the C++
   engine, bit-identical on 1,300 differentials).
2. `w°(K)`, the *ordered walk*: a deterministic program emitted along a
   canonical labelling of the constants (individualisation–refinement on the
   coloured incidence graph, computed by nauty), and `w*_ρ(K)`, the family's
   own greedy walk with that labelling as its residual tie key. **Theorem C**
   (proved): every deterministic emitter along a canonical labelling that
   round-trips is a complete isomorphism invariant; Corollary C: its
   Levenshtein distance is a metric on isomorphism classes. No search, no
   exponential case: one canonical-labelling call and a linear emission.

Common to every canonical program: *polynomial pairwise cost* — one
canonicalisation per knowledge base, then `O(L²)` per pair in tokens, raw
Levenshtein and never the length-normalised variant, which is not a metric;
and *a closed language* — every word decodes to a knowledge base. Prop. C.4
now proves what was only measured: every word of `Σ_HG` decodes to a
**connected** knowledge base with no isolated constant, so every prefix,
every edit, every alignment interior and every generated sample is one.
Measured again in RQ6, at campaign scale (27 seeds x 10,000 samples per
collection): every sample of the Isal generator is valid **and** connected —
270,000/270,000 on NDC and 270,000/270,000 on WD50K, validity 1.0000 and
connectivity 1.0000 on both. The fact-list generator's samples are all valid
but connected only 41.6 % of the time on NDC and 12.6 % on WD50K; no single
ratio describes both collections. The sharper contrast is the third generator:
an incidence-list serialisation with a strict decoder must **reject 98.10 %
(NDC) and 98.98 % (WD50K) of its own output**, against validity 1 by theorem.
Put on a single denominator — the fraction of *drawn* samples that are valid
**and** connected, which is what a user of a generator actually gets — the Isal
generator returns a usable knowledge base **every time**, the fact list **one
time in two** (NDC) and **one in eight** (WD50K), and the incidence list **one
in 578** and **one in 11,739**.

**Novelty is where the fact list wins, and the win is real**: 0.9883 (NDC) and
0.9425 (WD50K) of its samples are non-isomorphic to every member, against 0.9172
and 0.9138 for the Isal generator. What that figure conceals is the price. Of the
fact list's genuinely new samples, **7.3 % are connected** (WD50K); of ours,
**100 %**, by Proposition C.4 and not by measurement. Connectivity is the bar
rather than a nicety because it is this representation's domain condition (R3):
a disconnected sample cannot be encoded, so it cannot be canonicalised, compared,
or added to the collection at all. The fact list produces something connected,
which is then usually a near-copy of a member, or something novel, which is then
usually not encodable — rarely both. Its novelty is bought by leaving the domain,
and a closed language has nothing to buy it with, because there is nowhere
outside the domain to go. The dependence is a
WD50K phenomenon and is stated as one: on NDC the two are nearly independent
(joint 0.4040 against 0.4109 if they were).

One asymmetry a reader will notice, stated because the answer is evidence of
care rather than a concession: on the roles-carrying corpus the models are fitted
on role-aware words and every evaluation column is role-free, so a sample
reproducing a member up to argument roles counts as a **reproduction**. That
makes novelty harder to earn, not easier — and hardest for the comparator, whose
novelty figure is the one that beats ours.

**Compactness** rides along: `|w| ≤ m(1+kn)` (proved); measured medians of 6
(WD50K) and 8 (NDC) instructions per member against 12 rows of the canonical
adjacency certificate.

### 2.3 The fifth prerequisite: locality, and the canonical-program decision (RQ1)

The PI's criterion is that similar knowledge bases sit at small Levenshtein
distance. The family's canonical string `w*_c` fails it on the real corpora
(one edit rewrites 0.49–0.79 of the word, normalised; campaign of
2026-09-05) and is censored on 41–100 % of members whose incidence graph has
`|Aut| ≥ 10³`. Both limits have one root: **`w*_c` is the minimum of a
presentation-dependent search.** The minimum is discontinuous under edits,
and the search must try every ordering of automorphic constants because it
cannot tell they are automorphic. Neither is a defect of the alphabet. The
paper therefore keeps the machine, the alphabet and the decoder and changes
the *canonical program* — the rule that picks one program per isomorphism
class — and separates the two limits.

**The design space** is four canonical programs of one machine, arranged by
what a canonical-labelling engine (nauty) contributes — the ablation the
author asked for:

| cell | canonical program | nauty's job | exact by | cost | locality |
|---|---|---|---|---|---|
| no nauty | `w*_c`: tie-complete shortlex minimum over walks | none | Theorem A | exponential on symmetric inputs | the search's |
| oracle only | the same `w*_c`, one branch per stabiliser orbit | automorphism oracle at ties and seeds | Theorem A, value preserved (Prop. C.7) | polynomial oracle calls; measured below | the search's |
| order only | `w°`, the ordered walk: a deterministic emission along the canonical labelling | supplies the order | Theorem C | one nauty call + linear emission (0.08 ms/member) | the emission's |
| both | `w*_ρ`, the family's greedy walk with the labelling as its residual tie key | the order, used inside the search as the tie key | Theorem C | one greedy run (0.5 ms/member, C++) | the greedy walk's |

**What is proved** (`theorem_c_ordered_walk.tex`). Theorem C and Corollary
C (above). Prop. C.4: closed *and connected* language. Prop. C.5 (star
locality): on a knowledge base whose facts all contain the entity, inserting
a new argument costs the ordered walk exactly one `V` instruction and at
most one unit of one pointer run; a new fact over an existing argument at
most three instructions. Prop. C.6 (name-freedom): the word never names a
constant, so a change of the canonical order inside a class of equivalent
constants leaves it unchanged, whereas every rank-addressed serialisation
rewrites every row that names a re-ranked constant. Prop. C.7: orbit pruning
returns `w*_c` bit for bit.

**What is measured so far** (a local preview, 60 members per corpus, one
replication, instruction granularity; the campaign run on Picasso with 27
seeds, BCa intervals and Holm-corrected paired tests is pending at the time
of writing — the table below is to be replaced by it):

| edit (real corpora) | `w*_c` | ordered walk | certificate rows | fact list (record) |
|---|---|---|---|---|
| delete a fact — median instructions (≤ 2 fraction) | **1–3** (0.47–0.77) | **1–3** (0.43–0.61) | 12–15.5 (0.00) | 5–6 (0.12–0.20) |
| remove an argument | **2** (0.58–0.66) | **2** (0.51) | 10–14.5 (0.07–0.13) | 3–6.5 (0.12–0.39) |
| add a fact with a new constant | **4–7** (0.04–0.31) | 13–14.5 (0.02–0.09) | 13–17 (0.00) | 4–7 (0.08–0.18) |
| add an argument to a fact | 4 (0.14–0.16) | 6–7 (0.05–0.08) | 4.5–11 (0.18–0.32) | **2–5** (0.32–0.66) |
| add a fact over existing constants | 6–8 (0.03–0.07) | 14–17 (0.00–0.02) | 8–10 (0.00) | **2–3** (0.49–0.52) |

Three readings. (1) **The Isal walks are the most local representation
under deletions**: removing a fact or an argument removes instructions and
renumbers nothing, while a rank-addressed serialisation renumbers everything
after the gap. (2) **Under insertions the family's greedy walk is 2–3× more
local than the ordered walk**: the greedy walk creates a constant's facts
while that constant is still one pointer step away, and the ordered walk's
breadth-first order defers them until the constant has been pushed away and
then pays the excursion twice — a property of the ordering, not of the
machine, which is why the "both" cell (the greedy walk with a deterministic
tie key) is the representation candidate and the ordered walk the order-only
ablation. (3) Under insertions over existing constants the fact list keeps
the edge it was retired for: naming a constant by rank costs one token where
moving a pointer to it costs a run. That edge and its price (renumbering on
constant edits) are in the record, not in the paper's tables.

**The symmetric-input cost is lifted without changing the definition.** On
the 100 highest-symmetry WD50K members the unpruned C++ engine censors at
60 s, the orbit-pruned C++ engine completes 98 — all 37 with `|Aut| ≥ 10⁷` in
a median of 3 ms — and both Steiner triple systems of order 13, which the
unpruned search never finished, in 50 s and 7 s. On NDC it completes 48 of
100, because that corpus's censored tail is not symmetric: it is arity-10
members whose cost is the displacement search, which pruning cannot touch.
Both numbers go in the paper.

> **QUALIFIED by the 600 s characterisation (job 2279006, T-KBf).** "Pruning
> cannot touch it" stands — the orbit engine recovers only 24.7 % of that tail
> even at a tenfold budget. What does **not** stand is reading the tail as
> intractable *in itself*: the deterministic rank walk clears **50.9 %** of it at
> 600 s, significantly more than orbit (−26.3 %, 95 % CI [−41.6 %, −9.4 %],
> Fisher p = 0.00279; stratified sign test over shards p = 0.0386). So the cost is
> **the tie-complete search on that tail**, not a property of arity-10 members
> that no method can address. The census (69 of 77 at arity 10, |Aut| < 10³) is
> unchanged; only the explanation is. Rewrite at the fold.

**The selection rule was pre-registered** (design record §3): among the
exact, uncensored arms, the one with the highest fraction of
constant-preserving edits within two instructions, ties by median; the
losers stay in the same table. The decision is taken on the campaign table.

**The consequence the paper states itself.** Where the certificate's or the
fact list's locality is better, the article does not claim otherwise; its
distinctiveness rests on what a certificate does not have — a language that
is closed *and connected*, total decoding, the certified representative, and
generation with validity 1 — plus the one locality the Isal walk owns
outright, deletions. That argument is made in §6 and tested in RQ3 and RQ6.

## 3. Research questions

Each question names the knowledge-base problem it answers, the hypothesis, the
evidence, and the single evaluation it receives. They are the paper's
sections, in order.

### RQ1 — Canonical-program design within the Isal language. *Which canonical program of the machine makes similar knowledge bases close, and what does a canonical-labelling engine contribute — as an order, as an oracle, or both?*

- **Hypothesis (pre-registered 2026-09-06; the preview already corrects
  it).** The search was named as the root of both limits — confirmed: the
  orbit oracle removes the symmetric-input cost without changing `w*_c`, and
  the deterministic programs have no exponential case. The ordered walk was
  predicted to be the most local Isal program (H-M1a) — **falsified on
  insertions**: its breadth-first order defers a constant's facts and pays
  pointer excursions, so the family's own greedy walk is 2–3× more local
  there; the relative-addressing advantage (H-M1b) holds for growth around
  the entity (median 1 instruction against 12 certificate rows) and not for
  insertions elsewhere. Unpredicted and robust across both real corpora:
  **every Isal walk is the most local representation under deletions.**
- **Evidence.** The four cells of the nauty ablation and the two certificate
  tokenisations on identical seeded edits: exactness and relabelling
  invariance (M0); single-edit response per edit kind and regime in absolute
  instructions, the within-two fraction and the zero-shift flag (M1);
  correlation with the known fact-level difference on the real series (M2);
  cost and censoring per symmetry bucket (M3); correlation with the
  certificate (M4). Every Isal arm on the C++ engine.
- **Evaluation.** Median single-edit response in instructions with a cluster
  bootstrap over members, the within-two fraction with a Wilson interval,
  Holm-corrected paired Wilcoxon against the certificate rows, Spearman ρ on
  the ladders — the PI's criterion, stated as a number per edit kind.
- **Reading (contract).** The exact, uncensored Isal program with the best
  constant-preserving locality carries RQ2–RQ7; the other cells stay in the
  same table with their numbers and their mechanism; the retired fact list
  stays in the record as the comparator it was. *Pending: the campaign table
  (jobs 2247394/2248782/2248907, 2026-09-07).*

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
| Thm 1 | Exactness of the search-based canonical program: `F_c(K) = F_c(K') ⇔ K ≅ K'` for labelled knowledge bases | proved (Theorem A, tie-complete `w*_c`) | RQ1, RQ2, RQ4 |
| Thm 2 | Metric: `d(K,K') = d_Lev` on the canonical token sequences is a metric on isomorphism classes, one `(k, vocabulary)` per comparison | proved (Corollary A; Corollary C for the deterministic programs) | all |
| **Thm 3** | **Exactness of every deterministic canonical program**: an emitter along a canonical labelling that round-trips through `S2H` is a complete isomorphism invariant — the ordered walk `w°` and the rank-keyed greedy walk `w*_ρ` in particular | proved (Theorem C, `theorem_c_ordered_walk.tex`) | RQ1, RQ2 |
| Prop 1 | Length and key size: `\|w\| ≤ m(1+kn)` for every Isal program; measured medians 6 / 8 instructions (WD50K / NDC) against 12 certificate rows; fixed-width bits against the incidence list | proved / measured | RQ1, RQ7 |
| Prop 2 | Closure **and connectivity**: the interpreter is total, and every word of `Σ_HG` decodes to a *connected* knowledge base with no isolated constant — hence every prefix, edit, alignment interior and generated sample | proved (Prop. C.4); measured validity 1.0000 **and** connectivity 1.0000 on 270,000 samples per collection (`ow_ngram`, 27 seeds x 10,000, both NDC and WD50K), against fact-list connectivity 0.4157 (NDC) / 0.1260 (WD50K) and an incidence-list generator rejecting 98.10 % / 98.98 % of its own samples | RQ3, RQ6 |
| Prop 3 | Certificates: medoid `≤ (2 − 2/N)·OPT`; `LB ≤ OPT`; hence `LB ≤ OPT ≤ Σ_i d(M, K_i)` certifies any candidate | proved (Jiang–Münger–Bunke 2001 for the medoid) | RQ3 |
| Prop 4 | Fact-level simulation: a fact insertion is reachable through a non-canonical word with the pointer displacement as an additive cost, so the ball of radius `r` contains every knowledge base within `r` fact insertions up to that cost | measured (1,200/1,200 insertion witnesses, 717/717 deletions) | RQ1, RQ3 |
| Prop 5 | Source identifiability on the indel ball: if the members are `t` fact insertions from a common source, the source covers all `N` at radius `t` while no member reaches another in fewer than `2t` | measured (source unique maximiser 12/12 at both noise levels; member-to-member reach 0.00–0.02) | RQ3 |
| Prop 6 | Generative closure: any distribution over words pushes forward to a distribution over knowledge bases; autoregressive generation is valid at every prefix | immediate from Prop 2 | RQ6 |
| Prop 7 | Certificate sets are not languages: not closed under any edit, no total decoder, no prefix property; hence no ball, path or generative model exists on them | to be written (short) | RQ2, RQ6 |
| Prop 8 | The bipartite edit-path cost is not a metric (counterexample `d(A,B)=2, d(B,C)=4, d(A,C)=7` on 3+3+4 vertices); its raw assignment value is a pseudometric with false zeros | proved by counterexample; rates measured | RQ2 |
| Prop 9 | Incompleteness of refinement-based keys on hypergraphs | cited + measured merges | RQ2, RQ4 |
| Prop 10 | Star locality of the ordered walk: on a knowledge base whose facts all contain the entity, a new argument costs one `V` and at most one unit of one pointer run; a new fact over an existing argument at most three instructions | proved (Prop. C.5) under the no-crossing move rule; measured exact on 400 random stars | RQ1 |
| Prop 11 | Name-freedom: the Isal word never names a constant, so a change of the canonical order inside a class of equivalent constants leaves it unchanged, while every rank-addressed serialisation rewrites every row naming a re-ranked constant | proved (Prop. C.6) | RQ1 |
| Prop 12 | Orbit pruning is value-preserving: branching over one representative per orbit of the stabiliser of the placed prefix, recomputed at every tie, returns `w*_c` | proved (Prop. C.7, from Prop. 6.1 of the completeness proof); implemented in C++, bit-identical on 1,300 differentials; both STS(13) in 50 s / 7 s | RQ1, RQ7 |
| Obs 10 | Instability of the search-based program under insertions: the minimum of the tie-complete search moves under a single edit (normalised response 0.49–0.79, campaign 2026-09-05), with the two mechanisms named (seed and tie flips; pointer drift) | measured | RQ1 |
| Obs 13 | **The ordered walk's deferral.** A breadth-first emission by anchor defers a constant's own facts until the constant has been pushed away from the root, so insertions elsewhere than the entity cost pointer excursions (median 13–17 instructions) where the family's greedy walk creates them one step away (4–8) | measured (preview; campaign pending) | RQ1 |
| Obs 14 | **Deletion locality of the Isal walks.** Removing a fact or an argument removes instructions and renumbers nothing: median 1–3 instructions, within two on 0.43–0.77 of edits, against 10–15.5 rows for the certificate and 5–6.5 tokens for the fact list | measured on both real corpora (preview; campaign pending) | RQ1, RQ3 |
| Record | The fact-rank word's results — its one-token insertion locality, the refutation of content-hashed addresses (Obs 11), the renumbering trade-off (Obs 12) and the addressing frontier (Prop 13) — stay in the ledger and the supplement as the comparator's record; they are not the paper's representation (D-ART4 (1)) | measured 2026-09-04, retired 2026-09-06 | supplement |

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

**Nauty's role, stated once.** The canonical order of the constants is
computed by nauty's individualisation–refinement on the coloured incidence
graph; the Isal encoder then emits, along that order, a program for the Isal
machine — nauty decides *which* constant comes first, the language decides
*what* is written, and every string of that language decodes to a knowledge
base. For the family's own search-based form, nauty supplies the automorphism
group of the placed prefix, and the search explores one branch per orbit; the
string returned is the frozen `w*_c`. The comparison in every table is
therefore *a language* (nauty inside an Isal encoder) against *a certificate*
(nauty's canonical form written out).

**Conceded once, in the introduction.** For deciding isomorphism and
deduplicating a collection, the certificate engines are faster and equally
exact; we do not compete there and we report the timing. For the
deterministic Isal programs the gap is one linear emission on top of the
same nauty call.

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
| **The consensus substrate sits in the weak regime** (materialized and quantified): **75.8 %** of natural NDC consecutive pairs change the constant set (400 of 528), and restricting to the preserving regime leaves **15 drug classes with a run of ≥ 3 quarters and 2 with ≥ 5** — too small to carry RQ3 alone | RQ3 runs on constant-preserving ladders over *real* members (injected fact edits on real knowledge bases, constant set held) with the natural series reported beside them as the harder case; the alternative — moving the substrate — is an open scoping decision recorded in `foundation/probes_2026-09.md` §9 |
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

### 11.1 The alphabet stays; the canonical program is what changed (D-ART4)

**The ruling.** On 2026-09-04 the PI allowed the alphabet to change and the
criterion was set: *KBs parecidas deben codificarse en cadenas cuyas
distancias de Levenshtein sean pequeñas*. A fact-list alphabet addressed by
canonical rank was adopted and measured (§2.3's record). On 2026-09-06 the
PI ruled that the paper's representation is the instruction string of the
Isal family: a word for the machine with its circular list, its pointers and
`Σ_HG`. The fact list has no machine; it leaves the paper and stays in the
record as a comparator.

**What changes under the ruling.** Not the alphabet, not the decoder, not
the completeness argument: the *canonical program*. `w*_c` is the minimum
of a search, and the search is what made similar knowledge bases far apart
and symmetric ones expensive. The machine admits canonical programs that do
not search — a deterministic emission along a canonical labelling of the
constants (the ordered walk), or the family's greedy walk with that
labelling as its residual tie key — and these are complete by Theorem C.
The search itself is kept, as the family's own form `w*_c`, and made
polynomial on symmetric inputs by orbit pruning without changing its value.
A canonical-labelling engine enters as a subroutine of an Isal encoder, in
two roles the paper measures separately (§2.3's ablation).

**What the fact-list detour bought and what it cost.** Its measurements are
the comparator the paper argues against and they are kept: one-token
insertion locality where the constant set is preserved, the refutation of
content-hashed addresses, the renumbering trade-off. Its price was the
machine, and with it the two properties the paper claims and the fact list
cannot: a language closed under every edit whose words are all *connected*
knowledge bases (its samples are disconnected 58 % of the time on NDC and
87 % on WD50K), and a
deletion locality no rank-addressed serialisation has.

**The honest price, now paid.** Three canonical programs were implemented
in the C++ engine, each bit-identical to its Python reference on every
differential (the ordered walk on all 5,369 members of both corpora); a
theorem file was written; and every frozen `Σ_HG` measurement is re-labelled
as a statement about the search-based program: nothing is invalidated. The
restriction R4 (roles) is filed; R3 (connected domain) is now a proved
property rather than a restriction.

### 11.2 Glossary (additions to `logic_models/vocabulary.md`)

Each term earns its place by a claim that needs it.

- **Canonical-word metric.** `d_φ(A,B) = d_Lev(φ(A), φ(B))` for a complete
  invariant `φ` into words. *Constructive member*: ours. *Certificate
  member*: canonical labelling plus serialization. Needed to state the family
  and place the competitor inside it.
- **Language.** A set of words closed under the alphabet with a total decoder
  into objects. Needed for RQ6 and Prop 7.
- **Canonical program.** The rule that picks one program of the Isal machine
  per isomorphism class: the tie-complete search minimum `w*_c` (Theorem A),
  the ordered walk `w°` along a canonical labelling, or the greedy walk
  `w*_ρ` with that labelling as its tie key (both Theorem C). Needed to state
  RQ1 and the nauty ablation.
- **Ordered walk.** The deterministic emission: root by degree and type,
  facts by anchor, predicate and local signature with the canonical rank as
  the last key, closing facts swept by position, moves that never cross the
  root. Needed for Props. C.5–C.6.
- **Orbit pruning.** Branching over one representative per orbit of the
  automorphism group fixing the placed prefix, recomputed at every tie;
  returns `w*_c` unchanged. Needed for the symmetric-input result.
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
   canonical programs and what a canonical-labelling engine contributes.
4. The metric space — Thms 1–3, Props 1, 3, 8, 9, 12.
5. The language and its topology — Props 2, 4–7, 10–11; RQ1's measurement
   with the four-cell ablation.
6. The toolkit — algorithms and guarantees.
7. Experiments — RQ1–RQ7, one evaluation each, on the collections of §7; the
   decodability figure in RQ6.
8. Limitations.
9. Conclusion and future work (the logic paper named).
