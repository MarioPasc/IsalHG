# T-TBf — Reconcile the unmerged T-TBb closure into the working branch
**Declared:** 2026-07-17 20:30 CEST
**Status:** OPEN
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
