# Picasso execution environment — IEEE TKDE campaign

Everything measured while standing up the campaign's execution environment on
Picasso (UMA SCBI), 2026-09-05. Numbers here are **measured on the cluster on
that date**, not quoted from the SCBI manual. Cluster state drifts; re-read it
(`quota`, `squeue`, `scontrol show config`) before any large submission rather
than trusting a figure written here.

How to *use* the environment — the launcher/worker pattern, bundling, the
start-cutoff, `$LOCALSCRATCH` staging — is in
[`slurm/tkde/README.md`](../../../../slurm/tkde/README.md). This file records
what the environment *is* and how it was verified.

---

## 1. Frozen paths and names

| What | Where |
|---|---|
| Repo | `/mnt/home/users/tic_163_uma/mpascual/fscratch/repos/IsalHG-tkde` |
| Conda env | `isalhg-tkde` at `/mnt/home/users/tic_163_uma/mpascual/fscratch/conda_envs/isalhg-tkde` |
| Interpreter (`$PY`) | `…/fscratch/conda_envs/isalhg-tkde/bin/python` |
| Data root | `…/fscratch/datasets/isalhg_tkde/{raw,corpora}` |
| **Results root** | **`/mnt/home/users/tic_163_uma/mpascual/results/IEEETKDE`** — on **HOME**, not FSCRATCH (§2.1) |
| Logs | `/mnt/home/users/tic_163_uma/mpascual/execs/tkde/logs` |

**Conda envs are not under `~/.conda/envs` on Picasso.** They live in
`~/fscratch/conda_envs` (measured: `conda env list` shows `isalgraph`,
`isalhg`, `isalsr` all there). `CLAUDE.md`'s worktree-hazard note gives the
local convention; the remote one differs and `common.sh` encodes the remote one.

**`~/fscratch` is a symlink.** It resolves to
`/mnt2/fscratch/users/tic_163_uma/mpascual`, so `isalhg.__file__` reports
`/mnt2/fscratch/users/tic_163_uma/mpascual/repos/IsalHG-tkde/src/isalhg/__init__.py`.
Verification asserts the substring `IsalHG-tkde`, never equality against the
`/mnt/home/...` spelling — an equality check would fail on a correct install.

Untouched by this campaign, by instruction: `~/fscratch/repos/IsalHG`,
`~/fscratch/datasets/isalhg_f4`, `~/fscratch/results/f4_topology`.

---

## 2. Live cluster state (measured 2026-09-05, ~13:05 CEST)

### Quota — **read this before sizing any array**

```
                 HOME                              FSCRATCH
         space   used 24.23GB  quota 0.28TB  limit 0.75TB   grace none
         files   used 3.3k     quota 35.0k   limit 150.0k   grace none
         space   used 0.47TB   quota 1.40TB  limit 1.68TB   grace none
         files   used 230.9k   quota 250.0k  limit 400.0k   grace none
```

⚠ **FSCRATCH file count was already at 92 % of the soft quota before this
campaign touched anything** (230.9k of 250.0k). Disk space is not the
constraint (0.47 TB of 1.40 TB); the file count is.

### 🔴 After deployment the soft quota is EXCEEDED — grace period running

Measured immediately after deploying the repo and staging the data:

```
fscratc  0.47TB  1.40TB  1.68TB  none  ║  251.7k  250.0k  400.0k  7 days
-> Notice: You have exceeded your file count quota on FScratch.
```

| Contribution | Files |
|---|---|
| `repos/IsalHG-tkde` | 1031 (`count_files`) |
| `datasets/isalhg_tkde` | 35 (33 in `raw/`) |
| **added by this wave** | **≈ 1.07k** |

That ~1.07k crossed a threshold the account was already sitting under. **The
7-day grace period is now running**; when it expires, or at 400.0k, writes are
blocked outright — and a campaign that hits that at 80 % completion loses the
tail of every task while the jobs keep burning wallclock.

**This must be resolved before any wave-3 array is submitted.** It is an
account-level decision, so it is escalated rather than acted on here (the
obvious reclaim targets — `results/f4_topology`, `results/isalsr`, the four
other `repos/` checkouts — are explicitly outside this wave's scope). Options,
for whoever owns the call:

1. Harvest and prune completed prior campaigns from FSCRATCH (the local drive is
   the durable copy).
2. Mail `soporte@scbi.uma.es` for a file-quota increase, quoting the campaign's
   projected file count.
3. Both.

### 2.1 Decision (2026-09-05): results move to HOME

**`ISALHG_RESULTS_ROOT = /mnt/home/users/tic_163_uma/mpascual/results/IEEETKDE`.**
Inputs are unchanged and stay on FSCRATCH: repo, conda env, `raw/`, `corpora/`.
Logs stay in `~/execs/tkde/logs`.

HOME quota, read the same day:

```
home  24.23GB  0.28TB  0.75TB  none  ║  3.3k  35.0k  150.0k  none
```

Room to spare on both axes (9 % of space, 9 % of files), and HOME is
**permanent** where FSCRATCH is pseudo-volatile.

The asymmetry that decides it: **every input on FSCRATCH is reproducible** —
re-sync the repo, re-run `picasso_env_setup.sh`, re-stage the 16 MB of raw data —
**and a result is not**. Putting results on a filesystem that is over quota,
purged after two months of no access, and has no working recovery tool
(`fscratch_files` is not installed here) is the one placement the campaign
cannot afford.

Two consequences, both good: `tkde_stage_localscratch`'s copy-back is now *also*
the durable-storage step, so no separate FSCRATCH-to-HOME rescue job is needed;
and the campaign's output no longer consumes the exhausted FSCRATCH file quota.

⚠ **This does not clear the FSCRATCH problem — it only stops the campaign
adding to it.** FSCRATCH remains **over its file soft quota with the grace
period running**, and the reclaim targets (`results/f4_topology`,
`results/isalsr`, the four other `repos/` checkouts) are for the user to prune;
this wave deliberately deleted nothing there. The only FSCRATCH deletion made
was the now-empty `fscratch/results/IEEETKDE/` directory, after its `_smoke/`
contents were `mv`-ed to the new HOME root.

Consequences for every wave-3 launcher regardless:

- Project `N_tasks × (artefacts_per_task + 2 log files)` **before** submitting,
  and `count_files` the output directory afterwards. HOME's file quota is
  35.0k — far more headroom than FSCRATCH had, but not unlimited, so a launcher
  that would write tens of thousands of small artefacts must consolidate.
- Prefer one consolidated artefact per unit over five small ones.
- Harvest each RQ to the local drive as it completes; the local drive remains
  the copy a paper cites.
- The manual asks you to contact `soporte@scbi.uma.es` before the first array
  over 1000 jobs; given the FSCRATCH state, contact them earlier than that.

### Scheduler and entitlements

| Item | Value |
|---|---|
| `MaxArraySize` | 4096 (largest index 4095) |
| `MaxJobCount` | 15000 |
| QOS available | `short`, `medium_uma`, `long_uma` (accounts `tic_163_uma`, `mpascual`) |
| Queue at probe time | 2411 jobs, 40 users, R:1860 / PD:551, 24422 CPUs busy |
| Pre-existing job | `2132239` (`t28f2m`, PD, `JobHeldAdmin`) — not ours to touch |

`squeue -u` is **rejected** by Picasso's Lua wrapper; bare `squeue` is already
scoped to the user.

`fscratch_files` is **not installed** on this host, so purged FSCRATCH files are
not self-recoverable. Do not plan around recovery.

### Node families relevant here

| Feature | Cores | RealMemory | AVX-512 |
|---|---|---|---|
| `sd` (Intel Xeon Gold 6230R @2.10 GHz) | 52 | 187,000 MB | **yes** |
| `sr` (AMD EPYC 7H12) | 128 | 450,000 MB | no |
| `bc` (AMD EPYC 9754) | 256 | 700,000 MB | yes |
| `bl` (AMD EPYC 7H12, fat) | 128 | 1,900,000 MB | no |

---

## 3. Toolchain and the ISA decision

### Compiler

| Item | Value |
|---|---|
| Login-node CPU | Intel Xeon Gold 6230R @ 2.10 GHz (an `sd` machine, AVX-512) |
| System compiler | `g++ (SUSE Linux) 7.5.0` |
| `gcc` modules available | up to `gcc/13.2.0` (`11.1.0`, `12.2.0`, `13.1.0`, `13.2.0`) |
| Compiler actually used | the system `g++ 7.5.0` — no `module load` |

### Build flags

Taken unchanged from the project's `CMakeLists.txt` (Release):

```
-O3 -march=native -DNDEBUG -fno-plt -funroll-loops -Wall -Wextra -Wpedantic
+ interprocedural optimisation (LTO) when CheckIPOSupported succeeds
```

PGO (`ISALHG_PGO_GENERATE` / `ISALHG_PGO_USE`) is **not** used. `CMakeLists.txt`
and `pyproject.toml` were not modified (out of scope for this wave).

### The ISA decision: `-march=native` + `--constraint=sd`

`-march=native` on the login node emits **AVX-512**, which `sr` and `bl` do not
implement. This is the classic build-once-run-anywhere trap on this cluster and
it has already cost this project a job array:

| Array | Constraint | Outcome |
|---|---|---|
| `2206615` | `sr` | **SIGILL on every task in 8 s** (AMD EPYC, no AVX-512) |
| `2206622` | `sd` | completed |

**Decision: keep `-march=native` and pin every TKDE job to `--constraint=sd`.**
Two reasons, and the second is the stronger one:

1. `sd` is the login node's own family, so the `.so` built there runs.
2. Several RQs report wall-clock. A mixed Intel/AMD pool (2.10 GHz Cascade Lake
   vs 2.60 GHz EPYC) turns any timing comparison into a measurement of the
   scheduler. Pinning costs queue time; not pinning costs the result.

`sd` availability is good in practice: `sbatch --test-only` on 2026-09-05
reported an immediate start on `sd039`, and the real submission started at once.

**Documented fallback**, if `sd` queue time ever becomes prohibitive:

```bash
cd ~/fscratch/repos/IsalHG-tkde
rm -rf build
CMAKE_ARGS="-DCMAKE_CXX_FLAGS=-march=haswell" \
    ~/fscratch/conda_envs/isalhg-tkde/bin/python -m pip install -e ".[dev]" --no-deps
```

then relax to `--constraint=cpu`. `-march=haswell` is the AVX2 baseline that all
four families implement; it is the *older spelling* of `-march=x86-64-v3`, which
matters because **GCC 7.5 rejects `-march=x86-64-v2/v3/v4`** (those
microarchitecture levels arrived in GCC 11) and the whole `pip install` fails
with `cc1plus: error: bad value ('x86-64-v3') for '-march=' switch`. Taking this
fallback **invalidates every wall-clock number measured under `-march=native`**;
re-measure the timing arms, do not mix.

**A third option, not taken:** Picasso's `sbatch` wrapper prints a banner
recommending `avx512` over `sd`. `--constraint=avx512` would widen the pool to
`sd` + `bc`. It is plausible that a Cascade-Lake `-march=native` binary runs on
`bc` (EPYC 9754 implements the AVX-512 subsets Cascade Lake emits), but that is
**unverified** and it reintroduces the mixed-CPU timing confound. If it is ever
wanted, prove it with a smoke job pinned to `bc` first.

---

## 4. Environment contents

Created by cloning the pre-existing `isalhg` env (the one the F4 probe used),
then installing on top. Measured versions after setup:

| Package | Version |
|---|---|
| Python | 3.11.15 |
| pynauty | 2.8.8.1 |
| rapidfuzz | 3.14.5 |
| numpy | 2.4.6 |
| scikit-learn | (from clone; `joblib` 1.5.3, `threadpoolctl` 3.6.0) |
| pyarrow | 25.0.1 |
| netlsd | 1.0.2 |
| kmedoids | 0.5.5 |
| nanobind | 2.13.0 |
| scikit-build-core | 0.12.2 |
| cmake (pip) | 4.4.3 |
| ninja | 1.13.0 |
| pytest | 9.1.1 |
| hypothesis | 6.155.6 |
| isalhg | 0.0.1 (editable, from `IsalHG-tkde`) |

Compute nodes have **no outbound internet**: every install runs on the login
node via `scripts/tkde/picasso_env_setup.sh`.

### The extension's import name

The compiled module is **`isalhg.core._core`**, not `isalhg.core._native`.
`CMakeLists.txt` builds target `_core` and installs it to `isalhg/core`;
`src/isalhg/core/_native/` is the **C++ source directory** and is not an
importable Python module. `CODE_PLAN.md` §4 says `_native`; that is a naming
error in the plan, and the smoke test checks the real module. Verified path:

```
…/conda_envs/isalhg-tkde/lib/python3.11/site-packages/isalhg/core/_core.cpython-311-x86_64-linux-gnu.so
```

An editable install puts the extension in **site-packages**, not in the repo, so
a repo-local `find` will never reveal a stale one. `sync_to_picasso.sh` asserts
the `.so` mtime post-dates the sync for exactly this reason.

---

## 5. Staged data

`~/fscratch/datasets/isalhg_tkde/raw/`, 24 files, 16 MB. **All 24 md5sums match
the local originals** (`md5sum` on both sides, sorted, `diff` clean).

| Subtree | Source |
|---|---|
| `wd50k_66/` | `/media/mpascual/Sandisk2TB/…/isalhg/data/wd50k_66/` |
| `wd50k_100/` | `…/data/wd50k_100/` |
| `wd50k/` (incl. `types/p31_types.tsv`, md5 `34861083c50bda0b321ec8b063e19656`) | `…/data/wd50k/` |
| `arb_benson/temporal/NDC-classes/` | `…/data/arb_benson/temporal/NDC-classes/` |
| `arb_benson/temporal/NDC-substances/` | `…/data/arb_benson/temporal/NDC-substances/` |

`corpora/` is created empty; `kb-corpora` produces it later and
`sync_to_picasso.sh --corpora` pushes it (skipping cleanly when the local
directory does not exist).

File-count impact: 24 data files + 771 repo files ≈ 0.8k, negligible against the
19k FSCRATCH headroom. The *results* of the campaign are what will consume it.

---

## 6. The smoke job

`slurm/tkde/smoke_worker.sh`: 4 CPUs, 8 GB, 30 min, `--constraint=sd`,
`--account=tic_163_uma`. The **only** job in the campaign permitted under two
hours (SCBI's floor, 2026-08-07); its whole value is finishing fast, before real
work is queued.

| Job | Node | Elapsed | Result |
|---|---|---|---|
| `2210890` | sd039 | 00:02:02 | **FAILED** — 361 passed, 2 failed (see below) |
| `2210893` | sd030 | **00:07:02** | **COMPLETED** — all checks green, 363 passed |
| `2210916` | sd089 | **00:06:15** | **COMPLETED** — re-validation after the results root moved to HOME (§6.1) |

`seff 2210893`: `State: COMPLETED (exit code 0)`, CPU Utilized 00:21:45, Memory
Utilized **59.88 MB** — 0.73 % of the 8 GB requested. The smoke job's own
footprint is trivial; wave-3 arms must size `--mem` from their **own** measured
`MaxRSS`, not from this row.

The successful run takes ~5 min longer than the failed one because the STS
catalog is now present: `test_wstar_c_frozen.py` actually computes `w*_c` on both
true STS(13) systems (the slow-marked pins) instead of erroring out immediately.
The 30 min wall has ~4× headroom over the measured 6m39s.

### What `2210890` found — an rsync exclude bug

`sync_to_picasso.sh` excluded `data/` **unanchored**, and rsync matches such a
pattern at any depth. It therefore dropped the packaged STS catalog
`src/isalhg/datasets/data/sts/*.txt`, and
`tests/unit/core/test_wstar_c_frozen.py::test_wstar_c_pinned_on_true_sts13`
failed with `FileNotFoundError: … /src/isalhg/datasets/data/sts/sts13.txt`.

This is precisely the failure the deployment was built to catch, and it would
have been invisible until an RQ silently ran on a repo with missing package
data. Two things it also demonstrated, positively:

- the `$LOCALSCRATCH` copy-back ran on the **failing** path
  (`[stage] copy-back OK -> …/IEEETKDE/_smoke`), so the EXIT trap works;
- the pinned frozen-`w*_c` regression test is load-bearing.

**Fix:** every directory exclude is now root-anchored (`/data/`, `/build/`,
`/results/`, `/outputs/`, `/.claude/worktrees/`, …); only the cache/artefact
patterns (`**/__pycache__/`, `*.pyc`, `*.so`, `*.egg-info/`) stay
depth-independent. **Verified by listing both trees and diffing**: 771 local
files under the sync filter, **zero** present locally and missing remotely. The
only remote-only entries are `.pytest_cache/` artefacts the failed run wrote.

### `2210893` — the accepted run

Verbatim check lines from
`~/execs/tkde/logs/tkde-smoke_2210893.out`:

```
Node:          sd030
CPU model:     Intel(R) Xeon(R) Gold 6230R CPU @ 2.10GHz
CPUs/task:     4   threads=4
Deployed:      sha=7590df4 branch=worktree-agent-a57a0919d0e693ba9 …
Python:        …/fscratch/conda_envs/isalhg-tkde/bin/python

[PASS] isalhg_package_path: /mnt2/fscratch/users/tic_163_uma/mpascual/repos/IsalHG-tkde/src/isalhg/__init__.py
[PASS] cpp_extension_import: …/site-packages/isalhg/core/_core.cpython-311-x86_64-linux-gnu.so
[PASS] canonical_cpp_eq_python: w*_c(Fano) len=121 cpp==python
[PASS] pynauty_canon_label: canon_label on Fano Levi, 14 nodes
[PASS] rapidfuzz: rapidfuzz 3.14.5

======================= 363 passed in 389.63s (0:06:29) ========================
PYTEST EXIT: 0
ALL SMOKE CHECKS PASSED
Finished:  2026-09-05T13:20:51+02:00
Duration:  0h 6m 39s
[stage] copy-back OK -> …/results/IEEETKDE/_smoke
```

Harvested to `…/results/IEEETKDE/_smoke/` locally: `provenance.txt`,
`pytest_unit_core.txt`, `smoke_checks.txt`, `smoke_report.json`.

### 6.1 `2210916` — re-validation of the HOME results root

The move in §2.1 changes where every job writes, so it was **exercised, not
assumed**: one further smoke job after the change.

| Field | Value |
|---|---|
| Job | `2210916` (`--test-only` first: `2210915`, immediate start) |
| Node | `sd089` (Xeon Gold 6230R) |
| Elapsed | 00:06:15 |
| State | **COMPLETED** |
| Tests | 363 passed in 353.92 s, `PYTEST EXIT: 0` |

```
[stage] copy-back to : /mnt/home/users/tic_163_uma/mpascual/results/IEEETKDE/_smoke
[PASS] isalhg_package_path / cpp_extension_import / canonical_cpp_eq_python
[PASS] pynauty_canon_label / rapidfuzz
======================= 363 passed in 353.92s (0:05:53) ========================
PYTEST EXIT: 0
ALL SMOKE CHECKS PASSED
Duration:  0h 6m 5s
[stage] copy-back OK -> /mnt/home/users/tic_163_uma/mpascual/results/IEEETKDE/_smoke
```

HOME results tree afterwards:

```
/mnt/home/users/tic_163_uma/mpascual/results/IEEETKDE/_smoke:
-rw-r-----  272 Sep  5 13:50 provenance.txt
-rw-r----- 2620 Sep  5 13:50 pytest_unit_core.txt
-rw-r-----  571 Sep  5 13:44 smoke_checks.txt
-rw-r-----  762 Sep  5 13:44 smoke_report.json
```

`provenance.txt` also confirms the `.tkde_deploy` fix (it read `git=n/a` before):

```
node=sd089
cpu=Intel(R) Xeon(R) Gold 6230R CPU @ 2.10GHz
job=2210916
deploy=sha=e6bd84b branch=worktree-agent-a57a0919d0e693ba9 at=2026-09-05T13:43:20+02:00
date=2026-09-05T13:50:08+02:00
```

`fscratch/results/IEEETKDE/` was emptied by `mv`-ing its `_smoke/` to the new
root and then `rmdir`-ed. `fscratch/results/` still holds `f4_topology` and
`isalsr`, untouched.

Harvest re-run against the new root: `--dry-run` listed the four files, the real
run pulled them into
`/media/mpascual/Sandisk2TB/…/results/IEEETKDE/_smoke/`.

---

Re-run the smoke job after **any** environment change — a dependency bump, a
rebuild, a change to `common.sh`. Environment self-checks passing on the login
node is not evidence that a compute node will run the job.

---

## 6.2 Wave-3 campaign jobs (2026-09-05)

The provenance reference for every wave-3 result on HOME.

| Job | Id |
|---|---|
| RQ7 envelope | `2215078` |
| RQ2 well-posedness, main | `2215097` |
| RQ2 well-posedness, census | `2215136` |
| RQ1 addressing | `2215137` |
| RQ3 + RQ6 bundle | `2215096` |
| RQ5 patterns | `2215162` |
| RQ4 screen | `2215168` |

Four operational facts measured while placing them.

**Payloads run backgrounded.** Bash defers EXIT/TERM traps while it waits on a
foreground child, so `scancel` on job `2213210` killed the step before
`tkde_finalize` ran and fourteen minutes of rows died on the node. Every worker
now routes its payload through `tkde_run_synced` (`common.sh`), which
backgrounds it and mirrors the staged tree back every `TKDE_SYNC_INTERVAL_S`
(default 300 s) — the trap can then run, and a TIMEOUT or an OOM kill costs at
most one interval.

**Row files carry a run tag.** Campaign rows are
`rows_<table>__<8hex>-<unit>.csv`, the prefix being a hash of the parameters
that decide what the unit measures. The analyzers skip untagged files and any
path under `_smoke*`; smokes stage in their own subtree because they share the
campaign's unit-id namespace and would otherwise mark a unit done with five toy
members.

**Job records are purged.** `--dependency=afterok:<id>` on a job Slurm has
already forgotten is rejected at submission with `Job dependency problem`.
Check with `sacct -j <id>` before anchoring a dependency on it — an empty
listing means the record is gone, not that the job failed.

**Memory: read the `.batch` step.** `sacct -X` reports an empty `MaxRSS`
(accounting records memory on `.batch`; `-X` shows allocation lines only).
Measured peaks: the matrices job `2213202` at **34.2 GB**, the RQ3+RQ6 bundle at
**20.4 GB**. The RQ6 figure was cache growth across the units of one bundled
task, fixed by refitting per unit rather than by raising the request.

---

## 7. Deviations from the wave-1 brief

| # | Brief said | Reality | Resolution |
|---|---|---|---|
| 1 | check `import isalhg.core._native` | the module is `isalhg.core._core`; `_native` is the C++ source dir | smoke test checks `_core`; recorded in §4 |
| 2 | conda env under `~/.conda/envs` | Picasso envs live in `~/fscratch/conda_envs` | `common.sh` uses the measured location |
| 3 | logs with `%A_%a` | on a **non-array** job `%a` expands to the sentinel `4294967294` (log `tkde-smoke_2210890_4294967294.out`) | smoke launcher uses `%j`; arrays keep `%A_%a` |
| 4 | `pip install -e ".[dev]" --no-deps` | first attempt adds `--no-build-isolation` (the backend is installed in-env) | falls back to isolated build automatically; exit status read directly, never through a pipe |
| 5 | job header carries "git SHA of `$REPO_DIR`" | the deployed tree has no `.git` (rsync excludes it) | `sync_to_picasso.sh` stamps `.tkde_deploy` (sha, branch, source, timestamp); the header prints it |

Nothing outside the owned file set and the named remote paths was modified.
`CMakeLists.txt`, `pyproject.toml` and all Python sources are unchanged.

---

## 8. Reproducing this environment from scratch

```bash
# local
bash scripts/tkde/sync_to_picasso.sh                       # deploy + rebuild + verify
ssh picasso 'bash ~/fscratch/repos/IsalHG-tkde/scripts/tkde/picasso_env_setup.sh'

# prove it on a compute node
ssh picasso 'bash ~/fscratch/repos/IsalHG-tkde/slurm/tkde/smoke_launcher.sh --test-only'
ssh picasso 'bash ~/fscratch/repos/IsalHG-tkde/slurm/tkde/smoke_launcher.sh'

# bring results home (never deletes local files)
bash scripts/tkde/harvest_from_picasso.sh --dry-run
bash scripts/tkde/harvest_from_picasso.sh
```

`picasso_env_setup.sh --recreate` rebuilds the env from zero;
`--skip-deps` rebuilds only the extension.
