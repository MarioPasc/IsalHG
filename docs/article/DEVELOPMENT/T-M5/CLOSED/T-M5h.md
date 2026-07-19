# T-M5h — Propagate the S3 measured outcomes into the reasoning prose
**Declared:** 2026-07-19 16:51 CEST (orchestrator, S3 close — user-directed)
**Status:** DONE
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

---

## Closing note

**Branch:** T-M5h

### What was done

Three prose docs updated; no code touched.

**`docs/article/theoretical/stability.md` §4.2 — measured outcome appended.**
After the three-regime prediction bullets and the falsifiability note, a new
"Measured outcome" paragraph states: 5 confirmed, 2 falsified. Confirmed
(heavy_tail_frac = 0.000 where unimodal predicted): sparse (IQR_ours = 2.0,
IQR_nauty = 11.0), medium (4.0 / 17.0), dense (5.25 / 11.0), Fano (5.0 / 20.0),
STS(9) (7.0 / 15.0). Falsified: cyclic C13 (IQR_ours = 2.0, IQR_nauty = 19.0)
and GQ(2,2) doily (IQR_ours = 8.0, IQR_nauty = 10.0), both predicted heavy-
tailed, both measured heavy_tail_frac = 0.000 under single arity-3 Qin edits.
Both candidate explanations stated (arity-3 guard; asymptotic-regime
requirement). Follow-up test specified (arity-diverse edits, larger designs).
Nauty contrast confirmed including on falsified designs (IQR ratio 1.25–9.5×
across all seven regimes).

**`docs/article/theoretical/geometry.md` §6 — measured-profile summary added.**
Status header date stripped (process artifact). After the existing Consumers
bullet, a "Measured profile" paragraph records: IQR_ours 2.0–8.0 tokens,
heavy_tail_frac = 0.000 throughout; falsification on C13/GQ(2,2) noted with
cross-reference to stability.md §4.2; nauty contrast confirmed (IQR_nauty
10.0–20.0, ratio 1.25–9.5×); ladder near-monotone (≈80% monotone steps, mean
increment 3.2 → 11.7 with base size, all six ladders globally increasing).

**`docs/article/empirical/applications.md` §G2 — replaced forward-looking text
with measured outcomes.** "Predictions... falsification target stated there" →
measured IQR_ours range + falsification record. "monotone near-linear response is
the smoothness evidence" → ≈80% monotone, 3.2 → 11.7 increment. "Expected:
avalanche-everywhere" → measured IQR_nauty 10.0–20.0, ratio 1.25–9.5×. All three
bullets now report measured outcomes and cite rendered figures.

### Premises verified

- Numbers sourced from `g2_regime_confrontation.json` directly, not from the
  prose summary in the closing note (which had preliminary n_edits counts
  inconsistent with the JSON). The IQR values in both sources agree; the JSON
  is authoritative for n_edits (all design fixtures: 150 each).
- Prose summary in the task description stated "2.5–9.5× ours on every regime
  including the falsified designs." The JSON shows GQ(2,2) ratio = 10.0/8.0 =
  1.25×, below 2.5. The article prose uses "1.25–9.5×" (JSON-exact range).
- `PROPOSAL.md` §2 invariant table checked: no measured claim contradicts the
  table. The table names invariants and licensees only, with no numeric
  predictions; it stands unchanged.

### T-TBg acceptance grep output

```
docs/article/PROPOSAL.md:3:**Status:** ACTIVE scope, v3 (2026-07-18 rescope). This document supersedes the
docs/article/PROPOSAL.md:128:**Pivot 2 — away from the HGED-proxy framing (2026-07-18, v3).** The v2 scope
docs/article/PROPOSAL.md:240:- OQ-B [resolved 2026-07-19 — no]. The real-anchor gate measurement: `w*_c`
docs/article/PROPOSAL.md:255:- OQ-F [resolved, v3; PI-ratified 2026-07-18]. Mutual information `I(HGED; d)`
docs/article/PROPOSAL.md:258:  `DEVELOPMENT/DECISIONS.md` (D-ART2).
docs/article/theoretical/stability.md:194:the paper's own HGED-BFS (`qin_hged`) computes the same metric and anchors
docs/article/theoretical/stability.md:317:See T-B2 of `stability/theorem_b_stability.tex`.
docs/article/theoretical/stability.md:323:footprint. See §T-B2 of `stability/theorem_b_stability.tex`.
docs/article/theoretical/stability.md:381:`pointer_run_amortization.tex` §T-B3 and `scripts/tb3_coherence_criterion.py`) — **not the string-equality regime
docs/article/theoretical/stability.md:491:engineering ledger (`docs/article/DEVELOPMENT/T-TA/` and
docs/article/theoretical/stability.md:492:`docs/article/DEVELOPMENT/T-TB/`).*
docs/article/theoretical/stability_reformulations.md:1:# Stability after T-TBb: value assessment and reformulation space
[... stability_reformulations.md: out of scope per task, unchanged]
docs/article/empirical/correlation.md:38:branch-and-bound, the oracle) and `qin_hged` (the paper's HGED-BFS, the
docs/article/empirical/correlation.md:70:the paper's HGED-BFS and exhaustive enumeration on small pairs):*
docs/article/empirical/correlation.md:72:  Riesen–Bunke-seeded incumbents, not the paper's HGED-BFS. Measured
docs/article/empirical/correlation.md:73:  justification: HGED-BFS's Definition-5 node bound is identically zero on
docs/article/empirical/correlation.md:86:- (A5) HGED-BFS engineering (bitmask incidence sets, O(1)-incremental Ψ,
```

All hits are pre-existing legitimate references (same classification as the
T-TBg baseline): PROPOSAL.md not edited (out of scope); stability.md hits are
HGED-BFS algorithm name and proof-section labels T-B2/T-B3 in external .tex
files and ledger path references; stability_reformulations.md out of scope;
correlation.md hits are all HGED-BFS algorithm name. geometry.md line 3 date
was **removed** by this edit — no longer flagged. No new hits introduced.
