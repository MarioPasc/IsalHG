# T-KBt — two RQ6 tests fail on a stale `CollectionContext` helper
**Declared:** 2026-09-10 21:23 CEST
**Status:** OPEN
**Delegation:** agent
**Why out of scope:** found while closing T-KBo in the same test file. T-KBo's
scope is `Reach1Index`; these two failures predate it and are unrelated to
`reach'`.

**Context to read first:**
- `tests/experiments_tkde/test_rq36_smoke.py::TestModelIsNotSharedAcrossUnits::_context`
  — the helper that builds a `CollectionContext` positionally
- `experiments/tkde/rq6.py::CollectionContext` — gained `ow_words`,
  `ow_roots` and `k` when the ordered-walk model (`MODEL_OW`) landed
- `.claude/rules/coding_rules.md` §4 — testing discipline

**Description:** two tests fail with

```
TypeError: CollectionContext.__init__() missing 3 required positional
arguments: 'ow_words', 'ow_roots', and 'k'
```

- `TestUnitEnumeration::test_rq6_units_are_unique`
- `TestModelIsNotSharedAcrossUnits::test_a_used_model_is_not_reachable_from_the_context`

The dataclass grew three fields for the ordered-walk arm and the test helper was
not updated. Verified 2026-09-10 that both fail identically with `rq6.py`
reverted to HEAD, so they are **not** caused by T-KBo.

**Why it matters.** The second test is not cosmetic: it guards the
`TokenNGram` memo-cache leak that killed job 2213221 at 20.4 GB RSS. It has
been asserting nothing since the ordered-walk fields landed, so the regression it
exists to catch is currently unguarded.

**Acceptance:** the helper supplies `ow_words`, `ow_roots` and `k` derived
from the fixture members (`rq6._ow_word` / `rq6._ow_tokens` and
`required_k`), both tests pass, and the memo-cache assertion is confirmed to
still fail when the model is deliberately shared across units — otherwise the
guard is restored in name only.

**Out of scope here:** `Reach1Index` and `reach'` (T-KBo); the other six
known suite failures.
