# Final review of the merged TKDE draft

**From:** `[IsalHG-Fable-Review]`, 2026-10-04. **Draft:**
`…/isalhg/article/journal/6a788a680cdbdddd16e47a6e/submission/article/`
(`sections/*.tex`, `tables/*.tex`). One line per problem:
`file:line → problem → fix`. Severity tags: **[A]** a reviewer or our own
supplement contradicts the sentence; **[B]** scope wider than the evidence;
**[C]** sourcing or minor. Style not reviewed.

**Numbers.** 307 measured values were checked against the cited fact bases
and the frozen RQ1 statistics. Every printed value agrees with its source
except one rounding slip (discussion.tex:12). The ordered walk's census
(557 / 1,156 / 3,682, 0 merges, 0 censored) is attributed correctly, and
530 / 1,086 / 3,677 appears nowhere.

---

## sections/abstract.tex

- abstract.tex:21–22 → **[B]** "the distance matrix of 3,988 records takes 1.39 s" stands alone and reads as a speed claim; the paper's own scope is "against the search form, parity with the certificate" → append "against 28.9 min for the search-based form of the same language", or drop the timing.
- abstract.tex:4 → **[C]** the src cites `rq2_wellposedness_facts.md §1` (the search form's census) for a claim about the ordered walk → cite `foundation/rq2_ow_facts.md §4.1`; add the derivations 5,369 = 3,988 + 1,381 and 540,000 = 2 × 270,000.
- abstract.tex:7–8 → **[C]** "choosing its reference record" is listed among the operations that need the language; the paper only ships a medoid, which needs a metric and nothing else → keep, but do not let it read as a language result (the golden record is in the supplement and its word-space version loses to a fact-space one).

## sections/introduction.tex

- introduction.tex:35 → **[A]** "No existing dissimilarity provides the five together" implies ours does. It provides P1–P4 by construction and P5 only for pendant removals (properties.tex:179–180 says so) → add one sentence here: "ours provides P1–P4 by construction and P5 for pendant removals only (§8.2)".
- introduction.tex:68–71 and conclusion.tex:20 → **[A]** "this addition matters most for records whose facts share constants" contradicts Supplement S5: NDC-classes is 97 % relational and the recommender wins hit@10 there (0.32 vs 0.17). The measured statement is narrower → "on the relational records of WD50K(66) the word model proposes the missing fact more often; on NDC-classes and on stars counting leads, although the word model attaches better wherever attachment is not fixed".
- introduction.tex:92–93 → **[A]** "against edit-distance, feature-map, spectral, portrait, **transport** and certificate competitors": HyperCOT was never scored (setup.tex:61–62 and tab_capability.tex:60 say so; its environment failed in every run) → delete "transport" or write "and, by its published properties only, transport".
- introduction.tex:98–100 → **[A]** "deleting a fact or a constant from a record moves its word by at most two instructions in 59–88 % of cases" omits the condition. The figure is for **pendant** removals; interior fact deletion is within two in under 15 % of cases (Supplement S3) → "deleting a pendant fact, or a constant's last occurrence, …".
- introduction.tex:101–102 → **[B]** "completions over words attach the missing fact correctly more often than co-occurrence recommenders" is true and reads as "completion wins" → add "and propose the true fact more often on WD50K(66), not on NDC-classes".
- introduction.tex:74–76 → **[C]** "complete isomorphism invariant for labelled n-ary KBs" → add "connected" (the theorem's domain, properties.tex:35).
- introduction.tex:86–88 → **[C]** contribution 3 lists the census and the certified medoid, which the certificate provides equally (discussion.tex:40–41, operations.tex:54–55 concede it) → add "the first two hold for any complete invariant" so the list does not overclaim.
- introduction.tex:77–100 → **[C]** no `% src:` line in the whole file; all values are correct → add them (rq7 §1, §8; rq2_ow §4.1–4.2; rq6 joint rate; rq1_statistics regime 0).

## sections/results.tex

- results.tex:53–56 with setup.tex:83–85 → **[A]** H2 is written as a prediction ("should therefore leave … in place") and setup states that every hypothesis was fixed before its campaign. For locality that is not so: the registered hypothesis was that the ordered walk is the most local program (falsified on insertions), and the pendant / interior axis was found in the campaign's results. A reviewer who asks for the registration will see it → in setup.tex:83–85 restrict the statement to exactness, generation and completion, and say the pendant/interior distinction "was identified from the locality measurements and is reported as observed"; in results.tex:53 replace "Hypothesis H2 … should therefore" by a statement that Proposition (name-freedom) explains the observed removal locality.
- results.tex:198 → **[B]** title "Completions Are KBs and Attach Correctly on Relational Records": the matched models still misplace 0.84–0.85 of correct patterns on WD50K(66) → "… and Attach More Often Correctly …".
- results.tex:203–207, discussion.tex:8–14 → **[B]** the attachment advantage is credited to "a model over words". The fact-list n-gram, a sequence model over the baseline serialization, has attachment miss 0.30 on NDC-classes (tab_completion.tex:39), level with ours (0.31–0.37). Attachment is a property of sequence models over a serialization; what the language adds is that every proposal is a connected KB → say so, and keep "two families" as sequence models versus counting.
- results.tex:83–85 → **[B]** the examples "a product leaving a drug class or a retracted statement" are pendant only when the removed constant disappears from the record; an interior removal is not local (S3) → add "when the removed constant occurs nowhere else in the record".
- results.tex:129–133, discussion.tex:38, setup.tex:98–99 → **[C]** "1.09 to 1.19× … on 400 members": 1.19× is on 400 members, 1.09× on the 500-member tokenisation sweep; the source section does not record "workstation" → "on 400–500 members", and cite where the machine is recorded or drop the word. In discussion.tex:38 add "in a micro-benchmark".
- results.tex:216–217 → **[C]** "registered after a pilot and before re-measurement": it was also after the first full run of the free-running sampler; lines 241–243 report that honestly → make 216 read "after the first measurement and before re-measurement" so the two sentences agree.
- results.tex:61–77 → **[C]** src paths lack the `foundation/` prefix and the absolute path of the `rq1_statistics_*.md` files.
- results.tex H1, H3, H4: none.

## tables/tab_capability.tex

- tab_capability.tex:26 → **[C]** "Every entry is measured or follows from a stated result", but the header says *Pair cost* is reasoning → "…, or, for pair cost, is the standard complexity".
- tab_capability.tex:36, 73 → **[B]** the only locality column is pendant fact deletion, the most favourable cell; the caption says so, but the table is the paper's summary of itself → add to the caption "on interior argument edits the certificate is more local (Section S3)".
- tab_capability.tex:85 and language.tex:184–185 → **[C]** both cite the preprint for the completeness proof of the search form. The local preprint sources contain that proof only in the revised version (conjecture replaced by theorem) → make sure the cited arXiv version is that revision, or cite the supplement.
- tab_capability.tex:70 → **[C]** src says `rq2_wellposedness_facts.md §1 (… 3,983 members)`; 3,983 is in `foundation/rq2_ow_facts.md §4.1` → re-point. tab_capability.tex:27: 7,949,355 has no `% src:` line.
- Row values (merges, floors at 291,227 / 201,010, assignment 201,010, locality cells): none. The identical 201,010 for the assignment value and the degree-sequence floor is real, not a copy error.

## tables/tab_completion.tex

- tab_completion.tex:28–30 → **[B]** bold marks our WD50K(66) cells only; in the NDC-classes and star columns the best values (0.319, 0.624) are the recommender's and are not bold → bold the best value per column, or state "bold: ours".
- Numbers: none.

## sections/discussion.tex

- discussion.tex:65–67 → **[A]** "weak for every representation we tested, ours included, with adjusted Rand index below 0.08" contradicts the record: the search form `w*_c`, which is in the capability table, scored 0.156 / 0.171 / 0.063 in the earlier clustering run (ledger T-KBad, open, unexplained; possibly its censored-member subset) → restrict to "every representation in the run reported in Section S7, which does not include the search form", and resolve T-KBad before S7 is written.
- discussion.tex:12 → **[C]** "0.72 against 0.31": the source gives 0.3176 and 0.3106 → "0.31 to 0.32".
- discussion.tex:42–43 → **[B]** "no model over certificates generates or completes KBs" is too strong; a model can sample certificates and reject → "without a rejection step" or "with a validity guarantee".
- discussion.tex:16–20, 34–41, 50–63: none.

## sections/setup.tex

- setup.tex:83–85 → **[A]** see results.tex:53–56 above.
- setup.tex:37–38 → **[A]** "our claims are stated for the relational one" is true only for WD50K(66); NDC-classes is relational and loses → "for the relational stratum of WD50K(66); NDC-classes, almost entirely relational, is reported beside it".
- setup.tex:36–37 → **[C]** "counting methods are likely to tie … on stars": measured, counting wins (0.62 vs 0.18) → "tie or win".
- setup.tex:50 → **[B]** "We compare against every family that offers a distance on KBs": graph kernels and learned embeddings are not included → "the families of Table III".
- Numbers (22 checked): none.

## sections/conclusion.tex

- conclusion.tex:16–17 → **[B]** bare "1.39 s" again → add the comparator or drop.
- conclusion.tex:20 → **[A]** see introduction.tex:68–71.

## sections/properties.tex, operations.tex, problem.tex, language.tex, related_work.tex

- problem.tex:88–91 → **[C]** "§8.2 measures P5" is correct; pair it with the fix at introduction.tex:35 so the reader is not left to infer that P5 holds.
- properties.tex, operations.tex, language.tex, related_work.tex: none found on scope. operations.tex:54–55 ("nothing in the proposition is specific to words") and properties.tex:172–180 (no edit-distance proxy, no Lipschitz bound) are the right concessions.

## tables/tab_locality.tex, tab_generation.tex, tab_corpora.tex

- Numbers: none. Paths in the src comments lack `foundation/` and `WRITING_BRIEF_2026-10-04.md`.

---

## Against the supplement (S3, S5, S6)

- **S3 (interior edits, `w*_c`).** Consistent with results.tex:76–82 and discussion.tex:56–58. Inconsistent with introduction.tex:98–100 (above).
- **S5 (completion on NDC-classes and stars, amendments).** Consistent with results.tex:245–253 and tab_completion. Inconsistent with introduction.tex:68–71, conclusion.tex:20 and setup.tex:37–38 (above).
- **S6 (golden record).** Nothing in the main text contradicts it. Keep it that way: no sentence should say the language enables consensus, since the fact-space consensus recovers 0.984 against 0.433 for the word-space one.
