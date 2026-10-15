# KNN probe — experiment engineer work log (opened 2026-10-15 08:15 CEST)

**Status (2026-10-15 09:38 CEST): probe COMPLETE.** All three kill criteria fired (H-KNN-B 12/12
cells, H-KNN-A on NDC-substances, H-KNN-mix on both WD50K collections); see §6–§7. Commits on
`worktree-agent-a7cd2b6fdd3a1dd31`: `f9e24e7` (library + tests), `b607fe0` (CLI + diagnostics),
`e0bfa0f` (figure), then this log. Results: `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/
results/KNN_2026-10-15/probe/` (`SUMMARY.md`, `summary.json`, `cells/`, `items/`, figures,
`ablation_wstar_orbit/`).

Worktree `/home/mpascual/research/code/IsalHG/.claude/worktrees/agent-a7cd2b6fdd3a1dd31`,
branch `worktree-agent-a7cd2b6fdd3a1dd31`, base `19245a3`. Model `claude-opus-5-5`.
Pre-registration (binding): `docs/article/D_ART3/experiments/KNN_2026-10-15/LOG.md` in the main
checkout (not on this branch's base; read from the main checkout path).

## 0. The prompt (verbatim)

```
# Task: Probe two pre-registered kNN / k-medoids experiments on the TKDE knowledge-base collections

You are the **experiment engineer** of a small research group. The orchestrator (`main`) leads it. You will stay on this project after the probe, through the full run on the Picasso cluster, so build code you can scale, and keep notes you can resume from.

## Context (read first)
- **The pre-registration, binding: `/home/mpascual/research/code/IsalHG/docs/article/D_ART3/experiments/KNN_2026-10-15/LOG.md`.** Read all of it.
  - Implement Designs A and B of §2 exactly, test the hypotheses of §3, and do not change a kill criterion.
  - If something in the design is impossible or ill-posed, message `main` and record your assumption.
- **The paper.** An IEEE TKDE article, "Knowledge bases as words". It represents each small labelled n-ary knowledge base (KB) by a canonical instruction word, the ordered walk `w°` (code name `isal_ow_struct`). `d_I` is the Levenshtein distance between words. It is a metric on isomorphism classes and is local under *pendant* edits, which add or remove a statement together with its own value. It is not local under interior edits. The PI wants a kNN classification or k-medoids clustering experiment, with an attractive figure.
- **Closest prior experiment, C8 (near-duplicate retrieval).**
  - Write-up: `/home/mpascual/research/code/IsalHG/docs/article/D_ART3/experiments/NEWPOS_2026-10-13/C8_NEAR_DUPLICATE_RETRIEVAL.md`.
  - Code to reuse: `/home/mpascual/research/code/IsalHG/scripts/newpos/neardup.py`, which provides `down_neighbours`, `is_star`, ties at expected rank and the Holm / rank-biserial helpers; `scripts/newpos/build_ow_matrix.py` (`get_distance(arm).matrix(hs)`).
- **Library code (read-only):**
  - `src/isalhg/datasets/kb/{base.py,corruptions.py,ndc_quarterly.py,wd50k.py,io.py}`. `base.py` provides `KBRecord`, `compact`, `make_record` and `iso_fingerprint`; `corruptions.py` has seeded removals; `ndc_quarterly.py` holds the real NDC versions per node and window.
  - The distance registry: `src/isalhg/metric_space/registry.py` (`get_distance`, `available_distances`).
- **Frozen collections:** `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE/corpora/{wd50k66,wd50k100,ndc_classes,ndc_substances}/`. Cached full matrices are in `…/IEEETKDE/matrices/`; they are for members only, and copies need new matrices.
- **Competitor arm names:** `nauty_cert`, `nauty_cert_rows`, `fact_rank`, `wl_l1`, `netlsd`, `hpd_jsd`, `bipartite_ged_assign`, `bipartite_ged_path`, `degree_seq_l1`, `size_l1`. `wstar_orbit` is the ablation.
- **Picasso notes, for later:** `/home/mpascual/research/code/IsalHG/docs/article/D_ART3/experiments/PICASSO.md`.

## What to build (in your worktree)
1. **`scripts/newpos/knn/knn_lib.py`.** Building copies (Design B: pendant removals; the empirical-mix condition), building lineage samples (Design A), computing matrices for every arm on a list of records, leave-one-out kNN with ties at expected accuracy, macro-F1, k-medoids, ARI/NMI, and the seed loop. For k-medoids, prefer `scikit-learn-extra` `KMedoids(metric='precomputed', method='pam')` or the `kmedoids` package if installed in `~/.conda/envs/isalhg`. If neither is, implement PAM (BUILD + SWAP) and test it against brute force on a tiny case. Never `pip install` into the shared env; message `main` if you need a package.
2. **`scripts/newpos/knn/probe_knn.py`**, with a CLI.
   - Probe scale: 3 seeds.
   - Design B: S = 60 sources and c = 6 copies per source, r ∈ {1, 2, 3}, on all four collections.
   - Design A: NDC-classes and NDC-substances, on a lineage sample of comparable size.
   - The empirical-mix condition on WD50K(66).
   - Outputs go to `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/KNN_2026-10-15/probe/`; create it. Write JSON per cell plus a markdown table.
3. **`scripts/newpos/knn/fig_knn_probe.py`**, a draft of the PI's figure on one seed of Design B on WD50K(66):
   - t-SNE (`sklearn.manifold.TSNE(metric='precomputed', init='random')`, fixed perplexity and seed) for 12 sources;
   - panels for `w°`, certificate rows, fact list and WL (or NetLSD), coloured by source, with 1-NN accuracy and ARI in each title;
   - output as PNG + PDF in the probe directory.
4. **Unit tests** in `tests/newpos/test_knn.py`: copy validity (connected, at least 3 facts, removals pendant, non-isomorphic to the source unless impossible), kNN accuracy with ties, the PAM check.

## Rules
- **Never change `src/`.** Use only `~/.conda/envs/isalhg/bin/python`.
  - The editable install is pinned to the main checkout, whose `src/` is identical to your base, so imports work.
  - Run scripts with the worktree on `PYTHONPATH` only for `scripts/` imports.
- **Seeds:** pinned and recorded in every JSON.
- **Cost:** report wall-clock per arm per cell. The bipartite arms are the slow ones; if a probe cell would take more than about 15 min, shrink S for that cell and say so.
- **Copies:** deduplicate copies that are isomorphic to each other only if both exact representations would agree. Report how many were isomorphic; do not drop them silently.
- **No source in the evaluated set.**
- **Statistics at probe scale are descriptive.** Report point estimates and the per-seed spread; do not claim significance.
- **Sub-agents:** you may spawn at most 2, and must pass `model` explicitly: `"haiku"` for lookups, `"sonnet"` for mechanical coding or tests.
- **Commits:** commit in logical commits on your worktree branch. Never push, merge or rebase.
- **Work log:** keep it at `.claude/notes/2026-10-15-knn/probe-engineer.md` in your worktree. Record the prompt verbatim, your plan, decisions, commands, the result tables, timings and open questions, and commit it last.

## First action
Message `main` (SendMessage, `to: "main"`) with your model id, `pwd`, `git rev-parse --show-toplevel --abbrev-ref HEAD`, and your plan in at most 8 lines. Then work without waiting.

## Final message (at most 20 lines)
- status, branch, worktree, HEAD, log path;
- the result table per hypothesis (word vs best competitor, with its name, per cell);
- which kill criteria fired;
- the figure path;
- your recommendation;
- anything `main` must decide.
```

## 1. Plan (sent to `main` 08:13 CEST)

1. Read LOG.md, C8 write-up, `neardup.py`, `build_ow_matrix.py`, `kb/{base,corruptions,ndc_quarterly}.py`, registry.
2. `knn_lib.py`: Design-B copies (+ empirical mix on WD50K66), Design-A lineage samples, per-arm matrices
   with timings, LOO kNN with ties at expected accuracy, macro-F1, PAM, ARI/NMI, seed loop.
3. `tests/newpos/test_knn.py`.
4. `probe_knn.py` CLI; JSON per cell + markdown table.
5. `fig_knn_probe.py`.
6. This log; logical commits; no push.

## 2. Reconnaissance (08:15–08:40)

- `kmedoids` (python-kmedoids) is installed in `~/.conda/envs/isalhg`; `sklearn_extra` is not.
  `kmedoids.KMedoids(n_clusters, metric='precomputed', method='pam', init='build')` is used.
- sklearn 1.9.0, scipy 1.17.1, numpy 2.4.6, matplotlib 3.10.9. 24 cores, 31 GB RAM.
- Collections (members, n median, m median, max arity median):
  wd50k66 3,988 / 8 / 5 / 3; wd50k100 1,837 / 11 / 5 / 4; ndc_classes 1,381 / 9 / 3 / 6;
  ndc_substances 1,745 / 8 / 4 / 4. WD50K: 1 type, roles present (no arm reads roles);
  NDC: 1 predicate, 4 types (classes) or 1 (substances).
- NDC lineages (`meta.runs`): ndc_classes 171 lineages, 103 with >= 3 versions (1,293 versions,
  versions per lineage median 8, max 47); ndc_substances 360 lineages, 87 with >= 3 (1,417 versions,
  median 8, max 70).
- **Matrix cost on 360 members (n_jobs = 20):** every arm < 2.1 s (HPD 2.0 s, bipartite path 0.7 s,
  w° 0.04 s). A fresh build on a 360-member subset equals the cached full-collection sub-matrix
  exactly for all 11 arms on wd50k66 and ndc_classes (NetLSD to 6e-14): no arm resolves anything at
  corpus level that changes values, so cached sub-matrices are valid for Design A.
- `wstar_orbit` (the ablation): C++ engine, poisons forked children, needs a per-member 60 s screen
  (`experiments.tkde.budget.arm_fingerprint_screen`); the cached NDC-classes build took 1,467 s for
  1,311 members. It is opt-in (`--ablation`) and runs in its own subprocess.

## 3. Implementation readings of the pre-registration (ratified by `main` 08:3x CEST)

`main` ratified readings 1–5 (message after my 08:27 check-in) and asked that each be recorded as
an implementation reading of LOG.md:

1. **S = 60 in the probe.** LOG.md §2 says S = 100 for the probe; `main`'s brief (S = 60)
   supersedes it. S = 200 stays the full-run value.
2. **Sources shared across r within a seed.** A member is an eligible source iff it is not
   isomorphic (nauty certificate) to an already accepted source and `make_copies` returns c = 6
   pairwise non-isomorphic copies at every r in {1, 2, 3} within 40·c draws. Members are visited in a
   seeded random order, so the accepted S are a uniform draw from the eligible members. The r-curves
   are paired.
3. **Mix condition interior-draw correction.** A plain per-step Bernoulli(1 − p) overshoots the
   pendant share because stars (≈ 53 % of WD50K(66)) admit no valid interior removal. A step is drawn
   interior with probability q = min(1, (1 − p)/a) whenever an interior removal exists, where a is the
   share of members with a valid pendant removal that also admit a valid interior one
   (`interior_availability`, cached under `probe/calibration/`). If the drawn kind has no option the
   step takes the other kind (`steps_fallback`). The realized pendant share is reported per cell.
4. **Mix on both WD50K collections**, because H-KNN-mix claims "the WD50K collections".
5. **Design A.** Per seed, a uniform sample of L = 30 lineages (from 103 on NDC-classes, 87 on
   NDC-substances; all versions of each sampled lineage), LOO kNN with candidates restricted to
   versions of other windows, PAM with k = 30. Plus a deterministic all-lineage kNN reference
   (`Afull`, no clustering).

Further readings (mine, not contested):
- **Pendant removal** = a single down-edit (delete one fact, or remove one constant from a fact of
  arity >= 3) that changes the constant inventory; removal from an arity-2 fact would leave an arity-1
  fact, which is not a KB fact. A removal that duplicates an existing fact equals a deletion and is
  skipped (as in C8). Removals are sequential: each step is pendant w.r.t. the current copy.
- **Validity** = compacted result connected, >= 3 facts (`Envelope.m_min`), no duplicate fact. Roles
  are dropped (no arm reads roles).
- **Copy dedup** = a draw is rejected only when the nauty certificate AND the ordered-walk
  fingerprint both match the same accepted copy; disagreements are counted (`key_disagreements`).
  Copies are never isomorphic to their source (every pendant step lowers n); this is asserted per
  cell (`items_iso_to_source`).
- **Cross-source isomorphic copies are kept** and counted (`items_in_cross_class_iso`): they are
  genuine ambiguity of the task, identical for every exact arm.
- **kNN ties at expectation, exact.** The k nearest = strictly closer than the k-th distance plus a
  uniform draw from the tie block; plurality vote, vote ties uniform. `knn_label_probs` computes every
  label's probability exactly (DP over classes; checked against brute-force enumeration of all
  candidate orders). Macro-F1 is the F1 of the expected confusion matrix.
- **PAM** = `kmedoids.pam(D, k, init='build', max_iter=1000)` on a seeded random permutation of the
  items (index-order tie-breaking never aligned with the classes); k = number of classes. Non-finite
  distances (only the ablation can produce them) are set to 10·(max finite + 1).
- **Seeds**: per cell, `cell_seed(seed, condition, collection, ...)` (CRC32 + SeedSequence); recorded
  in every JSON (`source_seed`, `sample_seed`, `pam_seed`).

## 4. Diagnostics requested by `main` (descriptive, not hypotheses)

`main` (same message): do not change any design or kill criterion on early numbers; report every
cell; add (a) per cell, the ceiling = share of queries every arm gets right; (b) for Design A, the
share of versions whose isomorphism class is shared across lineages. Implemented as
`knn_lib.ceiling_census` (all-arms-correct share at 1-NN with certainty, mean of the per-query
minimum over arms, word-right/competitor-wrong and the reverse, arms with 1-NN >= 0.9) and
`cross_class_iso_fraction` in every cell's `iso_census`. The probe was restarted with `--force` at
08:3x so every cell carries them.

`main` then forwarded a request from the writing expert: for every k-medoids run, the Prop. 6.1
certified ratio `cost(M)/LB` per cluster (Overleaf `submission/article/sections/operations.tex`,
`prop:certified`: `LB = sum_{i<j} d(K_i,K_j)/(N-1) <= OPT`, the 1-medoid has `cost <= (2-2/N) LB`).
Implemented as `knn_lib.medoid_certificates` (per cluster: size, cost, LB, ratio, bound, the
in-cluster 1-medoid's ratio, whether the PAM medoid is the 1-medoid; per cell: median, max, counts
over the bound). Quick, so it is in the probe JSONs (`arms.<arm>.certified`).

I added two more diagnostics after the first look (both descriptive):
- `exact_arm_acc1_ceiling`: the highest 1-NN accuracy any complete invariant can reach (a query with
  isomorphic candidates draws its 1-NN among them). Note for `main`: the cross-class iso fraction is
  NOT an upper bound on `1 - accuracy` for an exact arm — items outside shared classes can be
  misclassified too. It bounds the error that isomorphism alone forces; the exact ceiling is the
  correct bound on accuracy.
- `p_correct1` per query per arm is now stored in each cell JSON, so later diagnostics and
  query-level paired tests need no rerun; `best_only_vs_best` / `word_only_vs_best` are the paired
  split against the best competitor.

Final probe run: started 09:02 CEST (`--force`), 62 cell JSONs, no traceback, total cell wall-clock
399 s on the workstation (`--n-jobs 16`).

## 5. Commands

```bash
PY=~/.conda/envs/isalhg/bin/python   # from the worktree root
OUT=/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/KNN_2026-10-15/probe
$PY -m pytest tests/newpos/test_knn.py -q            # 67 passed
$PY scripts/newpos/knn/probe_knn.py --designs B mix A Afull --seeds 0 1 2 --S 60 --c 6 \
    --r 1 2 3 --lineages 30 --n-jobs 16 --force --out $OUT     # writes cells/, items/, SUMMARY.md
$PY scripts/newpos/knn/fig_knn_probe.py --seed 0 --r 2                          # fig_knn_probe_r2_s0.*
$PY scripts/newpos/knn/fig_knn_probe.py --seed 0 --r 2 --third bipartite_ged_path  # ..._editpath.*
$PY scripts/newpos/knn/probe_knn.py --designs B --collections wd50k66 ndc_classes --seeds 0 \
    --ablation --out $OUT/ablation_wstar_orbit                  # the w*_c ablation, seed 0 only
```

## 6. Results (probe: S = 60, c = 6, 3 seeds; mean [min, max] over seeds; descriptive)

Full tables: `$OUT/SUMMARY.md` (generated), per cell `$OUT/cells/*.json`.

### H-KNN-B (pendant copies) — kill FIRES in 12/12 cells

| collection | r | `w°` 1-NN | best competitor 1-NN | `w°` ARI | best competitor ARI |
|---|---|---|---|---|---|
| WD50K(66) | 1 | 0.955 | bip. path 0.960 | 0.696 | — (`w°` best; bip. path 0.682) |
| WD50K(66) | 2 | **0.944** | bip. path 0.886 | 0.452 | bip. path 0.486 |
| WD50K(66) | 3 | **0.880** | bip. path 0.834 | 0.323 | bip. path 0.405 |
| WD50K(100) | 1 | 0.847 | bip. path 0.950 | 0.512 | bip. path 0.671 |
| WD50K(100) | 2 | 0.821 | bip. path 0.882 | 0.432 | bip. path 0.527 |
| WD50K(100) | 3 | 0.778 | bip. path 0.801 | 0.359 | bip. path 0.410 |
| NDC-classes | 1 | 0.767 | bip. path 0.844 | 0.447 | bip. assign 0.603 |
| NDC-classes | 2 | 0.676 | bip. assign 0.784 | 0.370 | bip. assign 0.470 |
| NDC-classes | 3 | 0.590 | bip. assign 0.722 | 0.308 | bip. assign 0.390 |
| NDC-substances | 1 | 0.789 | bip. path 0.866 | 0.323 | bip. path 0.614 |
| NDC-substances | 2 | 0.707 | bip. path 0.812 | 0.264 | bip. path 0.508 |
| NDC-substances | 3 | 0.623 | bip. path 0.753 | 0.234 | bip. assign 0.432 |

WD50K(66) r = 1 ARI: `w°` 0.696 vs bip. path 0.682 (word ahead) but 1-NN 0.955 < 0.960, so the
cell still fires. The word's ARI also trails the degree-sequence floor in 10/12 cells (all but
WD50K(66) r = 1, 2). `w°` beats every *other* exact representation (certificate bytes/rows, fact list)
in every cell, on both metrics.

### H-KNN-A (real NDC lineages, L = 30 lineages per seed) — kill FIRES (NDC-substances)

| collection | N | `w°` 1-NN | best competitor 1-NN | `w°` ARI | best competitor ARI |
|---|---|---|---|---|---|
| NDC-classes | 382 | **0.748** [0.627, 0.835] | bip. path 0.700 [0.601, 0.779] | **0.273** | fact list 0.256 |
| NDC-substances | 412 | 0.430 | bip. path 0.452 | 0.142 | HPD 0.208 |

All-lineage reference (1-NN): NDC-classes `w°` 0.504 vs bip. path 0.479; NDC-substances 0.239 vs
bip. path 0.285.

### H-KNN-mix (C8 edit mix) — kill FIRES on both WD50K collections

`w°` 1-NN vs bip. path: WD50K(66) 0.820 / 0.794 / 0.705 vs 0.934 / 0.835 / 0.739 (r = 1/2/3);
WD50K(100) 0.648 / 0.548 / 0.472 vs 0.864 / 0.752 / 0.647. Realized pendant share: WD50K(66)
0.81–0.86 (target 0.90), WD50K(100) 0.68–0.73 (target 0.75) — the calibration undershoots the
target slightly on both (the interior availability shrinks along a path).

### Diagnostics

- **Ceiling (main's (a)): the task is not too easy.** Arms with 1-NN >= 0.9: 0–2 per cell and seed
  (`w°` and bip. path on WD50K(66) r <= 2; bip. path on WD50K(100) r <= 2 and on mix WD50K(66)
  r = 1; zero elsewhere, and zero on every NDC cell). The all-arms-correct
  share is ~0 everywhere (the floors' ties make certainty rare; without the floors still <= 0.18).
  The exact-arm ceiling is 0.93–1.00 on every B cell, so isomorphism never limits Design B.
- **Design A isomorphism (main's (b)).** Cross-lineage isomorphic versions: 0.25 [0.08, 0.41]
  (NDC-classes sample), 0.29 (NDC-substances sample), 0.67 / 0.40 in the all-lineage reference.
  Exact-arm 1-NN ceiling: 0.92 / 0.79 (samples), 0.78 / 0.67 (all lineages).
- **Certified medoid (Prop. 6.1).** `w°` PAM medoids: median ratio 1.22–1.34 per cell, max 1.75,
  0 of 2,785 certified clusters over `2 - 2/N` (623 singleton clusters have no ratio); every `w°`
  PAM medoid is its cluster's 1-medoid. No arm (not even the non-metric edit path) has an in-cluster
  1-medoid over the bound. The bound is metric-generic, so it does not separate arms.
- **Registry WL is degenerate on copy sets.** `wl_l1` runs WL to the stable partition of the union
  of the evaluated items; on near-identical copies that partition separates every copy, so the
  distance collapses to `n_i + n_j` and 1-NN = 0.009–0.015 (chance) in every B cell. With a fixed
  round cap (not a registered arm; seed 0): h = 1 gives 1-NN 0.989 / 0.964 / 0.928 on WD50K(66)
  r = 1/2/3 (above `w°`) and 0.605 / 0.442 / 0.323 on NDC-classes; h >= 2 collapses again. On
  WD50K, a bag of local label signatures (predicates) already solves most of Design B.
- **Mechanism, seed 0 (`w°` vs bip. path).** Under `w°` a copy stays close to its source in median
  (1–4 tokens per removed statement) but the tail is heavy (p90 5–20, max 14–60 tokens per removal:
  hub-root / canonical-order avalanches). Worse, the nearest *impostor* is close in absolute terms:
  one V token carries a whole fact, so unrelated KBs of similar shape differ by a few tokens (NDC-
  classes r = 1: nearest sibling 1 token, nearest impostor 2). The bipartite GED prices a removed
  fact by its size, so impostors sit far (NDC-classes: sibling 1.5, impostor 6). Share of queries
  whose nearest sibling is closer than the nearest impostor: `w°` 0.43–0.96 vs bip. path 0.63–0.97.

### Cost (wall-clock, workstation, `--n-jobs 16`)

Per arm per B cell (matrix + evaluation, N = 360): `w°` 0.11 s, cert 0.19, rows 0.13, fact list
0.09, WL 0.31, NetLSD 0.50, HPD 2.7, bip. assign 0.34, bip. path 0.49, degree 0.13, size 0.06. A
whole B replicate (3 r-cells) takes 15–20 s; the largest cell (all-lineage NDC-substances,
N = 1,417) 63 s. No cell needed a smaller S.

### Figure

`$OUT/fig_knn_probe_r2_s0.{png,pdf,json}` (w°, certificate rows, fact list, NetLSD) and
`$OUT/fig_knn_probe_r2_s0_editpath.{png,pdf,json}` (third panel = bipartite edit path). 12 sources of
seed 0, r = 2, t-SNE perplexity 8, `random_state` 0, `init='random'`; titles give 1-NN and ARI on
the 72 copies shown: `w°` 0.972 / 0.748, rows 0.947 / 0.644, fact list 0.965 / 0.696, NetLSD
0.931 / 0.714, bip. path 0.986 / 0.967. Panel (b) is 1-NN vs r per collection. Encoding: a source is
a (hue, marker) pair, 3 validated hues x 4 shapes (only slots 1–3 pass the all-pairs CVD gates).
WL was dropped from the default panel set because the registry WL is degenerate here.

### Ablation `w*_c` (`wstar_orbit`, seed 0 only, `$OUT/ablation_wstar_orbit/`)

WD50K(66), r = 1/2/3: 1-NN `w*_c` 0.941 / 0.896 / 0.843 vs `w°` 0.962 / 0.953 / 0.899; ARI 0.422 /
0.401 / 0.318 vs 0.783 / 0.535 / 0.388; 0 members censored; wall-clock 161 / 64 / 41 s per cell (the
per-member 60 s screen forks once per copy). NDC-classes, r = 1/2/3: 1-NN 0.685 / 0.639 / 0.537 vs
`w°` 0.761 / 0.696 / 0.580; ARI 0.473 / 0.371 / 0.277 vs 0.451 / 0.410 / 0.316; 1 copy censored at
r = 1 (`41@465~r1c1`); 549 / 455 / 222 s per cell. The ordered walk beats the search form on 1-NN in
all 6 cells. The ablation costs 10–100x the main arms, so in a full run it belongs in a separate
array.

## 7. Open questions and notes for `main`

1. **Kill criteria fired on all three hypotheses at probe scale** (H-KNN-B 12/12 cells, H-KNN-A on
   NDC-substances, H-KNN-mix on both WD50K collections). The bipartite GED (edit path, or the
   assignment value on NDC) is the competitor that beats the word almost everywhere. In Design B a
   competitor leads 1-NN in 10/12 cells (by 0.005–0.13, >= 0.06 in 8) and ARI in 11/12 (by
   0.03–0.29). Only WD50K(66) r = 1 (1-NN gap 0.005, word ahead on ARI) could plausibly flip at
   S = 200 / 27 seeds; every other cell also fails on ARI by >= 0.03.
2. **The registry WL arm is degenerate on these item sets** (§6). Keep it as registered and
   footnote it, or pre-register a fixed-round WL (h = 1)? The h = 1 WL beats `w°` on WD50K(66).
3. **Harder, natural regime that targets the word's mechanism (described, not run):** draw the S
   sources as *look-alike groups* — members pairwise one interior edit apart (C8's radius-1 interior
   pairs) — and keep pendant copies. Under the GED an interior edit between sources costs as much as
   a pendant removal inside a class, so the GED's between-class margin vanishes; under `w°` interior
   edits move many tokens and pendant ones few (C8's H2 mechanism), so the word should keep the
   classes apart. Practical reading: "which of several near-identical records is this partial
   export of?". Feasibility (C8 truth files, radius-1 interior pairs): components of >= 3 look-alike
   members: 23 (WD50K(66), 210 members), 41 (WD50K(100), 536), 42 (NDC-classes, 455), 31
   (NDC-substances, 924). Enough for S = 60 as 20 groups of 3 on three collections; WD50K(66) is
   tight once pendant eligibility is applied. A second lever, schema/size matching (sources from one
   predicate-multiset or Wikidata-type block, matched n and m), removes the label-bag and size
   signals that WL(h = 1) and the floors exploit, but it would help every structure-aware arm, the
   GED included. Larger S alone is not a lever for the word: its impostor distances are already
   small.
4. **Picasso.** The probe needs `kmedoids` (python-kmedoids); check it is in `isalhg-tkde` on
   Picasso before any array. The full registered run (27 seeds, S = 200, N = 1,200 per cell) is
   about 540 cells; at N = 1,200 the matrices take ~10 s per arm and PAM a few seconds per arm, so a
   24-core workstation finishes it in about an hour. Picasso is optional for this experiment.
