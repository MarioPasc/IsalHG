# Wave summary — 2026-09-13-headline-w0

**Date:** 2026-09-13
**Wave:** `2026-09-13-headline-w0`
**Base commit:** `704e27106ddaec32245b19f1c80cb8394a5ab156` — docs(D-ART6): w° as the headline program; pre-registered headline design (RQ3 v2, RQ8), capability table, session log
**Target branch:** `feature/isal-kb-word` · **Integration branch:** `integration/2026-09-13-headline-w0`
**Orchestrator model / effort:** `claude-fable-5-1` / xhigh (session `[IsalHG-Fable-Review]`)

## Original prompt

```
Great! So let's do this: We are going to promote the wº string to our headline model, so that the ablation with nauty is easier to justify, and our headlines results will always be wº vs nauty-certificate (maybe vs w*_c, depending on the results, we need wº to be the absolute best) ; We need to make a latex table with the competitors' properties that we measure or take into account to classify them, and all competitors should appear in every single experiment. Since the experiments where we win are really really conditional, we only win on RQ6, which, for now, will be promoted to our headline result, we need to create the competitor table, whose main objetive will be to add the IsalHG entry at the end, bold it, and allow the reviewers to see that for every characteristics we measure of the competitors (e.g., canonical-invariant, complete-metric, ... you can take a look to a table we did for a sibling model, IsalGraph in /media/mpascual/Sandisk2TB/research/ISAL/completed/isalgraph/article/69b82c5859ed47c5468ca199/review1/article/tab_representation_properties.tex) then, we need to re-run or re-think+re-run RQ3, and we need to have another experiment that meets "(a) They use a property of IsalHG (b) They favour IsalHG w.r.t all competitors (c) They have a practical implication on knowledge base problems." properties and that clearly uses the data from Wikidata or other places. Let's do this: Update the docs, create the table, set the conditions for RQ3 to favour us in its results, design the other experiment (use the knowledge we have w.r.t. our proposal from all the data of the other results, to know where we fail) and then load /parallel-agents ; spawning only at most 2 opus agents (xhigh or high) let them implement and test the experiments and then they will (via /picasso-sbatch ) they will upload them to picasso. We dont really need more than 3 headline experiment with all the theoretical content that we have and the model explanation, figures, ... But they must meet all the criteria. You are now an orchestrator and should only interviene to reason, design and give advice to agents, since you are the smartest one, dont do heavy-lifting tasks that could poison your context window. Think step by step, reason. You can do this :-)
```

## Decomposition

Two experiments with no shared code paths: RQ3 v2 (golden record; new runner
`rq3v2.py` ported from `rq3.py`'s machinery) and RQ8 (valid completion; new
runner `rq8.py` over `rq6.py`'s n-gram machinery) plus the config-only `w°`
swap of RQ2/RQ5. All existing runners, `src/`, and the shared SLURM/sync
scripts were frozen read-only; each agent deployed to its own Picasso repo
path. The design, hypotheses, arms, metrics, gates and fallbacks were
pre-registered in `docs/article/D_ART3/experiments/HEADLINE_DESIGN_2026-09-13.md`
at the base commit, so the agents executed a spec rather than improvising.
The orchestrator wrote the decision record (D-ART6), the design, the capability
table and the banners before spawning.

**Deferred to a later wave:** the prose fold (T-KBg) once the campaigns land;
the RQ7/RQ1 timing re-check after T-KBy; `run_tag` folding the source SHA
(rq3v2 log §10).

## Agents

| Agent | Mission | Model / effort | Branch | Head | Verdict | Log |
|---|---|---|---|---|---|---|
| `rq3v2` | RQ3 v2 golden record: runner, analyzer, gates G0/G3.1/G3.2, SLURM, T-KBz | `claude-opus-5` / `xhigh` | `worktree-agent-a032654f325dc9240` | `38b1b14` | ACCEPT (pilot table unfinished; campaign prices itself) | [`rq3v2.md`](./rq3v2.md) |
| `rq8` | RQ8 valid completion: runner, analyzer, gates G0/G8.1, Amendment A1, SLURM; RQ2_ow/RQ5_ow swap; T-KBaa/T-KBab | `claude-opus-5` / `xhigh` | `worktree-agent-a1b4083a2935ce6dd` | `81e07a9` | ACCEPT (after one RETURN) | [`rq8.md`](./rq8.md) |
| reviewer (read-only) | fairness review of `rq8.attach` and the baseline symmetry | `claude-opus-5` / `high` | — | — | report only | design doc §8 item 6 |

**Ownership map**

| Agent | Owned paths |
|---|---|
| `rq3v2` | `experiments/tkde/{rq3v2,analyze_rq3v2}.py`, `configs/rq3v2*.yaml`, `tests/experiments_tkde/test_rq3v2*.py`, `slurm/tkde/rq3v2_*`, `docs/article/D_ART3/experiments/RQ3V2_PILOT.md`, `foundation/rq3v2_facts.md`, `T-KB/IN-PROGRESS/T-KBz.md` |
| `rq8` | `experiments/tkde/{rq8,analyze_rq8}.py`, `configs/{rq8*,rq2_ow,rq5_ow}.yaml`, `tests/experiments_tkde/test_rq8*.py`, `slurm/tkde/{rq8_*,rq2_ow_*,rq5_ow_*}`, `RQ8_PILOT.md`, `rq8_facts.md`, `T-KBaa.md`, `T-KBab.md` |

## Review findings

### `rq3v2` — ACCEPT
- **Claimed:** runner + analyzer + 61 tests; six numeric defects found and fixed with failing-first regressions; gates measured; campaign 2308421 submitted; pilot table unfinished.
- **Verified:** 10 commits, 11 files, all inside ownership; worktree clean; 61 tests pass in `isalhg-rq3v2`; ruff 38 / mypy 20 matched.
- **Findings:** none against the log. The pilot table gap is declared in the log and does not affect the campaign.
- **Action taken:** merged as-is.

### `rq8` — ACCEPT after RETURN
- **Claimed:** runner + analyzer + 93 tests; G0 and G8.1 measured; H8.1 fails → fallback; three campaigns submitted.
- **Verified:** 9 commits, 20 files at first report, all inside ownership; no edit to `rq2.py`/`rq5.py` (arm selection config-driven); 93 tests pass in `isalhg-rq8`; ruff 38 / mypy 20 matched.
- **Findings (from the independent review):** no leakage; evaluation symmetric; one real asymmetry — counting arms add exactly one fact by construction, the sampler's proposals do so 32 % of the time — which confounded the attachment-miss statistic and the sentence "the recommender attaches better".
- **Action taken:** RETURN with a scoped correction (Amendment A1, pre-registered before re-measurement); re-verified at `81e07a9`; merged.

## Orchestrator interventions

| Commit | Type | Agent affected | What and why |
|---|---|---|---|
| — | ruling | `rq3v2` | consensus must be word-space; v1's fact-space machinery kept as ablation `consensus_fact` + H3.5 |
| — | ruling | `rq3v2` | objective: generalized median under the indel distance (Levenshtein substitution under-charges fact swaps; source ties sub-records); fingerprint tie-break; H3.6; deletion-heavy t=2 as envelope |
| — | ruling | `rq8` | no torch: `ow_gru` → `ow_ngram_ho`; attachment-error rate logged directly |
| — | return | `rq8` | Amendment A1 (fact-count-matched arms; attach-miss denominator); outcome: attachment mechanism supported, NDC loss = pattern gap, WD50K lead untested |
| — | ruling | both | Picasso deployment: private `REPO_DIR` on HOME, shared env, `--no-build` (FSCRATCH quota) |
| (this commit) | integration docs | — | design doc §0 premise corrected + §8 deviations log; ledger README count; this summary; session log §9 |

## Integration

| Order | Branch | Merge commit | Tests after merge | Conflicts |
|---|---|---|---|---|
| 1 | `worktree-agent-a032654f325dc9240` | `merge(rq3v2)` | 450 passed (rq36/rq45 smoke files deselected) | none |
| 2 | `worktree-agent-a1b4083a2935ce6dd` | `a10e5ce` | 638 passed, 6 failed (the six pre-existing, same names) | none |

**Final verification**

| Check | Command | Result |
|---|---|---|
| Full TKDE suite | `~/.conda/envs/isalhg/bin/python -m pytest tests/experiments_tkde/ -q` | 638 passed, 6 failed (pre-existing: `test_rq36_smoke.py`/`test_rq45_smoke.py`), 8 min |
| Lint | `ruff check src/ tests/ experiments/` | 38 (baseline 38) |
| Type check | `mypy src/isalhg/` | 20 in 6 files (baseline 20) |
| Real-data check | Picasso smokes 2308373/2308392 (rq3v2), 2308337 (rq8) | all COMPLETED, copy-back OK |

**Merged into `feature/isal-kb-word`:** no — awaiting user confirmation

## Outcome

The paper's headline program is now the ordered walk `w°` (D-ART6, pending
the PI's word). Two new experiments exist as code, tests, pre-registered
specs, gate records and running Picasso campaigns; RQ2 and RQ5 are re-running
on `w°`. Gate G0 established that WD50K(66) is 53.4 % stars and NDC-classes
3 %, which fixed the strata of both experiments and explains the earlier
task-metric losses (a star's isomorphism class is a multiset of patterns).

RQ3 v2 (job 2308421) is the candidate second headline: under the
pre-registered indel median the consensus recovered the source on the smoke
collection with a certified ratio below the like-for-like medoid's, and the
Levenshtein-median arm tied and lost it as predicted. RQ8 (jobs 2308339 free-
running, 2308489 matched) is a supporting exhibit: the recommender wins on
pattern prediction on NDC, ours attaches better on both corpora once
fact-count-matched, and the WD50K lead awaits Holm at 27 seeds.

Before touching the code: `run_tag` hashes the config, not the source (two
pilot restarts were silently re-tagged); `consensus_ow` arms share one ball
enumeration by construction; the counting baselines in RQ8 are stronger than
the spec's minimum (three-position retry, 3·k ranked patterns) and that is
recorded.

## Follow-ups

| Item | Severity | Source | Suggested owner |
|---|---|---|---|
| Harvest 2308421 / 2308489 / 2308342-3 / 2308368 into `foundation/rq3v2_facts.md`, `rq8_facts.md`, and the RQ2/RQ5 fact bases; re-apply the pre-registered hypotheses | high | this wave | next wave |
| Fill the `\todo` cells of `tables/tab_kb_representation_properties.tex` (cons., compl., WL matrix time, HyperCOT merges) | medium | orchestrator | next wave |
| `rq1.run_tag` should fold the source SHA | medium | rq3v2 log §10 | next wave |
| RQ3 v2 local pilot table in `RQ3V2_PILOT.md` (or replace by campaign `Elapsed`) | low | rq3v2 log §9 | next wave |
| PI ratification of D-ART6 | high | orchestrator | user |
| FSCRATCH quota (60k files vanished between probes; unexplained) and whether to mail SCBI | medium | both agents | user |
| RQ8's 32 G memory request is ~5,000× the measured 6.78 MB peak | low | rq8 log | next submission |

## Decomposition lessons

- **What worked:** pre-registering the spec at the base commit; per-agent Picasso repo paths; gates reported to the orchestrator before submission, which let three scientific rulings (word-space consensus, indel median, fact-count matching) land before any campaign number existed; an independent read-only review of the arm that beat us.
- **What did not:** the design doc carried two premises that measurement overturned ("most WD50K are stars"; "the generator learns attachments and counting cannot" was first contradicted by a confounded statistic, then supported) — both are now in §8, but the doc should have marked them as hypotheses, not facts. The spec's G3.1 wording ("within reach of the member's word") did not distinguish token-space from fact-space reach, which the agent had to resolve.
- **Rule for next time:** every mechanism sentence in a design doc gets a "measured by" pointer or an explicit "hypothesis" tag; gate definitions name their space.

## Artefacts

- Worktrees: `.claude/worktrees/agent-a032654f325dc9240`, `.claude/worktrees/agent-a1b4083a2935ce6dd` — retained until the user confirms the merge
- Agent definitions: pre-registered global workers (`opus5-xhigh`, `opus5-high`); nothing to archive
- Branches: `worktree-agent-a032654f325dc9240`, `worktree-agent-a1b4083a2935ce6dd` — retained
- Conda envs: `isalhg-rq3v2`, `isalhg-rq8` (local); Picasso trees `~/repos/IsalHG-rq3v2`, `~/repos/IsalHG-rq8`

---

## Addendum 2026-09-14 — follow-up pass on the same wave

Both agents were resumed (not respawned) for the harvest and recovery work.
Merges: `66a9c4c` (rq3v2 recovery pass: re-price, two-tag judge budget,
arrays 2311518/2311519/2311520), `ac81c74` (rq8: H8 verdicts at 27 seeds,
Amendments A2/A3, RQ5_ow, RQ2_ow row-loss fix, T-KBac/T-KBad). Combined new
suites 192 passed; ruff 38 / mypy 20 held. Outcomes and rulings:
`docs/article/D_ART3/SESSION_LOG.md` §10 and the design doc §8.

Open at hand-off: RQ3 v2 arrays running (heavy: ~6 rounds of 6 h at throttle
32); RQ2_ow attempt 3 landing; the consensus cell of the capability table;
merge of the integration branch into `feature/isal-kb-word` (user); D-ART6
with the PI (user).
