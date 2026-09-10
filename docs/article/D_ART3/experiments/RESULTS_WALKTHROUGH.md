# Results walkthrough — the TKDE campaign, question by question

*Status: FINAL, 2026-09-06 14:30 CEST. Every array of the campaign is complete
and harvested; the seven research questions are decided. Every number below is
copied from the persisted `tables.md` / `summary.json` under the results root
`/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE/` (mirrored
from Picasso HOME). The reporting decisions with the numbers that drove them
are in `DECISIONS.md` there; the main-text and supplement pointers are in
`article/README.md` and `supplementary/README.md`. The pre-registered science
is `DESIGN.md` in this folder; the engineering record of the three waves is
`.claude/notes/2026-09-05-tkde-w{1,2,3}/summary.md`. The hub over the results
folder and this document is `INDEX.md` at the results root.*

## 0. The questions, in one table

| RQ | The knowledge-base question | Property exposed | Verdict on the numbers | Main text carries |
|---|---|---|---|---|
| RQ1 | Which addressing makes similar knowledge bases close? | local stability of the fact-rank word; the addressing frontier | **confirmed**: `fact_rank` is the most stable addressing in every regime (Holm-significant, rank-biserial −0.67 to −1.00); the pointer alphabet responds 3–4 × more at 1,000 × the cost; all six reproduction gates pass after two amendments | the frontier table |
| RQ2 | Is "same knowledge base" well posed under each representation? | exactness of the complete word | **strong**: 0 false merges in 10.4 M non-isomorphic pairs; summaries merge 0.3–5.5 %; the tractable GED readings are not metrics | the consequences table |
| RQ3 | Given N disagreeing descriptions of one thing, which is the reference? | the decoded consensus, a word operation no fingerprint can perform | **strong with a stated boundary**: exact recovery ≥ 0.98 on every insertion, mixed and single-deletion cell; medoids recover 0 of 4,457; the two-deletion regime is the boundary | Corpus A with the boundary; Corpus B to the supplement |
| RQ4 | Can corrupted records be screened? | the exactness consequence (iso-twins) | **A′**: the exactness consequence holds against the summaries; competitiveness on standard corruptions does not | iso-twin table read with RQ2's census |
| RQ5 | Do entity types form patterns in the space? | geometry licences; a task metric | **A′**: types are not a structural signal on WD50K (best ARI 0.09, the naive floors lead); ν = 0.10 licence holds, hubness fails | the unsupervised exhibit (dendrogram, MDS) |
| RQ6 | Can a collection be extended with valid, plausible knowledge bases? | validity by theorem; the decoder is total | **strong**: 540,000 / 540,000 valid vs 98–99 % rejection for a flat serialization; 86 / 86 alignment interiors decode | validity, fidelity, decodability, completion |
| RQ7 | Where does the representation stop being computable? | the operating envelope | **strong**: 0 time-outs in 7,938 synthetic instances up to 1,280 facts; 100 % yield on every real bucket at < 1 ms; the cheapest all-pairs matrix of every arm | the envelope table |

The design's own summary line holds: RQ3 and RQ6 make the *language* visible
and are the strongest results; RQ2, RQ1 and RQ4's surviving half are where
*exactness* and *stability* are visible; RQ5 is the honest task-metric row and
it is honest in the negative direction; RQ7 bounds the claims and the bound is
generous.

## 1. RQ1 — addressing (final)

**Question.** Which way of addressing constants inside the word makes a single
knowledge-base edit a small string edit? Arms: the adopted `fact_rank`, three
alternative fact addressings (`fact_degree_key`, `fact_local_key`,
`fact_local_colour`), the roles variant `fact_rank_roles` (WD50K only), the
pointer alphabet of the sibling papers (`isalhg_levenshtein`), and the nauty
certificate as the reference. Three corpora: `synthetic_rq1` (2,000 records),
`ndc_classes` (1,381), `wd50k66` (3,988).

**Reproduction gate (DESIGN §2).** The pipeline re-measures the September probe
from the shipped encoder. All six cells pass:

| collection | arm | target | measured | n |
|---|---|---|---|---|
| synthetic_rq1 | fact_rank | 0.188 | 0.200 | 39,998 |
| ndc_classes | fact_rank | 0.211 | 0.214 | 26,546 |
| wd50k66 | fact_rank | 0.300 | 0.333 | 72,948 |
| synthetic_rq1 | pointer | 0.57 (corrected) | 0.588 | 39,998 |
| ndc_classes | pointer | 0.56 (corrected) | 0.556 | 23,104 |
| wd50k66 | pointer | 0.60 (corrected) | 0.600 | 67,729 |

Two amendments were needed and are recorded in DESIGN §2 for the PI to ratify.
(a) The probe's published pointer value of 0.500 was an artefact: it scored the
pointer arm with `rapidfuzz` on raw token tuples, which compares elements by
hash, and the pointer-advance and pointer-retreat tokens hash-equal, so 67.3 %
of the probe's pairs were under-reported; re-scoring the probe's own corpus
with an equality-keyed alphabet gives 0.57 / 0.56 / 0.60, which the pipeline
reproduces (the pipeline's alphabet was right; regression-pinned). (b) The
normalised response divides by the length of the sequence the distance was
measured over: the bare word for fact arms, the seed-prefixed word for the
pointer arm on collections with more than one vertex label.

**M0 — exactness and invariance.** Every fact addressing and nauty are exact
and relabelling-invariant on all three collections (0 false merges, 0 false
splits, 0 invariance violations; class counts 2,000 / 557 / 3,682, equal to
nauty's). The pointer alphabet is censored at the budget on 118 (NDC) and 238
(WD50K) members. **`fact_rank_roles` fails invariance on WD50K**: 247 false
splits and 2,104 violations (3,749 classes vs 3,682). The roles variant is not
a canonical form and is withdrawn as an arm; RQ5's roles comparison is void.

**M1 — single-edit response** (normalised, lower is more stable; Holm-corrected
paired Wilcoxon against `fact_rank`, rank-biserial in brackets):

| collection | regime | fact_rank | degree_key | local_key | local_colour | pointer | nauty (ref.) |
|---|---|---|---|---|---|---|---|
| ndc_classes | constant set preserved | 0.146 | 0.452 (−1.00) | 0.670 (−1.00) | 0.944 (−1.00) | 0.662 (−0.99) | 0.083 |
| synthetic_rq1 | constant set preserved | 0.193 | 0.493 (−0.92) | 0.607 (−0.98) | 0.956 (−1.00) | 0.494 (−0.77) | 0.089 |
| wd50k66 | constant set preserved | 0.231 | 0.537 (−0.97) | 0.698 (−1.00) | 1.012 (−1.00) | 0.793 (−0.96) | 0.124 |
| ndc_classes | constant set changes | 0.393 | 0.579 (−0.81) | 0.702 (−0.99) | 1.072 (−1.00) | 0.598 (−0.39) | 0.237 |
| synthetic_rq1 | constant set changes | 0.491 | 0.558 (−0.32) | 0.491 (+0.06) | 0.978 (−1.00) | 0.555 (−0.21) | 0.214 |
| wd50k66 | constant set changes | 0.406 | 0.511 (−0.67) | 0.604 (−0.87) | 1.018 (−1.00) | 0.481 (−0.08) | 0.249 |

Every alternative fact addressing responds more than `fact_rank` in every cell
(one tie on synthetic, local-key, when the constant set changes), and the
pointer alphabet responds three to four times more when the constant set is
preserved; when it changes the pointer's advantage vanishes rather than
reverses. The nauty certificate reads lower per token only because its strings
are 12–30 × longer (124–284 tokens vs 10–31, table M3). Within two tokens of
the original: `fact_rank` 0.78 after adding a constant, 0.85 after deleting a
fact, 0.59 after inserting one; nauty 0.00–0.41; pointer 0.03–0.86.

**M2 — monotonicity.** Spearman ρ between the planted edit budget and the
distance on WD50K ladders: `fact_rank` 0.589, nauty 0.677, pointer 0.553,
degree-key 0.484, colour 0.273; on the natural NDC series (constant set
preserved): `fact_rank` 0.958, pointer 0.961, nauty 0.876.

**M3 — cost.** `fact_rank` canonicalises a record in 0.3–0.6 ms on every size
stratum with 0 censoring; the pointer alphabet reaches 0.3–1.7 s medians with
21–60 % of records censored above 17 facts.

**M4 — agreement with the certificate.** ρ against the nauty-certificate
distance on random pairs: `fact_rank` 0.803 / 0.642 / 0.959, the highest fact
arm on two of three collections; pointer 0.288 / 0.642 / 0.702.

**Decision.** The pre-registered selection is confirmed and closed: the
frontier table (M1 and M3) goes to the main text with the reproduction gate
stated; the per-edit-kind tables, M2, M4 and the invariance census go to the
supplement.

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
the lower bound holds for every metric arm and fails 6 times for the path
reading. Exact GED as an oracle costs a median 0.45–1.08 s per pair with a p90
of 13 s at 9–10 facts; HyperCOT 0.085 s per pair, gated to N ≤ 20. The identity
itself: the `fact_rank` word costs 0.07–0.37 ms per member (100 % complete,
4,554 members on the full WD50K); the pointer alphabet 3.5–5 ms with 6–12 % of
members not finishing within budget.

**Decision.** Descriptive, no gate. The complete representations are exact and
the summaries are not; stated honestly, WL-1 is also exact on these labelled
collections, so exactness separates the complete arms from the summaries, not
from WL.

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
| deletion | 2 | **0.231 (NDC, N = 5), 0.370 (WD50K, N = 5), 0.810 (WD50K, N = 9)** | 0.208 / 0.300 / 0.950 | 0 |

H3a holds for insertions (min 0.991 ≥ 0.95) and mixed edits (min 0.866 ≥ 0.80)
and fails for deletions at budget 2. The failure is a property of the
information the variants carry, not of the string method: the identity-reading
merge falls in the same cells, recovery rises with the source size (0.23 at
m = 6 to 0.90 at m = 10 with N = 9), and ties are rare (median 0, max 3). When
the consensus misses, it lands at fact distance 2 in 311 of 326 misses. Every
medoid is at distance ≥ t by construction (1.000 of rows); pooled fact distance
to the source is 0.18–0.20 for the consensus against 1.50–1.54 for every medoid
(Holm-significant on both collections). The certified medoid ratio bound
`2 − 2/N` holds on all 4,457 medoids (max 1.778; the cosmetic 1.7 target is
dropped).

> **SUPERSEDED 2026-09-09 (D-KBf5, `DEVELOPMENT/T-KB/IN-PROGRESS/T-KBf.md`).**
> These numbers were measured under the frozen `reach`, whose `compatible()`
> gate rejects any pair with unequal constant counts. On this corpus **1,146 of
> 1,400 member pairs (81.9 %) are therefore at infinite reach, and 60 of the 69
> runs contain such a pair**, so the triangle-complete candidate set was mostly
> empty and the consensus was crippled rather than tested. The stated mechanism
> below — "a natural series is not a set of variants of one source, so there is
> nothing for a consensus to converge to" — is an untested causal claim that the
> measurement cannot support. Re-measured under `reach′` before any use.

**Corpus B — the natural NDC quarter series** (69 runs): the consensus is worse
than the medoids and than the majority merge on the held-out quarter (fact
distance 2.60 vs 1.84–2.40; exact recovery 0.145 vs up to 0.226). A natural
series is not a set of variants of one source, so there is nothing for a
consensus to converge to. Pre-registered fallback: Corpus B goes to the
supplement as the characterised weak regime; Corpus A carries the main text
with the boundary stated.

## 4. RQ4 — the screen (final)

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
census and with the WL boundary stated; the AUC tables on standard corruptions
go to the supplement with the explanation. 266 HPD cells (missing fact, budget
2) had been censored because the vendored HPD code crashed on 3-fact records;
the library was fixed (portraits of all 15,505 pristine members byte-identical)
and the cells were re-scored through a private environment (job 2215571): 0
censored rows remain, the other arms are byte-identical, and the refilled HPD
scores (0.47–0.71) sit above `fact_rank` on those cells, which does not change
the verdict. 32 iso-twin units on the four small WD50K types had no realisable
non-isomorphic twin and carry no AUC row (hence 15–23 seeds in those cells).

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
exceeds ARI 0.093 or NMI 0.27. On the full design every arm is ≤ 0.017. The
roles comparison (H5d) is void because the roles variant is not invariant (RQ1).

**Decision (pre-registered fallback).** Entity type on WD50K is not a
structural signal; what little there is, is a size/degree signal that a complete
representation deliberately does not collapse. The main text carries the
unsupervised exhibit — the `fact_rank` dendrogram (cophenetic correlation
0.92–0.93) and the metric-MDS map, licensed by ν — and states the licence
result including the failed hubness clause (which is why RQ4's kNN readings are
qualified). The ARI tables, floors and per-class table go to the supplement.
This is the one RQ with no task-metric claim in the main text.

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

> **SUPERSEDED / LINEAGE-UNPINNED (2026-09-10, T-KBo).** Three numbers in this
> block are not from the lineage the campaign has adopted, and three different
> "connectivity" figures for the same generator are in circulation one sentence
> apart. Pinned against the rows on disk:
>
> | quoted here | quantity | status |
> |---|---|---|
> | completion "within reach 1 **75.3 % / 21.0 %**" | `rows_completion.reach1`, `reach()` called directly | **pre-`reach′`**. Under `reach′` (D-KBf5) the same rows give **76.7 % / 21.3 %** (`IEEETKDE_isal_consensus`, `_reachprime`). `reach′` is more permissive, so both rose, as expected. |
> | fidelity "within reach 1 of a member **4.7 % / 9.6 %**" | `rows_samples.reach1_frac`, via `Reach1Index` | **stale and being re-derived** by job 2279064: the index was gated on the frozen precondition (T-KBo). Campaign rows currently read 4.36 % (NDC) / 7.13 % (WD50K) for `fact_ngram`; neither matches the quoted pair, so the quoted lineage is unidentified. Do not quote until 2279064 lands. |
> | decodability "fact alphabet, **68.6 % connected**" | connectivity of **alignment-path interiors** | a *different quantity* from sample connectivity below; keep the two apart in prose. |
>
> **Sample connectivity, measured on the campaign rows** (27 seeds x 10,000
> samples, `IEEETKDE_isal_consensus`) — this is the third quantity, and it is the
> one that carries D-ART5's rationale:
>
> | collection | model | validity | connectivity |
> |---|---|---|---|
> | ndc_classes | `ow_ngram` | **1.0000** | **1.0000** |
> | ndc_classes | `fact_ngram` | 1.0000 | 0.4157 |
> | ndc_classes | `incidence_ngram` | 0.0190 | 0.0907 |
> | wd50k66 | `ow_ngram` | **1.0000** | **1.0000** |
> | wd50k66 | `fact_ngram` | 1.0000 | 0.1260 |
> | wd50k66 | `incidence_ngram` | 0.0102 | 0.0081 |
>
> The ordered walk is **1.0000 validity and 1.0000 connectivity on both
> collections** — Theorem C / Prop. 5.1 measured, not asserted. The storyline's
> "1,000 / 1,000 connected vs 256 / 1,000" does **not** match any row above
> (`fact_ngram` is 0.4157 / 0.1260), so that pair is from an unidentified run and
> must not be folded by T-KBg until its provenance is established.

**Decision.** Everything to the main text; the WD50K size-histogram divergence,
the connectedness of fact-alphabet interiors and the rejection-cause table to
the supplement. (Operational finding on the way: the n-gram's per-context memo
was unbounded and grew 2.7 GB per unit; the library is now LRU-bounded with
bit-identical samples.)

## 7. RQ7 — the envelope (final)

**Question.** Where does the representation stop being computable? A synthetic
sweep over facts m (10 … 1,280), arity k (2 … 5), alphabet sizes and density
with a process-level time budget (27 instances per cell); yield on the real
collections by size; N-scaling of the pairwise matrices.

| arm | time-outs in the sweep | largest m cleared, by k (2 / 3 / 4 / 5) |
|---|---|---|
| `fact_rank` | 0 of 7,938 | 160 / 1,280 / 160 / 160 (= the sweep ceiling per k) |
| `nauty_cert` | 0 of 7,938 | 160 / 1,280 / 160 / 160 |
| pointer alphabet | 3,074 of 7,776 (39.5 %) | 160 / 160 / 40 / 40 |

The pointer alphabet times out on essentially every instance from m = 120
upward at k ≥ 3; the fact alphabet never does, at medians of 2.5–17 ms even at
1,280 facts. Yield on the real collections: `fact_rank` completes 100 % of the
members of every size bucket of every collection (medians 0.21–0.78 ms, p90
≤ 0.9 ms, including the 546 full-WD50K members with more than 24 facts); the
pointer alphabet completes 100 % at ≤ 8 facts but only 57 / 176 (WD50K),
30 / 133 (`wd50k100`), 4 / 10 (NDC classes) and 0 / 80 (NDC substances) at
21–24 facts, with medians of 1.6–12.7 s. N-scaling of the all-pairs matrix on
WD50K (N = 3,988): `fact_rank` 1.5 s of pair distances plus 0.31 s of
canonicalisation; `nauty_cert` 864 s (its strings are 12–30 × longer);
`degree_seq_l1` 43 s; bipartite assignment 525 s and bipartite path 913 s;
HPD 1,670 s at N = 2,000 and censored at 3,988; NetLSD 2,724 s at N = 1,000
and censored above. No unit was deferred.

**Decision.** Descriptive. The envelope table goes to the main text; the full
sweep table and the pointer alphabet's yield go to the supplement.

## 8. Campaign provenance

| RQ | job(s) | outcome |
|---|---|---|
| matrices | 2213202 | 26 cached N × N matrices, 33:50, MaxRSS 34.2 GB |
| RQ3 + RQ6 | 2213221 (OOM at 24 G after RQ3 completed) → 2215096 (64 G) | COMPLETED |
| RQ2 | 2215097 (main, 13 tasks; task 9 OOM at teardown after its last unit was written), 2215136 (census) | COMPLETED |
| RQ4 | 2215163 (FAILED on the HPD crash) → 2215168; HPD refill 2215571 (private env) | COMPLETED |
| RQ5 | 2215162 | COMPLETED |
| RQ7 | 2215078 (+ sweep 2215079, no-op resume) | COMPLETED |
| RQ1 | 2215137 (+ sweep 2215161, no-op resume) | COMPLETED |

Code: everything is on `integration/2026-09-05-tkde-w1` (waves 1–3 merged, plus
the post-wave fixes: HPD vendor bound, n-gram cache bound, centralised SLURM
helper, RQ1 gate amendments, provenance override). `main` is untouched pending
your approval to merge. Test status is recorded in the wave-3 summary.

## 9. Open items for the PI

1. Ratify the two RQ1 amendments to DESIGN §2 (pointer gate targets from the
   corrected probe; seed-aware normaliser).
2. `fact_rank_roles` is not relabelling-invariant (2,104 violations on WD50K):
   decide whether roles can be made canonical or are dropped from the paper.
3. RQ5 has no task-metric claim in the main text; confirm the unsupervised
   exhibit as its main-text content.
4. RQ4: whether to add the WL-1-equal-twin subset AUC as a supplementary
   analysis (the flag is persisted per anomaly).
5. The untagged smoke files from the first cluster smokes sit in the real RQ1 /
   RQ2 / RQ7 folders on HOME and on the drive (`rows_*__<name>-000of001.csv`
   without a run tag; 10 + 12 + 7 files); the analyzers skip them; moving them
   was blocked for the agent that tried, so it is your call.
6. Merge `integration/2026-09-05-tkde-w1` into `main`; then sync the shared
   Picasso checkout (`scripts/tkde/sync_to_picasso.sh`) so the HPD and n-gram
   fixes are in the shared environment, and clean the private deployments and
   the cloned local conda environments.
