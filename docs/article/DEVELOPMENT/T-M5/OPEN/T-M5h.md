# T-M5h — Propagate the S3 measured outcomes into the reasoning prose
**Declared:** 2026-07-19 16:51 CEST (orchestrator, S3 close — user-directed)
**Status:** OPEN
**Depends on:** T-M5f (DONE), T-M5g (DONE); independent of T-M5b–e
**Delegation:** agent
**Why out of scope:** S3 produced measured results that the reasoning docs do
not yet reflect; the workers' lanes forbade them from editing the shared prose
(`stability.md` was T-TBg's lane, `geometry.md` T-M5f's), and per the
CLAUDE.md §Doc split convention the measured-outcome prose must land in the
reasoning docs deliberately, not as a merge side-effect.
**Context to read first:**
- `docs/article/DEVELOPMENT/T-M5/CLOSED/T-M5g.md` — closing note: the
  full-run three-regime confrontation (5 confirmed, 2 FALSIFIED) + the
  ladder summary + the nauty-contrast IQR ratios
- `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/T-M5g/analysis/`
  — `g2_regime_confrontation.json`, `g2_contrast_{random,designs}.pdf`,
  `ladder/<cell>/ladder.pdf` (the rendered evidence)
- `docs/article/theoretical/stability.md` §4.2 — the three-regime coherence
  prediction (the falsification target the data partially hit)
- `docs/article/theoretical/geometry.md` §6 — the two dynamic invariants and
  what each profile licenses
- `docs/article/empirical/applications.md` §G2 — the measurement spec the
  results answer
- `CLAUDE.md` §Doc split ("Reasoning vs. tasks") — no task ids/dates in the
  reasoning prose
**Description:** Fold the S3 measured outcomes into the article reasoning
docs, keeping them free of process artifacts. (a) `stability.md` §4.2:
qualify the three-regime prediction with the measured outcome — confirmed on
sparse/medium/dense random corpora, Fano, and STS(9) (heavy-tail fraction
0.000 where unimodal was predicted), **falsified on the two near-symmetric
designs** (C13 orbit and GQ(2,2): predicted heavy-tailed, measured heavy-tail
0.000 with narrow IQR 2.0 and 8.0 under single arity-bounded Qin edits);
state the two candidate explanations (the arity-3 edit guard excludes
arity-diverse symmetry-breaking edits; the avalanche mechanism may require
accumulated or arity-changing edits rather than single ones) and what a
follow-up would test. (b) `geometry.md` §6: record that the sensitivity
profile licenses neighbourhood methods with the measured ours-vs-nauty
contrast (nauty IQR 2.5–9.5× ours on every regime including the falsified
designs) and that the ladder response is near-monotone (≈80% monotone
steps, mean d_I increment growing 3.2 → 11.7 with base size). (c)
`applications.md` §G2: replace the "to be measured" framing with the
measured-profile summary and point to the G2 figure set. (d) Check
`PROPOSAL.md` §2's invariant table needs no numeric edits (it names the
invariants only) — touch it only if a claim there is now false.
**Acceptance:** the three docs state the measured outcomes without task ids,
dates, or session references; the falsification is stated plainly (not
hedged away) with its candidate explanations; no reasoning claim remains
that the G2 data contradicts; the T-TBg acceptance grep stays clean over
`docs/article/{PROPOSAL.md,theoretical/*,empirical/*}`.
**Out of scope here:** re-running any measurement; editing `DEVELOPMENT/`
ledger content beyond this file; the E1' harvest (T-M5a part 2, S5); any
`src/` or `experiments/` change.
