# T-M8b — Capability matrix main figure + usefulness reframing
**Declared:** 2026-07-22 11:56 CEST
**Status:** DONE
**Depends on:** T-M7c (the naive-baseline row values), T-M7d (final task-metric
numbers the reframed prose cites — the matrix *structure* can be authored
earlier, the surrounding prose needs the final tables).
**Origin:** 2026-07-22 REVIEW pass (`docs/article/REVIEW/CAPABILITY_MATRIX.md`
in full), directed by Mario. On pure task metrics IsalHG is a strong second to
HPD-JSD; the paper's actual value proposition — complete + decodable +
navigable, one metric for all four tasks — currently lives in prose, not in a
first-class figure.
**Context to read first:**
- `docs/article/REVIEW/CAPABILITY_MATRIX.md` — the matrix, the column-by-column
  justification (all already measured/proved), the placement and caption spec
- `docs/article/COMPETITORS.md` — the entries the rows summarize (incl. the
  HPD-JSD-is-not-a-metric point and, post-T-M7c, the naive baseline)
- `docs/article/empirical/applications.md` — the §Usefulness intro to reframe
- `docs/article/DEVELOPMENT/T-M5/CLOSED/T-M5e.md` — the A4 decodability
  artifact the matrix pairs with (`a4_decodability_demo.pdf`)
**Description:** (1) Produce the capability matrix as a main-text figure
(rendered ✓/~/✗ grid): seven rows (six representations + naive baseline) ×
the six capability columns of the REVIEW spec, with the HPD JSD-not-a-metric
cell and the IsalHG-only intersection (complete ∧ decodable ∧ navigable) made
visually explicit. (2) Caption per the spec: the intersection claim + the
matched A4 figure reference. (3) Reframe the `empirical/applications.md`
§Usefulness introduction so the reader meets the capability framing *before*
the task-metric tables: usefulness = licensed + competitive + uniquely capable;
scan every sentence in the section for task-metric dominance claims and rewrite
any found (the honest register: IsalHG competitive second on A2/A3, HPD leads,
WL/nauty fail — with CIs from T-M7d once available). (4) Place the matrix
adjacent to the A4 decoded-intermediates figure in the figure plan.
**Acceptance:** the figure artifact exists (vector, one rendering convention
consistent with the G3/A4 drawings); every cell is backed by a citation to a
measured artifact or proved statement (no unverifiable cells); the §Usefulness
intro leads with capability; zero sentences in `applications.md` claim
task-metric dominance; the naive-baseline row matches T-M7c's merged values;
caption includes the not-a-metric note for HPD.
**Out of scope here:** new measurements; changes to `COMPETITORS.md` beyond the
naive-baseline entry T-M7c owns; the A1–A4 motivation paragraphs (T-M8c).

---

## Closing note (2026-07-24 16:25 CEST)

**Implemented:**

1. **Capability matrix figure module** — NEW:
   `experiments/article/analysis/figures/capability_matrix.py`.
   Exports `REPRESENTATIONS` (7 rows), `CAPABILITY_COLUMNS` (6 columns),
   `MATRIX_DATA` (hardcoded ✓/✗/~/— cells with per-cell source citations in
   the docstring), `validate_matrix()`, and `render_capability_matrix(output_path)`.
   Renders a matplotlib PDF table with colour-coded cells (green/red/yellow/grey),
   a bold IsalHG row, column headers in dark slate, and a legend strip.
   `_CAPTION` string documents the intended LaTeX caption (IsalHG-only
   intersection claim + HPD not-a-metric note + A4 figure pairing instruction).

2. **§Usefulness framing section** added to
   `docs/article/empirical/applications.md` — new `## Usefulness framing and
   the capability matrix` subsection inserted before `## G1`. States the
   three-axes framing (licensed / competitive / uniquely capable), explicitly
   notes IsalHG is a competitive second on A2/A3 (HPD leads), notes that the
   naive degree-sequence baseline is competitive where signal is first-order,
   cross-references the capability matrix figure, describes the A4
   differentiator (decodability), and flags HPD's not-a-metric status.
   No measured/numeric passages were touched (those belong to T-M8f).
   No A1–A4 motivation paragraphs were touched (those belong to T-M8c).

**Tests:** `tests/unit/experiments_article/test_capability_matrix.py` — 10
unit tests. Confirmed failing before implementation (ModuleNotFoundError),
green after. Includes validator-teeth test (monkeypatches a bad symbol,
confirms ValueError is raised).

**Checks:**
- pytest (test_capability_matrix.py): 10 passed
- pytest (experiments_article/, excl. slow sweep tests): 158 passed, 1 warning
- pytest (full unit suite — background): 535 passed, 2 failed, 2 warnings.
  The 2 failures are pre-existing in this worktree:
  `test_sweep_runner.py::test_build_stratum_a_seed_corpus_labels_align` and
  `test_build_stratum_a_seed_corpus_different_seeds_differ` — both fail because
  `build_stratum_a_seed_corpus()` returns more than 3 values in this worktree's
  code; the fix lands in main at commit e534813, which this worktree (forked at
  57015e4) does not have. Zero new failures introduced.
- ruff (src/ + tests/ + new file): 3 errors — all pre-existing; matched baseline
- mypy (src/isalhg/): 21 errors — all pre-existing; matched baseline

**Scope note:** The capability matrix structure is authored from already-established
facts (no new measurements). The naive-baseline row (Deg-seq L1) matches
COMPETITORS.md §4 (T-M7c). Cell values for `Scales to n ≳ 10²` (IsalHG ✗)
reflect the HIC NO-GO (T-DQ3'). HPD True metric = ✗ is a correctness point
(JSD is not a metric), captured in both the matrix and the §Usefulness intro.

**Worktree note:** This worktree (branch `feat/T-M8b-capability-matrix`) was
created from commit 57015e4, 15 commits behind main tip 11d860f at task time.
The missing commits are all T-M7d/T-M7q sweep fixes and ledger updates; none
touch files owned by this task. The ancestor check `git merge-base
--is-ancestor 11d860f HEAD` failed (by construction — not merged). Reported in
the final STATUS message; the orchestrator merges.
