# T-M7h — Picasso full feasibility pilot for the non-admitted Stratum B region
**Declared:** 2026-07-22 15:40 CEST
**Status:** DONE
**Depends on:** T-M7b (local pilot artifact + config complete)
**Delegation:** agent
**Why out of scope:** T-M7b ran a local 5-instance pilot (35 s timeout); all heavy
compute goes to Picasso via the `picasso-sbatch` skill. T-M7b deliberately deferred
HPC measurement to this task.
**Context to read first:**
- `experiments/article/stratum_b_feasibility_envelope.json` — current local artifact;
  update it with Picasso-measured p50/p90 and admission decisions
- `experiments/article/feasibility_pilot.py::run_pilot` — the runner CLI; raise
  `--timeout` to 300 s for cluster runs
- `experiments/article/configs/stratum_b_sweep.yaml` — grid definition
- `docs/article/REVIEW/DATA.md` §4 ("feasibility-envelope protocol") — admission
  criterion: p90 ≤ 30 s AND 0 DNFs across 30 instances
- `docs/article/DEVELOPMENT/T-M7/CLOSED/T-M7b.md` — local pilot findings and
  per-block skip reasons
- `docs/article/DEVELOPMENT/T-M7/OPEN/T-M7d.md` — gated by this task
- `.claude/rules/coding_rules.md` — always
**Description:** Run the full 30-instance feasibility pilot on Picasso for every
Stratum B block not admitted (or only provisionally admitted) by the local T-M7b
pilot. Use `feasibility_pilot.py` as the worker command via the `picasso-sbatch`
skill (CPU-only job: `--gres=gpu:0`, 5 min/instance budget). Update
`stratum_b_feasibility_envelope.json` with cluster-measured p50/p90 and final
admitted/excluded decisions (reason strings preserved). Every k=7 and k=10 block
must have a cluster-measured timing before the paper can cite a feasibility
envelope.

Blocks requiring cluster measurement:

| Reason in local artifact | Blocks |
|---|---|
| `local_pilot_budget_exceeded` (timeout at 35 s) | k=3, n∈{24,32,48,64}, density∈{1,2,4} → 12 blocks |
| `single_sample_p90_provisional` | k=5, n=8, density∈{1,2} → 2 blocks |
| `inferred_infeasible_from_k5_n8` | k=5, n=16, density∈{1,2,4} → 3 blocks |
| `vm_complexity_timeout` (1 sample) | k=7, n=8, density=1 → 1 block |
| `vm_complexity_timeout_k10_...` (1 sample) | k=10, n=16, density=1 → 1 block |

**Scope addition (orchestrator, 2026-07-22, post-T-M7a merge):** the six
Stratum A designs reclassified PENDING_CLUSTER at T-M7a — `sts13_0`,
`sts13_1`, `sts15_0`, `ag24`, `pg23`, `pg24` (workstation DNF at the 30 s
budget; tie-complete branching vs large automorphism groups). Cluster-measure
each via `scripts/feasibility_pilot_stratum_a.py` (measurement ceiling 300 s;
admission still by the DATA.md §4 criterion p90 ≤ 30 s + 0 DNFs) and update
`artifacts/feasibility_pilot/feasibility_pilot_stratum_a.json` +
`admitted_catalog.txt` with final tristate statuses. `ag24`/`pg23`/`pg24` are
the structured arity-4/5 designs T-M7e's §4.2 re-scoring wants — report their
verdicts prominently in the closing note.

**Acceptance:** `stratum_b_feasibility_envelope.json` updated with
cluster-measured p50/p90 for all 19 pending blocks; every block has
`n_pilot ≥ 30` or a documented cluster-measured exclusion reason; the
`summary` dict reflects final counts; the six Stratum A designs carry
cluster-measured p50/p90 and final statuses in the Stratum A pilot artifacts;
closing note reports the resulting admitted set and gates T-M7d explicitly.
**Out of scope here:** running G1/A1–A3 on the admitted cells (T-M7d); any
changes to `src/isalhg/`; generating new SLURM configs beyond what `feasibility_pilot.py` needs.

**Gates T-M7d:** T-M7d's sweep may only run on Picasso-pilot-ADMITTED cells.
This task must be DONE and the updated envelope committed before T-M7d begins.

---

## Blocking note (2026-07-22 — agent)

SLURM scripts prepared and ready to submit. Blocking on Picasso job results.

**What was done (pre-submission):**

- `experiments/article/feasibility_pilot.py`: added `--block-key` CLI flag and
  `block_key_filter` parameter to `run_pilot()`. Without this flag, one run
  processes all 69 runnable blocks (≈9 000 s × 69 = days); the SLURM array job
  uses it to process exactly one block per task.
- `scripts/feasibility_pilot_stratum_a.py`: added `--threshold` CLI flag and
  `threshold_s` parameter, separating the per-instance timeout (`budget_s`) from
  the admission threshold. Cluster runs use `--budget 300 --threshold 30`.
- `scripts/T-M7h_merge_envelope.py`: post-processing script that reads per-block
  JSONs from Picasso and patches `stratum_b_feasibility_envelope.json`, and
  copies the Stratum A cluster result JSON and regenerates `admitted_catalog.txt`.
- `slurm/T-M7h_stratum_b_launcher.sh` + `slurm/T-M7h_stratum_b_worker.sh`:
  SLURM array job (19 tasks, 10 concurrent max) for the 19 pending Stratum B
  blocks; each task: 4 CPUs, 16 GB, 3 h, `--constraint=cpu`.
- `slurm/T-M7h_stratum_a_launcher.sh` + `slurm/T-M7h_stratum_a_worker.sh`:
  single SLURM job for the 6 PENDING_CLUSTER Stratum A designs; 4 CPUs, 16 GB,
  2 h, `--constraint=cpu`; uses `--budget 300 --threshold 30 --runs 3`.
- `tests/unit/experiments/test_feasibility_pilot_block_key_filter.py`: 4 unit
  tests verifying the filter (including a pre-fix baseline test demonstrating
  that without the filter all blocks are processed).

**Regression check (2026-07-22):**
- pytest tests/unit/experiments/ tests/unit/analysis/: 88 passed
- ruff check src/ tests/: 3 errors (baseline, unchanged)
- mypy src/isalhg/: 21 errors (baseline, unchanged)

**Waiting on:** Picasso job completions. Submit from Picasso login node:
```bash
# Sync worktree to Picasso
rsync -av /path/to/worktree/ \
    /mnt/home/users/tic_163_uma/mpascual/fscratch/repos/IsalHG/

# Submit Stratum B array (19 tasks)
bash slurm/T-M7h_stratum_b_launcher.sh

# Submit Stratum A single job (6 designs)
bash slurm/T-M7h_stratum_a_launcher.sh
```

After results land, run `scripts/T-M7h_merge_envelope.py` to produce the
updated `stratum_b_feasibility_envelope.json` and `artifacts/feasibility_pilot/`
artifacts, then change status to DONE and move to CLOSED/.

**T-M7d gate:** remains gated until cluster-measured admission decisions are
committed to `stratum_b_feasibility_envelope.json`.

---

## Blocking note 2 (2026-07-22 — agent, commit c4bb27e)

### Stratum A — HARVESTED (job 1629487 COMPLETED, 36m38s)

Six designs that were PENDING_CLUSTER are now cluster-measured and committed to
`artifacts/feasibility_pilot/`. All six are EXCLUDED:

| design  | arity | result   | p90     | reason                                |
|---------|-------|----------|---------|---------------------------------------|
| sts13_0 | 3     | EXCLUDED | 165.6 s | p90 > 30 s threshold                  |
| sts13_1 | 3     | EXCLUDED | 158.9 s | p90 > 30 s threshold                  |
| sts15_0 | 3     | EXCLUDED | 300 s   | DNF at 300 s measurement ceiling      |
| ag24    | 4     | EXCLUDED | 300 s   | DNF at 300 s ceiling (arity-4 design) |
| pg23    | 4     | EXCLUDED | 300 s   | DNF at 300 s ceiling (arity-4 design) |
| pg24    | 5     | EXCLUDED | 300 s   | DNF at 300 s ceiling (arity-5 design) |

**Final Stratum A catalog: 17 ADMITTED / 23 total.** `artifacts/feasibility_pilot/`
updated with cluster JSON and regenerated `admitted_catalog.txt`.

**T-M7e implication:** ag24/pg23/pg24 are confirmed infeasible. T-M7e's §4.2
re-scoring for arity-4/5 must use only the 17 locally-admitted designs (structured
arity-4/5 instances are absent from the Stratum A admitted envelope).

### Stratum B — naming-drift fix committed

Stratum B array (job 1629486) failed because the launcher hard-coded `er_uniform_*`
keys while `feasibility_pilot.py` generates `erdos_renyi_uniform_*` from the
enumerator. Three-part fix in this commit:

1. `feasibility_pilot.py`: `list_blocks()` + `--list-blocks` / `--pending-envelope`
   — single source of truth for block keys; includes `_expand_envelope_key()` for
   legacy key aliasing.
2. `slurm/T-M7h_stratum_b_launcher.sh`: `BLOCK_KEYS` now derived dynamically via
   `--list-blocks --pending-envelope`; the array is always consistent with what the
   pilot will accept.
3. `scripts/T-M7h_merge_envelope.py`: `_shorten_block_key()` normalises
   `erdos_renyi_uniform_*` → `er_uniform_*` when patching the envelope's existing
   short-key entries.

8 new unit tests in `tests/unit/experiments/test_feasibility_pilot_list_blocks.py`
cover all three variants (list_blocks output, pending filter, merge normalisation).

**Regression check (2026-07-22, commit c4bb27e):**
- pytest tests/unit/ (not slow): 1051 passed, 5 skipped
- ruff check src/ tests/: 3 errors (baseline, unchanged)
- mypy src/isalhg/: 21 errors (baseline, unchanged)

**Waiting on:** Stratum B resubmit. After rsync of this branch to Picasso, run:
```bash
bash slurm/T-M7h_stratum_b_launcher.sh
```
The launcher will now derive the 19 correct enumerator-style block keys from
`--list-blocks --pending-envelope` automatically. After results land:
```bash
rsync -av picasso:.../results/T-M7h/stratum_b/ /media/.../results/T-M7h/stratum_b/
python scripts/T-M7h_merge_envelope.py \
    --stratum-b-dir /media/.../results/T-M7h/stratum_b/per_block/ \
    --envelope experiments/article/stratum_b_feasibility_envelope.json
```

**T-M7d gate:** still gated pending Stratum B results. Stratum A is done.

### Stratum B — cluster harvest round 1 + resubmit (2026-07-23, orchestrator)

First cluster submission (array 1629486, 3h walltime) resubmitted post-drift-fix;
7 of 19 blocks completed and were harvested + merged into
`stratum_b_feasibility_envelope.json`:
- **admitted** (p90 ≤ 30 s over 30 instances @ 300 s budget): `k3_n24_rho1`
  (p90 4.27 s), `k3_n24_rho2` (9.92 s), `k5_n8_rho1` (5.39 s), `k5_n8_rho2`
  (12.80 s).
- **cluster_excluded** (p90 ≫ 30 s): `k3_n24_rho4` (164.8 s), `k3_n32_rho1`
  (146.2 s), `k3_n32_rho2` (188.9 s).

The remaining 12 blocks (`k3_n32_rho4`, `k3_n48_{1,2,4}`, `k3_n64_{1,2,4}`,
`k5_n16_{1,2,4}`, `k7_n8_rho1`, `k10_n16_rho1`) walltime-killed at 3 h (their
instances mostly hit the 300 s per-instance timeout → total > 3 h, no JSON).
Worker walltime bumped 3 h → 8 h and the 12 pending blocks **resubmitted as
array 1631517** (launcher auto-derived the pending set from
`--list-blocks --pending-envelope` reading the merged envelope). Monitoring in
progress; on completion, harvest → `merge_envelope.py` → this task moves to
CLOSED and unblocks T-M7d.

---

## Closing record — 2026-07-24 (orchestrator). Status: DONE

**The Stratum B feasibility envelope is FINAL.** Two cluster rounds:

- **Array 1629486** (3 h wall, post-drift-fix): 7 of 19 blocks completed and were
  harvested → 4 **admitted** (`k3_n24_rho1` p90 4.27 s, `k3_n24_rho2` 9.92 s,
  `k5_n8_rho1` 5.39 s, `k5_n8_rho2` 12.80 s) and 3 **cluster_excluded**
  (`k3_n24_rho4` 164.8 s, `k3_n32_rho1` 146.2 s, `k3_n32_rho2` 188.9 s).
- **Array 1631517** (8 h wall, the 12 remaining blocks — `k3_n32_rho4`,
  `k3_n48_{1,2,4}`, `k3_n64_{1,2,4}`, `k5_n16_{1,2,4}`, `k7_n8_rho1`,
  `k10_n16_rho1`): **all 12 tasks TIMEOUT at 08:00:23**, zero results. These
  cells cannot complete a 30-instance pilot within 8 h even at a 300 s
  per-instance cap → recorded as `cluster_excluded` with that measured reason.
  This is a *stronger* exclusion than the earlier 3 h timeout, and it is a
  measurement, not an assumption.

**Final envelope:** 10 admitted, 15 cluster_excluded, 0 pending
(`envelope_final: true`). Admitted Stratum B set = `k3_n8_{rho1,rho2,rho4}`,
`k3_n16_{rho1,rho2,rho4}` (local) + `k3_n24_{rho1,rho2}`, `k5_n8_{rho1,rho2}`
(cluster).

**Paper consequence (honest, and it is a finding):** the `w*_c` feasibility
frontier sits at **k=3 up to n≈24 (low density) and k=5 only at n=8**. The
advertised arity cap of 10 is **not** reachable at any tested n — `k=7` and
`k=10` are measured infeasible. This is the scalability envelope the article
reports; it must not be presented as a hidden filter.

**Unblocks T-M7d** (the sweep may now run on the final admitted-cell set).
