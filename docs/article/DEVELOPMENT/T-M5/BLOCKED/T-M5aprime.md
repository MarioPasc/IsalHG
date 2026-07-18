# T-M5a' — Full-scale Layer-1 execution on Picasso (E1/E2/E2b/E3 + info-content)
**Declared:** 2026-07-09 22:32 CEST (filed by the orchestrator at T-M5a close)
**Status:** BLOCKED — parked at D-ART2 (v3 rescope; 2026-07-18 S1 reconciliation)
**Depends on:** T-M5a (v2 pipeline; that closure superseded — see below)
**Context to read first:**
- `docs/article/DEVELOPMENT/T-M5/CLOSED/T-M5a.md` — the pipeline's closing note
  + orchestrator verification (smoke-scale numbers, acceptance transfer)
- `experiments/article/configs/{e1_correlation,e2_density_sweep,e2b_sensitivity,e3_ladder}.yaml`
- `slurm/T-M5a_launcher.sh`, `slurm/T-M5a_worker.sh` — ready-to-submit array-job pair
  (CPU-only, 4 CPU / 16 GB / 6 h per task; no `--constraint=dgx`)
- `docs/article/empirical/correlation.md` — the closing criteria this task signs off
- `docs/article/DEVELOPMENT/T-M2/CLOSED/T-M2c.md` §Orchestrator note — measured
  acceptance rates (correlation corpus 0.020 at seed 0: low-`m/n` cells oversample
  ~50×; budget generation time accordingly)

**Description:** Execute the T-M5a pipeline at full scale on Picasso and regenerate
the analysis at scale. Steps: (1) rsync the repo to
`/mnt/home/users/tic_163_uma/mpascual/fscratch/repos/IsalHG` and build/refresh the
`isalhg` conda env there (`pip install -e ".[dev]"`); (2) submit the four configs
via `bash slurm/T-M5a_launcher.sh <config>`; (3) retrieve cell JSONs to
`/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/T-M5a/`; (4) rerun the
analysis modules to produce full-scale figures (ρ-vs-Δ, scatter, sensitivity
histogram, ladder, info-content).

**Acceptance:** (a) `correlation.md` closing criteria reproduced at full scale;
(b) the ρ-vs-Δ figure shows the predicted decay over the full density range with
n>10 exact-HGED cells; (c) info-content ratio checked for the n=8–12 reversal
(IsalGraph precedent 1.45–1.89×) — report the outcome either way; (d) per-corpus
acceptance rates reported per cell (D-CONN1/DATA.md §1); (e) per-edit run
statistics logged at scale for T-TBb; (f) wall-clock + peak RSS per cell reported.

**Out of scope here:** competitor distances (T-M3a–d; rerun E1 with competitors
when they land); the applications (T-M5b–e); any `src/` or pipeline changes
(reopen via task-handoff if the pipeline itself needs fixing at scale).

---

## Submission record (orchestrator, 2026-07-09 ~22:50 CEST)

Steps (1)–(2) executed. Repo code surface rsynced to Picasso
(`fscratch/repos/IsalHG`), editable install rebuilt (fresh C++ compile), gates
green on the cluster (frozen `w*_c` pins + ladder arity tests: 17 passed).
Jobs submitted on `cpu_partition` (the tracked worker's `--partition=batch`
does not exist on Picasso; also its `~/.conda/envs` PYTHON default is wrong —
the env lives at `fscratch/conda_envs/isalhg`; submission used a thin wrapper
at `~/execs/isalhg/t5a_worker.sh` forwarding `--output-root`):

| Config | Job | Cells | Note |
|---|---|---|---|
| e1_correlation | 1547131 | 9 | running |
| e2_density_sweep | 1547132 | 18 | running |
| e2b_sensitivity | 1547133 | 6 | running |
| e3_ladder | **1547221** | 6 | v2 — first array 1547134 crashed on the arity bug (cell 4, `k exceeds K_MAX`), cancelled, partials wiped, resubmitted after the arity-gate merge |

Outputs: `fscratch/results/isalhg/T-M5a/<config>/` · logs `~/execs/isalhg/logs/`.
Retrieval (step 3): `rsync -az picasso:/mnt/home/users/tic_163_uma/mpascual/fscratch/results/isalhg/T-M5a/ /media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/T-M5a/full/`

Remaining for this task: monitor completion, retrieve, run analysis at full
scale (step 4), sign off acceptance (a)–(f). Note for (a)/(b): e3's ensemble
now caps snapshot arity at `arity_range[1]` (post-fix semantics) — the paper
must describe the ladder as arity-bounded.

---
**Parked (S1 reconciliation merge, 2026-07-18 — D-ART2).** The full-scale
v2 deliverables this task would harvest (E1 competitor correlation, E2
density sweep, E2b/E3 at v2 spec, MI) are retired from the article by
PI-ratified D-ART2; the v3 discussion evidence is the rescoped T-M5a (E1'
figure + bits, new mini-corpus batch submitted at S3). The Picasso jobs
recorded above (1547131/32/33) remain harvestable as follow-up material
only. No action unless the PI reopens the v2 axis.
