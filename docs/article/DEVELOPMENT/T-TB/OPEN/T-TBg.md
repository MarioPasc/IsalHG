# T-TBg — Disentangle article reasoning from engineering tracking in the legacy prose
**Declared:** 2026-07-17 20:30 CEST
**Status:** OPEN
**Delegation:** agent
**Note (D-ART2, 2026-07-18):** the v3 rewrite touched most reasoning docs and
wrote its *new* prose clean, but deliberately left the legacy inline tracking
(`stability.md` §6 checklist, `correlation.md` deviation-ledger refs, v2/v3
and D-* mentions in status headers) for this task. The acceptance grep below
still applies; run it after the v3 docs settle.
**Why out of scope:** Surfaced 2026-07-17 (Mario's disentanglement directive). The
D-ART1 reframe de-tagged the *newly written* prose, but the legacy article docs
still weave engineering tracking (task ids, `D-*` codes, dates, "orchestrator
post-audit", proof-effort checklists) into what should be article-reasoning prose.
The convention is now in `CLAUDE.md` (§Doc split, "Reasoning vs. tasks"); this task
applies it to the pre-existing docs.
**Context to read first:**
- `CLAUDE.md` §Doc split ("Reasoning vs. tasks") — the convention to enforce
- `docs/article/theoretical/stability.md` §6 ("Proof-effort checklist" T-B0..T-B5) + the "orchestrator post-audit" notes — the biggest offender: engineering/tracking woven into a reasoning doc
- `docs/article/empirical/correlation.md` §"Deviation ledger" — carries `T-M2a`/`OD4`/date refs inside reasoning prose
- `docs/article/DEVELOPMENT/T-TB/CLOSED/T-TB.md` — where the proof-tracking checklist content should live
- `.claude/rules/coding_rules.md` — always
**Description:** Move the proof-effort checklist (T-B0..T-B5 status) and the audit/timeline notes out of `stability.md` into the DEVELOPMENT/T-TB ledger, leaving `stability.md` as theorem statements + reasoning + honest status (proved / conditional / sketch) with no task-id or date tracking. Do the same light pass over `correlation.md` and any other `theoretical/`+`empirical/` doc: keep scientific-object references (Theorem A/B, `w*_c`, the mechanisms, cited papers), strip process artifacts (`T-*`, `D-*` inline tags, timestamps, "orchestrator/author-adopted"). Preserve every scientific fact; only relocate the tracking.
**Acceptance:** `grep -nE 'T-[A-Z0-9]|D-[A-Z0-9]|orchestrator|author-adopted|20[0-9]{2}-[0-9]{2}-[0-9]{2}'` over `docs/article/{PROPOSAL.md,theoretical/*,empirical/*}` returns only legitimate scientific cross-references (none of the stripped categories); the relocated proof-status content is present in `DEVELOPMENT/T-TB/`; no scientific claim lost (diff reviewed).
**Out of scope here:** the proofs themselves (external `.tex` volume, untouched); the ledger files under `DEVELOPMENT/` (they *keep* their tracking — that is their job); `stability_reformulations.md` (analysis doc, may keep light task pointers).
