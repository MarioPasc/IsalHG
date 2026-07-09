# T-TA — Completeness (Theorem A) for IsalHG
**Declared:** 2026-07-08 12:20 CEST
**Status:** BLOCKED — deliverables complete (proof + counterexamples + fix +
tests, all green); waits on PI review of the proof only (D-TA1 resolved
2026-07-09 → executed at T-TAd)
**Depends on:** —
**Context to read first:**
- `docs/article/theoretical/stability.md` §1 — statement + status
- `CLAUDE.md` §"Mathematical Foundation (brief)" — the conjecture
- IsalGraph paper `methodology.tex` (Theorem 1) — the proved graph analogue to port
- `.claude/rules/coding_rules.md` — always (for any test artefacts)
**Description:** Prove `w*(H1)=w*(H2) ⇔ H1≅H2` for IsalHG, or produce an airtight
empirical completeness section. Prerequisite for the metric property (Cor. A).
**Acceptance:** a written proof reviewed by the PI, or a completeness experiment
over a large sampled + design-fixture corpus with zero counterexamples.
**Out of scope here:** the stability bound (T-TB).
**Closing (2026-07-08 23:39 CEST):**
- *Premise correction (load-bearing):* **the conjecture as stated is FALSE for
  the implemented greedy variants.** The IsalGraph Theorem 1 proof does not
  port as-is — the sibling's canonical searches branch over every tied
  candidate at V-steps, whereas IsalHG's `_encode_from` commits to the
  **min-edge-id** member of the residual tie set (V candidates tying through
  the full cascade `(i, j, edge_label, new_labels, η)`). `w*` is therefore a
  function of the *presentation* (edge insertion order), not of the abstract
  hypergraph. Machine-verified minimal counterexample: n=4, m=4,
  `E={{1,3},{0,1,3},{0,2,3},{1,2}}` (primal graph K4 ⇒ η constant); two edge
  orderings give two different 7-token `w*` under both `greedy_min_nbrdeg` and
  `greedy_min`, Python ≡ C++. Failure is common, not adversarial: 5/16 random
  hypergraphs (n∈[5,12]) changed `w*` under an edge reshuffle alone. **Why
  every existing test passed:** `permute` preserves edge insertion order, so
  the property suite only ever sampled order-preserving isomorphisms (for
  which greedy IS equivariant — proved); the design fixtures live in the
  automorphism-coherent-tie regime (Fano: `w*_greedy = w*_complete`, verified).
- *Second gap:* the string never records the **seed vertex's label** ⇒ on
  non-trivial vertex vocabularies the bare `w*` is incomplete
  (labels-`[0,0]` vs `[1,0]` 2-vertex pair share `w*`;
  `IsalHGBackend.are_isomorphic` returns a **false positive** — handoff
  T-TAb). Theorem A is stated over the augmented fingerprint
  `F(H) = (ℓ_max(H), w*(H))`; trivial vocabulary (all current corpora):
  `F ≡ w*`.
- *Fix (additive, default untouched):* `tie_branch=True` mode in
  `core/hypergraph_to_string.py` (`_iter_v_candidates` factored out;
  `_tied_v_candidates`; `_encode_from` branches over the full tie set ×
  label-respecting orderings, lex-min completion) + new registered variant
  **`greedy_min_complete`** (`core/algorithms/greedy_min_complete.py`,
  nbrdeg seed set, pure-Python). Default path byte-identical (Python ≡
  unchanged C++ on 40/40; suite green).
- *Theorem A (proved, PI review pending):* (⇒) unconditional for every
  variant via round-trip soundness; (⇐) for `greedy_min_complete` via
  seed-set equivariance + step equivariance + execution-forest bijection.
  Corollary A: `d_I = d_Lev(w*_c, w*_c)` is a **metric on iso classes**.
  Extras: exact characterization of when greedy = complete
  (automorphism-coherent ties), admissible-pruning lemma (any iso-invariant
  tie-set refinement preserves the theorem — the C++-port lever). **Proof:**
  `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/theorem_a_completeness.{tex,pdf}`
  (10 pp., compiles clean; empirical scripts + counterexample JSONs archived
  in `proofs/empirical/`).
- *Empirical completeness arm:* 150/150 random instances invariant under
  vertex-relabel + edge-reshuffle for `w*_c`; biconditional
  (`w*_c` equal ⇔ pynauty iso) exact on Hypothesis-sampled pairs; pinned
  counterexample regression tests (greedy differs / complete agrees). New
  tests: `tests/unit/core/test_greedy_min_complete.py` (7),
  `tests/property/test_completeness.py` (2).
- *Closing checks:* `pytest tests/unit tests/property tests/integration -m
  "not slow" --hypothesis-seed=0` → **563 passed, 8 skipped, 3 deselected, 0
  failed** (+7 vs T-M2a's 556). Property suite 54 passed. ruff **3 ==
  baseline**; mypy **21 == baseline**. No C++ change → no rebuild.
- *Docs:* `stability.md` §1 + §6 checklist, `CLAUDE.md` §Mathematical
  Foundation, `canonical.py` / `exhaustive.py` / `hypergraph_to_string.py`
  docstrings all updated to the resolved status.
- *Handoffs spawned:* T-TAa (C++ `tie_branch` port + perf), T-TAb
  (seed-label fingerprint augmentation), T-TAc (WL-pruned variants use
  inadmissible id-dependent pruning). Decision for PI: **D-TA1** below.
