# T-TBb — Pointer-run amortization: close the layout-locality gap in Theorem B
**Declared:** 2026-07-09 19:16 CEST (orchestrator post-audit of T-TB)
**Status:** OPEN
**Depends on:** T-TB (Theorem B, conditional form — CLOSED); informs T-M5a instrumentation
**Why this task exists:** The T-TB audit found that Lemma B1's O(kΔ) locality is
conditional on two *layout* hypotheses that no combinatorial condition implies:
(iv) span-boundedness (`T_span(e) ≤ c₃kΔ`) and (v) run-locality
(`R(e) ≤ c₄kΔ`). Because `P_i`/`N_i` are unit steps, a vertex-count-changing
edit adds ±1 token to every later pointer run spanning the edited CDLL slot,
and a window re-encoding pays the CDLL distance to a changed member — up to
Θ(m) and Θ(n) respectively in adversarial layouts. This is the original
"CDLL-index hazard" of the T-TB task, vindicated: the shifted correspondence φ
resolves state identification but cannot bound run lengths. B-cond is proved
under (i)–(v); whether (iv)–(v) hold generically is the remaining theory.
**Context to read first:**
- `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/stability/theorem_b_stability.tex` — Definition (layout-locality), the vindication remark, the orchestrator post-audit note
- `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/stability/lemma_b1_restatement.tex` — key-crossing freedom (ii), the run-term decomposition in the lemma statement
- `docs/article/theoretical/stability.md` §2.2 (★, vindicated proof risk) and §6 (T-B1/T-B2/T-B4 status)
- `src/isalhg/core/hypergraph_to_string.py` + `core/instructions.py` — unit-step pointer semantics; whether κ's token order makes the lex-min prefer short runs
- `.claude/rules/coding_rules.md` — always
**Description:** Four deliverables. (1) **Amortized run bound or counterexample:**
prove that the κ-lex-min encoder keeps total pointer movement O(f(n,m,k)) with
per-edit spanning counts O(kΔ) generically — or construct the adversarial family
showing (iv)/(v) fail with non-vanishing probability, which demotes B-cond's
generic applicability and re-scopes the paper's claim to B-avg. The mechanism to
exploit: pointer tokens participate in the lexicographic key, so cheaper-run
candidates win ties and near-ties; formalize as an amortization argument over
the encoding. (2) **Analytical T-B3:** derive the Fano/STS(9)-coherent vs
STS(13)/GQ(2,2)-incoherent classification from the Prop 6.0
stabiliser-transitivity criterion alone (no appeal to T-TAa string equality).
(3) **Rigorous B-avg:** upgrade the Thm 3 sketch — precise random model,
concentration for ξ-distinctness through the depth-3 recursion, plus the
(iv)–(v) w.h.p. statement from (1). (4) **W-token check:** verify
`hypergraph_to_string.py` emits no `W` tokens in `w*_c` (length-lemma proviso in
`theorem_b_stability.tex`); pin with a unit test if true, else re-derive the
length envelope.
**Acceptance:** (iv)–(v) proved generically (stated model, explicit constants)
or refuted by counterexample with the paper-claim consequence written into
`stability.md`; T-B3 recovery derived or its obstruction documented; B-avg
either proved or explicitly demoted to empirical-only; W-token proviso
discharged with a test or the envelope corrected. `stability.md` §2.2/§6 and
both proof `.tex` files updated consistently.
**Out of scope here:** running E2b/T-M5a (only its `R(e)`/`T_span(e)` logging
spec, already noted in `theorem_b_stability.tex` §Δ-dependence); any change to
the frozen `w*_c` (D-TA2).
