# RQ2 well-posedness — the verified fact base

Every number `prose.md` may quote for RQ2, with the run that produced it. Same
rule as the other entries: **a number with no entry here is struck, not kept.**

## ⚠ The dominant direction here is the *inverse* one

`prose.md`'s RQ2 section (line 342) is a **plan, not results** — Hypothesis /
Evidence / Evaluation, and no measured figure. A screen of every number within
±1 line of its seven RQ2 mentions returns **four small integers, all collisions**;
six of the seven mentions are the Prop/Thm table's "which RQ" column and the
seventh is the section heading.

So for RQ2 the fold is a **fill**, not an audit: the results below exist in the
record and appear nowhere in the prose. That is the defect the precondition's
bidirectional half was added for — *"a result present in the fact base and absent
from the prose is as much a defect as a number in the prose absent from the fact
base"* — and RQ2 is its largest instance.

## Provenance

| | |
|---|---|
| main rows | `results/IEEETKDE/RQ2_wellposedness/` — the **shared** tree (RQ3–RQ7 moved to the clean `IEEETKDE_isal` root; RQ2 stayed, its rows tag-separable) |
| jobs | **2265309** (main), **2265310** (census, 9/9 COMPLETED) |
| tables | `rows_census` (66 files), `rows_exact0` (86), `rows_oracle` (15), `rows_bipartite` (7), `rows_certificate` (2), `rows_hypercot_timing` (2) |

**`2265309_10` was OUT_OF_MEMORY and it is a non-event for the data.** The log
shows `unit bipartite-ndc_classes done in 7792.2 s` and the kill **nine seconds
later**, after the rows were written; the job asked 32 GB and peaked at 33.4 GB
in its in-job finalisation. **All 85 of 85 units have rows.** Only
`tables.md` / `stats.json` / `summary.json` were lost and they regenerate from
the rows.

### Step 4's root question — resolved, not assumed

`rows_certificate.csv` exists in **four** roots, because step 4 had to be re-run
against the new certificate file once RQ3 landed:

| root | rows | written |
|---|---|---|
| `IEEETKDE` | 35,656 | 09-05 |
| `IEEETKDE_isal` | 46,407 | 09-09 15:28 |
| `IEEETKDE_isal_reachprime` | **49,027** | 09-09 19:04 |
| `IEEETKDE_isal_consensus` | **49,027** | 09-10 20:49 |

The last two share a row count and differ in checksum, so size cannot pick
between them. Diffed per row on `(collection, collection_id, arm)`:
**identical keys, 0 only-either-side, and every column identical except `secs`**
across all 49,027 rows. So the two are the same computation re-run, step 4's
**values are not root-dependent** between them, and the newest (`consensus`) is
the current one. The two earlier roots are superseded and must not be quoted.

## 1. The false-merge census — `n_false_merges`, and whether the induced partition is the true one

| arm | `ndc_classes` | `ndc_substances` | `wd50k66` | partition |
|---|---|---|---|---|
| **`wstar_orbit`** | **0** | **0** | **0** | **exact** (530 / 1,086 / 3,677) |
| `nauty_cert`, `nauty_cert_rows` | 0 | 0 | 0 | exact |
| `fact_rank` | 0 | 0 | 0 | exact |
| `wl_l1` | 0 | 0 | 0 | exact |
| `bipartite_ged_path` | 0 | 0 | 0 | **splits** — 574 classes against 557 |
| `netlsd` | 2,516 | 1 | 185,917 | merges |
| `hpd_jsd` | 7,618 | 9,885 | 212,179 | merges |

**The headline: `1,086 = 1,086` on the campaign's most arity-heavy collection**,
in 8,446 s — RQ2's exactness result, measured rather than assumed. H2a holds:
every incomplete representation merges non-isomorphic members at a non-zero rate
on some collection; the complete ones merge none.

`bipartite_ged_path` is the instructive row: **zero false merges but the wrong
partition**, splitting 574 classes where 557 exist, because it *separates*
isomorphic members. A representation can fail well-posedness by splitting as
well as by merging, and only the partition column shows it.

## 2. Step 4 / H2d — the medoid's certificate under a non-metric

`bipartite_ged_path` violates `LB ≤ cost` **27 times** — the pre-stated
consequence of its not being a metric. Under `fact_rank` and `nauty_cert` it
never does. So a medoid "certificate" computed under that pipeline can **lie**,
which is the measurable consequence H2d predicted.

## 3. Step 5 — identity timing, the L17 concession

Measured 2026-09-11 (the last outstanding RQ2 section, gated on RQ7's
N-scaling). Full table and caveats in `rq7_envelope_facts.md` §9; the two
numbers RQ2 needs:

- **the walk costs 0.058 ms on top of a 0.040 ms canonical-labelling call that
  every arm in the comparison pays** — cluster (`sd022`), 200 `wd50k66` members,
  **medians**;
- the tie-complete form's per-member cost is **435.69 ms as a mean** and
  **0.36 ms as a median** — a 790× divergence, so the statistic must be labelled
  and the concession's sentence takes the **median**.

**No speed claim against the certificate survives in either tokenisation**
(parity; L17). See `rq7_envelope_facts.md` §8.

## Status

**Screened, not audited.** The numbers above are sourced to runs and tables; the
**predicate pass** — does the noun beside each number name the right object —
has not run. And for RQ2 the fold's larger job is the inverse one: these results
are absent from the prose entirely.
