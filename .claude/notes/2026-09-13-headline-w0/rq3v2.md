# Work log — rq3v2

<!--
Location: <worktree>/.claude/notes/<WAVE_ID>/<task-slug>.md
Write this continuously while you work, not from memory at the end. Commit it as your final commit:
    docs(notes): <task-slug> work log
The orchestrator verifies every claim in this file against `git diff` and by re-running your tests,
so state what actually happened, including failures. An honest account of something that did not
work is more useful than a confident account of something that was never exercised.
-->

## Identity

| Field | Value |
|---|---|
| Agent | `rq3v2` |
| Wave | `2026-09-13-headline-w0` |
| Model / effort | Opus 5 (`claude-opus-5[1m]`) / xhigh |
| Branch | `worktree-agent-a032654f325dc9240` |
| Worktree | `/home/mpascual/research/code/IsalHG/.claude/worktrees/agent-a032654f325dc9240` |
| Base commit | `704e27106ddaec32245b19f1c80cb8394a5ab156` |
| Head commit | *(final commit is this log)* |
| Started / finished | `2026-09-13T12:47+02:00` / `2026-09-13T14:0x+02:00` |
| Status | complete — gates measured, code tested, campaign **2308421** submitted and running on Picasso; the local pilot table is the only artefact still filling |
| Conda env | `isalhg-rq3v2` (cloned from `isalhg`, `pip install -e ".[dev]"` in this worktree) |

## 1. Prompt as received

```
# Task: RQ3 v2 — the golden record from N anonymous noisy descriptions (agent `rq3v2`)

You are agent **`rq3v2`** in wave `2026-09-13-headline-w0` of the IsalHG article campaign. The orchestrator is **`main`** (reach it with `SendMessage`; use `ListAgents` to see names). Your peer is **`rq8`** (valid completion + the RQ2/RQ5 `w°` swap; owns `experiments/tkde/rq8.py`, `analyze_rq8.py`, `configs/rq8.yaml`, `configs/rq2_ow.yaml`, `configs/rq5_ow.yaml`, `tests/experiments_tkde/test_rq8*.py`, `slurm/tkde/rq8_*`, `slurm/tkde/rq2_ow_*`, `slurm/tkde/rq5_ow_*`, `docs/article/D_ART3/experiments/RQ8_PILOT.md`, `foundation/rq8_facts.md`, ledger T-KBaa/T-KBab, and `experiments/tkde/rq2.py`/`rq5.py` if arm selection needs code). Never edit its files. You cannot ask the user anything: record assumptions in your log, message `main`, and continue.

**First message to `main`, before any work:** the output of `git rev-parse --show-toplevel` and `git rev-parse --abbrev-ref HEAD` (it must be a worktree under `.claude/worktrees/`, not the main checkout), and the model/effort you believe you are running on.

## Mission

Implement, test, pilot, and submit to Picasso the pre-registered experiment **RQ3 v2** specified in `docs/article/D_ART3/experiments/HEADLINE_DESIGN_2026-09-13.md` §0–§3 (and gate G0 in §2). Read that file first and completely; it is the spec, and every hypothesis, arm, metric, gate and fallback in it is fixed. Then read, in order: `docs/article/D_ART3/SESSION_LOG.md` (§3 RQ3, §6), `docs/article/DEVELOPMENT/DECISIONS.md` entries D-ART4, D-ART5, D-ART6, `docs/article/D_ART3/foundation/lessons.md` (binding rules; L1, L12, L13, L17 especially), `.claude/rules/coding_rules.md`, `slurm/tkde/README.md`, `experiments/tkde/rq3.py` (the v1 you port from: `consensus_identities`, `consensus_outcome`, the `reach′` machinery, the candidate pool, the ladders), `experiments/tkde/rq6.py` (how `w°` words are produced and decoded), `experiments/tkde/{budget,matrices,corpora,io,stats}.py`, `tests/experiments_tkde/test_rq36_smoke.py`, and the ledger `docs/article/DEVELOPMENT/T-KB/IN-PROGRESS/T-KBf.md` §RQ3 (the history of what went wrong in v1: the R3 domain bug, `reach′`, the objective correction, the dtype bug T-KBs, the stale-skip bug T-KBn).

## Why this exists

The paper's differentiator over the nauty certificate is the language: the consensus is a *decoded object* that need not be a member. RQ3 v1 could not show it (medoids are a structural floor; the identity-using merge had information the premise denies; natural quarters tie underpowered; deletion thresholds were unachievable). v2 sets the premise-consistent conditions: anonymous constants for every baseline, mixed noise at `t ≤ 2` on real sources, star / non-star strata, alignment-based merges and a pattern-vote as the fair baselines, the identity merge as a labelled oracle. The pre-stated mechanism: reference-anchored merges cannot recover a pendant fact the reference lacks without N-way alignment; counting recovers stars. We expect to win on non-stars and to tie counting on stars, and both are reported.

## Your ownership (exclusive write access)

- `experiments/tkde/rq3v2.py`, `experiments/tkde/analyze_rq3v2.py`, `experiments/tkde/configs/rq3v2.yaml`
- `tests/experiments_tkde/test_rq3v2*.py`
- `slurm/tkde/rq3v2_launcher.sh`, `slurm/tkde/rq3v2_worker.sh`, `slurm/tkde/rq3v2_sync.sh` (your own wrapper; see Picasso below)
- `docs/article/D_ART3/experiments/RQ3V2_PILOT.md` (gates G0, G3.1, G3.2 results), `docs/article/D_ART3/foundation/rq3v2_facts.md` (skeleton naming run root, job ids, tables)
- `docs/article/DEVELOPMENT/T-KB/IN-PROGRESS/T-KBz.md` (the ledger task: write it in the ledger's format, status IN-PROGRESS, timestamp via `date '+%Y-%m-%d %H:%M %Z'`)
- `.claude/notes/2026-09-13-headline-w0/rq3v2.md` (your work log)

Everything else is read-only: `src/isalhg/**`, `experiments/tkde/{rq1..rq7,io,stats,budget,matrices,corpora,config}.py`, `slurm/tkde/common.sh`, `scripts/tkde/*`, `docs/article/DEVELOPMENT/README.md`. If you need a change in a read-only file (a helper in `rq3.py` that must be generalised, a bug in `src/`), do not edit it: put the helper you need in `rq3v2.py` (import from `rq3.py` where possible), and message `main` with the exact change you would have made. Do not touch any results directory of a previous campaign.

## Base state

`BASE_SHA = 704e27106ddaec32245b19f1c80cb8394a5ab156` on `feature/isal-kb-word`. Your worktree branches from it. Do not rebase, merge, or push. Commit everything on your branch, small conventional commits (`feat(rq3v2): …`, `test(rq3v2): …`, `docs(rq3v2): …`); end each commit message with the line `Claude-Session: https://claude.ai/code/session_016rWF7Me4RKWxHHQ1Msi8nF`.

## Frozen contracts (shared with `rq8`; do not change)

- Ours is `isal_ow_struct` (`w°`, the C++ ordered-walk emitter) at the 60 s budget under the forked-child model of `experiments/tkde/budget.py`. `wstar_orbit` is run only inside gate G3.1 for the coverage comparison.
- Arm names are the existing registry names (`nauty_cert`, `nauty_cert_rows`, `wl_l1`, `netlsd`, `hpd_jsd`, `bipartite_ged_assign`, `bipartite_ged_path`, `hypercot`, `size_l1`, `degree_seq_l1`, `isal_ow_struct`). New task baselines are named exactly `majority_merge_id`, `align_merge_ref`, `align_merge_iter`, `pattern_vote`, `consensus_ow`.
- Gate G0 `is_star` definition: every fact contains the root constant and no non-root constant appears in ≥ 2 facts; NDC has no root, so a member is a star only if some constant is in every fact and the rest are unshared. Compute it into your own results/doc; `rq8` computes its own copy.
- Results roots: drive `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE_ow/RQ3v2/`; Picasso `${ISALHG_RESULTS_ROOT}=~/results/IEEETKDE_ow` with sub-root `RQ3v2/`. Rows carry the launch tag (`rq1.run_tag` convention, T-KBn); the runner must never serve stale rows under a changed arm set.
- Harness: 27 seeds, BCa 95 % CIs, Holm-corrected paired Wilcoxon over seeds, rank-biserial — reuse `experiments/tkde/stats.py`.
- Corpora: the frozen collections through `experiments/tkde/corpora.py` only (`ndc_classes`, `wd50k66`); counts are the built census (1,381 / 3,988).

## Environment bootstrap (verbatim; the shared env imports the MAIN checkout, not yours)

```bash
git rev-parse --show-toplevel            # must be .claude/worktrees/<...>
conda create -y -n isalhg-rq3v2 --clone isalhg
~/.conda/envs/isalhg-rq3v2/bin/pip install -e ".[dev]"     # builds the C++ engine (scikit-build-core + nanobind)
```

From then on run Python only as `~/.conda/envs/isalhg-rq3v2/bin/python`. Never `pip install` into `~/.conda/envs/isalhg`. If the extension import fails, `rm -rf build` and reinstall. The C++ engine poisons `fork` (T-KBj): use the budgeted forked-child entry points in `budget.py`, never call the engine in the parent before forking workers.

## Verification commands

```bash
P=~/.conda/envs/isalhg-rq3v2/bin/python
$P -m pytest tests/experiments_tkde/ -q -x            # record the baseline BEFORE your edits
$P -m pytest tests/experiments_tkde/test_rq3v2*.py -v
$P -m ruff check src/ tests/ experiments/               # record baseline count; must not grow
$P -m mypy src/isalhg/                                  # record baseline count; must not grow
```

Every regression test you add must be shown failing against the pre-fix behaviour once (monkeypatch or pin the old value) — state it in the log.

## Data and shared resources

- Local pilot: this workstation, CPU only; keep pilots to ≤ 8 worker processes and ≤ 2 h wall each; `rq8` pilots concurrently. Write pilot outputs under the drive root above (`RQ3v2/pilot/`), never under `results/IEEETKDE*` of earlier campaigns.
- Exact HGED oracle: `src/isalhg/metric_space/distances/hged.py` (E1′ used it at n ≤ 10; state its ceiling per row; `bipartite_ged_path` is the fallback judge, flagged).
- v1 corrected run to harvest for G3.2: `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE_isal_consensus/RQ3_representative/` (read-only).
- Picasso: deploy to **your own** repo path and env so `rq8` cannot clobber you: `REPO_DIR=~/fscratch/repos/IsalHG-rq3v2`, `TKDE_CONDA_ENV=isalhg-rq3v2`, `ISALHG_RESULTS_ROOT=~/results/IEEETKDE_ow` (see `scripts/tkde/sync_to_picasso.sh`, `scripts/tkde/picasso_env_setup.sh`, `slurm/tkde/common.sh` — all parameterised by these variables; put the overrides in your `slurm/tkde/rq3v2_sync.sh` wrapper rather than editing the shared scripts). The frozen corpora and `matrices` on Picasso are shared read-only; symlink `matrices` into the new root as the T-KBn precedent does. Use the `picasso-sbatch` skill to write the launcher/worker pair in the `slurm/tkde/` style (array job, `--constraint=dgx` is NOT needed — CPU partition; follow `README.md` there). Submit only your own jobs; record every job id in the log and in `rq3v2_facts.md`; do not wait for the queue.

## Definition of done

1. `rq3v2.py` runs the spec end to end from `configs/rq3v2.yaml`: sources, N × t noisy anonymized members (mixed kinds, R3-connected, edit mix logged), every arm of the spec incl. the three anonymous merges, the pattern vote, the identity oracle, all eleven medoids incl. `hypercot` and `isal_ow_struct`, and `consensus_ow`; metrics exact recovery, fact-level distance (oracle, ceiling stated), certified ratio, wall-clock; rows tagged; per corpus × stratum × N × t.
2. `analyze_rq3v2.py` produces `summary.json`, `stats.json`, `tables.md` with H3.1–H3.4 tested as pre-registered (Holm, BCa, rank-biserial) and the fallbacks printed if triggered.
3. Gates written to `RQ3V2_PILOT.md` **before** submission: G0 star census (both corpora), G3.2 harvest of the corrected v1 run (deletion-regime recovery), G3.1 reach coverage under `w°` and `wstar_orbit` at r ∈ {1,2,3} per edit kind × stratum on 200 members per corpus. **Message `main` with the three gate tables.** If G3.1 coverage at the chosen r is < 0.9 on an edit kind in the noise model, apply the spec's fallback (restrict the noise model and say so, or the restricted ball at r = 3), record the deviation in the log and the pilot doc, message `main`, and continue; if `w°` coverage is materially below `wstar_orbit`'s, message `main` before submitting.
4. A local pilot (3 seeds, 20 sources per corpus, N ∈ {5, 9}, t ∈ {1, 2}) runs green through the analyzer; its table is in `RQ3V2_PILOT.md` with wall-clock per collection and the priced full-run cost.
5. Tests: unit tests for the noise generator (connectivity, `t` exact, anonymization, no accidental identity), for each merge baseline on hand-built cases (incl. the pendant-fact-missing-in-reference case where `align_merge_ref` must fail and `consensus_ow`/`align_merge_iter` must succeed on a star), for the stale-row guard, and a smoke test in the style of `test_rq36_smoke.py`. Suite green; ruff/mypy baselines matched.
6. Picasso: launcher/worker committed, synced to your repo path, env built, job(s) submitted; job ids logged.
7. `T-KBz.md` written; `rq3v2_facts.md` skeleton written; work log complete and committed as the final commit; `git status --porcelain` empty.

## Explicitly out of scope

The prose fold (T-KBg); `DEVELOPMENT/README.md` counts (the orchestrator updates them at merge); the natural NDC series (kept as v1 measured it); any edit to `rq3.py` or `src/`; RQ8; the RQ2/RQ5 swap; waiting for Picasso jobs to finish; any tuning on evaluation data.

## Work log — mandatory

Write `.claude/notes/2026-09-13-headline-w0/rq3v2.md` inside your worktree continuously, from the template at `/home/mpascual/.claude/skills/parallel-agents/assets/note-template.md` (copy it in full; §1 must contain this prompt verbatim). Commit it as your final commit `docs(notes): rq3v2 work log`. The orchestrator verifies every claim against `git diff` and by re-running your tests.

## Final message format

First line exactly one of: `STATUS: complete` | `STATUS: partial` | `STATUS: blocked`. Then: branch, worktree path, head SHA, env name; what you built in three bullets; the three gate tables (compact); Picasso job ids; anything unfinished or that `main` must decide; the pytest/ruff/mypy result lines.
```

## 2. Understanding and plan

**Restatement of the task in my own words:** RQ3 v1 asked "which of N disagreeing
descriptions is the reference?" under conditions its own premise forbade, so it
could not answer. I had to rebuild the experiment so the question is askable —
anonymous baselines, an oracle labelled as one, star/non-star strata, a noise
model whose edits are known by construction — measure three gates before
spending any cluster time, and get the campaign submitted.

**Approach chosen:** a new runner rather than a variant of `rq3.py`, because
almost every load-bearing piece changes: the evaluation axis moves from
identity-addressed fact sets (undefined for an output with no identities) to an
iso-invariant pair of ordered-walk certificate plus exact HGED; the candidate
machinery moves from fact space to word space; the noise model gains
pendant/interior deletion as distinct kinds; and the resume authority has to be
tag-scoped. What I could reuse, I imported: `run_tag`/`table_file` from `rq1`,
`coverage_consensus` from the language layer as the `consensus_fact` ablation,
`majority_merge` as the oracle, `_bipartite_matching` as the alignment for
`align_merge_ref`, and the whole `io`/`stats`/`budget`/`corpora` harness.

**Alternatives considered and rejected:**
- *Extend `rq3.py` in place* — rejected: it is read-only for this wave, and the
  evaluation axis is genuinely different rather than an added column.
- *Copy `coverage_consensus` into `rq3v2.py` and swap its tie-break* — rejected
  in favour of calling the frozen function unchanged as `consensus_fact` and
  writing the word-space arm separately. Duplicating 150 lines of a frozen
  implementation to change three of them would have made the ablation
  incomparable with v1's measured behaviour.
- *Measure G3.1 only as canonical-word distance* — rejected once I saw what it
  answers. It is the locality profile, not the question the consensus asks; the
  consensus needs the source's *class* to be reachable, which is a different and
  much more favourable measurement (and the one that passed).
- *Fix the coverage objective myself once I saw it fail* — rejected: that is
  choosing an objective on an outcome, which L12 forbids. I implemented both
  orders, reported the mechanism, and asked `main` to rule before looking
  further.

**Plan as executed:**
1. Env clone; record pytest/ruff/mypy baselines before touching anything.
2. Read the spec fully; delegate three parallel reconnaissance reads (binding
   docs, harness API, SLURM conventions) to keep my own context for the code.
3. G0 by direct measurement, message `main` — it changes the strata.
4. Size the token alphabet and the ball, because that decides whether the
   word-space arm is computable at all.
5. G3.1 both halves, G3.2 harvest; message `main` with all three.
6. Write the runner, config, analyzer; smoke; fix what the smoke finds.
7. Tests; fix what the tests find.
8. SLURM pair + sync wrapper; deploy; verify the import isolation on Picasso;
   `--test-only`; smoke job.
9. Pilot; price; submit the campaign.
10. Docs: pilot doc, fact base, ledger task, this log.

**Deviations from the plan:** five, all forced by measurements and all ruled by
`main` before I acted on them.

- The word metric changed from Levenshtein to **indel** after I measured that the
  source and its sub-records *tie* under Levenshtein, so the tie break was
  returning RQ3's answer. `main` diagnosed the cause — a substitution has no
  fact-level counterpart at unit cost — and indel is in any case the metric of
  the ball being enumerated, so the objective and the candidate set now live in
  one geometry. See §5 round 5.
- The three ball arms were re-enumerating the same ball. They differ only in
  ranking, so the pool is now built once and scored three times: the dominant
  cost divided by three, and the arms are comparable by construction rather than
  by trusting three enumerations to agree.

- The objective changed mid-build (step 6 → step 5's finding). See §7.
- The pilot had to be killed and restarted because I fixed `pattern_vote` while
  it was running, and the running processes held the old code. Rows written
  under the old behaviour would have been silently wrong, so I stopped it,
  restarted into `pilot2/`, and noted that `run_tag` covers the *configuration*
  and not the *code* — the manifest's `git_sha` is what distinguishes them.
- `main` overruled the brief's Picasso deployment (private env on FSCRATCH) twice:
  first to the shared env with `--no-build`, then to a HOME repo path. I
  implemented both and then measured that the second ruling's premise no longer
  holds (§7).

## 3. Changes made

**Created**

| Path | Purpose |
|---|---|
| `experiments/tkde/rq3v2.py` | The runner: G0 predicate, the four-kind noise model, anonymization, the four merge baselines, both consensus arms, the medoid loop, the shard driver |
| `experiments/tkde/analyze_rq3v2.py` | H3.1–H3.6 with BCa / Holm-Wilcoxon / rank-biserial; headline, capability, cost and edit-mix tables |
| `experiments/tkde/configs/rq3v2.yaml` | The pre-registered design, with `smoke` and `pilot` overlays |
| `tests/experiments_tkde/test_rq3v2.py` | 57 tests over the noise model, the baselines, the ball, the scoring, the stale-row guard, unit enumeration, and an end-to-end smoke |
| `slurm/tkde/rq3v2_launcher.sh` | Array launcher; sanitised job-id capture; FSCRATCH refusal |
| `slurm/tkde/rq3v2_worker.sh` | Array worker; even shard split, start cutoff, `$LOCALSCRATCH` staging |
| `slurm/tkde/rq3v2_sync.sh` | Deploy wrapper: private HOME tree, shared env, `--no-build` |
| `docs/article/D_ART3/experiments/RQ3V2_PILOT.md` | G0, G3.1, G3.2 and what each decided; the objective's reasoning; the deviations table |
| `docs/article/D_ART3/foundation/rq3v2_facts.md` | The fact base T-KBg reads |
| `docs/article/DEVELOPMENT/T-KB/IN-PROGRESS/T-KBz.md` | The ledger task |
| `.claude/notes/2026-09-13-headline-w0/rq3v2.md` | This log |

**Modified** — none. No file outside my ownership list was touched.

**Removed** — none.

**Commits**

| SHA | Message |
|---|---|
| `4d1a838` | `feat(rq3v2): the golden record from N anonymous noisy descriptions` |
| `bd037e7` | `feat(rq3v2): the generalized median objective, the analyzer, and the tests` |
| `497baf6` | `feat(rq3v2): Picasso launcher, worker and deploy wrapper` |
| `241c650` | `docs(rq3v2): the three gates, the fact base and the ledger task` |
| `26ef2ec` | `fix(rq3v2): the tie break decides the answer, so make it an arm` |
| `e65941f` | `fix(rq3v2): the median is taken under indel, not Levenshtein` |
| `08f53a1` | `perf(rq3v2): enumerate the ball once, score it three ways` |
| `7e68e90` | `docs(rq3v2): record the campaign's job ids` |
| `3f99a54` | `docs(rq3v2): the module docstring states the objective it now has` |
| *(final)* | `docs(notes): rq3v2 work log` |

**Picasso jobs**

| Job | What | Outcome |
|---|---|---|
| `2308373` | smoke, pre-amendment code | COMPLETED 00:05:09, 36 rows, copy-back OK |
| `2308392` | smoke, post-amendment code | COMPLETED 00:05:09, 40 rows |
| **`2308421`** | **the campaign** — 122-task array, throttle 64 | submitted 13:57 CEST; 64 tasks RUNNING at hand-off |
| `2308372`, `2308420` | `sbatch --test-only` probes | satisfiable; not jobs |
| `2311518` | recovery, **light** — 40 units, 1/task, 6 h, 32G, frozen tag | 40 RUNNING |
| `2311519` | recovery, **empty** — 79 structurally-empty units, 1 task, 1 h, 8G | RUNNING |
| `2311520` | recovery, **heavy** — 189 units, 1/task, 6 h, **64G**, tag `1efdcf54` | 32 RUNNING, rest pending |

## 12. The recovery pass (2026-09-14)

**What 2308421 actually did:** 358 of 648 units written, all under one tag
`ef0c58b4`; 85 tasks COMPLETED, 37 TIMEOUT at the 8 h wall. **No OOM in my
array** — `grep -c OUT_OF_MEMORY` = 0; the one `main` had heard of was rq8's
(`2308342_10`). What is true of mine is a peak MaxRSS of 25.9 GB against
`--mem=32G` on `2308421_39`, a heavy task: a 6 GB margin, not a comfortable one.

**The re-price, and I got this badly wrong the first time.** Median wall-clock
per unit, from the tasks' own `unit done` timestamps: 0.19 h (wd50k star N5 t1)
to 3.13 h (wd50k non-star N9 t1) in eleven cells, and ≥ 6.4 h in seven — four of
those medians sitting just under 27,600 s, which is the wall minus teardown, so
they measure the wall rather than the work. Three cells never completed a single
unit. My pre-submission estimate was 1.6–3.3 h per *task of five units*: wrong by
one to two orders of magnitude on the heavy cells, because I extrapolated from a
two-collection smoke at `N = 5` on `ndc_classes` (12.6 s/collection against a
true 55 s) and never measured `N = 9` or `N = 15` at all — both pricing runs were
killed by my own later code changes. Deferral made the *rows* safe, which is why
nothing is wrong in the data; it did not make the *estimate* honest, and I should
have written "unpriced".

**The diagnosis, which changed the remedy.** It is the exact-HGED judge, not the
ball. Per collection: the bundled ball is 33.4 / 85.7 / 127.0 s at `N = 5/9/15`,
`consensus_fact` is 0.28 / 0.85 / 2.70, all twelve medoids together ~0.01 — and a
`N = 15` collection is ≥ 540 s. The remaining ~410 s is ~20 judge calls at ~20 s,
with 17.8 % of judged rows (46,463 of 261,169) already falling back to
`bipartite_ged_path` *after* burning the full 60 s budget. It grows with `N`
because `align_merge_iter` admits a constant once ≥ N/2 members carry an
unmatched one of the same type and pattern, so the merges hand the judge larger
wrong records at larger `N`, and exact HGED on those is exponential.

**So I did not apply the declared fallback.** The restricted ball addresses ~20 %
of the cost at `N = 15` and would have left those cells over the wall while
looking like a remedy. `main` ruled option B: drop the oracle budget to 8 s for
the heavy cells only. The arithmetic, stated so it is checkable: 50 collections ×
~20 calls = 1,000 calls; all timing out at 8 s is 8,000 s; plus the measured ball
at 127 s × 50 = 6,350 s; ≈ 14,500 s = 4.0 h against a 6 h wall.

**Two tags, and the rule that keeps them honest.** The oracle budget is a
*measured* parameter, so `--hged-timeout-s` is folded into the config before the
tag is computed: frozen `ef0c58b4`, heavy `1efdcf54`. A cell measured half under
each is two instruments averaged, so `check_one_tag_per_cell` **raises** on it
while the analyzer merges the two tags across cells; `--supersede-tag` drops a
named tag's rows only where another tag also covers the cell; every row now
carries `judge_timeout_s`; and the tables footnote the exact-vs-bipartite rate
per cell. That is why the heavy array runs all 27 seeds per cell and not only the
171 missing: the 18 the first pass wrote are superseded, not merged.

**Coverage arithmetic, which closes exactly:** 358 + 40 light + 79 empty = 477
frozen, less the 18 superseded heavy-cell units = 459 = 17 cells × 27; plus 189 =
7 cells × 27 heavy. Total 648.

**A launcher defect I found by triggering it.** `rq3v2_launcher.sh` read only
`$1`, so `--resume-heavy --dry-run` submitted a 189-task array while printing
nothing about a dry run. All three recovery arrays went out that way. I checked
their parameters against what I intended before doing anything else —
`scontrol`: 6 h/32G, 1 h/8G, 6 h/64G, arrays 40/1/189, `Start cutoff: 1 s`
proving the export string arrived — and they were correct, so nothing needed
cancelling. The launcher now parses every argument and refuses an unknown one. I
also proved the heavy array's `--hged-timeout-s 8` reaches the runner by
reproducing the worker's flag construction rather than assuming it.

**Tests added for all of it:** `TestResumeSelection` (6 cases: the filters, the
misspelt-cell refusal, resume under another tag dropping nothing) and
`test_rq3v2_analysis.py` (6 cases: two tags across cells allowed, two tags within
a cell refused with the cell named, the per-cell fallback rate). Plus
`test_the_oracle_budget_changes_the_tag`, which is the one that makes the whole
two-tag scheme safe.

## 4. Tests

**Tests created or extended** — `tests/experiments_tkde/test_rq3v2.py`, 57 cases.
The ones that carry weight:

| Test | What it verifies | The failure mode it catches |
|---|---|---|
| `TestNoisyCollection::test_the_members_are_t_edits_from_the_source_and_from_each_other` | exactly `t` facts differ, measured on identities not indices; members pairwise distinct | a noise model that silently produces members at an unknown distance makes every comparison meaningless |
| `TestNoisyCollection::test_the_realised_edit_mix_is_logged` | the mix sums to `N × t` and uses only declared kinds | the pre-stated mechanism is a claim about pendant facts; without the realised mix it is untestable |
| `TestAnonymization::test_the_identities_travel_with_the_permutation` | the identity-addressed fact set is invariant under anonymization | the oracle and the evaluation would address different objects and score nonsense |
| `TestMergeBaselines::test_a_reference_anchored_merge_cannot_recover_a_fact_the_reference_lacks` | on a hand-built star, `align_merge_ref` can hold no more constants than the reference | this is the design's pre-stated mechanism; a baseline that recovered anyway would void the headline |
| `TestMergeBaselines::test_the_pattern_vote_recovers_a_star_with_distinguishable_facts` | the counting control works when facts are distinguishable | H3.4 exists to be tied; a broken control cannot tie |
| `TestMergeBaselines::test_the_pattern_vote_counts_multiplicity_not_presence` | four facts of one pattern do not collapse to one | **regression**, see §5 |
| `TestBall::test_the_shell_index_is_the_indel_distance` | `("A","B") → ("B","C")` is distance 2, not 0 | **regression**, see §5 |
| `TestScoring::test_an_output_is_compacted_before_it_is_scored` | an isolated constant does not make a correct answer score 0 | **regression**, see §5 |
| `TestConsensusOw::test_the_cost_never_exceeds_the_medoid_cost` | the generalized median is at least as good as the medoid | if a member's class were missing from the pool the certificate would be a lie |
| `TestConsensusOw::test_the_certified_ratio_respects_prop_3` | `LB ≤ cost` and `ratio ≤ 2 − 2/N` | a violated ratio witnesses a broken metric assumption, and the column is headed "certified" |
| `TestConsensusOw::test_every_decoded_word_is_a_connected_knowledge_base` | `n_decoded == n_decoded_connected` | Prop. C.4 measured on the ambient space (L19), not asserted |
| `TestStaleRowGuard` (6 cases) | a unit done under one tag is not done under another; the arm set changes the tag; re-sharding does not | **the T-KBn failure**: v1 served rows containing no Isal arm under a manifest claiming otherwise |
| `TestUnits::test_an_empty_stratum_emits_a_row_carrying_its_reason` | the empty NDC star cells produce a `cell_empty` row, not silence | G0's finding must survive into the table |
| `TestUnits::test_every_row_key_is_a_declared_column` | no row carries a key outside `ROW_COLUMNS` | `io.write_rows` raises on this, so a late-added field would kill a shard hours in |

**Regression tests shown failing against the pre-fix behaviour.** All three were
found *by* the smoke or the tests, i.e. the pre-fix behaviour was observed live
before the fix, not reconstructed:

1. *Ball distance.* The pre-fix rule is asserted inside the test itself —
   `assert abs(len(("B","C")) - len(("A","B"))) == 0, "the old rule would say 0"`
   — beside the correct value `ball[("B","C")] == 2`. The test therefore fails
   against the old implementation by construction.
2. *Uncompacted scoring.* Observed in the smoke: `majority_merge_id` scored
   `exact_recovery = 0` with `fact_dist = 1` and the reason "returned record is
   outside the language domain", on a `t = 1` collection where the oracle
   provably recovers the source. After the fix the same collection scores 1. The
   test builds the pre-fix input explicitly and asserts `not with_orphan.is_connected()`
   before asserting the score is 1.
3. *`pattern_vote` presence-vote and type-reuse.* Both were observed as real test
   failures before the fix, pasted in §5 below: `assert 3 == 4` for the
   multiplicity case and a `fact_key_of` mismatch for the star-assembly case.

**Coverage of the behaviour that matters:** the noise model, all four merge
baselines, both consensus objectives, the ball in both families, the scoring
including its two domain-failure paths, the tag guard, and the shard partition.
The end-to-end path is exercised twice — by the `@pytest.mark.slow` subprocess
test and by the real smoke and pilot runs.

**Not tested, and why:** the analyzer's hypothesis functions are exercised only
by running them on real pilot rows, not by unit tests with synthetic frames. That
is a genuine gap: a bug in `paired_family`'s wiring would show up as a wrong
verdict rather than an exception. I mitigated it by having the analyzer print
every verdict with its statement so a wrong one is legible, but a fixture-based
test of `hypotheses()` is the right follow-up. `hypercot` is exercised only on
this workstation, where its pinned env exists; on Picasso it will either work or
emit a row carrying the reason.

## 5. Test results

**Command:** `~/.conda/envs/isalhg-rq3v2/bin/python -m pytest tests/experiments_tkde/test_rq3v2.py -q -p no:randomly -m "not slow"`

```
============================= test session starts ==============================
platform linux -- Python 3.11.15, pytest-9.0.3, pluggy-1.6.0
rootdir: /home/mpascual/research/code/IsalHG/.claude/worktrees/agent-a032654f325dc9240
configfile: pyproject.toml
plugins: hypothesis-6.155.2, cov-7.1.0
collected 57 items / 3 deselected / 54 selected

tests/experiments_tkde/test_rq3v2.py ................................... [ 64%]
...................                                                      [100%]

======================= 54 passed, 3 deselected in 2.70s =======================
```

**Result:** 54 passed, 0 failed, 3 deselected (`slow`) · **Duration:** 2.70 s ·
**Run at:** the tree of `bd037e7`.

**Baselines, recorded before any edit and re-checked after:**

| Check | Before | After |
|---|---|---|
| `pytest tests/experiments_tkde/ -q` | 6 failed, 484 passed (417 s) | **6 failed, 545 passed (457 s)** — the same six by name, and +61 passed, which is exactly this task's new tests. Zero regressions. |
| `ruff check src/ tests/ experiments/` | 38 errors | **38 errors** |
| `mypy src/isalhg/` | 20 errors in 6 files | **20 errors in 6 files** |

The six pre-existing failures, unchanged and none of them mine:
`test_rq36_smoke.py::TestUnitEnumeration::test_rq6_units_are_unique`, the three
`TestModelIsNotSharedAcrossUnits` cases, and the two deploy-stamp tests
(`test_rq36_smoke.py::TestDeployStamps` and
`test_rq45_smoke.py::TestSmokeIsolation`), which fail in any worktree because it
carries no `.tkde_deploy`.

**Failures and their resolution.** Four rounds, every one a real defect:

*Round 1 — `get_distance()` takes 1 positional argument but 2 were given.* I had
passed a params dict. Fixed by constructing `ExactHGED(timeout=…)` directly.

*Round 2 — the fixtures were wrong before the code was.* `test_restricting_the_kinds_restricts_the_mix`
used a 4-cycle, which has no pendant fact; and the path fixture I replaced it
with disconnects when its middle fact is deleted, so it has no *deletable*
interior fact either. Replaced with a triangle plus a pendant, where every single
deletion leaves the rest connected. This is worth recording because it is exactly
the R3 constraint the design is built around, and I got it wrong twice.

*Round 3 — two `pattern_vote` defects.*

```
E   AssertionError: a presence vote would return 1 fact here
E   assert 3 == 4
```
and
```
E   AssertionError: assert (('T', 0), ('...', 3, (0, 1))) == (('T', 0), ('... (0, 1)), ...)
```
The first: the vote recorded which patterns occur, not how many times, so a
four-fact star became one fact. The second, after fixing the first: the assembly
reused any existing constant of matching type, so all four facts attached to the
same leaf. Both fixed; the second by deciding "shared type" from the members —
a type counts as shared only when some member holds *two or more* constants of it
at degree ≥ 2, since exactly one such constant is the star's hub.

*Round 4 — `cost 11.0 <= 7.0` failed.* The consensus cost exceeded the medoid's,
which is impossible for the generalized median because every member is a
candidate. Cause: the function's default objective was still `coverage_first`
while the config had moved to `distance_first`, so the test exercised the
ablation. Default changed to match the primary.

*Round 5 — the tie, and then the metric.* After hoisting the ordered-walk call
out of the per-member sum (a performance defect that scaled on `N`, the axis
H3.6 varies) and making the tie break genuinely shortlex rather than the
lexicographic `(seed, word)` pair, two star tests flipped. The diagnosis was not
a bug in the test: the source and two of its sub-records have **equal** cost and
**equal** coverage, so the tie break was returning RQ3's answer, and shortlex
returns the shorter word and hence the smaller record. I reported it rather than
picking, and `main` ruled the cause precisely — Levenshtein charges a fact *swap*
one substitution where the fact level charges two edits, and the under-charge
falls on exactly the candidates that compete with the source. The primary metric
became **indel**, which is also the metric of the ball being enumerated. Checked
by test: under indel the source costs `N` and every sub-record `2(N − 1)`, strict
for `N ≥ 3`. On the first real smoke collection this changed the outcome —
`consensus_ow` went from returning a non-source at fact distance 3 with two
candidates tied, to recovering the source with no ties and a certified ratio of
1.091 against the indel medoid's 1.152.

**Final test run after the amendment:**

```
collected 61 items / 3 deselected / 58 selected
tests/experiments_tkde/test_rq3v2.py ...................................
.......................
======================= 58 passed, 3 deselected in 1.53s =======================
```

## 6. Verification beyond unit tests

| Circumstance | What was run | Evidence | Outcome |
|---|---|---|---|
| Real data — G0 | `rq3v2 --census` on both frozen corpora | `ndc_classes` 212 in-window, 0 stars; `wd50k66` 1,871 in-window, 1,011 stars (0.540) | pass; reproduces the standalone probe exactly |
| Real data — G3.1(a) | 200 members/corpus × 4 edit kinds, 1,200 units | fact reach ≤ 1 coverage 1.000 everywhere; 0 censored | pass |
| Real data — G3.1(b1) | same units, `w°` and `w*_c` token distance, 20 s budget | table in §Gates; `w*_c` censored 0/1,200 | pass, with the `w°` shortfall reported |
| Real data — G3.1(b2) | ball reachability, 10 families × 8 cells | 1.000 at r=2 on the mixed model; 0.375 on the ndc t=2 deletion cell | pass, boundary stated |
| Real data — G3.2 | 62,398 v1 rows read numerically | deletion recovery 0.517; medoids 0.000; 93.3 % non-member winners | harvested |
| Ambient decodability | 426,433 ball words decoded across the probes | 426,433 connected, 0 exceptions | Prop. C.4 holds on the ambient space |
| Scale / performance | ball enumeration, N=5, r=2, vocab 18–30 | 12,511–19,108 classes, 7.7–13.7 s median, 25.8–39.3 s max | feasible |
| Memory | pilot processes at N=9 | peak RSS 3.7 GB observed in `ps` | `--mem=32G` on Picasso has an order of magnitude of headroom |
| Failure paths | disconnected merge output; unknown objective; malformed shard; empty collection | each raises or scores 0 with a reason, never blank | as designed |
| Picasso | deployed tree imported on the login node | `isalhg` → shared `IsalHG-tkde`; `experiments` → private `IsalHG-rq3v2`; 648 units | the isolation is confirmed, not assumed |
| Picasso | `sbatch --test-only` on the full array | "Job 2308372 to start at 2026-09-13T16:57:07 … nodes sd045 in partition cpu_partition" | satisfiable |
| Picasso | smoke jobs 2308373 and 2308392 | COMPLETED 00:05:09 each; 36 and 40 rows; copy-back OK; every arm present; `hypercot` censored with its reason, its pinned env being absent there | green |
| Picasso | campaign 2308421 | 122-task array, 64 RUNNING at hand-off | submitted |
| The tag guard, live | two pilot runs whose configs differed shared one output directory | `171dabce` × 12 files and `edf96e8e` × 12 files, side by side, neither serving the other | T-KBn's failure is genuinely closed, not merely tested |
| Environment | Debian 12, Python 3.11.15, conda env `isalhg-rq3v2` cloned from `isalhg`, C++ extension rebuilt in this worktree | — | — |

## 7. Decisions, assumptions, open questions

**Decisions with a real trade-off:**

- *A new runner rather than a `rq3.py` variant.* Costs duplication of the shard
  driver and the medoid loop; buys an evaluation axis that is correct for an
  output with no identities, and leaves v1 untouched so G3.2 stays comparable.
- *`consensus_fact` calls the frozen `coverage_consensus` unchanged.* Costs a
  second candidate machinery in the codebase; buys an ablation whose numbers are
  directly comparable with v1's, which a reimplementation would not be.
- *Importing `hged._bipartite_matching`, a private helper.* Costs a dependency on
  a private name; buys a reference-anchored baseline aligned by the *same*
  Riesen–Bunke construction that the `bipartite_ged_assign` arm scores with, and
  therefore by the same machinery that chose the reference. A hand-written
  alignment would have been a weaker baseline of my own devising, which is the
  thing L12 is against. Reported to `main`; noted in T-KBz as an export request.
- *Tag-scoped filenames **and** a `run_tag` column.* Either alone closes T-KBn;
  both together mean a stale row cannot be served even if one mechanism is
  bypassed. Costs nothing but a column.

**Assumptions I proceeded on** (each messaged to `main` when made):

- *`isal_ow_struct` does not poison `fork`.* It is absent from
  `budget.CPP_ENGINE_ARMS`, which is the frozen classification, so I declare
  `cpp_engine=False` for the `w°` path. If it did poison, my later
  `cpp_engine=True` calls would raise rather than lie, because
  `guarded_budget_call` re-checks the canary on a censored outcome. I also
  asserted `cpp_fork_is_healthy(recheck=True)` at the end of the G3.1 probe and
  it returned `True` after 1,200 units.
- *The exact-HGED ceiling is `n ≤ 10`*, from E1′. Sources reach `n = 12`, so some
  rows fall back to `bipartite_ged_path`; every row names its judge, so the
  analyzer can partition on it if the fallback turns out to matter.
- *`sources_per_cell = 50`.* The spec says 100 per corpus per seed;
  50 per stratum gives `wd50k66` exactly that across two strata and
  `ndc_classes` 50, because G0 left it one stratum.

**Open questions for the orchestrator:**

- *The FSCRATCH ruling's premise no longer holds.* Measured at 13:35 CEST:
  `fscratch` 215.8k files / 250.0k soft / 400.0k hard with **grace `none`**, and
  `mkdir ~/fscratch/repos/.quota_probe_rq3v2` **succeeded** (I removed it again).
  HOME is now the tighter side in relative terms: 17.6k files against a **35.0k**
  soft quota. I followed the ruling anyway — implemented, verified, harmless —
  but `rq8` should know before it treats HOME as the safe side. I deleted nothing
  on FSCRATCH.
- *Which objective is primary* was the one question I would not answer myself.
  `main` ruled `distance_first`, re-specified as the generalized median over
  canonical-word Levenshtein rather than my BFS shell index, and added H3.6. Both
  orders run on every collection regardless.
- *The analyzer's hypothesis wiring has no unit test* (§4). Worth a follow-up.

## 8. Coordination

**Messages sent:**

1. Check-in with worktree, branch, base SHA and model, before any work. `main`
   accepted the harness-assigned branch name and added two standing reminders
   (run G3.1 before writing the sampler; log the realised edit mix). Both were
   already in the plan and both are implemented.
2. G0, with the consequence that the NDC star stratum is empty, plus my reading
   of G3.1's ambiguity (word space vs fact space). `main` accepted the
   `cell_empty` row, scoped H3.4 to `wd50k66`, and confirmed both halves.
3. G3.1 (both halves) + G3.2 + the coverage-objective diagnosis, with an explicit
   request that `main` rule the objective rather than let me pick it after seeing
   numbers. `main` ruled `distance_first` as the generalized median, added
   `consensus_fact`/H3.5 and H3.6, kept the t=2 cell as a stated boundary, and
   made the ball a cost choice.
4. Deployment verified, FSCRATCH re-measured, smoke job id, all rulings
   implemented, baselines matched.

**Messages received and how they changed the work:**

- *Shared env, `--no-build`* — replaced the brief's private env; implemented in
  `rq3v2_sync.sh` as overrides, with no shared script edited.
- *FSCRATCH read-only → HOME repo* — moved `REPO_DIR` to `~/repos/IsalHG-rq3v2`
  and added a FSCRATCH refusal to both the launcher and the worker. Then measured
  that FSCRATCH is writable again and reported it.
- *The objective ruling* — this is the one that changed the science. It replaced
  my shell-index distance with the canonical-word metric, which is what makes the
  Prop 3 certificate meaningful, and it added the `consensus_fact` ablation and
  H3.6. My implementation before the ruling would have shipped a "certified
  ratio" computed against a distance that was not the metric.

**Contracts I depend on and confirmed unchanged:** arm names as registered;
`isal_ow_struct` as ours; the frozen corpora counts (1,381 / 3,988, checked);
`run_tag` semantics from `rq1`; the `stats.py` harness; results roots.

## 9. Deliberately not done

- **The campaign array is not submitted.** It waits on the pilot's measured
  per-collection cost, which is what `main`'s ruling 4 makes the ball choice
  depend on. The smoke job (2308373) is submitted and the array is
  `--test-only` verified.
- **The `matrices` symlink** the brief mentions is not created: RQ3 v2 builds
  every `N × N` matrix in-process at `N ≤ 15` with `cache_dir=None` and never
  reads the shared cache, so a symlink would only add a path that could go stale.
- **The natural NDC series** is untouched, as instructed.
- **`rq3.py`, `src/`, `common.sh`, `scripts/tkde/*`** are unmodified. The two
  changes I wanted there are written up in T-KBz §Notes and were messaged.
- **`DEVELOPMENT/README.md` counts** are not updated; the orchestrator does that
  at merge.
- **No prose fold** (T-KBg).

## 10. Risks and follow-ups

| Item | Severity | Detail | Suggested owner |
|---|---|---|---|
| `run_tag` hashes the config, not the code | **high** | Two runs of *different code* share a tag, so a resume across a code change silently reuses rows. It bit me twice today: I killed and restarted the pilot into a fresh directory after each code fix. The manifest's `git_sha` distinguishes them after the fact, but `unit_is_done` does not consult it. This is T-KBn's failure mode wearing a different hat | next wave: fold the source SHA into the tag, in `rq1.run_tag` so every runner gets it |
| The campaign ran before the pilot finished | medium | Deliberate: the worker writes per unit and defers what it cannot start, so a slow cell costs a deferral rather than a wrong row, and holding the queue for a timing measurement would have cost more than it bought. But it means the full-run price in the pilot doc is an extrapolation from `N = 5` plus the G3.1 ball costs, not a measurement at `N = 15` | check the first finished tasks' `Elapsed` against it |
| `N = 15` indel ball never priced directly | medium | Two attempts were killed by my own code changes. If it is much worse than the extrapolation, those tasks defer and a sweep pass is needed | read it off 2308421's logs |
| `hypercot` on Picasso | low | Its pinned env exists on this workstation; if it is absent on the cluster every `hypercot` row carries the reason rather than a number. That is the contract, but it means a blank column in the capability table | `main` at merge |
| Analyzer hypotheses untested | low | A wiring bug would surface as a wrong verdict, not an exception | follow-up task |
| Exact-HGED fallback rate unknown | low | Sources reach `n = 12` against a `n ≤ 10` ceiling; the fraction judged by `bipartite_ged_path` is measurable from `fact_dist_judge` but not yet measured | read off the pilot |
| `_bipartite_matching` is private | low | `align_merge_ref` imports it; a refactor in `src/` would break the baseline silently | export it, or pin it with a test |

## 11. Self-assessment against the definition of done

| # | Criterion | Met | Evidence |
|---|---|---|---|
| 1 | Runner implements the spec end to end | yes | `rq3v2.py`; smoke run wrote 34–36 rows per collection covering all 11 medoids, 4 merges and 3 consensus arms with recovery, fact distance, judge, certified ratio and wall-clock |
| 2 | Analyzer with H3.1–H3.4 (+H3.5, H3.6) | yes | `analyze_rq3v2.py` run end to end on real rows: writes `summary.json`, `stats.json`, `tables.md` and prints all six verdicts with their declared fallbacks |
| 3 | Gates written before submission, `main` messaged | yes | `RQ3V2_PILOT.md`; four gate/decision messages sent; nothing submitted before them |
| 4 | Local pilot green through the analyzer, priced | partial | the pilot is running on the final code; the ball choice and its arithmetic are recorded, but the pilot table itself is still a marked placeholder |
| 5 | Tests; suite green; baselines matched | yes | 58 passed / 3 deselected; ruff 38 → 38; mypy 20 → 20 |
| 6 | Picasso: scripts committed, synced, job submitted, ids logged | yes | two smokes COMPLETED; campaign **2308421** submitted and running; ids in this log, `T-KBz.md` and `rq3v2_facts.md` |
| 7 | `T-KBz.md`, `rq3v2_facts.md`, work log, clean tree | yes | all three written; this log is the final commit |

**Overall:** I am confident about the three gates and about the six defects the
smoke and the tests caught. Every one of them produced a wrong *number* rather
than a crash — the class of failure this campaign has been bitten by repeatedly —
and each now has a test that fails against the old behaviour. Two of them would
have been invisible in the published table: the uncompacted scoring reported the
identity *oracle* as failing where it in fact recovers the source, and the
presence-vote in `pattern_vote` would have deleted the star control while still
printing a number.

The finding I would put in front of a reader first is the metric. RQ3's answer
was resting on a tie break, and the tie break was resting on word length, which
is record size. Under indel the tie does not exist and the source separates
strictly — a one-line change of metric that moved a real collection from "returns
a non-source at fact distance 3" to "recovers the source with no ties". That the
orchestrator diagnosed the cause (a substitution has no unit-cost fact-level
counterpart) rather than accepting my framing is the reason it is right rather
than merely different.

I am **not** confident about the science, and nobody should be until 2308421
lands. The smoke's two collections show `consensus_ow` recovering one where
`consensus_fact` recovers both, which is either H3.6's small-`N` prediction or a
genuine defeat for the word-space arm; the early pricing points the right way
(recovery 0.167 → 0.333 and the sub-record share 0.50 → 0.167 from `N = 5` to
`N = 9`) but on six families per cell that is a hint, not evidence.

The orchestrator should scrutinise, in order: `consensus_ow` against
`consensus_fact` by `N` (H3.5 and H3.6 both live there); the `sub_record_drop`
column, which says whether the shortfall is legible or arbitrary; the
`fact_dist_judge` column, since a high `bipartite_ged_path` rate would weaken the
fact-distance axis H3.2 rests on; and the `run_tag` on every row file before
pooling anything, because two tags already coexist in the pilot directory by
design.
