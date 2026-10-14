# Work log — picasso-env

## Identity

| Field | Value |
|---|---|
| Agent | `picasso-env` |
| Wave | `2026-09-05-tkde-w1` |
| Model / effort | Opus 5 (1M) / high |
| Branch | `worktree-agent-a57a0919d0e693ba9` |
| Worktree | `/home/mpascual/research/code/IsalHG/.claude/worktrees/agent-a57a0919d0e693ba9` |
| Base commit | `7590df4c1624e0a885cead3d5d0479b12cd29510` |
| Head commit | `511520a` + this log commit |
| Started / finished | `2026-09-05T13:01+02:00` / `2026-09-05T13:35+02:00` |
| Status | complete |

## 1. Prompt as received

```
# Task: picasso-env — the Picasso execution environment for the TKDE experiments

You are agent `picasso-env` in wave `2026-09-05-tkde-w1` of the IsalHG TKDE experiments. You work in an isolated git worktree on your own branch, in parallel with two peers who own different files, and you also operate on the Picasso HPC cluster over `ssh picasso` (alias configured; use `-o ServerAliveInterval=60`). You never see the orchestrator's conversation; everything you need is in this prompt, the repository, and the `picasso-sbatch` skill. Confirm at the start that `git rev-parse --show-toplevel` is NOT `/home/mpascual/research/code/IsalHG` (the main checkout).

**First action:** invoke the skill `picasso-sbatch` (Skill tool) and follow it — it holds the measured cluster facts (node families, AVX-512 trap, the 2 h job floor, `$LOCALSCRATCH`, job-id capture, quota reading, native-code build recipe). Its rules are binding.

## Mission
Stand up a clean, verified execution environment on Picasso for the whole experiment campaign: a fresh repository deployment, a dedicated conda env with the C++ extension built and **proven to import and run on an `sd` compute node**, the raw data staged, a reusable SLURM common script encoding the project's conventions (env activation, `$LOCALSCRATCH` staging, whole-tree copy-back with traps, per-task pycache prefix, job header with CPU model), idempotent sync and harvest scripts, and a written record of everything measured. "Working" means: one smoke job on `--constraint=sd` completes and its log shows the C++ engine canonicalizing a fixture, pynauty and rapidfuzz importing, and unit tests passing, from the new env and the new repo path.

## Why this exists
Every experiment of the article (`docs/article/D_ART3/experiments/DESIGN.md`) executes on Picasso (`CODE_PLAN.md` §4) and is harvested to the local drive. The previous probe hit the AVX-512 trap (array `2206615` died with SIGILL on `sr` nodes because the extension was built on the Intel login node; array `2206622` succeeded pinned to `sd`). Wave-3 agents will write per-experiment launchers by sourcing your `common.sh` and reading your README; if your environment is wrong, seven experiments fail late and expensively.

## Read first
1. `CLAUDE.md` (loaded; note the editable-install path-pinning hazard), `docs/article/D_ART3/experiments/CODE_PLAN.md` §0, §4, §5; `DESIGN.md` G6–G7.
2. The existing, working Picasso scripts of this project: `scripts/diagnostics/d_art3_probes_2026-09-03/f4_topology/slurm/f4_ea_launcher.sh` and `f4_ea_worker.sh` (extend their environment fixes — do not author a worker from scratch), `slurm/T-M7d_worker.sh`, `slurm/T-M5a_worker.sh`.
3. `CMakeLists.txt` (build flags: `-O3 -march=native`, optional PGO), `pyproject.toml` (scikit-build-core + nanobind; the `[dev]` extras).

## Your ownership (exclusive write access)
- `slurm/tkde/common.sh` (new), `slurm/tkde/README.md` (new), `slurm/tkde/smoke_launcher.sh`, `slurm/tkde/smoke_worker.sh` (new)
- `scripts/tkde/sync_to_picasso.sh`, `scripts/tkde/harvest_from_picasso.sh`, `scripts/tkde/picasso_env_setup.sh` (new)
- `docs/article/D_ART3/experiments/PICASSO.md` (new)
- `.claude/notes/2026-09-05-tkde-w1/picasso-env.md` (your work log)
- Remote (Picasso): `~/fscratch/repos/IsalHG-tkde/` (NEW directory — never modify `~/fscratch/repos/IsalHG`, which is another checkout with a working build), the conda env `isalhg-tkde` (new), `~/fscratch/datasets/isalhg_tkde/`, `~/fscratch/results/IEEETKDE/`, `~/execs/tkde/logs/`.
Everything else in the repository is read-only (peers own `src/**`, `experiments/**`, `tests/**`, `scripts/tkde/freeze_corpora.py`).

## Base state
- Base commit: `7590df4`. Do not rebase, merge or cherry-pick. The code you deploy to Picasso now is your own worktree (= base + your files); the orchestrator re-runs your sync script after every merged wave.

## Frozen contracts (what wave-3 launchers will assume)
- Remote paths: repo `/mnt/home/users/tic_163_uma/mpascual/fscratch/repos/IsalHG-tkde`; env name `isalhg-tkde`; data root `/mnt/home/users/tic_163_uma/mpascual/fscratch/datasets/isalhg_tkde` with `raw/` and `corpora/` subdirs; results root `/mnt/home/users/tic_163_uma/mpascual/fscratch/results/IEEETKDE`; logs `/mnt/home/users/tic_163_uma/mpascual/execs/tkde/logs`.
- `slurm/tkde/common.sh` is `source`d by every worker after its `#SBATCH` header and exports: `PY` (absolute python of `isalhg-tkde`), `REPO_DIR`, `ISALHG_DATA_ROOT`, `ISALHG_RESULTS_ROOT`, `PYTHONPATH="$REPO_DIR/src:$REPO_DIR"`, `PYTHONUNBUFFERED=1`, `OMP_NUM_THREADS`/`MKL_NUM_THREADS` from `SLURM_CPUS_PER_TASK`, a per-task `PYTHONPYCACHEPREFIX`; defines `tkde_job_header` (job id, array id, node, `lscpu` model name, git SHA of `$REPO_DIR`, start time), `tkde_stage_localscratch <results_subdir>` (creates `$MYLOCALSCRATCH/out`, sets `OUT_DIR`, installs `EXIT`/`TERM`/`INT` traps that mirror the WHOLE `out/` tree into `$ISALHG_RESULTS_ROOT/<results_subdir>/` atomically and delete the node copy only after success), and `tkde_job_footer` (elapsed).
- Every job: `--account=tic_163_uma --constraint=sd`, explicit `--output/--error` under the logs dir with `%A_%a`, throttle on arrays, ≥ 2 h per task except the single smoke job.
- `scripts/tkde/sync_to_picasso.sh [--repo-from <path>] [--corpora]`: rsync the local checkout (default: the directory it is invoked from; excludes `.git`, `build/`, `**/__pycache__`, `.claude/worktrees`, `.claude/notes`, data, results) to the remote repo dir, then run the remote reinstall (`rm -rf build && pip install -e ".[dev]" --no-deps` in `isalhg-tkde`, exit status read directly, `.so` mtime asserted to post-date the sync); with `--corpora`, also rsync `$ISALHG_RESULTS_ROOT/corpora/` to the remote data root.
- `scripts/tkde/harvest_from_picasso.sh [--dry-run]`: `rsync -a` the remote results root into the local `ISALHG_RESULTS_ROOT` (default `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE`), never deleting local files.
- `scripts/tkde/picasso_env_setup.sh`: idempotent remote setup (env creation/clone, dependency install, build, verification), runnable again after a dependency change.

## Environment bootstrap (local worktree; you need the env only to run shellcheck-free bash and to read the repo)
```bash
cd "$(git rev-parse --show-toplevel)"
PY=~/.conda/envs/isalhg/bin/python        # read-only use locally; do NOT pip install into it
```
Remote: conda is `/mnt/home/soft/miniconda/programs/x86_64/miniconda3_py310_23.1.0` (module or absolute path — probe as the skill says); an env named `isalhg` already exists on Picasso (used by the f4 probe: Python 3.11, pynauty 2.8.8.1, a built extension) — find it with `conda env list`, clone it to `isalhg-tkde` (or create fresh py3.11 if cloning fails), then install into it: `pip install -e ".[dev]"` from the NEW repo dir after `rm -rf build`, plus `pynauty rapidfuzz kmedoids netlsd scikit-learn scipy pandas pyarrow pyyaml hypothesis pytest` (pin versions in `PICASSO.md`). The compute nodes have no outbound internet: install everything from the login node.

## Verification commands
```bash
bash -n slurm/tkde/*.sh scripts/tkde/*.sh                      # syntax
ssh picasso 'quota; squeue; scontrol show config | grep -E "MaxArraySize|MaxJobCount"; sacctmgr -nP show assoc user=$USER format=Account,QOS'   # live state, record in PICASSO.md
ssh picasso 'sbatch --test-only <remote smoke worker>'          # before the real submission
# the smoke job itself (the one allowed short job): --constraint=sd, ≤ 30 min, 4 cpus, 8G; its log must show lscpu model, python path inside IsalHG-tkde,
# `import isalhg.core._native` ok, canonical_string(Fano, backend="cpp") == the Python backend result, pynauty.canon_label on a Levi graph, rapidfuzz import,
# and `pytest tests/unit/core -q -m unit` passing (run inside the job, never on the login node)
```

## Data to stage (rsync from the local drive; record md5sums)
- `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/data/wd50k_66/`, `wd50k_100/`, `wd50k/` (including its `types/` subdirectory with the P31 TSV) → `~/fscratch/datasets/isalhg_tkde/raw/{wd50k_66,wd50k_100,wd50k}/`
- `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/data/arb_benson/temporal/NDC-classes/` and `NDC-substances/` → `raw/arb_benson/temporal/{NDC-classes,NDC-substances}/`
- Some of this already exists at `~/fscratch/datasets/isalhg_f4/`; do not modify that directory — copy into the new root.
- `corpora/` is produced by peer `kb-corpora` later; your `--corpora` flag must work when the local `corpora/` directory exists and skip cleanly when it does not.

## Definition of done
1. `~/fscratch/repos/IsalHG-tkde` deployed from your worktree; `isalhg-tkde` env exists; `pip install -e ".[dev]"` from that dir exited 0 (status read directly, not through a pipe); the extension `.so` under the env's site-packages (or the repo's build dir — locate it as the skill says) has an mtime after the sync; `python -c "import isalhg; print(isalhg.__file__)"` on the login node prints a path inside `IsalHG-tkde`.
2. The smoke job (job id recorded) COMPLETED on an `sd` node with all checks above green; its `.out` is copied into your log verbatim (trimmed to the check lines).
3. Raw data staged with md5sums matching the local files; `count_files` and `quota` outputs recorded before and after.
4. `slurm/tkde/common.sh` and `README.md` written; the README distils the skill's array/bundling/start-cutoff/copy-back/job-id-capture rules into the exact pattern a wave-3 launcher must follow (with a minimal launcher/worker skeleton that sources `common.sh`).
5. `sync_to_picasso.sh` and `harvest_from_picasso.sh` run end-to-end (sync: your worktree → remote, reinstall verified; harvest: `--dry-run` shows the remote tree, then a real harvest of the smoke job's output into the local results root under `IEEETKDE/_smoke/`).
6. `PICASSO.md` records: live quota/file counts/queue, QOS, MaxArraySize, node features, the exact build flags and compiler, the ISA decision (`-march=native` + `sd` pin) and the documented fallback (`-march=haswell` → `cpu`), package versions, the smoke job id and timings, and any deviation from this prompt.
7. Everything committed on your branch; working tree clean; log committed.

## Explicitly out of scope
- Writing any experiment runner or per-RQ launcher (wave 3).
- Modifying `CMakeLists.txt`, `pyproject.toml`, or any Python source.
- Touching `~/fscratch/repos/IsalHG`, `~/fscratch/datasets/isalhg_f4`, `~/fscratch/results/f4_topology`, or any running job (array `2206622` may still be running — leave it).
- Submitting anything beyond the single smoke job.

## Work log — mandatory
Maintain `.claude/notes/2026-09-05-tkde-w1/picasso-env.md` in your worktree from your first action, using **exactly** the template at `/home/mpascual/.claude/skills/parallel-agents/assets/note-template.md` (read it, copy its skeleton verbatim, fill every section, paste this prompt verbatim in §1). Commit it last with message `docs(notes): picasso-env work log`. Standing obligations: work only inside your worktree and ownership set (plus the named remote paths); commit everything before finishing; never `git push`, never touch a peer's branch; you cannot ask the user — on ambiguity message `main`, record the assumption, keep working; report failure honestly (a SIGILL or a failed build is a finding, not an embarrassment).

## Peers in this wave
- `main` — the orchestrator.
- `fact-alphabet` — the fact-token encoder/decoder and distances. Owns `src/isalhg/core/fact_word.py`, `src/isalhg/iso_backends/canonical_order.py`, `src/isalhg/metric_space/distances/fact_*.py`, `src/isalhg/datasets/schemas.py`.
- `kb-corpora` — knowledge-base records, loaders, generators, `scripts/tkde/freeze_corpora.py`; writes frozen corpora to the local `IEEETKDE/corpora/`. Owns `src/isalhg/datasets/kb/**`, `experiments/tkde/corpora.py`.

## Final message format (≤ 15 lines)
- STATUS / BRANCH / WORKTREE / HEAD / LOG
- SMOKE JOB: id, node, elapsed, checks passed
- Three bullets: what you built; anything the orchestrator must know (quota, queue, deviations); anything unfinished.
```

## 1b. Change request — 2026-09-05, after first merge

The coordinator sent a change request once the branch was already merged
(committed on the same branch for a second merge).

**Request, verbatim in substance:** move the Picasso results root from FSCRATCH
to HOME —
`ISALHG_RESULTS_ROOT = /mnt/home/users/tic_163_uma/mpascual/results/IEEETKDE`.
Reason given: FSCRATCH is over its file soft quota and is purged; HOME has
3.3k/35k files, 24 GB/280 GB, and is permanent. Repo, env, raw data and corpora
stay on FSCRATCH; logs stay in `~/execs/tkde/logs`. Six numbered steps: update
the four named files; create the remote directory and re-run the smoke job once
(≤ 10 min) so the copy-back into HOME is exercised for real; `mv` (not copy) the
previous smoke output to the new root and `rmdir` the emptied FSCRATCH results
directory, deleting nothing else there; re-run harvest dry-run then real; update
this log; commit and report.

**What changed**

| File | Change |
|---|---|
| `slurm/tkde/common.sh` | `ISALHG_RESULTS_ROOT` default → `${TKDE_USER_ROOT}/results/IEEETKDE`; header comment; note in `tkde_stage_localscratch` that the copy-back is now also the durable-storage step |
| `slurm/tkde/smoke_launcher.sh` | **its own `RESULTS_ROOT` default**, which is `--export`ed to the worker and would otherwise have silently overridden `common.sh` — not on the coordinator's list, but the change is inert without it |
| `scripts/tkde/picasso_env_setup.sh` | **its own `RESULTS_ROOT` default**, which the setup `mkdir -p`s — a stale value would have silently re-created the retired FSCRATCH results directory on the next setup run. Also not on the list; found by grepping for residual `fscratch/results` references rather than by trusting the list |
| `scripts/tkde/harvest_from_picasso.sh` | `TKDE_REMOTE_RESULTS` default → the HOME root; the header rationale rewritten (the remote is no longer the transient copy) |
| `slurm/tkde/README.md` | §Harvest replaced by §"Results go to HOME, not FSCRATCH": the decision, the reproducible-inputs/irreproducible-results asymmetry, and the reminder that HOME's own 35.0k file quota still forces consolidation |
| `docs/article/D_ART3/experiments/PICASSO.md` | §1 table row; new §2.1 (decision + the HOME quota read that day + FSCRATCH still over quota, for the user to prune); new §6.1 (re-validation job) |

The smoke job's checks were not otherwise touched. The `sd` pin and the sync
script's targets (repo and corpora stay on FSCRATCH) are unchanged.

**Evidence**

- Remote directory created; `_smoke/` **moved** (`mv`) from
  `fscratch/results/IEEETKDE/` to the HOME root; the emptied directory
  `rmdir`-ed after an `ls -A` confirmed it was empty. `fscratch/results/` still
  contains `f4_topology` and `isalsr` — nothing else was deleted.
- Re-validation smoke job **`2210916`** (`--test-only` `2210915` first):
  node **`sd089`**, **00:06:15**, **COMPLETED**, 363 passed,
  `PYTEST EXIT: 0`, and the line that mattered:
  `[stage] copy-back OK -> /mnt/home/users/tic_163_uma/mpascual/results/IEEETKDE/_smoke`.
  Under the 10-minute cap.
- HOME results tree after the run (files re-stamped 13:50 by the fresh
  copy-back, over the 13:20 set moved in):

  ```
  /mnt/home/users/tic_163_uma/mpascual/results/IEEETKDE/_smoke:
  -rw-r-----  272 Sep  5 13:50 provenance.txt
  -rw-r----- 2620 Sep  5 13:50 pytest_unit_core.txt
  -rw-r-----  571 Sep  5 13:44 smoke_checks.txt
  -rw-r-----  762 Sep  5 13:44 smoke_report.json
  ```

- Harvest `--dry-run` listed the four files from the HOME root; the real run
  pulled them into `…/results/IEEETKDE/_smoke/` locally. `provenance.txt` now
  reads `deploy=sha=e6bd84b …` where the previous run had `git=n/a`, confirming
  the `.tkde_deploy` stamp fix in the same commit.

**Note on the quota.** This stops the campaign *adding* to the FSCRATCH problem;
it does not clear it. FSCRATCH remains over its file soft quota with the grace
period running, and the reclaim targets are the user's to prune (§7, §10).

## 2. Understanding and plan

**Restatement of the task in my own words:** Build and *prove* a clean Picasso
execution environment for the whole TKDE campaign — a fresh repo deployment at
`IsalHG-tkde`, a dedicated `isalhg-tkde` conda env whose C++ extension actually
runs on an `sd` compute node, the raw KB data staged and checksummed, plus the
reusable shell layer (`common.sh`, launcher/worker skeleton, sync, harvest,
setup) that wave-3 agents will build every experiment on. Write down every
measured cluster fact so nobody has to re-derive it.

**Approach chosen:** Extend the one worker measured green on this cluster
(`f4_ea_worker.sh`) rather than authoring an environment block from scratch —
its conda-probe cascade, `PYTHONPATH` ordering and thread pinning are
accumulated fixes not discoverable from the application code. Factor those into
`common.sh`, add the `$LOCALSCRATCH` staging + trap machinery and the per-task
pycache prefix that the F4 worker did not need. Then drive the real thing
end-to-end: deploy, build, stage, submit, read the log, fix what the log
reveals, re-submit.

**Alternatives considered and rejected:**
- *Write a fresh worker from the skill's template.* Rejected: the skill itself
  warns that a fresh worker is missing the accumulated environment fixes, and
  the brief explicitly says to extend the F4 pair.
- *Build with `-march=haswell` and use `--constraint=cpu` for a wider node
  pool.* Rejected as the default: several RQs report wall-clock, and a mixed
  Intel/AMD pool (2.10 GHz Cascade Lake vs 2.60 GHz EPYC) turns a timing
  comparison into a measurement of the scheduler. Kept as the documented
  fallback in `PICASSO.md` §3, with the warning that taking it invalidates
  every timing number measured under `-march=native`.
- *`--constraint=avx512` (the sbatch wrapper's own recommendation), widening to
  `sd` + `bc`.* Rejected: plausible but **unverified**, and it reintroduces the
  mixed-CPU timing confound. Recorded in `PICASSO.md` §3 with the smoke-job
  test that would settle it.
- *Copy-back by enumerating expected files.* Rejected: a named-path copy-back
  returns every file it named, so anything written outside those paths vanishes
  silently. `tkde_finalize` mirrors the whole `out/` tree.
- *Deploy by `git clone` / `git pull` on Picasso.* Rejected: the campaign must
  be able to run a merged-but-unpushed wave, so rsync is the only correct
  transport.

**Plan as executed:**
1. Confirm worktree ≠ main checkout; invoke `picasso-sbatch`.
2. Read the F4 launcher/worker, `CMakeLists.txt`, `CODE_PLAN.md` §0/§3/§4/§5.
3. Probe live Picasso state (quota, QOS, `MaxArraySize`, queue, conda envs,
   compilers) and record it.
4. Write `common.sh`, `smoke_{worker,launcher}.sh`, the three `scripts/tkde/`
   scripts; `bash -n` all of them.
5. Deploy (`sync_to_picasso.sh --no-build`), run `picasso_env_setup.sh`.
6. Stage the five raw data subtrees; verify md5sums both sides.
7. `sbatch --test-only`, then submit the smoke job; read its log.
8. Fix what the log revealed; re-verify; re-submit.
9. Harvest; write `README.md`, `PICASSO.md`, this log; commit.

**Deviations from the plan:** Two, both driven by what the cluster showed.

- Step 8 was not anticipated as a *fix* step. Smoke job `2210890` FAILED on an
  rsync exclude bug I had introduced (§7), so the sync script was corrected, the
  deployment re-verified by a full tree diff, and the smoke job re-submitted as
  `2210893`.
- `common.sh` gained a `tkde_sync_partial` helper and a `.tkde_deploy`
  provenance stamp that the brief's contract did not name, both because the
  contract as written could not be satisfied otherwise (§7).

## 3. Changes made

**Created**
| Path | Purpose |
|---|---|
| `slurm/tkde/common.sh` | the frozen contract every TKDE worker sources: `PY`, paths, threads, per-task pycache, `tkde_job_header`, `tkde_stage_localscratch`, `tkde_sync_partial`, `tkde_finalize`, `tkde_job_footer` |
| `slurm/tkde/README.md` | how a wave-3 launcher must be written: skeleton pair, bundling to the 2 h floor, start-cutoff, job-id capture, `--export` comma trap, array limits, sizing, harvest |
| `slurm/tkde/smoke_worker.sh` | the environment proof on an `sd` compute node (6 checks) |
| `slurm/tkde/smoke_launcher.sh` | submits it; `--dry-run` / `--test-only` |
| `scripts/tkde/picasso_env_setup.sh` | idempotent remote env creation + dependency install + build + verification |
| `scripts/tkde/sync_to_picasso.sh` | rsync deploy + remote rebuild + freshness assertion |
| `scripts/tkde/harvest_from_picasso.sh` | pull the remote results tree home; never deletes local files |
| `docs/article/D_ART3/experiments/PICASSO.md` | the measured record: quota, QOS, node families, toolchain, ISA decision + fallback, package versions, smoke job, deviations |
| `.claude/notes/2026-09-05-tkde-w1/picasso-env.md` | this log |

**Modified** — none. No file outside my ownership set was touched;
`CMakeLists.txt`, `pyproject.toml` and every Python source are unchanged.

**Removed** — none.

**Commits**
| SHA | Message |
|---|---|
| `511520a` | `feat(slurm): TKDE Picasso execution environment` |
| `e6bd84b` | `docs(notes): picasso-env work log` |
| (this commit) | `fix(slurm): move the TKDE results root from FSCRATCH to HOME` (change request §1b) |

## 4. Tests

This wave produces shell infrastructure, not library code, so the "tests" are
the smoke job's six checks plus the deployment's own assertions. No pytest file
was added (none is owned by this agent).

**Checks created**
| Check | File | What it verifies | Why it matters |
|---|---|---|---|
| `isalhg_package_path` | `smoke_worker.sh` | `isalhg.__file__` contains `IsalHG-tkde` | the editable install is path-pinned; a wrong resolution mixes two checkouts with **no error** |
| `cpp_extension_import` | `smoke_worker.sh` | `import isalhg.core._core` on an `sd` node | the AVX-512/SIGILL gate — the failure that killed array 2206615 |
| `canonical_cpp_eq_python` | `smoke_worker.sh` | `canonical_string(Fano, "cpp") == (…, "python")` | proves the extension *computes* correctly, not merely that it loads |
| `pynauty_canon_label` | `smoke_worker.sh` | `pynauty.canon_label` on the Fano Levi graph, 14 nodes | the competitor engine is a native build too |
| `rapidfuzz` | `smoke_worker.sh` | import + `Levenshtein.distance("kitten","sitting") == 3` | `d_I` depends on it |
| `pytest tests/unit/core -m unit` | `smoke_worker.sh` | 363 unit tests on the compute node | catches missing package data, ABI drift |
| extension freshness | `sync_to_picasso.sh` | `.so` mtime ≥ sync epoch | a stale `.so` yields wrong numbers with no error |
| tree completeness | manual, §6 | `comm -23` local vs remote file lists | catches an over-broad rsync exclude — it did |

**Coverage of the behaviour that matters:** the deployment path (rsync →
rebuild → freshness → import → compute) and the compute-node execution path
(module load → activate → thread pinning → staging → payload → copy-back) are
both exercised end-to-end by a real submission. The copy-back was exercised on
**both** the success and the failure path (job 2210890 failed and still mirrored
its output back).

**Not tested, and why:**
- **Bundling and the start-cutoff are documented but not exercised.** The smoke
  job is deliberately a single short job; the loop skeleton in the README is
  untested code. First wave-3 launcher to use it should run one real task before
  its array. Flagged in §10.
- **The array path (`%A_%a`, throttling, index decode) is untested** — no array
  was submitted (out of scope: one smoke job only).
- **`--corpora`** is exercised only on its skip branch (the local `corpora/`
  directory does not exist yet); the copy branch runs first for `kb-corpora`.
- **The `-march=haswell` fallback was not built or run.** It is a documented
  recipe, not a measured one.
- **`--constraint=avx512` / `bc` compatibility is unverified** by design (§7).

## 5. Test results

**Command:** `bash slurm/tkde/smoke_launcher.sh` on Picasso (job 2210893), plus
local `bash -n` on all six scripts.

```
$ bash -n slurm/tkde/common.sh slurm/tkde/smoke_worker.sh slurm/tkde/smoke_launcher.sh \
         scripts/tkde/picasso_env_setup.sh scripts/tkde/sync_to_picasso.sh \
         scripts/tkde/harvest_from_picasso.sh
ALL SYNTAX OK
```

Smoke job `2210893`, node `sd030` (verbatim, trimmed to the check lines):

```
Node:          sd030
CPU model:     Intel(R) Xeon(R) Gold 6230R CPU @ 2.10GHz
CPUs/task:     4   threads=4
Mem requested: 8192 MB
Repo:          /mnt/home/users/tic_163_uma/mpascual/fscratch/repos/IsalHG-tkde
Deployed:      sha=7590df4 branch=worktree-agent-a57a0919d0e693ba9 at=2026-09-05T13:13:04+02:00
Python:        /mnt/home/users/.../fscratch/conda_envs/isalhg-tkde/bin/python
[stage] node scratch : /localscratch/users//mpascual/2210893_0/out
[stage] copy-back to : /mnt/home/users/.../fscratch/results/IEEETKDE/_smoke

[info] python  : /mnt/home/users/.../fscratch/conda_envs/isalhg-tkde/bin/python
[info] version : 3.11.15
[PASS] isalhg_package_path: /mnt2/fscratch/users/.../repos/IsalHG-tkde/src/isalhg/__init__.py
[PASS] cpp_extension_import: .../site-packages/isalhg/core/_core.cpython-311-x86_64-linux-gnu.so
[PASS] canonical_cpp_eq_python: w*_c(Fano) len=121 cpp==python
[PASS] pynauty_canon_label: canon_label on Fano Levi, 14 nodes
[PASS] rapidfuzz: rapidfuzz 3.14.5
```

```
======================= 363 passed in 389.63s (0:06:29) ========================
PYTEST EXIT: 0

ALL SMOKE CHECKS PASSED
Finished:  2026-09-05T13:20:51+02:00
Duration:  0h 6m 39s
[stage] copy-back OK -> /mnt/home/users/.../fscratch/results/IEEETKDE/_smoke

$ seff 2210893
State: COMPLETED (exit code 0)
CPU Utilized: 00:21:45
Memory Utilized: 59.88 MB
Memory Efficiency: 0.73% of 8.00 GB (8.00 GB/node)
```

**Result:** 363 passed, 0 failed, 0 skipped · **Duration:** 00:07:02 wall
(6m29s in pytest) · **Run at:** deployed `sha=7590df4`

The successful run is ~5 min longer than the failed one because the STS catalog
is now present: `test_wstar_c_frozen.py` actually computes `w*_c` on both true
STS(13) systems (the slow-marked pins) rather than erroring out at once. The
30 min wall has ~4× headroom over 6m39s.

Harvest (`harvest_from_picasso.sh`, dry-run then real) pulled 4 files into
`/media/mpascual/Sandisk2TB/…/results/IEEETKDE/_smoke/`: `provenance.txt`,
`pytest_unit_core.txt`, `smoke_checks.txt`, `smoke_report.json`.

**Failures and their resolution:**

Smoke job **`2210890` FAILED** — 361 passed, 2 failed:

```
E   FileNotFoundError: [Errno 2] No such file or directory:
    '/mnt2/fscratch/users/.../repos/IsalHG-tkde/src/isalhg/datasets/data/sts/sts13.txt'
FAILED tests/unit/core/test_wstar_c_frozen.py::test_wstar_c_pinned_on_true_sts13[1]
FAILED tests/unit/core/test_wstar_c_frozen.py::test_wstar_c_pinned_on_true_sts13[2]
2 failed, 361 passed in 100.46s
[stage] copy-back OK -> /mnt/home/users/.../results/IEEETKDE/_smoke
```

**Cause — my bug.** `sync_to_picasso.sh` excluded `data/` **unanchored**. rsync
matches such a pattern at any depth, so it dropped the *packaged* STS catalog
`src/isalhg/datasets/data/sts/*.txt` along with the intended root-level `data/`.

**Fix.** Every directory exclude is now root-anchored (`/data/`, `/build/`,
`/results/`, `/outputs/`, `/.claude/worktrees/`, …); only cache/artefact
patterns (`**/__pycache__/`, `*.pyc`, `*.so`, `*.egg-info/`) remain
depth-independent, deliberately. Re-synced (13.9 MB more transferred, 32.3 MB
total vs 18.2 MB) and **verified by tree diff rather than by re-reading the
excludes**: 771 local files under the sync filter, `comm -23` local vs remote
**empty** — no local file missing remotely. Job `2210893` then passed all 363.

Two things this failure demonstrated positively, worth keeping:
- the `$LOCALSCRATCH` copy-back ran on the **failing** path, so the EXIT trap
  works when it matters most;
- the frozen-`w*_c` regression pins are load-bearing — they caught a deployment
  defect, not a code defect.

## 6. Verification beyond unit tests

| Circumstance | What was run | Evidence | Outcome |
|---|---|---|---|
| Real cluster | `quota`, `sacctmgr`, `scontrol show config`, `squeue`, `conda env list`, `g++ --version` | FSCRATCH 0.47 TB/1.40 TB, **230.9k/250.0k files before**, **251.7k/250.0k after (grace 7 days)**; `count_files` 1031 repo / 35 data; QOS `short,medium_uma,long_uma`; `MaxArraySize=4096`, `MaxJobCount=15000`; queue 2411 jobs/40 users; envs in `~/fscratch/conda_envs`; `g++ 7.5.0`, `gcc` modules to 13.2.0 | recorded in `PICASSO.md` §2–3; quota escalated (§7) |
| Real data | rsync 5 subtrees, `md5sum` both sides, sorted, `diff` | 24 files, 16 MB; **24/24 md5 identical**; `wd50k/types/p31_types.tsv` = `34861083c50bda0b321ec8b063e19656` | pass |
| Real deployment | `sync_to_picasso.sh` | 771 files, 32.3 MB; `PIP EXIT: 0` (status read directly, not through a pipe); `.so` mtime `2026-09-05T13:13:15` ≥ sync epoch; `isalhg.__file__` inside `IsalHG-tkde` | pass |
| Deployment completeness | `find` both trees, `comm -23` | 771 local files, **0 missing remotely**; remote-only = `.pytest_cache/` from the failed run | pass (after the fix) |
| Compute node | smoke jobs 2210890, 2210893 on `sd039`/`sd030` | `sbatch --test-only` exit 0, immediate start; 5/5 engine checks; 363 unit tests | pass |
| Failure path | job 2210890 exited non-zero mid-worker | copy-back still ran: `[stage] copy-back OK` | traps verified |
| Edge case | `harvest_from_picasso.sh --dry-run` with an empty/partial remote tree | see §5 | pass |
| Edge case | `sync_to_picasso.sh --corpora` with no local `corpora/` | `[corpora] SKIP -- … does not exist yet` | pass (skip branch) |
| Environment | Picasso login: Xeon Gold 6230R, SUSE, Python 3.11.15, pynauty 2.8.8.1, rapidfuzz 3.14.5, numpy 2.4.6, pyarrow 25.0.1, netlsd 1.0.2, kmedoids 0.5.5, nanobind 2.13.0, pytest 9.1.1 | | recorded in `PICASSO.md` §4 |

## 7. Decisions, assumptions, open questions

**Decisions with a real trade-off:**

- **`-march=native` + `--constraint=sd`, not `-march=haswell` + `cpu`.** Costs
  queue time and caps the node pool at the 52-core Intel family. Buys a working
  extension (measured: `sr` → SIGILL) *and* wall-clock comparability across
  timing arms, which a mixed Intel/AMD pool would destroy. Fallback documented
  with the explicit warning that taking it invalidates prior timing numbers.
- **`sd` over the wrapper-recommended `avx512`.** `avx512` would add `bc` and
  widen the pool; it is plausible but unverified, and it reintroduces the timing
  confound. Recorded with the smoke test that would settle it.
- **Whole-tree copy-back via `rsync`, not an enumerated file list.** Slightly
  more data moved; makes it impossible to silently lose an artefact written
  outside the paths someone remembered to name.
- **Absolute `$PY` rather than relying on `conda activate`.** `common.sh` still
  activates (for `CONDA_PREFIX`, `LD_LIBRARY_PATH`, `pytest` on PATH) but never
  *depends* on it: a half-failed activation is silent, a wrong absolute path is
  not.
- **`--no-build-isolation` first, isolated build as fallback.** Faster and uses
  the in-env `scikit-build-core`/`nanobind`; the skill warns that a failed
  no-isolation build can leave the previous artefact importable, so the
  fallback plus the mtime assertion cover that.

**Assumptions I proceeded on:**

- **The extension module is `isalhg.core._core`, not `isalhg.core._native`** as
  both the brief and `CODE_PLAN.md` §4 state. Verified against `CMakeLists.txt`
  (`install(TARGETS _core … DESTINATION isalhg/core)`) and by import locally and
  on the compute node; `src/isalhg/core/_native/` is the C++ *source* directory
  and is not importable. If someone later "fixes" the smoke test back to
  `_native` it will fail. → `PICASSO.md` §4.
- **The env belongs in `~/fscratch/conda_envs`**, matching the three envs
  already there, not `~/.conda/envs` as the brief's bootstrap snippet implies.
- **Cloning `isalhg` is the right base** for `isalhg-tkde` (it is the env the F4
  probe ran green on). The clone succeeded, so the fresh-py3.11 branch of
  `picasso_env_setup.sh` is untested.
- **The job header's "git SHA of `$REPO_DIR`" is satisfied by a deploy stamp.**
  The rsync deployment excludes `.git`, so no SHA is resolvable remotely;
  `sync_to_picasso.sh` writes `.tkde_deploy` (sha, branch, source path,
  timestamp) and `tkde_job_header` prints it, falling back to `git` if the tree
  ever is a checkout. This is a superset of what was asked.
- **`TKDE_THREADS=1` is the timing-arm convention.** `common.sh` defaults
  threads to `SLURM_CPUS_PER_TASK` per the contract; timing arms must opt out.
  Documented in the README; wave-3 must honour it.

**Open questions for the orchestrator:**

- 🔴 **The FSCRATCH file soft quota is now EXCEEDED and a 7-day grace period is
  running.** It stood at 230.9k/250.0k *before* I touched anything; my
  deployment added ≈1.07k files (repo 1031 + data 35, both by `count_files`) and
  the post-deployment reading is **251.7k/250.0k, grace 7 days**, with
  `-> Notice: You have exceeded your file count quota on FScratch.` The hard
  limit is 400.0k, at which writes are blocked outright.

  **This should be resolved before any wave-3 array is submitted.** It is an
  account-level decision and the obvious reclaim targets
  (`results/f4_topology`, `results/isalsr`, the four other `repos/` checkouts)
  are explicitly outside this wave's scope, so I escalated rather than acted.
  Options: prune harvested prior campaigns from FSCRATCH; request a quota
  increase from `soporte@scbi.uma.es`; or both. Recorded in `PICASSO.md` §2.
- **Bundling/start-cutoff code in the README is a documented skeleton, not
  measured code.** The first wave-3 launcher that adopts it should run one real
  task before its array.
- I did not message `main`: nothing was blocking, and every ambiguity above was
  resolvable against the repository itself (CMake target, `conda env list`).

## 8. Coordination

**Messages sent:** none. No blocking ambiguity arose; the two naming
discrepancies (`_native`/`_core`, env location) were settled against
`CMakeLists.txt` and `conda env list` rather than by asking.

**Messages received and how they changed the work:** none.

**Contracts I depend on and confirmed unchanged:** none from peers — this wave's
deliverable is infrastructure and touches no file `fact-alphabet` or
`kb-corpora` own. The contracts *I* provide are in `slurm/tkde/README.md` and
`PICASSO.md` §1. The one interface I consume from a peer is `kb-corpora`'s
frozen `corpora/` directory, and `--corpora` skips cleanly until it exists.

## 9. Deliberately not done

- **No experiment runner or per-RQ launcher** — wave 3.
- **No change to `CMakeLists.txt` or `pyproject.toml`** — explicitly out of
  scope, so the build uses the project's flags unmodified and the ISA problem is
  solved by node pinning rather than by editing build flags.
- **No `-march=haswell` build.** Documented as a recipe; building it would have
  produced a second `.so` and muddied the freshness assertion.
- **No second job of any kind** — one smoke job was authorised; `2210890` and
  `2210893` are the same smoke job, the first having failed on my rsync bug.
- **Nothing touched under** `~/fscratch/repos/IsalHG`, `~/fscratch/datasets/isalhg_f4`,
  `~/fscratch/results/f4_topology`; no running job interfered with (`2132239`
  was already `PD/JobHeldAdmin` and left alone).
- **No `git push`**, no peer branch touched.
- **No FSCRATCH pruning.** The file soft quota is now exceeded (§7), and the
  obvious reclaim targets are directories this wave was told not to touch, so it
  is escalated rather than fixed.

## 10. Risks and follow-ups

| Item | Severity | Detail | Suggested owner |
|---|---|---|---|
| **FSCRATCH file soft quota EXCEEDED, 7-day grace running** | **medium** (was high) | 230.9k/250.0k before this wave; 251.7k/250.0k after (+≈1.07k from the deployment). Hard limit 400.0k blocks writes outright. **Mitigated by the 2026-09-05 change request** (§1b): results now go to HOME, so the campaign no longer adds to it, and only the repo/env/data remain there. **Not resolved** — FSCRATCH is still over quota and the reclaim targets (`results/f4_topology`, `results/isalsr`, spare `repos/`) are the user's to prune | user / orchestrator (reclaim targets outside this wave's scope) |
| HOME file quota is 35.0k, not unlimited | low | Results now land on HOME (3.3k used). Ample, but a launcher writing tens of thousands of small artefacts must still consolidate per unit | wave 3 |
| Bundling / start-cutoff skeleton unexercised | medium | The README's loop is documented, not measured. A missing first-unit exemption livelocks an array | first wave-3 launcher |
| `sd` pin narrows the node pool | medium | 52-core Intel family only. If queue time becomes prohibitive, the `-march=haswell` fallback exists but **invalidates timing numbers measured under `-march=native`** — do not mix arms | orchestrator |
| Array path untested | medium | `%A_%a`, throttle, index decode never exercised (one smoke job only). Run one real task before any array | wave 3 |
| `--corpora` copy branch untested | low | Only the skip branch ran; `kb-corpora` produces `corpora/` later | `kb-corpora` / wave 3 |
| `.pytest_cache/` left on the remote | low | Written by the failed run 2210890; harmless, and `rsync --delete` will not remove it since it is excluded | — |
| Fresh-py3.11 env branch untested | low | The clone of `isalhg` succeeded, so the fallback path in `picasso_env_setup.sh` never ran | — |
| `CODE_PLAN.md` §4 says `_native` | low | Documentation defect in a file I do not own; the correct name is `_core`. Recorded in `PICASSO.md` §7 | orchestrator |

## 11. Self-assessment against the definition of done

| # | Criterion | Met | Evidence |
|---|---|---|---|
| 1 | repo deployed, env exists, `pip install -e` exit 0 read directly, `.so` mtime post-dates sync, login-node import inside `IsalHG-tkde` | yes | `PIP EXIT: 0`; `.so` built `2026-09-05T13:13:15`; `isalhg.__file__` = `/mnt2/fscratch/…/IsalHG-tkde/src/isalhg/__init__.py` (§6) |
| 2 | smoke job COMPLETED on an `sd` node, all checks green, `.out` in this log | yes | job `2210893`, node `sd030`; 5/5 engine checks + 363 unit tests; verbatim in §5 |
| 3 | data staged, md5sums match, quota/file counts recorded | yes | 24/24 md5 identical; `quota` before (230.9k) and after (251.7k, **soft exceeded**); `count_files` = 1031 repo / 35 data — `PICASSO.md` §2 |
| 4 | `common.sh` + README with the launcher/worker pattern | yes | `slurm/tkde/common.sh`, `slurm/tkde/README.md` (skeleton, bundling, cutoff, job-id capture, copy-back, `--export` trap, sizing) |
| 5 | sync + harvest run end-to-end | yes | sync verified by rebuild + tree diff; harvest `--dry-run` then real into `IEEETKDE/_smoke/` (§5) |
| 6 | `PICASSO.md` records quota, QOS, MaxArraySize, node features, flags, compiler, ISA decision + fallback, versions, job id/timings, deviations | yes | `docs/article/D_ART3/experiments/PICASSO.md` §§1–8 |
| 7 | everything committed, tree clean, log committed | yes | §3 Commits |

**Overall:** I am confident in the parts that were exercised against the real
cluster: the deployment (proved complete by a tree diff, not by inspection), the
build (proved fresh and *correct* by `cpp == python`, not merely importable), the
data (24/24 md5), and the compute-node execution including the copy-back on both
the success and failure paths. The most valuable thing this wave produced is
arguably the failure: an unanchored rsync exclude silently dropped packaged data
and only a real test run surfaced it.

What the orchestrator should scrutinise first, in order: **(1) the FSCRATCH file
quota, which my own deployment tipped past its soft limit into a 7-day grace
period** — this is the campaign's real constraint and needs an account-level
decision (prune and/or request an increase) before any array is submitted, not
just a note; **(2) the bundling/start-cutoff skeleton**, which is
documentation rather than measured code and whose first-unit exemption is the
difference between a working array and a livelocked one; **(3) the `_core` vs
`_native` naming**, since `CODE_PLAN.md` still says `_native` and a wave-3 agent
following it will write a check that cannot pass.
