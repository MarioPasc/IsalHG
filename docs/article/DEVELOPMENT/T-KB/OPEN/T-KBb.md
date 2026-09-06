# T-KBb — C++ port of stabiliser-orbit pruning

**Status:** OPEN · declared 2026-09-06 21:11 CEST by the Isal-refinement
orchestrator.

## What

The Python tie-complete encoder gains an `orbit_oracle` hook in wave
`2026-09-06-isal-kb-w1` (`core/hypergraph_to_string.py`,
`iso_backends/orbit_oracle.py::PynautyOrbitOracle`), value-preserving by
Proposition C.7 of `theorem_c_ordered_walk.tex`. The C++ engine
(`core/_native/src/h2s.cpp::encode_from`, the `collect_tied_v_candidates` /
`enumerate_label_perms_cb` branch) still explores every tied branch. Port
the hook: a callback from the C++ tie-branch to Python (nanobind) that
returns orbit representatives, or a native automorphism computation.

## Acceptance

- Frozen `w*_c` pins (`tests/unit/core/test_wstar_c_frozen.py`, fast + slow)
  bit-exact with the C++ hook on; differential against the unhooked engine on
  ≥ 500 random instances; the RQ7 envelope re-measured with the `|Aut|` axis
  (D-ART4 (3) RQ7) showing the frontier moved from `|Aut|` to `m`.

## Context

`docs/engineering/CPP_OPTIMIZATION_LOG.md` Rounds 9–11 (what is already
pruned and the two open levers); the Python hook's contract in
`ISAL_VARIANT_DESIGN.md` §6 and the wave log
`.claude/notes/2026-09-06-isal-kb-w1/orbit-prune.md`.
