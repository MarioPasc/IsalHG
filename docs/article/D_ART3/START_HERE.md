# D-ART3 — START HERE

*Entry point for the IsalHG journal article re-scope (target **IEEE TKDE**).
Written 2026-09-03 after the PI focused the article on the consensus idea
(`logic_models/ideas/idea3_median.md`) and added four applications over
collections of knowledge bases (outlier filtering, dendrogram, k-medoids, MDS).
Everything an agent needs to pick this up is either in this file or one hop
away from it. Read this file end to end first, then `prose.md` (the article's
storyline), then the `foundation/` fact sheets, and only then the older v5.1
files, in the order given in §7.*

**Standing instruction (author, 2026-09-03).** Prior results are *guidance*,
not assets: every experiment of the new article may start from zero, designed
for its own question, on its own corpora. What carries over is the experience
(`foundation/lessons.md`), the theorems (`foundation/proved_facts.md`), the
code, and the feasibility envelope.

---

## 0. The one-paragraph state of play

The IsalHG canonical string `w*_c` is a proved complete isomorphism invariant
of connected labelled hypergraphs, so `d_I = Levenshtein(w*_c(·), w*_c(·))` is
a metric on isomorphism classes (Theorem A, Corollary A). Every word of the
alphabet decodes to a connected hypergraph (closure, proved; connectivity,
sketched — must be promoted). Three iterations of experiments established
one hard fact about this metric: **a single structural edit rewrites about
half of `w*_c` on random substrates** (measured 0.51–0.54 of the string on
2026-09-03; 0.30–0.50 at T-M4b), so `d_I` has no resolution in the
small-perturbation regime. That is why the v3 article lost clustering and kNN
to nauty-Levi edit, HPD and NetLSD on its final corpus, and it is why the
2026-09-03 pilot found that a generalized median searched under `d_I` cannot
improve on the medoid (≤ 1.6 %, 0/24 recoveries). The same pilot showed the
property no competitor has works without exception: 24,000/24,000 single-token
mutations of canonical strings decode to connected hypergraphs. **The article
must therefore be built on what `d_I` and the ambient space *do* give —
exactness, a metric with computable certificates, polynomial pairwise cost,
compact keys, and decodable neighbourhoods — and must not be built on fine
task geometry.** The knowledge-base framing (a KB is a set of ground facts,
i.e. a labelled hypergraph; comparison up to renaming of constants) is the
right venue framing and is verified novel (`foundation/literature_verified.md`).

## 1. Timeline — how we got here

| When | Scope | Outcome |
|---|---|---|
| 2026-06 | Iso-benchmark preprint (nauty/Traces/bliss on the Levi reduction) | complete, competitive, not faster than mature engines |
| 2026-07 | v3 metric-space article, *Information Sciences*: characterize → exploit (MDS, k-medoids, kNN, paths) | `d_I` loses A2/A3 on the FINAL size-controlled corpus (Stratum C, T-M4b); avalanche mechanism measured |
| 2026-08-09 | v4 draft: characterize → explain → instrument | honest but a limit paper |
| 2026-08-12 | **v5.1 D-ART3** (this folder): TKDE, "a certificate is not a space" — search framework C1, minimal countermodels C2, navigation C3, black-box optimization C4, real data C5 | pending PI; gates G-L1/G-D1/G-B1 unmeasured |
| 2026-08-12 | `logic_models/`: three PI ideas (repair, entailment, **median**) developed; P-MEDIAN recommended flagship; gate G-L4 closed (token lengths) | pending PI |
| 2026-09-03 | PI: idea 3 (consensus) leads; add outlier filtering, dendrogram, k-medoids, MDS over N KBs; venue TKDE | **this re-scope (v6)**: fact base verified, three probes run, storyline in `prose.md` |

Decision status: **D-ART3 is still pending the PI**; nothing in
`docs/article/{PROPOSAL,DATA,COMPETITORS,theoretical,empirical}` has changed.
This folder is the proposal; `prose.md` is its storyline.

## 2. The verified fact base (read the sheets; here are the headlines)

`foundation/` holds four sheets produced on 2026-09-03 by reading the data
files, the proof `.tex` sources, and the literature — not the prose:

| Sheet | What it settles |
|---|---|
| [`foundation/measured_facts.md`](foundation/measured_facts.md) | every prior number with its file; favourable and unfavourable properties; supersessions; two corrections to the ledger |
| [`foundation/proved_facts.md`](foundation/proved_facts.md) | every theorem/lemma with status PROVED / CONDITIONAL / REFUTED; what labels do; the 14 retracted claims; what supports or threatens a median |
| [`foundation/literature_verified.md`](foundation/literature_verified.md) | DOI-verified citations only; novelty verdict |
| [`foundation/probes_2026-09.md`](foundation/probes_2026-09.md) | the measurements run for this re-scope: planted-consensus pilot (§1), bipartite-GED metricity (§2), ambient reach and ball coverage (§3), ARB contact ego-KBs (§4), WD50K entity KBs (§5); appended as they land: ARB temporal variant series (§6), qualifier-rich KG collections and entity types (§7), the `Σ⁺` prototype and proofs (§8) |
| [`foundation/lessons.md`](foundation/lessons.md) | 25 design rules distilled from the previous iterations — binding on the new experiments |

**Headlines an agent must carry in its head.**

*Proved.*
- Theorem A: `F_c(H_1) = F_c(H_2) ⇔ H_1 ≅ H_2` for connected **labelled**
  hypergraphs, with `F_c = (seed label, w*_c)`; comparing bare `w*_c` on
  labelled inputs is a false positive. Corollary A: `d_I` on the
  seed-label-prefixed token sequence is a metric on isomorphism classes.
  Both are alphabet-scoped: one `(k, depth, vocabulary)` per comparison.
- Closure: every word of `Σ_HG(k)*` decodes (proved in the preprint);
  connectivity of every decoded word is an assumption plus a sketch — the
  new article promotes it to a proposition (easy induction).
- `|w*_c| ≤ m(1+kn)` (proved; measured slack 0.073). `|Σ_HG(k)| =
  k(k−1)/2 + 3k + 1` unlabelled; the labelled alphabet size has no estimator.
- Medoid ≤ 2·OPT in any metric space (Jiang–Münger–Bunke 2001); tightened to
  `(2 − 2/N)·OPT` by the same argument. Pairwise lower bound
  `LB = Σ_{i<j} d(K_i,K_j)/(N−1) ≤ OPT`, so every candidate carries a
  certified ratio `cost/LB`, and the medoid's is `≤ 2(N−1)/N`.
- Generalized median string is NP-complete (de la Higuera–Casacuberta 2000).
- Bipartite GED is not a metric (Serratosa 2019, in print).

*Refuted or retired — do not repeat.* `d_I` as an HGED proxy; Theorem B as a
stability bound (two hypotheses refuted); the greedy variants as invariants;
bare `w*` on labelled inputs; the A4 decodability score; the S7 "headlines";
"k = 7 and k = 10 measured infeasible" (no timing record exists);
"P-MEDIAN is immune to the small-perturbation weakness" (the 2026-09-03 pilot
refutes it for the generalized median).

*Measured, favourable.* Compactness r > 1 on 320/320 (median 1.441);
`ν` largest of all representations (0.137 → 0.011 with size); benign hubness;
E1′ ρ = 0.622 with HGED = 0 ⇔ d_I = 0; canonicalization 0.4–26 ms at
`n ≤ 10`, p50 1.7 s at `k = 3, n = 24`; certified medoid ratio ≤ 1.63 on all
24 pilot profiles; 24,000/24,000 mutations decode connected.

*Measured, unfavourable.* Avalanche 0.51–0.54 per edit on random substrates;
loses A2/A3 to nauty-Levi edit, HPD, NetLSD on Stratum C (Holm-significant);
local-search generalized median dead (≤ 1.6 %, 0/24); `k = 5` only at
`n = 8`; Steiner-type substrates uncomputable; nauty is orders of magnitude
faster at identity; the labelled code path (`LabelVocabulary.fit`) is
unimplemented, so no labelled corpus has ever been canonicalized.

## 3. Corrections to the documents in this folder

The v5.1 files and the `logic_models/` development were written before the
fact base was verified. Read them with these corrections:

1. `README.md` §6, `applications.md`, `data.md`, `logic_models/scope.md`:
   "`k = 7` and `k = 10` measured infeasible" — **unverified**; the drive holds
   only `not_runnable` records for those blocks.
2. `../DEVELOPMENT/README.md` "S7 measured headlines" — **superseded** numbers
   from the retracted Stratum A corpus; the FINAL numbers are Stratum C.
3. `logic_models/ideas/idea3_median.md` §0 marks "Hungarian GED is not a
   metric" as VERIFIED on the strength of a sketch and unverified citations.
   It is true, but the citation is Serratosa (2019), and the explicit
   counterexample and violation rate come from `foundation/probes_2026-09.md`.
4. `idea3_median.md` §2.1 cites "Hassin & Rubinstein 2001 [unverified]" for
   the 2-approximation; the citable source is Jiang, Münger & Bunke (TPAMI
   2001), and the bound sharpens to `2 − 2/N`.
5. `idea3_median.md` §4 "384× slower per matrix" used character lengths;
   corrected at G-L4 (`logic_models/competitors.md` §3.1): per-pair cost is
   comparable to Hungarian.
6. `idea3_median.md` §1.2/§3 and `logic_models/README.md` §5(3): "P-MEDIAN is
   immune to the small-perturbation weakness measured at T-M4b" — **false for
   the generalized median** (pilot: the objective changes by 25–35 % per
   single edit; local search cannot leave the medoid). True only of the
   medoid, which any metric provides.
7. `idea3_median.md` §5.1 "contact-high-school ≈ 327 students in ≈ 9 classes"
   and every statement about ego-net sizes and `N` per class were guesses;
   the measurement is in `foundation/probes_2026-09.md`.
8. `geometry.md` §1 and `applications.md`: the G2 contrast "3/5/9 tokens vs
   nauty 20/30/37" compares IsalHG *tokens* against nauty certificate
   *bytes* (`metric_space/representations/nauty_levi_edit.py` runs
   Levenshtein on the raw `pynauty.certificate` bytes). Re-measure with a
   stated tokenization before using it.
9. `theory.md` §0 and `CLAUDE.md`: "Prop 6.0" of the completeness proof does
   not exist under that number; the coherent-ties proposition is 6.1.
10. `logic_models/vocabulary.md` §2 and `logic_models/risks.md` §1: the alphabet question
    (`Σ_FO`, D3′) is **out of this article** (see §6, decision D3); E1/E2 into
    the current alphabet are the encodings used.
11. `venue.md` §1 "v5 answer" column and `competitors.md` Sets B/C: the
    search framework, minimal countermodels and model finders leave the
    paper (future work); see §5.

## 4. The article, v6.1 — one page (the full storyline is `prose.md`)

**Title (working).** *Knowledge Bases as Words: an Exact, Certified Metric
and a Closed Language for Collections of Relational Structures up to
Isomorphism.*

**Problem.** Given `N` knowledge bases over one signature — finite sets of
ground facts whose constants are anonymous or typed, so that renaming does
not change the knowledge base — find the member that best represents the
collection, filter the atypical members, organize the collection
(dendrogram, k-medoids), map it, and extend it with new valid members, under
a distance that is well defined on isomorphism classes.

**What no existing representation offers together.** Exact identity, a true
metric, polynomial per-pair cost, and a *closed language* in which every
string is a knowledge base. Exact structure edit distance is NP-hard per
pair; the bipartite approximation is polynomial but not a metric (Serratosa
2019; measured: asymmetric on 38 % of pairs, triangle violated on 1.4 % of
triples, ten-vertex counterexample); embeddings are metrics but incomplete
(false merges counted on real collections); hypergraph optimal transport is
computed to local optima and has no decoder; the canonical-labelling
certificate plus Levenshtein is an exact polynomial metric — the
*certificate member* of the family we introduce, faster and compared on
every table — but a certificate is not a language: no edit, prefix, path or
sample of one is an object.

**Thesis.** *A knowledge base is a word.* The canonical instruction word
gives knowledge-base space an exact identity (Theorem A), a metric with
computable certificates (Corollary A + the pairwise bound), compact keys,
and a closed language (every prefix, edit, alignment interior and generated
sample decodes to a connected knowledge base). The space has **two scales**:
the metric organizes distinct structures and certifies consensus; the
language resolves fact-level neighbourhoods, interpolates and generates. A
conservative extension of the language (`Σ⁺`: rank-addressed fact tokens,
decoder side only, canonical form untouched) makes the language scale
provable: the string ball of radius `r` contains every knowledge base within
`r` fact insertions.

**Research questions** (one evaluation each; hypotheses and evidence in
`prose.md` §3):

- **RQ1 well-posedness** — which distances satisfy which prerequisites, and
  what each missing one does to a real collection. *Theorems for ours;
  counterexamples and measured false merges for the others.*
- **RQ2 consensus without identity** — certified medoid (`≤ (2 − 2/N)·OPT`,
  measured ratio ≤ 1.63) and ball-coverage consensus (identifies the source
  of a variant collection: 11/12 measured under `Σ_HG`, provably complete
  for insertion variants under `Σ⁺`), evaluated by the exact fact-level
  distance to the held-out next member of real time series, against the
  identity-using majority-vote merge.
- **RQ3 outliers that statistics cannot see** — AUC of recovering injected
  corruptions on real substrates; false merges hide iso-twin outliers from
  incomplete representations.
- **RQ4 patterns of description** — k-medoids and dendrogram over `d_I`
  against Wikidata entity types (ARI; cophenetic correlation), licensed by
  the measured `ν > 0` and hubness.
- **RQ5 generation and interpolation** — a token sequence model over a real
  collection's words samples valid knowledge bases with probability 1 (Prop
  6) against an incidence-list generator's rejection rate; the decodability
  figure; certificates admit neither (Prop 7).
- **RQ6 envelope** — the frontier is the fact count, labels are the
  tie-breaker; one figure and the yield table.

**Data** (`prose.md` §7; `supplementary_data.md`). Two real collections, one
question each, each with a control in the supplement: entity knowledge bases
of **WD50K(66)** (3,167 n-ary members; Wikidata types as class labels;
WD50K(100) as purity control) and the quarterly co-formulation knowledge
bases of pharmacologic classes in **NDC-classes** (1,432 members, 21.6 % of
consecutive quarters one-edit variants with exact fact-level truth;
NDC-substances as control); controlled corruptions of real members for RQ3;
a synthetic envelope sweep for RQ6 only. Retired after probing: planted
families, Stratum C, contact induced ego-networks, HIC, JF17K, WikiPeople,
and ten of the twelve ARB temporal datasets (numbers in the supplement).

**Competitors.** Exact oracle, bipartite GED (both readings), majority-vote
merge with identities, WL, NetLSD, HPD, HyperCOT (gated), the certificate
member, two naive floors; capability matrix with eight columns filled by
theorem or counterexample.

**Theory delivered.** Theorems 1–2 (exactness, metric, for knowledge bases);
Props 1–3 (length and key size; closure and connectivity; certificates);
Props 2⁺, 4–6 (the language: extension, fact-level simulation and ball
inclusions, source identifiability, generative closure); Props 7–9 (what
certificates, bipartite GED and WL keys lack).

**Conceded in the introduction.** Canonical-labelling engines decide
identity faster; the envelope is small (facts in the low hundreds).

## 5. Disposition of the v5.1 folder, file by file

| File | Under v6 |
|---|---|
| `README.md` | historical (v5.1 hub). Its §1 PI quotes, §4 asset table and §6 risk 1 ("any dedup-shaped claim loses") remain valid |
| `proposal.md` | superseded by `prose.md`. Keep: §0 premise, §1 concession paragraph, the four-component table (ground set, moves, decoder, metric) as the explanation of *why* decodable neighbourhoods exist |
| `venue.md` | **survives**; TKDE checklist still binding. Its "v5 answer" column is replaced by §4 above |
| `theory.md` | P1 **promoted** (closure + connectivity proposition), P6 partially (ball enumeration soundness, for the reach layer); P2 → the limitation's mechanism, cited not proved; P3, P4, P5 → out |
| `applications.md` | C1, C2, C4 → **future work** (search framework, countermodels); C3 navigation → optional decodability exhibit; C5 completeness price → **RQ3**; the certificate-vs-space table → kept as explanation |
| `geometry.md` | **survives**, consumers re-pointed to the toolkit (`ν` → PAM/metric MDS; hubness → outlier scores; `D̂` → index applicability; sensitivity → limitation). Ball growth → the reach layer (measured: `\|B_1\|` ≈ 570–740 words, `\|B_2\|` ≈ 1.6–2.7 × 10⁵) |
| `data.md` | ARB tier table **survives**; size half of G-D1 answered by the probe; add the KB-collection corpora; HIC retired |
| `competitors.md` | Set A survives with corrected units (L9); Sets B/C → out; §0 concessions survive |
| `logic_models/README.md` | historical; §4b verdicts survive except "P-MEDIAN immune" (corrected) |
| `logic_models/vocabulary.md` | **binding glossary**, extended in `prose.md` §Vocabulary (certificate, reach, ball coverage) |
| `logic_models/problems.md` | P-MEDIAN survives as the flagship; P-MIN, P-REPAIR, P-ENTAIL → future work section |
| `logic_models/encoding.md` | E1 (symmetric single-relation KBs) and E2 (general) survive; the `Σ_FO` design space → future work |
| `logic_models/scope.md` | fragment and envelope survive |
| `logic_models/data.md` | §4 (ARB as KBs) survives; §2/§3 (TPTP, census) → future work |
| `logic_models/competitors.md` | §3 (P-MEDIAN baselines and contract) survives with corrections 3–6 |
| `logic_models/related_work.md` | replaced by `foundation/literature_verified.md` |
| `logic_models/risks.md` | folded into `prose.md` §Limitations; §2's corrected `d_amb` argument is the basis of the reach layer |
| `logic_models/ideas/idea3_median.md` | superseded by `prose.md` §Consensus; its §5–§6 experiment plan is the template, minus the generalized-median local search |
| `logic_models/ideas/idea1_repair.md`, `idea2_entailment.md` | future-work sources (repair via ball enumeration is the natural sequel if reach is small) |

## 6. Decisions for the PI — developed (2026-09-03, v6.1)

*Each decision is stated with the recommendation, the scientific reason it
is tied to knowledge bases rather than to machinery, what it costs, and what
it rules out. The author's guidance is folded in: the article must read as
science, positives only for now, one story on one evaluation axis, and at
least one small experiment that shows a property the certificate route
lacks, with theory saying why the property is useful.*

- **D1 — Centre of the paper: metric analytics of knowledge-base
  collections, on two scales.** The object is a *collection* of knowledge
  bases up to renaming of constants; the questions are the knowledge
  engineer's (which member represents the collection, which are atypical,
  which patterns of description exist, what a new plausible member looks
  like). The metric scale answers the first three with guarantees (exact
  identity, certified medoid, licensed clustering); the language scale
  answers the fourth and refines the first (fact-level neighbourhoods,
  ball-coverage consensus, interpolation, generation). Every algorithm is
  introduced by the question it answers, and every experiment reports the
  one metric that answers it (`prose.md` §3, §5). Ruled out: any section
  whose only content is a measurement without a knowledge-base question;
  the v5.1 search framework and countermodels (future work).
- **D2 — Consensus, positives only.** The deliverables are the certified
  medoid (Prop 3: `cost ≤ (2 − 2/N)·OPT`, ratio certified from the matrix;
  measured ≤ 1.63) and the ball-coverage consensus at the language scale,
  which identifies the source of a variant collection (measured 11/12 under
  `Σ_HG`; provably complete for insertion variants under `Σ⁺`, Props 4–5),
  evaluated on real variant series where the fact-level truth is known
  (`prose.md` RQ2). The local-search generalized median is not part of the
  story; it stays in the ledger as a design input (`foundation/probes` §1).
- **D3 — Extend the language, keep the canonical form.** Adopt `Σ⁺ = Σ_HG
  ∪ {A, A⁺}` (rank-addressed fact tokens; `prose.md` §11.1): a conservative
  extension on the decoder side, so `w*_c`, Theorem A and every frozen
  result are untouched, while the ambient claims become theorems (Prop 2⁺
  totality/connectivity; Prop 4 fact-level simulation and the ball
  inclusions; Prop 6 generative closure). It is the shift from the preprint
  that the venue values — the preprint gave the machine and its complete
  canonical form, this article gives the language — and it is what turns the
  measured 52–55 % one-edit coverage into 100 % for insertions. Cost: one
  proposition, decoder cases in Python and C++, a token enumerator, pinning
  tests. **Prototyped and checked 2026-09-03** (`foundation/probes` §8):
  conservativity 2,000/2,000, totality and connectivity 20,000/20,000,
  insertion witnesses 1,200/1,200, deletion witnesses 717/717, coverage
  theory met exactly (source covers 7/7 at radius `t` in 12/12 profiles per
  family); three pins added to the design (anchor label maximal — 300/300;
  `A⁺` runs chain like one `V` — the coordinator's first ruling, reverse
  emission, was falsified by the re-run and replaced; coverage on the indel
  ball — source unique maximiser 12/12 at both noise levels). Ruled out: re-designing
  the *encoder* (the pointer machine is what makes the word compact and the
  canonical form ours).
- **D4 — The certificate member is family, and two small experiments show
  what it lacks.** Present nauty-Levi + Levenshtein as the certificate member
  of the canonical-word family (exact, metric, faster; compared on every
  table). The differentiating property is the *language*: Prop 7 states
  that certificate sets are closed under no edit and have no decoder, hence
  no ball, reach, interpolation or generative model exists on them. The
  experiments that make the property visible on knowledge bases: (i) the
  ball-coverage consensus on real variant series (RQ2) — not computable from
  certificates; (ii) a token sequence model fitted on a real collection's
  words, sampled with validity 1 by theorem, against an incidence-list
  generator that must reject invalid outputs (RQ5) — undefined for
  certificates; plus the decodability figure (D8). The usefulness theory is
  Props 4–6.
- **D5 — Data: real collections, one question each, semi-synthetic only
  where truth needs intervention.** Primary: entity knowledge bases of a
  hyper-relational knowledge graph (WD50K(100); entity types as class labels)
  and time series of real interaction knowledge bases from the ARB
  collection (real one-edit variants with exact fact-level truth); the two
  probes selecting the datasets are running (`foundation/probes` §6–§7
  when they land). Controlled corruptions are applied to *real* members for
  the outlier test (RQ3), because outlier ground truth cannot exist without
  intervention; the only fully synthetic data is the envelope sweep (RQ6),
  because real collections do not span sizes. The synthetic planted
  families, Stratum C, the contact induced ego-networks and the HIC atlas
  are retired. Details and the standing defence of the two remaining
  synthetic uses: `prose.md` §7 and `supplementary_data.md`.
- **D6 — Labels are the tie-breaker; the whole paper runs on labelled
  knowledge bases.** Measured: labelled canonicalization runs in
  milliseconds where the unlabelled form fails at thirteen vertices; every
  real knowledge base carries predicate labels on facts and (where available)
  types on constants. First engineering task: `LabelVocabulary.fit`. The
  language extension carries labels in its tokens (`A[ℓ; …]`, `A⁺[ℓ; λ; …]`).
- **D7 — One evaluation axis per application.** Consensus: exact fact-level
  distance to the held-out next member of a real series. Outliers: AUC of
  recovering injected corruptions. Clustering: adjusted Rand index against
  entity types (cophenetic correlation for the dendrogram). Map: a figure
  with its stress. Generation: validity and profile fidelity. Envelope: the
  yield table. No secondary axes; no metric appears without its question.
- **D8 — One decodability figure.** The Levenshtein alignment path between
  the canonical words of two real entity knowledge bases, every interior
  word decoded and drawn as a knowledge base, beside the same alignment for
  the two certificates, whose interior decodes to nothing (Prop 7). Placed
  in RQ5.

The original short list (kept for the record):

- **D1 — Centre of the paper.** *Metric analytics over collections of KBs*
  (consensus, outliers, dendrogram, k-medoids, MDS) with guarantees, or the
  v5.1 search framework? **The former**; the search framework and the
  countermodel application become future work, except the ambient-space
  machinery the consensus/outlier layer uses.
- **D2 — The generalized median.** The local-search generalized median under
  `d_I` is measured dead. **Report it as a negative in one paragraph**; the
  deliverables are the certified medoid and the ball-coverage consensus,
  the latter scoped to one-instruction variants (the reach probe: 11/12
  recoveries at that scope, none beyond it).
- **D3 — Alphabet.** Keep `Σ_HG` (E1/E2 encodings) for this paper; the
  semantics-aligned `Σ_FO` (one fact = one token, absolute addressing) is the
  stated future work that attacks the avalanche. **Yes** — the alphabet
  redesign is a second paper.
- **D4 — nauty-edit's role.** Present the canonical-labelling edit distance as
  the *certificate member* of the canonical-word family we introduce (exact,
  metric, faster, not decodable), compared on every table, rather than as an
  adversary. **Yes** — it is honest and it turns a loss into a family result.
- **D5 — Real data.** A hyper-relational KG ego-KB corpus (WD50K) as the
  primary real collection (gated on its probe), ARB `contact-*` ego-KBs as
  a constrained exhibit (only 59 instances inside the envelope), sparse ARB
  star ego-KBs as the fallback. **Yes, in that order.**
- **D6 — Labels.** KBs are labelled; the whole paper runs on `d_I^Σ`
  (seed-label-prefixed). This requires implementing `LabelVocabulary.fit`
  first. **Yes.**
- **D7 — Evaluation axis.** Task metrics vs planted classes are reported
  under contract as a *secondary* axis; the primary axes are guarantees,
  certificates, false-merge counts, decoded outputs, and envelope. **Yes.**
- **D8 — Interpolation/paths (C3).** One decodability figure inside the
  consensus section, or drop. **One figure if space permits.**

## 7. Reading order for a new agent

1. This file.
2. [`prose.md`](prose.md) — the article's storyline: premise, research
   questions, theory, toolkit, data, competitors, the language extension
   (§11.1), section plan. Written to be sent to the PI as a whole.
2b. [`supplementary_data.md`](supplementary_data.md) — the self-contained
   data section: every collection with source, derivation, sizes, yield,
   repetition, timing and ground truth, plus the defence of the two
   remaining interventions.
3. `foundation/lessons.md` → `foundation/probes_2026-09.md` →
   `foundation/measured_facts.md` → `foundation/proved_facts.md` →
   `foundation/literature_verified.md`.
4. `logic_models/vocabulary.md` (binding names), `logic_models/encoding.md`
   §1 (E1/E2), `logic_models/ideas/idea3_median.md` §5–§6 (experiment
   template), `venue.md`.
5. For the algorithms: `../H2S_S2H.md`; for the code map:
   `../CODE_DESIGN.md`; for the proofs: the drive
   (`/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/`).
6. Only for history: `proposal.md`, `applications.md`, `competitors.md`,
   `logic_models/README.md`, `../DEVELOPMENT/RESCOPE_D-ART3_DRAFT.md`.

## 8. Execution sketch (ledger-ready once D1–D8 are decided)

| # | Work | Depends on | Size |
|---|---|---|---|
| E0 | Implement `LabelVocabulary.fit`; exercise the labelled canonical path on ARB ego-KBs; pin tests | — | small, blocking |
| E1 | Proposition: closure + connectivity of `S2H(Σ_HG(k)*)`; Hypothesis-pinned test | — | small |
| E2 | Certificates module: medoid, `LB`, ratio; k-medoids (PAM) and LOF/kNN outlier scores over a precomputed metric; dendrogram (average/complete linkage, cophenetic); metric MDS with stress | — | medium |
| E3 | Reach layer: `B_r` enumeration + decode + dedup by `F_c` (`r ≤ 2`; pruning for `r = 3` is research); reach graph; ball-coverage consensus; isolated-node outliers | E1 | medium |
| E4 | Competitor distances on KBs: bipartite GED (Riesen–Bunke, hypergraph-adapted), alternating majority vote (`d_SED`), exact oracle at small `n`; reuse WL/NetLSD/HPD/nauty-edit/floors | — | medium |
| E5 | Synthetic KB-collection generators: planted consensus (labelled, anchored, uniformity-preserving noise), planted outliers (iso-twins + corruptions), planted hierarchy, all size-controlled | lessons L1–L2 | medium |
| E6 | Real collections: ARB `contact-*` ego-KBs grouped by label (probe-sized); WD50K ego-KBs (gated) | E0, probe | medium |
| E7 | Experiments RQ1–RQ5 with the S=27/BCa/Holm harness and pre-registered contracts | E2–E6 | large |
| E8 | Prose fold into `docs/article/` (PROPOSAL, DATA, COMPETITORS, theoretical, empirical) | E7 | medium |
