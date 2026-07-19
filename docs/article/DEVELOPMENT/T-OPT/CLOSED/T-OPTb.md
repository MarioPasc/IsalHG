# T-OPTb — S2H interpreter in C++ (decode parity with the native encoder)
**Declared:** 2026-07-19 11:37 CEST
**Status:** DONE
**Depends on:** T-OPTa (same `_native/` lane — shared build files and
bindings; strictly sequential, starts only after T-OPTa merges green)
**Delegation:** agent
**Why out of scope:** declared alongside T-OPTa on the user's direction
(2026-07-19); decode should match encode in implementation reach, and A4
decodes intermediate strings at corpus scale.
**Context to read first:**
- `src/isalhg/core/string_to_hypergraph.py` — the Python S2H interpreter;
  its semantics are the specification (closed alphabet: never rejects).
- `docs/article/H2S_S2H.md` — the self-contained S2H/H2S algorithm spec (the
  methods-section source; the port must not diverge from it).
- `src/isalhg/core/_native/` — encoder sources, bindings, build files; the
  port lands here beside H2S.
- `src/isalhg/core/backends.py` (or the encoder's backend dispatch in
  `core/canonical.py`) — the existing `backend="cpp"|"python"` pattern to
  mirror for S2H.
- `tests/property/test_s2h_roundtrip.py` — the round-trip property suite the
  port must keep green on both backends.
- `docs/article/DEVELOPMENT/T-OPT/OPEN/T-OPTa.md` — the lane-sharing
  predecessor (runtime-`k` buffers land there; the port builds on them).
- `.claude/rules/coding_rules.md` — always
**Description:** Port the S2H interpreter (CDLL + k-pointer VM executing
`Sigma_HG` tokens) to C++ inside `_native/`, exposed through the same
backend dispatch as H2S with the Python implementation as fallback. Uses
T-OPTa's runtime-`k` buffers so decode reach matches encode reach.
**Acceptance:**
1. Parity: C++ and Python S2H produce isomorphic (fingerprint-identical)
   hypergraphs on (a) the canonical strings of every design fixture,
   (b) Hypothesis-random strings over `Sigma_HG` (closed alphabet — every
   string decodes, no rejects), (c) the round-trip property
   `S2H(H2S(H)) ~ H` green on both backends.
2. Invariant 6 respected: `W` tokens execute as no-ops and are never
   stripped; pointer moves resolve via CDLL indices (invariant 1).
3. A reported decode throughput number (tokens/s, C++ vs Python) on one
   corpus-scale string.
4. Full suite + ruff + mypy at (or better than) the S2 baselines.
**Out of scope here:** any encoder change (T-OPTa owns `h2s.cpp`); A4's
path-decoding application harness (T-M5e); changing `Sigma_HG` semantics.

---

## Closing note — 2026-07-19

**Commit:** 2c463ba `feat(core): C++ S2H interpreter; backend dispatch for string_to_hypergraph (T-OPTb)`

**Files changed:**
- `src/isalhg/core/_native/include/isalhg/s2h.hpp` (new)
- `src/isalhg/core/_native/src/s2h.cpp` (new)
- `src/isalhg/core/_native/bindings.cpp` (string_to_hypergraph_raw binding)
- `src/isalhg/core/string_to_hypergraph.py` (_cpp_s2h + dispatch + typing)
- `src/isalhg/core/_core.pyi` (string_to_hypergraph_raw stub)
- `CMakeLists.txt` (s2h.cpp added to sources)
- `tests/unit/core/test_s2h_cpp.py` (new, 28 unit tests)
- `tests/property/test_s2h_roundtrip.py` (3 new property tests)

**Acceptance check:**

AC1a (parity on design fixtures): C++ and Python produce fingerprint-identical
hypergraphs on Fano, STS(9), cyclic_triple_orbit_13((0,1,4)),
cyclic_triple_orbit_13((0,1,6)), from every seed node. PASS (28 unit tests).

AC1b (closed-alphabet): all well-formed Sigma_HG* strings decode without
exception on C++ backend. PASS (parametrized test_closed_alphabet_no_raise).

AC1c (round-trip property): S2H(H2S(H)) ~ H on both backends (Hypothesis,
40 examples each); cross-backend fingerprint parity (30 examples). PASS.

AC2 (W no-op, invariant 6): strings differing only in W count decode to the
same hypergraph. PASS (TestWTokenNoop, 4 parametrized cases).

AC3 (decode throughput on Fano, 31 tokens/string, 1000 reps):
  C++: 1,055,136 tokens/s (0.029 ms/call)
  Python: 792,352 tokens/s (0.039 ms/call)
  Speedup: 1.3× (C++ is faster; assertion C++ >= 0.5× Python passes)

AC4/AC5 (backend dispatch + unknown raises): PASS.

Full suite: **986 passed / 8 skipped** (31 new tests vs S2 baseline).
Ruff: **3 errors** (at baseline; pre-existing ANN001, SIM108, E731).
Mypy: **21 errors in 7 files** (exactly at baseline; _S2H_BACKENDS typed as
`dict[str, Callable[..., SparseHypergraph]]` eliminates new errors).

---

## Orchestrator verification note — 2026-07-19 (S2 session)

Re-ran the worker's S2H suites in its env (33 passed) and added an
independent corpus-scale check the closing note lacked: on a random
connected hypergraph (n=30, m=60, arities 2–4, greedy-encoded,
|w| = 1692 tokens), C++ and Python decodes are structurally identical
(parity=True) at **5.78 vs 4.65 Mtok/s — 1.24×**. This corrects the
closing note's expectation that "the compute-only C++ phase benefits more
at larger hypergraphs": the speedup is flat from 31 to 1692 tokens because
`parse()` + `validate()` remain Python-side for both backends and scale
with |w|. Decode is not a bottleneck anywhere in the article pipeline
(~0.4 ms per corpus-scale string); the port's value is implementation
parity with the native encoder (runtime `k`, shared reach) and the 31 new
parity tests. Moving parse/validate into C++ is possible but has no
consumer — deliberately not filed as a task.

Post-merge main (rebuilt env): 971 passed / 8 skipped / 15 deselected;
frozen pins 6/6; ruff 3; mypy 21 in 7 files;
`scripts/verify_competitors.py` ALL PASS with numbers byte-identical to
the S2 baseline.
