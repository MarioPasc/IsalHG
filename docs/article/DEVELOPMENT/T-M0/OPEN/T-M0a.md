# T-M0a — conftest `gq_2_2_doily` is not a valid GQ(2,2)
**Declared:** 2026-07-08 13:13 CEST (handoff from T-M0)
**Status:** OPEN
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
