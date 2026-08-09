# Decisions pending PI (mirror `CODE_DESIGN.md` §11)

- **D-M4b** — **[RESOLVED 2026-08-09, PI (Mario), in-session]** The
  size-controlled replacement corpus (T-M4b): **build Stratum C and report the
  honest outcome** per the pre-registered `COMPETITORS.md` §4 contract — PI:
  "we want to have good data first"; any post-hoc scope call on weak results
  stays with the PI. Full replacement of the primary corpus authorized; the
  binding requirement is a clean data-decision story (now `DATA.md` §1 + §7).
  **Adopted design:** 3 cells (9,12)/(12,20)/(15,35), k=3, irregular fixed
  degree sequence per (cell, seed), 12 swap-planted families × 6 members,
  t=2 incidence swaps, 10·m-swap seed separation, pynauty-Levi dedup, per-cell
  analysis, S=27 seeds. **Alternatives measured and rejected:** STS(15)-seeded
  families (pristine `w*_c` >900 s on rigid instances *and* total avalanche —
  within ≈ between d_I, ARI ≈ 0.03); STS(19) (same cost wall); old corpus +
  disclosure row (F7 option D — concedes A2/A3 measure size); rescoping A2/A3
  out (not taken; PI reserves it post-data). **Measured context the decision
  rests on:** single-edit d_I response is ≈30–50% of the string on every
  unanchored substrate (swap and Qin alike), so planted classes are
  d_I-unrecoverable while NetLSD (pilot) and nauty-Levi-edit (harness pilot,
  1 seed) do recover them — the honest outcome will likely show a competitor
  leading A2/A3 on the controlled corpus. Consequences for prose: A2/A3
  reframed around the measured avalanche/drift mechanisms; the discussion's
  impossibility argument gains task-level evidence. Execution: T-M4b (this
  session); `size_l1` registered as the second permanent naive baseline.

- **OD7** — **[PENDING PI]** Label-stripped HIC re-run: should the HIC genre
  corpora additionally be run with `LabelVocabulary.trivial()` (labels stripped)
  to produce a structural-only real-data row `d_I^⊥` per dataset? One extra
  `D.npy` per HIC dataset; makes the synthetic↔real geometry comparison
  apples-to-apples (`d_I^⊥` vs `d_I^⊥`, isolating the structural contribution
  from the vocabulary effect). As established in `theoretical/geometry.md` §3
  (and the Remark in `stability.md` §1), the HIC rows currently measure `d_I^Σ`
  (label-aware member) while the planted rows measure `d_I^⊥` (structural
  member); these are incomparable family members and the lower HIC `D̂ ≈ 10–11`
  may partly reflect the vocabulary rather than purely structural differences.
  Cost caveat (orchestrator correction, 2026-07-22): the `w*_c` cost is NOT
  unchanged under label-stripping — labels enter the seed cascade and the
  tie-breaking, so trivialising the vocabulary weakens tie-breaking and the
  tie-complete branching cost can only stay equal or grow; on near-symmetric
  instances it can grow sharply (the T-DQ3' DNF tail was symmetry-driven with
  labels still present). The stripped run therefore needs its own censoring
  pass, and the clean-dataset yield may drop below the labelled run's.
  Recommended only after a small stripped pre-pilot on one clean HIC dataset
  confirms acceptable yield. Not gating on any article claim. Execution owned
  by T-M7g if adopted.

- **OD6** — **[RESOLVED 2026-07-20, PI (Mario) directed: INCLUDE]** The
  *secondary* censored-subset HIC exhibit is adopted: run A1 (MDS + geometry
  table), A2 (clustering), A3 (kNN) on real HIC data **alongside** the planted
  fallback (which stays the primary corpus). **Scope (PI choices, 2026-07-20):**
  all **6 IMDB genre variants** (`IMDB-{Wri,Dir}-{Genre,Genre-M,Form}`), the
  **full arity ≤ 10 subset** per dataset. A4 (shortest-path) is **out of HIC
  scope** — it is ladder-based (synthetic perturbation budgets); HIC has no
  ladder structure. **Censoring protocol:** per-instance `w*_c` computed under
  a hard 5 s timeout (multiprocessing kill); DNFs dropped; per-class yield
  reported per dataset; framed as a credibility exhibit, not the anchor.
  **Feasibility (measured 2026-07-20):** on IMDB-Wri-Genre the arity ≤ 10
  subset is 901 items with 93% `w*_c` yield at 5 s (median 1 ms; DNFs are the
  T-DQ3' symmetry tail, e.g. n=8 m=13); IMDB-Dir-Form is the worst case
  (~57% yield, heavier label-correlated censoring — reported, not hidden).
  Executed under **T-M5j** (`T-M5/`). The primary-anchor fallback (`DATA.md`
  §2) is unchanged; HIC application claims are stated as censored-subset
  claims with the yield table attached.
- **OD1** — **[RESOLVED 2026-07-20, PI (Mario), at the S5 sweep]** Architecture:
  the **additive `metric_space/`** (the recommended option, de facto since
  T-M1a) is adopted. Reparenting to `isomorphisms/` remains exactly the
  optional T-M6 (S6, explicit opt-in) — executing T-M6 is the only path that
  reopens this.
- **OD2** — **[RESOLVED 2026-07-20, PI (Mario), at the S5 sweep]**
  `levi_reduction` home: **`core/levi_reduction.py`** (the recommended option,
  de facto since Phase 2; every Levi backend imports it from there).
- **OD3** — **[resolved 2026-07-18, author]** HyperCOT: dedicated pinned conda
  env via subprocess; runs on the small/mid corpora only, its `O(n³)`/pair
  scale limit stated in every results table (part of the D-ART2 package).
- **OD4** — **[resolved 2026-07-08]** `ExactHGED` = our own A*/ILP over the six
  edit ops. The `networkx.graph_edit_distance`-on-Levi wrapper is rejected: GED
  on the bipartite Levi graph is not obviously equal to HGED (vertex/edge nodes
  differ semantically; the cost-lift needs an unproven correctness argument).
- **OD5** — **[RESOLVED 2026-07-20, PI (Mario), at the S5 sweep]**
  `metric_space/metrics/embedding.py`: the classical-MDS solve + stress stay a
  **`src` primitive** (the recommended option; unit-tested at T-M5f, consumed
  by the T-M5b/T-M5j pipelines). Only the CV-dimension *loop* lives in
  experiments.
- **D-TA1** — **[resolved 2026-07-09, PI]** Which algorithm carries the
  article's `w*`. Theorem A (completeness ⇔) holds only for
  `greedy_min_complete` (tie-complete branching); the current default
  `greedy_min_nbrdeg` is presentation-dependent (edge-order counterexample,
  pinned test) and supports only the one-sided claim. **Decision: option (b)
  — the complete algorithm becomes the package default** for the IsalHG
  canonical/H2S pipeline, contingent on the T-TAd C++ port making it fast
  (admissible-pruning lemma is the sanctioned speed lever); goldens/caches
  regenerate where `w*` changes on tie-degenerate inputs. Executed at T-TAd.
- **D-TA2** — **[resolved 2026-07-09 11:38 CEST, PI]** *Which* tie-complete
  lex-min is the article's `w*_c`. **Decision: the unpruned tie-complete lex-min.**
  PI: "set the algorithm to be the tie-complete lex-min unpruned — that is our
  maximum priority. I'm willing to choose the most correct encoding algorithm for
  now, implement it in C++, and write the whole paper for it. Then, if we need, we
  optimise the algorithm." Correctness of the canonical form outranks its cost; the
  only sanctioned future speedup is stabiliser-orbit pruning (value-preserving by
  Proposition 6.0), never `ρ`-refinement (Lemma 6.1, which changes the form).
  Note the cost is already paid: the C++ tie-complete encoder shipped at T-TAa
  (`AlgorithmVariant::GreedyMinComplete = 7`, Fano 6.41 ms, random n ≤ 12 medians
  ≤ 0.7 ms). Executed at T-TAf; flipped at T-TAd.

  *Reasoning of record.* Lemma 6.1 of `theorem_a_completeness.tex`
  preserves **completeness** under any iso-invariant refinement key `ρ` of the
  residual tie set, but the refined search returns a **different canonical
  form** ("a κ-minimum over a proper subset of `T(σ)` need not equal the
  κ-minimum over `T(σ)`"). So `ρ`-pruning is a fork in the *definition* of
  `w*_c`, not an optimization of it, and it is one-shot: once tables are
  computed on one form, adopting the other changes every `d_I` value.
  The frozen form is the *unpruned* tie-complete lex-min, matching the proof text
  and the shipped C++ variant 7. Exactly one future speedup is sanctioned —
  **stabiliser-orbit pruning**, which by Proposition 6.0 returns the *same* `w*_c`
  (coherent tied branches have equal completions) and is the only lever that
  attacks the real cost, automorphism redundancy on vertex-transitive designs.
  T-TAa measured the alternative: `ρ`-refinement buys nothing there, since every
  tied candidate carries the same value under any iso-invariant key.
- **D-CONN1** — **[resolved 2026-07-09, PI]** The article's domain of discourse.
  `Σ_HG` provably cannot express disconnection (every `V_{i,j}` has `i ≥ 1`; no
  token creates an isolated vertex), so the S2H-reachable set *is* the connected
  hypergraphs, and Theorem A is stated only there (Assumption 1.3).
  **Decision: restrict the article to connected hypergraphs. The alphabet does not
  change.** Both glues are rejected — the alphabet extension would reopen Theorem A
  and invalidate the T-TAa C++ encoder; the sorted-tuple fingerprint would cost the
  paper its central claim ("a hypergraph is a word") and hold invariants #2/#3 only
  per component. Consequences: synthetic generators become connectivity-preserving
  and the paper says *connected* ER (the conditioning changes the ensemble); real
  corpora are restricted to their largest connected component with per-class
  retention reported; and the stability proof's transient-disconnection problem is
  discharged by a **path-normalization lemma**, not by native support — the triangle
  inequality bounds `d_I` along any path, so an all-connected path of the same Qin
  cost suffices (insert-before-delete, vertex insertions paired with an incidence).
  Executed at T-M2c; the lemma is `stability.md` §6 item T-B0.
- **D-ART1** — **[author-adopted 2026-07-17 (Mario), executed in docs; PI
  confirmation pending]** The article's headline claim.
  **Decision: lead with the metric geometry, not the stability bound.**
  Thesis becomes "`(w*_c, d_Lev)` is a complete, computable metric whose induced
  geometry (intrinsic dimension, Euclidean distortion, structural faithfulness) we
  characterize and validate"; Theorem B is repositioned from "★ core novelty" to
  the *faithfulness engine* — a regime-characterized bound with two named,
  measurable deviation mechanisms (drift, avalanche) and a per-edit error budget,
  still the sibling delta (IsalGraph gave no bound), no longer the sole
  load-bearing claim. *Rationale:* T-TBb proved the clean Lipschitz bound is
  conditional on five hypotheses, two of which fail generically (run-locality (v)
  by the orphaned introducer; average span-boundedness (iv) asymptotically), so
  leading with it aims peer review at the paper's weakest point, while the
  empirically-validated geometry (T-M5) is the real strength and matches the fixed
  decisions (raw Levenshtein over instruction strings, `w*_c`). *Scope of the
  decision:* framing only — the distance default stays **raw** `d_I`; displacement
  transcoding promotion is a separate, evidence-gated decision (T-TBc). Full
  argument in `theoretical/stability_reformulations.md` §7.

  *Sub-decisions (2026-07-17, with Mario).* (1) **Narrative order**
  foundation → geometry → usefulness → faithfulness bound; geometry
  (`theoretical/geometry.md`, new) is the headline, Theorem B the capstone.
  (2) **HGED-correlation → capstone:** the old "central empirical claim" (also the
  competitor head-to-head + Theorem B's validation) moves to the closing pillar;
  "faithfulness to structure" in the geometry pillar is carried by HGED-free
  signals (planted-family ARI/NMI, application metrics). (3) **Light scope
  re-aim:** doc framing only; milestone scope dirs and task IDs unchanged.
  (4) **Sibling unpublished:** the paper is self-contained and re-establishes
  IsalGraph's completeness/metric/correlation results for hypergraphs as its own
  (non-trivially for completeness — the tie-complete encoder was required).
  *Executed 2026-07-17:* `PROPOSAL.md` (§0 premise + spine),
  `theoretical/{geometry.md (new), README.md, stability.md}`,
  `empirical/{README.md, correlation.md, applications.md}`, repo `CLAUDE.md`
  thesis + context map; T-TBd closed. **Residual pending PI:** Ezequiel's
  confirmation of the demotion of Theorem B from headline to capstone.
  **Superseded by D-ART2 (2026-07-18), which goes further** — the pending-PI
  item folds into D-ART2's ratification.
- **D-ART2** — **[author-adopted 2026-07-18 17:56 CEST (Mario); PI-RATIFIED
  2026-07-18 18:23 CEST — points (a)–(e) approved as packaged, recorded from
  Mario's confirmation; docs pushed at `5e6b73e`]** The v3 rescope: **retire
  HGED-faithfulness as a pillar; the article is characterize → exploit.**
  *Diagnosis:* D-ART1 demoted Theorem B from headline to "capstone" but kept
  the whole HGED-validation layer (correlation study E1 with competitor rows +
  MI, density sweep E2 testing the `C(k,Δ)` Δ-prediction, HGED head-to-head as
  the competitor axis). That still framed `d_I` as an HGED proxy — a claim the
  stability analysis cannot support (B-cond conditional on five hypotheses,
  two failing generically) and that the author explicitly does not want the
  paper judged on.
  *Decision (the package):*
  1. **Thesis = characterize → exploit.** Measure the geometry of
     `(w*_c, d_Lev)` (six invariants: `ν` + Gram spectrum, `D̂` via CV-MDS,
     distortion, concentration + hubness, local sensitivity `s(e)`, ladder
     response — **no** δ-hyperbolicity), each bound to a consumer
     (**no-orphan-geometry rule**); then demonstrate usefulness on four
     applications (MDS; k-medoids + dendrogram; kNN; shortest path) scored on
     task metrics vs competitors. Narrative: foundation → compactness →
     geometry → usefulness → discussion.
  2. **HGED = closing discussion only:** length lemma + unconditional envelope
     `d_I ≤ m(1+kn)·HGED` as numbered propositions; no-bi-Lipschitz
     impossibility in prose (FSW-GNN/Chen et al. + our drift/avalanche
     mechanisms; the completeness–stability frontier); **one** exact-HGED
     correlation figure (E1', ours only, Spearman ρ, small connected
     mini-corpus). Retired: the density sweep E2, the competitor HGED
     head-to-head, and **MI** (existed for that head-to-head; PI had requested
     it — explicit ratification point).
  3. **E2b/E3 recast HGED-free** as geometry measurements (G2: sensitivity +
     ladder profiles; they never called the oracle), including the **measured
     nauty contrast** (its `s(e)` is avalanche-everywhere).
  4. **Applications:** four; medoid = PAM `k=1` inline; A4 scored HGED-free
     (ladder endpoints with known Qin budget; path recovery + monotonicity +
     decoded S2H intermediates).
  5. **Competitors:** WL, NetLSD (**promoted** from optional to full member),
     HyperCOT (scale-limited, stated), HPD, nauty contrast. Axes: task
     metrics, per-representation geometry (`D̂`, `ν`), capability matrix.
  6. **Bits subsection kept** (fixed-width estimator, Wilcoxon) in the main
     text near the representation intro; T-M4a (entropy-coded) optional.
  7. **Formal theory in the paper:** Theorem A + Corollary A in full; the two
     propositions of item 2; geometry theory cited (Schoenberg, Bourgain,
     Khot–Naor), not restated.
  8. **Parked pending this ratification:** T-TBc (displacement transcoding —
     its measurement vehicle, the v2-scale correlation corpus, no longer
     exists; moved to BLOCKED) and the density-sweep/Δ-prediction validation
     (follow-up material, recorded in `theoretical/stability.md` §4). T-TBe
     stays open as non-article stretch theory.
  *Executed 2026-07-18:* `PROPOSAL.md` (full v3 rewrite),
  `theoretical/{README,geometry,stability,stability_reformulations}.md`,
  `empirical/{README,applications,correlation}.md`, `COMPETITORS.md`,
  `DATA.md`, `RELATED_WORK.md`, `CODE_DESIGN.md`, `H2S_S2H.md` (intro),
  repo `CLAUDE.md` (thesis + context map); ledger updates per
  `DEVELOPMENT/README.md`.
  **Ratification points (all approved 2026-07-18):** (a) retiring the HGED
  head-to-head + density sweep; (b) dropping MI (PI-requested statistic);
  (c) the one-figure-only HGED footprint; (d) parking T-TBc (PI's own
  displacement idea — kept filed, not deleted; now parked for follow-up work
  unless the PI reopens it); (e) NetLSD promotion. **The only PI input still
  outstanding is T-M0c** (rename the cyclic-13 fixtures vs promote them to
  true STS(13)s) — a separate decision, never part of this package.
  *[Resolved 2026-07-18: PI chose (b) promote, extended to the full
  Kaski–Östergård catalog (orders 3–15); executed same day — see
  `T-M0/CLOSED/T-M0c.md`.]*
