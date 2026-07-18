# T-M0c — the "STS(13)" fixtures are not Steiner triple systems
**Declared:** 2026-07-09 12:12 CEST (handoff from T-M0a)
**Status:** DONE (2026-07-18, orchestrator — PI answer: option (b), extended to a full STS catalog)
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

---
**Closing note (orchestrator, 2026-07-18).** PI answer: **(b) promote — seek
true STS(13), plus STS(15), 3, 7, 9** from
`https://pottonen.kapsi.fi/sts19/sts{n}.txt`. Executed as (b) + (a) combined:
true Steiner systems added from the authoritative catalog; the partial cyclic
objects kept under truthful names (they remain the cheap fast-test hard pair
and the anchor of published measurements).

What landed:
- **Vendored catalog** `src/isalhg/datasets/data/sts/sts{3,7,9,13,15}.txt`
  (verbatim; provenance + sha256s in the sibling `README.md`) + loader
  `datasets/synthetic/sts_catalog.py` (`steiner_triple_system(n, index)`,
  `sts_count`, registered dataset `"sts_catalog"`, 85 items with
  `iso_class = item_id`).
- **Verification at vendoring** (pynauty over Levi, probe 2026-07-18): every
  listed system satisfies the Steiner axioms; iso-classes per order exactly
  **1/1/1/2/80** (matches the classification); catalog STS(7) ≅ in-repo Fano,
  catalog STS(9) ≅ in-repo `sts_9`.
- **Renames (truthful naming, option (a) side):** builder `cyclic_sts_13` →
  `cyclic_triple_orbit_13`; item ids `sts_13_cyclic_01{4,6}` /
  `sts13_cyclic_01{4,6}` → `cyclic_triple_13_01{4,6}`; conftest fixture
  `sts_13_pair` → `cyclic_triple_13_pair`; test names, variables, bench
  labels, and script docstrings de-misnomered across 13 files. The Heinlein
  citation's certifying role is replaced by the Kaski–Östergård catalog.
- **New pins:** `w*_c` (k=3, `algorithm="canonical"`) on the two true
  STS(13)s, `@pytest.mark.slow` (**~44 s each**, measured): lengths 472/472,
  sha256 `4e5e682d…` / `bd872631…` — **distinct**, so `w*_c` separates the
  two STS(13) isomorphism classes. The historical (0,1,3) pin is untouched
  (same object, same value, truthful test name) — **no D-TA2 event**.
- **New fixture** `sts_13_true_pair` (conftest) for slow tests.
- `w*_c` wall-clock on STS(15)#1 exceeds 240 s (probe timeout) — STS(15)
  stays catalog-only; no canonicalizing tests. Relevant to the T-DQ3'-style
  scale gates.

Acceptance clause-by-clause: `test_designs.py` asserts the Steiner property
iff the object claims it (catalog tests assert it; the renamed partial-orbit
tests assert 39/78 coverage) ✔; fixtures/ids renamed ✔; true STS(13)s with
regenerated pins present ✔. **Pending (PI-owned):** the proof
`theorem_a_completeness.tex` names the (0,1,3) partial object
"$\mathrm{STS}(13)$" at 6 spots (lines ≈634–5, 718, 723–4, 745, 766) — the
measurements there are valid for that object; only the name needs the
`C_{13}(0,1,3)` correction. Closing checks: targeted 116 passed; slow pins
2 passed in 89 s; full fast suite + ruff + mypy at baseline (see commit).
