# T-M2b — HGED convention unification: Qin's taxonomy becomes the single official metric
**Declared:** 2026-07-08 23:18 CEST (PI directive, same session as T-M2a close)
**Status:** DONE
**Depends on:** T-M2a (DONE)
**Description:** PI directive superseding T-M2a's D1 (reference-only): make the
Qin et al. (ICDE 2023) empty-shell taxonomy the **only** HGED in
`metric_space/distances` and the official metric of the article; document every
deviation from Qin with a justification.
**Closing (2026-07-08 23:18 CEST):**
- *Re-assessment (requested by PI: "best-fit HGED for our use case").* Qin
  verbatim is best-fit, not merely citable: (1) **commensurability** — `|w*|`
  scales with incidence mass (Θ(arity) tokens per hyperedge) and Qin prices
  edits by incidence count (arity-`a` edge delete/insert = `a+1`), so the
  direct-term contribution to the single-edit sensitivity is O(1)/unit-HGED
  where a unit whole-edge op made it O(k) — Theorem B's constant sheds a `k`
  factor from the direct term (remark added to `stability.md` §2.2, flagged
  for verification at T-B2); (2) the whole-edge variant's sole rationale (the
  ladder guarantee) is fully recovered by Qin-cost budgets; (3) computability
  is preserved by decoupling metric from solver.
- *Code:* `hged.py` re-costed to Qin (edge delete/insert diagonals `1+|E|` in
  `_edge_cost`/`_partial_edge_lb`; also fixed a latent big-M bug in
  `_partial_edge_lb` whose `forbidden` ignored vertex counts and could
  under-estimate at terminal states for small-m/large-n pairs);
  `core/sparse_hypergraph.py` gained `qin_edit_cost(before, after)` and
  `edit_path` now returns the **accumulated Qin cost** as its budget;
  `perturbation_ladder` accumulates the same budget (`budget_from_base`
  cumulative, strictly increasing); `qin_hged.py` re-documented as the paper's
  algorithm for the same official metric. Whole-edge convention removed
  everywhere (grep-verified).
- *Deviation ledger (PI requirement):* authoritative copy in
  `docs/article/empirical/correlation.md` §HGED — metric level **none**
  (Def. 3 verbatim); model level M1 simple-hypergraph dedup (consistent with
  Qin §III; MO 5,446→5,445 counted), M2 correspondence-based costing (no
  empty-shell intermediates materialized; Qin's own Alg-2 formulation),
  M3 composite MO tag-set labels; algorithm level A1 LSAP B&B oracle instead
  of HGED-BFS (measured: Def-5 node bound ≡ 0 unlabelled ⇒ 15/15 DNF from
  n=10), A2 Lemma-4.1 orientation (Qin's own), A3 no-cross pruning (proved
  never-dearer), A4 root-evaluated Def-5+6 bound (the 10²–10⁴× Table II
  factor), A5 value-neutral BFS engineering/ReRank tie-breaks; protocol level
  P1 Qin-cost ladder budgets, P2 dual pair-sampling in the Table II
  reproduction. Mirrored in `/media/.../HGED/docs/T-M2a_fidelity_report.md` §4.
- *Verification:* cross-solver **equality** property (`ExactHGED ≡ QinHGED`,
  Hypothesis) + BFS ≡ exhaustive-DFS + Example 2 == 6 on both solvers;
  Qin-value hand fixtures updated (edge delete = k+1 = 4, composite path = 4);
  ladder tests assert cumulative budget ≥ step and `Exact ≤ budget`. Suite:
  **555 passed, 8 skipped, 2 deselected, 0 failed** (−1 vs T-M2a: two property
  tests merged into the stronger equality test). ruff **3 == baseline**; mypy
  **21 == baseline**.
- *Note:* `scripts/bench_hged_ceiling.py` (T-M2 DQ1) numbers refer to the old
  cost model; the re-run gate probe (`gate_probe_seed0.json`, old file archived
  as `*_pre_unification_whole_edge.json`) supersedes them for feasibility.
