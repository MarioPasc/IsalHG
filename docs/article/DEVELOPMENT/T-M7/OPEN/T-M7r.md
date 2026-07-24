# T-M7r — Fix per-arity sub-corpus classification in sweep_multi_seed.py
**Declared:** 2026-07-24 13:25 CEST
**Status:** OPEN
**Depends on:** T-M7d
**Why out of scope:** Discovered during T-M7d S=3 smoke test on the 17-family Stratum A corpus; fixing `_arity_of_H` would go beyond the four narrowly-scoped corrections T-M7d was authorized to make.
**Context to read first:**
- `experiments/article/analysis/sweep_multi_seed.py::_arity_of_H` (line ~880) — the buggy classifier
- `experiments/article/analysis/sweep_multi_seed.py` lines ~951–976 — per-arity loop and pooling guard
- `src/isalhg/datasets/synthetic/known_design_catalog.py::ARITY_BY_ID` (or `COARSE_CLASS_BY_ID`) — family-level arity ground truth
- `docs/article/DEVELOPMENT/T-M7/CLOSED/T-M7d.md` — closing note documents observed symptom
- `.claude/rules/coding_rules.md` — always

**Description:** `_arity_of_H(H)` returns `min({len(members) for each edge})`, which misclassifies hypergraphs from k=4/5 families whose Qin-edit perturbations include a lower-arity edge (the per-family arity cap T-M7o introduced prevents ADDING higher-arity edges, but lower-arity edges from insertions/splits remain possible). Consequence: the k=3 sub-corpus is polluted with k=4-family items whose min-edge-arity is 3, and the pooling guard fires for all per-arity sub-corpora (`arity groups [3,4]`, `[4,5]`, etc.) → per-arity A2/A3 results are `None`. Fix: classify hypergraphs by family label (from `label_strings[i]` via `known_design_catalog` ARITY_BY_ID or similar) rather than by empirical min-edge-arity.

**Acceptance:** In the S=27 Picasso run (or a local S=3 smoke), the pooling guard no longer fires for per-arity sub-corpora; `a2_per_arity[3]` / `a2_per_arity[4]` / `a2_per_arity[5]` each receive non-None A2/A3 results; the arity-1 phantom group disappears from the warnings.

**Out of scope here:** changing PlantedFamilyDataset's perturbation strategy (T-M7o scope); editing `known_design_catalog.py` (frozen corpus); changing any Stratum B logic; changing the pooled (mixed-k) A2/A3 path (lines 942–943 — retain for backward compatibility per the inline comment).
