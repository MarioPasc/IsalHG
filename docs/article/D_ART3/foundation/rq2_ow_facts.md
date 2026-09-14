# RQ2 on the ordered walk — fact base

*Derivation of record for the `w°` re-run of RQ2 (D-ART6, T-KBab). Written by
agent `rq8`, wave `2026-09-13-headline-w0`. Kept separate from the campaign's
own RQ2 fact base, which this agent does not own; the orchestrator folds it.*

## 1. Status — RUN IN FLIGHT, NO NUMBERS YET

**No RQ2_ow number exists as of 2026-09-14 09:45 CEST.** The census is not
complete and nothing in this file may be cited until §4 is filled. The first
attempt produced zero rows; the cause, the fix and the re-run are below, because
a fact base that records only the successful attempt teaches nobody anything.

## 2. Provenance

| what | where |
|---|---|
| config | `experiments/tkde/configs/rq2_ow.yaml` — identical to `rq2.yaml` but for `wstar_orbit` → `isal_ow_struct` |
| launcher / worker | `slurm/tkde/rq2_ow_{launcher,worker}.sh` (D-KBab2: the shared pair hard-codes its config path) |
| Picasso results | `~/results/IEEETKDE_ow/RQ2_wellposedness/wellposedness/` |
| drive mirror | `results/IEEETKDE_ow/RQ2_wellposedness/` (pending) |
| runner | `experiments/tkde/rq2.py`, **unmodified** — the arm set is config-driven |

## 3. Attempt history, and the two defects it found

**Attempt 1 — jobs 2308342 (13 main tasks) / 2308343 (9 census tasks),
2026-09-13. Result: 21 COMPLETED, 1 OUT_OF_MEMORY, and ZERO rows.**

Every task ran real work — `unit bipartite-wd50k66 done in 8198.7 s:
{'bipartite': 9000}` — and every task printed `[stage] copy-back OK`. The
destination directory was empty.

*Cause.* `experiments/tkde/rq2.py` line 997 builds its output path from a
**module constant**:

```python
paths = RunPaths(root=results_root, rq=RQ_FOLDER, experiment=EXPERIMENT)
```

`EXPERIMENT` is `"wellposedness"`; the config's `experiment:` key is never read.
The ow worker set `EXPERIMENT="wellposedness_ow"` for subtree separation and
symlinked that name into the mirrored `out/` tree, so the runner wrote to
`${STAGE_ROOT}/RQ2_wellposedness/wellposedness` — a plain directory on node
scratch, outside the tree `tkde_finalize` mirrors. The copy-back faithfully
mirrored an empty directory and reported success. **Mirroring an empty tree
succeeds**, so nothing anywhere said the run had failed. About 7 wall-hours lost.

This is the defect `slurm/tkde/README.md` already records for the 2026-09-07
rank run ("wrote its rows to an unlinked `addressing` directory on node scratch
and lost them"). Reading that paragraph did not prevent reintroducing it, which
is the argument for the mechanical guards below over a documented caution.

*Fix.* `EXPERIMENT="wellposedness"`, matching the runner's constant. Separation
from the `wstar_orbit` census never needed a directory rename: the results
**root** already differs (`~/results/IEEETKDE_ow` against the campaign's
`~/results/IEEETKDE`), and the run tag differs because the arm list does. Pinned
by `tests/experiments_tkde/test_rq8_ow_worker_paths.py` (8 tests), shown failing
against the pre-fix worker.

*Memory, separately.* Task 10 was `OUT_OF_MEMORY` at **31.4 GB** against a 32 G
request after 5 h 55 m, still climbing; the heaviest COMPLETED sibling (task 3)
peaked at **26.1 GB**. The bipartite units dominate. The main array now requests
**96 G**; the census keeps 32 G.

**Attempt 2 — jobs 2311493 / 2311494. Result: all 22 FAILED in seconds. My own
guard, and a false positive.**

The new symlink check compared `readlink -f` of the link (canonical) against the
raw `${MYLOCALSCRATCH}/out`. Picasso exports `LOCALSCRATCH` **with a trailing
slash**, so `MYLOCALSCRATCH` is `/localscratch/users//mpascual/<job>`;
canonicalising only the left-hand side made a correct layout look wrong. Fixed
by canonicalising both sides with `readlink -m`; reproduced and verified
locally, including that the guard still fires on a genuinely stranded directory.
Cost: seconds, not hours — which is the guard behaving as intended even while
being wrong.

**Attempt 3 — jobs 2311593 (main) / 2311604 (census), 2026-09-14. RUNNING.**
Both guards pass in the logs:

```
[ok] runner writes to RQ2_wellposedness/wellposedness
[ok] rows land in /localscratch/users/mpascual/2311594_0/out (mirrored)
```

## 4. The measured table — PENDING

To fill when 2311593 / 2311604 complete and the rows are harvested:

- [ ] **False merges** per arm per collection (`ndc_classes`, `ndc_substances`,
      `wd50k66`), with `isal_ow_struct` among them. Pre-stated expectation
      (Theorem C): **0 false merges, exact partition**, as for `wstar_orbit`.
- [ ] **Censoring contrast.** `wstar_orbit` dropped members at the 60 s budget —
      its `.censored.json` companions are 20–57 KB across the three collections.
      The ordered walk is expected to censor **none**, which is the measurable
      half of lifting D-ART4's restriction R2 for symmetry. This is the number
      the swap exists for.
- [ ] Exactness at zero (step 0) for `isal_ow_struct` on all three collections.
- [ ] Bipartite metricity, oracle ceiling and the HyperCOT timing row — these
      are arm-independent and should reproduce the campaign's values; any
      disagreement is a red flag about the run, not a finding.

## 5. Guards now in place

- `rq2_ow_worker.sh` asserts `experiments.tkde.rq2.{RQ_FOLDER, EXPERIMENT}`
  against its own shell variables **before any unit runs**, and asserts the
  symlink resolves inside the mirrored tree.
- Both `rq2_ow_worker.sh` and `rq8_worker.sh` refuse to reach the copy-back when
  the staged tree holds no `rows_*.csv`, printing where the rows actually went.
- `T-KBac` (OPEN) proposes moving that emptiness check into
  `slurm/tkde/common.sh` so every experiment gets it.
