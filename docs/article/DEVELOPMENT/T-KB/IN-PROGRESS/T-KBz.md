# T-KBz — RQ3 v2: the golden record from N anonymous noisy descriptions

**Status:** IN-PROGRESS (2026-09-13 13:32 CEST) · declared 2026-09-13 by the
headline-design orchestrator (`../../../D_ART3/experiments/HEADLINE_DESIGN_2026-09-13.md`
§3), executing D-ART6. Wave `2026-09-13-headline-w0`, agent `rq3v2`. Peer task:
T-KBaa (RQ8), T-KBab (the RQ2/RQ5 `w°` swap).

## What

Redesign and run RQ3 under conditions its own premise allows, so that the
paper's second headline exhibit (H2 of the design's §0 table) can be scored.

RQ3 v1 could not answer its question. Its majority merge read the constant
identities every other method was refused, so an oracle competed as a baseline;
its medoids could only return a member, which is a structural floor rather than a
result; its natural NDC quarters tied under an underpowered gate; and its
deletion ladders failed for every method at a pre-registered ≥ 0.95 that no
method could reach. v2 fixes the conditions: every baseline is anonymous, the
identity merge is labelled an oracle wherever it appears, the strata are
star / non-star because on a star the isomorphism class is the multiset of fact
patterns and counting determines it, and the two consensus arms are scored
against each other so the word-space claim is bounded rather than asserted.

**Deliverables.**

- `experiments/tkde/rq3v2.py` — the runner: the four anonymous noise kinds mixed
  and R3-connected with the realised mix logged, the G0 strata, eleven medoid
  arms, the three anonymous merges, the pattern vote, the identity oracle, and
  the two consensus arms.
- `experiments/tkde/analyze_rq3v2.py` — `summary.json`, `stats.json`,
  `tables.md`; H3.1–H3.6 with BCa intervals, Holm-corrected paired Wilcoxon over
  seeds and rank-biserial, and each declared fallback printed when triggered.
- `experiments/tkde/configs/rq3v2.yaml` — the pre-registered design, with
  `smoke` and `pilot` overlays.
- `tests/experiments_tkde/test_rq3v2.py`.
- `slurm/tkde/rq3v2_{launcher,worker,sync}.sh`.
- `docs/article/D_ART3/experiments/RQ3V2_PILOT.md` — gates G0, G3.1, G3.2 and
  the priced pilot.
- `docs/article/D_ART3/foundation/rq3v2_facts.md` — the fact base (T-KBg
  precondition).

## Gates (all measured before submission; tables in RQ3V2_PILOT.md)

- **G0 — star census.** `ndc_classes` 0 stars of 212 inside the source window
  (3.0 % corpus-wide); `wd50k66` 1,011 / 1,871 = 54.0 % (53.4 % corpus-wide).
- **G3.2 — the corrected v1 run harvested.** Deletion-regime recovery 0.517
  pooled against v1's pre-correction 0.13–0.28; every medoid 0.000; 93.3 % of
  winners were objects no member wrote.
- **G3.1 — reach coverage.** Fact reach 1.000 at r = 1 on every cell. Ball
  reachability of the source class 1.000 at r = 2 on the mixed model at t = 1,
  both corpora, both strata; 0.375 on the deletion-heavy ndc t = 2 cell, which
  is reported as the r = 2 envelope boundary rather than patched. Canonical-word
  locality: a deletion moves `w°` by 1 token, an insertion by 5–14, and `w°` is
  materially less local than `w*_c` on `ins_new_constant`.

## Decisions

- **D-KBz1 (orchestrator, 2026-09-13).** `ndc_classes` star cells are
  structurally empty; they emit one `cell_empty` row carrying the reason and H3.4
  is measured on `wd50k66` alone.
- **D-KBz2 (orchestrator, 2026-09-13).** `consensus_ow` is defined in **word**
  space — the decoded token ball, grouped by certificate — or the exhibit does
  not use a property of IsalHG and fails the design's criterion (a).
- **D-KBz3 (orchestrator, 2026-09-13).** The primary objective is the
  **generalized median** in the word metric: minimise
  `Σᵢ d_I(w°(M), w°(Kᵢ))`, ties by coverage, then by shortlex of `w°`.
  Pre-registered on three a-priori grounds — the classical string-consensus
  objective; the medoid is the same objective restricted to the members, so the
  consensus cost is at most the medoid's; and Prop 3's pairwise bound gives a
  certified ratio `cost / LB` that a coverage objective cannot have. v1's
  coverage order runs as a named ablation on every collection.
- **D-KBz4 (orchestrator, 2026-09-13).** `consensus_fact` — v1's fact-space
  `reach′` computation at the same radius — is a pre-registered arm, and **H3.5**
  states `consensus_ow ≥ consensus_fact − 0.05` at lower enumeration cost. If
  the fact-space arm is strictly better that is reported and RQ3's language claim
  reduces to the decoded output, the certificate and the cost.
- **D-KBz5 (orchestrator, 2026-09-13).** **H3.6** is pre-registered: recovery
  under the median rises with `N`, and the `N = 5` shortfall is a *sub-record*
  rather than an arbitrary object. Every consensus row carries
  `sub_record_drop`.
- **D-KBz8 (orchestrator, 2026-09-14, after campaign 2308421).** 37 of 122 tasks
  hit the 8 h wall; 358 of 648 units written. The re-price from the campaign's
  own logs put a unit at 0.19–3.13 h in eleven cells and at or beyond the wall in
  seven. **Cause: the exact-HGED judge, not the ball.** At `N = 15` the ball is
  127 s of a ≥ 540 s collection; the rest is ~20 judge calls per collection on
  the merges' large wrong records, which grow with `N` because
  `align_merge_iter` admits a constant once ≥ N/2 members carry an unmatched one
  of the same type and pattern. 17.8 % of judged rows already fell back to
  `bipartite_ged_path` after burning the full 60 s budget.
  **The declared restricted-ball fallback was NOT applied**, because it addresses
  ~20 % of the cost and would have looked like a remedy without being one.
  Ruled instead (option B): the seven heavy cells re-run under a **shorter oracle
  budget, 8 s**, which is a measured parameter and therefore its own run tag
  (`1efdcf54` against the frozen `ef0c58b4`). All 27 seeds per heavy cell, not
  only the missing ones, because a cell split across two budgets is two
  instruments averaged; the analyzer refuses that (`check_one_tag_per_cell`) and
  the first pass's 18 heavy-cell units are superseded with
  `--supersede-tag ef0c58b4`. The primary metric, exact recovery, is
  certificate-based and untouched by the judge's budget; the secondary,
  fact distance (H3.2), is tested within cell and now footnotes its
  exact-vs-bipartite rate per cell.
  Arrays: **2311518** light (40 units, 6 h, 32G, frozen tag), **2311519** empty
  (79 structurally-empty units, 1 task, 1 h, 8G, frozen tag), **2311520** heavy
  (189 units, 6 h, **64G**, new tag). 64G because 2308421 peaked at 25.9 GB
  against 32G on a heavy task; there was no OOM in my array.
- **The pricing error, recorded rather than smoothed over.** The pre-submission
  estimate of 1.6–3.3 h per task was extrapolated from a two-collection smoke at
  `N = 5` on `ndc_classes`, and `N = 9` / `N = 15` were never measured — both
  pricing runs were killed by my own later code changes. The submission went
  ahead on the sound reasoning that deferral is safe (it was; no row is wrong),
  but the honest label at that moment was "unpriced", not a range.
- **A launcher defect, found by triggering it.** `rq3v2_launcher.sh` read only
  `$1`, so `--resume-heavy --dry-run` submitted a 189-task array while reporting
  a dry run. The three recovery arrays above were launched that way; their
  parameters were verified correct after the fact (`scontrol`: 6 h/32G, 1 h/8G,
  6 h/64G, arrays 40/1/189) so nothing had to be cancelled. The launcher now
  parses every argument and refuses an unknown one.
- **D-KBz7 (orchestrator, 2026-09-13, pre-registration amendment).** The word
  metric of the median is the **indel** distance
  (`|w₁| + |w₂| − 2|LCS|`), not Levenshtein. It is the metric of the ball the arm
  enumerates, and a substitution has no fact-level counterpart at unit cost: two
  members differing by a fact *swap* are one Levenshtein edit apart and two fact
  edits apart, and the under-charge falls on exactly the candidates that compete
  with the source. Derivation on the star fixture: under Levenshtein the source
  costs 4 and two sub-records also cost 4 (tie; the tie break decides, and
  shortlex decides downward); under indel the source costs `N` and every
  sub-record `2(N − 1)`, strict for `N ≥ 3`. Remaining ties break by coverage,
  then by the size-neutral augmented-fingerprint order. Shortlex is retired as a
  tie break and survives only as a test of its bias. Arms: `consensus_ow` (indel),
  `consensus_ow_lev`, `consensus_ow_coverage`, `consensus_fact`. The medoid arm
  `isal_ow_indel` is added so the certified ratio is compared within one metric;
  `isal_ow_struct`'s ratio is the Levenshtein one and is not comparable with it.
- **D-KBz6 (orchestrator, 2026-09-13).** Picasso deployment: private runner tree
  on **HOME** (`~/repos/IsalHG-rq3v2`) because FSCRATCH is at its file quota with
  the grace expired and is read-only; the **shared** `isalhg-tkde` environment
  with `--no-build`, since nothing under `src/` changes; results on HOME under
  `~/results/IEEETKDE_ow/`.

## Defects found and fixed (each with a regression test)

1. **The ball's distance was read off the word length**, which scores an
   insert-and-delete pair as 0 and corrupts the objective's distance criterion.
   Now the BFS shell index, which is the exact indel distance because the shells
   are generated over single edits.
   `TestBall::test_the_shell_index_is_the_indel_distance`.
2. **Outputs were scored uncompacted.** `majority_merge` carries the union of the
   identities, so a constant whose only fact lost the vote survived with no fact
   and the result was disconnected — which reported the identity *oracle* as
   failing at `t = 1` on a collection where it recovers the source. A knowledge
   base is its facts (D-KBf5), so every output is compacted before scoring.
   `TestScoring::test_an_output_is_compacted_before_it_is_scored`.
3. **`pattern_vote` counted presence, not multiplicity**, rebuilding a four-fact
   star as a one-fact record and quietly removing the star control.
   `TestMergeBaselines::test_the_pattern_vote_counts_multiplicity_not_presence`.
4. **`pattern_vote` reused a constant of matching type whenever one existed**,
   attaching every fact of a star to the same leaf. A type now counts as shared
   only when some member holds two or more constants of it at degree ≥ 2 — one
   such constant is exactly the hub.
   `TestMergeBaselines::test_the_pattern_vote_recovers_a_star_with_distinguishable_facts`.

## The stale-row guard (T-KBn)

RQ3 v1 decided which units were done by reading its own **untagged** aggregate
back off disk, so when the arm set changed the runner re-served rows that
contained no Isal arm at all, under a manifest claiming otherwise. v2 tags every
row with `run_tag` (the rq1 convention: an 8-hex SHA-1 over the measured
configuration, excluding `n_shards` and `smoke`) **and** scopes the file name to
it, `rows_golden__<tag>-<unit>.csv`, which is RQ2's safe precedent. A changed arm
set is a changed tag and therefore a different file, so stale rows cannot be
served. `TestStaleRowGuard`, five cases.

## Acceptance

- [x] G0, G3.1, G3.2 measured and written to `RQ3V2_PILOT.md` before submission.
- [x] Runner and analyzer implement the spec; rows tagged; strata handled.
- [x] Unit tests green; ruff and mypy baselines not grown.
- [x] Synced to Picasso; smoke jobs **2308373** and **2308392** both COMPLETED
      (00:05:09 each, 36 and 40 rows, copy-back OK, every arm present, `hypercot`
      censored there with its reason because its pinned env is not on the
      cluster); campaign **2308421** submitted 2026-09-13 13:57 CEST, a 122-task
      array at throttle 64, 64 tasks RUNNING at the time of writing.
- [ ] Local pilot green through the analyzer, with the priced full-run cost.
      *(Restarted after the indel amendment; the ball choice is already recorded
      in `RQ3V2_PILOT.md` with its arithmetic, and the campaign does not wait on
      it because a slow cell degrades into a deferral, not a wrong row.)*
- [x] H3.1–H3.6 verdicts written into `rq3v2_facts.md` (§7 after the harvest's
      renumbering) — on the 11 complete cells only, with the untestable cells
      named (2026-10-04, agent `harvest`).
- [ ] Every non-empty design cell complete at 27 seeds under one tag. **Not met:**
      7 of 18 are partial or absent (below).

## Closing evidence — the harvest (2026-10-04 10:20 CEST, agent `harvest`)

All four arrays harvested to
`/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE_ow/RQ3v2_golden_record/anonymous_consensus/`
(490 row files: 477 `ef0c58b4`, 13 `1efdcf54`) and analysed with
`--supersede-tag ef0c58b4 --expected-seeds 27`; outputs in that directory's
`_analysis_ef0c58b4+1efdcf54/`. Fact base: `../../../D_ART3/foundation/rq3v2_facts.md`
§6–§12; appended summary in `RQ3V2_PILOT.md` § "The harvest".

- **Coverage.** 2311518 40/40, 2311519 done, **2311520 11 COMPLETED / 178
  TIMEOUT, 13 units written** (one more finished 17 s after its cancel and was
  lost). 11 cells complete, 4 partial (`ndc` non-star N9 t2 11/27, N15 t1 2/27;
  `wd` non-star N9 t2 3/27; `wd` star N15 t2 3/27), 3 absent (`ndc` non-star N15
  t2; `wd` non-star N15 t1, t2), 6 empty by construction.
- **Verdicts (complete cells).** H3.1 supported on the tested cells, not testable
  at N = 15 and at non-star N = 9, t = 2; H3.2 supported vs 11 medoids
  (`hypercot` unscored); H3.3 not supported (0.385 vs oracle 0.921); H3.4 not
  supported (no tie, 0.491 vs `pattern_vote` 0.032 — baseline unaudited); H3.5
  not supported (0.433 vs `consensus_fact` 0.984, cheaper too) → the declared
  fallback applies; H3.6 not supported as stated (monotone 4/4, but most N = 5
  misses are not sub-records).
- **D-KBz8's cause does not survive 2311520.** At an 8 s judge the heavy units
  still exceeded 6 h because the ball is 99.1–99.7 % of each written unit's
  wall; the judge and all untimed work is 2–7 s per unit. The 127 s/collection
  basis of the 8 s arithmetic came from the one easy N = 15 cell, and the
  "17.8 % fallback after 60 s" is the `n > 10` ceiling.
- **Analyzer repaired** (crash under pandas 3; no coverage gate; H3.2 family
  missing the indel medoid; H3.6 confounded by composition under partial
  coverage), each with a failing-first test in
  `tests/experiments_tkde/test_rq3v2_analysis.py`.

**Why this stays IN-PROGRESS.** Seven heavy cells are incomplete, so H3.1's
"every N" is undecided and nothing at relational N = 15 exists; completing them
at the registered ball needs ~1.1–2.9× the 6 h wall per unit (or a smaller
ball), a resubmission decision this harvest did not take. Two items also need an
owner before the prose: the `pattern_vote` audit behind H3.4, and what the paper
says now that a representation-free consensus wins H3.5.

## Out of scope

The prose fold (T-KBg); `DEVELOPMENT/README.md` counts (the orchestrator updates
them at merge); the natural NDC series, kept as v1 measured it; any edit to
`rq3.py` or `src/`; RQ8 and the RQ2/RQ5 swap (T-KBaa, T-KBab).

## Notes

- A helper this task wanted in `src/`: `isalhg.language.consensus.coverage_consensus`
  has no way to swap its tie-break word, so `consensus_ow` is written in
  `rq3v2.py` rather than parameterising the frozen function. The change I would
  have made is a `tie_break: Callable[[SparseHypergraph], Any] | None = None`
  parameter defaulting to `isal_fingerprint`. Reported to the orchestrator; not
  made, because `src/` is read-only for this wave.
- `isalhg.metric_space.distances.hged._bipartite_matching` is imported by
  `align_merge_ref` so the reference-anchored baseline is aligned by the same
  Riesen–Bunke construction that the `bipartite_ged_assign` arm scores with, and
  therefore by the same machinery that chose the reference. It is private; if it
  is to stay a dependency it should be exported.
