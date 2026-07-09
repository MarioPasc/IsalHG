# Handoff — Canonical Backtracking Algorithm for IsalHG

**Status:** open investigation; sibling-port plan drafted.
**Owner of next iteration:** TBD.
**Last touched:** 2026-06-14.
**Parent docs:** `docs/engineering/DEVELOPMENT.md` (open question #1, "Algorithm-R&D
track (priority, pre-Tier 2)"), `docs/engineering/CODE_DESIGN.md` §1 (decision
tree), `docs/preprint/PROPOSAL.md` (canonical-completeness conjecture).

---

## 1. Problem surfacing

### 1.1 What we noticed (Phase 3 close, 2026-06-13)

`IsalHGBackend.fingerprint(H)` is the canonical-string computation. On
the named published designs used in Tier 1:

| Fixture | n_nodes | n_edges | IsalHG fingerprint wall-clock |
|---|---|---|---|
| Fano STS(7) | 7 | 7 | 0.78 s |
| STS(9) = AG(2,3) | 9 | 12 | 7.55 s |
| STS(13) cyclic {0,1,4} | 13 | 13 | 62 s |
| STS(13) cyclic {0,1,6} | 13 | 13 | 76 s |
| GQ(2,2) doily | 15 | 15 | 177 s |

For comparison, pynauty on the same Levi graphs is microseconds. The
gap is 6 orders of magnitude on GQ(2,2). The full Tier 1 sweep with
`include_large_designs: true` (the configuration that PROPOSAL §Tier 1
actually demands) is estimated at > 5 hours of IsalHG-cell wall-clock
purely on these named designs, before counting the enumerated cells.

### 1.2 Why this matters

Three reasons.

**Reason A — Tier 1 acceptance gap.** `docs/preprint/PROPOSAL.md` Tier 1
acceptance criterion 2 demands `canonical(H) = canonical(π(H))` for
**100 random vertex permutations per instance**. On GQ(2,2) that is
17,700 seconds (~5 h) for one cell of the Tier 1 sweep. We can run it,
but only once per workstation core. Iterating on the algorithm itself
under this latency is infeasible.

**Reason B — Tier 2 timing comparison.** Phase 5 (Tier 2 scaling)
publishes wall-clock plots of IsalHG vs pynauty/bliss/Traces on random
hypergraphs. The current algorithm will lose by 3-5 orders of
magnitude. This is publishable as "here is the gap; here is what we
need to close it", but it is not publishable as "IsalHG is
competitive". The latter is the headline claim PROPOSAL.md commits to.

**Reason C — open research question #1.** The PI-deferred "pruned
backtracking" variant has been on the open-question list since the
seed proposal (2026-06). `core/canonical_pruned.py` and
`algorithms/pruned_exhaustive.py` were stub files removed in the
architectural refactor (recorded in `docs/engineering/DEVELOPMENT.md` "Removed in
the architectural refactor" table) precisely because there was no
specified algorithm to reintroduce. This handoff is the algorithm-
spec document.

### 1.3 What the current algorithm does

`src/isalhg/core/hypergraph_to_string.py::_encode_from` runs **bounded
backtracking** on a single dimension:

- At each `V` (new-input emission) step, it branches over all
  `_label_respecting_perms(new_inputs_set, H)`. For trivial-vocabulary
  inputs (the only case currently exercised), this is `j!` branches per
  `V` step where `j` = number of new input vertices.
- At each branch, `state.clone()` is called — a full `O(n)` copy of the
  VM state (CDLL + pointer tables + consumed-edges set).
- **No backtracking** at the displacement-selection or edge-selection
  steps; both are pure greedy.

Worst-case branching factor across the encoding: `(j!)^{num V steps}`.
On vertex-transitive symmetric designs (Fano, STS, GQ), `j` is large
because the canonical seed selection picks vertices from the same
orbit, and the orbit is the whole vertex set.

---

## 2. How we proceeded

### 2.1 Sibling-port investigation (2026-06-14)

A general-purpose subagent investigated
`/home/mpascual/research/code/IsalGraph/src/isalgraph/core/` and
`/home/mpascual/research/code/IsalSR/src/isalsr/core/` for richer
backtracking machinery. Key findings:

**IsalGraph** ships two layers:

- `canonical.py::_step` — **full backtracking** at every `V/v` step.
  Crucially uses **in-place mutation + undo**, not `state.clone()`. The
  undo path is `O(j)` (number of new vertices to remove from CDLL +
  3 dict updates), versus IsalHG's `O(n)` clone per branch.
- `canonical_pruned.py::_pruned_step` — **structural-triplet pruning**.
  Pre-computes `(|N₁(v)|, |N₂(v)|, |N₃(v)|)` once per graph via BFS
  depth-3, then at each `V` step keeps only candidates achieving the
  max triplet. Documented caveat: the pruned canonical is a *different*
  invariant from the unpruned one (may produce longer strings on some
  graphs). This is a PI-level decision: do we adopt the pruned
  canonical as the published invariant, or do we use pruning only as
  an optimization that must preserve the unpruned canonical?

**IsalSR** ships three layers:

- `canonical_string` — exhaustive, similar to IsalGraph.
- `pruned_canonical_string` — **6-tuple** pruning (directed-graph
  analogue of IsalGraph's 3-tuple), with a critical fix: pruning is
  **label-aware**, grouping candidates by `node_label` first and
  picking max within each group. Cross-label pruning is invalid because
  automorphisms preserve labels.
- `fast_canonical_string` (the IsalSR default since 2026-03-26) — uses
  the **1-WL subtree hash** as the sort key, then backtracks **only over
  candidates with tied WL hash**. Claimed complete invariant, verified
  exhaustively for k = 1..8. Complexity `O(t^d × k²)` where `t` is the
  size of the tied WL group and `d` is the recursion depth.

IsalSR also documents two empirical failure rates for the 6-tuple
variant: 0.028% of inputs yield a longer-than-optimal string, and 0.09%
yield a same-length lex-different string. These are bookkeeping for
the 1-WL fast variant being preferred.

### 2.2 Five concrete port points

| # | Port | Source file | Expected effect on IsalHG |
|---|---|---|---|
| 1 | In-place mutation + undo at every `V` branch (replace `state.clone()`) | `IsalGraph/canonical.py::_step` | 5-15× constant-factor win per branch on n=15 designs |
| 2 | `xi`-based pruning at `V` candidate selection, *within each label class* | `IsalGraph/canonical_pruned.py::_pruned_step` + IsalSR label-grouping fix | Branching factor → 1 on non-symmetric inputs |
| 3 | 1-WL hash on the primal graph of `H`; sort `V` candidates by `(label, wl_hash)`, backtrack only over tied group | `IsalSR/canonical.py::_fast_step` | Branching factor → 1 on most non-vertex-transitive hypergraphs |
| 4 | `timeout: float \| None` parameter raising `CanonicalizationTimeoutError` | `IsalSR` timeout pattern | Clean fallback in `ExhaustiveSmallHypergraphs` enumeration |
| 5 | Bounded backtracking on **displacement ties** (currently pure greedy) | (not in siblings — new spec) | Closes one of the unspecified tie sources flagged in open question #1 |

**The xi/eta machinery already exists in IsalHG** —
`src/isalhg/core/structural_tuples.py` exposes `xi(v, H, depth=3)` and
the max-xi node-selection used in canonical seeding. Port point 2 just
plugs that existing function into the branch-pruning code path.

### 2.3 The honest gap — vertex-transitive designs

**None of the five port points help on Fano / STS(9) / STS(13) /
GQ(2,2).** These hypergraphs are vertex-transitive: their automorphism
group acts transitively on vertices. Consequently:

- `xi(v)` is identical for all v (no pruning).
- 1-WL hash converges to identical values for all v (no pruning).
- The canonical seed selection picks `argmax_lex xi(v)`, but every v
  achieves the max, so the seed-set IS the whole vertex set.

The siblings hit the same wall. IsalSR's `fast_canonical_string`
documents it: complexity `O(t^d × k²)` with `t = 1` only when WL
distinguishes the candidates; on vertex-transitive instances `t = n`
and the recursion is exponential.

The known route to break this is the **nauty/Traces strategy**:
**equitable partition refinement** combined with **individualisation-
refinement (IR)** backtracking, per McKay & Piperno 2014 *Practical
graph isomorphism, II* (J. Symb. Comput. 60). This is a substantially
larger algorithmic commitment than the sibling port: it requires:

- A refinement procedure that takes the current partial canonical
  state and produces an equitable partition of the remaining
  uncanonicalised vertices.
- An individualisation step that picks a target cell and branches over
  its members (the standard "choose a vertex, refine, recurse" loop).
- A pruning chain via the partial canonical string lex-comparison
  against the best-so-far — the same pruning that nauty itself uses.

This is publishable algorithm work, not a port.

---

## 3. Current state of the search

### 3.1 What we know

- The 5 port points from §2.2 are well-specified and will fix the
  constant-factor and non-symmetric-case performance.
- The vertex-transitive case requires a different algorithm (IR), not
  a port.
- The pruned canonical from IsalGraph and IsalSR is a *different
  invariant* from the unpruned canonical. Whether to publish the pruned
  invariant is a PI-level decision.
- `core/structural_tuples.py` already has `xi(v, H, depth=3)` —
  pruning needs no new structural machinery.
- The existing Phase-1 property tests
  (`tests/property/test_canonical_invariance.py`,
  `test_s2h_roundtrip.py`) will catch any port that breaks the current
  canonical invariant; this is a strong regression safety net.

### 3.2 What is missing — algorithmic specification

The next agent needs to produce (in order):

1. **A 1-page algorithm spec** as
   `docs/research/canonical_backtracking_algorithm_v1.md` covering:
   - Exact branch points (V emission, displacement tie, edge-selection
     tie).
   - Exact pruning rules (xi-based, label-grouped; 1-WL hash for tied
     xi classes; lex-min completion against best-so-far).
   - In-place mutation + undo invariants (what state mutates, what
     undoes it, ordering of operations).
   - Timeout semantics (check frequency, exception type, partial-result
     policy).
   - Decision: pruned-canonical-as-published vs pruning-as-optimization.

2. **A test plan** documenting:
   - Phase 1 / 2 / 3 fixtures (Fano, STS(9), iso/non-iso pairs) — must
     reproduce existing canonical strings if pruning is opt-in only,
     OR document the new strings as the new invariant.
   - Hypothesis property test: `canonical_pruned(H) ==
     canonical_pruned(π(H))` under random `permute(H, σ)`.
   - Timing benchmark: report fingerprint wall-clock on the 5 named
     designs from §1.1; target ≥ 10× improvement on STS(13), ≥ 30× on
     GQ(2,2).

3. **The implementation**, following `docs/engineering/CODE_DESIGN.md` §1.4
   structure:
   - Reintroduce `src/isalhg/core/canonical_pruned.py` and
     `src/isalhg/core/algorithms/pruned_exhaustive.py`.
   - Subclass `H2SAlgorithm` per `core/algorithms/base.py`.
   - Register a new backend `"isalhg_pruned"` in
     `iso_backends/registry.py` for side-by-side comparison.
   - Keep the current `"isalhg"` backend untouched until partition
     agreement holds across all Phase-1 fixtures.

### 3.3 What is NOT in scope for this handoff

- The **IR-refinement variant** for vertex-transitive designs. That is
  a separate research item that should be a second handoff once the
  sibling-port variant ships and the residual gap is measured.
- **`HG-CFI` construction** (open question #5) — this is a benchmark
  problem, not an algorithm problem. Belongs in the benchmark handoff
  (`docs/research/HANDOFF_hypergraph_benchmarks.md`).
- **Structural-tuple depth ≥ 4** (open question #3) — depth-3 is fixed
  by the IsalGraph analogy; whether to raise it depends on Tier 3
  empirical results, not on the backtracking algorithm.

---

## 4. Open questions for the PI

- Q1. Adopt the pruned canonical as the published invariant
  (single algorithm, different output from current Phase-1 strings),
  or keep both (current unpruned canonical as published invariant +
  pruning only as a same-output optimization)?
  - The first is simpler — one canonical, one algorithm. Some Phase-1
    canonical strings will change but the iso-invariance contract is
    preserved.
  - The second is more conservative — the published Phase-1 results
    remain valid as-is, and the new code is "an implementation
    optimization that does not change semantics". But the "must
    preserve unpruned canonical" requirement is hard to guarantee and
    may cap the pruning benefit.
- Q2. Is the IR-refinement variant (nauty-style) on the roadmap, or do
  we accept that IsalHG is slower on vertex-transitive designs and
  publish that as a known trade-off (with the caveat that the
  IsalHG-native algorithm provides interpretability / bijection
  witnesses that nauty does not)?
- Q3. Should the new backtracking algorithm support the same `timeout`
  semantics as IsalSR (raise `CanonicalizationTimeoutError`, no partial
  result), or should we return a partial canonical string with a flag?
  The latter is friendlier to dataset enumeration but introduces
  partial-state semantics that may be hard to specify precisely.
- Q4. Confirm Phase 5 ordering: this work is **parallel to Tier 2
  scaling**, not blocking it (per `docs/engineering/DEVELOPMENT.md` "Algorithm-R&D
  track (priority, pre-Tier 2)" section). Phase 5 ships the empirical
  data that informs which pruning dimensions matter most; the
  algorithm work uses that data to guide spec choices.

---

## 5. Pointers for the next agent

- `IsalGraph/canonical.py` — full backtracking, in-place mutation +
  undo. Port template for points 1 + 2.
- `IsalGraph/canonical_pruned.py` — structural-triplet pruning. Port
  template for point 2.
- `IsalSR/canonical.py` — three-layer architecture; the
  `fast_canonical_string` function is the gold standard. Port template
  for points 3 + 4.
- `isalhg.core.structural_tuples` — already exports `xi(v, H, depth)`.
  No new structural machinery needed.
- `isalhg.errors.CanonicalizationTimeoutError` — exception already
  declared. Port point 4 just needs to raise it.
- Phase 1 / 2 / 3 test fixtures stay valid as regression anchors.
- Property test
  `tests/property/test_canonical_invariance.py` validates iso-
  equivariance under random permutations and is the strongest
  guard-rail for the new algorithm.
