# Results walkthrough — the TKDE campaign, question by question

*Status: DRAFT written 2026-09-06 06:30 CEST while RQ1 and RQ7 were still
completing on Picasso; RQ2–RQ6 are final. RQ1 and RQ7 sections are marked
provisional and will be finalised when their arrays and recovery sweeps land.
Every number below is copied from the persisted `tables.md` / `summary.json`
under the results root `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE/`
(mirrored from Picasso HOME); the reporting decisions with their numbers are in
`DECISIONS.md` there, and the main-text / supplement pointers in `article/` and
`supplementary/`. The pre-registered science is `DESIGN.md` (this folder).*

## 0. The questions, in one table

| RQ | The knowledge-base question | Property exposed | Verdict on the numbers | Main text carries |
|---|---|---|---|---|
| RQ1 | Which addressing makes similar knowledge bases close? | local stability of the fact-rank encoding; the addressing frontier | reproduction gate passes for `fact_rank` on all three corpora; the pointer arm's probe target was wrong (fixed, see §1) | the addressing frontier table (provisional) |
| RQ2 | Is "same knowledge base" well posed under each representation? | exactness of the complete word | **strong**: 0 false merges in 10.4 M non-isomorphic pairs; summaries merge 0.3–5.5 %; tractable GED readings are not metrics | the consequences table |
| RQ3 | Given N disagreeing descriptions of one thing, which is the reference? | the decoded consensus (a word operation no fingerprint can do) | **strong with a stated boundary**: exact recovery ≥ 0.98 on every insertion, mixed and single-deletion cell; medoids recover 0 / 4,457; the two-deletion regime is the boundary | Corpus A with the boundary; Corpus B to the supplement |
| RQ4 | Can corrupted records be screened? | exactness consequence (iso-twins) | **A′**: exactness consequence holds against the summaries; competitiveness on standard corruptions does not | iso-twin table + RQ2 census |
| RQ5 | Do entity types form patterns in the space? | geometry licences; task metric | **A′**: types are not a structural signal on WD50K (best ARI 0.09, floors lead); licences: ν = 0.10 holds, hubness fails | unsupervised exhibit (dendrogram, MDS) |
| RQ6 | Can a collection be extended with valid, plausible knowledge bases? | validity by theorem; the decoder is total | **strong**: 540,000 / 540,000 valid vs 98–99 % rejection for a flat serialization; 86 / 86 alignment interiors decode | validity, fidelity, decodability, completion |
| RQ7 | Where does the representation stop being computable? | the operating envelope | provisional: `fact_rank` clears every sweep cell up to m = 1,280 at k = 3 and completes 100 % of every real collection in < 1 ms; the pointer arm censors from ~13 facts | envelope table (provisional) |

The design's own summary line holds up: RQ3 and RQ6 make the *language* visible
and are the strongest results; RQ2 (and RQ4's surviving half) are where
*exactness* is visible; RQ5 is the honest task-metric row, and it is honest in
the negative direction; RQ7 bounds the claims.

## 1. RQ1 — addressing (provisional; 31 of 48 tasks harvested)

**Question.** Which way of addressing constants inside the word makes a single
knowledge-base edit a small string edit? Arms: the adopted `fact_rank` and three
alternative fact-alphabet addressings (`fact_degree_key`, `fact_local_key`,
`fact_local_colour`), the pointer alphabet of the sibling papers
(`isalhg_levenshtein`), and the nauty certificate as the reference.

**Reproduction gate (DESIGN §2).** The pipeline had to reproduce the September
probe: pooled normalised single-edit median of `fact_rank` within ±0.05 of
0.188 / 0.211 / 0.300 (synthetic / NDC classes / WD50K), and of the pointer arm
within ±0.05 of the probe's 0.500.

| collection | arm | probe target | measured | n | gate |
|---|---|---|---|---|---|
| synthetic_rq1 | fact_rank | 0.188 | 0.190 | 39,998 | pass |
| ndc_classes | fact_rank | 0.211 | 0.200 | 25,104 | pass |
| wd50k66 | fact_rank | 0.300 | 0.300 | 38,987 | pass |
| synthetic_rq1 | pointer | 0.500 → 0.577 (corrected) | 0.588 | 39,998 | pass after correction |
| ndc_classes | pointer | 0.500 → 0.577 (corrected) | 0.556 | 22,311 | pass after correction |
| wd50k66 | pointer | 0.500 → (being re-derived) | 0.500 | 36,464 | pending |

The pointer arm first read 0.60 against 0.50. DESIGN treats a gate discrepancy
as a bug until explained, and the explanation is on the probe's side: the probe
scored the pointer arm with `rapidfuzz` on raw token tuples, which compares
elements by hash, and the pointer-advance and pointer-retreat tokens
`TokenP(i)` / `TokenN(i)` hash-equal, so 67.3 % of the probe's pairs were
under-reported. Re-scoring the probe's own corpus with an equality-keyed
alphabet gives 0.577; the pipeline's alphabet was right all along
(regression-pinned; DESIGN §2 amended with the reason). A second, smaller
inconsistency was fixed at the same time: the distance was measured over the
seed-prefixed sequence but normalised by the bare word length; the analyzer now
divides by the length of the sequence it measures (`|w| + 1`). Rows are
unchanged; the corrected wd50k66 target is being re-derived the same way.

**What the arms show (M1, normalised single-edit response, lower is more
stable; Holm-corrected paired Wilcoxon against `fact_rank`).**

| collection | regime | fact_rank | degree_key | local_key | local_colour | pointer | nauty (reference) |
|---|---|---|---|---|---|---|---|
| ndc_classes | constant-set-preserving | 0.146 | 0.452 | 0.670 | 0.944 | 0.662 | 0.083 |
| ndc_classes | constant set changes | 0.362 | 0.530 | 0.645 | 0.989 | 0.598 | 0.237 |
| synthetic_rq1 | constant-set-preserving | 0.193 | 0.493 | 0.607 | 0.956 | 0.494 | 0.089 |
| synthetic_rq1 | constant set changes | 0.491 | 0.558 | 0.491 | 0.978 | 0.555 | 0.214 |
| wd50k66 | constant set changes | 0.374 | 0.471 | 0.555 | 0.939 | 0.397 | 0.247 |

Every alternative fact addressing responds more than `fact_rank` (rank-biserial
−0.32 to −1.00, all Holm-significant), and the pointer alphabet responds three
to four times more when the constant set is preserved. The nauty certificate
responds less per token only because its strings are 12–30 × longer (124–284
tokens vs 10–30, table M3); its Spearman correlation with `fact_rank` on the
same pairs is 0.75–0.77 (M4). Cost (M3): `fact_rank` canonicalises a record in
0.3–0.6 ms on every size stratum with 0 censoring; the pointer arm reaches
0.3 s medians with 21 % of records censored at 17–20 facts.

**Decision (provisional).** The selection is closed by design ("no scientific
fallback"); the addressing frontier goes to the main text as measured. Two
amendments are recorded for the PI: the corrected pointer target and the
normaliser.

## 2. RQ2 — well-posedness (final)

**Question.** Under each representation, when are two knowledge bases "the
same"? Exactness at zero, the false-merge census, metricity of the tractable
bipartite-GED readings, the exact-GED oracle ceiling, certificate validity, and
the cost of the identity.

**The measured consequences** (all non-isomorphic member pairs: 949,712 on
`ndc_classes`, 1,516,294 on `ndc_substances`, 7,949,355 on `wd50k66`):

| arm | isomorphic pairs at 0 | false merges (ndc_classes / ndc_substances / wd50k66) | classes found vs true (wd50k66) |
|---|---|---|---|
| `fact_rank` (ours) | 100 / 100 | 0 / 0 / 0 | 3,682 / 3,682 |
| `nauty_cert` | 100 / 100 | 0 / 0 / 0 | 3,682 |
| `wl_l1` | 100 / 100 | 0 / 0 / 0 | 3,682 |
| `hpd_jsd` | 100 / 100 | 0.80 % / 0.65 % / 2.67 % | 782 |
| `netlsd` | 100 / 100 | 0.26 % / < 0.001 % / 2.34 % | 1,492 |
| `degree_seq_l1` | 100 / 100 | 0.57 % / 0.09 % / 2.53 % | 1,179 |
| `size_l1` | 100 / 100 | 5.5 % / 2.2 % / 3.7 % | 194 |
| `bipartite_ged_assign` | 100 / 100 | 0.006 % / 0.09 % / 2.53 % | 1,179 |
| `bipartite_ged_path` | 37 / 37 / 10 of 100 | 0 (but splits classes: 3,839 vs 3,682) | — |

Metricity of the bipartite readings (2,000 pairs / 5,000 triples per
collection): the path reading violates identity of indiscernibles on 882 and
981 of 2,000 isomorphic pairs and the triangle inequality on 8 and 7 of 5,000
triples; the assignment reading returns a false zero on 36 of 2,000
non-isomorphic WD50K pairs. Certificate validity over RQ3's 4,457 collections:
the lower bound holds for every metric arm (0 invalid) and fails 6 times for the
path reading. Exact GED as an oracle costs a median 0.45–1.08 s per pair with a
p90 of 13 s at 9–10 facts (why it is a ceiling, not an arm); HyperCOT 0.085 s
per pair, gated to N ≤ 20. The identity itself: the `fact_rank` word costs
0.07–0.37 ms per member (100 % complete, 4,554 members on the full WD50K); the
pointer alphabet 3.5–5 ms with 6–12 % of members not finishing within budget.

**Decision.** Descriptive, no gate. The complete representations are exact and
the summaries are not; stated honestly, WL-1 is also exact on these labelled
collections, so exactness separates the complete arms from the summaries (HPD,
NetLSD, degree, size, bipartite-assign), not from WL.

## 3. RQ3 — the representative record (final)

**Question.** Given N variants of one knowledge base that disagree, return the
reference, with a guarantee. Ours: the coverage consensus (a *decoded* word,
`r = 2`) and the identity-reading majority merge; competitors: the medoid under
every distance (a medoid can only return an input).

**Corpus A — planted variants** (2 collections × 12 cells × 216 collections;
insertion / deletion / mixed edits at budgets t ∈ {1, 2}, N ∈ {5, 9}):

| kind | t | exact recovery, coverage consensus (Wilson 95 %) | majority merge | any medoid |
|---|---|---|---|---|
| insertion | 1 | 0.991–1.000 | 1.000 | 0 of 4,457 |
| insertion | 2 | 1.000 | 0.995–1.000 | 0 |
| mixed | 1 | 0.991–0.995 | 1.000 | 0 |
| mixed | 2 | 0.866–0.972 | 0.704–0.940 | 0 |
| deletion | 1 | 0.979–1.000 | 1.000 | 0 |
| deletion | 2 | **0.231 (ndc, N = 5), 0.370 (wd50k66, N = 5), 0.810 (wd50k66, N = 9)** | 0.208 / 0.300 / 0.950 | 0 |

H3a holds for insertions (min 0.991 ≥ 0.95) and mixed edits (min 0.866 ≥ 0.80)
and fails for deletions at budget 2. The failure is a property of the
information the variants carry, not of the string method: the identity-reading
merge falls in the same cells, recovery rises with the source size (0.23 at
m = 6 to 0.90 at m = 10 with N = 9), and ties are rare (median 0, max 3). When
the consensus misses, it lands at fact distance 2 in 311 of 326 misses. Every
medoid is at distance ≥ t by construction (H3b: 1.000 of rows); pooled fact
distance to the source is 0.18–0.20 for the consensus against 1.50–1.54 for
every medoid (Holm-significant on both collections). The certified medoid ratio
bound `2 − 2/N` holds on all 4,457 medoids (max 1.778; the cosmetic 1.7 target
is dropped).

**Corpus B — the natural NDC quarter series** (69 runs): the consensus is *worse*
than the medoids and than the majority merge on the held-out quarter (fact
distance 2.60 vs 1.84–2.40; exact recovery 0.145 vs up to 0.226). A natural
series is not a set of variants of one source, so there is nothing for a
consensus to converge to. This is the pre-registered fallback: Corpus B goes to
the supplement as the characterised weak regime; Corpus A carries the main text
with the boundary stated.

## 4. RQ4 — the screen (final; HPD refill pending)

**Question.** Can a corrupted record be screened out by its distance to the
collection? kNN (k = 5) and LOF (k = 20) anomaly scores, 5 % contamination, four
corruptions (spurious fact, missing fact, wrong argument, and the
isomorphism-breaking *iso-twin*), 7 sub-collections × 27 seeds.

**H4a — the exactness consequence.** On `ndc_classes` (structural repetition)
the summaries cannot see the twin — `hpd_jsd` 0.512, `degree_seq_l1` 0.516,
`size_l1` 0.501 (chance) — while `fact_rank` 0.764 [0.758, 0.770] and
`nauty_cert` 0.717 detect it. Two honest qualifications: `wl_l1` detects it too
(0.805), and on the WD50K type sub-collections degree and NetLSD match or beat
`fact_rank`, because only 19.1 % of the realised twins are WL-1-indistinguishable
(the others leave degree-level traces).

**H4b — competitiveness on standard corruptions: fails.** `fact_rank` is below
the best competitor in 39 of 42 cells and inside the best competitor's interval
in 1 of 49 cells overall (mean AUC ours vs best: spurious 0.68 vs 0.84, missing
0.44 vs 0.64, wrong-argument 0.57 vs 0.81). Missing facts score *below* chance:
a shortened record looks more typical under a kNN score in a complete,
non-collapsing space whose k = 10 hubness skewness is 5.4 (RQ5).

**Decision (pre-registered fallback).** The main text carries the exactness
consequence — summaries at chance on twins, complete arms not — read with RQ2's
census, with the WL boundary stated; the AUC tables on standard corruptions go
to the supplement with the explanation. 266 HPD cells (missing fact, budget 2)
were censored because the vendored HPD code crashed on 3-fact records; the
library is fixed (portraits of all 15,505 pristine members byte-identical) and
the re-score is being submitted through a private environment.

## 5. RQ5 — patterns (final)

**Question.** Do Wikidata entity types form recoverable clusters in the space,
and which geometric licences hold? k-medoids (PAM) and agglomerative clustering
against 14 types on `wd50k66` (balanced 14 × 20, 27 seeds; full 3,492 members;
`wd50k100` control), plus the geometry table.

**Licences (H5a).** Non-Euclidean mass ν(`fact_rank`) = 0.101 with 1,553
negative Gram eigenvalues: PAM and metric MDS are licensed over centroid methods
and classical MDS. Hubness is *not* moderate: k = 10 skewness 5.41 against the
1.5 ceiling (HPD and NetLSD are effectively Euclidean, ν ≈ 0; WL has one hub of
occurrence 3,464).

**Task metric (H5b–H5d): all fail.** Balanced ARI of `fact_rank` is 0.010
(agglomerative) / 0.042 (PAM) against the naive floors `size_l1` 0.038 / 0.041
and `degree_seq_l1` 0.025 / 0.053 (0 of 4 floor comparisons won, 3 lost
Holm-significantly); the best competitor, `hpd_jsd`, reaches 0.064; no arm
exceeds ARI 0.093 or NMI 0.27; roles lower ARI marginally (0.040 vs 0.042,
p_Holm 0.032). On the full design every arm is ≤ 0.017.

**Decision (pre-registered fallback).** Entity type on WD50K is not a
structural signal; what little there is, is a size/degree signal that a complete
representation deliberately does not collapse. The main text carries the
unsupervised exhibit — the `fact_rank` dendrogram (cophenetic correlation
0.92–0.93) and the metric-MDS map, licensed by ν — and states the licence
result including the failed hubness clause (which is why RQ4's kNN readings are
qualified). The ARI tables, floors and per-class table go to the supplement.
This is the one RQ with no task-metric claim in the main text; flagged for the
PI.

## 6. RQ6 — generation (final)

**Question.** Can a collection be extended with new, valid, plausible knowledge
bases? An order-3 token n-gram over `fact_rank` words vs the same model over a
flat incidence serialization with a strict decoder; 27 seeds × 10,000 samples on
`wd50k66` and `ndc_classes`.

| claim | measured |
|---|---|
| validity by theorem (H6a) | 540,000 / 540,000 samples decode; the flat baseline is rejected on 98.10 % (NDC) and 98.98 % (WD50K) of samples, mostly out-of-range constant ids and type-count violations |
| fidelity (H6b) | JSD to the collection's histograms: size 0.07 / 0.21, facts 0.05 / 0.07, arity < 0.001, predicate ≤ 0.002, type ≤ 0.006; novelty 0.99 / 0.94; within reach 1 of a member 4.7 % / 9.6 %; closer than the baseline's accepted 1–2 % on facts, arity and predicates (Holm p ≤ 1e-7), the baseline's survivors closer on size |
| decodability (H6c) | 86 / 86 interior words of 20 real-pair alignment paths decode (fact alphabet, 68.6 % connected; pointer alphabet 100 % connected) |
| conditional completion | 300 / 300 valid; isomorphic to the original 68.3 % (NDC) / 14.0 % (WD50K); within reach 1 75.3 % / 21.0 % |

**Decision.** Everything to the main text; the WD50K size-histogram divergence,
the connectedness of fact-alphabet interiors and the rejection-cause table to
the supplement. (An operational finding on the way: the n-gram's per-context
memo was unbounded and grew 2.7 GB per unit; the library is now LRU-bounded
with bit-identical samples.)

## 7. RQ7 — the envelope (provisional; 66 of 74 tasks harvested)

**Question.** Where does the representation stop being computable? A synthetic
sweep over facts m, arity k, alphabet sizes and density with a process-level
time budget; yield on the real collections by size; N-scaling of the pairwise
matrices.

| arm | largest m cleared with no time-out, by k (2 / 3 / 4 / 5) |
|---|---|
| `fact_rank` | 160 / 1,280 / 160 / 160 (sweep ceiling per k; 0 time-outs so far) |
| `nauty_cert` | 160 / 1,280 / 160 / 160 |
| pointer alphabet | 160 / 160 / 40 / 40 |

Yield on real collections: `fact_rank` completes every member of every
collection (medians 0.25–0.8 ms, all buckets up to > 24 facts); the pointer
alphabet completes 57 of 176 WD50K members with 21–24 facts (median 5.2 s, p90
35 s) and 19 of 85 on `wd50k100`. N-scaling: the bipartite-GED assignment
reading needs 525 s for the 3,988 × 3,988 WD50K matrix; the `fact_rank` matrix
is dominated by 0.3 ms canonicalisations.

**Decision (provisional).** Descriptive; the envelope table goes to the main
text once the last sweep cells land.

## 8. Campaign provenance

| RQ | job(s) | outcome |
|---|---|---|
| matrices | 2213202 | 26 cached N × N matrices, 33:50, MaxRSS 34.2 GB |
| RQ3 + RQ6 | 2213221 (OOM at 24 G after RQ3 completed) → 2215096 (64 G) | COMPLETED |
| RQ2 | 2215097 (main, 13 tasks; task 9 OOM at teardown after its last unit was written), 2215136 (census) | COMPLETED |
| RQ4 | 2215163 (FAILED on the HPD crash) → 2215168 | COMPLETED; HPD refill in flight |
| RQ5 | 2215162 | COMPLETED |
| RQ7 | 2215078 (+ sweep 2215079) | running |
| RQ1 | 2215137 (+ sweep 2215161) | running |

Code: everything is on `integration/2026-09-05-tkde-w1` (waves 1–3 merged;
2,056 unit and property tests pass; ruff and mypy findings are the pre-existing
ones in untouched files). `main` is untouched pending your approval to merge.

## 9. Open items for the PI

1. Approve the two RQ1 amendments (pointer gate target from the corrected probe;
   seed-consistent normaliser).
2. RQ5 has no task-metric claim in the main text; confirm the unsupervised
   exhibit as its main-text content.
3. RQ4: whether to add the WL-1-equal-twin subset AUC as a supplementary
   analysis (the flag is persisted per anomaly).
4. The untagged smoke files from the first cluster smokes sit in the real RQ1 /
   RQ2 / RQ7 folders on HOME and on the drive (`rows_*__<name>-000of001.csv`
   without a run tag); the analyzers skip them; moving them was blocked for the
   agent that tried, so it is your call.
5. Merge `integration/2026-09-05-tkde-w1` into `main`.
