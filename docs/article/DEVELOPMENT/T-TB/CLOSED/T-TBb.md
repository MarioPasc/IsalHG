# T-TBb — Pointer-run amortization: close the layout-locality gap in Theorem B
**Declared:** 2026-07-09 19:16 CEST (orchestrator post-audit of T-TB)
**Status:** DONE (2026-07-14; closing note below)
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

---

## Closing note (2026-07-14 13:05 CEST, task-reader session)

**Proof document:**
`/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/stability/pointer_run_amortization.tex`
(+ compiled PDF; siblings `theorem_b_stability.tex`, `lemma_b1_restatement.tex`
amended and recompiled). Scripts: `scripts/probe_pointer_runs.py`,
`scripts/tb3_coherence_criterion.py`. Test: `tests/unit/core/test_no_w_tokens.py`.
Docs updated: `docs/article/theoretical/stability.md` §2.2/§3/§6,
`DEVELOPMENT/README.md`.

**(1) Amortized run bound / counterexample — REFUTED generically, with an exact
reduction.**
- *Crossing-averaging identity (rigorous):* every unit pointer step crosses the
  boundary after exactly one vertex, so `Σ_u X(u) = M(H)` (total pointer
  movement of `w*_c`), and for the uniform vertex-insertion ensemble under
  transparency, `T_span(e_u) = X_{>τ_u}(u)` gives **`E_u[T_span] ≤ M(H)/n`
  exactly**. Average (iv) ⟺ amortized movement `O(kΔ)` per vertex.
- *(v) refuted (worst case and on natural ensembles):* the
  **orphaned-introducer** mechanism — an incidence edit re-homes a vertex's
  introduction point; the orphaned introducer pays the CDLL distance between
  the old and new sites — yields bounded-degree (`Δ ≤ 5`), tie-free rigid-tree
  families with `R(e) = Θ(n)` at Qin cost 1 under (i)–(iii).
- *Probe (pinned seed 20260714, k=3, arities {2,3}, C++ tie-complete, budget
  5·10⁴):* `M/n` grows ≈ `n^0.75` at fixed density (density 2.0: 2.75 → 3.94 →
  5.17 → 6.38 → 7.69 for n = 12,16,24,32,48) while `kΔ` grows only
  logarithmically — **average (iv) fails asymptotically**; `max_u X(u)` stays
  ≈ `Δ` (within +3 in every cell), so the worst-case crossing peak is benign on
  random inputs and its order is left as a stated conjecture
  (`O(k(Δ + log m))`, RSL-doubling rationale; naive shuttle counterexamples
  provably fail against the min-displacement + insert-after-p₁ mechanisms).
- *Consequence written into `stability.md` §2.2/§3:* B-cond stands as the
  conditional theorem; the generic claim is re-scoped to the drift
  decomposition `E[s(e)] ≤ (1+Δ) + E[R + T_span] + P[tie exposure]·O(mk)`.

**(2) Analytical T-B3 — resolved with the obstruction documented.**
- Depth-2 classification proved by hand from Prop 6.0's criterion: Fano
  (pointwise line stabilizer = order-4 elation group, transitive), STS(9)
  (order-3 axis-shear group, transitive), GQ(2,2) (order-8 group, `(56)` swaps
  the remaining lines), cyclic-13 (**trivial** pointwise block stabilizer +
  2-element tie ⇒ incoherent — pure group theory, no computation).
- Exact **orbit-pruned full-tree audit** (`tb3_coherence_criterion.py`, no
  truncation; states 11/71/633/561): Fano — **no incoherent edge tie anywhere ⇒
  `w*_greedy = w*_c` PROVED analytically**; cyclic-13 first incoherent edge tie
  at depth 2 (matches the hand proof); GQ(2,2) at depth 6; **STS(9) at depth 3
  with genuinely divergent branch completions, yet per-seed greedy/complete
  equality holds on 0/72 shuffled (presentation, seed) pairs.** Prop 6.0 is
  strictly sufficient; the classification is **not criterion-decidable** —
  incoherence marks avalanche *exposure*, not divergence. New avalanche
  channel: incoherent *ordering* ties (present even on Fano at depth 3),
  invisible to greedy-vs-complete since both encoders branch over orderings.
- Corrections propagated: the "coherence inferred from Prop 6.0 + verified
  equality" entries for STS(9) in `stability.md` §3 and
  `lemma_b1_restatement.tex` §5–6 were affirming the consequent and are now
  corrected (the STS(9) one is refuted by computation).

**(3) Rigorous B-avg — demoted to empirical, obstruction proved.**
At constant density the depth-3 local neighbourhood converges to a bounded-size
Galton–Watson hypertree whose type distribution has an atom ⇒ two vertices
collide in ξ with probability bounded away from 0 ⇒ Θ(n²) collisions — the
sketch's "generically distinct ξ" premise is FALSE at constant density. Probe
confirms avalanche dominance: median `s(e)` grows ≈ linearly in n for *every*
edit type (145 vs `kΔ` = 21 at n = 32, density 1.5), approaching the string
length. B-avg restated as the instrumented drift decomposition; Thm 3 of
`theorem_b_stability.tex` annotated.

**(4) W-token proviso — DISCHARGED.** Python encoder constructs no `TokenW`;
C++ `Token::make_w()` is never called. Pinned by
`tests/unit/core/test_no_w_tokens.py` (13 tests, both backends, design fixtures
+ pinned random connected hypergraphs, 2.3 s). The `m(1+kn)` length envelope
and B-worst stand as stated. (Flag: CLAUDE.md invariant 6's "W can appear in a
canonical string" describes S2H *input* tolerance, not emission — wording
could be tightened, out of scope here.)

**T-M5a instrumentation spec (extended):** log per instance `M(H)` (one pass
over the string) and first-incoherent-tie depth; per edit `R(e)`, `T_span(e)`.
**Operational warnings for T-M5a:** (a) unpruned `w*_c` blows up on coherent-tie
symmetric inputs (complete binary trees d ≥ 5 exceed a 5·10⁴ branch budget);
(b) at density ≈ 1.0 and n ≥ 48, *random* draws frequently exceed the budget
too (hypertree-like pendant symmetries) — corpus n-ranges at low density must
budget for this or land stabilizer-orbit pruning first.

**Verification (test-runner agent, 2026-07-14):**

| Check | Result |
|---|---|
| pytest unit | 681 passed, 5 skipped (incl. `test_no_w_tokens.py`) |
| pytest property | 79 passed |
| ruff (`src/ tests/` + both new scripts) | clean after fixing 2 findings in the new scripts; 3 remaining findings pre-existing |
| mypy `src/isalhg/` | 20 errors, all pre-existing (no `src/` change in this task) |

No `src/isalhg/` source was modified (encoder read-only, per task scope).

**Status: DONE** — acceptance satisfied on every clause: (iv)–(v) refuted with
stated model, explicit mechanism, and the paper-claim consequence written into
`stability.md`; T-B3 derived at depth 2 by hand + full criterion audit with the
STS(9) obstruction documented; B-avg explicitly demoted with its premise
failure proved; W-proviso discharged with a pinned test; both proof `.tex`
files and `stability.md` §2.2/§6 updated consistently.
