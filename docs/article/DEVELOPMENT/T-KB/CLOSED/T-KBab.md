# T-KBab — the `w°` swap: RQ2 census and RQ5 clustering on `isal_ow_struct`

**Status:** DONE (2026-10-04 10:20 CEST, agent `harvest`, wave
`2026-10-04-harvest`) · declared 2026-09-13 by D-ART6,
wave `2026-09-13-headline-w0`, agent `rq8`. Pre-registration:
`../../../D_ART3/experiments/HEADLINE_DESIGN_2026-09-13.md` §5. Both swapped
tables are measured; closing evidence for RQ2_ow at the end.

## What

D-ART6 makes the ordered walk `w°` (`isal_ow_struct`) the paper's headline
program, so every main-text table runs on it. Two already-measured tables were
run on `wstar_orbit` and have to be re-measured:

- **RQ2 census on `w°`** — the false-merge census and the exact partition on
  `ndc_classes`, `ndc_substances`, `wd50k66`. Pre-stated expectation (Theorem C):
  0 merges and an exact partition, as for `wstar_orbit`, **but with no
  censoring**. `wstar_orbit` dropped members at the 60 s budget (its
  `<matrices>/<collection>/wstar_orbit.censored.json` files are 20–57 KB); the
  ordered walk censors none, which is the measurable half of lifting D-ART4's
  restriction R2 for symmetry.
- **RQ5 on `w°`** — the clustering table with `isal_ow_struct` in place of
  `wstar_orbit`. Pre-stated expectation: the same negative RQ5 already measured;
  the naive floors are expected to win, and no baseline is removed for winning
  (L12).

## Decisions taken in this task

- **D-KBab1 — no Python edit was needed.** Both runners take their arm set from
  the configuration (`rq2.yaml` `exact0_arms` / `census_arms`; `rq5.yaml` per
  experiment `arms:`), so the swap is two YAML files. `experiments/tkde/rq2.py`
  and `rq5.py` are unmodified.
- **D-KBab2 — RQ2's swap needed its own launcher/worker pair; RQ5's did not.**
  `rq5_launcher.sh` reads `RQ5_CONFIG` from the environment, so
  `rq5_ow_launcher.sh` is a thin wrapper over it. `rq2_launcher.sh` line 19 and
  `rq2_worker.sh` line 25 both **hard-code** `configs/rq2.yaml` with no override,
  so a wrapper would have run the swap against the `wstar_orbit` arm list.
  Editing the shared pair was out of scope (the `rq3v2` agent runs off the same
  directory this wave), so `rq2_ow_{launcher,worker}.sh` are copies differing in
  exactly three places: the config, the experiment name (`wellposedness_ow`, its
  own subtree) and the job name. **If the shared pair is ever parameterised by
  `RQ2_CONFIG`, the ow copies should be deleted in favour of a thin wrapper.**
- **D-KBab3 — the cached `isal_ow_struct` matrices already exist and are
  asserted, not assumed.** `matrices.yaml` has built them for `wd50k66`,
  `ndc_classes` and `wd50k100`; `ndc_substances` has none and RQ2 builds it
  itself (`census_own_collections`), exactly as the `wstar_orbit` run did. Both
  ow launchers assert the `.npy` files are present before submitting, because a
  missing cache fails halfway through a job that has already burned its
  placement and looks like queue time until then.

## Verification before submission

Local, both configs, through the unmodified runners:

- `rq2_ow.yaml --smoke`: exact0 and census units scored on `isal_ow_struct`;
  `wstar_orbit` appears **nowhere** in the log (0 matches).
- `rq5_ow.yaml --unit 11`: 22 clustering rows over eleven arms, including
  `isal_ow_struct` and excluding `wstar_orbit`.

## Files

| path | what |
|---|---|
| `experiments/tkde/configs/rq2_ow.yaml` | RQ2 with `isal_ow_struct`; experiment `wellposedness_ow` |
| `experiments/tkde/configs/rq5_ow.yaml` | RQ5 with `isal_ow_struct` |
| `slurm/tkde/rq2_ow_{launcher,worker}.sh` | the ow pair (D-KBab2) |
| `slurm/tkde/rq5_ow_launcher.sh` | thin wrapper over the shared RQ5 pair |

## Closing evidence (2026-09-14)

### RQ5_ow — DONE. Job **2308368**, COMPLETED 01:05:09, 65 units.

Harvested to `results/IEEETKDE_ow/RQ5_patterns/` (144 files); analysed with the
unmodified `analyze_rq5.py`. Full table:
`../../../D_ART3/foundation/rq5_ow_facts.md`.

- The pre-stated expectation held: **RQ5 stays negative**, every arm below
  ARI 0.08. Analyzer verdicts H5a/H5b/H5c `not_supported`, H5d `inconclusive`.
- Within that negative the swap is an improvement: `isal_ow_struct` leads NMI on
  `wd50k66_balanced` (0.2632, above `netlsd` 0.2606) and leads ARI on
  `wd50k100_balanced` (0.0768, above `degree_seq_l1` 0.0705); second on
  `wd50k66` ARI (0.0675 against `netlsd` 0.0705). The retired fact-rank word
  scored 0.0260 on the same design, so the ordered walk is **2.6× its ARI**.
- **The naive floors do NOT win here**, against the expectation carried over
  from the planted corpora: `size_l1` 0.0431, `degree_seq_l1` 0.0392 on
  `wd50k66_balanced`. Reported as measured (L12).
- **D-KBab4 — the requested `wstar_orbit` comparison is not possible.**
  `wstar_orbit` appears in **0 of 54** campaign RQ5 clustering row files, though
  `configs/rq5.yaml` lists it in all three experiments. Either the campaign RQ5
  predates that config or the arm was dropped at run time. The full field was
  recomputed from the campaign's own rows with identical aggregation instead;
  every shared arm reproduces to four decimals (`bipartite_ged_assign`
  0.0379/0.2305/0.5176 in both), which is the cross-check that the `w°` run is
  sound.

### RQ2_ow — RE-RUNNING. Attempt 1 lost everything; attempt 3 is in flight.

**Jobs 2308342 / 2308343 produced ZERO rows** despite 21 of 22 tasks reporting
COMPLETED and all 22 logging "copy-back OK". Diagnosis, fix, and the second
(false-positive) failure are recorded in full in
`../../../D_ART3/foundation/rq2_ow_facts.md` §3. In short:

- **D-KBab5 — `rq2.py` takes its output path from a module constant, not the
  config.** Line 997: `RunPaths(root=results_root, rq=RQ_FOLDER,
  experiment=EXPERIMENT)`. The ow worker's `EXPERIMENT="wellposedness_ow"`
  therefore symlinked a directory the runner never wrote to; the runner wrote to
  a plain node-scratch directory outside the mirrored tree, the copy-back
  mirrored an empty tree and **reported success**. ~7 wall-hours lost. This is
  the defect `slurm/tkde/README.md` already records for the 2026-09-07 rank run.
  Fixed: `EXPERIMENT="wellposedness"`; separation comes from the results **root**
  and the run tag, which is all it ever needed. Pinned by
  `tests/experiments_tkde/test_rq8_ow_worker_paths.py` (8 tests), shown failing
  against the pre-fix worker.
- **Memory:** task 10 OOM at **31.4 GB** against 32 G after 5 h 55 m, still
  climbing; heaviest COMPLETED sibling 26.1 GB. Main array now 96 G.
- **Attempt 2 (2311493/2311494) failed all 22 tasks in seconds on my own new
  guard — a false positive.** `readlink -f` canonicalised the link but the
  comparison used the raw `${MYLOCALSCRATCH}/out`, and Picasso exports
  `LOCALSCRATCH` with a trailing slash (`/localscratch/users//mpascual/...`).
  Both sides are now canonicalised with `readlink -m`; reproduced locally and
  verified the guard still fires on a genuinely stranded directory.
- **Attempt 3: jobs 2311593 (main) / 2311604 (census), RUNNING.** Both guards
  pass: `[ok] runner writes to RQ2_wellposedness/wellposedness` and
  `[ok] rows land in /localscratch/users/mpascual/2311594_0/out (mirrored)`.
- A generic emptiness guard now sits in both of this agent's workers and refuses
  to reach the copy-back when no row file was staged. **T-KBac** (OPEN) proposes
  moving it into `slurm/tkde/common.sh`.

**RQ2_ow numbers are NOT available and nothing may cite them yet.** The census
is complete only when rows exist; `rq2_ow_facts.md` §4 is the pending list.

## Open, for the orchestrator

- Results land under `~/results/IEEETKDE_ow/` on Picasso and are harvested to
  `results/IEEETKDE_ow/` on the drive. Job ids are in
  `../../../D_ART3/foundation/rq8_facts.md`.
- The `wstar_orbit` rows these supersede are kept on disk, per the N=60→240
  precedent; nothing is deleted.

## Closing evidence — RQ2_ow (2026-10-04, agent `harvest`)

**Jobs 2311593 (13/13 COMPLETED) and 2311604 (9/9 COMPLETED).** Harvested to
`/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE_ow/RQ2_wellposedness/wellposedness/`
(257 files, 85 row files, all tag `f14fffbc`, git `81e07a9`) and analysed with the
unmodified `analyze_rq2.py`. Unit count matches `configs/rq2_ow.yaml` exactly
(42 exact0, 33 census, 3 bipartite, 6 oracle, 1 HyperCOT timing). Full table:
`../../../D_ART3/foundation/rq2_ow_facts.md` §4.

- **The pre-stated expectation held, and the censoring half with it.**
  `isal_ow_struct`: 0 false merges and the exact partition on all three
  collections — 557 classes on all 1,381 `ndc_classes` members, 1,156 on all
  1,745 `ndc_substances`, 3,682 on all 3,988 `wd50k66` — with **0 members
  censored**; 100/100 isomorphic pairs at distance 0 on each. `wstar_orbit` had
  given 530 / 1,086 / 3,677 on the 1,311 / 1,661 / 3,983 members it survived at
  60 s. The two rows are the true partition of different member sets and are
  never to be compared without both denominators.
- **The run reproduces the campaign bit-for-bit** on all 30 shared arm ×
  collection census rows of the campaign's full-member tag `a5ff6092`, and the
  arm-independent steps (bipartite asymmetry 0.441 / 0.578 / 0.4905, triangle
  violations, false zeros, the oracle ceiling, the smallest violating triple)
  at the same rates.
- **Found while cross-checking:** the campaign's `tables.md` pools two census
  tags (`a5ff6092`, every member; `da0ff0af`, restricted to `wstar_orbit`'s
  survivors) in one table, which is how `rq2_wellposedness_facts.md` §1 came to
  put a 557-class split beside a 530-class `wstar_orbit` row; and **HyperCOT never
  ran** in either RQ2 campaign (every row is a missing-environment error, so the
  "HyperCOT timing (gated)" medians are time-to-failure). Both are recorded in
  `rq2_ow_facts.md` §4.2–§4.3; the campaign fact base is not this task's to edit.

**Acceptance.** Both swapped tables are re-measured on `w°` and written to their
fact bases (`rq2_ow_facts.md`, `rq5_ow_facts.md`); the `wstar_orbit` comparison
D-KBab4 could not make is now traced in T-KBad. Moved to `CLOSED/`.
