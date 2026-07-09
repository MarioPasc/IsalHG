# docs

Specs, paper scopes, and development notes for IsalHG.

## Layout

- `article/` — **active** journal-article scope (metric-space paper, target
  *Information Sciences*).
  - `PROPOSAL.md` — thesis, central experiment, applications, open questions.
  - `DATA.md` — data plan (HGED-correlation corpus, planted-family corpus).
  - `COMPETITORS.md` — competing representations and the fairness question.
  - `CODE_DESIGN.md` — `src/isalhg` refactor + `metric_space/` additions.
  - `RELATED_WORK.md` — verified bibliography (theory + competitors, with code).
  - `DEVELOPMENT/` — the live **task ledger**: one file per task under
    `<scope>/{OPEN,IN-PROGRESS,BLOCKED,CLOSED}/`, hub at `DEVELOPMENT/README.md`
    (use `task-reader`/`task-handoff`).
  - `theoretical/` — completeness → metric → **stability** theorem breakdown.
  - `empirical/` — controlled validation of the theorem, then applications.
- `preprint/` — the iso-benchmark preprint's methodology: `PROPOSAL.md`,
  `DATA.md`, `PREPRINT.md`. Superseded as the *next paper's* scope but retained
  as the preprint record.
- `engineering/` — the current code's spec, authoritative for the code as built:
  `CODE_DESIGN.md` (code layout), `DEVELOPMENT.md` (iso-benchmark dev log),
  `ALGORITHMS.md`, `CPP_OPTIMIZATION_LOG.md`, `CPP_SPEEDUP.md`.
- `research/` — research handoffs (canonical backtracking, benchmarks).
- `references/` — external PDFs (dreadnaut manual, expressivity paper).
- `isalhg_idea.pdf` — the PI's seed proposal (kept at `docs/` root).

## Which doc for which task

- Writing the metric-space paper or its code → `article/` (start at
  `article/PROPOSAL.md`; pick up work from `article/DEVELOPMENT/README.md`).
- Understanding the code as built → `engineering/CODE_DESIGN.md`.
- The preprint's validation methodology → `preprint/PROPOSAL.md`.
