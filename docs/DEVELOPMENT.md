# Development notes

Living document for IsalHG development. Pair-read with `CLAUDE.md` at the
repo root, `docs/CODE_DESIGN.md` (architectural lookup), and the seed
proposal (`docs/isalhg_idea.pdf` + `docs/PROPOSAL.md`).

## Status

**Phase 1 + Phase 2 closed (2026-06-11).** The repo now ships a working
canonical-string algorithm (`isalhg.core.*`) plus the `IsoBackend` interface
with both the IsalHG and pynauty-via-Levi concrete backends, the XGI
adapter, and a registry. Phases 3-6 (datasets, protocols, experiments,
remaining backends) remain scaffold-only.

## Implementation order

Coding agents should fill stubs in the six-phase order specified in
`docs/CODE_DESIGN.md` Section 7. Each phase closes with a concrete runnable
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

3. **Tier 1 end-to-end** -- `datasets/{base, registry, synthetic.exhaustive_small}`
   + `metrics.correctness` + `protocols/{base, pairwise_iso, registry}` +
   `experiments/{schemas, orchestrator}` + `tier1.yaml`. Closes on
   `python -m experiments.orchestrator --config tier1_correctness.yaml`
   reporting FP = FN = 0.
4. **Remaining backends** -- `bliss_levi`, then
   `subprocess_base` + `traces_levi`. Closes on Tier 1 re-running with all
   four backends in agreement.
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
8. **Isomorphism-pair generation** -- resolved by decision I44
   (`docs/PROPOSAL.md`, 2026-06-11). Positive pairs via stdlib-only
   `core.sparse_hypergraph.permute(H, σ)`; hard negatives from published
   design-theoretic non-iso pairs (Kaski & Östergård 2004 STS classifications,
   GQ(2,2) variants) embedded as Tier-1 fixtures, plus pynauty-certified
   random sweeps for Tier 2 / Tier 3. HG-CFI source documented as empty
   until C14 produces a construction.
9. **Label vocabulary** -- resolved by decision I45
   (`docs/PROPOSAL.md`, 2026-06-11). Vocabularies are dataset-scoped, fitted
   once at load by `LabelVocabulary.fit(items)` (lexicographic sort →
   contiguous int IDs), persisted on `DatasetMetadata`. `core/` never sees
   semantic strings; the Levi reduction lifts both color classes onto
   `B(H)` with disjoint id ranges. Mirrors the nauty / Traces / bliss
   colored-graph contract; faithful to the IsalSR pattern of a
   dataset-supplied operator catalog over a VM that stays
   alphabet-agnostic.

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
