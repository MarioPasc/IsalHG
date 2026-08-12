# Applications v5.1 — hypergraph space as a *search space*

*Proposed replacement for `../empirical/applications.md`. Status: pending PI.*
*Revised 2026-08-12 after the author's correction: the v5.0 draft built its
first pillar (B1) on isomorph-free enumeration, i.e. on deduplication
throughput. That is a losing frame — `nauty`/`bliss`/Traces on the Levi
reduction deduplicate faster than `w*_c` and with identical exactness, as our
own measurements show. This revision removes deduplication as a claim and
rebuilds the program on what a certificate cannot provide.*

---

## 0. The concession, stated first

**We do not compete on canonicalization.** For "are these two hypergraphs
isomorphic?" and "deduplicate this collection", the mature graph-isomorphism
engines on the Levi reduction are faster than the tie-complete `w*_c` and
exactly as precise (both are complete invariants). This is measured, not
conceded rhetorically: `w*_c` costs 617 s on PG(3,2) and > 900 s on rigid
STS(15) instances where nauty is milliseconds, and nauty-Levi edit distance
outperformed `d_I` on every task metric of the size-controlled corpus.

Any application whose core operation is *comparing two points* is therefore not
ours. The paper says so in the introduction, once, plainly — and then makes its
claim about something else.

## 1. The claim: a certificate is not a space

`nauty` returns a **certificate**: a witness that identifies a point. `Σ_HG`
returns a **space**: a ground set with moves, an order, a metric and a decoder,
in which point identity happens to be a by-product (Theorem A).

The distinction is precise and it is where the article now lives. A search over
combinatorial objects needs four components; the table records who supplies
which.

| Component | `Σ_HG` / `w*_c` | Levi + nauty/bliss/Traces |
|---|---|---|
| **Ground set** | all of `Σ_HG(k)*` — an explicitly describable, freely generated set | the *image* of the canonical map: a set with no description other than "canonize and compare" |
| **Membership** | free (closed alphabet: every word is a word) | must canonize to decide whether a given string is a certificate at all |
| **Move operator** | token edit; every result decodes to a **connected hypergraph** (P1) — no validity filter, no problem-specific edit taxonomy | none in certificate space; moves must be defined on the explicit structure, and an edited certificate is generally not a certificate |
| **Decoder** | `S2H`, **total** on the alphabet | partial: only points already in the image decode to a canonical structure |
| **Order** | shortlex, and `d_Lev(ε, w) = \|w\|` — the order *is* distance from the empty word | lexicographic on certificates; carries no structural meaning |
| **Metric** | `d_Lev` on tokens (characterized: §`geometry.md`) | edit distance on certificates — usable, and on small-perturbation tasks *better* than ours (measured), but the space is not navigable: its points are not freely constructible |
| **Identity** | Theorem A | **faster (conceded)** |

**The operative sentence for the paper.** *Moves in certificate space are
undefined; moves in structure space require re-canonization to be compared.
`Σ_HG` puts the moves, the objects and the comparison in one representation, so
a search can run entirely inside it.*

Four consequences, and they are the article's applications:

1. Sequence-level operators — Levenshtein-ball enumeration, crossover, splice,
   beam search, and (future work) sequence models — transfer to hypergraphs with
   no validity filter. *A hypergraph is a word* is an operational statement, not
   a slogan.
2. Every intermediate of a path is an inspectable object (P1), so
   *interpolation* and *repair* are meaningful.
3. The cost order is native, so "smallest object with property P" is a
   breadth-first sweep of balls around `ε`.
4. The geometry of the metric space **is** the geometry of the search space:
   ball growth is the branching factor, sensitivity is the coherence of moves,
   concentration is the discriminating power of a distance heuristic. This is
   the geometry→application link that the v3 program never had — the geometry
   is not decoration on a classifier, it is the parameter set of a search
   algorithm.

---

## C1 — Hypergraph space as a search space (the framework pillar)

**What it is.** The formal object: `(Σ_HG(k)*, d_Lev, S2H, w*_c)` as a
*searchable space* — ground set, move operator, decoder, canonical key, cost
order — together with the propositions that make each component well defined
(`theory.md` P1, P3, P6) and the measured parameters that make it usable
(`geometry.md`).

**Generic problem it solves.** *Find a minimum-cost connected hypergraph
satisfying a predicate `P`*, where `P` is a black box — evaluated by decoding
the candidate and running any test whatsoever (logical, spectral, combinatorial,
simulation-based). No requirement that `P` be expressible in a solver's input
language.

**Algorithm (the one the paper ships).** Breadth-first over cost levels; the
frontier is expanded by token edits; visited states are deduplicated
*syntactically* on the string (cheap, sound for visitation) and *semantically*
on `w*_c` where exactness of the census matters. Duplicate elimination is a
**correctness precondition, not a contribution** — and where its throughput
matters, nauty-on-Levi can be plugged in as the key, which the paper states
explicitly. What no other representation supplies is the rest of the loop.

**Measured parameters that make this concrete (`geometry.md`).**
- **Ball growth and its collapse.** `|B_r(w)|` in string space against the
  number of *distinct isomorphism classes* it contains: the redundancy of the
  move operator, i.e. how much duplicate work the search does per level. This is
  a **new measurement** and it is the cleanest quantitative link between the
  metric geometry and the search cost.
- **Sensitivity (measured: ≈30–50 % of the string per structural edit on
  unanchored substrates).** Read as a *design conclusion*: structure-guided
  moves are incoherent in string space, therefore the search moves in **string**
  space and orders by **cost**, never by distance-to-target. The avalanche that
  bounded v3's classification scores is here a fact about which move operator to
  choose — the same measurement, now load-bearing in the right direction.
- **Concentration / `D̂`.** Predicts (negatively) the value of a distance
  heuristic; reported as such.

**Honest limits.** The branching factor of token edits is large, the space is
exponential, and no claim of efficiency in general is made. What is claimed is
*applicability*: the loop runs for any decidable `P`, with no encoding step.

---

## C2 — Minimal countermodel search, and the geometry of model space (flagship)

Full specification in [`logic_models/`](logic_models/); the framing is what
changed. **The contribution is not isomorphism deduplication.** Model finders
already deduplicate (incompletely, by design, because complete rejection has
historically cost more than the duplicates it removes), and nauty deduplicates
exactly and faster than we do. The contribution is that **the model space of a
formula becomes a metric space with a total, decodable representation**, which
makes a class of questions computable that neither a SAT/SMT model finder nor a
canonical-labelling engine can answer at all:

| Question | SAT/SMT model finder | nauty | IsalHG |
|---|---|---|---|
| *Is there a countermodel? Find one.* | **yes, and faster** | — | yes (slower — conceded) |
| *Is this the same countermodel as that one?* | — | **yes, faster** | yes |
| *How far apart are two countermodels?* | no | no | **yes** (`d_L`) |
| *Give me every countermodel within edit radius `r` of this one* | no | no | **yes** (decode the ball, P1) |
| *Minimal repair path from this countermodel to a model, with every intermediate a valid structure* | no | no | **yes** (C3) |
| *How diverse is the set of minimal countermodels?* | no (enumeration without complete symmetry breaking repeats classes) | partially (can dedup a given set, cannot generate) | **yes** — spread, medoid, and the census by cost level |

The last three rows are the paper's results on this application, and they are
*geometric* results about a logical object. The census by cost level is
verifiable against known counts (`logic_models/data.md` §3), which is what keeps the
claim checkable.

**Reported.** Minimum cost per benchmark formula; the number and the
**geometric spread** of minimal countermodels up to isomorphism; radius-`r`
countermodel neighbourhoods; repair paths; and — plainly — the wall-clock
comparison against Mace4/Paradox and against a MaxSAT encoding of our own
objective, which we expect to lose (`competitors.md` §3).

---

## C3 — Navigation: shortest paths, interpolation, repair

*The PI's "hallar el camino más corto entre dos hipergrafos", promoted from
demonstration to pillar, backed by P1 rather than by an anecdote.*

Given `H_A`, `H_B`, the minimal-`d_I` path and its intermediates, in two regimes:
the **ambient path** (the Levenshtein alignment between the two canonical
strings — every intermediate word decodes to a connected hypergraph, including
the non-canonical interior) and the **pool path** (shortest path in the
`d_I`-graph over a set of intermediates; the v3 A4 construction, retained).

**Why nauty cannot do this.** Not because its canonical string is
undecodable — it is a serialization and it decodes — but because the *interior
of an alignment between two nauty certificates is not a certificate*, so the
path has no interpretable intermediates: you would be reading strings that are
not the canonical form of anything and whose decoding, if defined at all, is an
artifact of the serialization. Our alphabet is closed, so the interior is
populated by actual connected hypergraphs. Measured: 62/62 intermediates decode
and are connected, 52 of them non-canonical.

**Instances.** (i) synthetic ladders with known Qin budgets (monotone fraction
1.00, retained); (ii) **real temporal snapshots** from the ARB collection —
which structural path connects one week's contact hypergraph to the next;
(iii) **FOL model repair** (C2) — the path from a countermodel to a model as a
minimal repair sequence.

**Retained honesty.** Exact ladder-intermediate recovery is low (0.125): the
geodesic routes through same-budget alternatives rather than retracing the edit
sequence. Reported, and consistent with `d_I` not being an edit-distance proxy.
The withdrawn pool-based "decodability score" stays withdrawn; **T-M5m** is the
task that measures the ambient claim properly.

---

## C4 — Black-box structural optimization ("smallest `H` such that `P(H)`")

The instantiation of C1 where the property is **not expressible to a solver**,
which is precisely where both competitors drop out: a SAT/SMT/ASP encoding
requires `P` to be written in its logic, and nauty requires the candidate set to
already exist.

Candidate predicates, all decidable by decoding and testing:
- spectral: smallest connected hypergraph whose primal spectral gap exceeds a
  threshold, or whose Levi spectrum has a prescribed multiplicity;
- combinatorial: smallest hypergraph containing no copy of a forbidden
  sub-hypergraph, or violating a conjectured inequality (the classical
  "computer search for a minimal counterexample" workflow);
- statistical/simulated: smallest hypergraph on which a specified dynamic
  process exceeds a threshold.

**Status: proposed, scope-gated.** One such predicate, chosen for
verifiability (a known answer at small sizes), is enough to demonstrate the
loop. The paper should not attempt a portfolio here.

**What it demonstrates.** That the search space abstraction is *generic*: the
same loop, the same move operator, the same order, a different one-line
predicate. That genericity is the framework contribution and it is the answer to
"what is this representation for".

---

## C5 — Real-data structure: navigation and the completeness price (secondary)

Real corpora enter for credibility, on the ARB/Benson collection (`data.md`).
Two measurements, both honest about the nauty tie:

- **Navigation on real temporal data** (feeds C3): snapshots of the timestamped
  ARB datasets, paths between them, decoded intermediates.
- **The completeness price.** Group an ARB ego-hypergraph corpus by each
  representation's key and count pairs that share a key while being
  non-isomorphic (ground truth: `pynauty`-Levi). WL, NetLSD, HPD and the degree
  sequence merge non-isomorphic real structures at a measurable rate; `w*_c`
  and nauty both merge none. **The result is a tie with nauty and is reported as
  a tie** — its target is the stability-by-construction embeddings, and its
  purpose is to price what they buy their smoothness with. It is a subsection,
  not a pillar.

Also reported here: the structural census of real local structure (distinct
classes vs corpus size, class-frequency distribution) and the measured
feasibility envelope with its censoring table.

---

## 2. Disposition of earlier application sets

| Earlier | Now | Why |
|---|---|---|
| **B1 — isomorph-free enumeration** (v5.0) | **retired as a pillar**; absorbed into C1 as a *correctness precondition*, with nauty named as a pluggable and faster key | deduplication throughput is a loss against nauty; claiming it would invite exactly the right rejection |
| **B2 — minimal countermodels** | **C2, reframed** from "we dedup exactly" to "model space becomes navigable" | the dedup framing was the losing half of the idea |
| **B3 — navigation** | **C3**, unchanged in substance, strengthened in argument | — |
| **B4 — dedup + false merges** | **C5**, demoted to a subsection and reported as a tie with nauty | same reason as B1 |
| **B5 — retrieval (stretch)** | **dropped** | it competes rather than differentiates, and the geometry predicts weak pruning |
| — | **C4 — black-box optimization** (new) | the class where *both* competitors are inapplicable |
| **A1 — MDS** | one figure + the geometry table | not a capability |
| **A2/A3 — clustering, kNN** | one measured-limits subsection | contract-bound to report; motivates the reframe |
| **A4 — shortest path** | **C3** | PI-endorsed, promoted |
| **G1/G2 — geometry profiles** | retained, re-consumed as **search-space parameters** | see `geometry.md` |
| **Capability matrix** | retained; columns become *supplies a move operator*, *ambient space is objects*, *native cost order*, *exact key*, *fast key* — with nauty winning the last | the honest summary figure |

## 3. Application → what it needs → who else has it

| Application | Needs | Why nauty cannot | Why a solver cannot |
|---|---|---|---|
| C1 search space | move operator + decoder + order in one representation | certificate space has no freely constructible points | requires `P` encoded in its logic |
| C2 model geometry | metric + ball enumeration over models | no metric, no generation | no metric between models |
| C3 navigation | ambient decodability (P1) | alignment interiors are not certificates | no notion of path |
| C4 black-box optimization | decode-and-test loop over a cost-ordered space | cannot generate candidates | cannot express `P` |
| C5 completeness price | a complete key | **nauty ties — reported as a tie** | n/a |
