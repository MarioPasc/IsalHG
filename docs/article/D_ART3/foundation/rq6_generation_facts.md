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
| the quoted "4.7 % / 9.6 %" | **struck** — matches no run; superseded **by** `IEEETKDE_isal_reach1b` (job 2279079) |
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

**`reach1` SCORES NOBODY — it is characterisation, and the design says so.**
H6b (DESIGN §625) reads: *"most samples are **novel** (not isomorphic to a
member) while **a stated fraction** sit within reach 1 of one."* The design asks
for the fraction to be **stated**, not to be high or low, and it is right not to
name a direction, because both readings are defensible:

- high `reach1` = **fidelity**, samples landing near real knowledge bases;
- high `reach1` = **memorisation**, the generator reproducing near-copies of its
  training members.

Nothing in RQ6's evaluation — validity rate and profile divergence — settles
which. The direction-bearing claim is **novelty** (0.99 / 0.94), which is
precisely the memorisation guard; `reach1` describes how tightly the novel
samples sit around the collection.

So the numbers above are reported and **no arm is scored on them**. Deciding the
direction *after* seeing that it splits by collection — `fact_ngram` ahead on
WD50K, well behind on NDC — is the move this whole session has been about.
Raised by `[IsalHG-Fable]`; confirmed against the design text rather than
inferred.

**Verification.** `scripts/diagnostics/rq6_reach1_rederivation_check.py`,
committed before the rows existed: `rows_completion` (600), `rows_alignment`
(60) and `rows_rejections` (358) came back **bit-identical**, only the three
`reach1_*` columns moved, and neither `reach1_eligible` nor `reach1_hits` fell in
any unit.

---

## Censoring provenance — verification for the R2 counts

Recorded here rather than in the prose, per `CLAUDE.md`'s split: **assertions in
the paper, verification in the fact base.** D-ART5's R2 sentence states its
counts plainly and takes **no caveat**; a caveat would advertise a doubt this
audit has closed, and a reader could not evaluate it.

`censored` encodes two states — *attempted and exceeded the budget* and *never
attempted* — and the fork-poisoning defect could once write the second as the
first. **The current code cannot**: `guarded_budget_call` raises
`TkdeBudgetError` on a poisoned fork instead of recording a censoring, and no
caller swallows it (the two `rq3.py` mentions are `Raises` docstrings). Verified
2026-09-10, so the next reader does not go looking for a bug fixed on
2026-09-07.

**Verified per row against `a99775a`** ("a poisoned fork must not be recorded as
a censoring", 2026-09-07 09:17), resolving every `git_sha` the rows carry with
`git merge-base --is-ancestor`:

> **All rows in `IEEETKDE_isal_merged`, `_consensus`, `_preview`, `_reachprime`
> and `_reach1{,b}` are post-fix — 0 pre-fix rows.** The M3 census the 77/53 is
> counted from, and every RQ3 row behind the consensus readings, are therefore
> provably genuine censorings.

The 2,378,890 pre-fix rows carry one of four shas, all dated **2026-09-05** (the
first wave), and sit only in `IEEETKDE` (1,314,688) and `IEEETKDE_isal`
(1,064,202). Those two roots are marked in place; **T-KBu** carries the schema
split so the two states stop sharing a column.

---

## Normalisation: `novelty` and `reach1` do not use the same one

Raised by `[IsalHG-Fable]`. `novelty` compares `fact_word(H)` of the decoded
sample **as decoded**; `reach1` is `reach′` on **compacted** remainders. They
therefore disagree on any sample carrying an isolated constant, which could be
counted novel while sitting at reach 0 of the member it compacts onto.

**Measured, not argued** (`ndc_classes`, order-3 model, seed 60000):

| | |
|---|---|
| decoded `fact_ngram` samples carrying an **isolated constant** | **303 / 500 (60.6 %)** |
| collection members carrying one | **0 / 1,381** |
| does `fact_word` encode it? | **yes** — adding one isolated constant to a member changes its word |

So such a sample can never equal a member's word and is counted novel
*automatically*. `ow_ngram` cannot be affected: Prop. C.4 gives every decoded
word a connected knowledge base with no isolated constant, so compaction is the
identity there. **The two arms are therefore measured on different
normalisations, and the difference runs in the retired arm's favour.**

**The magnitude is small** (2,000 samples, 1,997 decoded):

| `ndc_classes` / `fact_ngram` novelty | |
|---|---|
| as computed (uncompacted) | **0.9895** |
| on `reach1`'s normalisation (compacted) | **0.9775** |
| novel *only* because of an isolated constant | **24 samples, 1.2 %** |

**Consequence: state the normalisation per column; change nothing.** Novelty and
reach1 answer different questions and either normalisation is defensible so long
as the paper says which. The 1.2-point gap moves no conclusion — novelty is 0.98
either way.

**A caution written here first was wrong and is withdrawn.** It said the paper
"contrasts 0.99 against 0.94, a gap of the same order as the artefact". Those two
numbers are **`fact_ngram` on NDC and on WD50K** — the two *collections* for one
arm, in the `X / Y` form used throughout — **not** a contrast between arms. Both
sides carry the artefact equally, so that comparison is on a consistent
normalisation and needs no caution. Written without establishing what the two
figures were, which is the defect this very section documents.

**The measured novelty, per arm and collection** (`IEEETKDE_isal_reach1b`, 27
seeds):

| collection | `ow_ngram` | `fact_ngram` | `incidence_ngram` |
|---|---|---|---|
| ndc_classes | 0.9172 | **0.9883** | 1.0000 |
| wd50k66 | 0.9138 | **0.9425** | 1.0000 |

**The fact alphabet is more novel than the ordered walk on both collections** —
a place the retired comparator beats us, and it is reported as such. The
artefact inflates the *fact* side, so correcting it **narrows** that lead rather
than widening it: on NDC from 0.0711 to about 0.0603. The reported gap is
therefore an over-statement of the comparator's advantage, not an under-statement
of ours, and the honest sentence says which normalisation produced it.

(`incidence_ngram` at 1.0000 is not a result: its validity is 0.0190 / 0.0102, so
the handful of samples that decode at all are all novel.)
