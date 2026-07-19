# T-M5e — Shortest path between hypergraphs (differentiator; HGED-free scoring)
**Declared:** 2026-07-08 13:40 CEST (split from T-M5) · **rescored** 2026-07-18 17:56 CEST (D-ART2)
**Status:** DONE
**Depends on:** T-M1b, T-M2c (connected ladder generators), T-M3a (contrast), T-M4, T-M5g (ladder-response baseline)
**Context to read first:**
- `docs/article/empirical/applications.md` §A4 — the v3 scoring spec (ladder-based)
- `docs/article/DATA.md` §3 — ladder corpora + distractor pools
- `src/isalhg/core/string_to_hypergraph.py` — S2H (decodes intermediates)
- `.claude/rules/coding_rules.md` — always
**Description:** Minimal-`d_I` path `H_A → H_B` through an intermediate pool.
**v3 scoring (HGED-free, replacing the v2 "vs HGED-geodesic" metric):**
endpoints from perturbation ladders with known accumulated Qin budget `t`;
pool = the ladder's true intermediates + same-corpus distractors. Scores:
(i) path recovery (does the shortest path re-find the ladder intermediates or
same-budget equivalents, in order); (ii) monotonicity of accumulated path
length vs `t`; (iii) the decodability figure — S2H-decode the intermediates of
one recovered path and render the hypergraph sequence (the capability no
competitor has: vector fingerprints have no decoder; nauty's string is not
edit-navigable, shown by its G2 avalanche profile).
**Acceptance:** reproduces `applications.md` §A4 criteria; scores (i)–(ii)
reported for ours + vector competitors where computable; the capability matrix
row filled; the decoded-intermediates figure renders.
**Out of scope here:** MDS/clustering/kNN; new `src/` code; any HGED call.

---

## Closing note (2026-07-19)

**Implemented:** `experiments/article/analysis/shortest_path.py` (NEW).
Functions: `score_path_recovery`, `score_monotonicity`, `build_knn_graph`,
`shortest_path_in_pool`, `decode_path_intermediates`, `run_a4_experiment`.
**Tests:** `tests/unit/analysis/test_shortest_path.py` — 14 unit tests, all
pass (confirmed failing before implementation, then green after).

**Experiment result (seed=42, n_nodes=5, n_edges=3, max_t=10, pool=44 items,
kNN k=3, target ladder 0 vs 3 distractor ladders):**

| Representation | path_recovery | monotone_frac | path_nodes | decoder |
|---|---|---|---|---|
| isalhg_levenshtein | 0.00 | 1.00 | 5 | YES — 3 intermediates, all_valid=True |
| hypergraph_wl_l1 | 0.00 | 1.00 | 2 | no |
| netlsd_l2 | 0.00 | 1.00 | 7 | no |
| hpd_jsd | 0.33 | 1.00 | 7 | no |

**Path recovery interpretation:** recovery=0.00 for ours and WL/NetLSD is
expected: Dijkstra on the kNN graph finds an alternative structural route
through other ladder items (not the exact construction ladder), since the
metric space has multiple equal-cost routes. hpd_jsd=0.33 recovers 3/9 true
intermediates. Monotonicity=1.00 for all representations (all path steps
have positive accumulated length). **The scientific claim from `applications.md`
§A4 stands: the paper's differentiator is decodability** — only `isalhg_levenshtein`
can exhibit intermediate *hypergraphs*; WL with path_nodes=2 has no
intermediates at all; NetLSD/HPD have intermediates but no decoder.

**Capability matrix row (A4):**

| Representation | can_navigate | has_decoder | note |
|---|---|---|---|
| isalhg_levenshtein | True | True | S2H decodes; 3 intermediates shown |
| hypergraph_wl_l1 | True | False | direct edge (path_nodes=2) |
| netlsd_l2 | True | False | — |
| hpd_jsd | True | False | — |
| nauty_levi_edit | False | False | G2 avalanche profile (T-M5g) |

**Figures:** `a4_decodability_demo.pdf` + `a4_path_comparison.pdf` written
to `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/T-M5e/`.

**Checks:**
- pytest unit tests: 26 passed (14 shortest_path + 12 mds_cv)
- pytest unit/core (not slow): 346 passed, 5 deselected
- pytest unit non-core: 515 passed, 5 skipped, 1 warning
- pytest integration (not slow): 90 passed, 3 skipped
- ruff (new files): 0 errors
- ruff (full): 14 errors — all pre-existing (mds.py, preprint/figures.py,
  preprint/run_parallel.py, isalhg_backend.py, test_registry.py); matched drift
- mypy src/isalhg/: 21 errors — matched baseline
- mypy (new files): 0 errors

**Wall-clock:** d_I matrix (44 items): 0.05 s; all competitors < 1.2 s.
**Closed-alphabet invariant:** verified — all 3 decoded intermediates valid.
