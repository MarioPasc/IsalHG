# T-M4' — HIC atlas loader (real-anchor + gates T-DQ3')
**Declared:** 2026-07-08 13:40 CEST
**Status:** DONE
**Depends on:** — (independent dataset loader)
**Context to read first:**
- `docs/article/DATA.md` §3 — the real-anchor role + scaling caveat
- `src/isalhg/datasets/hic_atlas.py` — the current stub (all methods `NotImplementedError`)
- `src/isalhg/datasets/synthetic/exhaustive_small.py` — the `HypergraphDataset` ABC + registry pattern
- `.claude/rules/coding_rules.md` — always
**Description:** Implement the `hic_atlas` loader (`github.com/iMoonLab/HIC`,
Apache-2.0) yielding whole-hypergraph instances with class labels (e.g.
IMDB→genre). Unblocks (a) T-DQ3' (`w*` timing on a real instance) and (b) the
**HGED-free** applications (MDS/clustering/kNN) on larger real hypergraphs.
**Acceptance:** loads ≥1 HIC dataset as a `HypergraphDataset` with instances +
labels; per-instance size stats (n, m, arity) reported; unit + integration test.
**Out of scope here:** the application pipeline (T-M5b–e); the `w*` timing (T-DQ3').

---

## Closing note — 2026-07-09

**Implemented** `src/isalhg/datasets/hic_atlas.py` and updated
`src/isalhg/datasets/registry.py` (one new `_LAZY_MODULES` entry `"hic_atlas"`,
last in the dict).

**New public surface:**
- `HICAtlasDataset(root, hic_name)` — implements `HypergraphDataset` ABC; eager
  loading; all 12 KNOWN_NAMES supported via `_HIC_FILE_MAP`.
- `ClassRetentionStats` — frozen dataclass; per-class LCC retention fractions.
- `_parse_hic_file(path)` — parses HIC `.txt` format into `_RawRecord` list.
- `_largest_connected_component(H)` — BFS over `SparseHypergraph.primal_graph()`;
  returns the sub-hypergraph induced on the largest component.

**D-CONN1 compliance:** every yielded `DatasetItem.hypergraph` is connected
(LCC restriction applied to all 12 datasets). Per-class vertex/edge retention
fractions logged at INFO and accessible via `dataset.retention_report`. A
WARNING is emitted if any class has vertex_fraction < 1.0 (label-correlated
fragmentation flag for reviewers).

**File format** (observed on disk): one `.txt` file per dataset; first line =
total count; each block = `n n_edges class_label` / vertex-labels line / n_edges
hyperedge lines. File paths: `RHG/RHG_*.txt`, `IMDB/IMDB_*.txt`,
`STEAM/stream_player.txt` (note: "stream" not "steam"), `TWITTER/twitter_friend.txt`.

**Label vocabulary:** HIC vertex labels are integers (all 0 across all 12
datasets on disk → `LabelVocabulary.trivial()` used). The general case (non-zero
labels) is handled: unique integers are sorted numerically and mapped to vocabulary
positions.

**Acceptance verification:**

```
pytest tests/unit/datasets/test_hic_atlas.py -q
# 32 passed in 0.09s

pytest tests/integration/test_hic_atlas_integration.py -v
# 32 passed in 7.77s (all 12 datasets load; all instances connected)

pytest tests/ -q
# 756 passed, 8 skipped in 165.95s

ruff check src/ tests/
# Found 3 errors  (pre-existing baseline; none in new files)

mypy src/isalhg/
# Found 20 errors in 6 files  (pre-existing baseline 21; 0 new errors in my files)

mypy src/isalhg/datasets/hic_atlas.py src/isalhg/datasets/registry.py
# Success: no issues found in 2 source files
```

**Decisions recorded:**
- D1: Eager loading (parse once at construction). Required for correct `__len__`.
- D2: `_HIC_FILE_MAP["Steam-Player"] = "STEAM/stream_player.txt"` — observed on
  disk as "stream" not "steam"; a discrepancy from the dataset name but matching
  the actual file.
- D3: LCC extraction uses `SparseHypergraph.primal_graph()` — no new imports.
- D4: No edge labels in HIC format; `n_edge_labels=1` throughout.
- D5: `retention_report` is a property on `HICAtlasDataset`, not in the frozen
  `DatasetMetadata` schema (which would require modifying `schemas.py`).
- D6: Registry key `"hic_atlas"` (one entry); factory takes `params["root"]` and
  `params["hic_name"]`.

**No doc edits needed** (DATA.md §3 is already current; retention-reporting
requirement satisfied in code and logs).
