# T-KBac — a worker must not report success on an empty copy-back

**Status:** OPEN (2026-09-14 09:34 CEST) · declared by agent `rq8`, wave
`2026-09-13-headline-w0`, on the orchestrator's instruction after the RQ2_ow
loss. Owner: the next wave that may edit `slurm/tkde/common.sh`.

## The failure this prevents

`tkde_finalize` prints `[stage] copy-back OK` whenever the mirror command
succeeds. **Mirroring an empty tree succeeds.** A task that produced no rows is
therefore indistinguishable in its log from one that worked: same banner, same
"copy-back OK", exit 0, `COMPLETED` in `sacct`.

Measured 2026-09-13, jobs **2308342** (13 tasks) and **2308343** (9 tasks),
RQ2_ow. All 22 tasks ran their units — the logs carry real work, e.g.
`unit bipartite-wd50k66 done in 8198.7 s: {'bipartite': 9000}` — all 22 printed
`copy-back OK`, 21 reported `COMPLETED`, and
`~/results/IEEETKDE_ow/RQ2_wellposedness/wellposedness_ow` held **zero files**.
About 7 wall-hours of work was discovered lost only because the harvest counted
rows. Nothing in SLURM, in the logs, or in the exit codes said anything was
wrong.

The proximate cause was specific (`rq2.py` builds its output path from the
module constant `EXPERIMENT`, not from the config key, so a worker that renamed
the experiment symlinked a directory the runner never wrote to — fixed in
`rq2_ow_worker.sh` and pinned by
`tests/experiments_tkde/test_rq8_ow_worker_paths.py`). The **general** hazard is
not: any future mismatch between where a runner writes and where a worker stages
produces the same silent, successful-looking empty run.

## What to add

A guard in `slurm/tkde/common.sh`, called by `tkde_finalize` before it prints
its success line — or exposed as a function every worker calls before teardown:

```bash
tkde_assert_out_dir_not_empty() {
    local n
    n=$(find "${OUT_DIR}" -name 'rows_*.csv' 2>/dev/null | wc -l)
    if [[ "${n}" -eq 0 ]]; then
        echo "[FATAL] ${OUT_DIR} holds no rows_*.csv after the payload ran." >&2
        echo "        The copy-back would mirror an empty tree and report OK." >&2
        find "${MYLOCALSCRATCH}" -name 'rows_*.csv' 2>/dev/null | head -5 >&2
        exit 1
    fi
    echo "[ok] ${n} row file(s) staged in ${OUT_DIR}"
}
```

The `find` over `${MYLOCALSCRATCH}` is the diagnostic half: it prints where the
rows actually went, which is exactly the question a reader has at that moment.

This agent has **already implemented it locally** in the two workers it owns —
`slurm/tkde/rq8_worker.sh` and `slurm/tkde/rq2_ow_worker.sh` — because
`common.sh` is read-only to it. Both carry a comment pointing here. The work is
to move it to `common.sh` and delete the two copies.

## Design points for whoever lands it

- **Opt-out, not opt-in.** A worker that legitimately produces no rows (a pure
  smoke, a `--count` probe) should set an explicit `TKDE_ALLOW_EMPTY_OUT=1`
  rather than the guard defaulting off. The failure mode being prevented is
  silence, so silence must not be the default.
- **Call it before the trap, not inside it.** Running it inside `tkde_finalize`
  works but the EXIT trap's own failure is easy to lose; calling it at the end
  of the payload section gives a clean non-zero exit and a readable log.
- **`rows_*.csv` is the right pattern for this campaign** but the guard should
  take the glob as an argument so a future experiment writing `.npy` or `.json`
  artefacts can use it.
- Consider pairing it with a positive check that the staged tree is the one
  mirrored: `readlink -f` of the experiment directory must resolve under
  `${MYLOCALSCRATCH}/out`. `rq2_ow_worker.sh` has that too.

## Context

- The RQ2_ow diagnosis and the per-worker fix: `T-KBab.md`, and the header
  comment of `slurm/tkde/rq2_ow_worker.sh`.
- The regression that pins the specific coupling:
  `tests/experiments_tkde/test_rq8_ow_worker_paths.py`.
- `slurm/tkde/README.md` already documents the 2026-09-07 sibling incident
  ("wrote its rows to an unlinked `addressing` directory on node scratch and
  lost them"). That paragraph was read and the defect was reintroduced anyway,
  which is the argument for a mechanical guard over a documented caution.
