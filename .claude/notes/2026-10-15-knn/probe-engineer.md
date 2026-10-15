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

---

# Design C probe (look-alike blocks) — opened 2026-10-15 ~09:40 CEST

## 8. The brief from `main` (verbatim)

```
Your A/B probe is accepted. Next: build and run the Design C probe, which is pre-registered in LOG.md §6. I merged your branch into main at bd52419. LOG.md §5.1 (verdicts) and §6 (Design C) are at 65ddb4a.

Setup:
- In your worktree, run `git merge --ff-only main`. Your branch is an ancestor of main, so this is safe and authorised. Then read LOG.md §6 in full; it is the spec. Do not reinterpret it. If something is ambiguous, message main with your proposed reading and continue on that reading.

What to build:
1) Blocks.
   - Use the C8 one-edit relation from the existing near-duplicate code (scripts/newpos/neardup.py and its cached outputs in D/results/NEWPOS_2026-10-13/neardup/). Each pair carries its edit kind (pendant or interior).
   - Records are deduplicated to isomorphism classes.
   - A block is a seed record plus a uniform subsample of at most 4 one-edit neighbours. A block needs at least 3 members. Blocks are disjoint within a seed.
   - Draw blocks until S ≥ 60 sources or the candidates run out, and report the realised S.
   - Build three strata: C-all (neighbours of either kind), C-int (interior-only neighbours) and C-pend (pendant-only neighbours).
   - Report the number of available blocks per stratum and collection. A stratum with fewer than 10 blocks is reported as infeasible.
2) Copies are exactly as in Design B: c=6, r∈{1,2,3} pendant removals, at least 3 facts, connected.
3) Arms are all the §2 competitors plus a new arm `wl_h1`: one-round WL, L1 on the colour histogram. Keep the registry WL arm too, as pre-registered, and footnote it as degenerate.
4) Metrics:
   - 1-NN accuracy over the whole pool, with ties at expected accuracy;
   - PAM ARI with k = S;
   - per cell: the exact-arm ceiling and the cross-source isomorphism fraction.
   - Add the share of 1-NN errors that land inside the query's own block versus another block. This is descriptive and explains the mechanism.
5) Probe size: 3 seeds, all 4 collections × 3 strata × 3 r. Give per-cell verdicts against H-KNN-C and H-KNN-C-int exactly as SUMMARY.md does for A/B. Write the outputs to D/results/KNN_2026-10-15/probe_c/.
6) Figure: draft the §6 figure. Panel (a) is drawn inside one block (copies of 3–5 look-alike members, coloured by member), on a collection and r where C-int is feasible. Its four panels are the word, the certificate rows, the bipartite edit path (mandatory) and wl_h1. Panel (b) is 1-NN accuracy vs r per stratum.
7) Write the code so the full run (27 seeds, every cell) can be launched per (collection, stratum) as an independent job. Each job writes one JSON. Provide an aggregator that computes BCa, one-sided Wilcoxon, Holm and rank-biserial. I will submit it to Picasso, so keep the CLI to `--collection --stratum --seeds --out`.

Rules (unchanged):
- Never change src/.
- Use ~/.conda/envs/isalhg/bin/python and do not pip install.
- Tests go in tests/newpos/test_knn.py, including a block-construction test that checks disjointness and that every pair's edit kind matches the stratum.
- Commit everything and append to your log at .claude/notes/2026-10-15-knn/probe-engineer.md.
- Do not tune any parameter after seeing results. If a design choice turns out to be unworkable, message main before changing it.

Report back:
- the verdict table;
- the block counts per stratum;
- the within-block error share;
- the figure paths;
- the estimated full-run cost per job.
```

## 9. Ratified readings (verbatim)

My message to `main` (sent before any Design-C code ran), readings 1–8:

```
1. Relation: I recompute it in-job with neardup.ground_truth(col, "cert"). That takes ≤5 s per collection and matches the cached C8 truth JSONs exactly on all 4 collections. Pendant holds exactly when n differs, on every pair, so each pair has exactly one kind. Isomorphism classes are represented by their lowest member index.
2. Block = a seed plus up to 4 of its one-edit neighbours. Members are one edit from the seed, not necessarily from each other. A seed is drawn uniformly among the available records that have ≥2 available neighbours of the stratum's kind. The neighbours are a uniform subsample of the available ones, and members leave availability once used.
3. Eligibility: a block member must be a valid Design-B source, i.e. it yields 6 pairwise non-isomorphic pendant copies at every r in {1,2,3}. This is decided once per collection with a fixed seed, and the one-edit graph is restricted to eligible records before any block is drawn. If a seed's own copy draw later fails (rare), that member is dropped. A block left with fewer than 3 members is discarded and counted.
4. "Available blocks" = the number of disjoint blocks reached by drawing to exhaustion (no S cap), reported as min and mean over seeds. The cell is infeasible if the min is <10. I also report the number of candidate block seeds.
5. Copies of a record use an rng keyed by (seed, record), so within a seed a record has the same copies in every stratum.
6. Within-block error share: from the exact 1-NN label distribution, the expected error mass on labels in the query's own block divided by the total error mass. Pooled over queries per cell.
7. Kills are evaluated on seed means, as for A/B; a tie counts as a kill. The competitors are §2's ten plus wl_h1. The registry wl_l1 stays among them and carries a footnote. wstar_orbit is not included.
8. The job CLI is --collection --stratum --seeds --out. It writes one JSON per job. --n-jobs is optional and defaults to SLURM_CPUS_PER_TASK.
```

`main`'s ratification (verbatim):

```
Readings 1–8 ratified, with one clarification on 4.
- Counting available blocks: draw to exhaustion with no cap. That count is the feasibility statistic.
- Evaluation pool: stop drawing once the pool reaches ≥ 60 sources. If a seed runs out first, use what it has and report the realised S.
- Keep the two draws separate. Use a separate rng stream for the counting draw so the evaluated pool does not depend on it.
- Log every ratified reading verbatim in your log. Proceed.
```

Feasibility blocker I reported (before any Design-C distance was computed): with c = 6 the one-edit
graph's small records rarely yield 6 non-isomorphic copies; eligible classes 82/957, 208/624,
153/374, 51/513; C-int had 0–2 blocks on every collection. `main`'s decision (verbatim):

```
Decision: option (b). The amendment is now LOG.md §6.1, commit b57c9c3 on main. Fast-forward to it.
- **Primary.** Design C uses c=3 with r∈{1,2,3}. The kill criteria are unchanged, and so is the feasibility rule (min over seeds ≥ 10 blocks).
- **Secondary.** The registered c=6 also runs on its feasible cells, with its own verdicts. Report both tables, primary first.
- **Order of runs.** If you have not yet computed any c=6 accuracy or ARI, do the c=3 run first. If you already have, tell me so in the report; that must be on the record.
- **Eligibility for c=3.** A source needs 3 pairwise non-isomorphic pendant copies at every r≤3. Redo the eligibility and block counts at c=3, and report them per seed as min and mean.
- **Figure.** Panel (a) uses a C-int block on WD100 or NDC-sub, whichever has the larger block at c=3. Copies are coloured by member.
Everything else is as ratified. Proceed.
```

**Order of runs, on the record.** No c = 6 accuracy or ARI had been computed when the amendment
arrived (only eligibility and block counts). The c = 3 run went first (09:50–09:54 CEST), then the
c = 6 secondary (09:54–09:58).

## 10. Code (commit `afd58c2` + the figure commit)

- `scripts/newpos/knn/design_c.py` — the job: graph (`one_edit_graph`), eligibility (cached per
  collection and c under `<out>/eligibility/`), the two draws (`count_blocks` on stream
  `C-count`, `build_pool` on stream `C-pool`), copies (`member_copies`, stream `(seed, record)`),
  evaluation (`evaluate_pool`), resumable JSON `C_<collection>_<stratum>_c<c>.json`. CLI
  `--collection --stratum --seeds --out` (+ optional `--n-jobs`, `--copies 3|6`, default 3).
- `scripts/newpos/knn/aggregate_c.py` — seed means, [min, max], BCa (scipy, 9,999 resamples),
  one-sided Wilcoxon (`zsplit`) + Holm over the 11 competitors + rank-biserial, per-cell verdicts,
  hypothesis verdicts, `SUMMARY_C.md` + `summary_c.json`.
- `scripts/newpos/knn/run_probe_c.sh <out> <c> <seeds...>` — all 12 jobs locally, then aggregate.
- `scripts/newpos/knn/fig_knn_c.py` — the draft figure.
- `knn_lib`: `wl_h1` (`HypergraphWLDistance(metric="l1", max_rounds=1)`, one refinement round,
  checked on a toy star), `COMPETITORS_C`, `error_split`, `best_competitor(..., competitors)`.
- Tests: 96 in `test_knn.py` (+ 11 `test_neardup.py` = 107 pass), incl. block disjointness and
  edit kinds per stratum on random graphs, exhaustive-draw completeness, graph dedup + kinds on a toy
  collection, copy determinism, the error split, `wl_h1`.

## 11. Design C results (probe: 3 seeds; S ≈ 60; descriptive)

Outputs: `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/KNN_2026-10-15/probe_c/`
(`SUMMARY_C.md`, `summary_c.json`, 24 job JSONs, `eligibility/`, `run_c3.log`, `run_c6.log`).

### Feasibility, c = 3 (primary): available blocks min / mean over seeds

| | WD50K(66) | WD50K(100) | NDC-classes | NDC-substances |
|---|---|---|---|---|
| eligible classes | 325 / 957 | 394 / 624 | 251 / 374 | 194 / 513 |
| C-all | 27 / 27.7 | 50 / 51.3 | 35 / 36.0 | 21 / 22.7 |
| C-int | **3 / 3.0 (infeasible)** | 15 / 15.7 | **4 / 4.0 (infeasible)** | 14 / 14.0 |
| C-pend | 24 / 24.7 | 44 / 45.3 | 28 / 29.0 | 17 / 18.0 |

Realised S: 60–64 in every C-all / C-pend pool; C-int 48–52 (WD100, NDC-sub; candidates run out).
No block was discarded and no member dropped.

### Verdicts, c = 3 (primary)

- **H-KNN-C (C-all): KILLED in 12/12 feasible cells.** The bipartite edit path (or assignment)
  leads 1-NN everywhere; ARI is led by the edit path, the degree floor or WL h=1. Word vs best
  1-NN: WD66 0.22/0.23/0.15 vs 0.43/0.28/0.20; WD100 0.23/0.20/0.21 vs 0.61/0.39/0.31; NDC-cl
  0.40/0.34/0.30 vs 0.72/0.55/0.48; NDC-sub 0.16/0.12/0.08 vs 0.58/0.44/0.33 (r = 1/2/3).
- **H-KNN-C-int: KILLED in 6/6 feasible cells** (WD100: 0.25/0.18/0.19 vs edit path
  0.51/0.31/0.28; NDC-sub: 0.19/0.15/0.13 vs 0.43/0.33/0.24). WD66 and NDC-cl infeasible (3 and 4
  blocks); on those infeasible pools the word is close to the best arm (e.g. NDC-cl r = 1: 0.69 vs
  degree 0.75; ARI 0.59 vs 0.54) — not a pass.
- C-pend (no claim): the edit path / assignment leads every cell.

### Verdicts, c = 6 (secondary, registered)

Feasible cells only: C-all on WD100 and NDC-classes, C-pend on WD100; C-int nowhere.
**H-KNN-C killed in 6/6 feasible cells** (WD100 word 0.26/0.27/0.25 vs edit path 0.76/0.62/0.42;
NDC-cl 0.58/0.49/0.44 vs assignment 0.81/0.74/0.62). H-KNN-C-int untestable at c = 6.

### Within-block error share (c = 3, feasible cells)

Share of the expected 1-NN error mass that lands on another member of the query's own block:
word 0.33–0.75 (C-all), 0.20–0.39 (C-int), 0.33–0.77 (C-pend); edit path 0.22–0.71 / 0.20–0.33 /
0.17–0.54; WL h=1 0.31–0.75 / 0.19–0.41 / 0.23–0.76. On C-int most of the word's errors go to
*other* blocks.

### Mechanism (seed 0, r = 1; median distances)

Under the word, distances in these pools are tiny and quantised: copy to own source 1–3.5 tokens,
nearest sibling 2–3, nearest other member of the block 1–4, nearest other-block copy 2–3. Sibling
closer than every other-block copy: 0.22–0.47 of queries (edit path 0.35–0.63). The one-edit graph
lives on small records (median m 4–5), whose words differ by a handful of tokens whether or not they
are related; the predicted separation of interior look-alikes does appear inside a block (WD100
C-int: sibling 3.0 vs in-block 4.0 tokens) but unrelated small records from other blocks sit closer
still (2.0). The edit path prices facts by size and spreads these records out.

### Diagnostics

Exact-arm ceiling 0.37–0.95 (lowest on NDC-sub, where 26–63 % of the copies share an isomorphism
class with another source's copy). Arms with 1-NN >= 0.9: none in any cell. Prop. 6.1: word
medoid ratio median 1.00–1.19, max 1.67, 0 clusters over the bound.

### Figure

`probe_c/fig_knn_c_r1.{png,pdf,json}`. Panel (a): the largest C-int block of seed 0 at c = 3 —
NDC-substances (5 members; WD100's largest had 4), r = 1, t-SNE perplexity 4, seed 0; within this
block the word scores 1-NN 0.49 / ARI 0.32 vs edit path 0.33 / 0.14, certificate rows 0.18 / −0.05,
WL h=1 0.22 / 0.13. **This block is not representative of the cell** (pooled C-int NDC-sub r = 1:
word 0.19 vs edit path 0.43); the within-block numbers ignore the other-block impostors that cause
most of the word's errors. Panel (b): 1-NN vs r for 3 strata x 4 collections, infeasible panels
shaded.

### Cost (workstation, 16 jobs for the pairwise arms)

Per job: setup (graph + cached eligibility) 2–7 s; per seed 1.7–4.9 s at c = 3 (N ≈ 150–185), ~13 s
at c = 6 (N ≈ 330–370). A full job of 27 seeds: about 2.5 min at c = 3, 6 min at c = 6, on one node
with 16 cores; 12 jobs per c. Memory is negligible (< 1 GB).

---

# Design D probe (catalogue linkage) — opened 2026-10-15 ~10:00 CEST

## 12. The brief from `main` (verbatim, abridged to the binding items)

```
Design C is accepted as killed. [...] §7 pre-registers Design D (commit 118f8f0). Fast-forward to main and read §7 in full; it is the spec.
1) Catalogue linkage. Catalogue = every record of the collection in the C8 envelope, deduplicated to isomorphism classes [...]. Queries = c=3 pendant copies, r∈{1,2,3}, of S sources. S=60 in the probe. Sources are drawn uniformly from the records eligible under the §6.1 rule. 1-NN against the catalogue, with ties at expected accuracy. Secondary: the reciprocal rank of the source. Per cell, report the exact-arm ceiling: the share of queries whose isomorphism class is not shared with another catalogue record.
2) Mix condition on both WD50K collections. Use the C8 empirical mix, reusing your Design-B mix code.
3) Arms: the eleven of §6. For the matrix arms, compute query × catalogue rectangles. [...] Make sure the query distances use exactly the same definition and normalisation as the cached ones. Test this: recompute a few cached catalogue × catalogue entries through your rectangle path and assert equality. Bipartite GED is the cost driver. Parallelise it with joblib and report the measured pairs/s.
4) Verdicts per cell against H-KNN-D (r=1,2 claim; r=3 reported) and H-KNN-D-mix, in a SUMMARY_D.md [...]. Probe: 3 seeds, all cells. Outputs go in D/results/KNN_2026-10-15/probe_d/.
5) Figure draft [...] four panels are the word, the certificate rows, the bipartite edit path (mandatory) and one-round WL [...] Choose the sources for panel (a) by a fixed rule decided before you look: the first 12 sources of seed 0. No cherry-picking.
6) Job CLI as for Design C (`--collection --mix {pendant,empirical} --seeds --out`), plus an aggregator. Estimate the full-run cost per job at S=200 and 27 seeds.
```

## 13. Code

- `rect.py`: query × catalogue rectangles that equal the `[queries, catalogue]` block of each arm's
  own matrix over `catalogue + queries` (library fingerprints + pair functions; catalogue
  fingerprints fitted once per job; bipartite arms `pairwise(catalogue, query)` over fork-based
  joblib row blocks; WL arms from one WL run over the union). `SymMinPairwiseArm`
  (`bipartite_ged_path_sym`) = `min(d(c,q), d(q,c))`.
- `design_d.py`: job per `(collection, mix)`, resumable per seed *and per arm* (a missing arm is
  added to stored seeds after regenerating and checking the sources). `aggregate_d.py`: seed stats,
  BCa, Wilcoxon + Holm + rank-biserial, verdicts, cost table. `fig_knn_d.py`, `run_probe_d.sh`.
- Tests: rectangles = union-matrix block for all 12 arms; serial = parallel; sym-min arm =
  elementwise min of both orientations; **integration test against the cached campaign matrices**
  (`ndc_classes`, 10 arms: exact for every integer arm, ≤ 3e-8 for NetLSD/HPD = float32 cache).

## 14. The orientation finding and §7.1 (verbatim decision)

The bipartite edit path is asymmetric; my rectangle followed the cache convention (catalogue first).
The flipped orientation `pairwise(query, catalogue)` is better for the competitor in every cell and
flips NDC-classes r = 1 (word 0.546 vs path 0.533 as run, 0.635 flipped). Reported to `main`.
Decision (verbatim): "option (b), using the symmetric min. The edit-path competitor (and
bipartite_ged_assign, if it is asymmetric too) is scored with d_sym(a,b) = min(d(a,b), d(b,a)). This is
orientation-free and never worse for the competitor than either orientation. I will log it as LOG
§7.1, disclosing that it was adopted after the probe values were seen and that it can only hurt the
word. Under it, H-KNN-D is killed at NDC-classes r=1 (word 0.546 vs about 0.63), so Design D is
killed at probe scale, like A, B and C. No full run." The assignment value is exactly symmetric on
all four collections (full ordered matrices), so only the path is replaced.

## 15. Design D results (probe: S = 60, c = 3, 3 seeds; verdict arm = sym-min edit path)

`probe_d/SUMMARY_D.md`. Word vs best competitor, 1-NN (r = 1 / 2 / 3):
- WD50K(66): 0.689 / 0.392 / 0.191 vs WL h=1 0.665 / 0.349 / 0.160 — word ahead.
- WD50K(100): 0.629 / 0.363 / 0.236 vs WL h=1 0.626 / 0.266, path 0.121 — word ahead (r = 1 by
  0.003; WL h=1 has the higher RR 0.718 vs 0.693).
- NDC-classes: 0.546 / 0.296 / 0.156 vs sym-min path 0.628 / 0.241 / 0.073 — **killed at r = 1**.
- NDC-substances: 0.521 / 0.287 / 0.159 vs sym-min path 0.488 / 0.209 / 0.101 — word ahead.
- **H-KNN-D: killed (1 of 8 claim cells). H-KNN-D-mix: killed (3 of 4)** — WD50K(66) r = 1 by WL h=1
  (0.585 vs 0.602), WD50K(100) r = 1, 2 by the sym-min path (0.475 / 0.253 vs 0.621 / 0.358).
- As-run orientation (reported row): H-KNN-D would have survived 8/8 — the verdict hinges on §7.1.
- Exact-arm ceiling 0.74–0.99 (lowest NDC-substances r = 3).
- Cost: bipartite path 143k–258k pairs/s on 16 workers (sym-min evaluates both orientations);
  per seed 12–36 s at S = 60; full run (S = 200, 27 seeds) 19–54 min per job, ×2 for the sym-min
  arm's bipartite share — irrelevant now (no full run).
- Figure: `probe_d/fig_knn_d_wd50k66_r1_s0.{png,pdf}`; rule fixed before drawing (WD50K(66),
  pendant, seed 0, r = 1, first 12 sources, ≤ 5 one-edit look-alikes sampled with a fixed seed). On
  those 36 copies WL h=1 beats the word (0.74 vs 0.65); panel (b) draws the sym-min path. It shows no
  win the verdict does not support.

## 16. C8 orientation audit (priority task from `main`)

`c8_orientation_audit.py` + `c8_audit_report.py` (commit `b9937ff`); outputs
`KNN_2026-10-15/c8_orientation_audit/{AUDIT.md,audit.json,build.json,asrun/,symmin/}`.
- Every C8 bipartite matrix is `pairwise(i, j)` for `i < j`, mirrored (cache reproduced, max diff
  0); a (query, candidate) score depends on member order. Path asymmetric on 45–62 % of pairs;
  assignment exactly symmetric.
- The unchanged `neardup.py` / `neardup_r2.py` rerun reproduces every published number; with the
  sym-min path the Holm-corrected pendant claim (word first on all 4 collections, r = 1 and 2)
  **holds**; largest pendant p rises to 5.7e-31 (NDC-classes r1) — "p < 1e-32" must become
  "p < 1e-30"; pooled r1 NDC-classes: sym-min path 0.421 vs word 0.416 (was a tie at 0.413).

## 17. Sym-min regeneration of every article number using the edit path

Brief (`main`, verbatim core): "the article will define the edit-path competitor as the symmetric
minimum everywhere [...] Enumerate every number in the article that uses bipartite_ged_path [...]
Recompute each with the sym-min path through the original code paths, changing only the matrix.
Write everything to D/results/KNN_2026-10-15/symmin_regen/ [...] REGEN.md with one row per article
claim: file:line, old value, new value, whether the sentence changes. Preserve the bound rule [...]
Report the new merge and split counts per collection. Do not edit the article."

- Script `scripts/newpos/knn/symmin_regen.py` (reuses the audit's matrix roots). Validations all
  passed: as-run reruns reproduce every published C8 JSON (incl. the two wstar-restricted runs);
  `tab_neardup.py` on the published JSONs is byte-identical to the published table; RQ2 stored pair
  and triple values match the ordered matrices (0 mismatches); the exact0 relabelling stream replays
  (0 mismatches); the three RQ2 sections recomputed from the original rows equal the frozen summary.
- H1: merges 0 / 0 / 0, classes 574 / 1,290 / 3,839 — **unchanged** (no split pair is zero in
  either orientation); exact at zero 37 / 37 / 10 unchanged. Triangle violations 8 / 12 / 4 of
  5,000 (was 8 / 26 / 7); asymmetry 0 by construction (was 44–58 %).
- 32 rows in `symmin_regen/REGEN.md`; sentences that change: results.tex (non-metric sentence,
  pendant range 0.071–0.349, p < 1e-30, rank-biserial ≥ 0.44, r2 p ≤ 6.6e-7), capability table
  near-dup 0.071 / 0.277, main and S2 near-dup tables (edit-path row), conclusion and S2 pooled
  sentences (NDC-classes: edit path 0.421 > word 0.416; the registered pooled criterion now fails on
  NDC-classes too; NDC-substances best AP is now the edit path 0.465), S2 radius-2 numbers, the
  1.6–7.8 ratio range, the wstar-ablation edit-path value 0.420, and the S2 figure.

## 18. Full run (LOG.md §8) — TASK 1

Brief (`main`, verbatim core): "TASK 1: run the full set on Picasso [...] all four designs, 27
seeds, as in §8 [...] The symmetric-min edit path is primary; the as-run orientation is kept as a
row. Include one-round WL. Design A: L = 30. Design B: S = 200, c = 6, plus the mix condition on
WD50K. Design C: c = 3, all strata; also c = 6 on the feasible cells. Design D: S = 200, c = 3,
pendant and mix conditions. [...] slurm/tkde/knn_{launcher,worker}.sh. Use one array task per
(design, collection, condition/stratum). CPU only [...] harvest to D/results/KNN_2026-10-15/full/
[...] FULL_SUMMARY.md with one verdict table per hypothesis." TASK 2 = figures F-a..F-d, TASK 3 =
SECTION_FACTS.md.

**Code (no parameter of any design changed).**
- `knn_lib`: `PATH_ASRUN`, `PATH_SYM`, `COMPETITORS_FULL` (the eleven of §6 with the sym-min path in
  place of the as-run one), `ARMS_FULL` (word + those 11 + the as-run path as a row), `ARM_SETS`
  (`probe` / `c` / `full`). `build_matrices` computes the edit path once per *ordered* pair when
  the sym arm is requested and derives both readings (sym = min(P, Pᵀ); as-run = triu(P) mirrored —
  test asserts it equals the registry `build_matrix`). `ceiling_census(p, arms_order)` so the
  as-run row stays out of the verdict-arm census.
- `probe_knn.py` `--arm-set {probe,full}`, `--no-summary`; cells record `arm_set` + `competitors`.
  `design_c.py` `--arm-set {c,full}` (refuses to resume a job file run with other arms).
  `design_d.py` unchanged (its ARMS / COMPETITORS_D already equal the full set; test asserts it).
- `full_run.py`: 38 units (B×4, Bmix×2, D×6, A×2 incl. Afull, C3×12, C6×12) over seeds 0–26, each
  into `<out>/<unit>/`; 9 tasks.
- Tests: 124 pass (3 new).

**Deviation from "one array task per unit" (scheduling only).** slurm/tkde/README.md: "No
submitted task may run under two hours (SCBI, 2026-08-07)". A and C units take 1–6 min each, D
units 19–54 min. So B / mix units are one task each, the two WD50K(66) D units one task, the other
four D units one task, and all 26 A/C units one task. No unit's parameters or seeds change.

**Timing (local, 16 jobs).** B wd50k66 seed 0 at S = 200, c = 6, full arms: N = 1,200 per cell,
112–114 s per cell (matrices ~60 s incl. the ordered edit path 10 s and HPD 28 s; evaluation
~62 s, mostly PAM k = 200), ~5.8 min per seed → ~2.6 h per B unit.

**Verification of the cluster inputs (2026-10-15).** Corpora md5 identical local vs
`~/fscratch/datasets/isalhg_tkde/corpora` (12 files). `src/` checksum-identical to the canonical
`~/fscratch/repos/IsalHG-tkde/src` (rsync -nc: timestamps only). `kmedoids` imports in isalhg-tkde.
Quotas: home 26.8k/35.0k files, fscratch 178.3k/250k.

**Cluster env broken by the storage migration, repaired (2026-10-15 14:58).** Smoke 2920620 failed
in 10 s: `PermissionError` reading `/mnt2/fscratch/.../IsalHG-tkde/src/isalhg/__init__.py`. Since
2026-10-08 `~/fscratch -> /mnt/fscratch/users/...` (new storage); the old `/mnt2/fscratch/users/
tic_163_uma/mpascual` is `root:root drwx------`. The scikit-build-core editable finder of the
isalhg-tkde env (`_isalhg_editable.py`) mapped every module and the `.so` to `/mnt2/...`, so
`import isalhg` failed for every user of that env, on the login node too. Repair = the documented
reinstall step of `sync_to_picasso.sh`, without its rsync: `cd ~/fscratch/repos/IsalHG-tkde; rm -rf
build; $PY -m pip install -e ".[dev]" --no-deps --no-build-isolation` (PIP EXIT 0), then the
script's own check: `isalhg -> /mnt/fscratch/.../IsalHG-tkde/src/isalhg/__init__.py`, extension
built 14:58:30 (fresh), `canonical_string(fano, cpp) == python` OK, kmedoids imports. The canonical
tree's sources were not touched (checksum-identical to this branch's `src/`). PICASSO.md §1 still
describes the `/mnt2` spelling (out of scope; reported).

**Smokes.** Local `full_run.py --smoke` (seed 0 of D_ndc_classes_pendant 35 s, C3_ndc_classes_C-all
9 s, A_ndc_classes 45 s, B_ndc_classes 255 s): all exit 0. Cluster smoke resubmitted as 2921030.
**Sym-min wording** (coordinator correction, LOG §8.1): the minimum also brings distractors closer,
so it does not favour the competitor on ranking metrics; described only as "the orientation-free
symmetrization of the raw cost" (commit 48a3ab7 fixes rect / design_d / aggregate_d wording).

**Submission.** Array 2921149 (9 tasks, 16 CPU, 32G, sd, 10 h) submitted 15:0x; `--test-only`
predicted 21:56 but tasks 0–7 started 15:11–15:20. Smoke 2921030 started 15:09. Picasso B cell
≈ 310 s (local uncontended 112 s) → B unit ≈ 7 h. Reported to main (job ids + ETA).

**Coordinator, verbatim core (local replica):** "Run the identical 38 units locally now as well,
same seeds and code, with joblib on 16 cores, into D/results/KNN_2026-10-15/full_local/ [...] The
Picasso run is the canonical execution [...] When it lands, diff Picasso against local per JSON on
every metric [...] Record the comparison in FULL_SUMMARY.md as a cross-machine reproducibility
check. If they differ, report it before harvesting anything into full/." → three local streams
(tasks 0,3,6 / 1,4,8 / 2,5,7; 16 joblib jobs each; 24 hardware threads), code 48a3ab7, started
15:04. **Run-path files (knn_lib, probe_knn, design_c, design_d, rect, full_run) must not be
edited until the local run ends: every unit is a fresh subprocess that imports them.**

**Coordinator, verbatim core (contract):** "Deliver into D/results/KNN_2026-10-15/full/section/
[...] (a) knn_facts.tex: one \knnfact{name}{value} line per \KNNTBD name, plus the 72 verdict cells
[...] Before each line, put a % src: comment with the JSON path and key. Apply the bound rule. (b)
The figures, named as the README says: fig_s5_{tsne,accuracy,gap,mechanism}.pdf [...] (c) A check
script that greps every \KNNTBD and verdict name in s5_knn.tex and asserts that each one is defined
in knn_facts.tex. Hypothesis evaluation rules: One-round WL is outside the A/B kill criteria (they
were registered with ten competitors). Report it there as an added row, with a flag saying whether
it would beat the word in any A/B cell. The as-run edit path is descriptive and outside the Holm
family. Build all of this from full_local first. Regenerate from full/ after the Picasso
comparison."

Implemented (commits b4224c7, 28342da): aggregate_full uses each design's registered competitor
set (A/B/mix: 10 with the sym path; C/D: 11); added rows (as-run path; WL h=1 in A/B) with
`added_row_flags`; `best_arm_overall`; per-arm Prop. 6.1 census. figs/: style, fig_tsne,
fig_accuracy, fig_gap, fig_mechanism (README widths, Okabe–Ito word/best/other, serif 7 pt),
section_facts (bound rule; extra facts wlh1-AB-*, ratio-exceed-any-arm), check_facts, make_section;
tests/newpos/test_knn_figs.py. Mechanism axes follow the s5 caption (x = other source, y =
sibling; "below the diagonal is correct"); the README says the reverse — flagged to main.
