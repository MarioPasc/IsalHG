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
  - **(⇐) proved for the tie-complete encoder** `"canonical"`
    (added at T-TA: branches over the full η-tie set, `tie_branch=True`;
    execution-forest bijection, the IsalGraph Step-2 argument done right).
    **Theorem A holds for `w*_c := w*_canonical`**; empirically backed
    (150/150 shuffle+relabel invariance; biconditional == pynauty under
    Hypothesis; pinned regression tests in
    `tests/{unit/core/test_canonical_encoder,property/test_completeness}.py`).
    Ported to C++ at T-TAa (native `AlgorithmVariant::GreedyMinComplete`,
    byte-identical to the Python reference on 3,344 per-seed comparisons):
    `w*_c` costs 6.4 ms on the Fano plane and 1.1 s on GQ(2,2), so every
    downstream `d_I` computation runs on `w*_c` at corpus scale.
    **Package default since T-TAd (D-TA1, 2026-07-09):** `canonical_string`,
    `canonical_fingerprint`, `IsalHGBackend`, and `IsalHGLevenshtein` all
    compute `w*_c` unless an algorithm is explicitly overridden
    (`ISALHG_ALGORITHM` env var preserved for the preprint pipeline).
    Measured on the designs, `w*_greedy = w*_c` on Fano and STS(9)
    (automorphism-coherent ties) but **differs on STS(13) and GQ(2,2)** — the
    greedy string is not canonical even on vertex-transitive designs.

**Frozen definition of `w*_c` (D-TA2, PI 2026-07-09).** `w*_c` is the
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
`tests/unit/core/test_wstar_c_frozen.py` fix `w*_c` on {Fano, STS(9), cyclic
STS(13), the n=4 counterexample}; a refinement that changes the value fails
loudly.

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
where `w*_greedy = w*_c` was verified at T-TAa, all-depth coherence is *inferred*
by Prop 6.0's sufficient direction; the coherence criterion predicts no heavy
tail in the E2b histogram for those designs (§4), which is the falsification test.

**Proof risk (vindicated at T-TB).** Pointer values are CDLL *indices*
(`CLAUDE.md` invariant 1); a vertex insertion shifts absolute indices globally.
The T-TB proof works in *relative* CDLL order via a shifted state
correspondence φ — but φ resolves state *identification* only. Because `P_i`/
`N_i` are **unit steps**, run lengths are slot counts: a vertex-count-changing
edit adds ±1 token to every later pointer run spanning the edited slot
(`T_span(e)`), and a window re-encoding's run to a changed member costs its
CDLL distance (`R(e)`). Neither term is bounded by any function of `(k,Δ)` in
the worst case, so the O(kΔ) locality is **conditional on layout-locality**
(conditions (iv)–(v), `theorem_b_stability.tex` Def. layout); the hazard this
paragraph originally flagged is real, and its generic (average-case) resolution
is ledger task T-TBb. The C branch requires separate treatment: from the
T-TAa closing analysis, "a C candidate requires `members == set(tentative_inputs
[:arity])` and `SparseHypergraph` forbids duplicate member sets, so the C tie set
is always a singleton — there is no edge-id dependence to remove" (T-TAa.md,
closing note). C therefore never produces a tie and never triggers an avalanche
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
footprint. Sharpened at T-B2.

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
   diverges. Wall-clock analogy: the high backtracking cost on STS(13)/GQ(2,2)
   (T-TAa: 270 ms / 1.09 s vs 34 ms / 61 ms greedy) is the search-tree analogue.
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

Empirical verdict (T-TAa, `scripts/bench_tie_complete.py`, i7-13700KF):

| Design | `w*_greedy = w*_c` | Coherence | Active sources |
|---|---|---|---|
| Fano plane | True | All depths (inferred from Prop 6.0 + verified equality) | 1–2 only |
| STS(9) | True | All depths (inferred) | 1–2 only |
| STS(13) cyclic | **False** | Incoherent at depth > 0 | 1–4 |
| GQ(2,2) doily | **False** | Incoherent at depth > 0 | 1–4 |

All four designs are vertex-transitive. The avalanche regime for `w*_c` is
**not the vertex-transitive regime as a whole**. The correct dividing line for
sources 3–4 is Proposition 6.0's coherence criterion, calibrated empirically by
the T-TAa string-equality measurements and the target for T-B3 to characterize
analytically. Sources 1–2 can occur on any input, including coherent designs.

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
   depends on the automorphism-coherence of ties (§3, Prop 6.0). Sources 1–2
   can occur on any input; sources 3–4 are suppressed on coherent inputs.
   - *Generic sparse*: sources 3–4 absent (no ties at any depth); sources 1–2
     rare on local edits → near-unimodal O(kΔ) peak.
   - *Coherent-tie symmetric designs (Fano, STS(9))*: sources 3–4 absent
     (coherence inferred from Prop 6.0 + verified `w*_greedy = w*_c`); sources
     1–2 possible but rare on small design edits → near-unimodal O(kΔ) despite
     high symmetry. **Changed from the earlier "symmetric ⇒ bimodal" prediction.**
   - *Incoherent-tie symmetric designs (STS(13), GQ(2,2))*: all four sources
     active → heavy-tailed or bimodal.
   Measuring the histogram on all four designs (Exp E2b) tests this prediction.
   A heavy tail on Fano or STS(9) would falsify §3's coherence criterion.

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

- [x] T-A: **PROVED AND PI-REVIEWED** (T-TA, proof 2026-07-08, review passed
      2026-07-09): proof for `"canonical"` + counterexamples for the greedy
      variants + empirical completeness suite. Corollary A — `d_I` is a metric on
      isomorphism classes of connected hypergraphs at fixed `k`, depth and
      vocabulary — is therefore **established, not conjectured**, and every claim
      below rests on it. `w*_c` is frozen as the *unpruned* tie-complete lex-min
      (D-TA2); the complete algorithm becomes the package default at T-TAd.
- [x] T-B0: **PROVED (T-TB, 2026-07-09, §2 of `stability/theorem_b_stability.tex`).**
      make the §2.1 decomposition well-defined. **Mechanism fixed by the PI
      at T-M2c (2026-07-09): the article's domain is the connected hypergraphs,
      `Σ_HG` does not change, and P1 is discharged by a path-normalization lemma —
      not by teaching `w*` to accept disconnected inputs.** The lemma to prove: the
      triangle inequality bounds `d_I` along *any* edit path, not only an optimal
      one, so it suffices that **some** path `H → H'` has all-connected
      intermediates and total Qin cost `≤ c·HGED(H,H')`. Such a path exists with
      `c = 1`, because Qin's ops are unit-cost and the following two reorderings
      preserve the op count: (i) **insert before delete** — all insertions and
      extensions first, reaching `H ∪ H'` under the optimal correspondence `π`,
      then all reductions and deletions; (ii) **no isolated vertex is ever
      materialized** — pair each vertex insertion with its first incidence
      addition, pair each vertex deletion with its last incidence removal, and
      delete leaf-first. Every intermediate on the first leg then contains the
      connected spanning `H`; on the second leg, the connected spanning `H'`.
      *Residuals (documented in the proof):* (a) `H ∪ H'` connected — fails only
      in the degenerate near-maximal-HGED regime, handled by B-worst; (b) the
      reduce-before-extend interleaving (P3) is now proved per edge, with an
      honest cost residual: matched edge pairs that are disjoint at arity `k`
      (and the `k=2`, one-shared-member case) fall back to delete-and-reinsert,
      inflating cost by ≤ 2 per such edge — zero under genericity, `≤ 2c_0`
      in general, giving `d_I ≤ C·(HGED + 2c_0)`.
- [x] T-B1: **PROVED under (i)–(v) (T-TB + orchestrator post-audit, 2026-07-09,
      §3 of `stability/theorem_b_stability.tex`).** Lemma B1 — locality of `w*_c`
      — holds under five conditions: seed membership (i), key-crossing freedom
      over `N_r[e]` r=3 (ii — the earlier "V-candidate non-incidence" form was
      unsatisfiable and is retracted), argmin-seed preservation (iii), plus the
      **layout-locality** conditions span-boundedness (iv) and run-locality (v)
      for the pointer-run terms `T_span(e)`, `R(e)`. The φ correspondence
      resolves state identification in relative CDLL order; it does NOT bound
      the run terms — unit-step `P_i`/`N_i` semantics make unconditional O(kΔ)
      locality FALSE in adversarial layouts (the vindicated §2.2 proof risk).
      Generic validity of (iv)–(v) is open → T-TBb. C candidates are a
      singleton tie set by construction (T-TAa.md closing: "a C candidate
      requires `members == set(tentative_inputs[:arity])` and
      `SparseHypergraph` forbids duplicate member sets, so the C tie set is
      always a singleton") — no C-tie avalanche possible; treated separately.
- [x] T-B2: **PROVED — structural part; run terms conditional (T-TB +
      orchestrator post-audit, 2026-07-09, §4 of
      `stability/theorem_b_stability.tex`).** Token-difference decomposition:
      ≤ `1+Δ` structural `V`/`C` token changes (one per affected edge encoding;
      per-edge count) + `R(e)` + `T_span(e)` pointer-run tokens. Under (iv)–(v):
      `s(e) ≤ (1+Δ) + (c_3+c_4)·k·Δ = O(k·Δ)` — see (★). Two prior formulas
      retracted (per-vertex `c_2·k·Δ` double count; `(2k+1)(1+Δ)` via the false
      "≤2k+1 tokens per edge" premise). Qin-costing remark: structural cost is
      one token per affected edge per unit Qin cost (ratio ≤ 1, uniform in
      arity); all `k`-dependence lives in the layout-locality run budget.
- [ ] T-B3: **criterion STATED (T-TBa via Prop 6.0); analytical recovery of the design classification PENDING.** Prop 6.0 (from `theorem_a_completeness.tex` §6) gives a criterion: a tie at depth `d` is incoherent iff `Aut(H)_{dom(μ_d)}` fails to act transitively on `T(σ_d)`. §5 of `theorem_b_stability.tex` records this criterion and notes that Fano/STS(9) are observed coherent and STS(13)/GQ(2,2) incoherent (T-TAa empirical measurement), but the derivation that the Prop 6.0 criterion *implies* this classification — from stabiliser structure alone, without the T-TAa empirical string-equality measurement — is not given. The analytical recovery from the stabiliser-transitivity criterion remains open.
- [ ] T-B4 (stretch): **SKETCH ONLY — not proved** (T-TB, 2026-07-09, §5 B-avg,
      Thm 3 of `stability/theorem_b_stability.tex`). The average-case bound
      (B-avg) over a random hypergraph model. A rigorous version must also show
      layout-locality (iv)–(v) holds w.h.p. (an amortization claim about the
      κ-lex-min encoder, not a consequence of tie scarcity) → T-TBb.
- [ ] T-B5: **PENDING T-M5a** — verify constants against measured `s(e)` histograms (Exp E2b).
      Predictions stated in §6 of `stability/theorem_b_stability.tex` and §4 of this file.
      T-M5a should additionally log `R(e)`/`T_span(e)` per edit to separate
      layout drift from avalanche effects. Empirical match is a documented
      pending clause; T-TB closed with this clause recorded.
- [ ] T-TBb (filed 2026-07-09, post-audit): pointer-run amortization — prove or
      refute generic layout-locality (iv)–(v); analytical T-B3 recovery; rigorous
      B-avg; verify the encoder emits no `W` tokens (length-lemma proviso). See
      `DEVELOPMENT/T-TB/OPEN/T-TBb.md`.
