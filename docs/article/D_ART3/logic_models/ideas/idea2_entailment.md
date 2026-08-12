# P-ENTAIL — entailment forcing via nearest-model search

*Status: documentation, pending PI ratification of D3′. Reading: closed-world
(CWA) throughout — see §1. Vocabulary: `vocabulary.md`. Shared foundation:
`encoding.md`, `scope.md`, `data.md`, `competitors.md`, `risks.md`. Sibling:
`idea1_repair.md` (P-REPAIR). Problem statement: `problems.md` §P-ENTAIL.*

---

## 0. Summary judgement (read this first)

P-ENTAIL is **worth doing as a short exhibit** gated on D3′ (the `Σ_FO`
alphabet), developed together with P-REPAIR in one shared section of the paper.
It is **not suitable as a standalone lead contribution** and **not a separate
paper** at this stage.

Reasons, in priority order:

1. **Feasibility gate.** Under the current `Σ_HG` alphabet (F0), P-ENTAIL is
   infeasible by measurement: a one-fact edit is ≈30–50 % of the string away in
   `d_I`, so ball enumeration at feasible radii does not reach one-fact repairs.
   This is not a quality concern — it is a procedure that does not work in F0.
   Every experiment depends on D3′ being ratified and implemented.
2. **The iso-invariance advantage is narrow here.** For universal /
   forbidden-pattern `T` (denial constraints, integrity axioms), bounded-search-
   tree FPT branching is **already iso-invariant by construction** — the target
   class is closed under isomorphism and the algorithm branches over moves, not
   over labelled objects. Our claim of "iso-invariance-by-construction without
   symmetry-breaking machinery" does not differentiate us on that fragment. For
   existential-positive `T` (the match-completion regime), the advantage holds:
   MaxSAT / ASP re-derive the same repair under every permutation of the fresh
   pool without BreakID / lex-leader; we emit none by construction.
3. **Implementation and data are shared.** P-ENTAIL and P-REPAIR run over the
   same encoding, the same ball-enumeration loop, and the same iso-invariance
   measurement. Their cost is largely the cost of P-REPAIR plus TPTP sourcing.

**Estimated cost under D3′.** 4–6 weeks for the encoder + experiments at
feasible scale; 1–2 weeks for the TPTP perturbation corpus; writing is shared
with P-REPAIR. If D3′ is deferred, P-ENTAIL is out of scope.

---

## 1. The CWA/OWA fork — resolved

**Decision: closed-world (CWA) throughout.** This is forced, not chosen.

`w*_c ∘ E` encodes one finite `σ`-structure. It does not encode a theory. The
sentence `K ⊭ T` therefore means: the single structure `K` falsifies `T`; the
target is the nearest member of `Mod(T)` (the class of finite models of `T`).
Arbitrary first-order `T` is meaningful.

The **open-world reading** (OWA) says: `K ⊨ T` iff every model of the ground
facts satisfies `T`. By the Łoś–Tarski preservation theorem, ground facts under
OWA can only entail sentences preserved under extensions, i.e. existential-
positive sentences (unions of conjunctive queries). Under OWA the *only*
interesting case is T being a UCQ, and P-ENTAIL collapses to: *add the cheapest
set of ground facts that creates a query match.* This is pure abduction /
minimum-cost match completion — a well-understood problem that does not require
our representation.

**OWA does not extend our reach.** The OWA-with-existential-positive-T case is
a *restriction* of CWA's existential-positive fragment: it bans deletions and
shrinkage. We handle the more general version (CWA, additions and deletions,
domain may grow or shrink) in §2. The OWA path gives us nothing not already
covered and adds the Łoś–Tarski constraint as baggage. We do not pursue it.

**Consequence for the paper.** Every section of this file operates under CWA.
The word "entailment" means: the single structure K does not satisfy T, and we
seek the nearest structure that does.

---

## 2. P-ENTAIL = P-REPAIR — the structural finding and its consequences

`problems.md` states this directly and it is correct: **P-ENTAIL and P-REPAIR
are the same problem.** The common form is:

> **Given** a sentence `ψ` and a KB `K` with `K ⊭ ψ`, **find**
> `argmin_{𝔐 ∈ Mod(ψ)} d(K, 𝔐)`.

P-REPAIR has `ψ = Σ` (an axiom set, typically a conjunction). P-ENTAIL has
`ψ = T` (a theorem). Same template; the sentence shape decides which algorithm
wins.

**Why keep two experiments.** The typical *shapes* of `Σ` and `T` differ, and
that shape difference sends the two problems into different algorithmic regimes
with different baselines:

- `Σ` is typically a conjunction of universal / denial constraints or
  functional dependencies. The repair regime is FPT branching (§3 row 2) or
  database repair (row 3).
- `T` is typically existential-positive in the KB / reasoning context: "there
  exists a path between A and B", "some fact pattern P is witnessed". The
  entailment regime is match-completion (§3 row 1).

One implementation, two regimes, two sections of experimental results, two sets
of baselines. The paper should present them in one section ("nearest-model
search") with the fragment taxonomy (§3) making the bifurcation explicit.

---

## 3. Fragment taxonomy and what we win where

Terminology from `vocabulary.md` and `problems.md`; complexity references
unverified [unverified] unless noted in `related_work.md`.

| Shape of `T` | Mechanism | Best known method | Our position |
|---|---|---|---|
| **Existential-positive / CQ** (∃x.φ(x), φ quantifier-free) | create a homomorphic image of the query pattern | minimum-cost match completion; PTIME in data complexity for fixed `T`, NP-hard in `\|T\|` [unverified] | **We compete here.** Iso-invariance-by-construction (zero duplicate results), decodable intermediates, measured `d_I` vs `d_SED` suboptimality gap. MaxSAT/ASP is the baseline. |
| **Universal / forbidden-pattern** (`∀x.¬φ(x)`, hereditary property) | destroy every witness | FPT in edit budget `k` by bounded-search-tree branching (Cai [unverified]); automatically iso-invariant | **We concede this fragment.** FPT branching is already iso-invariant (target class closed under iso); we have no asymptotic advantage and do not claim one. |
| **Denial constraints / functional dependencies** | subset or cardinality-minimal repair | mature ASP / MaxSAT encodings; PTIME islands (single-key) [unverified] | Same position as P-REPAIR: iso-by-construction differentiates us on duplicate count; wall-clock loss expected and reported. |
| **Additions-only / monotone** | abduction: find minimal `Δ` with `K ∪ Δ ⊨ T` | Eiter–Gottlob for propositional; Selman–Levesque for Horn [unverified] | A special case of our search (deletions and shrinkage disabled). We handle it but claim no advantage over dedicated abductive tooling. |
| **Mixed FO / genuinely general** | branch-and-bound over domain size | constrained model finder (ASP/MaxSAT) + explicit alignment variables for iso | **Primary niche.** Our representation is the only one that supplies iso-invariance without alignment variables; baselines need BreakID or lex-leader. Ball enumeration is the algorithm. |

**The critical row is universal/forbidden-pattern.** If the PI's target `T`
sentences are closer to integrity constraints than to existence claims, P-ENTAIL
lands in the FPT regime where our iso-invariance argument has no force. The
choice of fragment to emphasize in the paper must be made before experiments are
designed.

**Recommendation.** Lead with existential-positive `T` (the match-completion
regime): the iso-invariance advantage is real, the comparison against MaxSAT is
clean, and existential-positive sentences arise naturally in knowledge-base
reasoning (query entailment, missing-answer problems, ontology realization).
The universal fragment is mentioned as a conceded regime, with an explicit note
that FPT branching already covers it optimally.

---

## 4. The algorithm in our representation and its feasibility gate

**The algorithm (abstract, alphabet-agnostic).**

1. Compute `w = w*_c(E(K))` via the canonical encoder.
2. For `r = 0, 1, 2, …` (cost levels, P6):
   a. Enumerate the Levenshtein ball `B_r(w)`.
   b. For each `w' ∈ B_r(w)`: decode `K' = S2H(w')` (P1 guarantees a
      connected structure); test `K' ⊨ T`.
   c. If any `K'` satisfies `T`, collect all such `w'` at this level and
      return the iso-classes of their decodings as the `d_I`-optimal solutions.
3. Terminate when a cost ceiling `C` is reached (see §5).

The result set is complete up to isomorphism by Theorem A: `w*_c(K'_1) =
w*_c(K'_2)` iff `K'_1 ≅ K'_2`, and the enumeration visits every iso-class
within radius `r` exactly once (up to the many-to-one collapse discussed in
P6).

**Feasibility under F0 (current `Σ_HG`): INFEASIBLE.**

Composing two measured facts:
- Under E2, a one-fact edit = `1 + a` structural elements (one incidence node +
  `a` hyperedges in the bipartite encoding).
- One structural edit moves `w*_c` by ≈30–50 % of the string on unanchored
  substrates (T-M4b, G2 sensitivity profile).

A one-fact repair is therefore a large fraction of the full string away in
`d_I`. Ball enumeration at feasible radii (say, `r ≤ 10` tokens) does not reach
any one-fact repair of a realistically sized KB. This is a feasibility failure,
not a quality one: the method does not work in F0, regardless of the sentence
shape.

**Feasibility under F4 (`Σ_FO`, decision D3′): EXPECTED FEASIBLE.**

The F4 alphabet introduces a native `FACT` token: one token = one ground fact.
Under F4, a one-fact edit is exactly a one-token edit, and the ball of radius
`r` is approximately "the set of structures reachable by at most `r` fact-edits
under iso". The measured ≈30–50 % drift disappears by design — **the alphabet's
unit of change matches the semantics' unit of change.** The open question is
whether the tie-complete encoder under F4 is feasible at KB sizes of interest;
gate G-L1 (labelled envelope measurement) settles it.

**Conclusion.** P-ENTAIL is on the critical path of D3′. Do not schedule
experiments before the alphabet decision.

---

## 5. Decidability and the fragment that restores termination

**Trakhtenbrot's theorem.** For arbitrary first-order `T`, finite satisfiability
is only semi-decidable. P-ENTAIL as posed (unbounded domain, arbitrary `T`) is a
**semi-decision procedure**: it finds a solution when one exists within a growing
ball and does not terminate when none exists at any finite cost. This is the
standard position of every finite model finder and must be stated, not hidden.

**Two fixes, both required in the paper.**

1. **Cost ceiling `C`.** Declare "find the `d_I`-nearest model of `T` within
   `r ≤ C` token edits." This converts the semi-decision procedure into a
   decision procedure for "solution within budget `C`". The domain bound follows:
   under F4, the maximum number of fresh constants introduced by a radius-`C`
   search is at most `C` (each `FACT` token with fresh arguments introduces at
   most one new constant per argument, bounded by `a·C`). So the domain never
   exceeds `|adom(K)| + a·C`.
2. **Restrict `T` to a decidable finite-model fragment.** For P-ENTAIL the
   natural choice is **Bernays–Schönfinkel** (`∃*∀*`, no functions, no equality
   required): it has the finite model property (so every satisfiable sentence has
   a finite model), it covers denial constraints, transitivity, most integrity
   axioms encountered in practice, and its finite-model theory is
   well-understood. FO² (the two-variable fragment) and the guarded fragment
   also have the finite model property and are alternatives if the axiom shapes
   require them.

   For existential-positive `T` specifically: termination is **immediate** — if
   `T = ∃x.φ(x)` is satisfiable at all (it always is: add fresh facts), then
   adding one fact that witnesses `φ` satisfies `T` and the ball at radius
   `|φ|` contains a solution. No decidability concern for this fragment.

**Paper commitment.** The article should commit to one of:
- Existential-positive `T` as the primary case (recommended, §3), with
  termination immediate.
- Bernays–Schönfinkel as the general case, with finite model property stated.
- Both: existential-positive as the core, Bernays–Schönfinkel as the
  "how far can we go" extension.

The universal/forbidden-pattern regime is handled by FPT branching, which
terminates independently by the branching-tree argument (depth ≤ `k`, branching
factor ≤ `|𝔐|` facts), so no decidability concern there either.

---

## 6. Baselines — pre-registered interpretation contract

Written before results, binding in both directions: no baseline removed for
winning, no baseline added to bury a loss. Follows the style of
`../competitors.md` §4.

| Baseline | Fragment | Expected outcome | What we measure regardless |
|---|---|---|---|
| **MaxSAT** (soft keep-atom + hard grounded `T`; BreakID/lex-leader for iso) | general | **wins on wall-clock**; expected to return optimal `d_SED` solution | iso-class duplicate count with and without symmetry breaking; `d_I` vs `d_SED` suboptimality gap |
| **ASP with weak constraints** (`clingo`/DLV) | general | similar to MaxSAT | same |
| **Kodkod / Alloy** (built-in sym-breaking, bounded scope) | general | closest existing iso-invariant tool; faster than us at small scope | iso-class duplicate count; suboptimality gap; scope limit comparison |
| **FPT bounded-search-tree branching** (Cai-style) | universal/forbidden-pattern `T` only | **wins on this fragment**; automatically iso-invariant | edit-budget comparison; we report this loss plainly |
| **Minimum-cost match completion** (PTIME CQ homomorphism) | existential-positive `T` only | **wins on wall-clock for fixed `T`**; NP-hard in `\|T\|` | same; we compare on iso-class completeness |
| **Exact `d_SED` oracle** (A∗ / LSAP alignment, existing HGED solver) | small instances | optimal `d_SED` solution; NP-hard in general | suboptimality gap: `d_SED(K, K'_{d_I})` vs `d_SED(K, K'_{d_SED})`; reported as a percentage |

**The measurement that runs regardless of who wins.** Following
`competitors.md` §2: count isomorphic duplicate results emitted by MaxSAT/ASP
with and without symmetry breaking, against our zero. This directly quantifies
what iso-invariance-by-construction provides and is independent of wall-clock
comparison.

**What survives after the losses are reported.** If wall-clock losses to
MaxSAT/ASP are as expected:
- Zero duplicate results, by construction, with no symmetry-breaking code.
- All `d_I`-optimal solutions up to isomorphism, not a single one.
- Every intermediate of a repair path is a decodable, inspectable structure
  (P1). MaxSAT/ASP and FPT branching do not supply decodable intermediates.
- The measured suboptimality gap: "replacing the NP-hard `d_SED` with our
  polynomial `d_I` costs X % on these instances."

---

## 7. Data — what T, what K, and where ground truth comes from

### 7.1 The source of theorems T

**ARB-derived KBs are not a source of T.** The ARB/Benson hypergraphs are
single-relation, symmetric structures with no axioms of their own (`data.md`
§4). They provide `K` (the structure to be repaired) but not `T` (the theorem
to satisfy). For P-ENTAIL, `T` must come from elsewhere.

Four sources, in preference order:

1. **TPTP library (FOF/CNF problems).** Community-standard first-order formulas;
   finite models exist for many of them and are small enough for our scope.
   `data.md` §2 proposes this as the primary source. A pre-processing step
   selects problems with known finite models (ATP status "Satisfiable" or "Open"
   with a model found by Mace4/Nitpick) and restricts to Bernays–Schönfinkel or
   existential-positive sentences.
2. **Algebraic axioms (hand-crafted).** Group axioms (universal Horn), semilattice
   axioms (∀x.x∘x=x, commutativity, associativity — all universal), transitivity
   (∀xyz.R(x,y)∧R(y,z)→R(x,z) — universal). These are the most controlled
   setting: the fragment, the expected algorithm (FPT or database repair), and
   the census ground truth are all known.
3. **Existential graph-query theorems (custom).** For the match-completion
   regime: `T = ∃x₁…xₖ. R(x₁,x₂) ∧ R(x₂,x₃) ∧ … ∧ R(xₖ₋₁,xₖ)` (a path of
   length `k-1`), or triangle existence, or a specific induced subgraph. Ground
   truth: a structure K that contains no such pattern; the minimum edit to
   introduce one is computable directly.
4. **Denial constraints from repair benchmarks** (`data.md` §5). Established
   benchmarks in the Arenas–Bertossi–Chomicki line include constraint sets over
   small relational instances; adapt those constraints as `T`.

### 7.2 Construction of K (the starting KB)

**Perturbation-from-model construction** (`data.md` §2): take a known model `𝔐`
of `T`, apply a known sequence of `t` fact-edits to produce `K` with `K ⊭ T`,
and record `t` as the ground-truth repair budget. Then run P-ENTAIL on `K` and
check: (a) the returned solution satisfies `T`; (b) its `d_I` cost is ≤ `t`;
(c) the `d_SED` cost of the returned solution is compared to `t`.

This is the analogue of the perturbation-ladder construction used in G2 (T-M5g)
and A4 (T-M5e). The edit budget is known by construction, so no oracle is needed
to verify correctness — only to measure suboptimality.

### 7.3 ARB-derived K for existential-positive T

For existential-positive `T = ∃x₁x₂.R(x₁,x₂) ∧ S(x₁,x₃)` (a pattern), an
ARB ego-network that does not contain the pattern is a valid starting `K`. The
minimum-cost match completion is then computable exactly (find the cheapest set
of atoms that witnesses the pattern). ARB provides many small KBs at known
arity. This is the cleanest feasibility demonstration and should be the first
experiment under P-ENTAIL.

### 7.4 What is not available

- ARB KBs as a source of first-order axioms (ruled out; §7.1).
- Large-scale KBs (`|D| + |F|` beyond the size envelope; §3 of `scope.md`).
  Under F0, the ceiling is `|D| + |F| ≲ 23`; under F4 and with labels it is
  higher (gate G-L1).
- OWL/DL knowledge bases: equality, function symbols, and role inclusions require
  encoding extensions not in scope (first pass excludes equality, §1 of
  `scope.md`).

---

## 8. Distance-mismatch resolution

All three PI ideas are written in `d_SED` (iso-invariant symmetric difference of
ground facts). We compute `d_I`. They are not the same distance. The resolution
adopted here is **option (c) from `risks.md` §1**: compute both and report the
gap.

**The experiment.** On instances where exact `d_SED` is computable (the existing
HGED oracle, small connected instances), run P-ENTAIL under both distances:

1. `d_I`-guided ball enumeration (our method): returns `K'_{d_I}`.
2. Exact `d_SED` search (MaxSAT or A∗ alignment oracle): returns `K'_{d_SED}`.

Measure and report:
- `d_SED(K, K'_{d_I})` vs `d_SED(K, K'_{d_SED})` — the suboptimality ratio.
- Whether `K'_{d_I} ≅ K'_{d_SED}` — whether the d_I-optimal repair is the
  d_SED-optimal one.

**What the measurement says.** The T-M4b results show that `d_I` and
structural distance are only moderately correlated (Spearman ρ = 0.622 on
6,921 pairs in E1′). For P-ENTAIL: a repair that is distance-1 in `d_SED` may
be far in `d_I` (the avalanche / drift argument, P2). The suboptimality gap
quantifies exactly this: it converts ρ = 0.622 from a descriptive number to an
operational bound on how much worse the `d_I`-guided repair is in semantic terms.

This is a TKDE-shaped result: *"replacing the NP-hard fact-distance with the
polynomial-time string-distance costs at most X % suboptimality on this class of
instances."* It is honest in both directions and is independent of who wins on
wall-clock.

---

## 9. Relationship to P-REPAIR

**One template, one implementation, two exhibited regimes.**

| Dimension | P-REPAIR (idea 1) | P-ENTAIL (this file) |
|---|---|---|
| Sentence `ψ` | `Σ` (axioms; e.g., integrity constraints) | `T` (theorem; e.g., existential fact pattern) |
| Typical shape | universal / denial | existential-positive |
| Primary algorithmic regime | FPT branching (`Σ` is forbidden-pattern) | match-completion (PTIME for fixed `T`) |
| Primary baseline | MaxSAT/ASP; FPT branching (strongest on that fragment) | MaxSAT/ASP; minimum-cost homomorphism |
| Our differentiator | zero iso-duplicate repairs; decoded intermediates | same |
| Distance mismatch | `d_I` vs `d_SED`; report gap | same |
| Data | TPTP axiom sets; ARB KBs as K sources | TPTP theorems; ARB patterns as T sources |
| Shared | encoding E, canonical form w*_c, ball enumeration (P6), cost ceiling, G-L1 gate, D3′ gate | ← same |

**Paper structure.** Present P-REPAIR and P-ENTAIL in one section titled
"nearest-model search" (or "entailment and repair"). The fragment taxonomy
(§3) is the shared preamble. The experiments are separate (different baselines,
different data). The iso-invariance measurement (duplicate count) is reported
once for both.

**P-ENTAIL is not a separate paper.** Its novelty is entirely derivative of
P-REPAIR's, plus the fragment taxonomy. There is no theorem unique to P-ENTAIL.
Splitting them would produce two very thin papers; together they constitute one
solid section.

---

## 10. Verdict

**Include as a short exhibit alongside P-REPAIR, gated on D3′.**

P-ENTAIL is worth including because:
- It demonstrates the generality of the nearest-model search template (any ψ,
  not only axiom sets).
- The match-completion regime (existential-positive `T`) is the natural use case
  for "what facts do I need to add to my KB so that my system can answer this
  query?" — a real TKDE-relevant workload.
- The suboptimality-gap measurement (§8) is the most operationally useful result
  in the logic program: it converts the correlation result (ρ = 0.622) into a
  practical number.

P-ENTAIL should **not** be the lead application because:
- The FPT regime concession (§3, universal `T`) leaves the iso-invariance
  argument without force on the most natural axiom shapes.
- Under F0 it is infeasible. The exhibit depends entirely on D3′ being both
  ratified and implemented.
- The wall-clock loss to MaxSAT/ASP is expected and must be reported; the
  surviving advantages (zero duplicates, decoded intermediates, suboptimality
  gap) are secondary in the framing.

**If D3′ is deferred or rejected**: P-ENTAIL drops out entirely. Nothing in the
current `Σ_HG` infrastructure supports it. State this plainly in the next PI
meeting.

**If D3′ is ratified**: P-ENTAIL and P-REPAIR are one combined experiment,
estimated at 4–6 weeks implementation + 1–2 weeks data + shared writing. The
TPTP perturbation corpus (existential-positive T, algebraic axioms) is the
target. ARB ego-networks provide K for the existential-pattern case.

---

## 11. Requested changes to the shared foundation

The orchestrator should merge these into the relevant shared files. **Do not edit
the shared files directly.**

1. **`risks.md` §2** — Clarify scope of the infeasibility statement. Current
   phrasing ("P-REPAIR and P-ENTAIL are gated on decision D3′") is correct but
   could be read as a permanent infeasibility rather than an alphabet-specific
   one. Add: *"Under F4 (`Σ_FO`), a one-fact edit is one token edit, so ball
   enumeration at radius r ≈ t fact-edits is designed to be feasible. The
   infeasibility is specific to F0/E2."*

2. **`data.md` §4** — The limitation of ARB KBs for P-ENTAIL should be stated
   as a design constraint, not a passing remark. Current text says "no interesting
   axioms of their own" in passing. Add explicitly: *"ARB KBs are not a source
   of theorems T for P-ENTAIL. T must come from TPTP, hand-crafted axiom sets,
   or existential graph-query specifications (§2 above and `ideas/idea2_entailment.md`
   §7)."*

3. **`scope.md` §1** — The note "Closed-world reading throughout — forced, since
   `w*_c ∘ E` encodes one structure, not a theory" should reference the Łoś–Tarski
   consequence explicitly: *"Under OWA, only existential-positive `T` is
   meaningful (Łoś–Tarski), and P-ENTAIL collapses to abduction — a well-studied
   problem that does not require our representation. CWA is the reading that makes
   arbitrary FO `T` meaningful and the problem non-trivial."*

4. **`problems.md` §P-ENTAIL** — The sentence "They are the same problem" is
   technically correct but should be followed immediately by the recommendation
   "Keep them as two experiments, not one, because the sentence shapes differ and
   that shape difference drives the entire algorithmic analysis." Currently this
   appears two paragraphs later; it should be the first sentence after the
   equivalence statement.

5. **`encoding.md` §3.1** — The "absolute vs relative addressing" tension is
   described as a research question to settle by measurement. This is correct;
   add a forward reference to this file stating that P-ENTAIL's feasibility
   analysis depends on this choice (absolute addressing eliminates drift; relative
   addressing preserves compactness but imports the ≈30–50 % single-edit penalty
   even under F4 if pointer runs remain).
