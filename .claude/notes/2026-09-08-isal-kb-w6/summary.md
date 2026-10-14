# Wave 2026-09-08-isal-kb-w6 — the T-KBf budgeting audit

**Date:** 2026-09-08 · **Base commit:** `385d110` · **Work branch:**
`feature/isal-kb-word` · **Orchestrator:** `[IsalHG-Refinement-Opusxhigh]`

## The user's prompt, verbatim

> Read docs/article/D_ART3/experiments/HANDOFF_2026-09-07_isal.md end to end,
> arm its §4 monitor, and execute §5 in order (T-KBe, then T-KBf, then T-KBg),
> under the rules of §2. Report each step with its numbers; the pre-registered
> selection rule in ISAL_VARIANT_DESIGN.md §3 decides RQ1, the author/PI
> decides the representation. At the end, opdate docs. Think step by step,
> reason. If you need to take any decision on the matter that is really
> important, re-read the docs looking for an answer, if you dont find it,
> present the case to me. You can do this.

This wave covers the **code-only half of T-KBf** (the budgeting audit), run in
parallel with the T-KBe harvest because it is not gated on the RQ1 decision.
No experiment was submitted.

## Agents

| agent | model | effort | branch | worktree | head | verdict |
|---|---|---|---|---|---|---|
| budget-audit | opus5-xhigh | xhigh | `wave/2026-09-08-isal-kb-w6/budget-audit` | `.claude/worktrees/kbf-budget-audit` | `ba593a9` | **ACCEPT** (+ one orchestrator FIXUP) |

Log: [`budget-audit.md`](budget-audit.md) (committed in the worktree, arrived
with the merge). Env: `isalhg-kbf-budget`, cloned per `CLAUDE.md` §Environment
hazard.

## Verification — what I re-measured rather than believed

The log is a claim; these are the checks. Three of the agent's conclusions were
load-bearing enough to re-run independently, in **fresh processes** (poisoning
is process-global), with a 4-vertex input and a 20 s budget:

| probe | expectation | observed |
|---|---|---|
| poison via `canonical_string(backend="cpp")`, fork a **pure-Python** child | completes | **completes** |
| poison, fork a **C++** child (positive control) | censored | **censored** |
| run `ordered_symbols(backend="cpp")` first, fork a **C++** child | completes | **completes** |

So poisoning hangs only the C++ path — which is what licenses
`rq3.run_guarded`'s `cpp_engine=False` — and the ordered-walk emitter does not
poison at all, so its N×N matrices need no censoring machinery. Probe:
`scratchpad/poison_probe.py` (not committed; reproduced in the merge message).

Also verified:

- `engine_word`'s refactor into `guarded_budget_call` is behaviour-preserving
  **line for line** at both call sites (check before the fork; recheck on a
  censored result; refuse rather than report a fiction).
- `src/isalhg/metric_space/toolkit/matrix.py` imports nothing from
  `experiments/` — the budget screen is injected, so the layering rule holds.
- Tests: branch `8 failed, 245 passed` on `tests/experiments_tkde/`; main
  checkout on the three affected files `9 failed, 150 passed`. Set difference:
  **no new failures**, and one pre-existing failure fixed
  (`test_rq45_smoke.py::TestMatrixUnits::test_default_specs_cover_the_frozen_arms`).

## The agent corrected the brief twice, and was right both times

1. **The reported RQ7 defect was a false positive.** The handoff §5.3 said
   "RQ7's sweep per-instance path had no `engine_word` call at last grep"; I
   passed that on. `rq7.py:268,316` call `rq1.member_word`, which routes every
   `BUDGETED_ARM` through `engine_word` (`rq1.py:488`) — the grep missed an
   indirect call. The genuine unguarded fork was `run_nscaling` (`rq7.py:385`),
   now fixed.
2. **An unconditional fork-health canary in `rq3.run_guarded` refused valid
   work** (6 tests red). Its only call site guards `coverage_consensus`, whose
   candidate key is pure-Python `fact_key_of`; a forked child computes it
   correctly in a poisoned process. `cpp_engine` is therefore an explicit
   declaration of what the child does, defaulting to False there and documented
   as "a lie any other day".

A brief that is wrong on the facts is worse than a vague one; both corrections
came with the measurement that settles them, which is the standard to keep.

## Merge

`6865ea8` — `--no-ff` from the clean main checkout into `feature/isal-kb-word`.
No conflicts: ownership was disjoint (the agent held `experiments/tkde/{budget,
matrices,rq3,rq5,rq7}.py`, the configs, `toolkit/matrix.py` and
`tests/experiments_tkde/`; I held `merge_rq1_experiments.py`, `scripts/tkde/`,
`tests/unit/experiments/` and `docs/`).

**FIXUP `42f8c8e`** (mine, post-merge): `fact_rank_roles` removed from
`rq1.py::DEFAULT_ARMS`, which the agent could not touch because I owned the
file. This completes T-KBf item D.

## Deliberately left open — research decisions, not plumbing

- `rq3.py:473`'s medoid `build_matrix` over `MEDOID_ARMS` (including
  `wstar_rank`) is unbudgeted and poisons the parent. Not wired to
  `build_matrix_censored` because **a medoid over a censored subset is a
  research decision**, not a default.
- Whether `rq2/rq4/rq5` should tolerate a censored arm's short matrix; they
  currently read the full member order and would see a cache miss.
- Survivors' representations are computed twice in the censored matrix route
  (reusing the screen's value would change the matrix, since `matrix()`
  resolves `k` and the seed prefix per corpus while `fingerprint()` works per
  member).

## Follow-ups filed

- **T-KBj** — the fork poison itself, with the `spawn` fix Fable asked for.
  A canary is a workaround; a fresh interpreter cannot inherit the state. It
  must **not** land between RQ1 and RQ2, or the censoring censuses become
  incomparable.
- T-KBh, T-KBi — filed earlier in the session from the T-KBe work.

## What the decomposition got wrong

Nothing structural — one agent, disjoint ownership, clean merge. The defect
was in **my brief**: I copied the handoff's RQ7 claim without checking it, and
prescribed an unconditional canary for `rq3` that would have refused valid
work. The agent caught both. Next time, verify a defect report before
delegating a fix for it.
