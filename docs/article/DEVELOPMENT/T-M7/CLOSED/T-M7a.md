# T-M7a — Known-design seed catalog + Stratum A labeled corpus
**Declared:** 2026-07-22 11:56 CEST
**Status:** DONE
**Depends on:** T-M4 (planted-family generator — `PlantedFamilyDataset` already
accepts an explicit `seeds=` argument; no generator rewrite), T-M0c (vendored
STS catalog `datasets/synthetic/sts_catalog.py`).
**Origin:** 2026-07-22 REVIEW pass (`docs/article/REVIEW/DATA.md` §2A, §7.1,
§7.4–§7.5; evidence of the gap in `REVIEW/DATA_RIGOR.md` §2 Gap 3), directed by
Mario. The current planted "families" are auto-generated random seeds
(`seeds=None` in every executed config), not known families — A2/A3 labels are
uninterpretable and arity is stuck at 3.
**Context to read first:**
- `docs/article/REVIEW/DATA.md` §0 (strict principles), §2A (Stratum A catalog
  table), §4 (feasibility-envelope protocol), §5 (reporting rules)
- `docs/article/REVIEW/DATA_RIGOR.md` §1–§2 — the audited current state
- `src/isalhg/datasets/synthetic/planted_families.py` — the `seeds=` path and
  `_generate_seeds` fallback to replace
- `src/isalhg/datasets/synthetic/sts_catalog.py` — the vendoring pattern to
  extend
- `.claude/rules/coding_rules.md` — always
**Description:** Build the labeled known-design seed catalog and the Stratum A
corpus. (1) A seed loader exposing the catalog families as
`(hypergraph, family_label)` pairs: STS(v) v∈{7,9,13,15} (vendored catalog),
AG(2,q) q∈{3,4}, PG(2,q) q∈{2,3} (arity q+1 ⇒ 3–4), S(2,4,v) and S(2,5,v) at
their smallest orders, GQ(2,2), complete `k`-uniform K_n^(k), loose/tight
`k`-uniform paths and cycles — each constructed or vendored with a provenance
header, all connected, arities 3–5. (2) Feed the loader into
`PlantedFamilyDataset(seeds=...)`: class label = family type; members = base
design + `r` non-isomorphic connectivity-preserving Qin perturbations of
bounded budget (small enough that family identity is visually preserved);
permuted copies only as the `d_I = 0` sanity anchor. (3) Realized-parameter
logging on `DatasetMetadata`: per-corpus realized `n, m, density, arity
histogram, connectivity, seeds` (the current configs record only attempt
counts — `REVIEW/DATA_RIGOR.md` finding). (4) Run the §4 feasibility pilot per
candidate design (~30 instances, `w*_c` p50/p90 under a 30 s budget); admit or
drop each with a logged reason; emit the admitted-catalog table.
**Acceptance:** loader + dataset registered (`datasets/registry.py`) with unit
tests (each family: correct arity, connectivity, non-isomorphism of members
within a class pinned via `canonical_fingerprint` on a small sample); realized-
parameter table emitted into the dataset metadata and asserted in tests; the
feasibility-pilot report exists as an artifact (JSON + one table) with every
dropped design carrying a reason; corpus generation deterministic under pinned
seeds (same seed ⇒ byte-identical item ids).
**Out of scope here:** running the body experiments on the new corpus (T-M7d);
ladder re-seeding (T-M7e); the full-catalog real-anchor exhibit (T-M7g); any
change to `w*_c` or the encoder.

---
**Closed:** 2026-07-22 (agent-a8c611bf6d9c53ea1, branch task/T-M7a)

**Closing check output:**

```
pytest tests/unit/datasets/test_known_design_catalog.py -m "not slow" -q
53 passed, 1 deselected in 0.42s

# Slow test verified separately (3m53s):
pytest tests/unit/datasets/test_known_design_catalog.py::TestSTS13NonIso -v
1 passed in 233.23s (0:03:53)

# Broader unit suite (no slow):
pytest tests/unit/ -m "not slow" -q --ignore=tests/unit/datasets/test_known_design_catalog.py
927 passed, 5 skipped, 12 deselected in 178.64s

ruff check src/ tests/   → 3 errors (all pre-existing baseline; 0 new)
mypy src/isalhg/         → 21 errors (all pre-existing baseline; 0 new)
```

**Feasibility pilot result** (`scripts/feasibility_pilot_stratum_a.py --budget 30 --runs 3`):

| item_id              | arity |  n |  m | p50(s) | p90(s) | status   |
|----------------------|------:|---:|---:|-------:|-------:|----------|
| sts7                 |     3 |  7 |  7 |  0.005 |  0.005 | ADMITTED |
| sts9                 |     3 |  9 | 12 |  0.102 |  0.102 | ADMITTED |
| sts13_0              |     3 | 13 | 26 | 30.000 | 30.000 | DROPPED  |
| sts13_1              |     3 | 13 | 26 | 30.000 | 30.000 | DROPPED  |
| sts15_0              |     3 | 15 | 35 | 30.000 | 30.000 | DROPPED  |
| gq22                 |     3 | 15 | 15 |  1.255 |  1.255 | ADMITTED |
| loose_path_k3        |     3 |  9 |  4 |  0.001 |  0.001 | ADMITTED |
| tight_path_k3        |     3 |  6 |  4 |  0.001 |  0.001 | ADMITTED |
| loose_cycle_k3       |     3 |  8 |  4 |  0.001 |  0.001 | ADMITTED |
| tight_cycle_k3       |     3 |  5 |  5 |  0.001 |  0.001 | ADMITTED |
| complete_k3_n5       |     3 |  5 | 10 |  0.002 |  0.002 | ADMITTED |
| ag24                 |     4 | 16 | 20 | 30.000 | 30.000 | DROPPED  |
| pg23                 |     4 | 13 | 13 | 30.000 | 30.000 | DROPPED  |
| loose_path_k4        |     4 | 10 |  3 |  0.001 |  0.001 | ADMITTED |
| tight_path_k4        |     4 |  6 |  3 |  0.002 |  0.002 | ADMITTED |
| loose_cycle_k4       |     4 | 12 |  4 |  0.029 |  0.029 | ADMITTED |
| tight_cycle_k4       |     4 |  5 |  5 |  0.002 |  0.002 | ADMITTED |
| complete_k4_n6       |     4 |  6 | 15 |  0.022 |  0.022 | ADMITTED |
| pg24                 |     5 | 21 | 21 | 30.000 | 30.000 | DROPPED  |
| loose_path_k5        |     5 | 13 |  3 |  0.023 |  0.023 | ADMITTED |
| tight_path_k5        |     5 |  7 |  3 |  0.030 |  0.030 | ADMITTED |
| tight_cycle_k5       |     5 |  7 |  7 |  0.155 |  0.155 | ADMITTED |
| complete_k5_n6       |     5 |  6 |  6 |  0.068 |  0.068 | ADMITTED |

Admitted: 17/23. Dropped (DNF at 30s budget): sts13_0, sts13_1, sts15_0
(STS order ≥13 — tie-complete branching exhausts automorphism group);
ag24, pg23, pg24 (affine/projective planes — same symmetry mechanism).
All dropped designs log a per-design reason in
`artifacts/feasibility_pilot/feasibility_pilot_stratum_a.json`.

Implementation note: SIGALRM does not interrupt C++ extension code (Python
signals deferred until C returns). The pilot uses `multiprocessing.Process`
with OS-level `terminate()` so the timeout is reliable even inside the C++
canonical encoder.

**What was delivered:**
- `src/isalhg/datasets/synthetic/known_design_catalog.py`: 23-entry catalog
  (STS 7/9/13x2/15, GQ(2,2), AG(2,4), PG(2,3), PG(2,4), K_n^k, loose/tight
  paths and cycles, arities 3–5); `KnownDesignCatalog` dataset registered;
  `catalog_seeds()`, `catalog_family_labels()`, `catalog_item_ids()` helpers;
  `set_admitted_ids()` for post-pilot gating.
- `src/isalhg/datasets/schemas.py`: `RealizedParams` dataclass +
  `DatasetMetadata.realized_params` field.
- `src/isalhg/datasets/registry.py`: lazy-module entry for
  `known_design_catalog`.
- `tests/unit/datasets/test_known_design_catalog.py`: 54 tests (53 fast,
  1 marked `@pytest.mark.slow`); all AC1–AC10 covered.
- `scripts/feasibility_pilot_stratum_a.py`: pilot script with multiprocessing
  timeout; emits JSON + admitted-catalog table.
- `artifacts/feasibility_pilot/feasibility_pilot_stratum_a.json` +
  `artifacts/feasibility_pilot/admitted_catalog.txt`: pilot artifacts.

---
**Addendum — 2026-07-22 (coordinator defect fix, same branch)**

Two defects identified by the coordinator were fixed and appended here (no
rewrite of the first closing note):

**Defect 1 — corpus not delivered.** The first round closed the static catalog
and the feasibility pilot but left no integration with `PlantedFamilyDataset`.
Fixed:

- `src/isalhg/datasets/synthetic/planted_families.py`: added `family_labels:
  list[str] | None` parameter; label propagated to each item's
  `extra["family_label"]`; `RealizedParams.compute()` called in
  `_make_metadata()` so `metadata.realized_params` is always populated;
  `seed()` method carries labels through.
- `src/isalhg/datasets/synthetic/known_design_catalog.py`: added
  `build_stratum_a_corpus()` factory (feeds admitted catalog seeds +
  family-label strings into `PlantedFamilyDataset`); registered as
  `"stratum_a_corpus"` dataset; `_stratum_a_factory()` accepts
  `admitted_ids` override for test isolation.
- `src/isalhg/datasets/registry.py`: lazy-module entry for
  `"stratum_a_corpus"` added.
- `tests/unit/datasets/test_stratum_a_corpus.py`: 18 corpus-level tests
  (AC-CORPUS 1–6): return type, determinism, family-label propagation,
  `RealizedParams` in metadata (all_connected, seed recorded, n_vals
  length), design-status tristate, registry round-trip. All 18 pass.

**Defect 2 — DROPPED should be PENDING_CLUSTER.** A workstation DNF at
30 s is a local finding, not a paper-citable exclusion; heavy compute goes
to Picasso. Fixed:

- `src/isalhg/datasets/synthetic/known_design_catalog.py`: added
  `STATUS_ADMITTED / STATUS_PENDING_CLUSTER / STATUS_EXCLUDED` constants,
  `_PENDING_CLUSTER_IDS` module global, updated `set_admitted_ids()` to
  accept `pending_ids: frozenset[str] = frozenset()`, added
  `design_status(item_id)` tristate accessor.
- `scripts/feasibility_pilot_stratum_a.py`: DNF path now emits
  `"PENDING_CLUSTER"` (not `"DROPPED"`); JSON field `n_dropped` renamed
  `n_pending_cluster`; table section header updated.
- `artifacts/feasibility_pilot/feasibility_pilot_stratum_a.json` +
  `artifacts/feasibility_pilot/admitted_catalog.txt`: reclassified
  sts13_0, sts13_1, sts15_0, ag24, pg23, pg24 from DROPPED →
  PENDING_CLUSTER with reason "deferred to cluster pilot (T-M7h)".
  Final admission (300 s budget, A100) owned by T-M7h — do not modify
  T-M7h from this worktree.

**Addendum closing checks:**

```
pytest tests/unit/datasets/test_stratum_a_corpus.py -m unit -q
18 passed in 0.25s

pytest tests/unit/datasets/test_known_design_catalog.py -m "not slow" -q
53 passed, 1 deselected in 0.39s

pytest tests/unit/ -m "not slow" -q
998 passed, 5 skipped, 13 deselected, 1 warning in 35.81s

ruff check src/ tests/  → 3 errors (all pre-existing baseline; 0 new)
mypy src/isalhg/        → 21 errors (all pre-existing baseline; 0 new)
```
