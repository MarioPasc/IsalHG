# T-M2c — `d_I` undefined on disconnected hypergraphs vs HGED paths that pass through them (domain gap)
**Declared:** 2026-07-08 23:25 CEST (handoff from T-M2b)
**Status:** OPEN
**Depends on:** — (gates T-M5a E1/E3 and the T-TB §2.1 decomposition)
**Why out of scope:** found while assessing HGED completeness for Theorem B at
T-M2b close; fixing it touches `core/` canonicalization and corpus generators,
not the HGED metric itself.
**Context to read first:**
- `src/isalhg/core/canonical.py::_python_canonical_string` (and the C++ twin `_native/src/canonical.cpp`) — raise `DisconnectedHypergraphError` on any disconnected input (decision B11); `SparseHypergraph.is_connected` counts an isolated vertex as disconnection
- `src/isalhg/core/sparse_hypergraph.py::{random_edit, edit_path, insert_vertex}` — `insert_vertex` is always applicable, so ladder snapshots can be disconnected; `delete_hyperedge`/`remove_incidence` can disconnect too
- `src/isalhg/datasets/synthetic/_random_hg.py::random_hypergraph` — no connectivity guarantee, so `correlation_corpus` items can be disconnected
- `docs/article/theoretical/stability.md` §2.1 — the triangle-inequality decomposition over an optimal HGED path needs `d_I` defined at every intermediate state
- `docs/article/empirical/correlation.md` §Experiments (E1/E3) — the runs that would raise today
- `.claude/rules/coding_rules.md` — always
**Description:** `d_I = d_Lev(w*, w*)` is only defined on connected hypergraphs
(decision B11). This umbrella entry holds **three distinct problems** — do not
conflate them; each has its own fix surface (PI directive 2026-07-08):

- **(P1) Transient disconnection inside the theorem's proof — theory only.**
  Optimal Qin HGED edit paths pass through disconnected *intermediate* states
  (every vertex insertion starts isolated; incidence removals can disconnect),
  so Theorem B's §2.1 decomposition `d_I(H,H') ≤ Σ d_I(H_{i-1}, H_i)` has
  undefined terms even when both *endpoints* are connected. This does NOT by
  itself require the framework to accept disconnected inputs — it requires the
  *proof* to route around them: the macro-op regrouping lemma (whole-edge
  insert/delete, incidence move, isolated-vertex insert/delete, label
  substitution; reduce-before-extend interleaving keeps intermediates free of
  empty shells and within `arity ≤ k`) removes *some* disconnection, but "an
  optimal path through connected states exists" is likely false in general, so
  P1 ultimately needs the P3 mechanism or a weakened/conditional statement.
  Consumed by T-TB (checklist item T-B0 in `stability.md` §6).
- **(P2) Native disconnected inputs to the framework — engineering, the thing
  that crashes today.** `random_hypergraph` gives no connectivity guarantee
  (corpus items for E1 can be disconnected) and ladder snapshots can be
  disconnected (`insert_vertex` always applicable), so T-M5a's E1/E3 raise
  `DisconnectedHypergraphError`. Two fixes: (ii-a) *restrict generators*
  (connected-only corpus filter; connectivity-preserving random edits) — cheap,
  needs no theory, but narrows the empirical domain and leaves P1 untouched; or
  (ii-b) *native support* via the P3 mechanism. Which one is the PI's call
  after P3 is answered.
- **(P3) The theoretical crux for any native support: does concatenation of
  IsalHG instruction strings decode to the right hypergraph? Preliminary
  answer: NO — naive concatenation is provably the wrong gluing.** `Σ_HG`
  cannot express disconnection at all: every `V_{i,j}` has `i ≥ 1` (new nodes
  always arrive inside an edge shared with an existing node), `C_i` spans
  existing nodes only, and no token creates an isolated node — so the
  S2H-reachable set is exactly the *connected* hypergraphs (this is why B11
  exists). Appending component B's string after component A's therefore decodes
  as *growing component A further*: B's `V`/`C` instructions bind to A's nodes
  through the shared CDLL/pointer state, yielding a connected hypergraph, not
  the disjoint union. Per-component H2S is easy; a correct glue must be one of:
  (iii-a) **tuple fingerprint** — `w*_∪(H) :=` the lexicographically sorted
  tuple of per-component canonical strings, with `d_Lev` computed on the
  separator-joined tuple (separator ∉ `Σ_HG`); iso-invariant by construction
  and cheap, but the result is *not a decodable `Σ_HG` word*, so the
  closed-alphabet/round-trip invariants (#2/#3) hold only per component and the
  paper must present the disconnected fingerprint as a tuple, not a string; or
  (iii-b) **alphabet extension** — a fresh-component token (e.g. relaxing `V`
  to `i = 0`, or a dedicated start token) restoring decodability, but touching
  `instructions.py`, S2H, H2S, the C++ twin, and **re-opening Theorem A for the
  extended alphabet** (post-T-TA, completeness is proved for `w*_c` =
  `greedy_min_complete` on the *current* alphabet — any extension must re-prove
  or re-verify it, and every metric-space claim now attaches to `w*_c`).
**Acceptance:** (a) P3 answered in writing — a short proof/argument settling
whether and how gluing can be made correct, with the (iii-a)/(iii-b) decision
recorded by the PI; (b) P2 resolved per that decision — either
`canonical_string`/the fingerprint layer (both backends) accepts disconnected
inputs with an iso-invariance property test over disconnected pairs *of
`w*_c`*, or corpus/ladder generators guarantee connected outputs — and an
E1/E3 dry-run no longer raises; (c) P1's residual requirement handed to T-TB
explicitly (`stability.md` §2.1 / T-B0 updated with the chosen mechanism).
**Out of scope here:** the stability proof itself (T-TB); the HGED oracles
(unaffected — they are defined on disconnected inputs already).
