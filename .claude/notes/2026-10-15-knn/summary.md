# Wave 2026-10-15-knn: summary (code repo side)

**Dates.** 2026-10-15 to 2026-10-16.

**Orchestrator.** Main session, Opus 5.5, acting as group leader. The text side of this wave is
`2026-10-15-lighten`, in the Overleaf clone; its summary is
`.claude/notes/2026-10-15-lighten/summary.md` there.

## The user's request (verbatim core)

> "My PI has sent me a series of comments regarding the article. I'd like you to iterate on them just
> liek we have iterated on the other experiments... (1) A new experiment based off k-neighbours, with a
> really cool, visual figure (2) To aliviate the read in terms of words, not math... act then as an
> orchestrator... clear positive on our side... move one... to the supplementary. When you have
> designed, tested, orchestrated the code ( /parallel-agents ) and executed the experiment (
> /picasso-sbatch ) you will move onto the second text modification... keep some agents alive... 2 at
> most... keep the work logs organized in md files and a folder subtree... Think step by step, reason.
> Do several commits while you work, at the end, merge worktrees and push to overleaf and github.
> Review everythin exhaustively."

**The author's ruling, after four killed designs** (verbatim): "Create a self-contained tex file
that resembles the structure of a section in the supplementary with the details of the experiment's
results. Add visual and scientific figures."

## Agents

| agent | model / effort | branch | role | verdict |
|---|---|---|---|---|
| `a7cd2b6fdd3a1dd31`, probe engineer (long-lived) | Opus 5.5, xhigh | `worktree-agent-a7cd2b6fdd3a1dd31`, `feature/knn-mech2` | probe code, Designs C and D, orientation audit, sym-min regeneration, full run on Picasso, aggregation, S5 facts and figures | ACCEPT on every merge, after independent re-verification |
| `af69696281bd367c1`, writing expert (long-lived) | Opus 5.5 | Overleaf `agent/2026-10-15-lighten/compress` | text plan, waves 1–3 (see the Overleaf summary) | — |

**Engineer's log:** `probe-engineer.md`, in this folder.

## Merge record (code repo main)

| merge | content |
|---|---|
| `bd52419` | probe library, CLI, draft figure, tests |
| `46d5a7b` | Design C block builder, jobs, aggregator, figure, tests |
| `a7b607d` | Design D, C8 orientation audit, sym-min regeneration |
| `97a7cf3` | Picasso full run (array 2921149), registered-cell verdicts, S5 facts and figures |
| `4c31e7c` | rule-selected second row of the S5 mechanism figure, plus the mechanism range facts |

**Tests** after `4c31e7c`: `tests/newpos` 279 passed, 1 skipped. Ruff is clean on `scripts/newpos/knn`.

## Outcome

There is no kNN positive. All four pre-registered designs (A, B, C, D) are killed at full scale under
their registered rules. The record is `docs/article/D_ART3/experiments/KNN_2026-10-15/LOG.md`, §5–§9.

- **Design D:** the word leads 7 of its 8 claim cells, but is killed at NDC-classes, r = 1 (0.575 vs
  0.638). This reproduces the probe kill.
- **Main text:** carries no kNN claim. The experiment is supplement section S5, as a standalone file.
- **C8 under the symmetric-min edit path:** the pendant claim still holds (p < 10⁻³⁰). The pooled
  criterion now fails on both NDC collections. The article was regenerated (`symmin_regen/REGEN.md`).

## Interventions by the orchestrator

1. **Edit-path orientation.** The audit was triggered when the Design D probe showed the bipartite edit
   path is asymmetric. The fix: the symmetric minimum everywhere, and every article number regenerated.
2. **A false justification, corrected.** "The minimum can only favour the competitor" is false for
   ranking metrics. It was caught by the independent claim check and corrected in LOG §8.1 and in the
   text.
3. **Local replica cancelled.** The author asked for local compute to stop. The Picasso-vs-local
   comparison became a seed-0 cross-check: every arm is bitwise identical except NetLSD, whose float
   near-ties differ in 1-NN by at most 0.0196.
4. **Completeness defect in the verdict aggregator.** On a partial harvest it read H-KNN-D as
   "survives". The engineer was sent back (RETURN); verdicts now come from the registered cell set, and
   a regression test covers it. The leader recomputed the D means from the raw JSONs.
5. **The mechanism cell could not support its claim.** In the registered mechanism cell the word leads
   on 1-NN (79 % vs 78 % sibling-nearer). A second row was added by a stated rule (largest edit-path
   lead), together with range facts over the 12 B cells: the edit path has the higher sibling-nearer
   share in 10 of 12.

## What the decomposition got wrong

- **Harvest and aggregation were too loosely coupled.** The aggregator trusted the directory listing
  instead of the registration. Next time, freeze the registered cell set in code before the run.
- **Orientation of asymmetric competitors was not fixed in the pre-registration.** Any asymmetric
  distance needs its symmetrization stated before the first probe.

## Open items

- **T-KBae** (the C8 matrix mirror) is still open in the ledger.
- **Whether S5 enters `supplement.tex`** is the author's call.
- **Worktree cleanup** waits for the user's confirmation.

## Cleanup (2026-10-16, after the author's confirmation)

Each target was checked first: no uncommitted changes, branch an ancestor of `main`.

- **Code repo:** removed the worktree `.claude/worktrees/agent-a7cd2b6fdd3a1dd31` and deleted the branches `worktree-agent-a7cd2b6fdd3a1dd31`, `feature/knn-mech2` and `feature/knn-tsne-labels`.
- **Overleaf clone:** removed the worktrees `-evidence`, `-frontmatter`, `-lighten`, `-maintext`, `-method` and `-supplement`, and deleted their six `agent/…` branches.
- **Not deleted by the agent:** the cancelled replica `results/KNN_2026-10-15/full_local/` (319 MB, used nowhere; LOG §9). The permission rules blocked the agent's delete, so the command was handed to the author.
