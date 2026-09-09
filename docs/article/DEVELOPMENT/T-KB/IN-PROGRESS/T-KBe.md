# T-KBe — RQ1 harvest, merged table, and the representation decision

**Status:** OPEN · declared 2026-09-07 22:10 CEST by the Isal-refinement
orchestrator (handoff `../../../D_ART3/experiments/HANDOFF_2026-09-07_isal.md` §5.1–5.2).

## What

1. When jobs 2247394+2247395 (`addressing`), 2248782 (`addressing_rank`)
   and 2248907+2248908 (`addressing_cpp`) are terminal, harvest the three
   experiments into `results/IEEETKDE_isal/RQ1_addressing/` (not into the
   campaign's `RQ1_addressing/addressing`, which is the frozen record).
2. Merge with `experiments/tkde/merge_rq1_experiments.py` — one source per
   arm: `wstar_rank` from `addressing_rank`; `wstar_orbit`, `isal_ow_*`
   from `addressing_cpp`; the rest from `addressing` — into a separate root
   under the analyzer's default name, then `analyze_rq1 --root`.
3. Verify the join (equal seeded edit sets per unit across experiments).
4. Persist `tables.md`, `stats.json`, `manifest.json` + the merge manifest
   under `results/IEEETKDE/RQ1_isal/`.
5. Apply the pre-registered selection rule (`ISAL_VARIANT_DESIGN.md` §3) and
   bring the table, the per-kind reading and the R2 table to the author/PI
   for the decision (which canonical program carries RQ2–RQ7; the nauty
   sentence).

## Acceptance

M0 = 0/0/0 for every Isal arm; the table reports absolute instructions
first (L11), the ≤ 2 fraction, censoring per (arm, m, |Aut|) (L15), BCa and
Holm (G5); the decision recorded in `DECISIONS.md` as D-ART5 with the PI's
word.

---

## Progress — 2026-09-08 12:42 CEST

**Status:** IN-PROGRESS.

### The join is exact; two provenance defects were found before it

`scripts/tkde/verify_rq1_join.py` (new) checks that the three experiments
measured the same seeded units before any paired statistic is trusted. On the
cluster, restricted to the Isal campaign's launch tag:

| table | key | addressing | addressing_rank | addressing_cpp | disagreement |
|---|---|---|---|---|---|
| M0/M3 | `(collection, seed, member_id)` | 7,369 | 7,369 | 7,369 | 0 |
| M1 | `(collection, seed, base_id, edit_kind, edit_idx)` | 138,499 | 139,492 | 139,492 | 993 units still missing in `addressing` |

The 993 are the last two `m1` shards of the recovery sweep (job 2247395), which
re-runs all 143 shards; `addressing_rank` and `addressing_cpp` are complete.

**Defect 1 — `RQ1_addressing/addressing` on the cluster holds two campaigns.**
Launch tag `c3fb21de` is job 2215137 (submitted 2026-09-05 23:17; rows written
09-06 13:50 → 09-07 04:08, `git_sha 554dbe09`), the fact-rank campaign — the
run frozen on the drive as `results/IEEETKDE/RQ1_addressing/addressing`. Tag
`47c8a42c` is job 2247394 + its sweep 2247395 (submitted 09-07 10:05), the Isal
campaign, which re-measures every unit and is the only launch carrying the
instruction-granularity columns `d_instr`, `n_instr` and `aut_bucket` — the
paper's headline granularity. Both wrote the fact and certificate arms, so
concatenating the directory yields **904,442 duplicated `(unit, arm)` rows out
of 2,506,837**: those arms counted twice on a mix of two schemas while the Isal
arms are counted once. Nothing in the analyzer, the merge tool or `io.py`
deduplicated. Fixed at `314b4a3`: `--only-tags`, `--list-tags` and a duplicate
audit that refuses the merge (`MergeIntegrityError`) and records the census in
`merge_manifest.json`. The wave logs are silent on the tag collision.

**Defect 2 — `fact_rank_roles` would have reached the table.** It fails M0 on
wd50k66 (247 false splits, 2,104 invariance violations) and T-KBf requires it
off every table; `--drop-arms` (`f4cf4e6`) removes it at merge time while the
source experiments keep the census that condemns it.

The whole pipeline is one script, `scripts/tkde/build_rq1_isal_table.sh`
(`8d5029b`): list tags → gate on the join → merge one source per arm → analyze.
It runs on the Picasso login node; no heavy local compute (handoff §2.2).

### Deviation from the pre-registration to note

`wstar_600` is named as an arm in `ISAL_VARIANT_DESIGN.md` §3 but is absent
from `experiments/tkde/configs/rq1.yaml`; there is no 600 s re-run of the 60 s
censored tail in this campaign. The wave logs are silent on it. The `w*_c` row
is `isalhg_levenshtein` at the 60 s budget, with its censoring reported in M3.

---

## The per-arm merge source is load-bearing — a defect avoided (2026-09-08)

`--prefer wstar_orbit=addressing_cpp` is not bookkeeping. The same arm, over
the same 7,369 members at the same 60 s budget, reads:

| source experiment | engine | `wstar_orbit` censored |
|---|---|---|
| `addressing` (`configs/rq1.yaml`) | the **Python** orbit engine, guarded to small members | **406** |
| `addressing_cpp` (`configs/rq1_cpp.yaml`) | the **C++** orbit engine | **77** |

Had the merge taken the arm from the first source that carries it, the R2
headline would have been 406 rather than 77 — the paper understating its own
result more than fivefold — and it would have violated the author's rule that
every arm in a final table runs on the C++ engine. This is exactly the case
`configs/rq1_cpp.yaml` was written for, and it is why the merge pins the source
per arm and records the assignment in `merge_manifest.json` rather than
resolving it by first-come.

## Censoring at a wall-clock budget is not exactly reproducible

Reading the same members, same tag, same budget, at two times while the
recovery sweep re-ran shards: the unpruned engine's censoring moved from
**357 to 354** of 7,369. Nothing is wrong — the budget is wall clock, so a
member whose true cost sits near it is decided by node load. Two consequences.

**A censored member never changes a value, only its presence.** Identical seeds
give identical words, so censoring decides which units enter a table, never
what a unit says.

**The near-boundary mass says which counts can drift.** Completed members by
time-to-budget:

| arm | completed | ≥ 30 s | ≥ 45 s | ≥ 55 s | censored |
|---|---|---|---|---|---|
| `wstar_orbit` (C++) | 7,292 | 32 | 7 | 6 | 77 |
| `wstar_rank` | 7,316 | **0** | 0 | 0 | 53 |
| `isal_ow_struct` | 7,369 | **0** | 0 | 0 | **0** |
| `w*_c` unpruned | 7,015 | 67 | 20 | 6 | 354 |

The arm that drifted is the one with twice the near-boundary mass. `wstar_rank`
is bimodal — not one member within 30 s of the budget, yet 53 censored — so its
count cannot drift; the ordered walk has nothing to drift. Whether the pruned
engine's 77 are far *above* the budget is the question the 600 s re-run
answers, and it is deferred into the RQ7 envelope sweep.

### Pre-stated expectation for the 600 s re-run (written before it is run)

Recorded now so the RQ7 envelope sweep can confirm or refute it rather than
rationalise whatever it finds.

The `wstar_rank` cost distribution is **bimodal at the 60 s budget**: zero
completions in [30, 60) s with 53 censored. That is strong evidence of a gap,
but the censored side is unobserved — a censored member records the budget, not
its cost — so the gap is inferred, not measured.

The near-boundary mass therefore predicts different outcomes for the two
engines at 600 s:

- **`wstar_orbit`** has 32 completions in [30, 60) and 6 in [55, 60). A
  population that dense just below the budget should continue above it, so a
  material fraction of its 77 is expected to finish by 600 s.
- **`wstar_rank`** has none. If the gap is real, most of its 53 should still be
  censored at 600 s — they are arity-10 displacement enumerations, exponential
  in the arity, not slow instances of an otherwise-feasible search.

If instead most of the 53 complete at 600 s, the bimodality is an artefact of
the budget rather than of the mechanism, and the claim that the residual tail
is displacement rather than a slow tail of the same search would need
rewriting. That is the refutable form.

Run it inside the RQ7 sweep (the only place it changes a figure), never as a
row: under the adopted budget rule the published row is 60 s.

## Correction to the pre-registration's reading: H-M2 was not falsified (2026-09-08)

Recorded against `ISAL_VARIANT_DESIGN.md` §9.

The first reading of the final tree reported that no `ow_*` arm reaches
`w*_c`'s pre-registered monotonicity targets (0.961 NDC natural / 0.553 WD50K
ladder) and marked **H-M2 falsified for the ordered walk**. That verdict is an
**artefact of scoring arms on different pair sets**: the analyzer's M2 table
scores each arm on its own uncensored pairs, so the search-based engines were
measured on 96 / 351 / 4,727 pairs and the ordered walk on 128 / 400 / 5,000 —
and the pairs the search censors are the hard ones, whose absence inflates its
ρ.

Restricted to the intersection of the published arms (5,428 pairs), the
ordering reverses on both NDC series:

| series / regime | n | `wstar_orbit` | `wstar_rank` | `isal_ow_struct` | `isal_ow_rank` | `nauty_cert_rows` | `nauty_cert` |
|---|---|---|---|---|---|---|---|
| NDC natural, pendant | 372 | 0.4322 | 0.3984 | **0.5564** | 0.4577 | 0.2752 | 0.1836 |
| NDC natural, interior | 105 | 0.9485 | 0.9526 | 0.9501 | **0.9665** | 0.9354 | 0.9338 |
| WD50K ladder | 4,951 | **0.5372** | 0.5290 | 0.4726 | 0.5046 | 0.4936 | 0.6774 |

So on the natural NDC series the **order-only** program is the most monotone
Isal program; the search-based engine wins only the constant-preserving WD50K
ladder. H-M2 stands for the ordered walk on two of three series.

This does not reopen the representation decision — locality is the
pre-registered primary axis and the search leads it in every regime bar one —
but it changes what the RQ1 reading must say: **the search buys insertion
locality and pays for it in monotonicity on natural data and in cost.** The
four-cell ablation is sharper for it: order alone gives monotonicity and cost,
the search adds locality, the oracle adds nothing but time.

**Methodological rule this establishes:** no cross-arm comparison in RQ1 is
sound on the analyzer's per-arm sets. Every published comparison restricts to
the intersection over the published arms, and the table header carries that n
and the fact that it is the Isal engine's completed set at 60 s.

## Intervals: the per-corpus split reverses two headline comparisons (2026-09-08)

`scripts/tkde/rq1_statistics.py` puts cluster-bootstrap intervals and
Holm-corrected paired tests on every RQ1 table, restricted to the intersection
of the units all published arms completed. Clusters are entities, not members:
ndc's 1,381 members are 171 drug classes, its 528 M2 pairs are 61 entities, and
the WD50K ladders are 1,000 clusters of exactly 5 rungs — all asserted, raising
rather than warning.

**The pooled figures hide corpus disagreement.** Within ≤ 2 per corpus, on the
restricted set:

| cell | corpus | `wstar_orbit` | `isal_ow_struct` | `nauty_cert_rows` |
|---|---|---|---|---|
| pendant delete_fact | ndc | 0.5758 | **0.5940** | 0.0000 |
| | synthetic | **0.0901** | 0.0414 | 0.0000 |
| | wd50k66 | **0.8449** | 0.7938 | 0.0000 |
| pendant remove_constant | ndc | 0.8595 | **0.8767** | 0.0000 |
| | wd50k66 | 0.8137 | **0.8306** | 0.0000 |
| pendant insert_fact_new_constant | ndc / syn / wd50k | **0.117 / 0.068 / 0.334** | 0.042 / 0.020 / 0.152 | 0.0000 |

Three consequences for what may be claimed.

1. The pooled pendant-deletion figure (0.7705) **is WD50K's 0.8449**: WD50K
   supplies 12,293 of 15,604 rows and 3,946 of 4,535 clusters. NDC gives 0.576
   and synthetic 0.090. The number must be quoted with its corpus.
2. On pendant **narrowing** the ordered walk beats the orbit engine on *both
   real corpora*, and on pendant **deletion** it beats it on ndc. So "the orbit
   engine leads every regime except pendant narrowing" is false per corpus.
3. `insert_fact_new_constant` is the cell that survives unconditionally — the
   orbit engine leads the ordered walk on all three corpora and the certificate
   is 0.0000 everywhere. **It, not pendant deletion, is the cell that carries
   the locality argument.**

The certificate is exactly 0.0000 on all three corpora for pendant deletion,
pendant narrowing, constant-bringing insertion, interior deletion and interior
insertion; on `add_constant` and interior `remove_constant` it *leads* on ndc
and synthetic. The clean "certificate never lands within two" statement is
therefore true of the five fact-edit kinds, not of all seven.

**Paired tests separate the arms.** On pendant deletion (4,535 clusters) every
arm differs from `wstar_orbit` after Holm, `isal_ow_struct` included
(+0.0452 [0.0356, 0.0539], rank-biserial 0.302). Note the marginal intervals
overlap while the paired difference excludes zero — the paired test is the
correct one, and the tables print the difference column for that reason.

**Estimand note.** The printed interval bounds the statistic the table prints:
the pooled fraction and the pooled median, by cluster bootstrap. The first run
exposed why this matters — bounding the median of *per-cluster* medians made
BCa degenerate on all 48 cells, because per-cluster medians of a small-integer
response are heavily tied. The per-cluster convention is retained beside it for
continuity with `tables.md`, and an unweighted mean-of-cluster-fractions column
is the sensitivity check.

### The interval and the p-value answer different questions — say so in the caption

Several rows show a paired-difference interval that excludes zero beside a Holm
p above 0.05. On NDC pendant monotonicity, `nauty_cert_rows` is
Δρ = +0.157 [0.011, 0.327] with p_Holm = 0.168, and `wstar_rank` is
+0.034 [0.0007, 0.066] with p_Holm = 0.168.

That is not a contradiction and must not be left to look like one: **the
interval is per-comparison at 95 %, the p-value is corrected across the six
arms of its family.** One clause in the caption fixes it. The alternative —
printing simultaneous intervals — would be defensible but changes every
interval in the paper for the sake of a handful of rows.

### M2, what is and is not established (60 s budget, published-arm intersection)

| series | clusters | `w*_c` (orbit) vs row certificate | verdict |
|---|---|---|---|
| NDC natural, pendant | 50 | Δρ = +0.157 [0.011, 0.327] | p_Holm 0.168 — **within noise** |
| NDC natural, interior | 34 | Δρ = +0.013 [·] | p_Holm 0.156 — **within noise** |
| WD50K ladder | 997 | Δρ = **+0.044 [0.025, 0.063]** | p_Holm 0.006 — **established** |

So the Isal word leads the row certificate in point estimate on all three
series and significantly on one. The earlier phrasing "leads monotonicity on
every series measured" overstated it and is withdrawn.

Two results that do clear on the small NDC series: the **ordered walk beats the
search** on pendant pairs (Δρ = −0.124 [−0.228, −0.037], p_Holm 0.025) and the
search beats the **byte** certificate (+0.249, p_Holm 0.024). On the ladder the
byte certificate beats the search (−0.140 [−0.159, −0.120], p_Holm 0.006) by
responding about five times larger per edit. `wstar_rank` is indistinguishable
from `wstar_orbit` on every series — the tie key costs no monotonicity.

## Per-corpus paired tests: the reversal is a tie, not a reversal (2026-09-08)

Running the whole harness per corpus (`--collections`) puts the paired tests
and their Holm families inside a corpus rather than inside a mixture. On
pendant `delete_fact`:

| corpus | clusters | `wstar_orbit` | `isal_ow_struct` | Δ vs orbit | p Holm |
|---|---|---|---|---|---|
| ndc_classes | 161 | 0.5758 [0.5152, 0.6248] | 0.5940 [0.5292, 0.6483] | **−0.0003 [−0.0501, 0.0539]** | **1 — no** |
| wd50k66 | 3,946 | 0.8449 [0.8347, 0.8538] | 0.7938 [0.7825, 0.8036] | **+0.0467 [0.0369, 0.0576]** | **1.7e-18 — yes** |

So the apparent NDC reversal read off point estimates **is not a reversal, it
is a tie**: on 161 drug classes the search and the order-only program are
indistinguishable, and on WD50K the search leads. That is the sentence to
write, and it is a better one than either "leads" or "trails".

The certificate is 0.0000 on both corpora with the whole gap significant
(+0.5789 on ndc, +0.8144 on wd50k), so the claim that carries the paper is
unaffected by any of this.

### A second reading hazard: the effect column and the test are different functionals

On WD50K pendant deletion the **median** row for `isal_ow_struct` reads
difference **+0.0047 [−0.0922, 0.1119]** — an interval containing zero —
beside **p_Holm = 3.2e-10, reject**. Not a bug: the difference column is a
difference of per-entity *means*, while the p is a Wilcoxon signed-rank on the
paired differences, which tests the signs. With a skewed paired distribution
the two legitimately disagree — equal means, yet the ordered walk is the larger
of the pair on most entities.

On ndc the same pair of statistics disagrees in the other direction: median
difference −1.1056 [−1.7548, −0.6978], p_Holm 7.1e-05, while the within-≤2
fractions are tied. The ordered walk has the same mass under two instructions
and a heavier tail.

**Fix before publication: report the rank-biserial as the effect for the median
rows and drop the difference-of-means column**, so the effect and the test are
the same functional. Otherwise the caption must explain it, as it must for the
per-comparison interval beside the Holm p.

### Note

`synthetic_rq1` has no M2 rows at all (`m2_natural: [ndc_classes]`,
`m2_ladders: [wd50k66]`), so a per-corpus M2 run on it raises rather than emit
an empty table. Correct behaviour; run it with `--measures m1 m4`.

## Closing state — all RQ1 jobs terminal (2026-09-08)

Job **2247395 cancelled by the author's instruction** after the data was
complete and verified: 31 tasks completed, 17 cancelled. Every shard of the
Isal campaign tag survives (`m0items` 12, `m1` 118, `m2` 6, `m3` 12, `m4` 7 —
143 units), the join is exact, and the deliverable was already frozen. The
remaining tasks were re-runs of shards on disk and could only make the cluster
tree disagree with it.

Final job states: 2247394 38 completed / 9 OOM / 1 timeout · 2247395 31
completed / 17 cancelled · 2248782 8/8 · 2248907 16/16 · 2248908 16/16.

### The drift, one last time — and why it does not touch the published arms

Immediately after the cancellation the cluster tree reads the unpruned engine at
**353** censored. Across four reads of the same members, same code, same 60 s
budget, it has given **357, 354, 356, 353**. The frozen deliverable records 356.

In the same four reads the published arms never moved: `wstar_orbit` **77**,
`wstar_rank` **53**, `isal_ow_struct` **0**.

That is the near-boundary-mass model confirmed a fourth time — the only arm that
drifts is the one with members near the budget (67 completions within 30 s of
it, against the orbit engine's 32 and the other two arms' none). It is also the
reason the deliverable is frozen on the drive rather than regenerated on demand:
under a wall-clock budget the censoring census is a property of a run, and only
of the arm whose cost distribution touches the boundary.

**Nothing in the paper depends on the drifting number.** Under A′ the unpruned
engine appears only as the M3 no-nauty cost cell; every published row is
`wstar_orbit`'s, whose count is stable.

## D-ART5 recorded (2026-09-09) — the three "decisions" were already ruled

Put to the author as three open decisions; on review of the record, none was.
D-ART5 is now in `DECISIONS.md` as a **record of application**, not a new
ruling. The chain, in one line each:

- **Representation.** D-TA2 names stabiliser-orbit pruning as the *one*
  sanctioned speedup; the D-ART4 addendum says supersession is "required only
  if the canonical *value* changes"; the value is unchanged on 7,013/7,013
  words and 130,788/130,788 distances. Design §8(1) is not triggered. Only a
  departure (to `w*_ρ` or `w°`) would have been PI-level.
- **Budget.** 60 s is `pointer_budget_s` in all three configs, and design §3
  defines `wstar_600` as a re-run *of the censored tail* — characterisation by
  definition, never a row.
- **Fact arms.** D-ART4 (1) itself instructs the prose to own the consequence,
  and `prose.md` §2.3 already concedes it. Only the *quantification* is new,
  and that is the single item left for the author to strike if they wish.

**Acceptance.** Every measurement criterion is met (M0 0/0/0 on every Isal arm;
absolute instructions first; the ≤2 fraction; censoring per (arm, m, |Aut|);
BCa and Holm). The last clause — "with the PI's word" — waits on the author's
acknowledgement of the record, not on a pending judgement. T-KBe stays
IN-PROGRESS until then.

**Error of the orchestrator, recorded.** Escalating settled questions is not a
free action: it spends the author's attention and it invites a re-ruling on
matters already closed. The check that was missing is cheap — before putting a
question to the author, grep the decision record for the object it concerns and
read the *reasoning of record*, not only the ruling line. D-TA2's sanctioned-
speedup clause and D-ART4's addendum (i) each answer decision 1 outright.
