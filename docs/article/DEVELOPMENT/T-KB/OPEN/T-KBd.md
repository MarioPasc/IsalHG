# T-KBd — C++ port of the ordered-walk emitter

**Status:** OPEN · declared 2026-09-07 by the Isal-refinement orchestrator,
required by the author's rule that everything in the final article runs on
the C++ engine.

## What

`core/algorithms/ordered_walk.py` (the deterministic emitter of Definition
3.2 in `theorem_c_ordered_walk.tex`, three policies, no-crossing move rule)
ported to `core/_native/src/ordered_walk.cpp` with a binding, bit-identical
to the Python emitter; `iso_backends/isal_ordered.py` and
`metric_space/distances/isal_ordered.py` gain a `backend` parameter
defaulting to C++.

## Acceptance

- The golden `(len, sha256)` table of `tests/unit/core/test_ordered_walk.py`
  reproduced for every fixture × policy through the C++ path.
- Differential on all 3,988 `wd50k66` and 1,381 `ndc_classes` members × 3
  policies (both engines are milliseconds); round trip and invariance
  re-pinned through C++.
- Timing table C++ vs Python; the M3 rows of `isal_ow_*` re-measured in C++
  on Picasso (a third RQ1 experiment on the same seeded units).

## Context

Spawn prompt draft: `.claude/notes/2026-09-06-isal-kb-w1/wave4_cpp_ports_prompts_draft.md`
§B (note the shared `bindings.cpp` with T-KBb — run after it). The
ordered walk's role after the RQ1 preview is the "order only" ablation cell
with a named mechanism (breadth-first deferral pays excursions on
insertions), not the representation candidate; the port is still required
for its row to appear in a final table.
