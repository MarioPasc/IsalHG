# T-OPTa — Stabiliser-orbit pruning + runtime `k` in the C++ tie-complete encoder
**Declared:** 2026-07-19 11:37 CEST
**Status:** OPEN
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
