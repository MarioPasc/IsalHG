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
| results root (Picasso) | `~/results/IEEETKDE_ow/RQ3v2_golden_record/anonymous_consensus/` |
| results root (drive) | `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE_ow/RQ3v2/` |
| runner | `experiments/tkde/rq3v2.py` |
| analyzer | `experiments/tkde/analyze_rq3v2.py` |
| config | `experiments/tkde/configs/rq3v2.yaml` |
| SLURM | `slurm/tkde/rq3v2_{launcher,worker}.sh`; deploy `slurm/tkde/rq3v2_sync.sh` |
| corpora | the frozen `ndc_classes` (1,381) and `wd50k66` (3,988) |
| program | `isal_ow_struct` (`w°`), 60 s budget, under the forked-child model of `experiments/tkde/budget.py` |
| job ids | *pending submission* |
| run tag | *pending: written into every row, into `summary.json` and into `manifest.json`* |

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

Primary: the **generalized median in the word metric** — minimise
`Σᵢ d_I(w°(M), w°(Kᵢ))`, ties by coverage, then by the shortlex of `w°`. Grounds,
all a priori: it is the classical consensus objective in string spaces; the
medoid is the same objective restricted to the members, so the consensus cost is
at most the medoid's by construction; and Prop 3's bound
`LB = Σ_{i<j} d(Kᵢ,Kⱼ)/(N−1)` lower-bounds the optimum over every point, giving a
**certified ratio** `cost / LB` a coverage objective cannot have.

v1's coverage order runs on every collection as `consensus_ow_coverage_first`;
the fact-space computation runs as `consensus_fact` (H3.5).

Measured on two smoke collections only — worth nothing except as a sanity check,
and recorded here so it is not mistaken for a result: `consensus_ow` ratio 1.148
against medoid ratios 1.143–1.546, i.e. at the best medoid's ratio, while the
coverage order gave 1.67 and 1.86.

---

## 6. Hypotheses and their verdicts

| # | Statement | Verdict |
|---|---|---|
| H3.1 | non-star, t ≤ 2: `consensus_ow` recovery > the three anonymous merges, Holm-significant, every N | *pending* |
| H3.2 | `consensus_ow` fact distance < every medoid's | *pending* |
| H3.3 | non-star: `consensus_ow` ≥ `majority_merge_id` − 0.05 | *pending* |
| H3.4 | stars: `pattern_vote` ties `consensus_ow` (\|Δ\| < 0.05) — `wd50k66` only | *pending* |
| H3.5 | `consensus_ow` ≥ `consensus_fact` − 0.05 at matched r, at lower cost | *pending* |
| H3.6 | recovery rises with N; the N = 5 shortfall is a sub-record, not an arbitrary object | *pending* |

Fallbacks, as declared: H3.1 failing on one corpus scopes the claim to the other;
failing on both makes H3.2 plus the certificate the headline, moves the consensus
to a supporting exhibit and promotes RQ8. H3.5 failing reduces RQ3's language
claim to the decoded output, the certificate and the cost.

---

## 7. Capability-table cells this experiment fills

| column of `tab_kb_representation_properties.tex` | filled by |
|---|---|
| consensus is a decoded object | the `winner_origin` column: `decoded:non_member` versus `member:i` |
| every competitor's blank | the `reason` column of each censored row — "a medoid returns an input", "no decoder", the absent `hypercot` environment |
