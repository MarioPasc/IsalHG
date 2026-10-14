# T-KBm — a fully censored matrix unit succeeds silently with an empty matrix
**Declared:** 2026-09-09 09:35 CEST
**Status:** OPEN
**Depends on:** — (independent of the RQ2–RQ5 consumer wave, but see it first)
**Delegation:** agent
**Why out of scope:** found while pre-testing the censoring branch before job
2264831 reached it (T-KBf, D-KBf2). The campaign's real budgets do not trigger
it — `wstar_orbit` censors 7 of 3,988 on wd50k66 and 70 of 1,381 on ndc — so
fixing it is not on the submission path.

**Context to read first:**
- `src/isalhg/metric_space/toolkit/matrix.py::build_matrix_censored` — screens,
  then builds over the survivors with no floor on how many survive
- `experiments/tkde/matrices.py::run_unit` — treats a returned matrix as
  success; `::_write_censoring` writes the sidecar
- `experiments/tkde/matrices.py::load_cached_matrix` and the sidecar-aware
  loader added by the RQ2–RQ5 consumer wave — the consumers of an `n = 0` file
- `docs/article/DEVELOPMENT/T-KB/IN-PROGRESS/T-KBf.md` §D-KBf2 — the
  drop-and-count contract this sits under
- `docs/article/D_ART3/foundation/lessons.md` L15 — censoring is *reported*,
  which an empty matrix does not do
- `.claude/rules/coding_rules.md` — always

**Description:** when every member of a collection censors, the unit writes a
`(0, 0)` matrix with `manifest.n = 0`, logs `computed: n=0 secs=0.000` and
reports **success**. Reproduced 2026-09-09:

```
python -m experiments.tkde.matrices --smoke --out <dir> --fingerprint-budget-s 0.004
  wd50k66 / wstar_orbit: 40 of 40 members censored -> npy shape (0, 0), manifest n = 0
  ndc_classes / wstar_orbit: 12 of 40 censored -> npy 28x28, sidecar correct
```

The 28-survivor case is exactly right (`n_requested 40, n_censored 12,
member_ids 28`, manifest `n = 28` over the kept order). The empty case is the
hazard: a mis-set budget, a corpus outside the arm's envelope, or a future arm
would yield a complete, plausible, wrong result set — RQ4 would compute an AUC
over nothing and RQ5 a clustering of nothing, both of which can render as a
table cell rather than as an error. This is the failure mode the campaign has
paid for twice already (the duplicated launch tags; the per-arm merge source).

**Acceptance:** a unit whose survivor count falls below a stated floor
(suggest: fewer than 2 survivors, i.e. no pair exists, and configurably a
fraction) fails loudly with the arm, the collection, `n_requested` and
`n_censored` named, rather than writing an empty or degenerate matrix; a
consumer that meets an `n = 0` cached matrix raises rather than scoring it;
tests for both, parametrized over 0, 1 and 2 survivors.

**Out of scope here:** the censoring mechanism itself, the sidecar format, the
`daemon` fix of `c6a9a8c`, and any change to which members censor at the
campaign's 60 s budget — the censuses must stay comparable across RQ1–RQ7.
