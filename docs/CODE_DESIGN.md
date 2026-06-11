# IsalHG code design

Lookup document for coding agents. Pairs with `CLAUDE.md` (project mindset),
`docs/PROPOSAL.md` (validation methodology and scientific scope), and
`.claude/rules/coding_rules.md` (generic patterns).

When you are asked to add or modify code in this repo, read **this file
first**. It tells you where things go.

---

## 1. Decision tree -- "where does this go?"

```
I want to add ...
+-- a hypergraph data-structure operation (degree, neighbors, ...)
|     -> src/isalhg/core/sparse_hypergraph.py
+-- a random isomorphism of an existing hypergraph (positive iso-pair oracle)
|     -> src/isalhg/core/sparse_hypergraph.py::permute(H, sigma)
|        - free function, stdlib-only; DO NOT import xgi.relabel_nodes
|        - sigma is the known ground truth; checked against H2S-replay bijection
+-- a per-dataset label-to-int mapping (vocabulary builder)
|     -> src/isalhg/datasets/schemas.py::LabelVocabulary
|        - lexicographic sort -> contiguous int IDs in [0, |Sigma|)
|        - lives on DatasetMetadata; never reaches core/
+-- a Sigma_HG token or parser extension
|     -> src/isalhg/core/instructions.py
+-- a VM building block (CDLL slot, pointer move)
|     -> src/isalhg/core/{cdll, pointers}.py
+-- an H2S encoder variant
|     -> src/isalhg/core/algorithms/<variant>.py  (subclass of H2SAlgorithm)
+-- a new isomorphism backend (nauty / Traces / bliss / custom)
|     -> src/isalhg/iso_backends/<backend>.py  (subclass of IsoBackend)
|        - subprocess-based?  inherit from SubprocessIsoBackend
|        - graph-iso over Levi?  reuse isalhg.iso_backends.levi_reduction
|        - register in iso_backends/registry.py
+-- a bridge to an external hypergraph library (HyperNetX, XGI, ...)
|     -> src/isalhg/adapters/<lib>_adapter.py  (subclass of HypergraphAdapter)
+-- a new dataset (synthetic generator, real-world archive, atlas)
|     -> src/isalhg/datasets/<area>/<dataset>.py  (subclass of HypergraphDataset)
|        - register in datasets/registry.py
+-- a new benchmark protocol (new way to measure backends)
|     -> src/isalhg/protocols/<protocol>.py  (subclass of BenchmarkProtocol)
|        - register in protocols/registry.py
+-- a stateless metric (FP/FN counter, partition match, complexity fit)
|     -> src/isalhg/metrics/<topic>.py  (plain functions, no class)
+-- an experiment run configuration
|     -> experiments/configs/<tier_or_name>.yaml
+-- post-hoc analysis (aggregation, stats, figures)
|     -> experiments/analysis/{aggregate.py, stats.py, figures/}
+-- a pytest fixture used by many tests
|     -> tests/conftest.py
+-- a one-off script
|     -> scripts/<name>.py  (NOT in src/, NOT in experiments/)
```

If your change does not fit any leaf above, stop and ask the user. The
architecture is closed by construction; new top-level concepts require a
plan-mode design pass.

---

## 2. The four abstract base classes

Each ABC is the single point of extension for its concept. Subclasses live
in the same package; they are discovered through that package's `registry.py`.

### 2.1 `IsoBackend` -- `src/isalhg/iso_backends/base.py`

Mandate. Wrap one isomorphism algorithm behind a uniform interface so the
orchestrator treats IsalHG, nauty, Traces, and bliss interchangeably.

Required methods:

```python
@property
def name(self) -> BackendName: ...

def fingerprint(self, H: SparseHypergraph) -> Fingerprint: ...
def are_isomorphic(self, H1: SparseHypergraph, H2: SparseHypergraph) -> bool: ...
```

Optional method (override when the algorithm yields an explicit permutation):

```python
def bijection_certificate(
    self, H1: SparseHypergraph, H2: SparseHypergraph
) -> dict[NodeId, NodeId] | None: ...
```

Subprocess backends should inherit from `SubprocessIsoBackend`
(`iso_backends/subprocess_base.py`) which centralises binary discovery,
timeout, stderr capture, and temp-file management.

### 2.2 `HypergraphDataset` -- `src/isalhg/datasets/base.py`

Mandate. Yield `DatasetItem` instances in a deterministic order
(`(parameters, seed) -> items`) so reruns are reproducible.

Required:

```python
@property
def name(self) -> DatasetName: ...

@property
def metadata(self) -> DatasetMetadata: ...

def __iter__(self) -> Iterator[DatasetItem]: ...
def __len__(self) -> int: ...
```

Optional:

```python
def seed(self, seed: Seed) -> HypergraphDataset:
    """Return a copy bound to ``seed``. Default returns self (deterministic datasets)."""
```

`DatasetItem` carries `(item_id, hypergraph, iso_class | None, extra)`.
`iso_class is None` means "no ground-truth iso label" -- Tier 4 calibration
datasets, and Tier 2 generators where the partition is irrelevant.

**Label vocabulary.** Each dataset carries a `LabelVocabulary` on its
`DatasetMetadata` (see `datasets/schemas.py`). The vocabulary is fitted
once at dataset construction by `LabelVocabulary.fit(items)`, which
collects all vertex and edge labels seen in the corpus, sorts them
lexicographically, and assigns contiguous `int` IDs. Every yielded
`SparseHypergraph` carries `int`-encoded labels only; the semantic strings
("kinase", "tt0133093") live in `DatasetMetadata` and never reach `core/`.
This mirrors the nauty / Traces / bliss colored-graph convention where the
semantics-to-color mapping is the caller's responsibility. Trivial-label
(synthetic, unlabelled) datasets declare a single-symbol vocabulary
`LabelVocabulary(("⊥",), ("⊥",))` so the canonical algorithm runs
identically on labelled and unlabelled inputs without a special-case
branch. Stochastic datasets that synthesise labels do so deterministically
under the bound seed before fitting the vocabulary.

### 2.3 `BenchmarkProtocol` -- `src/isalhg/protocols/base.py`

Mandate. Define *what* to measure when one `(backend, dataset, seed)` triple
is exercised. Each PROPOSAL tier maps to one concrete protocol; the
orchestrator drives the matrix `Protocol x Backend x Dataset x Seed`.

Required:

```python
@property
def name(self) -> ProtocolName: ...

def measure(
    self,
    backend: IsoBackend,
    dataset: HypergraphDataset,
    seed: Seed,
) -> ProtocolResult: ...
```

`ProtocolResult.measurements` is a `dict[str, Any]` whose schema is fixed by
each concrete protocol's docstring. Analysis code in `experiments.analysis`
asserts on those keys.

### 2.4 `HypergraphAdapter` -- `src/isalhg/adapters/base.py`

Mandate. Translate between an external library's hypergraph type and
`SparseHypergraph`. The adapter is the only place external libraries may
be imported.

Required:

```python
@property
def name(self) -> str: ...

def from_external(self, obj: T) -> SparseHypergraph: ...
def to_external(self, H: SparseHypergraph) -> T: ...
```

External libraries (`hypernetx`, `xgi`, `hypergraphx`) must be imported
**inside method bodies** so the package remains importable when an optional
dependency is missing.

---

## 3. Registry pattern

Each of `iso_backends/`, `datasets/`, `protocols/` ships a `registry.py` with:

```python
def register_<thing>(name, factory): ...
def get_<thing>(name, params) -> <Thing>: ...
def available_<things>() -> tuple[<name-type>, ...]: ...
```

Concrete classes register themselves at *module import time* of their own
module -- not eagerly at package import. The orchestrator's YAML
referencing a backend by name triggers the lazy import in
`get_<thing>(name)`.

This keeps optional dependencies (`pynauty`, `python-igraph`, `dreadnaut`)
out of the import path until the corresponding backend is actually requested.

---

## 4. Dependency direction

One-way arrows; cycles are bugs.

```
                    +-> isalhg.metrics
                    |
  isalhg.types  ----+-> isalhg.core --+-> isalhg.adapters
       ^            |        ^         |
       |            |        +---------+
       |            v
       |    isalhg.iso_backends -----+
       |                              v
       +----- isalhg.datasets <--- isalhg.protocols
                                      ^
                                      |
                              experiments.* (repo-root)
```

Rules:

- `isalhg.core/` is **stdlib-only**.
- `isalhg.adapters/` is the only layer permitted to import HyperNetX / XGI /
  HypergraphX. Imports must be inside method bodies or `try/except
  ImportError`.
- `isalhg.iso_backends/` may import `core` and `adapters`; nothing else in
  the package.
- `isalhg.datasets/` may import `core` and `adapters`; nothing else in the
  package.
- `isalhg.protocols/` may import `core`, `iso_backends`, `datasets`, and
  `metrics`. It may NOT import `adapters` (data-format interop is not a
  protocol concern; protocols operate on `SparseHypergraph`).
- `isalhg.metrics/` is stateless and depends only on `core`.
- `experiments/` lives at repo root, not inside `src/`. It is not part of
  the installable package; it imports from the installed `isalhg.*` and
  from its own sub-modules.

If you find yourself wanting an upward import, you have probably mis-located
the code; re-read section 1.

---

## 5. Adding new things -- checklists

### 5.1 Add a new `IsoBackend`

1. Create `src/isalhg/iso_backends/<name>.py`.
2. Subclass `IsoBackend` (or `SubprocessIsoBackend`).
3. Implement `name`, `fingerprint`, `are_isomorphic`; optionally
   `bijection_certificate`.
4. Optional Python deps: import inside method bodies, not at module top.
5. Subprocess backends: set `BINARY_NAME` and implement `_serialize` /
   `_parse`.
6. Add a registry call in the same module (or in
   `iso_backends/registry.py` if conditional on availability).
7. Add a unit test under `tests/unit/iso_backends/test_<name>.py` and an
   integration test under `tests/integration/test_<name>_roundtrip.py`.
8. If the backend solves graph iso over the Levi reduction, reuse
   `iso_backends/levi_reduction.py`.

### 5.2 Add a new `HypergraphDataset`

1. Pick the right sub-folder: synthetic generator -> `datasets/synthetic/`;
   archive loader -> `datasets/<area>.py`.
2. Subclass `HypergraphDataset`.
3. Implement `name`, `metadata`, `__iter__`, `__len__`; override `seed()`
   for stochastic datasets.
4. Implement determinism: `(parameters, seed) -> items` must be a pure
   function.
5. Set `metadata.has_iso_labels` truthfully; if True, every yielded item
   must carry a non-None `iso_class`.
6. Register in `datasets/registry.py`.
7. Add `tests/unit/datasets/test_<dataset>.py`.

### 5.3 Add a new `BenchmarkProtocol`

1. Create `src/isalhg/protocols/<name>.py`, subclass `BenchmarkProtocol`.
2. Document the `ProtocolResult.measurements` schema in the class docstring.
3. Implement `name`, `measure`. If your protocol does not use the backend
   (calibration-only), accept it as an argument and ignore it.
4. Reuse `isalhg.metrics.*` primitives for any FP/FN, partition, runtime
   computation -- do not reinvent them in the protocol body.
5. Register in `protocols/registry.py`.
6. Add `tests/unit/protocols/test_<name>.py`.

### 5.4 Add a new `HypergraphAdapter`

1. Create `src/isalhg/adapters/<lib>_adapter.py`.
2. Subclass `HypergraphAdapter[<external_type>]`.
3. Implement `name`, `from_external`, `to_external`.
4. Import the external library *inside method bodies*, guarded with
   `try/except ImportError -> raise AdapterDependencyMissingError`.
5. Document any translation limitations (e.g. HyperNetX allows duplicate
   hyperedges; `SparseHypergraph` does not).
6. Add `tests/unit/adapters/test_<lib>.py` and
   `tests/integration/test_<lib>_adapter.py` (integration test guarded by
   `importorskip`).

---

## 6. Module index

| Path | Mandate |
|---|---|
| `src/isalhg/core/cdll.py` | Circular doubly-linked list of `NodeId`. |
| `src/isalhg/core/pointers.py` | `KPointerSet` -- k VM pointers into the CDLL. |
| `src/isalhg/core/sparse_hypergraph.py` | `SparseHypergraph` -- the in-memory model. Also hosts `permute(H, sigma)` -- free function, stdlib-only, vertex-permutation oracle for the positive iso-pair stream (decision I44 in `docs/PROPOSAL.md`). |
| `src/isalhg/core/instructions.py` | `Sigma_HG` tokens, parser, validator. |
| `src/isalhg/core/string_to_hypergraph.py` | S2H interpreter. |
| `src/isalhg/core/hypergraph_to_string.py` | H2S greedy encoder. |
| `src/isalhg/core/structural_tuples.py` | `xi`, `eta`, max-xi node selection. |
| `src/isalhg/core/canonical.py` | Canonical-string entry point. |
| `src/isalhg/core/algorithms/base.py` | `H2SAlgorithm` ABC. |
| `src/isalhg/core/algorithms/{greedy_single, greedy_min, exhaustive}.py` | Variants. |
| `src/isalhg/adapters/base.py` | `HypergraphAdapter` ABC. |
| `src/isalhg/adapters/{hypernetx, xgi, hypergraphx}_adapter.py` | Bridges. |
| `src/isalhg/iso_backends/base.py` | `IsoBackend` ABC. |
| `src/isalhg/iso_backends/subprocess_base.py` | `SubprocessIsoBackend`. |
| `src/isalhg/iso_backends/levi_reduction.py` | Shared Levi bipartite encoder. Emits a 3-class colouring `(v_color = vertex_label_id, e_color = \|Σ_v\| + edge_label_id + sentinel_offset)` so vertex-witness and edge-witness ranges are disjoint -- the standard "lift colours from H to B(H)" trick used by SageMath `IncidenceStructure` and GAP+FinInG. |
| `src/isalhg/iso_backends/{isalhg_backend, pynauty_levi, traces_levi, bliss_levi}.py` | Concrete backends. |
| `src/isalhg/iso_backends/registry.py` | Backend registry. |
| `src/isalhg/datasets/base.py` | `HypergraphDataset` ABC. |
| `src/isalhg/datasets/schemas.py` | `DatasetItem`, `DatasetMetadata`, `LabelVocabulary` (decision I45 in `docs/PROPOSAL.md`). `LabelVocabulary.fit(items)` is the per-dataset semantic-string → `int` ID builder; lexicographic sort, deterministic across Python runs. |
| `src/isalhg/datasets/synthetic/{exhaustive_small, erdos_renyi, chung_lu, hardness}.py` | Synthetic loaders (Tiers 1-3). |
| `src/isalhg/datasets/{arb_benson, xgi_loader, hic_atlas}.py` | Real-world loaders (Tiers 4-5). |
| `src/isalhg/datasets/registry.py` | Dataset registry. |
| `src/isalhg/protocols/base.py` | `BenchmarkProtocol` ABC + `ProtocolResult`. |
| `src/isalhg/protocols/pairwise_iso.py` | Tier 1 & 3 protocol. |
| `src/isalhg/protocols/fingerprint_timing.py` | Tier 2 protocol. |
| `src/isalhg/protocols/partition_agreement.py` | Tier 5 protocol. |
| `src/isalhg/protocols/structural_calibration.py` | Tier 4 protocol. |
| `src/isalhg/protocols/registry.py` | Protocol registry. |
| `src/isalhg/metrics/correctness.py` | FP/FN, bijection-certificate check. |
| `src/isalhg/metrics/runtime.py` | Wall-clock + peak-RSS helpers. |
| `src/isalhg/metrics/partition.py` | Equivalence-partition agreement. |
| `src/isalhg/metrics/complexity_fit.py` | `T ~ n^alpha m^beta r^gamma` regression. |
| `src/isalhg/errors.py` | Exception hierarchy. |
| `src/isalhg/types.py` | Primitive type aliases. |
| `experiments/schemas.py` | `CellSpec`, `ExperimentConfig`, `RunLog`. |
| `experiments/orchestrator.py` | Triple-loop runner. |
| `experiments/configs/tier{1..5}_*.yaml` | Per-tier configurations. |
| `experiments/analysis/aggregate.py` | Per-cell aggregation. |
| `experiments/analysis/stats.py` | Paired tests + bootstrap CIs. |
| `experiments/analysis/figures/` | One module per published figure. |

---

## 7. Implementation order

Six phases. Each closes with a concrete, runnable check; no phase opens until
its predecessor's check passes. Coding agents must report the closing check
output verbatim before moving on.

The ordering rests on three principles, in priority order:

1. **Hand-built fixtures before synthetic generators.** Random hypergraphs
   carry no ground-truth iso label; design-theoretic instances (Fano plane,
   STS(9), GQ(2,2), two non-iso STS(13)) do. Correctness can be asserted on
   the latter without yet having a baseline.
2. **Pynauty before bulk synthetic data.** Pynauty is the iso oracle, not a
   competitor. Every "fingerprint(H1) == fingerprint(H2)" assertion in a
   synthetic sweep needs independent confirmation; running 1000-instance
   sweeps before the oracle exists means the sweeps run blind.
3. **Metrics are interleaved, not deferred.** `metrics.correctness` ships
   with Tier 1; `metrics.runtime` with Tier 2. Deferring metrics produces
   inline metric code inside protocols that has to be extracted later --
   every protocol gets written twice.

### Phase 1 -- VM and canonical algorithm

Modules:

- `isalhg.core.sparse_hypergraph` (port from
  `IsalGraph/src/isalgraph/core/sparse_graph.py`, generalising arity-2 edges
  to arbitrary-arity sets). Includes `permute(H, sigma)` (decision I44) --
  the vertex-permutation oracle consumed by criterion 2 of Tier 1 and by
  the property test `tests/property/test_canonical_invariance.py`.
- `isalhg.core.cdll`, `isalhg.core.pointers` (port from
  `IsalGraph/src/isalgraph/core/cdll.py`).
- `isalhg.core.instructions` (parser + validator for `Sigma_HG`).
- `isalhg.core.string_to_hypergraph` (S2H interpreter).
- `isalhg.core.structural_tuples` (`xi`, `eta`).
- `isalhg.core.hypergraph_to_string` (greedy H2S with the mandatory
  tie-breaking cascade).
- `isalhg.core.canonical` + `isalhg.core.algorithms.greedy_min`.

Fixtures land in this phase: `tests/conftest.py` gets concrete builders for
the trivial hypergraph, Fano plane STS(7), STS(9), an explicit small iso
pair (with a known permutation), and a small non-iso pair with matched
degree sequences.

Closing check:

```
pytest tests/unit/core/ -m unit -q
pytest tests/property/test_s2h_roundtrip.py -m property -q
```

Both green. The property test asserts `S2H(H2S(H)) ~ H` on every fixture and
on a Hypothesis-generated distribution of random small hypergraphs.

### Phase 2 -- backend interface and the iso oracle

Modules:

- `isalhg.adapters.xgi_adapter` (XGI is needed by every later dataset).
- `isalhg.iso_backends.isalhg_backend` (wires `core.canonical` behind
  `IsoBackend`).
- `isalhg.iso_backends.levi_reduction`.
- `isalhg.iso_backends.pynauty_levi`.

Closing check:

```
pytest tests/integration/test_isalhg_end_to_end.py -m integration -q
pytest tests/integration/test_pynauty_roundtrip.py -m integration -q
```

Both green. The integration test asserts that on the Phase 1 fixtures,
`IsalHGBackend.fingerprint` induces the same partition as
`PynautyLeviBackend.fingerprint`. This is the first place IsalHG is
independently validated.

### Phase 3 -- Tier 1 end-to-end

Modules:

- `isalhg.datasets.base`, `datasets.schemas` (including `LabelVocabulary`,
  decision I45), `datasets.registry`.
- `isalhg.datasets.synthetic.exhaustive_small` (enumerated via XGI; emits
  the trivial vocabulary `LabelVocabulary(("⊥",), ("⊥",))` so the
  unlabelled-input path exercises the same canonical-algorithm code paths
  as the labelled one).
- `isalhg.metrics.correctness` (FP/FN counter, bijection-certificate
  verifier).
- `isalhg.protocols.base`, `protocols.pairwise_iso`, `protocols.registry`.
- `experiments.schemas` + `experiments.orchestrator`.
- `experiments/configs/tier1_correctness.yaml` populated with concrete
  cells.

Closing check:

```
python -m experiments.orchestrator --config experiments/configs/tier1_correctness.yaml
```

Reports FP = FN = 0 on every pair across all (n, r) cells in
n in {3..6}, r in {2, 3, 4}; bijection certificate valid on every iso pair;
HWL / k-GWL fixtures from Feng Fig. 3 and Zhang Fig. 3 distinguished.

### Phase 4 -- remaining backends

Modules:

- `isalhg.iso_backends.bliss_levi` (via `python-igraph`).
- `isalhg.iso_backends.subprocess_base`.
- `isalhg.iso_backends.traces_levi` (subprocess to `dreadnaut`).

Closing check: Tier 1 re-runs with the YAML extended to include all four
backends, and the partition-agreement assertion holds for every pair.

### Phase 5 -- Tier 2 scaling

Modules:

- `isalhg.datasets.synthetic.erdos_renyi`,
  `datasets.synthetic.chung_lu`.
- `isalhg.metrics.runtime`.
- `isalhg.protocols.fingerprint_timing`.
- `experiments.analysis.aggregate`, `experiments.analysis.stats`.
- `experiments/configs/tier2_scaling.yaml` populated.

Closing check:

```
python -m experiments.orchestrator --config experiments/configs/tier2_scaling.yaml
python -m experiments.analysis.aggregate --root experiments/outputs/tier2
```

Produces per-cell median wall-clock + IQR + bootstrap 95% CI on the speedup
ratio against `pynauty_levi` for every (backend, dataset, n, r, m/n)
combination.

### Phase 6 -- remaining tiers

Modules:

- `isalhg.datasets.synthetic.hardness` (Tier 3),
  `datasets.arb_benson`, `datasets.xgi_loader` (Tier 4),
  `datasets.hic_atlas` (Tier 5).
- `isalhg.metrics.partition`, `metrics.complexity_fit`.
- `isalhg.protocols.partition_agreement` (Tier 5),
  `protocols.structural_calibration` (Tier 4).
- `experiments/configs/tier{3,4,5}_*.yaml` populated.
- `experiments.analysis.figures/` populated, one module per published
  figure.

Closing check: all five tier YAMLs runnable end-to-end; Tier 5 reports
`P_IsalHG == P_pynauty == P_traces == P_bliss` across all 12 HIC datasets.

### Cross-phase gates

- Every step closes with tests under `tests/unit/...` populated and passing
  under the `unit` marker.
- After any change to canonical-related code, re-run
  `tests/property/test_canonical_invariance.py` under Hypothesis with at
  least `--hypothesis-seed=0 --hypothesis-deadline=none`.
- A phase is not closed until the `test-runner` agent reports the
  `pytest + ruff + mypy` table green, and the relevant closing check above
  is reproduced verbatim in the commit message.
