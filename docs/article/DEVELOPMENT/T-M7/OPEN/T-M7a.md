# T-M7a — Known-design seed catalog + Stratum A labeled corpus
**Declared:** 2026-07-22 11:56 CEST
**Status:** OPEN
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
