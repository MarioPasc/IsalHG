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

2. **Reordering cost.** A single edit perturbs the structural tuples `ξ(v)`
   (degree-based, `core/structural_tuples.py`) only for vertices in the closed
   neighbourhood `N[e]` of the edit (edited vertices + their neighbours),
   `|N[e]| = O(k·Δ)`. If the induced changes do **not** alter the canonical seed
   nor the *relative* greedy visitation order, the encoding of every unaffected
   region is preserved and only the `O(k·Δ)` affected vertices are re-emitted:
   reordering cost `≤ c_2·k·Δ · (token-width per vertex)`.

**Lemma B1 (locality of greedy H2S — to prove).** Fix seed `v_0` and the greedy
order `π`. If an edit `e` leaves `v_0` and the relative order `π` on
`V ∖ N[e]` unchanged, then `w*(H)` and `w*(H⊕e)` agree outside a set of at most
`O(k·Δ)` instruction positions. **Risk:** pointer values are CDLL *indices*
(`CLAUDE.md` invariant 1), so an insertion shifts absolute indices globally; the
proof must be phrased in terms of *relative* CDLL order, not absolute index, or
the bound inflates to `O(n)`. This is the crux of the proof and the main open
technical risk.

**Conditional bound.** Under the hypotheses of Lemma B1 (a *seed-stable* edit),
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

Bound (★) fails when the edit flips a **tie at the top of the `ξ` order** —
changing the canonical seed `v_0` or an early greedy choice. Then the greedy
trajectory diverges from the start and `w*` can be rewritten wholesale:
`s(e) = O(|w*|) = O(m·k)` worst case.

**Where avalanches live.** Seed/early-order ties are exactly the
vertex-transitive / high-automorphism regime — Fano, STS(9), STS(13), GQ(2,2) —
the same structures where IsalHG's bounded backtracking already explodes
(`docs/engineering/DEVELOPMENT.md` open Q1, timings 0.78 s → 177 s). So the avalanche regime
**coincides with the known hard regime**; it is not a new pathology.

**Consequence — the theorem's honest final form.** A two-part statement:
- **(B-worst)** Unconditionally, `d_I(H,H') ≤ (c·m·k)·HGED(H,H')` — a valid but
  weak envelope.
- **(B-cond)** For *seed-stable* edit paths (no top-`ξ` tie flips),
  `d_I(H,H') ≤ O(k·Δ)·HGED(H,H')` — the strong bound (★).
- **(B-avg)** *Target to pursue:* over random/generic hypergraphs, top-`ξ` ties
  have vanishing probability, so `E[s(e)] = O(k·Δ)` and the strong bound holds
  with high probability. An average-case / high-probability statement is the
  most likely *fully unconditional* win and matches the empirical correlation.

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

2. **Avalanche prediction.** On high-automorphism designs, ρ should drop sharply
   and `s(e)` histograms should be bimodal (most edits `O(kΔ)`, rare edits
   `O(mk)`). Measuring the single-edit sensitivity histogram directly
   (`../empirical/correlation.md`, Exp E2b) tests the §3 avalanche story.

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
      2026-07-09): proof for `greedy_min_complete` + counterexamples for the greedy
      variants + empirical completeness suite. Corollary A — `d_I` is a metric on
      isomorphism classes of connected hypergraphs at fixed `k`, depth and
      vocabulary — is therefore **established, not conjectured**, and every claim
      below rests on it. `w*_c` is frozen as the *unpruned* tie-complete lex-min
      (D-TA2); the complete algorithm becomes the package default at T-TAd.
- [ ] T-B0: make the §2.1 decomposition well-defined. **Mechanism fixed by the PI
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
      *Residual hypothesis to discharge:* `H ∪ H'` is connected, i.e. `π`
      identifies at least one vertex — this fails only in the degenerate
      near-maximal-HGED regime, where the bound is slack and the case is handled
      separately. Still owed alongside it: no arity`->k` intermediates
      (reduce-before-extend interleaving).
- [ ] T-B1: prove Lemma B1 (locality) in terms of *relative* CDLL order; resolve
      the global-index-shift risk.
- [ ] T-B2: bound the reordering cost to `O(k·Δ)` under seed-stability; nail
      the token-width factor.
- [ ] T-B3: characterize the seed-flip (avalanche) condition precisely; tie it
      to top-`ξ` ties and the automorphism group.
- [ ] T-B4 (stretch): the average-case/high-probability unconditional bound
      (B-avg) over a random hypergraph model.
- [ ] T-B5: verify constants against measured `s(e)` histograms (Exp E2b).
