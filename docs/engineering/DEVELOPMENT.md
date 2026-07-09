# Development notes

Living document for IsalHG development. Pair-read with `CLAUDE.md` at the
repo root, `docs/engineering/CODE_DESIGN.md` (architectural lookup), and the seed
proposal (`docs/isalhg_idea.pdf` + `docs/preprint/PROPOSAL.md`).

## C++ core extension

The canonical-string algorithm has two implementations, both living
inside the `isalhg.core` package:

- Pure-Python reference: regular functions named `_python_<fn>` in the
  same modules that expose the public entry points
  (`hypergraph_to_string.py`, `hypergraph_wl.py`, `structural_tuples.py`,
  `canonical.py`).
- C++17 extension: native module at `isalhg.core._core`, compiled from
  the source tree under `src/isalhg/core/_native/` via nanobind +
  scikit-build-core.

The two are selected per call with a `backend="cpp"|"python"` keyword;
the default backend is `"cpp"` (see `isalhg.core.backends.DEFAULT_BACKEND`).

```python
from isalhg.core.canonical import canonical_string
canonical_string(H)                        # cpp (default)
canonical_string(H, backend="cpp")         # explicit cpp
canonical_string(H, backend="python")      # pure-python reference
```

The same `backend=` kwarg is honoured by `greedy_h2s`,
`hypergraph_to_string`, `wl_hash`, `wl_partition`, and `max_xi_nodes`.

Build flow:

```bash
conda activate isalhg
pip install -e ".[dev]"        # scikit-build-core + CMake driven; first build ~30s
python -c "import isalhg.core._core; print(isalhg.core._core.ping())"  # smoke test
```

Iteration:

- Edit any `src/isalhg/core/*.py` shim or test — takes effect immediately
  (scikit-build-core editable mode uses a `.pth` redirect).
- Edit any `src/isalhg/core/_native/**/*.{cpp,hpp}` — re-run
  `pip install -e ".[dev]"` (CMake does an incremental rebuild, usually
  seconds after the first full build).

Sanitizer build:

```bash
CMAKE_ARGS="-DISALHG_ENABLE_SANITIZERS=ON" pip install -e ".[dev]" --no-build-isolation
LIBASAN=$(gcc -print-file-name=libasan.so)
LIBSTDCPP=$(gcc -print-file-name=libstdc++.so)
PYTHONMALLOC=malloc ASAN_OPTIONS=detect_leaks=0:halt_on_error=1 \
LD_PRELOAD="$LIBASAN:$LIBSTDCPP" \
    python -m pytest tests/property/ tests/unit/core/ -q
```

The `LIBSTDCPP` preload is required because ASan's `__cxa_throw`
interceptor must bind to the real C++ exception machinery before any
nanobind code runs.

Speedup (`scratchpad/cpp_speedup.py`, local laptop, single-threaded):

| Design          | greedy_min PY | C++     | Ratio |
|-----------------|--------------:|--------:|------:|
| Fano STS(7)     |        649 ms |    6 ms |  101× |
| STS(9) AG(2,3)  |       6.11 s  |   44 ms |  138× |
| STS(13) cyclic  |       63.4 s  |  352 ms |  180× |
| GQ(2,2) doily   |  DNF >300 s   |  659 ms |  DNF→s |

Extending the algorithm pool:

- New backend (e.g. Rust): append the implementation callable to the
  per-module dispatch dict (`_GREEDY_H2S_BACKENDS`,
  `_CANONICAL_STRING_BACKENDS`, etc.) at import time.
- Pure-Python algorithm: subclass `isalhg.core.algorithms.base.H2SAlgorithm`,
  call `register_algorithm("name", factory)`. `canonical_string(..., algorithm="name")`
  picks it up via the Python registry.
- C++-native variant: add an enum entry to
  `src/isalhg/core/_native/include/isalhg/canonical.hpp::AlgorithmVariant`,
  implement its filter in `canonical_string_compute`, recompile, then
  call `isalhg.core.canonical.register_cpp_variant("name", enum_id)`.

## Status

**Phases 1 + 2 + 3 + 4 closed (2026-06-13).** The repo now ships:

- the canonical-string algorithm (`isalhg.core.*`),
- the four `IsoBackend` implementations specified in PROPOSAL.md Tier 1
  (`isalhg`, `pynauty_levi`, `bliss_levi` via `python-igraph`,
  `traces_levi` via the `dreadnaut` subprocess),
- the dataset layer (`HypergraphDataset` ABC, `LabelVocabulary`,
  `ExhaustiveSmallHypergraphs` with itertools-enumeration +
  fingerprint-dedup + named-design slots for Fano / STS(9) / two
  cyclic STS(13) / GQ(2,2)),
- the protocol layer (`BenchmarkProtocol`, `PairwiseIsoProtocol` with
  FP/FN counting and bijection-certificate verification),
- the metrics layer (`confusion_from_partitions`,
  `verify_bijection_certificate`),
- the experiment orchestrator
  (`experiments.{schemas, orchestrator}`, atomic skip-if-exists JSON
  persistence, hardware capture, idempotent re-runs).

Phases 5-6 (Tier 2-5 datasets, runtime / partition / complexity_fit
metrics, fingerprint_timing / partition_agreement /
structural_calibration protocols, analysis figures) remain
scaffold-only.

## Implementation order

Coding agents should fill stubs in the six-phase order specified in
`docs/engineering/CODE_DESIGN.md` Section 7. Each phase closes with a concrete runnable
check that must be reproduced in the closing commit message; no phase opens
until its predecessor's check passes.

Phase headline (full detail in `CODE_DESIGN.md`):

1. **VM + canonical [COMPLETED 2026-06-11]** -- `core/*` +
   `algorithms/greedy_min` + hand-built fixtures (Fano, STS(9), iso/non-iso
   pairs). Closed on
   `pytest tests/unit/core/ tests/property/test_s2h_roundtrip.py` --
   136 tests green in 62s. ruff + mypy --strict clean. Implementation note:
   `greedy_h2s` runs a **bounded backtracking over new-input orderings**
   within each `V` emission's label classes (one extra branching point per
   `V` step; iso-equivariance was otherwise broken on symmetric structures
   like Fano and STS(9) by the input-id tie-break). Displacement and edge
   selection remain pure greedy. This refinement is local to
   `core/hypergraph_to_string.py::_encode_from` and does NOT introduce
   `canonical_pruned.py` (open question 1 still pending PI guidance).
2. **Backend interface + oracle [COMPLETED 2026-06-11]** -- `xgi_adapter`,
   `iso_backends/{isalhg_backend, levi_reduction, pynauty_levi, registry}`.
   Closed on
   `pytest tests/unit/iso_backends/ tests/unit/adapters/ tests/integration/test_isalhg_end_to_end.py tests/integration/test_pynauty_roundtrip.py tests/property/test_canonical_invariance.py`
   -- 37 tests green; partition-agreement table below confirms
   `IsalHGBackend.are_isomorphic == PynautyLeviBackend.are_isomorphic` on
   every Phase 1 fixture (4/4 iso pairs + 1/1 non-iso pair).

   **Phase 2 partition-agreement table** (seed=42):

   | fixture        | n, m    | IsalHG | pynauty | agree |
   |----------------|---------|--------|---------|-------|
   | trivial        | 1, 0    | True   | True    | True  |
   | single_edge    | 3, 1    | True   | True    | True  |
   | fano_plane     | 7, 7    | True   | True    | True  |
   | sts_9          | 9, 12   | True   | True    | True  |
   | non_iso_pair   | 4,2/4,3 | False  | False   | True  |

   **Phases 3 + 4 partition-agreement table** — pairwise iso classifier on
   the smoke-scale dataset `ExhaustiveSmallHypergraphs(n_range=(3,4),
   arity_range=(2,3), max_edges=3, include_designs=false,
   permutations_per_class=2)`, 36 iso-classes × 2 reps = 72 items,
   2,556 unordered pairs. All four backends report:

   | backend       | FP | FN | TP | TN     | bijection violations |
   |---------------|----|----|-----|--------|----------------------|
   | isalhg        | 0  | 0  | 36  | 2 520  | n/a (no certificate)|
   | pynauty_levi  | 0  | 0  | 36  | 2 520  | 0                    |
   | bliss_levi    | 0  | 0  | 36  | 2 520  | 0                    |
   | traces_levi   | 0  | 0  | 36  | 2 520  | n/a (no certificate)|

   Identical TP/TN across all four backends → four-way partition agreement.

3. **Tier 1 end-to-end [COMPLETED 2026-06-13]** -- shipped
   `datasets/{base, registry, schemas (with LabelVocabulary),
   synthetic.exhaustive_small}` + `metrics.correctness` +
   `protocols/{base, pairwise_iso, registry}` +
   `experiments/{schemas, orchestrator}` + `tier1_correctness.yaml`.
   The orchestrator was validated end-to-end via
   `tests/integration/test_orchestrator_tier1.py`:
   `python -m experiments.orchestrator --config
   experiments/configs/tier1_correctness.yaml` on the smoke-scale
   parameters (`n ∈ {3, 4}`, arity `∈ {2, 3}`, `max_edges = 3`, plus
   Fano + STS(9)) reports `FP = FN = 0` on both `isalhg` and
   `pynauty_levi` cells, and the pynauty bijection certificate is
   accepted by `verify_bijection_certificate` on every iso pair. The
   full-scale Tier 1 sweep (`n ∈ {3..6}`, arity `∈ {2..4}`, including
   the STS(13) pair and GQ(2,2) doily — currently ~3 min per
   IsalHG fingerprint on GQ(2,2), open question #1) is queued for
   execution on a workstation by raising the same YAML's
   `n_range`/`max_edges` and toggling `include_large_designs: true`.
   **Phase-2 bug fixed in passing**: `PynautyLeviBackend.bijection_certificate`
   composed `pi2^{-1}(pi1(v))` under the assumption that
   `pynauty.canon_label(g)[i]` is the canonical position of vertex
   `i`. The actual semantics are the inverse (`pi[i]` is the vertex at
   canonical position `i`), so the certificate was a permutation but
   not an edge-preserving one. The corrected composition is
   `pi2(pi1^{-1}(v))`.
4. **Remaining backends [COMPLETED 2026-06-13]** -- shipped
   `bliss_levi` (via `python-igraph` 1.0 `canonical_permutation` /
   `isomorphic_bliss`, same canon_label semantics fix as pynauty) and
   `subprocess_base` + `traces_levi` (subprocess to dreadnaut 2.9
   installed via `conda install -n isalhg -c conda-forge nauty`;
   serialises the Levi graph using the `At c -a n=N f=[...] g ... . x
   b6 q` session shape and parses the canonical `b6` line as the
   fingerprint). Tier 1 partition agreement across all four backends
   confirmed by `tests/integration/test_orchestrator_tier1.py::test_tier1_orchestrator_partition_agreement`
   (FP=FN=0 on every backend; equal TP/TN counts).
5. **Tier 2 scaling** -- `datasets.synthetic.{erdos_renyi, chung_lu}` +
   `metrics.runtime` + `protocols.fingerprint_timing` +
   `analysis.{aggregate, stats}` + `tier2.yaml`. Closes on a scaling sweep
   producing per-cell median + IQR + bootstrap CI on speedup.
6. **Tiers 3-5** -- `synthetic.hardness`, `arb_benson`, `xgi_loader`,
   `hic_atlas`, `metrics.{partition, complexity_fit}`,
   `protocols.{partition_agreement, structural_calibration}`, `tier{3,4,5}.yaml`,
   `analysis.figures/`. Closes on Tier 5 reporting partition-agreement
   across all four backends on all 12 HIC datasets.

Each step also lands with its unit tests populated and passing under
`pytest -m unit`.

## Removed in the architectural refactor

| Path | Reason |
|---|---|
| `src/isalhg/core/canonical_pruned.py` | PI has not specified the backtracking algorithm. Reintroduce when the algorithm is specified. |
| `src/isalhg/core/algorithms/pruned_exhaustive.py` | Same reason. |
| `tests/unit/test_canonical_pruned.py` | Mirror of the above. |
| `benchmarks/` (repo root) | Replaced by `src/isalhg/datasets/` (loaders) + `experiments/configs/` (run specs). |

## Open research questions (from the seed proposal and PROPOSAL.md)

1. **Backtracking procedure for greedy ties** -- partially resolved
   (2026-06-11). `core/hypergraph_to_string.py::_encode_from` now branches
   on label-class permutations of new-input vertices within each `V`
   emission and takes the lex-min completion; this restores
   iso-equivariance on vertex-transitive fixtures (Fano, STS(9)) without
   exploding (worst-case branching `(j!)^{num V steps}`, typically small).
   A separate **pruned backtracking** variant covering displacement and
   edge-selection ties (the original PI-deferred algorithm) remains
   unspecified; `core/canonical_pruned.py` and
   `algorithms/pruned_exhaustive.py` will be reintroduced once that
   algorithm exists. Validated empirically by the Phase 2 partition-agreement
   table -- IsalHG matches pynauty on every Phase 1 fixture.
   **2026-06-13 update**: empirical fingerprint wall-clock on highly
   symmetric designs measured at Phase 3 close:
   Fano STS(7) 0.78 s, STS(9) 7.55 s, STS(13) cyclic (013) 62 s,
   STS(13) cyclic (016) 76 s, GQ(2,2) doily 177 s on the workstation's
   default Python 3.13 build. The backtracking branching factor explodes on
   designs with large automorphism orbits; this is the same `(j!)^{num V}`
   worst-case noted above. Mitigations: `ExhaustiveSmallHypergraphs` now
   accepts `dedup_backend_name` so heavyweight named designs can be
   deduplicated against `pynauty_levi` (microseconds per call), and
   `include_large_designs` is opt-in. The full Tier 1 sweep with
   STS(13)/GQ(2,2) is therefore tractable when scheduled on a single
   workstation core rather than inside a unit-test budget.
2. **Value of `k`** -- capped at 10 (decision B12). Whether `k` should be
   input-dependent within that cap is open.
3. **Structural-tuple depth** -- fixed at 3 by analogy with IsalGraph; Tier 3
   results will tell us whether depth-3 distinguishes the large-Aut Steiner
   systems and non-Desarguesian PG(2,9). Depth >= 4 may be required, in which
   case Theorem 2's induction has to be redone.
4. **Disconnected hypergraphs** -- deferred (decision B11). Per-component
   encoding + lex-min merge is the obvious extension but undesigned.
5. **HG-CFI construction** -- needed to falsify Theorem 2 if it fails.
   Companion-paper task (C14); not built.
6. **Completeness proof (Theorem 2)** -- deferred to paper (b) under the
   two-paper split. Empirically checked in Tier 1 and Tier 5.
7. **Worst-case complexity bound (Theorem 3 procedure)** -- empirical-only
   by decision (C17).
8. **Isomorphism-pair generation** -- resolved by decisions I44
   (`docs/preprint/PROPOSAL.md`, 2026-06-11), I49 + I50 (2026-06-16), and the
   cohort spec in `docs/preprint/DATA.md`. Positive pairs via stdlib-only
   `core.sparse_hypergraph.permute(H, σ)`. Cross-class fixtures from
   (a) Kaski-Östergård plaintext STS catalogs `sts13.txt` (2 classes)
   and `sts15.txt` (80 classes) downloaded from
   `pottonen.kapsi.fi/sts19/` and parsed in pure Python; (b) the
   GQ(2,2) doily already shipped from Payne-Thas 2009; (c) SageMath
   designs library (PG(2, q), large-Aut STS, GQ(2,4)/(3,5), non-group
   Latin squares) generated in a sibling Sage env and committed as
   JSON fixtures; (d) the LLM4Hypergraph iso-recognition corpus
   (Feng et al. ICLR 2025, github.com/iMoonLab/LLM4Hypergraph, Apache
   2.0) with the missing `HGSCKernel` oracle substituted by
   `PynautyLeviBackend.are_isomorphic()`. Pynauty-certified random
   sweeps remain for Tier 2 / Tier 3 scale. HG-CFI confirmed unbuilt
   anywhere in the public literature as of 2026-06-16; companion
   paper task C14 stays open.
9. **Label vocabulary** -- resolved by decision I45
   (`docs/preprint/PROPOSAL.md`, 2026-06-11). Vocabularies are dataset-scoped, fitted
   once at load by `LabelVocabulary.fit(items)` (lexicographic sort →
   contiguous int IDs), persisted on `DatasetMetadata`. `core/` never sees
   semantic strings; the Levi reduction lifts both color classes onto
   `B(H)` with disjoint id ranges. Mirrors the nauty / Traces / bliss
   colored-graph contract; faithful to the IsalSR pattern of a
   dataset-supplied operator catalog over a VM that stays
   alphabet-agnostic. **2026-06-13 update**: the dataclass landed in
   `src/isalhg/datasets/schemas.py` with
   `LabelVocabulary.trivial()` returning `(("⊥",), ("⊥",))`. The
   production `fit(items)` path is gated behind a
   `NotImplementedError` until the labelled HIC-atlas loader (Phase 6),
   matching the actual sequencing in `docs/engineering/CODE_DESIGN.md`.

## Phase 3.5 follow-up (queued)

- Extract the Feng et al. TPAMI 2024 Figure 3 HWL-failure pair and
  the Zhang et al. ICML 2025 Figure 3(a)/(b) `k`-GWL pairs from their
  source PDFs; add them as `conftest.py` fixtures and as named
  designs in `synthetic.exhaustive_small`. PROPOSAL.md Tier 1
  acceptance criteria 5, 6, 7 cannot be ticked off until this lands.

## Benchmark cohort spec (2026-06-16)

The full data layer is documented in `docs/preprint/DATA.md` (authoritative
source). Summary for navigation only:

- **Cohort A — downloadable real data** (10 sources). Includes the
  Kaski-Östergård STS plaintext catalogs (STS(13)/15 with 2/80 non-iso
  classes), GQ(2,2) doily, Fano, STS(9), the SageMath designs library
  via sibling Sage env + JSON fixtures, HIC's 12 datasets, the
  LLM4Hypergraph iso-recognition corpus with pynauty oracle
  substitution, ARB, XGI-DATA, Hypergraphx, and Yaveroglu PPI
  hypergraphlets.
- **Cohort B — synthetic generators** (11 generator paths). Includes
  `core.permute()`, XGI Erdős-Rényi + Chung-Lu, XGI secondary
  generators (configuration model, planted partition, DCSBM),
  Hypergraphx auxiliaries (scale-free, HOAD), cyclic STS, Cayley
  hypergraphs, random regular at threshold, PG(2, q) via Sage,
  large-Aut Sage designs, and the HG-CFI construction (open).

`docs/preprint/DATA.md` §4 holds the implementation status table; `docs/preprint/DATA.md`
§5 enumerates nine prioritised tickets for the next round of work.
`docs/preprint/DATA.md` §6 carries the paper sentence that cites the cohort.

## Algorithm-R&D track (priority, pre-Tier 2)

**Open question #1 (pruned canonical backtracking) is escalated to a
priority Algorithm-R&D track.** Justification: empirical timings at
Phase 3 close (Fano 0.78 s, STS(9) 7.55 s, STS(13) 62-76 s,
GQ(2,2) 177 s; see open question #1) make IsalHG uncompetitive against
pynauty / bliss / Traces on high-automorphism fixtures by 3-5 orders of
magnitude. The full Tier 1 sweep with `include_large_designs: true` is
estimated at >5 h of IsalHG-cell wall-clock vs. seconds for the iso
backends. Tier 2 (Phase 5) will measure this gap at scale on random
hypergraphs; the gap will not close without algorithm work.

Scope of the Algorithm-R&D track (PI specification required):
1. Define the pruned backtracking algorithm that branches at every tie
   (displacement, edge-selection, label-class) and prunes via lex-min
   completion of the partial canonical string. Inputs from
   `IsalGraph` preprint footnotes are a starting point but were
   themselves PI-deferred.
2. Reintroduce `core/canonical_pruned.py` and
   `algorithms/pruned_exhaustive.py`; tests under
   `tests/unit/test_canonical_pruned.py`.
3. Establish a complexity bound on the branching factor (currently
   the worst case is `(j!)^{num V steps}` only over `V`-emission label
   classes; the pruned variant must cover all tie sources).
4. Re-validate on Phase 1 / Phase 2 / Phase 3 fixtures; the canonical
   string of the new algorithm must coincide with the bounded-backtracking
   variant on every test where both terminate.

This track is **parallel to Phase 5 (Tier 2 scaling)** -- Phase 5 work
proceeds with the current bounded backtracking and provides the
empirical data that informs the algorithm design (which orbit shapes
to prune first).

## Workstation execution (queued, post-Phase 4)

- Run `python -m experiments.orchestrator --config
  experiments/configs/tier1_correctness.yaml` at full Tier 1 scale
  (raise `n_range` to `[3, 6]`, `arity_range` to `[2, 4]`,
  `max_edges` to 6, set `include_large_designs: true`). Validate that
  the four-way partition agreement reported by
  `test_tier1_orchestrator_partition_agreement` extends to the
  full STS(13)/GQ(2,2) regime.

## Validation tier map (from `docs/preprint/PROPOSAL.md`)

| Tier | Datasets (`isalhg.datasets`) | Protocol (`isalhg.protocols`) |
|---|---|---|
| 1 (correctness) | `synthetic.exhaustive_small`, plus published designs | `pairwise_iso` |
| 2 (scaling) | `synthetic.erdos_renyi`, `synthetic.chung_lu` | `fingerprint_timing` |
| 3 (hardness) | `synthetic.hardness` | `pairwise_iso` (600 s timeout) |
| 4 (calibration) | `arb_benson`, `xgi_loader` | `structural_calibration` |
| 5 (atlas) | `hic_atlas` | `partition_agreement` |

The orchestrator drives `Protocol x Backend x Dataset x Seed` from each
`experiments/configs/tier{N}_*.yaml`.
