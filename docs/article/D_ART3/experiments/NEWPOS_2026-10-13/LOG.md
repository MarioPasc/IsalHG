# NEWPOS — searching for new comparative experiments where the language wins

**Owner:** `[IsalHG-Article-Iterator]` · **Opened:** 2026-10-13 14:32 CEST ·
**Branch:** `feature/newpos-experiments` (cut from `integration/2026-09-13-headline-w0` @ `216dd41`).

**Why.** The PI read the 2026-10-04 draft and asked for more experiments with
tables and figures, "especially comparative", and ruled on 2026-10-05: *"hay que
elegir aplicaciones en las que nuestro método vaya bien"*. Losses stay in the
record and go to the supplement; nothing is deleted.

**Rules for this log.** Append-only. Every probe states its hypothesis, its
mechanism (which property of the language should cause the win), its kill
criterion, and its competitors *before* it runs. Every number names the script
and the data it came from. Negative probes stay here with the same detail as
positive ones.

**Data (read-only).** `D = /media/mpascual/Sandisk2TB/research/ISAL/isalhg`.
Frozen corpora `D/results/IEEETKDE/corpora/{wd50k66, ndc_classes, ...}`; cached
full distance matrices `D/results/IEEETKDE/matrices/<collection>/<arm>.npy`
(member order = corpus order, `member_order_sha1` in each manifest). Arms:
`isal_ow_struct` (= `w°`), `wstar_orbit` (= `w*_c`, censored members listed in
`wstar_orbit.censored.json`), `nauty_cert`, `nauty_cert_rows`, `wl_l1`,
`netlsd`, `hpd_jsd`, `bipartite_ged_assign`, `bipartite_ged_path`,
`degree_seq_l1`, `size_l1`, `fact_rank` (retired word, record only).

---

## 0. Context digest (what the paper already has, what it lost)

Main text (5 hypotheses): H1 exactness (ties the certificate), H2 pendant-removal
locality (observation, not pre-registered), H3 envelope (vs `w*_c` only; parity
with the certificate), H4 generation validity (unconditional), H5 completion
(WD50K relational only). Supplement: interior locality, RQ8 on NDC and stars,
RQ3 v2 golden record (fact-space ablation wins), RQ5 clustering (negative for
all), RQ4 (never completed), RQ6 novelty (fact list wins standalone).

The measured pattern (WRITING_BRIEF §f.4): where a record is a multiset of fact
patterns (stars), counting wins; where constants are shared, the language wins on
attachment and validity. Anything only needing a complete invariant, the
certificate gives as well. **Stratify star / relational in every new probe.**

Already rejected (do not repeat): iso speed vs nauty; `d_I` as HGED proxy;
planted-family clustering/kNN; HIC anchor; fact-rank word; medoid-vs-source
consensus.

## 1. Candidate queue (ranked by prior × cost)

| id | candidate | property it exploits | competitors | cost |
|---|---|---|---|---|
| C1 | joint valid∧connected∧novel yield (MOSES/GuacaMol-style V·U·N) | closure + connectivity (Prop. C.4) | fact-list, incidence-list n-grams | zero (already measured, `rq6_generation_facts.md` "joint yield") |
| C2 | exact metric similarity search: intrinsic dimensionality `ρ = μ²/2σ²` (Chávez et al. 2001) + pivot-index distance computations per exact k-NN query | metric + locality spreading the distance distribution | certificate bytes/rows, WL, NetLSD, HPD, bipartite (non-metric → no exact pruning), floors | minutes, cached matrices |
| C3 | anonymous version linkage on the NDC quarterly series (match a class's quarter-q record to its quarter-q+1 record) | pendant locality on real version changes | all matrix arms | minutes, cached matrices |
| C4 | generation fidelity: does filtering a baseline's output to the domain bias its accepted samples (toward small / star KBs)? MMD / Wasserstein on m, n, arity, predicates, relational fraction | closure: no rejection step, so no selection bias | fact-list (accepted), incidence-list (accepted), held-out floor | hours, local |
| C5 | description length: held-out bits per KB under the same sequence model, and collection compression by generic compressors | name-freedom (Prop. C.6): the word never spends bits naming constants; no mass on invalid strings | certificate, fact list, incidence list, + xz/zstd | hours, local |
| C6 | noisy-duplicate retrieval under pendant noise (retracted statements) on WD50K relational stratum | pendant locality | all matrix arms, recomputed on noisy queries | hours |

## 2. Probes

*(appended below as they run)*

### P-C3a — version linkage on NDC-classes, nearest-neighbour ranking (2026-10-13 14:40)

**Hypothesis.** Consecutive quarterly versions of a drug class's record differ
mostly by products entering or leaving with new co-classes (pendant edits); `w°`
absorbs pendant removals in ≤ 2 instructions (H2), so a record's next version
should rank first among all records of the next quarter more often under `d_I`
than under the certificate. **Kill:** `w°` hit@1 not above the certificate's.
**Competitors:** every cached matrix arm. **Data:** `ndc_classes`, 528 natural
consecutive pairs (128 constant-preserving, 400 constant-changing), both
directions → 1,056 queries; candidates = every member of the target's window
(median 31, max 51). Ties scored by expectation. **Script:**
`scripts/newpos/probe_version_linkage.py`; output
`scratchpad/newpos/c3_linkage_ndc.txt`.

| arm | MRR | hit@1 | MRR pres. | hit@1 pres. | MRR chg. | hit@1 chg. |
|---|---|---|---|---|---|---|
| **`w°`** | 0.446 | **0.333** | 0.568 | 0.458 | 0.407 | **0.293** |
| certificate bytes | 0.303 | 0.195 | 0.686 | 0.556 | 0.180 | 0.079 |
| certificate rows | 0.283 | 0.189 | 0.677 | 0.557 | 0.157 | 0.072 |
| WL | 0.222 | 0.133 | 0.518 | 0.421 | 0.127 | 0.041 |
| NetLSD | 0.298 | 0.177 | 0.577 | 0.447 | 0.209 | 0.091 |
| HPD | **0.470** | 0.306 | 0.634 | 0.488 | **0.418** | 0.248 |
| bipartite assign | 0.401 | 0.276 | 0.668 | 0.541 | 0.316 | 0.191 |
| bipartite path | 0.431 | 0.313 | **0.696** | **0.576** | 0.346 | 0.228 |
| degree-seq floor | 0.311 | 0.191 | 0.539 | 0.408 | 0.238 | 0.121 |
| size floor | 0.236 | 0.130 | 0.466 | 0.331 | 0.162 | 0.066 |

(`w*_c` skipped: its matrix covers 1,311 of 1,381 members.)

**Reading.** The mechanism shows: on constant-changing pairs `w°` beats the
certificate 0.293 vs 0.079 hit@1 (3.7×), and on constant-preserving pairs the
certificate wins (0.556 vs 0.458), exactly the pendant/interior split of H2. But
the win is not clean against every competitor: HPD has the higher MRR overall
(0.470 vs 0.446) and on constant-changing pairs (0.418 vs 0.407); the edit-path
cost is within 0.02 of `w°` on hit@1. **Status: PROMISING, not yet a win.**
Untested: significance; 1-to-1 assignment linkage; larger gaps between versions.

### P-C2a — exact metric similarity search (2026-10-13 14:45)

**Hypothesis.** Pendant locality spreads `d_I`'s distance distribution, so
`d_I` has a lower intrinsic dimensionality `ρ = μ²/2σ²` (Chávez et al. 2001)
than the certificate's distance and an exact pivot index (LAESA-style,
max-separated pivots, best-first on the pivot lower bound) evaluates fewer
distances per exact 10-NN query. **Kill:** `w°` evaluates more distances than
the certificate on either collection. **Script:**
`scripts/newpos/probe_metric_search.py` (300 queries, k = 10, seed 0); outputs
`scratchpad/newpos/c2_{ndc,wd50k66}.txt`.

| arm | ρ NDC | eval@32 NDC | ρ WD50K | eval@32 WD50K | exact? |
|---|---|---|---|---|---|
| **`w°`** | 0.46 | 0.126 | 0.47 | 0.299 | yes |
| `w*_c` | 1.41 | 0.207 | 0.64 | 0.369 | yes |
| certificate bytes | 1.10 | 0.172 | 0.99 | **0.137** | yes |
| certificate rows | 4.18 | 0.737 | 2.12 | 0.960 | yes |
| WL | 8.34 | 0.810 | 3.46 | 0.902 | vector pseudometric |
| NetLSD | 1.32 | 0.035 | 1.30 | 0.016 | vector pseudometric |
| HPD | 15.55 | 0.273 | 9.94 | 0.333 | vector pseudometric |
| bipartite assign | 0.42 | 0.044 | 0.65 | 0.033 | pseudometric |
| bipartite path | 0.50 | 0.121 (47.7 % wrong answers) | 1.02 | 0.110 (65.3 % wrong) | **not a metric** |
| degree-seq / size | 0.22 / 0.53 | 0.041 / 0.084 | 0.60 / 0.65 | 0.041 / 0.044 | floors |

**Reading.** `ρ` is lowest for `w°` among the complete invariants on both
collections, but the practical pruning does not follow on WD50K, where the byte
certificate evaluates 0.137 of the collection against 0.299. The low `ρ` of
`w°` comes with a heavy right tail (σ > μ) that tracks word length, i.e. size —
the floors index even better, so indexability alone is not a quality. **Kill
criterion met on WD50K → NEGATIVE (supplement).** One reusable by-product: the
bipartite edit path, used as if it were a metric, returns a wrong 10-NN set for
48–65 % of queries under pivot pruning, a concrete consequence of its
non-metricity worth one sentence in H1.

### P-C3b — version linkage replication on NDC-substances (2026-10-13 14:55)

Same protocol as P-C3a on the second quarterly series (`ndc_substances`, one
constant type, 885 consecutive pairs → 1,770 queries, candidates median 36, max
95). The `w°` matrix was not cached for this collection; built with
`scripts/newpos/build_ow_matrix.py` (0.26 s, scratchpad). Output
`scratchpad/newpos/c3_linkage_ndcsub.txt`.

| arm | MRR | hit@1 | hit@1 chg. |
|---|---|---|---|
| `w°` | 0.406 | 0.261 | 0.255 |
| certificate bytes / rows | 0.292 / 0.234 | 0.152 / 0.139 | 0.134 / 0.120 |
| WL | 0.135 | 0.057 | 0.040 |
| NetLSD | 0.419 | 0.249 | 0.237 |
| HPD | 0.410 | 0.235 | 0.222 |
| bipartite assign / path | 0.435 / 0.437 | 0.281 / 0.290 | 0.266 / 0.274 |
| **degree-seq floor** | **0.443** | **0.291** | **0.279** |
| size floor | 0.351 | 0.203 | 0.196 |

**Reading.** The certificate gap replicates (`w°` 0.261 vs 0.152 hit@1), but the
degree-sequence floor beats every structural representation, `w°` included —
the size/degree confound of lesson L1. Version linkage by nearest neighbour is
**not a defensible win → NEGATIVE / MIXED (supplement)**. Not pursued further
without a design that removes the degree confound (none is pre-registered; I am
not fishing for one).

### Wave `2026-10-13-newpos-w1` (launched 2026-10-13 ~15:10)

Base `518824a`. Three Sonnet 5.5 (xhigh) workers in isolated worktrees (the
project's `CLAUDE_CODE_SUBAGENT_MODEL=sonnet` pins subagents to Sonnet). Each has
pre-registered hypotheses in its prompt and must report a pilot to the
orchestrator before its full run. Work logs land in
`.claude/notes/2026-10-13-newpos-w1/<slug>.md`; results in
`D/results/NEWPOS_2026-10-13/<slug>/`.

| slug | question | hypotheses | mechanism |
|---|---|---|---|
| `genbench-ngram` | fidelity of the **usable** samples (decoded ∧ connected) — RQ6 scored all decoded samples, including the fact list's out-of-domain ones | HA1 rejection bias in m/n (JSD, W1); HA2 relational fraction; HA3 VUN per draw; + the fact list's LCC-repair as the baseline's strongest construction | closure: no rejection step ⇒ no selection bias |
| `compression` | bits per KB of `w°` vs certificate (bytes, rows), fact list, incidence list under fixed-width, held-out n-gram (5-fold), xz/zstd/bzip2; version deltas (`zstd --patch-from`) on both NDC series | HB1 vs certificate; HB2 vs serializations; HB3 deltas (constant-changing) | name-freedom (the word never names a constant) |
| `neural-gen` | identical GRU LM over the three serializations; validity, usable yield, VUN, held-out bits | HC1 validity 1 by theorem; HC2 yield/VUN; HC3 neural bits/KB | closure is model-agnostic |

Shared contract: one JSONL sample format (frozen in both generation prompts) so
`genbench-ngram`'s evaluator scores the GRU samples after the merge.

**Amendment to `compression`'s pre-registration (sent ~15:20, before any result
was relayed; prompted by `[Opus-Article-Orchestrator]` and lesson L9).** The
certificate is reported under three granularities (bytes, rows, integers). The
compactness claim is made only if `w°` wins under every granularity and every
coder; if the verdict flips with tokenization, all are reported and none is
claimed. Fixed-width bits are reported under both the observed alphabet and the
theoretical one (`|Σ_HG(k)|` with labels; the certificate's full symbol range).
Median and mean token lengths are reported, to reconcile prose.md §2.2 (6/8
instructions vs 12 rows) with T-KBx (13.8 tokens vs 40 integers).

### Review by `[IsalHG-Fable-Review]` (received ~15:35) and the amendments it caused

- C (GRU) must run whatever the outcome; pre-register both outcomes ("guaranteed
  vs learned" with the residual rate printed). → sent to `neural-gen`.
- A goes to the main text only if the gap survives the LCC repair at **equal
  numbers of usable samples** (never equal draws), with the bias direction
  pre-stated (toward small / star KBs). → sent to `genbench-ngram`: matched
  subsampling is primary, arms with < 100 usable samples per seed are excluded
  from fidelity, and the directional HA1.
- B is supplement material, except the version deltas, which make name-freedom
  a measurable benefit. Compare at the row tokenization and report both edit
  regimes.
- New leads: (Z1) a full-matrix time table at N = 3,988, already measured (RQ7
  §8); (D1) augmentation by interpolation for under-populated entity types;
  (C7) RQ1 M2 — Spearman ρ between version distance and the true fact-level
  change on the NDC natural series, `w°` 0.556 vs certificate rows 0.275 and
  bytes 0.184 (WD50K ladder goes the other way), never measured against the
  floors or the vector representations.

### P-C7 — does version distance track the amount of change? (pre-registered 2026-10-13 15:40, before running)

**Hypothesis.** On natural consecutive version pairs, the distance between the
two versions increases with the true number of changed facts (`delta` in the
corpus metadata, computed from constant identities, which no representation
sees). Pendant locality (H2) predicts `d_I` tracks `delta` better than the
certificate. **Test:** Spearman ρ(d(a, b), delta) over pairs, per arm, on both
NDC series, with a 95 % cluster bootstrap over classes (2,000 resamples) and
the paired difference ρ(`w°`) − ρ(arm) bootstrapped on the same resamples.
**Kill:** any arm, floors included, with a point ρ ≥ `w°`'s on either series →
not a clean win (reported whole either way). **Script:**
`scripts/newpos/probe_change_tracking.py`.

**Result (15:50; output `scratchpad/newpos/c7_tracking.txt`).** Spearman ρ with
95 % cluster-bootstrap CI; Δ = ρ(`w°`) − ρ(arm) with its paired CI (bold = CI
excludes 0).

| arm | NDC-cl. all (528) | NDC-cl. chg (400) | NDC-sub. all (885) | NDC-sub. chg (828) |
|---|---|---|---|---|
| **`w°`** | 0.573 [0.42, 0.72] | 0.500 [0.34, 0.66] | 0.856 [0.75, 0.90] | **0.858** [0.75, 0.90] |
| certificate bytes | 0.561 | 0.192 (**Δ +0.31**) | 0.745 (**Δ +0.11**) | 0.713 (**Δ +0.15**) |
| certificate rows | 0.583 | 0.271 (**Δ +0.23**) | **0.867** (Δ −0.01) | 0.853 (Δ +0.01) |
| WL | 0.542 | 0.292 (**Δ +0.21**) | 0.786 | 0.769 |
| NetLSD | 0.454 | 0.037 (**Δ +0.46**) | −0.288 (**Δ +1.14**) | −0.388 (**Δ +1.25**) |
| HPD | **0.747** (**Δ −0.17**) | **0.558** (Δ −0.06) | 0.206 (**Δ +0.65**) | 0.125 (**Δ +0.73**) |
| bipartite assign | 0.591 | 0.323 (**Δ +0.18**) | 0.723 (**Δ +0.13**) | 0.693 (**Δ +0.17**) |
| bipartite path | 0.654 | 0.409 | 0.821 | 0.802 (**Δ +0.06**) |
| degree-seq floor | 0.559 | 0.330 (**Δ +0.17**) | 0.766 (**Δ +0.09**) | 0.746 (**Δ +0.11**) |
| size floor | 0.529 | 0.194 (**Δ +0.31**) | 0.486 (**Δ +0.37**) | 0.429 (**Δ +0.43**) |

On constant-preserving pairs (128 / 57) every arm except the size floor sits at
0.80–0.99 and HPD leads on NDC-classes (0.988).

**Reading.** Kill criterion met: HPD beats `w°` on NDC-classes (0.747 vs 0.573)
and the row certificate edges it on NDC-substances (0.867 vs 0.856). On
constant-changing pairs, the pendant regime, `w°` is never significantly beaten
and is the only arm in the top group on *both* series. Every competitor that
leads one series collapses on the other: HPD falls from 0.558 to 0.125, and
the row certificate from 0.853 to 0.271. That "robust across series" reading
was formed *after* seeing the data, so it cannot be claimed as a pre-registered
win. It can support the H2 paragraph as an observation on real version pairs,
with all arms printed. **Status: MIXED (supplement; one observational
sentence at most).** It reproduces the RQ1 M2 figure Fable cited (`w°` 0.556 vs
rows 0.275 / bytes 0.184 on the NDC natural pendant series) with a slightly
different pair set.

### `genbench-ngram` pilot (3 seeds; received ~16:05)

Evaluator reproduces RQ6 exactly on the all-decoded arms (validity,
connectivity, five JSDs: max relative difference 0). Star definition reproduces
53.4 % / 3.0 %. Pre-registration and amendment were written before any
usable-sample number existed.

| per 10,000 draws | WD50K(66) usable / VUN | NDC-classes usable / VUN |
|---|---|---|
| `w°` n-gram | 9,998 / 8,174 | 9,999 / 6,867 |
| fact list | 1,264 / 659 | 4,141 / 3,236 |
| fact list + LCC repair | 9,995 / 7,492 | 9,987 / 6,885 |
| incidence list | 0.7 / 0.7 | 16 / 16 (excluded from fidelity, u < 100) |

Fidelity of usable samples (unmatched; matched subsampling moves `w°` by
< 0.002 JSD): `w°` is equal or **worse** on JSD_n / JSD_m (NDC JSD_m: `w°` 0.127
vs fact list 0.026 vs LCC 0.049); W1_m favours `w°` on WD50K only. The
direction check fails: the fact list's usable samples are smaller than the
collection on WD50K but **larger** on NDC, and not more star-like on either.
HA2 is reversed against the raw fact list (`w°` over-produces relational
structure: star fraction 0.457 vs 0.534). **Reading: HA1/HA2 NEGATIVE
(rejection bias does not exist as hypothesised); HA3 yield holds against the raw
baselines, but the trivial LCC repair nearly closes it (VUN 0.749 vs 0.817 on
WD50K, 0.689 vs 0.687 on NDC).** The LCC repair, however, destroys stars
(star fraction 0.327 vs 0.534 on WD50K). 27-seed run authorised to make the
negative citable.

### P-C8 — one-edit near-duplicate detection (pre-registered 2026-10-13 16:15, before running)

**Rationale.** C3/C7 suggest `w°` is the only representation that is both
*exact at zero* (no false merges, unlike WL / NetLSD / HPD / bipartite
assignment / floors) and *local under pendant edits* (unlike the certificate).
A task that needs both is near-duplicate detection, a classic data-management
problem: in a collection, find the pairs of records that differ by exactly one
single-fact edit (two descriptions of one entity differing by one
statement/qualifier).

**Ground truth (exact, polynomial, no representation involved).** For every
member K, enumerate its *down-neighbours*: delete one fact, or remove one
constant from one fact of arity ≥ 2; drop constants left in no fact
(`compact`); discard results that are disconnected or carry duplicate facts.
Key each by the `w°` fingerprint `(root type, word)` (Theorem C; the key only
decides isomorphism and never enters a score). A pair (i, j), not isomorphic,
is **positive** iff K_j ≅ a down-neighbour of K_i or vice versa, i.e. one of the
four single-fact edits of §3 turns one into the other. Isomorphic pairs are
excluded from the task (the census handles them).

**Scores.** (i) Pairwise average precision over all non-isomorphic pairs,
ranking by distance (ties grouped); (ii) per query, for each member with ≥ 1
positive partner, the expected rank (ties by expectation) of its nearest
positive among all non-isomorphic others → MRR and hit@1. Stratified by
pendant/interior edit and by star/relational pair.

**Hypothesis H-ND.** `w°` has the highest AP and MRR among all cached arms on
WD50K(66) and NDC-classes. **Kill:** any arm ≥ `w°` on either metric on either
collection. **Pre-stated risk:** the bipartite edit-path cost is an upper bound
on the true edit distance, so every negative has path cost ≥ 2 while positives
have ≥ 1 — it may be near-perfect by construction (at cubic cost and without
the metric axioms). If it wins, that is the result. **Script:**
`scripts/newpos/probe_near_duplicates.py`.

**Result — probe (16:25, `probe_near_duplicates.py`), then hardened (16:45,
`scripts/newpos/neardup.py`; results
`D/results/NEWPOS_2026-10-13/neardup/neardup_<collection>.json` + truth files).**
Hardening, decided before the hardened run: the truth is keyed by the **nauty
certificate**, not by our word (`--key both` asserts both keys give the same
partition and positives — they do, 5,994 / 5,994 and 2,721 / 2,721). The
canonical-rank fact list `fact_rank` is added as the serialization baseline.
Per-query metrics (reciprocal rank of the nearest positive, hit@1/@10, AP) are
computed over every member with ≥ 1 positive partner, with tie blocks resolved
by expectation. CIs come from a bootstrap over queries clustered by class
(2,000 reps). Tests are one-sided paired Wilcoxon on per-query RR, `w°` vs each
arm, Holm-corrected, with rank-biserial effect.

Ground truth: NDC-classes 949,712 non-isomorphic pairs, **5,994 positives**
(4,451 pendant / 1,543 interior), 1,086 queries; WD50K(66) 7,949,355 pairs,
**2,721 positives** (2,437 pendant / 284 interior), 1,226 queries (794 stars).

| arm | NDC AP | NDC MRR [95 % CI] | NDC hit@1 | p_Holm, r_rb | WD AP | WD MRR [95 % CI] | WD hit@1 | p_Holm, r_rb |
|---|---|---|---|---|---|---|---|---|
| **`w°`** | **0.168** | **0.416** [0.366, 0.468] | **0.372** | — | **0.139** | **0.541** [0.520, 0.560] | **0.489** | — |
| certificate bytes | 0.031 | 0.144 | 0.124 | 4e-83, +0.68 | 0.001 | 0.039 | 0.022 | 4e-180, +0.95 |
| certificate rows | 0.019 | 0.169 | 0.143 | 8e-70, +0.62 | 0.001 | 0.035 | 0.017 | 5e-184, +0.96 |
| fact list (`fact_rank`) | 0.150 | 0.381 | 0.345 | **0.016, +0.09** | 0.004 | 0.101 | 0.074 | 2e-155, +0.88 |
| WL | 0.011 | 0.012 | 0.006 | 1e-167, +0.97 | 0.001 | 0.002 | 0.000 | 3e-201, +1.00 |
| NetLSD | 0.012 | 0.022 | 0.004 | 5e-153, +0.93 | 0.001 | 0.009 | 0.000 | 1e-200, +1.00 |
| HPD | 0.108 | 0.246 | 0.167 | 2e-32, +0.43 | 0.003 | 0.018 | 0.004 | 7e-197, +0.99 |
| bipartite assign | 0.066 | 0.334 | 0.270 | 2e-10, +0.23 | 0.001 | 0.021 | 0.008 | 5e-198, +0.99 |
| bipartite path | 0.067 | 0.413 | 0.353 | **0.19 (n.s.), +0.03** | 0.002 | 0.091 | 0.048 | 1e-176, +0.94 |
| degree-seq floor | 0.019 | 0.095 | 0.051 | 2e-107, +0.78 | 0.001 | 0.028 | 0.010 | 1e-198, +0.99 |
| size floor | 0.010 | 0.018 | 0.007 | 1e-152, +0.92 | 0.001 | 0.005 | 0.002 | 5e-200, +1.00 |

Stratified: `w°`'s AP on interior positives is ≈ 0 (0.002 / 0.000) — the H2
condition again — while the fact list (0.413) and the byte certificate (0.080)
detect interior one-edit pairs on NDC. Relational queries on WD50K: `w°` MRR
0.597 vs bipartite path 0.175 and fact list 0.190.

**Reading.** H-ND survives its kill criterion on point estimates on both
collections. On WD50K(66), the large hyper-relational collection, `w°` is
5–50× ahead of every representation on every metric. On NDC-classes it is
first on every metric, but statistically tied with the bipartite edit path on
MRR (p = 0.19), which costs cubic time per pair and is not a metric, and only
marginally ahead of the fact list (p = 0.016, r = 0.09). Mechanism: both
properties at once. Exactness at zero keeps non-isomorphic look-alikes from
outranking the true neighbours; WL, NetLSD, HPD and the floors drown in ties.
Pendant locality keeps the true neighbours within 1–2 instructions, where the
certificate moves 11–13 rows. **Status: STRONG CANDIDATE.** Next: confirmatory
replication on the two collections this probe has not seen.

### P-C8-rep — confirmatory replication (pre-registered 16:50, before running)

**H-ND-rep.** On `ndc_substances` (all arms; the `w°` matrix built by
`build_ow_matrix.py`) and `wd50k100` (cached arms only: certificate bytes, fact
list, WL, degree-seq, size, `w*_c`), `w°` has the highest MRR and global AP of
all arms. Same script, same settings, truth keyed by the certificate. **Kill:**
any arm with MRR or AP ≥ `w°`'s on either collection. The protocol is
unchanged from P-C8.

**Result (17:00; output `scratchpad/newpos/c8_rep.txt`, JSONs in the neardup
results dir).**

| collection (positives: pendant / interior) | `w°` MRR [CI] | best other MRR | `w°` AP | best other AP | `w°` AP pendant / interior |
|---|---|---|---|---|---|
| NDC-substances (17,162 / 13,586) | **0.717** [0.679, 0.748] | bipartite path 0.701 (p_Holm = 1.0, r = −0.06) | 0.430 | **degree-seq 0.459**, bipartite path 0.444 | **0.581** (next: degree-seq 0.269) / 0.075 (path 0.576, cert 0.455) |
| WD50K(100) (5,215 / 1,778), cached arms only | **0.685** [0.662, 0.709] | fact list 0.318 (p_Holm 3e-70, r +0.70) | **0.181** | fact list 0.089 | **0.226** / 0.004 (fact list 0.298) |

**Reading. Kill criterion met on NDC-substances (AP)**: the degree-sequence
floor and the bipartite edit path rank the whole positive set better. The cause
is visible in the stratification. 44 % of NDC-substances' positives are
interior one-edit pairs, where `w°` is blind (AP 0.075) and the certificate
and the edit path are strong. On the pendant positives `w°` leads by 2×. On
WD50K(100) `w°` again dominates the arms that are cached; the missing
competitors (rows, NetLSD, HPD, bipartite) are being built (background job,
`build_ow_matrix.py --arm`).

**Where H-ND stands.** On MRR, `w°` has the top point estimate on all four
collections. It is significantly first on both WD50K collections and tied with
the bipartite edit path on both NDC series; that path costs cubic time per
pair, is not a metric, and collapses on WD50K (0.091). On AP, `w°` is first
on three of four. The defensible scope is the H2 condition again: one-edit
near-duplicates **that differ by a pendant edit** (a statement or qualifier
added or removed together with its value). There `w°` leads every
representation on every collection, by 2× on NDC and 7–50× on WD50K. The
unconditional claim fails on NDC-substances and is stated as such.

**WD50K(100) completed (17:20).** The missing competitor matrices (rows,
NetLSD, HPD, bipartite assign/path) were built locally with the registry
defaults (same `params: {}` as the campaign manifests; 1.3 s / 3.5 s / 53 s /
65 s / 106 s). `w°` MRR **0.685** [0.662, 0.709] vs bipartite path 0.257, fact
list 0.318, certificate rows 0.179; AP **0.181** vs fact list 0.089, bipartite
path 0.048. Every Holm-corrected p < 1e-70, rank-biserial 0.70–1.00. Output
`scratchpad/newpos/c8_rep_wd100_full.txt`.

**Family ablation — the search form `w*_c` on the members it canonicalises
(`--restrict-to-arm wstar_orbit`; output `scratchpad/newpos/c8_wstar.txt`).**

| | `w°` MRR / AP | `w*_c` MRR / AP | bipartite path MRR | fact list MRR |
|---|---|---|---|---|
| NDC-classes (1,311 members) | 0.410 / 0.181 | **0.525 / 0.252** | 0.410 | 0.368 |
| WD50K(66) (3,983 members) | **0.541 / 0.139** | 0.475 / 0.105 | 0.091 | 0.101 |

The search form is better on NDC-classes, consistent with its insertion
locality (RQ1). There it beats the bipartite edit path that ties `w°`. Both Isal
programs lead every non-Isal representation on WD50K by about 5×.

### C8 status summary (17:25)

| collection | `w°` MRR | best non-Isal MRR | verdict |
|---|---|---|---|
| WD50K(66) | **0.541** | 0.101 (fact list) | `w°` first, p_Holm < 1e-150 |
| WD50K(100) | **0.685** | 0.318 (fact list) | `w°` first, p_Holm < 1e-70 |
| NDC-classes | **0.416** | 0.413 (bipartite path) | tie with the edit path (p = 0.19); `w*_c` 0.525 beats it |
| NDC-substances | **0.717** | 0.701 (bipartite path) | tie with the edit path; AP lost to degree-seq (0.459 vs 0.430) |

### Second review by `[IsalHG-Fable-Review]` on C8 (received ~17:35) and what it changed

1. Defensible for TKDE as "near-duplicate retrieval under anonymization". The
   strongest objection: radius-1 positives are found *exactly* by enumeration
   plus any complete invariant (that is how the truth is built), so the
   experiment measures **ranking quality for similarity search**, not
   detection — the text must say an exact radius-1 detector exists. Also, the
   pooled score is a mixture weighted by each collection's pendant share. →
   Print the shares; add a **radius-2 stratum**, where enumeration is no
   longer trivial: "if `w°` still ranks those first, the ranking generalises
   beyond the enumerable radius; if not, say the task is radius-1" (the
   reviewer's prediction, stated before the radius-2 run).
2. The kill fired on NDC-substances; switching the headline from AP to pooled
   MRR after the kill is the first thing a reviewer checks. **The headline is
   the stratified one**, and the pooled "first on 4/4" appears only in the
   table. Print the `w*_c` ablation and explain it by coverage.
3. Inflation checks: query selection (star fraction of queries vs corpus),
   domain filtering, censored cells, the certificate read as a strawman (keep
   the fact list and the edit path in every row).
4. `wd50k100` and `ndc_substances` are "controls" in the draft's setup;
   promoting them needs the data section updated.

### P-C8-strata — stratified per-query retrieval (17:45; `neardup.py`, output `scratchpad/newpos/c8_strata.txt`)

Per query, its positives are its pendant (or interior) one-edit partners. Its
partners of the other kind are removed from the candidate list, counting
neither as a miss nor as a hit. Same bootstrap and tests.

**Inflation checks.** Non-finite cells: 0 in every matrix of every collection.
The domain filter is **lossless**: every member is connected, so a
disconnected down-neighbour can match no member, and a remove-constant edit
that duplicates a fact equals a fact deletion already enumerated. Star fraction
of queries vs corpus: NDC-cl 0.021 / 0.030; NDC-sub 0.240 / 0.158; WD66 0.648 /
0.534; WD100 0.159 / 0.148 (mild star skew on two collections; MRR on
relational queries is reported per collection in the JSONs).

**Radius 1, pendant one-edit neighbours — `w°` first on all four collections.**

| collection (pendant queries) | `w°` MRR [95 % CI] | runner-up | max p_Holm vs `w°` | min r_rb |
|---|---|---|---|---|
| NDC-classes (936) | **0.449** [0.392, 0.503] | bipartite path 0.263 | 2.6e-33 | +0.47 |
| NDC-substances (994) | **0.726** [0.690, 0.760] | degree-seq 0.349 | 2.4e-95 | +0.77 |
| WD50K(66) (1,191) | **0.552** [0.534, 0.572] | bipartite path 0.065 | 1.9e-183 | +0.97 |
| WD50K(100) (925) | **0.691** [0.666, 0.714] | bipartite path 0.175 | 4.0e-129 | +0.93 |

**Radius 1, interior one-edit neighbours — `w°` loses everywhere** (the H2
condition). `w°` vs the best arm: NDC-cl 0.133 vs fact list 0.742; NDC-sub
0.209 vs bipartite path 0.742; WD66 0.049 vs fact list 0.390; WD100 0.145 vs
fact list 0.532. The certificate (0.20–0.55) also beats `w°` on every interior
stratum.

### P-C8-r2 — radius-2 stratum (18:00; `scripts/newpos/neardup_r2.py`, outputs `scratchpad/newpos/c8_r2_*.txt`, `neardup_r2_<collection>.json`)

Truth: non-isomorphic pairs not within radius 1 that are reached by two
down-edits, or that share a down-neighbour (delete on one side, insert on the
other, which covers relabelling or moving one fact). Pairs needing two
insertions with no common down-neighbour are not enumerated and count as
negatives for every arm. A pair is pendant when it has a path whose two steps
both change the constant inventory. Per query, radius-1 partners are removed
from the candidates. The hypothesis is the reviewer's, stated before the run;
no separate kill criterion was written in this log before running, and I
record that omission.

| collection (r2 pairs; pendant) | `w°` MRR all | runner-up all (p_Holm) | `w°` MRR pendant | runner-up pendant (p_Holm) |
|---|---|---|---|---|
| NDC-classes (17,887; 14,672) | **0.664** | bipartite path 0.583 (1.3e-8) | **0.689** | bipartite path 0.509 (1.5e-33) |
| NDC-substances (90,692; 37,552) | **0.745** | bipartite path 0.713 (**0.64, tie**) | **0.666** | degree-seq 0.486 (1.7e-42) |
| WD50K(66) (19,649; 16,278) | **0.762** | fact list 0.535 (9.0e-130) | **0.778** | fact list 0.531 (8.4e-143) |
| WD50K(100) (25,708; 14,390) | **0.715** | bipartite path 0.499 (2.9e-56) | **0.696** | bipartite path 0.475 (3.1e-58) |

**Reading.** The ranking generalises beyond the enumerable radius. At radius
2, `w°` is first on pendant pairs on all four collections, by 0.18–0.25 MRR.
Pooled over all two-edit pairs, it is first on all four and significant on
three; on NDC-substances it ties the bipartite edit path.

### Verdict on C8 (18:05) — the new positive experiment

**Near-neighbour retrieval of structural near-duplicates.** Under anonymization
a KB's versions and near-copies can only be found by structure. Using each
representation's distance, does a record's nearest neighbour lie one or two
single-fact edits away? The ground truth is exact and representation-free.
**Headline (stratified, as the reviewer requires):** when records differ by
pendant edits — statements or qualifiers added or removed together with their
values, which make up 56–90 % of the one-edit pairs — `w°` ranks the true
neighbour first far more often than every competitor on all four collections,
at radius 1 and at radius 2 (MRR 0.45–0.78 vs ≤ 0.53 for the best competitor;
Holm-corrected p < 1e-32 everywhere). When they differ by an interior edit, the
certificate, the fact list and the bipartite edit path rank better, as H2
predicts. The pooled kill on NDC-substances AP is reported. Mechanism:
name-freedom (Prop. C.6) + exactness at zero (Theorem C). It turns H2 from an
absolute movement against one competitor into a task against all ten.
**Status: POSITIVE — candidate for the main text** (deliverable:
`NEWPOS_2026-10-13/C8_NEAR_DUPLICATE_RETRIEVAL.md`).

### `genbench-ngram` final (27 seeds; verified 18:30, verdict ACCEPT)

Verification: 2 commits (`93e0190` code, `0824502` log) touching only its
ownership set; 89 tests re-run green in its worktree; ruff clean; tree clean.
Results `D/results/NEWPOS_2026-10-13/genbench_ngram/` (`tables.md`,
`stats.json`, `fig_rejection_bias.pdf`, 162 frozen sample files). It reproduces
RQ6 exactly on all 162 units.

| collection | baseline | HA1 rejection bias | HA2 relational fraction | HA3 yield (VUN / draw) |
|---|---|---|---|---|
| WD50K(66) | fact list | not supported | not supported | **supported** (`w°` 0.820 vs 0.065) |
| WD50K(66) | fact list + LCC | not supported | supported (repair drops stars to 0.32) | **supported** (0.820 vs 0.750, Holm 4.5e-8) |
| WD50K(66) | incidence | insufficient (u = 1) | insufficient | **supported** |
| NDC-classes | fact list | not supported | not supported | **supported** (0.684 vs 0.324) |
| NDC-classes | fact list + LCC | not supported | not supported | **not supported** (0.684 vs 0.687) |
| NDC-classes | incidence | insufficient (u = 17) | insufficient | **supported** |

Post-hoc and exploratory, in no Holm family: 15–19 % of `w°`'s usable samples
fall outside the collections' size window (mostly m < 3), against 1–6 % for the
fact list. Restricted to the window, `w°`'s NDC JSD_m falls from 0.125 to
0.025. **Reading: generation fidelity is NEGATIVE (supplement).** The yield
advantage is already in the paper's spirit (the joint rate); against a trivial
largest-component repair it holds on WD50K and ties on NDC. The guarantee
("no repair step") is the defensible claim, as the paper already states.

### `compression` final (four collections; verified 19:05, verdict ACCEPT)

Verification: 5 commits, with the pre-registration `9f9ef2d` committed before
the code `95cc9ef`; only its ownership set touched; 33 tests re-run green; ruff
clean; tree clean. Results `D/results/NEWPOS_2026-10-13/compression/`
(`tables.md`, `stats.json`, `fig_bits.pdf`, per-KB / compressor / delta CSVs;
`pilot/` superseded).

- **HB1 vs the certificate (5 granularities: bytes, 4-byte words, rows, plain
  integers, upper-triangle integers).** Median held-out order-3 n-gram bits/KB,
  WD66 / NDC-cl / WD100 / NDC-sub: `w°` **29.1 / 20.6 / 30.0 / 22.8**; best
  certificate rendering 57.1 / 25.3 / 69.2 / 54.1. xz bytes/KB: `w°` 6.5 / 3.3
  / 6.9 / 6.5 vs best certificate 10.5 / 5.2 / 11.3 / 10.7. `w°` wins on every
  coder and every granularity except one: the fixed-width code over the
  *theoretical* alphabet (`|Σ_HG(10)|` = 466,055 symbols with 4 types) against
  upper-triangle integers on NDC-classes (188 vs 125 bits). **Per the
  pre-registered rule: no unqualified headline.** The qualified statement
  holds: fewer bits than every certificate rendering under the learned code and
  the generic compressors, on all four collections.
- **HB2 vs the fact list and the incidence list: not convincing** (NDC 3-gram
  20.6 vs fact list 20.2). For m ≥ 13 on WD50K the walk has more tokens than
  rows or the fact list (median 51 vs 35).
- **HB3 version deltas.** `zstd --patch-from` bytes are smaller for `w°` than
  for every certificate form in both strata on both series (one cell n.s.;
  e.g. NDC-classes, all 528 pairs, median 21 vs 55 B). The certificate wins the
  constant-preserving edit distance on NDC-classes, as predicted. **The fact
  list has smaller deltas than `w°`.**
- **Length reconciliation (open item since 2026-09): median `w°` 6 (WD) / 9
  (NDC, with the root-type symbol) vs 12 certificate rows; mean 13.5 vs 40.0
  four-byte certificate words.** prose.md and T-KBx were both right — one
  compared medians against rows, the other means against 4-byte words.
- **Methodological catch by the agent.** The pre-registered with-replacement
  compressor bootstrap was biased 18–29 % low, because repeats compress for
  free. Final CIs use distinct drawn members, translated to the point estimate
  (documented in its log).

**Reading: compactness against the certificate is a qualified POSITIVE** (one
sentence plus a supplement table): "under a learned code and under generic
compressors, the word needs 1.2–2.4× fewer bits than the best rendering of the
certificate" (n-gram 1.23–2.37×; xz 1.58–1.65×). It is not a headline, and it is not a win against the fact list.

### `neural-gen` final (27 seeds; verified 19:20; uncapped sensitivity requested)

Verification: 5 commits, with the pre-registration `6845e65` committed before
the code `30bf26d`; only its ownership set touched; 30 tests re-run green in
`isalhg-newpos-gru`; ruff clean; tree clean; no samples or checkpoints in git.
Results `D/results/NEWPOS_2026-10-13/neural_gen/` (162 `.jsonl.gz`, `summary.md`,
`units.csv`, `stats.json`, `eval_full/`, `analysis_full/`,
`sensitivity_lr5e-4/`). `verify_samples.py`: 0 failing lines in 1.62 M.

| collection | arm | usable / draw | r = out-of-domain [95 % CI] | VUN / draw | test bits/KB |
|---|---|---|---|---|---|
| NDC-classes | **`w°`** | **1.000** | 0 | **0.408** | **17.5** (+1.64 root) |
| NDC-classes | fact list | 0.700 | 0.300 [0.275, 0.325] | 0.155 | 23.2 |
| NDC-classes | incidence | 0.607 | 0.393 [0.369, 0.423] | 0.148 | 26.3 |
| WD50K(66) | **`w°`** | **1.000** | 0 | **0.842** | **32.3** |
| WD50K(66) | fact list | 0.086 | 0.915 [0.905, 0.923] | 0.077 | 80.3 |
| WD50K(66) | incidence | 0.361 | 0.639 [0.627, 0.653] | 0.304 | 58.3 |

- **HC1 holds.** 540,000 of 540,000 GRU `w°` draws decode to connected KBs (76
  are the empty word, a single constant).
- **HC2 holds as registered.** 8 of 8 one-sided paired Wilcoxon tests reject,
  Holm p 6e-8 to 8e-6, `w°` higher in 27 of 27 seeds in every cell.
- **Amendment A1 outcome (a): the gap persists, but the baselines are no longer
  straw men.** The incidence list's usable rate rises from 0.0017 / 0.000085
  (n-gram) to 0.607 / 0.361. The fact list's connectivity rises on NDC (0.416 →
  0.700) and *falls* on WD50K (0.126 → 0.086), where it overfits a
  10,936-symbol role-aware alphabet.
- **Exploratory: the LCC repair of the GRU fact list beats `w°` on WD50K VUN
  (0.944 vs 0.842)** at a structural cost: its star fraction is 0.158 vs the
  collection's 0.534 (`w°` 0.543), and jsd_m is 0.058 vs 0.015. On NDC `w°`
  leads, 0.408 vs 0.357.
- The `w°` word also has the lowest held-out neural code length on both
  collections, which agrees with `compression`'s n-gram coder.
- The first sensitivity run (lr 5e-4) was capped at 60 epochs, so it does not
  settle undertraining on NDC. An uncapped symmetric run (max 200 epochs,
  3 seeds, all arms) was requested from the agent at 19:20.

**Reading: POSITIVE support for H4.** It answers "an n-gram is a toy": under an
identical neural model the guarantee is unchanged, and the baselines still leave
30–92 % of draws outside the domain. It is not a new headline — the claim stays
"guaranteed vs learned" — and the repaired fact list's VUN advantage on WD50K is
reported next to its structural distortion.

### Parked candidates (not yet run)

- **Z1 — cost table at N = 3,988 (zero compute).** RQ7 §8 already holds the
  full-matrix times: `w°` 1.39 s, certificate at parity, NetLSD 40.6 s,
  bipartite 10.6 min, WL 564 s, HPD censored, `w*_c` 28.9 min. A table instead
  of a sentence; caveat: the HPD/bipartite/WL implementations are Python, so
  this is not an algorithmic claim. Decision deferred to the writing plan (page
  budget).
- **D1 — augmentation by interpolation (Fable).** The only stored measurement
  is 20 WD50K pairs (`rows_alignment.csv`): fact-list alignment interiors are
  connected 59/86 = 0.686, and `w°` interiors 119/119. At scale, D1 would add
  type-conditional interpolation for under-populated Wikidata types, scored on
  usable fraction, novelty and type fidelity. Concern before running: its
  decisive column is again closure (a theorem), and the one non-tautological
  axis — whether an interior lies *between* its endpoints in fact space — could
  favour the fact list, since a single pointer-token edit can re-attach every
  later fact. Hold until the generation wave reports.
