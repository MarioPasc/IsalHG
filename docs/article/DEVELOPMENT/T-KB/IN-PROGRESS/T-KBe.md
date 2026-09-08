# T-KBe — RQ1 harvest, merged table, and the representation decision

**Status:** OPEN · declared 2026-09-07 22:10 CEST by the Isal-refinement
orchestrator (handoff `../../../D_ART3/experiments/HANDOFF_2026-09-07_isal.md` §5.1–5.2).

## What

1. When jobs 2247394+2247395 (`addressing`), 2248782 (`addressing_rank`)
   and 2248907+2248908 (`addressing_cpp`) are terminal, harvest the three
   experiments into `results/IEEETKDE_isal/RQ1_addressing/` (not into the
   campaign's `RQ1_addressing/addressing`, which is the frozen record).
2. Merge with `experiments/tkde/merge_rq1_experiments.py` — one source per
   arm: `wstar_rank` from `addressing_rank`; `wstar_orbit`, `isal_ow_*`
   from `addressing_cpp`; the rest from `addressing` — into a separate root
   under the analyzer's default name, then `analyze_rq1 --root`.
3. Verify the join (equal seeded edit sets per unit across experiments).
4. Persist `tables.md`, `stats.json`, `manifest.json` + the merge manifest
   under `results/IEEETKDE/RQ1_isal/`.
5. Apply the pre-registered selection rule (`ISAL_VARIANT_DESIGN.md` §3) and
   bring the table, the per-kind reading and the R2 table to the author/PI
   for the decision (which canonical program carries RQ2–RQ7; the nauty
   sentence).

## Acceptance

M0 = 0/0/0 for every Isal arm; the table reports absolute instructions
first (L11), the ≤ 2 fraction, censoring per (arm, m, |Aut|) (L15), BCa and
Holm (G5); the decision recorded in `DECISIONS.md` as D-ART5 with the PI's
word.

---

## Progress — 2026-09-08 12:42 CEST

**Status:** IN-PROGRESS.

### The join is exact; two provenance defects were found before it

`scripts/tkde/verify_rq1_join.py` (new) checks that the three experiments
measured the same seeded units before any paired statistic is trusted. On the
cluster, restricted to the Isal campaign's launch tag:

| table | key | addressing | addressing_rank | addressing_cpp | disagreement |
|---|---|---|---|---|---|
| M0/M3 | `(collection, seed, member_id)` | 7,369 | 7,369 | 7,369 | 0 |
| M1 | `(collection, seed, base_id, edit_kind, edit_idx)` | 138,499 | 139,492 | 139,492 | 993 units still missing in `addressing` |

The 993 are the last two `m1` shards of the recovery sweep (job 2247395), which
re-runs all 143 shards; `addressing_rank` and `addressing_cpp` are complete.

**Defect 1 — `RQ1_addressing/addressing` on the cluster holds two campaigns.**
Launch tag `c3fb21de` is job 2215137 (submitted 2026-09-05 23:17; rows written
09-06 13:50 → 09-07 04:08, `git_sha 554dbe09`), the fact-rank campaign — the
run frozen on the drive as `results/IEEETKDE/RQ1_addressing/addressing`. Tag
`47c8a42c` is job 2247394 + its sweep 2247395 (submitted 09-07 10:05), the Isal
campaign, which re-measures every unit and is the only launch carrying the
instruction-granularity columns `d_instr`, `n_instr` and `aut_bucket` — the
paper's headline granularity. Both wrote the fact and certificate arms, so
concatenating the directory yields **904,442 duplicated `(unit, arm)` rows out
of 2,506,837**: those arms counted twice on a mix of two schemas while the Isal
arms are counted once. Nothing in the analyzer, the merge tool or `io.py`
deduplicated. Fixed at `314b4a3`: `--only-tags`, `--list-tags` and a duplicate
audit that refuses the merge (`MergeIntegrityError`) and records the census in
`merge_manifest.json`. The wave logs are silent on the tag collision.

**Defect 2 — `fact_rank_roles` would have reached the table.** It fails M0 on
wd50k66 (247 false splits, 2,104 invariance violations) and T-KBf requires it
off every table; `--drop-arms` (`f4cf4e6`) removes it at merge time while the
source experiments keep the census that condemns it.

The whole pipeline is one script, `scripts/tkde/build_rq1_isal_table.sh`
(`8d5029b`): list tags → gate on the join → merge one source per arm → analyze.
It runs on the Picasso login node; no heavy local compute (handoff §2.2).

### Deviation from the pre-registration to note

`wstar_600` is named as an arm in `ISAL_VARIANT_DESIGN.md` §3 but is absent
from `experiments/tkde/configs/rq1.yaml`; there is no 600 s re-run of the 60 s
censored tail in this campaign. The wave logs are silent on it. The `w*_c` row
is `isalhg_levenshtein` at the 60 s budget, with its censoring reported in M3.
