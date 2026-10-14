# T-KBo — `rq6.Reach1Index` is unsound under `reach′`
**Declared:** 2026-09-09 16:05 CEST
**Status:** DONE
**Depends on:** D-KBf5 (merged) — this is its one unfixed consequence
**Delegation:** agent
**Why out of scope:** found by the `reach′` implementer while it held
`language/`; `rq6.py` was outside its ownership and RQ6 is later in the T-KBf
order. Filed rather than fixed inline.

**Context to read first:**
- `experiments/tkde/rq6.py::Reach1Index` — `_shape()` and the bucketing it drives
- `src/isalhg/language/reach.py::compatible` — the two post-compaction
  conditions that replaced the constant-count precondition
- `docs/article/DEVELOPMENT/T-KB/IN-PROGRESS/T-KBf.md` §D-KBf5 — the ruling
- `.claude/notes/2026-09-09-isal-kb-w10/reach-prime.md` — the repro
- `.claude/rules/coding_rules.md` — always

**Description:** `Reach1Index._shape()` hard-codes the **frozen** reach
precondition — constant count plus type multiset — and buckets members by it, so
`reach` is never called across differing constant counts. Under `reach′` a
deletion changes the constant count, so the index silently withholds exactly the
pairs the new definition admits. It also mixes `fact_word` keys with
now-compacted remainder keys.

Reproduction (in the work log): `reach(sample, src, 1) == 1` while
`within_one(sample)` returns `None` for the same pair.

Consequence: **RQ6's `reach1` column must be re-derived.** Nothing else in RQ6
is implicated — the generator, the validity/connectivity results and the sample
rows do not use this index.

**Acceptance:** `Reach1Index` buckets on a key that is valid after compaction
(or drops bucketing and calls `compatible(..., r_max)`); a test builds a pair
whose constant counts differ by one at `reach′ = 1` and asserts `within_one`
finds it; the `reach1` column is re-derived and the old value marked superseded
wherever it is quoted.

**Out of scope here:** `reach.py` and `consensus.py` (shipped at D-KBf5); RQ6's
generator, validity or connectivity measurements; any table placement decision.

---

**2026-09-10 — code landed; re-derivation in flight.** `Reach1Index` rebuilt on
`reach′`: the frozen bucket is gone, candidates come from an inverted index over
compacted remainder words, and the budget test is `ds + dm ≤ 1` on a *shared*
word (a set intersection would admit `reach′ = 2`). The obvious fact-count bucket
was measured first and rejected — only **1.2×** on `ndc_classes`, whose 14
distinct fact counts put nearly the whole collection in three adjacent buckets.
The index runs at 0.3–0.4 ms/call.

`analyze_rq6.completion_table` was counting a blank `reach1` as a measured
failure; fixed, with per-quantity denominators reported.

Tests: 6 new (`test_rq6_reach1_index.py`, including a brute-force agreement check
and a property test that no `reach′ ≤ 1` pair falls outside the bucket over 300
random pairs); the pre-existing test asserting `is None` for a differing constant
count encoded the stale gate and now asserts agreement with `reach` itself.
Two unrelated failures in the same file filed as **T-KBt**.

**Remaining for closure:** job **2279064** (root `IEEETKDE_isal_reach1/`) must
land and pass its pre-registered check — every non-`reach1` column bit-identical
to the superseded rows, sampling having been verified deterministic — after which
the old `reach1` is marked superseded wherever quoted.

---

**2026-09-10 22:30 — CLOSED. Job 2279079 passes the pre-registered check.**

`scripts/diagnostics/rq6_reach1_rederivation_check.py`, committed before any of
these rows existed, returns **PASS**:

- `rows_completion` **600 rows bit-identical**, `rows_alignment` **60**,
  `rows_rejections` **358** — so sampling is deterministic, the re-run was a
  re-derivation over the same samples, and the change touched only the index;
- only `reach1_frac`, `reach1_eligible` and `reach1_hits` moved;
- direction holds: `reach1_eligible` fell in **0** units, `reach1_hits` in **0**.

**The numeric prediction matched in all six cells**, exactly:

| collection | model | predicted | actual | `reach1_frac` | joint |
|---|---|---|---|---|---|
| ndc_classes | fact_ngram | 27,000 | **27,000** | 0.0459 | 0.00459 |
| ndc_classes | incidence_ngram | 5,135 | **5,135** | 0.0171 | 0.00033 |
| ndc_classes | ow_ngram | 27,000 | **27,000** | 0.1623 | 0.01623 |
| wd50k66 | fact_ngram | 27,000 | **27,000** | 0.2800 | 0.02800 |
| wd50k66 | incidence_ngram | 2,764 | **2,764** | **0.0275** | 0.00028 |
| wd50k66 | ow_ngram | 27,000 | **27,000** | 0.2711 | 0.02711 |

`wd50k66/incidence_ngram` lands at **0.0275**, the corrected value, against the
**0.0600** the `None` semantics reported — the 2.18× overstatement is gone, and
the joint rate 0.00028 matches the factorisation `validity × reach1_frac`.

**The superseded roots and what each was for.** `IEEETKDE_isal_reach1` is kept:
its entire value was failing the check and exposing the denominator defect.
`IEEETKDE_isal_reach1b` is the derivation of record. The pre-`reach′` `reach1`
values are superseded wherever quoted — `RESULTS_WALKTHROUGH.md` carries the
supersession note and `T-KBg` carries the do-not-quote list.
