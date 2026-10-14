# Audit of the TKDE campaign — design, results, and what may go to the main text

*Written 2026-09-06 against the results root
`/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE/` (head
`c3b5c68`, all seven arrays harvested), `DESIGN.md` (pre-registered
2026-09-05 12:57, git `7590df4`, before any campaign row existed),
`RESULTS_WALKTHROUGH.md`, `DECISIONS.md`, and `prose.md`. Every number quoted
below was re-read from the persisted `tables.md` files, or produced by a probe
named in §6. The reader is the first author and the PI.*

---

## 0. Verdict in one screen

1. **The design is sound and defensible at TKDE.** It is pre-registered (git
   history proves the hypotheses, arms, corpora, statistics and the A → A′
   fallbacks were fixed before results existed), it runs on two real
   collections with the community's own baselines and two mandatory naive
   floors, and each research question has one evaluation axis. The reporting
   rule the author wants — positives in the main text, negatives in the
   supplement as characterised limitations — is exactly what the design
   pre-committed to, so it is not post-hoc selection *provided the main text
   says which hypotheses failed and points to the supplement*.
2. **Two experiments failed their primary hypothesis** and the pre-registered
   fallback applies: RQ4 (screening is not competitive on standard
   corruptions: below the best competitor in 39 of 42 cells) and RQ5 (entity
   types are not recoverable by any representation: every ARI ≤ 0.09, the
   naive floors lead). Both are honest limitations, not defects, and both are
   already routed to the supplement. Neither threatens the paper if the main
   text states them in one sentence each.
3. **One main-text claim is currently wrong as worded and must be corrected
   before drafting.** The RQ3 deletion boundary (recovery 0.23–0.81 at two
   deletions per variant) is explained in the walkthrough and in
   `DECISIONS.md` as "the information is gone from the collection". It is not.
   We re-ran the frozen consensus on the same cells: the source is in the
   candidate set in **108 of 108** collections, the plain union of the variants
   equals the source in **108 of 108**, and the consensus loses because the
   frozen objective's second criterion (minimum summed reach) prefers a strict
   sub-record of the source, or because the lexicographic word tie-break
   picks against it. This is a property of the objective, not of the data. It
   remains a true boundary, but the mechanism sentence has to change (§3.3).
4. **The walkthrough carries stale numbers in RQ1 and small over-statements in
   RQ5 and RQ7** (§2). None changes a conclusion; all must be regenerated
   from the persisted tables before a sentence is drafted from them.
5. **Two structural weaknesses a TKDE reviewer will find**, neither fatal,
   both addressable now: (a) the adopted word is, in substance, a nauty
   canonical labelling serialised as a fact list, so every "strong" result
   that is not RQ3 or RQ6 is inherited from nauty plus the tokenisation, and
   the paper must say so and rest its distinctiveness on the language
   operations (the design already anticipates this in its risk register); (b)
   the roles variant is not a canonical form (2,104 invariance violations),
   so the whole campaign ran on *undirected* facts — a knowledge base in
   which `born_in(A, B)` and `born_in(B, A)` coincide. That is a fidelity
   limitation the paper must state, or fix (§5).

---

## 1. Is the experimental design correctly planned?

### 1.1 What is right

- **Pre-registration is real.** `DESIGN.md` was committed on 2026-09-05 at
  12:57, the first campaign rows were written that evening, and the two
  amendments dated 2026-09-06 (RQ1 pointer gate targets, seed-aware
  normaliser) are recorded in place with their cause. Every A → A′ fallback
  that was later invoked (RQ3 Corpus B, RQ4, RQ5) is spelled out in the
  pre-registered text with its trigger condition. This is the strongest
  methodological asset of the campaign and should be stated in the paper's
  reproducibility paragraph.
- **One question, one axis.** Each RQ is introduced by the knowledge
  engineer's question, exposes one property of the representation, and is
  scored on one metric. No secondary axes are used to rescue a result.
- **Real collections, community baselines, mandatory floors.** WD50K(66)
  entity knowledge bases and the NDC-classes quarterly series; the exact
  edit-distance oracle, bipartite GED in both readings, WL, NetLSD, HPD,
  HyperCOT (gated), the nauty certificate as the "certificate member" of our
  own family, and the two naive floors (size, degree sequence) on every task
  table. No baseline was dropped for winning.
- **Statistics harness.** 27 seeds, 95 % BCa intervals, Wilson intervals for
  proportions, paired Wilcoxon with Holm correction and rank-biserial effect
  sizes, cluster bootstrap where the unit is a real object, censoring
  reported per stratum. The rows behind every statistic are persisted with
  git SHA, host, CPU and SLURM ids.
- **The negative results are load-bearing, not hidden.** RQ4's iso-twin
  construction and RQ5's floors were designed *to* expose the blind spot of
  summaries and the size confound respectively, and the fallbacks were
  written for the case that materialised.

### 1.2 What is fragile

1. **The adopted word is nauty-derived.** `fact_rank` is
   `T[types…] F[pred; canonical ranks]…` with ranks from
   `pynauty.canon_label` on the coloured Levi graph. Exactness (RQ2), the
   envelope (RQ7) and the sub-millisecond cost are therefore nauty's
   properties plus a tokenisation; the stability result (RQ1) is a property
   of the tokenisation granularity (one token per fact). The design's own
   risk register (§10, row 1) names this. Consequence: the article's
   distinctiveness rests entirely on what a certificate cannot do — the
   decoded consensus (RQ3), total decoding and generation (RQ6) — and the
   introduction must say that in so many words rather than let the reader
   infer it from a table.
2. **The certificate comparison in RQ1 is tokenisation-confounded.** RQ1 M1
   compares `fact_rank` *tokens* against `nauty_cert` *bytes*; the design
   lists `nauty_cert_rows` (canonical adjacency rows as symbols) as the
   tokenisation-matched ablation, but it was run only in RQ2, RQ5 and RQ7,
   **not in RQ1** (0 occurrences in `RQ1_addressing/addressing/tables.md`).
   The walkthrough's sentence "nauty reads lower per token only because its
   strings are 12–30 × longer" is an interpretation, not a measurement. This
   is the same confound `START_HERE.md` §3 item 8 already flagged for the
   older G2 contrast. It is cheap to close (one extra arm in the M1/M3 pass).
3. **The single-edit response is normalised for the gate and the M1 table,
   but the distance the paper uses is raw** (L11). A reviewer will ask why
   stability is judged on `d/|w|` when every downstream task uses `d`. The
   M1 tables also carry the absolute medians (`median_abs`) and the
   "within ≤ 2 tokens" fraction; the main-text table should lead with those,
   since the PI's criterion ("similar knowledge bases at small Levenshtein
   distance") is about absolute distance.
4. **Roles were withdrawn, so facts are undirected.** See §5.2.
5. **RQ6's baseline is a straw man for the validity claim.** An n-gram over
   a flat serialisation with a strict decoder rejects 98–99 % of samples; a
   grammar-constrained sampler over the same serialisation would reject
   none. The claim that survives is the theorem (every word decodes; no
   generative model is definable over certificates), not the rejection
   rate. Keep the rate as an illustration, not as the comparison.
6. **RQ5's main-text content is an unvalidated exhibit.** A dendrogram
   (cophenetic 0.92) and an MDS map with no external criterion is what the
   v3 proposal called "orphan geometry". It is licensed by `ν = 0.10`, and it
   was asked for by the PI, but it should be one figure with one sentence
   saying that no representation recovers Wikidata types from structure.

## 2. Are the numbers in the walkthrough correct?

Sixty-plus headline numbers were re-read from the persisted tables. Outcome:

| RQ | status | detail |
|---|---|---|
| RQ2, RQ4, RQ6 | **all match** | every quoted number found verbatim |
| RQ3 | match, one gap | per-cell tables, pooled distances, ratio bound, Corpus B all match; the recovery-by-`m` breakdown (0.23 → 0.90), "311 of 326 misses at distance 2" and "ties median 0, max 3" are not in any `tables.md`/`summary.json` and must be re-derived from `rows_variants.csv` and persisted before being quoted |
| RQ1 | **stale** | the M1 row values for `ndc_classes` and `synthetic_rq1` in the walkthrough (e.g. 0.146 / 0.452 / 0.670 / 0.944) do not match the persisted Wilcoxon table (0.158 / 0.492 / 0.731 / 1.025); the `wd50k66` row, the pointer and nauty columns, the gate, M2 and M4 match. Also: M3 "0.3–0.6 ms" understates `wd50k66_full` (0.92 ms median), and the pointer censoring "21–60 %" is 29–69 % on WD50K |
| RQ5 | one wrong value | `size_l1` PAM floor quoted as 0.041; persisted 0.0486 (the conclusion "no floor beaten" still holds, 0.0417 < 0.0486) |
| RQ7 | two over-precise | pointer time-outs begin at `m = 80` in some `k = 3` sparse cells, not "from 120"; the `> 24 facts` WD50K bucket has p90 2.8 ms, so "p90 ≤ 0.9 ms including that bucket" is false as written |

The walkthrough also does not say whether its M1 table reports means or
medians (the persisted Wilcoxon table is means; the per-edit-kind table is
medians). Regenerate the M1/M3 paragraphs from `tables.md` and label the
statistic.

## 3. Are we failing an experiment?

Per research question, against its pre-registered hypotheses:

| RQ | primary hypothesis | outcome | disposition |
|---|---|---|---|
| RQ1 | H1a–H1c (stability ranking) | **holds**; H1d void (roles arm not invariant) | main text |
| RQ2 | descriptive | **holds**; WL-1 is also exact here (stated) | main text |
| RQ3 | H3a insertion/mixed | **holds** (≥ 0.866 everywhere) | main text |
| RQ3 | H3a deletion | **fails at t = 2** (0.23–0.81) | main text with the boundary — **mechanism sentence must be corrected, §3.3** |
| RQ3 | Corpus B | consensus worse than merge | supplement (pre-registered) |
| RQ4 | H4a iso-twin | **holds vs summaries**, not vs WL | main text, qualified |
| RQ4 | H4b non-inferiority | **fails** (39 of 42 cells below best) | supplement (pre-registered) |
| RQ5 | H5a licences | ν holds; hubness **fails** (5.4 vs 1.5) | main text, both stated |
| RQ5 | H5b–H5d task metric | **all fail** (ARI ≤ 0.09, floors lead) | supplement (pre-registered) |
| RQ6 | H6a–H6c | **hold** | main text |
| RQ7 | H7a–H7c | **hold** | main text |

So: two experiments failed their competitiveness hypotheses (RQ4, RQ5), one
failed a licence clause (hubness), and one has a real boundary (RQ3 deletion
at budget 2). All four were anticipated by a pre-registered fallback. The
plan "positives lead, negatives in the supplement as limitations" is
consistent with the design **as long as the main text contains, for each,
one sentence of the form "we tested X; it did not hold (numbers); see
Supplement §Y"**. A TKDE reviewer reads the supplement; a main text that
implies competitiveness it does not have will be caught.

### 3.1 RQ4 — what actually failed and why

The main-text statement (summaries at chance on iso-twins, complete arms
above chance) is true on `ndc_classes`: `hpd_jsd` 0.512, `degree_seq_l1`
0.516, `size_l1` 0.501 against `fact_rank` 0.764, `nauty_cert` 0.717. Its
boundaries are real and must be printed with it: `wl_l1` detects the twins
too (0.805, better than us), and on the WD50K types the twin construction
leaves degree traces that degree and NetLSD pick up (only 19.1 % of realised
twins are WL-1-indistinguishable). The advantage is over the *summaries*, not
over WL. The correct test of exactness against WL is the WL-1-equal subset
(open item 4 of the walkthrough): run it; if the subset is small, say that
the exactness advantage over WL is rare on these collections — that is the
honest finding, and it is consistent with RQ2.

The missing-fact scores are below chance on every WD50K type for both
canonical-string metrics (`fact_rank` 0.35–0.47, `nauty_cert` 0.37–0.56)
while the size floor is above chance there (0.53–0.77). This is not "a
complete space with hubness 5.4"; it is the length term of raw edit
distance: in a collection whose members differ mostly by their own facts,
`d(A, B) ≈ m_A + m_B − 2·|common|`, so a record that loses a fact moves
*closer* to every record that lacked it. The secondary LOF score does not
repair it (48 of 49 cells below the best competitor, worse than kNN). State
the mechanism as a limitation of the raw metric, and note that a
length-normalised edit distance (Yujian & Bo, IEEE TPAMI 2007, which keeps
the metric axioms) is the obvious follow-up.

### 3.2 RQ5 — what failed and what it means

No representation recovers Wikidata `P31` types from relational structure:
best ARI 0.075 (NetLSD, PAM), ours 0.042, the floors 0.049 (size) and 0.053
(degree), NMI ≤ 0.27, and on the full design every arm ≤ 0.017. This is a
statement about the collection, not about the method, and the paper should
say it in one sentence as a negative control. What is *not* fine is to leave
the reader with the dendrogram and the map as if they had been validated.
Hubness (skewness 5.4 at `k = 10`) fails the pre-registered moderation
clause, and the paper should say that this is why the kNN-type readings of
RQ4 are qualified.

### 3.3 RQ3 — the deletion boundary is real, the stated mechanism is wrong

`DECISIONS.md` and the walkthrough attribute the `t = 2` deletion failure to
information loss: "with two deletions per variant on six-fact sources the
information is gone from the collection and both consensus readings fall
together". We tested that claim by re-running the frozen consensus
(`coverage_consensus`, `r = 2`, triangle budget) on the same cell
definitions with the shipped variant generator and adding three
diagnostics per collection: whether the source's canonical key is in the
candidate pool, whether the source would tie or beat the returned winner
under the frozen objective, and whether the identity-addressed union of the
variants equals the source.

| collection | N | collections | consensus exact | source in pool | source ties/beats winner | union = source | majority merge |
|---|---|---|---|---|---|---|---|
| ndc_classes | 5 | 16 | 0.25 | **1.00** | 0.25 | **1.00** | 0.38 |
| wd50k66 | 5 | 58 | 0.43 | **1.00** | 0.59 | **1.00** | 0.28 |
| wd50k66 | 9 | 34 | 0.74 | **1.00** | 0.82 | **1.00** | 0.97 |

The recovery rates reproduce the campaign's (0.23 / 0.37 / 0.81). The
information is never gone: the union recovers the source in every
collection, and the source is always a candidate. The consensus loses for
two reasons, both properties of the objective as frozen:

- **Sub-record preference.** In 46 of the 54 misses the winner is a strict
  subset of the source with on average 1.3–2.0 fewer facts, at equal
  coverage and *lower* summed reach (NDC: winner Σ = 8.5 vs source Σ = 10).
  Under isomorphism, deleting a fact from a symmetric source makes its
  remainders coincide with the variants' remainders, so `S − {x, y}` sits at
  reach ≤ 2 from every variant with a smaller sum than `S` itself. NDC
  classes are star-shaped and highly symmetric, which is why the effect is
  strongest there.
- **Arbitrary tie-break.** The gap between "source ties or beats the winner"
  and "consensus exact" (0.59 vs 0.43 on WD50K `N = 5`) is the lexicographic
  word rule deciding against the source on an exact tie of
  `(coverage, Σ reach)`. This contradicts "ties do not explain it".

Both mechanisms weaken as `m` grows (WD50K `N = 5`: source ties/beats the
winner in 0.43 of collections at `m = 6`, 0.83 at `m = 9`), which is the
`m`-dependence the walkthrough observed and misattributed.

What this means for the paper. The boundary stays, and it is still an
honest one; what changes is the sentence. Proposed wording: *at budget
`t = r` on deletion-only collections the radius-`r` ball around the variants
contains both the source and its sub-records; the frozen objective breaks
that tie toward the sub-record on symmetric sources, and the identity-reading
majority merge fails in the same cells for its own reason (a fact deleted
from more than half the variants is lost to any majority). The source
remains in the candidate set and is recovered by the identity-addressed
union in every collection, so this is a limit of the objective, not of the
information; choosing between a source and its sub-record without a prior on
the edit direction is the open question.* The design forbids re-tuning the
objective after the fact (RQ3 gate: "no further tuning"), so a corrected
tie-break (e.g. largest fact set at equal coverage) may only appear as a
clearly labelled post-hoc variant in the supplement, or as future work.
Reproduction: `scripts/diagnostics/rq3_deletion_boundary_probe.py`
(`<collection> <N> <n_sources>`; ~3 min for the three rows above).

## 4. Walkthrough — what each experiment measures, why, and what came out

Each entry: the engineer's question (from `prose.md` §1), what is measured
and why that is the right measurement, the outcome with competitors, and
what belongs in the main text.

### RQ1 — Addressing: which encoding makes similar knowledge bases close?

**Question in practice.** Every downstream operation (representative,
screening, clustering, generation) relies on "one fact changed" being "a
small string edit". The PI made this the acceptance criterion. RQ1 asks
which way of naming constants inside the word achieves it.

**What is measured.** For every real member and five edit kinds, the
Levenshtein response of each encoding to one edit (absolute tokens,
normalised, and the fraction of edits that stay within two tokens), split by
whether the constant set is preserved; monotonicity of the distance against
a known edit budget (ladders and the natural NDC quarters); cost and
censoring per size stratum; and correlation with the certificate distance.
Arms: the adopted fact-rank word, three alternative fact addressings (degree
key, local key, local colour), the roles variant, the pointer alphabet of
the sibling papers, and the nauty certificate.

**Outcome.** The fact-rank word is exact and relabelling-invariant on all
three corpora (0 false merges, 0 false splits, class counts equal to
nauty's) and the most locally stable fact addressing in every cell:
mean normalised response 0.16–0.23 when the constant set is preserved
against 0.49–0.54 (degree key), 0.63–0.73 (local key), 1.00–1.03 (local
colour) and 0.49–0.79 (pointer); all Holm-significant, rank-biserial −0.75
to −1.00. One inserted fact costs one token (median), and 0.59–0.85 of
constant-preserving edits stay within two tokens against 0.00–0.41 for the
certificate and 0.03–0.86 for the pointer. When the constant set changes the
fact-rank word responds 0.39–0.51 and the pointer's advantage vanishes
(rank-biserial −0.08 to −0.32). Cost: 0.3–0.9 ms per member with no
censoring, against 0.3–4.6 s and 29–69 % censoring above 17 facts for the
pointer alphabet. The roles variant is **not** a canonical form (247 false
splits, 2,104 invariance violations on WD50K) and is withdrawn.

**Competitors.** The nauty certificate is the reference, not a competitor:
its normalised response is lower (0.08–0.25) but on 12–30 × longer strings,
and its within-two-tokens fraction is 0.00–0.41. The comparison is
tokens-vs-bytes (§1.2 item 2) until `nauty_cert_rows` is added.

**Main text.** The frontier table (M1 by regime, M3 cost) with the
reproduction gate stated. Lead with absolute tokens and the within-two
fraction. Supplement: per-edit-kind tables, M2, M4, invariance census, the
roles failure, and the gate amendment (the probe's pointer value 0.500 was a
rapidfuzz hash-equality artefact; corrected to 0.57 / 0.56 / 0.60, in the
direction unfavourable to the pointer alphabet — state it).

### RQ2 — Well-posedness: when are two knowledge bases "the same"?

**Question in practice.** Deduplication, identity resolution and any
distance-based analytics presuppose that distance zero means "same up to
renaming". A representation that merges different objects at zero (a false
merge) silently corrupts every operation built on it.

**What is measured.** On all non-isomorphic member pairs of three real
collections (10.4 M pairs), the number a representation places at distance
zero, and the number of classes it induces against the true count; exactness
in the other direction on 100 isomorphic pairs per collection; the metric
axioms of the tractable bipartite-GED readings on real members; the cost of
the exact edit-distance oracle; validity of the medoid's certificate under
each distance; and the cost of computing the identity.

**Outcome.** The complete representations — ours, the nauty certificate and,
on these labelled collections, WL-1 — merge nothing (0 in 10.4 M) and find
the true 557 / 1,156 / 3,682 classes. The summaries merge 0.3–5.5 % of
non-isomorphic pairs (HPD collapses 3,682 WD50K classes to 782; the size
floor to 194). The bipartite edit-path reading separates 44–49 % of
isomorphic pairs (identity of indiscernibles fails) and violates the
triangle inequality on 7–8 of 5,000 triples; the assignment reading has
false zeros (36 of 2,000 pairs). Exact GED costs 0.45–1.08 s per pair with a
p90 of 13 s at 9–10 facts, which is why it is a ceiling and not a
competitor. The identity costs 0.07–0.37 ms per member under the fact-rank
word against 3.5–5 ms with 6–12 % censoring under the pointer alphabet.

**Competitors.** All ran. WL-1 being exact here is stated honestly: on these
corpora exactness separates the complete arms from the summaries, not from
WL.

**Main text.** The consequences table plus the metricity counts and the
oracle ceiling. This is the paper's cleanest table.

### RQ3 — The representative record

**Question in practice.** `N` descriptions of one thing from different
sources, runs or quarters disagree; which one is kept as the reference?
Golden-record construction in master-data management, consensus of
extraction runs, the reference co-formulation pattern of a drug class.

**What is measured.** The exact fact-level distance (constant identities
used for scoring only) between the returned representative and the truth.
Ours: the coverage consensus, a *decoded word* that need not be any input;
the certified medoid with its ratio bound `≤ 2 − 2/N`. Competitors: the
medoid under every distance (a medoid can only return an input, so it is at
distance ≥ `t` by construction), and the identity-using majority merge as a
reference that sees information denied to every method. Corpus A: planted
constant-preserving variants of real members (insertion, deletion, mixed;
`t ∈ {1, 2}`, `N ∈ {5, 9}`, 27 seeds × 8 sources per cell). Corpus B: the
natural NDC quarter series with the next quarter held out.

**Outcome.** On Corpus A the consensus returns the source exactly in
0.991–1.000 of insertion collections, 0.866–0.995 of mixed collections and
0.979–1.000 of single-deletion collections, without using identities and
matching the identity-using merge (gap 0.014). Every medoid recovers 0 of
4,457 (pooled fact distance 1.50–1.54 against 0.18–0.20 for the consensus,
Holm-significant). The ratio bound holds on all 4,457 medoids (max 1.778).
The boundary is two deletions per variant (0.23–0.81; mechanism corrected in
§3.3). On Corpus B the consensus is worse than the majority merge and than
most medoids (fact distance 2.60 vs 1.84–2.40): a time series is not a set
of variants of one source, so there is nothing to converge to.

**Competitors.** The medoid comparison is by construction and should be
presented as "what any input-returning method can do at best", not as a
race. The meaningful comparison is with the majority merge, which the
consensus matches without identities.

**Main text.** Corpus A with the boundary and the corrected mechanism; the
ratio bound. Supplement: the `t = 2` deletion cells with the recovery-by-`m`
breakdown (to be persisted first), the medoid-ratio distribution, Corpus B.
This is the paper's flagship result and the one a certificate cannot
produce.

### RQ4 — The data-quality screen

**Question in practice.** Which descriptions are structurally anomalous —
extraction errors, schema violations, mis-typed entities? Knowledge-graph
error detection where the anomaly is the shape of the description.

**What is measured.** AUROC of kNN (`k = 5`) and LOF (`k = 20`) anomaly
scores over each distance matrix at 5 % contamination, for four injected
corruptions of real members: spurious fact, missing fact, wrong argument,
and the isomorphism-breaking twin (same size, arity histogram, degree
sequence, type and predicate multisets; verified non-isomorphic by nauty).
Seven sub-collections × 27 seeds.

**Outcome.** Exactness consequence (H4a): on the structurally repetitive NDC
collection, the summaries cannot see the twin (0.50–0.52) while the
complete arms do (ours 0.764, nauty 0.717, WL 0.805). Competitiveness (H4b)
fails: ours is below the best competitor in 39 of 42 standard-corruption
cells (mean AUC ours vs best: spurious 0.68 vs 0.84, missing 0.44 vs 0.64,
wrong argument 0.57 vs 0.81); the certificate behaves like us (within 0.05
on 44 of 49 cells), so this is a property of canonical-string metrics under
kNN, not of our tokenisation. Missing-fact is below chance for both
canonical-string metrics on every WD50K type (§3.1).

**Competitors.** NetLSD and HPD lead on standard corruptions; degree
sequence and NetLSD match or beat us on WD50K twins. All ran; the 266 HPD
cells censored by a vendored-library crash were re-scored (0 censored rows
remain).

**Main text.** The iso-twin table read with RQ2's census, with both
boundaries printed (WL detects them; on non-repetitive collections the twin
leaves degree traces). One sentence that non-inferiority on standard
corruptions was tested and failed, with the supplement pointer. Supplement:
the full AUC tables at both budgets and both scores, the Holm table, the
realisation table, and the WL-1-equal-twin subset once run.

### RQ5 — Description patterns

**Question in practice.** Which patterns of description exist in a
collection, how many, which are under-populated? Schema and pattern
induction, coverage audit, stratified sampling for annotation.

**What is measured.** The geometric licences (non-Euclidean mass `ν`, Gram
spectrum, `k = 10` hubness) that decide whether medoid methods and metric
MDS are the right tools; then k-medoids and average-linkage clustering
against 14 Wikidata types on a balanced design (14 × 20, 27 seeds) and on
the full 3,492 members, scored by ARI/NMI with both floors and every
competitor; cophenetic correlation of the hierarchy; `wd50k100` as a purity
control.

**Outcome.** `ν(fact_rank) = 0.101` with 1,553 negative eigenvalues: PAM and
metric MDS are licensed; HPD and NetLSD are effectively Euclidean
(`ν ≈ 0`). Hubness is not moderate (5.4 vs the 1.5 ceiling; WL 18.6 with one
hub of occurrence 3,464). No representation recovers types: ours ARI 0.010
(agglomerative) / 0.042 (PAM), floors 0.038 / 0.049 (size) and 0.025 / 0.053
(degree), best competitor NetLSD 0.066 / 0.075; on the full design every arm
≤ 0.017. Cophenetic correlation of our dendrogram 0.92–0.93.

**Competitors.** All ran, all fail the task; the floors lead the balanced
comparison.

**Main text.** The licence table (one row per representation: this is a
genuine comparison and it feeds RQ4's qualification) and one exhibit figure,
with one sentence that Wikidata type is not a structural signal for any
representation. Supplement: the ARI/NMI tables, the per-class table, the
control.

### RQ6 — Generation

**Question in practice.** "Give me more knowledge bases like these":
benchmark construction, synthetic stand-ins for records that cannot be
shared, completion suggestions.

**What is measured.** Validity of samples from an order-3 token n-gram
fitted on a real collection's words (every sample must decode, by theorem),
against the same model over a flat incidence serialisation with a strict
decoder; fidelity of the sample profile (Jensen–Shannon divergence to the
collection's size, fact-count, arity, predicate and type histograms),
novelty and reach-1 neighbourhood; decodability of every interior word of
20 real alignment paths; conditional completion of truncated members.

**Outcome.** 540,000 of 540,000 samples decode (Wilson lower bound
0.99999); the flat baseline is rejected on 98.1 % (NDC) and 99.0 % (WD50K).
Fidelity: JSD ≤ 0.002 on predicates, < 0.001 on arity, ≤ 0.006 on types,
0.05–0.07 on fact count, 0.07 (NDC) and 0.21 (WD50K) on constant count;
novelty 0.99 / 0.94. All 86 alignment interiors decode (68.6 % connected
under the fact alphabet, 100 % under the pointer alphabet). Completion:
300 of 300 valid, 68 % isomorphic to the original on NDC (14 % on WD50K).

**Competitors.** No certificate admits a generative model (a theorem, not a
measurement); the flat-serialisation baseline is an illustration of what a
non-closed language costs, not a fair contender (§1.2 item 5).

**Main text.** Validity, fidelity, the decodability figure, completion.
Supplement: the WD50K constant-count divergence (0.21, larger than the
baseline's accepted survivors), the connectedness of interiors, the
rejection-cause table.

### RQ7 — The operating envelope

**Question in practice.** For which knowledge-base sizes, arities and
vocabularies does this run, and how does the cost of an all-pairs analysis
scale with the collection size?

**What is measured.** A synthetic sweep over facts `m` (10 … 1,280), arity
`k` (2 … 5), alphabet sizes and density with a process-level time budget (27
instances per cell); yield on every real collection by size bucket;
wall-clock of the full `N × N` matrix on WD50K for every representation.

**Outcome.** The fact-rank word and the nauty certificate clear every cell
to the sweep ceiling (0 time-outs in 7,938 instances; medians 2.5–17 ms at
1,280 facts); the pointer alphabet times out on 39.5 % of its instances and
on essentially every instance above 80–120 facts at `k ≥ 3`. Yield on real
data: 100 % of members of every bucket at medians 0.2–0.9 ms (p90 up to
2.8 ms on the `> 24 facts` bucket); the pointer alphabet completes 0–57 % of
members at 21–24 facts. The all-pairs matrix on 3,988 members: 1.5 s of pair
distances plus 0.3 s of canonicalisation for us; 864 s for the certificate
(longer strings); 43 s degree sequence; 525–913 s bipartite GED; HPD and
NetLSD censored above 2,000 and 1,000 members.

**Competitors.** All timed. The pointer alphabet's envelope closes at about
13–20 facts, which is the measured reason the fact alphabet is the paper's
representation.

**Main text.** The envelope table, with the honest note that the fact
alphabet's cost is one canonical-labelling call (H7b) — the envelope is
nauty's, and we inherit it.

## 5. What must be done before drafting

Ordered by consequence.

1. **Correct the RQ3 deletion mechanism** in `DECISIONS.md`, the walkthrough
   and the prose (§3.3). Persist the recovery-by-`m`, misses-at-distance-2
   and ties statistics that the walkthrough quotes but no table carries.
2. **Regenerate the walkthrough's RQ1 M1/M3, RQ5 floor and RQ7 yield
   sentences from the persisted tables** (§2), and label means vs medians.
3. **Decide the roles question, because it is a fidelity limitation.** With
   roles withdrawn, every fact is an unordered set of constants: direction
   is lost for every binary Wikidata relation. Either (a) make roles
   canonical by colouring the Levi incidence with the role before canonical
   labelling (the certificate then sees roles; invariance follows from
   nauty's), and re-run RQ1 M0/M1 for the roles arm, or (b) state in the
   limitations that the encoding is undirected and the competitors were
   given the same undirected input. (a) is a few hours of work and removes a
   reviewer objection; (b) is honest but invites it.
4. **Add `nauty_cert_rows` to RQ1 M1/M3** so the stability comparison
   against the certificate is tokenisation-matched. Cost: one arm, minutes.
5. **Run the WL-1-equal-twin subset AUC** (walkthrough open item 4) and put
   the result in the supplement; it is the only test of the exactness
   advantage *over WL*.
6. **Write the "adopted word = canonical labelling serialised as facts"
   sentence into the introduction**, and let the paper's contributions be
   stated as: (i) the addressing characterisation with its frontier
   proposition; (ii) exact, metric, polynomial, closed-language
   representation of knowledge-base collections; (iii) the decoded
   consensus with a certificate; (iv) generation with validity by theorem;
   (v) the measured envelope. Everything else is characterisation.
7. **State Theorem 1 for the fact-rank word.** Theorem A of the preprint is
   about `w*_c`; the fact-rank word's exactness needs its own (short)
   statement via the canonical labelling. `START_HERE.md` §8 E9 lists it;
   it is not optional.
8. **One sentence per failed hypothesis in the main text** (RQ4 H4b, RQ5
   H5b–d, RQ5 hubness, RQ3 deletion at budget 2, RQ3 Corpus B), each with
   its numbers and the supplement pointer. This is what makes the A → A′
   rule defensible rather than cosmetic.
9. **Ratify the two RQ1 gate amendments** and update every document that
   still quotes the pointer response as 0.500 (`prose.md` §2.3,
   `START_HERE.md` §0 and §6.0).

## 6. Reviewer-risk register for TKDE

| objection | answer available | status |
|---|---|---|
| "Your word is nauty plus a fact list; what is the contribution?" | the language: decoded consensus (RQ3), total decoding and generation (RQ6), the addressing frontier (RQ1) | must be written explicitly (item 6) |
| "You lose to NetLSD/HPD on outlier detection and to the size floor on clustering" | tested, failed, reported; the paper claims exactness and the language, not task superiority | acceptable if stated in the main text (item 8) |
| "The consensus only wins against methods that cannot output a new object" | true by construction; the meaningful comparison is with the identity-using merge, which it matches | present it that way |
| "The deletion boundary" | real; the mechanism is the objective's tie-break, not information loss | correct the sentence (item 1) |
| "Facts are undirected" | fix roles or state the limitation | item 3 |
| "Tokens vs bytes against nauty" | run `nauty_cert_rows` in RQ1 | item 4 |
| "The generation baseline is a straw man" | keep the theorem, present the rejection rate as illustration | item in §1.2 |
| "Synthetic variants in RQ3" | real members, controlled edits, truth by construction; the natural series reported beside them as the weak regime | already in the design |

## 7. Provenance of this audit

- Number verification: every headline number of `RESULTS_WALKTHROUGH.md`
  re-read from the corresponding `tables.md` / `summary.json` / `stats.json`
  (RQ1–RQ7), 2026-09-06.
- RQ3 mechanism: `scripts/diagnostics/rq3_deletion_boundary_probe.py`, run
  in the `isalhg` environment against the frozen corpora under the results
  root, cells `(ndc_classes, N = 5)`, `(wd50k66, N = 5)`, `(wd50k66, N = 9)`,
  `t = 2`, deletion-only, seeds 0–1, 40 / 30 / 20 sources.
- RQ4 missing-fact mechanism: `RQ4_screen/analysis/tables.md`, §Standard
  corruptions, the `missing_fact` rows for `fact_rank`, `nauty_cert`,
  `netlsd`, `size_l1`.
- Pre-registration: `git log -- docs/article/D_ART3/experiments/DESIGN.md`.
