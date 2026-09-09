# T-KBl — resolve the fingerprint screen's `k` and prefix flag at the corpus level
**Declared:** 2026-09-09 09:10 CEST
**Status:** OPEN
**Depends on:** — (but see the landing window below)
**Delegation:** orchestrator-only
**Why out of scope:** found while executing T-KBf's D-KBf3 (giving `wstar_orbit`
an `N x N` matrix). The screen is correct on both campaign corpora — measured —
so fixing it now would change the censoring census between RQ1 and RQ2 for no
gain. Same landing constraint as T-KBj, and for the same reason.

**Context to read first:**
- `src/isalhg/metric_space/distances/isal_engine.py::IsalEngineLevenshtein.fingerprint`
  (`k = required_k(H)`, `augment = H.n_vertex_labels > 1`, per member) against
  `::matrix` / `::_resolve_corpus_k` (`k` = corpus max, `augment = any(...)`)
- `experiments/tkde/budget.py::arm_fingerprint_screen` — the screen, and its
  docstring's claim that the builder must recompute
- `src/isalhg/metric_space/toolkit/matrix.py::build_matrix_censored` — the two
  caller-owned properties, in particular "it costs the survivors'
  representations twice"
- `tests/unit/metric_space/test_isal_engine_k_invariance.py` — the 28 tests that
  pin why the present arrangement is safe *here*
- `docs/article/DEVELOPMENT/T-KB/IN-PROGRESS/T-KBf.md` §"D-KBf3 executed" — the
  measurement and the objection it answers
- `docs/article/DEVELOPMENT/T-KB/OPEN/T-KBj.md` — the sibling deferral
- `.claude/rules/coding_rules.md` — always

**Description:** `build_matrix_censored` screens each member through
`fingerprint` and then rebuilds the survivors through `matrix`, but the two
resolve `k` and the seed-prefix flag at different scopes. On the campaign's two
corpora this is provably harmless — `k` is value- *and* cost-invariant above
`required_k` (0 word mismatches over 43 ndc members at corpus `k` = 10, cost
ratio 0.96–1.03) and the label count is uniform per corpus (ndc 4, wd50k66 1),
so the two agree on every member. On a corpus with a **non-uniform** label
count they would not: the screen would certify a member on an unprefixed word
while the matrix builds a prefixed one, and the screen's census would not be the
matrix's census. The general fix is to resolve `k` and the flag at the corpus
level *inside the screen*; reuse of the screen's words then becomes correct by
construction and the deliberate double computation disappears.

Raised by the `[IsalHG-Fable]` session, which first proposed reuse as the
immediate fix; that was declined because reuse is unsound while the two scopes
differ, and this task is the precise form the point survives in.

**Acceptance:** the screen resolves `(k, augment)` over the corpus; a test on a
synthetic corpus with a **non-uniform** vertex-label count shows the present
screen and `matrix` disagreeing and the fixed screen agreeing;
`build_matrix_censored` consumes the screened words with the matrix values
unchanged on both campaign corpora (differential against the current build);
`test_isal_engine_k_invariance.py` still green.

**Out of scope here:** the `spawn` fix for the fork poison (T-KBj); anything
that alters `ISAL_MATRIX_ARMS`, `DEFAULT_SPECS` or a published arm set.

**Landing window:** **not between RQ1 and RQ2**, and not while job 2264827 or
any successor matrices job is unharvested — it changes which members a budgeted
arm censors, and the campaign's censuses must stay comparable. Land it with or
after T-KBj.
