# T-M3e — Propagate the S2 outcomes into the competitor + session docs
**Declared:** 2026-07-19 11:37 CEST
**Status:** OPEN
**Depends on:** T-DQ3' (CLOSED); T-OPTa/T-OPTb (their outcomes are appended
when they land — the S2-verification content is writable now)
**Delegation:** orchestrator-only (session-close doc sweep; touches
`SESSIONS.md`-adjacent prose and PI-facing wording)
**Why out of scope:** the S2 verification pass and the T-DQ3' verdict changed
facts that several docs still state in v2 form; user-directed at the S2
session ("declare a task to update the documentation with the outcomes of
this iteration").
**Context to read first:**
- `docs/article/COMPETITORS_USAGE.md` — §2 and §8 still frame the competitor
  matrices as inputs to an HGED "head-to-head correlation study" and §4.2
  still calls NetLSD the "optional spectral fifth"; both retired at D-ART2.
- `docs/article/DEVELOPMENT/DECISIONS.md` — D-ART2 points 2 and 5 (one
  ours-only E1' figure; NetLSD full member) — the wording to align to.
- `docs/article/DEVELOPMENT/T-DQ/CLOSED/T-DQ3prime.md` — the S2 numbers the
  usage doc's reproducibility claims should reference.
- `scripts/verify_competitors.py` — the re-runnable verification harness to
  cite as the reproduction path.
- `.claude/rules/coding_rules.md` — always
**Description:** Bring the downstream competitor documentation in line with
the v3 scope and the S2 measurements: retire the head-to-head framing from
`COMPETITORS_USAGE.md` (§2, §4.2 role wording, §4.3 pointer, §8 example
reframed to the E1'-only role), reference `scripts/verify_competitors.py`
and the 2026-07-19 verification numbers as the reproducibility anchor, and
record the HyperCOT env-rebuild facts (true upstream commit `5045539`).
Append T-OPTa/T-OPTb outcomes to the affected docs when those tasks close.
**Acceptance:** `grep -n "head-to-head" docs/article/COMPETITORS_USAGE.md`
returns only E1'-scoped or historical-note usages; §4.2 names NetLSD a full
member; the usage doc points at `scripts/verify_competitors.py`; SESSIONS.md
S2 row ticked with orchestrator notes appended (orchestrator's own act).
**Out of scope here:** reasoning-doc rewrites (`PROPOSAL.md`,
`theoretical/*` — already updated at the T-DQ3' close); any source edits.
