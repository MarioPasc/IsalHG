# T-KBw — no run records a proxy for search work, so the branch factor is only ever inferred
**Declared:** 2026-09-11 00:27 CEST
**Status:** OPEN
**Delegation:** agent
**Why out of scope:** raised by `[IsalHG-Fable]` while pre-registering RQ7's
reading. It is an instrumentation addition, not a fix to anything now running.

**Context to read first:**
- `experiments/tkde/rq7.py` — the sweep's row schema
- `docs/article/DEVELOPMENT/T-KB/OPEN/T-KBg.md` §"replacement sentence" — the
  mechanism the missing number would measure
- `docs/article/DEVELOPMENT/T-KB/IN-PROGRESS/T-KBf.md` §"tail600 COMPLETE"

**Description.** The corrected explanation of the residual tail is
**displacement enumeration × tie-complete branch factor**, with only the
multiplier specific to the search-based program. Every piece of evidence for it
is currently a **differential**: 24.7 % against 50.9 % recovery at a tenfold
budget, and 15 of 67 (22.4 %) of the hardest stratum orbit-only.

**No run records the branch factor itself.** RQ7's schema is `secs`,
`tokens_or_bytes`, `m`, `k`, `n`, `aut_bucket`, `censored` — wall-clock
and size. Nothing counts branches explored, tie sets entered, or nodes visited.
(RQ3 records `n_ties` per consensus run, but that is a different quantity in a
different experiment.)

So the mechanism sentence rests on two differentials agreeing, which is real
evidence but indirect, and a reviewer asking "how much branching?" gets an
inference rather than a number.

**Acceptance.** The canonical-string entry points expose a counter — tie sets
entered and branches explored are the two that matter — under three design
constraints, all raised by `[IsalHG-Fable]` against a weaker first draft.

**1. Separate the counted run from the timed one.** The first draft required a
counter "cheap enough not to perturb the budget-censored wall-clock it sits
beside". That constraint is **unfalsifiable by construction**: verifying "cheap
enough" needs the uninstrumented run it was supposed to replace. Design it away
instead — **cost is measured in one run with no counter, branch count in a second
run whose timings nobody uses.** Branch count is a *structural* quantity, so the
counted run does not need to be time-faithful and nothing about it has to match
the census.

**2. The instrumented run is characterisation, never a published row.** It is a
different pipeline from the frozen one, so it cannot supply a census row — the
same ruling as the 600 s tail (D-ART5 decision 2), for the same reason.

**3. Target the *completing* members, not the tail.** On a censored member the
search never finishes, so "branches explored" is bounded by the budget and
**measures the budget rather than the instance**. On completing members both cost
and branch count are fully observed, and their relation states the mechanism
**directly** instead of differentially:

> If cost tracks branch count × a displacement term growing with arity across the
> completing range, the multiplication reading becomes a **fitted relation on
> observed data**, and the censored tail becomes *extrapolation from it* rather
> than an inference from two rate differentials. A reviewer asking "how much
> branching?" then gets a **coefficient**, not a comparison.

**Tests:**
- zero for the ordered walk — no branching by construction;
- positive for the tie-complete search on an instance with a known non-trivial
  tie set;
- **identical across repeated runs of the same member.** Branch count is
  structural; if it varies, the counter is measuring **scheduling**, not search.

**Out of scope here:** re-running anything; the mechanism claim itself, which
stands on the differentials meanwhile.
