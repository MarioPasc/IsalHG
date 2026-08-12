# Encoding — structures as words, and the alphabet question

*Vocabulary: [`vocabulary.md`](vocabulary.md). This file carries decision **D3′**,
which after the three PI ideas is the largest technical decision in the rescope.*

---

## 1. Two encodings inside the current `Σ_HG`

### E1 — direct (symmetric fragment, arity-native)

`V = D`. The vertex label of `d` is the set of unary predicates true at `d`,
encoded as one composite symbol (the device already used for multi-label ARB
nodes, decision D2). Each fact `P_i(d_1,…,d_a)` with `a ≥ 2` becomes the
hyperedge `{d_1,…,d_a}` with edge label `i`. `k = max_i a_i`.

**Faithful** — `𝔐 ≅ 𝔑 ⇔ E1(𝔐) ≅ E1(𝔑)` — **only when** every predicate of
arity ≥ 2 is symmetric and its facts have no repeated arguments. Unary
predicates ride on vertex labels because `Σ_HG` has no arity-1 hyperedge.

### E2 — anchored incidence (general, arity 2)

`V = {⊤} ⊎ D ⊎ F` where `F` is the set of true ground atoms of arity ≥ 1 and
`⊤` is a distinguished **anchor**. Labels: `anchor`;
`dom:<sorted unary predicates true at d>`; `fact:<predicate name>`. Edges: for
each fact `f = P_i(d_1,…,d_a)` and each position `p`, the edge `{f, d_p}`
labelled `pos:p`; plus `{⊤, d}` labelled `dom` for every `d ∈ D`. `k = 2`.

**Faithful in general.** Labels pin the three-way vertex partition, fact labels
pin the predicate, edge labels pin the argument position, and repeated arguments
are separated by their position labels. The anchor exists because D-CONN1
restricts the article to connected hypergraphs while a bare element is
semantically load-bearing (it witnesses `∃x ¬P(x)`, and under fork (b) it is a
charged object) and cannot be dropped.

**Size.** `n' = 1 + |D| + |F|`, `m' = |D| + Σ_{f ∈ F} arity(f)`.

**Corollary (the bridge).** Under either encoding `w*_c ∘ E` is a complete
isomorphism invariant of finite relational structures and `d_I` is a metric on
their isomorphism classes — a corollary of Theorem A, requiring no new proof.

## 2. Why the reduction is not good enough for the three new ideas

The reduction was designed so Theorem A would transfer untouched. That was the
right instinct for P-MIN and it is **the wrong trade for P-REPAIR and
P-ENTAIL**, for a reason that is measured rather than aesthetic.

- **The unit of change is not the unit of encoding.** In E2 a single ground fact
  is one vertex and `a` edges, so a one-fact repair moves `1 + a` structural
  elements. In E1 it is one hyperedge, which is better, but the fragment is
  restricted.
- **And the measured single-edit response of `w*_c` is ≈30–50 % of the string**
  on unanchored substrates — the drift/avalanche result. Composing the two: a
  one-fact repair sits a *large fraction of the string* away in `d_I`.
- **Therefore ball enumeration at feasible radii will not find one-fact
  repairs.** P-REPAIR and P-ENTAIL are ball-enumeration problems. This is not a
  quality concern, it is a **feasibility** concern: the method does not work in
  the current alphabet.
- **E2 also inflates the ambient space.** `n' = 1 + |D| + |F|` pushes a KB with
  8 constants and 20 facts to `n' = 29`, already past the measured `w*_c`
  envelope (`k = 3` → `n ≈ 24` at low density) — though the envelope was measured
  on *unlabelled random* inputs and heavy labelling should help substantially.
  Gate G-L1 settles it.

The three PI ideas therefore *force* the alphabet question that the earlier
draft deferred.

## 3. `Σ_FO` — the design space (decision D3′)

Nothing is frozen except by choice. **D-TA2 fixed *which* tie-complete lex-min
is canonical for `Σ_HG`; it did not decide that `Σ_HG` is the only alphabet.**

| Option | Change | Consequence |
|---|---|---|
| **F0** — status quo | reduction E1/E2 into `Σ_HG` | zero new theory; distorted geometry; `n'` inflation; **ball search infeasible for P-REPAIR/P-ENTAIL** |
| **F1** — ordered `V`/`C` | construction tokens take an argument-order field | ordered relations native, arity stays the predicate's own; tie-break cascade grows one level |
| **F2** — incidence labels | each (vertex, edge) incidence carries a label | strictly more expressive than F1; deepest change to the tie-break (canonical form must compare incidence multisets) |
| **F3** — sorted/typed vertices | a sort field on new vertices | only needed if multi-sorted logic enters scope (currently out) |
| **F4** — **native `FACT` token** | one token per ground fact: `F[P; p_1…p_a]` over pointed vertices, predicate symbol as a field | **one token = one ground fact.** `cost(𝔐)` and token count align almost exactly; a one-fact edit is a one-token edit; the ball of radius `r` becomes approximately "structures within `r` fact-edits" |

**F4 is the recommendation**, and the three new ideas are the argument for it.
It repairs exactly the defect that makes P-REPAIR and P-ENTAIL infeasible under
F0, and it attacks the avalanche where it originates: an alphabet whose unit of
change matches the semantics' unit of change is the right starting point for a
locally stable canonical form.

### 3.1 The residual design tension inside F4 — absolute vs relative addressing

A `FACT` token still names its operands. Two choices, and they trade off:

- **Relative (pointer) addressing**, as today: operands are pointer positions
  reached by `P`/`N` runs. Compact, incremental, and it is what makes the bits
  result hold — but it is the source of **drift**, so a one-fact edit still
  perturbs the pointer runs around it.
- **Absolute addressing**: operands named by an iso-invariant vertex key (e.g.
  the vertex's position in the canonical order). Stable under edits — a one-fact
  edit is genuinely one token — but the operand field is now `O(log n)` wide and
  the encoding loses the incremental character that gives it compactness, and the
  canonical order must be computed before the string can be written, which
  changes the shape of the encoder.

**This is a sharp, measurable research question, and it is the most interesting
piece of new theory the logic program generates.** It should be settled by
measurement (single-edit response and compression ratio under both), not by
argument.

**Sharpened 2026-08-12 by the P-ENTAIL development.** The addressing choice is
exactly what determines the **ambient reach distance** `d_amb`
(`vocabulary.md` §2.1), which is what governs whether ball enumeration works for
P-REPAIR and P-ENTAIL:

- **Absolute addressing** ⇒ one ground fact is one token *with no preceding
  pointer moves*, so `d_amb = 1` per fact, exactly. Ball enumeration becomes
  trivially feasible and the search radius is the fact budget.
- **Relative addressing** ⇒ `d_amb = 1 + (CDLL displacement)`, so feasibility
  depends on how far the fact's vertices sit from the pointer trajectory. This
  is measurable *today, under F0*, by gate **G-L3** — and G-L3's answer is also
  the quantitative case for or against absolute addressing.

So the two questions are one question, and one cheap probe answers both. Run
G-L3 before deciding D3′.

### 3.2 The honest price of a new alphabet

1. **Theorem A must be re-proved** for `Σ_FO`. Its structure — iso-invariant
   seed set, tie-complete branching over an iso-invariant token order, shortlex
   lex-min — is **alphabet-parametric**, so the argument should port; each new
   token field adds cases. Real, bounded, and the existing proof volume is the
   template.
2. **P1/P6 must be re-established.** Every new token must preserve "every word
   decodes to a connected object": F4's `FACT` token needs the `i ≥ 1` analogue
   (at least one operand already present) or a companion anchoring rule.
3. **The encoder must be re-implemented**, Python and C++. The largest
   engineering item, and what makes D3′ a scheduling decision rather than a
   writing decision.
4. **The geometry pipeline must be re-run** — and this is *cheap and already
   built*: the harness consumes a `D_rep` matrix and is representation-agnostic.
   A sweep, not a project.
5. **Frozen results become alphabet-scoped.** E1′ (ρ = 0.622) and the bits
   result (r > 1 on 320/320) are statements about `Σ_HG` and stay true of it.
   Nothing is invalidated; things are *scoped*.

### 3.3 The recommended route — conservative extension

Design `Σ_FO` so that it **degenerates to `Σ_HG` on the unlabelled hypergraph
fragment**: every new field has a default value on which the token reduces to
its current form. Then every frozen `Σ_HG` result remains a result about the
fragment, Theorem A extends rather than restarts, and the alphabet change
becomes a **measurement** rather than a bet:

> **Does aligning the token with the unit of semantic change reduce the ≈30–50 %
> single-edit response?**

That measurement is publishable content on its own, and it is the most direct
empirical attack the article has on the avalanche.

## 4. What each problem needs from the encoding

| | needs faithful `E` | needs one-fact ≈ one-token | needs small `n'` | verdict under F0 |
|---|---|---|---|---|
| P-MIN | ✔ | helpful | ✔ | **feasible** — generation by cost level does not depend on locality |
| P-REPAIR | ✔ | **required** | ✔ | **infeasible** — see §2 |
| P-ENTAIL | ✔ | **required** | ✔ | **infeasible** — see §2 |
| P-MEDIAN | ✔ | helpful, not required | ✔ | **feasible** — the medoid needs only the distance matrix; the generalized median search benefits from locality but the set median does not |

This table is the scheduling argument of the whole folder: **P-MEDIAN and P-MIN
can proceed today under F0; P-REPAIR and P-ENTAIL are gated on D3′.**
