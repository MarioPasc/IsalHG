# Writing brief — IEEE TKDE article, "knowledge bases as words"

**For:** `[Opus-Article-Orchestrator]` · **From:** `[IsalHG-Fable-Review]` ·
**Date:** 2026-10-04 · **Branch holding everything below:**
`integration/2026-09-13-headline-w0` (head `3615c00`; **not merged** into
`feature/isal-kb-word` — the main checkout is on it, so paths resolve there).

Items marked **PENDING-P1** are being closed by the harvest agent (wave
`2026-10-04-harvest`); a second message will say what changed. Nothing else in
this brief depends on it.

---

## (a) State since 2026-09-14

**Nothing was decided or merged in the three weeks.** No commit after
2026-09-14, no new entry in `DEVELOPMENT/DECISIONS.md`.

- **D-ART6 (is `w°` the headline program?):** author-directed 2026-09-13,
  **PI ratification still pending** in the repo (`DECISIONS.md` line 665). If
  the author has the PI's word, it is not recorded. Write on `w°`; keep
  Theorem A and `w*_c` as the family's search form, appearing in the RQ1
  ablation only.
- **RQ4 (data-quality screen):** never completed and never resumed. 819 of
  1,323 units ran on 2026-09-10; no aggregation for any Isal arm exists. The
  only finished RQ4 table is the retired fact-rank one (2026-09-06). **RQ4 has
  no citable number for `w°`.** Omit it from the main text; in the supplement
  it can only be described as not completed.

| RQ | verdict | frozen numbers / source |
|---|---|---|
| RQ1 locality + nauty ablation | FINAL. Conditional: Isal programs win every *pendant* cell against the certificate; the certificate wins the two argument-level *interior* cells; pooled, no ordered-walk arm beats the certificate rows (0.070 vs 0.179), pre-registered escape clause fired | `results/IEEETKDE/RQ1_isal/merged/` (`published_tables.md`, `rq1_statistics_<corpus>.md`, `m1_instructions_by_kind.md`); `foundation/rq1_addressing_facts.md`; table in `SESSION_LOG.md` §3 |
| RQ2 well-posedness | **CLOSED (P1).** `w°`: 0 false merges, 0 members censored, exact partition **557 / 1,381, 1,156 / 1,745, 3,682 / 3,988** (classes / members; NDC-classes, NDC-substances, WD50K(66)). The earlier 530 / 1,086 / 3,677 are `w*_c` on the members it survived (1,311 / 1,661 / 3,983) — do not print them for `w°` | `foundation/rq2_ow_facts.md` §4; competitor counts in `foundation/rq2_wellposedness_facts.md` §1 |
| RQ3 v1 consensus | SUPERSEDED (fact-space machinery, coverage objective, identity-using baseline). Do not cite except the corrected-run harvest in `RQ3V2_PILOT.md` G3.2 | `results/IEEETKDE_isal_consensus/RQ3_representative/` |
| RQ3 v2 golden record | **CLOSED (P1) on 11 complete cells; NOT a headline for the language.** The word-space consensus beats the anonymous merges (0.21–0.73 vs 0.00–0.10) and every medoid, but its representation-free ablation — the same consensus computed in fact space — recovers 0.984 against 0.433 and is cheaper (H3.5 fails; pre-registered fallback applies). Seven heavy cells (non-star N = 15; non-star N = 9, t = 2; star N = 15, t = 2) never completed. **Supplement only** — see (c) R-F | `foundation/rq3v2_facts.md`; `experiments/RQ3V2_PILOT.md`; `results/IEEETKDE_ow/RQ3v2_golden_record/anonymous_consensus/_analysis_ef0c58b4+1efdcf54/` |
| RQ4 screen | NOT COMPLETED (above) | — |
| RQ5 patterns | NEGATIVE, final, on both programs. Every arm ARI < 0.08 against Wikidata types | `foundation/rq5_ow_facts.md`; `results/IEEETKDE_ow/RQ5_ow/` |
| RQ6 generation | DONE, the unconditional headline | `foundation/rq6_generation_facts.md`; `results/IEEETKDE_isal_consensus/RQ6_generation/`; reach-1 at `results/IEEETKDE_isal_reach1b/` |
| RQ7 envelope | COMPLETE, replicated | `foundation/rq7_envelope_facts.md`; `results/frozen/rq7_envelope_2271960_reading/`; `results/frozen/tail600_2279006_verdict/` |
| RQ8 valid completion | DONE at 27 seeds, three pre-registered amendments (A1–A3). Supported on WD50K's relational stratum only | `foundation/rq8_facts.md`; `experiments/RQ8_PILOT.md`; `results/IEEETKDE_ow/RQ8_completion/completion/_tag_c5380cde+7f25205b+52c4f4f9/` |

All `results/…` paths are under
`/media/mpascual/Sandisk2TB/research/ISAL/isalhg/`.

---

## (b) Reading list

**Authoritative, in order.**

1. `docs/article/D_ART3/SESSION_LOG.md` — §2 (model in plain words), §3 (per-RQ
   numbers), §6 (the five design answers), §8–§10 (the campaign and its
   rulings).
2. `docs/article/D_ART3/experiments/HEADLINE_DESIGN_2026-09-13.md` — §0 (why
   the strata), §3–§4 (the pre-registered designs), **§8 (deviations log: every
   amendment and its reason)**.
3. `docs/article/D_ART3/foundation/rq{1_addressing,2_wellposedness,2_ow,3v2,5_ow,6_generation,7_envelope,8}_facts.md`
   — the only place a number may be copied from.
4. Proofs: `…/isalhg/proofs/completeness/theorem_c_ordered_walk.tex`
   (Theorem C, Corollary C, Props C.4–C.7) and
   `…/isalhg/proofs/completeness/theorem_a_completeness.tex` (Theorem A,
   Corollary A, coherent-ties Prop. 6.1). Prop. C.8 (prefix property) is stated
   and proved in `experiments/RQ8_PILOT.md`.
5. `docs/article/H2S_S2H.md` — the S2H interpreter and the H2S encoder spec.
   It specifies the search encoder; the ordered walk is specified in the
   Theorem C file and `experiments/ISAL_VARIANT_DESIGN.md` (with §9 deviations),
   code in `src/isalhg/core/` (ordered-walk emitter, C++ under `core/_native/`).
6. `docs/article/D_ART3/prose.md` (v7) — the storyline and section plan (§1
   premise table, §11.2 glossary, §12 section plan). **Read under its D-ART6
   banner**: every "`w*_c` carries §§3–7" sentence, the §2.3 preview locality
   table, and §3's RQ3/RQ4/RQ5 entries are superseded by items 1–3.
7. `docs/article/D_ART3/tables/tab_kb_representation_properties.tex`.
8. `docs/article/DEVELOPMENT/DECISIONS.md` — D-ART4, D-ART5, D-ART6, D-KBg1.
9. `docs/article/D_ART3/foundation/lessons.md` — L1, L9, L11, L12, L13, L17,
   L18, L19 are binding on prose; `literature_verified.md` for citations and
   the novelty verdict; `proved_facts.md` for theorem statuses (it predates
   Theorem C).
10. `docs/article/D_ART3/supplementary_data.md` + `T-KB/OPEN/T-KBk.md` — the
    corpora, **with the counts corrected** (see (e)); `venue.md` (TKDE
    checklist); `experiments/ENCODINGS_WORKED_EXAMPLE.md`;
    `experiments/COMPETITOR_AUDIT.md` (competitor contracts).

**Proofs: main text vs appendix.**

| statement | where |
|---|---|
| Theorem C (a deterministic emitter along a canonical labelling that round-trips is a complete invariant) + Corollary C (metric) | main text, with proof — it is short and it is the headline program's foundation |
| Prop. C.4 (every word decodes to a connected knowledge base) | main text, with proof (short induction); it carries RQ6, RQ3, RQ8 |
| Prop. C.8 (appending instructions never removes a fact or constant) | main text, one line |
| Prop 3 (medoid ≤ (2 − 2/N)·OPT; pairwise bound LB ≤ OPT; certified ratio) | main text, statement + two-line proof, cite Jiang–Münger–Bunke 2001 |
| Prop. C.6 (name-freedom) | statement in main text (it explains pendant locality); proof appendix |
| Prop. C.5 (star locality) | appendix |
| Theorem A / Corollary A (`w*_c` completeness, labelled case) | statement in main text as the family's search form; proof appendix (long) |
| Prop. C.7 (orbit pruning is value-preserving) | appendix; needed only for the RQ1 ablation |
| Prop 8 (bipartite edit-path cost is not a metric; 10-vertex counterexample) | one sentence + appendix; Serratosa 2019 in print |

**Superseded — do not plan from these.** `START_HERE.md` §0–§8 (pre-D-ART4);
`D_ART3/{README,proposal,applications,competitors,geometry,theory,data}.md`
(v5.1); `D_ART3/logic_models/` (second paper); `experiments/RESULTS_WALKTHROUGH.md`
(stale numbers and a tokenisation confound, T-KBx);
`experiments/RESULTS_AUDIT_2026-09-06.md` and `foundation/probes_2026-09.md`
(fact-rank era, record only); `experiments/D_ART5_DECISION_BRIEF.md` (its
program choice is superseded by D-ART6); the `HANDOFF_*` / `STATE_*` files
(history); `foundation/measured_facts.md` (a different paper's corpus);
everything under `docs/article/{PROPOSAL,DATA,COMPETITORS}.md`,
`docs/article/{theoretical,empirical,figures}/` (the retired *Information
Sciences* scope); `docs/preprint/`.

---

## (c) Candidate main-text results

Each: the hypothesis, what to print, the scope that must stay in the sentence,
and what a TKDE reviewer would catch.

**R-A. Generation (RQ6).** *Hypothesis:* because the language is closed and
connected, any model over words samples knowledge bases with validity 1.
*Print:* 270,000 of 270,000 samples valid and connected on each collection (27
seeds × 10,000); incidence-list generator rejects 98.10 % (NDC) / 98.98 %
(WD50K); fact-list generator valid but connected 41.6 % / 12.6 %; per drawn
sample, usable one time in 578 / 11,739 for the incidence list. *Scope:* the
claim is validity and domain membership, by Prop. C.4, not sample quality.
*Overreach:* novelty — the fact list wins it (0.988 / 0.943 vs 0.917 / 0.914)
and that sentence must be printed; "better generator" unqualified.

**R-B. Operating envelope (RQ7).** *Hypothesis:* a deterministic canonical
program has no search frontier. *Print:* 0 of 7,776 sweep instances censored
at 60 s, including all 427 with `|Aut| ≥ 10⁷`; 8,951 of 8,951 real members
canonicalised at 0.60–0.70 ms median; the full 3,988 × 3,988 matrix in 1.39 s
against 28.9 min for the search form (1,252×, one alphabet, one code path);
censoring is monotone in the fact count `m`, not the constant count.
*Scope:* the cost comparison is `w°` against `w*_c`. *Overreach:* **any speed
claim against nauty or its certificate** — at matched tokenisation they are at
parity (1.09–1.19×), and the rows arm was timed through a Python loop that
inflated it 20× in our favour (T-KBy, unfixed). Concede identity speed in the
introduction (L17).

**R-C. Exactness (RQ2).** *Hypothesis:* the word determines the isomorphism
class (Theorem C). *Print:* `w°`: 0 false merges, no member censored, and the
exact partition on three collections — 557 classes over 1,381 members
(NDC-classes), 1,156 over 1,745 (NDC-substances), 3,682 over 3,988
(WD50K(66)) (`rq2_ow_facts.md` §4); NetLSD merges 2,516 / 1 / 185,917
non-isomorphic pairs, HPD 7,618 / 9,885 / 212,179; the bipartite edit-path
merges nothing but splits the true partition: 557 into 574 on NDC-classes,
1,156 into 1,290 on NDC-substances, 3,682 into 3,839 on WD50K(66).
HyperCOT was not measured (its environment never ran). *Scope:* the nauty certificate
is equally exact, and WL had zero merges on these corpora. *Overreach:*
implying WL failed here (its incompleteness is a theorem, not a measurement on
this data), or that exactness distinguishes us from the certificate.

**R-D. Pendant locality (RQ1).** *Hypothesis:* a word that never names a
constant (Prop. C.6) absorbs edits that change the constant inventory in a
constant number of instructions. *Print (fraction within two symbols, `w°` /
certificate rows):* delete a pendant fact 0.732 / 0.000; remove a pendant
constant 0.826 / 0.000; insert a fact with a new constant 0.096 / 0.000.
*Scope:* **pendant only**; these are pooled over three corpora and must be
quoted per corpus from `rq1_statistics_<corpus>.md` (the pooled `w*_c`
deletion 0.771 is WD50K 0.845, NDC 0.576, synthetic 0.090). *Overreach:*
"locally stable" unqualified — on interior argument edits the certificate wins
(0.324 / 0.355 vs our 0.077 / 0.093), pooled it wins (0.179 vs 0.070), and
`w*_c` is more local than `w°` on every insertion cell. If only favourable
results are in the main text, this one still needs its interior clause in the
same sentence: the condition is the result.

**R-E. Valid completion (RQ8).** *Hypothesis:* the prefix property (Prop. C.8)
makes every continuation of a record's program a valid completion, and on
records whose facts share constants the model also places the new fact
correctly. *Print:* proposals valid and connected 1.000 by theorem; on
WD50K(66) non-star records, hidden interior fact, fact-count-matched model
(`ow_ngram_ho_1f`): hit@10 0.048 [0.042, 0.056] against 0.019 [0.014, 0.024]
for item–item co-occurrence, Holm-corrected paired Wilcoxon over 27 seeds
p = 1.3 × 10⁻⁵, rank-biserial 1.000; attachment-miss on one-fact proposals
0.26–0.37 against 0.64 (NDC). *Scope:* relational stratum of WD50K only; the
matched arm is Amendment A1, registered after the pilot and before
re-measurement — say so. *Overreach:* presenting it as a completion method.
Absolute rates are low for every arm; on NDC the recommender wins (0.32 vs
0.19) and on star-shaped records it wins (0.62 vs 0.18), both on pattern
prediction. Those two losses are the scope of the claim and must appear at
least as one clause with a pointer to the supplement.

**R-F. Golden record (RQ3 v2). CLOSED — recommend supplement only.** Measured
on 11 fully covered cells (27 seeds each): the word-space consensus recovers
the source 0.21–0.73 of the time against 0.00–0.10 for the three anonymous
merges (Holm p ≤ 8.3 × 10⁻⁶), its fact distance is below every medoid's (4.90
vs 6.32–8.20), and its certified ratio is at or below the same-metric
medoid's (1.19–1.39 vs 1.26–1.51). **But the pre-registered ablation fails:
the same consensus computed in fact space, with no word, recovers 0.984
against 0.433 and costs less** (H3.5), and the identity oracle is far ahead
(0.921 vs 0.385, H3.3). So the consensus is a property of any complete
invariant plus fact edits, not of the language; a main-text hypothesis "the
language enables the golden record" would be refuted by our own supplement.
Not measured: non-star N = 15; non-star N = 9 at two edits. The star control
(H3.4) rests on a counting baseline that recovers stars only 0.02–0.05 of the
time and must not be quoted before that baseline is audited. If the author
wants it in the main text regardless, the only defensible sentence is the
capability one — a decoded, connected, non-member record with a certified
ratio — followed immediately by the fact-space number.

**Capability table** — the summary exhibit; every cell is now filled
(consensus footnote ¶ carries the fact-space caveat; HyperCOT merges "not
measured"; WL matrix 564 s).

**Compactness** — one sentence at most, and verify first: `prose.md` §2.2 says
"medians of 6 (WD50K) and 8 (NDC) instructions against 12 certificate rows";
T-KBx measured a mean of 13.8 walk tokens against 40 certificate integers on a
400-member WD50K sample. The two are not reconciled.

---

## (d) Supplement only

- RQ5 clustering, both programs — negative for every representation.
- RQ4 anomaly screen — not completed; state that, do not tabulate.
- RQ3 v1 natural NDC quarterly series — consensus ties the medoid, underpowered.
- RQ8 on NDC and on stars, with Amendments A1–A3 and the before/after controls.
- RQ8 H8.3 clause 3 — failed as registered (threshold ported from RQ6).
- RQ1 full table: interior cells, `w*_c`, the rank-keyed walk, ladder
  monotonicity (M2), censoring by symmetry bucket.
- Tail-600 characterisation of `w*_c`'s censored tail.
- The retired fact-rank word and its addressing arms (D-ART4: no main-text row).
- RQ3 v2 ablation arms (Levenshtein median, coverage-first, fact-space
  consensus), judge fallback rates, the heavy cells that did not complete.
- Corpus derivation, exclusion rules and counts (T-KBk, D-KBg1).

---

## (e) Reusable figures, table, notation

**Figures — almost nothing is rendered for this article.**

| exhibit | status | path |
|---|---|---|
| S2H / H2S step figures | exist only for the preprint: Fano plane, unlabelled, search encoder. Usable as a template; a labelled knowledge-base example under `w°` must be redrawn | `…/isalhg/article/preprint/6a31285eea907326ad1128f2/figures/fano_plane_hypergraphx_{s2h,h2s}_steps.pdf` (their generator was not located) |
| worked example (text) | exists | `docs/article/D_ART3/experiments/ENCODINGS_WORKED_EXAMPLE.md` |
| decodability figure (alignment path decoded) | **not rendered**; specified in `START_HERE.md` §6 D8; numbers in `rq6_generation_facts.md` | — |
| envelope figure | **not rendered**; data in `results/frozen/rq7_envelope_2271960_reading/` | — |
| capability table | exists | `docs/article/D_ART3/tables/tab_kb_representation_properties.tex` |
| structure model | IsalSR TPAMI sources | `/media/mpascual/Sandisk2TB/research/ISAL/completed/isalsr/article/arxiv/69b91250e7e60fc6079dfd5d/` |

**Notation and names to enforce.**

- Alphabet `Σ_HG = {V_{i,j}, C_i, P_i, N_i, W}`; `k` = maximum arity; the
  machine state is the circular list plus `k` pointers; `S2H` decodes, `H2S`
  encodes.
- Programs: **`w°`** ordered walk (code arm `isal_ow_struct`); **`w*_c`**
  tie-complete search (code `wstar_orbit` when orbit-pruned); `w*_ρ` rank-keyed
  walk (`wstar_rank`, ablation only). "Canonical program" for the rule,
  "word" for its output.
- Distances: `d_I` = raw Levenshtein on instruction tokens, never
  length-normalised (not a metric, L11). The consensus objective alone uses
  the indel distance `d_indel`.
- "Certificate" has two meanings: nauty's canonical form ("the certificate
  member", arms `nauty_cert` bytes and `nauty_cert_rows`) and the optimality
  guarantee of a representative — call the second "certified ratio" always.
- Domain vocabulary: knowledge base, fact, constant, predicate, type.
  Hypergraph, vertex, hyperedge only where the encoding is defined.
- Corpora: **WD50K(66)** (`wd50k66`): 3,988 members in the envelope, of which
  3,162 have a fact of arity ≥ 3 and 826 are binary; 53.4 % stars.
  **NDC-classes** (`ndc_classes`): 1,381 members; 519 dropped at the arity cap
  and 51 below three facts; 3.0 % stars. Controls `wd50k100`,
  `ndc_substances` (1,745). The supplement file still prints 3,167 / 1,432 /
  2,222 — **do not copy counts from `supplementary_data.md`**.
- Strata: *star* (every fact contains one constant and no other constant is
  shared) versus *non-star* / relational; edits and hidden facts are *pendant*
  or *interior*.
- Envelope: `n ≤ 24`, `3 ≤ m ≤ 110`, `k ≤ 10`, connected, labelled.

---

## (f) For a writer who has never seen IsalHG

1. A knowledge base is written as a program for a small pointer machine; a
   canonical program gives one word per isomorphism class; Levenshtein on
   words is then a metric on isomorphism classes; every word decodes to a
   connected knowledge base. That last sentence is the paper.
2. The nearest competitor is nauty's certificate plus Levenshtein. It is
   exact, a metric, polynomial and faster at identity. It is not a language.
   Every claim should be checked against "would the certificate also give
   this?"; if yes, it is a property of the family, not a contribution.
3. nauty is inside our encoder (it supplies the order `w°` follows). Say it
   once, plainly: nauty decides which constant comes first, the language
   decides what is written.
4. The measured pattern across every task contest: where a record's structure
   is a multiset of fact patterns (stars), counting wins; where constants are
   shared across facts, the language wins, on attachment and on validity. A
   main text that reports only the wins is defensible if each win carries its
   scope in the same sentence; it is not defensible if a scope condition is
   moved to the supplement.
5. Not claimed anywhere: a faster isomorphism test, an edit-distance proxy,
   scaling beyond the envelope, argument roles (facts are sets, R4), disconnected
   knowledge bases (R3).
6. Every experiment after 2026-09-13 was pre-registered with gates and
   fallbacks, and three results changed sign under amendments made in the
   baseline's favour. That history is an asset: state amendments where they
   apply.
7. Open on the engineering side and visible to a reviewer: the certificate-rows
   timing defect (T-KBy), the supplement's stale counts (D-KBg1, T-KBk), the
   unmerged integration branch.
