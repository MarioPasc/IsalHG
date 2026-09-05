# Wave summary — 2026-09-05-tkde-w3

<!--
Location: <REPO_ROOT>/.claude/notes/2026-09-05-tkde-w3/summary.md
Written by the orchestrator after integration. Append a new entry if this file already exists;
never overwrite a previous wave's record.
-->

**Date:** 2026-09-05 (wave started ~19:00 CEST by the previous orchestrator session; agents
killed by an API rate limit ~22:30; resumed by replacement agents from 23:00; integration
23:20–23:55 CEST the same day)
**Wave:** `2026-09-05-tkde-w3`
**Base commit:** `2e7d811` — wave-2 integration head at the time of the spawn
**Target branch:** `main` (untouched at `ccf6dd0`) · **Integration branch:**
`integration/2026-09-05-tkde-w1` (all three waves land here; merge into `main` awaits the user)
**Orchestrator model / effort:** `claude-fable-5-1` / `high` (this session; the previous
session that designed and spawned the wave ran Opus 5 at `xhigh`)

## Original prompt

The wave-3 prompts were written by the previous orchestrator session and are pasted verbatim
in §1 of each agent log in this directory. The user's overall brief for the campaign is
quoted verbatim in `docs/article/D_ART3/experiments/HANDOFF_2026-09-05.md` §0. The
instruction that governed this session's continuation:

```
You are the experimental orchestrator of the IEEE TKDE article for IsalHG ("knowledge bases as
words"). You continue the work of a previous orchestrator session that designed the experiments,
ran two implementation waves to completion and had the third wave (the seven experiment runners
and their Picasso jobs) in flight when its three agents were terminated by an API session rate
limit [...]. Your job is to finish wave 3, run the campaign on Picasso, harvest to the local
drive, and then do the interpretation pass. [...] 2 subagents max
```

## Decomposition

The seven experiments (RQ1–RQ7 of `docs/article/D_ART3/experiments/DESIGN.md`) were split
across three agents by shared infrastructure rather than by RQ number: `rq-4-5` owns the
cached distance matrices (built once, read by RQ2's census, RQ4 and RQ5); `rq-3-6` owns the
language-layer experiments (RQ3 consensus, RQ6 generation) and writes RQ2's certificate rows
as a by-product of RQ3; `rq-1-2-7` owns the addressing / well-posedness / envelope
experiments that need the process-level budget helper. Ownership is disjoint at the file
level (`experiments/tkde/rq<N>.py`, `analyze_rq<N>.py`, `configs/rq<N>.yaml`,
`slurm/tkde/rq<N>_*.sh`, one smoke-test module each). Two contracts crossed agents and were
frozen in the prompts: the matrix-cache layout (`matrices/<collection>/<arm>.npy`, keyed by
`isalhg.metric_space.toolkit.matrix.cache_paths` / `member_order_sha1`) and the certificate
file `RQ2_wellposedness/certificate_validity/rows_certificate.csv`.

The replacement agents of this session continued on the original worktrees, branches, cloned
envs and private Picasso deployments (`~/fscratch/repos/IsalHG-tkde-<slug>`), committing the
predecessors' uncommitted work first. Two post-wave fix agents were added when defects
surfaced outside any agent's ownership: `hpd-fix` (a vendored competitor crashed on corrupted
inputs) and, after the merges, `common-sync` (centralise the duplicated SLURM helper) and
`ngram-cache` (the library-side memory leak behind the RQ6 OOM).

**Deferred to a later wave:** the HPD refill of RQ4 (`rq4 --refill-censored-arm hpd_jsd`)
after the fixed `src/` is synced to the shared Picasso checkout; the interpretation pass for
RQ1/RQ2/RQ4/RQ5/RQ7 once their campaigns complete (RQ3 and RQ6 are decided, see
`results/IEEETKDE/DECISIONS.md`).

## Agents

| Agent | Mission | Model / effort | Branch | Head | Verdict | Log |
|---|---|---|---|---|---|---|
| `rq-1-2-7` (replacement) | RQ1 addressing, RQ2 well-posedness, RQ7 envelope: runners, analyzers, SLURM; submit | `claude-opus-5` / `xhigh` | `worktree-agent-a1401be85ab17a08d` | `2437643` | ACCEPT | [`rq-1-2-7.md`](./rq-1-2-7.md) |
| `rq-3-6` (replacement) | RQ3 representative, RQ6 generation, RQ2 certificate rows; OOM diagnosis + resubmission | `claude-opus-5` / `xhigh` | `worktree-agent-a30b6439b4518d41a` | `86c1c3c` | ACCEPT | [`rq-3-6.md`](./rq-3-6.md) |
| `rq-4-5` (replacement) | matrices job, RQ4 screen, RQ5 patterns; censored arms; refill mode | `claude-opus-5` / `high` | `worktree-agent-a275053d6dad23593` | `70bef32` | ACCEPT | [`rq-4-5.md`](./rq-4-5.md) |
| `hpd-fix` | vendored HPD `IndexError` on single-hyperedge inputs | `claude-opus-5` / `high` | `worktree-agent-ab2a7d8f76f4c34bf` | `2413abf` | ACCEPT | [`hpd-fix.md`](./hpd-fix.md) |
| `common-sync` | centralise `tkde_run_synced` into `common.sh`; fix the PYTHONPATH claim; document contracts | `claude-opus-5` / `high` | `worktree-agent-a4654a7c8320da94d` | `d2a9f26` | ACCEPT | [`common-sync.md`](./common-sync.md) |
| `ngram-cache` | bound `TokenNGram._distribution` memo (the RQ6 OOM) | `claude-opus-5` / `high` | `worktree-agent-a3554e620c7eb2d0d` | `b3a396c` | ACCEPT | [`ngram-cache.md`](./ngram-cache.md) |

**Ownership map**

| Agent | Owned paths |
|---|---|
| `rq-1-2-7` | `experiments/tkde/{budget,rq1,rq2,rq7,analyze_rq1,analyze_rq2,analyze_rq7}.py`, `experiments/tkde/configs/rq{1,2,7}.yaml`, `slurm/tkde/rq{1,2,7}_*.sh`, `tests/experiments_tkde/test_rq127_smoke.py` |
| `rq-3-6` | `experiments/tkde/{rq3,rq6,analyze_rq3,analyze_rq6}.py`, `experiments/tkde/configs/rq{3,6}.yaml`, `slurm/tkde/rq{3,6}_*.sh`, `tests/experiments_tkde/test_rq36_smoke.py` |
| `rq-4-5` | `experiments/tkde/{matrices,rq4,rq5,analyze_rq4,analyze_rq5}.py`, `experiments/tkde/configs/{matrices,rq4,rq5}.yaml`, `slurm/tkde/{matrices,rq4,rq5}_*.sh`, `tests/experiments_tkde/test_rq45_smoke.py` |
| `hpd-fix` | `src/isalhg/metric_space/representations/_hpd_vendor.py`, `tests/unit/metric_space/test_hpd_single_hyperedge.py` |
| `common-sync` | `slurm/tkde/common.sh`, `slurm/tkde/*_worker.sh`, `slurm/tkde/README.md`, `docs/article/D_ART3/experiments/PICASSO.md` |
| `ngram-cache` | `src/isalhg/generation/ngram.py`, `tests/unit/generation/test_ngram*.py` |

## Review findings

### `rq-1-2-7` — ACCEPT
- **Claimed:** runners + analyzers for RQ1/RQ2/RQ7; run-tagged row files; backgrounded synced
  payload; a launcher defect fixed (`--count` ran from `slurm/tkde`, where `experiments` is not
  importable, so no array had ever been sized); the predecessor's log corrected by a dated
  erratum (it claimed commits and full jobs that never existed); campaign submitted.
- **Verified:** tree clean; 5 commits on top of `458a3d8`, all descending from `2e7d811`;
  18 files, all inside ownership; 128 tests pass in `isalhg-rq127` (161 s); ruff clean;
  `bash -n` clean on six scripts. `sacct` confirms jobs 2215078 (+2215079 sweep), 2215097,
  2215136, 2215137 (+2215161 sweep) RUNNING with rows on HOME.
- **Findings:** the RQ2 census dependency on matrices job 2213202 was rejected by Slurm (the
  record was purged); submitted un-gated after proving the cache loads from a real stage root.
  Kept the worker-level symlink for the matrices root instead of rq-4-5's CLI flag; both honour
  the same contract (unified in docs by `common-sync`).
- **Action taken:** merged as-is (`40a185e`).

### `rq-3-6` — ACCEPT
- **Claimed:** job 2213221 did not die in RQ3 (which completed: 49,027 variant rows, 690
  natural rows, 35,656 certificate rows in 3,330 s); the OOM was RQ6's — `TokenNGram`'s
  unbounded per-context memo grew +2.7 GB per unit (local reproduction 19,980 MB at unit 7 vs
  cluster MaxRSS 19,969 MiB); fixed on the runner side by refitting per unit (RSS flat at
  3.9 GB); `--mem` 24G → 64G; resubmitted as 2215096.
- **Verified:** tree clean; 8 commits from `2e7d811`; 12 files, all inside ownership;
  124 tests pass in `isalhg-rq36`; ruff clean. Job 2215096 COMPLETED; the RQ3 rows were
  preserved by the resume (49,028 lines after stage-in). Diagnosis independently consistent
  with the `tracemalloc` attribution in the commit message.
- **Findings:** the library defect remained (assigned to `ngram-cache`).
- **Action taken:** merged as-is (`55ec11f`).

### `rq-4-5` — ACCEPT
- **Claimed:** the predecessor's directive diff committed; a blocking defect found (runners
  read the matrix cache under `--out`, the empty node-local stage root) and fixed with
  `--matrices-root`; background payload + periodic sync on all three workers; RQ4 censors a
  raising arm instead of dying; `--refill-censored-arm` added for the post-fix HPD re-score;
  smokes 2213203/2213204 never ran (dependency on the purged 2213202); RQ5 2215162 and RQ4
  2215168 submitted (2215163 FAILED on the HPD crash and was superseded).
- **Verified:** tree clean; 7 commits from `2e7d811`; 16 files, all inside ownership;
  115 tests pass in `isalhg-rq45`; ruff clean; `bash -n` clean on six scripts.
- **Findings:** none beyond the reported library defect.
- **Action taken:** merged as-is (`745d753`).

### `hpd-fix` — ACCEPT
- **Claimed:** root cause = the portrait's `k`-axis allocated with extent `N`, one short at
  `N == 1` (the lone hyperedge counts itself at distance 0); extent now `max(N, 2)`; portraits
  of all 15,505 pristine members across the six frozen collections byte-identical; 52,813
  corrupted `ndc_classes` variants exercised with 0 exceptions (4,295 at the formerly crashing
  `N = 1`); the crash set is exactly `missing_fact` at budget 2 on the 859 three-fact members.
- **Verified:** tree clean; 3 commits from `55ec11f`; 3 files inside ownership; the diff is a
  one-line allocation change plus a derivation comment; 467 tests pass in `isalhg-hpdfix`.
- **Findings:** a latent upstream issue (size-1 hyperedge folds onto the last size slice
  silently) was left unfixed by design — it never fires on these corpora (min hyperedge size 2).
- **Action taken:** merged as-is (`21da071`).

### `ngram-cache` — ACCEPT
- **Claimed:** LRU-bounded memo with `cache_size=1024` (one entry = `8·|V|` bytes; 166 MiB at
  the largest frozen vocabulary `|V| = 21,263`; 69.5 MB on `wd50k66` vs the 731 MB per unit the
  unbounded memo accumulated), `cache_size=None` for the old behaviour, public `reset_cache()`;
  samples and log-probabilities bit-identical across cache sizes.
- **Verified:** tree clean; 3 commits from `21da071`; 3 files inside ownership; 171 tests pass
  in `isalhg-ngram` (generation + RQ6 smoke).
- **Findings:** `rq6.py`'s per-unit refit docstring now describes a fixed defect (harmless
  0.15 s redundancy; follow-up).
- **Action taken:** merged as-is (`a8d0005`).

### `common-sync` — ACCEPT
- **Claimed:** single `tkde_run_synced` definition in `common.sh` (byte-identical body), eight
  copies removed, every worker still calls it (11 call sites); PYTHONPATH comment corrected
  (PEP 660 finder ⇒ `isalhg.*` always from the shared checkout); README/PICASSO.md document the
  matrices-root contract, run tags, purged dependencies, memory peaks, the job table;
  functional trap test reproduces the 2213210 defect and shows the fix.
- **Verified:** tree clean; 3 commits from `21da071`; 12 files inside ownership; only one
  `tkde_run_synced()` definition; `bash -n` clean on all 19 scripts; merge preview conflict-free.
- **Findings:** `common.sh` is the frozen cluster contract, so a smoke re-run is required before
  the next submission from the shared checkout. Run-tag enforcement is not universal (RQ3/RQ4/RQ5
  analyzers exclude `_smoke*` paths only), documented as measured.
- **Action taken:** merged as-is (see Integration).

## Orchestrator interventions

| Commit | Type | Agent affected | What and why |
|---|---|---|---|
| — | relay | `rq-1-2-7` | rq-4-5's matrices-root defect relayed; rq-1-2-7 proved on Picasso its symlink already resolves the cache to HOME and kept its mechanism |
| — | direction | `rq-4-5` | asked for the idempotent `--refill-censored-arm` so HPD can be re-scored after the vendor fix without recomputing other arms |
| — | spawn | `hpd-fix` | library defect outside every wave-3 ownership set; scoped agent instead of a FIXUP |
| — | spawn | `common-sync`, `ngram-cache` | post-merge consolidation and the library-side fix behind the RQ6 OOM |

## Integration

| Order | Branch | Merge commit | Tests after merge | Conflicts |
|---|---|---|---|---|
| 1 | `worktree-agent-a1401be85ab17a08d` (rq-1-2-7) | `40a185e` | `tests/experiments_tkde` 128 passed | none |
| 2 | `worktree-agent-a30b6439b4518d41a` (rq-3-6) | `55ec11f` | 182 passed | none |
| 3 | `worktree-agent-a275053d6dad23593` (rq-4-5) | `745d753` | 227 passed | none |
| 4 | `worktree-agent-ab2a7d8f76f4c34bf` (hpd-fix) | `21da071` | full suite (see below) | none |

| 5 | `worktree-agent-a3554e620c7eb2d0d` (ngram-cache) | `a8d0005` | generation + metric_space + RQ6 smoke: 638 passed, 1 skipped | none |
| 6 | `worktree-agent-a4654a7c8320da94d` (common-sync) | `87b161d` | `bash -n` clean on all 19 SLURM scripts (shell + docs only) | none |

**Final verification** (full suite on `21da071`, i.e. after merges 1–4; the ngram-cache merge
re-ran the generation, metric-space and RQ6 smoke tests)

| Check | Command | Result |
|---|---|---|
| Full test suite | `pytest tests/unit tests/property -q -x --hypothesis-seed=0` | 2,056 passed, 7 skipped, 588 s |
| Lint | `ruff check src/ tests/ experiments/` | 38 findings — identical count per directory on the wave base `2e7d811` (src 2, tests 1, experiments 35, all in `experiments/article/**` and `experiments/preprint/**`, untouched by this wave); `experiments/tkde` clean |
| Type check | `mypy src/isalhg/` | 20 errors in 6 files — the pre-existing set recorded in the handoff (untouched core files) |
| Real-data check | harvest + `analyze_rq3`, `analyze_rq6` on the local results root | RQ3: 49,027 / 690 / 35,656 rows analysed; RQ6: 108 sample rows, 40 alignment rows; tables written |

**Merged into `main`:** no — awaiting user confirmation (the whole integration branch,
waves 1–3).

## Campaign (Picasso, `--account=tic_163_uma --constraint=sd`, results on HOME)

| RQ | job(s) | shape | state at 2026-09-05 23:30 CEST |
|---|---|---|---|
| RQ3 + RQ6 | 2215096 (resubmission of 2213221 OOM) | 1 task, 64G, 8 h | COMPLETED |
| RQ7 | 2215078 (+ sweep 2215079) | 74 × 5 shards, throttle 16, 16G, 24 h | RUNNING |
| RQ2 main | 2215097 | 13 × 4 shards, throttle 10, 32G | RUNNING (5 tasks done; MaxRSS ≤ 156 MB) |
| RQ2 census | 2215136 | 8 × 4 shards, 32G | RUNNING (1 done) |
| RQ1 | 2215137 (+ sweep 2215161) | 48 × 3 shards, throttle 16, 12G, 24 h, ≈ 125 core-h | RUNNING (1 done) |
| RQ5 | 2215162 | 1 task, 65 units, 48G, 6 h | RUNNING |
| RQ4 | 2215168 (2215163 FAILED, superseded) | 3 × 441 units, 48G, 8 h | RUNNING (hpd_jsd censored on the `N = 1` crash set until the refill) |
| matrices | 2213202 | 1 task, 64G | COMPLETED 33:50, MaxRSS 34.2 GB |

## Open follow-ups

1. Sync `src/` (HPD fix, n-gram cache bound) to the shared Picasso checkout with
   `scripts/tkde/sync_to_picasso.sh` **after** the running campaign completes (a mid-campaign
   sync would give later tasks a different `src_deploy` stamp), then run
   `rq4 --refill-censored-arm hpd_jsd` and re-harvest.
2. Interpretation pass for RQ1, RQ2, RQ4, RQ5, RQ7 on the completed rows
   (`results/IEEETKDE/DECISIONS.md`; RQ3 and RQ6 are recorded).
3. Untagged smoke rows from the 2026-09-05 cluster smokes sit in the real folders on HOME and
   were harvested locally (`RQ1_addressing/addressing/`, `RQ2_wellposedness/*/`,
   `RQ7_envelope/envelope/`, files named `rows_<table>__<name>-000of001.csv` without the 8-hex
   run tag). The analyzers skip them; moving them was blocked by the permission classifier
   when an agent tried, so the user decides.
4. Purged-job dependencies: Slurm rejects `--dependency=afterok:<id>` once the upstream record
   is purged (`Job dependency problem`); the launchers must check `sacct -j <id>` first.
5. The `rq-1-2-7` reader imports `cache_paths`/`member_order_sha1` from the shared toolkit (no
   drift possible); `experiments.tkde.matrices` remains the single writer.
6. Remove the six worktrees and cloned envs (`isalhg-rq127`, `isalhg-rq36`, `isalhg-rq45`,
   `isalhg-hpdfix`, `isalhg-commonsync`, `isalhg-ngram`) after the user confirms.

## What the decomposition got wrong

- The matrices-root contract was frozen as a file layout but not as a *root*: on Picasso the
  runner's `--out` is an empty node-local stage tree, so the layout alone was insufficient.
  Two agents solved it two ways (symlink vs. CLI flag). The contract should have named the
  root variable (`$ISALHG_RESULTS_ROOT`).
- The copy-back-on-signal defect in `common.sh` was discovered mid-wave and patched in eight
  workers by three agents; a shared helper should have been in `common.sh` from wave 1 with a
  signal test.
- The competitor audit (wave 2) never scored *corrupted* inputs, so the HPD crash surfaced only
  in RQ4's full run. Every competitor should be exercised on the perturbation generators before
  a campaign.
- Smoke jobs sharing unit ids and folders with the campaign (fixed mid-wave by `_smoke*`
  staging and run tags) should have been a wave-1 convention.
