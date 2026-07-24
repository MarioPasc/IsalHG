# T-M8f — Fold the S7 measured numbers into the reasoning prose
**Declared:** 2026-07-24 12:31 CEST
**Status:** DONE
**Depends on:** T-M7d (A1–A3/G1/bits tables with CIs + Holm-corrected tests),
T-M7q (G2/A4 on the corrected corpus) — both merged, caches final.
**Origin:** 2026-07-24, S7 re-run session. Gap found while scheduling: every
S7 measurement task disclaims the prose fold in its own *Out of scope* —
T-M7d ("a follow-up doc pass owns it; only the artifact tables/curves are
produced here"), T-M7e §4.2, T-M7f `geometry.md`, T-M7g `DATA.md` — and the
follow-up task was never filed. As a result the S7 exit criteria could all be
met while `empirical/applications.md` and `theoretical/geometry.md` still cite
the superseded S4/S5 numbers ("planted corpus, N = 240, twenty families",
`ν = 0.250`, `D̂ = 26`, stress-1 = 0.062, hubness 1.75) — measurements taken
on a corpus built by the pre-T-M7o generator, whose arity cap made the corpus
arity-3 in effect. This task closes the loop.
**Context to read first:**
- `docs/article/DEVELOPMENT/HANDOFF_S7_RERUN.md` §3 — the two
  claim-constraining findings and the PI-agreed framing
- `docs/article/PROPOSAL.md` §0 (the narrative spine), §2 (the no-orphan-geometry
  rule), §3 (the application/licence table)
- the T-M7d and T-M7q closing notes + their emitted artifact tables/curves
- `docs/article/empirical/applications.md`, `docs/article/theoretical/geometry.md`
  — the two documents rewritten here
- `CLAUDE.md` §"Reasoning vs. tasks" — process artifacts (`T-*`, `D-*`, dates,
  "executed/adopted") **must not** enter the reasoning prose
- the `humanizer` skill — the prose is article text, not a task report
**Description:** Replace the superseded measured passages in
`empirical/applications.md` (G1/G2 profiles, the geometry table, A1–A4 measured
blocks) and `theoretical/geometry.md` (the invariant table and its reading)
with the S7 numbers, each carrying its 95% CI and, for every
competitor-vs-IsalHG claim, its Holm-corrected p and effect size. Three
framing constraints, all PI-agreed, all non-negotiable:
1. **A2/A3 honestly.** The naive degree-sequence baseline beats IsalHG on ARI
   and kNN AUC, and NetLSD also beats it; the design families separate on
   degree alone, and a degree-controlled corpus was proven impossible (T-M7p).
   State it plainly. Do not arrange the tables to obscure it, and do not claim
   A2/A3 task dominance.
2. **Usefulness leads on A4 + the capability matrix** — decodable, navigable
   intermediates, one metric across four tasks, a capability no competitor has.
3. **The scalability envelope is reported, not hidden:** `w*_c` is feasible at
   k = 3 up to n ≈ 24 and at k = 5 only at n = 8; k = 7 and k = 10 are measured
   infeasible, so the advertised arity cap of 10 is not reachable at any tested
   n.
The no-orphan-geometry rule still binds: every invariant that survives into the
prose names the application licence or competitor contrast that consumes it.
The N = 240 numbers are demoted to the superseded record on the drive (the
N = 60 → 240 precedent at T-M5l), not deleted.
**Acceptance:** no measured passage in either document cites the N = 240 /
twenty-family corpus as current; every headline number traces to a T-M7d or
T-M7q artifact and carries its CI; every competitor comparison carries a
Holm-corrected p and an effect size; the three framing constraints above are
visibly satisfied in the text; the arity/feasibility frontier appears as a
stated limit; no `T-*`/`D-*` ids, dates, or orchestration vocabulary appear in
either document; `docs/article/DEVELOPMENT/README.md` critical-path paragraph
updated to the S7 headline numbers.
**Carried in from T-M8b (2026-07-24).** The §Usefulness framing section added
at T-M8b was authored on a fork predating the T-M7q merge, so any *number* it
contains predates the corrected corpus. One such claim is in the text — the
single-edit sensitivity "IQR 2–8 tokens" attributed to G2. Re-derive it from
the merged T-M7q G2 artifacts and correct or remove it; then sweep that section
for any other numeric claim and check each against a current artifact. The
qualitative content (three axes; IsalHG second to HPD-JSD on A2/A3; the
degree-sequence floor; the completeness ∧ decodability ∧ navigability
intersection; HPD's failure of the triangle inequality) is capability-based and
stands.

**Out of scope here:** producing any new measurement (this task only reads
artifacts); the capability-matrix figure itself (T-M8b); the reproducibility
artifact (T-M8d); `theoretical/stability.md` §4.2's regime prose (folded from
T-M7q's re-scored confrontation — may be done here if T-M7q's numbers are
final, otherwise filed separately).

---

**Closing note (2026-07-24).**

All four acceptance criteria satisfied:

1. **No N=240/twenty-family citation as current.** `grep -n "N = 240\|twenty families\|twenty-family\|planted corpus" applications.md` → 0 matches. `geometry.md` retains one reference to "a different planted corpus (20 random families)" as historical context — not cited as current.

2. **Headline numbers trace to T-M7d/T-M7q artifacts with 95% CI.** Every table entry in §A1 carries `[CI_lo, CI_hi]` from percentile bootstrap over 27 seeds. A2/A3 blocks carry both the mean [CI] and the Holm-corrected p + effect size r.

3. **Framing constraints satisfied:**
   - A2/A3 honestly: "degree-seq leads A2-ARI 0.451, NetLSD 0.479, IsalHG 0.285; Holm p < 10⁻⁷; HPD ns" — plainly stated in §A2 and §Usefulness.
   - Usefulness leads on A4: decodability categorical result (8/8 valid), WL recovery 0%, contrast central.
   - Scalability envelope: k=3 n≤24 (low ρ), k=5 n=8 only, k=7/10 infeasible; 3-cell exclusion; arity-axis shortfall (k∈{3,5}). Stated in §G1 and §Runtime.

4. **No T-*/D-* ids or orchestration vocabulary in either article doc** (grep confirmed 0 matches).

5. **IQR corrected:** "IQR 2–8 tokens" → "IQR 3–9 tokens, median 5" (1700 edits, T-M7q catalog_all).

6. **`docs/article/DEVELOPMENT/README.md` critical-path paragraph** updated with S7 measured headlines (ν=0.097, D̂=17, stress=0.046; degree_seq/NetLSD lead A2/A3; WL hubness 2.37 → AUC 0.495 chance; G2 IQR 3–9; scalability frontier).

**Checks:** pytest 1499 passed / 9 skipped / 0 failed · ruff 3 (pre-existing) · mypy 21 (pre-existing). No new failures from docs changes.
