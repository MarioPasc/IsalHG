# IsalHG code design — metric-space article extension

**Status:** ACTIVE (v3 rescope 2026-07-18; structure unchanged from the
2026-07-08 design — the rescope changes *which studies run*, §9, not where code
goes). Design document for the `src/isalhg` refactor + additions required by
the metric-space article (`PROPOSAL.md`, `theoretical/`, `empirical/`,
`COMPETITORS.md`, `DATA.md`). Pairs with the repo-level
`docs/engineering/CODE_DESIGN.md` (the iso-benchmark code map, still
authoritative for the code as built). **This document does not remove
iso-detection code; it extends the package and separates the two concerns.**

Grounded on a full survey of the *actual* tree (2026-07-08), not the aspirational
map — see "Current state" below.

---

## 0. Guiding constraints

1. **Preserve iso-detection.** `iso_backends`, the iso `protocols`, and iso
   `metrics` (correctness, partition) keep working unchanged in behaviour.
2. **Separate the two concerns** structurally: iso-detection vs metric-space.
3. **Execution and statistics stay out of `src/`.** `src/` provides *distances*
   and *stateless scoring primitives* (pure functions of hypergraphs / strings /
   matrices). Running MDS / k-medoids / kNN / shortest-path, cross-validation,
   hypothesis tests, bootstrap CIs, and figures live in `experiments/`.
4. **Reuse before build.** WL exists (`core/hypergraph_wl.py`); the Levi encoder
   exists (`iso_backends/levi_reduction.py`); the canonical string exists
   (`core/canonical.py`). New code wraps these; it does not duplicate them.
5. **`core/` stays stdlib-only.** Verified clean today; keep it that way.
6. **Optional deps are guarded** (import inside method bodies), mirroring the
   adapter / subprocess pattern already in the repo.

---

## 1. Current state (survey 2026-07-08)

- `core/` — stdlib-only (verified: no numpy/networkx/xgi/torch). Holds the VM,
  `canonical.py`, `hypergraph_to_string.py`, `structural_tuples.py` (seed
  selection), `hypergraph_wl.py`, `sparse_hypergraph.py` (with `permute`), and a
  C++ extension `_core` compiled from `_native/`. **stdlib-only guarantee is a
  load-bearing asset — do not break it.**
- `structural_tuples.py` already exposes **two** seeders: `max_xi_nodes`
  (BFS-shell) and `max_neighbor_degree_nodes` (PI 2026-06-23), each with a C++
  twin in `_native/include/isalhg/structural_tuples.hpp`. Algorithm variants
  `greedy_min_nbrdeg` / `greedy_single_nbrdeg` already route to the latter.
- **Package default (T-TAd, 2026-07-09; renamed at T-TAg):** the canonical
  algorithm defaults to `"canonical"` — the frozen `w*_c` (D-TA2) — at all three
  surfaces:
  `canonical_string`/`canonical_fingerprint`, `IsalHGBackend` (the
  `ISALHG_ALGORITHM` env override is preserved), and `IsalHGLevenshtein`. The
  greedy variants stay registered as fast one-sided heuristics (the preprint's
  measurement apparatus).
- `iso_backends/` — all four backends implemented; `levi_reduction.py` (108 LOC)
  imported module-level by `pynauty_levi`, `bliss_levi`, `traces_levi`.
- `metrics/` — `correctness` + `runtime` implemented; `partition` +
  `complexity_fit` are STUBs.
- `datasets/` — `exhaustive_small`, `symmetric_designs`, `erdos_renyi` real;
  `chung_lu`, `hardness`, `arb_benson`, `hic_atlas`, `xgi_loader` STUBs.
  **Architecture violation:** `synthetic/exhaustive_small.py` imports
  `isalhg.iso_backends.{base,registry}` at *module* level (lines 36–37),
  contradicting `datasets/__init__.py`. Fix to a lazy import during this refactor.
- `viz/` — a real, undocumented package (visualization; imports core + adapters).
  Shared; unaffected.
- **No string-distance, Levenshtein, edit-distance, MDS, medoid, or silhouette
  code exists anywhere** in `src/`, `tests/`, or `experiments/`. The metric-space
  layer is greenfield.
- `experiments/` — root `orchestrator.py` real; `analysis/{aggregate,stats}` are
  STUBs; the active analysis pipeline lives under `experiments/preprint/`.

---

## 2. Target architecture

Two concerns as sibling packages, with shared primitives at the top level.
`core` stays shared because `w*(H)` feeds **both** iso fingerprints and the
metric-space distance.

```
src/isalhg/
  types.py            shared (keep import-light: core imports it, so NO numpy at module level)
  errors.py           shared (+ metric-space exception hierarchy, §5)
  core/               shared, stdlib-only
    …                 unchanged VM / canonical / string
    structural_tuples.py   ← seed-selection optimization lands here (+ _native twin)  [§6]
    sparse_hypergraph.py   ← gains structural edit ops (vertex/edge/incidence ins-del) [§6]
    levi_reduction.py      ← MOVED here from iso_backends (shared by both concerns)     [§4.3]
  adapters/           shared
  datasets/           shared (+ planted_families, perturbation_ladder, correlation_corpus) [§7]
  viz/                shared, unchanged
  metrics/            shared stateless primitives ONLY: runtime.py, complexity_fit.py

  isomorphisms/       CONCERN 1 — iso-detection (relocated existing code) [Option B, §8]
    iso_backends/     IsoBackend + isalhg/pynauty/bliss/traces + subprocess_base + registry
    protocols/        pairwise_iso, fingerprint_timing, algorithm_benchmark,
                      partition_agreement, structural_calibration
    metrics/          correctness, partition  (iso-specific)

  metric_space/       CONCERN 2 — the new article (greenfield) [§3]
    base.py           HypergraphDistance ABC
    registry.py       register_distance / get_distance / available_distances
    distances/        ours + ground truth
      isalhg_levenshtein.py   d_I = Levenshtein(w*(H1), w*(H2))     [our method]
      hged.py                 ExactHGED (branch-and-bound oracle) + BipartiteHGED
                              (Riesen–Bunke upper bound) — the OFFICIAL HGED: Qin
                              (ICDE 2023) empty-shell taxonomy verbatim (PI 2026-07-08)
      qin_hged.py             QinHGED — the paper's own HGED-BFS algorithm for the
                              same metric; fidelity anchor (Example 2) + thresholded queries
    representations/  competitors (each a HypergraphDistance)
      wl.py                   hypergraph-WL histogram → L1/χ²   (wraps core.hypergraph_wl)
      nauty_levi_edit.py      nauty canonical form via core.levi_reduction → string edit  [contrast]
      hypercot.py             HyperCOT (optional dep; pinned-env subprocess)
      hpd.py                  Hyperedge Portrait Divergence (optional dep; vendored)
      netlsd.py               optional spectral (pip netlsd)
      subprocess_base.py      SubprocessRepresentation (pinned-env competitors, mirrors iso subprocess_base)
    metrics/          stateless scoring primitives (OUR non-standard ones)
      association.py          Spearman/Pearson between two distance matrices (E1'; MI retired with the v2 head-to-head axis)
      information.py          fixed-width-code bits, compression ratio (Wilcoxon input vector)
      embedding.py            classical-MDS solve (double-center→eig), stress, PSD / neg-eigenvalue mass ν
      geometry.py             concentration stats (diameter/median ratio, length-difference floor), hubness (k-occurrence skewness)
```

**Note on `isomorphisms/` (Option A vs B).** Moving the existing iso packages
under a parent is a *large* import churn (registry, tests, experiments). It is
**optional and sequenced last** (§8). The additive `metric_space/` sibling
(§3) delivers the paper without it; the parent reparent is cosmetic symmetry.

---

## 3. The central new abstraction — `HypergraphDistance`

The metric-space analogue of `IsoBackend`. `IsoBackend` yields an iso *decision /
fingerprint*; `HypergraphDistance` yields a *real-valued dissimilarity*. This
resolves COMPETITORS.md CQ5: the competitors are **not** `IsoBackend`s.

`metric_space/base.py`:

```python
class HypergraphDistance(ABC):
    @property
    @abstractmethod
    def name(self) -> DistanceName: ...

    @abstractmethod
    def pairwise(self, H1: SparseHypergraph, H2: SparseHypergraph) -> float: ...

    def matrix(self, corpus: Sequence[SparseHypergraph]) -> "np.ndarray":
        """Dense symmetric dissimilarity matrix. Default loops `pairwise`;
        override when a representation computes a whole-corpus embedding /
        coupling more efficiently (HyperCOT, WL, NetLSD)."""

    # optional: precompute a per-hypergraph fingerprint to amortize matrix()
    def fingerprint(self, H: SparseHypergraph) -> Any | None:  # default None
        ...
```

Every method that follows subclasses this uniform interface, so the Layer-1
correlation study (`empirical/correlation.md`) is literally:
`corr(D.matrix(corpus), ExactHGED().matrix(corpus))` for each registered `D`.

Members and their homes:

| Distance | File | Reuses | Optional dep |
|---|---|---|---|
| `IsalHGLevenshtein` (ours, `d_I`) | distances/isalhg_levenshtein.py | `core.canonical` | `rapidfuzz` (fast C++ Levenshtein) |
| `ExactHGED` (ground truth) | distances/hged.py | `core.sparse_hypergraph` edits | — (A*/ILP) |
| `BipartiteHGED` (BP-HGED scale oracle) | distances/hged.py | `core.levi_reduction` | `scipy.optimize.linear_sum_assignment` |
| `HypergraphWLDistance` | representations/wl.py | `core.hypergraph_wl` | — |
| `NautyLeviEditDistance` (contrast) | representations/nauty_levi_edit.py | `core.levi_reduction` | `pynauty`, `rapidfuzz` |
| `HyperCOTDistance` | representations/hypercot.py | adapters (→HyperNetX) | `hypernetx==1.2`, `POT==0.8.0` (pinned env) |
| `HPDDistance` | representations/hpd.py | — | vendored `Hor_dissimilarity_measures` |
| `NetLSDDistance` | representations/netlsd.py | `core.levi_reduction` | `netlsd` |

Distance parameters (raw vs length-normalized vs token-weighted Levenshtein;
MI estimator; WL depth) are constructor kwargs, so ablations are config, not new
classes.

### 3.1 The `rapidfuzz` decision

The correlation study is O(N²) pairwise over thousands of hypergraphs → millions
of `d_Lev` calls. Pure-Python DP is too slow. Use `rapidfuzz` (C++ Levenshtein),
imported *inside* `IsalHGLevenshtein.pairwise`/`matrix`, raising
`RepresentationDependencyMissingError` if absent. Raw edit distance is primary
(matches IsalGraph ρ=0.934); normalized / token-aware are kwargs.

### 3.2 Pinned-environment competitors

HyperCOT pins `hypernetx==1.2` + `POT==0.8.0`, incompatible with our HyperNetX.
Do **not** pollute the `isalhg` env. Mirror the existing `traces_levi` pattern:
a `SubprocessRepresentation` base that serialises the corpus, shells out to a
dedicated conda env (`isalhg-hypercot`), and parses back a distance matrix. HPD
is pure-Python (numpy/scipy) → vendor the two functions (MIT) into
`representations/_hpd_vendor.py` with provenance in the header. NetLSD is
pip-installable directly.

---

## 4. Shared-primitive promotions

### 4.1 `core.sparse_hypergraph` — structural edit operations
HGED (exact + ladder), the planted-family generator, and the single-edit
sensitivity measurement (`theoretical/stability.md` §2.1, Exp E2b) all need
*apply one edit*. Add free functions beside `permute` (stdlib-only):
`insert_vertex`, `delete_vertex`, `insert_hyperedge`, `delete_hyperedge`,
`add_incidence`, `remove_incidence`, plus `random_edit(H, rng)` and
`edit_path(H, t, rng)` (returns the perturbed hypergraph *and* the known edit
budget `t`, the ladder's upper-bound HGED). These are the six unit ops of the
Qin et al. (2023) HGED — the same ops `ExactHGED` searches over.

### 4.2 `metrics/` split
`correctness` + `partition` are iso-specific → `isomorphisms/metrics/`.
`runtime` + `complexity_fit` are genuinely shared (both papers report
wall-clock / peak-RSS and empirical complexity) → stay in top-level `metrics/`.
New metric-space scoring → `metric_space/metrics/` (§3 tree).

### 4.3 `levi_reduction` → `core`
Currently `iso_backends/levi_reduction.py`, but the metric-space
`NautyLeviEditDistance` and `NetLSDDistance` need it too. If it stayed under a
future `isomorphisms/`, `metric_space` would depend on `isomorphisms` — breaking
the separation. It is stdlib-only and a pure structural transform, so move it to
`core/levi_reduction.py`; update the three iso backends' imports. This is the one
*required* move (independent of Option A/B).

---

## 5. Errors and types

`errors.py` gains a metric-space hierarchy: `MetricSpaceError(IsalHGError)` →
`DistanceComputationError`, `HGEDComputationError` (e.g. exact solver timeout),
`RepresentationDependencyMissingError` (guarded optional deps; carries an install
hint), `SubprocessRepresentationError`.

`types.py` gains `DistanceName` (str alias) but **not** a numpy-backed
`DistanceMatrix` alias (types is imported by stdlib-only `core`; keep it
numpy-free). Annotate matrices as `np.ndarray` locally in `metric_space` modules
under `TYPE_CHECKING` if needed.

---

## 6. Seed-selection optimization (PI 2026-07, the first coding task)

Refines the H2S seed set to fewer starting nodes while preserving
isomorphism-invariance of `w*`. New rule, in priority order:
1. if labelled, restrict to nodes of **maximal label**;
2. among those, nodes of **maximal degree**;
3. among those, nodes whose **decreasing-sorted neighbour-degree list** is
   **lexicographically maximal**.

- Files: `core/structural_tuples.py` (add `max_label_degree_nbrseq_nodes` or
  extend the existing seeders) + its C++ twin
  `_native/include/isalhg/structural_tuples.hpp` (+ `structural_tuples` impl) +
  the dispatch in `canonical.py::_python_canonical_string` and
  `_native/src/canonical.cpp::canonical_string_compute` (new `AlgorithmVariant`).
- **Serves both concerns**: it changes `w*`, so it changes iso fingerprints
  *and* `d_I`. Acceptance criteria: (a) `tests/property/test_canonical_invariance`
  still green under Hypothesis; (b) iso-backend partition agreement unchanged;
  (c) measured wall-clock drop on the design fixtures (Fano/STS/GQ) reported.
- Rationale link: fewer seeds also *shrinks the avalanche surface*
  (`theoretical/stability.md` §3) — the optimization and the stability theorem
  are the same lever.

---

## 7. Datasets additions (shared layer)

New under `datasets/synthetic/` (subclass `HypergraphDataset`, register in
`datasets/registry.py`):

- `planted_families.py` — `F` seed motifs × `r` **seed-stable, non-isomorphic**
  perturbations; family id = class label. Serves A1/A2/A3
  (`empirical/applications.md`). **Enforce non-isomorphism** within family
  (dedup via lazy `metric_space`/`iso` check) — the corpus survey's
  `permute()`-copies shortcut is invalid (`DATA.md` §1). Class members must be
  distinct iso-classes.
- `perturbation_ladder.py` — `edit_path(H, t)` chains (Exp E3); yields
  known-upper-bound HGED = `t`.
- `correlation_corpus.py` — tiny (`n ≤ ~10`) corpus for the exact-HGED
  Layer-1 study; may just parametrize `exhaustive_small`.

Fix the `exhaustive_small.py` module-level `iso_backends` import → lazy
(inside the dedup method), restoring the documented dependency direction.
`LabelVocabulary.fit()` (currently a stub) is only needed if a labelled corpus
lands; planted families can use `LabelVocabulary.trivial()`.

---

## 8. Dependency direction (updated)

```
core (stdlib-only)  ← adapters, datasets, metrics, isomorphisms/*, metric_space/*, viz, experiments
core.levi_reduction ← isomorphisms/iso_backends, metric_space/{distances,representations}
adapters            → core
datasets            → core, adapters      (dedup → iso/metric distance: LAZY only)
metrics (shared)    → core
isomorphisms/*      → core, adapters, datasets, metrics
metric_space/*      → core, adapters, metrics ; optional external libs (guarded)
metric_space MUST NOT import isomorphisms   (enabled by levi_reduction living in core)
experiments/*       → everything
```

Rules unchanged from the repo doc: one-way arrows, `core` stdlib-only, optional
deps guarded inside method bodies, registries drive lazy import by name.

---

## 9. The `src/` ↔ `experiments/` boundary (honours constraint 3)

| Study (v3) | `src/` provides (library) | `experiments/` does (execution + stats) |
|---|---|---|
| Geometry profiles (G1) | `metrics.geometry` (concentration, hubness) | per-corpus geometry table (with `ν`, `D̂` from A1), figures |
| Sensitivity + ladder (G2) | `sparse_hypergraph` edits + `qin_edit_cost`, `d_I` | `s(e)` histograms (ours **and** nauty contrast), ladder-response curves |
| MDS (A1, flagship) | `metrics.embedding` (classical solve, stress, PSD, ν) | SMACOF, **CV dimension selection**, Mardia ratios, Shepard, figures |
| Clustering / dendrogram (A2) | distance matrices | k-medoids (PAM), linkage, silhouette/Dunn/DB/ARI (sklearn/scipy directly) |
| kNN classification (A3) | distance matrices | kNN CV, accuracy/F1/AUC, interpreted against the G1 profile |
| Shortest path (A4) | distance matrices + ladder corpora + S2H decode | path search over pool + distractors; recovery/monotonicity scores; decoded-intermediates figure |
| Discussion figure (E1') | `HypergraphDistance.matrix`, `ExactHGED`, `metrics.association` (ρ) | one mini-corpus scatter + ρ (ours only; no sweep, no competitor rows) |
| Information content | `metrics.information` (bits, ratio) | Wilcoxon signed-rank, OLS β, figure |

*(v2 studies retired at the 2026-07-18 rescope: the full correlation study E1
with competitor rows + MI, and the density sweep E2. Their library surface —
`ExactHGED`, `association` — survives for E1'.)*

Standard indices (silhouette, ARI, cophenetic, accuracy) are called from
`sklearn`/`scipy` **in experiments** — not re-wrapped in `src/` (reuse rule).
`metric_space/metrics` holds only *our* non-standard primitives.

Proposed `experiments/article/` (mirrors `experiments/preprint/`):
`configs/*.yaml`, a runner that computes + caches `D` matrices per
`(distance, dataset, seed)`, and `analysis/{correlation, information_content,
mds, clustering, classification, shortest_path, figures}/`. No new `src/` code
for the applications themselves.

---

## 10. Implementation order (phases, each with a closing check)

- **M0 — seed-selection optimization** (§6). Closes on: canonical-invariance
  property test green + wall-clock drop table on design fixtures. *First task;
  unblocks every sweep by making `w*` cheaper.*
- **M1 — metric-space skeleton** (§3): `metric_space/{base,registry}` +
  `IsalHGLevenshtein` + `HypergraphWLDistance`; `levi_reduction`→core (§4.3);
  `sparse_hypergraph` edits (§4.1); errors/types (§5). Closes on: `d_I` on the
  design fixtures = 0 for isomorphic pairs, > 0 otherwise (unit test), and
  `matrix()` on a 10-item corpus runs.
- **M2 — HGED oracle** (§3): `ExactHGED` (small) + `BipartiteHGED`;
  `datasets/perturbation_ladder` + `correlation_corpus`. Closes on: exact HGED
  matches hand-computed edit counts on tiny fixtures; ladder `t` ≥ exact HGED.
- **M3 — competitors** (§3.2): `NautyLeviEditDistance`, `HPDDistance`,
  `NetLSDDistance`, then `HyperCOTDistance` (subprocess env). Closes on: each
  `matrix()` runs on the correlation corpus; iso pairs → distance 0 for the
  metric competitors (sanity).
- **M4 — planted families** (§7) + `metric_space/metrics/*`. Closes on: a
  planted corpus with verified non-isomorphic within-family members + known
  labels; `association`/`information`/`embedding` primitives unit-tested.
- **M5 — experiments** (§9): `experiments/article/`; the studies run
  end-to-end. Closes per `empirical/` acceptance criteria. **No `src/` changes.**
- **M6 (optional) — `isomorphisms/` reparent** (§2 Option B). Pure move +
  import rewrite; closes on full test suite green. Do only if the symmetry is
  wanted; sequence LAST to avoid blocking the science.

Every module lands with unit tests under `tests/unit/metric_space/…`; any change
touching `core/canonical` or seeds re-runs `tests/property/`.

---

## 11. Open decisions for the user / PI

- OD1. **Option A (additive `metric_space/` only) vs Option B (also reparent to
  `isomorphisms/`).** Recommendation: **A now, B optional/later** — A delivers
  the paper with far less churn; B is cosmetic symmetry, sequenced last (M6).
- OD2. `levi_reduction` new home: `core/levi_reduction.py` (recommended) vs a new
  shared `reductions/` package. (A move is required either way, §4.3.)
- OD3. **[resolved, v3]** HyperCOT: dedicated pinned conda env via subprocess;
  run on the small/mid corpora only, its scale limit stated in every table
  (`COMPETITORS.md` §2).
- OD4. **[resolved 2026-07-08; shipped]** `ExactHGED` is our own solver over
  Qin's ops (no public HGED solver exists); the Levi-lift route was rejected
  for its unproven equality with HGED. In v3 the oracle serves only the E1'
  mini-corpus.
- OD5. Whether `metric_space/metrics/embedding.py` should host the classical-MDS
  *solve* at all, or push even that into `experiments` (stricter reading of
  constraint 3). Recommendation: keep the deterministic solve + stress as a
  primitive; keep CV / SMACOF / figures in experiments.
