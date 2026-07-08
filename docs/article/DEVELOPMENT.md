# IsalHG metric-space article — task ledger

Living, append-only task ledger for the metric-space journal article (target
*Information Sciences*). Scope docs live alongside this file in `docs/article/`;
this file tracks the *work*. Distinct from `docs/engineering/DEVELOPMENT.md`, which remains
the iso-benchmark / preprint code-as-built log.

## How to use this file

- **Pick up a task** with the `task-reader` skill (`/task-reader T-M0`). It reads
  the task, all its cited context, and the coding rules, then plans before
  touching code.
- **Add a task** with the `task-handoff` skill when you find out-of-scope work
  mid-development. It appends a new entry here with a live timestamp and the
  context pointers the next agent needs. Never solve out-of-scope work inline.
- **Timestamps** are wall-clock at declaration, captured via
  `date '+%Y-%m-%d %H:%M %Z'`. Entries are append-only; do not reorder or rewrite
  existing entries except to update their `Status` and paste closing-check output.

## Status legend

`OPEN` — declared, not started · `IN-PROGRESS` — actively worked ·
`BLOCKED` — waiting on a decision/dependency · `DONE` — acceptance check passed.

## Where HGED is (and is not) needed — the scope decision (2026-07-08)

HGED is load-bearing for exactly three things: the **stability theorem** (T-TB,
its right-hand side), the **Layer-1 correlation** that validates the theorem
(T-M5a), and the **head-to-head vs competitors** (the axis on which `d_I` beats
the canonical-form baselines). The **applications — MDS, clustering, kNN,
shortest path (T-M5b–e) — do NOT use HGED**; they self-validate on task metrics
(ARI vs planted labels, accuracy, stress). Consequences:
- The applications can run on **larger real hypergraphs** than the exact-HGED
  ceiling allows — their scale is gated by `w*` (and competitor) wall-clock
  (T-DQ3'), **not** by HGED.
- HGED will be computed on **HPC with high parallelism**, so the exact-oracle
  `n`-ceiling for the density sweep goes **well past n=10** (T-M2 benchmarks it).
- BP-HGED demotes to an **optional** ladder-cross-check, not a blocker.

## Milestone dependency graph

```
T-M0 ✔ seed optimization (DONE)

T-M1a  metric_space foundation (ABC + registry + errors/types + levi→core + edit ops)
   ├─► T-M1b  d_I + WL distances
   ├─► T-M2   HGED oracle (ExactHGED + ladder; BP optional)          [HGED track]
   ├─► T-M3a..d competitors (nauty-edit / HPD / NetLSD / HyperCOT)
   └─► T-M4   planted-family datasets + scoring primitives

T-M4'  HIC atlas loader (independent) ─► real-anchor apps + gates T-DQ3'

experiments:
   T-M5a  correlation / density-sweep / info-content   ← M1b, M2, M4     [needs HGED]
   T-M5b MDS · M5c clustering+dendrogram · M5d kNN · M5e shortest-path
                        ← M1b, M3a–d, M4 (+ M4' for the real anchor)      [HGED-free]

theory (parallel):  T-TA completeness ─► T-TB stability (informed by M5a data)
last:               T-M6 isomorphisms/ reparent (optional)
handoffs:           T-M0a, T-M0b
```

**Runnable in parallel right now** (M0 done): **T-TA** (completeness — theory,
no deps), **T-M1a** (foundation — no deps), **T-M4'** (HIC loader — independent).
After T-M1a lands: T-M1b, T-M2, T-M3a–d, T-M4 fan out. After those: T-M5a–e.
Use isolated git worktrees for agents that touch overlapping `core/` files.

---

## Task ledger

### T-M0 — Seed-selection optimization (label → degree → lex-max neighbour-degree)
**Declared:** 2026-07-08 12:20 CEST
**Status:** DONE
**Depends on:** —
**Context to read first:**
- `docs/article/CODE_DESIGN.md` §6 ("Seed-selection optimization") — the spec
- `docs/article/PROPOSAL.md` §6 — the PI directive it implements
- `docs/article/theoretical/stability.md` §3 ("avalanche obstruction") — why fewer seeds shrink the avalanche surface
- `src/isalhg/core/structural_tuples.py::max_xi_nodes` and `::max_neighbor_degree_nodes` — the existing seeders to extend (the second, PI 2026-06-23, is the starting point)
- `src/isalhg/core/canonical.py::_python_canonical_string` — the dispatch site
- `src/isalhg/core/_native/include/isalhg/structural_tuples.hpp` and `src/isalhg/core/_native/src/canonical.cpp::canonical_string_compute` — the C++ twin + variant enum
- `tests/property/test_canonical_invariance.py` — the iso-invariance guard-rail
- IsalGraph paper `/media/mpascual/Sandisk2TB/research/ISAL/completed/isalgraph/article/69b82c5859ed47c5468ca199/methodology.tex` — seed-selection precedent
- `.claude/rules/coding_rules.md` — always
**Description:** Refine the H2S seed set to fewer starting nodes — maximal label,
then maximal degree, then lexicographically-maximal decreasing neighbour-degree
list — preserving isomorphism-invariance of `w*`, in both the Python reference
and the C++ core. Shrinks `w*` wall-clock (unblocks every downstream sweep) and
reduces the stability-theorem avalanche surface.
**Acceptance:** `tests/property/test_canonical_invariance.py` green under
Hypothesis (`--hypothesis-seed=0 --hypothesis-deadline=none`); iso-backend
partition agreement unchanged; measured wall-clock drop reported on the design
fixtures (Fano / STS(9) / STS(13) / GQ(2,2)).
**Out of scope here:** the pruned-backtracking variant (`canonical_pruned.py`) —
that is the separate Algorithm-R&D track; the stability *proof* (T-TB).
**Closing (2026-07-08 13:13 CEST):**
- *Premise correction:* the three-level cascade was **already implemented** (PI
  2026-06-23) in both `_python_max_neighbor_degree_nodes` and the C++ twin
  `max_neighbor_degree_nodes_compute`, wired as variants `greedy_min_nbrdeg`(5) /
  `greedy_single_nbrdeg`(6). The task therefore reduced to **validate → promote →
  measure**, not writing the seeder.
- *Promotion (global flip, per PI decision this session):* default `algorithm`
  → `"greedy_min_nbrdeg"` at all three surfaces — `canonical_string`,
  `IsalHGBackend.__init__`, `_DEFAULT_ISALHG_ALGORITHM` (env override
  `ISALHG_ALGORITHM` preserved, so the preprint pipeline is unaffected).
  Registered `isalhg_greedy_min_nbrdeg` / `isalhg_greedy_single_nbrdeg` backends.
  Updated Critical Invariant #4 (CLAUDE.md) + the `max_xi_nodes` "only admissible"
  docstring to "any iso-invariant seed set".
- *(a) property test:* `test_canonical_invariance.py` parametrized over
  `{greedy_min, greedy_min_nbrdeg}` — green under Hypothesis, `--hypothesis-seed=0`,
  incl. pynauty cross-check. Python≡C++ locked via `test_backend_equivalence.py`
  (nbrdeg added). New `tests/unit/iso_backends/test_isalhg_nbrdeg.py`.
- *(b) partition agreement:* `test_nbrdeg_partition_matches_pynauty` — the nbrdeg
  backend induces the **same iso-partition** as pynauty on {Fano, Fano′, STS(9),
  STS(9)′, STS(13)_a, STS(13)_b}. `w*` is **identical** to the ξ seeder on every
  design fixture (empirically verified).
- *(c) wall-clock:* `scripts/bench_seed_selection.py`. Honest result: **no drop in
  the default parallel regime** (parity) — the designs are vertex-transitive
  (identical seed sets) and the C++ pool parallelizes the fan-out (critical-path-
  bound). The seed-count win (gq22: 10→7) surfaces only under core saturation:
  `taskset -c 0` gives **1.34× on gq22** (561→420 ms), parity on the transitive
  designs. "Shrinks `w*` wall-clock" is really "shrinks seed-count / CPU work,"
  realized as wall-clock only on saturated cores; promotion stands on
  correctness + avalanche-surface reduction + never regressing.
- *Closing checks:* `pytest tests/unit tests/property tests/integration
  -m "not slow" --hypothesis-seed=0` → **408 passed, 8 skipped, 0 failed** (after
  fixing 3 pre-existing stale `name` assertions surfaced by the flip:
  `test_isalhg_backend.py`, `iso_backends/test_registry.py`,
  `protocols/test_fingerprint_timing.py`). ruff/mypy: **no new violations** (mypy
  baseline == current == 21 pre-existing `resolve()`-dispatch errors; 3 pre-existing
  ruff violations, none in changed logic). No C++ change → no rebuild.
- *Handoffs spawned:* T-M0a (conftest `gq_2_2_doily` is not a valid GQ(2,2)),
  T-M0b (Python `_neighbour_degree_key` rebuilds `primal_graph()` per node).

### T-M1a — `metric_space/` foundation + shared promotions
**Declared:** 2026-07-08 12:20 CEST · **split from T-M1** 2026-07-08 13:40 CEST
**Status:** OPEN
**Depends on:** — (parallel-safe with the now-DONE T-M0; use an isolated worktree)
**Context to read first:**
- `docs/article/CODE_DESIGN.md` §3 ("HypergraphDistance"), §4 (shared promotions), §5 (errors/types)
- `docs/article/empirical/correlation.md` — how `matrix()` feeds the study
- `src/isalhg/iso_backends/levi_reduction.py` — the module to move to `core/` (+ its 3 importers: `pynauty_levi`, `bliss_levi`, `traces_levi`)
- `src/isalhg/core/sparse_hypergraph.py::permute` — pattern for the new edit ops
- `src/isalhg/iso_backends/base.py` and `registry.py` — ABC + registry pattern to mirror
- `.claude/rules/coding_rules.md` — always
**Description:** The foundation every metric-space task builds on. Create
`metric_space/{base,registry}` with the `HypergraphDistance` ABC
(`pairwise`/`matrix`); move `levi_reduction` → `core/levi_reduction.py` (update
the three iso backends); add the six structural edit ops (vertex/hyperedge/
incidence ins-del + `random_edit` + `edit_path`) to `core/sparse_hypergraph.py`;
extend `errors.py` (`MetricSpaceError` hierarchy) and `types.py` (`DistanceName`,
numpy-free). **No concrete distance yet.**
**Acceptance:** package imports; ABC+registry unit-tested via a trivial stub
distance; the six edit ops each unit-tested (incidence changes as expected);
iso-backend tests still green after the `levi_reduction` move; full suite + ruff
+ mypy green.
**Out of scope here:** any concrete distance (T-M1b), HGED (T-M2), competitors
(T-M3a–d), the `isomorphisms/` reparent (T-M6).

### T-M1b — `IsalHGLevenshtein` (`d_I`) + `HypergraphWLDistance`
**Declared:** 2026-07-08 13:40 CEST (split from T-M1)
**Status:** OPEN
**Depends on:** T-M1a
**Context to read first:**
- `docs/article/CODE_DESIGN.md` §3 (table), §3.1 (rapidfuzz decision)
- `docs/article/COMPETITORS.md` §2 — the WL baseline
- `src/isalhg/core/canonical.py` — `w*` entry point for `d_I`
- `src/isalhg/core/hypergraph_wl.py` — reused by `HypergraphWLDistance`
- `.claude/rules/coding_rules.md` — always
**Description:** Implement the first two `HypergraphDistance` subclasses:
`IsalHGLevenshtein` (`d_I` = raw Levenshtein on `w*`, rapidfuzz-guarded; raw is
primary, normalized/token-aware are ablation kwargs) and `HypergraphWLDistance`
(wraps `core.hypergraph_wl`, L1/χ² on the colour-count vector). Register both.
**Acceptance:** `d_I` = 0 on isomorphic design-fixture pairs, > 0 otherwise;
`d_I.matrix()` and `WL.matrix()` run on a 10-item corpus; suite green.
**Out of scope here:** HGED (T-M2), the other competitors (T-M3a–d).

### T-M2 — HGED oracle + correlation corpora
**Declared:** 2026-07-08 12:20 CEST · **rescoped** 2026-07-08 13:40 CEST
**Status:** OPEN
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
**Acceptance:** exact HGED matches hand-computed edit counts on tiny fixtures;
ladder budget `t` ≥ exact HGED on the same pairs; exact-oracle `n`-ceiling
benchmarked on the HPC parallel regime and reported (DQ1).
**Out of scope here:** the correlation *experiment* itself (T-M5a); competitor
distances (T-M3a–d).

### T-M3a — `NautyLeviEditDistance` (contrast baseline)
**Declared:** 2026-07-08 13:40 CEST (split from T-M3)
**Status:** OPEN
**Depends on:** T-M1a
**Context to read first:**
- `docs/article/COMPETITORS.md` §2–§3 — the *contrast* role (iso-only, no navigable geometry)
- `src/isalhg/iso_backends/pynauty_levi.py` + `src/isalhg/core/levi_reduction.py` (post-M1a)
- `.claude/rules/coding_rules.md` — always
**Description:** `HypergraphDistance` computing string-edit distance between the
nauty canonical forms of the Levi graphs. The deliberate contrast that *fails*
A4 (shortest path). Register in `metric_space/registry.py`.
**Acceptance:** `matrix()` runs on the correlation corpus; distance 0 on
isomorphic pairs; guarded `pynauty` import raises `RepresentationDependencyMissingError`.
**Out of scope here:** the head-to-head study (T-M5a).

### T-M3b — `HPDDistance` (Hyperedge Portrait Divergence, vendored MIT)
**Declared:** 2026-07-08 13:40 CEST (split from T-M3)
**Status:** OPEN
**Depends on:** T-M1a
**Context to read first:**
- `docs/article/COMPETITORS.md` §2 · `docs/article/RELATED_WORK.md` §Competitors — Agostinelli et al. 2026, `cosimoagostinelli/Hor_dissimilarity_measures`
- `docs/article/CODE_DESIGN.md` §3.2 — vendoring strategy
- `.claude/rules/coding_rules.md` — always
**Description:** Vendor the HPD function (MIT) into `representations/_hpd_vendor.py`
(provenance header); wrap as a `HypergraphDistance` (hyperedge-path tensor →
Jensen–Shannon). Register.
**Acceptance:** `matrix()` runs on the correlation corpus; numpy/scipy-only guard.
**Out of scope here:** Hyper-NetSimile (the sibling measure — skip unless needed).

### T-M3c — `NetLSDDistance` (optional spectral, pip)
**Declared:** 2026-07-08 13:40 CEST (split from T-M3)
**Status:** OPEN
**Depends on:** T-M1a
**Context to read first:**
- `docs/article/COMPETITORS.md` §2 (optional spectral) · `RELATED_WORK.md` — Tsitsulin et al. 2018, `pip install netlsd`
- `src/isalhg/core/levi_reduction.py` (post-M1a) — heat-trace on the Levi/clique expansion
- `.claude/rules/coding_rules.md` — always
**Description:** `HypergraphDistance` = L2 between NetLSD heat-trace signatures of
the Levi expansion. Register. (Optional fifth competitor.)
**Acceptance:** `matrix()` runs; guarded `netlsd` import.
**Out of scope here:** promoting it to a headline baseline (it is the spectral aside).

### T-M3d — `HyperCOTDistance` (pinned conda env, subprocess)
**Declared:** 2026-07-08 13:40 CEST (split from T-M3)
**Status:** OPEN
**Depends on:** T-M1a
**Context to read first:**
- `docs/article/COMPETITORS.md` §2 (dual role: theory anchor + competitor) · `RELATED_WORK.md` — Chowdhury et al. 2024, `samirchowdhury/HyperCOT` (pins `hypernetx==1.2`, `POT==0.8.0`)
- `docs/article/CODE_DESIGN.md` §3.2 — `SubprocessRepresentation`
- `src/isalhg/iso_backends/subprocess_base.py` — the subprocess pattern to mirror
- `.claude/rules/coding_rules.md` — always
**Description:** `SubprocessRepresentation` base + `HyperCOTDistance`: serialize
the corpus, shell out to a dedicated `isalhg-hypercot` conda env, parse back the
distance matrix. Register. Heaviest/most independent competitor.
**Acceptance:** `matrix()` runs on the correlation corpus via the pinned env;
distance 0 on isomorphic pairs; `SubprocessRepresentationError` with a setup hint
when the env is absent.
**Out of scope here:** the head-to-head study (T-M5a); a learned/GNN baseline (dropped).

### T-M4 — Planted-family datasets + metric-space scoring primitives
**Declared:** 2026-07-08 12:20 CEST · **retargeted** 2026-07-08 13:40 CEST
**Status:** OPEN
**Depends on:** T-M1a
**Context to read first:**
- `docs/article/DATA.md` §2 — the non-iso planted-family constraint (the iso-copy trap)
- `docs/article/CODE_DESIGN.md` §7 (datasets), §3 tree (metrics)
- `docs/article/empirical/applications.md` — what the metrics score
- `docs/article/empirical/correlation.md` §Information content — the bits estimator
- `src/isalhg/datasets/synthetic/exhaustive_small.py` — dataset ABC + registry pattern (fix its module-level iso import to lazy)
- `.claude/rules/coding_rules.md` — always
**Description:** `datasets/synthetic/planted_families.py` (non-isomorphic,
seed-stable within-family members; family = label) and
`metric_space/metrics/{association,information,embedding}` (Spearman/MI,
fixed-width-code bits, classical-MDS solve + stress + PSD check).
**Acceptance:** planted corpus verified non-isomorphic within family (dedup
check) with known labels; each metric primitive unit-tested against a
hand-computed value.
**Out of scope here:** running MDS/clustering/kNN (T-M5b–e, experiments); standard
sklearn indices (called in experiments, not re-wrapped).

### T-M4' — HIC atlas loader (real-anchor + gates T-DQ3')
**Declared:** 2026-07-08 13:40 CEST
**Status:** OPEN
**Depends on:** — (independent dataset loader)
**Context to read first:**
- `docs/article/DATA.md` §3 — the real-anchor role + scaling caveat
- `src/isalhg/datasets/hic_atlas.py` — the current stub (all methods `NotImplementedError`)
- `src/isalhg/datasets/synthetic/exhaustive_small.py` — the `HypergraphDataset` ABC + registry pattern
- `.claude/rules/coding_rules.md` — always
**Description:** Implement the `hic_atlas` loader (`github.com/iMoonLab/HIC`,
Apache-2.0) yielding whole-hypergraph instances with class labels (e.g.
IMDB→genre). Unblocks (a) T-DQ3' (`w*` timing on a real instance) and (b) the
**HGED-free** applications (MDS/clustering/kNN) on larger real hypergraphs.
**Acceptance:** loads ≥1 HIC dataset as a `HypergraphDataset` with instances +
labels; per-instance size stats (n, m, arity) reported; unit + integration test.
**Out of scope here:** the application pipeline (T-M5b–e); the `w*` timing (T-DQ3').

### T-M5a — Correlation / density-sweep / information-content (Layer 1; NEEDS HGED)
**Declared:** 2026-07-08 13:40 CEST (split from T-M5)
**Status:** OPEN
**Depends on:** T-M1b, T-M2, T-M4 (+ any T-M3* competitors to include)
**Context to read first:**
- `docs/article/empirical/correlation.md` — E1/E2/E2b/E3 + acceptance
- `docs/article/theoretical/stability.md` §4 — the Δ-prediction the sweep tests
- `docs/article/CODE_DESIGN.md` §9 — the src/experiments boundary
- `experiments/preprint/` — the pipeline pattern; `experiments/orchestrator.py`
- `.claude/rules/coding_rules.md` — always
**Description:** `experiments/article/` runner that caches `D` matrices per
`(distance, dataset, seed)`, then: correlation (Spearman/Pearson/MI) of `d_I` and
each competitor vs HGED; the **density sweep** (n>10 on HPC) testing the `C(k,Δ)`
Δ-prediction; single-edit sensitivity histogram (E2b); information-content bits +
one-sided Wilcoxon. No `src/` changes.
**Acceptance:** reproduces `correlation.md` closing criteria; ρ-vs-Δ figure shows
the predicted decay.
**Out of scope here:** the applications (T-M5b–e); new `src/` code (`task-handoff` it).

### T-M5b — MDS (flagship application; HGED-FREE)
**Declared:** 2026-07-08 13:40 CEST (split from T-M5)
**Status:** OPEN
**Depends on:** T-M1b, T-M3a–d, T-M4 (+ T-M4' for the real anchor)
**Context to read first:**
- `docs/article/empirical/applications.md` §A1 — method + CV dimension selection
- `docs/article/CODE_DESIGN.md` §9 — boundary (classical-MDS solve is a `src` primitive; CV/SMACOF/figures in experiments)
- `.claude/rules/coding_rules.md` — always
**Description:** Classical + SMACOF MDS on `D_I` and each competitor; CV
dimension selection (primary), Mardia ratios, negative-eigenvalue floor; stress;
PSD report; Shepard diagram. Runs on the planted corpus and — if T-DQ3' is green
— a larger real HIC corpus. **No HGED.**
**Acceptance:** reproduces `applications.md` §A1 criteria; `D̂` reported per
representation; figures render.
**Out of scope here:** clustering/kNN/path (M5c–e); new `src/` code.

### T-M5c — Clustering + dendrogram (HGED-free)
**Declared:** 2026-07-08 13:40 CEST (split from T-M5)
**Status:** OPEN
**Depends on:** T-M1b, T-M3a–d, T-M4 (+ T-M4' for the real anchor)
**Context to read first:**
- `docs/article/empirical/applications.md` §A2 — k-medoids + dendrogram, metrics
- `.claude/rules/coding_rules.md` — always
**Description:** k-medoids (PAM) + agglomerative dendrogram on `D_I` and
competitors; silhouette/Dunn/DB + ARI/NMI vs planted labels; cophenetic
correlation. Report metrics vs density (ties back to Theorem B). **No HGED.**
**Acceptance:** reproduces `applications.md` §A2 criteria; figures render.
**Out of scope here:** MDS/kNN/path; new `src/` code.

### T-M5d — kNN classification (HGED-free)
**Declared:** 2026-07-08 13:40 CEST (split from T-M5)
**Status:** OPEN
**Depends on:** T-M1b, T-M3a–d, T-M4 (+ T-M4' for the real labelled anchor)
**Context to read first:**
- `docs/article/empirical/applications.md` §A3 — kNN, metrics
- `docs/article/DATA.md` §2–§3 — labelled corpora (planted families; HIC real)
- `.claude/rules/coding_rules.md` — always
**Description:** kNN in `(·, d_I)` and competitors, LOO/stratified CV; accuracy,
macro-F1, AUC vs `k`. Planted-family labels + (if T-M4' loaded) HIC class labels.
**No HGED.**
**Acceptance:** reproduces `applications.md` §A3 criteria; figures render.
**Out of scope here:** MDS/clustering/path; new `src/` code.

### T-M5e — Shortest path between hypergraphs (differentiator; HGED-free)
**Declared:** 2026-07-08 13:40 CEST (split from T-M5)
**Status:** OPEN
**Depends on:** T-M1b, T-M3a (contrast), T-M4
**Context to read first:**
- `docs/article/empirical/applications.md` §A4 — the differentiator competitors cannot do
- `.claude/rules/coding_rules.md` — always
**Description:** Minimal-`d_I` path `H_A→H_B` through an intermediate pool;
recovered-path length vs HGED-geodesic; show nauty-contrast cannot navigate.
**No HGED for scoring** (HGED-geodesic only on the small corpus as a reference).
**Acceptance:** reproduces `applications.md` §A4 criteria; figures render.
**Out of scope here:** MDS/clustering/kNN; new `src/` code.

### T-M6 — (optional) reparent iso packages under `isomorphisms/`
**Declared:** 2026-07-08 12:20 CEST
**Status:** OPEN
**Depends on:** T-M1a..T-M5e (do last; cosmetic)
**Context to read first:**
- `docs/article/CODE_DESIGN.md` §2 (target tree), §8 (dependency direction)
- `.claude/rules/coding_rules.md` §2 (refactor protocol)
**Description:** Move `iso_backends/`, iso `protocols/`, iso `metrics/`
(correctness, partition) under `isalhg/isomorphisms/`; update registries,
experiments, tests. Pure move + import rewrite.
**Acceptance:** full test suite + ruff + mypy green; no behaviour change.
**Out of scope here:** any functional change; the shared `metrics/{runtime,
complexity_fit}` stay top-level.

### T-TA — Completeness (Theorem A) for IsalHG
**Declared:** 2026-07-08 12:20 CEST
**Status:** OPEN
**Depends on:** —
**Context to read first:**
- `docs/article/theoretical/stability.md` §1 — statement + status
- `CLAUDE.md` §"Mathematical Foundation (brief)" — the conjecture
- IsalGraph paper `methodology.tex` (Theorem 1) — the proved graph analogue to port
- `.claude/rules/coding_rules.md` — always (for any test artefacts)
**Description:** Prove `w*(H1)=w*(H2) ⇔ H1≅H2` for IsalHG, or produce an airtight
empirical completeness section. Prerequisite for the metric property (Cor. A).
**Acceptance:** a written proof reviewed by the PI, or a completeness experiment
over a large sampled + design-fixture corpus with zero counterexamples.
**Out of scope here:** the stability bound (T-TB).

### T-TB — Stability (Theorem B) incl. Lemma B1
**Declared:** 2026-07-08 12:20 CEST
**Status:** OPEN
**Depends on:** T-TA (metric property), informed by T-M5a (empirical `s(e)` data)
**Context to read first:**
- `docs/article/theoretical/stability.md` §2–§4 — statement, reduction, avalanche, theory↔empirics
- `docs/article/RELATED_WORK.md` — TMD (proof template), co-OT (Levi-Lipschitz), FSW-GNN (one-sided justification)
- `src/isalhg/core/hypergraph_to_string.py::_encode_from`, `src/isalhg/core/cdll.py` — the CDLL-index hazard (Lemma B1)
- `.claude/rules/coding_rules.md` — always
**Description:** Prove `d_I(H,H') ≤ C(k,Δ)·HGED(H,H')`; resolve Lemma B1's
CDLL-index hazard (relative vs absolute order); if the worst-case bound is
unattainable, prove the average-case / high-probability form.
**Acceptance:** a written proof (or conditional/average-case theorem) whose
predicted `C(k,Δ)` Δ-dependence matches the T-M5a density-sweep data.
**Out of scope here:** implementing the experiments (T-M5a–e).

### T-DQ3' — Measure `w*` wall-clock on a HIC instance (real-anchor gate)
**Declared:** 2026-07-08 12:20 CEST
**Status:** OPEN
**Depends on:** T-M0 (DONE — seed-optimized `w*`), T-M4' (HIC loader)
**Note (2026-07-08):** raised in value — since applications are now HGED-free,
`w*` wall-clock is the *only* gate on running MDS/clustering/kNN at real scale,
so this one measurement decides how large the application corpora can be.
**Context to read first:**
- `docs/article/DATA.md` §3 (DQ3') — why this decides the real anchor
- `src/isalhg/datasets/hic_atlas.py` — the (stubbed) loader
- `src/isalhg/core/canonical.py` — the `w*` entry point to time
- `.claude/rules/coding_rules.md` — always
**Description:** Time `canonical_string` on one real HIC IMDB instance (post
T-M0 + C++). One number decides whether a real-world anchor (A1/A2 at scale) is
in scope or the paper stays on synthetic + small designs.
**Acceptance:** a reported wall-clock (seconds/minutes/DNF) on a named HIC
instance, with a go/no-go recommendation for the real anchor.
**Out of scope here:** building the full HIC application pipeline (deferred to T-M5b–e).

### T-M0a — conftest `gq_2_2_doily` is not a valid GQ(2,2)
**Declared:** 2026-07-08 13:13 CEST (handoff from T-M0)
**Status:** OPEN
**Depends on:** —
**Context to read first:**
- `tests/conftest.py` — the `gq_2_2_doily` fixture (hardcoded 15-line edge list)
- `tests/property/test_backend_equivalence.py::_doily` — the CORRECT construction (points = 2-subsets of {1..6}, lines = perfect matchings of {1..6})
- `docs/article/theoretical/stability.md` §3 — lists GQ(2,2) among the vertex-transitive designs; the fixture must actually be vertex-transitive for that claim to hold
- `.claude/rules/coding_rules.md` — always
**Description:** The `gq_2_2_doily` fixture's hardcoded edge list is not a valid
generalised quadrangle: lines `{5,10,13}` and `{10,13,14}` share the pair
`{10,13}` (two lines meeting in two points violate the partial-linear-space
axiom), and the primal graph is not 6-regular (vertex 13 has degree 5), so it is
not vertex-transitive and not the doily. Replace the edge list with the
matching-based construction already in `test_backend_equivalence.py::_doily`
(or share that builder). Found during T-M0: the fixture's asymmetry is why the
nbrdeg seeder drops 10→7 seeds on it (a valid hypergraph, wrong *design*).
**Acceptance:** fixture is 3-uniform, 15 points / 15 lines, primal graph
6-regular (srg(15,6,1,3)); `max_neighbor_degree_nodes` returns all 15 (vertex-
transitive); any golden/partition test using the fixture updated + green.
**Out of scope here:** T-M0's promotion (it flags the fixture with `*` and does
not depend on it being the true doily).

### T-M0b — Python `_neighbour_degree_key` rebuilds `primal_graph()` per node
**Declared:** 2026-07-08 13:13 CEST (handoff from T-M0)
**Status:** OPEN
**Depends on:** —
**Context to read first:**
- `src/isalhg/core/structural_tuples.py::_neighbour_degree_key` + `::_python_max_neighbor_degree_nodes`
- `src/isalhg/core/sparse_hypergraph.py::primal_graph` (line 254) — uncached; rebuilds the adjacency dict every call
- `.claude/rules/coding_rules.md` — always
**Description:** `_python_max_neighbor_degree_nodes` builds `adj = H.primal_graph()`
once, but `_neighbour_degree_key` calls `H.primal_graph()` again per survivor
node, so the adjacency is rebuilt `(1 + m)` times — `O((1+m)·Σ|e|²)`. Reference
(Python) path only; the C++ default seeder uses the prebuilt `primal_adj` and is
unaffected. Fix: thread `adj` into `_neighbour_degree_key` (2-line change);
optionally memoise `primal_graph` on `SparseHypergraph` (broader — also helps the
`xi` BFS).
**Acceptance:** `_neighbour_degree_key` consumes a passed-in `adj`; no behaviour
change (`test_backend_equivalence.py` + `test_canonical_invariance.py` green);
`primal_graph` built once per seeder call.
**Out of scope here:** the C++ path (already uses prebuilt adjacency); a general
`primal_graph` cache is a separate decision.

---

## Decisions pending PI (mirror `CODE_DESIGN.md` §11)

- **OD1** — Architecture: additive `metric_space/` now (recommended) vs also
  reparenting to `isomorphisms/` (T-M6, optional/last).
- **OD2** — `levi_reduction` home: `core/levi_reduction.py` (recommended) vs a
  new shared `reductions/` package.
- **OD3** — HyperCOT: dedicated pinned conda env via subprocess (recommended).
- **OD4** — **[resolved 2026-07-08]** `ExactHGED` = our own A*/ILP over the six
  edit ops. The `networkx.graph_edit_distance`-on-Levi wrapper is rejected: GED
  on the bipartite Levi graph is not obviously equal to HGED (vertex/edge nodes
  differ semantically; the cost-lift needs an unproven correctness argument).
- **OD5** — `metric_space/metrics/embedding.py`: keep the classical-MDS solve +
  stress as a `src` primitive (recommended) vs push all of MDS into experiments.
