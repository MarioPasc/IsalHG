# T-M0c — the "STS(13)" fixtures are not Steiner triple systems
**Declared:** 2026-07-09 12:12 CEST (handoff from T-M0a)
**Status:** OPEN
**Depends on:** T-M0a (introduced the shared builder these fixtures now call)
**Why out of scope:** T-M0a's boundary is the GQ(2,2) fixture. This is the same
class of defect on a different design, found because T-M0a's new axiom test
asserted the Steiner property and it failed.
**Context to read first:**
- `src/isalhg/datasets/synthetic/designs.py::cyclic_sts_13` — the shared builder;
  its docstring already records the misnomer
- `tests/unit/datasets/test_designs.py::test_cyclic_13_is_not_a_steiner_triple_system_known_limitation`
  — pins the 39-of-78 pair coverage
- `tests/conftest.py::sts_13_pair` · `src/isalhg/datasets/synthetic/exhaustive_small.py::{_sts_13_pair_a,_sts_13_pair_b}`
  — the callers, whose item ids `sts_13_cyclic_014` / `sts_13_cyclic_016` carry the name
- `tests/unit/core/test_greedy_min_complete.py::test_complete_differs_from_greedy_on_sts13`
  and `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/theorem_a_completeness.tex`
  Remark `rem:coherence-recursive` + §Empirical — both call the object "STS(13)"
- `docs/article/DEVELOPMENT/T-M0/OPEN/T-M0a.md` — the sibling defect
- `.claude/rules/coding_rules.md` — always
**Description:** A single cyclic starter block on `Z/13Z` generates one orbit of
13 blocks covering 39 of the 78 point-pairs. STS(13) requires 26 blocks from two
starters (e.g. `{0,1,4}` with `{0,2,7}`). The three starters in use (`(0,1,3)` in
the benches and the proof, `(0,1,4)` / `(0,1,6)` in the fixtures) all produce
partial triple systems, and the Heinlein 2023 "exactly two iso-classes"
citation does not certify them. The mathematics that rests on these objects is
unaffected — they are 3-uniform, 3-regular and vertex-transitive under rotation,
which is all any caller uses, and the `(0,1,4)`/`(0,1,6)` pair really is
non-isomorphic — so this is a naming and citation defect, not a wrong result.
**Acceptance:** decide with the PI whether to (a) rename the fixtures and item
ids to `cyclic_triple_13_*` and drop the Heinlein citation, or (b) promote them
to genuine STS(13)s by adding the second starter orbit — which changes `n_edges`
13→26, every archived `w*` on them, and the `test_complete_differs_from_greedy_on_sts13`
pin. Whichever is chosen, `tests/unit/datasets/test_designs.py` asserts the
Steiner property iff the object claims it, and the proof's Remark + §Empirical
use the object's true name.
**Out of scope here:** the GQ(2,2) fixture (T-M0a, closed); T-TAd's default flip.
