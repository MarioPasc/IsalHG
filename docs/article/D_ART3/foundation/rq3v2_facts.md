# RQ3 v2 — the golden record — the verified fact base

Every number the prose may quote for RQ3 v2, with the run that produced it. Same
rule as `rq6_generation_facts.md` and `rq7_envelope_facts.md`: **a number with no
entry here is struck, not kept**, whichever way it points, and this is a
precondition on the T-KBg fold rather than a cleanup inside it.

Design: `../experiments/HEADLINE_DESIGN_2026-09-13.md` §0–§3. Gates and their
reasoning: `../experiments/RQ3V2_PILOT.md`. Ledger:
`../../DEVELOPMENT/T-KB/IN-PROGRESS/T-KBz.md`.

## Provenance

| | |
|---|---|
| results root (Picasso) | `~/results/IEEETKDE_ow/RQ3v2_golden_record/anonymous_consensus/` (490 row files + `config.json`, `manifest.json`, `summary.json`) |
| results root (drive) | `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE_ow/RQ3v2_golden_record/anonymous_consensus/` — harvested 2026-10-04 by `rsync -a` (additive), 493 files, 131.3 MB. The older `IEEETKDE_ow/RQ3v2/` holds the pilots and smokes only. |
| analysis (drive) | `IEEETKDE_ow/RQ3v2_golden_record/anonymous_consensus/_analysis_ef0c58b4+1efdcf54/RQ3v2_golden_record/anonymous_consensus/{summary,stats}.json`, `tables.md` — **every number in §6–§11 is read from these three files** unless a row says otherwise |
| analysis command | `python -m experiments.tkde.analyze_rq3v2 --root <drive>/IEEETKDE_ow --out <the analysis dir above> --supersede-tag ef0c58b4 --expected-seeds 27` (config `experiments/tkde/configs/rq3v2.yaml` supplies the design grid), at the harvest branch's analyzer (coverage gate, §6) |
| runner | `experiments/tkde/rq3v2.py` |
| analyzer | `experiments/tkde/analyze_rq3v2.py` |
| config | `experiments/tkde/configs/rq3v2.yaml` |
| SLURM | `slurm/tkde/rq3v2_{launcher,worker}.sh`; deploy `slurm/tkde/rq3v2_sync.sh` |
| corpora | the frozen `ndc_classes` (1,381) and `wd50k66` (3,988) |
| program | `isal_ow_struct` (`w°`), 60 s budget, under the forked-child model of `experiments/tkde/budget.py` |
| job ids | **2308421** — first pass, 122-task array, 8 h wall, submitted 2026-09-13 13:57 CEST: 85 COMPLETED / 37 TIMEOUT, 358 units. **2311518** — light recovery pass, 40 units, 40/40 COMPLETED. **2311519** — the six structurally empty `ndc_classes` star cells, 79 units, COMPLETED. **2311520** — heavy recovery pass, 189 tasks (7 cells × 27 seeds, one unit each), 6 h wall, 64 G: 11 COMPLETED / 178 TIMEOUT, 13 units written. Smokes: 2308373, 2308392. 2308372 and 2308420 were `--test-only` probes, not jobs. States from `sacct`, 2026-10-04. |
| run tags | `ef0c58b4` — 60 s exact-HGED judge (2308421, 2311518, 2311519): 477 row files. `1efdcf54` — 8 s judge (2311520): 13 row files. Tag in each filename equals the tag in its rows (490/490). |
| git | rows of 2308421 carry `08f53a1`; rows of the three recovery arrays carry `38b1b14`, the deploy stamp of a tree that also held the then-uncommitted diff committed 29 s later as `033b9fd` (`Deployed: … at=2026-09-14T09:40:53`; commit 09:41:22). `033b9fd` changes `rq3v2.py` only operationally (`--only-cells`, `--resume`, `--hged-timeout-s`, the `judge_timeout_s` column), so the `ef0c58b4` rows of both SHAs measure one configuration. |

**Row files are tag-scoped** (`rows_golden__<run_tag>-<unit>.csv`). A number read
from a file whose tag is not the one in the manifest belongs to another
configuration and is not this campaign's.

---

## 1. Gate G0 — the star census (FINAL)

Measured 2026-09-13 by `rq3v2.star_census`; reproduce with
`python -m experiments.tkde.rq3v2 --config … --census`.

| corpus | scope | N | stars | frac star | non-stars |
|---|---|---|---|---|---|
| `ndc_classes` | whole corpus | 1,381 | 42 | 0.030 | 1,339 |
| `ndc_classes` | source window | 212 | **0** | 0.000 | 212 |
| `wd50k66` | whole corpus | 3,988 | 2,128 | 0.534 | 1,860 |
| `wd50k66` | source window | 1,871 | 1,011 | 0.540 | 860 |

Source window: `4 ≤ n ≤ 12`, `4 ≤ m ≤ 12`, max arity ≤ 6, constant identities
present. Non-star medians: `ndc_classes` 2 shared constants / 4 shared facts;
`wd50k66` 2 / 3.

**Quotable consequences.** (a) The `ndc_classes` star stratum is empty inside the
source window, so H3.4 is measured on `wd50k66` alone and the NDC star cells
carry one `cell_empty` row each. (b) `wd50k66` is 53.4 % stars corpus-wide, so
the design's "most WD50K descriptions are stars" is about half, not most.

---

## 2. Gate G3.2 — the corrected v1 run (FINAL, harvested)

Source `results/IEEETKDE_isal_consensus/RQ3_representative/corpus_a/rows_variants.csv`,
git `4eebccc`, 62,398 rows, 27 seeds, censoring 0.000 on all eleven arms.

| quantity | value |
|---|---|
| coverage consensus, exact recovery, del / ins / mix | 0.517 / 0.998 / 0.863 |
| `majority_merge_id` (oracle), del / ins / mix | 0.680 / 0.999 / 0.913 |
| every medoid, all kinds | 0.000 |
| consensus, deletion regime, (N5,t1)/(N5,t2)/(N9,t1)/(N9,t2) | 0.826 / 0.195 / 1.000 / 0.525 |
| oracle, same cells | 1.000 / 0.252 / 1.000 / 0.950 |
| mean fact distance, deletions, consensus t=1 / t=2 | 0.19 / 1.32 |
| mean fact distance, deletions, every medoid t=1 / t=2 | 1.00 / 2.00 (the floor) |
| winner origin `transfer` (an object no member wrote) | 0.933 |

v1 before the objective correction measured 0.13–0.28 in the deletion regime.

---

## 3. Gate G3.1 — reach coverage (FINAL)

### 3.1 Fact reach — 200 members/corpus, 1,200 units, 0 censored

`reach_F(K, K ⊕ e) ≤ 1` coverage **1.000** on every corpus × stratum × edit kind.
Availability: `wd50k66` star × `del_interior` = 0.00 (a star has no interior
fact, by definition); `wd50k66` non-star × `del_interior` = 0.54; all others
0.95–1.00.

### 3.2 Canonical-word distance — the `w°` / `w*_c` locality contrast

`w*_c` censoring 0 / 1,200 at a 20 s budget. Coverage at r = 2, and the median
token distance:

| cell | `w°` r2 / median | `w*_c` r2 / median |
|---|---|---|
| ndc non-star `del_pendant` | 0.589 / 1 | 0.568 / 1 |
| ndc non-star `del_interior` | 0.101 / 4 | 0.384 / 3 |
| ndc non-star `ins_existing` | 0.020 / 14 | 0.010 / 8 |
| ndc non-star `ins_new_constant` | 0.060 / 10 | 0.070 / 7 |
| wd50k non-star `del_pendant` | 0.576 / 2 | 0.707 / 1 |
| wd50k non-star `del_interior` | 0.093 / 9 | 0.056 / 6 |
| wd50k non-star `ins_existing` | 0.030 / 9 | 0.020 / 6 |
| wd50k non-star `ins_new_constant` | 0.030 / 11 | 0.190 / 5 |
| wd50k star `del_pendant` | 1.000 / 1 | 1.000 / 1 |
| wd50k star `ins_existing` | 0.020 / 8 | 0.040 / 5 |
| wd50k star `ins_new_constant` | 0.240 / 4 | 0.370 / 3 |

**Quotable.** A single fact deletion moves `w°` by a median of 1 token; a single
fact insertion moves it by 5 to 14. `w°` is materially less local than `w*_c` on
`ins_new_constant` and on ndc `del_interior`, consistent with `SESSION_LOG.md`
§6.5. This asymmetry is the mechanism behind the objective choice (§5) and
behind H3.6.

### 3.3 Ball reachability — the operative gate

Is the source's class in the decoded image of `⋃ᵢ B_r(w°(Kᵢ))`? Ten families per
cell; the ball is deduplicated on the decoded structure, never on a multiset
signature.

| cell | ball | source in ball | classes (median) | s median / max |
|---|---|---|---|---|
| wd50k non-star N5 t1 mixed | indel r=1 | 1.000 | 300 | 0.06 / 0.12 |
| wd50k non-star N5 t1 mixed | indel r=2 | 1.000 | 12,511 | 7.7 / 25.8 |
| wd50k non-star N5 t2 deletions | indel r=2 | 1.000 | 261 | 0.23 / 1.05 |
| wd50k star N5 t1 mixed | indel r=2 | 1.000 | 5,592 | 2.4 / 16.0 |
| ndc non-star N5 t1 mixed | indel r=2 | 1.000 | 19,108 | 13.7 / 39.3 |
| ndc non-star N5 t1 mixed | restricted a≤3/d≤2 | 1.000 | 2,983 | 1.6 / 3.0 |
| ndc non-star N5 t2 deletions | indel r=2 | **0.375** | 1,052 | 0.33 / 0.80 |

**Quotable.** The gate passes at r = 2 on the mixed model at t = 1 (1.000, both
corpora, both strata). The deletion-heavy t = 2 cell on ndc is the measured
boundary of the r = 2 envelope and is reported as such, not patched by a larger
radius. The restricted ball reaches the same coverage at one ninth the cost.

### 3.4 Ambient decodability (Prop. C.4, measured)

426,433 ball words decoded during the G3.1 probes; **426,433** decoded to a
connected knowledge base. No exception, no disconnected result. This is the
ambient-space measurement lesson L19 requires, not a count over objects that
were already knowledge bases.

---

## 4. Corpus and design constants

| | |
|---|---|
| corpora | `ndc_classes` (1,381), `wd50k66` (3,988) — the built census, never the supplement's |
| source window | n 4–12, m 4–12, max arity ≤ 6, identities present |
| strata | star / non-star (G0); ndc has only non-star inside the window |
| N | 5, 9, 15 |
| t | 1, 2 |
| noise kinds | `del_pendant`, `del_interior`, `ins_existing`, `ins_new_constant`, drawn uniformly per edit |
| sources per stratum per seed | 50 |
| seeds | 27, from `config.seeds(32, 27)` |
| radius | 2, indel ball (restricted a≤3/d≤2 is the declared fallback) |
| harness | 95 % BCa CIs, Holm-corrected paired Wilcoxon over seeds, rank-biserial |
| exact-HGED ceiling | n ≤ 10; above it, and on timeout, the row is judged by `bipartite_ged_path` and says so in `fact_dist_judge` |

---

## 5. The objective (pre-registered, 2026-09-13)

Primary: the **generalized median in the indel word metric** — minimise
`Σᵢ d(w°(M), w°(Kᵢ))` with `d(w₁,w₂) = |w₁| + |w₂| − 2|LCS(w₁,w₂)|`, ties by
coverage, then by the augmented-fingerprint order. Grounds, all a priori: it is
the classical consensus objective in string spaces; the medoid is the same
objective restricted to the members, so the consensus cost is at most the
medoid's by construction; Prop 3's bound `LB = Σ_{i<j} d(Kᵢ,Kⱼ)/(N−1)`
lower-bounds the optimum over every point, giving a **certified ratio**
`cost / LB` a coverage objective cannot have; and the indel metric is the metric
of the ball the arm enumerates, so objective and candidate set live in one
geometry.

**Why not Levenshtein (amendment, 2026-09-13, pre-registered).** A substitution
has no fact-level counterpart at unit cost. Measured on a star whose members each
drop one fact: under Levenshtein the source costs 4 and two of its sub-records
also cost 4 — a tie the objective cannot break, resolved by a tie break that
prefers the shorter word and so the smaller record. Under indel the source costs
`N` and every sub-record `2(N−1)`, strict for `N ≥ 3`.

Ablation arms, all on every collection: `consensus_ow_lev` (metric only),
`consensus_ow_coverage` (first criterion only), `consensus_fact` (fact space,
H3.5).

**Certified ratios are comparable only within a metric.** `medoid:isal_ow_indel`
is the members' medoid under the same indel metric and is the row
`consensus_ow`'s ratio is read against; `medoid:isal_ow_struct` is the
Levenshtein one, for the cross-representation table.

Measured on two smoke collections only — worth nothing except as a sanity check,
and recorded here so it is not mistaken for a result: on the first collection
`consensus_ow` under indel recovers the source (`fact_dist` 0, `n_ties` 0, ratio
1.091 against the indel medoid's 1.152), while `consensus_ow_lev` on the same
collection returns a non-source at `fact_dist` 3 with `n_ties` 2.

---

## 6. Coverage — which cells may be tested (FINAL, harvested 2026-10-04)

The rule (`SESSION_LOG.md` §10, `RQ3V2_PILOT.md` "Do not run the hypothesis tests
on partial coverage"): **a hypothesis is tested only on cells that carry all 27
seeds under one run tag.** A partial cell's seeds are the ones that finished
inside the wall, not the sample the harness fixes, so its numbers are
descriptive and censored and enter no test and no pooled figure. After
`--supersede-tag ef0c58b4` (12,000 superseded rows in the two cells the heavy
tag also covers), the analyzer's gate reads the 24 design cells as:

| corpus | stratum | N | t | tag | seeds | status |
|---|---|---|---|---|---|---|
| ndc_classes | non-star | 5 | 1 | `ef0c58b4` | 27 | complete |
| ndc_classes | non-star | 5 | 2 | `ef0c58b4` | 27 | complete |
| ndc_classes | non-star | 9 | 1 | `ef0c58b4` | 27 | complete |
| ndc_classes | non-star | 9 | 2 | `1efdcf54` | 11 | **partial** (+7 superseded `ef0c58b4`; union 16) |
| ndc_classes | non-star | 15 | 1 | `1efdcf54` | 2 | **partial** (+5 superseded `ef0c58b4`; union 7) |
| ndc_classes | non-star | 15 | 2 | — | 0 | **absent** |
| ndc_classes | star | 5, 9, 15 | 1, 2 | `ef0c58b4` | 27 each | empty by construction (G0) — six cells |
| wd50k66 | non-star | 5 | 1 | `ef0c58b4` | 27 | complete |
| wd50k66 | non-star | 5 | 2 | `ef0c58b4` | 27 | complete |
| wd50k66 | non-star | 9 | 1 | `ef0c58b4` | 27 | complete |
| wd50k66 | non-star | 9 | 2 | `ef0c58b4` | 3 | **partial** |
| wd50k66 | non-star | 15 | 1 | — | 0 | **absent** |
| wd50k66 | non-star | 15 | 2 | — | 0 | **absent** |
| wd50k66 | star | 5 | 1 | `ef0c58b4` | 27 | complete |
| wd50k66 | star | 5 | 2 | `ef0c58b4` | 27 | complete |
| wd50k66 | star | 9 | 1 | `ef0c58b4` | 27 | complete |
| wd50k66 | star | 9 | 2 | `ef0c58b4` | 27 | complete |
| wd50k66 | star | 15 | 1 | `ef0c58b4` | 27 | complete |
| wd50k66 | star | 15 | 2 | `ef0c58b4` | 3 | **partial** |

**11 complete cells, 4 partial, 3 absent, 6 empty.** All seven heavy cells of the
recovery ruling are incomplete; none of them is tested. Every complete cell holds
1,350 collections (27 seeds × 50 sources), each scored by 20 methods.

*Two checks on the merge.* (i) The primary metric does not depend on the judge:
on the two seeds both tags measured in `ndc_classes` non-star `N = 9, t = 2`
(320013, 320025), exact recovery is identical on all 1,897 paired rows; fact
distance differs on 2 (`pattern_vote`, exact → bipartite under 8 s). The union
of the two tags is still partial (16 of 27), so it is not tested either. (ii) One
finished unit was lost: `ndc_classes non_star_N9_t2 s320008` (task 9 of 2311520)
logged `unit done` 17 s after the SLURM time-limit cancel, so its copy-back never
ran (`~/execs/tkde/logs/tkde-rq3v2-heavy_2311520_9.{out,err}`).

**What the paper can claim, by scope.** The relational (non-star) headline is
measured at `N ∈ {5, 9}` for `t = 1` and at `N = 5` for `t = 2`, on both corpora;
the star control on `wd50k66` at `N ∈ {5, 9}` for `t ∈ {1, 2}` and at `N = 15` for
`t = 1`. **It cannot claim anything at `N = 15` on the non-star stratum (either
corpus), at `N = 9, t = 2` on the non-star stratum (either corpus), or at
`N = 15, t = 2` on stars.** Every statement below is conditional on the indel
word ball at `r = 2` around the members' `w°` words, and on `ndc_classes` at
`t = 2` it sits on the envelope boundary G3.1 measured (source reachable in the
ball for 0.375 of deletion-heavy collections, §3.3).

---

## 7. Hypotheses and their verdicts (complete cells only)

Seed-level BCa intervals (10,000 resamples), paired one-sided (H3.1, H3.2) or
two-sided (H3.3–H3.5, descriptive beside a margin rule) Wilcoxon over the 27
seeds, Holm within each family, rank-biserial `r_rb`. Source:
`stats.json` of the analysis dir in Provenance.

| # | Statement | Verdict |
|---|---|---|
| H3.1 | non-star, t ≤ 2: `consensus_ow` recovery > the three anonymous merges, Holm-significant, every N | **supported on the tested cells** (`N = 5` at `t ∈ {1,2}`, `N = 9` at `t = 1`, both corpora); **not testable** at `N = 15` (both corpora) and at `N = 9, t = 2`. "For every N" is therefore **not established**. |
| H3.2 | `consensus_ow` fact distance < every medoid's | **supported** against the 11 medoids that were scored; `medoid:hypercot` **not scored** (every row censored: pinned environment absent on Picasso) |
| H3.3 | non-star: `consensus_ow` ≥ `majority_merge_id` − 0.05 | **not supported** (gap −0.537) |
| H3.4 | stars: `pattern_vote` ties `consensus_ow` (\|Δ\| < 0.05) | **not supported** — no tie: `consensus_ow` leads by 0.459. See the baseline caveat below. |
| H3.5 | `consensus_ow` ≥ `consensus_fact` − 0.05 at matched r, at lower cost | **not supported** on either clause (gap −0.551; `consensus_fact` is also 1–2 orders of magnitude cheaper) |
| H3.6 | recovery rises with N; the N = 5 shortfall is a sub-record | **not supported as stated**: the monotonicity clause holds in 4 of 4 comparable series; the sub-record clause fails (sub-record share of `N = 5` misses 0.05–0.48, below half in all six series) |

**H3.1, per family** (seed-level recovery pooled over the tested `t` of that
`(corpus, N)`; diff = ours − baseline, BCa):

| corpus, N (t tested) | ours | `align_merge_ref` | `align_merge_iter` | `pattern_vote` | p_Holm (each) | r_rb |
|---|---|---|---|---|---|---|
| ndc_classes, 5 (1, 2) | 0.209 | 0.076, diff [0.116, 0.148] | 0.066, [0.127, 0.156] | 0.007, [0.188, 0.216] | 8.2 × 10⁻⁶ | 1.000 |
| ndc_classes, 9 (1) | 0.496 | 0.104, [0.370, 0.420] | 0.098, [0.374, 0.429] | 0.010, [0.463, 0.512] | 8.1 × 10⁻⁶ | 1.000 |
| wd50k66, 5 (1, 2) | 0.331 | 0.006, [0.312, 0.338] | 0.004, [0.314, 0.341] | 0.000, [0.318, 0.345] | 8.3 × 10⁻⁶ | 1.000 |
| wd50k66, 9 (1) | 0.732 | 0.004, [0.706, 0.748] | 0.004, [0.706, 0.749] | 0.001, [0.710, 0.750] | 8.0 × 10⁻⁶ | 1.000 |

The family pools `t = 1` and `t = 2` for `N = 5` as registered; the per-cell
split (§8) shows that the `t = 2` margin is thin on `ndc_classes` (0.031 against
0.023 / 0.016 / 0.007) and was not tested separately.

**H3.2** (fact distance pooled over the 11 complete cells): `consensus_ow` 4.899
against every scored medoid, all `p_Holm ≤ 5.6 × 10⁻⁶`, `r_rb = −1.000`:

| medoid | mean | diff (ours − medoid), BCa |
|---|---|---|
| `bipartite_ged_path` | 6.321 | [−1.480, −1.358] |
| `bipartite_ged_assign` | 6.353 | [−1.505, −1.403] |
| `degree_seq_l1` | 6.555 | [−1.707, −1.606] |
| `netlsd` | 6.561 | [−1.722, −1.607] |
| `size_l1` | 6.589 | [−1.739, −1.643] |
| `nauty_cert` | 6.628 | [−1.777, −1.676] |
| `nauty_cert_rows` | 6.836 | [−2.001, −1.872] |
| `isal_ow_struct` (Levenshtein) | 7.186 | [−2.340, −2.231] |
| `isal_ow_indel` | 7.433 | [−2.595, −2.473] |
| `hpd_jsd` | 7.485 | [−2.641, −2.536] |
| `wl_l1` | 8.204 | [−3.352, −3.249] |

The axis is exact HGED where the oracle answered and `bipartite_ged_path`
otherwise; the per-cell fallback rates are in §9 and must travel with this table.

**H3.3** (non-star complete cells): `consensus_ow` 0.385 [0.378, 0.391] against the
identity oracle `majority_merge_id` 0.921 [0.915, 0.927]; gap −0.537, paired diff
[−0.546, −0.527], p = 5.6 × 10⁻⁶, `r_rb = −1.000`. The anonymous word-space
consensus does not approach an oracle that has the identities.

**H3.4** (`wd50k66` star complete cells): `consensus_ow` 0.491 [0.479, 0.502]
against `pattern_vote` 0.032 [0.028, 0.036]; gap +0.459, paired diff
[0.448, 0.471], p = 5.6 × 10⁻⁶, `r_rb = 1.000`. Per cell (§8) the counting
baseline recovers 0.016–0.047 of star sources. **Caveat, not a result:** the
design's premise was that counting fact patterns recovers a star exactly, and
`pattern_vote`'s fact distance on stars is 9.7–10.8 (against 1.8–5.2 for the
consensus), so the baseline is failing for a reason its construction has not
been audited for. RQ8's star recommender needed two pre-registered repairs (A2,
A3) before it reached 0.624. **Until `pattern_vote` is audited, H3.4's outcome
must not be quoted as the consensus beating counting on stars**; it is reported
as "the registered control did not tie".

**H3.5** (all complete cells): `consensus_ow` 0.433 [0.427, 0.438] against the
fact-space ablation `consensus_fact` 0.984 [0.981, 0.986]; gap −0.551, paired
diff [−0.555, −0.546], p = 5.6 × 10⁻⁶, `r_rb = −1.000`. Cost goes the same way:
`consensus_fact` median 0.20–2.83 s per collection against `consensus_ow`
6.5–145 s (§10). `consensus_fact` reads the same anonymized members and returns
an object no member wrote in 0.994 of collections (`winner_origin = transfer`),
so it is an anonymous, representation-free consensus that nearly matches the
identity oracle. **Declared fallback, applied:** RQ3's language claim reduces to
the decoded output and the certificate; the cost half of the fallback's wording
does not survive either.

**H3.6** — read within each corpus × stratum × t series, because under partial
coverage the pooled figure per `N` compares different cells at different `N`
(the rule fixed before any per-`N` number was read; log §7). `consensus_ow` exact
recovery with seed-level BCa, and the share of misses that are a sub-record of
the source within three dropped facts:

| series | N = 5 | N = 9 | N = 15 | monotone | sub-record share of N = 5 misses |
|---|---|---|---|---|---|
| ndc non-star t1 | 0.386 [0.359, 0.410] | 0.496 [0.473, 0.522] | — | yes | 0.481 |
| ndc non-star t2 | 0.031 [0.021, 0.042] | — | — | n/a (one N) | 0.273 |
| wd non-star t1 | 0.552 [0.530, 0.573] | 0.732 [0.711, 0.752] | — | yes | 0.198 |
| wd non-star t2 | 0.111 [0.093, 0.131] | — | — | n/a (one N) | 0.237 |
| wd star t1 | 0.610 [0.585, 0.637] | 0.724 [0.693, 0.750] | 0.767 [0.744, 0.794] | yes | 0.053 |
| wd star t2 | 0.137 [0.119, 0.153] | 0.216 [0.196, 0.240] | — | yes | 0.129 |

Monotone in all four comparable series. The second clause has no registered
threshold, but the measured shares are below one half everywhere: most small-`N`
misses are **not** sub-records of the source, so the insertion-asymmetry
mechanism explains at most half of the shortfall. The analyzer's `held` flag
reads the monotonicity clause only and prints HELD; this fact base is the
verdict of record.

**Fallbacks, as declared, and what fires.** H3.1 held on every tested cell, so
neither H3.1 fallback fires — but its "every N" is unestablished (§6). H3.5
failed, so RQ3's language claim reduces to the decoded output and the
certificate (§9, §11). H3.3 is a stretch and has no fallback. Read together:
the consensus beats every anonymous merge and every medoid, and it is the only
arm that returns a decoded non-member with a certificate; it does **not** match
the identity oracle, and a representation-free fact-space consensus beats it by
0.55 at lower cost.

---

## 8. Exact recovery and fact distance per cell (descriptive)

Exact recovery (isomorphism to the source by certificate). Every medoid's
recovery is at most 0.003 in every cell (a member can be isomorphic to the source
when two edits cancel). Partial cells are **censored**: their seeds are the ones
that finished, n seeds given; they are not tested and not pooled.

| cell | `consensus_ow` | `_lev` | `_coverage` | `consensus_fact` | oracle | `align_ref` | `align_iter` | `pattern_vote` |
|---|---|---|---|---|---|---|---|---|
| ndc ns N5 t1 | 0.386 | 0.316 | 0.185 | 1.000 | 1.000 | 0.129 | 0.116 | 0.006 |
| ndc ns N5 t2 | 0.031 | 0.022 | 0.177 | 0.930 | 0.683 | 0.023 | 0.016 | 0.007 |
| ndc ns N9 t1 | 0.496 | 0.387 | 0.203 | 1.000 | 1.000 | 0.104 | 0.098 | 0.010 |
| wd ns N5 t1 | 0.552 | 0.413 | 0.342 | 0.997 | 1.000 | 0.010 | 0.005 | 0.001 |
| wd ns N5 t2 | 0.111 | 0.068 | 0.443 | 0.941 | 0.845 | 0.001 | 0.003 | 0.000 |
| wd ns N9 t1 | 0.732 | 0.531 | 0.335 | 1.000 | 1.000 | 0.004 | 0.004 | 0.001 |
| wd star N5 t1 | 0.610 | 0.338 | 0.797 | 0.996 | 1.000 | 0.039 | 0.036 | 0.041 |
| wd star N5 t2 | 0.137 | 0.047 | 0.904 | 0.961 | 0.899 | 0.019 | 0.023 | 0.016 |
| wd star N9 t1 | 0.724 | 0.310 | 0.807 | 1.000 | 1.000 | 0.028 | 0.030 | 0.047 |
| wd star N9 t2 | 0.216 | 0.027 | 0.989 | 0.996 | 0.983 | 0.019 | 0.024 | 0.010 |
| wd star N15 t1 | 0.767 | 0.167 | 0.754 | 1.000 | 1.000 | 0.027 | 0.029 | 0.044 |
| *censored:* ndc ns N9 t2 (11 seeds, 8 s judge) | 0.077 | 0.055 | 0.256 | 0.991 | 0.873 | 0.009 | 0.004 | 0.007 |
| *censored:* ndc ns N15 t1 (2 seeds, 8 s judge) | 0.576 | 0.323 | 0.162 | 1.000 | 1.000 | 0.110 | 0.120 | 0.020 |
| *censored:* wd ns N9 t2 (3 seeds) | 0.186 | 0.069 | 0.531 | 0.973 | 0.967 | 0.013 | 0.013 | 0.000 |
| *censored:* wd star N15 t2 (3 seeds) | 0.303 | 0.028 | 0.986 | 1.000 | 1.000 | 0.013 | 0.013 | 0.007 |

Two readings the table forces. (i) On every `t = 2` cell the coverage-first
ablation `consensus_ow_coverage` recovers more than the registered indel median
(e.g. `wd50k66` star `N = 9, t = 2`: 0.989 against 0.216), and on the star
`t = 1` cells at `N ∈ {5, 9}` as well; on the four non-star `t = 1` cells the
median leads. The objective chosen on smoke collections (§5) is the weaker of the
two on 6 of the 11 complete cells. This is reported, not acted on: the primary
was registered before the campaign and is not swapped after it (L12).
(ii) `consensus_fact` is at or above 0.930 everywhere.

Mean fact distance (judge as in §9): `consensus_ow` 1.82–9.28; `consensus_fact`
0.82–3.62; the best medoid per cell 4.15–9.41; `align_merge_ref` 16.6–28.3;
`align_merge_iter` 20.2–30.3; `pattern_vote` 9.7–13.2. Per-cell values:
`tables.md` § Headline.

Censoring of `consensus_ow` (1,800 s method budget): 0.000–0.003 on complete
cells (39 censored rows campaign-wide, all three ball arms together).

---

## 9. The certificate, and the judge footnote

**Certified ratio** `cost / LB` (Prop 3's pairwise bound), consensus against the
members' medoid **under the same metric** — the only comparison the ratio
supports. `n` = paired collections. Source: `tables.md` § Certified ratio.

| cell | n | `consensus_ow` (indel) | `medoid:isal_ow_indel` | consensus strictly lower |
|---|---|---|---|---|
| ndc ns N5 t1 | 1,350 | 1.190 | 1.255 | 0.716 |
| ndc ns N5 t2 | 1,349 | 1.249 | 1.315 | 0.819 |
| ndc ns N9 t1 | 1,350 | 1.260 | 1.325 | 0.768 |
| wd ns N5 t1 | 1,350 | 1.196 | 1.272 | 0.794 |
| wd ns N5 t2 | 1,346 | 1.242 | 1.317 | 0.843 |
| wd ns N9 t1 | 1,346 | 1.257 | 1.348 | 0.905 |
| wd star N5 t1 | 1,350 | 1.236 | 1.324 | 0.696 |
| wd star N5 t2 | 1,350 | 1.256 | 1.338 | 0.832 |
| wd star N9 t1 | 1,350 | 1.332 | 1.446 | 0.808 |
| wd star N9 t2 | 1,350 | 1.346 | 1.438 | 0.920 |
| wd star N15 t1 | 1,350 | 1.389 | 1.513 | 0.865 |

Means; medians agree to ±0.01. The consensus is at or below the medoid on
**every** paired collection (fraction 1.000 in every cell), which is the
construction (the search includes the members) holding on the rows, not a
finding. The certificate states how far each answer can be from the optimum of
its own objective: within 19–39 % on average, against 26–51 % for the medoid.
The Levenshtein pair (`consensus_ow_lev` against `medoid:isal_ow_struct`) reads
1.230–1.465 against 1.277–1.491 and belongs to the ablation, never beside the
indel row.

**Judge footnote** (every fact-distance column carries it). Fraction of judged rows
scored by `bipartite_ged_path` instead of exact HGED, per cell; budget 60 s
(`ef0c58b4`) unless marked:

| corpus × stratum | per-cell bipartite share |
|---|---|
| ndc non-star | 0.206 (N5 t1), 0.206 (N5 t2), 0.200 (N9 t1); censored: 0.177 (N9 t2, 8 s), 0.141 (N15 t1, 8 s) |
| wd non-star | 0.334, 0.324, 0.321; censored: 0.268 (N9 t2) |
| wd star | 0.099, 0.100, 0.090, 0.091, 0.082; censored: 0.057 (N15 t2) |

The fallback is the `n ≤ 10` ceiling, not oracle timeouts: across all 311,483
judged rows harvested (both tags, superseded rows included), rows whose source
has `n > 10` are scored bipartite 100 % of the time and rows with `n ≤ 10` 2.5 %
of the time.

---

## 10. Pools and wall-clock (complete cells)

Per collection, medians; `consensus_ow`'s seconds are the bundled ball
enumeration plus its scoring. Source: `tables.md` § Cost.

| cell | `consensus_ow` s (max) | pool classes | words decoded | `consensus_fact` s | `consensus_fact` pool |
|---|---|---|---|---|---|
| ndc ns N5 t1 | 33.5 (430) | 13,750 | 195,554 | 0.30 | 138 |
| ndc ns N5 t2 | 89.5 (1,400) | 32,742 | 469,845 | 0.21 | 114 |
| ndc ns N9 t1 | 121.1 (1,172) | 45,571 | 660,066 | 0.97 | 401 |
| wd ns N5 t1 | 36.0 (1,388) | 17,355 | 179,486 | 0.47 | 182 |
| wd ns N5 t2 | 100.8 (1,785) | 51,464 | 416,380 | 0.27 | 124 |
| wd ns N9 t1 | 144.8 (1,797) | 66,029 | 603,495 | 1.53 | 515 |
| wd star N5 t1 | 6.5 (112) | 4,714 | 32,644 | 0.33 | 143 |
| wd star N5 t2 | 25.0 (518) | 18,475 | 109,313 | 0.20 | 109 |
| wd star N9 t1 | 24.4 (304) | 16,286 | 114,061 | 0.95 | 403 |
| wd star N9 t2 | 102.7 (1,709) | 74,177 | 382,525 | 0.52 | 333 |
| wd star N15 t1 | 96.7 (903) | 61,653 | 406,957 | 2.83 | 1,092 |

Per-unit wall-clock (50 collections) from the tasks' own timestamps:
`RQ3V2_PILOT.md` § "The measured price" (2308421) and §11 below (2311520).

---

## 11. Capability cells, and why the heavy pass did not finish

**The consensus is a decoded object (Prop. C.4 on the arm's own output).** Over
the 15,774 non-censored `consensus_ow` collections of the campaign (complete and
partial cells; a census, not a test): the returned record is a decoded
**non-member** in 0.899 of collections (non-star 0.862, star 0.946) and a member
in 0.101; it is a connected knowledge base in **15,774 of 15,774**; of its 6,597
exact recoveries, 6,595 are decoded non-members. Across those collections the
ball enumeration decoded **8,353,279,624** words and every one decoded to a
connected knowledge base (`n_decoded_connected = n_decoded`, summed). Every
medoid, under every distance, returns a member by construction. `consensus_fact`
also returns a non-member (alignment transfer, 0.994), but in fact space, with no
word, no decoder and no certificate; `medoid:hypercot` has no score (environment
absent, every row).

**Why 2311520's heavy units still exceeded 6 h at an 8 s judge.** *Cause: the
`consensus_ow` ball, not the judge.* On the 13 units the heavy pass wrote (650
collections, joined row-by-row to the task logs), the bundled ball enumeration
plus its scoring is **99.1–99.7 % of each unit's wall** (16,974–21,577 s); the
residual outside every timer — the judge and all bookkeeping — is **2–7 s per
unit**, every judge call in those collections answered exactly, and no 8 s
timeout fired. Across all 6,252 collections the 189 tasks started, the judge
timed out 145 times, i.e. at most 1,160 s of 3.95 × 10⁶ collection-seconds
(0.03 %). The ball on the heavy cells costs a median 278 s (`ndc` non-star
`N = 9, t = 2`) to 340 s (`ndc` non-star `N = 15, t = 1`) per collection over
pools of 0.9–1.1 × 10⁵ classes from 1.3–1.7 × 10⁶ decoded words; from the logs,
the finished-collection median wall runs 314–1,495 s by cell and 25–179
collections per cell hit the 1,800 s method budget, so a 6 h task finished a mean
17.2–47.0 of the 50 collections a unit needs. The pre-submission arithmetic
("Why 8 s") took the ball at 127 s per collection at `N = 15`; that median was
pooled over the `N = 15` collections 2308421 had written, 27 of whose 35 units
were `wd50k66` star `N = 15, t = 1` (96.7 s median), the one easy `N = 15` cell.
On `t = 2` and on non-star `N = 15` the ball is 3–4× that. The evidence offered
for the judge diagnosis of the first pass does not hold either: its "17.8 %
fallback after the full 60 s" is the `n > 10` ceiling (§9), which spends no
oracle time. (How much of 2308421's wall the 60 s judge did take is not
recoverable from the rows and was not re-derived from that job's logs.) Sources: `~/execs/tkde/logs/tkde-rq3v2-heavy_2311520_*.{out,err}`
(189 pairs, copied to the harvest scratchpad for the join), the 13 `1efdcf54` row
files, `sacct -j 2311520`.

---

## 12. Capability-table cells this experiment fills

| column of `tab_kb_representation_properties.tex` | value and source |
|---|---|
| Cons., `w°` row | ✓ with footnote: decoded non-member 0.899, connected 15,774/15,774, certified ratio below the same-metric medoid on every collection; scope non-star `N ∈ {5,9}` / stars `N ≤ 15`, `r = 2`; and the fact-space consensus recovers more (H3.5). §7, §9, §11 |
| Cons., certificate and vector rows | "--": a medoid under any distance returns a member (exact recovery ≤ 0.003 in every cell, §8); `hypercot` unscored (environment absent) |
