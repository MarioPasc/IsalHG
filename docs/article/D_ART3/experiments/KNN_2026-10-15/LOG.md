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
