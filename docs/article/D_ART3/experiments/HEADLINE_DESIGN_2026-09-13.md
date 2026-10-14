# Headline design — `w°` as the paper's program, three headline exhibits

**Declared:** 2026-09-13 by `[IsalHG-Fable-Review]` (orchestrator), on the
author's instruction. Pre-registered: every hypothesis, arm, metric and
fallback below is fixed before the runs. Deviations are logged in the agents'
notes and in §8, never silently.

**Decision it executes:** D-ART6 (`../../DEVELOPMENT/DECISIONS.md`) — the
ordered walk `w°` (`isal_ow_struct`) is the paper's headline program; every
table runs on it. `w*_c` stays as the family's search-based form, appearing in
RQ1's four-cell ablation and nowhere else in the main text.

**Reads first:** `SESSION_LOG.md` §6 (the reasoning), `prose.md` §2–§3,
`foundation/lessons.md` (binding), `experiments/tkde/README` conventions in
`slurm/tkde/README.md`, and the ledger tasks T-KBz / T-KBaa / T-KBab.

---

## 0. Why this design (the reasoning the agents must carry)

**What the paper can win.** The certificate member (nauty canonical labelling
+ Levenshtein) matches IsalHG on exactness, the metric axioms, polynomial pair
cost and compactness. Vector representations (WL, NetLSD, HPD) are stable but
incomplete and have no decoder. The only properties every competitor lacks are
the *language* properties: every string decodes to a connected knowledge base
(Prop. C.4), so neighbourhoods, alignments, consensus candidates and generated
samples are all knowledge bases. A headline experiment must therefore use the
language (criterion a), beat every competitor that can be scored and blank the
rest with a stated reason (b), and answer a knowledge-engineer's question (c).

**Where we have lost, and why.** RQ5 (clustering vs Wikidata types) and RQ4
(anomaly AUC) are task-metric contests where counting and vectors suffice. RQ1
locality is conditional (pendant yes, interior no). The mechanism behind all of
it is the same: **about half of WD50K entity knowledge bases are stars**
(53.4 %, measured at G0; §8 item 1) — every fact
contains the root entity, and if no non-root constant is shared between facts
the isomorphism class is the multiset of fact patterns, which WL, degree
sequences and plain counting determine exactly. The hypergraph machinery only
matters where constants are shared across facts. NDC co-formulation records
(products sharing classes) are genuinely relational; WD50K is relational only
on its non-star subset. **Every headline below is therefore stratified by
star / non-star**, and the claim is stated for the relational stratum with the
star stratum as the control where counting is expected to tie.

**The three headline exhibits.**

| # | exhibit | property used | who is blank, why | engineer's question |
|---|---|---|---|---|
| H1 | RQ6 generation (done, `ow_ngram`) | closed connected language | certificates and vectors: no generative model definable | "give me more records like these" |
| H2 | RQ3 v2 golden record (this doc §3) | consensus is a decoded object; balls in word space | medoids return a member (recovery 0 by construction); vectors/certificates cannot produce a non-member | "N anonymous descriptions of one thing disagree — which is the reference?" |
| H3 | RQ8 valid completion (this doc §4) | prefix property + total decoder | certificates and vectors: no completion definable | "what is this record probably missing?" |

Plus the measured capability table (§6), which is the summary of all of it.

---

## 1. Standing rules for the campaign

1. **Program.** Ours = `isal_ow_struct` (`w°`, C++ ordered-walk emitter),
   60 s budget, in every table. `wstar_orbit` appears only in RQ1.
2. **Every competitor in every table.** Rows: `nauty_cert`, `nauty_cert_rows`,
   `wl_l1`, `netlsd`, `hpd_jsd`, `bipartite_ged_assign`, `bipartite_ged_path`,
   `hypercot` (where per-pair cost permits — always in RQ3 v2, N ≤ 15),
   `size_l1`, `degree_seq_l1`, plus the task baselines named per RQ. A row that
   cannot be scored carries the reason in the cell ("no decoder", "no
   generative model"), never an empty cell. The retired fact-rank word appears
   in no main-text table (D-ART4 (1)); where it was a comparator it is a
   sentence and a supplement row.
3. **Harness.** S = 27 seeds, 95 % BCa bootstrap CIs, Holm-corrected paired
   Wilcoxon over seeds against every competitor, rank-biserial effect size.
   Pre-registered hypotheses with fallbacks; nothing dropped for winning
   (L12).
4. **Results root.** A clean root per campaign (T-KBn precedent):
   Picasso `~/results/IEEETKDE_ow/` with `matrices` symlinked to the shared
   build; drive mirror `results/IEEETKDE_ow/`. Sub-roots `RQ3v2/`, `RQ8/`,
   `RQ2_ow/`, `RQ5_ow/` — disjoint per agent.
5. **Corpora.** The frozen corpora only (`ndc_classes`, `wd50k66`; controls
   `ndc_substances`, `wd50k100` where the RQ already used them). Counts as in
   the built census (1,381 / 3,988), never the supplement's.
6. **Gates before Picasso.** Each RQ has a local pilot gate (G-*) whose result
   is reported to the orchestrator *before* submission. A pilot never tunes on
   evaluation data.
7. **Fact base.** Each RQ ships `foundation/rq3v2_facts.md` / `rq8_facts.md`
   skeletons naming run root, job ids and tables (T-KBg precondition).

---

## 2. Gate G0 — the star census (both corpora; both agents compute it into their own dir)

For each member: `is_star` = every fact contains the root constant
(WD50K: the entity; NDC: no root — treat NDC as non-star by construction unless
a constant is in every fact) **and** no non-root constant appears in ≥ 2
facts. Report per corpus: fraction of stars, and for non-stars the number of
shared constants and shared facts. Deliverable: one table, one sentence in the
data section. This decides the strata of §3 and §4 and is itself a finding
("structure exists in X % of WD50K descriptions").

---

## 3. RQ3 v2 — the golden record from N anonymous noisy descriptions

**Question.** N descriptions of one thing, from different sources or runs,
disagree by a few facts, and their constants are anonymous. Which record is
the reference, and with what guarantee?

**Why v1 could not answer it.** (i) Medoids are a structural floor (the source
is not a member, so recovery is 0 by construction). (ii) The identity-using
majority merge had information the premise denies; with identities, insertion
ladders are trivial (the union recovers 108/108, audit §3.3). (iii) Natural NDC
quarters tie and the gate was underpowered. (iv) Deletion ladders failed for
every method at the pre-registered ≥ 0.95, which was unachievable.

**Design.**

- *Sources.* Real members: WD50K(66) with 4 ≤ m ≤ m_max, stratified star /
  non-star (G0); NDC-classes with 4 ≤ m ≤ m_max. 100 sources per corpus per
  seed (re-sampled per seed), 27 seeds.
- *Members.* N ∈ {5, 9, 15} anonymized variants of the source. Each member
  receives t ∈ {1, 2} independent random in-domain edits, **mixed** kinds
  drawn uniformly from {delete a pendant fact, delete an interior fact, insert
  a fact over existing constants, insert a fact with a new constant}, subject
  to: the result is connected (R3), differs from the source, and the edit
  kinds' realised mix is logged. Constants are then randomly relabelled.
  Ground truth = the source; the fact-level distance from member to source is
  t by construction.
- *Regime note (pre-stated mechanism).* Reference-anchored merges cannot
  recover a pendant fact the reference lacks without an N-way alignment of
  constants absent from the reference; on stars, counting fact patterns
  recovers the source without any alignment. The consensus is expected to win
  on the **non-star** strata and to tie counting on stars.
- *Arms (all present).*
  - medoid under every distance of §1 rule 2, incl. `hypercot` and
    `isal_ow_struct` — recovery 0 by construction (printed as such);
    fact-level distance to source and the certified ratio reported;
  - `majority_merge_id` — identity-using majority vote (**oracle upper bound**,
    labelled as such; uses the true identities);
  - `align_merge_ref` — anonymous: align every member to the reference (the
    `bipartite_ged_assign` medoid) by the Hungarian assignment, majority-vote
    facts in reference coordinates; facts over unmatched constants are
    dropped;
  - `align_merge_iter` — the same, re-aligned to the merged result for 3
    rounds, unmatched constants admitted when ≥ N/2 members carry an
    unmatched constant of the same type and fact pattern (the strongest
    practitioner merge we can write without solving N-way alignment);
  - `pattern_vote` — anonymous, alignment-free: majority over fact patterns
    (predicate, arity, multiset of constant types); assembles a star; on
    non-stars it must choose attachments by a stated heuristic (highest-degree
    matching type) — the counting baseline that must tie us on stars;
  - **ours** `consensus_ow` — ball-coverage consensus in the `w°` language:
    candidates = decoded words within reach r of the members (the existing
    `reach′` machinery in `experiments/tkde/rq3.py`, ported to `w°` words);
    score = number of members within reach r; ties by the sum of reaches then
    by shortlex of `w°`; r = 2 primary, r = 3 via the restricted ball if
    G3.1 requires it.
- *Metrics.* Exact recovery of the source (isomorphism via the certificate);
  fact-level distance of the returned record to the source by the exact HGED
  oracle (`metric_space/distances/hged.py`, ceiling stated; `bipartite_ged_path`
  as the fallback judge, flagged per row); wall-clock. Per corpus × stratum ×
  N × t.
- *Hypotheses.* **H3.1** (headline): on the non-star strata at t ≤ 2,
  `consensus_ow` exact recovery > `align_merge_ref`, `align_merge_iter` and
  `pattern_vote`, Holm-significant, for every N. **H3.2**: `consensus_ow`
  fact-level distance < every medoid (expected; the floor is stated).
  **H3.3** (stretch): `consensus_ow` ≥ `majority_merge_id` − 0.05 on
  non-stars (we match an oracle that has identities). **H3.4** (control): on
  stars, `pattern_vote` ties `consensus_ow` (|Δ| < 0.05) — reported as the
  scope statement, not hidden.
- *Fallbacks.* If H3.1 fails on one corpus, the claim is scoped to the other;
  if it fails on both, the headline becomes H3.2 + the certificate and the
  consensus moves to a supporting exhibit; RQ8 becomes the second headline.
- *Gate G3.1 (local pilot, before Picasso).* Reach coverage under `w°`: for
  200 real members per corpus and every single fact edit kind, is the edited
  knowledge base within reach r ∈ {1, 2, 3} of the member's word? Report
  coverage per edit kind × stratum, and the same for `wstar_orbit` on the same
  units. If coverage at the chosen r is < 0.9 on any edit kind used in the
  noise model, restrict the noise model to the covered kinds **and say so** in
  the design, or raise r with the restricted ball (append ≤ 3 tokens ∪ delete
  ≤ 2 tokens), whichever the pilot prices as feasible. If `w°` coverage is
  materially below `w*_c`'s, report to the orchestrator before proceeding.
- *Gate G3.2.* Harvest the corrected-objective v1 run
  (`results/IEEETKDE_isal_consensus/RQ3_representative/`) and report its
  deletion-regime recovery, so v2's objective inherits the fix.
- *Natural NDC series.* Kept as v1 measured it, supplement, unchanged.

**Files (Agent A owns).** `experiments/tkde/rq3v2.py`,
`experiments/tkde/analyze_rq3v2.py`, `experiments/tkde/configs/rq3v2.yaml`,
`tests/experiments_tkde/test_rq3v2*.py`, `slurm/tkde/rq3v2_{launcher,worker}.sh`,
`docs/article/D_ART3/experiments/RQ3V2_PILOT.md`,
`docs/article/D_ART3/foundation/rq3v2_facts.md`,
`docs/article/DEVELOPMENT/T-KB/IN-PROGRESS/T-KBz.md`.

---

## 4. RQ8 — valid completion of a record

**Question.** A record is probably missing a fact. Propose completions that
are guaranteed to be records, and rank them by how often the true completion
is among them.

**Property used.** The prefix property: `w°(K⁻)` is a program of the machine,
and any continuation of it decodes to a connected knowledge base that contains
`K⁻` (appending instructions never removes a fact or a constant — state and
prove as a one-line proposition, Prop. C.8). So a sequence model over words,
conditioned on the prefix, proposes only valid completions. No certificate
and no vector admits a completion operation.

**Design.**

- *Substrates.* NDC-classes members with m ≥ 4; WD50K(66) members with m ≥ 4,
  stratified star / non-star (G0). WD50K stars are the control stratum.
- *Units.* (member, hidden fact). On non-stars the hidden fact is drawn among
  **interior** facts (sharing ≥ 1 non-root constant with another fact) — the
  stratum where attachment matters; on stars, uniformly. `K⁻` must remain
  connected (else resample; log the rate). Truth = the member.
- *Split.* 80/20 by member, stratified by type where available, re-drawn per
  seed; models are fitted on the training words only; 27 seeds.
- *Ours.* `ow_ngram`: the RQ6 n-gram (order as in `rq6.py`) over `w°` words of
  the training split; continuation from `w°(K⁻)` kept verbatim as the prefix;
  sample until the end token; require ≥ 1 new fact (resample up to R = 20);
  k = 10 distinct completions (dedup by certificate). Secondary arm `ow_gru`
  (one-layer GRU, 128 hidden, same data) **only if** G8.1 shows the n-gram's
  interior hit@10 below 0.5 × `pattern_cooc`; declared here so it is not a
  post-hoc addition.
- *Baselines (all present).* `fact_ngram` (continuation of the retired
  fact-rank word of `K⁻`; supplement-row status per D-ART4 but scored here as
  the generative comparator it was in RQ6); `incidence_ngram`; `pattern_freq`
  (top-k fact patterns by training frequency, type-conditioned, attached by
  the stated heuristic: root for stars, highest-degree constants of matching
  type otherwise); `pattern_cooc` (item–item conditional frequency of patterns
  given the patterns in `K⁻`, top-k, same attachment) — the strong
  practitioner recommender; `random_pattern`. Non-generative rows
  (`nauty_cert*`, `wl_l1`, `netlsd`, `hpd_jsd`, bipartite, floors): "no
  completion definable".
- *Metrics.* **hit@10**: some proposal is valid ∧ connected ∧ isomorphic to
  the truth (primary); **pattern@10**: the hidden fact's pattern appears among
  added facts of some proposal; validity and connectivity of proposals; per
  corpus × stratum × hidden-fact kind (pendant / interior).
- *Hypotheses.* **H8.1** (headline): hit@10 of `ow_ngram` > every baseline on
  the interior units of both corpora, Holm-significant. **H8.2** (control): on
  star units `pattern_cooc` ≥ `ow_ngram` is expected and reported as the
  scope. **H8.3**: proposals valid ∧ connected: ours 1.000 (theorem);
  `fact_ngram` < 1; `incidence_ngram` < 0.05.
- *Fallbacks.* If H8.1 fails, the claim reduces to H8.3 plus the measured gap
  to the recommender, and RQ8 becomes a supporting exhibit.
- *Gate G8.1 (local pilot, before Picasso).* 3 seeds, 200 interior units per
  corpus, all arms: report hit@10 and pattern@10 per arm. If `ow_ngram` ≤
  `pattern_cooc` on interior units, report to the orchestrator with the
  numbers before submitting; the GRU arm is enabled per the rule above.

**Files (Agent B owns).** `experiments/tkde/rq8.py`,
`experiments/tkde/analyze_rq8.py`, `experiments/tkde/configs/rq8.yaml`,
`tests/experiments_tkde/test_rq8*.py`, `slurm/tkde/rq8_{launcher,worker}.sh`,
`docs/article/D_ART3/experiments/RQ8_PILOT.md`,
`docs/article/D_ART3/foundation/rq8_facts.md`,
`docs/article/DEVELOPMENT/T-KB/IN-PROGRESS/T-KBaa.md`, and §5 below.

---

## 5. The `w°` swap for the tables already measured (Agent B)

- **RQ2 census on `w°`.** False-merge census and exact partition with
  `isal_ow_struct` on `ndc_classes`, `ndc_substances`, `wd50k66` (expected: 0
  merges, exact partition — Theorem C). Config `configs/rq2_ow.yaml`; results
  `RQ2_ow/`.
- **RQ5 on `w°`.** Re-run the clustering table with `isal_ow_struct` in place
  of `wstar_orbit` (expected: the same negative; the naive floors still win).
  Config `configs/rq5_ow.yaml`; results `RQ5_ow/`.
- RQ6 and RQ7 already carry `w°`; RQ1 keeps all arms.
- Edits to `experiments/tkde/rq2.py` / `rq5.py` only if arm selection cannot
  be done from the YAML; note every such edit.

---

## 6. The capability table (`docs/article/D_ART3/tables/tab_kb_representation_properties.tex`)

Mirrors the sibling's `tab_representation_properties.tex` (every cell
measured or by theorem, source column per cell in the comments). Rows: every
competitor of §1 rule 2, then `w*_c` (family form), then **`w°`** last, bold.
Columns and their sources:

| column | filled from |
|---|---|
| complete (exact at 0) | theorem / counterexample (RQ2 Prop 8–9; Thm A/C) |
| false merges on `wd50k66` (7,949,355 non-iso pairs) | RQ2 census |
| metric on iso-classes | theorem; bipartite path: measured 38 % asym., 1.4 % triangle |
| N = 3,988 matrix, s | RQ7 N-scaling (`rq7_envelope_facts.md` §8), rows arm after T-KBy |
| closed language (every string decodes, connected) | Prop. C.4; certificates ✗; vectors ✗ |
| generative validity (valid ∧ connected) | RQ6 |
| consensus is a decoded object | RQ3 v2 |
| completion definable | RQ8 |
| pendant / interior within-2 (delete a fact) | RQ1 M1 (`published_tables.md`) |

Cells that depend on RQ3 v2 / RQ8 are marked `\todo` in the draft.

---

## 7. Orchestration

Two agents, one wave, `WAVE_ID = 2026-09-13-headline-w0`:

| agent | mission | model / effort | ownership |
|---|---|---|---|
| `rq3v2` | §2 G0 (own copy), §3 incl. gates, T-KBz | Opus 5 / xhigh | §3 file list |
| `rq8` | §2 G0 (own copy), §4 incl. gate, §5, T-KBaa, T-KBab | Opus 5 / xhigh | §4 + §5 file lists |

Both: cloned conda env per worktree, tests green, local pilot, `picasso-sbatch`
launcher/worker under `slurm/tkde/`, sync + submit, job ids in the note, no
waiting on the queue. Read-only for both: `src/isalhg/**`,
`experiments/tkde/{rq1..rq7,io,stats,budget,matrices,corpora}.py`; a needed
change there is a message to the orchestrator, not an edit.

## 8. Deviations log

*Appended by the orchestrator from the agents' gate reports (wave
`2026-09-13-headline-w0`, notes in `.claude/notes/2026-09-13-headline-w0/`).
Each entry was ruled before the number it concerns was measured.*

1. **§0 premise corrected (G0).** "Most WD50K entity knowledge bases are
   stars" is too strong: 2,128 of 3,988 (53.4 %) corpus-wide, 54.0 % in the
   RQ3 source window, so wd50k66 supplies both strata in balance. NDC-classes
   is 3.0 % stars (42 of 1,381) and its star stratum is **empty** in every
   pool used here (0 of 212 RQ3 sources; 1 of 522 RQ8 members), so H3.4 and
   H8.2 are wd50k66-only; NDC star cells are printed as structurally empty.
2. **RQ3 v2 candidate machinery is word-space (§3).** v1's `reach′` pool is
   fact-space and representation-free, so `consensus_ow` is defined on the
   decoded token ball (union of `B_r(w°(K_i))`, grouped by certificate);
   v1's machinery survives as the ablation arm `consensus_fact` with the
   added **H3.5** (`consensus_ow` recovery ≥ `consensus_fact` − 0.05 at
   matched `r`, at lower enumeration cost).
3. **RQ3 v2 objective (§3).** Coverage-first is biased toward sub-records in
   word space (deletions move `w°` by 1 token, insertions by 5–10). Primary =
   generalized median over pool ∪ members; and, because Levenshtein
   substitution charges a fact swap 1–2 while a deletion costs 1 (source and
   sub-records tie exactly on deletion noise), the median's metric is the
   **indel** distance (`|w1|+|w2|−2·LCS`, the ball's own geometry), under
   which the source strictly beats every sub-record for `N ≥ 3`. Ties:
   coverage, then the size-neutral augmented-fingerprint order; shortlex
   retired as size-biased. Ablations on every collection: `consensus_ow_lev`
   (Levenshtein median), `consensus_ow_coverage`, `consensus_fact`;
   like-for-like `medoid[isal_ow_indel]` so certified ratios compare within
   one metric. **H3.6** added: recovery under the median increases with `N`
   and the small-`N` shortfall is a sub-record (the insertion asymmetry).
4. **RQ3 v2 envelope (§3).** The deletion-heavy `t = 2` NDC cell has source
   reachability 0.375 at `r = 2`; kept, printed as the envelope boundary,
   radius not raised. Ball: full indel `r = 2` (coverage 1.000 in every
   mixed `t = 1` cell), chosen on price.
5. **RQ8 secondary arm (§4).** `ow_gru` replaced by `ow_ngram_ho` (order-6
   backoff n-gram) before G8.1, to add no dependency. Its enabling rule fired
   (NDC 0.107 < 0.5 × 0.303); it closed a sixth of the gap on NDC and none on
   WD50K.
6. **RQ8 outcome and Amendment A1 (§4).** G8.1: H8.1 fails on NDC
   (recommender 0.303 vs ours 0.107 hit@10) and is a wash on WD50K → the
   pre-registered fallback; RQ8 is a supporting exhibit. An independent
   review found the counting arms add exactly one fact by construction while
   the free-running sampler's proposals add one fact 32 % of the time, so the
   attachment-miss statistic was confounded. Amendment A1 (committed before
   re-measurement): fact-count-matched arms `ow_ngram_1f` / `ow_ngram_ho_1f`,
   attach-miss over one-fact proposals on both sides. Matched: every
   ordered-walk arm attaches better than either recommender (NDC 0.35–0.39
   vs 0.66 / 0.58), so §0's attachment mechanism is **supported**; the NDC
   loss is a pattern gap (0.29 vs 0.89 pattern@10); on WD50K the matched arm
   leads (0.038 vs 0.013), untested until Holm at 27 seeds. H8.3's third
   clause (incidence < 0.05) is reported failed with the reason that the RQ6
   threshold assumed unconditional sampling; not moved.
7. **Deployment.** Private runner trees on Picasso HOME (`~/repos/IsalHG-rq*`)
   with the shared `isalhg-tkde` env, `--no-build`, because FSCRATCH was
   measured read-only at the file quota (276.3k / 250k soft, grace expired)
   at 13:2x and writable again (215.8k) at 13:35; nothing was deleted by any
   agent. Contradicts `slurm/tkde/README.md`'s "inputs stay on FSCRATCH";
   both workers refuse to start if any output path resolves under FSCRATCH.
8. **Jobs.** RQ3 v2 campaign `2308421` (122 tasks); RQ8 free-running
   `2308339` (completed, record) and amended `2308489`; RQ2_ow `2308342` +
   `2308343`; RQ5_ow `2308368`. Results root `~/results/IEEETKDE_ow/`.
