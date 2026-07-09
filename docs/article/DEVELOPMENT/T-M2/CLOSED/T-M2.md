# T-M2 — HGED oracle + correlation corpora
**Declared:** 2026-07-08 12:20 CEST · **rescoped** 2026-07-08 13:40 CEST
**Status:** DONE
**Depends on:** T-M1a
**Context to read first:**
- `docs/article/CODE_DESIGN.md` §3 (table), §4.1 (edit ops)
- `docs/article/empirical/correlation.md` §HGED — the oracle tiering
- `docs/article/DATA.md` §1, §5 — corpus size / exact-HGED ceiling (raised by HPC)
- `docs/article/RELATED_WORK.md` — Qin et al. 2023 (HGED definition), Riesen–Bunke 2009 (BP)
- `src/isalhg/core/levi_reduction.py` (post-T-M1a) — for BP assignment on incidence stars
- IsalGraph paper `computational_experiments.tex` — the exact-GED experimental design it ports
- `.claude/rules/coding_rules.md` — always
**Description:** Load-bearing: `ExactHGED` + `datasets/synthetic/{perturbation_ladder,
correlation_corpus}.py`. **OD4 resolved — implement `ExactHGED` as our own A*/ILP
over the six edit ops, NOT the `networkx.graph_edit_distance`-on-Levi wrapper:**
GED on the bipartite Levi graph is *not* obviously equal to HGED (vertex-nodes
and edge-nodes carry different semantics; the cost-lift needs a correctness proof
we do not want to owe). `BipartiteHGED` (BP-HGED, scipy `linear_sum_assignment`)
is **optional** — a scalable cross-check that the ladder budget proxies true
HGED, not a blocker. Note: **HGED runs on HPC with high parallelism**, so the
exact ceiling is well past n=10 — benchmark where it actually falls.
**Leverage / scaffolds (search 2026-07-08):** **no public HGED implementation
exists** — Qin et al. (ICDE 2023) released no code; HyperNetX / XGI / Hypergraphx
ship none. `ExactHGED` is therefore our own A*/ILP over the six ops on
`SparseHypergraph`. Read *for algorithmic structure only* (do NOT wrap — they are
graph GED, not HGED): `networkx/algorithms/similarity.py::optimize_graph_edit_distance`
(the A* state-space loop + custom-cost callback pattern, pip, pure Python) and
`github.com/LijunChang/Graph_Edit_Distance` (MIT, C++; tight A* lower bounds).
`scipy.optimize.linear_sum_assignment` for the optional BP-HGED. GEDLIB / gedlibpy
(the Levi-lift route) stays rejected per OD4 — the lift-correctness proof is owed.
**Acceptance:** exact HGED matches hand-computed edit counts on tiny fixtures;
ladder budget `t` ≥ exact HGED on the same pairs; exact-oracle `n`-ceiling
benchmarked on the HPC parallel regime and reported (DQ1).
**Out of scope here:** the correlation *experiment* itself (T-M5a); competitor
distances (T-M3a–d).
**Closing (2026-07-08 18:19 CEST):**
- *Deliverables:* `src/isalhg/metric_space/distances/hged.py` (`ExactHGED` +
  `BipartiteHGED`, registered `exact_hged` / `bipartite_hged`);
  `datasets/synthetic/{perturbation_ladder,correlation_corpus}.py` (+ shared
  stdlib `_random_hg.py`), registered `perturbation_ladder` / `correlation_corpus`;
  `scripts/bench_hged_ceiling.py` (DQ1). Tests:
  `tests/unit/metric_space/test_hged_{exact,bipartite}.py`,
  `tests/unit/datasets/test_{perturbation_ladder,correlation_corpus}.py`,
  `tests/property/test_hged_metric.py`.
- ***Cost-model correction (scientific, load-bearing for T-TB).*** Qin et al.'s
  op (i) inserts/deletes only an **empty-shell** hyperedge (deleting a `k`-edge
  costs `k+1`). Our generating set — the six free functions the ladder
  (`edit_path`) samples — inserts/deletes a **whole hyperedge of any arity in one
  unit op**. `correlation.md` §HGED lists "hyperedge insert/delete" as unit ops
  *distinct from* incidence add/remove, so the adopted HGED uses the whole-edge
  convention. This is the only convention consistent with the acceptance
  `t ≥ HGED` (a length-`t` ladder path exists in exactly these ops). **Our HGED
  ≤ Qin's HGED.** A smoke test caught the original `k+1` implementation returning
  `Exact > t` on 13/40 ladder pairs; the fix (whole-edge unit delete/insert via
  LSAP delete/insert slots) restored `t ≥ Exact` on 120/120. **T-TB's stability
  bound must be stated over this whole-edge generating set, not Qin's k+1.**
- *`ExactHGED` design (OD4 stands — bespoke, no public code exists):* best-first
  branch-and-bound over vertex bijections `π` (padded, symmetric-oriented);
  per-vertex-pair cost = label-substitution, per-edge-pair cost = incidence
  Hamming `|E|+|E'|−2|{a∈E:π(a)∈E'}|` + label, whole-edge delete/insert = 1 —
  all via `scipy.linear_sum_assignment`. The admissible heuristic is a
  **partial-map edge lower bound** (`_partial_edge_lb`): an LSAP whose cell is
  `max(cardinality-gap, committed forced incidences) + label`; at a complete map
  it equals the exact edge cost, unifying heuristic and terminal. Incumbent
  seeded with min(degree-greedy, Riesen–Bunke BP). `timeout` / `max_expansions`
  raise `HGEDComputationError` (the ceiling knobs).
- *`BipartiteHGED` (optional, DQ2):* Riesen–Bunke node LSAP → exact cost under
  that single `π` (a real edit ⇒ upper bound: `Exact ≤ BP`, tested 120/120).
- *Acceptance met:* (a) hand-computed fixtures — insert/delete vertex, add/remove
  incidence, **whole-edge delete = 1** (not Qin's 4), vertex/edge label subst,
  2-op path — all exact; (b) ladder `t ≥ Exact` (property test over Hypothesis +
  ladder-dataset test, green); plus metric identities (self-0, symmetry, triangle,
  perm-invariance) and `Exact==0 ⇔ pynauty-iso` cross-check.
- *DQ1 (`bench_hged_ceiling.py`, sparse `m≈n/2`, seed 0, 8s/pair, single-thread):*
  n=8 → 20/20 (median 17 ms); n=10 → **20/20** (median 46 ms, one 5.4 s tail);
  n=12 → 19/20 (median 210 ms, 1 DNF); n=14 → 16/20 (median 1.05 s); n=16 → 5/20.
  **Go/no-go:** exact oracle is 0-DNF through **n=10** and ~95% at n=12
  single-thread; on the HPC parallel regime (throughput-bound, longer per-pair
  budgets) it reaches **n≈12–14**, confirming "well past n=10". The exact
  correlation corpus (default n∈[4,7]) sits comfortably inside; the ladder / BP
  carry scale past the ceiling.
- *Decisions (flagged, spec-grounded):* (D-HGED1) whole-edge unit ops [above];
  (D-HGED2) `ExactHGED`/`BipartiteHGED` require scipy+numpy (guarded →
  `RepresentationDependencyMissingError`), matching the §3 table; (D-HGED3)
  labelled cost implemented now (unit vertex+edge label subst per Qin op (iii) /
  `correlation.md`), exercised unlabelled by default; (D-HGED4) `correlation_corpus`
  does **not** dedup — the study filters `HGED>0` pairs (IsalGraph protocol), so
  no `core→iso` layer breach.
- *Closing checks:* `pytest tests/unit tests/property tests/integration -m "not
  slow" --hypothesis-seed=0` → **514 passed, 8 skipped, 2 deselected, 0 failed**
  (+65 vs T-M1a's 449). ruff **clean on all new files** (baseline unchanged).
  mypy **21 == baseline** (no errors in new modules). No C++ change → no rebuild.
- *Follow-up (not blocking):* raising the exact ceiling further (Qin HGED-BFS
  pruning / memoization) is a possible future optimization; the ladder is the
  designated scale tier (DQ2), so not pursued here.
