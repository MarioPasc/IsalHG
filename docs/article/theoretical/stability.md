# Stability of the IsalHG hypergraph metric

**Status:** ACTIVE. This document holds the paper's
**foundation** (§1 completeness → metric — Theorem A + Corollary A, the only
formal theorem/corollary pair the article states) and the **HGED-relation
analysis** (§2–§4) that the closing discussion compresses. Since the v3 rescope
(PROPOSAL §1, pivot 2) Theorem B is **not** a pillar: the article states only
the length lemma and the unconditional envelope as short propositions, argues
the impossibility of a bi-Lipschitz proxy in prose (with the drift/avalanche
mechanisms named and measured), and shows one exact-HGED correlation figure
(ours only). Everything else in §2–§4 — the conditional bound B-cond, its five
hypotheses, the coherence classification — is the *internal analysis record*
backing that discussion and potential follow-up work, not article claims. The
geometry characterization lives in `geometry.md`; the old §5 here is a
cross-reference.

Notation. `H` a hypergraph; `w*(H)` its canonical H2S string over `Σ_HG`;
`d_I(H,H') := d_Lev(w*(H), w*(H'))` the induced hypergraph dissimilarity (raw
Levenshtein, matching the IsalGraph precedent). `k` = max arity, `Δ` = max
vertex degree, `n=|V|`, `m=|E|`. `HGED(H,H')` = hypergraph edit distance under
unit topology costs (edit ops: vertex ins/del, hyperedge ins/del, incidence
add/remove); NP-hard, exact only at small scale.

---

## 1. Foundation: completeness ⇒ metric (port of IsalGraph Thm 1 / Cor 1)

**Theorem A (Completeness).** `w*(H1) = w*(H2) ⇔ H1 ≅ H2`.

- Status in IsalGraph: **proved** (their Theorem 1) — for their *exhaustive /
  triplet-pruned* canonical searches, which branch over every tied candidate.
- Status in IsalHG: **RESOLVED**, with a split verdict.
  Full proof + counterexamples:
  `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/theorem_a_completeness.{tex,pdf}`.
  - **(⇒) proved unconditionally** for every variant (round-trip soundness of
    S2H), over the *augmented fingerprint* `F(H) = (ℓ_max(H), w*(H))` — the
    string alone never records the seed vertex's label, so on non-trivial
    vertex vocabularies the bare string is incomplete (2-vertex counterexample;
    backend false positive). Trivial vocabulary (all corpora to date): `F ≡ w*`.
    **Implemented:** `core.canonical.canonical_fingerprint`
    returns `F(H)`, `IsalHGBackend.fingerprint` serialises it, and `d_I` takes
    the distance over the seed-label-prefixed token sequence (Corollary A).
    The seed label is recovered as the one vertex label of `H` that `w*` never
    emits, so the derivation is independent of the seed cascade; under both
    production cascades it is the label all seeds share.
  - **(⇐) FALSE for the implemented greedy variants** (`greedy_min`,
    `greedy_min_nbrdeg`, `exhaustive`): their residual V-tie-break by raw edge
    id makes `w*` a function of the *presentation* — a machine-verified n=4,
    m=4 counterexample (primal graph K4, constant η) yields two different `w*`
    for two edge orderings of the *same* hypergraph. The historical property
    suite missed it because `permute` preserves edge insertion order.
  - **(⇐) proved for the tie-complete encoder** `"canonical"`
    (branches over the full η-tie set, `tie_branch=True`;
    execution-forest bijection, the IsalGraph Step-2 argument done right).
    **Theorem A holds for `w*_c := w*_canonical`**; empirically backed
    (150/150 shuffle+relabel invariance; biconditional == pynauty under
    Hypothesis; pinned regression tests in
    `tests/{unit/core/test_canonical_encoder,property/test_completeness}.py`).
    Available in C++ (native `AlgorithmVariant::GreedyMinComplete`,
    byte-identical to the Python reference on 3,344 per-seed comparisons):
    `w*_c` costs 6.4 ms on the Fano plane and 1.1 s on GQ(2,2), so every
    downstream `d_I` computation runs on `w*_c` at corpus scale.
    **Package default:** `canonical_string`,
    `canonical_fingerprint`, `IsalHGBackend`, and `IsalHGLevenshtein` all
    compute `w*_c` unless an algorithm is explicitly overridden
    (`ISALHG_ALGORITHM` env var preserved for the preprint pipeline).
    Measured on the designs, `w*_greedy = w*_c` on Fano and STS(9)
    (automorphism-coherent ties) but **differs on the cyclic C13 and
    GQ(2,2)** — the greedy string is not canonical even on vertex-transitive
    designs.

**Frozen definition of `w*_c`.** `w*_c` is the
**unpruned** tie-complete lex-min: the κ-minimum over the *full* residual tie
set `T(σ)` and all label-respecting orderings, exactly as implemented by the
Python reference (`tie_branch=True`) and the C++
`AlgorithmVariant::GreedyMinComplete` (variant 7). Refining `T(σ)` with an
iso-invariant key ρ (proof Lemma 6.1) preserves *completeness* but returns a
*different* canonical form — a κ-minimum over a proper subset of `T(σ)` need
not equal the κ-minimum over `T(σ)` — so ρ-refinement forks the definition and
is not sanctioned, before or after tables exist. The only value-preserving
speedup is **stabiliser-orbit pruning** (proof Proposition 6.0: tied branches
related by an automorphism fixing `dom(μ)` pointwise have equal completions),
which also attacks the actual cost — automorphism redundancy on
vertex-transitive designs, where every tied candidate carries the same value
under *any* iso-invariant key. Regression pins in
`tests/unit/core/test_wstar_c_frozen.py` fix `w*_c` on {Fano, STS(9), the
cyclic partial C13(0,1,3), the n=4 counterexample} (fast) and on both true
STS(13)s (slow marker); a refinement that changes the value fails
loudly.

**Corollary A (Metric).** With Theorem A for `w*_c`, `d_I(H,H') :=
d_Lev(w*_c(H), w*_c(H'))` is a metric on isomorphism classes (per fixed `k`
and vocabulary): non-negativity and symmetry from `d_Lev`; identity of
indiscernibles from Theorem A; triangle inequality inherited from `d_Lev`.
Direct port of IsalGraph Corollary 1. **All downstream metric-space claims and
Theorem B must be stated over `w*_c`**, not the greedy `w*` (which stays a fast
one-sided heuristic: equal strings still certify isomorphism, and it is exact
on edge-order-preserving pipelines and on automorphism-coherent-tie inputs
like the design fixtures — Fano verified `w*_greedy = w*_c`).

**Remark (Label-conditional metric family).** For each fixed `k`, `h`, and
vocabulary `Σ = (Σ_V, Σ_E)`, the metric `d_I^{k,h,Σ}` is a metric on
isomorphism classes of connected `Σ`-labelled hypergraphs of arity ≤ k, where
isomorphism means *label-preserving* isomorphism — a bijection on vertices that
simultaneously preserves all hyperedges and all vertex and edge labels. The
proof is immediate from Theorem A: Theorem A is stated for arbitrary `Σ` (the
augmented fingerprint `F(H) = (ℓ_seed, w*_c(H))` is computed under any
`LabelVocabulary`), and the three metric axioms of Corollary A carry through
per fixed `(k, h, Σ)` with label-preserving isomorphism in place of plain
isomorphism. Under the trivial vocabulary `Σ = (⊥, ⊥)`, label-preserving
isomorphism reduces to plain structural isomorphism, and `d_I^{k,h,⊥}` is the
structural metric on unlabelled hypergraphs. Members from different vocabularies
are metrics on different isomorphism-class domains and are therefore
incomparable: their values must not be pooled or directly compared in one
distance matrix or MDS embedding.

**Index family.** The metric `d_I` depends on the pointer count `k` (which
caps the maximum supported arity), the structural-tuple depth `h` (depth of
the `xi`/`eta` tuples, default 3), and the vertex and edge vocabulary sizes
(the label universe `Σ_V × Σ_E`).  The correct name is the *family*
`{d_I^{k,h,Σ}}`: values from different `(k, h, Σ)` triples lie in
incomparable metric spaces and must not be mixed in one distance matrix or
MDS embedding.  `IsalHGLevenshtein` enforces a shared `k` within each
comparison (pair maximum in `pairwise`, corpus maximum in `matrix`, or a
user-supplied fixed `k`); the paper must state `(k, h, vocabulary)` once when
introducing `d_I` and use the same triple throughout.  Domain restriction:
`d_I` is defined only for `n ≥ 1`; the empty hypergraph is excluded because
`w*_c(∅) = ""` is indistinguishable from `w*_c(•)` (the single vertex),
breaking identity of indiscernibles (`DegenerateHypergraphError` in code).
The normalized ablation `edit/max_len` is a *dissimilarity*, not a
metric: it violates the triangle inequality (Marzal & Vidal, IEEE TPAMI
15(9), 1993; pinned witness triple in
`tests/unit/metric_space/test_isalhg_levenshtein.py::TestNormalizedNonMetric`).

**Greedy `d_Lev` caveat.** On the greedy variants `d_Lev` is not even
well-defined on isomorphism classes (presentation-dependent); per fixed
presentation it is at best a pseudometric. The paper must not use it for the
metric claim.

---

## 2. Theorem B (Stability) — the faithfulness capstone

*Since the v3 rescope Theorem B is **discussion material, not a pillar**. The
clean bound is conditional (five hypotheses, two failing generically), so what
the article keeps is the subset that is unconditionally true or honestly
negative: the length lemma, the envelope (B-worst), and the two named, measured
deviation mechanisms (drift, avalanche) that explain why no clean Lipschitz
bound exists — which in turn justifies validating usefulness directly on task
metrics (the paper's own program, PROPOSAL §5). The conditional analysis below
(§2.1–§3) is retained as the record that grounds those mechanisms and as the
starting point for any follow-up paper. Value inventory:
`stability_reformulations.md` §2.*

**Target statement.** There is an explicit constant `C(k,Δ)` such that for all
hypergraphs `H, H'`
```
        d_I(H, H') ≤ C(k, Δ) · HGED(H, H').                     (Lipschitz / upper bound)
```
i.e. structurally close hypergraphs have close canonical strings. This was the
**v2 target statement**. The analysis below establishes it only under five
hypotheses, two of which fail generically (§3); the v3 article therefore states
the unconditional envelope instead and treats (★) as the mechanism map behind
the discussion's drift/avalanche prose — not as a claimed bound.

**Why the upper bound is the useful side.** A lower bound
`d_I ≥ (1/C')·HGED` would say "far strings ⇒ far structure" (discriminativity);
useful but secondary. The applications need the *upper* bound: that the map
`H ↦ w*(H)` does not amplify small structural perturbations into large string
perturbations. The competing canonical-form engines (nauty/bliss) provably lack
this (§3, avalanche is their *generic* behaviour) — that contrast is the paper's
edge.

### 2.0 Positioning against prior bounds (from `../RELATED_WORK.md`)

The theorem is not built in a vacuum — three precedents supply the scaffold and
justify its one-sided form:

- **Proof template — Tree Mover's Distance** (Chuang & Jegelka, NeurIPS 2022):
  bounds a *representation* distance by a *structural* graph distance, proved by
  bounding the change in the local computation tree by the number of affected
  edges. Our §2.1 single-edit reduction is the hypergraph analogue (canonical
  string in place of GNN output).
- **A proved piece of the chain — hypergraph co-optimal transport** (Chowdhury
  et al. 2023): the Levi/bipartite expansion `H ↦ B(H)` is Lipschitz with an
  **arity-`k`-dependent constant**. Our `C(k,Δ)` inherits this `k`-dependence;
  since IsalHG already operates on `B(H)`, this bounds part of our pipeline for
  free.
- **Why only an upper bound — WL/canonical non-lower-Lipschitzness** (FSW-GNN,
  LoG 2025; WL-distance, Chen et al. 2023): canonical/WL representations are
  *generically not lower-Lipschitz* (non-iso hypergraphs can have vanishing
  representation distance at fixed structural distance). So a bi-Lipschitz bound
  is provably out of reach for arbitrary canonical encodings; the **upper bound
  is the strongest achievable form**, and pursuing it is not a concession.

HGED is the one from Qin et al. (ICDE 2023) **verbatim** — its Definition-3
empty-shell taxonomy, all ops unit cost, so deleting/inserting an arity-`a`
hyperedge costs `a+1` — adopted as the article's single official cost model
(an interim whole-edge variant in which a whole-hyperedge insert/delete was
one unit op is superseded). The right-hand side of Theorem B is therefore a
citable object with no convention caveat. Two consequences, both favourable:
(a) the §2.1 single-edit reduction decomposes an optimal HGED path into
Qin's *atomic* ops — each strictly more local than a whole-edge op (a
`k`-edge never appears or vanishes in one step), so the per-op sensitivity
`s(e)` to bound involves at most one incidence, one isolated vertex, one
empty shell, or one label; (b) the perturbation-ladder guarantee is restated
as `HGED ≤ budget` where the budget is the accumulated Qin cost of the
applied generator edits (`core/sparse_hypergraph.py::qin_edit_cost`),
preserved by construction. The oracle is `exact_hged` (LSAP branch-and-bound);
the paper's own HGED-BFS (`qin_hged`) computes the same metric and anchors
fidelity on Example 2 (`HGED(EGO(u4), EGO(u5)) = 6`); a property test asserts
the two solvers agree exactly.

### 2.1 Reduction to a single edit

By an optimal HGED edit path `H = H_0 → H_1 → ⋯ → H_t = H'`, `t = HGED(H,H')`,
and the triangle inequality for `d_Lev`,
```
        d_I(H, H') ≤ Σ_{i=1}^{t} d_I(H_{i-1}, H_i) ≤ t · max_e s(e),
```
where `s(e) := d_I(H, H⊕e)` is the *single-edit sensitivity*. So
**`C(k,Δ) = max over edit types of s(e)`**, and the whole theorem reduces to
bounding the single-edit sensitivity.

### 2.2 Anatomy of a single edit's sensitivity

Decompose `s(e)` into two contributions to the change in `w*`:

1. **Direct cost.** The instructions that encode the edited hyperedge/vertex
   itself: one `V`/`C` emission plus `O(k)` pointer moves (`P_i`/`N_i`).
   Bounded by `c_1·k` tokens, *independent of graph size*.

2. **Branching-tree stability.** The tie-complete encoder `w*_c` does not follow a
   fixed visitation order; it maintains a search *tree* of completions and returns
   the lex-minimum leaf. Structural tuples `ξ` have depth `r = 3` (CLAUDE.md
   invariant 8), so a single edit perturbs `ξ(v)` for all vertices `v` in the
   depth-`r` ball `N_r[e]` around the edit (`core/structural_tuples.py`). This
   has two effects on the search tree:
   - *Local effect*: the instructions that encode the directly-affected vertices
     and edges (those in `N_1[e]`, the 1-hop closed neighbourhood) change:
     `O(k)` tokens per directly-affected edge. This is the encoding window that
     the O(k·Δ) bound in (★) applies to (`|N_1[e]| = O(k·Δ)` vertices).
   - *Tie-set effect*: changing `ξ(v)` for `v ∈ N_r[e]` (the broader depth-`r`
     ball) can alter the tie set `T(σ)` at states `σ` reached during the
     branching search — at **any depth**, not only at the root — because `ξ`
     comparisons drive the key-prefix ordering that determines which V-candidates
     tie. If `T(σ)` changes at depth `d`, the lex-minimum completion may switch
     to a different branch and propagate changes through the remaining `|w*_c| - d`
     positions of the string.

**Lemma B1 (locality of `w*_c` — to prove).** Fix seed `v_0 ∈ S(H)`. Say an
edit `e` is *tie-set transparent from `(H, v_0)`* if:
- (i) **seed membership**: `v_0 ∈ S(H⊕e)`;
- (ii) **tie-set stability**: no vertex in `N_r[e]` (the depth-`r` ball around
  the edit, r = structural-tuple depth = 3, CLAUDE.md invariant 8) participates
  in any tie `T(σ)` in the branching search of `H` from `v_0`; and
- (iii) **argmin-seed preservation**: `v_0` remains the κ-minimum seed in
  `H⊕e`, i.e. `w*_c(H⊕e, v_0) ≤_κ w*_c(H⊕e, v')` for every `v' ∈ S(H⊕e)`.

Under all three conditions, the branching search trees of `H` and `H⊕e` from
`v_0` are isomorphic outside the direct encoding of `N_1[e]`, and
`w*_c(H, v_0)` and `w*_c(H⊕e, v_0)` agree outside at most `O(k·Δ)` positions.

**Two radii.** Condition (ii) uses `N_r[e]` (r = 3) because structural tuples at
depth 3 can change for vertices up to distance 3 from the edit, shifting
key-prefix comparisons at any search depth. The O(k·Δ) *bound* in (★) covers
only the encoding positions for vertices in `N_1[e]` (directly re-encoded after
the edit); the transparency condition is the broader set `N_r[e]`. Condition (iii)
is needed because even with conditions (i–ii) satisfied per-seed, a change inside
one seed's O(k·Δ) encoding window can flip a lex comparison at an early position
and migrate the κ-argmin to a different seed — and two seeds' encodings are not
Levenshtein-close (their distance is the seed-migration sensitivity).

**Relationship to the greedy condition.** For the single-trajectory greedy encoder,
condition (ii) reduces to "the greedy order `π` is unchanged on `V ∖ N_r[e]`"
and condition (iii) is not applicable (the greedy runs from a fixed `v_0` without
taking a lex-min over seeds). Both encoders yield the same O(k·Δ) bound when
their respective conditions are satisfied; `w*_c`'s condition is strictly stronger.

**Does the lex-min structure help or hurt?** Taking the lex-min over the search tree
does not make `w*_c` generically more stable than any single greedy trajectory.
When a tie set `T(σ)` is perturbed at depth `d`, the lex-min can jump
discontinuously to a different branch; the sensitivity is `Θ(|w*_c| - d)` in the
worst case, the same order as the greedy's avalanche. The lex-min is stable under
tie-set perturbations only when the perturbed tie is *automorphism-coherent*
(Proposition 6.0 of `theorem_a_completeness.tex`): all branches of a coherent tie
return equal completions, so the lex-min is indifferent to which branch is chosen.
Coherence therefore eliminates the tie-jump avalanche sources (§3 sources 3–4) —
it does not protect against sources 1–2 (seed-level changes). On Fano/STS(9),
where `w*_greedy = w*_c` was verified (see `scripts/bench_tie_complete.py`), all-depth coherence is *inferred*
by Prop 6.0's sufficient direction; the coherence criterion predicts no heavy
tail in the E2b histogram for those designs (§4), which is the falsification test.

**Proof risk (vindicated).** Pointer values are CDLL *indices*
(`CLAUDE.md` invariant 1); a vertex insertion shifts absolute indices globally.
The proof works in *relative* CDLL order via a shifted state
correspondence φ — but φ resolves state *identification* only. Because `P_i`/
`N_i` are **unit steps**, run lengths are slot counts: a vertex-count-changing
edit adds ±1 token to every later pointer run spanning the edited slot
(`T_span(e)`), and a window re-encoding's run to a changed member costs its
CDLL distance (`R(e)`). Neither term is bounded by any function of `(k,Δ)` in
the worst case, so the O(kΔ) locality is **conditional on layout-locality**
(conditions (iv)–(v), `theorem_b_stability.tex` Def. layout); the hazard this
paragraph originally flagged is real. **Resolved (see `pointer_run_amortization.tex`):** (v) is *refuted* — the orphaned-introducer
mechanism (an incidence edit re-homes a vertex's introduction point; the
orphaned introducer pays the CDLL distance between the sites) gives
bounded-degree tie-free families with `R(e) = Θ(n)` at Qin cost 1 under
(i)–(iii), and the same mechanism makes `E[R]` grow with `n` for uniform
incidence edits. (iv) *on average* reduces exactly to amortized movement via
the crossing-averaging identity `E_u[T_span(e_u)] ≤ M(H)/n` (`M(H)` = total
pointer movement of `w*_c`), and the probe (`scripts/probe_pointer_runs.py`)
shows `M(H)/n` grows with `n` at fixed density — so average-case (iv) also
fails generically; the drift is polynomial, additive, and directly measurable
per instance. The C branch requires separate treatment: from the
completeness proof, "a C candidate requires `members == set(tentative_inputs
[:arity])` and `SparseHypergraph` forbids duplicate member sets, so the C tie set
is always a singleton — there is no edge-id dependence to remove". C therefore never produces a tie and never triggers an avalanche
via the tie-set mechanism.

**Conditional bound.** Under tie-set transparency (i)–(iii) *and*
layout-locality (iv)–(v),
```
        s(e) ≤ (1+Δ) + R(e) + T_span(e) ≤ (1+Δ) + (c_3+c_4)·k·Δ = O(k·Δ). (★)
```
The bound decomposes as: at most `1+Δ` **structural** (`V`/`C`) token changes —
counted per edge, one token per affected edge encoding — plus the two
**pointer-run** terms: `R(e)` (window runs to changed member slots) and
`T_span(e)` (post-window runs spanning an inserted/removed CDLL slot, `v±`
edits only). The run terms are O(kΔ) *by hypothesis* (iv)–(v), not by
combinatorics: unit-step pointer semantics make them Θ(n)/Θ(m) in adversarial
layouts. Two earlier formulas are retracted: `c_2·k·Δ` (per-vertex double
count) and `(2k+1)·(1+Δ)` (rested on a false "≤2k+1 tokens per edge" premise).
See T-B2 of `stability/theorem_b_stability.tex`.

**Remark (why Qin's costing tightens the constant).** Per affected edge the
structural cost is exactly one `V`/`C` token against Qin cost ≥ 1 — ratio ≤ 1,
uniformly in arity. The entire `k`-dependence of `C(k,Δ)` enters through the
layout-locality run budget `(c_3+c_4)·k·Δ`, not through the edit's structural
footprint. See §T-B2 of `stability/theorem_b_stability.tex`.

---

## 3. The avalanche obstruction (why the bound is conditional)

Bound (★) fails when any of Lemma B1's five conditions is violated. Conditions
(i)–(iii) fail through the four *avalanche* sources below (branch/seed jumps —
large, discontinuous `s(e)`); conditions (iv)–(v) fail through *pointer-run
drift* (accumulated ±1 token edits — a distinct, non-avalanche mechanism, up to
O(m) for `v±` edits in adversarial layouts; see the vindicated proof-risk note
in §2.2). The avalanche failure modes, grouped by mechanism:

**Four avalanche sources:**
1. **Seed set change** (condition i fails): edit changes `S(H)` so `v_0 ∉ S(H⊕e)`
   → the entire `w*_c` is recomputed from a different starting point →
   `s(e) = O(m·k)`.
2. **Argmin migration** (condition iii fails): `S(H) = S(H⊕e)` but the edit
   shifts the per-seed encoding inside one seed's O(k·Δ) window, flipping a lex
   comparison early enough that a different seed `v' ∈ S(H⊕e)` becomes the
   κ-minimum → `s(e) = d_Lev(w*_c(H,v_0), w*_c(H⊕e,v')) = O(m·k)`. This is
   distinct from source 1: `v_0 ∈ S(H⊕e)` but it is no longer the κ-winner.
   The original "seed flip" label collapsed sources 1 and 2; for `w*_c` they are
   separate channels.
3. **Early tie perturbation** (condition ii fails, depth `d` small): edit shifts
   `ξ(v)` for some `v ∈ N_r[e]` (r = tuple depth = 3) that participates in an
   early tie `T(σ_d)` → the search switches branch early and the remaining string
   diverges. Wall-clock analogy: the high backtracking cost on the cyclic C13/GQ(2,2)
   (270 ms / 1.09 s vs 34 ms / 61 ms greedy for the complete vs greedy encoder) is the search-tree analogue.
4. **Deep tie perturbation** (condition ii fails, depth `d` arbitrary): same as
   source 3 at arbitrary `d`; sensitivity `≤ |w*_c| - d`. Uncommon on sparse
   inputs; frequent on dense or symmetric inputs.

For the greedy encoder, sources 3–4 do not exist: the greedy makes one comparison
per state along its single path and commits without branching, so only sources 1–2
can trigger a wholesale rewrite. For `w*_c`, all four sources are active.

**Where avalanches live — refined by Proposition 6.0 / Remark 6.1.**
The discriminant for sources 3–4 is *automorphism-coherence* of ties
(`theorem_a_completeness.tex`, §6). A tie at state `σ` is coherent if every pair
of tied candidates `e, e' ∈ T(σ)` is related by an automorphism of `H` that
fixes `dom(μ)` pointwise. By Proposition 6.0, when all reachable ties are
coherent, all branches give equal completions; the lex-min is therefore stable
against tie-set perturbations — sources 3–4 are suppressed. By Remark 6.1, the
stabiliser of `μ` at depth `d` shrinks as `d` increases; vertex-transitivity
buys coherence at the root only.

Empirical verdict (`scripts/bench_tie_complete.py`, i7-13700KF):

| Design | `w*_greedy = w*_c` | First incoherent edge tie (exact orbit-pruned audit) | Sources 3–4 exposure |
|---|---|---|---|
| Fano plane | True | none over the full orbit-pruned tree | Absent — **proved** via Prop 6.0 |
| STS(9) | True | **depth 3** (branch completions genuinely diverge) | **Exposed** despite equality |
| C13 cyclic (partial; formerly labelled STS(13)) | **False** | depth 2 (hand-proved: trivial pointwise block stabiliser) | Active |
| GQ(2,2) doily | **False** | depth 6 | Active |

All four designs are vertex-transitive. The avalanche regime for `w*_c` is
**not the vertex-transitive regime as a whole**, and — corrected (see
`pointer_run_amortization.tex` §T-B3 and `scripts/tb3_coherence_criterion.py`) — **not the string-equality regime
either**: the earlier "coherence inferred from Prop 6.0 + verified equality"
entries for Fano/STS(9) affirmed the consequent, and the exact orbit-pruned
criterion audit refutes the STS(9) one (incoherent tie at depth 3 with
divergent branch completions, yet per-seed greedy/complete equality holds on
0/72 shuffled (presentation, seed) pairs — mechanism open, not stabiliser
coherence). Prop 6.0 is strictly sufficient: criterion-coherence *proves*
equality (Fano); criterion-incoherence marks avalanche *exposure* (an edit can
switch the lex-min to a genuinely different completion) but does not decide
equality. Additionally, *ordering-level* ties (label-respecting orderings of a
V emission's new inputs) are a fifth avalanche channel with the same exposure
criterion — invisible to greedy-vs-complete (both branch over orderings), and
present even on Fano (depth 3). Sources 1–2 can occur on any input.

**Consequence — the theorem's honest final form:**
- **(B-worst)** Unconditionally, `d_I(H,H') ≤ (c·m·k)·HGED(H,H')` — a valid but
  weak envelope.
- **(B-cond)** For *tie-set transparent* edit paths (all three Lemma B1 conditions
  satisfied along every step), `d_I(H,H') ≤ O(k·Δ)·HGED(H,H')` — the strong
  bound (★). Replacing the earlier "seed-stable" label; the new condition is
  strictly stronger (conditions i–iii vs. depth-0 only).
- **(B-avg)** *Target to pursue:* over random/generic hypergraphs, ties are rare
  at every depth (structural tuples generically separate vertices), so source
  3–4 probability vanishes; sources 1–2 also vanish generically on local edits
  that preserve the dominant seed. Hence `E[s(e)] = O(k·Δ)` with high
  probability.

---

## 4. Theory ↔ empirics bridge (v3: what is still measured, and where)

The strong bound scales as `C(k,Δ) = O(k·Δ)`. Its two predictions now have
different fates:

1. **Density prediction — out of the article (v3).** A looser Lipschitz
   constant admits more slack, so `ρ(d_I, HGED)` should decrease as Δ grows;
   the sibling's data trend matches (Spearman ρ = 0.934 at mean-degree 3.07 →
   0.682 at 4.56 → 0.349 at 10.70). With the HGED-validation layer demoted,
   the controlled density sweep is **not run for the article**; the prediction
   is recorded here as follow-up material. The article's single correlation
   figure (PROPOSAL §5) reports one small corpus, ours only, no sweep.

2. **Sensitivity prediction — measured, in the geometry pillar.** The `s(e)`
   histogram shape depends on the automorphism-coherence of ties (§3,
   Prop 6.0). Sources 1–2 can occur on any input; sources 3–4 are suppressed
   on coherent inputs:
   - *Generic sparse*: near-unimodal O(kΔ) peak (no ties at any depth;
     sources 1–2 rare on local edits).
   - *Coherent-tie symmetric designs (Fano, STS(9))*: near-unimodal despite
     high symmetry (coherence inferred from Prop 6.0 + verified
     `w*_greedy = w*_c`).
   - *Incoherent-tie symmetric designs (cyclic C13, GQ(2,2))*: all four sources
     active → heavy-tailed or bimodal.
   This is measured by the **local sensitivity profile** (`geometry.md` §6) —
   a geometry measurement consumed by the contrast baseline and the
   discussion's mechanism prose, no longer an HGED-validation experiment. A
   heavy tail on Fano or STS(9) would falsify §3's coherence criterion; the
   falsifiability survives the rescope intact.

   **Measured outcome (connectivity-preserving single Qin edits, `max_arity = 3`,
   seven regimes: sparse/medium/dense random, Fano, STS(9), cyclic C13 orbit,
   GQ(2,2)).** 5 confirmed, 2 falsified.
   - *Confirmed (heavy_tail_frac = 0.000 where unimodal predicted):* sparse
     (IQR_ours = 2.0, IQR_nauty = 11.0), medium (4.0 / 17.0), dense (5.25 /
     11.0), Fano (5.0 / 20.0), STS(9) (7.0 / 15.0).
   - ***Falsified:*** cyclic C13 (predicted heavy-tailed; measured
     heavy_tail_frac = 0.000, IQR_ours = 2.0, IQR_nauty = 19.0) and GQ(2,2)
     doily (predicted heavy-tailed; measured heavy_tail_frac = 0.000,
     IQR_ours = 8.0, IQR_nauty = 10.0). Both designs are 3-uniform; all edits
     are drawn at `max_arity = 3`.

   Two candidate explanations, not mutually exclusive: (i) the `max_arity = 3`
   guard restricts edits to the same arity family as the existing edges,
   excluding arity-diverse edits that would cross a tier boundary in the `w*_c`
   branching tree — the predicted avalanche may require adding edges of higher
   arity to break the uniform structure; (ii) the avalanche mechanism is grounded
   in tie-set discontinuity near symmetric inputs, and a single discrete
   connectivity-preserving Qin edit at these `n` values (C13: n = 13, GQ(2,2):
   n = 15) may not reach the asymptotic regime the mechanism requires. A
   follow-up would test `s(e)` with arity-diverse edits on the same fixtures and
   on larger symmetric designs.

   The nauty contrast is confirmed including on the falsified designs: IsalHG
   IQR_ours = 2.0–8.0 tokens against IQR_nauty = 10.0–20.0 across all seven
   regimes (ratio 1.25–9.5×). The compact IsalHG profile on C13 and GQ(2,2) is
   not shared by nauty (IQR_nauty = 19.0 and 10.0 respectively), confirming that
   the low sensitivity variance is a property of the IsalHG encoding, not of the
   structural edits themselves.

---

## 5. Downstream: non-Euclidean geometry and MDS (moved to `geometry.md`)

*The geometry pillar lives in `geometry.md`; the paragraphs below are retained as
the seed and cross-reference. `geometry.md` §2/§4 develop the non-Euclidean
curvature `ν`, the intrinsic-dimension estimator, and the Bourgain/Khot–Naor
distortion brackets in full.*

`d_I` is an edit-distance metric; edit metrics are generically **non-Euclidean**
(the double-centred Gram matrix `B` has negative eigenvalues; Schoenberg
criterion). Consequences the applications section must own:
- Classical MDS is *approximate*, not isometric; report whether `B` is PSD per
  corpus and use the negative-eigenvalue floor / cross-validation for dimension
  selection (PI note, PROPOSAL §5).
- The *intrinsic dimension* estimated by cross-validated MDS is itself a result:
  "hypergraph space under `d_I` has estimated intrinsic dimension `D̂`."
- Bourgain/JL give `O(log n)`-distortion Euclidean embeddings if isometry is not
  required — a fallback framing if the non-Euclidean residual is large.

*Proof-effort status for Theorem A and Theorem B is tracked in the
engineering ledger (`docs/article/DEVELOPMENT/T-TA/` and
`docs/article/DEVELOPMENT/T-TB/`).*
