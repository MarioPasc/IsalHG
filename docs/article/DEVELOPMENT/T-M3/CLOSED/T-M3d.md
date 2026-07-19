# T-M3d — `HyperCOTDistance` (pinned conda env, subprocess)
**Declared:** 2026-07-08 13:40 CEST (split from T-M3)
**Status:** DONE (env rebuilt + end-to-end verified 2026-07-19; see S2 verification note)
**Depends on:** T-M1a
**Context to read first:**
- `docs/article/COMPETITORS.md` §2 (dual role: theory anchor + competitor) · `RELATED_WORK.md` — Chowdhury et al. 2024, `samirchowdhury/HyperCOT` (pins `hypernetx==1.2`, `POT==0.8.0`)
- `docs/article/CODE_DESIGN.md` §3.2 — `SubprocessRepresentation`
- `src/isalhg/iso_backends/subprocess_base.py` — the subprocess pattern to mirror
- `.claude/rules/coding_rules.md` — always
**Description:** `SubprocessRepresentation` base + `HyperCOTDistance`: serialize
the corpus, shell out to a dedicated `isalhg-hypercot` conda env, parse back the
distance matrix. Register. Heaviest/most independent competitor.
**Acceptance:** `matrix()` runs on the correlation corpus via the pinned env;
distance 0 on isomorphic pairs; `SubprocessRepresentationError` with a setup hint
when the env is absent.
**Out of scope here:** the head-to-head study (T-M5a); a learned/GNN baseline (dropped).

---

## Closing note — 2026-07-15 (agent task/T-M3d)

**BLOCKED: no network access; `isalhg-hypercot` env cannot be built.**

### What was delivered

All five file-lane deliverables are committed on branch `task/T-M3d`:

- `src/isalhg/metric_space/representations/subprocess_base.py` —
  `SubprocessRepresentation` base: corpus JSON serialisation, subprocess
  invocation of a pinned-env Python worker, dense matrix parsing, temp-file
  cleanup.
- `src/isalhg/metric_space/representations/hypercot.py` —
  `HyperCOTDistance(SubprocessRepresentation)`: `name="hypercot"`,
  `PINNED_ENV="isalhg-hypercot"`, `WORKER_SCRIPT=scripts/hypercot_worker.py`;
  self-registers via `register_distance("hypercot", HyperCOTDistance)`.
- `scripts/hypercot_worker.py` — corpus JSON → HyperNetX 1.2 hypergraphs →
  `hypercot.hypercot_distance(H1, H2)` pairwise → output JSON matrix.
  Header documents upstream URL, commit hash placeholder, pinned versions,
  and exact function called.
- `envs/hypercot.yml` — conda spec: `python=3.10`, `hypernetx==1.2`,
  `POT==0.8.0`, `numpy`; HyperCOT installed manually from cloned repo.
- `tests/unit/metric_space/test_hypercot.py` — guard-path (5, always run)
  + end-to-end (4, skip when env absent) + HIC smoke (1, skip when env
  absent or HIC_ROOT missing).

### Test results

Guard-path: **5 passed** (confirmed pre-fix failure: bogus env name raises
`SubprocessRepresentationError` with setup hint; registration check passes).
End-to-end + HIC smoke: **5 skipped** (env absent). Full suite: 752 passed,
10 skipped, 0 failed.

ruff: 0 new errors (baseline 3, pre-existing). mypy: 0 new errors on new
files (baseline 20 errors in 6 pre-existing files).

### Env build failure (exact errors)

```
$ git clone https://github.com/samirchowdhury/HyperCOT
fatal: unable to access 'https://github.com/samirchowdhury/HyperCOT/':
Could not resolve host: github.com
```

No local copy of HyperCOT was found on any mounted path. The conda cache
contains `hypernetx-2.4.0` but not `hypernetx==1.2` or `POT==0.8.0`.
`conda env create -f envs/hypercot.yml` would also fail (no network to
install the pinned packages from PyPI).

**Unblocks when:** network access is restored; then run:
```
conda env create -f envs/hypercot.yml
git clone https://github.com/samirchowdhury/HyperCOT /tmp/HyperCOT
~/.conda/envs/isalhg-hypercot/bin/pip install -e /tmp/HyperCOT
# update scripts/hypercot_worker.py header with actual commit hash
pytest tests/unit/metric_space/test_hypercot.py -v
```

### Premise correction

The task spec quoted `hic_name="MUTAG"` for the HIC smoke test. "MUTAG" is
not a valid `HICAtlasDataset` name; the valid names are the 12 HIC atlas
datasets (`"RHG-10"`, `"RHG-3"`, `"IMDB-Dir-Form"`, …). The smoke test
uses `hic_name="RHG-10"` instead.

### Worker API assumption

`scripts/hypercot_worker.py` calls `hypercot.hypercot_distance(H1, H2)`.
This function name is inferred from the paper and package conventions; it
must be verified against the actual source when the env is built. If the
name differs, only `scripts/hypercot_worker.py` needs updating (no change
to `src/` files).

---

## S2 verification note — 2026-07-19 10:58 CEST (orchestrator)

The BLOCKED state above was superseded in two steps:

1. **`c2fddd6` (2026-07-15, pre-reconciliation):** the coordinator pre-built
   the env on that machine and rewrote the worker with the verified upstream
   API (`get_hgraph_dual → convert_to_line_graph → get_v → get_omega(...,
   "jaccard_index")`, then `cot.cot_numpy(...)[2]` per pair), replacing the
   inferred `hypercot_distance` call. This file was never updated then —
   fixed now.
2. **S2 rebuild (2026-07-19, this machine):** `isalhg-hypercot` env rebuilt
   from the `envs/hypercot.yml` recipe verbatim (network restored); HyperCOT
   cloned at upstream HEAD `5045539ac1465626f985813aabcf89489d5c98a4`
   (2023-01-19 — the repo never moved, so the `f190266` hash previously in
   the worker header was a copy-paste from the HPD vendor commit; header
   corrected).

Verification against acceptance (all clauses):

```
pytest tests/unit/metric_space/test_hypercot.py -m "" -q
10 passed  (guard-path 5, end-to-end 4, HIC smoke 1 — the smoke ran on real
            RHG-10 data after fixing the stale HIC_ROOT path, which was
            missing the /hypergraph segment; data was on disk all along)

matrix() on the S2 planted corpus (18 hypergraphs, 5 planted iso pairs):
symmetric, zero diagonal, non-negative; iso-pair max 7.1e-16; off-diag
median 5.36. PASS — distance 0 on isomorphic pairs confirmed.
```
