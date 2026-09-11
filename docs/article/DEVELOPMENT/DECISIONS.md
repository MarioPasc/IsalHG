# Decisions pending PI (mirror `CODE_DESIGN.md` §11)

- **D-ART3** — **[PENDING PI — revised to v5, 2026-08-12]** Rescope the article
  from "characterize → exploit" to **"enumerate, deduplicate, decode,
  navigate"**. *History:* raised by the PI 2026-08-09 after the T-M4b close
  ("maybe we need to re-think the paper as a more theoretical paper") and
  drafted the same day as v4 (theory-forward: characterize → explain →
  instrument). **Revised 2026-08-12 on four PI inputs:** (i) venue changes to
  **IEEE TKDE** (ISSN 1041-4347), not *Information Sciences*; (ii) a new
  flagship problem — exhaustive search for the **smallest countermodel** of a
  first-order formula, using the fact that every finite model *is* a labelled
  hypergraph and that our advantage shows under exhaustive rather than random
  search (the IsalSR precedent); (iii) applications must be ones where IsalHG is
  *indispensable* rather than competitive — explicitly "enumerar los vecinos" and
  "el camino más corto", with the shortest-path work **kept and promoted**, not
  abandoned; (iv) real corpora from the ARB/Benson collection replace the failed
  HIC anchor, derived by Qin et al.'s own ICDE-2023 ego-network definition
  (already implemented in-repo). *Scope:* nine files in
  [`../D_ART3/`](../D_ART3/) (hub: `README.md`), mirroring the article's own
  documents. *Decision record and v4 history:*
  [`RESCOPE_D-ART3_DRAFT.md`](RESCOPE_D-ART3_DRAFT.md). *Carried from v4
  unchanged:* the encoding-format constraint (the measured culprit is the
  instruction format, not completeness — nauty is complete too and localizes the
  same edits), P1 (ambient decodability, low risk) and P2 (drift/avalanche
  lower bound, moderate risk, time-boxed with a pre-agreed fallback).
  **Revised the same day to v5.1 on two author corrections.** (α) *The alphabet
  is not fixed.* D-TA2 froze which tie-complete lex-min is canonical **for
  `Σ_HG`**, not that `Σ_HG` is the only alphabet; a purpose-built `Σ_FO` is a
  first-class option and the geometry harness (representation-agnostic) can be
  re-run on it. Recommended: a native `FACT` token as a **conservative
  extension** degenerating to `Σ_HG` on the unlabelled fragment, which keeps
  every frozen result true of the fragment, extends Theorem A rather than
  restarting it (the proof is alphabet-parametric), and turns the change into a
  measurement of whether a semantics-aligned token reduces the ≈30–50 %
  single-edit response. (β) *Deduplication is not a claim* — Levi-`{nauty,
  bliss, Traces}` deduplicate faster with identical exactness, so isomorph-free
  enumeration is demoted to a correctness precondition with nauty named as a
  faster pluggable key. The operative framing becomes **"a certificate is not a
  space"**: applications are C1 (search-space framework), C2 (minimal
  countermodels + the geometry of model space), C3 (navigation, promoted),
  C4 (black-box structural optimization) and C5 (real data; the
  completeness-price measurement is reported as a *tie* with nauty). *Obligations
  at v5.1:* **P6** (move-operator closure, ball enumerability, reachability —
  now the load-bearing one) with P1 and P3 beneath it; P4 demoted off the
  critical path; P5 (HGED envelope as a candidate certified filter — expected
  too weak, measured before any claim). *New geometry invariant:* ball growth
  and its collapse onto isomorphism classes — the search's branching factor.
  **Six PI decisions are open** (`../D_ART3/README.md` §5): flagship vs second
  pillar; one paper or two; **D3′ the alphabet** (reduction into `Σ_HG` vs a
  purpose-built `Σ_FO` — now the largest technical decision); the P2 time-box;
  retiring the HIC exhibit; the A2/A3 disposition. **Gates blocking scope
  commitment:** G-L1 (`w*_c` cost on encoded structures), G-D1 (ARB arity/size
  feasibility), G-B1 (ball growth / branching factor), G-B2 (frontier ceiling).
  *Data:* the full ARB/Benson collection is being downloaded to
  `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/data/arb_benson/`
  (author-directed 2026-08-12). Recommendation: adopt v5.1. Until ratified, the
  v3 scope (D-ART2) stays active and no scope doc changes.

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

- **D-ART4** — **[PI-RULED 2026-09-06; author decisions (1)–(3) recorded the
  same day, assessed below]** *The paper's representation is the instruction
  string of the Isal family.* This reverses the encoding half of D-ART3 v7 /
  `../D_ART3/START_HERE.md` §6.0 (the fact-rank word adopted on 2026-09-04 under
  a fact-list reading of "F4"). Background and the PI's three questions answered
  with measurements: `../D_ART3/experiments/PI_QA_2026-09-06_isal_string.md`;
  the worked example of the three encodings on one record:
  `../D_ART3/experiments/ENCODINGS_WORKED_EXAMPLE.md`; the campaign audit:
  `../D_ART3/experiments/RESULTS_AUDIT_2026-09-06.md`.

  **(1) Remove the fact-rank word from the paper** — *author decision, ACCEPTED
  with one refinement.* The fact-rank word is retired as a representation, and
  with it the addressing arms (`fact_degree_key`, `fact_local_key`,
  `fact_local_colour`, `fact_rank_roles`), the addressing-frontier result and
  Prop 13 (all fact-alphabet results), and the two RQ1 gate amendments (moot).
  Nothing on disk is deleted (`results/IEEETKDE/` keeps every row as the
  record); the rows simply do not appear in the article. *Refinement:* the
  certificate baseline must be kept in **two standard tokenisations** — the
  raw certificate bytes (`nauty_cert`) and the canonical adjacency rows
  (`nauty_cert_rows`, already implemented and run in RQ2/5/7) — because the
  bytes-only comparison is a tokenisation confound (audit §1.2 item 2). A
  canonical adjacency list under a canonical labelling is nauty's own
  canonical form written row-wise, i.e. a standard object, not something we
  made up; it is the honest per-token comparator for locality and cost.
  *Consequence to own in the prose:* against that comparator the Isal string
  is less local and slower; the paper's advantages are the language
  operations (decoded consensus, generation, decodable interiors — RQ3, RQ6)
  and its own completeness theorem. The paper is written as "a language vs a
  certificate".

  **(2) Restrictions of the Isal methodology on knowledge bases** — recorded
  for iteration (numbers in the PI Q&A):
  - **R1 locality.** `w*_c` = lex-min over walks ⇒ an edit that moves the seed
    or a tie rewrites the walk: normalised single-edit response 0.49–0.79 vs
    0.08–0.25 (certificate bytes); within two tokens 0.03–0.86.
  - **R2 cost on symmetric inputs.** C++ engine, 60 s: censored 5.7 % (WD50K)
    / 12.3 % (NDC classes); censoring tracks `|Aut(Levi)|` (0.00 at ≤ 10,
    0.41–0.48 at 10³–10⁶, 1.00 at ≥ 10⁸) more than `m` (at 9–12 facts:
    symmetric 0.53 vs asymmetric 0.02). Real KBs are symmetric by nature.
  - **R3 domain.** Connected only; isolated constants not representable
    (RQ3's deletion variants and RQ6's interiors must respect this).
  - **R4 roles / argument order** not carried (facts are sets); shared with
    every set-based encoding; future work.
  - **R5 alphabet scoping.** One `k` per collection; fingerprint
    `(seed label, w*_c)` on labelled inputs.
  - **R6 identity speed** vs canonical-labelling engines: conceded.

  **(2a) "A canonical string over something other than the lex-min over
  walks"** — *assessed: yes, and it is the lever that addresses R1 and R2
  together.* Theorem A's proof is parametric in the iso-invariant rule that
  fixes the string; nothing forces the lex-min over all walks. Options, in
  order of promise:
  - *(i) Canonical-order walk.* Obtain an iso-invariant total order of the
    constants by individualisation–refinement (the canonical-labelling
    paradigm; Isal-native if implemented, borrowed from nauty otherwise) and
    emit the program deterministically along it: constants enter through `V`
    in order, facts in order through `V`/`C`, pointers moved with `P`/`N`.
    Completeness immediate. Locality = the order's stability under edits,
    measured for nauty's order at 0.68–0.85 of edits leaving it intact, with
    a few-token response otherwise. Symmetry handled by the same machinery
    (orbit pruning is native to individualisation–refinement). **Hypothesis
    unique to Isal, to be measured:** pointer moves are *relative* addresses,
    so inserting a constant should cost O(1) tokens where absolute
    addressing (ranks / adjacency rows) renumbers everything after it — a
    potential locality advantage over every rank-based serialisation.
  - *(ii) Lex-min over a restricted walk family* (e.g. a BFS/DFS from the
    refinement root with children ordered by refinement colour — the gSpan
    DFS-code family): still a lex-min, but over a tree-shaped family whose
    minimum moves less under edits.
  - *(iii) Status quo* (`w*_c`): locality bounded by the avalanche; only
    typical-case gains from pruning.
  Theoretical ceiling for all three: every complete invariant is
  discontinuous near symmetric inputs (the frontier prose survives); the
  target is typical-case locality.

  **(2b) The sibling engines' pruning** — *checked in the sources; would not
  help the symmetric tail.* IsalGraph `pruned_canonical_string`
  (`core/native/src/canonical.cpp`): structural-triplet candidate filter +
  branch-and-bound on string length. IsalSR (`core/native/src/canonical.cpp`,
  `wl.cpp`): candidate key `(label, WL hash)`, all tied candidates explored,
  lex-min. Both are *invariant-based*: they discard candidates an invariant
  distinguishes and explore every candidate it cannot. Automorphic nodes share
  every invariant, so on symmetric records the filter is a no-op (the IsalHG
  `greedy_min_wl_pruned` docstring states the same for vertex-transitive
  designs), and the IsalHG C++ engine already carries this class (neighbour-
  degree seed cascade, structural tuples, cost-class enumeration + bound,
  Rounds 9–11 of `docs/engineering/CPP_OPTIMIZATION_LOG.md`). What R2 needs is
  **stabiliser-orbit pruning** — one branch per orbit of the automorphism
  group fixing the placed prefix — which is value-preserving (Prop 6.0 of the
  completeness proof) and unimplemented in all three engines. Practical route:
  an automorphism oracle at tie points (`pynauty.autgrp` on the Levi graph
  with the placed constants individualised), giving bit-identical `w*_c` with
  polynomial oracle calls in place of exponential branching; nauty then
  appears as a *pruning subroutine*, not as the canonical form — the PI must
  accept that, or orbit detection is implemented natively (research). Option
  (2a)(i) sidesteps R2 entirely.

  **(3) Re-think the RQs** — *assessed: re-aim, do not restart.* The seven
  questions are about knowledge-base collections and are encoder-agnostic
  (`DESIGN.md` §0); that is the campaign's asset. Changes:
  - **RQ0 (new, thesis).** Why a language rather than a certificate: the
    capability matrix (decode any string, edit, prefix, interior, generate,
    consensus as a decoded object) filled by theorem or counterexample for
    every arm. Makes the paper's fight explicit.
  - **RQ1 → canonical-string design within the Isal language.** Arms:
    `w*_c` (60 s; 600 s on the censored tail), the canonical-order walk
    (2a-i) in its Isal-native and borrowed-order forms, `nauty_cert`,
    `nauty_cert_rows`. Axes: exactness, single-edit response (absolute
    tokens first), zero-shift fraction, the relative-vs-absolute addressing
    hypothesis under constant-set changes, cost and censoring by `|Aut|`.
  - **RQ2** unchanged; the Isal arm brings its own theorem.
  - **RQ3** unchanged (the consensus is fact-level; candidate key = the Isal
    string; interiors connected by construction — stronger). The deletion
    boundary's mechanism must be corrected regardless (audit §3.3). Variant
    generator: reject stranding deletions (R3).
  - **RQ4** keep the iso-twin exactness consequence; the standard-corruption
    AUC is pre-stated as characterisation (the certificate already behaves
    like every canonical-string metric there: expected negative).
  - **RQ5** licences (`ν`, hubness) + one exhibit; no task claim (expected
    negative for every arm).
  - **RQ6** unchanged and stronger: validity *and connectivity* by
    construction under `S2H`.
  - **RQ7** the envelope gains the symmetry axis: cells over
    `(m, k, |Aut|)`, since `|Aut|` is the measured frontier, not `m`.
  Corpus policy: connected-only; censored members dropped and reported per
  bucket, or the source window restricted — decided from the RQ1 table.

  **Also noted.** (a) The retired fact-rank rows remain evidence: the RQ4/RQ5
  negatives hold for `nauty_cert` too and will hold for any canonical-string
  metric. (b) Before launching RQ3 under the Isal arm, pilot one NDC cell: the
  consensus canonicalises hundreds of candidates per collection and NDC
  sources are symmetric (R2). (c) Documents to reverse: `START_HERE.md`
  §0/§0.1/§6.0, `prose.md` §2.1–2.3, `DESIGN.md` G1; the `fact_rank` arm stays
  registered in code as a baseline, not as ours. (d) Order of work: RQ1 first,
  the primary representation chosen from its table, then the encoder swap
  for RQ2–RQ7.

  **Addendum 2026-09-06 (author) — nauty inside the Isal methodology is
  accepted, and framed.** The author's ruling: *"We can integrate nauty inside
  the Isal methodology without a problem … when comparing to the nauty
  certificate, we are comparing something like 'nauty+Isal' vs 'nauty', which
  is really defensible and perfectly scoped, but always under the knowledge
  databases preface and measuring things that have an impact."* Consequences: (i) the PI's supersession of D-TA2 is required only if
  the canonical *value* changes (`lem:pruning` of the completeness proof:
  invariant tie refinement is complete but yields a different string;
  stabiliser-orbit pruning is value-preserving); (ii) nauty's role must be
  stated in one sentence in the paper, whichever variant wins. An agent is
  spawned to design and measure the variants; its binding brief is
  [`../D_ART3/experiments/ISAL_REFINEMENT_BRIEF.md`](../D_ART3/experiments/ISAL_REFINEMENT_BRIEF.md)
  (reading list, fixed facts, theory constraints, the A–D design space with
  hypotheses, code map, pitfalls, deliverables).

- **D-ART5** — **[RECORDED 2026-09-09 under D-TA2 and D-ART4 — not a new
  ruling; one item flagged for the author's objection]** The knowledge-base
  article's canonical program is the family's frozen `w*_c`, **computed by the
  stabiliser-orbit-pruned C++ engine**. Published budget: **60 s**. The
  ordered walk `w°` is the order-only cell of the RQ1 ablation and the
  deterministic cost floor of RQ7; the rank-keyed walk `w*_ρ` is the "both"
  cell of RQ1 only.

  *Why this is a record and not a decision.* Three questions were put to the
  author as open. On review of the record all three were already answered, and
  putting them up as open was an error of the orchestrator's, corrected here.

  1. **The representation is D-TA2 executed as written.** D-TA2 froze the
     *unpruned* tie-complete lex-min and named exactly one sanctioned
     optimisation: "the only sanctioned future speedup is **stabiliser-orbit
     pruning** (value-preserving by Proposition 6.0), never `ρ`-refinement".
     The D-ART4 addendum (author, 2026-09-06) closes it: "the PI's supersession
     of D-TA2 is **required only if the canonical *value* changes** …
     stabiliser-orbit pruning is value-preserving". Design §8(1)/A3 says the
     same. The value is unchanged, measured rather than assumed: identical
     words on **7,013/7,013** members, identical single-edit distances on
     **130,788/130,788** M1 units, identical ladder distances on **5,174/5,174**
     M2 pairs with ρ equal to four decimals. So §8(1) is **not triggered**;
     adopting the orbit engine *confirms* D-TA2. What *would* be PI-level is a
     departure from it — `w*_ρ` is a different canonical value (65 % word
     agreement) with no theorem in the proof file, and `w°` is a second
     canonical form; neither is adopted. The pre-registration's naming of `w°`
     as "the representation candidate" was an orchestrator decision (recorded
     as such in the wave summary, "Design decisions taken by the orchestrator
     (not the user)"), so departing from it is a §9 deviation, already
     recorded, not a supersession.
  2. **The budget is the pre-registration.** `pointer_budget_s: 60.0` in all
     three RQ1 configs; design §3 defines `wstar_600` as "the same on the 60 s
     -censored tail at 600 s" — a re-run *of the censored tail*, i.e.
     characterisation by definition, never a row. Merging it would choose a
     budget after seeing the numbers, force M1–M4 to be recomputed for every
     arm, and make a published row a property of a budget rather than of the
     representation. Nothing on record points the other way. The 600 s re-run
     of the 77 orbit-censored members folds into the RQ7 envelope sweep.
  3. **The fact arms were already conceded, in the main text.** D-ART4 (1)
     retires the fact word *as a representation* — "the rows simply do not
     appear in the article" — and in the same breath instructs the prose to own
     the consequence: "*Consequence to own in the prose:* against that
     comparator the Isal string is less local and slower." `prose.md` §2.3,
     written after that ruling, already says "Where the certificate's or the
     fact list's locality is better, the article does not claim otherwise."
     The apparent tension between "leaves the paper" and "remains evidence" is
     only apparent: the word is not ours, its rows are not in our tables, and
     naming it as the comparator that beats us on two axes is what the author's
     standing rule requires ("report failures with the same directness as
     successes"). **The one item for objection:** the sentence now carries
     numbers — the fact list is within two instructions on 57 % of interior
     insertions against the Isal word's 8 %, and `fact_local_key` is more
     monotone on all three series. The author may strike the quantification and
     keep the qualitative concession.

  *What the pre-registered rule decided.* Applied to the final data, the §3
  selection rule (which ranges only over the `ow_*` arms) selects
  `isal_ow_struct` — pooled within-≤2 of 0.0703 [0.0686, 0.0720], median 8,
  against 0.0700 (median 9) and 0.0694 (median 9); the three are not
  distinguishable at Holm-corrected 0.05 and the median breaks the tie. **Its
  escape clause fired**: no `ow_*` arm beats `nauty_cert_rows` (0.1787), so, in
  the rule's own words, "the paper argues from the language alone (D-ART4 (1)
  already anticipates it) and the number is printed."

  *The nauty sentence* (design §8(2), addendum (ii) "one sentence whichever
  variant wins"): under D-ART5 the **oracle** sentence of design §7 is the
  methods sentence — nauty supplies the automorphism group of the placed
  prefix, the family's search explores one branch per orbit, and the string
  returned is the frozen `w*_c`; the value does not depend on nauty, only the
  time does. The **order** sentence is used once, in the RQ1 ablation.

  *Restrictions after the decision.* R1 regime-specific and per corpus (see
  T-KBe); R2 **lifted for symmetry** — orbit pruning takes censoring at
  |Aut| ≥ 10⁷ from 36 to 0 and on WD50K from 237 to 7 — and **not lifted for
  arity**, the residual 77 being 69 arity-10 members at |Aut| < 10³, which is
  the RQ7 envelope's `(m, k)` axis; R3 proved (Prop. C.4); R4 filed (T-KBa);
  R5 kept; R6 conceded for the search, with `w°` the machine's sub-millisecond
  member.

---

## D-KBg1 (pending) — does `supplementary_data.md` get corrected to the built corpora?

**Raised:** 2026-09-11 04:43 CEST, by `[IsalHG-Fable]` via the corpus figure screen.
**Rule 10 check:** grepped `DECISIONS.md` for `supplement` — **no existing
ruling**, so it survives and is put to the author rather than settled in the
ledger.

**The situation.** `supplementary_data.md` §S1–S4 publishes the corpus census
as it stood **before** the freeze. The built corpora differ on 16 audited
quantities, the largest being `ndc_substances` **2,222 → 1,745** and
`ndc_classes` **1,432 → 1,381**. `prose.md` §7 references the supplement as
documenting the corpora in full, and now says 1,381 and 3,162 itself — so as
things stand **the paper would ship a supplement contradicting its own data
section**.

**One premise, checked and false.** The concern was raised that correcting the
supplement would make the freeze audit vacuous — `expected` becoming
`obtained`, every row matching, the record of what changed lost.
**It would not.** `scripts/tkde/freeze_corpora.py` holds `EXPECTED` as a
**hardcoded literal dict** ("the census of supplementary_data.md S1–S4, as
published"); it does not read the document at runtime. The reconciliation is
also pinned in every `census.json`'s `audit.rows`. So the audit record survives
correction in **two** independent places, and there is no trade-off between
fixing the supplement and keeping the history.

**What is actually being decided**, therefore, is narrower and is editorial:

1. **Correct the supplement** to the built corpora, keeping the reconciliation
   in `freeze_corpora.py` + `census.json` (and optionally a short "what changed
   at freeze" note in the supplement itself). The paper then describes what was
   run, everywhere.
2. **Leave it**, and add a sentence to the supplement and to `prose.md` §7
   saying it documents the *pre-freeze* corpora and naming where the built
   census lives.

**Recommendation: (1).** The supplement's job is to document the corpora the
experiments ran on; it currently documents corpora nothing ran on. Option 2
preserves an inconsistency the reader has to be warned about, in the document
whose purpose is to remove the need for warnings.

**Why it needs the author rather than the ledger:** it changes a published
artefact of the paper, and option 2 changes what `prose.md` §7 claims about it.

**Second finding, 2026-09-11 — it is not only the numbers, it is the framing.**
`supplementary_data.md` line 190 calls the fact-addressed word **"the adopted
encoding"**. That is pre-**D-ART4** language: the fact word left the article with
that ruling, and the paper's representation is the Isal instruction string. The
file mentions **D-ART4 zero times**.

So the decision is slightly larger than "correct the census or label it": under
option 1 the framing is corrected with the counts; under option 2 the label has
to cover **both** — that the supplement describes the pre-freeze corpora *and*
names a representation the article no longer adopts. A reader who takes
"the adopted encoding" at face value from a published supplement reaches the
opposite conclusion from §2.3.

*Not edited here, deliberately: this file's disposition is the decision, so
changing it would pre-empt the ruling. Recorded instead.* (The sweep that found
it was proposed by `[IsalHG-Fable]` on the basis that the test is not whether a
number is stale but whether the sentence assumes the fact word is the paper's
answer — the same sweep found `START_HERE.md`'s §0 and cleared `DESIGN.md` L47,
which correctly *defines* the `fact_rank` arm rather than adopting it.)

**Until it is ruled**, the screen excludes `supplementary_data.md` by default
(`--exclude`), so the gate is not held by a file whose staleness may be
deliberate — and that exclusion is **named in the output on every run** rather
than silent, so it cannot outlive the decision unnoticed.
