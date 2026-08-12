# Related work — the literature map

*Skeleton, populated from the PI's source material in [`src/`](src/) and from
prior project knowledge. **Nothing here is verified to the project's citation
standard yet** — `../../RELATED_WORK.md` admits only verified entries, and task
**L-LIT** must run before any of this migrates there. Items flagged `[unverified]`
came from chat-level analysis and may be misattributed.*

---

## 1. Belief change — the ancestry of P-REPAIR and P-MEDIAN

- **Katsuno & Mendelzon** — the revision/update distinction, and the framework
  that makes explicit that a belief-change operator is *parameterized by a
  distance*. This is the licence for defining an operator by `d_I`
  (`risks.md` §1(a)).
- **Dalal** — cardinality-minimal symmetric difference; the propositional
  ancestor of the distance all three ideas use.
- **Winslett (PMA)** — the subset-minimal variant.
- **Konieczny & Pérez** — model-based merging operators, in particular `Δ^Σ`
  (sum aggregation), which is exactly P-MEDIAN under a **rigid, named**
  vocabulary. Isomorphism-invariance is precisely the assumption they make that
  we drop. `[unverified]`
- **Wijsen** — update repairs; the symmetric-difference repair setting.
  `[unverified]`

## 2. Database repair — the applied line for P-REPAIR

- **Arenas, Bertossi & Chomicki** and successors — consistent query answering
  and repairs under integrity constraints; subset-minimal vs cardinality-minimal;
  mature ASP and MaxSAT encodings; PTIME islands (e.g. single-key repairs).
  `[unverified]`
- Repair over **existential rules / TGDs with labelled nulls** — the closest
  match to the "domain may grow" direction, since fresh elements are exactly
  chase nulls. `[unverified]`

## 3. Finite model finding — P-MIN, and the model-existence oracle everywhere

- **McCune**, *Mace4 Reference Manual and Guide* (Argonne, 2003).
- **Claessen & Sörensson**, *New techniques that improve MACE-style finite model
  finding* (CADE-19 workshop, 2003) — Paradox; static symmetry breaking over
  constants.
- **Zhang & Zhang**, *SEM: a system for enumerating models* (IJCAI 1995) — the
  least-number heuristic.
- **Reynolds et al.**, *Finite model finding in SMT* (CAV 2013) — CVC4/cvc5.
- **Reger, Suda & Voronkov**, *Finding finite models in multi-sorted first-order
  logic* (SAT 2016) — Vampire's finite model builder.
- **Torlak & Jackson**, *Kodkod: a relational model finder* (TACAS 2007);
  **Jackson**, *Alloy* (TOSEM 2002); **Blanchette & Nipkow**, *Nitpick* (ITP
  2010).
- **Sutcliffe** — the TPTP library and the CASC divisions.

## 4. Minimal models

- **Bry & Yahya** — minimal Herbrand model generation via positive unit
  hyperresolution tableaux (JAR 2000). `[unverified]`
- **Niemelä**; circumscription; stable-model / answer-set semantics —
  subset-minimality.
- **Creignou, Olive & Schmidt**, *Complexity of reasoning with cardinality
  minimality conditions* (AAAI 2023) — `CardMinSat`, typically `Θ₂ᵖ`-complete.
  `[unverified]`
- Weighted MaxSAT with unit soft clauses; ASP `#minimize` — the standard
  practical route to cardinality-minimal models.

## 5. Distance between structures — where our contribution lands

- **Qin et al.**, *Computing Hypergraph Edit Distance* (ICDE 2023) — our adopted
  cost model (Definition 3, verbatim) and our ego-network definition
  (Definition 1). **Verified; already in `../../RELATED_WORK.md`.**
- **Riesen & Bunke** (2009) — bipartite/Hungarian GED approximation. The
  competitor whose output is an upper bound, not a metric.
- **Justice & Hero**; **Lerouge et al.** — assignment-based ILP formulations of
  GED. `[unverified]`
- **Jiang, Münger & Bunke**, *On median graphs: properties, algorithms and
  applications* (IEEE TPAMI 2001) — the generalized median graph problem; NP-hard.
  **The direct ancestor of P-MEDIAN.** `[unverified — check exact title/year]`
- **Ferrer, Valveny, Serratosa, Riesen & Bunke** — generalized median graph by
  graph embedding into vector spaces; the pipeline whose **reconstruction** step
  we do not need. `[unverified]`
- **Sim & Park** — NP-hardness of the median string problem. `[unverified]`
- **Babai** — quasipolynomial graph isomorphism; the reason "distance zero" is
  not known to be polynomial.

## 6. Isomorph-free generation — the borrowed framework

- **McKay**, *Isomorph-free exhaustive generation* (J. Algorithms, 1998).
- **Read** (1978), orderly algorithms; **Faradžev**.
- **Kaski & Östergård**, *Classification Algorithms for Codes and Designs*
  (Springer, 2006) — already in the repo's orbit via the vendored STS catalogue.
- **Yan & Han**, *gSpan* (ICDM 2002) — the minimum DFS code: a constructive
  canonical form preferred over an external certificate because mining needs the
  extension operator. The precedent for our positioning.

## 7. Structure modification — the FPT island

- **Cai** — vertex deletion to properties with a finite forbidden set; and the
  H-free edge-modification results. Universal / forbidden-pattern `ψ` is FPT in
  the edit budget `k`, automatically iso-invariant. **The strongest baseline on
  that fragment.** `[unverified]`
- **Eiter & Gottlob**; **Selman & Levesque** — complexity of abduction, the
  additions-only case of P-ENTAIL. `[unverified]`

## 8. Model theory background

- **Ebbinghaus & Flum**; **Hodges** — the isomorphism lemma; Łoś–Tarski and
  homomorphism preservation (which forces the OWA fork in `vocabulary.md` §4);
  **Trakhtenbrot** — undecidability of finite validity.

---

## L-LIT — the verification task

**Blocks every novelty claim.** Required queries, in priority order:

1. **Has anyone put a *tractable* metric on isomorphism classes of finite
   relational structures and used it for repair, merging, or median?** This is
   the query that decides whether our framing is "a new approach" or "a new
   problem". If a canonical-form-based structure distance already exists in this
   literature, we must cite it and reposition.
2. Generalized median graph computed via a **canonical-string** distance —
   i.e. median-string-as-median-graph. Has it been done?
3. Belief merging with a **non-rigid** vocabulary (isomorphism-invariant
   merging).
4. Repair/update where the domain may grow **and** the search is iso-invariant.
5. The combined `|D| + Σ_i |P_i|` objective for minimal countermodels.

Every `[unverified]` item above must be confirmed (authors, title, venue, year,
DOI) or dropped before it reaches `../../RELATED_WORK.md`.
