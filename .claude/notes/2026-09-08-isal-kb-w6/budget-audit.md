# T-KBf budgeting audit — code half

Wave `2026-09-08-isal-kb-w6`, task slug `budget-audit`.
Branch `wave/2026-09-08-isal-kb-w6/budget-audit`, base `385d110`.
Worktree `.claude/worktrees/kbf-budget-audit`, env `isalhg-kbf-budget`.

## Measurement that shaped every fix

A probe run before touching anything (fresh process per mode, two- to
four-vertex inputs, `cpp_fork_is_healthy(recheck=True)` as the read-out):

| first in-process call | forked child healthy afterwards |
|---|---|
| none (control) | **True** |
| `isal_ordered.ordered_symbols(H, backend="cpp")` | **True** |
| `canonical_string(H, backend="cpp")` | False |
| `orbit_oracle.canonical_fingerprint_rank(H)` (the `wstar_rank` arm) | **False** |

So the poisoning documented for the C++ *canonicalizer* extends to the C++
*rank* engine, and does **not** extend to the ordered-walk emitter. Two
consequences used below: any in-process `wstar_rank` fingerprint (which is what
`toolkit/matrix.py`'s fingerprint-first route does) poisons the process for
every later budgeted fork; and the ordered-walk arms are safe in-process.
Probe script (scratchpad, not committed):
`.../scratchpad/probe_poison.py`.

**The canary is therefore conditional, not universal.** `budget.py`'s own
docstring already recorded that poisoning hangs the C++ path *and nothing
else*, so a forked child computing a fact word, a nauty certificate or a vector
fingerprint runs correctly in a poisoned process and its censoring is genuine.
Guarding those unconditionally refuses work that would have succeeded — which
is what a first version of this branch did, and it turned 6 passing tests red
in a pytest session whose earlier tests had canonicalized in-process.
`guarded_budget_call` therefore takes `cpp_engine: bool` (default True) and
`CPP_ENGINE_ARMS = ("isalhg_levenshtein", "wstar_rank", "wstar_orbit")` names
the arms for which it is True.

## (A) `experiments/tkde/rq7.py` — the sweep path

**Finding — the reported defect is a false positive, one real defect beside it.**
`grep engine_word rq7.py` is empty because the call is one level down:
`rq7.py:47` imports `member_word` from `rq1`, and `rq1.py:488` routes every arm
of `BUDGETED_ARMS` (`isalhg_levenshtein`, `wstar_orbit`, `wstar_rank`) through
`engine_word` under `pointer_budget_s`. Both per-instance paths use it —
`run_sweep` (`rq7.py:250`) and `run_yield` (`rq7.py:290`) — so the arity-10
hazard named in the task is already bounded there.

Every other in-process canonicalization on those two paths, audited one by one:

| call | site | bound |
|---|---|---|
| `get_distance(arm).fingerprint(H)` for `isal_ow_*` | via `rq1.member_word:500` | one nauty call + a linear emission; measured above not to poison forks |
| `fact_word(H)` for `fact_rank` | same | no engine; linear in the fact list |
| `nauty_certificate_bytes` for `nauty_cert` | same | one nauty call — the campaign's own cost reference |
| `aut_bucket(H)` per swept instance | `rq7.py:245` | `pynauty.autgrp` on the coloured Levi graph; **not** provably ms in the worst case, but the same call RQ1 already makes per member unbudgeted (`rq1.py:611 _cached_aut_bucket`). Inherited, unchanged. |
| `required_k(H)` | `rq7.py:289` | max arity; O(m) |
| `word_tokens` → `parse(word)` | `rq7.py:266` | O(\|w\|) |

**The real defect: `run_nscaling`.** `rq7.py:385` forked under
`nscaling_budget_s` (3600 s) with `run_with_budget_detail`, i.e. no fork-health
canary. `_matrix_timing` canonicalizes inside that child, so for an engine arm a
poisoned parent turns every row into a one-hour "censored" that never ran.

**Change.** `run_nscaling` now calls
`guarded_budget_call(..., cpp_engine=arm in CPP_ENGINE_ARMS)` — the guard
applies to the three engine arms of the 15 in `nscaling_arms` and to no others;
the module docstring records the three-way audit above so the next grep does not
re-raise the false positive. `_matrix_timing`'s hardcoded `("fact_rank",
"fact_rank_roles")` branch now reads `WORD_ARMS` from the toolkit.

**Test.** `tests/experiments_tkde/test_budget_audit.py::TestRq7NScalingGuard` —
an injected unhealthy verdict makes `run_nscaling` raise on `wstar_rank`
(before any fork) and *not* on `size_l1`; the healthy case still measures.

**Residual risk.** `aut_bucket` stays unbudgeted; if a swept instance's Levi
graph is hard for nauty the sweep cell stalls. Changing it would change RQ1's
discipline too and is out of this task.

## (B) `src/isalhg/metric_space/toolkit/matrix.py` — the N×N route

**Finding.** `_build_from_fingerprints` (`matrix.py:~250` on base) computes
every member's representation up front through `distance.matrix(items)`, with
no per-member bound — which is exactly why `matrices.py:74` had excluded
`wstar_orbit` and `isalhg_levenshtein` from the matrices ("a budget is a
per-member notion that a whole-matrix build has nowhere to record") while
`wstar_rank` was left in and is the arm that censors at 60 s.

**Change (layered as required: `src/isalhg` imports nothing from
`experiments/`).**

- `matrix.py`: `FingerprintScreen` type alias (`(H) -> bool`, injected),
  frozen `MatrixCensoring` (`member_ids`, `censored_ids`, `n_requested`,
  `n_censored`, `censored_fraction`), and `build_matrix_censored(...) ->
  (matrix, MatrixCensoring)`. It screens every member, drops the rejected ones,
  and builds the survivors' matrix through `build_matrix` itself — so values,
  path selection and cache entry are bit-identical to an unscreened build of
  that sub-corpus. `build_matrix` is unchanged.
- `experiments/tkde/budget.py`: `arm_fingerprint_screen(arm, seconds)` builds
  the screen out of `guarded_budget_call`, i.e. one forked child per member.
- `experiments/tkde/matrices.py`: `BUDGETED_MATRIX_ARMS =
  ("wstar_rank", "wstar_orbit", "isalhg_levenshtein")`; config key
  `fingerprint_budget_s` (60.0 in `configs/matrices.yaml`) plus
  `--fingerprint-budget-s`; a budgeted unit runs `build_matrix_censored` inside
  a forked child (`_build_censored_child`) so the build's in-process
  canonicalizations cannot poison the runner for the next unit's screen — the
  measured hazard above. Only the two id tuples cross the pipe; the `.npy` is
  written by the child.
- Reporting per L15 (`analyze_rq1.m3_censoring`'s convention — censored counts
  in the denominator, never in a statistic): `rows_matrices` gains
  `n_requested`, `n_censored`, `censored_ids`, and `censored` is now the real
  flag instead of a hardcoded `0`; the full id list is also persisted next to
  the matrix as `<arm>.censored.json` (`censoring_path` / `read_censoring` /
  `_write_censoring`), which is what lets `run_unit`'s cache check and a
  downstream consumer address a censored arm by its surviving order instead of
  reading it as a cache miss.

**Test.** `TestBuildMatrixCensored` (4 cases): unscreened equals `build_matrix`;
a synthetic screen drops and names the member; the survivors' matrix equals the
sub-corpus matrix; length mismatch raises. No real canonicalization is run.

**Residual risk — stated, not hidden.**
1. **The survivors' representations are computed twice** (once by the screen,
   once by the build). Threading the screened values into the build would
   change what is measured: an arm's `matrix()` resolves `k` and the
   `("seed", label)` prefix over the *corpus* (`isal_engine.py:203-207`) while
   `fingerprint()` resolves them per member (`isal_engine.py:186-188`), so
   reusing them would silently produce a different matrix. Correctness was
   preferred over the ~1.5× cost on the `N`-half of the job.
2. The re-computation is bounded (each survivor finished inside the budget in a
   child) but it is in-process, so `build_matrix_censored` must be called from
   a disposable process. `matrices.py` does that; any new caller must too. The
   docstring says so explicitly.
3. Consumers (`rq2`, `rq4`, `rq5`) still call `load_cached_matrix(..., ids)`
   with the *full* frozen order and will raise `MatrixCacheMissingError` on a
   censored arm. The sidecar gives them what they need to subset, but wiring
   them to read it is **not** done here — no consumer was in scope. Flagged.
4. `rq3.py:473`'s medoid loop calls `build_matrix` in-process on `MEDOID_ARMS`
   (which includes `wstar_rank`): unbudgeted, and it poisons the process before
   the consensus `run_guarded` calls that follow at `rq3.py:552`. After (C)
   that now fails **loudly** instead of writing fictitious censorings. Wiring
   it to `build_matrix_censored` was deliberately not done: taking a medoid
   over a censored subset is a research decision (the medoid must be a member),
   not a budgeting fix. Flagged for the ledger.

## (C) `experiments/tkde/rq3.py::run_guarded`

**Finding.** `rq3.py:302` (base) hand-rolled the fork — `mp.get_context("fork")`,
`Pipe`, `poll(budget_s)`, `kill` — with no `cpp_fork_is_healthy` canary, so a
deadlocked child returned `("timeout", None)` and the caller
(`rq3.py:552`, the consensus at each radius) wrote `censored: 1`.

**Change.** The primitive was reused rather than duplicated. `budget.py` gains
`guarded_budget_call(fn, args, seconds, *, cpp_engine=True)` = the canary
discipline `engine_word` already had (check before the fork; on a censored
result recheck and raise `TkdeBudgetError` rather than report), and
`engine_word`'s two copies of that logic were replaced by calls to it.
`run_guarded` is now a five-line adapter onto it, keeping its
`("ok"|"timeout"|"error", value)` contract; `_guard_target` and the
`multiprocessing` import are gone.

**But the correction the brief expected is not the one the code needs.**
`run_guarded`'s one call site (`rq3.py:552`) guards `consensus_outcome` →
`coverage_consensus`, and that keys its hundreds of candidates with
`fact_key_of` (`isalhg/core/fact_word.py`, imported at
`language/consensus.py:69`) — **pure Python, not the C++ engine**. A poisoned
parent does not affect that child, so its censoring is genuine and refusing it
would be wrong. `run_guarded` therefore takes `cpp_engine: bool = False`, the
truth of the call site, with the docstring recording both why the default is
False today and that it must be flipped the day a consensus key becomes an Isal
word. The guard is live and tested; it is simply declared, not assumed.

**Test.** `TestRq3RunGuarded` (ok / error / poisoned-with-`cpp_engine=True` /
the pure-Python default not being refused) and `TestGuardedBudgetCall` (the
primitive, both branches, plus the arm list).

**Residual risk.** `rq3.py:473`'s medoid loop does reach the engine
(`build_matrix` over `MEDOID_ARMS`, which includes `wstar_rank`), unbudgeted and
in-process, and poisons the process before every `run_guarded` call that
follows. Under the current arms that is harmless; it stops being harmless the
moment either the consensus key or a `run_guarded` payload touches the engine.
See (B).4 — that loop is the RQ3 item this task deliberately did not decide.

## (D) `fact_rank_roles` dropped from every table

Removed as a measured/reported arm; the encoder is untouched
(`register_distance("fact_rank_roles", ...)` in
`distances/fact_levenshtein.py:217` and the `WORD_ARMS` route in `matrix.py`
both stay, and a test pins that the distance still resolves).

| file | removed |
|---|---|
| `experiments/tkde/matrices.py` | `DEFAULT_SPECS["wd50k66"]`, `SMOKE_SPECS["wd50k66"]` |
| `experiments/tkde/rq5.py` | `DEFAULT_ARMS` |
| `experiments/tkde/configs/matrices.yaml` | `collections[wd50k66].arms` |
| `experiments/tkde/configs/rq1.yaml` | `arms` |
| `experiments/tkde/configs/rq5.yaml` | two `designs[*].arms` (`wd50k66_full`, `wd50k66_balanced`) |
| `experiments/tkde/configs/rq7.yaml` | `nscaling_arms` |
| `experiments/tkde/rq7.py` | the hardcoded `("fact_rank", "fact_rank_roles")` branch → `WORD_ARMS` |
| `tests/.../test_rq45_smoke.py` | the assertion that it *is* a unit, replaced by the assertion that it is not |

`test_default_specs_cover_the_frozen_arms` also asserted `len(units) == 26`.
That number was already stale on the base commit, where `DEFAULT_SPECS` yields
**38** units — the assertion is one of the nine pre-existing failures below, not
a casualty of this change. Since my edit moves that number anyway (38 → 37),
leaving a knowingly-wrong constant was not an option; it now reads
`sum(len(arms) for arms in DEFAULT_SPECS.values()) == 37`, which states the
invariant as well as the count. That is the one pre-existing failure this branch
repairs, and it is called out here because it was not asked for.

**Test.** `TestRolesArmIsNotMeasurable` — absent from `matrices.DEFAULT_SPECS`,
`matrices.SMOKE_SPECS`, `rq5.DEFAULT_ARMS`, and every shipped config (textually
and after parsing every `*arms*` list); the encoder still resolves.

**Not done — outside my file permissions.** Two surfaces still name it and are
owned by another worker this wave:

- `experiments/tkde/rq1.py:54,89` — `ROLES_ARM` is still in `DEFAULT_ARMS`, so a
  run without an explicit `arms:` key would still measure it. `configs/rq1.yaml`
  no longer asks for it, so the shipped path is clean.
- `experiments/tkde/analyze_rq5.py:23,46,274-283` — hypothesis **H5d** is
  defined on `fact_rank_roles` and will now be permanently "inconclusive".

## Verification

Cloned env `~/.conda/envs/isalhg-kbf-budget`, `PYTHONPATH` = the worktree.

- `python -m pytest tests/ -q -m unit` —
  **8 failed, 2489 passed, 8 skipped, 276 deselected, 21 warnings in 893.18s
  (0:14:53)**. The eight are the pre-existing nine listed below minus the stale
  `== 26` this branch repaired; no new failure.
  `tests/experiments_tkde/test_budget_audit.py` alone: **24 passed in 0.15s**.
- Fail-without-the-change, measured: the same test file run against a worktree
  of base `385d110` gives **10 failed, 10 passed** — every (A), (C), (D) test
  fails there. The four `TestBuildMatrixCensored` cases passed in that run only
  because the editable-install finder resolved `isalhg` to *this* worktree
  (printed and checked); `git show 385d110:src/isalhg/metric_space/toolkit/matrix.py`
  contains **0** occurrences of `build_matrix_censored`/`MatrixCensoring`, so on
  a real base tree the module import fails and all four fail with it. (That run
  predates the `cpp_engine` refinement, which renamed two of the ten.)
- **Pre-existing failures, measured on the base tree**, by checking base `src`,
  `experiments` and `tests` out into this worktree and running
  `pytest tests/experiments_tkde/ -q -m unit`: **9 failed, 220 passed in
  246.32s** — `test_rq127_smoke.py::TestSmokeEndToEnd::{test_runner_then_analyzer
  [experiments.tkde.rq7], test_a_rerun_skips_the_units_already_written}`,
  `test_rq36_smoke.py::{TestUnitEnumeration::test_rq6_units_are_unique,
  TestModelIsNotSharedAcrossUnits (3), TestDeployStamps::
  test_the_stamps_name_the_imported_package}`, and
  `test_rq45_smoke.py::{TestMatrixUnits::test_default_specs_cover_the_frozen_arms,
  TestSmokeIsolation::test_deploy_stamps_name_both_trees}`. None of the nine is
  caused by this branch; one of them (the stale `== 26`) is repaired by it.
- `python -m ruff check src/ tests/ experiments/` — **Found 38 errors**, none in
  any file this branch touches (all in `experiments/article/power_pilot_main.py`,
  `experiments/preprint/**`, `experiments/article/analysis/**`,
  `src/isalhg/viz/instruction_view.py`, `src/isalhg/iso_backends/isalhg_backend.py`,
  `tests/unit/core/algorithms/test_registry.py`). Pre-existing on the base.
- `python -m mypy src/isalhg/` — **Found 20 errors in 6 files (checked 150
  source files)**, all in `core/{canonical,hypergraph_to_string,hypergraph_wl,
  structural_tuples}.py`, `core/_core.pyi` and `iso_backends/isalhg_backend.py`.
  None in `metric_space/toolkit/matrix.py`. Pre-existing on the base.

No corpus sweep, no RQ run, no SLURM submission. The only executed engine calls
were the four-vertex poisoning probe and the canary inside it.
