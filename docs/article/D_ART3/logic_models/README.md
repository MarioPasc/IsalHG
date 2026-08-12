# Logic models — the hub

*Replaces the monolithic `../logic_models.md`. Status: proposal, pending PI.
Last restructure 2026-08-12, after the PI contributed three extensions to the
original countermodel idea (raw material in [`src/`](src/)).*

---

## 1. What changed, and why this is now a folder

The original idea (2026-08-11) was: *every finite model of a first-order formula
is a labelled hypergraph, so search exhaustively for the smallest countermodel.*
The PI has since contributed **three extensions**, all of them closer to real
data-engineering workloads and all of them, in his words, a better fit for TKDE:

| # | Idea (PI) | Raw material | Formal shape |
|---|---|---|---|
| 1 | **KB repair.** A knowledge base contradicts a set of axioms `Σ`. Find the closest KB that satisfies `Σ`. Domain may grow or shrink. | [`src/idea1.txt`](src/idea1.txt) | nearest point of `Mod(Σ)` to a query point |
| 2 | **Entailment forcing.** A KB does not entail a theorem `T`. Find the closest KB that does. | [`src/idea2.txt`](src/idea2.txt) | nearest point of `Mod(T)` to a query point |
| 3 | **Medianoid.** Given `N` knowledge bases, find the consensus KB minimizing `Σᵢ d(M, Kᵢ)`. | [`src/idea3.txt`](src/idea3.txt) | 1-median of `N` points |

**They are one problem family.** Every one of them is a *metric query on
isomorphism classes of finite relational structures*: nearest-point-in-a-set
(1, 2), or 1-median (3). The original countermodel search is the fourth member —
*cheapest point of `Mod(¬φ)`, unconstrained by a query point*.

That is why they now share a folder: a common vocabulary, a common encoding, a
common scope, and a common risk register, with one file per idea developed on
top.

## 2. The observation that makes this IsalHG's problem

Read the three analyses in [`src/`](src/) for their **bottleneck** statements.
They agree, independently:

> *"Computing the iso-invariant distance is graph-edit-distance, which is NP-hard
> and even hard to approximate."* — src/idea2.txt
>
> *"Deciding distance zero (is M already an isomorphic model?) contains graph
> isomorphism, so it's GI-hard."* — src/idea2.txt
>
> *"Once the alignments are fixed, the exact median is just per-atom majority
> vote. **All of the hardness lives in choosing the joint alignment.**"* —
> src/idea3.txt
>
> *"Without symmetry breaking you'll re-derive the same repair under every
> permutation of the fresh pool and waste enormous effort."* — src/idea1.txt

In all three the difficulty is **alignment**: to compare two structures up to
isomorphism you must search over bijections. The recommended pipelines are built
entirely around managing that — Hungarian/bipartite GED approximations,
permutation synchronization, lex-leader symmetry breaking, BreakID, alignment
variables in the ILP.

**IsalHG removes the alignment step.** `w*_c` is a complete isomorphism
invariant, so

```
d_I(A, B) = d_Lev( w*_c(E(A)), w*_c(E(B)) )
```

is well defined **on isomorphism classes with no bijection search at all**:
canonicalize once per structure, then every pairwise distance is a string
comparison. Three consequences, one per idea:

- **Idea 3.** The `N × N` distance matrix costs `N` canonicalizations plus `N²`
  string comparisons instead of `N²` NP-hard GED solves. The set median is then
  a **provable 2-approximation** of the generalized median — provable because
  Corollary A gives us the triangle inequality, which the Hungarian GED
  *upper bound* used by the standard pipeline does not have. And the
  *generalized* median is a **median-string** problem in an ambient space where
  every point decodes (P1) — so the "embed → median in vector space →
  **reconstruct**" pipeline of the generalized-median-graph literature loses its
  lossy final step.
- **Ideas 1 and 2.** "Nearest structure satisfying `Σ`" becomes ball enumeration
  around `w*_c(E(K))`: grow the radius, decode every point (total decoder),
  test `⊨ Σ`. The fresh-element symmetric group that `src/idea1.txt` calls the
  dominant symmetry **does not exist in this search space** — permuted fresh
  elements are the same canonical object.

## 3. The problem that must be solved first, stated up front

**`d_I` is not the distance the three ideas are written in terms of.** They all
use symmetric difference of ground atoms (Dalal distance lifted to isomorphism
classes), i.e. structure edit distance. We have measured our relation to that
distance: Spearman ρ = 0.622 on the E1′ mini-corpus, an unconditional but very
loose envelope, and a proof-backed argument that **no bi-Lipschitz relation is
achievable**. So `d_I`-minimal is not fact-minimal.

Worse for ideas 1 and 2 specifically: the measured single-edit response of
`w*_c` is **≈30–50 % of the string** on unanchored substrates. If one ground
fact costs a third of the string, then a one-fact repair sits far away in `d_I`,
and ball enumeration at feasible radii will simply not find it.

**This is why the alphabet question is not optional here.** A `Σ_FO` in which
one ground fact is one token (design option F4, [`encoding.md`](encoding.md))
is not a refinement — it is the precondition that makes ideas 1 and 2 work at
all, and it attacks the avalanche at its root. The three ideas *motivate* the
alphabet redesign, and the alphabet redesign is what makes the three ideas
feasible. That reciprocity is the spine of this folder.

The honest resolutions, in the order they should be attempted, are in
[`risks.md`](risks.md) §1.

## 4. Reading order

**Shared foundation — read before touching any idea file.**

| File | Holds |
|---|---|
| [`proposal.md`](proposal.md) | the premise, the thesis for the logic program, what the contribution is and is not |
| [`vocabulary.md`](vocabulary.md) | **the shared glossary**: structures, KBs, the distance family, cost forks, CWA/OWA. Every idea file uses these names |
| [`problems.md`](problems.md) | the four problems stated uniformly (P-MIN, P-REPAIR, P-ENTAIL, P-MEDIAN) and how they relate |
| [`encoding.md`](encoding.md) | E1/E2 into `Σ_HG`, and the `Σ_FO` design space (F0–F4) with costs |
| [`scope.md`](scope.md) | FO fragment, decidability limits, the measured size envelope, what is in and out |
| [`data.md`](data.md) | TPTP, algebraic census ground truth, ARB-as-KBs, repair benchmarks |
| [`competitors.md`](competitors.md) | baselines per problem, and the comparisons conceded in advance |
| [`related_work.md`](related_work.md) | belief revision/merging, database repair, generalized median graph, finite model finding, GED |
| [`risks.md`](risks.md) | the honest register — the distance mismatch, scale, decidability, what must be measured |

**Per-idea development** (one file each, developed against the foundation):

| File | Idea |
|---|---|
| [`ideas/idea1_repair.md`](ideas/) | KB repair — nearest model of `Σ` |
| [`ideas/idea2_entailment.md`](ideas/) | entailment forcing — nearest model of `T` |
| [`ideas/idea3_median.md`](ideas/) | medianoid — consensus of `N` KBs |

## 5. Standing recommendation on scope

**Idea 3 is the strongest of the three and should lead.** Reasons, in order:

1. It needs only the pairwise-distance matrix plus an ambient space — **both
   already built** (the `metric_space/` harness, the `D.npy` caches, the
   competitor representations).
2. Its central guarantee is *theorem-backed by work we have already done*: the
   medoid is a 2-approximation **because `d_I` is a metric** (Corollary A), and
   the standard pipeline's Hungarian GED approximation is not a metric, so that
   guarantee does not transfer to it. This is a rare case where our proof buys a
   concrete algorithmic property a competitor cannot claim.
3. It is an *aggregation* task, so it does not depend on the small-perturbation
   class structure that the A2/A3 measurements showed we lack.
4. The generalized-median-graph literature's standard method ends in an
   approximate **reconstruction** step; ours does not, because the alphabet is
   closed and `S2H` is total.
5. Data exists today: ARB ego-networks *are* sets of ground facts.

Ideas 1 and 2 are the more ambitious pair and are gated on the alphabet
decision (§3). They should be developed, priced, and then scheduled behind
idea 3 unless the `Σ_FO` work lands early.

## 6. Status

- The PI has asked for a **videoconference in the last week of August** to
  settle this. This folder is the material for that meeting.
- Nothing here is ratified. `../../PROPOSAL.md` and the rest of the active
  article scope are unchanged; D-ART3 remains pending
  (`../../DEVELOPMENT/DECISIONS.md`).
