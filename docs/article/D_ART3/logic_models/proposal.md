# Proposal — the logic program

*The premise, the thesis, and what the contribution is and is not. Vocabulary:
[`vocabulary.md`](vocabulary.md). Status: proposal, pending PI (D-ART3).*

---

## 1. What the contribution is not

**It is not isomorphism deduplication.** Two independent reasons, both decisive
and both stated in the paper's introduction:

1. `nauty` / `bliss` / Traces on the Levi reduction canonize faster than the
   tie-complete `w*_c` and are equally exact. A complete invariant is a complete
   invariant.
2. Finite model finders already handle symmetry — SEM's least-number heuristic,
   Paradox's static symmetry-breaking clauses, Kodkod's symmetry predicates —
   incompletely and **on purpose**, because complete rejection has historically
   cost more than the duplicates it removes. Arguing that we make it complete
   argues for a trade the field considered and declined, using the slower
   canonizer.

Deduplication is a *correctness precondition* of every algorithm here. Where its
throughput matters, a Levi-nauty key is a faster pluggable substitute inside our
own loop, and the paper says so.

## 2. What the contribution is

**A polynomial-time, alignment-free, provably metric, decodable distance on
isomorphism classes of finite relational structures — and the space it defines.**

The three PI ideas and the original countermodel problem are four instances of
one template (`problems.md` §0): nearest-point-in-a-definable-set, and 1-median.
In every published treatment of them the bottleneck is the same and is stated
explicitly in the PI's own source material: the natural iso-invariant distance
is alignment-based, NP-hard, and GI-hard at zero, so the algorithms are built
around *managing the alignment* — Hungarian GED approximations, permutation
synchronization, lex-leader symmetry breaking, alignment variables in an ILP.

`w*_c` deletes the alignment step. Canonicalize once per structure; every
pairwise distance is then a string comparison. What that buys, per problem:

- **P-MEDIAN.** The `N × N` matrix costs `N` canonicalizations plus `N²` string
  comparisons instead of `N²` NP-hard solves. The **medoid is a provable
  2-approximation of the generalized median because `d_I` is a metric**
  (Corollary A) — a guarantee the standard pipeline's Hungarian upper bound
  cannot claim. And the *generalized* median is a **median-string** problem in
  an ambient space where every point decodes (P1), so the graph literature's
  lossy final **reconstruction** step disappears.
- **P-REPAIR / P-ENTAIL.** "Nearest structure satisfying `ψ`" becomes ball
  enumeration around `w*_c(E(K))`. The **full symmetric group on fresh
  anonymous elements** — which `src/idea1.txt` identifies as the dominant
  symmetry and the thing that most needs breaking — **does not exist in this
  search space**: permuted fresh elements are the same canonical object.
- **P-MIN.** Exact enumeration by cost level with a verifiable census.

## 3. Thesis for the logic program

> Finite relational structures modulo isomorphism form a metric space whose
> distance is normally intractable. Writing each structure as a word makes that
> distance polynomial and alignment-free, makes the space's points enumerable
> and decodable, and thereby turns repair, entailment-forcing, and consensus
> from alignment problems into search problems in a space that can actually be
> searched.

This is the same thesis as the article's (`../proposal.md`: *a certificate is
not a space*), instantiated where it has the most leverage — because in the
logic setting the alternative distance is not merely awkward, it is NP-hard, and
the objects being compared are exactly what the user cares about.

## 4. How the logic program relates to the article's premise

The connection the author asked about — geometry → application — runs like this,
and every arrow is something already measured or provable:

| Article asset | What the logic program does with it |
|---|---|
| Theorem A (completeness) | makes `d_I` well defined on isomorphism classes **without a bijection search** — this is the whole contribution |
| Corollary A (metric) | licenses the medoid **2-approximation** for P-MEDIAN and triangle-inequality pruning everywhere |
| P1 / P6 (closure, decodability, ball enumeration) | makes ball search well posed for P-REPAIR/P-ENTAIL, and removes the **reconstruction** step from the generalized median |
| Ball growth + collapse (new, G-B1) | the branching factor of the repair search and the cost model of the neighbourhood query |
| Local sensitivity (≈30–50 % per edit) | says the search must be **cost-ordered, not distance-guided** — and, in the logic setting, forces the alphabet question (`encoding.md` §2) |
| Compactness (bits, r > 1 on 320/320) | the size of a stored frontier element / a stored KB fingerprint |
| E1′ (ρ = 0.622) + the envelope | becomes **operational**: it prices the suboptimality of using `d_I` instead of the intractable fact distance (`risks.md` §1(c)) |

The last row matters most for the article's coherence. Under D-ART2 the HGED
relation was a closing-discussion footnote. In the logic program it is a
*working quantity*: the gap between the polynomial surrogate and the intractable
objective, measured, on problems where that objective is what the user asked
for.

## 5. What must be true for this program to be worth doing

Stated as falsifiable preconditions, so the August meeting can check them:

1. **G-L1**: `w*_c` on encoded structures is cheap enough that KBs of realistic
   *shape* (if not size) are reachable. If encoded KBs cost like unlabelled
   random hypergraphs, the whole program is capped at toy scale.
2. **D3′**: either F0 suffices (only if P-MEDIAN leads) or the `Σ_FO` extension
   is scheduled. P-REPAIR and P-ENTAIL are infeasible under F0 (`risks.md` §2).
3. **L-LIT**: nobody has already put a tractable metric on isomorphism classes
   of finite structures and used it this way.
4. **The gap is reportable**: the `d_I` vs `d_SED` suboptimality is measurable on
   instances where the exact oracle runs. It is — the oracle exists.

## 6. Recommended shape

One problem developed fully, the others as instances of the template:

- **Lead with P-MEDIAN.** It runs on infrastructure we have, its guarantee is
  theorem-backed, it has real data today (ARB ego-networks are sets of ground
  facts), and it is immune to the small-perturbation weakness measured at
  T-M4b.
- **P-MIN** as the generation demonstration plus the verifiable census
  (published counts of small algebraic structures to reproduce).
- **P-REPAIR / P-ENTAIL** developed on paper here, scheduled behind D3′, and
  either included as a short instance or split into the follow-up paper.
