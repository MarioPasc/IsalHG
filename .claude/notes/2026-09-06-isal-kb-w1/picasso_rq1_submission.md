# Picasso RQ1 Submission — 2026-09-07

## Summary

Synced branch `feature/isal-kb-word` (HEAD `0ea59e2`) to Picasso, rebuilt the
editable install, ran the smoke, and submitted the RQ1 array.

Two mid-task scope changes applied before submission:
1. A new commit (`2ccc9fa`, budget.py displacement-tuple guard) was already on
   the branch at sync time — picked up automatically.
2. `wstar_rank` was commented out of `rq1.yaml` (both `arms:` and `smoke: arms:`)
   with note "defective engine; re-run after the C++ port" — committed as
   `0ea59e2` before the final sync.

Memory flag: `--mem=12G` was already in `rq1_worker.sh` (≥ 8 GB required). No
change needed.

---

## Commands run (verbatim)

### 1. Quota check (before sync)
```
ssh picasso 'quota'
```
Result: FSCRATCH 276.1k / 250.0k (soft exceeded, 5 days grace) / 400.0k hard.
HOME 9.4k / 35.0k. Safe to proceed.

### 2. Sync + remote rebuild
```
bash scripts/tkde/sync_to_picasso.sh
```
From: `/home/mpascual/research/code/IsalHG` (sha `0ea59e2`)
To: `picasso:/mnt/home/users/tic_163_uma/mpascual/fscratch/repos/IsalHG-tkde`
Extension built at: `2026-09-07T09:54:08` — `verify: extension fresh, cpp == python OK`

### 3. Import verification (on cluster)
```
PYTHONPATH="$REPO/src:$REPO" $PY -c "
import isalhg, isalhg.core._core
from isalhg.metric_space.registry import get_distance
print(get_distance('isal_ow_struct').name, get_distance('wstar_rank').name)"
PYTHONPATH="$REPO/src:$REPO" $PY -c "import pynauty, rapidfuzz; print('OK')"
```
Output:
```
isal_ow_struct: isal_ow_struct
wstar_rank: wstar_rank
pynauty OK, rapidfuzz OK
```

### 4. Smoke job
```
ssh picasso 'REPO=.../IsalHG-tkde; cd "$REPO"; REPO_DIR="$REPO" bash slurm/tkde/rq1_launcher.sh --smoke'
```
Job 2247379 — COMPLETED 0:0 on `sd065` (Intel Xeon Gold 6230R) in 7m 13s.
Row files: 20 CSV files (M0-M4 on synthetic_rq1 + ndc_classes) + 4 control JSONs.
Results under: `$ISALHG_RESULTS_ROOT/RQ1_addressing/_smoke/addressing/`

Note: a first smoke (2247370) ran from old worktree `IsalHG-tkde-rq127` before the
scope changes. It also COMPLETED 0:0. Only 2247379 (from correct tree, correct
config) is the accepted smoke.

### 5. Quota check (after sync)
```
ssh picasso 'quota'
```
Result: FSCRATCH 276.2k (was 276.1k — +100 files from sync delta). HOME 9.4k.
Hard limit 400.0k; 123.8k headroom. No risk.

### 6. Full array submission
```
ssh picasso 'REPO=.../IsalHG-tkde; cd "$REPO"; REPO_DIR="$REPO" bash slurm/tkde/rq1_launcher.sh'
```
Output:
```
RQ1: 143 shards -> 48 tasks (bundle 3, throttle 16, wall 1-00:00:00)
Submitted RQ1 array 2247394 (48 tasks)
Submitted RQ1 recovery sweep 2247395 (afterany:2247394)
```

---

## Quota before / after

| Point | FSCRATCH files | HOME files |
|-------|---------------|------------|
| Before sync | 276.1k / 400.0k hard | 9.4k / 150.0k hard |
| After sync | 276.2k / 400.0k hard | 9.4k / 150.0k hard |

---

## Job IDs and array size

| Job | Type | Tasks | Status at submit |
|-----|------|-------|-----------------|
| 2247394 | RQ1 array | 48 | RUNNING (sd084 + others) |
| 2247395 | Recovery sweep | 48 | PD (afterany:2247394) |

Array: 143 shards, bundled 3-per-task → 48 array tasks. Wall: 1 day.
Throttle: 16 concurrent tasks.

---

## squeue output (at submission)

```
JOBID      NAME        USER      STATUS    TIMELEFT    CPUS/NODES  REASON
2247395    tkde-rq1    mpascual  [PD]      1-00:00:00  2/1         Dependency
2247394    tkde-rq1    mpascual  [R]       23:59:59    2/1         sd084
2247394    tkde-rq1    mpascual  [PD:79/R:15]  1-00:00:00  188   Dependency,JobArrayTaskLimit
```

---

## Results path (cluster)

```
/mnt/home/users/tic_163_uma/mpascual/results/IEEETKDE/RQ1_addressing/addressing/
```

Logs: `/mnt/home/users/tic_163_uma/mpascual/execs/tkde/logs/tkde-rq1_2247394_*.out`

---

## Harvest command

```bash
bash scripts/tkde/harvest_from_picasso.sh RQ1_addressing
```

Or a dry-run to preview:
```bash
bash scripts/tkde/harvest_from_picasso.sh --dry-run RQ1_addressing
```

---

## Config diff (rq1.yaml)

Two lines changed (wstar_rank commented out in both arms and smoke sections):
```diff
-  - wstar_rank             # the greedy walk keyed by nauty's rank
+  # - wstar_rank           # defective engine; re-run after the C++ port
```
```diff
-      wstar_rank,
+      # wstar_rank,         # defective engine; re-run after the C++ port
```

Commit: `0ea59e2` — "fix(tkde/rq1): remove wstar_rank from RQ1 submission arms"

---

## Notes / caveats

- The launcher's default `REPO_DIR` is hardcoded to `IsalHG-tkde-rq127` (an old
  worktree). Both smoke and array were submitted with `REPO_DIR=.../IsalHG-tkde`
  overridden in the environment. This should be fixed in the launcher for future
  waves.
- `wstar_rank` is absent from this run. Re-run after the C++ port lands and is
  merged to the branch.
- FSCRATCH remains over its soft quota (5-day grace). No FSCRATCH files were
  written by this campaign (results go to HOME per the 2026-09-05 decision).
- Array size is 48 tasks (< 1000), so no soporte contact required before this
  submission.
