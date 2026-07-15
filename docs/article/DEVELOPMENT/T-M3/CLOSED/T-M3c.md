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
