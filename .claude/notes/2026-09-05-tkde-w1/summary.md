# Wave summary — 2026-09-05-tkde-w1

**Date:** 2026-09-05 · **Orchestrator:** main session `[Experimental-Orchestrator]` (Fable 5.1) · **Work branch:** `main` (untouched) · **Integration branch:** `integration/2026-09-05-tkde-w1` · **Base commit:** `7590df4` (docs(tkde): pre-registered experimental design and engineering plan)

## User prompt (verbatim)

> CONTEXT: You are the experimental orchestrator of the IEEE TKDE article for IsalHG. Start reading on /home/mpascual/research/code/IsalHG/docs/article/D_ART3/START_HERE.md. We have been iterating on the article, and finally found a prose (/home/mpascual/research/code/IsalHG/docs/article/D_ART3/prose.md) that correctly fits everything we need. TASK: First, you must gather enough context and information regarding the proposal to understand, mainly, what is the scope of the article. We have initially decided on everything: Data, competitors, experiments, ... ; Then, you must design the experimental design of the article to prove our points, we are already a theory-heavy article, so we need to keep the experimens scoped, prove their effectiveness (as mi PI said: "    Confirmo que creo que el centro del artículo debe ser el procesamiento de KBs en el espacio de cadenas (pregunta D1), porque así nos quitamos de un plumazo todos los competidores. Ahora bien, habrá que justificar que estas tareas que vamos a acometer (medianoides, detección de outliers, dendrogramas, etc) serían de utilidad en el mundo real. "). You must spawn opus agents (high, xhigh) to implement the code, prompting them with a really really scoped prompt so that they do not overengineer or deviate fromt the task you have designed. EVERYTHING must be executed on Picasso and then copied back to local disk (look at FOLDERS). To orchestrate agents, load /parallel-agents and to let agents know how to use Picasso, either prompt them or tell them to load /picasso-sbatch ; You can spawn agents to set up the picasso env correctly (we NEED to use the C++ engine of Picasso, it is faster), they are allowed to modify src/isalhg, you can download data and tranfer it to Picasso. You are allowed to do almost everything you need that does not require deleting something permanently, if you are worried about Picasso quota, dont worry, we have 7 days of spare time.  IN-SCOPE: Designing the experimental setting of the article and detailing it, designing the statistical procedure (p-value, effect sites, CIs, ...) so that you can also specify which data we must save per experiment to compute them afterwards; interpreting results and deciding on whether if the hypothesis question should be refactored into a different one that measures the concrete property of IsalHG (e.g., if we set out to measure property A of IsalHG but the experiment states that A in IsalHG is weak, we do not report that on the article, rather in the supplementary material, and what we do is propose a property A' for the main article that really exhibits the true, complete behaviour os isalhg). OUT OF SCOPE: Designing figures, latex tables, writing the article, implementing code/executing yourself, ... FOLDERS: For results, save everything cleanly and self-contained in /media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE no folder mess. ACCEPTANCE CRITERIA: You have designed, documented, spawned agents to implement and monitor, reviewed the results, and modified anything you needed fo the experimental set up, until everything has been executed, and the results align with our vision of "exposing the best properties of isalhg in the main article", gather the context you need, tierate for as long as you need, and ask me anything you need. Think step by step, reason. You can do this, you are the best.

Follow-ups during the wave: "poison your context window as less as possible"; "What if we save the results on the home partition of Picasso instead of the fscratch one?" (adopted — results root moved to `$HOME/results/IEEETKDE`).

## Agents

| Agent | Model / effort | Branch | Worktree | Head | Verdict | Log |
|---|---|---|---|---|---|---|
| `fact-alphabet` | Opus 5 / xhigh | `worktree-agent-a6987ab85f8053d12` | `.claude/worktrees/agent-a6987ab85f8053d12` | `a62ba4f` | ACCEPT | `.claude/notes/2026-09-05-tkde-w1/fact-alphabet.md` |
| `kb-corpora` | Opus 5 / high | `worktree-agent-a115a1c540ce48e82` | `.claude/worktrees/agent-a115a1c540ce48e82` | `4c6e23d` | ACCEPT | `.claude/notes/2026-09-05-tkde-w1/kb-corpora.md` |
| `picasso-env` | Opus 5 / high | `worktree-agent-a57a0919d0e693ba9` | `.claude/worktrees/agent-a57a0919d0e693ba9` | `e6bd84b` (+ follow-up pending: results root → HOME) | ACCEPT | `.claude/notes/2026-09-05-tkde-w1/picasso-env.md` |

Verification per agent: clean worktree; commits present; `git diff --name-only` equal to the declared ownership set; branched from `7590df4`; tests re-run by the orchestrator in each agent's own env (fact-alphabet 143 new tests; kb-corpora 108 new tests; picasso-env `bash -n` + smoke job `2210893` COMPLETED on `sd030`, 363 unit tests on the compute node).

## Interventions

- Ratified four contract clarifications from `fact-alphabet` before implementation: two-pass total decoding (T tokens form the prefix, F tokens read as a set); colour-carrying certificate rows; function-body import of `canonical_ranks` from `iso_backends`; `LabelVocabulary.fit` already implemented.
- Ruled on three `kb-corpora` findings: facts of arity ≥ 2 only (NDC 1,381 / 528 instead of the supplement's 1,432 / 555, both recorded); the `m ≥ 3` floor stays (WD50K(66) 3,988); the RQ7 sparse density becomes `n = min(⌈1.5m⌉, m(k−1)+1)` (36 impossible cells fixed).
- Change request to `picasso-env` after the user's question: results root moved to Picasso HOME (FSCRATCH over its file soft quota, purged after two months); one re-validation job allowed.

## Merge record

```
93dd9e1 merge(fact-alphabet)   → 490 core unit tests pass
760546f merge(picasso-env)     → bash -n ok
183001e docs(integration): fold wave-1 findings (rank vector vs word; census; RQ7 rule; _core module; .gitignore fix; CODE_DESIGN stale note; metric_space dependency note)
6f2d54f merge(kb-corpora)
e7f8c0d docs(integration): results root → HOME; RQ3 Corpus B from the frozen census
```
Full verification at `e7f8c0d`: `pytest tests/unit -m unit` 1,588 passed / 6 skipped (287 s); `pytest tests/property -m property` 111 passed; ruff and mypy report only pre-existing findings in untouched files (mypy: 20 errors in `core/structural_tuples.py`, `iso_backends/isalhg_backend.py`, `core/hypergraph_wl.py`, `core/hypergraph_to_string.py`, `core/canonical.py`, `core/_core.pyi`).

No merge conflicts. The `integration/…` branch has not been merged into `main` (awaiting the user's confirmation; wave 2 branches from `e7f8c0d`).

## Findings worth keeping

- The canonical rank vector is invariant only up to an automorphism of the canonical form (557 / 2,000 random cases); the word is invariant. Never transport rank vectors between knowledge bases (now in DESIGN.md G1).
- An unanchored rsync exclude (`data/`) silently dropped the packaged STS catalog on the first Picasso deployment; the deployment is now verified by a full tree diff.
- Picasso: extension module is `isalhg.core._core`; envs under `~/fscratch/conda_envs`; `%a` in non-array log names expands to a sentinel; FSCRATCH file quota 251.7k / 250k soft (hard 400k), HOME 3.3k / 35k (hard 150k).

## Decomposition defects

None (ownership sets were disjoint; no conflicts). Orchestrator error worth recording: a `cd` into a worktree persisted across Bash calls and made one merge a no-op inside the agent's worktree; recovered by re-running with an explicit path. Rule for later waves: every git command names the main checkout explicitly.

## Open follow-ups

- `picasso-env` follow-up commit (results root → HOME, re-validation job) to be merged when it lands.
- `supplementary_data.md` S2 carries swapped node/product counts and the singleton-inclusive census; to be corrected in the prose fold (E8), not by this campaign.
- User to prune or archive `~/fscratch/results/isalsr` (65,944 files) or request a quota raise before the FSCRATCH grace period ends.
