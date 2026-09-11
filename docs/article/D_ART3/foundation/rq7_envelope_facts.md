# RQ7 operating envelope — the verified fact base

Every number the prose may quote for RQ7, with the run that produced it. Same
rule as `rq6_generation_facts.md`: **a number with no entry here is struck, not
kept**, whichever way it points, and this is a precondition on the T-KBg fold
rather than a cleanup inside it.

## Provenance

| | |
|---|---|
| results root | `IEEETKDE_isal/RQ7_envelope/envelope/` — **not** `IEEETKDE_isal_merged`, which carries no envelope sweep |
| job | 2271960 (array), 369 files, newest 2026-09-11 02:01 |
| tables | `rows_sweep*.csv` (39,204 rows), `rows_yield_members*.csv` (26,994), `rows_nscaling*.csv` (174) |
| grid | 6 `m` × 4 `k` × 3 `\|Σ_E\|` × 2 `\|Σ_V\|` × 2 density × 27 seeds = **7,776** per arm |
| extension | `fact_rank` / `nauty_cert` only: `m ∈ {320, 640, 1280}` at `k=3` → +162 = **7,938** |
| budget | 60 s per instance |
| reading | `scripts/diagnostics/rq7_envelope_reading.py` (claims + refutation conditions pre-registered in its docstring before it read a row) |
| local mirror | `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/` |

Completeness verified per arm: 7,776 / 7,776 / 7,776 / 7,938 / 7,938.

## 1. Censoring per arm × `aut_bucket` — a total tabulation, nothing selected

| `aut_bucket` | n | `isalhg_levenshtein` | `wstar_orbit` | `isal_ow_struct` |
|---|---|---|---|---|
| `<1e3` | 6,734 | 2094 (31.1 %) | 1953 (29.0 %) | **0** |
| `1e3–1e6` | 615 | 548 (89.1 %) | 400 (65.0 %) | **0** |
| `≥1e7` | 427 | 427 (**100 %**) | 392 (91.8 %) | **0** |

`fact_rank` and `nauty_cert`: **0 censored in every bucket** (including the
extension, 508 rows at `≥1e7`).

**The quotable claim.** The ordered walk censors **0 of 7,776**, including all
427 instances at `|Aut| ≥ 1e7` where the pointer alphabet fails every one. No
interval is needed: this is a census, not an estimate.

## 2. The join — symmetry against size

The `|Aut|` marginal is confounded: **all 427 instances at `≥1e7` have `m ≥ 80`**
(min 80, median 160, max 160; none at `m ∈ {10,20,40}`).

Censoring at fixed `(m,k)` across `aut_bucket`, 15 cells with two levels at
n ≥ 5: **rises in 9, falls in 0.** Pooled median rise +0.006, an artefact of
saturation (most cells pinned at 0.00 or 1.00).

`wstar_orbit` censoring on the `(m, k)` grid:

| k | m=10 | 20 | 40 | 80 | 120 | 160 |
|---|---|---|---|---|---|---|
| 2 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 3 | 0.000 | 0.000 | 0.009 | 0.340 | 0.519 | 0.648 |
| 4 | 0.000 | 0.034 | 0.315 | 0.756 | 0.926 | 0.997 |
| 5 | 0.009 | 0.269 | 0.670 | 0.981 | 1.000 | 1.000 |

**Arity gates; symmetry modulates inside the gate.** `k = 2` is 0.000 at every
`m` and every symmetry level, including **0/22** at `m = 160`, `|Aut| ≥ 1e7`.

## 3. H7a — the frontier is `m`, not `n`

Within `aut_bucket <1e3` (symmetry held fixed), `wstar_orbit`:

| | m=10 | 20 | 40 | 80 | 120 | 160 |
|---|---|---|---|---|---|---|
| sparse (median n = 1.5 m) | 0.005 | 0.142 | 0.371 | 0.447 | 0.477 | 0.526 |
| dense (median n = 0.5 m) | 0.000 | 0.009 | 0.153 | 0.432 | 0.588 | 0.633 |

Monotone in `m` in both series; the density effect (a pure `n` move) is
non-monotone and **changes sign at m ≈ 100**. Marginally the two looked
comparable (1.017 vs 1.278 median `|log₂|` cost ratio) — the join overturned it,
because **every dense cell sits in `<1e3`**.

## 4. Real collections placed on the grid — the RQ1 reconciliation

| collection | n | median m | p90 | max | at `m ≥ 80` |
|---|---|---|---|---|---|
| `ndc_classes` | **828 of 1,381** | 3 | 5 | 30 | 0 — **partial, see below** |
| `ndc_substances` | 1,745 | 4 | 16 | 41 | **0** |
| `wd50k100` | **919 of 1,837** | 5 | 11 | 27 | 0 — **partial, see below** |
| `wd50k66` | 3,988 | 5 | 11 | 29 | **0** |
| `wd50k66_full` | 4,554 | 5 | 18 | 303 | 41 (0.9 %) |

**RQ1 (orbit pruning takes censoring at `|Aut| ≥ 1e7` from 36 to zero on real
corpora) and RQ7 (orbit censors 392/427 in that bucket) are both correct and
describe disjoint regions.** Every `≥1e7` sweep instance has `m ≥ 80`; **no
member of `wd50k66` (3,988) or `ndc_substances` (1,745) — the two gated
collections read whole — reaches it**; at the real median `m ≈ 5` the sweep
censors 0.000 at every arity.

Two qualifications belong beside it, not in a footnote. `ndc_classes` and
`wd50k100` are read partial (§ below) and are evidence neither way. And
**`wd50k66_full` — the ungated variant of `wd50k66` — has 41 members (0.9 %) at
`m ≥ 80`**: the claim is about the *gated* collections, **not** about real
knowledge bases in general, and the row four lines above says so. **The paper
states this explicitly** — both numbers are going in, and unreconciled they are
a reviewer's gift.

## 5. Yield on the real collections (60 s budget, one row per member)

| collection | `fact_rank` | `isal_ow_struct` | `isalhg_levenshtein` | status |
|---|---|---|---|---|
| `ndc_classes` ⚠ | 828/828 | 828/828 | 726/828 = 0.877 | *(60 % of 1,381 — no claim)* |
| `ndc_substances` | 1745/1745 = 1.000 | **1745/1745 = 1.000** | 1489/1745 = 0.853 | complete |
| `wd50k100` ⚠ | 919/919 | 919/919 | 771/919 = 0.839 | *(50 % of 1,837 — no claim)* |
| `wd50k66` | 3988/3988 = 1.000 | **3988/3988 = 1.000** | 3742/3988 = 0.938 | complete |
| `wd50k66_full` | 4554/4554 = 1.000 | not run | not run |

Median cost on completed members: `fact_rank` 0.156–0.199 ms,
`isal_ow_struct` **0.573–0.696 ms** (3.5× the certificate, same order),
`isalhg_levenshtein` 4.235–13.533 ms.

## 6. H7b — reported as the measurement, not as a surviving half

| arm | stratum | cells | worst cell median | censored |
|---|---|---|---|---|
| `fact_rank` | main grid (m ≤ 160) | 288 | 7.2 ms | 0 |
| `fact_rank` | extension (320–1280) | 6 | **6,241 ms** | 0 |
| `nauty_cert` | main grid | 288 | 6.8 ms | 0 |
| `nauty_cert` | extension | 6 | **6,282 ms** | 0 |

H7b claimed "microseconds to milliseconds across the whole grid **and far beyond
it**". It holds on the grid and fails by three orders of magnitude at
`m = 1,280`. The measurement above is what is reported; the hypothesis is not
defended, and note the refutation runs **in our favour** (H7b is a claim about
the competitor's strength), which is the direction to state most conservatively.

## 7. Within-cell symmetry sensitivity — a floor

Spread of median `log₂(secs)` across `aut_bucket` within a fixed
`(m, k, |Σ_E|, |Σ_V|, density)` cell:

| arm | usable cells | median spread | p90 |
|---|---|---|---|
| `isal_ow_struct` | 38 | 0.147 | 0.431 |
| `fact_rank` | 38 | 0.113 | 0.408 |
| `nauty_cert` | 38 | 0.144 | 0.364 |
| `wstar_orbit` | 12 | 0.565 | 0.906 |
| `isalhg_levenshtein` | 4 | 3.507 | 3.865 |

Search/walk ratio **3.84×**. Quoted **only with its direction**: `wstar_orbit`'s
12 usable cells are the ones where it did *not* censor — where symmetry cost it
least — so the true spread is higher and 3.84× is a **lower bound**. The ordered
walk sits level with both certificate arms (0.147 against 0.113 / 0.144).

## 8. H7c — withheld

Two array tasks were still running at the time of reading (`isal_ow_struct` at
N=250, `wstar_orbit` at N=3,988), so both Isal arms have a truncated `N` range
and **no slope is fitted on it** — a slope over a truncated range is a different
quantity and would have to be re-reported later under the same name.

Competitors, complete over `N ∈ {250, 500, 1000, 2000, 3988}` (log-log slope of
the pair phase on `N`): `bipartite_ged_assign` 1.913, `bipartite_ged_path`
1.924, `wl_l1` 1.872, `nauty_cert` 1.706, `nauty_cert_rows` 1.638, `netlsd`
1.494, `degree_seq_l1` 1.476, `size_l1` 1.149.

### ⚠ Two collections were read partial, and the slice is not random

Raised by `[IsalHG-Fable]`, who noticed the yield table gives `ndc_classes` at
**828** where RQ1's census gives **1,381**. The corpora manifest is
authoritative: 1,381. The yield pass shards a collection by contiguous
`block_slice`, and for `ndc_classes` only blocks **002, 003, 004 of 005** have
landed; for `wd50k100`, block **000 of 002** (manifest: 1,837). Nothing failed —
array tasks 60 and 64 are still running.

**The slice is ordered in `m`, descending.** Measured on the collections that
*are* complete, block medians run 6, 6, 5, 4, 4, 3 (`ndc_substances`) and
5, 5, 4, 4, 4, 5 (`wd50k66`). So the direction differs per collection and must
be stated per collection:

| collection | read | blocks present | missing | which end |
|---|---|---|---|---|
| `ndc_classes` | 828 / 1,381 (60 %) | 2, 3, 4 | **0, 1** | its **largest** members |
| `wd50k100` | 919 / 1,837 (50 %) | 0 | 1 | its smallest members |

So `ndc_classes`'s observed maximum of `m = 30` is a **floor**, and its
`m ≥ 80` count of zero is **not yet established** — the unread blocks are
exactly where a large member would be. `wd50k100`'s zero is on the larger half
and is the better-supported of the two. Neither carries a yield claim until its
blocks land.

**What this cost, and why the guard did not fire.** The sweep's expected row
counts were declared up front (7,776 / 7,938) and verified; the yield's were
not, so "828/828 = 1.000" reported a rate over whatever had arrived. The rule
that catches this is L26's — *declare the input* — applied to one half of the
same script and not the other. `rq7_envelope_reading.py` now asserts every
collection against the manifest and names the absent blocks, since the blocks
present cannot report the ones that never landed.

**What the partial read does and does not reach.** Stated as a boundary so no
reader re-checks the rest of this document:

| affected | unaffected |
|---|---|
| the yield table's `ndc_classes` and `wd50k100` rows | **the sweep: 0 of 7,776, verified per arm** |
| the `m`-distribution table's two partial rows | the arity gate (`k=2` at 0.000 everywhere) |
| the reconciliation's population, now named | the within-cell symmetry rises (9 of 15, 0 falling) |
| | the whole `(m,k)` × `aut_bucket` join |
| | H7a's frontier reading (sweep rows only) |
| | H7b's certificate-arm measurement (sweep rows only) |

Every affected figure draws on `rows_yield_members`; nothing in the sweep
analysis touches those rows.

**The claim that survives unchanged.** The 0-of-7,776 sweep censoring is
untouched: the sweep is complete and verified per arm. The real-corpus yield
claim currently rests on `wd50k66` (3,988) and `ndc_substances` (1,745) read
whole — 5,733 members, every one canonicalized by the ordered walk — and is
restated to those two until the rest lands.
