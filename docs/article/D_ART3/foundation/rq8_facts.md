# RQ8 fact base — valid completion of a record

*The derivation of record for every RQ8 number the prose may cite. Precondition
for T-KBg. Declared 2026-09-13, wave `2026-09-13-headline-w0`, agent `rq8`.
Ledger: `../../DEVELOPMENT/T-KB/IN-PROGRESS/T-KBaa.md`. Gate evidence:
`../experiments/RQ8_PILOT.md`.*

**Rule for this file.** A number enters here only with the run that produced it.
Where a campaign table is not yet harvested the row says so; it is never filled
from the pilot, whose seeds are deliberately outside the campaign schedule.

---

## 1. Run roots and provenance

| what | where |
|---|---|
| Picasso results root | `~/results/IEEETKDE_ow/RQ8_completion/completion/` |
| Picasso runner tree | `~/repos/IsalHG-rq8` (HOME, not FSCRATCH — see §5) |
| Picasso library tree | `~/fscratch/repos/IsalHG-tkde` (shared, read-only) |
| conda env | `~/fscratch/conda_envs/isalhg-tkde` (shared, not rebuilt) |
| corpora | `~/fscratch/datasets/isalhg_tkde/corpora/` (read-only) |
| drive mirror | `results/IEEETKDE_ow/RQ8/` |
| pilot rows (gate G8.1) | `results/IEEETKDE_ow/RQ8/pilot/RQ8_completion/pilot_g8_1/` |
| deployed SHA | `9840460` on `worktree-agent-a1b4083a2935ce6dd`, from BASE_SHA `704e271` |

## 2. Job ids

Submitted 2026-09-13 from `~/repos/IsalHG-rq8`, deployed SHA `9840460`.

| job | id | array | what |
|---|---|---|---|
| `tkde-rq8` (cluster smoke) | **2308337** | `0-0` | the `--smoke` configuration, staged under `_smoke/`; payload green in 0.5 s, both tree assertions passed |
| `tkde-rq8` (campaign) | **2308339** | `0-0` | 81 units, 27 seeds, six arms + `ow_ngram_ho` |
| `tkde-rq2-ow-main` | **2308342** | `0-12` | exact0 / bipartite / oracle / hypercot, 52 shards over 13 tasks |
| `tkde-rq2-ow-census` | **2308343** | `0-8` | the false-merge census, 33 shards over 9 tasks |
| `tkde-rq5-ow` | **2308368** | `0-0` | 65 units, three experiments |

`sbatch --test-only` was run and passed for all three before submission
(probe ids 2308268, 2308340/2308341, 2308362 — test-only, no job created).

Monitor: `sacct -j <id> -X -n -P -o JobID,State,Elapsed,NodeList`; memory needs
the `.batch` step, so drop `-X`.

## 3. Gate G0 — the star census (FINAL, measured locally 2026-09-13)

`is_star` = some constant in every fact **and** every other constant in at most
one. Root convention for the interior/pendant rule: the hub (max fact-degree,
ties by smallest id).

| corpus | N | stars | fraction | non-stars | shared constants (median/mean) | shared facts (median/mean) |
|---|---|---|---|---|---|---|
| `ndc_classes` | 1,381 | 42 | 0.0304 | 1,339 | 2 / 2.938 | 3 / 3.500 |
| `wd50k66` | 3,988 | 2,128 | 0.5336 | 1,860 | 3 / 3.254 | 4 / 4.719 |

Substrate pool at `m ≥ 4`: `ndc_classes` 522 (521 non-star, 1 star);
`wd50k66` 2,775 (1,641 non-star, 1,134 star). Every non-star in both pools has at
least one interior fact. NDC's star stratum is `n = 1` and **not reportable**.

Cross-checked independently by the `rq3v2` agent: agrees to the member.

**Citable sentence.** Structure exists in 46.6 % of WD50K(66) entity
descriptions; NDC-classes is 97.0 % non-star, i.e. genuinely relational.

## 4. Gate G8.1 — the pilot (FINAL, 3 off-schedule seeds, 200 interior units/corpus)

Seeds 80900–80902 (`seed_offset: 900`), disjoint from the campaign's
80000–80026. `hit@10` is `usable@10`: valid ∧ connected ∧ isomorphic to truth.

| corpus | arm | N | hit@10 | pattern@10 | validity | connectivity | pattern right, attachment wrong |
|---|---|---|---|---|---|---|---|
| `ndc_classes` | `ow_ngram` | 600 | 0.1067 | 0.3750 | 1.0000 | 1.0000 | 0.716 |
| `ndc_classes` | `ow_ngram_ho` | 600 | 0.1417 | 0.3850 | 1.0000 | 1.0000 | 0.632 |
| `ndc_classes` | `pattern_cooc` | 600 | 0.3033 | 0.8917 | 1.0000 | 1.0000 | 0.660 |
| `ndc_classes` | `pattern_freq` | 600 | 0.1867 | 0.4400 | 1.0000 | 1.0000 | 0.576 |
| `ndc_classes` | `fact_ngram` | 600 | 0.0950 | 0.3667 | 1.0000 | 0.8670 | 0.741 |
| `ndc_classes` | `incidence_ngram` | 600 | 0.0117 | 0.2700 | 0.1695 | 1.0000 | 0.957 |
| `ndc_classes` | `random_pattern` | 600 | 0.0267 | 0.0833 | 1.0000 | 1.0000 | 0.680 |
| `wd50k66` | `ow_ngram` | 600 | 0.0150 | 0.7317 | 1.0000 | 1.0000 | 0.979 |
| `wd50k66` | `ow_ngram_ho` | 600 | 0.0100 | 0.6350 | 1.0000 | 1.0000 | 0.984 |
| `wd50k66` | `pattern_cooc` | 600 | 0.0133 | 0.7067 | 1.0000 | 1.0000 | 0.981 |
| `wd50k66` | `pattern_freq` | 600 | 0.0083 | 0.5850 | 1.0000 | 1.0000 | 0.986 |
| `wd50k66` | `fact_ngram` | 600 | 0.0050 | 0.7417 | 1.0000 | 0.5116 | 0.993 |
| `wd50k66` | `incidence_ngram` | 600 | 0.0000 | 0.4067 | 0.1427 | 1.0000 | 1.000 |
| `wd50k66` | `random_pattern` | 600 | 0.0000 | 0.0317 | 1.0000 | 1.0000 | 1.000 |

**Verdicts, pre-registered and ruled before submission.**

- H8.1 **not supported**; the fallback applies and RQ8 is a **supporting
  exhibit**, not a headline (D-KBaa2).
- H8.2 holds trivially and then some: `pattern_cooc` does not merely tie us on
  the star control, it beats us on the *relational* corpus.
- H8.3 clauses 1 and 2 hold — ours valid 1.0000 and connected 1.0000 by theorem,
  `fact_ngram` connectivity 0.867 / 0.512 below 1. Clause 3 **fails as written**
  and the threshold was not moved (D-KBaa4).
- The design's §0 attachment mechanism is **contradicted** (D-KBaa3).

## 5. Deployment deviations, with their measured reason

| deviation | reason |
|---|---|
| runner tree on HOME (`~/repos/IsalHG-rq8`), not FSCRATCH | FSCRATCH measured **read-only** 2026-09-13: 276.3k files against a 250.0k soft quota with the grace **expired**; `mkdir ~/fscratch/repos/...` returns "Disk quota exceeded". Contradicts `slurm/tkde/README.md`, which assumes HOME's file quota is the scarce one. |
| shared `isalhg-tkde` env, `--no-build` | This wave changes nothing under `src/**`; the editable install is a PEP 660 finder, so `isalhg.*` must keep resolving to the canonical tree — which every worker in `slurm/tkde/` asserts. |
| `ow_ngram_ho` replaces the design's `ow_gru` | torch is not installed and adding a dependency was out of scope; same enabling rule, declared before the measurement (D-KBaa1). |

Run-time write audit before submission: every write target is `$LOCALSCRATCH`
(node-local), `$ISALHG_RESULTS_ROOT` (HOME) or `~/execs/tkde/logs` (HOME).
`TMPDIR=/localscratch/users/tmp` and `PYTHONPYCACHEPREFIX` are node-local.
Nothing writes to FSCRATCH at run time, so the quota block cannot kill a job
mid-run.

## 6. Campaign tables — PENDING HARVEST

Not yet filled. When jobs 2308489 / 2308495 / 2308496 / 2308498 complete, harvest
with `scripts/tkde/harvest_from_picasso.sh` and fill:

- [ ] RQ8 hit@10 and pattern@10, 27 seeds, BCa 95 % CIs, Holm-corrected paired
      Wilcoxon against every baseline, per corpus × stratum × hidden-fact kind.
- [ ] RQ8 validity and connectivity per arm with CIs (the H8.3 sentence).
- [ ] RQ8 mechanism table: pattern right, attachment wrong, per arm.
- [ ] RQ2_ow: false merges per arm per collection, and the censoring contrast
      against `wstar_orbit` (expected 0 censored for `isal_ow_struct`).
- [ ] RQ5_ow: ARI / NMI / silhouette per arm, against the naive floors.
