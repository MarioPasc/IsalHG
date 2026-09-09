# IEEE TKDE article — experimental design (pre-registered)

*Authority for every experiment of the "knowledge bases as words" article
(`../prose.md`, v7, PI-ratified scope in `../START_HERE.md` §6.0). Written
2026-09-05 by the experimental orchestrator before any result of the new
pipeline exists. Everything below is a contract: hypotheses, corpora, arms,
procedures, the single evaluation axis per application, the statistical
procedure, the rows every run must persist, and the pre-agreed fallback when a
measured property turns out weak. Engineering (module map, waves, agent
ownership, Picasso layout) is in `CODE_PLAN.md`; this file is the science.*

**Reporting rule (author's instruction, 2026-09-05).** Every experiment is run
and persisted in full. The main article carries the properties the measurement
shows to be strong; a property measured weak is reported in the supplementary
material with its numbers, and the main article states the neighbouring
property that the measurement does support (the "A → A′" rule, spelled out per
research question under *Gate and fallback*). Nothing measured is discarded and
no baseline is removed for winning (`../foundation/lessons.md` L12).

---

## 0. What the experiments must prove, in one table

| RQ | The knowledge-base question | The property of the representation it exposes | Single evaluation axis |
|---|---|---|---|
| RQ1 | which addressing makes similar knowledge bases close | local stability of the adopted fact-rank encoding; the addressing frontier | single-edit response (tokens, normalized); ρ with the true fact-level difference |
| RQ2 | which distances are well posed for collection analytics | exactness + metric + polynomial cost, and the measured price of lacking each | false-merge census, metric-violation rates, oracle ceiling, certificate validity |
| RQ3 | which member is the reference record | certified medoid; a decoded consensus that is not any input | exact fact-level distance of the returned representative to the truth |
| RQ4 | which descriptions are structurally anomalous | distance-based screening over an exact metric; the iso-twin blind spot of incomplete representations | AUROC of recovering injected corruptions |
| RQ5 | which description patterns exist | licensed clustering (`ν > 0`, hubness) over an exact metric | ARI / NMI vs entity types; cophenetic correlation |
| RQ6 | can the collection be extended with valid new members | closed language: validity 1 by theorem; alignment interiors decode | validity rate; fidelity divergence |
| RQ7 | for which sizes does this run | envelope of both alphabets; labels as tie-breaker | wall-clock, time-out fraction, word length per `(m, k, |Σ|)` |

RQ1 was measured once already (`../foundation/probes_2026-09.md` §9) and its
selection is closed; the pipeline **re-measures it from the shipped encoder** so
that every number in the paper comes from one code base and one statistics
harness. RQ3 and RQ6 are the experiments that make the language visible; RQ2
and RQ4 are where exactness is visible; RQ5 is the honest task-metric row; RQ7
bounds the claims.

---

## 1. Global decisions (frozen)

### G1. The representation under test

**`fact_rank`** — fact tokens addressed by global canonical rank (arm B of
RQ1, adopted). Word of a knowledge base `K` with `n` constants and `m` facts:

```
T[τ(π⁻¹(0))] … T[τ(π⁻¹(n−1))]   F[ℓ₁; r₁ < … < r_a] … (m fact tokens, sorted by (ℓ, rank tuple))
```

`π` is the total order on constants induced by a canonical labelling of the
coloured Levi graph (`pynauty.canon_label`, vertex colour = type, edge-node
colour = `|Σ_V| + predicate`); `rank[v]` is the position of `v` in that order
restricted to constant nodes. One token is one atomic symbol; two tokens are
equal iff their whole tuple is equal. `|w| = n + m`.

**What is invariant is the word, not the rank vector.** A canonical labelling
is canonical only up to an automorphism of the canonical form, so the rank
vectors of `K` and of a relabelled copy need not correspond under the
isomorphism (measured 2026-09-05: 557 of 2,000 random labelled knowledge bases;
0 changed words). The word is invariant regardless, because such an
automorphism fixes the type prefix and the fact multiset. Consequence for every
algorithm in this design: never transport a rank vector between two knowledge
bases; compare words, and obtain alignments only from canonical labellings of
*isomorphic* objects (e.g. the isomorphic remainders of §RQ3's delete-and-match),
where rank equality is a genuine isomorphism.

**Roles.** A fact whose predicate has named argument positions carries
`(role, rank)` pairs instead of bare ranks (`F[ℓ; (ρ₁, r₁) …]`, sorted by rank).
Roles exist only in WD50K (subject / object / qualifier value). **The primary
arm on every table is `fact_rank` *without* roles**, because the competitors
see the same information (the labelled hypergraph, encoding E1) and the
comparison must be information-matched. `fact_rank_roles` is an ablation arm
in RQ1 (its stability cost) and RQ5 (does role information help).

**Distance.** `d_F(K, K′) = Levenshtein(w(K), w(K′))` over tokens, raw (never
length-normalized — L11). Computed with `rapidfuzz` on tuples of hashable
symbols. Alphabet scoping: one `(k_max, type vocabulary, predicate vocabulary)`
per collection; distances are never compared across collections.

### G2. The language (the decoder is total)

`decode(tokens)` is defined on **every** finite sequence over the token
vocabulary `Σ_F(n_max, k, Σ_P, Σ_T) = {T[τ]} ∪ {F[ℓ; ranks]}`: constants are
created in order — a `T` token appends a constant of that type; an `F` token
whose largest rank exceeds the current constant count appends untyped
constants up to that rank; facts form a set (a repeated fact is a no-op).
Consequences the experiments use: every prefix, every single-token edit, every
interior word of a Levenshtein alignment and every sample of a sequence model
decodes to a knowledge base (Prop 2 / Prop 6 of `../prose.md`); the decoded
class of a word depends only on the multiset of its fact tokens and the type
prefix, not on token positions (a lemma to be pinned by test; it is what makes
the fact-level ball of §RQ3 equal to the decoded string ball). Disconnected
knowledge bases are legal in this language.

### G3. Competitors and the contract

| name | what it is | exact at 0 | metric | pair cost | language | role in the tables |
|---|---|---|---|---|---|---|
| `fact_rank` | ours (G1) | yes | yes | `O(L²)` | yes | constructive member; every table |
| `nauty_cert` | Levenshtein over `color_signature ++ pynauty.certificate` **bytes** of the Levi graph (existing `nauty_levi_edit`) | yes | yes | `O(B²)` | no | **certificate member** of the family; every table (tokenization = bytes, stated) |
| `nauty_cert_rows` | Levenshtein over the canonical Levi adjacency rows as symbols | yes | yes | | no | supplementary ablation of the certificate tokenization (L9) |
| `wl_l1` | hypergraph-WL colour histogram, L1, labels honoured | no | yes | | no | incomplete embedding |
| `netlsd` | NetLSD heat trace on the Levi expansion, L2 | no | yes | | no | incomplete embedding (labels ignored: stated) |
| `hpd_jsd` | hyperedge portrait divergence | no | yes | | no | incomplete embedding |
| `bipartite_ged` | bipartite (Hungarian) edit-path cost, labelled unit costs (existing `bipartite_hged`) | no (false zeros in the raw reading) | **no** | `O((n+m)³)` | no | polynomial approximation to an edit distance; both readings in RQ2 |
| `exact_ged` | exact structure edit distance (existing `exact_hged`) | yes | yes | NP-hard | no | oracle ceiling in RQ2 only |
| `hypercot` | hypergraph optimal transport | — | local optimum | `O(n³)`/iter | no | capability matrix + one RQ2 timing row; gated `N ≤ 20` (L24) |
| `majority_merge` | fact kept iff present in `> N/2` members, **with constant identities** | — | — | | — | RQ3 reference only (uses information denied to every other method) |
| `size_l1` | `\|Δn\| + \|Δm\|` | no | pseudo | | no | naive floor, mandatory (L1) |
| `degree_seq_l1` | L1 between sorted degree sequences | no | pseudo | | no | naive floor, mandatory (L1) |
| `pointer`, `local_colour`, `local_key`, `degree_key` | the four displaced addressings (RQ1 arms A, C, D, D1) | yes | yes | | yes | RQ1 only; supplement |

Contract: every competitor runs on every table where its per-pair cost is
feasible on the collection; no competitor is dropped for winning; the naive
floors appear on every task table; `hypercot` and `exact_ged` are gated and the
gate is printed with the table.

### G4. Corpora (frozen files, one manifest each)

All collections are frozen to JSONL (one knowledge base per line: constants
with types, facts with predicates, optional roles, optional external identities
for evaluation only, optional class label) plus a `vocab.json`, under
`results/IEEETKDE/corpora/<collection>/`, and are the only inputs the runners
read. Derivations follow `../supplementary_data.md` exactly; the loader
reproduces its census numbers as an acceptance test.

| collection | members | labels on constants | labels on facts | ground truth carried | used by |
|---|---|---|---|---|---|
| `wd50k66` | WD50K(66) entity knowledge bases inside the envelope (`3 ≤ m ≤ 110`, `n ≤ 24`, arity `≤ 10`): 3,988 (3,994 without the `m ≥ 3` floor) | none (single type) | main relation; roles S/O/Q in a side field | Wikidata P31 class of the subject (14 classes with ≥ 20 members covering 87.6 %; imbalance stated) | RQ1, RQ2, RQ4, RQ5, RQ6, RQ7 |
| `wd50k66_full` | the same without the envelope filter (4,554) | | | | RQ7 yield row (fact alphabet only) |
| `wd50k100` | purity control (1,837) | | | 7 classes with ≥ 20 members (frozen census; the 8th has 19) | RQ5 supplement |
| `ndc_classes` | NDC-classes quarterly co-formulation knowledge bases, encodable (`3 ≤ m ≤ 110`, `n ≤ 24`, arity `≤ 10`, **facts of arity ≥ 2 only**): 1,381 members and 528 consecutive pairs with exact `Δ` and regime flag (1,432 / 555 when singleton products are counted as facts — the supplement's figure, reproduced to the unit); runs per class | FDA class type: `[epc]`, `[moa]`, `[pe]`, untyped | one predicate | NDC node identities (evaluation only); `Δ` of consecutive quarters | RQ1, RQ2, RQ3, RQ4, RQ7 |
| `ndc_substances` | control (1,745; 2,222 counting singletons) | none | one predicate | identities | RQ2 census, RQ7 yield (supplement) |

A singleton product (one class) is a unary statement, carries no relational
structure and is encodable by neither alphabet; the collections therefore keep
facts of arity ≥ 2 only, and `census.json` in each frozen collection is the
authoritative count (expected vs obtained, both conventions recorded).
| `synthetic_rq1` | 2,000 random connected labelled knowledge bases, `n ∈ [6,16]`, `m ∈ [6,20]`, arity 2–4, 3 types, 3 predicates (the probe's corpus) | 3 types | 3 predicates | — | RQ1 |
| `envelope_sweep` | random connected labelled knowledge bases on the RQ7 grid | grid | grid | — | RQ7 |

Derived, generated by the runners from frozen members with pinned seeds (their
generators are library code with tests): constant-preserving edit ladders
(RQ1 M2, RQ3), variant collections (RQ3), corruption sets (RQ4).

### G5. Statistics harness (one procedure everywhere)

- **Replication unit.** Where randomness exists, `S = 27` seeds; the
  seed-level aggregate is the sample for every test and interval (harness
  convention, L14). Where the unit is a real object (a pair, a member), the
  interval is a cluster bootstrap over the natural cluster (base knowledge base
  for edits and ladders; member for corruptions).
- **Intervals.** 95 % BCa bootstrap (`scipy.stats.bootstrap`, 10,000
  resamples, seed 0) for means and medians; Wilson 95 % for proportions;
  percentile bootstrap (1,000 resamples, clustered) for Spearman `ρ`.
- **Paired comparisons.** Ours vs each competitor on the same seeds:
  two-sided Wilcoxon signed-rank over the 27 seed-level scores; Holm correction
  over the family "all competitors in one table"; effect size = matched-pairs
  rank-biserial `r` and the BCa interval of the paired difference. Directional
  hypotheses are stated as such below and tested one-sided; everything else is
  two-sided. `α = 0.05`.
- **Unpaired contrasts** (regimes, strata): Cliff's `δ` with bootstrap CI;
  Mann–Whitney only if a test is needed.
- **Censoring.** Every time-budgeted computation reports the censored fraction
  per stratum; censored items are excluded from medians and counted (L15).
- **Persistence.** The Wilcoxon table, the Holm table and every interval are
  written to `stats.json`; the rows they were computed from are written beside
  them so any reader can recompute (L14: they were silently lost once).

### G6. Saved data — universal conventions

Every run writes, under `<RESULTS_ROOT>/<RQ>/<experiment>/`:

| file | content |
|---|---|
| `rows_<table>.csv` | one row per finest measurement unit (schemas below); columns always include `rq, experiment, collection, seed, arm, git_sha, host_cpu, secs, censored` |
| `config.json` | every parameter, seed, path, version, budget |
| `manifest.json` | git SHA, hostname, CPU model, Python and package versions, SLURM job/array ids, start and end wall-clock, row counts |
| `summary.json` | the aggregates that feed the tables |
| `stats.json` | intervals, Wilcoxon/Holm tables, effect sizes |
| `tables.md` | the human-readable tables (inputs for the article's figure/table designer, not the article itself) |

`RESULTS_ROOT` is `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE`
locally and `$HOME/results/IEEETKDE` on Picasso (the permanent filesystem, not
the purged FSCRATCH); the harvest script mirrors the second into the first. Cached `N × N` distance matrices live under
`<RESULTS_ROOT>/matrices/<collection>/<arm>.npy` with a sidecar manifest (member
order, arm parameters, wall-clock); every runner reads the cache before
computing.

### G7. Compute policy

Everything executes on Picasso (`../START_HERE.md` author instruction). Node
family pinned to `sd` (Intel Xeon Gold 6230R; the C++ extension is built on the
login node of that family with `-march=native`); wall-clock is a reported
quantity only under that pin. Every submitted task runs ≥ 2 h (units bundled,
start-cutoff with first-unit exemption); output staged on `$LOCALSCRATCH`,
mirrored back whole; `--account=tic_163_uma`. One smoke job per research
question is allowed below the floor. Seeds: master `20260905`; per-RQ seeds
`RQ_index · 10⁴ + s`, `s ∈ 0..26`.

### G8. What "main article" and "supplement" mean here

The design fixes, per RQ, which measured statement is the *main claim* if the
measurement supports it and which *neighbouring* statement takes its place if
it does not (the A → A′ rule). The decision is taken by the orchestrator on the
persisted numbers, recorded in `DECISIONS.md` of this folder with the numbers
that drove it, and never by deleting rows or arms.

---

## 2. RQ1 — Representation design (addressing)

**Question.** Which addressing makes similar knowledge bases close, at what
cost in exactness, compactness and time?

**Hypotheses (pre-registered; selection already made on the probe).**
H1a: `fact_rank`'s normalized single-edit response is below every other arm's
on constant-preserving edits, and its median absolute response to one inserted
fact over existing constants is exactly 1 token. H1b: on constant-changing
edits `fact_rank` is not better than `pointer` (the measured inversion; both
regimes are reported). H1c: `local_colour`, `local_key` and `degree_key` never
land within two tokens of a one-edit neighbour more often than `fact_rank`
(the frontier proposition's measured basis). H1d: the roles field costs
`fact_rank` at most +0.02 in normalized median response on WD50K.

**Corpora.** `synthetic_rq1` (2,000), `ndc_classes` (1,432), `wd50k66`
(3,994) — all members.

**Arms.** `pointer` (A; C++ `w*_c`, per-instance budget 60 s, `k` = pair
maximum), `fact_rank` (B), `fact_rank_roles` (B′, WD50K only), `local_colour`
(C, WL depth 3), `local_key` (D), `degree_key` (D1).

**Procedure.**
1. *M0 — exactness and invariance.* For every member: random relabelling
   `σ` → assert word equality; partition of the collection by word vs by the
   nauty fingerprint → false merges and false splits per arm (all must be 0).
2. *M1 — single-edit response.* For every base member and each edit kind in
   `{insert_fact, delete_fact, add_constant, remove_constant,
   insert_fact_new_constant}`, 4 distinct edits (rejection: result connected,
   inside the envelope, not isomorphic to the base; identical instances for all
   arms). Edit-kind semantics (the probe's, ported verbatim): `insert_fact` /
   `delete_fact` add or remove one fact over existing constants;
   `add_constant` / `remove_constant` add an existing constant to one fact or
   remove one from it (an arity change — the constant set is preserved unless
   the removal strands a constant, which is then compacted away);
   `insert_fact_new_constant` is the only kind that grows the constant set.
   The regime flag is stamped from the constant identities, not from the kind. Record `d(base, edited)` per arm, `|w(base)|`, `|w(edited)|`, the
   regime (`constant_set_preserved ∈ {0,1}`), and the *zero-shift* flag for
   `fact_rank` (canonical order of the surviving constants unchanged).
3. *M2 — correlation with the known fact-level difference.* (a) the 555 NDC
   natural consecutive pairs, `Δ = |F_t △ F_{t+1}|` from identities, regime
   flag; (b) 1,000 constant-preserving fact-edit ladders on `wd50k66` members,
   `t = 1..5`. Per arm: `d` per pair.
4. *M3 — compactness and cost.* Tokens per member and canonicalization
   wall-clock per arm (pinned `sd`), censoring per stratum of `n`.
5. *M4 — relation to the certificate.* Spearman `ρ` between each arm's
   distance and `nauty_cert` on the M1 pairs and on random pairs.

**Evaluation (one axis).** Median and IQR of the single-edit response,
absolute and normalized by `|w(base)|`, per corpus × edit kind × regime; the
Δ = 1 "within two tokens" fraction; Spearman `ρ(Δ, d)` on M2 per regime.

**Statistics.** Paired per instance across arms → Wilcoxon (Holm over the
arms) on the normalized response, per corpus and regime; medians with cluster
bootstrap over base members; `ρ` with clustered percentile bootstrap; the
"within two tokens" fraction with Wilson CI.

**Rows.** `rows_m1`: `collection, base_id, edit_kind, edit_idx, regime,
zero_shift, arm, d_abs, len_base, len_edit, secs_canon, censored`.
`rows_m2`: `collection, series, pair_id, delta, regime, arm, d, len_a, len_b`.
`rows_m0`: `collection, arm, n_members, n_classes_arm, n_classes_nauty,
false_merges, false_splits, invariance_violations`. `rows_m3`: `collection,
member_id, n, m, k, arm, tokens, secs, censored`. `rows_m4`: pair-level
distances for the two arms compared.

**Gate and fallback.** The pipeline must reproduce the probe within tolerance
(pooled normalized median of `fact_rank` within ±0.05 of 0.188 / 0.211 / 0.300;
`pointer` within ±0.05 of **0.57 / 0.56 / 0.60**). A discrepancy is a bug until
explained. No scientific fallback: the selection is closed.

*Amendment (2026-09-06, after the first campaign rows).* The probe's pointer
value of 0.500 (`../foundation/probes_2026-09.md` §9) is superseded. The probe
scored the pointer arm with `rapidfuzz.distance.Levenshtein.distance` applied
directly to tuples of `Σ_HG` tokens, and rapidfuzz compares generic sequence
elements by hash; `TokenP(i)` and `TokenN(i)` are hash-equal frozen dataclasses,
so pointer advances and retreats were matched against each other and the
response was under-reported on 67.3 % of pairs. Re-scoring the probe's own
corpus and edits with an equality-keyed alphabet
(`experiments/tkde/budget.py::symbol_distance`, regression-pinned) gives
0.569 / 0.556 / 0.600 on `synthetic_rq1` / `ndc_classes` / `wd50k66` (the
targets above, rounded); the pipeline measures 0.588 / 0.556 / 0.583. The
`fact_rank` targets are unaffected (0 of 2,400 probe pairs under-reported on
fact words) and stand. The selection conclusion — `fact_rank` responds to a
single edit at a third of the pointer alphabet's response — is unchanged and
strengthened. Normalization of the single-edit response: the distance is
divided by the length of the sequence it was measured over — the bare word for
every fact arm, and the seed-prefixed word (`|w| + 1`, the fingerprint
`F = (seed label, w*)`) for the pointer arm on collections with more than one
vertex label (`synthetic_rq1`, `ndc_classes`; `wd50k66` has one label and no
seed symbol). The rows persist `d_abs` and `len_base = |w|` unchanged.
Investigation record: `.claude/notes/2026-09-05-tkde-w3/rq1-gate.md`.

**Compute.** ≈ 150 k edited instances; arms B–D1 ≈ 50 µs each; arm A ≈ 125
core-hours at the 60 s budget → one array on `sd`, tasks bundled to ≥ 2 h.

---

## 3. RQ2 — Well-posedness (prerequisites and their measured consequences)

**Question.** Which distances satisfy the prerequisites the operations need,
and what does each missing one do to a real collection?

**Hypotheses.** H2a: every incomplete representation merges non-isomorphic
members of the real collections at a non-zero rate; `fact_rank` and
`nauty_cert` merge none. H2b: the bipartite edit-path cost is asymmetric and
violates the triangle inequality on real members at rates comparable to the
probe (38 % / 1.4 %); its raw assignment reading has false zeros. H2c: the
exact oracle completes only below `n ≈ 10` within a 600 s budget. H2d: under
a non-metric the medoid's pairwise lower bound is invalid (`LB > cost`) on a
measurable fraction of collections, so its "certificate" lies; under
`fact_rank` and `nauty_cert` it never does.

**Corpora.** `wd50k66`, `ndc_classes`, `ndc_substances` (census); the RQ3
variant collections (certificate validity); real pairs stratified by `n` for
the oracle.

**Procedure.**
0. *Exactness at zero, both directions.* For each collection and each
   representation: on 100 isomorphic pairs (random relabellings, `permute`),
   the fraction at distance 0 (`< 10⁻⁹` for real-valued arms) — a complete
   invariant scores 1.000; the audit of 2026-09-05
   (`COMPETITOR_AUDIT.md`) found the bipartite **edit-path** reading at
   0.08–0.19, i.e. it *separates* isomorphic knowledge bases, so it does not
   respect isomorphism classes and cannot carry a medoid certificate; HyperCOT
   returned 3.46 on an isomorphic pair (convergence failure) — negatives are
   clamped to 0 and the tolerance is stated.
1. *False-merge census.* For each collection and each representation: number
   of unordered pairs at distance 0 (or `< 10⁻⁹` for real-valued embeddings —
   NetLSD has 9 exact zeros but 186 below tolerance on 200 members, so the
   tolerance is not optional) whose members are non-isomorphic by the nauty
   fingerprint; number of classes induced by the representation vs true
   classes. Every per-pair computation is bounded at the **process level**
   (a forked child killed at the budget): the pointer alphabet's C++ call and
   the oracles do not return to the interpreter on time-out, so `SIGALRM` and
   the oracles' own `timeout` argument do not bound them (measured).
2. *Bipartite metricity on real members.* 2,000 random ordered pairs per
   collection: asymmetry rate of the edit-path reading; 5,000 random triples:
   triangle-violation rate; false-zero rate of the raw assignment reading on
   non-isomorphic pairs. Report the smallest violating triple found.
3. *Oracle ceiling.* `exact_ged` on 30 real pairs per stratum
   `n ∈ {≤ 6, 7–8, 9–10}` (both members in the stratum, `m ≤ 8`), budget 600 s:
   completion rate and median time (L23: nothing larger is scheduled).
4. *Certificate validity.* From RQ3's matrices: for every variant collection
   and every representation with a medoid, `LB = Σ_{i<j} d(K_i,K_j)/(N−1)`,
   `cost(medoid)`, and the flag `LB > cost`.
5. *Identity timing (the concession).* Canonicalization time per member:
   `pynauty` certificate vs `fact_rank` vs `pointer` (from RQ7's pass).

**Evaluation.** One table of measured consequences: rates with Wilson CIs;
counts.

**Rows.** `rows_census`: `collection, arm, n_members, n_pairs,
n_noniso_pairs, n_false_merges, n_classes_arm, n_classes_true`.
`rows_bipartite`: `collection, kind ∈ {pair, triple}, ids, d_ab, d_ba, d_bc,
d_ac, violation`. `rows_oracle`: `collection, pair_id, n_a, n_b, m_a, m_b,
secs, censored, value`. `rows_certificate`: `collection, collection_id, arm,
N, LB, medoid_cost, invalid`.

**Gate and fallback.** None needed: every row is descriptive. If the false-merge
rate of a representation is exactly 0 on a collection, that is reported (the
real collections are near-unique under labels; the census says so).

---

## 4. RQ3 — The representative record

**Question.** Given `N` descriptions of one thing that disagree, which is the
reference, and with what guarantee?

**Definitions (frozen).**
- *Reach.* `reach′_F(K → K′) = min{ |A| + |B| : A ⊆ F(K), B ⊆ F(K′),
  compact(K − A) ≅ compact(K′ − B) }`, the fewest fact-token indels from `w(K)`
  to a word decoding to `K′` (substitution excluded — the **indel** ball of
  Prop 5, because a substitution would collapse the `2t` gap between siblings).
  Computed exactly for `r ≤ 2` by delete-and-match: enumerate `A`, `B` with
  `|A| + |B| ≤ r` and compare canonical keys of the *compacted* remainders.
  **Amended 2026-09-09 (D-KBf5):** the remainders are compacted because a
  knowledge base is its set of facts (§2.1), so a deletion that takes the last
  fact naming a constant takes the constant with it; the earlier reading pinned
  the constant set and therefore returned ∞ on every deletion variant and on
  1,146 of the 1,400 natural Corpus B member pairs.
- *Coverage consensus.* Over candidates `C`, return
  `argmax_{c ∈ C} ( cov_r(c), −Σ_i min(reach′_F(c → K_i), r+1), lexicographic word )`
  with `cov_r(c) = #{ i : reach′_F(c → K_i) ≤ r }`. Candidates: the members, and
  every knowledge base `K_i − A′ + π(B′)` obtained from an alignment `(A, B, π)`
  of two members `K_i`, `K_j` with `|A| + |B| ≤ 2r` — the *triangle-complete*
  set, since a candidate within `r` of both members forces
  `reach′_F(K_i, K_j) ≤ 2r` — taking `A′ ⊆ A`, `B′ ⊆ B` with `|A′| + |B′| ≤ r`
  (alignment-transfer generation), with decoded classes deduplicated by
  canonical key. `π` comes from the canonical labellings of the two isomorphic
  compacted remainders, never from the ranks of `K_i` and `K_j` themselves (G1);
  it is therefore *partial*, and a transferred fact naming a constant `B`
  stranded creates that constant with the donor's type and identity — the
  `insert_fact_new_constant` edit (D-KBf5, 2026-09-09). The
  narrower budgets "per side" (`|A|, |B| ≤ r`) and "sum" (`|A| + |B| ≤ r`) are
  implemented as recorded variants only; under "sum" the source is provably
  outside the candidate set for `t = r`, which is how the ambiguity was found
  (2026-09-05). Default radius `r = 2` (budget unknown to the method); `r = t`
  reported as the known-budget variant.
- *Certified medoid.* `M = argmin_i Σ_j d(K_i, K_j)`; `LB = Σ_{i<j} d(K_i,K_j)/(N−1)`;
  `ratio = cost(M)/LB` (`≤ 2 − 2/N` by Prop 3 in any metric).
- *Truth and the axis.* Exact fact-level distance `|F(out) △ F(truth)|`
  computed with constant identities carried through the pipeline for
  evaluation only: a member keeps its identities; a candidate inherits the
  identities of the member it was derived from; a transferred fact is expressed
  in that member's constant space where it can be, and where it names a
  constant that member does not have, the constant is created and keeps the
  *donor's* identity. The methods never read identities.

**Hypotheses.** H3a (directional): the coverage consensus returns the source
exactly (distance 0) in ≥ 95 % of insertion-only and deletion-only variant
collections, and in ≥ 80 % of mixed ones, at `r = 2`, `t ∈ {1, 2}`. H3b: the
medoid's distance to the source is ≥ `t` by construction (it returns a member),
so the coverage consensus dominates it — the point is that no method
restricted to returning an input can do what a decoded consensus does. H3c:
the coverage consensus matches `majority_merge` (which uses identities) on
recovery rate within 5 points. H3d: every medoid ratio under `fact_rank` is
≤ `2 − 2/N`, and the measured ratios are ≤ 1.7.

**Corpus A — fact-edit variant collections over real members (primary).**
Sources: real members of `ndc_classes` and `wd50k66` with
`4 ≤ n ≤ 12`, `4 ≤ m ≤ 12`, max arity `≤ 6`; per cell `(collection, N ∈ {5, 9},
t ∈ {1, 2}, kind ∈ {ins, del, mix})`, 27 seeds × 8 sources = 216 variant
collections; members are `t` independent fact edits of the source (mix: each
edit insert or delete with probability ½), pairwise non-isomorphic and
non-isomorphic to the source (50 resampling attempts, else the collection is
dropped and counted). Every member is connected, and a deletion that takes the
last fact naming a constant takes the constant with it, so members of one
collection may differ from the source and from each other in constant count
(renamed off "constant-preserving" at D-KBf5, 2026-09-09;
`meta["constant_set_preserved"]` records which members kept the source's set).
**Deletion-only eligibility (amended 2026-09-05):** a source with `m` facts has
at most `m` single-fact deletions, fewer up to isomorphism, so `N` pairwise
non-isomorphic deletion variants need `m ≥ N + 1`; the deletion cells sample
their sources from that sub-pool (the first runner found the `N = 9, t = 1`
deletion cells 100 % dropped otherwise). Pool sizes are recorded per cell; a
cell with fewer than 8 eligible sources runs with what exists and is marked
`pool_limited`, an empty pool is marked `infeasible`.

**Corpus B — the natural NDC series (the harder case, reported beside A).**
Every drug class with a run of `T ≥ 4` consecutive encodable quarters (frozen
census: 42 classes with runs ≥ 3, 19 with ≥ 5): collection = quarters
`1..T−1`, truth = quarter `T`; reported for all runs and for the
constant-preserving runs separately. Constants change in 400 of the 528
natural consecutive pairs (76 %), so this is the regime in which the adopted
encoding is at its weakest, and the paper says so. Sizes come from
`corpora/ndc_classes/census.json` (`series` block), not from this text.

**Methods.** `medoid[d]` for `d ∈ {fact_rank, nauty_cert, wl_l1, netlsd,
hpd_jsd, bipartite_ged, degree_seq_l1, size_l1}` with certified ratio where `d`
is a metric; `coverage[fact_rank]` at `r = 2` and `r = t`; `majority_merge`
(identities; reference). The local-search generalized median is excluded on
the record of `../foundation/probes_2026-09.md` §1 (measured dead) and said so.

**Evaluation (one axis).** Exact fact-level distance to the truth; the
exact-recovery rate (distance 0). Secondary, under contract: the medoid's
certified ratio, wall-clock, number of candidates and ties.

**Statistics.** Seed-level means (27) per cell → BCa; paired Wilcoxon
`coverage` vs each medoid and vs `majority_merge` (Holm); recovery rates with
Wilson CIs; ratios reported as max and distribution.

**Rows.** `rows_variants`: `collection, seed, cell (N, t, kind), source_id,
collection_id, method, arm, fact_dist, exact_recovery, medoid_cost, LB, ratio,
n_candidates, n_ties, secs`. `rows_natural`: `class_id, T, regime_preserving,
method, arm, fact_dist, exact_recovery, ratio, secs`.

**Gate and fallback (A → A′).** If H3a fails because of ties among candidates,
the tie rule is the pre-registered `Σ reach` — no further tuning. If the
alignment-transfer candidate set misses the source in > 5 % of insertion-only
collections, that is a bug (the source is provably in it). If Corpus B shows
the consensus no better than the medoid, Corpus B goes to the supplement as the
characterized weak regime and the main text carries Corpus A with the regime
boundary stated (this is the plan of record in `../START_HERE.md` §6.0).

**Compute.** 2 collections × 12 cells × 216 = 5,184 variant collections;
per collection `N²` alignments × ≈ 200 canonicalizations at 50 µs ≈ 1–5 s →
a few core-hours; bipartite GED medoids dominate (`N²` pairs × ms). One array.

---

## 5. RQ4 — The data-quality screen

**Question.** Which descriptions are structurally anomalous, and does
exactness change the answer?

**Hypotheses.** H4a (directional, the exactness claim): on *iso-twin*
anomalies, incomplete representations score at chance (`AUC ≈ 0.5`, since the
twin is indistinguishable from the original for them), while `fact_rank` and
`nauty_cert` score above chance where the collection has structural repetition
(`ndc_classes`). H4b (non-inferiority): on spurious / missing / wrong-argument
corruptions, `fact_rank`'s AUC is within the 95 % CI of the best competitor's
on each collection — competitiveness, not superiority, is claimed.

**Corpora.** (a) `ndc_classes`, all 1,432 members (structural repetition:
≈ 7 members per unlabelled class); (b) `wd50k66` per-type sub-collections for
the six types with ≥ 47 members (human, film, big city, television series,
animated film, sovereign state) — anomalies must be judged against their own
kind.

**Corruptions (frozen).** Contamination 5 % of the members, chosen per seed;
the corrupted version **replaces** the original (the anomaly is a bad record,
not a duplicate). Types: `spurious_fact` (a fact over existing constants not
in the member), `missing_fact`, `wrong_argument` (one argument of one fact
replaced by another constant, fact stays distinct), each at budget
`b ∈ {1, 2}`; `iso_twin` (degree-preserving 2-fact swaps applied until the
result is non-isomorphic to the original — nauty-verified — with the same `n`,
`m`, arity histogram, degree sequence, type multiset and predicate multiset;
the WL-depth-1 histogram equality is recorded as a flag and reported). Every
anomaly is verified non-isomorphic to its original. One experiment per
`(collection, type, b)`; `S = 27` seeds.

**Scores.** Primary: mean distance to the `k = 5` nearest neighbours in the
precomputed matrix. Secondary: local outlier factor (`k = 20`,
`metric='precomputed'`). Representations: `fact_rank, nauty_cert, wl_l1,
netlsd, hpd_jsd, bipartite_ged, degree_seq_l1, size_l1`.

**Evaluation (one axis).** AUROC, anomaly = positive, per
`(collection, type, b, representation, score)`.

**Statistics.** 27 seed-level AUCs → BCa; paired Wilcoxon `fact_rank` vs each
representation, Holm within each `(collection, type, b)` table; rank-biserial
`r`. H4a is tested one-sided against 0.5 for the exact arms (Wilcoxon of
seed-level AUCs against 0.5) and reported for the incomplete arms.

**Rows.** `rows_auc`: `collection, subcollection, corruption, budget, seed,
arm, score, auc, n_inliers, n_anomalies, secs`. `rows_anomalies`: `collection,
seed, member_id, corruption, budget, twin_wl1_equal, noniso_verified`.

**Gate and fallback (A → A′).** If H4b fails (ours significantly below the
best competitor on the three standard corruptions on both collections), the
main-article RQ4 becomes the exactness consequence — the iso-twin table
(H4a) plus the false-merge census of RQ2 — and the AUC table on standard
corruptions moves to the supplement. If H4a is also null (exact arms at chance
on iso-twins), RQ4 has no main-text claim: it is reported in the supplement
and the orchestrator records the decision for the PI.

**Compute.** Matrices are cached from RQ5's pass; per seed, only anomaly-to-
collection distances are new (`≈ 0.05 · N²` pairs). Bipartite GED is the
slow arm. One array.

---

## 6. RQ5 — Description patterns

**Question.** Which patterns of description exist in a collection, and does
the structure recover known kinds?

**Hypotheses.** H5a (licences): on `wd50k66` the non-Euclidean mass
`ν(fact_rank) > 0` with a non-trivial negative Gram spectrum, and the
`k = 10` hubness skewness is moderate (`< 1.5`) — the measured licences for
PAM over centroid methods and for metric MDS over classical MDS. H5b
(directional): `fact_rank` recovers types better than both naive floors on the
balanced design. H5c (non-inferiority): `fact_rank` is within the CI of the
best labelled competitor (`wl_l1`, `nauty_cert`, `hpd_jsd`) on ARI. H5d:
`fact_rank_roles` does not lower ARI relative to `fact_rank`.

**Corpus.** `wd50k66` members with one of the 14 classes of ≥ 20 members
(≈ 3,500). Two designs: *full* (all members, imbalance stated, per-class
recall reported) and *balanced* (20 members per class sampled per seed,
`14 × 20 = 280`, 27 seeds) — the balanced design is the primary statistical
comparison because ARI on the full design is dominated by human and film
(73 %). `wd50k100` as purity control in the supplement.

**Methods.** k-medoids (PAM, `k = 14`, `metric='precomputed'`, 27
initializations); average-linkage agglomerative hierarchy cut at 14 →
ARI/NMI, and cophenetic correlation with the distance matrix; per-class
recall. Geometry per representation: `ν`, Gram spectrum, hubness (`k = 10`
`k`-occurrence skewness). Map: metric MDS (SMACOF, 2-D) with stress-1 on
`fact_rank` — a figure input, not an evaluation. Representations: all of G3
except the gated ones and the RQ1-only arms; `fact_rank_roles` as the
ablation.

**Evaluation (one axis).** ARI (NMI beside) against types; cophenetic
correlation for the hierarchy.

**Statistics.** Balanced design: 27 seed-level ARIs → BCa; paired Wilcoxon
`fact_rank` vs each arm, Holm; rank-biserial `r`. Full design: one value per
arm with a member-level bootstrap CI of ARI. Floors on every table.

**Rows.** `rows_clustering`: `collection, design, seed, arm, method ∈ {pam,
agglo}, k, ari, nmi, cophenetic, silhouette, secs`. `rows_per_class`:
`collection, design, seed, arm, method, class, support, recall, precision`.
`rows_geometry`: `collection, arm, N, nu, n_negative_eigen, largest_negative,
hubness_skew_k10, diameter_over_median`. `rows_mds`: coordinates and stress.

**Gate and fallback (A → A′).** If H5b fails (a naive floor within the CI of
`fact_rank` on the balanced design), the type signal is largely a size signal
on this collection; the main text then carries the unsupervised exhibit
(dendrogram with cophenetic correlation and the MDS map, both licensed by the
measured `ν`) and the ARI table moves to the supplement with the floors, as
L13 anticipates. If H5c fails but H5b holds, the ARI table stays with the
honest ranking.

**Compute.** Eight `N × N` matrices on ≈ 3,500 members (cached, shared with
RQ4); bipartite GED ≈ 6 M pairs at ≈ 0.2 ms → ≈ 20 core-minutes ×
parallelism. One array.

---

## 7. RQ6 — Generation

**Question.** Can a collection be extended with new, valid, plausible
knowledge bases?

**Hypotheses.** H6a: every sample of a sequence model over `fact_rank` words
decodes to a knowledge base (validity 1.000, asserted, by Prop 6); the same
model over a flat incidence-list serialization with a strict decoder rejects a
measurable fraction of its samples; no model is definable over certificates
(Prop 7, capability matrix). H6b: the structural profile of the samples is
close to the collection's (small Jensen–Shannon divergences on the size,
arity, predicate and type histograms), and most samples are novel (not
isomorphic to a member) while a stated fraction sit within reach 1 of one.
H6c: every interior word of the Levenshtein alignment between two real members'
words decodes (the decodability figure), while a certificate's interior decodes
to nothing.

**Corpora.** `wd50k66` (roles on for the exhibit: nothing abstracted away)
and `ndc_classes`.

**Procedure.**
1. Fit an order-3 token n-gram with interpolated Kneser–Ney (or
   Witten–Bell) on the collection's canonical words; sample 10,000 words per
   seed (27 seeds), decode all, assert validity.
2. Baseline: the same n-gram on a flat serialization
   (`n`, `FACT`, predicate, constant ids, `END`) with a strict decoder that
   rejects ill-formed sequences (unbalanced, out-of-range id, arity < 2,
   duplicate fact, dangling tokens): rejection rate; accepted samples continue
   to the fidelity comparison.
3. Fidelity: JSD between sample and collection histograms of `n`, `m`, arity,
   predicate and type; novelty = fraction not isomorphic to any member;
   neighbourhood = fraction within `reach_F ≤ 1` of some member (on a 1,000-
   sample subset).
4. Decodability figure input: 20 random pairs of real `wd50k66` members; the
   alignment path between their words; every interior word decoded, its
   `(n, m, connected)` recorded; the pointer-alphabet path for the same pairs
   (interior decodes; connected by construction) as the second panel.
5. Conditional completion exhibit: for 100 members, remove the last third of
   the fact tokens and sample completions; report validity and the fraction
   whose completion is isomorphic to the original or within reach 1.

**Evaluation (one axis).** Validity rate; fidelity divergences.

**Statistics.** 27 seed-level JSDs → BCa; paired Wilcoxon ours vs the
baseline's accepted samples; rejection rate with Wilson CI.

**Rows.** `rows_samples`: `collection, seed, model, n_samples, n_valid,
n_rejected, jsd_n, jsd_m, jsd_arity, jsd_pred, jsd_type, novelty, reach1_frac,
secs`. `rows_alignment`: `collection, pair_id, arm, path_len, n_interior,
n_decoded, n_connected`. `rows_completion`: `collection, member_id, seed,
valid, iso_original, reach1`.

**Gate and fallback.** Fidelity poor → the exhibit stays short (validity and
the impossibility for certificates hold by theorem); pre-agreed in
`../prose.md` §9.

**Compute.** Minutes; one job (bundled with RQ7's analysis to respect the
floor).

---

## 8. RQ7 — Operating envelope

**Question.** For which knowledge-base sizes, arities and vocabularies does
this run, and how does cost scale with `N`?

**Hypotheses.** H7a: the pointer alphabet's frontier is the fact count `m`
(not `n`) and labels are the tie-breaker; H7b: `fact_rank` and `nauty_cert`
are dominated by one canonical-labelling call and run in microseconds to
milliseconds across the whole grid and far beyond it; H7c: total cost is `N`
canonicalizations plus `N²` string comparisons, and the `N × N` matrix on the
full `wd50k66` is seconds for `fact_rank`, minutes for the embeddings, hours
for bipartite GED.

**Sweep.** Random connected labelled knowledge bases on the grid
`m ∈ {10, 20, 40, 80, 120, 160}` × `k ∈ {2, 3, 4, 5}` × `|Σ_E| ∈ {1, 3, 10}` ×
`|Σ_V| ∈ {1, 4}` × density `n ∈ {min(⌈1.5 m⌉, m(k−1)+1) (sparse), ⌈0.5 m⌉ + k
(dense)}`, 27 seeds per cell (7,776 instances). The sparse cap is the largest
connected constant count for `m` facts of arity `≤ k`; it binds only at `k = 2`,
where the sparse cells are trees (`n = m + 1`) — without it those 36 cells are
structurally impossible (found by the corpus generator, 2026-09-05). Arms: `pointer` (C++, budget 60 s),
`fact_rank`, `nauty_cert`. Extension for the fact alphabet only:
`m ∈ {320, 640, 1280}` at `k = 3`, `|Σ_E| = 3`, `|Σ_V| = 1`, both densities.
Real collections placed by their per-member `(m, k, |Σ|)` and measured
canonicalization time (from the corpus pass); yield per collection and size
bucket, including `wd50k66_full` under the fact alphabet.

**`N`-scaling.** Wall-clock of the full `N × N` matrix on `wd50k66` for
`N ∈ {250, 500, 1,000, 2,000, 3,994}` for every representation of G3 that runs
on it (3 repetitions).

**Evaluation.** Median and p90 wall-clock, time-out fraction, tokens (bytes
for the certificate) per cell; the yield table; the `N`-scaling curve.

**Statistics.** Bootstrap CIs of medians; no tests.

**Rows.** `rows_sweep`: `cell (m, k, sigma_e, sigma_v, density), seed, n, arm,
secs, censored, tokens_or_bytes`. `rows_yield`: `collection, bucket, arm,
n_members, n_completed, median_secs, p90_secs`. `rows_nscaling`: `collection,
N, arm, rep, secs_canon_total, secs_pairs_total`.

**Compute.** Pointer arm ≤ 7,776 × 60 s ≈ 130 core-hours worst case; the rest
minutes. Pinned `sd`; timing tasks single-threaded (`OMP_NUM_THREADS=1`).

---

## 9. Order of execution and dependencies

```
corpora frozen ─┬─► RQ1 (needs pointer arm: C++) ─┐
                ├─► RQ7 sweep + yield              ├─► RQ2 timing row
                ├─► matrices (wd50k66, ndc_classes; all arms) ─┬─► RQ5 ─► RQ4
                │                                              └─► RQ2 census
                ├─► RQ3 variant collections + natural series ─► RQ2 certificate validity
                └─► RQ6 (words only)
RQ2 bipartite metricity + oracle: independent, HPC.
```

Interpretation (the A → A′ decisions) happens after RQ3, RQ4, RQ5 land; RQ1,
RQ2, RQ6, RQ7 have no fallback branches.

## 10. Risks register (measured or anticipated)

| risk | consequence | mitigation in the design |
|---|---|---|
| the coverage consensus is "nauty + fact-level edit search" in substance | a reviewer says the language is not doing the work | RQ6 (generation, alignment interiors) and the decodability figure carry the string-native properties; RQ3's text says what the language contributes (a consensus that is a decoded word, not any input) |
| distance-based outlier detection is weak on near-unique collections | RQ4 null | per-type sub-collections; the iso-twin construction; pre-registered A → A′ |
| size confound in RQ5 (`T` prefix contributes `\|Δn\|`) | floors win | floors mandatory; balanced design; A → A′ |
| bipartite GED too slow at `N ≈ 3,500` | missing arm | it is `O((n+m)³)` per pair at `n + m ≤ 134`: minutes on 52 cores; if not, subsample and state |
| C++ extension built on the login node is not portable | SIGILL on AMD nodes | every job pinned to `sd` |
| Picasso queue pressure | schedule slips | arrays throttled; all runners idempotent per unit; harvest incremental |

## 11. Open points for the author / PI (recorded, not blocking)

1. Roles as the primary arm on WD50K (information-matched comparison says
   no; faithfulness says yes). Design: primary without roles, ablation with.
   Reverse if the PI prefers faithfulness on every table.
2. RQ3 Corpus B (natural series) in the main text or the supplement — decided
   on the measurement per §4's fallback.
3. Whether `hypercot` appears anywhere beyond the capability matrix (gated
   `N ≤ 20`): the design runs it only for the RQ2 timing row.
