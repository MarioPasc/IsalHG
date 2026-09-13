# T-KBaa — RQ8: valid completion of a record

**Status:** IN-PROGRESS (2026-09-13 13:23 CEST) · declared 2026-09-13 by D-ART6,
wave `2026-09-13-headline-w0`, agent `rq8`. Pre-registration:
`../../../D_ART3/experiments/HEADLINE_DESIGN_2026-09-13.md` §0, §2, §4.
Sibling: T-KBz (RQ3 v2). Companion: T-KBab (the `w°` swap).

## What

A record is probably missing a fact. Propose completions guaranteed to be
records, and score whether the true completion is among them.

The property used is the **prefix property** of the ordered walk: `w°(K⁻)` is a
program of the machine, so any continuation decodes to a connected knowledge
base containing `K⁻` (Proposition C.8, stated and proved in
`../../../D_ART3/experiments/RQ8_PILOT.md` §1). A sequence model over `w°` words
conditioned on that prefix therefore proposes only valid, connected extensions.
No certificate and no vector fingerprint admits a completion operation, so the
non-generative rows carry "no completion definable".

Ours is **`ow_ngram`** — the RQ6 order-3 Kneser–Ney n-gram over the `w°` words of
the training split. It is **not** `fact_ngram`: that is the retired fact-rank
word of D-ART4 (1), scored here as the generative comparator it was in RQ6. The
RQ6 analyzer's `MODEL_OURS = "fact_ngram"` mislabel (tracked in T-KBf) is not
inherited; `rq8.ARM_OURS` is `"ow_ngram"` and a smoke test asserts it.

## Decisions taken in this task

- **D-KBaa1 — the secondary arm is `ow_ngram_ho`, not `ow_gru`.** The design's
  rule ("enable the secondary arm only if G8.1 shows the n-gram's interior
  hit@10 below 0.5 × `pattern_cooc`") FIRED: 0.1067 < 0.5 × 0.3033 on
  `ndc_classes`. torch is not installed in the campaign environment and adding a
  dependency was out of scope, so the orchestrator replaced the one-layer GRU
  with a higher-order n-gram — order 6, same interpolated Kneser–Ney smoothing,
  same training words. Declared in `configs/rq8.yaml` and in the pilot doc
  *before* the second pilot pass, so it is not post hoc.
- **D-KBaa2 — H8.1 fails; the pre-registered fallback applies.** `pattern_cooc`
  beats `ow_ngram` 0.3033 to 0.1067 on `ndc_classes` interior units; on
  `wd50k66` ours leads 0.0150 to 0.0133, which is noise. **RQ8 is a supporting
  exhibit, not a headline.** Orchestrator ruling, 2026-09-13, before submission.
  The full 27-seed run exists to put CIs on H8.3 and on the measured gap, not to
  reverse the pilot.
- **D-KBaa3 — the §0 attachment mechanism is CONTRADICTED by measurement.**
  §0 states that on non-stars the completion must choose attachments, "which the
  generator learns and counting cannot". Measured directly: among units where
  the pattern was right, the fraction where the attachment was still wrong is
  **0.716 for `ow_ngram` against 0.660 for `pattern_cooc`** on `ndc_classes` —
  the recommender attaches *better*. The NDC gap is a pattern-prediction gap
  (pattern@10 0.375 vs 0.892), not an attachment gap. One qualification:
  `ow_ngram_ho` reaches 0.632, below `pattern_cooc`, so the mechanism is right
  about direction and wrong about magnitude and about which arm wins.
  **The orchestrator folds this correction into the design doc at merge.**
- **D-KBaa4 — H8.3's third clause is inapplicable, and the number was NOT
  moved.** `incidence_ngram` validity is 0.1695 / 0.1427 against a
  pre-registered ceiling of 0.05. The ceiling was ported from RQ6, where
  sampling is *unconditional*; under conditional completion the prefix is a
  well-formed serialization and a truncated continuation decodes far more often.
  The clause is reported **failed with that reason** (L12), and the paper's
  sentence is the measured 0.17 / 0.14 against 1.000 by theorem.
- **D-KBaa5 — the pilot runs off-schedule seeds.** `seed_offset: 900` puts G8.1
  on seeds 80900–80902, outside the campaign's `seeds(8, 27) = 80000…80026`, so
  no unit the 27-seed run scores was ever seen by the gate. The offset enters
  the run tag, so a pilot row can never be served to the campaign.
- **D-KBaa6 — two prefix constructions that would otherwise have measured the
  harness.** The incidence prefix drops its `("END",)` terminator (with it,
  validity reads 1.0000 instead of 0.1718 and the H8.3 contrast inverts); every
  completion may run `max_new_tokens` past the prefix (without it a long word is
  capped to zero continuation). Both are pinned by regression tests shown
  failing against the pre-fix behaviour.

## Files

| path | what |
|---|---|
| `experiments/tkde/rq8.py` | the runner: G0, the unit generator, six arms, scoring |
| `experiments/tkde/analyze_rq8.py` | H8.1–H8.3, the tables, the blank rows |
| `experiments/tkde/configs/rq8.yaml` | the campaign, 27 seeds, 81 units |
| `experiments/tkde/configs/rq8_pilot.yaml` | gate G8.1, off-schedule seeds |
| `tests/experiments_tkde/test_rq8_units.py` | unit generator, census, baselines (40) |
| `tests/experiments_tkde/test_rq8_prefix_property.py` | Proposition C.8 (13) |
| `tests/experiments_tkde/test_rq8_smoke.py` | end-to-end + the stale-row guard (29) |
| `slurm/tkde/rq8_{launcher,worker}.sh` | one task, `--constraint=sd`, node staging |
| `slurm/tkde/rq8_sync.sh` | the private deployment wrapper |
| `docs/article/D_ART3/experiments/RQ8_PILOT.md` | Prop. C.8, G0, G8.1 |
| `docs/article/D_ART3/foundation/rq8_facts.md` | run root, job ids, campaign tables |

## Acceptance check

```
$P -m pytest tests/experiments_tkde/test_rq8_units.py \
             tests/experiments_tkde/test_rq8_prefix_property.py \
             tests/experiments_tkde/test_rq8_smoke.py -q
82 passed
```

`ruff check src/ tests/ experiments/` stays at the 38-error baseline;
`mypy src/isalhg/` stays at 20. The pre-existing 6 failures in
`test_rq36_smoke.py` and `test_rq45_smoke.py` are at BASE_SHA and untouched
(see the work log).

## Open, for the orchestrator

- The prose fold (T-KBg) has to carry D-KBaa2/3/4 verbatim; RQ8 is a supporting
  exhibit and the §0 mechanism correction is the sentence the design doc needs.
- The capability table's "completion definable" column is now measured and can
  leave `\todo`.
