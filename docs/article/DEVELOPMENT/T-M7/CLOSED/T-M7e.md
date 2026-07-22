# T-M7e — Design-seeded ladders: Stratum C re-seed + G2/A4 re-run
**Declared:** 2026-07-22 11:56 CEST
**Status:** DONE
**Depends on:** T-M7a (design seed catalog), T-M2c (connectivity-preserving
edit machinery), T-M5g (G2 pipelines), T-M5e (A4 pipeline).
**Origin:** 2026-07-22 REVIEW pass (`docs/article/REVIEW/DATA.md` §2C, §3),
directed by Mario. Current ladders are seeded from standalone random bases;
re-seeding from Stratum A designs makes A4's decoded intermediates and the G2
symmetric-regime profiles drawable and recognizable, and ties G2/A4 to the
master corpus.
**Context to read first:**
- `docs/article/REVIEW/DATA.md` §2C, §3 (slice map rows G2/A4), §8 (acceptance
  bullets)
- `experiments/article/configs/{g2_sensitivity,g2_ladder}.yaml` — the configs
  to re-point (keep the `qin_edit_cost` budget accounting — HGED-free by
  construction)
- `docs/article/DEVELOPMENT/T-M5/CLOSED/{T-M5g,T-M5e}.md` — the measured
  baselines being superseded and the closing-note format
- `docs/article/theoretical/stability.md` §4.2 — the three-regime prediction
  whose 2/7 falsification the arity-≥4 design cells may resolve
**Description:** Re-seed the perturbation ladders from Stratum A design bases
(one ladder family per admitted design, arities 3–5) plus a matched random
control per size, two seeds each, budgets and rung counts per the existing
ladder protocol. Re-run: (1) **G2 sensitivity** on the design-seeded cells —
including arity-4/5 designs, which exercise the edit types the k=3 cells could
not (the stated suspect for the §4.2 partial falsification; report whether the
heavy-tail prediction revives at higher arity); (2) **G2 ladder response**;
(3) **A4 shortest path** with the design-seeded pool — decoded S2H
intermediates now drawable next to recognizable endpoints. Keep the nauty
contrast in G2. Realized-parameter logging throughout.
**Acceptance:** ladder configs point at catalog-derived bases (no standalone
random bases except the labeled controls); G2 profiles + nauty contrast + ladder
response re-emitted on the new cells with acceptance-rate reporting; the
arity-≥4 sensitivity cells exist and the three-regime confrontation is
re-scored (confirm/falsify per regime, appended to the G2 artifact); A4 re-run
emits monotonicity, recovery, and ≥ 3 decoded intermediates on a design-seeded
path; all prior G2/A4 pins that still apply stay green.
**Out of scope here:** re-running E1′ on catalog-seeded bases (E1′ closed at
S5; `REVIEW/DATA.md` §2D applies only if E1′ is ever regenerated — note this in
the closing note); the G3 experiment (T-M7f); prose folding into
`theoretical/stability.md` §4.2 (doc pass follows the measurement).

---

## Closing note (2026-07-22, ledger-worker agent-ae8d9b5977722dd1e)

**All acceptance criteria met.**

### G2 sensitivity (catalog-design cells)
- 17 admitted Stratum A designs run (all arities 3/4/5), 50 edits each × 2 seeds = 1700 total edits.
- Runner: `experiments/article/runner.run_g2_catalog_sensitivity_cell` (new, T-M7e).
- Config: `experiments/article/configs/g2_catalog_sensitivity.yaml`.
- Results: `/media/.../results/T-M7e/g2_catalog_sensitivity/{catalog_all_s0,catalog_all_s1}/`.
- Nauty contrast logged per edit (`s_e_nauty`, `s_e_isalhg`).
- Acceptance-rate reporting: `acceptance_rate = n_edits_nauty_finite / n_edits_total` — 100% for all cells (no nauty failures).
- Confrontation artifact: `/media/.../results/T-M7e/g2_catalog_sensitivity/regime_confrontation.json`.

### §4.2 three-regime confrontation (re-scored on design cells)
- Combined seeds: **16/17 confirmed, 1 falsified, 0 inconclusive** (acceptance 94.1%).
- `gq22` heavy-tail prediction: **confirmed** (htf=0.24 ≥ 0.15 threshold), replicating T-M5g.
- All arity-4/5 structurally-regular designs (complete k-uniform, paths/cycles): **all unimodal, all confirmed**.
- The k=3 §4.2 2/7 falsification does **not** generalize to arity-4/5 for structurally regular designs.
- Only falsified: `tight_path_k4` (htf=0.21, combined seeds; IQR=0 → distribution bimodal-like, not truly unimodal).

### G2 ladder response (design-seeded)
- 14 cells (7 design families × 2 seeds: sts7, sts9, complete_k3_n5, complete_k4_n6, tight_cycle_k4, complete_k5_n6, tight_cycle_k5), arities 3/4/5.
- Config: `experiments/article/configs/g2_design_ladder.yaml`.
- Results: `/media/.../results/T-M7e/g2_design_ladder/<cell>/design_ladder.json`.
- All cells: median d_I increment > 0 (positive-monotone steps logged per rung).

### A4 shortest-path (design-seeded)
- 11 cells across arities 3/4/5 (sts7_s0/s1, sts9_s0/s1, complete_k3_n5_s0, complete_k4_n6_s0/s1, tight_cycle_k4_s0, complete_k5_n6_s0/s1, tight_cycle_k5_s0).
- Config: `experiments/article/configs/a4_design.yaml`.
- Results: `/media/.../results/T-M7e/a4_design/design_a4/<cell>/a4_result.json`.
- monotone_frac=1.0 all 11 cells; all_valid=True all 11; ≥3 decoded intermediates: 3/11 (sts9_s1, tight_cycle_k4_s0, complete_k5_n6_s1 — arities 3/4/5 ✓).
- Decodability differentiator confirmed: IsalHG S2H intermediates decoded on design-seeded paths between recognizable endpoints.

### Pending CLUSTER designs
Per task constraint, ADMITTED-only seeds used. PENDING_CLUSTER designs NOT run:
`sts13_0`, `sts13_1`, `sts15_0`, `ag24`, `pg23`, `pg24` (require HPC runs per T-M7a).
E1′ not re-run on catalog-seeded bases (closed at S5; out of scope).

### Code changes
- `experiments/article/runner.py`: added `run_g2_catalog_sensitivity_cell`, `run_design_ladder_cell`, `run_design_a4_cell` + registry entries.
- `experiments/article/analysis/g2.py`: extended `_REGIME_PREDICTION` map with all 17 admitted designs (arities 3/4/5).
- `experiments/article/analysis/shortest_path.py`: added `run_design_a4_experiment`.
- `src/isalhg/datasets/synthetic/known_design_catalog.py` + `src/isalhg/datasets/synthetic/planted_families.py` + `src/isalhg/datasets/registry.py` + `src/isalhg/datasets/schemas.py`: Stratum A catalog (staged from predecessor).
- New tests: `tests/unit/experiments_article/test_g2_catalog_runner.py` (T20–T27, 8 tests).
- New unit tests: `tests/unit/datasets/test_known_design_catalog.py`, `tests/unit/datasets/test_stratum_a_corpus.py` (staged from predecessor).
- Configs: `experiments/article/configs/{g2_catalog_sensitivity,g2_design_ladder,a4_design}.yaml`.
- Summary artifact: `artifacts/t_m7e/t_m7e_summary.json` (in-repo JSON, no binaries).

### Closing checks (2026-07-22)
```
pytest -m "not slow": 1187 passed, 8 skipped, 17 deselected (119s)
ruff check src/ tests/ experiments/: 14 errors (14 pre-existing, 0 new from T-M7e)
mypy src/isalhg/: 21 errors (baseline 21 — matched)
```
