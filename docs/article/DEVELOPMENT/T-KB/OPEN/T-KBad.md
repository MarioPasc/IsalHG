# T-KBad — provenance: where did T-KBf's `wstar_orbit` RQ5 numbers come from?

**Status:** OPEN (2026-09-14 10:02 CEST) · filed by agent `rq8`, wave
`2026-09-13-headline-w0`, on the orchestrator's instruction. **Filed, not
investigated** — this agent was told to record the question and stop.

## What was found

While re-running RQ5 on the ordered walk (T-KBab) the `wstar_orbit` comparison
the brief asked for could not be made, because:

- **`wstar_orbit` appears in 0 of 54** campaign RQ5 clustering row files under
  `results/IEEETKDE/RQ5_patterns/rows/rows_clustering__*balanced*.csv`.
  Measured by `grep -l wstar_orbit ... | wc -l` → `0`.
- The arms actually present in those rows are: `bipartite_ged_assign`,
  `bipartite_ged_path`, `degree_seq_l1`, `fact_rank`, `fact_rank_roles`,
  `hpd_jsd`, `nauty_cert`, `nauty_cert_rows`, `netlsd`, `size_l1`, `wl_l1`.
  Note `fact_rank_roles` **is** there — an arm D-ART4 (1) retired — which
  suggests these rows predate some config revisions.
- **`experiments/tkde/configs/rq5.yaml` lists `wstar_orbit` in all three
  experiments** (lines 26, 45, 64). So the config and the rows disagree.

## Why it matters

The RQ5 fact base referenced from T-KBf quotes `wstar_orbit` numbers. If those
numbers were not produced by the rows now on the drive, then either they came
from a run whose rows are elsewhere (or were superseded), or they were carried
over from a different experiment. Until that is settled, **any prose that cites a
`wstar_orbit` RQ5 number is citing something whose derivation is not currently
locatable**, which is exactly the failure `docs/article/DEVELOPMENT/README.md`
records for an earlier round ("lost the inputs a table was computed from, and no
reader could recompute it").

This is a provenance question only. Nothing about the `w°` swap depends on it:
T-KBab substituted a full-field comparison recomputed from the campaign's own
rows with identical aggregation, and every arm the two runs share reproduces to
four decimals (e.g. `bipartite_ged_assign` 0.0379 / 0.2305 / 0.5176 in both),
which is a stronger cross-check than the single-arm delta would have been.

## Candidate explanations, none verified

1. **The campaign RQ5 predates the config.** `wstar_orbit` was added to
   `rq5.yaml` after the rows were produced, and no re-run followed. The presence
   of `fact_rank_roles` in the rows is consistent with them being old.
2. **The arm was dropped at run time.** RQ5 reads cached `N × N` matrices;
   `wstar_orbit`'s matrices carry `.censored.json` companions in every
   collection (20–57 KB), so a censored member set may have removed the arm
   rather than the runner refusing.
3. **The T-KBf numbers come from a different results root.** Several exist:
   `IEEETKDE_isal`, `_isal_consensus`, `_isal_merged`, `_isal_preview`,
   `_isal_reach1`, `_isal_reach1b`, `_isal_reachprime`.

## The check the next agent must run

1. Locate every `rows_clustering__*.csv` under **all** `results/IEEETKDE*` roots
   (local drive and `~/results/` on Picasso) that contains `wstar_orbit`, and
   read its `manifest.json` for the job id, git SHA and `run_tag`.
2. Compare that `run_tag` against `run_tag(load_yaml("configs/rq5.yaml"))` at
   the SHA the manifest names. A mismatch says the numbers were produced under a
   different configuration than the one now in the tree.
3. Cross-check the quoted T-KBf values against whatever rows are found. If none
   match, the fact base's `wstar_orbit` RQ5 row must be marked
   **derivation not locatable** rather than silently kept.
4. Decide whether `wstar_orbit` should be re-run for RQ5 at all. Under D-ART6 it
   appears only in RQ1's four-cell ablation, so the answer may be no — in which
   case remove it from `rq5.yaml` so the config stops promising an arm nothing
   produces.

## Context

- T-KBab (the `w°` swap) and `../../../D_ART3/foundation/rq5_ow_facts.md` §3,
  which records the absence and what was substituted.
- The RQ5_ow run that surfaced it: job 2308368, 65 units, COMPLETED.
