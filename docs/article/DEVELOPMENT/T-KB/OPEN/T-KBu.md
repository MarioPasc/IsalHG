# T-KBu — `censored` conflates "exceeded the budget" with "never attempted"
**Declared:** 2026-09-10 22:21 CEST
**Status:** OPEN
**Delegation:** agent
**Why out of scope:** raised by `[IsalHG-Fable]` as the fourth instance of the
collapsed-binary pattern (L26). Unlike the other three it reaches **published**
numbers, so it is filed rather than fixed inline.

**Context to read first:**
- `experiments/tkde/budget.py::guarded_budget_call` — the canary, and the
  `TkdeBudgetError` it raises
- `a99775a` "fix(tkde): a poisoned fork must not be recorded as a censoring"
  (**2026-09-07 09:17**) and `ba95008` (2026-09-08 13:01, factored into
  `guarded_budget_call`)
- `docs/article/D_ART3/foundation/lessons.md` L15 and L26
- `DECISIONS.md` D-ART5 R2 — quotes 77 of 7,369 censored

**Description.** `censored = 1` encodes two states: *attempted and exceeded the
budget*, and *never attempted*. The merged state is the one that reads as an
honest measurement, and a row saying censored is indistinguishable from a row
saying censored. L15 publishes this census per stratum and D-ART5's R2 sentence
quotes it, so the numbers currently mean "exceeded the budget" without being
able to prove they do not also mean "never ran".

**The current code is not defective.** `guarded_budget_call` **raises**
`TkdeBudgetError` on a poisoned fork rather than reporting a censoring, and no
caller swallows it — the two `rq3.py` mentions are `Raises` docstrings.
Verified 2026-09-10. This is a question about **rows already on disk**.

**Audited 2026-09-10, from the `git_sha` the rows already carry** — every sha
resolved with `git merge-base --is-ancestor a99775a`:

| results root | PRE-FIX rows | post-fix rows |
|---|---|---|
| `IEEETKDE` | **1,314,688** | 5,326,601 |
| `IEEETKDE_isal` | **1,064,202** | 3,607,126 |
| `IEEETKDE_isal_consensus` | 0 | 227,012 |
| `IEEETKDE_isal_merged` | 0 | 1,953,096 |
| `IEEETKDE_isal_preview` | 0 | 2,033,069 |
| `IEEETKDE_isal_reachprime` | 0 | 227,012 |
| `IEEETKDE_isal_reach1{,b}` | 0 | — |

All 2,378,890 pre-fix rows carry one of four shas, **all dated 2026-09-05**, i.e.
the first wave. **Every derived root is clean**, including the M3 census
`IEEETKDE_isal_merged` that T-KBp's 77/53 is counted from and the RQ3 rows the
consensus readings come from.

**So the exposure is bounded and is not where the published numbers live** — but
"bounded" is not the same as "verified per row", which is what this task is for.

**Acceptance:**
1. The schema distinguishes the two states — e.g. `censored` for *attempted and
   exceeded* and a separate `not_attempted` (or a three-valued `outcome`), so
   "could not determine" is never encoded as either outcome.
2. A test drives the poisoned path and asserts the row records *not attempted*
   rather than *censored*, and that the census counts it separately.
3. The two pre-fix roots are marked in place with the audit above, so anyone
   reading them knows which counts are provably genuine and which are not.
4. **The audit generalises**: sweep every flag column for the same collapse —
   anywhere a guard can short-circuit *before* the work happens. The fork-health
   canary is one such guard and is upstream of every budgeted arm; `skipped`,
   `n_censored_members` and `n_excluded_candidates` are the other candidates.

**Out of scope here:** re-running any campaign job; the canary itself, which is
correct; L15's reporting format.
