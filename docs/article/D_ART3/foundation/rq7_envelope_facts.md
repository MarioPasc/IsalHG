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
| `ndc_classes` | 1,381 | 3 | 5 | **30** | **0** |
| `ndc_substances` | 1,745 | 4 | 16 | 41 | **0** |
| `wd50k100` | 1,837 | 5 | 11 | 27 | **0** |
| `wd50k66` | 3,988 | 5 | 11 | 29 | **0** |
| `wd50k66_full` | 4,554 | 5 | 18 | 303 | **39** (0.86 %) |

**RQ1 (orbit pruning takes censoring at `|Aut| ≥ 1e7` from 36 to zero on real
corpora) and RQ7 (orbit censors 392/427 in that bucket) are both correct and
describe disjoint regions.** Every `≥1e7` sweep instance has `m ≥ 80`; **no
member of any of the four gated collections — 8,951 members in all — reaches
it**; at the real median `m ≈ 5` the sweep
censors 0.000 at every arity.

Two qualifications belong beside it, not in a footnote. And
**`wd50k66_full` — the ungated variant of `wd50k66` — has **39** members (0.86 %) at
`m ≥ 80`**: the claim is about the *gated* collections, **not** about real
knowledge bases in general, and the row four lines above says so. **The paper
states this explicitly** — both numbers are going in, and unreconciled they are
a reviewer's gift.

## 5. Yield on the real collections (60 s budget, one row per member)

| collection | `fact_rank` | `isal_ow_struct` | `isalhg_levenshtein` | status |
|---|---|---|---|---|
| `ndc_classes` | 1381/1381 = 1.000 | **1381/1381 = 1.000** | 1263/1381 = 0.915 | complete |
| `ndc_substances` | 1745/1745 = 1.000 | **1745/1745 = 1.000** | 1489/1745 = 0.853 | complete |
| `wd50k100` | 1837/1837 = 1.000 | **1837/1837 = 1.000** | 1541/1837 = 0.839 | complete |
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

## 8. H7c — measured (the last N cells landed 03:15)

**The full 3,988 × 3,988 matrix on `wd50k66`.** Whole-matrix wall-clock, median
of 3 reps, censored/skipped reps excluded:

| arm | whole matrix | canon phase | pair phase |
|---|---|---|---|
| `fact_rank` | **1.11 s** | 0.221 | 0.889 |
| **`isal_ow_struct`** | **1.39 s** | 0.414 | 0.971 |
| `size_l1` | 2.81 s | 0.004 | 2.804 |
| `degree_seq_l1` | 12.62 s | 0.017 | 12.602 |
| `nauty_cert_rows` | 13.87 s | 0.328 | 13.541 |
| `nauty_cert` | 24.19 s | 0.234 | 23.960 |
| `netlsd` | 40.61 s | 10.757 | 29.850 |
| `wl_l1` | 564.21 s | none | 564.208 |
| `bipartite_ged_assign` | 10.6 min | none | 634.016 |
| `bipartite_ged_path` | 15.9 min | none | 952.501 |
| `wstar_orbit` | 28.9 min | 1737.537 | *< noise* |
| `hpd_jsd` | **≥ 60 min** | — | **censored at the 1 h cap** |

**H7c said "seconds for `fact_rank`, minutes for the embeddings, hours for
bipartite GED".** The ordering holds; two magnitudes do not. NetLSD is
**seconds** (40.6 s), not minutes, and bipartite GED is **minutes** (10.6 /
15.9), not hours. As with H7b, the misses run **in the competitors' favour** —
they are faster than predicted — so the measurement is reported and the
hypothesis is not defended.

**No speed claim against the certificate survives, in either tokenisation — and
the reading is parity, not a reversal.** Measured on `wd50k66`, 400 identical
members, same machine, min of 3 reps, 160,000 ordered pairs:

| | secs | s/pair |
|---|---|---|
| `nauty_cert_rows` `matrix()` — **Python double loop** | 0.0561 | 3.51e-07 |
| `isal_ow_struct` `matrix()` | 0.0236 | 1.47e-07 |
| `nauty_cert_rows` bare `cdist` | 0.0052 | 3.25e-08 |
| `isal_ow_struct` bare `cdist` | 0.0044 | 2.73e-08 |

| comparison | ratio | what it measures |
|---|---|---|
| both bare `cdist` | rows **1.19×** | **parity** — the representations |
| both `matrix()` | rows **2.38×** | the rows arm's Python loop |
| rows `cdist` vs walk `matrix()` | 0.22× | **not a comparison** |

Two real findings and one retracted. **Real:** `nauty_cert_rows.matrix()` fills
the upper triangle in a Python loop while `isal_ow_struct` and `nauty_cert` call
`process.cdist` — a **10.8×** penalty over a bare `cdist` on its own
fingerprints, against the walk's 5.4×, and it falls on the arm D-ART4 designates
as the *non-confounded* comparator (→ T-KBy). **Also real:** every arm's
`matrix()` carries substantial overhead above a bare `cdist` — 5.4× for the walk
— which every RQ matrix pays. **Retracted:** an earlier revision of this section
read "the row-tokenised certificate is 4.5× *faster* than the Isal word", from
comparing a bare `cdist` on precomputed row fingerprints against a full
`matrix()` call on the walk. Those are different operations. At equal
implementation the two are **at parity**; `[IsalHG-Fable]` caught it against this
section's own cdist table, which had said 1.09× four lines above.

And the byte figure is an artefact in the other direction. Three tokenisations of
the *same* canonical form, all via `cdist`, span **19.2×**:

| handed to `rapidfuzz` as | mean L | s/pair | ratio to the walk |
|---|---|---|---|
| bytes | 160.5 | 6.22e-07 | 20.9× |
| 4-byte integers | 40.1 | 7.94e-08 | 2.66× |
| adjacency rows | 15.2 | 3.24e-08 | **1.09×** |
| *(walk tokens)* | 13.7 | 2.98e-08 | 1× |

So the pair-phase cost of this canonical form is **whatever its serialisation
says it is**, and a multiplier against it states a tokenisation choice rather
than a property of either representation. **L17 already ruled this out** —
*"concede identity and deduplication speed to nauty/bliss/Traces … never build a
claim on canonicalization speed"* — and the headline had drifted into exactly the
claim the lesson base forbids. It does not need a reversal to retire; parity
retires it.

**What survives, and it is the paper's actual claim.** `isal_ow_struct` 1.39 s
against `wstar_orbit` **28.9 min — 1,252×**. Same alphabet, same tokenisation,
same distance, same `matrix()` path — so the wrapper overhead appears on both
sides and cancels — same corpus: **the search is what costs, and the same
language without it is three orders of magnitude cheaper.** Nothing in this
correction touches it.

The certificate comparison is reported as a table of tokenisations with the
implementation penalty named, and **carries no multiplier in either direction**.

*Mechanism: measured, and it is length — at the granularity the library
actually sees.* The gap is in the pair phase (0.971 s against 23.960 s,
**24.7×**). Measured on `wd50k66` itself, 400–500 member samples:

| | median | mean | max |
|---|---|---|---|
| `isal_ow_struct` (**tokens**) | 6 | 13.8 | 141 |
| `nauty_cert` (**bytes**) | 140 | 159.7 | 460 |
| `nauty_cert` (**4-byte integers**) | 35 | 39.9 | 115 |
| `fact_rank` (tokens) | 12 | 15.1 | 53 |

**400 of 400 certificate lengths are divisible by 4** — it is a sequence of
4-byte big-endian integers, so its natural symbol count is `bytes/4`. But
`rapidfuzz` is handed the **bytes**, and a runtime is governed by what the
algorithm iterates over, so the byte length is the one in the cost model:
Myers' `O(L₁·⌈L₂/64⌉)` predicts 481.6 against the walk's 13.7, i.e. ≈35×,
against 24.7× measured — with the residual in the expected direction, since the
walk's arm sits 41× above its own compute floor and cannot scale down
proportionally.

**Re-timed at each granularity** (500 members, `process.cdist`, same machine):

| handed to `rapidfuzz` as | mean L | s/pair | ratio to the walk |
|---|---|---|---|
| bytes | 160.5 | 6.23e-07 | **20.9×** |
| 4-byte integers | 40.1 | 7.95e-08 | **2.67×** |
| walk tokens | 13.7 | 2.98e-08 | 1× |

**Granularity alone accounts for 7.83× of the certificate's measured cost.** At
its own symbol granularity the certificate costs **2.67×** the Isal word — which
is the 2.9× length ratio, and is the representation-level number.

**This is why D-ART4 requires both tokenisations, and it is a point in favour of
the methodology rather than a caveat.** The byte comparison *overstates* the
certificate's cost, because bytes are a finer granularity than the
representation's own symbols; the row figure is the one that is not an artefact
of how the comparator was serialised for the comparison. So the paper reports
both and **the claim rests on the row tokenisation**, never on the byte one.

*(The lengths previously quoted here — 3,886 tokens against 11,692 bytes — are
from the **sweep** at `m = 160`, not from `wd50k66`, whose members have median
`m = 5`. Quoting them beside a `wd50k66` matrix timing invited the inference that
the matrix could not be doing full pairwise work; `[IsalHG-Fable]` made it, and
the figures were mine to put there. A first correction then went too far the
other way, using the natural-unit ratio to declare the length mechanism
disconfirmed — the same error one turn later, in the opposite direction. The
measurement above settles it.)*

**Compactness at member granularity** — a statement the paper has not previously
had: on real members the ordered walk's median word is **6 tokens** against the
certificate's **140 bytes / 35 symbols**.

**Two arms' `censored` / `nan` handling matters here.** `hpd_jsd` recorded
exactly 3600.000 s at N=3,988 with `censored=1` and its other two reps
`skipped=1`: that is the cap, not a measurement, and it is reported as a lower
bound. `wstar_orbit`'s canon pass (1737.5 s) slightly *exceeds* its whole-matrix
pass (1736.4 s) in all three reps — two separate timing passes of the same
~1,736 s work, so its pair phase is below run-to-run noise rather than negative.

**`wstar_orbit` does not follow a power law, so no slope is quoted for it.**
Canon totals against a constant doubling of `N`:

| N | 250 | 500 | 1,000 | 2,000 | 3,988 |
|---|---|---|---|---|---|
| canon total | 16.4 s | 48.3 s | 292.0 s | 907.9 s | 1,737.5 s |
| step | — | 2.95× | **6.04×** | 3.11× | 1.91× |

A fitted exponent of 1.771 over that series is a summary that hides its
structure: the cost is dominated by a few expensive members, so what matters is
*which* members enter at each `N`, not `N` itself. The series is reported; the
exponent is not.

**Log-log slopes where a power law does hold** (N ∈ {250, 500, 1000, 2000,
3988}; `canon` = canonicalization phase, `whole` = whole matrix — **not** a pair
slope, since `secs_pairs_total` is the whole-matrix time):

| arm | canon | whole |
|---|---|---|
| `bipartite_ged_assign` | — | 1.913 |
| `bipartite_ged_path` | — | 1.924 |
| `wl_l1` | — | 1.872 |
| `nauty_cert` | 0.842 | 1.706 |
| `nauty_cert_rows` | 0.876 | 1.638 |
| `netlsd` | 0.906 | 1.494 |
| `degree_seq_l1` | 0.871 | 1.476 |
| `size_l1` | 1.034 | 1.149 |
| `isal_ow_struct` | 0.798 | 0.837 |
| `fact_rank` | 0.824 | 0.687 |
| `hpd_jsd` | withheld | withheld (censored) |

Canonicalization is ≈ linear across every arm that has one (0.80–1.03), as H7c
predicted. The whole-matrix slope reaches ≈ 1.9 only for the arms whose pair
phase dominates; for `fact_rank` and `isal_ow_struct` the matrix is fast enough
at N = 3,988 that fixed overhead still flattens the curve, so their sub-linear
slopes are an artefact of the range, not evidence against an `N²` pair phase.

## 9. Per-member canonicalisation — the L17 concession (feeds RQ2 step 5)

`wd50k66`, N = 3,988, canonicalisation phase of the N-scaling pass: every arm on
the same code path, machine and corpus.

| arm | per member | vs `nauty_cert` |
|---|---|---|
| `fact_rank` | 0.0555 ms | 0.95× |
| `nauty_cert` | 0.0587 ms | 1.00× |
| `nauty_cert_rows` | 0.0823 ms | 1.40× |
| **`isal_ow_struct`** | **0.1039 ms** | **1.77×** |
| `netlsd` | 2.6974 ms | 45.9× |
| **`wstar_orbit`** | **435.69 ms** | **7,420×** |

The ordered walk is **1.77× one certificate call** — it makes that call and adds
the walk, so this is one call plus 77 %. The tie-complete form is **7,420×**, and
the two Isal arms differ by 4,193× on the same corpus and path.

**Not to be mixed with the yield figures.** The yield rows measure the harness
path (a forked budget guard per member): `fact_rank` 0.187 ms, `isal_ow_struct`
0.654 ms on the same corpus — **3.4×** and **6.3×** the canon-loop values. The
overhead is not constant across arms, so the two bases are not interchangeable.

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
| `ndc_classes` | 1,105 / 1,381 (80 %) | 0, 2, 3, 4 | **1** | its **#2 of 5** band in descending-m order |
| `wd50k100` | **1,837 / 1,837 — complete as of 03:15** | 0, 1 | — | — |

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

**RESOLVED 2026-09-11 03:21 — array 2271960 is 74/74 COMPLETED.** All five
collections are now whole (1,381 / 1,745 / 1,837 / 3,988 / 4,554), and the
outcome is worth recording because it was **not** the safe assumption:

| | partial read | complete |
|---|---|---|
| `ndc_classes` members | 828, then 1,105 | **1,381** |
| its max `m` | 30 (a *floor*) | **30** |
| its members at `m ≥ 80` | 0, unestablished | **0**, established |
| `isal_ow_struct` yield | 828/828, no claim | **1381/1381** |

The unread blocks were the large-`m` end, so the floor could have moved and did
not. That is the reason the claim was held rather than shipped with a hedge: a
hedge would have been indistinguishable from this result, and only the
measurement separates them.

One correction the completion also forced: `wd50k66_full` has **39** members at
`m ≥ 80`, not the 41 stated earlier. The 41 was **reconstructed from a rounded
rate** — 0.009 × 4,554 — rather than counted. A count derived from a displayed
percentage is not a count, and the rounding that makes a rate readable is
exactly what makes it unusable in the other direction.

**The claim that survives unchanged.** The 0-of-7,776 sweep censoring is
untouched: the sweep is complete and verified per arm. The real-corpus yield
claim currently rests on `wd50k66` (3,988) and `ndc_substances` (1,745) read
whole at the time — 5,733 members — and is restated to all four (8,951) now
that the rest has landed.
