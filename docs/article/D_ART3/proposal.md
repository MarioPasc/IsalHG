# Proposal v5.1 — premise, thesis, spine

*Proposed replacement for `../PROPOSAL.md`. Status: pending PI (D-ART3).*
*Revised 2026-08-12: the v5.0 spine put isomorph-free **enumeration** at its
centre. Corrected — Levi-`{nauty, bliss, Traces}` deduplicate faster than `w*_c`
and equally exactly, so deduplication is a correctness precondition, never a
claim. The centre is the **search space**: moves, order, decoder, metric.*

---

## 0. Premise (unchanged, and now doing real work)

*A hypergraph is a word.* The IsalHG instruction language encodes any connected
hypergraph as a string over the **closed** alphabet `Σ_HG`, and the frozen
tie-complete canonical form `w*_c` makes that encoding a fingerprint:

> **Theorem A.** `w*_c(H) = w*_c(H') ⇔ H ≅ H'`.
> **Corollary A.** `d_I(H,H') = d_Lev(w*_c(H), w*_c(H'))` is a metric on
> isomorphism classes of connected hypergraphs.

Three properties follow that no competing hypergraph representation has
simultaneously, and v5 is built on their *conjunction*:

| Property | Source | What it enables |
|---|---|---|
| **Completeness** | Theorem A | exact isomorphism rejection: a key that never merges two non-isomorphic objects and never splits one |
| **Closure + totality** | invariant 2 (`S2H` never rejects) + P1 | the *ambient space is made of hypergraphs*: every word decodes, so generation, mutation and interpolation cannot produce an invalid object |
| **Constructivity** | `w*_c` *is* a construction sequence | the canonical form doubles as the generation operator: extending an object is appending tokens |

The metric is the fourth property, and it is what turns a set of keys into a
*space*: objects can be ordered, indexed, diffed, and joined by paths.

## 1. The thesis (v5)

**v3 (D-ART2) said:** characterize the geometry, then exploit it on standard ML
pipelines. **Measured outcome (T-M4b):** on a size-controlled corpus the
exploit pillar falls — nauty-Levi edit leads clustering (ARI up to 0.614) and
kNN (AUC up to 0.938), IsalHG is statistically above the floor but small (ARI
0.016–0.028). The mechanism is measured: a single edit moves `w*_c` by
≈30–50 % of the string on unanchored substrates.

**v4 (draft) said:** keep the skeleton, reframe as characterize → explain →
instrument. Honest, but it makes the paper's destination a *limit result*.

**v5.1 says:** the measured limit is real and is about *task geometry under
small structural perturbations* — the direction structure → string. It says
nothing about the direction the representation is actually used in for search
(string → structure), nor about the three properties above. So:

> **Thesis.** A certificate identifies a point; an alphabet gives you a space.
> `Σ_HG` supplies, in one representation, the four components a search over
> hypergraphs needs — a freely generated ground set, a move operator that never
> leaves the space, a native cost order, and a total decoder — with point
> identity (Theorem A) as a by-product. We prove what makes each component well
> defined, measure the geometry that governs how the search behaves in it, and
> demonstrate it on problems that require *moving* in the space: finding and
> repairing the **smallest countermodel** of a first-order formula, navigating
> between real hypergraph snapshots, and minimizing a black-box structural
> objective.

**The concession that must appear in the introduction.** For deciding
isomorphism and for deduplicating a collection, `nauty`/`bliss`/Traces on the
Levi reduction are faster than `w*_c` and exactly as precise. We measure it, we
say it, and we do not build a claim on it. Deduplication is a precondition of
the search loop, and where its throughput matters a Levi-nauty key can be
substituted for ours inside our own framework.

The pitch line for the abstract: *we do not claim a better hypergraph
dissimilarity, and we do not claim a faster isomorphism test; we claim that
hypergraph space, written as words, becomes **searchable**.*

## 2. Narrative spine

Each step is motivated by the previous; the `§` numbers here are this document's,
not the paper's.

0. **Foundation.** `Σ_HG`, the VM, H2S/S2H, Theorem A, Corollary A. *Source:*
   `../H2S_S2H.md`, `../theoretical/stability.md` §1.
1. **A certificate is not a space.** The concession (nauty is faster and equally
   exact at identity), then the four-component table: ground set, move operator,
   order, decoder — who supplies which. Backed by ambient decodability (**P1**),
   cost accounting (**P3**) and move-operator soundness (**P6**). Compactness
   (bits, r > 1 on 320/320) enters here as *search-state size*: what one frontier
   element costs to store. *Source:* `applications.md` §1, `theory.md`.
2. **Geometry — synthesized, and re-pointed at the search.** Ball growth (the
   branching factor and its collapse to distinct isomorphism classes), local
   sensitivity (which move operator to use — measured: string-space, not
   structure-space), concentration and `D̂` (the discriminating power of a
   distance heuristic — measured: weak), non-Euclideanness (triangle-inequality
   pruning is licensed, Euclidean indexing is not). *Source:* `geometry.md`.
3. **The framework — hypergraph space as a search space.** Move operator, cost
   levels, frontier dedup (with `nauty` named as a faster pluggable key), and
   the generic problem it solves: *smallest connected hypergraph satisfying a
   black-box predicate `P`*. *Source:* `applications.md` C1.
4. **The flagship instantiation — minimal countermodels, and the geometry of
   model space.** The FOL bridge, the alphabet question (`Σ_HG` reduction vs a
   purpose-built `Σ_FO`), the MIN-CM objective, and the four questions the
   metric makes computable that neither a model finder nor a canonical-labelling
   engine can answer: distance between countermodels, radius-`r` countermodel
   neighbourhoods, minimal repair paths, and the diversity of the minimal set.
   *Source:* `logic_models/`.
5. **Navigation.** Shortest paths in `(Σ_HG*, d_Lev)` with decodable
   intermediates — the PI's "camino más corto" — on synthetic ladders, on real
   temporal snapshots, and as model repair. *Source:* `applications.md` C3.
6. **Real data.** ARB/Benson ego-hypergraph corpora: the structural census,
   navigation between temporal snapshots, and the **completeness price** — how
   many non-isomorphic real structures each stability-by-construction embedding
   merges (reported as a *tie* with nauty, which merges none either).
   *Source:* `applications.md` C5, `data.md` §1.
7. **Where the metric does not help (measured).** The size-controlled corpus,
   the two naive floors, the A2/A3 outcome, and the avalanche mechanism. One
   honest subsection, reported under the pre-registered contract. *Source:*
   `../empirical/applications.md` (retained), `applications.md` §4.
8. **Discussion.** The completeness–stability frontier corrected (the culprit is
   the *encoding format*, not completeness — nauty is complete too and localizes
   the same edits); the HGED relation (length lemma, unconditional envelope,
   impossibility of a bi-Lipschitz proxy, the E1' figure ρ = 0.622); the
   envelope as a candidate filtering bound for threshold search (**P5**, to be
   measured, likely weak); future work.

**Why this order.** It leads with what is proved, spends the geometry only where
an engineering decision depends on it, and puts the capability claims where they
can be tested rather than asserted. The measured negative (step 7) arrives
*after* the reader knows what the representation is for, so it reads as a
characterized boundary rather than as the paper's result.

## 3. What changes relative to the active v3 scope

| v3 | v5.1 |
|---|---|
| Thesis: characterize → exploit | Thesis: **a certificate is not a space — we supply the space** |
| Pillars: geometry + four ML applications | Pillars: **the search-space framework (C1) + minimal countermodels and model-space geometry (C2) + navigation (C3) + black-box structural optimization (C4)**, with real data as the credibility exhibit (C5) |
| Six geometry invariants, ML consumers | **Four** invariants, **search-design** consumers (branching factor, move-operator choice, heuristic power, pruning licence) |
| A1 MDS as flagship application | one figure and one table; MDS is not an application |
| A2/A3 as the exploit pillar | one honest limits subsection |
| A4 as "capability differentiator" demo | **promoted to a pillar** (C3), backed by P1 rather than by a demo |
| Real anchor: HIC (gate failed, censored exhibit) | Real anchor: **ARB/Benson ego-hypergraphs**, derived by Qin et al.'s own ICDE-2023 protocol (already implemented in-repo) |
| Competitors: five representations, dissimilarity head-to-head | purpose-specific sets, **with the canonicalization comparison conceded in the introduction** |
| Alphabet: `Σ_HG` frozen | **`Σ_HG` is not frozen** — a purpose-built `Σ_FO` (conservative extension) is on the table, and the geometry pipeline can be re-run on it (`logic_models/encoding.md` §3) |
| Venue: *Information Sciences* | **IEEE TKDE** |

## 4. What is *not* proposed

- **No claim that IsalHG wins on identity or on deduplication.** Not against
  `nauty`/`bliss`/Traces for canonical labelling, not against SAT/MaxSAT for
  "does a countermodel exist". Both are conceded in the introduction and
  measured in the tables. The claim is the space: moves, order, decoder, metric,
  in one representation.
- **No re-run of the frozen `Σ_HG` results.** E1', bits, G2 profiles, the
  Stratum C tables and the HIC measurement stay as measured. *If* D3′ adopts a
  new alphabet, those results remain results **about `Σ_HG`** and are scoped as
  such; a conservative extension keeps them true of the hypergraph fragment.
- **No unbounded alphabet redesign.** D3′ is a single, priced decision with four
  named options and a recommended one; it is not an invitation to iterate on the
  encoding.
- **No abandonment of the measured limits.** The A2/A3 outcome is contract-bound
  and stays in the paper.
- **No abandonment of the HGED discussion.** At TKDE it becomes *more* relevant
  (Qin et al. is an ICDE paper), and it acquires an algorithmic question worth
  measuring (P5).

## 5. Open scope questions

- **OQ-1.** Does the paper state MIN-CM as a *new problem* or as a *new
  algorithmic approach to a known one*? Depends on the outcome of L-LIT
  (`logic_models/risks.md` §6). Default, until verified: "a known problem family
  (finite model finding + cardinality-minimal models) under an objective the
  standard tools optimize separately."
- **OQ-2.** How much of the geometry survives into the main text vs an appendix?
  Proposed split in `geometry.md` §4.
- **OQ-3.** Is B5 (retrieval over an ego-net store) in scope, or is B4
  (cataloguing + false merges) sufficient real-data evidence? B5 costs a metric
  index implementation; B4 costs a sweep. Default: **B4 in, B5 stretch.**
- **OQ-4.** Bits: keep the fixed-width estimator, or re-express as bytes/key for
  the dedup-index framing? Recommended: report both, one line each — the
  estimator is reviewer-tested and the byte figure is what a TKDE reader wants.
