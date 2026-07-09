# T-TAf — Freeze the canonical form: unpruned `w*_c`, orbit-pruning only (D-TA2)
**Declared:** 2026-07-09 11:25 CEST (handoff from the T-TAa/T-TAd assessment)
**Status:** OPEN
**Depends on:** T-TA (proof) — must land **with or before** T-TAd
**Why out of scope:** T-TAa's mandate was to port and measure the tie-complete
encoder; T-TAd's is to flip the default. Neither settles *which* tie-complete
lex-min is the article's `w*_c`, and that is a definitional decision with a
one-shot cost, not an implementation detail.
**Context to read first:**
- `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/theorem_a_completeness.tex` — Lemma 6.1 (`lem:pruning`), Proposition 6.0 (`prop:coherent`), §7 item 3
- `docs/article/DEVELOPMENT/DECISIONS.md` — **D-TA2**, the decision this task executes
- `docs/article/DEVELOPMENT/T-TA/CLOSED/T-TAa.md` — decision D2 and the wall-clock table (GQ(2,2) 1.09 s; `ρ`-refinement buys nothing on vertex-transitive designs)
- `src/isalhg/core/hypergraph_to_string.py::{_tied_v_candidates,_encode_from}` — where a refinement key would be applied
- `docs/article/theoretical/stability.md` §1 — the claims that attach to `w*_c`
- `.claude/rules/coding_rules.md` — always
**Description:** Lemma 6.1 preserves *completeness* under any iso-invariant
refinement key `ρ` of the residual tie set, but the refined search returns a
**different** canonical form — the lex-min over a proper subset of `T(σ)` need not
equal the lex-min over `T(σ)`. So `ρ`-pruning forks the definition of `w*_c`, and
once any table in the paper is computed on one form, adopting the other invalidates
every `d_I` value. Freeze the definition **now**, before numbers exist: `w*_c` is
the *unpruned* tie-complete lex-min (proof text; shipped C++ variant 7). Sanction
exactly one future speedup — **stabiliser-orbit pruning**, which by Proposition 6.0
returns the *same* `w*_c` because tied branches related by an automorphism fixing
`dom(μ)` pointwise have equal completions — and record that it, not `ρ`-refinement,
is the lever that attacks the actual cost (automorphism redundancy on
vertex-transitive designs, where every tied candidate carries the same value under
*any* iso-invariant key).
**Acceptance:** D-TA2 recorded as resolved in `DECISIONS.md` with the PI's call;
`theorem_a_completeness.tex` §Consequences states the frozen definition and names
orbit pruning as the only value-preserving lever; `stability.md` §1 and
`CLAUDE.md` §"Mathematical Foundation" say `w*_c` is the unpruned tie-complete
lex-min; a regression test pins `w*_c` on {Fano, STS(9), STS(13), the n=4
counterexample} so any future refinement that changes the value fails loudly.
**Out of scope here:** implementing orbit pruning (a research subtask — detecting
the stabiliser during search is the hard part of nauty); the default flip (T-TAd);
the surface hardening (T-TAg).
