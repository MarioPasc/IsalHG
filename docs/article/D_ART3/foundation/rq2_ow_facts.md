# RQ2 on the ordered walk — fact base

*Derivation of record for the `w°` re-run of RQ2 (D-ART6, T-KBab). Written by
agent `rq8`, wave `2026-09-13-headline-w0`. Kept separate from the campaign's
own RQ2 fact base, which this agent does not own; the orchestrator folds it.*

## 1. Status — FINAL (harvested and analysed 2026-10-04, agent `harvest`)

Attempt 3 (jobs 2311593 / 2311604) completed; §4 holds the measured table. The
first attempt produced zero rows; the cause, the fix and the re-run are kept
below, because a fact base that records only the successful attempt teaches
nobody anything.

## 2. Provenance

| what | where |
|---|---|
| config | `experiments/tkde/configs/rq2_ow.yaml` — identical to `rq2.yaml` but for `wstar_orbit` → `isal_ow_struct` |
| launcher / worker | `slurm/tkde/rq2_ow_{launcher,worker}.sh` (D-KBab2: the shared pair hard-codes its config path) |
| Picasso results | `~/results/IEEETKDE_ow/RQ2_wellposedness/wellposedness/` |
| drive mirror | `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE_ow/RQ2_wellposedness/wellposedness/` — `rsync -a` (additive) 2026-10-04, 257 files (85 row files + `config.json`, `manifest.json`, 85 `_shards/*/` manifests) |
| analysis | `python -m experiments.tkde.analyze_rq2 --root <drive>/IEEETKDE_ow`, unmodified analyzer; writes `summary.json`, `stats.json`, `tables.md` beside the rows in the drive mirror (Picasso has none of the three, so nothing mirrored is overwritten) |
| jobs | **2311593** (main, 13 tasks, 13 COMPLETED) and **2311604** (census, 9 tasks, 9 COMPLETED), `sacct` 2026-10-04 |
| run tag / git | every row file `f14fffbc`; rows and manifest carry git `81e07a9` (`runner_deploy … branch=worktree-agent-a1b4083a2935ce6dd at=2026-09-14T09:42:30`) |
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

**Attempt 3 — jobs 2311593 (main) / 2311604 (census), 2026-09-14. COMPLETED,
13/13 and 9/9.** Both guards passed in the logs:

```
[ok] runner writes to RQ2_wellposedness/wellposedness
[ok] rows land in /localscratch/users/mpascual/2311594_0/out (mirrored)
```

## 4. The measured table (FINAL)

**Unit count against `configs/rq2_ow.yaml`.** 85 row files, all tag `f14fffbc`:
`exact0` 42 = 3 collections × 14 `exact0_arms` (4,200 rows = 42 × 100 pairs);
`census` 33 = 3 × 11 `census_arms`; `bipartite` 3 = 3 `bipartite_collections`
(26,988 rows); `oracle` 6 = 2 `oracle_collections` × 3 `n` strata (180 rows = 6 ×
30); `hypercot_timing` 1 = 1 collection (20 rows). Every configured unit is
present, none twice. Source of every number below: the drive mirror's
`tables.md` / `summary.json` (Provenance), or the `rows_census__f14fffbc-*.csv`
files directly.

### 4.1 `isal_ow_struct` — false merges and the induced partition

| collection | members | non-iso pairs | members censored | false merges | classes (`w°`) | classes (true, same members) |
|---|---|---|---|---|---|---|
| `ndc_classes` | 1,381 | 949,712 | 0 | **0** | **557** | 557 |
| `ndc_substances` | 1,745 | 1,516,294 | 0 | **0** | **1,156** | 1,156 |
| `wd50k66` | 3,988 | 7,949,355 | 0 | **0** | **3,682** | 3,682 |

**Zero false merges and the exact partition on all three collections, with no
member censored.** Exactness at zero (step 0): 100 / 100 isomorphic pairs at
distance 0 on each collection, 0 censored.

**The expected 530 / 1,086 / 3,677 are not `w°`'s numbers, and are not "the true
partitions" of the collections.** They are the true partitions of the member
subsets `wstar_orbit` survived at 60 s in the campaign's census tag `da0ff0af`.
Side by side, each with its own denominator:

| collection | `wstar_orbit` (campaign, tag `da0ff0af`) | `isal_ow_struct` (this run, tag `f14fffbc`) |
|---|---|---|
| `ndc_classes` | 530 classes on **1,311** members (70 censored; common subset for every arm of that tag) | 557 classes on **1,381** members (0 censored) |
| `ndc_substances` | 1,086 classes on **1,661** members (84 censored; the other arms of that tag ran on all 1,745) | 1,156 classes on **1,745** members (0 censored) |
| `wd50k66` | 3,677 classes on **3,983** members (5 censored; common subset) | 3,682 classes on **3,988** members (0 censored) |

Both arms produce the true partition **of the members they cover**; the ordered
walk covers every member. This is the censoring contrast the swap exists for:
`wstar_orbit` loses 70 / 84 / 5 members at the 60 s budget, `isal_ow_struct`
none. (Census wall-clock as recorded in the rows, `secs`: `isal_ow_struct` 1.38 /
0.27 / 0.52 s; `wstar_orbit`'s `ndc_substances` census, which had to compute its
own words, 8,446 s.)

### 4.2 Every arm of this run, against the campaign

| arm | `ndc_classes` merges / classes | `ndc_substances` merges / classes | `wd50k66` merges / classes |
|---|---|---|---|
| `isal_ow_struct` | 0 / 557 | 0 / 1,156 | 0 / 3,682 |
| `nauty_cert` | 0 / 557 | 0 / 1,156 | 0 / 3,682 |
| `nauty_cert_rows` | 0 / 557 | 0 / 1,156 | 0 / 3,682 |
| `fact_rank` | 0 / 557 | 0 / 1,156 | 0 / 3,682 |
| `wl_l1` | 0 / 557 | 0 / 1,156 | 0 / 3,682 |
| `bipartite_ged_path` | 0 / **574** (splits) | 0 / **1,290** (splits) | 0 / **3,839** (splits) |
| `bipartite_ged_assign` | 59 / 546 | 1,332 / 946 | 201,010 / 1,179 |
| `degree_seq_l1` | 5,397 / 337 | 1,332 / 946 | 201,010 / 1,179 |
| `netlsd` | 2,516 / 459 | 1 / 1,155 | 185,917 / 1,492 |
| `hpd_jsd` | 7,618 / 294 | 9,885 / 722 | 212,179 / 782 |
| `size_l1` | 52,660 / 71 | 33,713 / 290 | 291,227 / 194 |

True classes on the full member sets: 557 / 1,156 / 3,682.

**Cross-check against the campaign (`results/IEEETKDE/RQ2_wellposedness/wellposedness/`).**
That directory holds census rows under **two** tags, and its `tables.md` pools
them without distinguishing: `a5ff6092` (10 arms, no `wstar_orbit`, every member)
and `da0ff0af` (11 arms with `wstar_orbit`, restricted to the members it
survived on `ndc_classes` and `wd50k66`). This run reproduces `a5ff6092`
**bit-for-bit on all 30 shared arm × collection rows** (members, non-iso pairs,
merges, classes arm, classes true). Against `da0ff0af` 10 of 30 rows are
identical (all of `ndc_substances`, where that tag did not restrict the other
arms) and 20 differ only through the excluded members (e.g. `bipartite_ged_path`
on `ndc_classes`: 547 vs 530 on 1,311 members there, 574 vs 557 on 1,381 here).

**The `bipartite_ged_path` split that `rq2_wellposedness_facts.md` §1 quotes as
"574 classes where 557 exist" is measured on `ndc_classes`, all 1,381 members**
(campaign tag `a5ff6092`; reproduced here). It is not on the member subset of
that fact base's `wstar_orbit` row (530 / 1,311), which is why 557 matched none of
the three numbers in that row. On `wd50k66` (3,988 members) the same arm splits
3,682 true classes into 3,839; on `ndc_substances` (1,745) 1,156 into 1,290.

### 4.3 The arm-independent steps reproduce

| step | this run | campaign | reading |
|---|---|---|---|
| bipartite path asymmetry (pairs) | `ndc_classes` 882/2,000 = 0.441; `ndc_substances` 1,156/2,000 = 0.578; `wd50k66` 981/2,000 = 0.4905 | 1,764/4,000; 2,312/4,000; 1,962/4,000 — same rates | the campaign pools two tags of the same 2,000 pairs |
| bipartite path triangle violations | 8/5,000; 26/5,000; 7/5,000 | 16/10,000; 52/10,000; 14/10,000 | same rates; smallest violating triple identical (`ndc_substances`, 3 + 3 < 8, excess 2) |
| bipartite assign false zeros | 0/1,992; 2/1,996; 36/2,000 | 0/3,984; 4/3,992; 72/4,000 | same rates |
| exact oracle ceiling | 30/30 completed in every `n` stratum of both collections; median 0.35–0.78 s, p90 up to 10.6 s (`ndc_classes` 9–10) | 60/60; median 0.44–0.91 s | complete in both |

**HyperCOT did not run in either campaign.** Every one of this run's 300 `exact0`
`hypercot` rows and 20 `hypercot_timing` rows carries
`SubprocessRepresentationError: Pinned-env Python not found …/isalhg-hypercot/bin/python`;
the campaign's 600 and 40 rows carry the same error. The "HyperCOT timing
(gated)" medians in both `tables.md` (0.068 s here, 0.077 s there) are the time
to raise that error, **not a HyperCOT measurement**, and must not be quoted as
one. HyperCOT is not in either run's `census_arms`, so no HyperCOT false-merge
count exists.

## 5. Guards now in place

- `rq2_ow_worker.sh` asserts `experiments.tkde.rq2.{RQ_FOLDER, EXPERIMENT}`
  against its own shell variables **before any unit runs**, and asserts the
  symlink resolves inside the mirrored tree.
- Both `rq2_ow_worker.sh` and `rq8_worker.sh` refuse to reach the copy-back when
  the staged tree holds no `rows_*.csv`, printing where the rows actually went.
- `T-KBac` (OPEN) proposes moving that emptiness check into
  `slurm/tkde/common.sh` so every experiment gets it.
