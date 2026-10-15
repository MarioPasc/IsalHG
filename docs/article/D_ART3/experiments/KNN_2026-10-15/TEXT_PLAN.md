# TEXT_PLAN — a lighter TKDE main text, and the slot for the kNN / k-medoids experiment

Plan only; nothing in the Overleaf clone was edited. Written 2026-10-15 (08:10–08:35 CEST) by the writing agent (`claude-opus-5-5`, xhigh) for `main`, on the draft as pushed (Overleaf `main` `97d1e76`, `…/6a788a680cdbdddd16e47a6e/submission/article`) and its supplement. `LOG.md` §5 held no probe result yet, so every H4 item below is **conditional on the kill criterion of LOG §3** (fallback in §4.6).

## 0. Recommendation
1. Compress the prose by **−1,609 words (−18.9 %)** of the 8,520 prose words outside proofs and definitions; mathematics, theorem statements and scope qualifiers stay. The P1+P2 cuts alone give −1,456 (−17.1 %).
2. Place the new experiment as **H4 "Representatives"** at §8.4, between cost (H3) and generation (which becomes H5), the row order Table I already has.
3. Move the **hidden-fact recovery of completion** (current H5, Table VII, Alg. 3) to S4; its validity result stays as one sentence in the generation subsection.
4. Figures: the new **Fig. R** (figure\*, one row), **F1** (partition recovered; replaces H1's number paragraph) and **F2** (draws per usable KB; replaces Table VI).
5. Expected length **12.2–12.4 pages** (12.6 if only 75 % of the cuts land). Keep the 1.4–1.8 pages of slack as the reserve for the revision round.

## 1. Diagnosis
### 1.1 Page fill (`pdftotext -bbox`; one column ≈ 700 pt)
- 14 pages. On p14 the right column ends at y = 621 of 747 pt: **0.18 column (0.09 page) of slack**, 13.91 pages used.
- The 28 columns: front matter 1.05 · floats 5.34 · acknowledgments, data, references, biographies 2.21 · slack 0.18 · running text 19.2 for 9,620 section words (prose + formal) → **≈500 words/column, 1,000–1,100 words/page** (writing plan §6 assumed 950). All page estimates use this rate (±10 %).

### 1.2 Words per section
*detex* = `detex sections/X.tex | wc -w` (follows `\input`, so floats included); *prose* = comments, theorem-like environments, proofs, algorithms and figures removed; *num/100w* = numerals per 100 prose words; *>35w* = sentences over 35 words.

| § (pages) | detex | prose | formal | num/100w | >35w |
|---|---|---|---|---|---|
| 1 Introduction (1–3) | 1,894 | 1,351 | 0 | 1.6 | 9 |
| 2 Related Work (3) | 563 | 563 | 0 | 0.0 | 2 |
| 3 Problem Setting (3–4) | 719 | 498 | 221 | 0.2 | 2 |
| 4 Instruction Language (4–6) | 1,495 | 1,290 | 106 | 0.4 | 6 |
| 5 Properties (6–7) | 1,182 | 508 | 674 | 0.2 | 1 |
| 6 Collection Operations (7–8) | 629 | 530 | 99 | 1.1 | 1 |
| 7 Experimental Setup (8–9) | 1,173 | 816 | 0 | 5.0 | 2 |
| 8 Results (9–12): H1 257 · H2 506 · H3 243 · H4 311 · H5 341 | 2,460 | 1,820 | 0 | 10.9 · 7.5 · 11.5 · 7.7 · 8.8 | 6 |
| 9 Conclusions (12–13): Impact ≈430 · Limitations ≈554 | 1,144 | 1,144 | 0 | 4.0 | 9 |
| **Total** (abstract 245/250; back matter 84; biographies 159) | 11,259 | **8,520** | 1,100 | — | 38 |

### 1.3 Floats (cost in columns; a full-width float costs both columns)
| Float | Page | Width | Cost | Float | Page | Width | Cost |
|---|---|---|---|---|---|---|---|
| Fig. 1 overview (TikZ) | 2 | col | 0.39 | Tab. IV capability | 10 | full | 0.77 |
| Tab. I map | 2 | col | 0.28 | Tab. V near-dup | 10 | col | 0.35 |
| Tab. II alphabet | 4 | col | 0.26 | Fig. 3 envelope | 11 | col | 0.36 |
| Alg. 1 decoder | 5 | col | 0.30 | Tab. VI generation | 11 | col | 0.27 |
| Alg. 2 ordered walk | 5 | col | 0.33 | Fig. 4 corridor | 11 | col | 0.49 |
| Fig. 2 worked example | 6 | full | 0.70 | Tab. VII completion | 12 | col | 0.34 |
| Alg. 3 completion | 8 | col | 0.25 | Tab. III corpora | 8 | col | 0.25 |

Total 5.34 columns = 2.67 pages: 4 figures take 1.94 columns, 7 tables and 3 algorithms 3.40. The Results section carries 1.3 columns of tables and one data figure (Fig. 3); Fig. 4 is an illustration.

### 1.4 Where the reading is heaviest
- **H1 numbers** (results.tex L25–41): 18 counts in four sentences (10.9 numerals per 100 words); a reader cannot rank the representations from prose.
- **H2 design and result** (L75–108): 310 words, four sentences over 35 words; the eight MRRs appear in text and in Table V.
- **H5** (L213–257): 341 words explaining three protocol amendments and two attachment rules for a hit@10 below 0.05.
- **Introduction ¶5** (L68–86, 234 words) restates the machine of §4.1 and holds a 49-word sentence ("Because every word…").
- **Contributions** (L102–143, 327 words): "41–69 %", "1.39 s vs 28.9 min" and "212,179" each appear four times (abstract, introduction, results, conclusions).
- **The operation→property map** is stated three times: introduction ¶2, Table I, problem.tex L87–92.
- **Conclusions**: mean sentence 24.5 words (paper ≈20); 9 sentences over 35 words.

## 2. Cut list (C = compress, M = moves with H5, A = addition; P1 must, P2 should, P3 could)
Every cut keeps the mathematics, the theorem-like statements and every scope qualifier. A qualifier may move into a caption or table note, never into the supplement (writing plan §4 rule 2).

| ID | Where | Passage → action | Words | Δ | Pr |
|---|---|---|---|---|---|
| I1 | intro L6–17 | three uses of small KBs → one sentence per case | 133→95 | −38 | P2 |
| I2 | intro L19–36 | five operations → one clause per property (the spine); drop the sentence announcing Def. 3.3 | 188→145 | −43 | P2 |
| I3 | intro L38–51 | competitor families → one sentence per family naming its missing property | 138→95 | −43 | P1 |
| I4 | intro L53–64 | certificate and samplers → keep the P4/P5 failure and the single "to our knowledge" (rule 8) | 127→100 | −27 | P2 |
| I5 | intro L68–91 | "We close this gap" → drop the machine internals (in §4.1) and the 49-word sentence; keep nauty's two roles, "P1, P2, P4 proved; P3 once canonicalized; P5 measured", and the identity-speed concession as one sentence (rule 4) | 282→200 | −82 | P1 |
| I6 | intro L95–100 | prose tour of Table I → one sentence | 62→25 | −37 | P1 |
| I7 | intro L102–143 | contributions → one number per item; drop the repeated 1-in-578 | 327→247 | −80 | P1 |
| I8 | intro L145–155 | keep the delta to the preprint; drop the roadmap | 94→55 | −39 | P2 |
| R1 | rw L16–28 | WL/NetLSD/HPD/HyperCOT → drop what intro ¶3 states | 120→85 | −35 | P2 |
| R2 | rw L43–52 | SELFIES/GraphRNN → drop the restated canonical-string gap | 109→75 | −34 | P2 |
| P1 | problem L44–50 | star/pendant definitions → tighten the examples | 97→80 | −17 | P3 |
| P2 | problem L65–68 | "The first three need… the last two…" → cut | 45→15 | −30 | P2 |
| P3 | problem L87–92 | third copy of the map → keep "P5 is empirical…" and the pointers | 73→30 | −43 | P1 |
| L1 | lang L11–21 | machine: informal paraphrase overlaps the formal state → keep the formal state | 188→155 | −33 | P2 |
| L2 | lang L150–161 | emission cost → keep P3 / no end-to-end claim; trim restated counts | 121→100 | −21 | P3 |
| L3 | lang L163–168 | prose tour of Fig. 2 → into the caption | 67→30 | −37 | P2 |
| L4 | lang L186–204 | §4.4 → keep w\*c's definition, "no claim rests on its completeness", orbit pruning → S1, the two roles in one sentence; cut the repeat of closure/prefix | 213→140 | −73 | P1 |
| Pr1 | prop L7–10 | section opener | 41→25 | −16 | P3 |
| Pr2 | prop L135–138 | bridge to Prop. 5.9 | 45→25 | −20 | P3 |
| Pr3 | prop L152–169 | what name-freedom buys → keep the rank-addressed argument; the exact star bound becomes one clause + S1 | 230→160 | −70 | P2 |
| O1 | ops L35–40 | §6.3 restates P5 → two sentences | 65→35 | −30 | P2 |
| O2 | ops L73–80 | §6.5 generation | 85→60 | −25 | P3 |
| S1 | setup L10–33 | filter counts (519, 51; 3,162/826) → Tab. III note; operating range stays in text (rule 5) | 240→165 | −75 | P2 |
| S2 | setup L55–73 | competitors → Tab. IV carries the properties; keep exact HGED capability-only, both certificate serializations and why, HyperCOT unscored, the floors | 181→120 | −61 | P1 |
| S3 | setup L105–114 | implementation | 83→65 | −18 | P3 |
| Re1 | res L8–11 | opener | 37→20 | −17 | P3 |
| Re2 | res L16–48 | H1 → F1 carries the 18 counts; text keeps 0 merges / true partition, "up to 212,179", edit-path splits + non-metric in one sentence, the WL caveat (rule 5) | 257→125 | −132 | P1 |
| Re3 | res L55–63 | H2 hypothesis re-derives Prop. 5.9 | 90→55 | −35 | P2 |
| Re4 | res L66–72 | P5 measured | 85→70 | −15 | P3 |
| Re5 | res L75–93 | H2 design → tie rule, radius-2 definition and the competitor list into the Tab. V caption | 190→120 | −70 | P1 |
| Re6 | res L96–108 | H2 result → MRRs live in Tab. V; text keeps hit@1 range, best-competitor range, Holm p, rank-biserial, certificate < 0.07, radius 2 | 120→75 | −45 | P1 |
| Re7 | res L125–155 | H3 → trim the hypothesis restatement; keep the snapshot caveat and the re-run over 1 h | 243→185 | −58 | P2 |
| Re8 | res L174–204 | generation → F2 carries the joint rates; keep 270,000/270,000, novelty, GRU + S3 | 260→175 | −85 | P1 |
| Co1 | concl L4–16 | summary repeats the abstract | 141→100 | −41 | P2 |
| Co2 | concl L21–42, 53–59 | impact: deduplication, near-duplicates, synthetic → one property + one result + one citation each | 255→190 | −65 | P2 |
| Co3 | concl L44–51 | representatives impact | 75→60 | −15 | P2 |
| Co4 | concl L134–137 | Untested uses → drop the certified-ratio sentence once H4 passes; keep entity types (ARI < 0.08) | 34→30 | −4 | — |
| M1 | ops L85–117 | §6.6 → operation, guarantee (Prop. 5.8) and cost in ~60 words; Alg. 3 → S4 | 135→60 | −75 | M |
| M2 | setup L36–40 | stars paragraph motivating H5's stratum → delete (Tab. III keeps the star column) | 70→0 | −70 | M |
| M3 | setup L96–100 | the three completion amendments → S4 | 35→0 | −35 | M |
| M4 | res L213–257 | H5 → S4; one sentence + pointer stays (§5) | 341→45 | −296 | M |
| M5 | concl L61–69 | completion impact → structural guarantee + S4 | 90→40 | −50 | M |
| M6 | concl L119–131 | Limitations gen./compl. → generation kept; completion one clause + S4 | 160→75 | −85 | M |
| M7 | intro L139–142 | completion sentence of contribution 4 | 45→0 | −45 | M |
| A1–A7 | various | new §8.4 (+310); intro contribution (+35); op (iii) as k groups (+15); §6.4 PAM sentence (+20); setup pre-registration (+20); summary (+15); impact result (+20) | — | +435 | A |

**Totals.** P1 −751 (−8.8 %) · P2 −705 · P3 −153 → **C −1,609 (−18.9 %)** · M −656 · A +435 · **net 8,520 → 6,690 (−21.5 %)**.

## 3. Figure plan
### 3.0 Conventions for every new figure
- **One palette.** Figs. 3–4 already use Okabe–Ito with ours `#0072B2` (`fig_envelope.py` `ARMS`, `fig_corridor.py` `C_OURS`); the C8 palette (`#2a78d6 #eb6834 #1baf7a #eda100`) survives only in S2 Fig. S1. Use Okabe–Ito: ours `#0072B2`; competitors `#D55E00`, `#009E73`, `#E69F00`; floors and "other" `#8C8C8C`. No existing figure is regenerated.
- **One encoding per job.** Position = the measured quantity; colour = representation (ours always blue); marker = collection (○ NDC-classes, □ NDC-substances, △ WD50K(66), ◇ WD50K(100)). No dual axes; log axes labelled; an explicit zero where the axis cannot show one.
- **Grey and type.** Every series is told apart by shape, line style or a direct label (check with `gs -sDEVICE=pnggray`). Fonts ≥ 7 pt; no in-plot titles; captions ≤ 60 words with what to see and the scope; vector PDF; a `% src:` line above each `\includegraphics`.

### 3.1 Fig. R — new experiment (figure\*, top of the page holding §8.4; one row, ≈0.24 page)
- **(a)–(d) t-SNE of partial copies**: 12 sources × 6 copies of WD50K(66) at r = 2; the first 12 sources of the seed-0 sample, not hand-picked. Precomputed distances; same perplexity and seed; `init='random'`; no ticks.
  - Panels follow a rule fixed before plotting: w°; certificate rows (the exact competitor); the best competitor by 1-NN accuracy at r = 2; the degree-sequence floor.
  - Membership is drawn as thin grey spokes from each copy to its source's centroid, which reads in grey. Source is colour × shape (4 hues × 3 shapes), the one stated exception to the colour rule. A black ring marks each k-medoids medoid.
  - A corner label gives 1-NN accuracy and ARI computed on the full distance, not on the embedding.
- **(e)–(f)**: the word's lead over the best competitor in 1-NN accuracy (e) and k-medoids ARI (f) against r ∈ {1,2,3}. BCa 95 % CI of the paired difference over 27 seeds; one line per collection, labelled at its end; dashed zero line. "Lead > 0 everywhere" is exactly the kill criterion. Absolute values go to Tab. IV ("Groups") and to S2.
- **Data.** The KNN run of this folder (LOG §5; path filled at freeze). Needed in one JSON: the per-panel embeddings; per (collection, r, representation) 1-NN, ARI and CIs; the paired-difference CIs; cost(M)/LB per cluster (§4.3).
- **Replaces** nothing: it is new evidence, with +310 words of prose (§4). Variant: two rows with larger panels, 0.40 page (affordable, §6).

### 3.2 F1 — "Partition recovered by each distance" (column, §8.1, ≈0.28 column)
- **Shows** a dot plot. x = classes found ÷ true classes (linear, 0–1.15), reference line at 1 = true partition; left of 1 merges, right of 1 splits. Rows: 11 representations sorted by the WD50K(66) ratio; one marker per collection; the w° row is blue.
- **Reading.** w°, both certificates, the fact list and WL sit at 1. The edit path sits right of 1 (574 / 1,290 / 3,839 classes for 557 / 1,156 / 3,682). HPD reaches 782/3,682 = 0.21, the size floor 194/3,682. The caption keeps "up to 212,179 merged pairs" and the WL caveat.
- **Data** (existing): `docs/article/D_ART3/foundation/rq2_ow_facts.md` §4.2, table at L131–145 (11 arms × 3 collections; true classes 557 / 1,156 / 3,682). Asymmetry and triangle counts: §4.3.
- **Replaces** Re2, H1's 18-number paragraph (results.tex L25–41): −132 words.

### 3.3 F2 — "Draws per usable KB" (column, §8.5, ≈0.23 column, replaces Tab. VI at 0.27)
- **Shows** x = draws per valid and connected KB, log10 axis from 1 to 2 × 10⁴. Two row groups, n-gram and GRU, each with w°, fact list and incidence list; markers ○ NDC-classes, △ WD50K(66).
- **Reading.** w° = 1 in all four cells (540,000/540,000 GRU; 270,000/270,000 per collection n-gram); the incidence n-gram needs 578 and 11,739 draws.
- **Data** (existing): `foundation/rq6_generation_facts.md`, joint-rate table at L55–59 (one usable in 2 / 8 / 578 / 11,739); `results/NEWPOS_2026-10-13/neural_gen/stats.json`, `cells[*].usable_per_draw` with BCa (fact list 0.700 / 0.086).
- **Replaces** Tab. VI and the rate sentences of Re8 (−85 words). The "New" column becomes one clause; the fact-list 0.988/0.943 stays in Limitations.

### 3.4 Considered, not planned
Matrix-time panel (c) on Fig. 3 (−55 words, +0.05 column; the fallback if F1 is dropped) · the C8 dot plot (S2 Fig. S1) instead of Tab. V (+0.1 page, fits the reserve) · Fig. 4 as a 2 × 3 grid (−0.15 column).

## 4. Where the new experiment goes in the narrative
### 4.1 Label and place
- **Renumber in operation order.** The new experiment becomes **H4 at §8.4**, after H3 (cost); generation becomes H5 (§8.5). Reasons: Table I already lists Deduplication, Near-duplicate, Every comparison, **Representative**, Generation, Completion; the introduction promises "the experiments follow the operations"; and metric operations then precede language operations.
- **Alternative** (no renumbering): H6 at §8.6. Only if H5 stays in the main text; it puts representatives after completion.
- **Title.** "H4: Representatives: Partial Copies of One Record Share a Medoid" (design A: "… Versions of One Record …"). There is no sixth operation: kNN is the classification reading of the same neighbourhoods, reported inside H4.

### 4.2 Hypothesis sentence (draft; fix once the LOG §3 verdict is in)
> *Hypothesis H4.* A representative needs P2: under a metric, the medoid of a group carries the certified ratio of \cref{prop:certified}, and k-medoids returns one such medoid per group. Good groups also need P5. Partial copies of one record, each missing up to $r$ statements removed with their own values, differ by pendant edits, so under $\dI$ they should lie closer to one another than to copies of other records: k-medoids should recover the source of each copy, and the nearest neighbour of a copy should be a copy of the same source.

Scope sentence after it: "The certified ratio holds under any metric, the certificate's included; the hypothesis concerns the groups."

### 4.3 What the main text needs from the run (to the engineer via `main`)
- **cost(M)/LB per k-medoids cluster**, which LOG §2 does not record. It costs nothing beyond the matrices. Without it, H4 tests clustering, not the representative operation, and "Untested uses" cannot be dropped. Report it for every metric and pseudometric; for the edit path report "no certificate" (not a metric).
- **Fixed before plotting:** the display rule of §3.1, and the paired-difference CIs.
- **Which design leads.** Prefer **design A** if it survives: real NDC versions are ground truth that we did not construct. Design B is a constructed regime next to H2; if only B survives, call it "partial copies of real records" and state the empirical-mix result (H-KNN-mix) as a scope clause.

### 4.4 Table I and Table IV
- **Table I.** Representative → `P2, metric; P5 for the groups | Cor. 5.5, Prop. 6.1; groups measured | H4`. Generation → `H5`. Completion → `Prop. 5.8 | H5 (validity); S4 (recovery)`. Row order is unchanged, and the caption "H1–H5" stays true.
- **Table IV.** Add a column **Groups** = k-medoids ARI at r = 2 (WD50K(66) / NDC-classes for B; one NDC value for A). The group header "Locality" becomes "Neighbourhoods" over Near-dup. and Groups. Drop the **Family** column (≈2.2 cm) to keep `\textwidth`; rows are already grouped by family. Exact HGED, HyperCOT and w\*c: n.m.

### 4.5 Other edits the slot requires
- problem.tex (iii) → "partition into k groups and return each group's medoid, with a bound on its distance from the best KB".
- §6.4 gains one sentence (A, +20); "Nothing in Prop. 6.1 is specific to words" (L66) **stays**.
- Fig. 1 TikZ: "certified medoid" → "certified medoids (k-medoids)". Contribution 4: +35 words.
- Abstract: one sentence in, 25 words out (stays ≤ 250). Impact "Certified representatives" quotes the H4 result. "Untested uses" keeps only entity types.
- References 29 → 31: PAM (Kaufman & Rousseeuw 1990, DOI 10.1002/9780470316801), ARI (Hubert & Arabie 1985, DOI 10.1007/BF01908075), t-SNE (van der Maaten & Hinton, JMLR 9, 2008); drop GraphRNN.

### 4.6 Fallback if the main-text design is killed (any competitor ≥ word in any cell)
No renumbering; Representative stays "proof only"; H5 stays, compressed by ≈120 words; Alg. 3 still moves to S4 (writing plan §6, lever 1); the experiment goes to S2 as LOG §3 states; F1 and F2 apply unchanged.

## 5. Which experiment moves to the supplement
| H | Evidence | Interest for the argument | Verdict |
|---|---|---|---|
| H2 near-dup | 4/4 collections; Holm p < 10⁻³²; rank-biserial ≥ 0.46 | The only result where the word beats the certificate | keep (core) |
| H4→H5 generation | 270,000/270,000 vs 1 usable in 578 / 11,739; GRU 27/27 seeds | P4 made tangible; visual | keep |
| H3 cost | 0/7,776 censored; 1,252× over w\*c | Justifies the ordered walk over the search form | keep |
| H1 exactness | 0 merges; competitors up to 212,179 | Foundation of deduplication; the certificate ties by design | keep, compress (F1) |
| H5 completion | hit@10 0.046 vs 0.019 (p = 1.3e-5), relational WD50K(66) only, needs fact-count matching; free-running 0.015 vs 0.019 (p = 0.85); loses on NDC-classes (0.32 vs 0.17–0.19) and stars (0.62 vs 0.18) | The most "language" operation, but small absolute rates | **move** |

**Move H5's recovery result to S4, on merit rather than for space** (§6: the plan fits even with H5 kept).
- **For moving.** It is the main text's weakest positive, needs a three-amendment trail, and carries the longest Limitations item (≈160 words). The main text holds positives only (LOG §0), and H4 takes its slot, so five experiments remain.
- **Against.** Completion loses its only main-text test of something beyond validity. The answer: validity *is* the proved, differentiating property (the certificate cannot complete at all), it stays measured, and S4 already holds the strata and amendments.
- **What stays**, at the end of §8.5 (≈50 words): "The prefix property carries validity over to completion: every proposal continued from a record's word was a connected KB containing the record (1.000), against 0.692 connected for the fact list and 0.191 decodable for the incidence list (`% src: foundation/rq8_facts.md §6`). Section S4 reports how often proposals recover a hidden fact."
- Limitations keeps one clause, "hit@10 < 0.05 for every method; the word model leads only on relational WD50K(66) records under fact-count matching (Section S4)", so nothing negative leaves the main text.

## 6. Page budget (1,000–1,100 words per page; floats as measured in §1.3)
| Change | Δ pages |
|---|---|
| Start (p14 slack 0.09) | 13.91 |
| C, all cuts (−1,609 words) | −1.46 to −1.61 |
| M: prose −656 words, Tab. VII −0.17, Alg. 3 −0.12 | −0.95 |
| A: +435 words, Fig. R +0.24, Tab. IV column +0.01 | +0.69 |
| F1 +0.14; F2 replaces Tab. VI −0.02 | +0.12 |
| **Recommended plan** | **12.2–12.4** |
| Only the P1+P2 cuts land / 75 % of all cuts land | 12.4 / 12.6 |
| H5 kept (compressed −120 words, Alg. 3 moved), all to 75 % of cuts | 12.9–13.3 |
| H4 killed (§4.6) | 12.2–12.3 |

- **Every scenario fits 14 pages.** The tightest (H5 kept, 75 % of the cuts) still leaves 0.7 page.
- **Do not fill the slack now.** TKDE charges $200 per page above 14 (hard cap 18), and revision rounds add text. To spend 0.15–0.25 page, the candidates are the two-row Fig. R and the C8 dot plot.
- **Supplement 12 → ≈14 pages.** S4 gains Tab. VII, the design paragraph and Alg. 3 (as Alg. S1). Fold H4's full tables into S2 ("Retrieval, grouping and locality"), so the supplement keeps three experiment sections (author's rule of 2026-10-14) and gets no S5.

## 7. Risks
### 7.1 Claims that a cut could weaken (the text pass must keep them)
- **K1** (I5) the identity-speed concession stays in the introduction (rule 4). **K2** (I4) "To our knowledge" survives once (rule 8). **K3** (Re2) the WL zero "describes these collections and carries no guarantee" (rule 5).
- **K4** (Re2) the edit-path numbers (asymmetric on 44–58 % of 2,000 pairs; 7–26 triangle violations in 5,000 triples) back the "–" in Tab. IV. Move them into note *a* or the F1 caption; never delete them.
- **K5** (Re3–Re6) "pendant" stays in every H2 sentence; "significant on three of four" at radius 2 stays (Tab. V dagger).
- **K6** (Re7) keep "28.9 min from the frozen snapshot; a re-run exceeded 1 h" and "costs are measurements, not bounds".
- **K7** (S1) the operating range (n ≤ 24, 3 ≤ m ≤ 110, k ≤ 10) stays in §7.1, because Limitations "Scope" cites it.
- **K8** setup L93–97 keeps its honesty sentences ("the pendant split emerged from the first measurements"; "radius 2 added afterwards").
- **K9** (H4) a medoid is a *member* under every representation. The certified ratio holds for any metric (the certificate included) and, by the same proof, for any pseudometric relative to its coarser space; only the edit path loses it. Claim the **groups**, never "only the word certifies".
- **K10** (Fig. R) t-SNE is illustrative: the scores come from the distances, the sources are not hand-picked, and every panel shares perplexity and seed.
- **K11** the abstract is at 245/250 words; every addition needs an offset. **K12** references 29 → 31, above the soft 30.
- **K13** (H5 move) a reviewer may ask where completion's test went; the pointer sentence and the Limitations clause answer it.

### 7.2 Cross-references (the supplement hard-codes main-text numbers; no `xr` package)
| Location | Now | After the plan |
|---|---|---|
| s1_proofs.tex:2, 16, 89, 159, 194, 217, 265, 418; s3:108; abstract_supp:3 | Def. 3.2, Lem. 5.1–5.3, Thm 5.4, Prop. 5.6, 5.7, 5.9, Sec. 5 | unchanged: no theorem-like environment is added, removed or reordered (Prop. 6.1 stays 6.1; H4 adds none). Cor. 5.5, Prop. 5.8 and Prop. 6.1 are not cited by number. |
| abstract_supp:6–7, 13; s2:6, 8, 20, 122, 130, 167; tab_s2_locality:14 | 8.2/H2, 9.2, 7.1–7.3, H1, H3 | unchanged; §7 and §9 keep their subsections |
| abstract_supp:9–10; s3_generation:6, 9, 19 | "H4 (Section 8.4)", generation | "H5 (Section 8.5)" |
| abstract_supp:11; s4_completion:6, 8 | "H5 (Section 8.5)", completion | rewrite: defined in Sec. 6.6, validity in H5 (Sec. 8.5), recovery here; Alg. S1 = old Alg. 3 |
| main: hard-coded "H1–H5"/"H4" (intro L97–99, Tab. I caption, res L8, concl L21, 29, 39, 54, 67, setup L39, 44) | — | renumber by hand; `\cref` labels keep their names; new label `sec:res-representatives` |
| main → "Section~S1–S4" (lang L198; prop L9, 78, 167; res L203, 238; Tab. V/VII captions; concl L105, 115, 131) | — | S1–S4 kept; add one S2 pointer for H4 |

The claim ledgers in the clone's `.claude/notes/` key claims by H label; record the renumbering in the next wave summary.

## 8. Execution (the later text pass)
Worktree from Overleaf `main` `97d1e76`; article and supplement in disjoint directories, as on 2026-10-14. Order: (1) P1 cuts, build, `pdfinfo`; (2) F1 and F2 scripts in `figures/src/` (existing data); (3) H4 and Fig. R once LOG §5 freezes; (4) the H5 move with the S4/S2 edits; (5) an independent read-only claim check on every changed sentence; (6) a humanizer pass on changed paragraphs only. Verify with `latexmk -pdf main.tex` (never `-C`), a theorem-label diff against `97d1e76`, a grep of `Section~[0-9]` in the supplement, detex counts against §2, and outward bound rounding.

## Log
- 08:07 Task received; reported model id and plan to `main`. 08:10 Read `LOG.md` (§5 empty); Overleaf clone `git status` clean at `97d1e76`.
- 08:11 `latexmk -pdf -interaction=nonstopmode main.tex`: up to date, 14 pages (`pdfinfo`). Thumbnails with `pdftoppm -r 45/60` + `montage` (scratchpad), pages 1–14 viewed.
- 08:12 `detex sections/*.tex | wc -w`; per-page `pdftotext`; labels and pages from `main.aux`.
- 08:13–08:16 Read every `sections/*.tex` in full, plus `tables/{tab_map,tab_capability,tab_neardup,tab_generation,tab_completion,tab_corpora}.tex` and `fig_overview.tex` L56–95. 08:16 Prose-only, paragraph, numeral-density and sentence-length counts (Python + `detex`); repeated numbers by `grep`.
- 08:17 `ARTICLE_WRITING_PLAN.md` §4–6 (L148–289), §8–12 (L685–823), §15 (L945–1001); wave `summary.md`; `maintext-opus.md` §7–10 (L557–621) and a heading scan.
- 08:18 Supplement: grep of hard-coded main-text references; section map; 12 pages; no `xr`. TKDE information for authors (`pdftotext`): 14 pages including references and biographies, $200 per page beyond 14, maximum 18.
- 08:19 IsalSR paper: introduction 642, results 2,092, conclusion 370 words; 5 figures, 5 tables.
- 08:20 F1 and F2 data checked: `rq2_ow_facts.md` L120–159, `rq6_generation_facts.md`, `rq7_envelope_facts.md` §8, `neural_gen/stats.json` (`usable_per_draw`); palettes in `fig_envelope.py`, `fig_corridor.py`, `fig_neardup.py`.
- 08:21 Float heights and p14 slack from `pdftotext -bbox` (line gaps per column).
- 08:22–08:35 Wrote this file (one rewrite to meet the length cap; corrected the H5-kept scenario to 12.9–13.3 and the tightest slack to 0.7 page). It is the only file created; nothing in the Overleaf clone or the repository was edited.
