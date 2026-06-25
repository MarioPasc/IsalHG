# Preprint pipeline — Picasso driver

The 720-cell preprint sweep (`docs/PREPRINT.md` §3–§4) runs on Picasso
as two SLURM array jobs. This directory carries the array entry point,
the launcher/worker pair, and the analysis that turns the per-cell JSONs
into Figures 1–3 + Tables 1–2.

```
pipeline/
├── run_cell.py             # SLURM array entry: index → run one cell
├── slurm/
│   ├── launcher.sh         # submits fast + slow arrays
│   └── worker.sh           # SBATCH headers + array task body
└── analysis/
    ├── aggregate.py        # 720 JSONs → per_cell / per_nrc CSVs
    └── figures.py          # CSVs → fig1-3 + table1-2
```

## End-to-end usage

1. **Regenerate the YAML** (idempotent; rerun if you edit the axes):
   ```bash
   python experiments/preprint/data/build_preprint_config.py
   ```
   Produces `experiments/configs/preprint_random_sweep.yaml` (720 cells).

2. **Smoke locally** (under a minute):
   ```bash
   python -m experiments.orchestrator \
       --config experiments/configs/preprint_smoke.yaml
   ```

3. **Smoke the single-cell entry point**:
   ```bash
   python -m experiments.preprint.pipeline.run_cell \
       --config experiments/configs/preprint_smoke.yaml \
       --tier all --cell-index 0 \
       --output-root /tmp/iso_smoke
   ```

4. **Dry-run the launcher** (no submission):
   ```bash
   bash experiments/preprint/pipeline/slurm/launcher.sh --dry-run
   ```
   Confirms the per-tier cell counts (680 fast + 40 slow).

5. **Submit on Picasso**:
   ```bash
   bash experiments/preprint/pipeline/slurm/launcher.sh
   # → two sbatch --parsable returns; one fast array (680 tasks),
   #   one slow array (40 tasks).
   ```
   Monitor: `squeue -j <fast_id>` / `squeue -j <slow_id>`.
   Per-cell JSONs land under
   `$RESULTS_ROOT/preprint/pipeline/random_sweep/`.

6. **Aggregate**:
   ```bash
   python -m experiments.preprint.pipeline.analysis.aggregate \
       --results-root $RESULTS_ROOT/preprint/pipeline/random_sweep \
       --output-dir experiments/preprint/pipeline/analysis_output
   ```

7. **Render figures + tables**:
   ```bash
   python -m experiments.preprint.pipeline.analysis.figures \
       --aggregate-dir experiments/preprint/pipeline/analysis_output \
       --output-dir   experiments/preprint/pipeline/analysis_output
   ```

## Memory tiers

The launcher splits the 720 cells into two arrays:

| Tier | Cells satisfying ... | Count | `--time`     | `--mem-per-cpu` | `--array=...%conc` |
|------|----------------------|------:|--------------|-----------------|--------------------|
| fast | `n < 1000 OR c < 25` |   640 | `01:30:00`   | `8G`            | `0-639%128`        |
| slow | `n = 1000 AND c = 25`|    80 | `04:00:00`   | `32G`           | `0-79%32`          |

Both arrays share `--cpus-per-task=1`, no GPU, no `--constraint=dgx`
(plain CPU partition). Per-cell wall-clock is capped by the
`FingerprintTimingProtocol` `signal.alarm` watchdog at 600 s per
fingerprint (10 repeats max ⇒ 6000 s worst case; well under the slow
tier's 4 h budget). The orchestrator's atomic skip-if-exists JSON
pattern makes resubmission of a failed array task a no-op for the
cells that already finished.

## Restarting individual failed tasks

```bash
# Re-queue one task by array index (Picasso scontrol):
scontrol requeue <jobid>_<arraytask>

# Or rerun the whole tier; the orchestrator skips completed cells:
bash experiments/preprint/pipeline/slurm/launcher.sh --tier slow
```

## Acceptance criteria (mirror `docs/PREPRINT.md` §7)

- 720 JSONs under the output root; `per_cell.csv` reports 720 rows.
- `correctness.csv` reports four-way partition agreement (pass rate
  = 1.0 modulo DNFs).
- `figures/fig{1,2,3}_*.{pdf,png}` and `tables/table{1,2}_*.tex`
  rendered.

## Environment overrides

| Variable             | Default                                                   |
|----------------------|-----------------------------------------------------------|
| `CONDA_ENV_NAME`     | `isalhg`                                                  |
| `REPO_DIR`           | `/mnt/home/users/tic_163_uma/mpascual/fscratch/repos/IsalHG` |
| `RESULTS_ROOT`       | `/mnt/home/users/tic_163_uma/mpascual/fscratch/isalhg_results/preprint/pipeline` |
| `NODE_CONSTRAINT`    | `avx512` (passed as `--constraint=`; the `isalhg` env's compiled extensions hit `Illegal instruction` on the AMD `sr*` nodes without AVX-512) |

Export these in the calling shell to relocate the run.
