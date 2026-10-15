# KNN — classification and clustering of KBs by distance (opened 2026-10-15 08:07 CEST)

Append-only experiment log. Leader: the orchestrator session. Every hypothesis and kill criterion is
written here **before** the run it governs; every result is appended after it; nothing is deleted.

## 0. Why this exists

The PI, by email after reading the TKDE draft:
- He asks for an experiment of **classification (k-nearest neighbours) or clustering (k-medoids) of
  KBs, based on the IsalHG distance**, as an illustration of practical uses. The competitor set is
  then restricted to representations that define a distance.
- He misses **figures and plots that lighten the reading**. Classification and clustering experiments
  could provide attractive visualizations.
- The main text keeps positive results only.

The author's instruction:
- find such an experiment;
- make it orthogonal to the current main-text experiments, or a reformulation of one of them;
- make it a clear positive;
- execute it on Picasso;
- then rework the main text to integrate it, with fewer words and more figures;
- if space requires, move the least favourable main-text experiment to the supplement.

## 1. What is already known (do not repeat)

- **Synthetic hypergraphs.** On unlabelled hypergraphs with swap-planted families, the search form
  lost both kNN and k-medoids to the nauty-Levi edit distance. The source is
  `foundation/measured_facts.md` §B and the T-M4b record. The cause is that swaps are interior edits,
  where the word is not local.
- **WD50K entity types.** Clustering WD50K members by Wikidata type gives ARI < 0.08 under every
  representation (`foundation/rq5_ow_facts.md`). Structure alone does not carry type. The word also
  writes the root type as its first symbol, so a type label would leak through `d_I`. **Entity types
  are therefore not a valid label here.**
- **Pendant locality (C8, H2).** On real one-edit near-duplicate pairs, 56–90 % are pendant. On those
  pairs the word's nearest neighbour is the true partner far more often than under any of the ten
  competitors (MRR 0.45–0.73 vs at most 0.35). On interior pairs it loses.
- **NDC version linkage (C3, mixed).** The next quarterly version of an NDC record is ranked first more
  often under the word on NDC-classes (hit@1 0.333 vs the certificate's 0.195). However, HPD has the
  higher MRR there, and the degree-sequence floor wins on NDC-substances.

**Design rule:** the class structure must be the one real collections exhibit (records that differ by
statements added or removed with their values), or it must be the real class structure itself.

## 2. Candidate designs (both pre-registered; both reported whatever the outcome)

### Design A — real lineages (NDC quarterly versions)

- **Data.** A class is one NDC node `c` (a pharmacologic class or substance). Its members are the KBs
  of `c` in the different windows `t`; these are real versions, and node identity is ground truth
  that no isomorphism computation touches. Use every lineage with at least 3 versions inside the
  envelope.
- **kNN.** Leave one version out. Its neighbours are the versions of *other windows* only, which
  prevents same-window leakage. Score 1-NN and 5-NN accuracy (ties at expected accuracy) and
  macro-F1.
- **Clustering.** k-medoids (PAM, k = number of lineages in the sample) over the versions of a random
  sample of lineages, scored by ARI and NMI against lineage.

### Design B — partial copies of real records ("which record is this a copy of?")

- **Data.** A class is a real member (the source, never in the evaluated set). Its members are `c`
  partial copies, each obtained by removing `r` statements or qualifier values *together with their
  own value*. These are pendant removals: delete a fact holding a constant found in no other fact, or
  remove a constant from its last fact. The copy stays connected and keeps at least 3 facts.
- **Practical reading.** Different systems export different subsets of the same entity's statements;
  the task is to recognise which entity a partial export describes (record linkage without
  identifiers), and to group exports by entity (k-medoids).
- **Settings.**
  - `r ∈ {1, 2, 3}`.
  - `c = 6` copies.
  - `S` sources sampled uniformly from the members with enough pendant structure. Use S = 100 in the
    probe and S = 200 in the full run.
- **Robustness condition (reported, not headline).** The edit mix follows the measured pendant /
  interior share of the collection's real one-edit pairs, i.e. C8's shares: 90 % pendant on WD50K(66),
  75 % on WD50K(100), 74 % on NDC-classes and 56 % on NDC-substances.

### Competitors

All cached distances, as in C8:
- certificate bytes and certificate rows;
- fact list;
- WL L1;
- NetLSD;
- HPD JSD;
- bipartite GED, assignment value and edit-path cost;
- degree-sequence L1;
- size L1.

The search form `w*_c` is a within-family ablation. HyperCOT has no matrix. **Every competitor is a
distance** (the bipartite edit-path cost is not a metric; this is stated).

### Statistics

- **Seeds.** 27 seeds; each seed redraws the sources and copies (B) or the lineage sample (A).
- **Intervals.** 95 % BCa intervals over seeds.
- **Tests.** One-sided paired Wilcoxon over seeds of the word vs each competitor, Holm-corrected over
  the competitors, with rank-biserial effect sizes.

## 3. Hypotheses and kill criteria (fixed before any probe)

- **H-KNN-A (real lineages).** The word has the highest 1-NN accuracy and the highest k-medoids ARI
  on NDC-classes and on NDC-substances. **Kill:** any competitor ≥ the word on either metric on
  either collection.
- **H-KNN-B (partial copies, pendant removals).** The word has the highest 1-NN accuracy and the
  highest k-medoids ARI on all four collections at every `r`.
  - **Kill:** any competitor ≥ the word on either metric in any (collection, `r`) cell.
  - **Expected risk:** at `r = 3` on NDC-substances, where C8's degree-sequence floor and edit path
    were strongest.
- **H-KNN-mix (robustness).** Under the empirical edit mix, the word has the highest 1-NN accuracy on
  the WD50K collections. No claim is made on NDC, where C8 pooled ties with the edit path.

Only a design that survives its kill criterion goes to the main text. The other is recorded here and,
if useful to users, offered for the supplement.

## 4. Visualization plan (the PI's request)

One double-column figure:
- **(a)** a 2-D embedding of the partial copies of 12 sources under the word and three competitors
  (certificate rows, the fact list or edit path, and WL or NetLSD), coloured by source. It uses t-SNE
  on the precomputed distances with the same perplexity and seed for every panel, and gives the
  panel's 1-NN accuracy and ARI in its title.
- **(b)** 1-NN accuracy against the number of removed statements `r`, one line per representation,
  with 95 % CIs.

The k-medoids medoids under the word are actual KBs (every word decodes), which ties the experiment to
the certified-representative operation (Prop. 6.1) that the paper so far has not exercised.

## 5. Probes and results

(appended below as they run)

### 5.1 Probe of Designs A and B (2026-10-15; S = 60, c = 6, 3 seeds, all cells, 399 s)

Code: `scripts/newpos/knn/{knn_lib,probe_knn,fig_knn_probe}.py`, tests `tests/newpos/test_knn.py` (78 pass
with `test_neardup.py`), merged into `main` at `bd52419`. Outputs and the generated tables:
`D/results/KNN_2026-10-15/probe/{SUMMARY.md,summary.json}`. Engineer's log:
`.claude/notes/2026-10-15-knn/probe-engineer.md`. The leader re-ran the tests and checked the numbers
below against `SUMMARY.md`. Point values are seed means, with [min, max] over the 3 seeds.

**Verdicts. All three kill criteria fired.**

- **H-KNN-B (pendant partial copies): killed in 12 of 12 cells.**
  - The bipartite edit path, or the assignment value, has the highest 1-NN accuracy in every cell
    except WD50K(66) at r = 2 and r = 3. In those two the word leads 1-NN (0.944 vs 0.886; 0.880 vs
    0.834) but loses ARI (0.452 vs 0.486; 0.323 vs 0.405).
  - The gap is widest on NDC-substances: word ARI 0.323 / 0.264 / 0.234 vs 0.614 / 0.508 / 0.432.
- **H-KNN-A (real NDC lineages): killed.**
  - NDC-classes: the word leads both metrics, 1-NN 0.748 vs 0.700 (edit path) and ARI 0.273 vs 0.256
    (fact list), but the seed ranges overlap.
  - NDC-substances: the word loses, 1-NN 0.430 vs 0.452 and ARI 0.142 vs HPD's 0.208.
- **H-KNN-mix: killed in all 6 WD50K cells,** by the edit path (e.g. WD50K(100) at r = 1: 0.648 vs
  0.864). The realized pendant share was 0.81–0.86 against the 0.90 target, and 0.68–0.73 against the
  0.75 target.

**Diagnostics.**

- **No ceiling effect.** At most 2 arms reach 1-NN ≥ 0.9 in any cell. The ceiling for exact arms is
  0.93–1.00 on every Design-B cell.
- **Isomorphism shared across lineages (Design A):** 0.25 / 0.29 of items, with exact-arm ceilings of
  0.92 / 0.79. The ceiling, not the shared fraction, is what bounds accuracy.
- **Prop. 6.1 holds in every arm.** For the word, cost(M)/LB has a median of 1.22–1.34 and a maximum of
  1.75. 0 of 2,785 clusters exceed the 2 − 2/N bound, so the bound does not separate the arms.
- **Ablation: the word beats `w*_c` on 1-NN in 6 of 6 cells** (seed 0, WD50K(66) and NDC-classes).
  `w*_c` costs 41–549 s per cell.
- **The pre-registered WL arm is degenerate on this task.** Run to a stable partition, every pair's
  distance is n_i + n_j, so 1-NN ≈ 0.014. A fixed one-round WL reaches 0.989 / 0.964 / 0.928 on
  WD50K(66), above the word. This is recorded here and is not hidden: §6 adds it as a competitor.

**Mechanism (seed-0 diagnostics).**

- One token of the word carries a whole fact, so on small records copies of *unrelated* sources sit
  only a few tokens apart. On NDC-classes the nearest copy of another source is 2 tokens away and the
  nearest sibling 1 token away; the word also has avalanche tails of up to 60 tokens per removal.
- The bipartite edit cost of a removal grows with the size of the removed fact. Unrelated sources drawn
  at random therefore stay far apart under it.
- **Lesson.** When the sources are drawn uniformly from a few thousand records, the pool is sparse. It
  then lacks exactly the look-alike records that made C8's distractors hard, and in that regime an
  edit-cost distance is the right tool.
- **The word still beats every certificate and fact-list arm in every Design-B cell.**

**Decision (leader).**

- The kills are accepted.
- Designs A and B do not go to the main text and are not run at full scale. They are kept for the
  supplement, as the honest "random records" condition.
- The draft figure (`probe/fig_knn_probe_r2_s0*.png`) shows that the visual format works.

## 6. Design C — linkage among look-alike records (C8 reformulated as kNN / k-medoids)

Pre-registered 2026-10-15, before any Design-C code runs. Rationale:
- C8 showed the word's advantage on real near-duplicate neighbourhoods, where the distractors are the
  record's look-alikes.
- Record linkage in practice runs *after blocking*: the linker is handed candidates that already look
  alike (Christen, *Data Matching*, Springer 2012, ch. 4).
- Design C keeps Design B's noise model (partial exports, pendant removals) but draws the sources the
  way a blocking step presents them: as groups of look-alike records.

**Blocks.**
- Take the C8 one-edit relation among the real records of the collection: single-fact edits,
  enumerated, keyed by the nauty certificate, with records deduplicated to isomorphism classes.
- A block is a seed record plus a uniform subsample of at most 4 of its one-edit neighbours. A block
  has at least 3 members.
- Blocks drawn in one seed are disjoint. Draw blocks uniformly at random until the pool holds ≥ 60
  sources or the candidates run out, and report the realised S.
- **Strata, fixed now:**
  - **C-all:** the neighbours may be of either edit kind, in the collection's natural proportion.
  - **C-int:** only neighbours one *interior* edit from the seed.
  - **C-pend:** only *pendant* neighbours. Reported, with no claim.
- A stratum with fewer than 10 available blocks on a collection is reported as infeasible there. An
  infeasible cell is not a pass.

**Copies, competitors and statistics.**
- Copies are as in Design B: c = 6 per member, r ∈ {1, 2, 3} pendant removals, at least 3 facts kept,
  connected.
- Competitors are those of §2 plus the **one-round WL** (fixed h = 1, L1 on the colour histogram).
- 27 seeds, BCa intervals, one-sided Wilcoxon with Holm correction and rank-biserial effect sizes.

**Metrics (primary, no others promoted later).**
- 1-NN accuracy over the whole pool (ties at expected accuracy).
- k-medoids ARI against the source, with k = S.
- Each cell reports the exact-arm ceiling and the fraction of items whose isomorphism class is shared
  across sources.

**Hypotheses and kills.**
- **H-KNN-C (natural blocks, C-all).** The word has the highest 1-NN accuracy and the highest ARI on
  all four collections at every r. **Kill:** any competitor ≥ the word on either metric in any feasible
  cell.
- **H-KNN-C-int (mechanism).** The same claim and kill, on C-int.
- **Prediction, written down so it can be wrong.** C-int favours the word: a pendant removal moves few
  tokens of the word, and an interior edit moves many, whereas an edit cost prices both by fact size.
  C-pend is expected to favour no one, because the copies of a record and of its pendant extension
  collide.

**Main-text admission (fixed now).**
- If H-KNN-C survives, it is the headline.
- If only H-KNN-C-int survives, it may enter the main text only if:
  - the same sentence carries the scope "look-alike records that differ in how their facts are
    linked";
  - the main text points to the Design-B negative (random records: the bipartite edit path wins) and
    to the C-all result.
- If neither survives, there is no kNN positive. The leader reports this to the author, and the
  experiment goes to the supplement whole.

**Figure.** As in §4, with panel (a) drawn *inside one block* (copies of 3–5 look-alike records,
coloured by member). The edit-path panel is always one of the four, because it is the strongest
competitor.

### 6.1 Amendment before any Design-C result (2026-10-15)

**Feasibility finding.** The engineer counted blocks before computing any distance. With c = 6, the
stratum C-int is infeasible on every collection, because the one-edit graph lives on small records:
- the median record has 3–5 facts, and 21–52 % of the isomorphism classes have m = 3;
- many of these records cannot yield 6 pairwise non-isomorphic pendant copies.

The binding constraint is c, not r.

| | WD50K(66) | WD50K(100) | NDC-classes | NDC-substances |
|---|---|---|---|---|
| Eligible classes, c = 6 | 82 / 957 | 208 / 624 | 153 / 374 | 51 / 513 |
| Disjoint blocks, c = 6 (all / int / pend) | 3 / 0 / 3 | 21 / 2 / 21 | 17 / 2 / 11 | 2 / 0 / 1 |
| Disjoint blocks, c = 3 (all / int / pend) | 27 / 3 / 25 | 50 / 15 / 47 | 38 / 4 / 29 | 22 / 14 / 19 |

Block counts are for seed 0, drawn to exhaustion. Eligible classes are given out of all classes in the
one-edit graph.

**Amendment.**
- **Copies.** Design C uses **c = 3** copies per member, with r ∈ {1, 2, 3} unchanged. Every query then
  has 2 siblings, and a cell holds about 180 items.
- **Feasibility.** The rule is unchanged: at least 10 blocks, taken as the minimum over seeds.
- **Kill criteria.** The kill criteria of §6 apply unchanged to the c = 3 cells. These cells are the
  primary result.
- **The registered c = 6 run.** It still runs on its feasible cells and is reported with its own
  verdicts, so the amendment cannot hide a c = 6 failure.
- **Variable c.** Rejected, because unequal class sizes bias both 1-NN accuracy and ARI.

**Consequence, stated now.** H-KNN-C-int is testable only on WD50K(100) and NDC-substances. Its claim
is restricted to the feasible cells, and the infeasible cells are reported as infeasible.

No Design-C distance, accuracy or ARI had been computed when this amendment was written.
