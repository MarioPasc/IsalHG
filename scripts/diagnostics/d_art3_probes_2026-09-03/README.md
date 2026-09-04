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

These are diagnostics, not library code: they do not follow the package
conventions and are kept for provenance until the ledger tasks re-implement
the measurements inside `src/` and `experiments/`.
