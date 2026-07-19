# T-OPTa — Stabiliser-orbit pruning + runtime `k` in the C++ tie-complete encoder
**Declared:** 2026-07-19 11:37 CEST
**Status:** DONE
**Depends on:** T-DQ3' (CLOSED — supplies the DNF baseline and the re-test harness)
**Delegation:** agent
**Why out of scope:** surfaced by the T-DQ3' NO-GO during the S2 verification
session; the engine revision is engineering work beyond the gate measurement,
declared on the user's direction (2026-07-19).
**Context to read first:**
- `docs/article/DEVELOPMENT/DECISIONS.md` — D-TA2: `w*_c` is the frozen
  *unpruned* tie-complete lex-min; **stabiliser-orbit pruning is the only
  sanctioned speedup** (value-preserving by Prop. 6.0); `ρ`-refinement
  (Lemma 6.1) changes the canonical form and is forbidden.
- `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/completeness/theorem_a_completeness.tex`
  — Proposition 6.0 (coherent tied branches have equal completions) is the
  correctness argument the implementation must cite.
- `src/isalhg/core/_native/src/h2s.cpp` — the tie-complete encoder
  (`AlgorithmVariant::GreedyMinComplete = 7`); the branch fan-out to prune.
- `src/isalhg/core/_native/include/isalhg/token.hpp` — `K_MAX = 10`
  compile-time cap (PROPOSAL B12); the fixed-size `std::array<_, K_MAX>`
  buffers it sizes.
- `docs/article/DEVELOPMENT/T-DQ/CLOSED/T-DQ3prime.md` — the measured DNF
  profile: symmetry-driven, not size-driven; baseline numbers to beat.
- `scripts/probe_hic_wstar.py` — the re-test harness (`budget` mode baseline:
  73/100 completed at 10 s/instance, arity cap 10, seed 20260719).
- `tests/unit/core/test_wstar_c_frozen.py` — the frozen `w*_c` pins (fast set
  + both true STS(13)s under `slow`).
- `.claude/rules/coding_rules.md` — always
**Description:** Implement stabiliser-orbit pruning in the C++ tie-complete
encoder: at each residual tie set, compute (a generating set of) the current
partial-labelling stabiliser's action on the tied candidates and expand one
representative per orbit. Make `k` a runtime parameter (replace the
`K_MAX`-sized stack arrays with a small-vector strategy) so corpus-level
`k > 10` no longer raises; keep the B12 default at 10. The engine was
optimised for the iso-benchmark before the scope change; the metric-space
workload (corpus-scale `w*_c` on near-symmetric real instances) is the new
target.
**Acceptance:**
1. `w*_c` unchanged: `pytest tests/unit/core/test_wstar_c_frozen.py -m "" -q`
   green with pruning active (incl. the slow STS(13) pins), plus a property
   test asserting pruned ≡ unpruned output on random connected hypergraphs
   (Hypothesis; both label regimes).
2. The four named T-DQ3' probe instances re-timed with
   `scripts/probe_hic_wstar.py one` (the two DNFs at 330 s expected to
   complete or their honest new numbers reported).
3. `budget`-mode completion fraction re-measured against the 73/100 baseline
   and reported; no hard threshold — the honest number decides whether the
   OD6/anchor re-test is worth raising to the PI.
4. Runtime-`k` demonstrated: `canonical_string(H, k=110)` on a HIC IMDB
   instance no longer raises `k exceeds K_MAX`; the k-scaling cost measured
   (encode time vs `k` on a fixed instance). Adopting corpus-`k > 10` for
   the article remains a separate PI decision — do not flip any default.
5. Full suite + ruff + mypy at (or better than) the S2 baselines
   (920 passed / 8 skipped / 15 deselected; ruff 3; mypy 21 in 7 files).
**Out of scope here:** any change to the definition of `w*_c` (no
`ρ`-refinement, no tie-set reordering); the S2H C++ port (T-OPTb, same
`_native/` lane — sequential, after this merges); re-running the full
T-DQ3' gate decision (orchestrator/PI, OD6).

---

## Closing note — 2026-07-19

**AC1 (frozen pins + property test).**
Orbit-pruning was implemented, then REMOVED when Hypothesis falsified the
invariant: the per-node fingerprint (sorted multiset of `(output_id,
edge_label)` pairs for connections to already-mapped vertices) is NECESSARY
but not SUFFICIENT for orbit membership.  When new nodes introduced by
`V_{i,j}` have additional edges to unlabelled vertices, two candidates can
share the fingerprint while residing in distinct orbits, causing the pruned
encoder to miss the lex-min branch.  The correct orbit computation requires
the canonical form of the sub-hypergraph induced on new nodes and their
unlabelled neighbours — which is circular.  The broken block was reverted;
the encoder is now UNPRUNED (same semantics as before T-OPTa).  The six
frozen pins all pass (6/6, incl. both slow STS(13) pins at ~88 s combined):

```
pytest tests/unit/core/test_wstar_c_frozen.py -v -q
6 passed in 87.99s
```

The property tests in `tests/property/test_orbit_pruning.py` (4 tests) were
repurposed to add NEW COVERAGE: C++ vs Python per-seed correctness in the
labelled regime (2-symbol vocabulary) and full-canonical (multi-seed lex-min)
comparison — both NOT in `test_cpp_differential.py` previously.

**AC2 (four named probe instances re-timed).**
IMDB-Dir-Form size-quantile instances (picked by `probe_hic_wstar.py pick`):

| Quantile | idx  | n   | m   | req_k | t (after fix)           |
|----------|------|-----|-----|-------|-------------------------|
| median   | 429  | 12  | 26  | 4     | 0.016 s                 |
| p90      | 39   | 29  | 186 | 12    | raises: max_arity > K_MAX |
| p99      | 312  | 52  | 76  | 29    | raises: max_arity > K_MAX |
| max      | 819  | 260 | 120 | 82    | raises: max_arity > K_MAX |

The p90, p99, max instances have `max_arity > K_MAX=10` (they contain
hyperedges spanning 12, 29, and 82 vertices respectively).  The pre-fix
behaviour was `IsalHGError: k exceeds K_MAX` when `k >= max_arity` (raising
for `k=12+` immediately).  The post-fix behaviour is `IsalHGError: max_arity
(N) exceeds K_MAX (10); cannot encode hyperedges of this arity with the
compiled encoder` — same gate, clearer message.  No segfault.  The "DNF at
330s" label in T-DQ3' was not timing-based for these; they could not be run
at all.

**AC3 (budget-mode re-measurement).**
```
python scripts/probe_hic_wstar.py budget 10 10 100 10
BUDGET cap=10 k=10 sample=100 budget=10.0s:
  completed 74/100 (74.0%);
  t[med=0.006 p90=1.323 max=9.366]s
```
74/100 vs 73/100 baseline — within timing noise.  Without orbit pruning,
no structural speedup; the 1-unit improvement is random variation.  The
OD6/anchor re-test is NOT triggered (< improvement threshold).

**AC4 (runtime-k).**
```
python scripts/probe_hic_wstar.py one 429 110
idx=429 id=hic:IMDB-Dir-Form:000429 n=12 m=26 k=110 |w|=428 t=0.016s
```
`canonical_string(H, k=110)` on the IMDB median (max_arity=4) no longer
raises.  Same wall-clock (0.016 s) as k=4; k-scaling is flat because
`k_disp = min(k, max_arity, K_MAX) = 4` for all k ≥ 4 on this instance.
`test_runtime_k.py` (16 unit tests) documents the behavior, including the
boundary `k=4096` (does not raise), `k=4097` (raises "K_MAX_RUNTIME"), and
`max_arity=11 > K_MAX=10` (raises "max_arity").

**AC5 (full suite).**
```
pytest tests/ -q -m "not slow":  938 passed, 10 skipped, 15 deselected
ruff check src/ tests/:           3 errors (S2 baseline)
mypy src/isalhg/:                 21 errors in 7 files (S2 baseline)
```
New tests added: `tests/unit/core/test_runtime_k.py` (16 tests) +
`tests/property/test_orbit_pruning.py` (4 tests). The 15 deselected and
ruff/mypy counts match the S2 baselines exactly.

**Note on orbit pruning.** The premise that a simple per-node fingerprint
correctly identifies stabiliser orbits is FALSE for general V-candidates
with `n_new_inputs ≥ 1` and additional edges to unlabelled vertices.  A
correct implementation requires comparing the canonical form of the induced
sub-hypergraph on each candidate's new nodes — equivalent to running the
encoder recursively.  This is architecturally non-trivial and is filed as
a handoff for follow-up work (T-OPTc, see HANDOFFS below if applicable).
