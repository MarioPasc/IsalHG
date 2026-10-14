# T-KBp — the 600 s re-run of the censored tail is not implemented anywhere
**Declared:** 2026-09-10 15:05 CEST
**Status:** OPEN
**Delegation:** agent
**Why out of scope:** found while submitting RQ7 (T-KBf). D-ART5 folds this
measurement "into the RQ7 envelope sweep", and RQ7's code has no 600 s path at
all, so it is a missing deliverable rather than a defect in what runs.

**Context to read first:**
- `docs/article/DEVELOPMENT/T-KB/IN-PROGRESS/T-KBe.md`
  §"Pre-stated expectation for the 600 s re-run" — the prediction, written
  before the data and explicitly refutable
- `docs/article/DEVELOPMENT/DECISIONS.md` D-ART5, decision 2: the 600 s run is
  "a re-run *of the censored tail*, i.e. characterisation by definition, never
  a row"
- `experiments/tkde/rq7.py` — the sweep; `aut_bucket` per instance is the
  `|Aut|` axis and is implemented, the 600 s tail is not (`grep 600` finds only
  `nscaling_budget_s`)
- the censored id lists, already on disk:
  `results/IEEETKDE/matrices/{ndc_classes,wd50k66,wd50k100}/wstar_orbit.censored.json`
- `experiments/tkde/budget.py::engine_word` — the budgeted entry point
- `.claude/rules/coding_rules.md` — always

**Description:** D-ART5 keeps the published budget at 60 s and folds a 600 s
re-run of the censored members into RQ7 as tail characterisation. No such code
exists. The measurement is small and self-contained: take the members censored
at 60 s, re-run each at 600 s, report how many complete.

T-KBe pre-stated the outcome so the run can refute it:

- **`wstar_orbit`** has 32 completions in [30, 60) s and 6 in [55, 60), so a
  population that dense just below the budget should continue above it — *a
  material fraction of its 77 is expected to finish by 600 s*.
- **`wstar_rank`** has none in [30, 60) yet 53 censored, i.e. bimodal — *if the
  gap is real most of its 53 should still be censored at 600 s*, because they
  are arity-10 displacement enumerations, exponential in the arity, not slow
  instances of a feasible search.
- **The refutable form:** if most of the 53 complete at 600 s, the bimodality
  is an artefact of the budget rather than of the mechanism, and D-ART5's claim
  that the residual tail is *displacement rather than symmetry* needs
  rewriting.

**Cost gate:** worst case is every member hitting the ceiling — roughly 130
members × 600 s ≈ 22 h sequential. It must be sharded or run with a wall that
accommodates it, and it must be a **separate job**, since it is characterisation
and its rows must never join a published table.

**Acceptance:** a runner that reads the censored id lists, re-runs each member
at 600 s under the same budgeted forked-child model, and writes rows carrying
`(member_id, collection, arm, m, k, aut_bucket, secs, censored)`; completion
counts reported per arm against the pre-stated expectation, with the verdict
stated as confirmed or refuted; the rows land outside every RQ table and are
labelled tail characterisation.

**Out of scope here:** changing the published 60 s budget (D-ART5 decision 2);
merging any of these rows into an RQ table; RQ7's sweep, yield or N-scaling
passes.
