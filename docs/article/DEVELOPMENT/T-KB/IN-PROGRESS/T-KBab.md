# T-KBab — the `w°` swap: RQ2 census and RQ5 clustering on `isal_ow_struct`

**Status:** IN-PROGRESS (2026-09-13 13:23 CEST) · declared 2026-09-13 by D-ART6,
wave `2026-09-13-headline-w0`, agent `rq8`. Pre-registration:
`../../../D_ART3/experiments/HEADLINE_DESIGN_2026-09-13.md` §5.

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

## Open, for the orchestrator

- Results land under `~/results/IEEETKDE_ow/` on Picasso and are harvested to
  `results/IEEETKDE_ow/` on the drive. Job ids are in
  `../../../D_ART3/foundation/rq8_facts.md`.
- The `wstar_orbit` rows these supersede are kept on disk, per the N=60→240
  precedent; nothing is deleted.
