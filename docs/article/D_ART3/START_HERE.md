# D-ART3 — START HERE

*Entry point for the IsalHG journal article (target **IEEE TKDE**). Everything
an agent needs to pick this up is here or one hop away. Read this file end to
end, then [`prose.md`](prose.md) (the article's storyline — the document that
goes to the PI), then [`supplementary_data.md`](supplementary_data.md) and the
`foundation/` sheets, and only then the older v5.1 files, in the order of §7.
Last updated 2026-09-04, after the PI ratified the scope (§6.0) and the
addressing question was measured and closed (§0, RQ1).*

**Standing instruction (author).** Prior results are *guidance*, not assets:
every experiment may start from zero, designed for its own question, on its own
corpora. What carries over is the experience (`foundation/lessons.md`), the
theorems (`foundation/proved_facts.md`), the code, and the feasibility
envelope. And: one story, one evaluation axis per application; positives lead,
with the measured boundaries stated rather than hidden.

---

## 0. The one-paragraph state of play (2026-09-04)

The article is **metric analytics over collections of knowledge bases**, in
string space, at TKDE (PI-ratified, §6.0). A knowledge base is a set of facts
over anonymous constants — a labelled hypergraph — and the canonical word of a
knowledge base is a complete isomorphism invariant, so Levenshtein distance on
those words is a metric on isomorphism classes with polynomial pairwise cost,
computable optimality certificates, and a closed language in which every word
decodes to an object. The **alphabet changed** on the PI's ruling that similar
knowledge bases must sit at small distance: the inherited *pointer* addressing
fails that (one fact rewrites half the word, 0.500 normalized on all three
corpora), and the adopted encoding is a **fact token addressed by global
canonical rank** — one token per fact insertion, canonicalization from
milliseconds-with-6 %-censoring down to 20–60 µs with none. Two content-based
alternatives were built and refuted, which closed the design space and turned
the result into a frontier proposition (`prose.md` Prop 13): no
isomorphism-invariant addressing is `O(1)`-local under both fact edits and
constant edits without an extrinsic identifier, and **locality is won by the
mass of zero-cost edits, not by low average damage**. The adopted encoding's
boundary is therefore real and stated: it is one-token-local when the constant
set is preserved and inverts when constants move (75 % of real consecutive
quarters), which is why RQ3 runs on constant-preserving ladders over real
members with the natural series reported beside them. The knowledge-base
framing and the canonical-word metric are verified novel
(`foundation/literature_verified.md`).

## 0.1 What a takeover agent should do next

Nothing is blocked on a decision; the next work is implementation.

1. **Implement the adopted encoder in the package** (§8 E1). The probe's
   reference implementation is `scripts/diagnostics/d_art3_probes_2026-09-03/f4_topology/f4_encodings.py`
   (E-B); it needs a home under `src/isalhg/`, the role field of `prose.md`
   §2.1, `LabelVocabulary.fit`, and pinned tests including the completeness and
   iso-invariance checks the probe ran.
2. **Re-measure the two things the alphabet change invalidated**: the role
   field's cost under the adopted encoding (measured only under a refuted one),
   and compactness/bits, which was a pointer-alphabet result.
3. **Then the experiment pipeline** in the order of §8.

**One background job is live**: Picasso array `2206622` (`f4-ea`, 2 of 4 shards
written to `~/fscratch/results/f4_topology/ea/`) widens the slow pointer-alphabet
arm's coverage. It cannot move any conclusion — it only adds pairs to an arm
that already lost — so do not wait on it; harvest it into
`foundation/probes_2026-09.md` §9 when it lands.

## 1. Timeline — how we got here

| When | Scope | Outcome |
|---|---|---|
| 2026-06 | Iso-benchmark preprint (nauty/Traces/bliss on the Levi reduction) | complete, competitive, not faster than mature engines |
| 2026-07 | v3 metric-space article, *Information Sciences*: characterize → exploit (MDS, k-medoids, kNN, paths) | `d_I` loses A2/A3 on the FINAL size-controlled corpus (Stratum C, T-M4b); avalanche mechanism measured |
| 2026-08-09 | v4 draft: characterize → explain → instrument | honest but a limit paper |
| 2026-08-12 | **v5.1 D-ART3** (this folder): TKDE, "a certificate is not a space" — search framework C1, minimal countermodels C2, navigation C3, black-box optimization C4, real data C5 | pending PI; gates G-L1/G-D1/G-B1 unmeasured |
| 2026-08-12 | `logic_models/`: three PI ideas (repair, entailment, **median**) developed; P-MEDIAN recommended flagship; gate G-L4 closed (token lengths) | pending PI |
| 2026-09-03 | PI: idea 3 (consensus) leads; add outlier filtering, dendrogram, k-medoids, MDS over N KBs; venue TKDE | **v6 re-scope**: fact base verified from the data files and proof sources, five probes run, storyline in `prose.md` |
| 2026-09-03 | Data re-plan on the author's instruction (real corpora over synthetic) | two real collections selected by probe — WD50K(66) entity KBs and NDC-classes quarterly co-formulation KBs; ten ARB temporal datasets, JF17K, WikiPeople, HIC and the synthetic strata retired |
| **2026-09-04** | **PI ratifies the scope** (§6.0): string-space processing of KB collections is the centre, the logic material becomes a second paper, the alphabet may change, criterion = similar KBs at small Levenshtein distance | **v7**: `prose.md` rewritten, logic apparatus removed, real-world use stated per task, RQ1–RQ7 |
| **2026-09-04** | **The addressing question measured and closed** (RQ1) | fact tokens by global canonical rank adopted; two content-based schemes refuted; frontier proposition (Prop 13); the constant-set boundary quantified and RQ3 re-scoped accordingly |

Decision status: **the scope is PI-ratified** (§6.0) and the one technical gate
it opened is closed (§0). The active-article documents
`docs/article/{PROPOSAL,DATA,COMPETITORS,theoretical,empirical}` still describe
the superseded v3 scope and are folded last (§8 E8); this folder is the
authority until then, and `prose.md` is the storyline.

## 2. The verified fact base (read the sheets; here are the headlines)

`foundation/` holds four sheets produced on 2026-09-03 by reading the data
files, the proof `.tex` sources, and the literature — not the prose:

| Sheet | What it settles |
|---|---|
| [`foundation/measured_facts.md`](foundation/measured_facts.md) | every prior number with its file; favourable and unfavourable properties; supersessions; two corrections to the ledger |
| [`foundation/proved_facts.md`](foundation/proved_facts.md) | every theorem/lemma with status PROVED / CONDITIONAL / REFUTED; what labels do; the 14 retracted claims; what supports or threatens a median |
| [`foundation/literature_verified.md`](foundation/literature_verified.md) | DOI-verified citations only; novelty verdict |
| [`foundation/probes_2026-09.md`](foundation/probes_2026-09.md) | every measurement behind this scope: planted-consensus pilot (§1), bipartite-GED metricity (§2), ambient reach and ball coverage (§3), ARB contact ego-KBs (§4), WD50K entity KBs (§5), ARB temporal variant series (§6), qualifier-rich KG collections and entity types (§7), the `Σ⁺` prototype and proofs (§8), **the addressing/topology probe and the frontier (§9, with two follow-ups)** |
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

## 4. The article, v7 — one page (the full storyline is `prose.md`)

**Title (working).** *Knowledge Bases as Words: an Exact, Certified and
Locally Stable Metric for Collections of Relational Data up to Isomorphism.*

**Problem.** Given `N` knowledge bases over one schema — finite sets of facts
whose constants are anonymous or typed, so that renaming does not change the
knowledge base — find the member that best represents the collection, screen
the anomalous ones, organize it (hierarchy, k-medoids), map it, and extend it
with new valid members, under a distance well defined on isomorphism classes.
Each of these is a task an engineer already performs (`prose.md` §1 names the
setting for each — the PI's ratification obligation).

**What no existing representation offers together.** Exact identity, a true
metric, polynomial per-pair cost, a *closed language* in which every string is
a knowledge base, and *local stability*. Exact structure edit distance is
NP-hard per pair; the bipartite approximation is polynomial but not a metric
(Serratosa 2019; measured: asymmetric on 38 % of pairs, triangle violated on
1.4 % of triples, ten-vertex counterexample); embeddings are metrics and
stable but incomplete (false merges counted on real collections); hypergraph
optimal transport is computed to local optima and has no decoder; the
canonical-labelling certificate plus Levenshtein is an exact polynomial
metric — the *certificate member* of the family we introduce, faster and
compared on every table — but a certificate is not a language: no edit,
prefix, path or sample of one is an object.

**Thesis.** *A knowledge base is a word.* The canonical instruction word
gives knowledge-base space an exact identity (Theorem A), a metric with
computable certificates (Corollary A + the pairwise bound), compact keys, and
a closed language (every prefix, edit, alignment interior and generated sample
decodes to a knowledge base). A **fifth** prerequisite is now explicit because
the PI made it the criterion: *local stability* — similar knowledge bases at
small Levenshtein distance. The pointer alphabet fails it (one fact rewrites
half the word, measured), so the paper's second contribution is the
**addressing design**: pointer, global canonical rank, or local
`(colour, index)`, or positional-within-a-local-class. **Measured and closed
(RQ1):** the two content-based schemes are refuted with their mechanism;
global canonical rank gives one token per fact insertion where the constant
set is preserved and inverts where it is not; and the three failures together
yield a **frontier proposition** — no isomorphism-invariant addressing is
`O(1)`-local under both fact and constant edits without an extrinsic
identifier. That characterization is the contribution, and the rank encoding
is adopted because it maximizes the fraction of edits that cost nothing.

**Research questions** (one evaluation each; hypotheses and evidence in
`prose.md` §3):

- **RQ1 representation design** — which addressing makes similar knowledge
  bases close, at what cost in exactness, compactness and time. *Single-edit
  response and correlation with the true fact-level difference; the PI's
  criterion as a number. **Measured: global canonical rank adopted, one token
  per fact insertion; local colour addressing refuted with its mechanism.***
- **RQ2 well-posedness** — which distances satisfy which prerequisites, and
  what each missing one does to a real collection. *Theorems for ours;
  counterexamples and measured false merges for the others.*
- **RQ3 the representative record** — certified medoid (`≤ (2 − 2/N)·OPT`,
  measured ratio ≤ 1.63) and ball-coverage consensus (identifies the source of
  a variant collection: 12/12 measured), evaluated by the exact fact-level
  distance to the held-out next quarter, against the identity-using majority
  merge.
- **RQ4 the data-quality screen** — AUC of recovering injected corruptions on
  real members; false merges hide iso-twin anomalies from incomplete
  representations.
- **RQ5 description patterns** — k-medoids and hierarchy against Wikidata
  entity types (ARI with per-class support; cophenetic correlation), licensed
  by the measured `ν > 0` and hubness.
- **RQ6 generation** — a token sequence model over a real collection's words
  samples valid knowledge bases with probability 1 (Prop 6) against an
  incidence-list generator's rejection rate; the decodability figure;
  certificates admit neither (Prop 7).
- **RQ7 envelope** — the frontier is the fact count, labels are the
  tie-breaker; one figure and the yield table.

**Data** (`prose.md` §7; `supplementary_data.md`). Two real collections, one
question each, each with a control in the supplement: entity knowledge bases
of **WD50K(66)** (3,167 n-ary members; Wikidata types as class labels;
WD50K(100) as purity control) and the quarterly co-formulation knowledge
bases of pharmacologic classes in **NDC-classes** (1,432 members, 21.6 % of
consecutive quarters one-edit variants with exact fact-level truth;
NDC-substances as control); controlled corruptions of real members for RQ4;
a synthetic envelope sweep for RQ7 only. Retired after probing: planted
families, Stratum C, contact induced ego-networks, HIC, JF17K, WikiPeople,
and ten of the twelve ARB temporal datasets (numbers in the supplement).

**Competitors.** Exact oracle, bipartite GED (both readings), majority-vote
merge with identities, WL, NetLSD, HPD, HyperCOT (gated), the certificate
member, two naive floors; capability matrix with eight columns filled by
theorem or counterexample.

**Theory delivered.** Thms 1–2 (exactness and metric, for any
isomorphism-invariant addressing); Props 1–3 (length and key size; closure;
certificates); Props 4–6 (fact-level simulation and ball inclusions, source
identifiability, generative closure); Props 7–9 (what certificates, bipartite
GED and refinement keys lack); Obs 10 (the measured instability of pointer
addressing — the motivation for RQ1). Full table: `prose.md` §4.

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

## 6.0 PI ratification (2026-09-04) — his answers, and what they change

*The PI answered against the older list in [`README.md` §5](README.md#5-decisions-the-pi-must-make),
not against §6 below. His words, the mapping, and the consequence:*

| His answer (verbatim, condensed) | Maps to | Consequence |
|---|---|---|
| *"el centro del artículo debe ser el procesamiento de KBs en el espacio de cadenas, porque así nos quitamos de un plumazo todos los competidores. Ahora bien, habrá que justificar que estas tareas (medianoides, detección de outliers, dendrogramas, etc) serían de utilidad en el mundo real."* | README D1 / §6 D1 | **RATIFIED with an obligation.** String-space processing of knowledge-base collections is the centre. New requirement met in `prose.md` §1: a table giving each operation its engineer's question and the setting where it is already performed (golden-record construction, knowledge-graph error detection, schema/pattern induction, collection audit, benchmark generation). |
| *"el manuscrito para TKDE no debería profundizar demasiado en los aspectos lógicos… Si más adelante queremos hacer un segundo manuscrito centrado en la lógica, estaría bien como extensión."* | README D2 | **RATIFIED: two papers.** The logic apparatus (first-order fragments, decidability, model-theoretic justification) is out of this manuscript; `prose.md` standing rule (iii) enforces it, `logic_models/` becomes source material for the follow-up, and `prose.md` §10 names it. Knowledge bases are treated as data throughout. |
| *"no tenemos por qué obligarnos a mantener el alfabeto del preprint… la propuesta F4 sería la mejor… eso aumentaría las novedades respecto al preprint, y eso es bueno. Lo importante es que el espacio de cadenas tenga una buena estructura topológica: KBs parecidas deben codificarse en cadenas cuyas distancias de Levenshtein sean pequeñas."* | README D3′ / §6 D3 | **RATIFIED, and it enlarges the decision.** The alphabet may change and F4 (a native fact token) is preferred. **The criterion is stronger than the design I had proposed:** my `Σ⁺` was a *decoder-side* extension that leaves `w*_c` — and therefore the distance — unchanged, so it does not deliver "similar KBs at small Levenshtein distance". Meeting the criterion requires changing the **encoder**. `prose.md` §2.3 states the addressing design space (pointer / global rank / local `(colour,index)`) and **RQ1 measured it the same day** (`foundation/probes_2026-09.md` §9): local colour addressing is refuted with its mechanism; global canonical rank meets his criterion **where the constant set is preserved** (one token per fact insertion; canonicalization 20–60 µs with no censoring) and *inverts* where constants move, so what the article can promise him is a characterized trade-off between content- and position-addressing rather than an unqualified improvement. The locally-keyed third design that would have escaped the trade-off was built and is also refuted, which closes the design space and turns the trade-off into a frontier proposition (`prose.md` Prop 13). |
| *"Para las preguntas D4, D5 y D6, no veo inconveniente en seguir la recomendación de Claude."* | README D4, D5, D6 | **RATIFIED as recommended.** D4: the instability lower bound stays time-boxed with the measurement as its pre-agreed fallback (`prose.md` Obs 10) — and under a fact alphabet it becomes the *motivation* for the redesign rather than an apology. D5: the HIC exhibit is retired from the paper, loader and gate kept in the ledger. D6: the earlier clustering/kNN negative was measured on a corpus that is now retired from the data plan, so the reporting obligation transfers to the Limitations section as the characterized instability of the pointer alphabet — consistent with the author's "one axis, positives first" instruction, since under a fact alphabet those numbers describe the *old* representation. |

**Two decisions the first author took on the same day, extrapolating where the
PI's answers did not reach:**

- **RQ1 selection rule, pre-registered before the measurement.** Adopt the
  addressing scheme with the **best measured local stability**, whichever it
  is — even if it turns out to be the global-rank scheme whose distance is
  statistically indistinguishable from the nauty-certificate distance. Present
  the best result, then explain why it is the best; the losing encodings keep
  their numbers in the supplement and the internal record. *Consequence the
  paper must own explicitly (`prose.md` §2.3): if the global-rank scheme wins,
  the distinctiveness rests entirely on the language properties — total
  decoding, the ball-coverage consensus, the generative model — and that
  argument has to be written, not implied.*
- **Argument roles ride inside the fact token.** A statement's subject, object
  and qualifier values are encoded as `(role, constant)` pairs, so nothing is
  abstracted away and arity stays native; the arity-2 incidence encoding
  remains the fallback for the pointer alphabet, at the cost of inflating the
  constant count (`prose.md` §2.1). Sent to the running probe as an optional
  fourth arm on WD50K, to be re-measured later if it does not fit the budget.

**The gate is closed (2026-09-04, `foundation/probes_2026-09.md` §9).** The
PI's criterion is met by **fact tokens addressed by global canonical rank**: a
fact inserted over existing constants costs **exactly one token** on all three
corpora, against 5–15 tokens and half the word under the pointer alphabet
(normalized single-edit response 0.188–0.300 against 0.500), completeness and
iso-invariance clean over 3,000 instances, and canonicalization down from
milliseconds-to-seconds with a 6 % censor rate to 20–60 µs with none. Two
findings came with it that the article now owns:

- **My local-addressing hypothesis was refuted.** Addressing by
  `(refinement colour, index)` is the *worst* of the three — it rewrites the
  whole word — because a colour is a global hash: one fact edit moves 92–98 %
  of depth-3 colours (36–52 % at depth 1), while the canonical rank order
  survives 68–85 % of edits. The generalizable lesson, now a paper
  observation: **address symbols must be positional, not content-hashed.**
- **The boundary is the constant set, and it is an inversion rather than a
  caveat.** Split by regime on the real NDC series (140 constant-preserving
  pairs, 415 changing): where constants are preserved the rank encoding gives
  **1 token** at Δ = 1 against the pointer alphabet's 5, and 77 % of pairs
  within two tokens against 17 %; where constants change it is **worse than
  the pointer alphabet** — 7 tokens against 4, 0 % within two tokens against
  40 % — and its distance tracks *the number of constants moved* (ρ = 0.503)
  rather than the number of facts changed. The pooled figures above average a
  1:3 mix on that corpus and must not be quoted alone. The honest shape of the
  result is a **trade-off**: content-addressed encodings pay globally per fact
  edit, position-addressed ones pay globally per constant edit. Whether a
  third point is local in both (positional addressing within a locally
  determined class) was then built and measured, in a fine and a coarse
  variant — **also refuted**, never within two tokens of a one-edit neighbour
  in 31,279 pairs. That closes the design space and turns the trade-off into a
  **frontier proposition** (`prose.md` Prop 13): content-determined addresses
  change at every fact edit's site (0 of 21,528 edits left such a map intact);
  position-determined ones are untouched with probability 0.22–0.57 under fact
  edits but renumber the word when the constant set changes; hybrids inherit
  both; escaping requires an extrinsic identifier, which invariance forbids.
  The keeper sentence: **locality is won by the mass of zero-cost edits, not
  by low average damage** — which is precisely why the rank encoding wins, and
  it stays adopted for that measured reason.
- **It bites RQ3.** Restricted to constant-preserving quarters the NDC corpus
  collapses to **15 drug classes with a run of ≥ 3 quarters, 2 with ≥ 5** —
  too small to carry the consensus experiment alone. Plan of record: RQ3 runs
  on constant-preserving ladders over *real* members, with the natural series
  reported beside them as the harder case. Open scoping decision, recorded not
  buried.

**Accepted with it:** the adopted encoding correlates with the
canonical-labelling certificate distance at ρ = 0.62–0.96, so — exactly as
pre-registered — the article's distinctiveness rests on the language
properties, and `prose.md` §2.3 and §6 make that argument explicitly.

## 6. Decisions for the PI — developed (2026-09-03, v6.1; superseded in part)

> **Read §6.0 first.** This section is the pre-ratification development. Where
> the two disagree, §6.0 and `prose.md` win. Two items below are now factually
> wrong and are corrected in place: D3's "ruled out: re-designing the encoder"
> (the encoder *is* what changed) and D5's "probes running" (they landed, and
> the collections changed).

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
  ball — source unique maximiser 12/12 at both noise levels). ~~Ruled out:
  re-designing the *encoder*.~~ **Overtaken by the PI's ratification**: the
  encoder is exactly what changed, because a decoder-side extension cannot
  make similar knowledge bases close. The `Σ⁺` work is retained as the
  constructive basis for Props 4–5, not as the alphabet.
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
  hyper-relational knowledge graph and time series of real interaction
  knowledge bases with exact fact-level truth. **Settled by the probes
  (`foundation/probes_2026-09.md` §6–§7): WD50K(66)** entity KBs (not
  WD50K(100), which is the purity control) **and NDC-classes** quarterly
  co-formulation KBs (not the contact corpora, whose consecutive windows churn
  wholesale). Controlled corruptions are applied to *real* members for the
  outlier test, because outlier ground truth cannot exist without
  intervention; the only fully synthetic data is the envelope sweep, because
  real collections do not span sizes. The synthetic planted
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
- ~~**D3 — Alphabet.** Keep `Σ_HG` for this paper; the semantics-aligned
  alphabet is future work.~~ **REVERSED by the PI and by measurement**: the
  alphabet changed in *this* paper, to fact tokens addressed by global
  canonical rank (§6.0, `prose.md` §2.3).
- **D4 — nauty-edit's role.** Present the canonical-labelling edit distance as
  the *certificate member* of the canonical-word family we introduce (exact,
  metric, faster, not decodable), compared on every table, rather than as an
  adversary. **Yes** — it is honest and it turns a loss into a family result.
- ~~**D5 — Real data.** WD50K primary, ARB `contact-*` as a constrained
  exhibit.~~ **Superseded by the probes**: WD50K(66) and NDC-classes quarterly
  are the two collections; the contact corpora are out (§6.0 D5,
  `supplementary_data.md`).
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

## 8. Execution sketch — ledger-ready (scope ratified; RQ1 closed)

Nothing here waits on a decision. E1 is blocking because every later row
consumes the adopted encoding.

| # | Work | Depends on | Size |
|---|---|---|---|
| **E1** | **Adopted encoder into the package.** Port the probe's reference implementation (`scripts/diagnostics/d_art3_probes_2026-09-03/f4_topology/f4_encodings.py`, arm E-B) to `src/isalhg/` as a first-class encoding: fact tokens `F[ℓ; (role, rank)…]` with the role field of `prose.md` §2.1, the type prefix, canonical ranks from the Levi canonical labelling. Implement `LabelVocabulary.fit` (still `NotImplementedError`). Pin: completeness and iso-invariance (the probe's N0/M0 checks as tests), plus a golden word per fixture | — | medium, **blocking** |
| E2 | **Re-measure what the alphabet change invalidated**: (a) the role field's cost under the adopted encoding — it was measured only under a refuted one; (b) compactness/bits, which was a pointer-alphabet result and needs the `n + m` word and a labelled alphabet-size estimator | E1 | small |
| E3 | Distance + certificates module: token Levenshtein on the new words; medoid, pairwise lower bound `LB`, certified ratio; k-medoids (PAM), kNN/LOF outlier scores, average-linkage dendrogram with cophenetic correlation, metric MDS with stress — all over a precomputed metric | E1 | medium |
| E4 | Language layer: total decoder for the new alphabet; ball enumeration at `r ≤ 2` with dedup by canonical key; ball-coverage representative; the decodability figure of D8 | E1 | medium |
| E5 | Competitor distances on KBs: bipartite GED (both readings, hypergraph-adapted), the identity-using majority merge, exact oracle at small `n`; reuse WL / NetLSD / HPD / certificate member / naive floors | — | medium |
| E6 | Collections: WD50K(66) entity KBs with types (loader exists in `hyperrel/`); NDC-classes quarterly KBs (loader exists in `arb_temporal/`); **constant-preserving ladders over real members** for RQ3; corruption injector (spurious / missing / wrong-argument / iso-twin) for RQ4; the envelope sweep generator for RQ7 | E1 | medium |
| E7 | Experiments RQ1–RQ7, one evaluation axis each, S = 27 / BCa / Holm harness, pre-registered contracts written before results | E2–E6 | large |
| E8 | Prose fold into `docs/article/` (`PROPOSAL`, `DATA`, `COMPETITORS`, `theoretical`, `empirical`), which still describe the superseded v3 scope | E7 | medium |
| E9 | Write the propositions the measurements now support: Thm 1 for fact addressing, Prop 4 (fact-level simulation), Prop 7 (certificate sets are not languages), **Prop 13** (the addressing frontier) | E1 | medium |

**Retired from this sketch:** the `Σ⁺` decoder-side extension as an alphabet
(kept only as the constructive basis of Props 4–5), the reach layer over the
pointer alphabet, and the ARB `contact-*` collections.
