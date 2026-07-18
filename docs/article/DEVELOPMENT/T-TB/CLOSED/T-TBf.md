# T-TBf — Reconcile the unmerged T-TBb closure into the working branch
**Declared:** 2026-07-17 20:30 CEST
**Status:** DONE (2026-07-18, orchestrator — closed via the S1 reconciliation merge)
**Depends on:** —
**Delegation:** orchestrator-only
**Why out of scope:** Surfaced during the 2026-07-17 review; the T-TBb closure lives in a commit not present on the working branch, so on `perf/canonical-complete-orbit-pruning` the ledger is wrong (`T-TBb.md` reads OPEN) and a worker could redo closed work. Housekeeping, not article content.
**Context to read first:**
- commit `e6b0af7` ("docs(T-TBb): close pointer-run amortization — generic (iv)-(v) refuted") — the ledger move + `scripts/probe_pointer_runs.py` + `scripts/tb3_coherence_criterion.py` + `tests/unit/core/test_no_w_tokens.py`; also `a362657` (W-token test) may be the same line
- branch `perf/canonical-complete-orbit-pruning` (current HEAD `c8b6a57`) — where `T-TBb.md` still sits under `OPEN/`
- `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/stability/STABILITY_EXPLAINED.md` §7 — references task `T-TAi` (stabiliser-orbit pruning) that is absent from the ledger on this branch (likely on the same unmerged line)
- `.claude/rules/coding_rules.md` — always
**Description:** Cherry-pick or merge `e6b0af7` (and `a362657` if separate, and the `T-TAi` task file if it exists on the source branch) into the working branch so `T-TBb.md` reads CLOSED, the two probe scripts and the no-W test are present, and the `STABILITY_EXPLAINED.md` `T-TAi` reference resolves. Confirm no conflict with this branch's `perf/` C++ work.
**Acceptance:** `T-TBb.md` filed under `CLOSED/` on the working branch; `scripts/probe_pointer_runs.py`, `scripts/tb3_coherence_criterion.py`, `tests/unit/core/test_no_w_tokens.py` present; `test-runner` green; the `T-TAi` task present under the ledger or its `STABILITY_EXPLAINED.md` reference removed.
**Out of scope here:** any new proof or code; re-running the probe; the orbit-pruning implementation itself (that is T-TAi's own work).

---
**Closing note (orchestrator, 2026-07-18).** Resolved by a full merge of
`origin/main` (commit `65314ec`) rather than the anticipated cherry-pick:
the unmerged line turned out to hold not just the T-TBb closure but the whole
pre-rescope execution wave (T-M2c, T-M4, T-M4', T-M3a–d, T-M5a-v2) — surfaced
to the human, who chose the full reconciliation. Acceptance, clause by clause:
- `T-TBb.md` filed under `CLOSED/` on the working branch (`main`) ✔
- `scripts/probe_pointer_runs.py` (9.6K), `scripts/tb3_coherence_criterion.py`
  (18.0K), `tests/unit/core/test_no_w_tokens.py` (3.0K) all present ✔
- Suite green on the merged tree: **877 passed, 18 skipped, 13 deselected**
  (`pytest tests/unit tests/property tests/integration -m "not slow"
  --hypothesis-seed=0`); ruff 3 / mypy 21 — both identical to the pre-merge
  baseline ✔ (no C++ conflict: the duplicated perf commits were
  content-identical, `_native/` auto-merged with zero diff)
- `T-TAi.md` present under `T-TA/OPEN/` ✔ (the `STABILITY_EXPLAINED.md`
  reference resolves)
