# T-M7h — Picasso full feasibility pilot for the non-admitted Stratum B region
**Declared:** 2026-07-22 15:40 CEST
**Status:** OPEN
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
