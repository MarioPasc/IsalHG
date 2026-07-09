# T-M1b — `IsalHGLevenshtein` (`d_I`) + `HypergraphWLDistance`
**Declared:** 2026-07-08 13:40 CEST (split from T-M1)
**Status:** DONE
**Depends on:** T-M1a
**Context to read first:**
- `docs/article/CODE_DESIGN.md` §3 (table), §3.1 (rapidfuzz decision)
- `docs/article/COMPETITORS.md` §2 — the WL baseline
- `src/isalhg/core/canonical.py` — `w*` entry point for `d_I`
- `src/isalhg/core/hypergraph_wl.py` — reused by `HypergraphWLDistance`
- `.claude/rules/coding_rules.md` — always
**Description:** Implement the first two `HypergraphDistance` subclasses:
`IsalHGLevenshtein` (`d_I` = raw Levenshtein on `w*`, rapidfuzz-guarded; raw is
primary, normalized/token-aware are ablation kwargs) and `HypergraphWLDistance`
(wraps `core.hypergraph_wl`, L1/χ² on the colour-count vector). Register both.
**Acceptance:** `d_I` = 0 on isomorphic design-fixture pairs, > 0 otherwise;
`d_I.matrix()` and `WL.matrix()` run on a 10-item corpus; suite green.
**Out of scope here:** HGED (T-M2), the other competitors (T-M3a–d).
**Closing (2026-07-08 17:11 CEST):**
- *`IsalHGLevenshtein` (`d_I`)* — `metric_space/distances/isalhg_levenshtein.py`.
  `d_I = d_Lev(w*(H), w*(H'))` over the **token sequence** of `w*` (recovered via
  `instructions.parse`), not the serialised ASCII: `instructions.py`'s own
  docstring mandates token-tuple comparison (the `P[10]` vs `P[1]` multi-digit
  pitfall), and the stability theorem reasons per token. rapidfuzz (C++ Lev.)
  guarded inside method bodies; tokens encoded to private-use code points under
  one shared vocabulary (Levenshtein is relabelling-invariant) so `pairwise` and
  `matrix` (via `rapidfuzz.process.cdist`) agree. Raw distance primary;
  `normalize=True` is the length-normalized ablation kwarg. Registered
  `isalhg_levenshtein`.
- *`HypergraphWLDistance`* — `metric_space/representations/wl.py`. Wraps
  `core.hypergraph_wl.wl_hash`; fingerprint = colour histogram; distance = `l1`
  (default) or symmetric `chi2`. Registered `hypergraph_wl_l1` / `hypergraph_wl_chi2`.
- *Decisions taken (flagged, spec-grounded, reversible):*
  (D1) **k held consistent per comparison** (Critical Invariant #7): `matrix`
  uses corpus-max `required_k`, `pairwise` the pair-max, unless a fixed `k` is
  passed — else two `w*` at different `k` are not comparable and iso pairs could
  read `d_I>0`. (D2) **WL histograms via one disjoint-union WL run**, not naive
  per-graph: `wl_hash` early-stops per graph, so raw colours are only
  cross-comparable on a shared refinement schedule; the union makes every
  component read out at the same round, keeping the baseline *fair* (COMPETITORS
  §3 forbids strawmanning). Iso-invariance holds either way; the simpler
  per-graph wrap is a trivial revert if the PI prefers. (D3) **token-aware
  substitution costs deferred** — rapidfuzz's uniform weights cannot express a
  per-token-pair cost matrix (`V`↔`C` cheaper than `V`↔`P`); it needs a general
  DP and belongs in the T-M5a ablation table, not here. Only `normalize` shipped.
- *`_LAZY_MODULES` populated* in `metric_space/registry.py` with the three names →
  their modules; each module self-registers at import (guarded deps stay inside
  method bodies, so `available_distances()` imports them without needing
  rapidfuzz/numpy present).
- *Acceptance met:* `d_I=0` on `iso_pair_small` + `permute(fano)` + self; `d_I>0`
  on `non_iso_pair_small` and the **two non-isomorphic STS(13)** (the hard
  same-parameter case); `d_I.matrix()` and `WL.matrix()` run on a 10-item corpus
  (symmetric, zero-diagonal, iso members at 0).
- *Closing checks* (`pytest tests/unit tests/property tests/integration
  -m "not slow" --hypothesis-seed=0`): **470 passed, 8 skipped, 0 failed**
  (+21 vs T-M1a's 449 = 11 `d_I` + 10 WL). ruff **3 == baseline**, mypy
  **21 == baseline** — zero new violations; the seven new `metric_space` modules
  are lint/type-clean. No `core/` change → property tests untouched, no C++ rebuild.
- *Follow-ups (next tasks' scope, no handoff):* T-M2 adds `ExactHGED` honouring
  T-M1a's isolated-only `delete_vertex`; T-M3a's `NautyLeviEditDistance` and the
  other competitors register alongside these two.
