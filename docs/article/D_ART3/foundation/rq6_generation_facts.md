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

## Pending

`rows_samples.reach1_frac` is **do-not-quote** until job 2279064 lands and passes
`scripts/diagnostics/rq6_reach1_rederivation_check.py`. The quoted
"4.7 % / 9.6 %" matches no run (campaign rows read 4.36 % / 7.13 %) and is struck
under the rule above.
