# Article writing plan — IEEE TKDE, "Knowledge bases as words"

**Owner:** `[Opus-Article-Orchestrator]` · **Created:** 2026-10-04 ·
**Status:** DEFINITIVE (v1). Changes after this date are appended in §15, never
rewritten in place.
**Target output:** `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/article/journal/6a788a680cdbdddd16e47a6e/submission/article/`
(an Overleaf git clone; local commits only — **never `git push` without the
author's explicit word**).

**Inputs this plan was built from (read in this order if you are a writer).**
1. This file (binding).
2. `WRITING_BRIEF_2026-10-04.md` — Fable's brief: per-RQ state, reading list,
   framing per result, supplement list, notation.
3. `foundation/rq{1_addressing,2_wellposedness,2_ow,3v2,6_generation,7_envelope,8}_facts.md`
   — **the only place a number may be copied from.** Per-corpus RQ1 tables:
   `…/isalhg/results/IEEETKDE/RQ1_isal/merged/rq1_statistics_{wd50k66,ndc_classes}.md`.
4. Proofs: `…/isalhg/proofs/completeness/theorem_c_ordered_walk.tex` (Theorem C,
   Corollary C, Props C.4–C.7) and `theorem_a_completeness.tex` (Theorem A);
   Prop. C.8 in `experiments/RQ8_PILOT.md` §1.
5. `experiments/HEADLINE_DESIGN_2026-09-13.md` §0, §3, §4, §8 (designs,
   hypotheses, amendments).
6. `foundation/literature_verified.md` + `docs/article/RELATED_WORK.md` (verified
   citations).
7. Structural model: IsalSR TPAMI paper,
   `/media/mpascual/Sandisk2TB/research/ISAL/completed/isalsr/article/journal/69c1637a28a81fea2badda9a/article/paper/`
   (12 pages, compsoc; Intro → Related → Methodology with S2D/D2S figures and
   theorems → Experiments → Results → Discussion → Conclusion).

`…/isalhg/` = `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/`. Paths without
a root are relative to `docs/article/D_ART3/` in the IsalHG repo.

---

## 1. Venue constraints (IEEE TKDE)

| constraint | value | consequence |
|---|---|---|
| Regular paper length | **14 formatted pages including references and author biographies**; hard maximum 18 with mandatory over-length page charges | budget is 14.0 pages (§6); the 15th page is a defect, not a buffer |
| Template | IEEEtran, Computer Society journal: `\documentclass[10pt,journal,compsoc]{IEEEtran}` | the sample in `submission/article/bare_jrnl_new_sample4.tex` is the non-compsoc template; do not build on it |
| Abstract | IEEE guidance 150–250 words; we write **≤ 200** | one paragraph, no citations, no math beyond `w°` |
| Keywords | IEEE CS index terms, 5–8 | §3 |
| Supplemental material | allowed, does not count toward pages | full proofs, negative and neutral results, corpus derivation |
| Prior version | the authors' preprint **arXiv:2607.10194** ("Instruction Set and Language for Hypergraphs") is public, and IEEE CrossCheck indexes arXiv | cite it, state the delta (§3.2) in the introduction and the cover letter, and **write every sentence fresh** — no text reuse from the preprint, IsalGraph (arXiv:2603.11039) or IsalSR |
| Review model | to verify on the TKDE author page before submission (single-blind expected) | `main.tex` carries an `\ifanonymous` switch that hides authors, bios, acknowledgments, and rewrites self-citations to third person; output goes to `submission/double_blind/` if needed |
| AI disclosure | IEEE requires disclosure of AI-generated content in the acknowledgments | reuse the IsalSR wording pattern (code + manuscript drafting assistance, reviewed by the authors) |
| Code and data | stated in the paper | `https://github.com/MarioPasc/IsalHG`; corpora derivation scripts in the repo |

Sources: IEEE CS TKDE author information (regular papers 14 pages incl.
references and bios; 18-page maximum with MOPC), cross-checked 2026-10-04 via
the computer.org CFP and the indexed author-information summary. **Verify once
more on the live author page before submission** (§14 item 8).

What TKDE rewards (from `venue.md` §1, still valid in substance): a
data/knowledge problem, an algorithm with pseudocode and stated complexity,
scalability with an operating envelope, real data, community baselines, theory
that licenses the algorithms. Desk-rejection triggers to avoid: "application
study whose engineering contribution is incidental", "novelty is a renamed
component", "decisive table depends on a single benchmark".

---

## 2. The paper in one paragraph

A knowledge base (KB) is a finite set of facts over constants whose names do
not matter, so it is a labelled hypergraph and two KBs that differ by a
renaming are the same object; collections of such KBs arise as entity
descriptions in hyper-relational knowledge graphs, extraction runs, anonymised
fragments and periodic category records. Deduplicating a collection, choosing
its reference record, generating more records like it, and completing a
partial record all require a distance on isomorphism classes, and every
existing candidate misses at least one prerequisite: exactness at zero, the
metric axioms, polynomial per-pair cost, a closed language in which every
string is a KB, and locality under small edits. We write each KB as a program
for a small pointer machine and define a deterministic canonical program, the
**ordered walk `w°`**, that emits the program along a canonical labelling of
the constants: nauty decides which constant comes first, the language decides
what is written. `w°` is a complete isomorphism invariant (Theorem C), so
Levenshtein distance between words is a metric on isomorphism classes,
computed after one canonical-labelling call and a linear emission; and every
word decodes to a connected KB (Prop. C.4), so edits, alignments, consensus
candidates, samples and continuations of words are all KBs. A
canonical-labelling certificate with Levenshtein is as exact and as fast for
identity, and we say so first; what it lacks is a language, and the
operations that need one are where the paper's results are.

**Working title (default):** *Knowledge Bases as Words: An Exact Metric and a
Closed Language over Isomorphism Classes of N-ary Knowledge Bases.*
Alternatives: (b) *Writing Knowledge Bases as Programs: Exact Comparison,
Consensus and Generation up to Renaming*; (c) *IsalHG: A Closed Instruction
Language for Collections of N-ary Knowledge Bases.* The author picks (§14).

**Authors (default, to confirm):** Mario Pascual-González, Ezequiel
López-Rubio (corresponding), as on arXiv:2607.10194. Bio photos present in
`submission/article/` (`MarioPascual.jpg`, `EzequielLopez.pdf`).

---

## 3. Contributions and the novelty delta

### 3.1 Contributions (the list printed at the end of the introduction)

- **C1 — A canonical program without search.** The ordered walk `w°`, a
  deterministic emitter along a canonical labelling of the constants, with a
  proof that every such round-tripping emitter is a complete isomorphism
  invariant (Theorem C); hence `d_I = d_Lev(w°(K), w°(K'))` is a metric on
  isomorphism classes of labelled n-ary KBs, at the cost of one
  canonical-labelling call plus an emission linear in the word.
- **C2 — The language properties that a certificate lacks.** Every word over
  the alphabet decodes to a connected KB (Prop. C.4); every continuation of a
  record's word decodes to a KB containing the record (Prop. C.8); the word
  never names a constant, so a change of canonical order inside a class of
  equivalent constants leaves it unchanged (Prop. C.6).
- **C3 — Collection operations with guarantees.** Exact census and
  deduplication; the certified medoid; a golden-record consensus computed as a
  generalized median over decoded word balls, which can return a record no
  member wrote; generation with validity 1; and valid completion of a partial
  record — each with pseudocode and complexity.
- **C4 — Evaluation on two real collections.** WD50K(66) hyper-relational
  entity descriptions (3,988 KBs) and NDC-classes co-formulation records (1,381
  KBs), against edit-distance, feature-map, spectral, portrait, transport and
  certificate competitors, 27 seeds, BCa intervals, Holm-corrected tests:
  zero false merges where embeddings merge up to 212,179 non-isomorphic pairs;
  every generated sample valid and connected (270,000 / 270,000 per
  collection) where an incidence-list generator returns one usable sample in
  578 and 11,739; a 1,252× faster distance matrix than the family's
  search-based form with no censored member; pendant deletions (a fact, or a
  constant's last occurrence) absorbed within two instructions on 59–88 % of
  cases where the certificate never is (pendant insertions with a new constant:
  4–15 %, still above the certificate's 0 %); completion
  that places a missing fact correctly more often than co-occurrence
  recommenders on relational records.

### 3.2 Delta to the authors' prior work (state it in §1 and the cover letter)

| object | where it first appeared | status here |
|---|---|---|
| machine, alphabet `Σ_HG`, decoder S2H, closure | arXiv:2607.10194 | restated compactly for self-containment, newly written, cited |
| search-based canonical string `w*_c`, its completeness (Theorem A) | arXiv:2607.10194 | cited as the family's search form; appears in the cost ablation only |
| iso-testing benchmark vs nauty/Traces/bliss | arXiv:2607.10194 | not repeated; identity speed conceded |
| labelled KBs as the object; collection operations | **new** | — |
| ordered walk `w°`, Theorem C, Corollary C | **new** | — |
| connected language (C.4), prefix property (C.8), name-freedom (C.6), star locality (C.5), orbit pruning (C.7) | **new** | — |
| every experiment (RQ1–RQ8) | **new** | — |
| graphs (IsalGraph, arXiv:2603.11039), DAGs for symbolic regression (IsalSR, TPAMI submission) | siblings | cited as the family; neither handles n-ary labelled facts |

---

## 4. Framing rules (binding on every writer)

The author's instruction: the main text carries the results that favour
IsalHG, presented as hypotheses about IsalHG that experiments test; negative
and neutral results go to the supplement (written later). The rules below make
that exposition both persuasive and correct under review.

1. **Hypotheses follow from the theory.** Each result subsection opens with a
   hypothesis stated as a consequence of a proved property ("Proposition 2
   implies that any model over words samples only KBs; we test whether…").
   Never write a timeline ("before the experiments we expected"). The word
   *pre-registered* appears once, in the protocol paragraph of §7, where it is
   literally true: hypotheses, metrics, baselines and fallbacks were fixed
   before each campaign, and amendments made before re-measurement are named
   where they apply (RQ8's fact-count-matched protocol).
2. **Scope in the sentence.** Every main-text claim carries its scope condition
   in the same sentence or the next: *pendant* edits (RQ1), *relational*
   (non-star) records of WD50K(66) (RQ8), *validity and domain membership*, not
   sample quality (RQ6), cost *against the search form*, not against nauty
   (RQ7). A scope condition is never moved to the supplement; the numbers that
   lie outside the scope are.
3. **One clause and a pointer for each scoped-out loss.** Where a competitor
   wins outside the claimed scope, the main text gives one clause naming the
   condition and points to the supplement ("on interior argument edits the
   certificate is more local; Supplementary Table S3"). Four such clauses
   exist: RQ1 interior edits; RQ6 novelty (the fact-list generator wins it —
   print the number and the 7.3 % connected-of-novel figure beside it); RQ8 on
   NDC-classes and on star-shaped records (pattern-prediction gaps); and, in
   the discussion, clustering against entity types (RQ5).
4. **Concede identity speed in the introduction** (lesson L17): for deciding
   isomorphism and deduplicating, canonical-labelling engines are equally
   exact and faster or at parity; we make no canonicalization-speed claim
   against nauty anywhere.
5. **Never claim:** a faster isomorphism test; that `d_I` approximates or
   proxies an edit distance (L18); local stability without the pendant
   qualifier; scaling beyond the measured envelope (`n ≤ 24`,
   `3 ≤ m ≤ 110`, `k ≤ 10`, connected, labelled); argument roles (facts are
   sets); results on disconnected KBs; that WL *failed* on these corpora (its
   incompleteness is a theorem; its measured merges here are zero).
6. **Every number has a source comment.** In the `.tex`, the line above any
   sentence carrying a measured number holds
   `% src: foundation/<file>.md §<section>` (invisible in the PDF). Unsourced
   numbers are deleted at review.
7. **Process vocabulary stays out of the paper.** No task ids, decision codes,
   run tags, job ids, "arm", "cell", "campaign", "gate", "wave", code names
   (`isal_ow_struct`, `pattern_cooc`). Use display names (§5.3).
8. **Novelty phrasing.** "To our knowledge" at most once, for the
   canonical-word metric on isomorphism classes of n-ary KBs
   (`literature_verified.md`, verdict 1). No "first", "novel",
   "groundbreaking".

---

## 5. Notation, names and terminology (canonical; `macros.tex` implements it)

### 5.1 Symbols

| concept | symbol | macro |
|---|---|---|
| knowledge base; collection | `K`; `\mathcal{K} = \{K_1,…,K_N\}` | — |
| constants, facts | `V(K)`, `E(K)`; `n = |V|`, `m = |E|` | — |
| type of a constant, predicate of a fact | `\ell_V`, `\ell_E` | — |
| maximum arity | `k` | — |
| alphabet | `\Sigma_{\mathrm{HG}}(k) = \{V_{i,j}, C_i, P_i, N_i, W\}` | `\SigHG` |
| decoder / encoder | `\mathrm{S2H}` / `\mathrm{H2S}` | `\StH`, `\HtS` |
| machine state | `(H, L, p_1,…,p_k)`, `L` the circular doubly linked list | — |
| ordered walk (headline program) | `w^{\circ}(K)` | `\wo` |
| tie-complete search form | `w^{*}_{c}(K)` | `\wc` |
| canonical labelling | `\pi_K` | — |
| word distance | `d_I(K,K') = d_{\mathrm{Lev}}(w^\circ(K), w^\circ(K'))` on instruction tokens, raw (never length-normalised: not a metric) | `\dI` |
| indel distance (consensus objective only) | `d_{\mathrm{indel}}(u,v) = |u|+|v|-2\,|\mathrm{LCS}(u,v)|` | `\dindel` |
| ball of radius `r` | `B_r(u)` | — |
| certified ratio | `\mathrm{cost}(M)/\mathrm{LB}`, `\mathrm{LB} = \sum_{i<j} d(K_i,K_j)/(N-1)` | — |

### 5.2 Words

- "knowledge base (KB)" defined once in §1, then **KB** throughout; "fact",
  "constant", "predicate", "type". "Hypergraph", "vertex", "hyperedge" only in
  §3 where the encoding is defined and in proofs.
- "canonical program" = the rule; "word" = its output; "program" = any word.
- "certificate" means **nauty's canonical form only**; the representative's
  guarantee is always "certified ratio".
- *star* KB: one constant in every fact and no other constant shared;
  *relational* (non-star) otherwise. Edits and hidden facts are *pendant*
  (change the constant inventory) or *interior*.
- "closed language": every word decodes; "connected language": every word
  decodes to a connected KB. Use "closed and connected" when both are meant.

### 5.3 Display names (code arm → paper name)

| code | paper |
|---|---|
| `isal_ow_struct` | ordered walk `w°` (ours) |
| `wstar_orbit` | search form `w*_c` (orbit-pruned) |
| `nauty_cert`, `nauty_cert_rows` | nauty certificate (byte / row serialization) + Levenshtein |
| `wl_l1` | WL histogram (L1) |
| `netlsd` | NetLSD (Levi graph) |
| `hpd_jsd` | hyperedge portrait divergence (HPD) |
| `bipartite_ged_assign` / `_path` | bipartite GED, assignment value / edit-path cost |
| exact HGED oracle | exact hypergraph edit distance |
| `hypercot` | HyperCOT |
| `size_l1`, `degree_seq_l1` | size floor, degree-sequence floor |
| `ow_ngram`, `ow_ngram_ho_1f` | n-gram over `w°` words; fact-count-matched back-off n-gram |
| `fact_ngram` | n-gram over a canonical-rank fact list |
| `incidence_ngram` | n-gram over an incidence-list serialization |
| `pattern_cooc`, `pattern_freq`, `random_pattern` | co-occurrence recommender, frequency recommender, random pattern |
| `consensus_ow` | word-space consensus (ours) |
| `align_merge_ref`, `align_merge_iter`, `pattern_vote` | reference-aligned merge, iterative aligned merge, pattern vote |
| `majority_merge_id` | identity-using majority merge (oracle reference) |
| `wd50k66`, `ndc_classes` | WD50K(66), NDC-classes |

---

## 6. Page and word budget (14.0 pages)

IEEEtran compsoc 10 pt two-column: ≈ 950 words per full text page. Budgets
include in-section figures/tables as page area.

| § | section | pages | words (text) | owner |
|---|---|---|---|---|
| — | title, abstract (≤ 200), index terms | 0.45 | 200 | orchestrator |
| 1 | Introduction | 1.25 | 1,150 | orchestrator |
| 2 | Related Work | 0.90 | 850 | orchestrator |
| 3 | Problem Setting | 0.70 | 650 | Worker A |
| 4 | The Instruction Language | 1.90 | 1,250 + Fig. 2 + Tab. I + Alg. 1–2 | Worker A |
| 5 | Properties of the Word Space | 1.40 | 1,300 | Worker A |
| 6 | Collection Operations | 0.90 | 700 + Alg. 3 | Worker A |
| 7 | Experimental Setup | 0.85 | 700 + Tab. II | Worker B |
| 8 | Results | 2.95 | 1,900 + Tabs. III–VII + Figs. 3–4 | Worker B |
| 9 | Discussion and Limitations | 0.55 | 520 | Worker B |
| 10 | Conclusion | 0.25 | 230 | orchestrator |
| — | acknowledgments, AI disclosure, data availability | 0.15 | 120 | orchestrator |
| — | references (≈ 50 entries, IEEEtran) | 1.30 | — | all |
| — | biographies (2) | 0.45 | 2 × 90 | orchestrator |
| | **total** | **14.00** | ≈ 9,750 | |

Overflow levers, in order: (1) move Alg. 3 to the supplement and keep its
complexity statement; (2) merge Tabs. V and VII into one; (3) shorten §2 to 700
words; (4) Fig. 1 from full width to column width.

---

## 7. Section-by-section plan, paragraph level

Each item is one paragraph unless marked. "Src" names the source for the
facts in that paragraph.

### Abstract (orchestrator, written last, ≤ 200 words)

Problem (collections of anonymous n-ary KBs; operations need a distance on
isomorphism classes) → gap (no existing distance is exact, metric, polynomial
and a closed language) → method (KBs as programs for a pointer machine;
ordered walk along a canonical labelling) → theory (complete invariant ⇒
metric; every word decodes to a connected KB) → evidence (three numbers: 0
false merges vs up to 212,179; 270,000/270,000 valid and connected samples vs
1 usable in 578 / 11,739; matrix 1.39 s vs 28.9 min for the search form with
no censored member) → scope sentence (identity speed conceded; the gains are
the language's) → code URL.

### §1 Introduction (orchestrator, 1,150 words)

1. **Collections whose names do not matter.** One-hop entity descriptions with
   qualifiers in hyper-relational KGs (WD50K [Galkin 2020]), fact sets from
   extraction runs, anonymised/blank-node RDF fragments, periodic category
   records (NDC). Constants are anonymous, untrusted or irrelevant; facts of
   arity ≥ 3 make the object a hypergraph. Two KBs differing by a renaming are
   one object.
2. **What is done with a collection.** Deduplicate; pick the reference among N
   disagreeing descriptions (golden record [Bleiholder & Naumann; data
   fusion]); generate more (benchmark construction, synthetic stand-ins);
   complete a record. Each needs a dissimilarity that is (P1) exact at zero,
   (P2) a metric, (P3) polynomial per pair, (P4) a closed language, (P5) local
   under small edits. One sentence on why each matters (P1 → exact dedup; P2 →
   approximation ratio of the medoid; P3 → an N × N matrix at all; P4 →
   consensus, generation and completion return KBs; P5 → near-identical KBs
   close).
3. **What exists, and what each lacks.** Exact (H)GED: NP-hard per pair [Qin
   ICDE 2023; Blumenthal & Gamper]. Bipartite GED: polynomial, not a metric
   [Serratosa 2019; Riesen & Bunke]. WL / spectral / portrait embeddings:
   metrics on vectors, incomplete on isomorphism classes [Cai–Fürer–Immerman;
   NetLSD; HPD]. HyperCOT: a metric in theory, computed as a local optimum,
   needs a measure, no decoder [Chowdhury 2024]. Canonical labelling plus
   Levenshtein: exact, metric, fast — but a certificate is not a language: an
   edited certificate is not a certificate and no model generates
   certificates [McKay & Piperno].
4. **Our approach.** Write each KB as a program for a pointer machine [arXiv:2607.10194];
   choose one program per isomorphism class by emitting it along a canonical
   labelling of the constants. nauty decides which constant comes first; the
   language decides what is written. Name the two consequences: a metric on
   isomorphism classes, and a language whose every word is a connected KB.
5. **The concession, stated plainly.** For identity alone, certificate engines
   are equally exact and at least as fast; we do not compete there. The
   paper's claims are about what a language adds.
6. **Contributions** — the C1–C4 list of §3.1, each with ≤ 1 headline number.
7. **Relation to prior work by the authors** — two sentences from §3.2, then a
   one-line roadmap.

### §2 Related Work (orchestrator, 850 words, four subsections)

- **2.1 Distances on graphs, hypergraphs and their metric status.** GED and
  HGED [Qin 2023; Blumenthal et al. VLDBJ 2020; Blumenthal & Gamper 2020];
  bipartite approximation and its non-metricity [Riesen & Bunke 2009;
  Serratosa 2019]; WL kernels and hypergraph WL bounds [Cai et al. 1992; Huang
  & Yang 2021]; NetLSD; hyperedge portrait divergence; HyperCOT. Close: none
  is exact, metric, polynomial and decodable at once.
- **2.2 Canonical forms as data primitives.** nauty/Traces [McKay & Piperno
  2014], bliss [Junttila & Kaski 2007]; gSpan's minimum DFS code as a
  canonical string for enumeration, not a metric [Yan & Han 2002]; canonical
  SMILES [Weininger] — **verify**. The Isal family [IsalGraph, IsalSR, the
  preprint]. Close: canonical codes are used for identity; we define a
  distance on them and use their language.
- **2.3 Closed string languages and valid-by-construction generation.**
  SELFIES (every string a valid molecule) [Krenn et al. 2020 — **verify**],
  grammar-constrained generation [Kusner et al. 2017 — **verify**], graph
  generators with validity checks [GraphRNN, You et al. 2018 — **verify**].
  Position: SELFIES gives robustness for molecules; it is not a complete
  invariant with a metric on isomorphism classes and does not address n-ary
  labelled facts. This paragraph pre-empts the "SELFIES for KBs" objection.
- **2.4 Consensus, golden records and KB completion.** Generalized median
  graphs and the medoid's 2-approximation [Jiang, Münger & Bunke 2001]; median
  string NP-completeness [de la Higuera & Casacuberta 2000]; embedding-based
  median graphs [Ferrer et al. 2010]; data fusion / golden records
  [Bleiholder & Naumann — **verify**]; distance-based KB merging over named
  vocabularies [Konieczny & Pino Pérez 2002]; n-ary KG link prediction (StarE
  [Galkin 2020], HINGE [Rosso 2020]) — which predicts facts over *named*
  entities, unlike our structural completion of anonymous records.

### §3 Problem Setting (Worker A, 650 words)

1. **Definition 1 (knowledge base).** Finite set of facts; a fact is a
   predicate over a set of constants; constants carry a type. Facts are sets
   (argument roles not carried; one sentence of scope).
2. **Definition 2 (encoding and isomorphism).** Constants → labelled vertices,
   facts of arity ≥ 2 → labelled hyperedges, `k` = maximum arity;
   `K ≅ K'` iff a type- and predicate-preserving bijection maps facts to
   facts. Domain: connected KBs (state why: the machine builds connected
   objects; Prop. C.4 later shows the language never leaves the domain).
3. **Collection operations** — a short list with the engineer's question for
   each (census/deduplication, representative, golden record, generation,
   completion). Table-free.
4. **Definition 3 (prerequisites P1–P5)** stated formally: P1 `d(K,K')=0 ⇔ K≅K'`;
   P2 metric axioms on isomorphism classes; P3 polynomial per pair after a
   per-KB preprocessing; P4 a set of strings closed under edits with a total
   decoder into KBs; P5 locality under single fact edits (stated as a measured
   distribution, not a theorem). One sentence: §5 proves P1–P4 for `w°`, §8
   measures P5.

### §4 The Instruction Language (Worker A, 1,250 words + Fig. 2 + Tab. I + Alg. 1–2)

1. **4.1 Machine and alphabet.** State `S = (H, L, p_1..p_k)`; initial state;
   Tab. I gives the five token families with semantics and index constraints
   (`V_{i,j}`: new fact over `i` pointed constants and `j` new ones inserted
   after `p_1`; `C_i`: new fact over `i` pointed constants, no-op if present;
   `P_i/N_i`: move pointer `i`; `W`: no-op), labelled forms `V[ℓ;i;j;λ…]`,
   `C[ℓ;i]`. Cite arXiv:2607.10194 for the machine.
2. **4.2 Decoding (S2H).** Alg. 1; deterministic and total; `O(|w| · k)` time.
   Note pointers are list positions, not constant names (prepares
   name-freedom).
3. **4.3 The ordered walk `w°`.** Canonical labelling `π_K` of the coloured Levi
   (incidence) graph by individualisation–refinement (nauty); the emission
   rules (root by degree and type; facts by anchor, predicate and local
   signature with canonical rank as last key; closing facts swept by
   position; pointer moves never cross the root). Alg. 2. Cost: one
   labelling call + `O(|w|)` emission, `|w| ≤ m(1+kn)` (Prop. 1).
   Src: Theorem C file §3 (`def:ow`), `experiments/ISAL_VARIANT_DESIGN.md`.
4. **Fig. 2 walk-through** — two to three sentences reading the figure: the
   record, the emitted word, the decoder rebuilding it token by token.
5. **4.4 nauty's two roles and the search form.** The family's search form
   `w*_c` (tie-complete lexicographic minimum, complete by Theorem A
   [preprint]); nauty can enter it as an automorphism oracle that prunes ties
   without changing its value (Prop. C.7, supplement), or as the order the
   ordered walk follows. One sentence: the language's properties (§5) belong to
   the alphabet and the machine, not to how the canonical program is chosen;
   §8.3 measures what removing the search buys. The four-cell cost table goes
   to the supplement.

### §5 Properties of the Word Space (Worker A, 1,300 words)

Theorem environments numbered per IsalSR (`[section]`). Proofs in the main
text where marked; otherwise "proof in Supplementary Section S1".

1. **Theorem 1 (completeness of the ordered walk; = Theorem C).**
   `w°(K) = w°(K') ⇔ K ≅ K'` for labelled connected KBs. **Proof in main
   text** (≈ 12 lines): (⇐) canonical relabelling is a complete invariant
   (Lemma C.1) and the emitter is a deterministic function of the canonically
   relabelled KB; (⇒) round trip `S2H(w°(K)) ≅ K` (Lemma C.3). Lemmas stated,
   their proofs in the supplement.
2. **Corollary 1 (metric).** `d_I` is a metric on isomorphism classes; P1–P3.
   Two-line proof (identity of indiscernibles from Theorem 1; symmetry and
   triangle from Levenshtein). Remark: raw Levenshtein only; the normalised
   variant is not a metric [Marzal & Vidal 1993].
3. **Proposition 1 (length).** `|w°(K)| ≤ m(1+kn)`; one-line argument. No
   measured compactness number (unreconciled; §14 item 4).
4. **Proposition 2 (closed and connected language; = C.4).** Every word
   decodes to a connected KB with no isolated constant; hence prefixes,
   alignment interiors and samples are KBs. **Proof in main text** (short
   induction on tokens: `C` adds a fact over existing constants, `V` adds new
   constants inside a fact that touches an existing one, moves and `W` change
   no fact). This is P4.
5. **Proposition 3 (prefix property; = C.8).** For every `u`, `w°(K)·u`
   decodes to a connected KB containing `K`. **Proof in main text** (no token
   removes a fact or a constant).
6. **Proposition 4 (name-freedom; = C.6).** Statement only; proof in the
   supplement. One paragraph of consequence: a rank-addressed serialization
   (certificate rows, any word writing constant ranks) rewrites every row
   naming a re-ranked constant; the word does not, which is why edits that
   change the constant inventory are absorbed locally (tested in §8.2). Star
   locality (C.5) mentioned in one sentence with pointer to the supplement.
7. **What is not claimed** (one short paragraph): `d_I` is not an
   edit-distance proxy (envelope `d_I ≤ m(1+kn)·HGED` only, supplement); no
   Lipschitz stability theorem.

### §6 Collection Operations (Worker A, 700 words + Alg. 3)

1. **Census and deduplication.** Word equality = isomorphism (Theorem 1); hash
   the words; `N` canonicalizations, exact.
2. **The distance matrix.** `N` canonicalizations + `N²/2` Levenshtein
   evaluations at `O(L²)` each.
3. **Certified representative.** Proposition 5: medoid cost
   `≤ (2 − 2/N)·OPT` [Jiang et al. 2001]; `LB = Σ_{i<j} d(K_i,K_j)/(N−1) ≤ OPT`;
   certified ratio `cost/LB` for any candidate. Two-line proof.
4. **Golden record by word-space consensus.** Candidates = decoded words in
   `⋃_i B_r(w°(K_i))` (Prop. 2 makes every candidate a KB), grouped by
   isomorphism class; objective = generalized median under `d_indel`; ties by
   coverage then fingerprint order. Why indel: a substitution has no unit-cost
   fact counterpart; under Levenshtein a source and its sub-records tie on
   deletion noise, under indel the source strictly wins for `N ≥ 3`
   (state as Proposition 6 with a short argument, src `rq3v2_facts.md` §5).
   Alg. 3; complexity exponential in `r`; `r = 2`. The consensus can return a
   KB no member wrote; its certified ratio is computed against `LB`.
5. **Generation.** Any token model over words of a collection (an order-n
   n-gram here); samples decode with validity 1 by Prop. 2; no rejection step.
6. **Completion.** Condition the token model on the prefix `w°(K⁻)`; each
   continuation decodes to a connected KB containing `K⁻` (Prop. 3); keep
   draws in sampling order that add ≥ 1 fact, deduplicate by isomorphism
   class, stop at 10 proposals or the resample budget (as implemented in
   `experiments/tkde/rq8.py`; there is no probability ranking).

### §7 Experimental Setup (Worker B, 700 words + Tab. II)

1. **Corpora.** WD50K(66): 3,988 entity KBs within the envelope, 3,162 with a
   fact of arity ≥ 3, 826 binary; Wikidata qualifiers make facts n-ary. NDC-
   classes: 1,381 quarterly co-formulation KBs of pharmacologic classes (519
   dropped at the arity cap, 51 below three facts). Controls: WD50K(100),
   NDC-substances (1,745). **Counts from the brief §(e), never from
   `supplementary_data.md`.** Tab. II: members, `n`, `m`, max arity, star
   fraction.
2. **Structure census.** 53.4 % of WD50K(66) KBs are stars, 3.0 % of
   NDC-classes. Stars are determined by their multiset of fact patterns, so
   counting baselines are expected to tie there; every experiment that
   compares task metrics is stratified star / relational. Src
   `rq8_facts.md` §3.
3. **Envelope sweep.** 7,776 random labelled KBs over `(m, k, |Σ|)` with
   symmetry buckets; the only synthetic data. Src `rq7_envelope_facts.md`.
4. **Competitors**, grouped by family with what each lacks (one sentence
   each; the capability table, Tab. III, is the summary): exact HGED (small
   instances); bipartite GED (assignment, edit path); WL histogram; NetLSD;
   HPD; HyperCOT where per-pair cost permits; nauty certificate + Levenshtein
   (byte and row serializations); size and degree-sequence floors; task
   baselines per experiment (named in §8).
5. **Protocol.** 27 seeds; 95 % BCa bootstrap intervals; Holm-corrected paired
   Wilcoxon over seeds against every competitor, rank-biserial effect size;
   RQ1 uses a cluster bootstrap over members (2,000 resamples). 60 s
   canonicalization budget. Pre-registration sentence (rule 4.1).
6. **Implementation and hardware.** C++ engine bit-identical to the Python
   reference on every differential; nauty via pynauty; HPC CPU nodes for
   campaigns; the per-member timings' hardware from `rq7_envelope_facts.md`
   provenance. Code URL.

### §8 Results (Worker B, 1,900 words + Tabs. III–VII + Figs. 3–4)

Each subsection: *Hypothesis* (one sentence, italic run-in) → design (≤ 2
sentences, rest in §7) → evidence with numbers and intervals → scope sentence.

**8.1 H1 — Exactness on real collections.** *Theorem 1 implies `d_I` never
puts two non-isomorphic KBs at distance zero; representations that are not
complete invariants should merge non-isomorphic KBs on real data.* Print: `w°`
0 false merges and the exact partition on three collections (530 / 1,086 /
3,677 classes) — **PENDING-P1 for the `w°` census; if it has not landed,
state the zero as Theorem 1's consequence and print only the competitor
counts, which do not depend on our program**; NetLSD merges 2,516 / 1 /
185,917 non-isomorphic pairs, HPD 7,618 / 9,885 / 212,179; bipartite GED
edit-path cost splits 557 true classes into 574 (not a metric: 38 %
asymmetric pairs, 1.4 % triangle violations). Scope sentence: the nauty
certificate is equally exact, and WL showed no merge on these collections
although it is provably incomplete; exactness is a property of the family.
Tab. III (capability table) is introduced here. Src `rq2_wellposedness_facts.md`
§1, `rq2_ow_facts.md` §4.

> **2026-10-13 — superseded on the draft branch `newpos-c8` (`e9feddb`, not pushed).**
> H2 is now the task-level comparison C8, "Records One Pendant Edit Apart Are
> Nearest Neighbours", with Fig. 3 `fig_neardup_retrieval.pdf`.
>
> - **What it shows.** On pendant one-edit pairs, `w°` has MRR 0.449 / 0.726 /
>   0.552 / 0.691 (NDC-cl / NDC-sub / WD66 / WD100). The best of ten competitors
>   reaches 0.263 / 0.349 / 0.065 / 0.175, with Holm p < 1e-32. At radius 2, `w°`
>   is first on all four collections.
> - **Mandatory scope clause.** Interior pairs are lost to 4–8 of the 10
>   competitors. Pooled over all edits, the bipartite edit path ties `w°` on both
>   NDC series. The pre-registered pooled AP criterion failed on NDC-substances.
> - **Where the old material goes.** Tab. IV (`tab_locality`, below) moves to S3,
>   and its numbers stay in one sentence.
> - **Source of every number.** `experiments/NEWPOS_2026-10-13/C8_NEAR_DUPLICATE_RETRIEVAL.md`
>   §4, and the JSONs and `tab_neardup.tex` in
>   `D/results/NEWPOS_2026-10-13/neardup/`.
>
> The text below records the 2026-10-04 plan.

**8.2 H2 — Pendant edits are absorbed locally.** *Proposition 4 implies an
edit that changes the constant inventory leaves the rest of the word in place,
whereas a rank-addressed certificate rewrites every row after the change.*
Tab. IV, per corpus, fraction of single edits within two symbols [95 % CI] and
median response, `w°` vs certificate rows:

| pendant edit | WD50K(66) `w°` | cert. rows | NDC-classes `w°` | cert. rows |
|---|---|---|---|---|
| delete a fact | 0.794 [0.783, 0.804], med 1 | 0.000, med 11 | 0.594 [0.529, 0.648], med 1 | 0.000, med 13 |
| remove a constant from its last fact | 0.831 [0.819, 0.844], med 1 | 0.000, med 11 | 0.877 [0.831, 0.910], med 1 | 0.000, med 11 |
| insert a fact with a new constant | 0.152 [0.145, 0.158], med 7 | 0.000, med 11 | 0.042 [0.034, 0.053], med 12 | 0.000, med 13 |

Src `…/results/IEEETKDE/RQ1_isal/merged/rq1_statistics_{wd50k66,ndc_classes}.md`
(M1, regime 0). The certificate never lands within two rows on any pendant
edit. Scope clause (rule 4.3): on interior argument edits the certificate is
more local (e.g., adding a constant to an existing fact: 0.252 vs 0.109 on
WD50K(66), 0.399 vs 0.021 on NDC-classes); Supplementary Table S3 gives every
interior cell and the search form `w*_c`. Practical reading: versions of a
record that gain or lose a constant (a new cast member, a product leaving a
class) stay within a few instructions.

**8.3 H3 — A canonical program without search has no symmetry frontier.**
*The ordered walk performs one labelling call and a linear emission, so its
cost should not depend on symmetry, unlike the search form.* Print: 0 of 7,776
sweep KBs censored at 60 s, including all 427 with `|Aut| ≥ 10⁷`, where the
unpruned search censors every one and orbit-pruned `w*_c` 91.8 %; on the real
collections 8,951 of 8,951 members canonicalised at 0.60–0.70 ms median; the
full 3,988 × 3,988 matrix on WD50K(66) in 1.39 s against 28.9 min for `w*_c`
(1,252×; one alphabet, one tokenization, one code path; cite the frozen
reading); for the search form, censoring tracks the fact count `m`, not `n`.
Cross-representation matrix times (NetLSD 40.6 s, bipartite GED 10.6 min) may
be given in one sentence; the certificate is **at parity** with `w°` at
matched tokenization (1.09–1.19×) and that sentence is mandatory if any
cross-representation time is printed. Fig. 4. Src `rq7_envelope_facts.md` §1,
§3, §5, §8; `results/frozen/rq7_envelope_2271960_reading/`.

**8.4 H4 — Every sample is a usable KB.** *Proposition 2 implies any
distribution over words is a distribution over connected KBs.* Tab. V (joint
rate = valid ∧ connected per drawn sample, 27 seeds × 10,000 per collection):

| generator | NDC-classes | WD50K(66) |
|---|---|---|
| n-gram over `w°` words (ours) | 1.000 (270,000 / 270,000) | 1.000 (270,000 / 270,000) |
| n-gram over canonical-rank fact list | 0.416 | 0.126 |
| n-gram over incidence list | 0.0017 (1 in 578; 98.10 % rejected) | 0.000085 (1 in 11,739; 98.98 % rejected) |

Novelty clause (rule 4.3): the fact-list generator produces more samples
non-isomorphic to every member (0.988 / 0.943 vs 0.917 / 0.914), but on
WD50K(66) only 7.3 % of its novel samples are connected, against 100 % of
ours by Proposition 2; a disconnected sample is outside the domain and cannot
be encoded, compared or added. Fig. 3 (decodability corridor) closes the
subsection: every interior word of an alignment between two members decodes
to a connected KB; in the consensus experiments 426,433 of 426,433 ball words
decoded to connected KBs. Src `rq6_generation_facts.md` §Sample validity,
§joint rate, §Quoted forms; `rq3v2_facts.md` §3.4.

**8.5 H5 — The golden record can be a record no member wrote.**
**PENDING-P1.** *Proposition 2 makes every word near the members a candidate
KB, so a consensus over word balls can recover the source of N noisy anonymous
descriptions, which any medoid (it returns a member) cannot.* Design:
real sources, N ∈ {5, 9(, 15)} anonymised variants with `t` random fact
edits (mixed pendant/interior, insertion/deletion), constants relabelled;
metric exact recovery (certificate equality) and fact distance to source.
Two variants, chosen when the fact base carries verdicts:
- **Variant A (H3.1 holds on the relational stratum of ≥ 1 corpus):** full
  subsection; Tab. VI: exact recovery per corpus × stratum × N for the
  consensus, the reference-aligned and iterative merges, pattern vote, every
  medoid (0 by construction, printed), the identity-using majority merge as an
  oracle reference; certified ratio vs the indel medoid. Scope: `t = 1`, the N
  measured, `r = 2`; star stratum as the control where pattern vote is
  expected to tie.
- **Variant B (H3.1 not supported):** 0.35 page; the capability
  demonstration only: the consensus is a decoded non-member, its fact distance
  to the source is below every medoid's (H3.2), and it carries a certified
  ratio; merges comparison to the supplement.
Already citable regardless: the source lies in the union of radius-2 balls in
every mixed `t = 1` cell (1.000, both corpora, both strata). Src
`rq3v2_facts.md`.

**8.6 H6 — Completions are KBs, and on relational records they attach
correctly.** *Proposition 3 makes every continuation of `w°(K⁻)` a connected
KB containing `K⁻`; a model over words also sees where facts attach.* Design:
hide one interior fact of a relational record; propose ten completions;
hit@10 = some proposal isomorphic to the hidden record. Fact-count-matched
protocol, fixed before re-measurement, because counting recommenders add
exactly one fact by construction. Print: proposals valid and connected 1.000
by Proposition 3 (fact-list 0.692 connected; incidence list 0.191 valid); on
WD50K(66) relational records hit@10 0.048 [0.042, 0.056] vs 0.019
[0.014, 0.024] for the co-occurrence recommender, Holm-corrected paired
Wilcoxon over 27 seeds p = 1.3 × 10⁻⁵, rank-biserial 1.000; attachment miss on
one-fact proposals 0.26–0.37 vs 0.64 / 0.59 (NDC-classes) and 0.85 vs
0.97 / 0.98 (WD50K(66)). Tab. VII. Scope clause (rule 4.3): absolute rates
are low for every method; on NDC-classes and on star-shaped records the
co-occurrence recommender leads (0.32 vs 0.19; 0.62 vs 0.18) because those
units reduce to predicting the fact pattern, where frequency counting is
strong; Supplementary Section S5. Src `rq8_facts.md` §4.2, §4.3, §6, §7.

### §9 Discussion and Limitations (Worker B, 520 words)

1. **Where the language matters.** Across H4–H6 the advantage concentrates
   where constants are shared across facts: on stars, the isomorphism class is
   the multiset of fact patterns and counting suffices; on relational records,
   attachment and validity decide, and the language supplies both. Frame as a
   characterization that tells a practitioner when to use which tool.
2. **The certificate's place.** nauty + Levenshtein shares P1–P3 and is at
   parity in cost; IsalHG uses nauty as its order and adds the language. A
   pipeline that only deduplicates should use the certificate.
3. **Limitations.** Envelope (`n ≤ 24`, `m ≤ 110`, `k ≤ 10`, labelled,
   connected); facts as sets (roles are future work); ball operations at
   `r ≤ 2`, exponential in `r`; locality holds for pendant edits only;
   completion rates are low in absolute terms; the clustering of entity types
   from structure alone is weak for every representation, ours included
   (supplement).
4. **Future work.** Sequence models beyond n-grams; argument roles via the
   coloured incidence graph; models of first-order structures (one sentence,
   no detail).

### §10 Conclusion (orchestrator, 230 words)

Restate thesis in two sentences, the three strongest numbers, the concession,
and the one-sentence outlook. No new claims.

### Back matter (orchestrator)

Acknowledgments (funding: **ask the author**); AI-use disclosure (IsalSR
pattern); data and code availability; IEEE biographies (photos present).

---

## 8. Figures, tables, algorithms

| id | content | width | owner | how |
|---|---|---|---|---|
| Fig. 1 | Overview: a collection of anonymous KBs → canonical labelling (nauty) → ordered-walk emission → word space with two uses: metric (census, matrix, medoid) and language (decode: golden record, generation, completion) | column (full if room) | Worker A | TikZ, in `figures/src/fig_overview.tex` |
| Fig. 2 | Worked example: (a) one small **relational** KB with one arity-3 fact (a qualifier) and a shared constant, `n ≤ 7`, `m ≤ 5`, drawn as a labelled hypergraph; (b) S2H execution: 5–7 columns, each the list `L` with pointers, the token, the partial KB; (c) the full `w°` word, tokens coloured by the fact they create; optional (d) the certificate rows of the same KB | full | Worker A | prefer a real WD50K(66) non-star member (anonymised types/predicates in display); render with `isalhg.viz` (`composite.steps_figure`, `cdll_view`, `instruction_view`) on `core/algorithms/ordered_walk.py`; script in `figures/src/fig_worked_example.py`; TikZ fallback. The existing worked example (`experiments/ENCODINGS_WORKED_EXAMPLE.md`) is a star and does not show sharing — do not use it as is |
| Fig. 3 | Decodability corridor: the optimal Levenshtein alignment between the `w°` words of two real relational members; 4–6 intermediate words, each decoded and drawn | column | Worker B | script `figures/src/fig_corridor.py` using the repo's decoder and `rapidfuzz`/own alignment; a visualization, not an experiment |
| Fig. 4 | Envelope: censoring fraction vs fact count `m` (or vs `|Aut|` bucket) for unpruned search, orbit-pruned `w*_c`, `w°`; real collections placed | column | Worker B | `figures/src/fig_envelope.py` from `results/frozen/rq7_envelope_2271960_reading/`; matplotlib, vector PDF, colour-blind-safe palette, same palette across figures |
| Tab. I | Alphabet and semantics | column | Worker A | |
| Tab. II | Corpora | column | Worker B | |
| Tab. III | Capability table | full | Worker B | adapt `tables/tab_kb_representation_properties.tex`: replace *Matrix (s)* by *Pair cost* (complexity, no timings: the row-certificate timing is invalid, T-KBy); keep *Pendant* locality, drop *Int.* (its content goes to the H2 scope clause and the supplement); fill *Cons.* after P1; `w°` last and bold |
| Tab. IV | Pendant locality per corpus | column | Worker B | §7 §8.2 |
| Tab. V | Generation joint rate | column | Worker B | §8.4 |
| Tab. VI | Golden record | column | Worker B | PENDING-P1 |
| Tab. VII | Completion | column | Worker B | §8.6 |
| Alg. 1 | S2H decoder | column | Worker A | `algorithm` + `algpseudocode` |
| Alg. 2 | Ordered-walk emitter | column | Worker A | |
| Alg. 3 | Word-space golden record | column | Worker A | first overflow lever |

Figure rules: vector PDF; fonts ≥ 7 pt at print size; one palette shared by
all figures (ours always the same colour); no titles inside plots (captions
carry them); captions state what to see and the scope, ≤ 60 words.

---

## 9. Supplement (written later; the main text points to it)

S1 full proofs (Lemmas C.1–C.3, Prop. C.5 star locality, C.6 name-freedom, C.7
orbit pruning, Prop. 6 indel argument, bipartite counterexample) — **drafted
now by Worker A** in `submission/supplementary/proofs.tex` because main-text
statements cite it. Written later by the authors: S2 corpus derivation and
counts; S3 RQ1 full locality tables (interior, `w*_c`, rank-keyed walk, ladder
monotonicity); S4 nauty-role cost ablation (four cells); S5 RQ8 on NDC-classes
and stars with Amendments A1–A3; S6 RQ3 v2 ablations and incomplete cells; S7
clustering vs entity types (negative, all representations); S8 natural NDC
series (RQ3 v1, underpowered tie); S9 tail characterisation of `w*_c`; S10 the
data-quality screen (not completed: state so, no table).

**Added 2026-10-13 (NEWPOS session; the draft branch `newpos-c8` already cites
these sections).** All paths below are under `experiments/NEWPOS_2026-10-13/`.

- **S3** also carries the full C8 table, `tab_neardup.tex`. It gives P / I / 2
  columns per collection, for all ten competitors and `w°`. It also carries the
  pooled radius-1 table and the `w*_c` ablation (`C8_…md` §4.3, §5).
- **S11** is the GRU language model. It is trained identically on `w°`, the fact
  list and the certificate rows, over 27 seeds. It covers validity, yield and
  VUN, and the out-of-domain rate of the baselines. It also covers the LCC
  repair and the uncapped sensitivity run (`HANDOFF_2026-10-13.md` §2, GRU row).
- **S12** is compactness under learned and generic coders. It covers the
  3-of-4 result against the fact list and the version deltas
  (`HANDOFF_…` §2, rows C5, C5-len and C5-delta).
- **Unassigned so far**, but they must appear (they are negative or mixed):
  - C2: metric search;
  - C3/C3b: version linkage;
  - C7: change tracking;
  - C4/HA1–HA2: rejection bias;
  - C4-post: the size window.

  Their tables and verdicts are in `HANDOFF_…` §2 and `LOG.md`.

---

## 10. Bibliography

- `submission/article/references.bib`, IEEEtran style. Seeded by the
  orchestrator from `literature_verified.md`, `docs/article/RELATED_WORK.md`,
  the preprint's and IsalSR's `.bib` files (only entries actually cited).
- **Rule:** an entry enters only with a resolving DOI, arXiv id, or an
  `existence verified` note from `literature_verified.md`. Each new entry
  carries `% verified: <how>, 2026-10-xx` above it. Entries marked
  **verify** in §7 are checked by web search before use; unverifiable → not
  cited.
- Must-cite set: arXiv:2607.10194; IsalGraph arXiv:2603.11039; IsalSR (TPAMI
  submission / arXiv); Galkin 2020 (WD50K); NDC directory (FDA, dataset
  citation); McKay & Piperno 2014; Junttila & Kaski 2007; Qin et al. ICDE
  2023; Riesen & Bunke 2009; Serratosa 2019; Blumenthal et al. 2020 (×2); Cai
  et al. 1992; NetLSD; HPD; Chowdhury et al. 2024; Yan & Han 2002; Jiang et al.
  2001; de la Higuera & Casacuberta 2000; Marzal & Vidal 1993; SELFIES; Konieczny
  & Pino Pérez 2002; Rosso et al. 2020; Bleiholder & Naumann; Chávez et al.
  2001; Levenshtein 1966.

---

## 11. LaTeX infrastructure (orchestrator builds before the workers start)

```
submission/article/
  main.tex            compsoc journal; \ifanonymous switch; \input of sections
  macros.tex          every symbol of §5.1; \pending{} (red box), \todo{}
  references.bib
  sections/{abstract,introduction,related_work,problem,language,properties,
            operations,setup,results,discussion,conclusion,backmatter}.tex
  tables/tab_*.tex
  figures/*.pdf
  figures/src/        generation scripts (python: ~/.conda/envs/isalhg/bin/python, read-only use of the IsalHG checkout)
  ../supplementary/proofs.tex
```

Packages: `amsmath, amssymb, amsthm, booktabs, multirow, graphicx, xcolor,
tikz, algorithm, algpseudocode, cleveref, siunitx, hyperref` (compsoc-safe
order). Theorem styles as IsalSR. Build: `latexmk -pdf main.tex`; zero
undefined references and citations; `pdfinfo` page count reported at every
merge. The template sample files stay untouched; `main.tex` becomes the
Overleaf main document (author sets it).

---

## 12. Style rules for every writer (from the `humanizer` skill, scientific mode)

**Voice.** Academic "we", active voice, direct verbs (*reduces, proves,
returns, decodes*). Concrete subjects ("the ordered walk emits…", not "it
can be observed that…"). Sentence length varies: short declaratives between
long ones; no paragraph of uniform 25-word sentences.

**Banned words and moves** (grep at review): *leverage, utilize, facilitate,
novel, groundbreaking, pivotal, crucial, paramount, delve, showcase,
underscore, seamless, robust* (unless a statistical term), *landscape, realm,
tapestry, notably, furthermore/moreover* as paragraph openers, *it is worth
noting, plays a key role, in this paper we* (more than once), *comprehensive,
state-of-the-art* (without a citation), *a testament to*. No "not only… but
also". No "X — not Y" slogans; the antithesis construction ("is not A but B")
at most once per page. Em dashes: at most one pair per paragraph; prefer
commas, parentheses, colons or a new sentence. No bold or italics for
emphasis in running text (italics only for defined terms at first use and the
run-in *Hypothesis* label). No triads by reflex (lists of three adjectives or
three clauses). No closing "summary" sentence that repeats the paragraph. No
rhetorical questions.

**Precision.** Quantify every comparative ("faster" → "1,252× faster than
`w*_c` on the same matrix"). Intervals in brackets, `p` with Holm stated,
effect size beside every test. One term per concept (§5.2); no synonym
cycling (*record / description / entry* — pick "KB" and "record" only where
the engineer's word is meant, defined once).

**Paragraph shape.** Topic sentence that states the claim; evidence; scope.
Paragraphs of 3–7 sentences. Section openings go straight to content (no
"In this section, we…").

---

## 13. Work split and orchestration

**Wave 0 — orchestrator, before spawning.** Build §11's skeleton in the
Overleaf clone, seed the `.bib`, write `macros.tex`, compile an empty shell,
commit `chore: article skeleton` locally; this commit is the pinned base for
both workers.

**Wave 1 — two Opus 5.5 workers in parallel (`parallel-agents` skill), each in
its own worktree and branch cut from the base, each writing its work log.**

| worker | files it owns (and only these) | deliverable |
|---|---|---|
| A — method | `sections/{problem,language,properties,operations}.tex`, `tables/tab_alphabet.tex`, `figures/{fig_overview,fig_worked_example}.*`, `figures/src/fig_{overview,worked_example}.*`, `../supplementary/proofs.tex`, `refs_A.bib` | §3–§6 per §7, Figs. 1–2, Tab. I, Algs. 1–3, supplementary proofs |
| B — evidence | `sections/{setup,results,discussion}.tex`, `tables/tab_{corpora,capability,locality,generation,golden,completion}.tex`, `figures/{fig_corridor,fig_envelope}.*`, `figures/src/fig_{corridor,envelope}.py`, `refs_B.bib` | §7–§9 per §7, Figs. 3–4, Tabs. II–VII; PENDING-P1 placeholders as `\pending{}` |
| orchestrator (concurrently) | `sections/{abstract,introduction,related_work,conclusion,backmatter}.tex`, `main.tex`, `macros.tex`, `references.bib` | §1, §2, §10, back matter; abstract last |

Workers add bibliography entries to their own `refs_X.bib` (merged by the
orchestrator) to avoid conflicts; they never edit `macros.tex` — they request
a macro in their log and use a local `\providecommand` meanwhile.

**Worker acceptance criteria.** (1) `latexmk -pdf` builds with their sections
included, no errors, no undefined references in their files; (2) word budgets
within ±10 %; (3) every measured number has its `% src:` comment and matches
the fact base; (4) every claim carries its scope (rules 4.2–4.3); (5) the
banned-word grep of §12 returns nothing; (6) no sentence reused from the
preprint or siblings; (7) figures regenerate from their scripts; (8) work log
complete.

**Wave 2 — review and revision (orchestrator).** For each branch: diff read in
full; spot-check ≥ 30 % of numbers against fact bases (all headline numbers);
style pass against §12 using the `humanizer` skill's scientific checklist;
revision requests sent to the worker (SendMessage) with line-level items; merge
when the criteria hold; compile; page count.

**Wave 3 — fill and finish (orchestrator).** P1 numbers into §8.1 / §8.5 /
Tab. III; abstract and contribution numbers final; global humanizer pass;
consistency grep (every number in abstract/intro/conclusion appears in §8 with
the same value); page count ≤ 14; `SESSION_LOG`-style handoff note in the
article repo.

---

## 14. Open items that need the author or the PI

1. **D-ART6 ratification** — the paper is written on `w°`; the PI's word is
   not recorded (`DECISIONS.md`).
2. **Title and author list / order / corresponding author** (defaults in §2).
3. **Funding acknowledgment text.**
4. **Compactness numbers are unreconciled** (6/8 instruction medians vs a
   T-KBx mean of 13.8 walk tokens against 40 certificate integers): the paper
   states the proved bound only, until reconciled. **Resolved 2026-10-13.**
   Both statements were right: the median `w°` is 6 instructions (WD) or 9
   (NDC, including the root type) against 12 rows, and the mean is 13.5 against
   40.0 four-byte words. Source: `experiments/NEWPOS_2026-10-13/HANDOFF_2026-10-13.md`
   §2, row C5-len.
5. **T-KBy** (row-certificate timing through a Python loop) is unfixed: no
   certificate-row timing appears in the main text.
6. **RQ3 v2 is partial** (heavy N = 15 cells timed out): §8.5 is written in
   Variant A or B when the fact base carries verdicts; N = 15 is not claimed.
7. **RQ2 on `w°`**: harvest pending; fallback per §8.1.
8. **TKDE review model** (single- vs double-blind) and the live page limit:
   verify on the author page before submission.
9. **Pushing to Overleaf** requires the author's explicit instruction.
10. The integration branch `integration/2026-09-13-headline-w0` is not merged
    into `feature/isal-kb-word`; the paper's sources cite files that exist only
    there.
11. **NEWPOS (2026-10-13).** Two branches await the author:
    - the Overleaf branch `newpos-c8` (`e9feddb`), which holds C8 as H2, the GRU
      sentence and the compactness sentence, and is not pushed;
    - the code branch `integration/2026-10-13-newpos-w1`, which holds scripts,
      tests and docs only (`src/` is untouched) and is not merged.

    Remaining ledger work is T-KBae: mirror five locally built matrices.

---

## 15. Change log

- 2026-10-04 — v1 created by `[Opus-Article-Orchestrator]` from the
  brief of `[IsalHG-Fable-Review]` and the fact bases; RQ1 per-corpus pendant
  numbers transcribed from `rq1_statistics_{wd50k66,ndc_classes}.md`; RQ6 and
  RQ8 numbers cross-checked against their fact bases.
- 2026-10-04 — §3.1 C4 corrected: the 59–88 % within-two figure holds for
  pendant *deletions* only (delete a fact 0.794 / 0.594; remove a constant
  0.831 / 0.877); pendant insertions with a new constant are 0.152 / 0.042
  (certificate 0.000 on all). Found by the orchestrator's claim ledger while
  humanizing the introduction; introduction and conclusion fixed; both workers
  warned.
- 2026-10-04 — Worker A decisions accepted: Def. 1 admits arity 1..k (unary
  facts arise only in decoded words; lemmas re-proved in S1); `w°(K)` carries
  the root type as its first symbol (`d_I = [types differ] + d_Lev(tokens)`,
  checked); completion described as implemented (§7 §6 item 6 corrected); the
  bipartite counterexample depends on the assignment solver's tie rule (exact
  GED(A,C) = 5), so the main text cites Serratosa 2019 plus measured rates.
- 2026-10-04 — **P1 landed; scope change.** (a) H1 uses the `w°` census
  (`rq2_ow_facts.md` §4): 557 / 1,156 / 3,682 classes on 1,381 / 1,745 / 3,988
  members, 0 false merges, 0 censored (`w*_c` loses 70 / 84 / 5); bipartite
  edit path splits 557→574, 1,156→1,290, 3,682→3,839; assignment value merges
  59 / 1,332 / 201,010. (b) **The golden record (old H5) moves to the
  supplement (S6)**: H3.1/H3.2 hold, but the pre-registered ablation fails (a
  fact-space consensus recovers 0.984 vs the word-space 0.433), so the
  operation needs a complete invariant, not the language. §6 drops the
  consensus, `prop:indel` and Alg. 3 (Alg. 3 = completion, `alg:completion`);
  Tab. VI and the capability table's Consensus column are dropped; results are
  H1–H5 with H5 = completion. (c) Fable's framing check
  (`FRAMING_CHECK_2026-10-04.md`) applied: all three completion-protocol
  amendments named; H3 "inherits the labelling engine's cost"; metric-violation
  rates are from random pairs; completion's primary matched model is 0.046
  (p = 1.33e-5, r = 0.989) with the free-running non-support stated in one
  clause; pendant insertion is "more local than the certificate, not local".
  Change orders sent to both workers.
- 2026-10-04 — **Draft merged and reviewed.** Integration branch
  `integration/2026-10-04-tkde-draft` in the Overleaf clone, 14 pages. Fable's
  final review (`FINAL_REVIEW_2026-10-04.md`: 307 numbers checked, one rounding
  slip; six scope items) applied in full. Two framing changes to this plan
  follow from it: (1) **H2 is reported as an observation**, not a
  pre-specified hypothesis (the pendant/interior axis emerged from the
  measurements; rule 1's protocol sentence now covers exactness, generation and
  completion only); (2) the completion claim is the relational stratum of
  WD50K only — NDC-classes is relational and the recommender wins there, so
  "matters most when facts share constants" is withdrawn. The public arXiv
  abstract of the preprint states the search form's completeness as a
  *conjecture*; the paper no longer cites it as proved. The completion table
  shows the claimed stratum and the attachment mechanism; NDC hit@10 and stars
  stay in the text's scope clause and go to S5.
- 2026-10-13 — **NEWPOS session: C8 replaces H2's evidence (draft branch
  `newpos-c8`, `e9feddb`, not pushed).** This answers the PI's 2026-10-05
  request for comparative experiments that favour the method. The session is
  recorded in `experiments/NEWPOS_2026-10-13/{C8_NEAR_DUPLICATE_RETRIEVAL,HANDOFF_2026-10-13,LOG}.md`.

  **What the draft gains.**
  - C8, near-neighbour retrieval of structural near-duplicates, against all ten
    competitors on all four collections. It is placed under Option B: Fig. 3
    replaces `tab_locality`, and `tab_locality` moves to S3.
  - The capability table's locality column now gives pendant MRR for every
    representation.
  - One GRU sentence in H4 (S11) and one compactness sentence in the discussion
    (S12).
  - `wd50k100` and `ndc_substances` are promoted to evaluation collections.

  **Framing constraints the writer must keep.**
  - The pre-registered hypothesis was *pooled* (highest MRR and AP on every
    collection). It failed on NDC-substances AP. The stratified headline was
    adopted after that failure, at Fable's instruction. Pendant/interior
    stratification had been pre-registered as a reporting dimension, not as the
    test.
  - The radius-2 stratum was run on Fable's prediction, without a kill
    criterion written in advance (`LOG.md` records the omission).
  - This keeps H2 an observation, per the 2026-10-04 rule. C8 is the
    observation's out-of-sample task test: the edits are naturally occurring
    pairs in the collections, not edits applied by us. The scope clause
    (interior lost to 4–8 of 10; pooled tie with the edit path on NDC) is
    mandatory.

  **Checks.** The writing orchestrator re-checked every C8 number against the
  JSONs and corrected two overstatements in the hand-off. Fable reviewed the
  design and the pooled results, but not the final stratified and radius-2
  numbers.
- 2026-10-14 — **Final writing pass (wave `2026-10-14-tkde-polish`; Overleaf clone branch `integration/2026-10-14-tkde-polish`, `97d1e76`, not yet merged or pushed).** The author's instructions change three rules of this plan.
  - **§4 rule 3 is superseded.** Losses are not given one clause where they occur. Every loss and constraint lives in ONE Limitations subsection of the Conclusions (`sec:limitations`, Section 9.2, about 550 words). A claim's own scope qualifier stays in the claim (rule 2).
  - **The Discussion section is dissolved**, and the Conclusions gain "Impact and Applications": five uses, each tied to a proved property and to cited work.
  - **§9 is superseded.** The supplement (`submission/supplementary/supplement.tex`, same IEEEtran template, 12 pages) holds:
    - S1 Proofs;
    - S2 Near-duplicate retrieval and locality by edit type;
    - S3 Generation under a GRU;
    - S4 Completion strata and amendments.

    Compactness, clustering, the nauty-role cost split, the golden record and the probe-level negatives are deliberately left out.

  Also:
  - The C8 figure is now a compact table in the main text; the figure moved to S2.
  - The bibliography has 29 references; the abstract is 245 words.
  - Bounds are rounded outward: upper bounds up, lower bounds down.
  - An independent claim check found 14 scope or wording issues and no wrong number; all are fixed.

  Record: the Overleaf clone's `.claude/notes/2026-10-14-tkde-polish/summary.md`.
