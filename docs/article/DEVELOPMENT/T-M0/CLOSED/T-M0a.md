# T-M0a — conftest `gq_2_2_doily` is not a valid GQ(2,2)
**Declared:** 2026-07-08 13:13 CEST (handoff from T-M0)
**Status:** DONE
**Depends on:** —
**Context to read first:**
- `tests/conftest.py` — the `gq_2_2_doily` fixture (hardcoded 15-line edge list)
- `tests/property/test_backend_equivalence.py::_doily` — the CORRECT construction (points = 2-subsets of {1..6}, lines = perfect matchings of {1..6})
- `docs/article/theoretical/stability.md` §3 — lists GQ(2,2) among the vertex-transitive designs; the fixture must actually be vertex-transitive for that claim to hold
- `.claude/rules/coding_rules.md` — always
**Description:** The `gq_2_2_doily` fixture's hardcoded edge list is not a valid
generalised quadrangle: lines `{5,10,13}` and `{10,13,14}` share the pair
`{10,13}` (two lines meeting in two points violate the partial-linear-space
axiom), and the primal graph is not 6-regular (vertex 13 has degree 5), so it is
not vertex-transitive and not the doily. Replace the edge list with the
matching-based construction already in `test_backend_equivalence.py::_doily`
(or share that builder). Found during T-M0: the fixture's asymmetry is why the
nbrdeg seeder drops 10→7 seeds on it (a valid hypergraph, wrong *design*).
**Acceptance:** fixture is 3-uniform, 15 points / 15 lines, primal graph
6-regular (srg(15,6,1,3)); `max_neighbor_degree_nodes` returns all 15 (vertex-
transitive); any golden/partition test using the fixture updated + green.
**Out of scope here:** T-M0's promotion (it flags the fixture with `*` and does
not depend on it being the true doily).
**Update (2026-07-09 11:25 CEST) — priority raised, this now contaminates a
proof claim.** T-TAa reported `w*_greedy ≠ w*_c` on "GQ(2,2)" alongside STS(13),
and `theorem_a_completeness.tex` Remark 6.1 cites that pair as evidence that
vertex-transitivity does **not** buy *recursive* tie-coherence. But this fixture
is not vertex-transitive (that is exactly the defect above), so it is not evidence
for that claim: **STS(13) is its only valid support.** The same fixture supplies
T-TAa's headline "worst observed blow-up on a vertex-transitive design = 1.09 s".
Fix the fixture, then re-measure both the `w*_greedy` vs `w*_c` comparison and the
wall-clock on the true doily, and correct the proof's §Empirical — **before the PI
reviews the proof**.

**Closing (2026-07-09 12:12 CEST):**

- *The Update's contamination premise was tested and is **false**.* T-TAa did not
  use this fixture. Its GQ(2,2) row came from `scripts/bench_tie_complete.py::_doily`,
  which already built the doily from perfect matchings. Re-measured both
  constructions side by side (C++ backend, `greedy_min_nbrdeg` vs
  `greedy_min_complete`, i7-13700KF):

  | construction | greedy | complete | ratio | `w*_g == w*_c` |
  |---|---|---|---|---|
  | broken fixture | 123.4 ms | 254.8 ms | 2.1× | **True** |
  | true doily | 57.4 ms | 1044.7 ms | 18.2× | **False** |
  | T-TAa's published row | 61.25 ms | 1092.9 ms | 17.8× | False |

  T-TAa's row reproduces on the true doily and on nothing else — the broken
  fixture even inverts the `w*_g == w*_c` verdict. Consequently
  `theorem_a_completeness.tex` needs **no correction**: Remark `rem:coherence-recursive`
  keeps both STS(13) *and* GQ(2,2) as support, and §Empirical's `1.09 s` stands.
  The `.tex` was left untouched (PI decision, this session). Post-fix rerun of
  `bench_tie_complete.py`: doily 56.00 ms / 1095.32 ms / 19.6× / False.

- *Defects confirmed before fixing* (`n=15`, `m=15`, 3-uniform in both cases):
  the old edge list covered **44** distinct point-pairs, not 45, duplicating
  `{10, 13}` across lines `{5,10,13}` and `{10,13,14}`; its primal graph had
  degrees `13×6, 2×5`; `max_neighbor_degree_nodes` returned **7** seeds and
  `max_xi_nodes` **10**. The true doily: 45 pairs, no duplicate, 6-regular,
  **15/15** seeds under both cascades.

- *Deliverables.* New `src/isalhg/datasets/synthetic/designs.py` — the single,
  side-effect-free source of truth for Fano / STS(9) / cyclic-13 / GQ(2,2). The
  doily is now *constructed* as Sylvester's duad–syntheme geometry of `S_6`
  (points = 2-subsets of `{1..6}`, lines = perfect matchings), never transcribed.
  Seven call sites collapsed onto it: `tests/conftest.py`,
  `datasets/synthetic/{symmetric_designs,exhaustive_small}.py`,
  `scripts/bench_{seed_selection,tie_complete}.py`,
  `tests/property/test_{backend_equivalence,cpp_differential}.py`. Four of those
  carried the invalid edge list; three carried a correct but duplicated copy.
  Citations corrected (the Payne & Thas W(2) attribution was on an object that is
  not a GQ).

- *New tests.* `tests/unit/datasets/test_designs.py` (14 tests) asserts the
  *defining incidence axioms* rather than an edge list: partial-linear-space
  (two lines meet in ≤1 point), point graph srg(15,6,1,3), the GQ(2,2) axiom
  (for `p ∉ L`, exactly one point of `L` is collinear with `p`), and both seed
  cascades returning all 15. Plus `test_complete_differs_from_greedy_on_doily`
  (slow), which moves Remark 6.1's GQ(2,2) support out of a bench script and into
  the regression suite, alongside the existing STS(13) pin.

- ***Correction to T-M0's own evidence.*** T-M0 reported the nbrdeg cascade
  dropping `10 → 7` seeds on "GQ(2,2)". That drop was the broken fixture's
  asymmetry, not a property of the seed rule. On the true doily both cascades
  return all 15, and `bench_seed_selection.py` now shows **parity on every
  fixture in it** (including `asym_er12`, where both return 1 seed). The T-M0
  promotion still stands — both rules are iso-invariant, which is what makes `w*`
  well-defined — but its "wall-clock drops" acceptance has no supporting instance
  in that bench. A seed-count win needs an input whose `ξ`-tuples tie where the
  neighbour-degree lists do not; none is included. Recorded in the bench
  docstring.

- *Out-of-scope discovery, parked as* [`T-M0c`](../OPEN/T-M0c.md): the "STS(13)"
  fixtures are not Steiner triple systems either (one cyclic starter → 13 blocks
  covering 39 of 78 pairs; STS(13) needs 26 blocks from two starters). Naming and
  citation defect only — the objects are 3-uniform, 3-regular, vertex-transitive
  and the pair is genuinely non-isomorphic, which is all any caller uses. Pinned
  by `test_cyclic_13_is_not_a_steiner_triple_system_known_limitation`.

- *Closing checks.*
  `pytest tests/unit tests/property tests/integration -m "not slow" --hypothesis-seed=0`
  → **666 passed, 8 skipped, 7 deselected, 0 failed**.
  `pytest -m slow --hypothesis-seed=0` → **7 passed, 1 skipped** (the +1 over
  T-TAa's 6 is `test_complete_differs_from_greedy_on_doily`; the doily reorder-
  invariance gate now runs on the true design).
  ruff **3 == baseline**; mypy **21 == baseline**.
  `python scripts/bench_seed_selection.py` → `gq22  15  15  |xi|=15  |nbr|=15`.
