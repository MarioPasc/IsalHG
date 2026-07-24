# T-M7t — Paired tests never ran at S=27: aggregate Wilcoxon + Holm + BCa from the harvested seed metrics
**Declared:** 2026-07-24 21:01 CEST
**Status:** OPEN
**Depends on:** T-M7d (harness — CLOSED), T-M7s (harvest — CLOSED). No new
compute: everything needed is already on disk.
**Origin:** 2026-07-24, found by the orchestrator while verifying the T-M8f
prose fold. **The S=27 run produced no paired tests at all.** All 11 stats files
under `results/T-M7d/stats/` (local and on Picasso) carry populated `cis` and an
**empty `wilcoxon` dict** — 66 CI entries, 0 Wilcoxon entries — and
`grep -rl "p_holm\|holm"` over the whole results tree returns nothing.
**Mechanism (verify before fixing).** Each array task computes one
`(cell, representation)` pair, so no single task ever holds two
representations' per-seed scores; the Wilcoxon/Holm step needs them together and
nothing runs after the array to do it. The Holm machinery exists in
`sweep_multi_seed.py` — it is simply never invoked at array scale. The S=8
validation appeared to pass because a post-run aggregation was done by hand
then; that is where the "60 Wilcoxon entries" figure came from, and it belongs
to array 1640880, not 1640910.
**Two artifacts are wrong because of this, and both must be corrected here:**
1. `artifacts/T-M7d-harvest/harvest_summary.json` reports
   `ac3_wilcoxon_coverage: {n_wilcoxon_entries: 60, n_complete: 60, pass: true}`
   against files that contain none. The count was taken without checking that
   the entries existed.
2. The S7 exit criterion "every competitor-vs-IsalHG claim carries a
   Holm-corrected p + effect size" is therefore **not currently met**.
**Context to read first:**
- `docs/article/REVIEW/STATS_PASS_PLAN.md` — the specified tests: seed-level
  pairing, **BCa** bootstrap (not percentile), one-sided Wilcoxon signed-rank,
  Holm–Bonferroni across the (representations × metrics) family, median paired
  difference + rank-biserial effect size, and the nested-CV rule for A3
- `experiments/article/analysis/sweep_multi_seed.py` — the existing BCa /
  Wilcoxon / Holm implementation to reuse, **not** reimplement
- `scripts/harvest_T_M7s.py` — the harvest whose `ac3` check must become real
- `docs/article/DEVELOPMENT/T-M7/CLOSED/T-M7s.md` — the exclusion policy this
  must respect
**Inputs, all present on disk:** `results/T-M7d/seed_metrics/a/stratum_a/seed{0..26}/{rep}.json`
(27 seeds × 7 representations, verified) and the Stratum B equivalents under
`seed_metrics/b/<cell>/`.
**Description:** Add an aggregation entry point that reads the harvested
per-seed metrics and emits, per cell, the statistics the plan specifies: BCa 95%
CIs per (representation, metric); one-sided Wilcoxon signed-rank vs IsalHG per
competitor; Holm–Bonferroni across the (representations × metrics) family;
median paired difference and rank-biserial effect size. Write them into the
stats artifacts so the `wilcoxon` dicts are populated from the pipeline rather
than by hand. Then re-run the harvest so `ac3` reflects reality, and correct
`all_acceptance_pass` / `acceptance_shortfalls` accordingly.
**Exclusion policy — carry it, do not re-derive it.** The three cells that timed
out on `isalhg_levenshtein` (`er_uniform_k3_n16_rho4`,
`er_uniform_k3_n24_rho2`, `er_uniform_k5_n8_rho2`) are excluded whole-cell from
every IsalHG comparison; partial seed data (18/27, 9/27, 13/27) is not used, and
no competitor-vs-IsalHG p-value, CI, or effect size may be emitted for them.
**Acceptance:** the aggregation runs from the committed harvested inputs with no
cluster access; `wilcoxon` is non-empty for Stratum A and for every
IsalHG-complete Stratum B cell, each entry carrying a Holm-corrected p, a median
paired difference and a rank-biserial effect size; CIs are **BCa**, and the
artifact records which bootstrap was used so percentile values can never be
mistaken for BCa; the three excluded cells carry no IsalHG comparison; the
regenerated `harvest_summary.json` reports true counts and an honest
`all_acceptance_pass`; a regression test fails if a stats file has ≥2
representations present and an empty `wilcoxon`, and another fails if a
comparison is emitted for an excluded cell; suite matches the session baselines
(1470 passed / 9 skipped / 29 deselected, ruff 3, mypy 21).
**Out of scope here:** re-running the array or any Picasso job (this is pure
recomputation from harvested data); the prose (T-M8f re-points at these
artifacts once they exist); the arity-axis shortfall, which is a real limitation
and stays reported.
