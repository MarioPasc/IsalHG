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
