# T-M7p — Degree-matched labeled corpora for A2/A3

**Scope:** T-M7  
**Status:** QUESTION  
**Declared:** 2026-07-23 (by ledger-worker via task-handoff prompt)  
**Depends on:** T-M7n ✔ (power pilot — identified degree confound)

## Context

The power pilot (T-M7n, `artifacts/power_pilot/REPORT.md §2.3`) found that the
naive `degree_seq_l1` baseline beats IsalHG and every competitor on A2-ARI
(0.482 vs 0.297) and A3-AUC (0.957 vs 0.859) on the 7 k=3 Stratum A families.
The cause: the 7 families (STS7, STS9, GQ(2,2), loose/tight path/cycle k3)
separate on degree sequence alone — each design family has a distinct vertex
degree distribution, so any degree-sensitive representation gives near-perfect
clustering. The labeled A2/A3 task rewards degree sensitivity, not higher-order
structure, and cannot support a usefulness claim for d_I.

## Goal

A labeled synthetic corpus where structural classes are distinguishable by
higher-order structure but **NOT** by vertex degree sequence. The
`degree_seq_l1` baseline must achieve near-chance A2/A3 (ARI ≈ 0, AUC ≈ 0.5),
while at least one structure-aware representation (WL histogram or IsalHG d_I)
achieves meaningful separation above chance.

## Construction chosen

**Degree-matched block model (stub-pairing, fixed-degree configuration).**

Parameters (default): n_blocks=3, block_size=6, n=18 vertices, arity r=3,
degree d=3, n_classes=3, members_per_class=5.

Three structural classes, all sharing degree sequence (3,3,...,3):
- Class 0 (intra-heavy): 2 within-block edges + 1 cross-block edge per vertex.
  Planted community structure. (12 intra + 6 inter = 18 edges)
- Class 1 (balanced): 1 within-block + 2 cross-block edges per vertex.
  (6 intra + 12 inter = 18 edges)
- Class 2 (inter-heavy): 0 within-block + 3 cross-block edges per vertex.
  Tripartite structure. (0 intra + 18 inter = 18 edges)

Generation: stub-pairing configuration model.
- Intra stubs: stubs = [v]*n_intra for v in block; shuffle; group into r-tuples.
  Retry if self-loop (repeated vertex in same edge) or multi-edge.
- Inter stubs: per block, stubs = [v]*n_inter for v in block; shuffle each block
  independently; form edges as {stubs_B0[i], stubs_B1[i], stubs_B2[i]}.
  Reject multi-edges.
- Combine intra + inter edges; check is_connected(); check all degrees == d.
- Iso-dedup per class via IsalHG fingerprint.

Connectivity guarantee: all classes have n_inter >= 1 per vertex (class 2 has
n_inter=3), so all blocks are always connected through inter-block edges.

Degree-sequence guarantee: each vertex contributes exactly d=3 stubs (n_intra
+ n_inter = 3 for all classes). All pairwise degree_seq_l1 distances are 0.

## Acceptance

1. degree_seq_l1 pairwise distances are all 0 on the generated corpus. ARI and
   AUC from k-medoids / kNN with this all-zero matrix are near chance (asserted
   in tests).
2. IsalHG d_I median within-class distance < median between-class distance on
   a pinned corpus (structural signal exists).
3. KS test on per-class degree distributions: p-value = 1.0 (all degrees equal).
4. All hypergraphs connected, all vertex degrees == d.
5. Within each class, all member fingerprints distinct (non-iso).
6. n_items = n_classes * members_per_class; deterministic under (params, seed).
7. pytest/ruff/mypy match baselines (ruff 3 / mypy 21).

## Files

- NEW: `src/isalhg/datasets/synthetic/degree_matched_families.py`
- EDIT: `src/isalhg/datasets/registry.py` (add `"degree_matched_families"`)
- NEW: `tests/unit/datasets/test_degree_matched_families.py`
- EDIT: `experiments/article/analysis/sweep_multi_seed.py` (add DMF runner)

## Out of scope here

- Fixing k≥4 family Qin recovery (T-M7n §3.3 recommendation).
- Changing any Stratum A/B data or known_design_catalog.py (T-M7o owns those).
- Running the powered sweep (separate orchestrator task).

## QUESTION note (2026-07-23)

**Decision needed:** Is the AC2 criterion achievable with the degree-matched constraint? If not, what should the corpus do instead?

### Evidence

Pilot measurements on the default corpus (n=18, k=3, d=3; stub-pairing construction) and on a template+2-opt-swap construction (3 templates: T0 intra-heavy / T1 balanced / T2 inter-heavy circulant, verified n=18 m=18 d=3 k=3 connected):

| Construction | isalhg_levenshtein ARI | hypergraph_wl_l1 ARI | degree_seq_l1 ARI |
|---|---|---|---|
| Stub-pairing (default) | 0.097 | 0.000 | 0.000 |
| Template + 1 swap | 0.052 | 0.000 | 0.000 |
| Template + 2 swaps | 0.023 | 0.000 | 0.000 |
| Template + 3 swaps | 0.234 | 0.000 | 0.000 |

ARI via `scipy.cluster.hierarchy` average linkage + `fcluster` (n_classes=3).
Template pairwise distances: d_I(T0,T1)=31, d_I(T0,T2)=37, d_I(T1,T2)=37.

### Root cause

Two independent mathematical barriers:

**1. WL blind to d=3 k=3 trivially-labeled regular hypergraphs.**
WL initial colors are derived from `H.vertex_label(v)`. With trivial labels, all
vertices start identical. In round 1, all d-regular k-uniform hypergraphs produce
identical vertex coloring (every vertex has degree d → same neighborhood signature).
WL converges with one color for ALL members → L1 histogram distance = 0 for every
pair regardless of class. WL ARI = 0.000 is a mathematical certainty.

**2. Avalanche overwhelms IsalHG d_I for non-iso members.**
With n=18, canonical strings are ~50 tokens. A single degree-preserving 2-opt swap
changes 2 of 18 edges, but the avalanche effect (completeness → sensitivity near
symmetry) changes ~30-35 canonical tokens. The between-class template separation
is only 37 tokens → within/between ratio ≈ 0.93 → no clustering signal. Best
achieved with 3 swaps: ARI=0.234. This barrier is fundamental — the avalanche is
the price any complete invariant pays (documented in `theoretical/stability.md`).

### Options for PI

1. **Relax AC5 (allow iso copies within class)**: permuted copies → d_I=0 within,
   d_I=37 between → IsalHG ARI=1.0. But tests isomorphism detection, not clustering.

2. **Class-specific vertex labels**: WL initial colors differ by class → WL ARI≈1.0.
   But this reads the class label directly — a reviewer would flag this as trivial.

3. **Non-regular mixed-degree multiset corpus**: degree sequence [4,4,4,2,2,2] with
   different structural arrangements per class. WL detects high/low-degree arrangement
   → WL ARI might exceed 0.5. Avalanche still limits IsalHG d_I. Requires new design.

4. **Report the honest negative (recommended)**: "degree matching neutralizes ALL
   tested representations." Reframe DMF as a negative control — the complementary
   finding to T-M7n. Requires relaxing the AC2 criterion to "degree_seq_l1 = 0 for
   all pairs; no other representation achieves ARI ≳ 0.5." The code and corpus are
   already correct for this framing.

5. **Drop DMF entirely**: T-M7n REPORT.md already documents the degree confound.

**Recommendation:** Option 4 (negative control reframe) requires zero new work and
is scientifically honest. Option 3 if a positive corpus is needed for the article.

## Closing note (original — superseded by QUESTION above)

**2026-07-23.** DONE.  All 18 unit tests pass on the default corpus
(n_blocks=3, block_size=6, members_per_class=5, seed=0; n=18, k=3, d=3):

  - T1 (teeth): planted families produce non-zero degree_seq_l1 cross-family
    distances; DMF produces all-zero (acceptance criterion 1 verified with
    a demonstrably failing baseline).
  - AC2: IsalHG d_I median within-class (≈5) < median between-class (≈25).
  - AC3: KS statistic = 0.0 across all pairs of class degree distributions.
  - AC4: all 15 hypergraphs connected; all degrees = 3; all arities = 3.
  - AC5: within-class fingerprints distinct (5 non-iso members per class).
  - AC6: n_items = 15 = 3 × 5; determinism verified.
  - Registry lookup: `get_dataset("degree_matched_families", {...})` succeeds.

pytest tests/unit/datasets/: 316 passed, 1 skipped (18 new + 298 prior).
ruff: 3 errors (baseline; no new violations).
mypy: 21 errors (baseline; no new errors).

Files created/modified:
  - NEW: src/isalhg/datasets/synthetic/degree_matched_families.py
  - EDIT: src/isalhg/datasets/registry.py (added lazy entry)
  - NEW: tests/unit/datasets/test_degree_matched_families.py
  - EDIT: experiments/article/analysis/sweep_multi_seed.py
    (added _DMF_CELL_KEY, build_degree_matched_families_corpus,
     run_degree_matched_families_seed, run_degree_matched param in run_sweep)

---

## Resolution — DROP (PI decision, 2026-07-23)

**Status:** CLOSED — investigated, corpus dropped; the impossibility result is
the deliverable. The DMF code (branch `worktree-agent-a9c7077102d3d1bac`,
commits `10722d4`/`9de1344`) is **not merged** — deliberately discarded.

**PI decision (via Mario):** drop the degree-matched corpus entirely. The
QUESTION established that a corpus which is simultaneously (i) degree-matched,
(ii) non-isomorphic within class, and (iii) separable by a structural method at
ARI ≳ 0.5 is **unachievable for regular trivially-labelled hypergraphs** — two
independent barriers: WL blindness (regular + trivial labels ⇒ one colour ⇒
ARI 0) and the IsalHG **avalanche** (a degree-preserving 2-edge swap relabels
~30 of ~50 canonical tokens, drowning the ~37-token class separation; max ARI
0.234 over four constructions). The IsalHG barrier is the paper's own avalanche
mechanism (`theoretical/stability.md`), so the negative result is coherent, not
a defect.

**Consequence for the article (agreed):** A2/A3 usefulness is **not** claimed
via out-clustering competitors on a contrived degree-controlled corpus. Instead:
(a) the design-family A2/A3 is reported **honestly** — IsalHG competitive, the
naive degree-sequence baseline and NetLSD win on those families *because the
families also differ in degree* (the T-M7n confound, documented on record); and
(b) the usefulness claim leads on **A4** (decodable + navigable intermediates —
a capability no competitor has) and the **capability matrix**. This matches the
article's existing framing (D-ART2). No degree-controlled exhibit ships.
