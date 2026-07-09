# T-TBa — Restate Lemma B1 and the avalanche over `w*_c`, not greedy H2S
**Declared:** 2026-07-09 11:25 CEST (handoff from the T-TAa/T-TAd assessment)
**Status:** DONE
**Depends on:** T-TA (Theorem A for `w*_c`) — blocks T-TB's T-B1/T-B2/T-B3
**Why out of scope:** T-TB is the stability proof. This task fixes the *object*
that proof is about: `stability.md` §1 says every metric-space claim attaches to
`w*_c`, while §2.2 and §3 reason about the deterministic greedy trajectory. The
two sections currently describe different functions, and no amount of work on T-B1
is valid until that is reconciled.
**Context to read first:**
- `docs/article/theoretical/stability.md` §1 (claims attach to `w*_c`) vs §2.2 ("Lemma B1 (locality of **greedy** H2S). Fix seed `v_0` and the greedy order `π`…") and §3 (avalanches live at top-`ξ` ties)
- `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/theorem_a_completeness.tex` — Proposition 6.0 (`prop:coherent`) and Remark 6.1: vertex-transitivity buys tie-coherence **at the root only**; the stabiliser of the partial map shrinks as the search descends
- `docs/article/DEVELOPMENT/T-TA/CLOSED/T-TAa.md` — the machine-verified consequence: `w*_greedy = w*_c` on Fano and STS(9) but **not** on STS(13)
- `src/isalhg/core/hypergraph_to_string.py::_encode_from` (`tie_branch=True`) — the lex-min-over-branches semantics the lemma must now cover
- `docs/article/empirical/correlation.md` §Exp E2b — the sensitivity histogram whose predictions were derived for greedy
- `.claude/rules/coding_rules.md` — always
**Description:** Lemma B1 as written fixes a seed `v_0` and a greedy visitation
order `π`, and concludes that an edit leaving `π` unchanged outside `N[e]` perturbs
`w*` in `O(k·Δ)` positions. The tie-complete encoder takes a **lex-min over
exponentially many trajectories**, so fixing `π` no longer pins the output: an edit
can perturb a tie set at *any depth* and the minimiser jumps to a different branch.
Proposition 6.0's remark makes this concrete — ties fail to be automorphism-coherent
*deep* in the search, not at the root — so §3's claim that avalanches live at
top-`ξ` ties (i.e. in the vertex-transitive regime) understates the avalanche
surface. Restate Lemma B1 for the branching search, determine whether the min
structure helps or hurts `s(e)` (the direction is not obvious: a min over a set can
be more stable than any member, or can jump discontinuously), and rewrite §3's
avalanche condition in terms of tie-set perturbation at arbitrary depth rather than
seed flips. Then re-derive E2b's predictions.
**Acceptance:** `stability.md` §2.2 and §3 state Lemma B1 and the avalanche
condition over `w*_c`, with no residual reference to a fixed greedy order; the
`s(e)` decomposition (direct + reordering) is either re-derived for the branching
search or replaced by whatever the branching search admits; E2b's predicted
histogram shape is restated and marked as the falsification test; the T-B1/T-B2/T-B3
checklist items in §6 are rewritten against the new statement.
**Out of scope here:** proving the restated Lemma B1 (T-B1); the constant (T-B2);
the disconnected-path domain gap (T-M2c / T-B0); running E2b (T-M5a).

---
**Closing (2026-07-09):**
- *Premise verification:* The task's premise is correct and non-trivial. `stability.md` §2.2
  and §3 were written against the greedy encoder's fixed-trajectory semantics, while §1
  and all downstream claims attach to `w*_c`. Prop 6.0 / Remark 6.1 of
  `theorem_a_completeness.tex` supply the precise mechanism (stabiliser shrinkage as the
  search descends) that the restatement must incorporate.
- *Lemma B1 restated (§2.2):* The "reordering cost" paragraph and the greedy-order-fixing
  Lemma B1 are replaced by a "branching-tree stability" exposition and a new Lemma B1
  stated over the tie-complete branching search. The stability condition is now
  **tie-set transparency** (Definition: seed preserved; no vertex in N[e] participates in
  any tie T(σ) at any search depth). The relationship to the greedy condition is made
  explicit (strictly stronger; same O(k·Δ) bound when satisfied). The question "does the
  min structure help or hurt?" is answered: no generic advantage; coherent-tie regime is
  stable, incoherent-tie regime is not. C-step singletonness is noted (from T-TAa analysis)
  as eliminating C-tie avalanches entirely.
- *Avalanche condition restated (§3):* Three avalanche sources (depth 0 = seed flip;
  depth d small = early tie perturbation; depth d arbitrary = deep tie perturbation) replace
  the single "top-ξ tie" criterion. The vertex-transitive regime is explicitly split into
  coherent (Fano, STS(9) — stable for w*_c) and incoherent (STS(13), GQ(2,2) — avalanche-prone)
  using the T-TAa empirical result. The three-part theorem (B-worst/B-cond/B-avg) is preserved;
  "seed-stable" → "tie-set transparent" in B-cond.
- *§4 avalanche prediction updated:* The bimodal prediction for "high-automorphism designs"
  is split into three regimes mirroring §3.
- *T-B1/T-B2/T-B3 checklist updated (§6):* Items rewritten against the new Lemma B1
  (tree correspondence, relative CDLL order, C-branch singletonness for B1; branching window
  and token-width constant for B2; stabiliser-orbit characterization using Prop 6.0 for B3).
- *E2b re-derived (correlation.md):* Histogram prediction revised from "symmetric ⇒ bimodal"
  to the three-regime split. Falsification target made explicit: a bimodal result on Fano or
  STS(9) would contradict the coherence criterion.
- *External derivation:* `stability/lemma_b1_restatement.tex` written to
  `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/stability/` (permanent, outside repo).
- *No code touched.* No tests to run; task touches only `docs/`.
- *Checks:* pytest not run (docs-only task); ruff/mypy not run (no Python changed).
  Baselines ruff 3 / mypy 21 assumed unchanged.
