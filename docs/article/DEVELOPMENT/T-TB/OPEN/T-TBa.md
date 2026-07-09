# T-TBa — Restate Lemma B1 and the avalanche over `w*_c`, not greedy H2S
**Declared:** 2026-07-09 11:25 CEST (handoff from the T-TAa/T-TAd assessment)
**Status:** OPEN
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
