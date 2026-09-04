# D-ART3 (v5) — proposal folder: the enumeration-and-search rescope

> **2026-09-03 — superseded as the entry point.** The article was re-centred
> on the consensus idea and the four collection-level applications; the
> current entry point is [`START_HERE.md`](START_HERE.md), the storyline is
> [`prose.md`](prose.md), and the verified fact base is [`foundation/`](foundation/).
> This file is kept as the v5.1 record; `START_HERE.md` §5 says which parts
> of it survive.

**Status:** PROPOSAL, pending PI ratification. Written 2026-08-12 after the PI's
feedback on the v4 draft (`../DEVELOPMENT/RESCOPE_D-ART3_DRAFT.md`). **Nothing
in `docs/article/{PROPOSAL,DATA,COMPETITORS,theoretical,empirical}.md` changes
until this is ratified**; the v3 scope (D-ART2) remains the active scope and the
active docs remain the authority on what the paper currently is.

This folder is written *from the ground up* as the replacement scope. Each file
mirrors an active document of the same nature and states what it would become.
Files are deliberately small and disentangled; the reasoning that connects them
lives here.

---

## 1. What the PI changed, in one page

Four inputs, arriving together:

1. **Venue: IEEE TKDE** (ISSN 1041-4347), not *Information Sciences*. →
   [`venue.md`](venue.md)
2. **A new problem to solve.** Every finite model of a first-order formula *is*
   a labelled hypergraph; search exhaustively for the **smallest countermodel**
   of a formula. Rationale from IsalSR: *"nuestros métodos brillan cuando la
   búsqueda es exhaustiva y no aleatoria, ya que de esta manera nuestra ventaja
   de ser invariantes a isomorfismos es más obvia."* →
   [`logic_models/`](logic_models/)
3. **Applications must be ones where IsalHG is indispensable, not ones where it
   competes.** *"no se consigue que IsalHG sea mejor en aplicaciones de
   aprendizaje supervisado ni no supervisado […] hay que buscar aplicaciones en
   las que sea imprescindible o muy ventajoso lo que diferencia IsalHG: un
   espacio con una distancia definida, formado por puntos que son invariantes
   frente a isomorfismos. Lo ideal serían problemas en los que **enumerar los
   vecinos** de un hipergrafo, o **hallar el camino más corto** entre dos
   hipergrafos, sea muy relevante."* → [`applications.md`](applications.md)
4. **Real hypergraph corpora exist — use them.** The Benson/ARB collection
   (`cs.cornell.edu/~arb/data/`), 28 datasets. → [`data.md`](data.md)

Plus one standing instruction on the writing: **synthesize the geometry**
(*"es muy amplia […] Debes intentar sintetizarla un poco, porque se pierde uno
leyendo"*). → [`geometry.md`](geometry.md)

## 2. The resulting thesis, in one sentence

Not *"a hypergraph is a word, and words cluster well"* (v3 — measured false on
task metrics), and not *"a hypergraph is a word, and here is why the word moves
so much"* (v4 — true but a limit paper). Instead:

> **A certificate is not a space. `nauty` tells you whether two hypergraphs are
> the same — faster than we do and just as exactly. `Σ_HG` gives hypergraph
> space a ground set, a move operator, an order, a metric and a decoder in one
> representation, so a *search* can run inside it. The paper is about the space,
> and its applications are the problems that require *moving* in it rather than
> *comparing* points of it.**

**Revision v5.1 (2026-08-12), on the author's correction.** The v5.0 draft made
isomorph-free enumeration (deduplication) its first pillar. That is a losing
frame: Levi-`{nauty, bliss, Traces}` deduplicate faster than `w*_c` with
identical exactness, so any dedup claim is a tie at best. Deduplication is
demoted to a **correctness precondition** — with nauty named in the paper as a
faster pluggable key — and the pillars are rebuilt on the components a
certificate does not provide. The centre of gravity moves from *comparing
dissimilarity matrices* to *searching a space*, and the geometry stops being
decoration on a classifier: ball growth is the branching factor, sensitivity is
the coherence of moves, concentration is the discriminating power of a
heuristic. That is the geometry→application link the v3 program never had.

## 3. Reading order

| File | Replaces / extends | What it holds |
|---|---|---|
| [`proposal.md`](proposal.md) | `../PROPOSAL.md` | premise, thesis v5, narrative spine, what each pillar carries, what is retired |
| [`venue.md`](venue.md) | (new) | TKDE fit: what the venue rewards, what must be added, what must be cut, in-community related work |
| [`theory.md`](theory.md) | `../theoretical/{stability,geometry}.md` obligations | the proof obligations P1–P6, their risk levels, their fallbacks, and which application each one licenses |
| [`logic_models/`](logic_models/) | (new) | the FOL bridge: **the alphabet question (`Σ_HG` reduction vs a purpose-built `Σ_FO`)**, the MIN-CM problem, model-space geometry, the data sources, the literature position |
| [`applications.md`](applications.md) | `../empirical/applications.md` | **the certificate-vs-space argument** and the application program C1–C5, with the disposition of A1–A4 and of the retired B1–B5 |
| [`data.md`](data.md) | `../DATA.md` | ARB/Benson corpora + ego-net derivation (already implemented), the logic data sources, retained synthetic corpora, the feasibility gates |
| [`geometry.md`](geometry.md) | `../theoretical/geometry.md` | the synthesis: the invariants that survive, re-pointed at **search-space** consumers, and what moves to an appendix |
| [`competitors.md`](competitors.md) | `../COMPETITORS.md` | competitor sets + pre-registered contracts, including the **conceded** canonicalization comparison |

## 4. What survives from the current article (nothing measured is discarded)

| Asset | Status under v5.1 |
|---|---|
| Theorem A + Corollary A (`w*_c` complete ⇒ `d_I` a metric) | **Foundation** — it makes the space's points well defined. It is *not* sold as a dedup advantage (nauty ties and is faster) |
| Compactness / bits (r > 1 on 320/320, median 1.441, p = 1.6 × 10⁻⁵⁴) | **Kept, re-consumed** — search-state size: bytes per stored frontier element |
| G1 concentration + hubness | **Kept, re-consumed** — the discriminating power of a distance heuristic (predicted: weak; reported) |
| G2 sensitivity + ladder + the nauty contrast | **Kept, promoted** — it decides *which move operator the search uses*: string-space moves, cost order, no distance guidance |
| A4 shortest path + 62/62 ambient decodability | **Promoted to a pillar** (C3) — the PI's "camino más corto" |
| A1 MDS geometry table | **Demoted to one figure + one table**; MDS stops being an application |
| A2 clustering / A3 kNN on Stratum C | **Kept as a short measured-limits subsection**, not a pillar (this is exactly the PI's point) |
| E1' (ρ = 0.622, N = 6,921) + envelope + impossibility | **Kept in the discussion, and gains an algorithmic use to test** — envelope as a filtering bound for HGED-threshold search (`theory.md` P5; likely too weak, must be measured before any claim) |
| Stratum C corpus + the `size_l1`/`degree_seq_l1` floors | **Kept** — the falsifiable-corpus methodology is a genuine contribution and it carries the measured-limits subsection |
| HIC censored exhibit | **Candidate for retirement** (PI decision D5 below) — superseded as a real anchor by ARB ego-nets |

## 5. Decisions the PI must make

> **ANSWERED 2026-09-04.** The PI ratified D1 (string-space processing of KB
> collections as the centre, with a new obligation to justify the tasks'
> real-world utility), D2 (the logic material becomes a *second* manuscript —
> this one stays out of the logical aspects), D3′ (the preprint's alphabet is
> not binding; F4 preferred; **criterion: similar KBs must encode to strings at
> small Levenshtein distance**), and D4–D6 as recommended. His words, the
> mapping and the consequences — including the fact that the D3′ criterion
> requires an *encoder* change rather than the decoder-side extension that had
> been proposed — are in [`START_HERE.md` §6.0](START_HERE.md).

Listed in the order that unblocks the most work.

- **D1 — Is the search-space pillar the flagship, or a second pillar?**
  Recommended: **flagship**. It is the only framing in which IsalHG is
  *indispensable* rather than *competitive*, which is the PI's own criterion.
  Note the v5.1 correction: the pillar is the **space** (moves, order, decoder,
  metric), not enumeration throughput.
- **D2 — One paper or two?** The full program (theory + the search-space
  framework + the logic instantiation + real-data navigation + the limits) is
  large for one TKDE submission. Recommended: **one paper**, with the logic
  application as the flagship instantiation rather than a separate contribution.
  A dedicated logic paper (AAAI / IJCAR / JAR) is the natural follow-up.
- **D3′ — The alphabet (supersedes D3, and this is now the biggest technical
  decision).** Reduce relational structures into the current `Σ_HG` (encodings
  E1/E2), or design a purpose-built **`Σ_FO`** and re-run the geometry pipeline
  on it? Nothing is frozen except by choice: D-TA2 fixes *which* tie-complete
  lex-min for `Σ_HG`, not that `Σ_HG` is the only alphabet. Recommended:
  **F4 — a native `FACT` token, added as a *conservative extension*** that
  degenerates to today's `Σ_HG` on the unlabelled hypergraph fragment, so every
  frozen result stays true of the fragment, Theorem A extends rather than
  restarts, and the alphabet change becomes a *measurement*: does a
  semantics-aligned alphabet reduce the ≈30–50 % single-edit response? Full
  design space, costs and fallbacks: `logic_models/encoding.md` §3.
- **D4 — Time-box on P2** (the drift/avalanche lower bound). Recommended: keep,
  time-boxed, fallback pre-agreed; it is *explanatory*, not load-bearing.
- **D5 — Retire the HIC exhibit?** Recommended: **retire from the paper**, keep
  the loader and the gate measurement in the ledger. ARB replaces it.
- **D6 — A2/A3 disposition.** Recommended: one honest subsection (~1 page). Do
  not delete: the pre-registered contract binds us to report it.

## 6. The largest risks, stated now

1. **Any claim shaped like "we deduplicate" loses.** Levi-`{nauty, bliss,
   Traces}` canonize faster than `w*_c` and are equally exact; `nauty`-based
   canonical augmentation (McKay 1998) is the state of the art for isomorph-free
   generation; MACE-style SAT finders will beat naive enumeration on "does a
   countermodel exist". **The paper concedes all three in its introduction** and
   claims the space instead: moves, order, decoder, metric, and the questions
   they make computable. Contracts: `competitors.md`.
2. **Feasibility of `w*_c` on encoded structures is unmeasured.** The envelope
   (k = 3 → n ≈ 24; k = 5 → n = 8) came from *unlabelled random* hypergraphs;
   the logic encodings are heavily labelled and arity-2, where tie-breaking is
   much stronger and cost should be far lower — a hypothesis, not a measurement.
   Gate **G-L1** blocks the whole logic scope.
3. **The alphabet decision has a real engineering price.** A new `Σ_FO` means
   re-proving Theorem A (alphabet-parametric, so it should port), re-establishing
   P1, re-implementing the encoder in Python *and* C++, and re-running the
   geometry sweep (cheap — the harness is representation-agnostic). This is a
   scheduling decision, not a writing decision, and it must be priced before it
   is taken.
4. **Scope inflation.** The program touches automated reasoning, isomorph-free
   generation, metric search and hypergraph mining. The discipline that keeps it
   one paper: *one framework (C1), one flagship instantiation (C2), one
   navigation result (C3), one generic-optimization demonstration (C4), one
   real-data exhibit (C5), everything else cited or appendixed.*
5. **Novelty on the logic side is not verified by us.** The "combined objective
   is unstudied" claim came from a chat-level survey, not a verified
   `literature-search` pass. Task **L-LIT** must run before it enters
   `RELATED_WORK.md` — and its most important query is whether anyone has
   already put a *metric* on finite models.

## 7. If ratified — execution sketch (ledger-ready, not yet filed)

Gates first, then the alphabet decision, then theory, then the framework, then
instantiations.

| # | Work | Depends on | Size |
|---|---|---|---|
| G-L1 | `w*_c` cost probe on encoded models across (domain, facts), per surviving encoding | — | small, blocking |
| G-D1 | ARB feasibility. **Arity half closed 2026-08-12** (all 28 datasets on disk, scanned; 5 datasets at max arity 5 need no filter). **Size half open and binding**: ego-net `n` distribution + `w*_c` wall-clock | ARB download ✔ | small, blocking |
| G-B1 | ball growth / branching-factor probe: `\|B_r(w)\|` vs distinct iso-classes it contains | — | small |
| D3′ | the alphabet decision, priced against G-L1 | G-L1 | decision |
| T-P1 | P1 ambient decodability — proposition + proof + pinned test | — | small |
| T-P6 | P6 move-operator / ball-enumeration soundness | P1 | small |
| T-P2 | P2 drift/avalanche lower bound (time-boxed, fallback pre-agreed) | — | the open one |
| A-FO | `Σ_FO` design + Theorem A extension + encoder (only if D3′ chooses F1/F2/F4) | D3′ | large |
| E-C1 | the search-space framework: move operator, cost levels, frontier dedup, pluggable key | T-P1, T-P6 | medium |
| E-C2 | MIN-CM: formula input (TPTP subset), model checker, search driver, neighbourhood + diversity queries | E-C1, G-L1 | medium |
| E-C3 | navigation/repair on ladders, ARB temporal snapshots, and model space | G-D1, E-C1 | small |
| E-C4 | one black-box optimization predicate with a verifiable known answer | E-C1 | small |
| E-C5 | ARB census + the completeness-price measurement (reported as a nauty tie) | G-D1 | medium |
| L-LIT | verified literature pass (finite model finding, minimal models, metrics on structures) | — | small |
| W-1 | prose fold: the eight files here → the active `docs/article/` docs | all | medium |

**Recommendation.** Adopt v5.1. It keeps every measured asset, converts the v4
negative result from an apology into a *design input* (which move operator the
search uses), answers the PI's "indispensable, not competitive" criterion by
conceding every comparison we would lose and claiming only what a certificate
cannot provide, and lands the paper in a venue whose community already owns the
objects it uses (hypergraph edit distance — Qin et al., ICDE 2023; constructive
canonical forms for mining — gSpan, ICDM 2002; metric-space search —
ACM CSUR 2001).

**The single sentence that has to survive review:** *`nauty` decides identity
faster than we do; we are the only representation in which hypergraph space has
moves, an order, a decoder and a metric at once, so a search can run inside it.*

