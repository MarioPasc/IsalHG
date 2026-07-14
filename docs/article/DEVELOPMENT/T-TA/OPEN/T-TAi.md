# T-TAi — Stabilizer-orbit pruning for `w*_c` (the D-TA2-sanctioned speedup)
**Declared:** 2026-07-14 13:42 CEST
**Status:** OPEN
**Depends on:** T-TA (Prop 6.0 — CLOSED); gates T-M5a's corpus n-range at low density
**Delegation:** orchestrator-only
**Why out of scope:** discovered during T-TBb (pointer-run amortization), whose scope forbade any change to the frozen `w*_c`; this is a value-preserving *implementation* change to the production encoder, not theory.
**Context to read first:**
- `docs/article/DEVELOPMENT/DECISIONS.md` — D-TA2: "the only sanctioned future speedup is **stabiliser-orbit pruning** (value-preserving by Proposition 6.0), never ρ-refinement"
- `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/completeness/theorem_a_completeness.tex` — Prop 6.0 (coherent tied branches related by a `dom(μ)`-fixing automorphism have equal completions)
- `scripts/tb3_coherence_criterion.py::automorphisms`, `::pointwise_stabilizer`, `::edge_orbit_reps`, `::ordering_orbit_reps` — working Python orbit machinery (T-TBb audit); the production version ports the *orbit-collapse* to the C++ encoder (`src/isalhg/core/_native/`)
- `docs/article/DEVELOPMENT/T-TB/CLOSED/T-TBb.md` — closing note §operational warnings: unpruned `w*_c` exceeds a 5·10⁴ branch budget on complete binary trees d ≥ 5 and on random connected draws at density ≈ 1.0, n ≥ 48 (hypertree-like pendant symmetries)
- `tests/unit/core/test_wstar_c_frozen.py` — the regression pins: any pruning that changes `w*_c` fails loudly
- `.claude/rules/coding_rules.md` — always
**Description:** Implement stabilizer-orbit pruning in the tie-complete encoder: at each residual tie (edge-level and label-respecting-ordering-level), explore one representative per orbit of the pointwise stabilizer of `dom(μ)` instead of every candidate. Prop 6.0 guarantees the returned `w*_c` is unchanged; the win is exactly the automorphism redundancy that makes symmetric and hypertree-like inputs blow up. Needs an automorphism-group computation (port the T-TBb backtracking or bind nauty via the existing Levi reduction) whose cost must be amortized against the branching saved.
**Acceptance:** `test_wstar_c_frozen.py` and the full unit+property suites green with pruning enabled; complete binary trees d ≤ 8 and density-1.0 connected ER draws at n = 48–96 encode within seconds (benchmarked before/after, wall-clock reported); byte-identical `w*_c` vs the unpruned encoder on a pinned random corpus (n ≤ 12 exhaustive-ish sample) and on {Fano, STS(9), cyclic-13, GQ(2,2)}.
**Out of scope here:** any ρ-refinement of the tie set (changes the frozen definition, D-TA2); changing the seed cascade; T-M5a itself.
