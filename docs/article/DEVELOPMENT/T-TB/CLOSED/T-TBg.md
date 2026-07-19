# T-TBg — Disentangle article reasoning from engineering tracking in the legacy prose
**Declared:** 2026-07-17 20:30 CEST
**Status:** DONE
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

---

**Closing note:**

Files edited:
- `docs/article/theoretical/stability.md` — removed §6 "Proof-effort checklist" (T-A through T-TBb entries, ~90 lines); replaced with a two-line pointer to the engineering ledger. Stripped inline task IDs, decision codes, timestamps, and "orchestrator post-audit" references from §1–§4 prose. Proof-section labels (T-B2, §T-B2, §T-B3) inside citations of `theorem_b_stability.tex` / `pointer_run_amortization.tex` are retained as scientific cross-references.
- `docs/article/theoretical/README.md` — removed "v3 rescope 2026-07-18" from status header.
- `docs/article/empirical/correlation.md` — removed "v3 rescope 2026-07-18" from status header; removed "PI decision 2026-07-08" from the HGED definition parenthetical.
- `docs/article/empirical/applications.md` — removed "v3 rescope 2026-07-18" from status header; removed "the T-DQ3' measurement" task-ref from the scale decision note; removed "(T-M0c)" from the STS(13) timing sentence; replaced "gated by T-DQ3' — `../DATA.md`" with "`../DATA.md` §2".
- `docs/article/empirical/README.md` — removed "v3 rescope 2026-07-18" from status header.
- `docs/article/DEVELOPMENT/T-TB/CLOSED/T-TB.md` — appended v3 rescope addendum for T-B5 (destination: T-M5g geometry pillar, not T-M5a density sweep; no separate T-B5 task needed).

Acceptance grep output:

```
docs/article/PROPOSAL.md:3: (v3 rescope 2026-07-18)
docs/article/PROPOSAL.md:128: (2026-07-18, v3)
docs/article/PROPOSAL.md:240: (2026-07-19 — no)
docs/article/PROPOSAL.md:255: (PI-ratified 2026-07-18)
docs/article/PROPOSAL.md:258: (D-ART2)
docs/article/theoretical/stability.md:194: HGED-BFS
docs/article/theoretical/stability.md:317: T-B2 of theorem_b_stability.tex
docs/article/theoretical/stability.md:323: §T-B2 of theorem_b_stability.tex
docs/article/theoretical/stability.md:381: pointer_run_amortization.tex §T-B3
docs/article/theoretical/stability.md:461-462: DEVELOPMENT/T-TA/ and T-TB/ (ledger pointer)
docs/article/theoretical/geometry.md:3: (v3 rescope 2026-07-18) — not edited (owned by another agent)
docs/article/theoretical/stability_reformulations.md: multiple — out of scope per task
docs/article/empirical/correlation.md:38,70,72,73,86: HGED-BFS (algorithm name)
```

Legitimacy classification:

1. **PROPOSAL.md (5 hits):** Out-of-scope file (not editable per task). Expected.
2. **stability.md line 194:** `HGED-BFS` — scientific algorithm name. Grep false-positive via `D-B` substring.
3. **stability.md lines 317, 323:** `T-B2` inside citation of `stability/theorem_b_stability.tex` — section label in the external proof document, scientific cross-reference.
4. **stability.md line 381:** `§T-B3` in citation of `pointer_run_amortization.tex` — proof section label, same justification.
5. **stability.md lines 461–462:** `T-TA/` and `T-TB/` as directory paths in the ledger-pointer footnote. These are path references that redirect readers to the engineering ledger, replacing the deleted checklist.
6. **geometry.md line 3:** Out-of-scope file. Expected.
7. **stability_reformulations.md:** Explicitly out of scope. Expected.
8. **correlation.md lines 38, 70, 72, 73, 86:** `HGED-BFS` — algorithm name, grep false positive.

No scientific claim lost. §6 checklist content is preserved in T-TB/CLOSED/T-TB.md. No code touched; pytest/ruff/mypy not applicable.
