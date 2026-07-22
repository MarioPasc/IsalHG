# T-M7i — Implement Chung–Lu and mixed-arity connected generators
**Declared:** 2026-07-22 15:40 CEST
**Status:** OPEN
**Depends on:** T-M7b (declared the cells that need these generators)
**Delegation:** agent
**Why out of scope:** T-M7b's scope was limited to `experiments/article/`; filling
the `ChungLuHypergraphs` stub and adding a mixed-arity generator requires
`src/isalhg/datasets/synthetic/` and `tests/unit/datasets/`, which belong to a
separate lane. This task must NOT run concurrently with T-M7a (both touch the
same `src/isalhg/datasets/synthetic/` module tree and the dataset registry).
**Context to read first:**
- `src/isalhg/datasets/synthetic/chung_lu.py` — stub raising `NotImplementedError`;
  fill `__iter__`, `metadata`, `__len__`, `seed()` matching the
  `UniformErdosRenyiHypergraphs` interface
- `src/isalhg/datasets/synthetic/erdos_renyi.py::UniformErdosRenyiHypergraphs` —
  the template for a connected-only hypergraph generator (rejection sampling,
  `require_connected`, `connected_max_attempts`)
- `src/isalhg/datasets/registry.py` — register the Chung–Lu dataset; add a
  mixed-arity ER generator under a new name
- `docs/article/REVIEW/DATA.md` §2B ("Stratum B grid") — grid parameters the
  generators must support: density `c = m/n`, arity cap `k`, mixed arity `[2,k]`
- `docs/article/DEVELOPMENT/T-M7/CLOSED/T-M7b.md` — which cells are blocked on
  these generators (skip_reason in {`generator_not_impl`, `mode_not_impl`})
- `docs/engineering/CODE_DESIGN.md` §5.2 ("Add a new HypergraphDataset") —
  checklist for dataset additions
- `.claude/rules/coding_rules.md` — always
**Description:** Fill the `ChungLuHypergraphs` stub (connected-only, rejection
sampling, deterministic under `(parameters, seed)`) and add a mixed-arity ER
generator that draws each hyperedge's arity uniformly from `[2, k]` rather than
fixing it at `k`. Register both in `datasets/registry.py`. Without these,
approximately two-thirds of the Stratum B declared grid (`generator_not_impl` and
`mode_not_impl` cells) is undischargeable.
**Acceptance:** `ChungLuHypergraphs` is registered and generates connected
hypergraphs deterministically; a mixed-arity `[2,k]` ER generator is registered
under a new name (e.g. `"random_erdos_renyi_mixed"`); `stratum_b_cells.py`
skip_reason is empty for all previously `not_impl` cells; unit tests under
`tests/unit/datasets/` cover determinism, connectivity, seed contract, and the
mixed-arity arity distribution; `pytest tests/unit/datasets/ -q` green.
**Out of scope here:** running the Picasso feasibility pilot for these cells
(T-M7h); any changes to `experiments/article/`; updating
`stratum_b_feasibility_envelope.json` (that is T-M7h's job after this unblocks it).
