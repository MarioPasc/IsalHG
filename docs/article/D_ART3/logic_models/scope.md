# Scope — fragment, decidability, size envelope, in and out

*Vocabulary: [`vocabulary.md`](vocabulary.md).*

---

## 1. Logical fragment

**In (first pass).**
- Function-free, relational signatures. Constants and functions arrive by
  MACE-style flattening if needed.
- **Equality-free.** MACE-style tools treat `=` as a built-in congruence; our
  encoding has none. Adding equality means either axiomatizing it (expensive:
  congruence axioms blow up the ground problem) or extending the encoding.
  First pass excludes it and says so.
- Single-sorted. Multi-sorted signatures need F3 (`encoding.md`) and are out.
- Arities small enough for the encoding (see §3).
- **Closed-world reading** throughout (`vocabulary.md` §4) — forced, since
  `w*_c ∘ E` encodes one structure, not a theory.

**Out (first pass).** Equality, sorts, functions before flattening, infinite
domains, open-world entailment, probabilistic or weighted KBs.

## 2. Decidability — the boundary that must be stated

**Trakhtenbrot.** For arbitrary first-order `ψ`, finite satisfiability is
semi-decidable, not decidable. Consequences for each problem:

- **P-MIN, P-REPAIR, P-ENTAIL** are **semi-decision procedures** as posed. Ball
  enumeration / cost-level sweeping finds a solution when one exists and does not
  terminate when none does. This is exactly the position every finite model
  finder is in; it is stated, not hidden.
- Two ways to obtain termination, both standard, and the paper should use both:
  1. **Bound the search** — a cost ceiling `C` turns each problem into a
     decision procedure for "solution of cost ≤ `C`". For P-REPAIR the bound is
     principled rather than arbitrary: the incumbent bounds the fresh-element
     count, so the domain never exceeds `|adom(K)| + C` (`problems.md`).
  2. **Restrict `ψ` to a decidable finite-model fragment** — FO², guarded,
     Bernays–Schönfinkel `∃*∀*`, monadic. Bernays–Schönfinkel is the most useful
     here: it has the finite model property and covers denial constraints and
     most integrity axioms.
- **P-MEDIAN has no decidability issue at all** — there is no sentence. It is
  purely an optimization over a metric space. One more reason it should lead.

## 3. Size envelope — the binding practical constraint

Measured `w*_c` feasibility on **unlabelled random** hypergraphs: `k = 3` up to
`n ≈ 24` at low edge density (`n = 16` medium, `n = 8` high); `k = 5` only at
`n = 8`; `k = 7` and `k = 10` infeasible at every tested size.

Under E2 an instance has `n' = 1 + |D| + |F|`. Taken literally that caps us near
`|D| + |F| ≲ 23` — a KB of, say, 6 constants and 16 facts. **That is small**, and
it must be said plainly: our instances will be small even though the *problems*
are realistic.

**Two mitigations, one measured and one hypothesized.**
- *Hypothesized (gate G-L1).* The envelope came from unlabelled inputs. KB
  encodings are heavily labelled — predicate names, argument positions, unary
  predicate sets — and labels strengthen tie-breaking and shrink automorphism
  groups, so the tie-complete search should be far cheaper. The known
  counter-mechanism runs the same way (stripping labels can only make the search
  equal or slower, OD7's correction), so the direction is expected favourable.
  **Magnitude unknown. Measure before scoping.**
- *Structural.* F4 with a `FACT` token keeps `n = |D|` instead of `1 + |D| + |F|`,
  which is a first-order improvement in the binding parameter, not a constant
  factor. Another argument for D3′.

**Honest framing for the paper.** Small-scope search is not a defect in this
field — it is the working assumption of Alloy's small scope hypothesis and of
every finite model finder's competitive regime. But the claim must be *"exact,
iso-invariant search at small scope"*, never *"scales to real knowledge bases"*.
A reviewer will check this, and the ARB-derived KBs (`data.md`) are the honest
way to show real *provenance* at feasible *size*.

## 4. What is in scope for the article, and what is follow-up

**In scope (candidate, subject to the PI meeting).**
- One problem developed fully with baselines and a measured comparison —
  recommended **P-MEDIAN** (`README.md` §5).
- P-MIN as the generation demonstration and the verifiable census.
- The `Σ_HG` vs `Σ_FO` sensitivity measurement if D3′ adopts an extension.

**Follow-up / separate paper.**
- P-REPAIR and P-ENTAIL developed to competitive depth against MaxSAT/ASP
  encodings — this is an automated-reasoning contribution and belongs at
  IJCAR/JAR/AAAI unless it stays clearly subordinate to the representation
  claim.
- Equality, sorts, open-world entailment.
- Weighted and subset-minimal variants.

## 5. Scope risks

1. **Three ideas is more than one paper holds.** The PI's framing is that all
   three fit TKDE; the discipline that keeps them one paper is *one developed
   fully, the others stated as instances of the same template with a small
   demonstration each*. If all three are developed to depth, the paper becomes
   two.
2. **The logic material can swamp the representation claim.** The paper's
   contribution is the representation and the space; the logic problems are
   where the space pays. If the automated-reasoning content grows past roughly a
   third of the paper, the framing has drifted.
3. **The distance mismatch** (`risks.md` §1) is a scope risk as much as a
   technical one: if it forces us to report `d_I`-minimal repairs rather than
   fact-minimal repairs, the claim changes and the baselines change with it.
