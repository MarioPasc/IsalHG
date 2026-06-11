# Development notes

Living document for IsalHG development. Pair-read with `CLAUDE.md` at the
repo root, `docs/CODE_DESIGN.md` (architectural lookup), and the seed
proposal (`docs/isalhg_idea.pdf` + `docs/PROPOSAL.md`).

## Status

The repo currently holds a **scaffold + documentation refactor only**: ABCs,
registry stubs, signature-only placeholders that `raise NotImplementedError`,
and test files that `pytest.skip("not implemented yet")`. No algorithmic code
yet.

## Implementation order

Coding agents should fill stubs in the order specified in
`docs/CODE_DESIGN.md` Section 7. Brief summary:

1. `core/sparse_hypergraph.py`, `core/cdll.py`, `core/pointers.py`
   (port from IsalGraph templates).
2. `core/instructions.py`, `core/string_to_hypergraph.py`,
   `core/hypergraph_to_string.py`, `core/structural_tuples.py`,
   `core/canonical.py`.
3. `core/algorithms/{greedy_single, greedy_min, exhaustive}.py`.
4. `adapters/xgi_adapter.py` (unlocks Tier 1, 2, 4 datasets).
5. `iso_backends/{isalhg_backend, levi_reduction, pynauty_levi}.py`.
6. `datasets/base.py`, `datasets/synthetic/exhaustive_small.py`,
   `datasets/registry.py`.
7. `protocols/{base, pairwise_iso}.py`, `protocols/registry.py`.
8. `experiments/orchestrator.py` end-to-end on Tier 1.
9. Remaining backends, datasets, protocols, analysis.

Each step lands with its unit tests populated and passing under
`pytest -m unit`.

## Removed in the architectural refactor

| Path | Reason |
|---|---|
| `src/isalhg/core/canonical_pruned.py` | PI has not specified the backtracking algorithm. Reintroduce when the algorithm is specified. |
| `src/isalhg/core/algorithms/pruned_exhaustive.py` | Same reason. |
| `tests/unit/test_canonical_pruned.py` | Mirror of the above. |
| `benchmarks/` (repo root) | Replaced by `src/isalhg/datasets/` (loaders) + `experiments/configs/` (run specs). |

## Open research questions (from the seed proposal and PROPOSAL.md)

1. **Backtracking procedure for greedy ties** -- unspecified by the PI.
   A `core/canonical_pruned.py` module will be reintroduced once an algorithm
   exists.
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

## Validation tier map (from `docs/PROPOSAL.md`)

| Tier | Datasets (`isalhg.datasets`) | Protocol (`isalhg.protocols`) |
|---|---|---|
| 1 (correctness) | `synthetic.exhaustive_small`, plus published designs | `pairwise_iso` |
| 2 (scaling) | `synthetic.erdos_renyi`, `synthetic.chung_lu` | `fingerprint_timing` |
| 3 (hardness) | `synthetic.hardness` | `pairwise_iso` (600 s timeout) |
| 4 (calibration) | `arb_benson`, `xgi_loader` | `structural_calibration` |
| 5 (atlas) | `hic_atlas` | `partition_agreement` |

The orchestrator drives `Protocol x Backend x Dataset x Seed` from each
`experiments/configs/tier{N}_*.yaml`.
