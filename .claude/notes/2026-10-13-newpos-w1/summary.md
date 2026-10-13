# Wave summary — 2026-10-13-newpos-w1

**Date:** 2026-10-13
**Wave:** `2026-10-13-newpos-w1`
**Base commit:** `518824a80baf3238e1e565aafd6aaee0271c0bbc` — chore(newpos): probe scripts C2/C3, experiment log, tests package
**Target branch:** `feature/newpos-experiments` (cut from `integration/2026-09-13-headline-w0` @ `216dd41`) · **Integration branch:** `integration/2026-10-13-newpos-w1`
**Orchestrator model / effort:** `claude-opus-5-5` / `xhigh` (session `[IsalHG-Article-Iterator]`)

## Original prompt

The user's words follow verbatim. The pasted e-mail thread between the author
and the PI is summarised in brackets rather than reproduced. Its operative
lines are the PI's "faltan experimentos, con sus tablas y gráficas de
resultados, especialmente comparativas" and "hay que elegir aplicaciones en las
que nuestro método vaya bien".

```
CONTEXT: We finished the first version of the IsalHG article, and, in my opinion, it was an actual success. The methodology and the proposal is robust, I think we data we test, although limited, is within the expected for every property we are trying to prove. However, check this line of emails between me an my PI: "[pasted e-mail thread]" My PI may be demanding some more experiments, although maybe he has misunderstood my intentions, and thought that there are no good experiments in the article. (Good as experiments that favour us). First of all, you are tasked to gather all the context from the article and the approach we have been applying towards experiments. For that end, I'd recommend that you message two other agents that are online right now, and whose context windows are filled with that information: [Opus-Article-Orchestrator] and [IsalHG-Fable-Review]; You should message the fable agent not so often, since it is a costly model, and the session limits could be wasted on that, rather, only on really ocasional points you should ask it to review work or give you guidance. TASK: Once you have gathered enough context from the results we already have, the proposal, we data we use, ... (ask the other agents to tell you the absolute paths to results and other important intermediate artifacts), you should try to find experiments that favour us, since those will be the ones that will go into the article, since those are the ones that expose a characteristics of the method (negatives will go to the supplementary). You should act like a scientist, gathering information, proposing an hypothesis, testing it with small probes, and if they are promising, launching a bigger experiment via /picasso-sbatch ; you are allowed to spawn up to three subagents via /parallel-agents to carry out some coding or testing work for you. YOu must keep a md log of your experiments and the results, and propose creative things that we may have not proposed yet (thats why you should have extensive knowledge of the results). You can work with a team, where you spawn and keep alive agents that specialize in the results, in the code, ... and you ask them, while they are able to spawn up to 2 sub-subagents each. You should iterate for as long as you need, until you find at least one more experiments that adds more conclusive evidence to the article that favours our proposal, don't forget to not delete the negatives, since they would go to the supplementary. Be organized, think step by step, reason. You should iterate until you have an md file describing this new positive experiment and its results, and you have handed off all the previous md files of the work sessions of other agents, negative results, ... You are allowed to create and delete conda envs in Picasso and delete intermediate results in there too.
```

## Decomposition

The orchestrator probed the cheap, matrix-only hypotheses itself: C2 metric
search, C3 version linkage, C7 change tracking, and later C8 near-duplicate
retrieval. It delegated the three hypotheses that needed new machinery and hours
of compute to agents. Each agent was given its own code directory, test file and
results subdirectory, so the ownership sets were disjoint by construction. The
one shared contract — the frozen JSONL sample format — was written into both
generation prompts, so `neural-gen`'s samples could be scored by
`genbench-ngram`'s evaluator without either agent waiting on the other.
Reviewer-driven amendments were relayed by the orchestrator before any full
result existed.

**Deferred to a later wave:** D1 (augmentation by interpolation) and Z1 (the
cost table needs no compute), both parked in `LOG.md`; T-KBae (integration of
C8 into the draft; mirroring the matrices).

## Agents

All three ran on Sonnet 5.5 (`sonnet55-xhigh`; the project's
`CLAUDE_CODE_SUBAGENT_MODEL=sonnet` pins subagents), in isolated worktrees.

| Agent | Mission | Model / effort | Branch | Head | Verdict | Log |
|---|---|---|---|---|---|---|
| `genbench-ngram` | fidelity / rejection bias / VUN of the **usable** n-gram samples; generator-agnostic evaluator | `sonnet55-xhigh` | `worktree-agent-a73daebaecdd65b18` | `0824502` | ACCEPT | [`genbench-ngram.md`](./genbench-ngram.md) |
| `compression` | bits per KB of `w°` vs the certificate (5 renderings), fact list, incidence list; version deltas | `sonnet55-xhigh` | `worktree-agent-a1a377c3e23505bac` | `4f4f04b` | ACCEPT | [`compression.md`](./compression.md) |
| `neural-gen` | identical GRU LM over three serializations; validity, yield, VUN, held-out bits; symmetric sensitivity | `sonnet55-xhigh` | `worktree-agent-a9b5d669578441723` | `20c0048` | ACCEPT | [`neural-gen.md`](./neural-gen.md) |

**Ownership map**

| Agent | Owned paths |
|---|---|
| `genbench-ngram` | `scripts/newpos/genbench/**`, `tests/newpos/test_genbench.py`, `D/results/NEWPOS_2026-10-13/genbench_ngram/` |
| `compression` | `scripts/newpos/compression/**`, `tests/newpos/test_compression.py`, `D/results/NEWPOS_2026-10-13/compression/` |
| `neural-gen` | `scripts/newpos/neural_gen/**`, `tests/newpos/test_neural_gen.py`, `D/results/NEWPOS_2026-10-13/neural_gen/`, conda env `isalhg-newpos-gru`, the local GPU |
| orchestrator | `scripts/newpos/*.py`, `tests/newpos/{__init__,test_neardup}.py`, `docs/article/D_ART3/experiments/NEWPOS_2026-10-13/`, `D/results/NEWPOS_2026-10-13/neardup/`, `docs/article/DEVELOPMENT/T-KB/OPEN/T-KBae.md` |

## Review findings

### `genbench-ngram` — ACCEPT
- **Claimed:** 27 seeds; exact reproduction of RQ6; HA1 and HA2 not supported;
  HA3 supported except against the LCC repair on NDC; a post-hoc size-window
  diagnostic.
- **Verified:** 2 commits, only owned paths; 89 tests re-run green; ruff clean;
  tree clean; the verdict table read directly from `tables.md`.
- **Findings:** none. The post-hoc diagnostic is clearly labelled as outside
  every Holm family.
- **Action taken:** merged as is.

### `compression` — ACCEPT
- **Claimed:** pre-registration committed before the code; `w°` wins every
  certificate granularity under the learned and compressor coders but fails
  one theoretical-alphabet fixed-width cell; not convincingly better than the
  fact list; the length contradiction resolved.
- **Verified:** 5 commits (`9f9ef2d` pre-registration precedes `95cc9ef` code);
  33 tests green; ruff clean; the verdict flags in `tables.md` match the claim.
- **Findings:** the agent caught a bias of its own pre-registered bootstrap
  (with-replacement resampling undercounts compressed size by 18–29 %) and
  documented the fix. One `pkill` was permission-denied; it let the run finish
  instead of working around the denial.
- **Action taken:** merged as is.

### `neural-gen` — ACCEPT
- **Claimed:** HC1 (540,000 / 540,000); HC2 (8 / 8 tests, 27 / 27 seeds);
  amendment outcome (a); the exploratory LCC result; the uncapped sensitivity
  run changes nothing.
- **Verified:** 7 commits (pre-registration `6845e65` first); 30 tests green
  under `isalhg-newpos-gru`; ruff clean; no samples or checkpoints in git.
- **Findings:** it corrected a misstatement from its own pilot (duplicate rate)
  in its final report.
- **Action taken:** resumed once for the uncapped symmetric sensitivity run
  (the first sensitivity run was capped at 60 epochs and could not settle the
  undertraining question), then merged.

## Orchestrator interventions

| Commit | Type | Agent affected | What and why |
|---|---|---|---|
| — | relay | `genbench-ngram` | peers were not addressable by name; all peer traffic routed via main |
| — | amendment | `compression` | three certificate granularities plus two fixed-width alphabets, and the "claim only if all win" rule (lesson L9, via `[Opus-Article-Orchestrator]`); sent before any result |
| — | amendment | `genbench-ngram` | matched-usable-count fidelity primary; u < 100 excluded; directional HA1; the LCC as the strongest baseline (via `[IsalHG-Fable-Review]`) |
| — | amendment | `neural-gen` | pre-register both outcomes ("guaranteed vs learned"; residual rate with CI) |
| — | relay | `neural-gen` | the evaluator's CLI from `genbench-ngram` |
| — | return | `neural-gen` | uncapped symmetric sensitivity (≤ 200 epochs, all arms) |

## Integration

| Order | Branch | Merge commit | Tests after merge (`tests/newpos`) | Conflicts |
|---|---|---|---|---|
| 0 | `feature/newpos-experiments` (orchestrator work, `9d5db6e`) | — (branch point) | 11 passed | none |
| 1 | `worktree-agent-a1a377c3e23505bac` (`compression`) | `b91696c` | 44 passed | none |
| 2 | `worktree-agent-a73daebaecdd65b18` (`genbench-ngram`) | `396c16a` | 133 passed | none |
| 3 | `worktree-agent-a9b5d669578441723` (`neural-gen`) | `004df6c` | 163 passed (torch env); 133 + 1 skipped (main env) | none |

**Final verification**

| Check | Command | Result |
|---|---|---|
| New suites | `pytest tests/newpos -q` (env `isalhg-newpos-gru`) | 163 passed |
| Full suite (non-slow) | `pytest tests/ -q -m "not slow"` (env `isalhg`) | see the appended line below |
| Lint | `ruff check tests/newpos scripts/newpos/{genbench,compression,neural_gen}` | all checks passed |
| `src/` untouched | `git diff --stat 216dd41..HEAD -- src/` | empty |

**Merged into `feature/newpos-experiments` / `integration/2026-09-13-headline-w0`:**
no — awaiting the author.

## Outcome

The wave and the orchestrator's own probes found one new main-text experiment,
**C8 — near-neighbour retrieval of structural near-duplicates**. Its ground
truth is exact and representation-free: single-fact edit neighbourhoods, keyed
by the nauty certificate. On pairs one or two pendant edits apart, `w°`'s
nearest neighbour is the true near-duplicate far more often than under any of
ten competitors on all four collections (Holm p < 1e-32). On interior edits it
loses, and the pre-registered pooled criterion failed on NDC-substances AP;
both are printed. Two supporting results are suitable for one sentence each:
the GRU generator, where the guarantee is model-independent and the baselines
stay 30–92 % out of the domain, and compactness against the certificate under
learned and generic coders. Five negatives or mixed results go to the
supplement: C2, C3, C7, generation fidelity HA1/HA2, and compactness against
the fact list.

The code is scripts and tests only; `src/` is untouched. Every number has a
script and a results file; the C8 table is generated from JSONs. Before writing
from these results, read `docs/article/D_ART3/experiments/NEWPOS_2026-10-13/HANDOFF_2026-10-13.md`.

## Follow-ups

| Item | Severity | Source | Suggested owner |
|---|---|---|---|
| Write C8 into the draft (placement A/B, page budget), promote `wd50k100` / `ndc_substances` in the setup | high | `C8_…md` §7; T-KBae | author + PI, writing orchestrator |
| Mirror the five locally built matrices into `D/results/IEEETKDE/matrices/` with manifests | medium | T-KBae | next session |
| Decide whether "usable" includes the collection's size window | low | `genbench-ngram.md` §7.1.1 | author |
| The T-KB hub counts in `DEVELOPMENT/README.md` were already stale (22 open listed; 30 files in `OPEN/`) | low | observed | ledger owner |
| Three old worktree gitlinks (`.claude/worktrees/agent-a3a2…`, `-a6d4…`, `-acfe…`) show as deleted in the main checkout; not touched by this wave | low | `git status` | author |

## Decomposition lessons

- **What worked:** disjoint directories per agent, plus one frozen file
  format, meant zero conflicts and no cross-agent waiting. Pilot gates caught a
  hypothesis failure (HA1) before any compute was wasted on its framing.
  Relaying reviewer amendments before results kept every pre-registration
  intact.
- **What did not:** peers could not message each other by name (the Agent call
  takes no name), so the orchestrator had to relay. The orchestrator wrote
  estimated clock times into its log and corrected them later. The first
  sensitivity run inherited an epoch cap that made it uninformative.
- **Rule for next time:** read `date` for every timestamp, never estimate. When
  a prompt asks for a sensitivity run, specify every budget parameter
  (epochs, patience), not only the one being varied. Give peers addresses in
  the prompt only if the spawn mechanism supports names.

## Artefacts

- Worktrees: `.claude/worktrees/agent-{a73daebaecdd65b18,a1a377c3e23505bac,a9b5d669578441723}` — retained until the author confirms the merge.
- Agent definitions: none written (pre-registered global workers).
- Branches: retained.
- Conda env: `isalhg-newpos-gru` (local, torch) — retained; delete with `conda env remove -n isalhg-newpos-gru` when no longer needed.
- Picasso: not used. Every probe and campaign ran locally in minutes (C8: 6–48 s per collection; GRU: about 63 min of unit time), so no cluster resources were created or deleted.
