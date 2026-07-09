# T-TAd — Fast complete canonical algorithm (C++), promoted to package default
**Declared:** 2026-07-09 10:23 CEST (PI directive; resolves D-TA1; supersedes T-TAa)
**Status:** OPEN — **reduced to the default flip.** The C++ port shipped at
T-TAa (2026-07-09 11:07): `AlgorithmVariant::GreedyMinComplete = 7`, byte-equal
to the Python reference, Fano 6.41 ms / STS(9) 137 ms / STS(13) 270 ms /
GQ(2,2) 1.09 s, random n≤12 medians ≤ 0.7 ms. The port's speed gate ("Fano
≤ ~50 ms") is met, so the flip's precondition is satisfied. What remains: flip
the default at the three surfaces, regenerate goldens/caches where `w*`
changes, and update the docs. Note the goldens *will* change on more than
tie-degenerate inputs — `w*_greedy ≠ w*_c` on STS(13) and GQ(2,2) (T-TAa
finding), so any cached design fingerprint is affected.
**Depends on:** T-TA (proof + Python reference, DONE pending review); T-TAa
(C++ port, DONE) — which it originally absorbed and now merely follows.
**Why out of scope:** T-TA's mandate was the theorem; making the complete
algorithm *fast* and *the default* is an engineering + promotion effort the PI
authorized on 2026-07-09 after reviewing the T-TA findings.
**Reasoning (why this algorithm must exist):** Theorem A (completeness `⇔`)
holds only for the tie-complete search: the greedy default
(`greedy_min_nbrdeg`) resolves residual V-ties by raw edge id, so its `w*`
depends on the edge insertion order — it defines **no canonical form at all**
on the isomorphism class (pinned n=4 counterexample; 5/16 random instances
flip under edge reshuffle). Without a complete default, `d_I` is not
well-defined on iso classes and the metric-space thesis (Corollary A, Theorem
B, every T-M5 application) has no foundation. The article therefore needs a
canonical algorithm that (i) provably reaches the canonical form on every
presentation (tie-complete branching — proved), (ii) is fast enough for the
T-M5 corpora and the design fixtures (the pure-Python reference is ~3.5 s on
Fano — unusable at corpus scale), and (iii) is C++-implementable inside the
existing `_native` variant dispatch. Speed lever, sound by the proof's
admissible-pruning lemma: refine the residual tie set with any iso-invariant
edge key (deeper `η`, canonically-computed WL edge colours, orbit refinement)
*before* branching; branch only over what remains. Raw-id keys remain
forbidden (that is exactly the bug being removed).
**Context to read first:**
- `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/theorem_a_completeness.{tex,pdf}` — Theorem A, the admissible-pruning lemma (the perf lever), Appendix code↔proof map
- `src/isalhg/core/hypergraph_to_string.py::{_iter_v_candidates,_tied_v_candidates,_encode_from}` — the `tie_branch=True` Python reference: the semantics the C++ twin must mirror bit-for-bit
- `src/isalhg/core/algorithms/greedy_min_complete.py` — the variant to wire to the single-FFI fast path (keep the registered name)
- `src/isalhg/core/_native/src/canonical.cpp::canonical_string_compute` + `include/isalhg/canonical.hpp::AlgorithmVariant` + the C++ `_encode_from` twin in `core/_native/src/` — the extension surface
- `src/isalhg/core/canonical.py::{_CPP_VARIANT_IDS,canonical_string}` — variant registration + default surface 1
- `src/isalhg/iso_backends/isalhg_backend.py` — default surfaces 2–3 (`IsalHGBackend.__init__`, `_DEFAULT_ISALHG_ALGORITHM`; preserve the `ISALHG_ALGORITHM` env override, T-M0 pattern)
- `src/isalhg/metric_space/distances/isalhg_levenshtein.py` — `d_I` must compute `w*_c` once the default flips
- `docs/article/theoretical/stability.md` §1 · `CLAUDE.md` §Mathematical Foundation + Critical Invariants — the claims that attach to the default
- `.claude/rules/coding_rules.md` — always
**Description:** Implement the tie-complete canonical search in C++ (branch
over the residual V-tie set × label-respecting orderings, lex-min completion),
optionally shrink the tie set with admissible (iso-invariant) pruning keys,
register it, wire `greedy_min_complete` to the fast path, and **flip the
package default** for the canonical algorithm at all three T-M0 surfaces so
IsalHG's H2S/canonical pipeline computes `w*_c` by default. S2H needs no
change (deterministic total interpreter). Regenerate any goldens/caches that
pinned greedy `w*` on tie-degenerate inputs; update docs so the default
statement matches the theorem.
**Tests to run (the Theorem-A completion gate):**
1. Differential: C++ tie-complete ≡ `_python_greedy_h2s(tie_branch=True)` on
   every conftest fixture, the pinned counterexample (both presentations), and
   a Hypothesis sweep (mirror `tests/property/test_cpp_differential.py` /
   `test_backend_equivalence.py`).
2. `tests/unit/core/test_greedy_min_complete.py` — including the `slow` Fano
   test (run without `-m "not slow"`).
3. `tests/property/test_completeness.py --hypothesis-seed=0` — invariance
   under relabel+reorder AND the `w*_c`-equality ⇔ pynauty biconditional,
   exercised through the C++/default path.
4. `tests/property/test_canonical_invariance.py --hypothesis-seed=0` —
   parametrization extended to the new default.
5. Partition agreement vs pynauty on {Fano, STS(9), STS(13) pair, GQ(2,2)}
   (`test_backend_equivalence.py` pattern) through the new default.
6. Full closing check: `pytest tests/unit tests/property tests/integration -m
   "not slow" --hypothesis-seed=0` + ruff + mypy at their recorded baselines.
7. Wall-clock report: {Fano, STS(9), STS(13), GQ(2,2)} + a random corpus
   (n∈[4,12]) vs the greedy default and vs the 3.5 s Python reference; state
   the worst observed branching blow-up on η-degenerate inputs.
**Acceptance:** C++ output identical to the Python tie-complete reference on
all of (1); tests (2)–(6) green with the complete algorithm as the package
default; goldens/caches regenerated where `w*` changed; wall-clock on Fano
≤ ~50 ms and corpus-scale timings compatible with T-M5a/T-M5b (report the
numbers; if a fixture stays pathologically slow, document the admissible
pruning applied and the residual cost); docs updated (`stability.md` §1,
`CLAUDE.md`, `CODE_DESIGN.md` default mentions).
**Out of scope here:** the proofs (done at T-TA — but if the C++ port adds a
pruning key, verify it against the admissible-pruning lemma and record the key
in the proof doc's §Consequences); the seed-label fingerprint augmentation
(T-TAb); the WL-pruned variant reconciliation (T-TAc); disconnected-input
support (T-M2c).
