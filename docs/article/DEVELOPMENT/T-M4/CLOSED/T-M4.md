# T-M4 — Planted-family datasets + metric-space scoring primitives
**Declared:** 2026-07-08 12:20 CEST · **retargeted** 2026-07-08 13:40 CEST
**Status:** DONE
**Depends on:** T-M1a
**Context to read first:**
- `docs/article/DATA.md` §2 — the non-iso planted-family constraint (the iso-copy trap)
- `docs/article/CODE_DESIGN.md` §7 (datasets), §3 tree (metrics)
- `docs/article/empirical/applications.md` — what the metrics score
- `docs/article/empirical/correlation.md` §Information content — the bits estimator
- `src/isalhg/datasets/synthetic/exhaustive_small.py` — dataset ABC + registry pattern (fix its module-level iso import to lazy)
- `.claude/rules/coding_rules.md` — always
**Description:** `datasets/synthetic/planted_families.py` (non-isomorphic,
seed-stable within-family members; family = label) and
`metric_space/metrics/{association,information,embedding}` (Spearman/MI,
fixed-width-code bits, classical-MDS solve + stress + PSD check).
**Acceptance:** planted corpus verified non-isomorphic within family (dedup
check) with known labels; each metric primitive unit-tested against a
hand-computed value.
**Out of scope here:** running MDS/clustering/kNN (T-M5b–e, experiments); standard
sklearn indices (called in experiments, not re-wrapped).

---

**Closed:** 2026-07-09 · ledger-worker agent (branch worktree-agent-aed0a24022b870136)

**Closing check output:**

```
pytest tests/unit/datasets/test_planted_families.py tests/unit/metric_space/ -x -q
146 passed in 4.38s

pytest tests/ -q --tb=short
745 passed, 8 skipped in 159.29s

ruff check src/ tests/ --output-format=concise
3 errors (pre-existing baseline; 0 new)

mypy src/isalhg/
20 errors in 6 files (baseline was 21; 1 pre-existing fixed by exhaustive_small.py lazy-import refactor)
```

**Files landed:**
- `src/isalhg/datasets/synthetic/planted_families.py` — `PlantedFamilyDataset` (new)
- `src/isalhg/metric_space/metrics/__init__.py` — package (new)
- `src/isalhg/metric_space/metrics/association.py` — Spearman/Pearson/MI (new)
- `src/isalhg/metric_space/metrics/information.py` — fixed-width-code bits + compression ratio (new)
- `src/isalhg/metric_space/metrics/embedding.py` — classical MDS + stress + PSD (new)
- `src/isalhg/datasets/synthetic/exhaustive_small.py` — lazy iso import fix
- `src/isalhg/datasets/registry.py` — one `_LAZY_MODULES` entry for `planted_families`
- `tests/unit/datasets/test_planted_families.py` — AC1–AC6 suite (new)
- `tests/unit/metric_space/test_metrics_association.py` — hand-computed assertions (new)
- `tests/unit/metric_space/test_metrics_information.py` — alphabet size + bits (new)
- `tests/unit/metric_space/test_metrics_embedding.py` — 1-D/2-D recovery + stress (new)

**Acceptance verified:**
- AC1 connectivity: all 146 planted-family items pass `is_connected()`.
- AC2 non-iso within family: fingerprint dedup confirmed by test (isalhg backend).
- AC3 iso_class = family index: confirmed.
- AC4 length: `len(ds) == n_families * members_per_family`.
- AC5 determinism: same `seed_value` → identical hypergraph sequences.
- AC6 registry: `get_dataset("planted_families", {})` and `{"members_per_family": 2}` succeed.
- Metric primitives: each function tested against a hand-computed value (alphabet size k=2→8, k=3→13, k=10→76; bits; compression ratio; 1-D/2-D MDS recovery; Kruskal stress-1 = 0 on exact embedding; Spearman/Pearson on monotone vectors; MI = 0 on independent, MI > 0 on correlated).
- D-CONN1: `is_connected()` enforced on seed motif generation and every perturbation candidate.
