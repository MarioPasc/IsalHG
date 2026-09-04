# Follow-up — which regime is the NDC natural series in?

2026-09-04, companion to `probe_f4_topology.md` §4 and §9. The 555 encodable consecutive NDC-classes quarterly pairs are split on the ARB node-id sets of their
two members: **constant-set-preserving** iff `V_t = V_{t+1}` (the fact-level difference neither introduces nor strands a constant), **changing** otherwise.
`followup_ndc_regime.py`; E-A distances read from the cached `m2_rows_ndc.json`, so no new canonicalization was run (`followup_ndc_regime.json`). **Split: 140
preserving, 415 changing (25.2 % / 74.8 %).**

## 1. The two regimes scored separately

`ρ`/`r` = Spearman/Pearson of `Δ` against `d`; "med d" = median distance per `Δ` stratum; Δ=1 columns = fractions within 2 and 5 tokens, and median `d/|w|`.

| split | enc | n | ρ | r | med d at Δ = 0 / 1 / 2 / 3–5 / >5 | Δ=1 n | ≤2 | ≤5 | med d/\|w\| |
|---|---|---|---|---|---|---|---|---|---|
| preserving | E-A | 108 | 0.965 | 0.760 | 0 / 5 / 5 / — / — | 18 | .167 | .556 | .561 |
| preserving | **E-B** | 140 | **0.962** | 0.817 | 0 / **1** / 2 / — / — | 35 | **.771** | **1.000** | **.077** |
| preserving | E-C | 140 | 0.903 | 0.827 | 0 / 14 / 11 / — / — | 35 | .000 | .000 | 1.000 |
| changing | **E-A** | 365 | **0.511** | 0.510 | — / **4** / 3 / 6 / 13 | 75 | **.400** | **.707** | **.400** |
| changing | E-B | 415 | 0.281 | 0.315 | — / 7 / 6 / 8 / 9 | 85 | .000 | .059 | .533 |
| changing | E-C | 415 | 0.307 | 0.367 | — / 16 / 13.5 / 17 / 20 | 85 | .000 | .000 | 1.125 |

**Reading** (stratum sizes — preserving 85 / 35 / 20 / 0 / 0, changing 0 / 85 / 114 / 191 / 25). The regimes separate cleanly and **invert the ranking**. On preserving pairs E-B is what the synthetic ladders promised — Δ=1 median
**1 token**, 77 % within 2, **100 % within 5**, normalized median 0.077, i.e. **7× tighter than E-A's 0.561**. On changing pairs E-B collapses below the status
quo: Δ=1 median 7 tokens against E-A's 4, **0 %** within 2 against E-A's 40 %, ρ 0.281 against 0.511. The pooled §4 figure (E-B ρ 0.632, no better than E-A's
0.683) is an average of these two, dominated 3:1 by the regime where E-B loses. **One caveat, stated**: the splits are not exchangeable in `Δ` — preserving the
constant set caps how many facts can differ, so every preserving pair has `Δ ≤ 2` while the changing split carries the whole range. The ρ values are therefore
not comparable across splits; the Δ=1 columns and the per-stratum medians are, and they say the same thing.

## 2. How much variant series survives inside E-B's strong regime

Maximal runs of consecutive encodable quarters with one constant set throughout (equality is transitive, so a run whose consecutive pairs all preserve has one set):

| quantity | value |
|---|---|
| drug classes with ≥ 1 encodable quarter | 172 |
| classes with a preserving run of length ≥ 3 | **15** |
| classes with a preserving run of length ≥ 5 | **2** |
| longest preserving run anywhere | 5 quarters |
| runs of length ≥ 3 / ≥ 5, all classes | 29 / 2 |

**Restricting to E-B's strong regime all but destroys the corpus**: 15 of 172 classes (8.7 %) reach a 3-quarter series and 2 reach 5, with no run longer than 5.
A consensus experiment scoped to constant-set-preserving NDC series would run on ~15 series of 3–5 members; as presently scoped it therefore sits in **E-B's weak
regime**, where E-A is the better-behaved encoding.

## 3. Does the degradation scale with how many constants move?

Over the 415 changing pairs, `moved = |V_t △ V_{t+1}|`: median **6**, mean 6.17, max 25 — comparable to the KBs' median `n` of 9.

| correlation | ρ |
|---|---|
| moved vs `d_B` | **0.503** |
| moved vs `d_C` | 0.390 |
| moved vs `d_A` (365 pairs with a cached `w*_c`) | 0.430 |

**Yes, and it hurts E-B most.** E-B's distance tracks the moved-constant count at ρ = 0.503, above E-A's 0.430 — the mechanism predicted in §9: every moved
constant renumbers the canonical ranks downstream of it, so E-B's word churns in proportion to the constants that move rather than to the facts that change.
E-A, whose pointer runs are already noisy, is less sensitive in relative terms.

**Picasso.** Array `2206622` had **not** finished at 21:14 (tasks 0–1 COMPLETED, tasks 2–3 RUNNING at 1 h 35 m), so the full-scale E-A numbers are not in and
nothing here waits on them. Every E-A figure above comes from the cached local subsample (365 of 415 changing, 108 of 140 preserving pairs); the cluster run can
only tighten those coverages, not change which regime a pair falls in.
