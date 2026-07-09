# Decisions pending PI (mirror `CODE_DESIGN.md` §11)

- **OD1** — Architecture: additive `metric_space/` now (recommended) vs also
  reparenting to `isomorphisms/` (T-M6, optional/last).
- **OD2** — `levi_reduction` home: `core/levi_reduction.py` (recommended) vs a
  new shared `reductions/` package.
- **OD3** — HyperCOT: dedicated pinned conda env via subprocess (recommended).
- **OD4** — **[resolved 2026-07-08]** `ExactHGED` = our own A*/ILP over the six
  edit ops. The `networkx.graph_edit_distance`-on-Levi wrapper is rejected: GED
  on the bipartite Levi graph is not obviously equal to HGED (vertex/edge nodes
  differ semantically; the cost-lift needs an unproven correctness argument).
- **OD5** — `metric_space/metrics/embedding.py`: keep the classical-MDS solve +
  stress as a `src` primitive (recommended) vs push all of MDS into experiments.
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
