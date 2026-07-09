# Stability of the IsalHG hypergraph metric

**Status:** DRAFT (scoping 2026-07-08). Core theoretical document. Iterate here.

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
- Status in IsalHG: **RESOLVED at T-TA (2026-07-08)**, with a split verdict.
  Full proof + counterexamples:
  `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/theorem_a_completeness.{tex,pdf}`.
  - **(⇒) proved unconditionally** for every variant (round-trip soundness of
    S2H), over the *augmented fingerprint* `F(H) = (ℓ_max(H), w*(H))` — the
    string alone never records the seed vertex's label, so on non-trivial
    vertex vocabularies the bare string is incomplete (2-vertex counterexample;
    backend false positive). Trivial vocabulary (all corpora to date): `F ≡ w*`.
    **Implemented at T-TAb (2026-07-09):** `core.canonical.canonical_fingerprint`
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
  - **(⇐) proved for the tie-complete encoder** `greedy_min_complete`
    (added at T-TA: branches over the full η-tie set, `tie_branch=True`;
    execution-forest bijection, the IsalGraph Step-2 argument done right).
    **Theorem A holds for `w*_c := w*_complete`**; empirically backed
    (150/150 shuffle+relabel invariance; biconditional == pynauty under
    Hypothesis; pinned regression tests in
    `tests/{unit/core/test_greedy_min_complete,property/test_completeness}.py`).
    Ported to C++ at T-TAa (native `AlgorithmVariant::GreedyMinComplete`,
    byte-identical to the Python reference on 3,344 per-seed comparisons):
    `w*_c` costs 6.4 ms on the Fano plane and 1.1 s on GQ(2,2), so every
    downstream `d_I` computation runs on `w*_c` at corpus scale.
    Measured on the designs, `w*_greedy = w*_c` on Fano and STS(9)
    (automorphism-coherent ties) but **differs on STS(13) and GQ(2,2)** — the
    greedy string is not canonical even on vertex-transitive designs.

**Corollary A (Metric).** With Theorem A for `w*_c`, `d_I(H,H') :=
d_Lev(w*_c(H), w*_c(H'))` is a metric on isomorphism classes (per fixed `k`
and vocabulary): non-negativity and symmetry from `d_Lev`; identity of
indiscernibles from Theorem A; triangle inequality inherited from `d_Lev`.
Direct port of IsalGraph Corollary 1. **All downstream metric-space claims and
T-TB must be stated over `w*_c`**, not the greedy `w*` (which stays a fast
one-sided heuristic: equal strings still certify isomorphism, and it is exact
on edge-order-preserving pipelines and on automorphism-coherent-tie inputs
like the design fixtures — Fano verified `w*_greedy = w*_c`).

**Greedy `d_Lev` caveat.** On the greedy variants `d_Lev` is not even
well-defined on isomorphism classes (presentation-dependent); per fixed
presentation it is at best a pseudometric. The paper must not use it for the
metric claim.

---

## 2. Theorem B (Stability) — the core contribution

**Target statement.** There is an explicit constant `C(k,Δ)` such that for all
hypergraphs `H, H'`
```
        d_I(H, H') ≤ C(k, Δ) · HGED(H, H').                     (Lipschitz / upper bound)
```
i.e. structurally close hypergraphs have close canonical strings. This is the
*continuity* direction — the one that makes MDS, clustering, and kNN on `d_I`
well-behaved. IsalGraph asserted this empirically; we prove it (fully, or in the
conditional/average-case form of §3).

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
(PI decision 2026-07-08 at T-M2a close; an interim whole-edge variant from
T-M2, in which a whole-hyperedge insert/delete was one unit op, is
superseded and removed). The right-hand side of Theorem B is therefore a
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
   the lex-minimum leaf. A single edit perturbs the structural tuples `ξ(v)` for
   all `v ∈ N[e]` (`core/structural_tuples.py`), where `|N[e]| = O(k·Δ)`. This
   has two effects on the search tree:
   - *Local effect*: the instructions that encode the region `N[e]` directly
     change (O(k) tokens; covered by the direct cost above).
   - *Tie-set effect*: changing `ξ(v)` for `v ∈ N[e]` can alter the tie set
     `T(σ)` at states `σ` reached during the branching search — at **any depth**,
     not only at the root — because `ξ` comparisons drive the key-prefix ordering
     that determines which V-candidates tie. If `T(σ)` changes at depth `d`,
     the lex-minimum completion may switch to a different branch and propagate
     changes through the remaining `|w*_c| - d` positions of the string.

**Lemma B1 (locality of `w*_c` — to prove).** Fix seed `v_0 ∈ S(H)`. Say an
edit `e` is *tie-set transparent from `(H, v_0)`* if: (i) `v_0` remains a seed
vertex in `H⊕e`; and (ii) for every encoder state `σ` reachable in the branching
search of `H` from `v_0`, the key-prefix comparison among all V-candidates is
unchanged in `H⊕e` at the corresponding state — equivalently, no vertex in
`N[e]` participates in any tie `T(σ)` of the search. Under these conditions,
the branching search trees of `H` and `H⊕e` from `v_0` are isomorphic outside
`N[e]`, and `w*_c(H, v_0)` and `w*_c(H⊕e, v_0)` agree outside at most
`O(k·Δ)` positions.

**Relationship to the greedy condition.** For the single-trajectory greedy encoder,
condition (ii) reduces to "the greedy order `π` is unchanged on `V ∖ N[e]`" —
the only comparison that matters is the one the greedy makes at each step. For
`w*_c`, every tie at every depth is a comparison point, making the condition
strictly stronger. Both encoders yield the same O(k·Δ) bound when their
respective conditions are satisfied.

**Does the lex-min structure help or hurt?** Taking the lex-min over the search tree
does not make `w*_c` generically more stable than any single greedy trajectory.
When a tie set `T(σ)` is perturbed at depth `d`, the lex-min can jump
discontinuously to a different branch; the sensitivity is `Θ(|w*_c| - d)` in the
worst case, the same order as the greedy's avalanche. The lex-min buys stability
only when the tie is *automorphism-coherent* in the sense of Proposition 6.0 of
`theorem_a_completeness.tex`: all branches of a coherent tie return equal
completions, so the lex-min is indifferent to which branch is chosen and the
edit does not propagate. On inputs where all reachable ties are coherent (Fano
plane, STS(9) — empirically verified at T-TAa), no avalanche is possible in
`w*_c` for any edit that preserves the seed; on inputs with incoherent ties at
some depth (STS(13), GQ(2,2) — verified), a tie-set perturbation at that depth
triggers an avalanche in `w*_c` just as in the greedy.

**Proof risk (unchanged).** Pointer values are CDLL *indices* (`CLAUDE.md`
invariant 1); a vertex insertion shifts absolute indices globally. The proof must
be phrased in terms of *relative* CDLL order throughout and must construct a
state correspondence between the branching searches of `H` and `H⊕e` from `v_0`.
This is the crux of T-B1. The C branch requires separate treatment: by the T-TAa
analysis, the C tie set is always a singleton (duplicate member sets are
forbidden by `SparseHypergraph`), so C never produces a tie and never triggers
an avalanche via the tie-set mechanism.

**Conditional bound.** Under the hypotheses of Lemma B1 (a *tie-set transparent* edit),
```
        s(e) ≤ c_1·k + c_2·k·Δ = O(k·Δ).                        (★)
```

**Remark (why Qin's costing tightens the constant).** Re-encoding an edited
arity-`a` hyperedge costs Θ(a) tokens in `w*` (one `V`/`C` emission plus its
pointer moves), and Qin prices the corresponding whole-edge edit at `a+1` —
the cost model is *commensurate* with the encoding's incidence-mass scaling.
Per unit of HGED, the direct-cost contribution to `s(e)` is therefore O(1)
in arity; under a unit whole-edge op it would be O(k). Expectation for the
proof (flagged, to verify at T-B2): `C(k,Δ)`'s `k`-dependence should come
only from the reordering term, not from the direct term.

---

## 3. The avalanche obstruction (why the bound is conditional)

Bound (★) fails when the edit changes the tie set `T(σ)` at some reachable state
`σ` in the branching search — causing the lex-minimum to switch to a different
branch and rewiring the completion from depth `d(σ)` onwards:
`s(e) ≤ |w*_c| - d(σ) = O(m·k)` in the worst case, with worst case `d(σ) = 0`
(seed flip).

**Three avalanche sources** (by search depth):
1. **Seed flip** (depth 0): edit changes which vertex achieves max structural
   tuple → `v_0` changes → the entire `w*_c` is recomputed from a different
   starting point → `s(e) = O(m·k)`.
2. **Early tie perturbation** (depth `d` small, `d > 0`): edit shifts `ξ(v)` for
   some `v ∈ N[e]` that appears in an early tie `T(σ_d)` → the search switches
   branch early and the remaining string diverges. Wall-clock analogy: the
   high backtracking cost on STS(13)/GQ(2,2) (T-TAa: 270 ms / 1.09 s vs 34 ms /
   61 ms greedy) is the search-tree analogue of this effect.
3. **Deep tie perturbation** (depth `d` arbitrary): edit touches a vertex in
   `N[e]` that participates in a tie at depth `d` → sensitivity `≤ |w*_c| - d`.
   These edits are uncommon on sparse inputs (few ties); frequent on dense or
   symmetric inputs.

The earlier formulation of §3 described only source 1 and attributed all
avalanches to "top-ξ ties" (seed/early-order flips). For the greedy encoder this
is correct — the greedy commits at depth 0, so only the root-level comparison can
trigger a wholesale rewrite. For `w*_c`, which revisits tie sets at every depth,
sources 2 and 3 are distinct avalanche surfaces.

**Where avalanches live — refined by Proposition 6.0 / Remark 6.1.**
The discriminant is *automorphism-coherence* of ties
(`theorem_a_completeness.tex`, §6). A tie at state `σ` is coherent if every pair
of tied candidates `e, e' ∈ T(σ)` is related by an automorphism of `H` that
fixes `dom(μ)` pointwise. By Proposition 6.0, when all reachable ties are
coherent, all branches give equal completions; the lex-min is therefore stable —
an edit that preserves coherence cannot switch the branch. By Remark 6.1, the
stabiliser of the partial map `μ` at depth `d` is a subgroup of `Aut(H)` that
SHRINKS as `d` increases; vertex-transitivity buys coherence at the root only.

Empirical verdict (T-TAa, `scripts/bench_tie_complete.py`, i7-13700KF):

| Design | `w*_greedy = w*_c` | Avalanche regime for `w*_c` |
|---|---|---|
| Fano plane | True | None — all ties coherent at all depths |
| STS(9) | True | None — all ties coherent at all depths |
| STS(13) (cyclic, `{i,i+1,i+3}`) | **False** | Yes — incoherent ties at depth > 0 |
| GQ(2,2) (doily) | **False** | Yes — incoherent ties at depth > 0 |

All four designs are vertex-transitive. The avalanche regime for `w*_c` is
therefore **not the vertex-transitive regime as a whole** — it is the subset
with incoherent ties at some search depth. Proposition 6.0 is the correct
dividing line; it is machine-verified (T-TAa pinned the two failing designs) and
is the target for T-B3 to characterize analytically.

**Consequence — the theorem's honest final form (updated conditions):**
- **(B-worst)** Unconditionally, `d_I(H,H') ≤ (c·m·k)·HGED(H,H')` — a valid but
  weak envelope.
- **(B-cond)** For *tie-set transparent* edit paths (no tie-set perturbation at
  any search depth), `d_I(H,H') ≤ O(k·Δ)·HGED(H,H')` — the strong bound (★).
  This replaces the earlier "seed-stable" condition; they coincide at depth 0 but
  B-cond is strictly stronger at depth > 0.
- **(B-avg)** *Target to pursue:* over random/generic hypergraphs, ties are rare
  at every search depth (structural tuples generically separate vertices), so
  tie-set transparency holds with high probability. Hence `E[s(e)] = O(k·Δ)` and
  the strong bound holds in expectation. The same argument applies to any
  hypergraph family whose automorphism group is trivial: no ties means no
  avalanche, regardless of density.

---

## 4. Theory ↔ empirics bridge (answers "does the theorem correlate with the experiments?")

The strong bound scales as `C(k,Δ) = O(k·Δ)`. Two testable predictions:

1. **Density prediction.** Correlation `ρ(d_I, HGED)` should *decrease as Δ
   (density) increases*, because a looser Lipschitz constant admits more slack
   between `d_I` and `HGED`. **The IsalGraph data already exhibits this**:
   Spearman ρ = 0.934 at mean-degree 3.07 (IAM LOW) → 0.682 (IAM HIGH, 4.56) →
   0.349 (AIDS, 10.70). The IsalHG controlled experiment
   (`../empirical/correlation.md`, Exp E2) sweeps density at fixed `n` and checks
   that the ρ-decay tracks the predicted `1/C(k,Δ)`. **This is the experiment
   that validates Theorem B empirically** — the theorem is not decorative, its
   Δ-dependence is the falsifiable content.

2. **Avalanche prediction (revised at T-TBa).** The `s(e)` histogram shape
   depends on the automorphism-coherence of ties (§3, Prop 6.0), not on
   vertex-transitivity alone. Three regimes:
   - *Generic sparse*: near-unimodal O(kΔ) (ties absent at every depth).
   - *Coherent-tie symmetric designs (Fano, STS(9))*: near-unimodal O(kΔ)
     despite high symmetry — all ties coherent, so no avalanche in `w*_c`.
   - *Incoherent-tie symmetric designs (STS(13), GQ(2,2))*: heavy-tailed or
     bimodal — incoherent ties at depth > 0 create an avalanche surface.
   Measuring the histogram on all four designs (Exp E2b) tests this three-way
   prediction. A bimodal result on Fano or STS(9) would falsify §3's
   coherence criterion.

If either prediction fails, Theorem B's proof strategy is wrong — that is the
value of stating it falsifiably.

---

## 5. Downstream: non-Euclidean geometry and MDS (feeds `../empirical/applications.md`)

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

---

## 6. Proof-effort checklist (what has to be done)

- [x] T-A: **done pending PI review** (T-TA 2026-07-08): proof for
      `greedy_min_complete` + counterexamples for the greedy variants +
      empirical completeness suite. Cor. A and the "metric" claim now attach
      to `w*_c`. Default flip decided (D-TA1 resolved 2026-07-09): the
      complete algorithm becomes the package default once the T-TAd C++ port
      makes it fast.
- [ ] T-B0: make the §2.1 decomposition well-defined — (a) path-normalization
      lemma regrouping Qin's atomic ops into macro-ops with no empty-shell and
      no arity->k intermediates (reduce-before-extend interleaving), and (b)
      resolve the connectivity domain gap: `w*` rejects disconnected inputs
      (decision B11) but optimal HGED paths pass through disconnected states
      (ledger T-M2c; candidate fix: component-wise `w*`).
- [ ] T-B1: prove the restated Lemma B1 — locality of `w*_c` under tie-set
      transparency — in terms of *relative* CDLL order. The proof must construct
      a correspondence between the branching search trees of `H` and `H⊕e` from
      `v_0`, showing they are isomorphic outside `N[e]` when transparency holds.
      The global-index-shift risk from pointer values (CDLL indices, `CLAUDE.md`
      invariant 1) requires the argument to work in relative CDLL order
      throughout. C candidates are a singleton tie set by construction (T-TAa
      analysis: `SparseHypergraph` forbids duplicate member sets → no C-tie
      avalanche) and need separate, simpler treatment.
- [ ] T-B2: bound the *branching window* — the number of instruction positions
      that change under a tie-set-transparent edit — to `O(k·Δ)`. The token-width
      factor (instructions per vertex in the affected window; the `c_2` constant
      in `s(e) ≤ c_1·k + c_2·k·Δ`) must be nailed. The Qin-costing remark in
      §2.2 (direct term is O(1) in arity per unit HGED) should transfer to the
      branching-window count as well.
- [ ] T-B3: characterize when an edit `e` perturbs a tie set at depth `d` —
      the condition under which tie-set transparency fails and an avalanche occurs.
      The characterization should use Proposition 6.0 (automorphism-coherent ties,
      `theorem_a_completeness.tex` §6): a tie at depth `d` is incoherent iff the
      stabiliser `Aut(H)_{dom(μ_d)}` fails to act transitively on `T(σ_d)`. The
      empirical classification in §3 (Fano/STS(9) coherent; STS(13)/GQ(2,2)
      incoherent) is the ground truth the analytical characterization must recover.
      Connection to T-B4 (average-case): random sparse hypergraphs generically
      have no ties at any depth → condition holds vacuously → (B-avg) follows.
- [ ] T-B4 (stretch): the average-case/high-probability unconditional bound
      (B-avg) over a random hypergraph model.
- [ ] T-B5: verify constants against measured `s(e)` histograms (Exp E2b).
