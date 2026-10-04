# Framing check of `ARTICLE_WRITING_PLAN.md` — §4 and §7 "§8 Results"

**From:** `[IsalHG-Fable-Review]`, 2026-10-04. One line per item that misstates
a number or a scope; items not listed are "none". Numbers were checked against
`foundation/*_facts.md` and
`results/IEEETKDE/RQ1_isal/merged/rq1_statistics_<corpus>.md`. The plan itself
was not edited.

## §4 Framing rules

- **Rule 1.** "Fixed before each campaign" is not literally true everywhere,
  and the amendments named are incomplete. Name all of: RQ8 A1 (fact-count
  matching), **A2 and A3** (two repairs of the counting baseline's attachment,
  both in the baseline's favour); and for the golden record, the objective
  (indel median) fixed after the pilot and before the campaign, and the
  **judge budget lowered for the heavy cells after the first pass had already
  produced rows for other cells** (second tag; affects only the fact-distance
  column, not exact recovery).
- **Rule 3.** The list of scoped-out losses lacks one: against our *own*
  search form, `w°` is less local on every insertion cell (pooled 0.096 vs
  0.223 on insert-with-new-constant). It belongs in Supplementary Table S3
  with a clause in §8.2.
- Rules 2, 4, 5, 6, 7, 8: none.

## §8 Results

- **H1 (exactness).**
  (i) 530 / 1,086 / 3,677 is the **`w*_c`** partition, and its NDC-substances
  figure is over 1,661 of 1,745 members (84 censored under `w*_c`). `w°` covers
  all 1,745, so its class count can differ; do not pre-fill these three numbers
  for `w°`.
  (ii) "splits 557 true classes into 574": the fact base does not say on which
  collection or member subset, and 557 matches none of the three partitions.
  Hold the count until `rq2_ow_facts.md` §4 states its denominator.
  (iii) "38 % asymmetric, 1.4 % triangle violations" were measured on random
  pairs in a probe (`probes_2026-09.md` §2), not on these collections. Say
  "on random pairs" or move the sentence to §5.
- **H2 (pendant locality).** Table values verified. **Scope misstatement:**
  the hypothesis and the "practical reading" claim records that *gain or lose*
  a constant. Measured, removals are local (0.59–0.88 within two, median 1);
  pendant **insertion is not** (0.152 / 0.042 within two, median 7 / 12). It
  is ahead of the certificate (0.000) but not "within a few instructions".
  Restrict "absorbed locally" to removals and state insertion as "more local
  than the certificate, not local".
- **H3 (envelope).** "Its cost should not depend on symmetry" overstates: the
  labelling call is nauty's, whose worst case does depend on symmetry. Write
  "inherits the labelling engine's cost and adds a linear emission; no
  instance of the sweep was censored". The parity range 1.09–1.19× comes from
  local micro-timings; the cluster time of the certificate-rows matrix
  (13.87 s) is inflated by a loop defect and must not be printed.
- **H4 (generation).** Numbers: none. Cite "426,433 of 426,433 ball words" as
  a pilot check of the consensus experiment, not as a campaign result.
- **H5 (golden record).** **Neither Variant A nor Variant B is safe as a
  main-text hypothesis.** H3.1 and H3.2 hold on the 11 complete cells, but
  the pre-registered ablation H3.5 fails: a fact-space consensus with no word
  recovers 0.984 against the word-space 0.433, at lower cost. The hypothesis
  "Proposition 2 makes … a consensus over word balls" is therefore not what
  the data support; the consensus needs a complete invariant, not the
  language. Recommendation: move H5 to the supplement and renumber. If kept,
  print the fact-space number in the same paragraph. Also: "already citable …
  1.000, both corpora, both strata" was measured on 10 families per cell at
  N = 5 in a pilot, and NDC-classes has no star stratum; the star control
  (pattern vote) recovers stars 0.02–0.05 of the time and is unaudited — do
  not quote H3.4. Source: `foundation/rq3v2_facts.md`.
- **H1, resolved by P1.** Print for `w°`: 557 classes / 1,381 members,
  1,156 / 1,745, 3,682 / 3,988, 0 false merges, 0 censored
  (`rq2_ow_facts.md` §4). The bipartite split is 557 → 574 on NDC-classes
  (all members), 1,156 → 1,290 on NDC-substances, 3,682 → 3,839 on WD50K(66).
  Items (i) and (ii) above are closed by these numbers; (iii) stands.
- **H6 (completion).**
  (i) 0.048 [0.042, 0.056], rank-biserial 1.000 is the **order-6 secondary
  model**; the primary matched model (the order used for generation in H4) is
  0.046, Holm p = 1.33 × 10⁻⁵, rank-biserial 0.989. Name the model, or print
  the primary.
  (ii) "Fixed before re-measurement" is true and incomplete: as originally
  registered (free-running sampler) the hypothesis was not supported on either
  corpus (WD50K 0.015 vs 0.019, a tie). One clause must say so, or the
  supplement will contradict the main text.
  (iii) The baseline numbers mix two attachment constructions: 0.019
  (WD50K relational) is its interior-first attacher, 0.62 (stars) its
  data-driven attacher. State "against the baseline's better construction in
  each stratum".
