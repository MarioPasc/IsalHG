# The four problems, stated uniformly

*Vocabulary is [`vocabulary.md`](vocabulary.md) and is binding. All problems are
posed **on isomorphism classes** of finite `σ`-structures, closed-world reading,
cardinality-minimal, function-free signature.*

---

## 0. The common form

Let `𝒮` be the set of isomorphism classes of finite `σ`-structures and let `d`
be a metric on `𝒮`. Three of the four problems are instances of one template:

> **Nearest point of a definable set.** Given `K ∈ 𝒮` and a first-order sentence
> `ψ`, find `argmin_{𝔐 ∈ Mod(ψ)} d(K, 𝔐)`.

and the fourth is the aggregation dual:

> **1-median.** Given `K_1,…,K_N ∈ 𝒮`, find `argmin_{𝔐 ∈ 𝒮} Σ_i d(𝔐, K_i)`.

Everything else — which `ψ`, which `d`, whether a query point exists — is a
parameter. Writing them this way is not cosmetic: it is what lets one
implementation (ball enumeration over a decodable ambient space, plus one
`⊨` test) serve all four, and it is what makes the distance choice the single
decision that governs the whole family.

---

## P-MIN — minimal countermodel *(the original idea, 2026-08-11)*

**Given** a sentence `φ`. **Find** `𝔐 ⊭ φ` minimizing
`cost(𝔐) = |D| + Σ_i |P_i^𝔐|`.

**Template position:** the degenerate case with **no query point** — the
objective is absolute size rather than distance to something. Equivalently:
nearest point of `Mod(¬φ)` to the empty structure, under a cost that counts
elements and facts.

**Character.** Pure generation: sweep cost levels upward, test each candidate.
No alignment, no query. The easiest of the four to implement and the hardest to
win on wall-clock (MACE-style finders do exactly this, with SAT underneath).

---

## P-REPAIR — nearest model of the axioms *(PI idea 1, `src/idea1.txt`)*

**Given** axioms `Σ` and a KB `K` with `K ⊭ Σ`. **Find**
`argmin_{𝔐 ∈ Mod(Σ)} d(K, 𝔐)`, with the domain allowed to grow or shrink.

**Template position:** nearest point of `Mod(Σ)`, query point `K`.

**What the PI's analysis establishes.**
- Domain **shrink** is free: it is just fact deletion under the active-domain
  reading (fork (a)), or a charged element deletion under fork (b).
- Domain **growth** is the unbounded direction and needs iterative deepening,
  bounded by the incumbent: if the best repair found costs `C`, no repair needs
  more than `C` genuinely participating fresh elements, so the domain never
  exceeds `|adom(K)| + C`. **This bound transfers to our setting unchanged** and
  is the termination argument for ball enumeration.
- The dominant symmetry in the standard encoding is the **full symmetric group
  on the fresh anonymous elements**, and breaking it well matters more than
  breaking `Aut(K)`. **In our search space that symmetry is absent**: permuted
  fresh elements are the same canonical object. This is the sharpest single
  statement of what iso-invariant search buys, and it is a claim we can measure
  (count the duplicate repairs a symmetry-broken MaxSAT encoding still derives,
  against ours which derives none).

**Literature position.** Symmetric-difference / **update repair** (Wijsen);
Katsuno–Mendelzon *update* rather than revision; the grow-with-fresh-elements
mechanism is the chase with labelled nulls, so for existential-rule `Σ` the
TGD-repair literature is the nearest neighbour.

---

## P-ENTAIL — nearest model of the theorem *(PI idea 2, `src/idea2.txt`)*

**Given** a theorem `T` and a KB `K` with `K ⊭ T`. **Find**
`argmin_{𝔐 ∈ Mod(T)} d(K, 𝔐)`.

**Template position:** identical to P-REPAIR with `ψ = T`. **They are the same
problem.** What differs is the *shape of the sentence*, and that is what decides
which algorithm wins:

| Shape of `ψ` | Regime | Best known method |
|---|---|---|
| existential-positive / conjunctive query | create a homomorphic image of the pattern | minimum-cost match completion; PTIME in data complexity for fixed query, NP-hard in query size |
| universal / forbidden-pattern (denial constraints, hereditary property) | destroy every witness | **FPT in the edit budget `k`** by bounded-search-tree branching (Cai; H-free edge modification) — and automatically iso-invariant, since the target class is closed under isomorphism |
| denial constraints / FDs | database repair | mature ASP and MaxSAT encodings; PTIME islands |
| additions only (monotone) | abduction: minimal `Δ` with `K ∪ Δ ⊨ T` | Eiter–Gottlob; Selman–Levesque for Horn; ALP/ATMS tooling |
| genuinely mixed FO | general | branch-and-bound over domain size around a constrained model finder |

**Keep P-REPAIR and P-ENTAIL as two experiments, not one**, precisely because
the sentence shapes differ: `Σ` is typically universal/denial (the FPT regime),
`T` typically existential-positive (the match-completion regime). One
implementation, two regimes, two sets of baselines.

**A decidability caveat that binds both.** For arbitrary first-order `ψ`,
finite satisfiability is only semi-decidable (Trakhtenbrot), so "is there a
finite model near `K`" has no general decision procedure. Ball enumeration is
therefore a **semi-decision procedure**: it finds a repair if one exists within
the growing radius, and does not terminate otherwise. Fix by bounding the domain
or restricting `ψ` to a decidable finite-model fragment (see
[`scope.md`](scope.md)).

---

## P-MEDIAN — the medianoid *(PI idea 3, `src/idea3.txt`)*

**Given** `K_1,…,K_N`. **Find** `argmin_{𝔐 ∈ 𝒮} Σ_i d(𝔐, K_i)`.

**Template position:** the aggregation dual. No sentence, `N` query points.

**What the PI's analysis establishes, and why it is the best fit of the three.**

1. **The hardness is entirely in the alignment.** Fix a bijection `σ_i` per
   input into a common reference domain; then
   `Σ_i d(𝔐, K_i)` decomposes per ground atom and the optimum is **per-atom
   majority vote**. Consensus is trivial; alignment is everything. It is the
   multiple-sequence-alignment phenomenon.
2. **This is the generalized median graph problem** (Jiang, Münger & Bunke,
   TPAMI 2001) — NP-hard — and, in belief merging, the model-based `Δ^Σ`
   operator of Konieczny & Pérez, whose standing assumption of a *rigid, named*
   vocabulary is exactly what isomorphism-invariance drops.
3. **The set medianoid (medoid) is a 2-approximation because the distance is a
   metric.** This is where our theory pays: Corollary A *proves* `d_I` is a
   metric, so the 2-approximation holds. The standard pipeline's
   Hungarian/bipartite GED is an **upper bound, not a metric**, so the same
   guarantee does not transfer to it. A guarantee our competitor's distance
   cannot claim is a rare and concrete advantage.
4. **The generalized median needs an ambient space, and ours is decodable.**
   The graph literature's route (Ferrer, Valveny, Serratosa, Riesen & Bunke)
   embeds graphs into a vector space, takes the vector median, and then
   **reconstructs** a graph — the lossy step. In `(Σ*, d_Lev)` the generalized
   median is a **median string**, it lives in the space, and `S2H` decodes it
   exactly. No reconstruction.
5. **It does not depend on small-perturbation class structure**, so it is
   immune to the failure mode measured at T-M4b.

**The honest counterweight.** The median string problem is itself NP-hard (Sim &
Park), so we trade one NP-hard problem for another — but for a *far* better
studied one, with standard approximation algorithms, and with the medoid
2-approximation available for free. And the `N²` distance computation, which
dominates in practice, goes from NP-hard-per-pair to string-comparison-per-pair.
That is the claim to measure.

---

## Cross-cutting: what each problem needs from the representation

| | complete invariant | metric | ambient decodable space | move operator | cost order |
|---|---|---|---|---|---|
| P-MIN | for the exact census | — | for generation | ✔ | ✔ |
| P-REPAIR | for iso-invariance without symmetry breaking | ✔ | ✔ (ball enumeration) | ✔ | ✔ |
| P-ENTAIL | same | ✔ | ✔ | ✔ | ✔ |
| P-MEDIAN | for the distance matrix | ✔ **(2-approx guarantee)** | ✔ **(no reconstruction step)** | for the generalized median search | — |

Every column is a property we have and the alternatives do not have jointly.
Every row is a problem the PI proposed. That coincidence is the argument for the
whole logic program.
