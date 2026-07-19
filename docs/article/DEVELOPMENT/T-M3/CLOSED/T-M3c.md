# T-M3c — `NetLSDDistance` (optional spectral, pip)
**Declared:** 2026-07-08 13:40 CEST (split from T-M3)
**Status:** DONE
**Depends on:** T-M1a
**Context to read first:**
- `docs/article/COMPETITORS.md` §2 (optional spectral) · `RELATED_WORK.md` — Tsitsulin et al. 2018, `pip install netlsd`
- `src/isalhg/core/levi_reduction.py` (post-M1a) — heat-trace on the Levi/clique expansion
- `.claude/rules/coding_rules.md` — always
**Description:** `HypergraphDistance` = L2 between NetLSD heat-trace signatures of
the Levi expansion. Register. (Optional fifth competitor.)
**Acceptance:** `matrix()` runs; guarded `netlsd` import.
**Out of scope here:** promoting it to a headline baseline (it is the spectral aside).

---
**Closed:** 2026-07-15

**Closing-check output (2026-07-15):**

```
pytest tests/unit/metric_space/test_netlsd.py -v
10 passed, 1 skipped (HIC RHG-10 data file not present on disk)

pytest tests/unit/ -q
678 passed, 6 skipped in 7.77s

ruff check src/isalhg/metric_space/representations/netlsd.py tests/unit/metric_space/test_netlsd.py
All checks passed!

mypy src/isalhg/ --ignore-missing-imports
Found 20 errors in 6 files (baseline 22; netlsd.py adds 0 new errors)
```

**Notes:**
- Task premise error: `hic_name="MUTAG"` is not a valid HIC dataset name (MUTAG is a
  graph-classification benchmark). Valid names are RHG-10/3/Table/Pyramid, IMDB-*,
  Steam-Player, Twitter-Friend. Fixed to "RHG-10". HIC file absent on disk → skipped.
- netlsd.heat() accepts scipy sparse adjacency matrices directly.
- Iso-pair L2 distance on Fano plane: 3.4e-15 (well within atol=1e-6).
- register_distance("netlsd_l2", NetLSDDistance) is at module bottom (same as wl.py).
  Registry _LAZY_MODULES left for orchestrator to wire at merge.

---
**v3 rescope note (D-ART2, 2026-07-18; appended at the S1 reconciliation
merge).** Promoted from optional fifth to **full member**: NetLSD runs on
every corpus, including those HyperCOT's `O(n³)`/pair cannot reach, so it is
the guaranteed at-scale fair baseline. The v3 acceptance additions —
`matrix()` on the planted corpus; iso pairs → distance 0 (sanity) — are
pending verification in the S2 verification pass (SESSIONS.md).

---
**S2 verification (2026-07-19 10:58 CEST, orchestrator).** Promoted
acceptance verified: `netlsd_l2.matrix()` on the planted corpus (18
hypergraphs = 4 families × 3 members + 4 permuted copies + Fano pair, seed
0): symmetric, zero diagonal; iso-pair max 1.51e-14 (within the spectral
tolerance); off-diag median 0.183. Two environment facts surfaced: (a)
`netlsd` was **not installed in the main `isalhg` env** until now (the
T-M3c closing tests ran only in the worker's cloned env) — installed
`netlsd 1.0.2` and added it to the `bench` extra; (b) the HIC smoke test's
`HIC_ROOT` was missing the `/hypergraph` segment, so it skipped as "data
absent" on a machine where the data was present — path fixed, smoke now
runs (11 passed, 0 skipped).
