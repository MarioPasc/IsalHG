# T-OPTb — S2H interpreter in C++ (decode parity with the native encoder)
**Declared:** 2026-07-19 11:37 CEST
**Status:** OPEN
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
