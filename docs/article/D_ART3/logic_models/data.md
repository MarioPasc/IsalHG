# Data for the logic program

*Vocabulary: [`vocabulary.md`](vocabulary.md). Companion to `../data.md`, which
carries the hypergraph corpora.*

---

## 1. Correctness fixtures — hand-written

Small `σ`-sentences and KBs whose answers are known by hand: failed
transitivity, failed antisymmetry, failed Euclidean property, "every element has
a distinct successor". Per problem:

- **P-MIN**: minimal countermodel known by hand.
- **P-REPAIR**: a KB violating a stated axiom, with the obvious one-fact repair.
- **P-ENTAIL**: a KB one fact short of entailing `T`.
- **P-MEDIAN**: `N = 3` structures with an obvious consensus.

These are unit tests, not experiments; they exist so a regression is visible.

## 2. TPTP — the community benchmark

**TPTP** (Sutcliffe, *The TPTP Problem Library and Associated Infrastructure*)
is the standard first-order library and the substrate every MACE-style finder is
evaluated on; using it is what makes the comparison legible to that community.
Relevant slices:

- Problems with status **`Satisfiable`** / **`CounterSatisfiable`** — by
  definition the ones with models / countermodels to find.
- The **CASC `FNT`** (First-order Non-Theorems) and `SAT` division lists — the
  model-finding competition tracks.
- The **quasigroup existence problems (QG1–QG7)**, historically the driver of
  SEM and Mace4 and exactly the high-symmetry stress case our invariant targets.

Selection rule must be stated in the paper (it is a filter, and filters are
methodological choices): relational, equality-free, small arity, capped
signature, and a finite-model-fragment restriction where termination is claimed
(`scope.md` §2).

**For P-REPAIR / P-ENTAIL specifically**, TPTP supplies the *axioms* but not the
*KBs*. Two options: derive a KB by perturbing a known model of the axioms (which
also gives a known repair budget, exactly the perturbation-ladder device the
article already uses), or take the KB from §4 and the axioms from TPTP.
**The perturbation route is preferred** because it yields ground truth: a KB
built by applying `t` fact-edits to a model of `Σ` has a repair of cost ≤ `t`
by construction.

## 3. Verifiable enumeration ground truth — algebraic census

For the census claim to be checkable, the enumeration must reproduce numbers
someone else published. Known non-isomorphic counts at small order (literature +
OEIS): **groups**, **semigroups** and **monoids**, **quasigroups / Latin
squares**. Plus the in-repo **Steiner triple systems** (`sts_catalog`, orders
3–15, 85 classes) — free, already vendored, already pinned by tests.

Reproducing published counts is the cleanest evidence that the enumeration is
exact and complete, independent of any performance claim.

## 4. Real KBs — the ARB collection re-read as ground facts

*This is the strongest data connection the logic program has, and it uses data
already on disk.*

The ARB/Benson collection is downloaded in full (28 datasets, 3.6 GB) at
`/media/mpascual/Sandisk2TB/research/ISAL/isalhg/data/arb_benson/` (see
`../data.md` §1 for the layout, the measured arity table and the tier list).

**A hypergraph is a knowledge base.** A hyperedge over `{c_1,…,c_a}` is the
ground fact `R(c_1,…,c_a)` of one symmetric relation `R`; a node label is a unary
predicate. So:

- **Ego-hypergraphs** (Qin et al., ICDE 2023, Definition 1 — implemented as
  `core/sparse_hypergraph.py::ego_network`) give **many small KBs over one
  signature**, which is exactly the input shape P-MEDIAN needs: `N` knowledge
  bases to reach consensus over.
- **The labelled family** (`walmart-trips`, `trivago-clicks`, senate/house
  bills and committees, contact-*) gives **typed** constants, i.e. genuine unary
  predicates rather than a trivial vocabulary.
- **Temporal snapshots** give an ordered sequence of KBs over the same
  signature — natural input for consensus-over-time and for P-REPAIR (repair a
  later snapshot against axioms extracted from earlier ones).

**Measured feasibility (arity half of G-D1, closed 2026-08-12).** Five datasets
have maximum simplex arity exactly 5 and need no filtering: `tags-stack-overflow`
(14.5 M), `tags-math-sx` (822 k), `tags-ask-ubuntu` (271 k),
`contact-high-school`, `contact-primary-school`. Under E1 these encode with
`k = 5`; under E2 with `k = 2`. **Open and binding:** the ego-net *size*
distribution and the `w*_c` wall-clock distribution — `n = |NEI(v)|` is what the
envelope constrains and it is not bounded by the arity result.

**Honest limitation.** These are **single-relation, symmetric** KBs: one
predicate, no argument order, no axioms of their own. They are excellent for
P-MEDIAN (consensus of many observed structures) and for the E1 encoding; they
are *not* a source of interesting first-order axioms. Axioms for P-REPAIR and
P-ENTAIL come from §2 or are written by us and stated as such.

## 5. Repair and merging benchmarks from the neighbouring literature

For P-REPAIR and P-MEDIAN there are established benchmark traditions worth
mining rather than reinventing — database repair under denial constraints and
functional dependencies (the Arenas–Bertossi–Chomicki line and its ASP/MaxSAT
successors), and belief-merging evaluation sets. **Status: to be surveyed by
L-LIT**; named here so the idea files check before building bespoke corpora.

## 6. Data gates

- **G-L1** — `w*_c` wall-clock on encoded structures across `(|D|, |F|)`, per
  surviving encoding. Blocks the entire logic scope.
- **G-D1 (size half)** — ARB ego-net size distribution and `w*_c` yield. Blocks
  the real-KB experiments.
- **G-L2 (new)** — for P-MEDIAN: the distribution of `N` and of KB size obtainable
  from a given ARB dataset at a given ego radius, i.e. *how many KBs of what size
  does a real dataset actually give us to reach consensus over?* Cheap; runs with
  G-D1.

## 7. Open data questions

- **DQ-L1.** For P-MEDIAN on ARB: what defines a *group* of KBs whose consensus
  is meaningful? Candidates: ego-nets of vertices sharing a label; snapshots
  within a time window; ego-nets at matched size. The choice is the experiment's
  design and must be justified, not defaulted.
- **DQ-L2.** Do ARB node labels enter (`d_I^Σ`) or are instances stripped
  (`d_I^⊥`)? For KBs, labels *are* unary predicates, so `d_I^Σ` is the honest
  choice — which means the logic program needs its own geometry measurement, as
  the article's existing tables are `d_I^⊥` (`vocabulary.md` §2, fact 3).
- **DQ-L3.** Perturbation-ladder construction for P-REPAIR ground truth: which
  edit types, and does the Qin cost model or a fact-level cost define the
  budget?
