# T-KBs — a results column's dtype depends on whether any unit was censored
**Declared:** 2026-09-10 21:01 CEST
**Status:** OPEN
**Delegation:** agent
**Why out of scope:** found while applying the pre-registered winner_origin check
under T-KBf. It is a defect in how rows are written, not in the RQ3 measurement,
and it silently corrupts *readers* rather than results.

**Context to read first:**
- `experiments/tkde/rq3.py` — where the rows frame is assembled and written
- `docs/article/DEVELOPMENT/T-KB/IN-PROGRESS/T-KBf.md` §"RQ3 consensus 2276107"
  — the measurement that exposed it, and the four misreads it caused
- `scripts/diagnostics/rq3_consensus_forensics.py::_num` — the coercion that
  works around it, and the docstring stating why it exists
- `.claude/rules/coding_rules.md` §5.2 — idempotent runs / result contracts

**Description:** the same column is written with different dtypes in different
corpora of the same experiment, decided by whether any unit in that corpus was
wall-clock censored.

| column | Corpus A (rows_variants.csv) | Corpus B (rows_natural.csv) |
|---|---|---|
| `exact_recovery` | `'0'` / `'1'` | `'0.0'` / `'1.0'` |
| `censored` | `'0'` only | `'0'` / `'1'` |
| `winner_connected` | `'1.0'` / blank | `'1.0'` / blank |

Mechanism: Corpus B has 7 censored units whose `exact_recovery` is blank, so
pandas infers `float64` for the whole column; Corpus A censors nothing, so the
column stays `int64`. Censoring is a function of node load and wall-clock, so
**the schema of the output is not stable across runs of the same code** — the
same corpus can change dtype between submissions.

**Why this matters more than a formatting nit.** Any reader written and validated
against one corpus is silently wrong on the other, and wrong by *matching
nothing* rather than by erroring. It produced four misreads in one session, one
of which was reported as a scientific result ("Corpus B recovery collapsed to
0.0000") before being caught. `winner_connected` shows the same trap already
fires within a single corpus.

**Acceptance:** every boolean/indicator column has one declared dtype,
independent of censoring — either write a sentinel for censored units instead of
a blank, or cast explicitly at write time and declare the schema. A test writes
two frames, one with a censored unit and one without, and asserts the serialised
values of `exact_recovery`, `censored` and `winner_connected` are identical in
form across both. Prefer fixing at the writer over coercing at every reader; the
readers already on disk (`rq3_consensus_forensics.py`, the analyzers) keep their
coercion either way, because rows already written under the old behaviour stay
on the drive and must remain readable.

**Out of scope here:** RQ3's measurements, which are unaffected — the values are
correct in both corpora and only their spelling differs; the censoring mechanism
itself; T-KBn's stale-row skip.

---

## Extension (2026-09-10): the guard belongs in the analyzers, not only the diagnostics

Raised by `[IsalHG-Fable]` and folded here rather than opened as a new task,
because it is the same fix one layer up.

`scripts/diagnostics/rowsio.py` now makes the row-reading rules structural for
**diagnostics** — `num()` coerces instead of string-comparing, `key_by()` raises
on key collision instead of dropping by last-wins, `load_rows()` announces the
row count consumed, `expect_rows()` fails when it is not the expected one
(19 tests, `tests/experiments_tkde/test_rowsio_guards.py`).

**But one of the two silent failures lived in an *analyzer*.** The `fillna(0)`
that counted a blank as a measured failure was
`analyze_rq6.completion_table`, and the analyzers are what write `tables.md`,
which is what the prose folds from. So the guards currently protect the ad-hoc
scripts and **not** the pipeline that produces publishable numbers.

The pandas path is less exposed to the collision mode — a `groupby` aggregates
rather than overwriting — but fully exposed to the other two, **both of which
have now fired in this campaign**:

1. a filter that silently matches nothing (the `== "1"` against `'1.0'`);
2. a rate whose denominator is `len(group)` rather than the count of rows where
   the quantity exists (`completion_table`, fixed).

**Surveyed 2026-09-10.** Several analyzer tables already carry their
denominators — `analyze_rq7` reports `n_instances`, `n_members`, `n_reps`,
`n_censored`, `n_skipped`; `analyze_rq6.validity_table` reports `n_seeds` and
sums `n_samples`/`n_valid`/`n_rejected` explicitly. So the convention exists and
is followed unevenly rather than absent, which is the cheap case to finish.

**Acceptance (extension):** every analyzer table announces the number of rows it
consumed and the denominator of every rate it prints, and **fails** when either
differs from what the join manifest says it should be. The manifest already
carries the expected unit counts, so the expectation exists and is simply not
being asserted against — one assertion per table. A test feeds an analyzer a
frame with a deliberately missing unit and asserts the table refuses to emit
rather than emitting a rate over the survivors.

That is the difference between a wrong number being caught by whoever
re-derives it by hand and being caught by the run that produced it.
