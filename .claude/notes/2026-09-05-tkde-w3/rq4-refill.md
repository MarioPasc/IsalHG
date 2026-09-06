# rq4-refill — HPD arm refill on the 266 censored RQ4 cells

Agent: `rq4-refill` (wave `2026-09-05-tkde-w3`, orchestrator `main`).
Date: 2026-09-06. All work done in a PRIVATE deployment + PRIVATE env; the
shared checkout `~/fscratch/repos/IsalHG-tkde` and the shared env
`isalhg-tkde` were never written to.

## 1. What was wrong, and what the refill does

The vendored hyperedge-portrait code allocated the portrait's last axis with
extent `N` while the histogram it fills is indexed up to `max(1, N - 1)`; on a
3-fact record (`N = 1`) that is an out-of-bounds write and the `hpd_jsd` arm
raised. RQ4's `_row_worker` wrote `censored=1` instead of a number.

Measured baseline on `~/results/IEEETKDE/RQ4_screen/rows` (before any change):

```
auc files: 1291
total rows per arm: {fact_rank 2582, nauty_cert 2582, wl_l1 2582, netlsd 2582,
                     hpd_jsd 2582, bipartite_ged_path 2582, degree_seq_l1 2582,
                     size_l1 2582}
censored per arm:   {hpd_jsd: 266}      <- the only censored arm
units with any censored row: 133        (2 scores per unit -> 266 rows)
censored units by sub-collection: ndc_classes 27, wd50k66_Q5 27,
    wd50k66_Q11424 27, wd50k66_Q1549591 27, wd50k66_Q5398426 15,
    wd50k66_Q202866 9, wd50k66_Q3624078 1
censored units by cell: missing_fact_b2 133      (single cell, as expected)
```

The library fix (`max(N, 2)` in
`src/isalhg/metric_space/representations/_hpd_vendor.py`) is on
`integration/2026-09-05-tkde-w1` at local HEAD `4d192d9`.

## 2. Private deployment

```
rsync -az --delete --info=stats1 \
  --exclude '/.git/' --exclude '/build/' --exclude '**/__pycache__/' --exclude '*.pyc' \
  --exclude '*.so' --exclude '*.egg-info/' --exclude '/.pytest_cache/' --exclude '/.mypy_cache/' \
  --exclude '/.ruff_cache/' --exclude '/.claude/worktrees/' --exclude '/.claude/notes/' \
  --exclude '/data/' --exclude '/results/' --exclude '/outputs/' --exclude '/experiments/outputs/' \
  -e "ssh -o ServerAliveInterval=60" \
  /home/mpascual/research/code/IsalHG/ \
  picasso:/mnt/home/users/tic_163_uma/mpascual/fscratch/repos/IsalHG-tkde-refill/
# sent 27,207,567 bytes; 1231 files on the remote side
```

Stamp written in the same format the other deployments carry
(`IsalHG-tkde-rq45` was `sha=3b7ee68 branch=worktree-agent-... from=worktree at=...`):

```
$ cat ~/fscratch/repos/IsalHG-tkde-refill/.tkde_deploy
sha=4d192d9 branch=integration/2026-09-05-tkde-w1 from=/home/mpascual/research/code/IsalHG (rq4-refill agent) at=2026-09-06T08:02:28+02:00
```

FSCRATCH file quota at the time: 256.5k used / 250.0k soft / 400.0k hard,
6 days of grace already running. The deployment added 1231 files (docs included
— the excludes are the sync script's, unmodified) and the env clone added
~20k inodes (see below). Both stay well under the 400k hard limit; nothing else
was written to FSCRATCH.

## 3. Private env

Conda envs live in `~/fscratch/conda_envs`, not `~/.conda/envs` (common.sh
§Python interpreter). Clone:

```
source /mnt/home/soft/miniconda/programs/x86_64/miniconda3_py310_23.1.0/etc/profile.d/conda.sh
conda create -y -p ~/fscratch/conda_envs/isalhg-tkde-refill --clone isalhg-tkde
# -> Python 3.11.15
```

**One repair was needed.** The clone produced a broken `pip`: the source env's
pip had been upgraded by pip itself (26.2.1) over the conda-managed package, and
`conda create --clone` reassembled a mixture of both versions —
`ImportError: cannot import name 'get_runnable_pip' from
'pip._internal.utils.misc'`. Fixed inside the PRIVATE env only:

```
rm -rf $ENVP/lib/python3.11/site-packages/pip $ENVP/lib/python3.11/site-packages/pip-*.dist-info
$PY -m ensurepip --upgrade      # pip 24.0
$PY -m pip install --upgrade pip # pip 26.2.1, matching the shared env
```

Build, exactly as `picasso_env_setup.sh` step 4 (deps skipped — the clone
carries them), on the Intel login node so `-march=native` matches
`--constraint=sd`:

```
cd ~/fscratch/repos/IsalHG-tkde-refill && rm -rf build
$PY -m pip install -e ".[dev]" --no-deps --no-build-isolation
# PIP EXIT: 0 ; Successfully installed isalhg-0.0.1
```

Login-node verification:

```
isalhg     : /mnt2/fscratch/users/tic_163_uma/mpascual/repos/IsalHG-tkde-refill/src/isalhg/__init__.py
extension  : .../conda_envs/isalhg-tkde-refill/lib/python3.11/site-packages/isalhg/core/_core.cpython-311-x86_64-linux-gnu.so
built at   : 2026-09-06T08:04:56
hpd fix    : max(N, 2) present in hyperedge_portrait
verify     : cpp == python OK   (fano_plane canonical string)
```

`isalhg` resolves through the refill tree's editable finder — which is the
whole point: the shared env's finder points at `IsalHG-tkde`, which does not
carry the fix.

## 4. Sizing and the shard structure

`--count` returns 1323 (the full unit grid) regardless of refill mode, so the
work was sized from disk. Per-shard census with the runner's own enumeration
(`enumerate_units` + `matrices.shard_bounds`):

```
shard 0/3 units[0,441)     -> 45 censored units,  90 rows
shard 1/3 units[441,882)   -> 44 censored units,  88 rows
shard 2/3 units[882,1323)  -> 44 censored units,  88 rows
TOTAL 133 units, 266 rows
shard_{0,1,2}_3/manifest.json all exist
```

**Why the job runs three sharded passes rather than one un-sharded pass.**
`rq4._shard_manifest_stamp` reads
`RQ4_screen/shard_<tag>/manifest.json` to fill the refill manifest's
`refilled_from` — the provenance of the seven arms the refill does NOT touch.
Un-sharded, `shard_tag` is `all`, `shard_all/manifest.json` does not exist, and
`refilled_from` would be `null`. Sharded 0/3, 1/3, 2/3 it matches the three
manifests the original run wrote.

**`refilled_from` is a manifest field, not a row column.** `ROWS_AUC_COLUMNS` is
unchanged by a refill (the rewritten rows are byte-shaped like the originals,
with `censored=0`), so "266 rows with `refilled_from` set" is not checkable per
row; the provenance lives in
`RQ4_screen/refill_hpd_jsd_<i>_3/manifest.json`.

## 5. The worker

Deploy-only, at
`~/fscratch/repos/IsalHG-tkde-refill/slurm/tkde/rq4_refill_worker.sh`
(NOT committed; the orchestrator decides). Verbatim copy kept at
`<scratchpad>/rq4_refill_worker.sh`. Its two non-obvious decisions:

- **No `tkde_stage_localscratch`.** `refill_unit` READS
  `<out>/RQ4_screen/rows/rows_auc__<unit>.csv`, drops the arm's rows, re-scores
  and REWRITES the same file. Pointed at an empty node scratch it would find no
  AUC files, refill nothing, report success and copy an empty tree back. `--out`
  is therefore `${ISALHG_RESULTS_ROOT}` and the runner writes in place on HOME.
  `tkde_run_synced` is kept anyway (backgrounds the payload so SIGTERM is
  serviced; `tkde_sync_partial` is a documented no-op when nothing was staged).
- **A compute-node import assertion before any write.** A wrong `isalhg` would
  re-score the arm with the UNFIXED vendor and write plausible, wrong numbers
  over the censored ones — worse than the censoring. The job asserts
  `/IsalHG-tkde-refill/` in `isalhg.__file__` (directory name, never a prefix
  match on `$REPO_DIR` — `~/fscratch` is a symlink to `/mnt2/...`), imports
  `isalhg.core._core`, and asserts `max(N, 2)` in
  `inspect.getsource(hyperedge_portrait)`.

Resources: `--time=0-04:00:00 --ntasks=1 --cpus-per-task=8 --mem=48G
--constraint=sd --account=tic_163_uma`. One recovery job, exempt from the
campaign's 2 h task floor.

## 6. Jobs

`sbatch --test-only` → `Job 2215538 to start at 2026-09-06T13:59:52 using 8
processors on nodes sd008 in partition cpu_partition`.

### Smoke — job 2215545, COMPLETED in 00:05:18 (node sd008)

`TKDE_REFILL_SMOKE=1`, `--time=0-00:30:00`. It runs the compute-node import
chain, the vendor's own regression suite, and the runner's refill code path
under `--tag _smoke_refill` (whose `rows/` holds no AUC files, so every unit is
skipped and nothing in the real tables is touched).

```
isalhg     : /mnt2/fscratch/.../IsalHG-tkde-refill/src/isalhg/__init__.py
extension  : .../isalhg-tkde-refill/.../_core.cpython-311-x86_64-linux-gnu.so
built at   : 2026-09-06T08:04:56
hpd fix    : max(N, 2) present in hyperedge_portrait
[smoke] hpd regression suite
tests/unit/metric_space/test_hpd_single_hyperedge.py .........ssssssss  [ 56%]
tests/unit/metric_space/test_hpd.py ............s                       [100%]
21 passed, 9 skipped in 2.34s
[smoke] refill dry pass under _smoke_refill (expects 0 units rewritten)
refill: 0 unit(s) of 441 rewritten for arm hpd_jsd
```

Only artefact: `RQ4_screen/_smoke_refill/refill_hpd_jsd_0_3/manifest.json`.

### Real refill — job 2215571

Submitted with `TKDE_SYNC_INTERVAL_S=60` (the default 300 s adds a full sleep
interval to each of the three sequential passes).

```
$ sacct -j 2215571 -X -n -P -o JobID,State,Elapsed,ExitCode
2215571|COMPLETED|00:18:11|0:0        node sd086, 8 cpus, 48 G
```

Three sequential passes, ~6 min each (the per-shard cost is dominated by the
corpus + matrix-cache load, not by HPD itself):

```
refill: 45 unit(s) of 441 rewritten for arm hpd_jsd   (shard 0/3)
refill: 44 unit(s) of 441 rewritten for arm hpd_jsd   (shard 1/3)
refill: 44 unit(s) of 441 rewritten for arm hpd_jsd   (shard 2/3)
-> 133 units, exactly the censored set counted before the run
```

Manifests written: `RQ4_screen/refill_hpd_jsd_{0,1,2}_3/manifest.json`, each
with `refilled_arm=hpd_jsd`, `n_units_refilled=45/44/44`,
`n_units_examined=441`, and

```
"refilled_from": "sha=9f973af branch=integration/2026-09-05-tkde-w1 from=/home/mpascual/research/code/IsalHG at=2026-09-05T18:29:52+02:00"
"runner_deploy": "sha=4d192d9 ... (rq4-refill agent) at=2026-09-06T08:02:28+02:00"
```

## 7. Verification

A BEFORE snapshot was taken over the whole rows tree so that "no other arm
changed" is checkable byte-for-byte rather than by mtime:

```
{"n_auc_files": 1291,
 "n_other_arm_rows": 18074,
 "sha_other": "78b72cb8d17348c29f720a8363965ec520a2c7fb10ac3444e374c737097fbd90",
 "n_hpd_rows": 2582,
 "sha_hpd": "69fa287bb538da8362fecf26b0b7e0ea194b860629a186172f7415807e287734",
 "n_nonauc_files": 1323,
 "sha_nonauc": "74e908a237eaab5152513cbfaa22766edd3ee223eecc6af055828651863d130f"}
```

(`sha_other` is the SHA-256 of every non-`hpd_jsd` AUC row in file-sorted
order; `sha_nonauc` covers every `rows_anomalies__*` / other row file.)

AFTER, recomputed the same way:

```
AFTER  auc files      : 1291 (before 1291)
AFTER  rows per arm   : {fact_rank 2582, nauty_cert 2582, wl_l1 2582, netlsd 2582,
                         hpd_jsd 2582, bipartite_ged_path 2582, degree_seq_l1 2582,
                         size_l1 2582}
AFTER  censored       : NONE          <- was {hpd_jsd: 266}

non-hpd arm rows      : 18074 == 18074            True
non-hpd sha UNCHANGED : True     (78b72cb8...)
non-auc files         : 1323 == 1323              True
non-auc sha UNCHANGED : True     (74e908a2...)
hpd row count         : 2582 == 2582              True
hpd sha CHANGED       : True
```

So: **0 censored rows remain on any arm**, the 266 that were censored are now
scored, the `hpd_jsd` row COUNT is unchanged (rows were replaced, not added),
and every one of the 18,074 rows of the other seven arms plus all 1,323
non-AUC row files is byte-identical to before the job.

Spot check of a refilled unit (`ndc_classes__missing_fact_b2__seed40000`) —
real numbers, `censored=0`, in range:

```
{'arm': 'hpd_jsd', 'score': 'knn', 'auc': '0.61313074407918',  'censored': '0'}
{'arm': 'hpd_jsd', 'score': 'lof', 'auc': '0.8151234977023682','censored': '0'}
16 rows in the file, auc range 0.406 .. 0.836
```

## 8. Out of scope — for the orchestrator

- **The three refill manifests record a WRONG `src_deploy`.** Each says
  `src_deploy = sha=9f973af ...`, the stamp of the SHARED
  `~/fscratch/repos/IsalHG-tkde` tree — but the library that computed the
  refilled rows was the private `IsalHG-tkde-refill` tree at `4d192d9` (the job
  asserted this on the compute node before writing anything, and
  `IsalHG-tkde` does not carry the HPD fix at all). Cause:
  `experiments/tkde/matrices.py::deploy_stamps` reads a hard-coded
  `SRC_DEPLOY_STAMP` pointing at the shared checkout, with no environment
  override — unlike `experiments/tkde/rq1.py::deploy_stamps`, which honours
  `$ISALHG_SRC_REPO` (default the same path). rq4 imports the `matrices`
  version. I did NOT hand-edit the manifests. Two clean options: teach
  `matrices.deploy_stamps` to honour `$ISALHG_SRC_REPO` (one line, matches
  rq1), or correct the three files deliberately. The correct value is the
  `runner_deploy` string already in each manifest.
  Note `refilled_from` is unaffected — it is *meant* to be the shared tree's
  stamp (the provenance of the seven arms the refill did not touch).

- **32 units have `rows_anomalies__*.csv` but no `rows_auc__*.csv`** (1291 AUC
  files vs 1323 units vs 1323 non-AUC files). First few:
  `wd50k66_Q5398426__iso_twin_b1__seed40000`,
  `wd50k66_Q3624078__iso_twin_b1__seed40000`,
  `wd50k66_Q202866__iso_twin_b1__seed40003`,
  `wd50k66_Q202866__iso_twin_b1__seed40006`. Pre-existing, unrelated to HPD,
  untouched by this job. A resume pass of the ordinary RQ4 array would fill
  them (`_unit_done` keys on the AUC file). Not investigated.
- **`slurm/tkde/rq4_refill_worker.sh` exists only in the private deployment.**
  If it should be committed, take it from `<scratchpad>/rq4_refill_worker.sh`.
- **The pip breakage in `conda create --clone isalhg-tkde`** will recur for any
  future clone of that env (the shared env's pip is pip-upgraded over the
  conda-managed one). The repair is in §3.
- **Assets created, safe to delete when the wave closes:**
  `~/fscratch/repos/IsalHG-tkde-refill`,
  `~/fscratch/conda_envs/isalhg-tkde-refill`,
  `~/results/IEEETKDE/RQ4_screen/_smoke_refill/`, and (removed by this agent
  after verification) `~/results/IEEETKDE/.rq4_refill_before.json`.
