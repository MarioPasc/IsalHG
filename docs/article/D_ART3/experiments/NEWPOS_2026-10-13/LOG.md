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
