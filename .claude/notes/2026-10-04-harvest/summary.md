# Wave summary — 2026-10-04-harvest

**Date:** 2026-10-04 · **Base commit:** `3615c00` · **Target / integration branch:** `integration/2026-09-13-headline-w0` (still unmerged into `feature/isal-kb-word`)
**Orchestrator:** `claude-fable-5-1` (session `[IsalHG-Fable-Review]`)

## Original prompt

A cross-session request from `[Opus-Article-Orchestrator]`: with at most one
Opus 5.5 agent, finish what is owed from jobs already submitted (harvest,
analyse, fact bases, the `\todo` cells of the capability table — RQ3 v2,
RQ2_ow, RQ5_ow, T-KBad; no new campaigns), and write
`docs/article/D_ART3/WRITING_BRIEF_2026-10-04.md`.

## Agent

| Agent | Mission | Model / effort | Branch | Head | Verdict | Log |
|---|---|---|---|---|---|---|
| `harvest` | RQ3 v2 + RQ2_ow harvest and analysis, T-KBad, table cells | `claude-opus-5-5` / `xhigh` | `worktree-agent-a9c34e6bb3d1fadbf` | `fcbb983` | ACCEPT | [`harvest.md`](./harvest.md) |

## Review

- **Verified:** 6 commits, 10 files, all inside ownership; tree clean; analyzer resolves inside the worktree; rq3v2/rq8 suites 202 passed (192 at base); ruff 38 / mypy 20 unchanged.
- **Findings:** the RQ3 v2 analyzer had four defects blocking analysis (pandas-3 crash on mixed tags, no coverage gate, indel medoid missing from H3.2, composition-confounded H3.6), fixed with failing-first tests before any per-N number was read.
- **Merge:** `dc89d8a`, no conflicts; suites 202 passed after merge.

## Outcome

RQ2 on `w°` closed (0 merges, 0 censored, 557 / 1,156 / 3,682 classes). RQ3 v2
closed on 11 complete cells: H3.1, H3.2 supported; H3.3, H3.5 not; the
fact-space ablation beats the word-space consensus 0.984 to 0.433, so RQ3 is
not a headline for the language. Capability table fully filled. T-KBab closed;
T-KBz in progress (seven cells incomplete; pattern-vote audit); T-KBad open
(real `w*_c` RQ5 rows lead every arm, unexplained).

## Orchestrator interventions

- Asked the agent to establish the denominator of the bipartite "557 → 574" split and to correct the orchestrator's own unverified table footnote ("on NDC"); resolved: NDC-classes, all 1,381 members.
- Wrote `WRITING_BRIEF_2026-10-04.md` and `FRAMING_CHECK_2026-10-04.md` for the writing session.

## Lessons

- The 2026-09-14 ruling to lower the judge budget acted on a diagnosis taken from row timers that excluded the dominant component; the logs' unit timestamps were the right evidence and were available. Diagnose from the coarsest honest clock first.
- The ablation that sank the headline (H3.5) was added by the orchestrator on purpose; it cost a headline and saved a rebuttal.

## Artefacts

Worktree `.claude/worktrees/agent-a9c34e6bb3d1fadbf` and its branch retained until the user confirms the integration merge.
