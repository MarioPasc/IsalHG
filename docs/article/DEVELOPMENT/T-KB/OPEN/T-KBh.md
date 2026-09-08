# T-KBh — the analyzers pool launch tags they were built to separate

**Status:** OPEN · declared 2026-09-08 13:02 CEST by the Isal-refinement
orchestrator, found while executing T-KBe (harvest → merge → table).

## What

`slurm/tkde/README.md` §"Row files carry a run tag" fixes the convention: a row
file is `rows_<table>__<8hex>-<unit>.csv`, the `8hex` prefix is
`experiments.tkde.rq1.run_tag(config)` — a hash of the parameters that decide
*what* a unit measures — and it exists because "two runs whose unit ids coincide
but whose parameters differ are indistinguishable on disk" without it.

`load_table` honours half of that contract: it skips **untagged** files and any
path with a `_smoke` component. It does **not** partition by tag. Every tagged
file in an experiment directory is concatenated, so two launches with different
parameters are pooled into one table, and the arms they share are counted once
per launch.

Measured on the cluster (2026-09-08), `RQ1_addressing/addressing`:

| launch tag | job | rows written | schema | arms |
|---|---|---|---|---|
| `c3fb21de` | 2215137 (submitted 09-05 23:17) | 09-06 13:50 → 09-07 04:08 | no `d_instr`/`n_instr`/`aut_bucket` | fact + certificate arms |
| `47c8a42c` | 2247394 + sweep 2247395 (submitted 09-07 10:05) | 09-07 11:30 → | full | + the Isal arms |

Concatenated: **904,442 duplicated `(unit, arm)` rows of 2,506,837**. Nothing in
`analyze_rq1.py`, `io.py` or (before `314b4a3`) `merge_rq1_experiments.py`
deduplicated, and `m1_paired_vs_cert_rows` pivots with `aggfunc="first"`, so a
duplicate is silently resolved rather than raised.

**No published number is affected.** The frozen drive record
`results/IEEETKDE/RQ1_addressing/addressing/tables.md` was generated
2026-09-06T11:59, before the second launch existed, and the cluster directory
carries no analyzer output at all (checked 2026-09-08). T-KBe's table is built
through `--only-tags`, so it is clean by construction.

## Why it still needs fixing

The guard is currently in the merge tool only. Anyone running
`python -m experiments.tkde.analyze_rq1 --root <root>` against an experiment
directory that accumulated two launches gets a pooled table with no warning —
and the RQ2 and RQ7 analyzers share `load_table`.

## Proposed shape

1. `load_table` reports the tags it found; the analyzer refuses (or warns
   loudly and records in `stats.json`) when an experiment directory carries
   more than one tag without an explicit `--only-tags`/`--run-tag` selection.
2. Reuse the duplicate audit of `merge_rq1_experiments.audit_duplicates` as the
   general assertion rather than duplicating the logic.
3. Same treatment for `analyze_rq2.py` and `analyze_rq7.py`, which share the
   loader; RQ3/RQ4/RQ5 exclude by `_smoke` path only and need the same audit.

## Acceptance

A unit test in which one experiment directory holds two tags: the analyzer
refuses without a selection, and produces the single-launch table with one.
`experiments/tkde/analyze_rq1.py`'s hardcoded `EXPERIMENT` (handoff §7) can be
retired in the same pass.
