# IsalHG

## Project Identity

**IsalHG** -- *Instruction Set and Language for Hypergraphs*. Third member of
the Isal algorithm family (Grupo de Inteligencia Computacional y Analisis de
Imagen, UMA. PI: Ezequiel Lopez-Rubio).

The family represents combinatorial structures as strings over a compact
instruction alphabet executed against a Circular Doubly-Linked List + pointer
virtual machine. Members:

- **IsalGraph** (`/home/mpascual/research/code/IsalGraph`) -- finite simple
  graphs. Preprint 2026.
- **IsalSR** (`/home/mpascual/research/code/IsalSR`) -- labeled DAGs for
  symbolic-regression evaluation deduplication. IEEE TPAMI submission 2026.
- **IsalHG** (this repo) -- hypergraphs of arity `2 <= a <= k`. Seed proposal
  2026-06.

IsalHG has produced **two papers**:

1. **Iso-benchmark preprint (complete).** A native hypergraph isomorphism test
   via canonical-string equality, benchmarked against nauty, Traces, and bliss
   on the Levi bipartite reduction. Its methodology lives in
   `docs/preprint/{PROPOSAL,DATA,PREPRINT}.md` and the code-as-built spec in
   `docs/engineering/{CODE_DESIGN,DEVELOPMENT,ALGORITHMS}.md`. The C++ core is
   competitive but does not beat mature graph-iso engines on speed.
2. **Metric-space journal article (ACTIVE, target *Information Sciences*).** The
   pivot: the canonical string `w*(H)` embeds every hypergraph into the discrete
   metric space `(Σ_HG*, d_Lev)`; because `w*` is isomorphism-invariant,
   `d_I(H,H') = Levenshtein(w*(H), w*(H'))` is an iso-invariant hypergraph
   distance. The paper proves a **stability theorem** relating `d_I` to hypergraph
   edit distance and exploits it in classical applications (MDS, k-medoids,
   dendrograms, kNN, shortest path). This scope supersedes the *paper* framing of
   the preprint but **does not remove** the iso-detection code, which is its
   foundation.

Full seed proposal: `docs/isalhg_idea.pdf`. The active-article scope is the
context map below.

## Active scope — metric-space article (2026-07)

**Thesis.** IsalHG induces a structure-faithful metric on hypergraph space via
edit distance on canonical strings; a stability bound `d_I ≤ C(k,Δ)·HGED`
(provable, unlike the sibling's empirical-only claim) explains why the induced
geometry drives standard unsupervised/supervised pipelines, and its `Δ`-dependence
is a falsifiable prediction the density-sweep experiment tests.

**Context map (the hub — read the file relevant to your task).**

| Doc | Holds |
|---|---|
| `docs/article/PROPOSAL.md` | thesis, central experiment, applications, open questions |
| `docs/article/DATA.md` | corpora: exact-HGED correlation corpus + planted-family applications corpus |
| `docs/article/COMPETITORS.md` | the four competing representations + the fairness framing |
| `docs/article/CODE_DESIGN.md` | the `src/isalhg` refactor + `metric_space/` additions for this article |
| `docs/article/RELATED_WORK.md` | verified bibliography (theory + competitors, with code URLs) |
| `docs/article/theoretical/stability.md` | completeness → metric → **stability** theorem, proof strategy |
| `docs/article/empirical/correlation.md` | controlled validation: HGED oracle, correlation/density/info-content |
| `docs/article/empirical/applications.md` | MDS (flagship), clustering, kNN, shortest path |
| `docs/article/DEVELOPMENT/` | **the task ledger** — one file per task, under `<scope>/{OPEN,IN-PROGRESS,BLOCKED,CLOSED}/`; `README.md` is the hub (index, dependency graph, critical path) |

**Workflow.** Pick up work with the `task-reader` skill on a task in
`docs/article/DEVELOPMENT/`. When you find work outside your current task, log
it with the `task-handoff` skill rather than scope-creeping.

**Doc split.** `docs/article/` = the new article. `docs/preprint/`
(`PROPOSAL/DATA/PREPRINT.md`) = the iso-benchmark preprint's methodology.
`docs/engineering/` (`CODE_DESIGN/DEVELOPMENT/ALGORITHMS/CPP_*.md`) = the current
code's spec — still authoritative for the code as built.

## Scientific Mindset

- **No sycophancy.** When the user states a fact, verify it against the code,
  the proposal, or the seed PDF before building on it. If wrong or
  unsupported, say so directly and cite the contradicting source.
- **Mathematical rigor first.** When a design decision involves a derivation
  (string length bound, structural-tuple completeness, complexity), produce
  the derivation. Heuristic answers are flagged as heuristic.
- **Proactive.** Surface ablations, missing proofs, untested edge cases
  without being prompted. Open questions in `docs/preprint/PROPOSAL.md` (backtracking,
  value of `k`, tuple depth, completeness) are research tasks, not silent
  defaults.
- **Pursue completeness.** Every canonical-string claim must be empirically
  backed (unit + property tests over random hypergraphs) and eventually
  proved (theorem). Track both.

## Environment

- Conda env: `isalhg`
- Python: `~/.conda/envs/isalhg/bin/python`
- Project root: `/home/mpascual/research/code/IsalHG`

| Action | Command |
|---|---|
| Activate env | `conda activate isalhg` |
| Editable install | `pip install -e ".[dev]"` |
| Tests | `python -m pytest tests/ -v` |
| Unit tests only | `python -m pytest tests/unit/ -v -m unit` |
| Lint | `python -m ruff check src/ tests/` |
| Format | `python -m ruff format src/ tests/` |
| Types | `python -m mypy src/isalhg/` |
| HPC submit (Picasso) | use the `picasso-sbatch` skill; outputs land in `slurm/` |

## Architecture Overview

The architecture is documented in three layers:

1. `docs/preprint/PROPOSAL.md` -- scientific scope and validation methodology
   (5 tiers, competitors, datasets, metrics).
2. `docs/engineering/CODE_DESIGN.md` -- "where does code go": the four ABCs, the
   registry pattern, per-module mandates, the implementation order.
3. `.claude/rules/coding_rules.md` -- project-agnostic patterns (ABC +
   registry + lazy import, refactor protocol, style).

### Instruction set `Sigma_HG`

| Token | Semantics | Constraints |
|---|---|---|
| `V_{i,j}` | New edge over `i` existing nodes (`p_1..p_i`) + `j` new nodes (inserted after `p_1` in `L`) | `1 <= i,j <= k-1`, `2 <= i+j <= k` |
| `C_i` | New edge over `i` existing nodes (`p_1..p_i`); no pointer movement; no-op if edge exists | `1 <= i <= k` |
| `P_i` | Advance pointer `p_i` (forward in `L`) | `1 <= i <= k` |
| `N_i` | Retreat pointer `p_i` (backward in `L`) | `1 <= i <= k` |
| `W` | No-op | -- |

### Virtual machine state

`S = (H, L, p_1, ..., p_k)`. Initial state: `H` = single node, `L = [0]`,
all `p_i = 0`. Parameter `k` caps the maximum supported hyperedge arity
(default 10 per PROPOSAL decision B12).

### Dependency layering

```
isalhg.types     primitive type aliases
isalhg.errors    exception hierarchy

isalhg.core      ZERO non-stdlib deps              (VM + canonical algorithm)
  +-- core.algorithms                              (H2S variants, H2SAlgorithm ABC)

isalhg.adapters  optional: hypernetx / xgi /       (data-format bridges)
                          hypergraphx              (HypergraphAdapter ABC)

isalhg.iso_backends                                (isomorphism algorithms)
  +-- IsalHGBackend (wraps core.canonical)
  +-- PynautyLeviBackend, BlissLeviBackend
  +-- TracesLeviBackend  (subprocess via dreadnaut)

isalhg.datasets                                    (HypergraphDataset ABC)
  +-- synthetic/{exhaustive_small, erdos_renyi, chung_lu, hardness}
  +-- {arb_benson, xgi_loader, hic_atlas}

isalhg.protocols                                   (BenchmarkProtocol ABC)
  +-- pairwise_iso, fingerprint_timing,
      partition_agreement, structural_calibration

isalhg.metrics                                     (stateless primitives)

experiments/    (repo root, not installable)
  +-- configs/, orchestrator.py, schemas.py, analysis/
```

`core/` must never import from `adapters/`, `iso_backends/`, `datasets/`,
`protocols/`, or `metrics/`. Each higher layer imports only from layers
below it. See `docs/engineering/CODE_DESIGN.md` Section 4 for the full direction.

### Key modules

See `docs/engineering/CODE_DESIGN.md` Section 6 for the per-module mandate table.

## Critical Invariants

1. **Pointers are CDLL indices, not hypergraph node IDs.** Always resolve via
   `cdll.get_value(p_i)` before passing to any hypergraph operation.
2. **Closed alphabet.** Every string in `Sigma_HG*` decodes to a valid
   hypergraph. The S2H interpreter never rejects input.
3. **Round-trip.** `S2H(H2S(H)) ~ H` for every valid hypergraph `H`.
4. **Canonical seed.** The canonical algorithm runs greedy H2S from an
   *iso-invariant* seed set -- a node set preserved by every hypergraph
   automorphism -- and takes the lex-min string over it. The default
   (since T-M0) is the neighbour-degree cascade `max_neighbor_degree_nodes`
   (max label -> max degree -> lex-max sorted-desc neighbour degrees,
   variant `greedy_min_nbrdeg`); the historical `argmax_lex (xi_1, xi_2,
   xi_3)` set (`greedy_min`) is equally sound. What breaks the
   isomorphism-invariance claim is a *non*-iso-invariant seed rule -- e.g.
   selecting by raw node id (`greedy_single*`, a speed heuristic, not an
   exact iso test).
5. **`V` over `C` in ties.** Step 2 of the tie-breaking cascade is
   non-optional -- switching `V/C` priority changes the canonical string.
6. **`W` is meaningful.** Even though `W` is a no-op on the VM, it can appear
   in a canonical string to pad alignment. Do not strip `W` tokens during
   canonicalization.
7. **Pointer count = `k`.** The pointer-count parameter `k` must match the
   maximum hyperedge arity supported by the alphabet. Mismatch silently
   corrupts encoding.
8. **Structural-tuple depth.** Default depth 3 inherited from IsalGraph. Any
   deviation requires re-validating the canonical completeness conjecture.
9. **Backend equivalence under iso.** Every concrete `IsoBackend` satisfies
   `H1 ~ H2 => backend.fingerprint(H1) == backend.fingerprint(H2)`. The
   reverse direction is required for IsalHG (Conjecture) and asserted
   empirically for the baselines via Tier 5.

## Code Organization Rules

See `.claude/rules/coding_rules.md` for the full set. Project-specific
points:

- `core/` is stdlib-only. No `numpy`, no `networkx`, no `torch`.
- `adapters/` import external libraries only inside method bodies, so
  `from isalhg.adapters import xgi_adapter` succeeds even when XGI is not
  installed.
- `iso_backends/` import optional deps (`pynauty`, `python-igraph`) only
  inside method bodies; subprocess backends discover their binary via
  `shutil.which` at first call.
- Custom exception hierarchy per module under `isalhg.errors`.
- Python 3.10+ syntax (`X | None`, `list[int]`, `tuple[int, ...]`).
- Type hints on every function signature and return.
- NumPy-style docstrings with `Parameters` / `Returns` / `Raises`.

### Sibling project reference

When implementing a core module, **read the corresponding IsalGraph file
first** -- most modules port directly with the substitution
"edge = pair -> hyperedge = set" and "2 pointers -> k pointers".

| IsalHG module | Port template |
|---|---|
| `core/cdll.py` | `IsalGraph/src/isalgraph/core/cdll.py` |
| `core/sparse_hypergraph.py` | `IsalGraph/src/isalgraph/core/sparse_graph.py` |
| `core/algorithms/*.py` | `IsalGraph/src/isalgraph/core/algorithms/*.py` |
| `adapters/base.py` | `IsalSR/src/isalsr/adapters/base.py` (preferred over IsalGraph) |
| `iso_backends/base.py` | `IsalSR/src/isalsr/core/algorithms/base.py` (ABC + registry pattern) |
| `experiments/orchestrator.py` | `IsalSR/experiments/models/orchestrator.py` (idempotent JSON-skip loop) |
| `experiments/schemas.py` | `IsalSR/experiments/models/schemas.py` |

## Mathematical Foundation (brief)

**Round-trip.** For all `w in Sigma_HG*` reachable from a valid hypergraph:
`H2S(S2H(w)) == w` up to canonical-string normalization. Equivalently,
`S2H(H2S(H)) ~ H` for all hypergraphs `H` representable by the chosen `k`.

**Canonical string.**
`w*(H) := argmin_lex { w in greedy_H2S(H, v_0) : v_0 in S(H) }` for an
iso-invariant seed set `S(H)` (invariant 4).
**Completeness (RESOLVED at T-TA, 2026-07-08; proof in
`/media/.../ISAL/isalhg/proofs/theorem_a_completeness.{tex,pdf}`):**
- `w*(H1) = w*(H2) => H1 ~ H2` holds unconditionally for every variant
  (round-trip soundness) — over the augmented fingerprint
  `F(H) = (seed vertex label, w*(H))`; the bare string misses the seed
  vertex label on non-trivial vocabularies. Implemented at T-TAb:
  `core.canonical.canonical_fingerprint` computes `F`, `IsalHGBackend`
  serialises it (`b"{label}|{w*}"`, prefix omitted when `|Sigma_V| = 1`),
  and `d_I` measures the seed-label-prefixed token sequence.
- The converse is **FALSE for the greedy variants** (`greedy_min`,
  `greedy_min_nbrdeg`, `exhaustive`): the residual V-tie-break by raw edge
  id makes `w*` depend on the edge insertion order (pinned n=4
  counterexample in `tests/unit/core/test_greedy_min_complete.py`).
- The converse is **proved for `greedy_min_complete`** (tie-complete
  branching, `tie_branch=True`), whose `w*_c` is a complete isomorphism
  invariant. Metric-space claims (`d_I`, Theorem B) attach to `w*_c`.

**Isomorphism test.** `iso(H1, H2) := (F(H1) == F(H2))` — exact with
`greedy_min_complete`; with the greedy variants it is one-sided (equal
fingerprints certify iso) and exact only under edge-order-preserving inputs.
Comparing bare `w*` instead of `F` is a false positive on labelled inputs.

## Scientific Development Protocol

### 1. Evidence-grounded changes
Every implementation decision points to either (a) a section of
`docs/preprint/PROPOSAL.md` or the seed PDF (`docs/isalhg_idea.pdf`), (b) a section
of an IsalGraph or IsalSR paper, or (c) a unit test that fails without the
change. No silent defaults.

### 2. Plan -> Test -> Implement -> Verify
Each module begins with an acceptance-criteria checklist (top comment or
sibling `.md`), then a failing test, then the implementation, then a
written summary of what the diff confirms.

### 3. Interdisciplinary rigor
Where hypergraph theory and pointer-machine theory disagree, surface the
disagreement in the docstring and link to the source paper.

### 4. Proactive agent behavior
When implementing the canonical algorithm, flag every place where the
completeness conjecture is unverified. When implementing an adapter, flag
every edge case the external library handles differently (HyperNetX allows
multi-hyperedges with identical node sets; `SparseHypergraph` does not).

### 5. Code & experiment standards
- Random seeds pinned and printed.
- Wall-clock + peak RSS reported alongside correctness for every benchmark.
- Hypothesis property tests for `S2H`/`H2S` round-trip and canonical
  invariance.
- All `print` calls in library code routed through `logging`. `print` is
  OK in scripts and notebooks.

### 6. Communication standards
Quantify. "Properties P1-P3 hold on all 2,400 sampled hypergraphs with
`k in {2..5}`, `n in {3..20}`" beats "passes tests". Cite IsalGraph and
IsalSR papers when porting reasoning.

### 7. Verification & self-correction
After any non-trivial implementation, invoke the `test-runner` agent.
After any change to canonical-related code, also re-run the property tests
under hypothesis. Report the table even if all green.

## Custom Agents and Skills

| Agent | Model | Tools | Purpose |
|---|---|---|---|
| `test-runner` | haiku | Bash, Read | Run pytest + ruff + mypy in the `isalhg` env; report summary table |

Useful skills:
- `task-reader` -- pick up a task from `docs/article/DEVELOPMENT/` and execute
  it context-first (plan mode, read cited context, flag decisions, verify).
- `task-handoff` -- park out-of-scope work as a new ledger task mid-development.
- `picasso-sbatch` -- SLURM scripts for Picasso.
- `research-rigor` -- audits experimental plans for missing ablations /
  leakage / unjustified parameters.
- `humanizer` -- writing-style normalization.
- `read-paper`, `literature-search` -- related work.

## Key References

- Lopez-Rubio, E. & Pascual-Gonzalez, M. *Representation of Graphs by
  Sequences of Instructions* (preprint, 2026).
- Lopez-Rubio, E., Pascual-Gonzalez, M. & Thurnhofer-Hemsi, K.
  *Representation of Directed Acyclic Graphs by Sequences of Instructions
  for Symbolic Regression* (IEEE TPAMI submission, 2026).
- Lopez-Rubio, E. *IsalHG seed proposal* (2026-06-06). Local:
  `docs/isalhg_idea.pdf`.
- Bai, S., Zhang, F. & Torr, P.H.S. *Hypergraph Convolution and Hypergraph
  Attention*. Pattern Recognition 110, 2021.
- McKay, B.D. & Piperno, A. *Practical graph isomorphism, II*. Journal of
  Symbolic Computation 60, 2014. (nauty + Traces)
- Junttila, T. & Kaski, P. *Engineering an efficient canonical labeling
  tool for large and sparse graphs*. ALENEX 2007. (bliss)

## Detailed Specifications

Active-article scope (auto-loaded): thesis + the task-ledger hub. Individual task
files under `docs/article/DEVELOPMENT/<scope>/<status>/` are read on demand by the
`task-reader` skill, not auto-loaded.

@docs/article/PROPOSAL.md
@docs/article/DEVELOPMENT/README.md

Code map (iso-benchmark spec, still authoritative for the code as built):

@docs/engineering/CODE_DESIGN.md
@.claude/rules/coding_rules.md

The iso-benchmark dev log `docs/engineering/DEVELOPMENT.md` is no longer auto-loaded; it is
reachable via the context map above. The article code map is
`docs/article/CODE_DESIGN.md`.
