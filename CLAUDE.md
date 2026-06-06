# IsalHG

## Project Identity

**IsalHG** — *Instruction Set and Language for Hypergraphs*. Third member of the Isal algorithm family (Grupo de Inteligencia Computacional y Análisis de Imagen, UMA. PI: Ezequiel López-Rubio).

The family represents combinatorial structures as strings over a compact instruction alphabet executed against a Circular Doubly-Linked List + pointer virtual machine. Members:

- **IsalGraph** (`/home/mpascual/research/code/IsalGraph`) — finite simple graphs. Preprint 2026.
- **IsalSR** (`/home/mpascual/research/code/IsalSR`) — labeled DAGs for symbolic-regression evaluation deduplication. IEEE TPAMI submission 2026.
- **IsalHG** (this repo) — hypergraphs of arity `2 ≤ a ≤ k`. Seed proposal 2026-06.

Primary application of IsalHG: a native hypergraph isomorphism test via canonical-string equality. Target venue: a Computational Mathematics journal.

Full seed proposal: see project memory `idea_060626.md` (also at `docs/isalhg_idea.pdf`).
Family abstraction summary: see project memory `family_isal_precedents.md`.

## Scientific Mindset

- **No sycophancy.** When the user states a fact, verify it against the code or the PI's proposal before building on it. If wrong or unsupported, say so directly and cite the contradicting source.
- **Mathematical rigor first.** When a design decision involves a derivation (string length bound, structural-tuple completeness, complexity), produce the derivation. Heuristic answers are flagged as heuristic.
- **Proactive.** Surface ablations, missing proofs, untested edge cases without being prompted. The IsalHG seed proposal has explicit open questions (backtracking, value of `k`, tuple depth, completeness) — these are research tasks, not implementation details to silently default.
- **Pursue completeness.** Every canonical-string claim must be empirically backed (unit tests over random hypergraphs) *and* eventually proved (theorem). Track both.

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

### Instruction set `Σ_HG`

| Token | Semantics | Constraints |
|---|---|---|
| `V_{i,j}` | New edge connecting `i` existing nodes (`p_1..p_i`) plus `j` new nodes (inserted after `p_1` in `L`) | `1 ≤ i,j ≤ k-1`, `2 ≤ i+j ≤ k` |
| `C_i` | New edge connecting `i` existing nodes (`p_1..p_i`); no pointer movement; no-op if edge exists | `1 ≤ i ≤ k` |
| `P_i` | Advance pointer `p_i` (forward in `L`) | `1 ≤ i ≤ k` |
| `N_i` | Retreat pointer `p_i` (backward in `L`) | `1 ≤ i ≤ k` |
| `W` | No-op | — |

### Virtual machine state

`S = (H, L, p_1, ..., p_k)` where `H` is the partial hypergraph, `L` is the CDLL of node IDs, and `p_1..p_k` are pointer indices into `L`. Initial state: `H` = single node, `L = [0]`, all `p_i = 0`. Parameter `k` is the maximum hyperedge arity supported.

### Dependency layering

```
isalhg.core          ZERO non-stdlib deps        (algorithm)
isalhg.adapters      optional: hypernetx / xgi   (bridges)
                              hypergraphx / dhg
```

`core` must never import from `adapters`. Adapters guard their external imports behind try/except and raise `ImportError` with a clear install hint on first use.

### Key modules (post-bootstrap)

- `src/isalhg/core/cdll.py` — `CircularDoublyLinkedList`, array-backed. Port template: `IsalGraph/src/isalgraph/core/cdll.py`.
- `src/isalhg/core/pointers.py` — `KPointerSet`. Manages `p_1..p_k` and their advance/retreat semantics.
- `src/isalhg/core/sparse_hypergraph.py` — adjacency-set hypergraph (contiguous int IDs; hyperedges as frozensets). Generalizes `IsalGraph/src/isalgraph/core/sparse_graph.py`.
- `src/isalhg/core/instructions.py` — `Σ_HG` token definitions, parsing, validity.
- `src/isalhg/core/string_to_hypergraph.py` — S2H interpreter.
- `src/isalhg/core/hypergraph_to_string.py` — H2S greedy encoder with tie-breaking cascade.
- `src/isalhg/core/structural_tuples.py` — `ξ` (per-node) and `η` (per-edge) computation, depth 3 by default.
- `src/isalhg/core/canonical.py` — canonical entry point; seeds from max-`ξ` nodes.
- `src/isalhg/core/canonical_pruned.py` — backtracking variant (algorithm currently **unspecified** by the PI; see open questions).
- `src/isalhg/adapters/{hypernetx,xgi,hypergraphx,dhg}_adapter.py` — library bridges.

## Critical Invariants

1. **Pointers are CDLL indices, not hypergraph node IDs.** Always resolve via `cdll.get_value(p_i)` before passing to any hypergraph operation.
2. **Closed alphabet.** Every string in `Σ_HG*` decodes to a valid hypergraph. The S2H interpreter never rejects input.
3. **Round-trip.** `S2H(H2S(H)) ≅ H` for every valid hypergraph `H`.
4. **Canonical seed.** The canonical algorithm runs greedy H2S from nodes of *maximum lexicographic* `(ξ_1, ξ_2, ξ_3)`. Any other seed strategy breaks the isomorphism-invariance claim.
5. **`V` over `C` in ties.** Step 2 of the tie-breaking cascade is non-optional — switching `V/C` priority changes the canonical string.
6. **`W` is meaningful.** Even though `W` is a no-op on the VM, it can appear in a canonical string to pad alignment. Do not strip `W` tokens during canonicalization.
7. **Pointer count = `k`.** The pointer-count parameter `k` must match the maximum hyperedge arity supported by the alphabet. Mismatch silently corrupts encoding.
8. **Structural-tuple depth.** Default depth 3 inherited from IsalGraph. Any deviation requires re-validating the canonical completeness conjecture.

## Code Organization Rules

- `core/` is stdlib-only. No `numpy`, no `networkx`, no `torch`.
- `adapters/` import external libraries only inside method bodies or under `try/except ImportError`, so `from isalhg.adapters import xgi_adapter` succeeds even when XGI is not installed.
- One class per file when the class exceeds ~100 lines.
- Custom exception hierarchy per module under `isalhg.errors`: `IsalHGError → {InvalidInstructionError, CanonicalizationTimeoutError, ArityMismatchError}`.
- Python 3.10+ syntax (`X | None`, `list[int]`, `tuple[int, ...]`).
- Type hints on every function signature and return.
- NumPy-style docstrings with `Parameters` / `Returns` / `Raises`.
- Brief inline comments explain *why*, not *what*.

### Sibling project reference

When implementing a core module, **read the corresponding IsalGraph file first** — most modules port directly with the substitution "edge = pair → hyperedge = set" and "2 pointers → k pointers". Reference paths:

| IsalHG module | Port template |
|---|---|
| `core/cdll.py` | `IsalGraph/src/isalgraph/core/cdll.py` |
| `core/sparse_hypergraph.py` | `IsalGraph/src/isalgraph/core/sparse_graph.py` |
| `core/algorithms/*.py` | `IsalGraph/src/isalgraph/core/algorithms/*.py` |
| `adapters/base.py` | `IsalGraph/src/isalgraph/adapters/base.py` |

## Mathematical Foundation (brief)

**Round-trip.** For all `w ∈ Σ_HG*` reachable from a valid hypergraph: `H2S(S2H(w)) ≡ w` up to canonical-string normalization. Equivalently, `S2H(H2S(H)) ≅ H` for all hypergraphs `H` representable by the chosen `k`.

**Canonical string.** `w*_H := argmin_{lex} { w : w ∈ greedy_H2S(H, v_0), v_0 ∈ argmax_{lex} ξ(v) }`. Conjecture: `w*_{H_1} = w*_{H_2} ⇔ H_1 ≅ H_2` under hypergraph isomorphism. **Not yet proved**; required for publication.

**Isomorphism test.** `iso(H_1, H_2) := (w*_{H_1} == w*_{H_2})`. Pending the conjecture above, this is correct by construction.

## Scientific Development Protocol

### 1. Evidence-grounded changes
Every implementation decision points to either (a) a section of the PI's seed proposal (`docs/isalhg_idea.pdf` / `idea_060626.md`), (b) a section of an IsalGraph or IsalSR paper, or (c) a unit test that fails without the change. No silent defaults.

### 2. Plan → Test → Analyze → Fix
Begin every module with a written acceptance-criteria checklist (in a comment block at the top of the file or in a sibling `.md`). Then write the failing test. Then implement. Then read the test output and explain what the diff confirms. No "looks right" closures.

### 3. Interdisciplinary rigor
Where hypergraph theory and pointer-machine theory disagree, surface the disagreement in the docstring and link to the source paper.

### 4. Proactive agent behavior
Surface ablations and missing tests without being asked. When implementing the canonical algorithm, flag every place where the completeness conjecture is unverified. When implementing an adapter, flag every edge case the external library handles differently (e.g., HyperNetX allows multi-hyperedges with identical node sets; `SparseHypergraph` does not).

### 5. Code & experiment standards
- Random seeds pinned and printed.
- Wall-clock + memory reported alongside correctness for every benchmark.
- Hypothesis property tests for `S2H`/`H2S` round-trip and canonical-equality invariance.
- All `print` calls in library code routed through `logging`. `print` is OK in scripts and notebooks.

### 6. Communication standards
Quantify. "Properties P1–P3 hold on all 2,400 sampled hypergraphs with `k ∈ {2..5}`, `n ∈ {3..20}`" beats "passes tests". Cite IsalGraph and IsalSR papers when porting reasoning.

### 7. Verification & self-correction
After any non-trivial implementation, invoke the `test-runner` agent. After any change to canonical-related code, also re-run the property tests under hypothesis. Report the table even if all green.

## Custom Agents and Skills

| Agent | Model | Tools | Purpose |
|---|---|---|---|
| `test-runner` | haiku | Bash, Read | Run pytest + ruff + mypy in the `isalhg` env; report summary table |

Useful skills (global, no project-specific config required):
- `picasso-sbatch` — generates SLURM scripts for Picasso (`slurm/` layout).
- `research-rigor` — audits experimental plans for missing ablations / leakage / unjustified parameters.
- `humanizer` — applies the lab's writing-style normalization to scientific text.
- `read-paper`, `literature-search` — when expanding the related-work section.

## Key References

- López-Rubio, E. & Pascual-González, M. *Representation of Graphs by Sequences of Instructions* (preprint, 2026). Local: `/media/mpascual/Sandisk2TB/research/ISAL/completed/isalgraph/article/69b82c5859ed47c5468ca199`.
- López-Rubio, E., Pascual-González, M. & Thurnhofer-Hemsi, K. *Representation of Directed Acyclic Graphs by Sequences of Instructions for Symbolic Regression* (IEEE TPAMI submission, 2026). Local: `/media/mpascual/Sandisk2TB/research/ISAL/completed/isalsr/article/journal/69c1637a28a81fea2badda9a/article/paper`.
- López-Rubio, E. *IsalHG seed proposal* (2026-06-06). Local: `docs/isalhg_idea.pdf` (mirrored from `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/docs/`).
- Bai, S., Zhang, F. & Torr, P.H.S. *Hypergraph Convolution and Hypergraph Attention*. Pattern Recognition 110, 2021. — cited in IsalGraph as the named gap that IsalHG fills.

## Detailed Specifications

@src/isalhg/core/README.md (created post-bootstrap; current scaffold has a placeholder)
@docs/DEVELOPMENT.md
