# RQ6 generation — the verified fact base

Every number the prose quotes for RQ6 generation, with the run that produced it.
Written because three separate figures for "connectivity of the fact-list
generator" were circulating one sentence apart in `prose.md`, and one of them
matched no run on disk.

**Rule (L26, and `CLAUDE.md` §"the verified fact base behind every number"):** a
number with no entry here is **struck, not kept** — whichever way it points. This
is a **precondition** on the T-KBg prose fold, not a cleanup inside it: the fold
does not start until the source table exists.

## Provenance

| | |
|---|---|
| results root | `IEEETKDE_isal_consensus/` (`reach′` lineage, D-KBf5) |
| table | `RQ6_generation/generation/rows_samples.csv`, 162 rows |
| design | 27 seeds × 10,000 samples per (collection, model) = **270,000 per cell** |
| local mirror | `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/` |

## Sample validity and connectivity — from raw counts, not from ratios

| collection | model | `n_samples` | `n_valid` | `n_rejected` | `n_connected` | validity | connectivity (of valid) |
|---|---|---|---|---|---|---|---|
| ndc_classes | **`ow_ngram`** | 270,000 | **270,000** | 0 | **270,000** | **1.0000** | **1.0000** |
| ndc_classes | `fact_ngram` | 270,000 | 270,000 | 0 | 112,252 | 1.0000 | 0.4157 |
| ndc_classes | `incidence_ngram` | 270,000 | 5,135 | 264,865 | 467 | 0.0190 | 0.0909 |
| wd50k66 | **`ow_ngram`** | 270,000 | **270,000** | 0 | **270,000** | **1.0000** | **1.0000** |
| wd50k66 | `fact_ngram` | 270,000 | 270,000 | 0 | 34,009 | 1.0000 | 0.1260 |
| wd50k66 | `incidence_ngram` | 270,000 | 2,764 | 267,236 | 23 | 0.0102 | 0.0083 |

Derived, and quotable: rejection rate **0.9810** (NDC) and **0.9898** (WD50K) for
the incidence-list generator; fact-list samples disconnected **58.4 %** (NDC) and
**87.4 %** (WD50K).

## The headline is the JOINT rate, because `connectivity` is conditional

`rq6.py:496` writes ``connectivity = n_connected / n_valid`` — **conditional on
validity**, for every arm. For `ow_ngram` and `fact_ngram` validity is 1.0000 so
conditional and unconditional coincide and the distinction never surfaces. For
`incidence_ngram` it does, visibly: connectivity 0.0909 sits *above* validity
0.0190, which is only coherent because the denominator is the 1.9 % that decoded
at all. Quoting the three connectivity figures side by side puts them on two
different denominators — the same defect class as a pooled column, one level
down.

So the quotable headline is the **joint rate**, the fraction of *drawn samples*
that are valid **and** connected, which is what a user of a generator actually
gets:

| collection | model | validity | connectivity given valid | **joint** | one usable sample in |
|---|---|---|---|---|---|
| ndc_classes | **`ow_ngram`** | 1.0000 | 1.0000 | **1.000000** | **1** |
| ndc_classes | `fact_ngram` | 1.0000 | 0.4157 | 0.415748 | 2 |
| ndc_classes | `incidence_ngram` | 0.0190 | 0.0909 | 0.001730 | **578** |
| wd50k66 | **`ow_ngram`** | 1.0000 | 1.0000 | **1.000000** | **1** |
| wd50k66 | `fact_ngram` | 1.0000 | 0.1260 | 0.125959 | 8 |
| wd50k66 | `incidence_ngram` | 0.0102 | 0.0083 | 0.000085 | **11,739** |

One number, one denominator, no interval needed, and it states exactly what the
closed-language claim buys: **every sample is a usable knowledge base, against
one in 578 and one in 11,739.** Validity and connectivity are then reported as
its two factors rather than as competing headlines.

**The ordered walk is 1.0000 / 1.0000 on both collections** — Theorem C and
Prop. C.4 measured at 270,000 samples per collection, not asserted. It is the
cleanest number in the campaign.

## Struck for want of a source

| number | where it was | why struck |
|---|---|---|
| "256 / 1,000" fact-list connected | `prose.md` ×2, Prop 2 row | matches no run: the measured values are 0.4157 and 0.1260. **Note it moved *against* us on NDC** — the real number is better for the fact list than the one we were quoting. |
| "disconnected three times in four" | `prose.md` ×2 | encodes the same 0.256; no single ratio describes both collections (58 % / 87 %). |
| "1,000 / 1,000" Isal connected | `prose.md`, Prop 2 row | true but understated by 270×; the campaign figure is 270,000 / 270,000 per collection. |

## Three distinct quantities that must not be conflated

They sit one sentence apart in `RESULTS_WALKTHROUGH.md` §RQ6:

1. **sample connectivity** — the table above;
2. **alignment-interior connectivity** — 68.6 % for the fact alphabet, 100 % for
   the pointer alphabet (`rows_alignment`, a different measurement entirely);
3. **within reach 1** — itself two different columns:
   `rows_samples.reach1_frac` (via `Reach1Index`, **being re-derived**, job
   2279064) and `rows_completion.reach1` (via `reach()` directly; pre-`reach′`
   0.753 / 0.210, under `reach′` **0.767 / 0.213**).

## Reach-1 neighbourhood — SOURCED (job 2279079, root `IEEETKDE_isal_reach1b/`)

Superseded twice before landing, so the lineage matters:

| lineage | status |
|---|---|
| the quoted "4.7 % / 9.6 %" | **struck** — matches no run |
| `IEEETKDE_isal_consensus` (frozen `Reach1Index`) | superseded: the index was gated on the *frozen* reach precondition (T-KBo) |
| `IEEETKDE_isal_reach1` (job 2279064) | superseded: `None` for an empty fact-count window dropped samples from the denominator, overstating one arm **2.18×** |
| **`IEEETKDE_isal_reach1b` (job 2279079)** | **the derivation of record** |

`reach1_frac` counts over the **valid** subset, so it is conditional on validity
in exactly the way `connectivity` is. Report all three columns; the joint
factorises as `validity × reach1_frac`.

| collection | model | `reach1_eligible` | `reach1_hits` | reach1 given valid | **joint** |
|---|---|---|---|---|---|
| ndc_classes | `ow_ngram` | 27,000 | 4,382 | 0.1623 | **0.01623** |
| ndc_classes | `fact_ngram` | 27,000 | 1,238 | 0.0459 | 0.00459 |
| ndc_classes | `incidence_ngram` | 5,135 | 88 | 0.0171 | 0.00033 |
| wd50k66 | `ow_ngram` | 27,000 | 7,321 | 0.2711 | **0.02711** |
| wd50k66 | `fact_ngram` | 27,000 | 7,560 | 0.2800 | 0.02800 |
| wd50k66 | `incidence_ngram` | 2,764 | 76 | 0.0275 | 0.00028 |

**`reach1_eligible` is the decoded subset**: 27 seeds × the 1,000-sample
`reach1_subset` for the arms at validity 1.0000, and `n_valid` for the incidence
arm, whose decoded totals fall below the subset size. Every one of the six
matched its **pre-registered** value exactly.

**Read it honestly:** on WD50K the fact list is *marginally ahead* of the ordered
walk on this axis (0.2800 against 0.2711) and on NDC it is well behind (0.0459
against 0.1623). No single direction covers both, and the WD50K cell is one the
comparator wins.

**Verification.** `scripts/diagnostics/rq6_reach1_rederivation_check.py`,
committed before the rows existed: `rows_completion` (600), `rows_alignment`
(60) and `rows_rejections` (358) came back **bit-identical**, only the three
`reach1_*` columns moved, and neither `reach1_eligible` nor `reach1_hits` fell in
any unit.
