# T-TB — Stability (Theorem B) incl. Lemma B1
**Declared:** 2026-07-08 12:20 CEST
**Status:** DONE
**Depends on:** T-TA (metric property), informed by T-M5a (empirical `s(e)` data)
**Context to read first:**
- `docs/article/theoretical/stability.md` §2–§4 — statement, reduction, avalanche, theory↔empirics
- `docs/article/RELATED_WORK.md` — TMD (proof template), co-OT (Levi-Lipschitz), FSW-GNN (one-sided justification)
- `src/isalhg/core/hypergraph_to_string.py::_encode_from`, `src/isalhg/core/cdll.py` — the CDLL-index hazard (Lemma B1)
- `.claude/rules/coding_rules.md` — always
**Description:** Prove `d_I(H,H') ≤ C(k,Δ)·HGED(H,H')`; resolve Lemma B1's
CDLL-index hazard (relative vs absolute order); if the worst-case bound is
unattainable, prove the average-case / high-probability form.
**Acceptance:** a written proof (or conditional/average-case theorem) whose
predicted `C(k,Δ)` Δ-dependence matches the T-M5a density-sweep data.
**Out of scope here:** implementing the experiments (T-M5a–e).

---
**Closing (2026-07-09):**

*Proof document:* `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/stability/theorem_b_stability.tex`
(alongside `lemma_b1_restatement.tex` from T-TBa; permanent, outside repo).

*What was proved:*
- **T-B0 (path normalization):** Lemma: for connected H, H' there exists an
  all-connected HGED edit path of the same Qin cost (insert-before-delete
  reordering; vertex insertions paired with first incidence; vertex deletions
  paired with last incidence removal). Degenerate case (disjoint vertex sets)
  handled separately by B-worst.
- **T-B1 (Lemma B1):** Full proof in relative CDLL order. The shifted
  correspondence φ maps absolute CDLL indices of H to those of H⊕e under
  vertex insertion (the only index-shifting edit) and is the identity otherwise.
  The branching search trees T(H,v_0) and T(H⊕e,v_0) are isomorphic outside
  the N_1[e] encoding window when all three tie-set-transparency conditions
  (i–iii) hold. C-steps treated separately (singleton tie set, no branching).
  Condition (iii) lifts the per-seed bound to the global w*_c via the argmin
  preservation assumption.
- **T-B2 (branching window):** Explicit constants: c_1 = 3 (direct encoding per
  op), c_2 ≤ 2k+1 (tokens per vertex in N_1[e]). Window = O(k^2 Δ).
  Qin-costing remark confirmed: direct term is O(1) in arity per unit HGED;
  k-dependence of C(k,Δ) comes from the window term.
- **T-B3 (avalanche characterization):** Analytical criterion from Prop 6.0
  (automorphism-coherent ties). Sources 3–4 suppressed when all reachable ties
  are coherent; sources 1–2 remain possible on any input. Fano/STS(9) coherent
  (sources 1–2 only); STS(13)/GQ(2,2) incoherent (all four sources). Recovered
  from the analytical criterion.
- **B-worst (Thm 1):** d_I(H,H') ≤ (2k+1)(m+1)·HGED(H,H') unconditionally.
- **B-cond (Thm 2):** d_I(H,H') ≤ C(k,Δ)·HGED(H,H'), C(k,Δ) ≤ (2k+1)(1+kΔ),
  for tie-set-transparent edit paths. This is the paper's primary claim.
- **B-avg (Thm 3):** Sketch with heuristic probability estimates for random
  sparse hypergraphs; flagged as non-proved, target only.
- **Δ-dependence prediction:** ρ(d_I, HGED) decreases with Δ; near-unimodal
  histograms on Fano/STS(9); heavy tail on STS(13)/GQ(2,2). Falsification
  criteria stated explicitly.

*Documented pending clause — T-B5:*
The acceptance criterion requires predicted C(k,Δ) Δ-dependence to match the
T-M5a density-sweep data. T-M5a has not run (2026-07-09). Predictions are
stated explicitly in §6 of theorem_b_stability.tex and §4 of stability.md.
This task closes DONE with the pending clause documented; T-B5 is recorded in
stability.md §6 as PENDING T-M5a. No separate BLOCKED task needed — the proof
is complete, the predictions are falsifiable, and T-M5a is already tracked.

*No code touched.* No Python changed; no tests to run.
*Checks:* pytest not run (proof-only task); ruff/mypy not run (no Python changed).
Baselines ruff 3 / mypy 21 assumed unchanged.

---
**Round-2 revision (2026-07-09) — orchestrator math audit, six defects fixed:**

The round-1 closing note above contained six mathematical errors corrected in a
single pass on `theorem_b_stability.tex` and `lemma_b1_restatement.tex`. What
changed per defect:

- **Defect 1 — T-B0 P3 gap.** The original proof argued about the optimal path
  π* directly, which is not the reordered path. Fix: added a three-sub-step
  structure — (P3a) per-edge reduce-before-extend (four cases: s≥2; s=1
  |M_H|<k; s=1 |M_H|=k; s=0 with delete+reinsert fallback for |M_H|=k adding
  ≤2 cost per edge); (P3b) global insert-before-delete; (P3c) BFS-outward
  connectivity for the insertion leg and leaf-first reverse-BFS for the deletion
  leg.

- **Defect 2 — T-B0 connectivity legs false.** "H∪H' contains H as a connected
  spanning subhypergraph" was false: new edges over only-new vertices create
  disconnected blobs. Fix: insertion leg reordered so each new edge has ≥1
  member already present (BFS-outward); deletion leg uses leaf-first reverse-BFS
  toward the H'-core. Premise holds for connected H∪H'; degenerate case
  (disjoint vertex sets) handled separately by B-worst.

- **Defect 3 — T-B1 inductive step wrong.** "η(f) unchanged since f∉N_1[e]"
  was incorrect — η uses ξ-tuples of members, and ξ changes for vertices in
  N_3[e]\N_1[e]. Fix: two-part argument. Part A (order): condition (ii) as
  V-candidate non-incidence ensures no V-candidate at any state has a member in
  N_r[e], so no η comparison (strict or tied) flips. Part B (content): tokens
  are determined by the selected edge and CDLL positions, not ξ values. Also
  removed the false "equivalently" clause from `lemma_b1_restatement.tex`
  condition (ii) (the tie-based rephrasing was an under-sufficient
  approximation; only the V-candidate non-incidence primary clause is correct).

- **Defect 4 — k-dependence double-count.** The per-vertex derivation charged
  (2k+1) tokens per vertex in N_1[e] (kΔ vertices), yielding O(k²Δ). The O(kΔ)
  headline was asserted but not derived. Fix: count per edge — at most Δ
  affected edge encodings, each ≤2k+1 tokens. Explicit bound: s(e) ≤
  (2k+1)(1+Δ) = O(kΔ). The round-1 note's "c_1=3, c_2≤2k+1, Window=O(k²Δ)"
  is superseded; stability.md §2.2 (★) updated accordingly.

- **Defect 5 — B-worst wrong constant.** "(2k+1)(m+1)·HGED" referenced
  intermediate-path edges (up to m+t). Fix: direct proof without the path —
  d_I ≤ max(|w*_c(H)|, |w*_c(H')|) ≤ (2k+1)max(m,m'). Theorem B-worst
  restated as d_I(H,H') ≤ (2k+1)max(m,m')·HGED(H,H'). The round-1 note's
  "(2k+1)(m+1)" is superseded.

- **Defect 6 — T-B3 over-claim.** Marked "ESTABLISHED analytically — Fano/STS(9)
  vs STS(13)/GQ(2,2) recovered from the analytical criterion." The analytical
  recovery (deriving the coherence classification from stabiliser-transitivity
  alone, without the T-TAa string-equality measurement) was not given; the
  classification was inferred empirically. Fix: §5 of `theorem_b_stability.tex`
  downgraded to "CRITERION STATED (T-TBa via Prop 6.0); analytical recovery of
  design classification PENDING." T-B3 checkbox in `stability.md §6` changed
  from [x] to [ ]. The round-1 note's "Recovered from the analytical criterion"
  is superseded. B-cond constant corrected: C(k,Δ) ≤ (2k+1)(1+Δ), not
  (2k+1)(1+kΔ).

---

## Orchestrator post-audit (2026-07-09 19:16 CEST, Fable — after the worker's two rounds)

The two-round iteration budget was spent; the orchestrator audited the round-2
artifacts and applied the remaining corrections directly (both proof `.tex`
files, `stability.md` §2.2/§3/§6). Both `.tex` files compile (`pdflatex`,
2026-07-09). Corrections of record:

- **Condition (ii) was unsatisfiable.** The round-2 "V-candidate non-incidence"
  form (no V-candidate at any reachable state has a member in `N_r[e]`) is met
  by no edit on any hypergraph — every edge, perturbed or not, must eventually
  become a candidate and be consumed — so Lemma B1 and B-cond were vacuously
  true. Replaced by **key-crossing freedom**: perturbed-vs-unperturbed
  comparisons resolve identically at every state; perturbed-vs-perturbed may
  permute freely (absorbed in the window).
- **Pointer-run terms were uncounted.** `P_i`/`N_i` are unit steps, so run
  lengths are slot counts: Part B's "relative order ⇒ same pointer tokens" was
  false. Made explicit: `T_span(e)` (±1 per post-window run spanning an
  inserted/removed slot; `v±` edits) and `R(e)` (window runs to changed member
  slots). Neither is bounded by (k,Δ) worst-case ⇒ new **layout-locality
  conditions (iv)–(v)**; Lemma B1, T-B2, and B-cond restated over (i)–(v).
  The task's original "CDLL-index hazard" is thereby vindicated, not resolved:
  worst-case unconditional O(kΔ) locality is false by explicit mechanism.
- **Constants re-derived.** (★) is now `s(e) ≤ (1+Δ) + R + T_span ≤ (1+Δ) +
  (c₃+c₄)kΔ` under (i)–(v); the round-2 `(2k+1)(1+Δ)` rested on the false
  "≤2k+1 tokens per edge" premise. B-worst restated with the honest length
  envelope `|w*_c| ≤ m(1+kn)` (W-emission proviso flagged).
- **Macro-steps added to the reduction.** `d_I` is undefined on the
  disconnected intermediate after a bare `v⁺`; the Corollary now groups paired
  vertex+incidence ops so every telescoping step is evaluated on connected
  states. T-B0's `k=2`, `s=1`, arity-`k` case folded into the delete-reinsert
  residual (cost `+2c₀`, zero under genericity).
- **T-B4 checkbox corrected** from [x] to [ ] (a sketch is not done).

Open theory consolidated in **T-TBb** (`OPEN/T-TBb.md`): generic (iv)–(v)
amortization, analytical T-B3, rigorous B-avg, W-token check. Disposition
unchanged: T-TB is DONE as a **conditional** theorem (the acceptance clause
explicitly admits one), with T-B5 pending T-M5a and the conditions honestly
stated.

---

## v3 rescope addendum (D-ART2, 2026-07-18) — T-B5 destination

The T-B5 pending clause above was written against the v2 scope ("validate
C(k,Δ) against the T-M5a density sweep"). Under v3 (D-ART2, PI-ratified
2026-07-18) the density sweep is retired. T-B5 is **rescoped**:

- The `s(e)` histograms — formerly T-B5's evidence base — are now the geometry
  pillar's **local sensitivity profile** (G2 in `empirical/applications.md`),
  tracked under **T-M5g**.
- Logging `R(e)` / `T_span(e)` per edit separates layout drift from avalanche
  and feeds the discussion's mechanism prose (PROPOSAL §5).
- Verifying the (★) constants against the G2 histogram shapes is
  **follow-up work**, no longer an article deliverable.

The acceptance criterion of T-TB is thereby satisfied under v3: the conditional
theorem is stated, the predictions are falsifiable via the G2 experiment (T-M5g),
and the v2 empirical gate (T-M5a density sweep) is replaced by the HGED-free
geometry evidence. No separate T-B5 task is created; T-M5g owns the
instrumented `s(e)` run.
