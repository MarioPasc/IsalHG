# T-KBi — `ordered_walk.py` imports a private symbol across module ownership

**Status:** OPEN · declared 2026-09-08 13:02 CEST by the Isal-refinement
orchestrator, from the wave-1 record (the cpp-ow agent flagged it "harmless;
keep at merge"; it is not in the handoff's §6 defect table).

## What

`src/isalhg/core/algorithms/ordered_walk.py` imports `_movement_tokens` — a
private symbol — from `core/hypergraph_to_string.py`, the module the
orbit-pruning work owns. Both files are `core/` and stdlib-only, so no layering
rule is broken; the problem is coupling: the pointer-run rendering convention
(all `N` by pointer index, then all `P`) is now a shared contract expressed as
an underscore-prefixed function with no test asserting the two emitters agree
on it.

The move rule is load-bearing for the locality claim — `ISAL_VARIANT_DESIGN.md`
§1 records that the earlier "shorter direction" rule falsified Proposition C.5
and was replaced by the no-crossing rule. A refactor of
`hypergraph_to_string.py` that changed `_movement_tokens` would silently move
the ordered walk's measured locality.

## Proposed shape

Promote the rendering to a named, documented public helper (its own module or a
public function with a docstring stating the convention and why crossing the
root is forbidden), and pin it with a test that both emitters render the same
`(from, to)` displacement identically.

## Acceptance

No private cross-module import remains; one test covers both emitters against
the same displacement table; the golden `w°` pins are unchanged (the change is
a rename, not a semantic one).
