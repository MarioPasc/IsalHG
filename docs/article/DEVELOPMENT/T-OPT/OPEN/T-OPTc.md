# T-OPTc — Correct stabiliser-orbit pruning (post-refutation follow-up)
**Declared:** 2026-07-19 13:05 CEST
**Status:** OPEN
**Depends on:** T-OPTa (CLOSED — records the refuted cheap-fingerprint
approach); T-OPTb (same `_native/` lane — sequential)
**Delegation:** agent
**Why out of scope:** T-OPTa's closing note promised this handoff but did not
file it; the orchestrator files it at the S2 close. The T-DQ3' DNF tail
(symmetry-driven, 27% of the arity-capped IMDB sample at 10 s/instance) is
still unaddressed — orbit pruning remains the only sanctioned lever.
**Context to read first:**
- `docs/article/DEVELOPMENT/T-OPT/CLOSED/T-OPTa.md` — the refutation record:
  a per-node fingerprint (sorted mapped-neighbour pairs) is *necessary but
  not sufficient* for orbit membership; Hypothesis found an n=5 witness
  where distinct orbits share the fingerprint and the pruned encoder misses
  the lex-min branch. Any new attempt must add that witness as a pinned
  regression test before implementing.
- `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/completeness/theorem_a_completeness.tex`
  — Proposition 6.0: pruning is value-preserving only for *genuine*
  stabiliser orbits (coherent tied branches), not fingerprint classes.
- `src/isalhg/core/_native/src/h2s.cpp` — the unpruned tie-complete encoder.
- `docs/article/DEVELOPMENT/DECISIONS.md` — D-TA2 (ρ-refinement forbidden;
  orbit pruning sanctioned) and OD6 (the anchor re-test this would enable).
- `tests/unit/core/test_wstar_c_frozen.py` + `scripts/probe_hic_wstar.py` —
  the invariance pins and the 73–74/100 budget baseline to beat.
**Description:** Implement orbit pruning against *actual* partial-labelling
stabilisers: maintain (a generating set of) the automorphism subgroup fixing
the mapped prefix — refined incrementally as vertices are labelled, in the
individualization-refinement style of nauty/Traces (McKay & Piperno 2014) —
and expand one representative per genuine orbit of the residual tie set.
Candidate cheaper route: compute `Aut(H)` once up front (via the existing
pynauty Levi bridge as an *oracle for testing only* — the encoder itself
stays stdlib-only C++) and derive stabilisers by chain filtering; measure
whether group management amortises on the DNF instances.
**Acceptance:** (1) the T-OPTa Hypothesis witness pinned and green; (2)
`w*_c` byte-identical on the frozen pin set (incl. slow STS(13)s) and on a
pruned-vs-unpruned Hypothesis sweep; (3) budget-mode completion fraction on
the T-DQ3' sample re-measured — a material improvement (target: the
symmetry DNFs at n≤15 complete) triggers the OD6/anchor re-test question to
the PI; (4) suite + ruff + mypy at baselines.
**Out of scope here:** ρ-refinement in any form; changing `w*_c`; the OD6
decision itself (PI).
