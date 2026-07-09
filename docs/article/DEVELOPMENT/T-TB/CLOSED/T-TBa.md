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

---
**Round 2 correction (2026-07-09) — six defects fixed:**

- *A (merge conflict):* `git merge main` on the stale worktree left conflict markers in
  `stability.md` §6 (T-A/T-B0 items) and `DEVELOPMENT/README.md` (scope table + critical
  path paragraph). Both resolved: §6 keeps main's T-A ("PROVED AND PI-REVIEWED", `"canonical"`,
  D-TA2) and main's T-B0 (D-CONN1 insert-before-delete path-normalization mechanism); my updated
  T-B1/B2/B3 (four-source framing, N_r[e], three conditions) sit on top. README.md scope
  table: T-TA 0/9, T-TB 1/1. Critical path paragraph merged: T-TA chain + T-TBa both
  described; "Runnable in parallel" updated to T-TB (now unblocked), T-M2c P3, T-M4', T-M3a-d.

- *B (missing condition iii + argmin migration source):* Lemma B1 (stability.md §2.2 and
  lemma_b1_restatement.tex §3) now lists three conditions: (i) seed membership, (ii) tie-set
  stability in N_r[e], (iii) argmin-seed preservation — v_0 remains the κ-minimum seed in H⊕e.
  Without (iii), the per-seed O(k·Δ) bound does not lift to the global s(e). Argmin migration
  added as source 2 in the four-source §3 table and §6 avalanche list.

- *C (coherence overstatement):* stability.md §2.2, §3, §4 and lemma_b1_restatement.tex §5
  now state that coherence (Prop 6.0) suppresses sources 3-4 only (early and deep tie
  perturbations). Sources 1 (seed-set change) and 2 (argmin migration) remain possible even on
  fully coherent hypergraphs. The old phrasing "no avalanche for any edit that preserves the
  seed" is gone.

- *D (wrong radius N[e] vs N_r[e]):* All occurrences of "N[e]" as the transparency condition
  set changed to "N_r[e] (r=3, structural-tuple depth)". The encoding window remains N_1[e]
  (1-hop, O(k·Δ) vertices). Distinction stated explicitly in stability.md §2.2 (two-radii
  paragraph), in Lemma B1 statement, in §3 sources 3-4, and in lemma_b1_restatement.tex
  Definition 1, Lemma 2, proof sketch, §4 greedy comparison, §6 sources 3-4, §7 T-B2 item.

- *E (evidence imprecision):* "empirically verified at T-TAa" changed to "inferred from
  Prop 6.0's sufficient direction; verified equality w*_greedy = w*_c" throughout. stability.md
  §3 table "all ties coherent at all depths" → "All depths (inferred from Prop 6.0 + verified
  equality)". lemma_b1_restatement.tex §5 stability paragraph and §6 table rows similarly
  updated. C-singleton claim now quotes the exact T-TAa.md closing note sentence.

- *F (greedy comparison wording):* lemma_b1_restatement.tex §4. "The greedy makes comparisons
  only at a single depth" and "the only comparison points are the root-level decisions" were
  wrong (the greedy makes comparisons at every state along its single path). Replaced with:
  "The greedy makes one comparison per state and commits immediately; the trajectory is a single
  path, not a tree. A tie at depth d perturbs only the decision at depth d and those downstream
  on the same path." The radius is correctly stated as N_r[e] (r=3) for both encoders.
