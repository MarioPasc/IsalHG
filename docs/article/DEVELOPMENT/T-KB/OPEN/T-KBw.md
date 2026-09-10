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

**Acceptance:** the canonical-string entry points expose a cheap counter — tie
sets entered and branches explored are the two that matter — and the runs that
sweep cost record it beside `secs`. It must be **cheap enough not to perturb
the wall-clock it sits beside**, since those runs are budget-censored and the
counter must not change what censors. A test asserts the counter is zero for the
ordered walk (no branching by construction) and positive for the tie-complete
search on an instance with a known non-trivial tie set.

**Out of scope here:** re-running anything; the mechanism claim itself, which
stands on the differentials meanwhile.
