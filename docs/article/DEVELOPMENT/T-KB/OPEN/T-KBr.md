# T-KBr — the orbit contract test passes or fails by machine load
**Declared:** 2026-09-10 17:05 CEST
**Status:** OPEN
**Delegation:** agent
**Why out of scope:** found while verifying the consensus merge (T-KBf). The
test is correct about the property it guards; what is wrong is that its verdict
depends on how busy the machine is.

**Context to read first:**
- `tests/integration/test_cpp_orbit_corpus.py::test_orbit_matches_unpruned_wstar_c`
  — both asserts, and the docstring's own reasoning about censored baselines
- `docs/article/DEVELOPMENT/DECISIONS.md` D-ART5 — the claim this test guards,
  and the 7,013/7,013 evidence that actually carries it
- `docs/article/DEVELOPMENT/T-KB/IN-PROGRESS/T-KBf.md` §"Matrices 2264831
  COMPLETED" — wall-clock censoring measured drifting with node load
  (`wstar_orbit` 7 → 5 on wd50k66 between runs)
- `.claude/rules/coding_rules.md` §4 — testing discipline

**Description:** the test draws members, computes `w*_c` under both the unpruned
and the orbit-pruned engine at a 60 s budget, and compares **only where the
unpruned arm completes**. It then requires at least `N_MEMBERS // 2 = 12`
successful comparisons.

That second assert is a wall-clock threshold in disguise. Under load more
members exhaust the budget, fewer pairs are comparable, and the test fails
having found **no disagreement whatsoever**. Measured 2026-09-10 on the same
commit:

| run | result |
|---|---|
| inside the full suite, with three ssh monitors and an agent active | **2 failed** |
| the same two tests alone | **2 passed** (254 s) |

A value mismatch would be deterministic and would have failed in both, so the
failing assert is the count guard, not `pruned.value == base.value`.

**Why this matters more than a flaky test usually does.** It guards D-ART5 — that
orbit pruning returns the frozen `w*_c` — which is the decision letting the
campaign use the pruned engine at all. A guard that cries wolf under load is a
guard that gets ignored, and the day it fails for the real reason it will be
dismissed as "the busy-machine one". The claim itself is not at risk: it rests
on 7,013/7,013 identical words, 130,788 identical single-edit distances and
5,174 ladder pairs, plus the matrices job independently reproducing RQ1's
censoring census to the member id.

**Acceptance:** the test's verdict does not depend on machine load. Either the
comparison budget is removed from the pass criterion (compare whatever
completes, assert only on disagreement, and `pytest.skip` with a clear message
when too few complete — a skip is honest where a failure is not), or the
members are drawn from a pinned set known to complete well inside the budget so
the count is deterministic. Do **not** simply raise the budget: that trades one
wall-clock threshold for another.

**Out of scope here:** D-ART5 itself; the budget mechanism; the campaign's
censoring numbers, which are measurements rather than assertions and are
expected to drift.
