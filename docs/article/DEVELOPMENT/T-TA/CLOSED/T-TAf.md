# T-TAf — Freeze the canonical form: unpruned `w*_c`, orbit-pruning only (D-TA2)
**Declared:** 2026-07-09 11:25 CEST (handoff from the T-TAa/T-TAd assessment)
**Status:** DONE (2026-07-09 13:25 CEST, orchestrator)
**Depends on:** T-TA (proof) — must land **with or before** T-TAd
**Delegation:** orchestrator-only — this freezes the *definition* of the paper's
central object; getting it subtly wrong is unrecoverable once tables exist.
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

---

## Closing note (2026-07-09 13:25 CEST, orchestrator)

Executed directly by the orchestrator in the main tree (delegation:
orchestrator-only). Acceptance, clause by clause:

1. **D-TA2 recorded** — already resolved in `DECISIONS.md` (PI, 2026-07-09
   11:38 CEST) with the verbatim call and the reasoning of record; no edit
   needed.
2. **Proof doc** — `theorem_a_completeness.tex` §Consequences gains a
   *Frozen definition (D-TA2)* item: `w*_c` = the unpruned tie-complete
   lex-min (κ-min over the full `T(σ)` × label-respecting orderings; Python
   `tie_branch=True` ≡ C++ variant 7); ρ-refinement forks the definition and
   is not sanctioned; stabiliser-orbit pruning (Prop. `prop:coherent`) is the
   only value-preserving lever. The C++-port item's "lever remains available"
   sentence is corrected to say D-TA2 takes ρ off the table even on
   η-degenerate rigid inputs. Recompiled clean: two `pdflatex` passes exit 0,
   0 undefined references; PDF regenerated.
3. **Docs** — `stability.md` §1 gains the frozen-definition paragraph before
   Corollary A; `CLAUDE.md` §Mathematical Foundation gains the frozen-`w*_c`
   bullet. Both name orbit pruning as the only sanctioned speedup and point
   to the pin test.
4. **Regression pins** — new `tests/unit/core/test_wstar_c_frozen.py` pins
   `(len, sha256)` of `w*_c` (k=3, `greedy_min_complete`) on the four required
   inputs: Fano `(121, 9695315f…)`, STS(9) `(227, a6282f85…)`, cyclic STS(13)
   `(256, 77d9fa1e…)`, n=4 counterexample `(54, ab9393ff…)`.

Closing check (verbatim):

```
$ pytest tests/unit/core/test_wstar_c_frozen.py -q
============================== 4 passed in 0.47s ===============================
$ mypy tests/unit/core/test_wstar_c_frozen.py
Success: no issues found in 1 source file
$ ruff check tests/unit/core/test_wstar_c_frozen.py
All checks passed!
```
