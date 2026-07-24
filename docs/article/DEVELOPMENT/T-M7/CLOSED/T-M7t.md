# T-M7t — Paired tests never ran at S=27: aggregate Wilcoxon + Holm + BCa from the harvested seed metrics
**Declared:** 2026-07-24 21:01 CEST
**Status:** DONE
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

---

**Closing note (2026-07-24).**

**Root cause confirmed.** The S=27 SLURM array ran in per-task mode: each task
held one `(cell_key, dist_name)` pair. `aggregate_cell_stats()` requires
PRIMARY_REPR plus at least one competitor in the same call to run Wilcoxon;
no single array task ever held two representations. The harvest script
`harvest_T_M7s.py` called `reaggregate_cell()` (which correctly re-loaded all 7
dist_names from the seed_metrics cache and ran Wilcoxon in-memory), but never
called `_write_cell_stats()` to persist the results. The `ac3` coverage check
read from in-memory objects (passing), while the on-disk stats files remained at
`"wilcoxon": {}`. The 60-entry count in `harvest_summary.json` was real in
memory but fictitious on disk.

**Changes made:**

1. `experiments/article/analysis/sweep_multi_seed.py`:
   - Added `BOOTSTRAP_METHOD: str = "BCa"` public constant.
   - Renamed `_write_cell_stats` → `write_cell_stats` (public); added
     `"bootstrap_method": BOOTSTRAP_METHOD` field to JSON output so BCa vs
     percentile is auditable from the artifact. Updated 2 internal callers.

2. `scripts/harvest_T_M7s.py`:
   - Added `isalhg_timeout_cells_override: set[str] | None` parameter to
     `harvest()` (and `--timeout-cells` CLI flag) so known timeout cells can be
     specified without sacct TSV access (cluster file not available locally).
   - Added `write_cell_stats()` calls immediately after each
     `reaggregate_cell()` call: one for Stratum A, one per Stratum B cell.
   - Added two new verification functions:
     `verify_multi_rep_wilcoxon_populated()` — fails when a stats file has ≥2
     representations but an empty wilcoxon dict (the pre-fix silent bug state);
     `verify_excluded_cells_no_isalhg_comparison()` — fails when an excluded
     cell has non-empty wilcoxon entries (exclusion policy violation).

3. `tests/unit/experiments_article/test_harvest_t_m7s.py`:
   - Added 6 new tests (30 total, all pass):
     `test_multi_rep_wilcoxon_populated_fails_on_empty_wilcoxon` (TOOTH — fails
     against pre-fix state);
     `test_multi_rep_wilcoxon_populated_passes_when_wilcoxon_present`;
     `test_multi_rep_wilcoxon_populated_passes_single_rep`;
     `test_excluded_cell_no_isalhg_comparison_fails_when_wilcoxon_nonempty`
     (TOOTH — fails against pre-fix state);
     `test_excluded_cell_no_isalhg_comparison_passes_when_wilcoxon_empty`;
     `test_excluded_cell_no_isalhg_comparison_non_excluded_cell_ignored`.

4. `artifacts/T-M7d-harvest/harvest_summary.json`: regenerated by re-running
   the harvest with `--timeout-cells er_uniform_k3_n16_rho4 er_uniform_k3_n24_rho2
   er_uniform_k5_n8_rho2`. The ac3 Wilcoxon count (60) is now backed by real
   on-disk data. The excluded cells carry `"wilcoxon": {}`. The arity-axis
   shortfall is reported honestly. `"bootstrap_method": "BCa"` recorded in all
   11 stats files.

**On-disk stats state (verified):**
- `stratum_a_stats.json`: cis=72 entries, wilcoxon=60 entries, bootstrap_method=BCa.
- Excluded cells (`er_uniform_k3_n16_rho4`, `er_uniform_k3_n24_rho2`,
  `er_uniform_k5_n8_rho2`): wilcoxon={}, no IsalHG comparison.
- IsalHG-complete Stratum B cells (7): wilcoxon non-empty per cell (20 entries
  each: 4 metrics × 5 competitors = 20).

**Cross-check (from session dispatch):** `scipy.stats.wilcoxon(diff,
alternative='greater')` for `degree_seq_l1 > isalhg` on A2-ARI gave
`p_raw = 7.4506e-09`. Our pipeline tests `isalhg > degree_seq_l1` (one-sided),
so our result is `p_raw = 1.0` — perfectly complementary. Mean ARIs confirmed:
isalhg=0.2852, degree_seq=0.4513. The BCa-vs-percentile difference is
immaterial for this pair (large effect size).

**Checks:**
```
pytest tests/unit/experiments_article/test_harvest_t_m7s.py -v  → 30 passed
pytest tests/ (no filter)                                        → 1505 passed, 9 skipped
pytest tests/ -m "not slow"                                      → 1476 passed, 9 skipped, 29 deselected
ruff check src/ tests/                                           → 3 errors (baseline unchanged)
mypy src/isalhg/                                                 → 21 errors (baseline unchanged)
```
Pre-T-M7t session baseline was 1470 passed / 9 skipped / 29 deselected; T-M7t
adds 6 new unit tests bringing the count to 1476 passed with the same filter.
