# Work log — rq8

## Identity

| Field | Value |
|---|---|
| Agent | `rq8` |
| Wave | `2026-09-13-headline-w0` |
| Model / effort | Opus 5 (`claude-opus-5[1m]`) / `xhigh` |
| Branch | `worktree-agent-a1b4083a2935ce6dd` |
| Worktree | `/home/mpascual/research/code/IsalHG/.claude/worktrees/agent-a1b4083a2935ce6dd` |
| Base commit | `704e27106ddaec32245b19f1c80cb8394a5ab156` |
| Head commit | the commit carrying this file — `docs(notes): rq8 work log`, the fifth and last (§3); the one before it is `a5748f2` |
| Started / finished | 2026-09-13 12:36 CEST / 2026-09-13 13:32 CEST |
| Status | complete |

## 1. Prompt as received

```
# Task: RQ8 — valid completion of a record, plus the `w°` swap of RQ2/RQ5 (agent `rq8`)

You are agent **`rq8`** in wave `2026-09-13-headline-w0` of the IsalHG article campaign. The orchestrator is **`main`** (reach it with `SendMessage`; use `ListAgents` to see names). Your peer is **`rq3v2`** (the golden-record experiment; owns `experiments/tkde/rq3v2.py`, `analyze_rq3v2.py`, `configs/rq3v2.yaml`, `tests/experiments_tkde/test_rq3v2*.py`, `slurm/tkde/rq3v2_*`, `docs/article/D_ART3/experiments/RQ3V2_PILOT.md`, `foundation/rq3v2_facts.md`, ledger T-KBz). Never edit its files. You cannot ask the user anything: record assumptions in your log, message `main`, and continue.

**First message to `main`, before any work:** the output of `git rev-parse --show-toplevel` and `git rev-parse --abbrev-ref HEAD` (it must be a worktree under `.claude/worktrees/`, not the main checkout), and the model/effort you believe you are running on.

## Mission

Three deliverables, in this order of priority:

1. **RQ8 — valid completion**, pre-registered in `docs/article/D_ART3/experiments/HEADLINE_DESIGN_2026-09-13.md` §0–§2 and §4: implement, test, pilot (gate G8.1), submit to Picasso.
2. **Gate G0 — the star census** (§2), computed into your own results/doc.
3. **The `w°` swap** (§5): RQ2 census and RQ5 clustering re-run with `isal_ow_struct` in place of `wstar_orbit`, submitted to Picasso.

Read the design file first and completely; every hypothesis, arm, metric, gate and fallback in it is fixed. Then, in order: `docs/article/D_ART3/SESSION_LOG.md` (§3 RQ6, §6.3), `docs/article/DEVELOPMENT/DECISIONS.md` entries D-ART4, D-ART5, D-ART6, `docs/article/D_ART3/foundation/lessons.md` (binding; L1, L12, L13, L17), `docs/article/D_ART3/foundation/rq6_generation_facts.md`, `.claude/rules/coding_rules.md`, `slurm/tkde/README.md`, `experiments/tkde/rq6.py` (the n-gram over `w°` words, how words carry labels, sampling, decoding, the `ow_ngram` / `fact_ngram` / `incidence_ngram` arms, the certificate dedup), `experiments/tkde/rq2.py` and `rq5.py` (arm selection), `experiments/tkde/{budget,matrices,corpora,io,stats}.py`, `tests/experiments_tkde/test_rq36_smoke.py` and `test_rq245_consumers.py`, and the ledger `docs/article/DEVELOPMENT/T-KB/IN-PROGRESS/T-KBf.md` §RQ6 (the `MODEL_OURS` mislabel, the reach-1 bugs, T-KBo).

## Why this exists

The paper's differentiator over the nauty certificate is the language. RQ6 showed unconditional generation is valid and connected by theorem. RQ8 makes it *useful*: conditioned on a record's canonical program as a prefix, every continuation decodes to a connected knowledge base containing the record (state and prove the one-line Prop. C.8 — appending instructions never removes a fact or a constant — in `RQ8_PILOT.md`), so a sequence model proposes only valid completions, and we score whether the true completion is among them. The pre-stated mechanism: on stars the missing statement is a pattern-prediction contest where a co-occurrence recommender is expected to tie or win; on non-stars the completion must also choose *attachments* to existing constants, which the generator learns and counting cannot. The claim is for the interior units of the non-star stratum; the star stratum is the printed control.

## Your ownership (exclusive write access)

- `experiments/tkde/rq8.py`, `experiments/tkde/analyze_rq8.py`, `experiments/tkde/configs/rq8.yaml`, `experiments/tkde/configs/rq2_ow.yaml`, `experiments/tkde/configs/rq5_ow.yaml`
- `experiments/tkde/rq2.py`, `experiments/tkde/rq5.py` — **only if** arm selection cannot be expressed in YAML; note every edit in the log
- `tests/experiments_tkde/test_rq8*.py`
- `slurm/tkde/rq8_launcher.sh`, `slurm/tkde/rq8_worker.sh`, `slurm/tkde/rq2_ow_launcher.sh`, `slurm/tkde/rq5_ow_launcher.sh` (thin launchers reusing the existing workers if their arm set is config-driven), `slurm/tkde/rq8_sync.sh` (your wrapper; see Picasso below)
- `docs/article/D_ART3/experiments/RQ8_PILOT.md` (G0, G8.1, Prop. C.8), `docs/article/D_ART3/foundation/rq8_facts.md` (skeleton naming run root, job ids, tables)
- `docs/article/DEVELOPMENT/T-KB/IN-PROGRESS/T-KBaa.md` (RQ8) and `T-KBab.md` (the swap), in the ledger's format, status IN-PROGRESS, timestamp via `date '+%Y-%m-%d %H:%M %Z'`
- `.claude/notes/2026-09-13-headline-w0/rq8.md` (your work log)

Everything else is read-only: `src/isalhg/**`, `experiments/tkde/{rq1,rq3,rq4,rq6,rq7,io,stats,budget,matrices,corpora,config}.py`, `slurm/tkde/common.sh`, `scripts/tkde/*`, `docs/article/DEVELOPMENT/README.md`. If you need a change there (e.g. a sampler in `rq6.py` that must accept a prefix), do not edit it: import what you can and put the extension in `rq8.py`; message `main` with the exact change you would have made. Do not touch any results directory of a previous campaign.

## Base state

`BASE_SHA = 704e27106ddaec32245b19f1c80cb8394a5ab156` on `feature/isal-kb-word`. Your worktree branches from it. Do not rebase, merge, or push. Commit everything on your branch, small conventional commits (`feat(rq8): …`, `feat(rq2-ow): …`, `test(rq8): …`, `docs(rq8): …`); end each commit message with the line `Claude-Session: https://claude.ai/code/session_016rWF7Me4RKWxHHQ1Msi8nF`.

## Frozen contracts (shared with `rq3v2`; do not change)

- Ours is `isal_ow_struct` (`w°`, C++ ordered-walk emitter) at the 60 s budget under the forked-child model of `experiments/tkde/budget.py`; the generator arm is `ow_ngram` (the RQ6 n-gram, same order and smoothing as `rq6.py`); the optional secondary arm is named `ow_gru` and is enabled only under the rule in spec §4.
- Baseline arm names exactly: `fact_ngram`, `incidence_ngram`, `pattern_freq`, `pattern_cooc`, `random_pattern`; non-generative rows (`nauty_cert`, `nauty_cert_rows`, `wl_l1`, `netlsd`, `hpd_jsd`, `bipartite_ged_assign`, `bipartite_ged_path`, `hypercot`, `size_l1`, `degree_seq_l1`) appear in every RQ8 table with the cell "no completion definable".
- Gate G0 `is_star` definition: every fact contains the root constant and no non-root constant appears in ≥ 2 facts; NDC has no root, so a member is a star only if some constant is in every fact and the rest are unshared. `rq3v2` computes its own copy.
- Results roots: drive `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE_ow/{RQ8,RQ2_ow,RQ5_ow}/`; Picasso `${ISALHG_RESULTS_ROOT}=~/results/IEEETKDE_ow` with the same sub-roots. Rows carry the launch tag (T-KBn); a runner must never serve stale rows under a changed arm set.
- Harness: 27 seeds, BCa 95 % CIs, Holm-corrected paired Wilcoxon over seeds, rank-biserial — reuse `experiments/tkde/stats.py`. Splits 80/20 by member, re-drawn per seed; models fit on training words only; no tuning on evaluation units.
- Corpora: the frozen collections through `experiments/tkde/corpora.py` only (`ndc_classes`, `wd50k66`; for RQ2_ow also `ndc_substances`; for RQ5_ow whatever `configs/rq5.yaml` used); counts are the built census (1,381 / 3,988).

## Environment bootstrap (verbatim; the shared env imports the MAIN checkout, not yours)

```bash
git rev-parse --show-toplevel            # must be .claude/worktrees/<...>
conda create -y -n isalhg-rq8 --clone isalhg
~/.conda/envs/isalhg-rq8/bin/pip install -e ".[dev]"     # builds the C++ engine (scikit-build-core + nanobind)
```

From then on run Python only as `~/.conda/envs/isalhg-rq8/bin/python`. Never `pip install` into `~/.conda/envs/isalhg`. If the extension import fails, `rm -rf build` and reinstall. The C++ engine poisons `fork` (T-KBj): use the budgeted forked-child entry points in `budget.py`, never call the engine in the parent before forking workers. If `ow_gru` is enabled, torch is available in the env only if already installed — check; do not add dependencies without messaging `main`.

## Verification commands

```bash
P=~/.conda/envs/isalhg-rq8/bin/python
$P -m pytest tests/experiments_tkde/ -q -x            # record the baseline BEFORE your edits
$P -m pytest tests/experiments_tkde/test_rq8*.py -v
$P -m ruff check src/ tests/ experiments/               # record baseline count; must not grow
$P -m mypy src/isalhg/                                  # record baseline count; must not grow
```

Every regression test you add must be shown failing against the pre-fix behaviour once — state it in the log.

## Data and shared resources

- Local pilot: this workstation, CPU only; ≤ 8 worker processes and ≤ 2 h wall per pilot; `rq3v2` pilots concurrently. Pilot outputs under the drive root (`RQ8/pilot/`), never under `results/IEEETKDE*` of earlier campaigns.
- Picasso: deploy to **your own** repo path and env so `rq3v2` cannot clobber you: `REPO_DIR=~/fscratch/repos/IsalHG-rq8`, `TKDE_CONDA_ENV=isalhg-rq8`, `ISALHG_RESULTS_ROOT=~/results/IEEETKDE_ow` (see `scripts/tkde/sync_to_picasso.sh`, `scripts/tkde/picasso_env_setup.sh`, `slurm/tkde/common.sh` — parameterised by these variables; put the overrides in `slurm/tkde/rq8_sync.sh` rather than editing shared scripts). Frozen corpora and `matrices` on Picasso are shared read-only; symlink `matrices` into the new root (T-KBn precedent). Use the `picasso-sbatch` skill for launcher/worker pairs in the `slurm/tkde/` style (CPU partition; follow `README.md`). Submit only your own jobs; record every job id; do not wait for the queue.

## Definition of done

1. `rq8.py` runs the spec from `configs/rq8.yaml`: units (member, hidden fact) with the interior/pendant rule per stratum, `K⁻` connected (resample rate logged), per-seed 80/20 split, `ow_ngram` fitted on training words and continued from `w°(K⁻)` verbatim, ≥ 1 new fact enforced (R = 20), k = 10 distinct completions by certificate, every baseline of the spec with the stated attachment heuristic, metrics hit@10 / pattern@10 / validity / connectivity per corpus × stratum × hidden-fact kind; rows tagged.
2. `analyze_rq8.py` produces `summary.json`, `stats.json`, `tables.md` with H8.1–H8.3 tested as pre-registered and the fallback printed if triggered; the non-generative rows present with their reason.
3. `RQ8_PILOT.md` holds Prop. C.8 (statement + proof), G0 (both corpora), and G8.1 (3 seeds, 200 interior units per corpus, all arms: hit@10, pattern@10). **Message `main` with the G0 and G8.1 tables before submitting.** If `ow_ngram` ≤ `pattern_cooc` on interior units, enable `ow_gru` per the spec's rule, record the deviation, message `main`, and continue.
4. Tests: unit tests for the unit generator (connectivity, interior/pendant classification, split leakage guard), for Prop. C.8 (decoded completion ⊇ `K⁻` on random continuations, property-style), for each baseline on hand-built cases, for the stale-row guard, and a smoke test in the style of `test_rq36_smoke.py`. Suite green; ruff/mypy baselines matched.
5. The swap: `configs/rq2_ow.yaml` and `configs/rq5_ow.yaml` (with `isal_ow_struct` replacing `wstar_orbit`, everything else identical to `rq2.yaml`/`rq5.yaml`), launchers, a local smoke of each through the existing analyzers, and submission.
6. Picasso: RQ8, RQ2_ow, RQ5_ow synced to your repo path, env built, jobs submitted; job ids in the log and in `rq8_facts.md`.
7. `T-KBaa.md`, `T-KBab.md` written; `rq8_facts.md` skeleton written; work log complete and committed as the final commit; `git status --porcelain` empty.

## Explicitly out of scope

The prose fold (T-KBg); `DEVELOPMENT/README.md` counts (orchestrator at merge); RQ3 v2; any edit to `rq6.py` or `src/`; adding dependencies; waiting for Picasso jobs; any tuning on evaluation units; fixing the RQ6 analyzer's `MODEL_OURS` label (already tracked; do not touch `analyze_rq6.py`).

## Work log — mandatory

Write `.claude/notes/2026-09-13-headline-w0/rq8.md` inside your worktree continuously, from the template at `/home/mpascual/.claude/skills/parallel-agents/assets/note-template.md` (copy it in full; §1 must contain this prompt verbatim). Commit it as your final commit `docs(notes): rq8 work log`. The orchestrator verifies every claim against `git diff` and by re-running your tests.

## Final message format

First line exactly one of: `STATUS: complete` | `STATUS: partial` | `STATUS: blocked`. Then: branch, worktree path, head SHA, env name; what you built in three bullets; the G0 and G8.1 tables (compact); Picasso job ids for RQ8, RQ2_ow, RQ5_ow; anything unfinished or that `main` must decide; the pytest/ruff/mypy result lines.
```

## 2. Understanding and plan

**Restatement of the task in my own words:** Build RQ8, an experiment that hides
one fact from a knowledge base, asks six representations to propose ten
completions, and scores whether the true one is among them — the point being
that only the Isal language can propose *at all*, because the ordered walk's
prefix property makes every continuation a valid connected record. Measure gate
G0 (what fraction of each corpus is a star) and gate G8.1 (the local pilot),
report both to the orchestrator before submitting, and separately re-run RQ2's
census and RQ5's clustering with `isal_ow_struct` in place of `wstar_orbit`.

**Approach chosen:** A single-file runner mirroring `rq1.py`'s idiom (frozen
`Unit`, `run_tag`-scoped row files, `--shard`, `--start-cutoff-epoch`, two G6
tables), with the arm logic factored into small functions so each is testable on
a hand-built record. The analyzer is separate and tests the three hypotheses
exactly as pre-registered, printing the fallback when one fails. The swap is two
YAML files, because both runners read their arm set from configuration.

**Alternatives considered and rejected:**
- Extending `rq6.py`'s completion unit instead of a new runner — rejected:
  `rq6.py` is read-only for me, its completion unit truncates a *fact word* by
  token count rather than hiding a fact, and its `MODEL_OURS` points at the
  retired arm. Reusing it would have inherited the mislabel.
- Scoring hit@10 by word equality rather than by certificate — rejected:
  the emitter places a fact where the walk reaches it, so a correct completion
  appended at the end yields a different word from `w°(K)` while being the same
  knowledge base. Isomorphism is the question; the Theorem C certificate answers
  it in sub-milliseconds.
- Identifying "added facts" by constant id — rejected: only `ow_ngram` is
  prefix-monotone in ids. The multiset difference of fact *patterns* is the one
  definition every arm expresses in the same vocabulary.
- Editing `rq2_launcher.sh` / `rq2_worker.sh` to take the config from the
  environment — rejected: they are shared with the `rq3v2` agent this wave. I
  copied them instead and filed the cleanup in T-KBab (D-KBab2).

**Plan as executed:**
1. Read the design spec in full, then the machinery: `rq6.py`, `ngram.py`,
   `isal_ordered.py`, `ordered_walk.py`, `budget.py`, `stats.py`, `io.py`,
   `corpora.py`, `kb/base.py`, `rq1.py`'s runner idiom, `slurm/tkde/README.md`.
2. Record the pre-edit baselines (pytest / ruff / mypy).
3. Probe G0 and the prefix property on the real corpora *before* writing the
   runner, so the design's premises were checked against data first.
4. Write the runner, config, analyzer; smoke locally; fix what the smoke showed.
5. Write the three test files; demonstrate each regression failing pre-fix.
6. Run gate G8.1; report to `main`; execute the rule that fired.
7. Write the swap configs; smoke each through its unmodified runner.
8. SLURM layer; deploy; `--test-only`; cluster smoke; submit.
9. Docs: pilot doc, facts sheet, two ledger tasks, this log.

**Deviations from the plan:** Three, all forced and all messaged to `main`
when they arose:
- The secondary arm `ow_gru` became `ow_ngram_ho` (no torch; §7).
- The Picasso conda env stayed shared rather than private (§7).
- The Picasso runner tree moved from FSCRATCH to HOME (§7) — FSCRATCH was
  measured read-only.

## 3. Changes made

**Created**

| Path | Purpose |
|---|---|
| `experiments/tkde/rq8.py` | the RQ8 runner: G0 census, unit generator, six arms, scoring, shard driver |
| `experiments/tkde/analyze_rq8.py` | H8.1–H8.3 as pre-registered, the tables, the "no completion definable" rows |
| `experiments/tkde/configs/rq8.yaml` | the campaign: 27 seeds, 81 units, three strata |
| `experiments/tkde/configs/rq8_pilot.yaml` | gate G8.1: 3 off-schedule seeds, 200 interior units/corpus |
| `experiments/tkde/configs/rq2_ow.yaml` | RQ2 with `isal_ow_struct`; experiment `wellposedness_ow` |
| `experiments/tkde/configs/rq5_ow.yaml` | RQ5 with `isal_ow_struct` |
| `tests/experiments_tkde/test_rq8_units.py` | 40 tests: census, interior/pendant, deletion, split leakage, baselines, attachment |
| `tests/experiments_tkde/test_rq8_prefix_property.py` | 13 tests: Proposition C.8, parametrized and under hypothesis |
| `tests/experiments_tkde/test_rq8_smoke.py` | 29 tests: end-to-end runner + analyzer, the stale-row guard, two regressions |
| `slurm/tkde/rq8_worker.sh` | one task, `--constraint=sd`, node staging, in-task analysis |
| `slurm/tkde/rq8_launcher.sh` | count-from-the-decoder, sanitised job id, private deployment |
| `slurm/tkde/rq8_sync.sh` | the deployment wrapper and its two recorded deviations |
| `slurm/tkde/rq2_ow_worker.sh` | RQ2_ow worker (D-KBab2: the shared one hard-codes its config) |
| `slurm/tkde/rq2_ow_launcher.sh` | RQ2_ow launcher, with the matrices-present assertion |
| `slurm/tkde/rq5_ow_launcher.sh` | thin wrapper over the shared RQ5 pair |
| `docs/article/D_ART3/experiments/RQ8_PILOT.md` | Prop. C.8 with proof, gate G0, gate G8.1 |
| `docs/article/D_ART3/foundation/rq8_facts.md` | run roots, job ids, the frozen gate tables, pending harvest |
| `docs/article/DEVELOPMENT/T-KB/IN-PROGRESS/T-KBaa.md` | ledger task for RQ8 |
| `docs/article/DEVELOPMENT/T-KB/IN-PROGRESS/T-KBab.md` | ledger task for the swap |
| `.claude/notes/2026-09-13-headline-w0/rq8.md` | this log |

**Modified**

| Path | Change | Reason |
|---|---|---|
| — | — | No file outside my ownership list was modified. |

**Removed**

| Path | Reason |
|---|---|
| — | Nothing was removed. |

**Commits**

| SHA | Message |
|---|---|
| `14a72c7` | `feat(rq8): valid-completion runner over the ordered-walk prefix property` |
| `45207d5` | `feat(rq8): analyzer with the three pre-registered hypotheses and the blank rows` |
| `eb1c9ec` | `test(rq8): unit generator, Prop. C.8, the baselines, and three regressions` |
| `9840460` | `feat(rq2-ow,rq5-ow): the w-degree swap, and RQ8's SLURM layer` |
| `a5748f2` | `docs(rq8): Prop. C.8, the two gates, and the ledger for T-KBaa / T-KBab` |
| `8f0787b` | `docs(notes): rq8 work log` (first version) |
| `1ff6c90` | `docs(rq8): pre-register Amendment A1 -- the fact-count-matched arms` |
| `107ed20` | `feat(rq8): Amendment A1 -- fact-count-matched arms, and the sign reverses` |
| `5aeee73` | `docs(notes): rq8 work log -- Amendment A1` |
| (this one) | `docs(rq8): the two readings of "matched", and the claim status at hand-off` |

`git diff --name-only 704e271..HEAD` matches the Created table exactly. In
particular `experiments/tkde/rq2.py` and `rq5.py` are **unmodified**: the arm
selection was fully expressible in YAML (D-KBab1), which the brief made the
condition for touching them.

## 4. Tests

**Tests created or extended**

| Test | File | What it verifies | Why it matters |
|---|---|---|---|
| `TestStarCensus` (6) | `test_rq8_units.py` | both clauses of `is_star` separately, the hub root, the census counts | a census that is wrong in one clause silently changes which stratum every claim is about |
| `TestInteriorAndPendant` (4) | `test_rq8_units.py` | a star has no interior fact; a chain's interior is exactly its shared-constant facts | the interior rule decides what H8.1 is stated over |
| `TestDeleteFact` (4) | `test_rq8_units.py` | `K⁻` compacted; a bridge deletion returns `None` | a disconnected `K⁻` has no ordered walk at all (R3) |
| `TestEvalUnits` (6) | `test_rq8_units.py` | stratum rule, connectivity, per-member and total caps, resample accounting | the resample rate is a reported number; it must be the real one |
| `TestSplitLeakage` (6) | `test_rq8_units.py` | train/eval disjoint, covering, deterministic in the seed, redrawn across seeds, every class in training | leakage would make every hit@10 meaningless and would not raise |
| `TestPatternBaselines` (5) | `test_rq8_units.py` | frequency order, co-occurrence conditioning and its fallback, random draws in-vocabulary | a mis-fitted recommender makes the headline look better for the wrong reason |
| `TestAttachment` (8) | `test_rq8_units.py` | root for stars, highest degree otherwise, connectivity, hub fallback, duplicate refusal, rank retry, out-of-range rank | the attachment heuristic IS the mechanism under test |
| `TestPropositionC8` (8) | `test_rq8_prefix_property.py` | prefix reproduces the input; 40 random continuations per base decode, stay connected, contain `K⁻` | this is the theorem the whole exhibit rests on |
| `TestPropositionC8Hypothesis` (1) | `test_rq8_prefix_property.py` | the same under a generated distribution, 60 examples | a parametrized set can miss a shape a generator finds |
| `TestCertificateGuards` (4) | `test_rq8_prefix_property.py` | `None` on disconnected input; agreement on isomorphic, disagreement on non-isomorphic | hit@10 is certificate equality; a wrong certificate is a wrong headline |
| `TestUnitEnumeration` (5+2 param) | `test_rq8_smoke.py` | the stratum × seed grid, uniqueness, shard parsing | a duplicate unit id makes the idempotence check skip real work |
| `TestRunnerEndToEnd` (8) | `test_rq8_smoke.py` | both tables + census written; tagged; ours is `ow_ngram` not `fact_ngram`; ours valid+connected at 1.0; idempotent; sharding covers; declared columns; `--census-only` | the D-ART4 arm-identity contract and the G6 file contract |
| `TestStaleRowGuard` (4) | `test_rq8_smoke.py` | the tag changes with the arm set and not with the shard count; a done unit is not done under another tag; a changed arm set rewrites | T-KBn: RQ3 v1 served rows containing no Isal arm under a manifest claiming otherwise |
| `TestAnalyzer` (5) | `test_rq8_smoke.py` | four artefacts; all three hypotheses reported; a failed headline prints its fallback; the blank rows carry their reason; the secondary-arm flag | L12: a fallback that is not printed is a fallback that is not reported |

**Coverage of the behaviour that matters:** every arm's proposal path, the two
strata, both hidden-fact kinds, the split, the tag, both tables, the analyzer's
three verdicts, and the theorem. The runner is exercised end to end through
`main()` against a real frozen-collection layout written to `tmp_path`, not
through mocked internals.

**Not tested, and why:**
- The 27-seed statistics (`paired_family`, BCa, Holm) are not re-tested here;
  they are `experiments/tkde/stats.py`, already covered by the campaign's own
  suite, and I reuse rather than reimplement them. The analyzer's *call* into
  them is exercised, its numerical correctness is not re-derived.
- The SLURM scripts are syntax-checked (`bash -n`) and exercised by an actual
  cluster job, not unit-tested; there is no harness for that in this repo.
- `ow_ngram_ho` has no arm-specific test beyond the shared dispatch path; it is
  the same `TokenNGram` class at a different order.

## 5. Test results

**Command:** `~/.conda/envs/isalhg-rq8/bin/python -m pytest tests/experiments_tkde/test_rq8_units.py tests/experiments_tkde/test_rq8_prefix_property.py tests/experiments_tkde/test_rq8_smoke.py -q`

```
tests/experiments_tkde/test_rq8_units.py ............................... [ 37%]
.........                                                                [ 48%]
tests/experiments_tkde/test_rq8_prefix_property.py .............         [ 64%]
tests/experiments_tkde/test_rq8_smoke.py .............................   [100%]

82 passed in 1.79s
```

**Result:** 82 passed, 0 failed, 0 skipped · **Duration:** 1.79 s · **Run at:** `9840460`

Re-run at the final head (after the doc commit `a5748f2`): **82 passed in 2.68 s**.
After Amendment A1 (`107ed20`), with the 11 new one-fact tests: **93 passed in
1.64 s**. ruff and mypy still at 38 / 20.

**Amendment A1's regression, shown failing against the pre-amendment
behaviour.** A scratch pytest plugin restored the old acceptance
(`Δfacts ≥ 1` for every arm) and the old unrestricted attach-miss denominator:

```
7 failed, 4 passed, 40 deselected
FAILED ...::test_a_multi_fact_proposal_is_never_accepted_by_the_1f_arm[2]
FAILED ...::test_a_multi_fact_proposal_is_never_accepted_by_the_1f_arm[3]
FAILED ...::test_a_multi_fact_proposal_is_never_accepted_by_the_1f_arm[5]
FAILED ...::test_a_multi_fact_proposal_is_never_accepted_by_the_1f_arm[35]
FAILED ...::test_collect_under_the_1f_rule_returns_only_one_fact_proposals
FAILED ...::test_the_1f_budget_is_the_same_R_and_a_slot_may_go_unfilled
FAILED ...::test_scoring_restricts_the_attach_miss_denominator_to_one_fact
E   assert True is False  # pattern_hit_1f on a three-fact proposal
```

**Whole-directory run, and the pre-existing failures.**
`python -m pytest tests/experiments_tkde/ -q` at **BASE_SHA, before any edit of
mine**:

```
6 failed, 484 passed in 414.41s
FAILED test_rq36_smoke.py::TestUnitEnumeration::test_rq6_units_are_unique
FAILED test_rq36_smoke.py::TestModelIsNotSharedAcrossUnits::test_each_call_returns_a_fresh_model
FAILED test_rq36_smoke.py::TestModelIsNotSharedAcrossUnits::test_the_fresh_model_samples_identically
FAILED test_rq36_smoke.py::TestModelIsNotSharedAcrossUnits::test_a_used_model_is_not_reachable_from_the_context
FAILED test_rq36_smoke.py::TestDeployStamps::test_the_stamps_name_the_imported_package
FAILED test_rq45_smoke.py::TestSmokeIsolation::test_deploy_stamps_name_both_trees
```

**The same whole-directory run repeated at head** (`9840460`, after all code was
committed):

```
6 failed, 566 passed in 435.29s (0:07:15)
```

with the **identical six failures**, name for name. The delta against the
baseline is therefore exactly `+82 passed, +0 failed` — my 82 tests, and nothing
else moved. (While this run was in flight its output looked stuck at 40 % for
several minutes; that was pytest's own buffering under load, not a hang. I had
written a note here saying I could not confirm the summary line; the line then
arrived and this is it.)

These are **not mine**. `test_rq6_units_are_unique` asserts
`2*2*4 + 1 + 2*2 = 21` units while `rq6.SAMPLE_MODELS` now holds three models
and produces 29; the two `DeployStamps` tests assert an exact key set that
`rq1.deploy_stamps` has since widened with `isalhg_path` / `isalhg_git_sha`.
Both are stale assertions against `rq6.py` / `rq1.py`, which are read-only for
me and out of scope. Recorded here as a follow-up (§10), not fixed.

**Failures and their resolution (mine):** one, during development.
`TestAttachment::test_an_attachment_reproducing_an_existing_fact_is_refused`
failed on its first write because I had assumed the star's own pattern would
attach to a *different* leaf; it does not — the heuristic is deterministic and
resolves to the existing fact. That is the correct behaviour, so the test was
rewritten to assert it, and the observation produced the `rank` retry that keeps
a deterministic heuristic from wasting the recommender's slot. Green after.

**Lint and types**

```
ruff check src/ tests/ experiments/  ->  Found 38 errors.   (baseline: 38)
mypy src/isalhg/                     ->  Found 20 errors in 6 files (baseline: 20)
```

Neither grew. `ruff check experiments/tkde/rq8.py` and `analyze_rq8.py`
individually report "All checks passed", so my files contribute zero of the 38.

**Regressions shown failing against the pre-fix behaviour** (each restored by a
pytest plugin in the scratchpad that monkeypatches the old behaviour; not
committed):

| test | pre-fix behaviour restored | observed failure |
|---|---|---|
| `test_a_counting_arm_never_reports_a_decode_failure` | a refused attachment recorded as an invalid proposal | `AssertionError: assert 0.5 == 1.0` |
| `test_a_changed_arm_set_reruns_rather_than_resuming` | untagged row file names | `AssertionError: a changed arm set must write new row files; assert set()` |
| `test_the_incidence_baseline_rejects_some_of_its_own_samples` | the `("END",)` terminator kept in the prefix | on the synthetic smoke collection the test still passed, so it was demonstrated on the real corpus instead: `ndc_classes` incidence validity **1.0000 with the terminator, 0.1718 without** — the predicate `validity < 1.0` is False pre-fix and True post-fix |

## 6. Verification beyond unit tests

| Circumstance | What was run | Evidence | Outcome |
|---|---|---|---|
| Real data — G0 | census over both frozen corpora | `ndc_classes` 1,381 members / 42 stars (0.0304); `wd50k66` 3,988 / 2,128 (0.5336); pools at `m ≥ 4` of 522 and 2,775 | pass; agrees to the member with `rq3v2`'s independent copy |
| Real data — Prop. C.8 | 25 members × 8 continuations × 2 corpora | 400/400 decoded, connected, ⊇ `K⁻`; 0 failures | pass |
| Real data — gate G8.1 | 3 seeds × 200 interior units × 2 corpora × 7 arms | the table in `RQ8_PILOT.md` §3; `ow_ngram` validity and connectivity 1.0000 on both corpora across all 600 unit-arm observations | ran; H8.1 **not supported** (§7) |
| Real data — RQ2_ow | `--smoke` through the unmodified `rq2.py` | `isal_ow_struct` in exact0 and census; `wstar_orbit` **0 matches** in the whole log | pass |
| Real data — RQ5_ow | unit 11 through the unmodified `rq5.py` | 22 clustering rows, 11 arms, `isal_ow_struct` present, `wstar_orbit` absent | pass |
| Edge cases | empty record has no root; singleton class survives the split; out-of-range attachment rank clamps; disconnected input has no certificate | all asserted in the suite | pass |
| Failure paths | bridge deletion → `None`; stratum below `min_pool` → logged warning and an empty unit; a stratum with no surviving eval unit → `RQ8Error` | exercised | pass |
| Scale / performance | local pilot, i7-13700KF: 5.6–7.6 s per `ndc_classes` unit, 8.3–9.4 s per `wd50k66` unit at 200 eval units × 6 arms. Picasso `sd` node: ~13 s per unit, MaxRSS **6.78 MB** on the smoke against a 32 G request | 81-unit campaign ≈ 18 min | pass; the memory request is 3 orders too generous (§10) |
| Environment | Debian 12; `isalhg-rq8` cloned from `isalhg`, `pip install -e ".[dev]"`; Python 3.11.15; C++ extension at `~/.conda/envs/isalhg-rq8/lib/python3.11/site-packages/isalhg/core/_core.cpython-311-x86_64-linux-gnu.so`; ordered-walk backends `['cpp', 'python']`; **torch NOT installed** | | the torch absence forced the `ow_gru` substitution |
| Cluster | job 2308337, the real `--smoke` on `sd` | COMPLETED 00:05:08; both tree assertions passed (`experiments -> ~/repos/IsalHG-rq8/...`, `isalhg -> /mnt2/fscratch/.../IsalHG-tkde/...`); 5 row files; `[stage] copy-back OK` | pass |

## 7. Decisions, assumptions, open questions

**Decisions with a real trade-off:**

- **`ow_ngram_ho` replaces the design's `ow_gru`.** Costs a departure from a
  pre-registered arm name; buys not adding torch, which the brief forbade. Same
  model class, same smoothing, same training words, order 6 instead of 3; and it
  was written into the config and the pilot doc *before* being measured, so it
  cannot read as post hoc. Orchestrator-ruled.
- **Shared conda env on Picasso instead of a private one.** Costs a deviation
  from my brief; buys not breaking `rq5_worker.sh`'s
  `assert "IsalHG-tkde" in isalhg.__file__` and not rebuilding an identical
  extension. `common.sh` documents that `isalhg.*` resolves through the env's
  PEP 660 finder while `PYTHONPATH` only moves `experiments.*`, so the isolation
  the brief wanted is the private `REPO_DIR`, which I do use.
  **If a future wave touches `src/**` this no longer holds.** Approved.
- **Runner tree on HOME, not FSCRATCH.** Costs ~900 files of HOME's 35.0k
  quota and contradicts `slurm/tkde/README.md`; buys being able to deploy at
  all. FSCRATCH measured 276.3k files / 250.0k soft with the **grace expired**,
  i.e. read-only: `mkdir ~/fscratch/repos/...` returned "Disk quota exceeded".
  The README's rule assumes HOME's file quota is the scarce one; the measured
  state is the reverse. Approved; same ruling given to `rq3v2`.
- **`rq2_ow_worker.sh` is a copy, not a wrapper.** Costs a duplicated file;
  buys not editing `rq2_worker.sh`, which `rq3v2` also runs off this wave. The
  cleanup (parameterise the shared pair by `RQ2_CONFIG`, delete the copies) is
  filed in T-KBab D-KBab2.
- **The attachment heuristic retries one rank down and anchors on the hub.**
  Costs a small departure from the spec's bare wording; buys a baseline that is
  not handicapped by my construction (L12). Without the retry a deterministic
  heuristic emits at most one proposal per pattern and caps the recommender
  below `k`; without the hub anchor a pattern with no matching type would score
  the recommender's connectivity rather than its recommendation. Both strengthen
  the baseline, never ours — and the baseline then beat us.
- **The incidence prefix drops `("END",)`; every completion may run
  `max_new_tokens` past the prefix.** Both are harness corrections, both change
  a reported column, both are pinned by regression tests and documented in the
  source and the pilot doc.

**The measured correction the orchestrator asked me to record verbatim, and its
subsequent reversal.**

I first recorded, as instructed:

> The mechanism in the design doc's §0 — "the generator learns attachments and
> counting cannot" — was **contradicted by measurement**.

**That is now withdrawn, and the sign is the other way.** An independent
read-only review of `rq8.attach` found the reason: a counting arm adds exactly
one fact by construction, while only **31.6 %** of `ow_ngram`'s accepted
proposals do (607/1,923; median 2, max 35). So two thirds of ours' ten slots
went on proposals that could not be a hit, and a proposal carrying the right
pattern *plus two unrelated facts* was scored as an **attachment** miss. The
denominator was not comparable between arms.

Amendment A1 (pre-registered in commit `1ff6c90`, **before** any new number)
added the fact-count-matched arms and re-measured on the same three seeds. On
that denominator:

| `ndc_classes` interior | attach-miss ∣ one-fact |
|---|---|
| `ow_ngram` | 0.347 |
| `ow_ngram_1f` | 0.393 |
| `ow_ngram_ho` | 0.303 |
| `ow_ngram_ho_1f` | 0.346 |
| `pattern_cooc` | **0.660** |
| `pattern_freq` | **0.576** |

Every ordered-walk arm attaches **better** than either recommender, and on
`wd50k66` too (0.871/0.874 against 0.981/0.986). **§0's mechanism is supported.**
The `ndc_classes` loss is entirely a pattern-prediction loss and a *larger* one
than the free-running table showed — matched `pattern@10` 0.288 against 0.892,
because a free-running proposal's extra facts were incidentally covering the
hidden pattern.

Matching also moves the headline numbers: `hit@10` 0.1067 → **0.1750** on
`ndc_classes` (0.1950 for `ow_ngram_ho_1f`, above `pattern_freq`'s 0.1867) and
0.0150 → **0.0383** on `wd50k66`, where the matched arm **leads every baseline**
including `pattern_cooc` at 0.0133. **H8.1 still fails**, now as a scoped
failure — satisfied on `wd50k66`, not on `ndc_classes` — so the fallback stands
and RQ8 remains a supporting exhibit. 27 seeds decide whether the `wd50k66`
lead survives Holm.

Two readings of "matched", and why mine beats the review's counterfactual. A
re-read of the *original* draws gives `hit@10` **0.100**; the pre-registered
re-draw rule — first ten distinct one-fact proposals under the **unchanged**
`R = 20` per slot, so a rejected multi-fact draw costs an attempt and the arm
keeps drawing — gives **0.175**, at the price shown in the `acc` column (matched
arms fill 5.8–8.7 slots of ten against the free-running 7.9–9.8). The re-draw
rule is what was written down before the numbers were seen, so it is what is
reported; unfilled slots are stated, never bought back. I offered to add the
review's stricter reading as a third arm; the orchestrator declined and asked
for both figures in one sentence of the pilot doc instead, which is there.

**Status of each claim at hand-off, as ruled:** the attachment mechanism is
**supported**; the `ndc_classes` deficit is a **pattern gap**; the `wd50k66`
lead is **untested** until Holm at 27 seeds and must not be quoted before then.

**Assumptions I proceeded on (each messaged to `main` when made):**
- The root is the hub (max fact-degree, ties by smallest id), since the frozen
  records carry no root. Breaks nothing in G0 (on a star the hub *is* the
  every-fact constant); it only qualifies "non-root" in the interior rule.
  Accepted by the orchestrator.
- "Fitted on training words only" means the training split of the substrate
  pool, not the whole collection minus the eval split. Symmetric across arms and
  strata, and no eval member's word is ever seen.
- "At least one new fact" is tested as `|facts(proposal)| > |facts(K⁻)|` —
  arm-neutral, and for `ow_ngram` equivalent by Prop. C.8.
- The RQ2_ow census may write `ndc_substances` matrices through the shared
  symlink. Intended: that matrix belongs in the shared cache. Stated in the
  launcher.

**Open questions for the orchestrator:**
- H8.3's third clause (`incidence_ngram` validity < 0.05) is **inapplicable to a
  conditional experiment** and I reported it failed rather than moving it. If
  the design should instead be amended, that is a pre-registration edit and
  yours to make.
- RQ8 is now a supporting exhibit. If RQ3 v2 also misses, the paper is down to
  RQ6 plus the capability table — a scope question I surfaced but did not act
  on.

## 8. Coordination

**Messages sent** (7, to `main`):
1. Check-in: worktree, branch, BASE_SHA, model/effort. Acknowledged.
2. Gate G0 + the Prop. C.8 pre-check, plus the torch absence flagged early.
   Accepted; the root convention and the "NDC star stratum not reportable"
   treatment were ruled on; `ow_gru` → `ow_ngram_ho` decided *before* G8.1 so it
   was pre-registered rather than post hoc.
3. Gate G8.1 with the full table, H8.1's failure, the contradicted mechanism,
   the H8.3 clause, and a recommendation to submit anyway. Five rulings back.
4. The `ow_ngram_ho` row and the confirmation that hit@10 is already usable@10
   by construction; plus the request to approve the shared-env deployment.
   Both accepted.
5. The FSCRATCH blocker, with the measured quota and the probe output, flagged
   as also blocking `rq3v2`, and my proposed HOME workaround. Approved; the
   same ruling was given to `rq3v2`.
6. Job ids for all five submissions, the write audit result, and the memory
   over-request note.

**Messages received and how they changed the work:**
- "Make sure ours is `ow_ngram`, not the RQ6 `MODEL_OURS`" → `ARM_OURS` is a
  module constant, asserted by `test_ours_is_scored_and_is_not_fact_ngram`, and
  `analyze_rq8.py` imports it rather than re-deriving.
- "G8.1 must run on a seed you then discard" → `seed_offset` was added to the
  runner and the pilot config runs 80900–80902.
- "`ow_gru` is replaced by `ow_ngram_ho`" → written into `configs/rq8.yaml`,
  `rq8.py` and the pilot doc before the second pilot pass.
- "Measure pattern-right-attachment-wrong directly" → it is a row column
  (`n_pattern_hit_attach_miss`), an analyzer table, and the number that
  falsified §0.
- "Add `usable@10`" → verified it was already the implemented semantics; renamed
  the header and documented it rather than adding a duplicate column.
- "Confirm nothing writes to FSCRATCH at run time" → audited `common.sh` and
  measured `TMPDIR` / `LOCALSCRATCH` on the cluster before submitting.

**Contracts I depend on and confirmed unchanged:** `experiments/tkde/stats.py`
(`paired_family`, `bca_ci`, `wilcoxon_paired`), `io.py`'s six-file G6 layout,
`rq1.run_tag` / `table_file`, `analyze_rq1.load_table`'s tag-and-`_smoke`
filtering, `corpora.load_collection`, `isal_ordered.ordered_fingerprint`,
`generation.ngram.TokenNGram`, `slurm/tkde/common.sh`. None modified.

## 9. Deliberately not done

- The prose fold (T-KBg) — out of scope; D-KBaa2/3/4 are written so it can be
  done from the ledger.
- `DEVELOPMENT/README.md` scope counts — the orchestrator's, at merge.
- The six pre-existing test failures in `test_rq36_smoke.py` /
  `test_rq45_smoke.py` — they are at BASE_SHA, in read-only files, and fixing
  them would have mixed an unrelated repair into this wave's diff.
- `analyze_rq6.py`'s `MODEL_OURS` mislabel — explicitly out of scope and already
  tracked in T-KBf.
- Waiting on the queue, per the brief. Job states at hand-off are in §6.
- Anything on Picasso's FSCRATCH. I did not delete a file there, and I did not
  contact SCBI: both are the user's decisions and the orchestrator is surfacing
  them.

## 10. Risks and follow-ups

| Item | Severity | Detail | Suggested owner |
|---|---|---|---|
| The `wd50k66` matched lead is untested | medium | `ow_ngram_1f` 0.0383 against `pattern_cooc` 0.0133 is the one place ours wins, and three pilot seeds cannot test it. Job 2308489 supplies the 27-seed Holm comparison; until then the number must not be quoted as a result. | orchestrator, at harvest |
| Two RQ8 campaigns now exist on disk | low | 2308339 (free-running, COMPLETED) and 2308489 (Amendment A1, nine arms). Different run tags, so neither overwrites the other, and the paper reports both. Do not merge them into one table. | orchestrator |
| FSCRATCH is read-only for this account | **high** | 276.3k/250.0k files, grace expired. Every future deployment fails the same way, and any job that *writes* there mid-run would die. This wave works around it; the account state is unresolved. | user (via orchestrator) |
| 6 pre-existing test failures | medium | `test_rq36_smoke.py` (5) and `test_rq45_smoke.py` (1), stale assertions against `rq6.SAMPLE_MODELS` (21 vs 29 units) and the widened `rq1.deploy_stamps` key set. Present at BASE_SHA. | next wave |
| RQ8's `--mem=32G` is ~3 orders too large | low | Smoke MaxRSS 6.78 MB. Over-requesting costs queue time; I left it because the campaign is already placed. Read the real figure off job 2308339's `.batch` step and size the next run from it. | next wave |
| `rq2_ow_{launcher,worker}.sh` duplicate the shared pair | low | Only because the shared pair hard-codes its config. Parameterise it by `RQ2_CONFIG` and delete the copies. | next wave |
| H8.3's third clause is mis-specified | medium | The 0.05 ceiling is an RQ6 number and does not transfer to conditional completion. Reported failed rather than moved; the design should be amended. | orchestrator |
| The shared-env decision is not a standing licence | medium | It holds only while a wave changes nothing under `src/**`. `rq8_sync.sh` says so in a comment; a wave that touches `src/` must reopen it. | future waves |

## 11. Self-assessment against the definition of done

| # | Criterion | Met | Evidence |
|---|---|---|---|
| 1 | `rq8.py` runs the spec: units with the interior/pendant rule, connected `K⁻` with the resample rate logged, per-seed 80/20 split, `ow_ngram` on training words continued verbatim, ≥ 1 new fact at R = 20, k = 10 deduped by certificate, every baseline with the stated heuristic, the four metrics per corpus × stratum × kind, rows tagged | yes | `test_rq8_units.py` (40), `test_rq8_smoke.py::TestRunnerEndToEnd` (8), `resample_rate` column, gate G8.1 ran the whole thing on real data |
| 2 | `analyze_rq8.py` writes `summary.json` / `stats.json` / `tables.md`, tests H8.1–H8.3 as pre-registered, prints the fallback, carries the non-generative rows | yes | `TestAnalyzer` (5); the pilot's own run printed the H8.1 fallback |
| 3 | `RQ8_PILOT.md` holds Prop. C.8 + proof, G0 both corpora, G8.1 3 seeds × 200 interior units × all arms; **G0 and G8.1 messaged to `main` before submitting**; the `ow_gru` rule executed and the deviation recorded | yes | the file; messages 2 and 3, both answered before any submission; `ow_ngram_ho` in the config, the pilot doc and T-KBaa D-KBaa1 |
| 4 | Tests for the unit generator, Prop. C.8 property-style, each baseline on hand-built cases, the stale-row guard, an end-to-end smoke; suite green; ruff/mypy baselines matched | yes | 82 passed; whole directory at head 6 failed / 566 passed against a baseline of 6 failed / 484 passed — same six names, delta `+82 passed, +0 failed`; ruff 38 = 38, mypy 20 = 20; three regressions shown failing pre-fix (§5) |
| 5 | `configs/rq2_ow.yaml` and `rq5_ow.yaml` identical but for the arm; launchers; a local smoke of each through the existing analyzers; submitted | yes | both smokes verified `isal_ow_struct` present and `wstar_orbit` absent; jobs 2308342 / 2308343 / 2308368 |
| 6 | Synced to my own repo path, env, jobs submitted, ids in the log and in `rq8_facts.md` | yes, with two approved deviations | HOME path instead of FSCRATCH (forced, approved); shared env instead of private (approved, with reason). Ids in §6, in `rq8_facts.md` §2 and in message 6 |
| 7 | `T-KBaa.md`, `T-KBab.md`, `rq8_facts.md`, this log committed last; `git status --porcelain` empty | yes | all four written; this is the final commit |

**Harvest addendum (2026-09-14) — the campaigns, and two things I got wrong.**

*What landed.* RQ8 both campaigns COMPLETED (2308339 free-running tag
`b327d7c5`; 2308489 Amendment A1 tag `c5380cde`), 81 units each at 27 seeds,
counts verified against the config. RQ5_ow COMPLETED (2308368, 65 units). Full
numbers in `foundation/rq8_facts.md` and `rq5_ow_facts.md`.

*The result.* H8.1 as pre-registered still fails on both corpora — the pilot was
right at power. But the **matched arms win `wd50k66` Holm-clean**:
`ow_ngram_1f` 0.0463 and `ow_ngram_ho_1f` 0.0481 beat all five baselines
including `pattern_cooc` (0.0185), every `p_Holm` ≈ 1.3e-05, rank-biserial
+0.989 / +1.000. And the §0 attachment mechanism is **confirmed at power**:
every ordered-walk arm attaches better than either recommender on both corpora
(0.256–0.373 vs 0.643/0.586 on NDC; 0.845/0.854 vs 0.974/0.979 on WD50K). The
Amendment A1 reversal holds.

*Amendment A2 — the star control was a hole in my own baseline, and repairing
it turned a non-result into the cleanest result in RQ8.* `pattern_cooc` scored
**exactly 0.0000** on stars because a star's facts share patterns, the
deterministic attachment then reproduced an existing fact, and the proposal was
refused — the baseline could not express "another instance of a repeated
pattern", which is precisely what a star completion is. Pre-registered the fix
(instantiate over fresh constants, pendant to the hub), re-ran the 27 star units
under tag `7f25205b`, merged by stratum under a duplicate-key guard.

The amendment is its own control: **every ours-arm is byte-identical before and
after**, so the fallback touched only what it was meant to. `pattern_cooc` rose
0.0000 → 0.0404. **Ours still leads**: 0.1156 free-running, 0.1846 matched,
p = 5.5e-06, rank-biserial +1.000. Per the pre-registration that makes it a
result, and it contradicts design §0's expectation that counting ties or wins on
stars.

The decomposition is the best evidence in the whole task for §0's mechanism: the
recommender gets the **pattern** right 2.3× as often (0.6243 vs 0.2719) and
still loses 2.9×, because its attach-miss is **0.935** while ours is **exactly
0.000** over 624–997 one-fact opportunities per arm. A pendant completion
emitted by the ordered walk chains its new constant onto the placed frontier by
construction, so the attachment cannot be wrong — `ow_ngram_1f`'s `pattern@10`
and `hit@10` are literally the same number.

I should have caught the 0.0000 myself when I first reported it. I flagged it as
a caveat and moved on; the orchestrator was right that a baseline scoring exactly
zero across 27 seeds is a hole, not a control.

*Mistake 1 — RQ2_ow lost every row, and it was my defect.* 22 tasks, all
logging "copy-back OK", 21 `COMPLETED`, **zero rows**. `rq2.py` line 997 builds
its path from the module constant `EXPERIMENT`, never from the config key; my
worker had renamed the experiment for subtree separation, so the runner wrote to
plain node scratch outside the mirrored tree and the copy-back faithfully
mirrored an empty directory. ~7 wall-hours. This is the defect
`slurm/tkde/README.md` already documents for the 2026-09-07 rank run — I read
that paragraph and reintroduced it anyway, which is precisely the argument for a
mechanical guard over a documented caution. Separation never needed the rename:
the results root and the run tag already differ.

*Mistake 2 — my fix's guard was itself a false positive.* The re-submission
failed all 22 tasks in seconds because I compared `readlink -f` of the symlink
(canonical) against the raw `${MYLOCALSCRATCH}/out`, and Picasso exports
`LOCALSCRATCH` with a trailing slash. Both sides are canonicalised now. It cost
seconds instead of hours, which is the guard behaving correctly while being
wrong — but it was still wrong, and I should have reproduced the path shapes
before submitting rather than after.

*Two analyzer corrections, both about not fooling myself.* Both campaigns share
a directory and `load_table` concatenates every tagged file, so reading them
together **silently pooled two measurements of overlapping arms**; `--run-tag`
is now required when several are present. And the Holm family was including
`ow_ngram_1f` / `ow_ngram_ho*` as *competitors* — inflating the correction and
scoring our own arms against each other. The family is now ours against the
baselines only.

*One thing the brief asked for that does not exist.* `wstar_orbit` appears in
**0 of 54** campaign RQ5 row files although `rq5.yaml` lists it in all three
experiments, so the requested `w°`-vs-orbit RQ5 comparison cannot be made. I
recomputed the whole field from the campaign's own rows instead; every shared
arm reproduces to four decimals, which is a stronger check than the missing
single-arm delta would have been.

**Post-review addendum (Amendment A1).** An independent read-only review found
the one thing I had not: `rq8.attach` is sound and the evaluation is symmetric,
but the *arms* were not fact-count matched, and my attachment sentence was
computed on an incomparable denominator. I had flagged `attach` as the thing to
scrutinise first; the defect was one level up, in what I compared it against.
The amendment was pre-registered before re-measurement, the matched arms were
added under an unchanged `R`, and the conclusion reversed: the ordered-walk
arms attach **better** than the recommenders, the `ndc_classes` loss is purely
a pattern gap, and on `wd50k66` the matched arm leads every baseline. H8.1 still
fails and RQ8 remains a supporting exhibit. Job 2308339 had already COMPLETED
(81/81 units) so nothing was cancelled; the amended campaign is **2308489**
under its own run tag, and both sit on disk as the free-running and the matched
measurement.

**Overall.** I am confident in the engineering and in the measurements, and the
headline claim is the part that did not survive them. The runner, the analyzer
and the 82 tests do what the spec asks; Proposition C.8 is proved, pinned by a
property test, and independently confirmed on 400 real continuations and again
on every `ow_ngram` unit of the pilot at validity and connectivity 1.000. The
two gates are measured on real corpora and G0 cross-checks to the member with
the peer agent. What I am *not* confident about — and reported as soon as I saw
it — is the pre-registered headline: `pattern_cooc` beats `ow_ngram` 0.3033 to
0.1067 on the corpus the design nominated, the §0 attachment mechanism is
contradicted by direct measurement rather than merely unconfirmed, and the
higher-order arm closes a sixth of the gap on one corpus and nothing on the
other. The fallback applies and RQ8 is a supporting exhibit.

**What the orchestrator should scrutinise first**, in order: (1) the attachment
heuristic in `rq8.attach` — it is the baseline's whole strength, I deliberately
made it stronger twice, and it then beat us, so if it is *unfairly* strong the
headline verdict changes; (2) the H8.3 clause-3 decision, which is a
pre-registration question and not mine; (3) the `[:-1]` on the incidence prefix,
which moved a reported column from 1.0000 to 0.1718 and whose justification is
an argument, not a theorem.
