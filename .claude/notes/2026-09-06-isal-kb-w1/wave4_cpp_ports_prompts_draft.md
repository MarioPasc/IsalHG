# Wave 4 draft — the two C++ ports the article rule requires

*Orchestrator draft, 2026-09-07. User rule: everything in the final article
runs on the C++ engine. Spawn after the quota window reopens (13:10):
two Opus xhigh agents in worktrees, base = the head of `feature/isal-kb-word`
at spawn time; disjoint ownership; same standing obligations, bootstrap
(`isalhg-cpporbit`, `isalhg-cppow` envs), verification commands, log
template and final-message format as the wave-3 prompt
(`.claude/notes/2026-09-07-isal-kb-w3/cpp-rank.md` §1 holds it verbatim).*

## A. `cpp-orbit` — the stabiliser-orbit oracle inside the C++ tie-complete search

**Mission.** `canonical_string(H, k=k, algorithm="canonical_orbit",
orbit_oracle=<PynautyOrbitOracle>, backend="cpp")` returns the frozen
`w*_c` bit for bit, with the C++ tie-branch (`h2s.cpp::encode_from`,
`collect_tied_v_candidates`, `enumerate_label_perms_cb`) branching over one
representative per orbit supplied by the oracle, and the seed loop over one
seed per `Aut(H)`-orbit.

**Design (fixed).** Callback, not native automorphisms: the bindings accept a
Python object implementing the `core/orbit_oracle.py::OrbitOracle` protocol;
the C++ variant (`AlgorithmVariant::GreedyMinCompleteOrbit`, next free id)
calls it at every residual tie with `(placed input ids in creation order,
tied edge ids)` and `(placed, edge, orderings)` under `nb::gil_scoped_acquire`;
the seed loop for this variant is single-threaded (the persistent thread pool
must not call into Python concurrently). Representatives returned by the
oracle are used verbatim (value-equivalent by Prop. C.7).

**Ownership.** `src/isalhg/core/_native/**` (except files `cpp-ow` owns),
`src/isalhg/core/canonical.py` (the cpp dispatch of `canonical_orbit` only),
`src/isalhg/iso_backends/orbit_oracle.py` (`backend` parameter on
`canonical_string_orbit` / `canonical_fingerprint_orbit`, default cpp),
`tests/unit/core/test_cpp_orbit.py`, `tests/integration/test_cpp_orbit_corpus.py`,
`docs/engineering/CPP_OPTIMIZATION_LOG.md` (one entry), its log.

**Definition of done.** (1) Frozen `w*_c` pins bit-exact through the C++
orbit path: Fano, STS(9), `C_13(0,1,3)`, n=4, GQ(2,2), and both STS(13)
(slow; the C++ engine makes them minutes, not hours — report the time).
(2) Differential vs the Python orbit engine on ≥ 500 guard-satisfying random
instances and 200 stars; vs C++ `w*_c` (unpruned) on ≥ 300 wd50k66 and 300
ndc_classes members the unpruned engine completes within 60 s. (3) Branch
collapse reproduced in C++ (q = 5..10 stars; frames and oracle calls).
(4) Censored tail: the 100 highest-|Aut| wd50k66 members censored by the
unpruned C++ engine at 60 s, and 100 ndc_classes members likewise — completion
fraction per |Aut| bucket, median seconds; this is the R2 number of the
article. (5) `engine_word(engine="orbit")` picks the C++ path and the Python
memory guard no longer applies to it. (6) Full suite, lint, mypy at baseline.

## B. `cpp-ow` — the ordered-walk emitter in C++

**Mission.** `ordered_walk(H, ranks, policy)` in C++ (`_native/src/ordered_walk.cpp`,
bindings `ordered_walk_tokens(...)`), bit-identical to the Python emitter
`core/algorithms/ordered_walk.py` for the three policies; the Python entry
points (`iso_backends/isal_ordered.py`, `metric_space/distances/isal_ordered.py`)
gain `backend` (default cpp when available). No change to the definition
(Def. 3.2 of `theorem_c_ordered_walk.tex`, the no-crossing move rule).

**Ownership.** `src/isalhg/core/_native/src/ordered_walk.cpp` (+ header,
the bindings' additions in a clearly delimited block of `bindings.cpp` —
coordinate the shared file with `cpp-orbit` through `main`: `cpp-orbit` owns
`bindings.cpp`; `cpp-ow` sends its binding block to `main` as a patch, or
`main` serialises the two), `src/isalhg/core/algorithms/ordered_walk.py`
(backend dispatch only), `src/isalhg/iso_backends/isal_ordered.py`,
`src/isalhg/metric_space/distances/isal_ordered.py` (backend), tests
`tests/unit/core/test_cpp_ordered_walk.py`, `tests/integration/test_cpp_ordered_walk_corpus.py`,
its log.

*Decomposition note:* `bindings.cpp` and the CMake list are shared between A
and B — the partition is not disjoint there. Either run B after A (safer:
one wave each) or give A the shared files and have B deliver its binding
block by message. Prefer sequential: A first (it carries the article's R2
number), then B.

**Definition of done.** (1) Golden `(len, sha256)` table of the Python
emitter reproduced for every fixture × policy. (2) Differential on all
3,988 wd50k66 + 1,381 ndc_classes members × 3 policies (both engines are
ms). (3) Round trip and invariance re-pinned through the C++ path.
(4) Timing table C++ vs Python (median µs). (5) Full suite, lint, mypy.

## After both

Re-run M3 (timing) rows for `wstar_orbit` and `isal_ow_*` in C++ on Picasso
(a third RQ1 experiment on the same units, arms `wstar_orbit`, `isal_ow_struct`,
`isal_ow_rank`, `isal_ow_rank0`), then build the RQ1 table from the three
experiments joined on (collection, base_id, edit_kind, edit_idx); the
locality rows of the Python arms are identical by bit-exactness and can be
reported from the first run, with the provenance stated.
