# T-TAa — C++ port of the tie-complete encoder (`tie_branch`)
**Declared:** 2026-07-08 23:39 CEST (handoff from T-TA)
**Status:** DONE — un-superseded 2026-07-09 (PI): the port lands on its own, the
default flip stays with T-TAd, which is now unblocked and reduced to the flip
**Depends on:** T-TA (its D-TA1 decision fixes the target: new C++ variant vs
new default)
**Context to read first:**
- `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/theorem_a_completeness.pdf` §6 (admissible pruning — Lemma 7.3) and Appendix (code↔proof map)
- `src/isalhg/core/hypergraph_to_string.py::{_iter_v_candidates,_tied_v_candidates,_encode_from}` — the Python reference semantics to mirror bit-for-bit
- `src/isalhg/core/algorithms/greedy_min_complete.py` — the variant to twin
- `src/isalhg/core/_native/src/canonical.cpp::canonical_string_compute` + `include/isalhg/canonical.hpp::AlgorithmVariant` — the variant enum to extend
- `tests/property/test_completeness.py`, `tests/unit/core/test_greedy_min_complete.py` — the invariance guard-rails (must stay green through the C++ path)
- `.claude/rules/coding_rules.md` — always
**Description:** `greedy_min_complete` is pure Python (Fano ≈ 3.5 s; unusable
for T-M5 corpora at scale). Port `tie_branch` into the C++ `_encode_from` twin
(branch over the residual V-tie set × label-respecting orderings, lex-min
completion), register variant id, and wire `greedy_min_complete` to the
single-FFI fast path. Optional (Lemma "admissible pruning"): refine the tie
set with any iso-invariant edge key (deeper η, canonical WL edge colours)
before branching — sound by the proof, and the main perf lever on
η-degenerate inputs.
**Acceptance:** C++ output ≡ Python reference on every fixture + the pinned
counterexample + a Hypothesis differential sweep; completeness property tests
green through the C++ path; wall-clock on {Fano, STS(9), STS(13), GQ(2,2)}
reported vs the greedy default; no change to any other variant's output.
**Out of scope here:** flipping the package default (D-TA1, PI); the proofs.
**Closing (2026-07-09 11:07 CEST):**
- *Deliverables:* `tie_branch` threaded through the C++ encoder
  (`_native/src/h2s.cpp`: the V-candidate enumeration factored into
  `for_each_v_candidate` — the twin of Python `_iter_v_candidates` — plus
  `v_key_prefix_equal` / `collect_tied_v_candidates`, and a V branch that loops
  `tie set × label-respecting perms` keeping the lex-min completion);
  `AlgorithmVariant::GreedyMinComplete = 7` (`canonical.hpp`/`canonical.cpp`,
  nbrdeg seeds + `tie_branch`, multi-seed fan-out over the existing thread
  pool); `tie_branch=` kwarg on `_core.greedy_h2s`/`greedy_h2s_tokens`
  (bindings), on `core.hypergraph_to_string.greedy_h2s` (both backends), and
  `_CPP_VARIANT_IDS["greedy_min_complete"] = 7` + the Python-backend dispatch
  in `_python_canonical_string`. `scripts/bench_tie_complete.py`.
- *Decisions (PI, this session):* (D1) **scope = T-TAa only** — port + measure;
  the default flip is contingent on these numbers, so it stays in T-TAd, which
  the port unblocks. (D2) **no admissible pruning** — a `lem:pruning`
  refinement of the tie set changes `w*_c` (lex-min over a subset ≠ lex-min
  over the tie set), so it would have to land in *both* implementations and
  invalidate the pinned counterexample / archived empirical arm; and it buys
  nothing on the slow fixtures (Fano/STS(9)/GQ(2,2) are vertex-transitive, so
  every tied edge carries the same invariant colour — the blow-up there is
  automorphism redundancy, which no invariant key can prune). The faithful
  port turned out fast enough that the lever is unnecessary.
- *C branch left un-branched (verified, not assumed):* a C candidate requires
  `members == set(tentative_inputs[:arity])` and `SparseHypergraph` forbids
  duplicate member sets, so the C tie set is always a singleton — there is no
  edge-id dependence to remove. This is why the proof only branches V.
- *Acceptance (a) differential:* C++ ≡ `_python_greedy_h2s(tie_branch=True)` on
  **3,344/3,344** per-seed comparisons (300 random instances, n∈[3,8], every
  seed, both `tie_branch` modes, seed 0); `canonical_string` cpp ≡ python on
  60/60 random instances; Fano + STS(9) + both presentations of the pinned n=4
  counterexample byte-equal. New tests: `test_cpp_differential.py` (+5:
  fano / sts9[slow] / counterexample / 2 Hypothesis sweeps),
  `test_backend_equivalence.py` (+3: fano[slow] / Hypothesis / variant
  registered), `test_greedy_min_complete.py` (+3, and the Fano reorder test
  un-marked `slow` — it now costs 9 ms).
- *Acceptance (b) completeness through the C++ path:*
  `tests/property/test_completeness.py --hypothesis-seed=0` green (invariance
  under relabel+reorder, and the `w*_c`-equality ⇔ pynauty biconditional) —
  it now runs in 0.8 s instead of minutes because `canonical_string` routes to
  variant 7. 150/150 relabel+reshuffle invariance in the standalone sweep.
- *Acceptance (c) wall-clock* (`scripts/bench_tie_complete.py`, i7-13700KF,
  Release `-O3 -march=native`, seed 0):

  | design | greedy (C++) | complete (C++) | ratio | `w*_g == w*_c` | complete (Python) | speed-up |
  |---|---|---|---|---|---|---|
  | Fano | 1.68 ms | **6.41 ms** | 3.8× | True | 3448.6 ms | 538× |
  | STS(9) | 7.26 ms | 137.5 ms | 18.9× | True | 132 075.9 ms | 961× |
  | STS(13) | 33.98 ms | 270.2 ms | 8.0× | **False** | — | — |
  | GQ(2,2) doily | 61.25 ms | 1092.9 ms | 17.8× | **False** | — | — |

  Random corpus (30 connected instances per `n`, median / max complete):
  n=4 0.06/0.58 ms · n=8 0.08/2.25 ms · n=10 0.13/11.6 ms · n=11 0.66/13.5 ms ·
  n=12 0.28/**43.7 ms**. Fano ≤ 50 ms met (6.41 ms); no DNF anywhere. The
  T-M5 corpora (n ≤ 12) cost sub-millisecond medians, so `d_I` over `w*_c`
  is affordable at corpus scale; the worst observed blow-up is the
  vertex-transitive GQ(2,2) at 1.1 s (17.8× the greedy default).
- ***Scientific finding (new, load-bearing for the T-TAd flip).*** The proof's
  remark that vertex-transitive designs sit in the automorphism-coherent-tie
  regime holds at the root but **not recursively**: `w*_greedy = w*_c` on Fano
  and STS(9), yet `w*_greedy ≠ w*_c` on the cyclic **STS(13)** and on
  **GQ(2,2)**. The greedy default therefore fails to be canonical on two of the
  four design fixtures, not just on the pinned n=4 counterexample. Pinned as
  `test_complete_differs_from_greedy_on_sts13`. `stability.md` §1 and the
  proof's §Empirical updated.
- *Closing checks:* `pytest tests/unit tests/property tests/integration -m "not
  slow" --hypothesis-seed=0` → **610 passed, 8 skipped, 6 deselected, 0 failed**
  (the delta over T-TA's 563 mixes this task's +11 with T-TAb's tests, landed
  concurrently in the same tree). Slow gates: **6 passed** (incl. the STS(9)
  tie-complete differential, 15.0 s, and the doily/STS(9) reorder invariance).
  ruff **3 == baseline** (none in changed files; `scripts/` clean);
  mypy **21 == baseline**. C++ rebuilt via `pip install -e ".[dev]"`.
- *Concurrency note:* T-TAb was being implemented by a parallel session in the
  same working tree while this task ran (`core/canonical.py` gained
  `seed_vertex_label`/`canonical_fingerprint` mid-session). Edits were
  region-disjoint and the combined suite is green, but the two tasks share one
  `_core` build — re-run `pip install -e .` after pulling either.
