# D-ART3 re-scope probes (2026-09-03)

Scripts and raw results of the five measurements reported in
`docs/article/D_ART3/foundation/probes_2026-09.md`. They were run from a
session scratchpad with `PYTHONPATH` set to that directory and
`~/.conda/envs/isalhg/bin/python`; seeds are fixed inside each script
(master seed 20260903).

| Probe | Script(s) | Raw results |
|---|---|---|
| §1 planted-consensus pilot | `preflight.py`, `pilot_consensus.py`, `pilot_analyze.py`, `pilot_addendum.py` | `pilot_consensus_results.json` |
| §2 bipartite-GED metricity | `probe_bpged_metric.py` | `probe_bpged_metric_results.json` |
| §3 ambient reach + ball coverage | `reach_sizing.py`, `reach_probe.py`, `reach_analyze.py` | `reach_results.json`, `reach_log.txt` |
| §4 ARB contact ego-KBs | `probe_arb_egonets.py`, `aggregate_timing.py` | `probe_stats.json`, `probe_timing.json` |
| §5 WD50K entity KBs | `probe_wd50k.py`, `probe_worker.py` | `probe_wd50k_results.json` (data under `/media/.../isalhg/data/wd50k/`) |

Two further probes were added on 2026-09-04, after the PI ratified the scope:

| Probe | Script(s) | Raw results |
|---|---|---|
| §9 addressing / topology (RQ1) — pointer vs global-rank vs local-colour fact addressing | `f4_topology/{f4_encodings,f4_corpora,f4_exec,run_probe,run_ea_full,probe_wl_locality,render_tables,merge_ea_shards}.py`, `f4_topology/slurm/` | `f4_topology/m*_results.json`, `f4_topology/probe_f4_topology.md` |
| §9 follow-ups — the regime split, and the locally-keyed third design | `f4_topology/{followup_ndc_regime,f4_local_key,run_local_key,render_local_key}.py` | `f4_topology/{followup_ndc_regime,n*_results}.json`, `probe_f4_followup.md`, `probe_f4_local_key.md` |

The per-pair record dumps (`*_rows_*.json`, 1.6–3.1 MB each) are **not
committed** — see `.gitignore` here. They are regenerable from these scripts
with the seeds pinned in each report; the aggregated statistics the reports
quote are committed.

A Picasso array (`f4-ea`, job `2206622`) widens the slow pointer-alphabet arm's
coverage; its launcher/worker are under `f4_topology/slurm/` and its shards land
in `~/fscratch/results/f4_topology/ea/`. Note for future submissions of this
engine: the cluster build is AVX-512, so `--constraint=sd` is required —
`--constraint=sr` dies with SIGILL.

These are diagnostics, not library code: they do not follow the package
conventions and are kept for provenance until the ledger tasks re-implement
the measurements inside `src/` and `experiments/`.
