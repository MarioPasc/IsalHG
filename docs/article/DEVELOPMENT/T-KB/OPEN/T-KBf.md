# T-KBf — RQ2–RQ7 with the Isal arms (the encoder swap)

**Status:** OPEN · declared 2026-09-07 22:10 CEST by the Isal-refinement
orchestrator (handoff §5.3). Depends on T-KBe's decision for the headline
arm; the runs can start with both C++ candidates (`wstar_rank`,
`isal_ow_struct`) and `wstar_orbit` where budgets allow.

## What

- **Budgeting audit before any submission:** every in-process Isal engine
  call must fork under a budget or be provably milliseconds. Fixed: RQ1
  (`BUDGETED_ARMS`), RQ2 (`POINTER_ARMS`). To audit: the RQ7 sweep
  per-instance path (no `engine_word` at last grep); the N×N matrices for
  `wstar_rank` (fingerprint-first route in `toolkit/matrix.py` is
  unbudgeted; arity-10 members censor at 60 s) — implement a
  censoring-aware fingerprint step and report censored members per L15;
  `rq3.run_guarded` lacks the fork-health canary.
- Drop `fact_rank_roles` from every table (fails M0 invariance 43/60).
- Order: matrices → RQ2 → RQ3 (pilot one NDC cell first) → RQ4 → RQ5 → RQ6
  (the Isal `ow_ngram` generator; validity and connectivity 1,000/1,000
  measured locally) → RQ7 (with the `|Aut|` axis). Harvest each into the
  results root; persist tables.
- Pre-stated readings: RQ2 exact/metric/polynomial; RQ3 carries over with
  connected interiors; RQ4/RQ5 at the certificate's level → supplement
  (author ruling); RQ6 stronger; RQ7 the envelope from `|Aut|` to `m`.

## Acceptance

One Isal row (C++ engine) in every RQ table, with provenance stamps, under
`results/IEEETKDE/`; the negatives reported with the same directness.
