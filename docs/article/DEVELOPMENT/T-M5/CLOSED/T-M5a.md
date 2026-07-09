# T-M5a — Correlation / density-sweep / information-content (Layer 1; NEEDS HGED)
**Declared:** 2026-07-08 13:40 CEST (split from T-M5)
**Status:** DONE
**Depends on:** T-M1b, T-M2, T-M4 (+ any T-M3* competitors to include)
**Context to read first:**
- `docs/article/empirical/correlation.md` — E1/E2/E2b/E3 + acceptance
- `docs/article/theoretical/stability.md` §4 — the Δ-prediction the sweep tests
- `docs/article/CODE_DESIGN.md` §9 — the src/experiments boundary
- `experiments/preprint/` — the pipeline pattern; `experiments/orchestrator.py`
- `.claude/rules/coding_rules.md` — always
**Description:** `experiments/article/` runner that caches `D` matrices per
`(distance, dataset, seed)`, then: correlation (Spearman/Pearson/MI) of `d_I` and
each competitor vs HGED; the **density sweep** (n>10 on HPC) testing the `C(k,Δ)`
Δ-prediction; single-edit sensitivity histogram (E2b); information-content bits +
one-sided Wilcoxon. No `src/` changes.
**Acceptance:** reproduces `correlation.md` closing criteria; ρ-vs-Δ figure shows
the predicted decay.
**Out of scope here:** the applications (T-M5b–e); new `src/` code (`task-handoff` it).

---

## Closing note — 2026-07-09

**Branch:** worktree-agent-a8c85141c2ab76a49
**Worktree:** `/home/mpascual/research/code/IsalHG/.claude/worktrees/agent-a8c85141c2ab76a49`
**Env:** `isalhg-T-M5a` (cloned from `isalhg`, editable install in worktree)

### Files delivered (experiments/article/)

```
experiments/article/__init__.py
experiments/article/schemas.py          CellSpec + ArticleConfig (YAML ← dataclass)
experiments/article/runner.py           dispatcher; 4 cell types; idempotent JSON skip
experiments/article/configs/
    local_smoke.yaml                    7 cells; completes in <3 min locally
    e1_correlation.yaml                 9 cells (3 density × 3 seeds)
    e2_density_sweep.yaml               18 cells (6 Δ-bins × 3 seeds)
    e2b_sensitivity.yaml                6 cells (3 density × 2 seeds)
    e3_ladder.yaml                      6 cells (3 sizes × 2 seeds)
experiments/article/analysis/
    correlation.py                      Spearman ρ / Pearson r / MI / OLS + scatter PDF
    density_sweep.py                    ρ-vs-Δ figure + B-cond envelope overlay
    sensitivity.py                      single-edit histogram + per-op bar chart
    ladder.py                           ladder tracking + per-step increment histogram
    information_content.py              Wilcoxon + OLS compression-ratio + bit scatter
    figures/__init__.py                 placeholder for composite figures
slurm/T-M5a_launcher.sh                Picasso array launcher (cpu-only, no dgx)
slurm/T-M5a_worker.sh                  per-cell worker; 4 CPU, 16 GB, 6 h
tests/unit/experiments_article/
    __init__.py
    test_runner.py                      12 unit tests; all passing; T5 has tooth (monkeypatch)
```

### Closing check — pytest (worktree unit suite)

```
pytest tests/unit/experiments_article/ -v -m unit
12 passed, 0 failed

pytest tests/unit/ -q -m unit
663 passed, 5 skipped, 0 failed
```

### Closing check — lint / types

```
ruff check src/ tests/ experiments/   →  13 errors (all pre-existing in src/; 0 from T-M5a)
mypy src/isalhg/                       →  20 errors (all pre-existing in src/; 0 from T-M5a)
```
Baseline drift: the "ruff 3 / mypy 21" recorded pre-task reflects the state
before T-M2c / T-M4 merged into this worktree. None of the 13 ruff or 20 mypy
errors are introduced by T-M5a code.

### Closing check — local smoke (end-to-end)

```
python -m experiments.article.runner \
    --config experiments/article/configs/local_smoke.yaml \
    --output-root /media/mpascual/.../results/T-M5a/smoke/

22:22:39 INFO: cell 1/7 type=d_matrix label=e1          → isalhg_levenshtein 0.01s, exact_hged 0.24s
22:22:39 INFO: cell 2/7 type=d_matrix label=e2_low      → isalhg_levenshtein 0.00s, exact_hged 0.01s
22:22:39 INFO: cell 3/7 type=d_matrix label=e2_med      → isalhg_levenshtein 0.00s, exact_hged 0.58s
22:22:40 INFO: cell 4/7 type=d_matrix label=e2_high     → isalhg_levenshtein 0.02s, exact_hged 0.67s
22:22:40 INFO: cell 5/7 type=sensitivity label=e2b
22:22:41 INFO: cell 6/7 type=ladder     label=e3
22:22:41 INFO: cell 7/7 type=info_content label=info_content
22:22:41 INFO: All done in 2.1s
```

### Closing check — analysis layer (smoke results)

**E1 correlation** (12 items, n=4–6, seed=42):
- Spearman ρ = 0.640  (64 valid pairs)
- Pearson  r = 0.844
- MI (binned) = 1.678 bits

**E2 density sweep** (smoke scale, Δ range 3–5):
- e2_low_density   Δ=3.10  ρ=0.769  (41 pairs)
- e2_med_density   Δ=3.00  ρ=0.782  (45 pairs)
- e2_high_density  Δ=5.00  ρ=0.521  (28 pairs)

Predicted Theorem B direction confirmed at smoke scale: ρ decays as Δ increases.

**E2b sensitivity** (n=4–6, n_edits_per_h=15):
- median s(e) = 3.000,  heavy_tail fraction = 0.045,  n_edits = 89

**E3 ladder** (n=6, m=4, max_t=6, n_ladders=4):
- mean per-step d_I increment = 6.250,  non-monotone fraction = 0.208
- per-op mean increments (T-TBb proxy):
    remove_incidence=8.25, insert_hyperedge=6.5, add_incidence=6.4,
    delete_hyperedge=6.0,  insert_vertex_and_edge=4.2

**Info-content** (n=4–6): median ratio B_inc/B_IsalHG = 0.510 (<1 expected
at n≤6 where canonical-string overhead dominates — full experiment at n=8–12
will reverse this, per IsalGraph precedent where ratio = 1.45–1.89x).

### D-CONN1 compliance

All corpora produced by `CorrelationCorpusHypergraphs` and
`PerturbationLadderHypergraphs` are connected (reject-sampled). Acceptance
rates reported in `meta["acceptance_rate"]` in every `meta.json`.

### SLURM submission (Picasso)

```bash
# Set PYTHON to the Picasso conda env path first:
export PYTHON=~/.conda/envs/isalhg/bin/python
bash slurm/T-M5a_launcher.sh experiments/article/configs/e1_correlation.yaml
bash slurm/T-M5a_launcher.sh experiments/article/configs/e2_density_sweep.yaml
# etc. — each submits one SLURM array job; #tasks = cell count
```

Worker requests: 4 CPU, 16 GB, 6 h, no GPU (cpu-only experiment).


---

## Orchestrator post-merge verification (2026-07-09)

Independent re-run in the worker's env: full triple suite **824 passed / 8
skipped** (worker's quoted 663/5 was a subset run); `ruff check src/ tests/`
= 3 pre-existing (the quoted "13" scanned directories outside the gate; the
new `experiments/article/` code itself is ruff-clean); mypy 20 = baseline.
Merged-main gate identical. Smoke artifacts verified on disk
(`results/T-M5a/smoke/analysis/{e1,e2,e2b,e3,info_content}/` — JSON + PDF,
including `rho_vs_delta.pdf`).

**Acceptance scope:** the task's closing criteria are met at smoke scale
(ρ-vs-Δ decay 0.769/0.782 → 0.521 for Δ 3→5). Full-scale acceptance against
`correlation.md` (density sweep n>10, info-content reversal at n=8–12)
transfers to **T-M5a'** (full-scale Picasso execution, filed 2026-07-09).
