# T-M7r — G3 OFAT re-run on the corrected Stratum A corpus
**Declared:** 2026-07-24 12:18 CEST
**Status:** OPEN
**Depends on:** T-M7f (the G3 experiment this re-executes — CLOSED),
T-M7m (prune), T-M7o (arity-cap fix).
**Origin:** 2026-07-24 S7 re-run handoff
(`docs/article/DEVELOPMENT/HANDOFF_S7_RERUN.md` §4.3), directed by Mario.
T-M7f closed on 2026-07-22 with all five OFAT axes run on ADMITTED Stratum A
bases of the *pre-prune* membership; T-M7m/T-M7o then changed which families
exist. The G3 result dirs are archived as superseded and the five filmstrips
must be regenerated from bases that are still in the corpus. **The corpus is
FINAL — do not re-derive or re-litigate it.**
**Context to read first:**
- `docs/article/DEVELOPMENT/HANDOFF_S7_RERUN.md` — §5 the landmines
- `docs/article/DEVELOPMENT/T-M7/CLOSED/T-M7f.md` — the full spec being
  re-executed (five axes M1–M5, the four measured responses per axis, the
  competitor contrast, the filmstrip + rendering convention) and the
  superseded measured baseline
- `src/isalhg/datasets/synthetic/known_design_catalog.py` — `DATA_MANIFEST`
  is the single source of truth for Stratum A membership (17 ids)
- `experiments/article/{g3_sequence.py,g3_analysis.py}`,
  `experiments/article/configs/g3_ofat.yaml`
**Description:** Re-select the G3 bases from `DATA_MANIFEST.stratum_a_ids`
(n ≲ 20 for drawability), then re-execute the five-axis OFAT experiment
exactly per T-M7f: M1 vertex growth, M2 densification, M3 arity increase
(per-`k` analysis only), M4 incidence edit (drift probe), M5 symmetry break
(avalanche probe). Re-emit per axis: response curve + monotone fraction, MDS
trajectory + continuity statistic, ν-contribution sign, `s(e)` distribution by
move type, competitor contrast (all seven representations including the naive
degree-sequence baseline; nauty's jump statistic vs ours), and the filmstrip
artifact under the single stated rendering convention. Report the delta
against T-M7f's superseded per-axis numbers. Local compute; nothing here goes
to Picasso.
**Acceptance:** every base id used is a member of
`DATA_MANIFEST.stratum_a_ids`; five filmstrip artifacts (one per axis) exist
under one stated rendering convention; per axis the response curve, monotone
fraction, MDS continuity statistic, and ν-contribution sign are emitted; every
`H_t` decodes via S2H with the round-trip asserted in tests; competitor
trajectories emitted with nauty's jump statistic; M3 never pools raw `d_I`
across `k` (the `assert_single_arity_group` guard stays); the sequence
generator's unit tests still pin budget accounting, connectivity, and the
per-axis invariants; superseded T-M7f result dirs moved under the
`results/superseded/` convention, not deleted; suite matches the session
baselines (1430 passed / 9 skipped / 25 deselected, ruff 3, mypy 21).
**Out of scope here:** the sweep/stats harness (T-M7d), G2/A4 (T-M7q), E1′
(frozen), folding G3 into `theoretical/geometry.md` prose (doc pass follows),
any change to `src/isalhg/datasets/synthetic/` corpus definitions.
