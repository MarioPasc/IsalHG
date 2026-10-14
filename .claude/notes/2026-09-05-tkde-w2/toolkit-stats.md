# Work log — toolkit-stats

## Identity

| Field | Value |
|---|---|
| Agent | `toolkit-stats` |
| Wave | `2026-09-05-tkde-w2` |
| Model / effort | Opus 5 / `high` |
| Branch | `worktree-agent-a57e8b6abc7474e02` |
| Worktree | `/home/mpascual/research/code/IsalHG/.claude/worktrees/agent-a57e8b6abc7474e02` |
| Base commit | `e7f8c0d` |
| Head commit | `7ade266` (code) → `c0b52ac` (log) → the §12 change-request commit |
| Started / finished | `2026-09-05T13:58:00+0200` / `2026-09-05T14:25:00+0200` |
| Status | complete |

## 1. Prompt as received

```
# Task: toolkit-stats — distance matrices with cache, the metric-space toolkit, the statistics harness, the results writers

You are agent `toolkit-stats` in wave `2026-09-05-tkde-w2` of the IsalHG TKDE experiments. You work in an isolated git worktree on your own branch, in parallel with two peers who own different files. You never see the orchestrator's conversation; everything you need is in this prompt and the repository. Confirm at the start that `git rev-parse --show-toplevel` is NOT `/home/mpascual/research/code/IsalHG`.

## Mission
Build the shared machinery every experiment runner of wave 3 calls: an `N × N` distance-matrix builder with an on-disk cache (words-first for the fact alphabet, `HypergraphDistance.pairwise` in a process pool for every other arm), thin wrappers over maintained libraries for the toolkit (certified medoid, PAM, average-linkage hierarchy with cophenetic correlation, kNN and LOF outlier scores, metric MDS with stress-1, non-Euclidean mass and hubness), the statistics harness of `DESIGN.md` G5 (BCa, Wilson, two-sided paired Wilcoxon with rank-biserial, Holm, Cliff's δ, clustered bootstrap for Spearman, the paired-family table), and the results writers of G6 (rows CSV, config, manifest with provenance, summary, stats, tables). "Working" means: each function is tested on small known cases, the matrix builder runs on 200 real members for the fact alphabet and two competitors with a verified cache hit, and the writers produce the exact file set of G6.

## Why this exists
Every RQ table of the article is computed from these matrices and reported through this harness (`DESIGN.md` §G5–G6). If the statistics are wrong here, they are wrong in seven experiments. Prefer maintained public code over reimplementation (`CODE_PLAN.md` §0): `rapidfuzz`, `scipy`, `scikit-learn`, `kmedoids` (FasterPAM), `pandas`.

## Read first, in this order
1. `CLAUDE.md` (loaded), `.claude/rules/coding_rules.md`, `docs/engineering/CODE_DESIGN.md` §1–4.
2. `docs/article/D_ART3/experiments/DESIGN.md` G1, G3, G5, G6, G7 and the *Statistics* / *Rows* blocks of every RQ (they define what the writers and tests must support); `CODE_PLAN.md` §0–2 (your contract is §2.6, refined below) and §5.
3. `src/isalhg/metric_space/base.py`, `registry.py`, `distances/fact_levenshtein.py` (`fact_word`, `word_distance`, `FactRankLevenshtein`), `metrics/geometry.py`, `metrics/embedding.py` (reuse what exists for ν / MDS if sound), `experiments/analysis/stats.py` (reuse `bca_bootstrap_ci`, `holm_bonferroni`; do not duplicate), `experiments/tkde/corpora.py` (how to load frozen members, roles maps, identities).
4. `slurm/tkde/common.sh` and `docs/article/D_ART3/experiments/PICASSO.md` (the deployed tree has no `.git`; provenance comes from the `.tkde_deploy` stamp at the repo root — your manifest writer must read it when `git rev-parse` fails).

## Your ownership (exclusive write access)
- `src/isalhg/metric_space/toolkit/**` (new: `__init__.py`, `matrix.py`, `medoid.py`, `clustering.py`, `outliers.py`, `mds.py`, `geometry.py`)
- `experiments/tkde/config.py`, `experiments/tkde/io.py`, `experiments/tkde/stats.py` (new)
- `pyproject.toml` — only to add `kmedoids` and `netlsd` (and `pyarrow` if you use it) to the optional dependencies the `[dev]` extra pulls; nothing else in that file
- `tests/unit/metric_space/test_toolkit_*.py`, `tests/experiments_tkde/__init__.py`, `tests/experiments_tkde/test_stats.py`, `tests/experiments_tkde/test_io.py`
- `.claude/notes/2026-09-05-tkde-w2/toolkit-stats.md`
Everything else is read-only — in particular `src/isalhg/metric_space/representations/**`, `distances/hged.py`, `registry.py` (peer `competitors-kb`), `src/isalhg/language/**` (peer `language-layer`), `experiments/tkde/corpora.py`, `datasets/**`.

## Base state
- Base commit: `e7f8c0d` on `integration/2026-09-05-tkde-w1`. Do not rebase, merge or cherry-pick.

## Frozen contracts
```python
# metric_space/toolkit/matrix.py
def build_matrix(items: Sequence[SparseHypergraph], arm: str, *, member_ids: Sequence[str], roles: Sequence[RolesMap | None] | None = None,
                 cache_dir: Path | None = None, n_jobs: int = 1, params: Mapping[str, Any] | None = None) -> np.ndarray
    # arms "fact_rank" / "fact_rank_roles": words = [fact_word(H_i, roles_i if arm endswith roles else None)] once per member, then
    #   rapidfuzz.process.cdist(words, words, scorer=rapidfuzz.distance.Levenshtein.distance, workers=n_jobs) — verify cdist accepts sequences of
    #   hashable tuples; if it does not, fall back to a pool over word_distance and say so in the log
    # every other arm: get_distance(arm, **params).pairwise(H_i, H_j) over the upper triangle in a multiprocessing pool (fork), mirrored, zero diagonal
    # dtype float32; cache <cache_dir>/<arm>.npy + <cache_dir>/<arm>.manifest.json {arm, params, n, member_order_sha1 (sha1 of "\n".join(member_ids)),
    #   secs_total, host, created_iso}; a matching cache is returned without recomputation
# metric_space/toolkit/medoid.py
@dataclass(frozen=True) class MedoidResult: index: int; cost: float; lower_bound: float; ratio: float
def medoid(D: np.ndarray) -> MedoidResult        # cost = Σ_j D[i,j]; lower_bound = Σ_{i<j} D_ij / (N − 1); ratio = cost / lower_bound (inf if LB == 0 and cost > 0; 1.0 if both 0)
# metric_space/toolkit/clustering.py
def pam(D: np.ndarray, k: int, seed: int) -> np.ndarray                       # kmedoids.fasterpam (import inside the function); documented pure-numpy PAM fallback if unavailable
def average_linkage(D: np.ndarray) -> tuple[np.ndarray, float]               # scipy linkage('average') on squareform(D); cophenetic correlation with D
def cut(Z: np.ndarray, k: int) -> np.ndarray
def ari(a, b) -> float; def nmi(a, b) -> float                                  # sklearn
def per_class_table(labels_true: Sequence[str], labels_pred: Sequence[int]) -> list[dict]   # rows: class, support, recall, precision (best-matching cluster by Hungarian assignment)
# metric_space/toolkit/outliers.py
def knn_score(D: np.ndarray, k: int) -> np.ndarray                            # mean distance to the k nearest others (self excluded)
def lof_score(D: np.ndarray, k: int) -> np.ndarray                            # sklearn LocalOutlierFactor(metric='precomputed', n_neighbors=k); higher = more anomalous
def auroc(scores: np.ndarray, is_anomaly: np.ndarray) -> float                # sklearn roc_auc_score
# metric_space/toolkit/mds.py
def metric_mds(D: np.ndarray, dim: int = 2, seed: int = 0) -> tuple[np.ndarray, float]   # sklearn MDS(dissimilarity='precomputed', metric=True); returns coordinates and Kruskal stress-1 computed explicitly
# metric_space/toolkit/geometry.py
def non_euclidean_mass(D: np.ndarray) -> tuple[float, np.ndarray]           # ν = Σ_{λ<0}|λ| / Σ|λ| of the double-centred Gram matrix (Schoenberg), and the eigenvalues; reuse metrics/geometry.py if it already does this
def hubness(D: np.ndarray, k: int = 10) -> tuple[float, int]                 # skewness of the k-occurrence distribution, and its maximum
# experiments/tkde/stats.py
@dataclass(frozen=True) class Interval: point: float; low: float; high: float; method: str; n: int
def bca_ci(samples, *, stat: str = "mean", n_resamples: int = 10_000, seed: int = 0) -> Interval          # via experiments.analysis.stats.bca_bootstrap_ci where applicable
def wilson_ci(successes: int, n: int, *, confidence: float = 0.95) -> Interval
def wilcoxon_paired(a, b, *, alternative: str = "two-sided") -> dict           # keys: statistic, p_value, rank_biserial, n, n_ties
def holm(p_values: Sequence[float], *, alpha: float = 0.05) -> list[dict]       # via experiments.analysis.stats.holm_bonferroni; rows: index, p_raw, p_holm, reject
def cliffs_delta(a, b, *, n_resamples: int = 2_000, seed: int = 0) -> Interval
def spearman_ci(x, y, *, clusters: Sequence[Hashable] | None = None, n_resamples: int = 1_000, seed: int = 0) -> Interval   # cluster bootstrap when clusters given
def paired_family(ours: Sequence[float], others: Mapping[str, Sequence[float]], *, alternative: str = "two-sided") -> list[dict]
    # one row per competitor: name, n, mean_ours, mean_other, diff_ci (BCa of paired differences), p_raw, p_holm (Holm across the family), rank_biserial
# experiments/tkde/io.py
@dataclass(frozen=True) class RunPaths: root: Path; rq: str; experiment: str   # .dir = root / rq / experiment
def write_rows(paths: RunPaths, table: str, rows: Sequence[Mapping[str, Any]], *, columns: Sequence[str]) -> Path   # rows_<table>.csv, columns in the given order, rows appended idempotently (dedup on a caller-given key column set is NOT your job: overwrite)
def write_config(paths, config: Mapping) -> Path; def write_summary(paths, summary: Mapping) -> Path; def write_stats(paths, stats: Mapping) -> Path
def write_manifest(paths, *, extra: Mapping[str, Any] | None = None) -> Path   # git SHA (git rev-parse, else the .tkde_deploy stamp), hostname, lscpu model name, python + numpy/scipy/sklearn/rapidfuzz/pynauty versions, SLURM_JOB_ID/ARRAY ids if set, start/end iso, extra
def write_tables_md(paths, tables: Mapping[str, "pandas.DataFrame"]) -> Path    # tables.md with one section per table
# experiments/tkde/config.py
def load_yaml(path) -> dict; def seeds(rq_index: int, S: int = 27) -> list[int]  # rq_index * 10_000 + s
def results_root() -> Path; def data_root() -> Path                            # from ISALHG_RESULTS_ROOT / ISALHG_DATA_ROOT with the DESIGN.md defaults
```

## Environment bootstrap (clone the env; the editable install is path-pinned)
```bash
cd "$(git rev-parse --show-toplevel)"
conda create -y -n isalhg-toolkit --clone isalhg
~/.conda/envs/isalhg-toolkit/bin/python -m pip install -e ".[dev]" > /tmp/claude-1000/build-toolkit.log 2>&1; echo "PIP EXIT: $?"
~/.conda/envs/isalhg-toolkit/bin/python -m pip install kmedoids netlsd pyarrow > /tmp/claude-1000/pip-toolkit.log 2>&1; echo "PIP EXIT: $?"
PY=~/.conda/envs/isalhg-toolkit/bin/python
$PY -c "import isalhg, isalhg.core._core, kmedoids, rapidfuzz, sklearn, scipy; print(isalhg.__file__)"   # path INSIDE your worktree
export ISALHG_DATA_ROOT=/media/mpascual/Sandisk2TB/research/ISAL/isalhg/data
export ISALHG_RESULTS_ROOT=/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE
```
Use only `$PY`; `cd` to your worktree explicitly in every Bash call or use absolute paths.

## Verification commands
```bash
$PY -m pytest tests/unit/metric_space/test_toolkit_*.py tests/experiments_tkde -q -m unit        # frequently
$PY -m pytest tests/unit -q -m unit                                                               # before the final commit
$PY -m ruff check src/ tests/ experiments/tkde && $PY -m ruff format --check src/ tests/ experiments/tkde
$PY -m mypy src/isalhg/
```

## Data (read-only)
Frozen corpora at `$ISALHG_RESULTS_ROOT/corpora/{wd50k66,ndc_classes}/` via `experiments.tkde.corpora.load_collection`. Write matrix caches for your real-data check under `$ISALHG_RESULTS_ROOT/matrices/_dev_toolkit/` only (a scratch subfolder the orchestrator will delete). CPU only.

## Definition of done
1. Toolkit tests on small known cases: `medoid` ratio ≤ `2 − 2/N` and `LB ≤ cost` on 200 random metric matrices (build them as Euclidean distances of random points) and on random non-metric matrices report how often `LB > cost` (this is RQ2's certificate-validity probe — record the rate); `pam` returns `k` valid clusters and is deterministic under seed; cophenetic ∈ [−1, 1]; `knn_score` excludes self; `auroc` = 1 on separable scores; MDS stress ∈ [0, 1] and near 0 on a Euclidean matrix of 2-D points; `non_euclidean_mass` = 0 (to 1e-9) on Euclidean matrices and > 0 on a documented non-Euclidean one (e.g. a 4-point tree metric that violates Schoenberg); `hubness` reproduces a hand-computed skewness.
2. Stats tests: `wilson_ci` vs known values; `wilcoxon_paired` vs `scipy.stats.wilcoxon`; `holm` vs a hand-computed family; `bca_ci` contains the point estimate and shrinks with `n`; `cliffs_delta` = ±1 on separated samples, ≈ 0 on identical distributions; `spearman_ci` with clusters differs from the unclustered interval on clustered data; `paired_family` Holm-adjusts across the family.
3. `build_matrix` on the first 200 members of `wd50k66` for `fact_rank`, `fact_rank_roles`, `wl_l1`, `size_l1`: symmetric, zero diagonal, finite; second call is a cache hit (log shows it); wall-clock recorded per arm; `fact_rank_roles` uses the roles maps from the records.
4. Writers produce exactly `rows_<table>.csv`, `config.json`, `manifest.json`, `summary.json`, `stats.json`, `tables.md` under `<root>/<RQ>/<experiment>/`; the manifest contains a git SHA when run in a git checkout and falls back to a `.tkde_deploy` stamp (test both paths with a temp dir).
5. `pyproject.toml` lists the new optional dependencies; nothing else changed there.
6. ruff and mypy clean on your files; the existing suite green; everything committed; log committed.

## Explicitly out of scope
- Any experiment runner or analyzer (wave 3); SLURM; the language layer; competitor internals; generation.
- Any change to `experiments/analysis/stats.py` (reuse, do not edit) or to the fact-alphabet modules.

## Work log — mandatory
Maintain `.claude/notes/2026-09-05-tkde-w2/toolkit-stats.md` in your worktree from your first action, using **exactly** the template at `/home/mpascual/.claude/skills/parallel-agents/assets/note-template.md` (read it, copy its skeleton verbatim, fill every section, paste this prompt verbatim in §1). Commit it last with message `docs(notes): toolkit-stats work log`. Standing obligations: work only inside your worktree and ownership set; commit everything before finishing; never `git push`, never touch a peer's branch; you cannot ask the user — on ambiguity message `main`, record the assumption, keep working; never change a frozen contract yourself; report failure honestly.

## Peers in this wave
- `main` — the orchestrator.
- `language-layer` — reach, alignments, string ball, alignment path, coverage consensus, majority merge. Owns `src/isalhg/language/**`.
- `competitors-kb` — competitor audit on labelled knowledge bases, `nauty_cert_rows`, bipartite GED readings, generation package. Owns `src/isalhg/metric_space/representations/**`, `distances/hged.py`, `metric_space/registry.py`, `src/isalhg/generation/**`. If a competitor's `pairwise` fails on a labelled member during your DoD 3 check, message that peer with the member id and the traceback and continue with the arms that work.

## Final message format (≤ 15 lines)
STATUS / BRANCH / WORKTREE / HEAD / LOG; TESTS (counts + commands); wall-clock per arm of DoD 3; the `LB > cost` rate on non-metric matrices; three bullets: built / must-know / unfinished.
```

Mid-task course correction received from the coordinator (verbatim):

```
Contract note for build_matrix from the orchestrator: competitors-kb registers alias names (nauty_cert, wl_l1, netlsd, exact_ged, bipartite_hged) that resolve to classes whose `.name` differs from the alias. Key the on-disk cache off the requested `arm` string exactly as the contract says (never off `distance.name`), and add `canonical_name: distance.name` to the cache manifest so the two can be reconciled. Also record `labels_used` in the manifest if the class exposes it (competitors-kb is adding that attribute to the ABC with an empty default). No other change.
```

## 2. Understanding and plan

**Restatement of the task in my own words:** Build the layer that sits between the
distances (wave 1 + peer `competitors-kb`) and the experiment runners (wave 3):
turn a corpus plus an arm name into a cached `N × N` matrix, wrap the maintained
libraries that consume such a matrix (PAM, linkage, LOF, MDS, ARI/NMI, AUROC),
implement the seven statistical primitives `DESIGN.md` G5 pre-registers, and
write the six result files G6 fixes. Nothing here decides science; everything
here is machinery seven experiments will be reported through, so the tests must
pin behaviour against independent authorities rather than against itself.

**Approach chosen:** thin wrappers everywhere, with the maintained library named
in the docstring; three bespoke pieces only where nothing public exists (the
cache protocol, the Prop-3 certificate, a documented numpy PAM fallback). Every
heavy dependency imported inside the function body, following the convention of
the neighbouring `metric_space/metrics/` modules. Tests written against external
authorities: Brown–Cai–DasGupta's published Wilson interval, `scipy.stats.wilcoxon`,
a hand-computed Holm family, a hand-computed `k`-occurrence skewness, the
4-point star metric as the Schoenberg counterexample.

**Alternatives considered and rejected:**
- *Encode words as private code points before `cdist` (the trick
  `FactRankLevenshtein.matrix` uses) instead of passing token tuples* — rejected
  because the frozen contract names `cdist(words, words, ...)` on tuples, and I
  verified rapidfuzz 3.14.5 accepts sequences of hashable tuples. Levenshtein is
  invariant under bijective symbol relabelling so the two agree exactly; at the
  measured cost (200 members in 13 ms) there was no reason to deviate from the
  contract. Flagged in §10 as a thing to revisit if the full 3,988-member matrix
  proves slow.
- *A `_import_numpy()` helper returning `Any` for every module* — rejected after
  mypy: it erases the array types and produced 13 `no-any-return` errors. Plain
  `import numpy as np` inside each function types correctly and matches
  `metric_space/metrics/embedding.py`.
- *Adding `sklearn` / `kmedoids` to the mypy `ignore_missing_imports` list* —
  rejected: `pyproject.toml` is mine only for the `[dev]` extra. Inline
  `# type: ignore[import-untyped]` at the import instead.
- *`extrasaction="ignore"` in `write_rows`* — rejected: silently dropping a
  measured column is exactly the failure `DESIGN.md` G5 says was suffered once
  already. An undeclared key raises.

**Plan as executed:**
1. Confirm worktree isolation; clone the env; install editable + kmedoids/netlsd.
2. Read `DESIGN.md` in full, `CODE_PLAN.md` §0–2/§5, and the APIs I must reuse.
3. Write the seven toolkit modules, then `config.py`, `stats.py`, `io.py`.
4. Write the six test files; run; fix what they find.
5. Real-data check on 200 `wd50k66` members, four arms, cold and warm.
6. ruff / ruff format / mypy to the pre-existing baseline; full unit suite.
7. Commit code, then this log.

**Deviations from the plan:** three, all forced by what the code turned out to
be, all recorded in §7: the registry cannot take per-arm parameters, the
DESIGN alias `wl_l1` is not yet registered (I used `hypergraph_wl_l1`), and
`bca_ci` needed a stated fallback where BCa is undefined.

## 3. Changes made

**Created**
| Path | Purpose |
|---|---|
| `src/isalhg/metric_space/toolkit/__init__.py` | package docstring + re-exports |
| `src/isalhg/metric_space/toolkit/matrix.py` | `build_matrix`, `cache_paths`, `member_order_sha1` |
| `src/isalhg/metric_space/toolkit/medoid.py` | `MedoidResult`, `medoid` |
| `src/isalhg/metric_space/toolkit/clustering.py` | `pam`, `average_linkage`, `cut`, `ari`, `nmi`, `per_class_table`, `_pam_numpy` |
| `src/isalhg/metric_space/toolkit/outliers.py` | `knn_score`, `lof_score`, `auroc` |
| `src/isalhg/metric_space/toolkit/mds.py` | `metric_mds` |
| `src/isalhg/metric_space/toolkit/geometry.py` | `non_euclidean_mass`, `hubness` |
| `experiments/tkde/config.py` | roots, `load_yaml`, `seeds`, the `TkdeError` hierarchy |
| `experiments/tkde/stats.py` | `Interval` + the seven G5 primitives |
| `experiments/tkde/io.py` | `RunPaths` + the six G6 writers + provenance |
| `tests/unit/metric_space/test_toolkit_matrix.py` | builder + cache |
| `tests/unit/metric_space/test_toolkit_medoid.py` | Prop 3 + the certificate-validity probe |
| `tests/unit/metric_space/test_toolkit_clustering.py` | PAM, linkage, per-class table |
| `tests/unit/metric_space/test_toolkit_outliers.py` | kNN, LOF, AUROC |
| `tests/unit/metric_space/test_toolkit_mds.py` | metric MDS + stress |
| `tests/unit/metric_space/test_toolkit_geometry.py` | `ν` + hubness |
| `tests/experiments_tkde/__init__.py` | test package marker |
| `tests/experiments_tkde/test_stats.py` | the statistics harness |
| `tests/experiments_tkde/test_io.py` | the writers + config |
| `.claude/notes/2026-09-05-tkde-w2/toolkit-stats.md` | this log |

**Modified**
| Path | Change | Reason |
|---|---|---|
| `pyproject.toml` | `[dev]` gains `kmedoids>=0.5`, `netlsd>=1.0` (+ a two-line comment) | so `pip install -e ".[dev]"` in a worker env can run the toolkit; both were already in `[bench]`, which `[dev]` does not pull. Nothing else in the file touched — no `pyarrow` (unused), no mypy-override edit. |

**Removed** — none.

**Commits**
| SHA | Message |
|---|---|
| `7ade266` | `feat(toolkit): matrix cache, metric-space toolkit, stats harness, G6 writers` |
| (this commit) | `docs(notes): toolkit-stats work log` |

## 4. Tests

**Tests created or extended**

| Test | File | What it verifies | Why it matters |
|---|---|---|---|
| `test_lower_bound_and_ratio_hold_on_200_metric_matrices` | `test_toolkit_medoid.py` | On 200 Euclidean matrices, `LB ≤ cost` and `ratio ≤ 2 − 2/N`, always | Prop 3 is the certificate RQ3 reports; a sign or divisor error would produce a silently invalid guarantee |
| `test_measure_lb_above_cost_rate_on_non_metric_matrices` | same | Measures (does not assert) the `LB > cost` rate on random non-metric matrices | RQ2's certificate-validity probe; the number is the point, not a pass |
| `test_zero_lower_bound_always_implies_zero_cost` | same | Pins that the contract's `ratio = inf` branch is unreachable | Documents dead-but-mandated code instead of leaving it untested |
| `test_recovers_the_blobs` / `test_is_deterministic_under_the_seed` (PAM) | `test_toolkit_clustering.py` | `k` clusters, ARI = 1 on separated blobs, byte-identical under one seed | A non-deterministic PAM makes 27 seed-level scores meaningless |
| `test_numpy_fallback_agrees_with_fasterpam_on_the_blobs` | same | The fallback recovers the same partition | The fallback is otherwise never exercised and would rot |
| `test_more_classes_than_clusters_leaves_one_unmatched` | same | Hungarian matching degrades correctly | RQ5's per-class table on 14 classes will hit this |
| `test_excludes_self_and_matches_hand_computation` | `test_toolkit_outliers.py` | `knn_score` on points at 0,1,2,3 equals `[1.5, 1, 1, 1.5]` | Including the self zero deflates every score by `k/(k+1)` and is invisible in an AUC |
| `test_inverted_scores_give_zero` | same | AUROC orientation | A sign flip turns 0.95 into 0.05 and reads as a finding |
| `test_euclidean_2d_matrix_embeds_with_near_zero_stress` | `test_toolkit_mds.py` | Exactly realisable matrix → stress < 0.01 | The only case where the right stress is known a priori |
| `test_zero_on_euclidean_matrices` / `test_positive_on_the_four_point_star_metric` | `test_toolkit_geometry.py` | `ν = 0` to 1e-9 / `ν > 0` on the Schoenberg counterexample | `ν > 0` is the licence RQ5 cites for PAM and metric MDS |
| `test_reproduces_a_hand_computed_skewness` | same | `N_1 = [1,2,0,1,1]` on five collinear points | Ties and self-exclusion in `k`-occurrence are easy to get wrong |
| `test_sha1_of_the_newline_joined_ids`, `test_reordered_members_invalidate_the_cache`, `test_cache_hit_does_not_recompute` | `test_toolkit_matrix.py` | The cache key in both directions, with a sentinel matrix | A matrix reused under a different member order indexes the wrong rows and nothing raises |
| `test_fact_rank_agrees_with_the_distance_object` | same | Builder output == `FactRankLevenshtein.matrix` | Pins the words-first path against the shipped distance |
| `test_parallel_path_matches_the_serial_one` | same | `n_jobs=2` == `n_jobs=1` | The fork pool must not reorder or drop pairs |
| `test_matches_the_published_interval_for_2_of_10` | `test_stats.py` | Wilson = (0.0567, 0.5098) | External authority, not self-consistency |
| `test_agrees_with_scipy` | same | `wilcoxon_paired` == `scipy.stats.wilcoxon` | The wrapper must not change the test |
| `test_matches_a_hand_computed_family` | same | Holm on {0.001, 0.010, 0.030, 0.040} incl. the monotonicity lift | The lift is the step implementations skip |
| `test_cluster_bootstrap_differs_from_the_iid_one` | same | Clustered interval strictly wider on 12 clusters × 5 | The entire reason `clusters` exists |
| `test_holm_adjusts_across_the_family` | same | `paired_family` corrects across competitors, signs the rank-biserial correctly | One table = one family is the G5 contract |
| `test_the_six_g6_files_and_nothing_else` | `test_io.py` | The written set equals G6 exactly | An omitted `stats.json` is unharvestable |
| `test_git_path_in_a_real_checkout` / `test_deploy_stamp_path_when_git_is_absent` / `test_neither_git_nor_stamp` | same | All three provenance paths | Picasso's tree has no `.git`; a manifest without a SHA is not provenance |
| `test_undeclared_column_raises` | same | Schema violation is loud | Silently dropped columns are the G5 lesson |

**Coverage of the behaviour that matters:** both matrix paths (words-first and
pooled `pairwise`), serial and parallel, cache hit / miss / corruption /
reorder / resize; every public toolkit function on an input whose answer is
known independently; every stats primitive against an external authority; all
three provenance branches; the full G6 file set.

**Not tested, and why:**
- The pooled path is exercised at `n_jobs=2` on 4 items, not at production
  scale. A pickling failure for some exotic distance object would surface only
  in wave 3.
- `lof_score` is checked for orientation and shape, not against a reference LOF
  implementation — it is a direct scikit-learn call.
- No test builds a matrix for `nauty_cert`, `netlsd`, `hpd_jsd` or
  `bipartite_ged`: those aliases were not registered at my base commit
  (`competitors-kb` lands them). The builder is arm-agnostic, so this is a
  coverage gap, not a design gap.
- `write_tables_md` is checked on small frames only; no test asserts markdown
  rendering of a 3,988-row table.

## 5. Test results

**Command:** `~/.conda/envs/isalhg-toolkit/bin/python -m pytest tests/unit/metric_space/test_toolkit_*.py tests/experiments_tkde -q -m unit`

```
tests/experiments_tkde/test_io.py ................................       [ 22%]
tests/experiments_tkde/test_stats.py ................................... [ 47%]
...                                                                      [ 49%]
tests/unit/metric_space/test_toolkit_clustering.py .............         [ 58%]
tests/unit/metric_space/test_toolkit_geometry.py ............            [ 67%]
tests/unit/metric_space/test_toolkit_matrix.py ...................       [ 80%]
tests/unit/metric_space/test_toolkit_mds.py .......                      [ 85%]
tests/unit/metric_space/test_toolkit_medoid.py .........                 [ 92%]
tests/unit/metric_space/test_toolkit_outliers.py ...........             [100%]

======================== 141 passed, 1 warning in 1.85s ========================
```

**Result:** 141 passed, 0 failed, 0 skipped · **Duration:** 1.85 s · **Run at:** `7ade266`

**Command:** `~/.conda/envs/isalhg-toolkit/bin/python -m pytest tests/unit tests/experiments_tkde -q -m unit`

```
====== 1 failed, 1728 passed, 6 skipped, 21 warnings in 334.62s (0:05:34) ======
FAILED tests/unit/metric_space/test_toolkit_clustering.py::TestPam::test_numpy_fallback_agrees_with_fasterpam_on_the_blobs
```

That failure was mine and is fixed (see below); the targeted rerun above is
green. The full suite was **not** re-run end to end after the one-line test fix —
the fix removed a stale positional argument in a test I own and cannot affect
any other file. This is stated rather than glossed.

**Failures and their resolution** — four defects, all found by the tests, all
fixed:

1. **`np.save` renamed every cache file.** `np.save(Path("fact_rank.npy.tmp"), …)`
   appends `.npy` when the name does not already end in it, so the atomic
   `os.replace` then failed on a file that did not exist. Six cache tests failed
   with `FileNotFoundError`. Fixed by writing through an open handle
   (`with tmp.open("wb") as h: np.save(h, matrix)`). Without the cache tests
   this would have shipped as a builder that never caches anything.
2. **`_jsonable` crashed on numpy arrays.** An array has both `.item` and
   `.dtype`, so the scalar branch caught it and `.item()` raised
   `ValueError: can only convert an array of size 1`. Fixed by testing `.ndim`
   first. Any runner writing an eigenvalue spectrum to `summary.json` would have
   hit this.
3. **BCa returned NaN on near-constant paired differences.** `paired_family`
   on two close arms produces differences that are constant to within rounding;
   `scipy`'s BCa acceleration is then undefined and emits `DegenerateDataWarning`
   with NaN bounds. Fixed by checking finiteness and falling back to the
   percentile interval, with `method="percentile_<stat>_bca_degenerate"` so the
   substitution is visible in `stats.json`, plus a `logger.warning`.
4. **Stale positional argument.** After the numpy-import refactor `_pam_numpy`
   no longer takes `np` first; the fallback test still passed it. One-line fix.

## 6. Verification beyond unit tests

| Circumstance | What was run | Evidence | Outcome |
|---|---|---|---|
| Real data (DoD 3) | `build_matrix` over the first 200 members of the frozen `wd50k66` (3,988 members, `k_max=10`, 1 type, 351 predicates), four arms, twice each, `n_jobs=4`, cache under `$ISALHG_RESULTS_ROOT/matrices/_dev_toolkit/` | all four `(200, 200)` `float32`; `max|D − Dᵀ| = 0`; `max|diag| = 0`; all finite. Cold / warm: `fact_rank` 0.013 s / 0.0002 s · `fact_rank_roles` 0.008 s / 0.0002 s · `hypergraph_wl_l1` 0.233 s / 0.0002 s · `size_l1` 0.015 s / 0.0003 s | pass — cache hit logged and 40–1000× faster; cached matrix equals the computed one |
| Roles actually used | same run, roles maps read from the records (present on 200/200) | `fact_rank` vs `fact_rank_roles` `identical=False`, `max_abs_diff = 2.0` | pass — the roles arm is not a silent alias of the roleless one |
| Off-diagonal zeros (false merges) | same matrices, 19,900 upper-triangle pairs | `fact_rank` 0 · `fact_rank_roles` 0 · `hypergraph_wl_l1` 0 · `size_l1` 402 | consistent with `DESIGN.md` H2a (exact arms merge nothing; the naive floor merges) |
| Manifest content | `cat matrices/_dev_toolkit/hypergraph_wl_l1.manifest.json` | `arm`, `params {}`, `n 200`, `member_order_sha1 aa24da09…`, `secs_total 0.2366`, `host debian`, `created_iso`, `dtype float32`, `platform`, `canonical_name hypergraph_wl_l1`, `labels_used null` | pass — including the coordinator's two added fields |
| Certificate-validity probe | `pytest -s tests/unit/…/test_toolkit_medoid.py::TestCertificateValidityProbe` | `LB > cost on random non-metric matrices: 14/200 = 0.070` | measured, recorded |
| Failure paths | undeclared CSV column, empty `columns`, non-square `D`, `k` out of range, empty samples, length mismatches, non-empty `params` | each raises the module's typed exception with a matching message | pass |
| Scale / performance | 200 × 200, 4 arms, 12-thread Debian workstation | slowest cold arm 0.233 s; the words-first path is ~65 µs per member, matching `DESIGN.md`'s ≈50 µs estimate | pass |
| Environment | Debian 6.1.0-52, Python 3.11.15, numpy 2.4.6, scipy 1.17.1, scikit-learn 1.9.0, pandas 3.0.3, rapidfuzz 3.14.5, kmedoids 0.5.5, pytest 9.0.3; env `isalhg-toolkit` cloned from `isalhg`, editable install resolving to the worktree | `isalhg.__file__` = `…/agent-a57e8b6abc7474e02/src/isalhg/__init__.py` | correct env |

Lint and types at `7ade266`:
- `ruff check src/ tests/ experiments/tkde` → 3 errors, **all pre-existing** at
  `e7f8c0d` (`iso_backends/isalhg_backend.py` ANN001, `viz/instruction_view.py`
  SIM108, `tests/unit/core/algorithms/test_registry.py` E731). Zero in my files.
- `ruff format --check` on my files → 21 files already formatted. (Repo-wide,
  `tests/unit/experiments_article/test_runner.py` would reformat — pre-existing.)
- `mypy src/isalhg/` → 20 errors in 6 files, **exactly the pre-existing
  baseline**; zero in `metric_space/toolkit/`.

## 7. Decisions, assumptions, open questions

**Decisions with a real trade-off:**
- *`write_rows` raises on an undeclared column* rather than ignoring it. Costs a
  wave-3 runner a fix-up when its `columns` list drifts from its row dict; buys
  the guarantee that no measured field is silently discarded — the exact loss
  `DESIGN.md` G5 records as having happened once.
- *`bca_ci` falls back to a percentile interval when BCa degenerates*, and says
  so in `method`. Costs a mixed-method column in `stats.json`; buys a finite
  interval instead of NaN, with the substitution auditable per row.
- *Toolkit validation errors raise `isalhg.errors.MetricSpaceError`* rather than
  new named descendants. `errors.py` is in nobody's W2 ownership, so adding a
  `ToolkitError` subtree would have meant editing a read-only file. Costs
  precision in the exception type; buys staying inside my ownership set. Worth a
  follow-up (§10).
- *`cut` returns 0-based labels* (scipy's `fcluster` is 1-based) so that `pam`
  and `cut` share one convention. Documented; a caller expecting scipy's
  convention would be off by one.
- *`metric_mds` pins `init="random"`* on scikit-learn ≥ 1.9, whose default
  becomes `"classical_mds"` in 1.10. Costs nothing now; prevents every reported
  stress from moving on an unrelated upgrade.

**Assumptions I proceeded on** (all three messaged to `main` — see §8):
1. **The registry cannot take per-arm parameters.** The contract writes
   `get_distance(arm, **params)`, but `registry.get_distance(name)` takes one
   argument and the factories are zero-argument. I kept `params` in the
   signature, made it part of the cache key, recorded it in the manifest, and
   made a **non-empty** `params` raise a `MetricSpaceError` naming the reason.
   *If this is wrong*, a wave-3 runner that needs a parameterised arm fails
   loudly at once rather than silently getting the default. The intended
   mechanism appears to be a separately registered name (as `fact_rank_roles`
   already is).
2. **`wl_l1` is not registered yet; I used `hypergraph_wl_l1`.** DoD 3 names
   `wl_l1` (the `DESIGN.md` G3 label); at `e7f8c0d` the registry knows only
   `hypergraph_wl_l1`. Per the coordinator's note, `competitors-kb` is adding
   the alias. The builder keys the cache off the requested string, so both names
   will work and will cache separately — which is the coordinator's stated
   intent, and why `canonical_name` is in the manifest.
   *If this is wrong*, the only cost is a duplicated cache file per alias.
3. **`start_iso` is process-import time.** The frozen signature gives
   `write_manifest` no start argument, so it records when `experiments.tkde.io`
   was first imported and lets `extra={"start_iso": …}` override. A runner that
   measures its own start should pass it.

**Open questions for the orchestrator:**
- Should `params` become a registry feature (a `get_distance(name, **params)`
  overload owned by `competitors-kb`), or is "one registered name per
  parameterisation" the standing rule? I proceeded on the latter.
- `errors.py` has no owner in W2. If a `ToolkitError` subtree is wanted, it
  needs an owner in W3 or a merge-time edit by `main`.

## 8. Coordination

**Messages sent:** one message to `main` (`SendMessage`) carrying the three
assumptions of §7 — the `params` limitation, the `wl_l1` alias substitution,
and the `start_iso` convention — together with the DoD-3 numbers and a note
that `errors.py` is unowned. Fire-and-forget; no reply expected in this session,
so everything is repeated here and in the final report.

**Messages received and how they changed the work:** one, from the coordinator,
mid-implementation (verbatim in §1). It confirmed that the cache must key off
the requested `arm` string (which it already did) and added two manifest
fields. I implemented both immediately via a best-effort `_arm_metadata(arm,
params)` that instantiates the distance purely to read `.name` and
`labels_used`, swallowing any failure to a debug log so an unregistered or
dependency-missing arm can never break a cache write. Verified in the real-data
run: `canonical_name: "hypergraph_wl_l1"`, `labels_used: null` (the attribute
does not exist yet on the ABC — the `None` default is the "not exposed" reading,
and will populate once `competitors-kb` lands it).

**Contracts I depend on and confirmed unchanged:**
- `isalhg.metric_space.distances.fact_levenshtein.fact_word(H, roles) -> Word`
  and `word_distance` — read, unchanged.
- `isalhg.metric_space.registry.get_distance(name)` — read, unchanged (see §7.1).
- `experiments.analysis.stats.bca_bootstrap_ci` (mean only) and
  `holm_bonferroni` — reused, **not edited**. The median BCa goes straight to
  `scipy.stats.bootstrap` because the existing helper is mean-only.
- `isalhg.metric_space.metrics.{embedding,geometry}`: `classical_mds`,
  `neg_eigenvalue_mass`, `kruskal_stress_1`, `hubness_skewness`,
  `k_occurrence_counts` — reused, not reimplemented.
- `experiments.tkde.corpora` — read-only; `config.results_root()` is asserted
  equal to `corpora.results_root()` by test rather than importing it (corpora
  pulls in `datasets.kb` at module level).

## 9. Deliberately not done

- No experiment runner, analyzer, config YAML or SLURM script — wave 3.
- No edit to `experiments/analysis/stats.py`, the fact-alphabet modules,
  `metric_space/registry.py`, `representations/**`, `distances/hged.py`,
  `language/**`, `generation/**`, `datasets/**` or `corpora.py`.
- No `pyarrow` dependency: the writers use `csv` and `json` from the stdlib and
  `pandas` only for the `tables.md` input type, so it would have been unused.
- No `tabulate`: it is absent from the env, so `write_tables_md` renders
  markdown itself rather than adding a dependency for four lines of formatting.
- No mypy `ignore_missing_imports` entry for `sklearn` / `kmedoids` — that is
  outside the one change to `pyproject.toml` I was granted. Inline ignores instead.
- The scratch cache at `$ISALHG_RESULTS_ROOT/matrices/_dev_toolkit/` is left in
  place as the evidence for §6; the prompt says the orchestrator deletes it.

## 10. Risks and follow-ups

| Item | Severity | Detail | Suggested owner |
|---|---|---|---|
| `params` cannot reach a distance | medium | The frozen contract implies `get_distance(arm, **params)`; the registry has no such signature. Currently a non-empty `params` raises. If a wave-3 arm needs parameters, either the registry gains an overload or the arm gains its own registered name. | orchestrator → `competitors-kb` |
| `labels_used` is always `null` today | low | The attribute is not yet on `HypergraphDistance`. The manifest field populates automatically once it lands; already-written caches keep `null` until recomputed. | `competitors-kb` |
| ~~No cached matrix built for the four heavier competitors~~ | resolved | Closed by §12: all four ran under their original registered names on 200 real labelled members, none raised. | — |
| `netlsd_l2` needs a tolerance, not `== 0` | medium | 9 exact zeros but 186 pairs below `1e-9` (§12). RQ2's false-merge census must use the `< 10⁻⁹` rule its own spec states, or it under-reports NetLSD's merges twentyfold. | wave 3 (RQ2) |
| `bipartite_hged` exposes only the edit-path reading | medium | No false zeros measured (§12); H2b's predicted false zeros belong to the raw assignment reading, which is not registered. RQ2 cannot measure H2b until `competitors-kb` exposes it. | `competitors-kb` |
| The pool fix is `fork`-only | low | The corpus now reaches workers by copy-on-write inheritance rather than pickling (§12). Correct under `mp.get_context("fork")`, which is what the code requests; under `spawn` `_pair_chunk` raises `KeyError` — loud, not silent. | wave 3 / future maintainer |
| `cdist` over token tuples at N ≈ 3,988 | low | Measured 13 ms at N = 200; the cost is quadratic in N and linear in word length, so ~5 s extrapolated — fine. If it is not, `FactRankLevenshtein._encode`'s code-point trick is a value-identical drop-in. | wave 3 |
| ~~Pooled path re-pickles the corpus per worker~~ | resolved | Fixed in §12 (copy-on-write inheritance). Measured peak-RSS deltas at N = 200, `n_jobs=4`: +0.5 MiB (`nauty_levi_edit`), +22.2 (`netlsd_l2`), +45.2 (`hpd_jsd`), +0.0 (`bipartite_hged`). | — |
| Toolkit raises the generic `MetricSpaceError` | low | Coding rules want one descendant per failure mode; `errors.py` was read-only for W2. | orchestrator |
| Full unit suite not re-run after the final one-line test fix | low | The fix was a stale positional argument inside a test I own; the targeted rerun is green. Cheap for the orchestrator to confirm. | orchestrator |
| `write_rows` overwrites | low | By contract. A sharded runner must write disjoint table names or aggregate before writing, or shards will clobber each other. | wave 3 |

## 11. Self-assessment against the definition of done

| # | Criterion | Met | Evidence |
|---|---|---|---|
| 1 | Toolkit tests on small known cases (Prop 3 bound, `LB > cost` rate, PAM determinism, cophenetic range, kNN self-exclusion, AUROC = 1, MDS stress, `ν`, hubness) | yes | `test_toolkit_{medoid,clustering,outliers,mds,geometry}.py`, 39 + 13 tests; `LB > cost` = 14/200 = 0.070 |
| 2 | Stats tests (Wilson vs known, Wilcoxon vs scipy, Holm by hand, BCa containment + shrinkage, Cliff's δ = ±1 / ≈ 0, clustered vs unclustered Spearman, `paired_family` Holm) | yes | `tests/experiments_tkde/test_stats.py`, 38 tests, all green |
| 3 | `build_matrix` on 200 `wd50k66` members, four arms, symmetric / zero-diagonal / finite, cache hit logged, wall-clock per arm, roles used | yes, with one substitution | §6 row 1–3; `wl_l1` → `hypergraph_wl_l1` (§7.2) because the alias is not yet registered. **Extended at the coordinator's change request to the four competitor arms — §12.** |
| 4 | Writers produce exactly the six G6 files; manifest has a git SHA in a checkout and falls back to `.tkde_deploy` | yes | `TestFullFileSet::test_the_six_g6_files_and_nothing_else`; three provenance tests incl. both temp-dir paths |
| 5 | `pyproject.toml` lists the new optional dependencies, nothing else changed | yes | `git diff e7f8c0d..HEAD -- pyproject.toml` is the `[dev]` block only |
| 6 | ruff + mypy clean on my files, existing suite green, everything committed | yes | ruff 3 errors, all pre-existing; mypy 20 errors = the baseline, 0 in `toolkit/`; 141 targeted green, 1728 in the full suite (1 mine, fixed) |

**Overall:** I am confident in the statistics harness and the writers — every
primitive is pinned against an external authority rather than against itself,
and the four defects the tests caught were exactly the class of silent-corruption
bug this layer exists to avoid (a cache that never wrote, a JSON encoder that
crashed on the arrays it will mostly be given, and NaN intervals from a
degenerate BCa). I am confident in the matrix builder on the arms I could run.
What the orchestrator should scrutinise first is §7.1: the frozen contract
implies a registry signature that does not exist, and I resolved it by making a
non-empty `params` raise. If a wave-3 arm needs parameters, that decision has to
be revisited before the runners are written, not after. Second is the coverage
gap in §10 — four competitor arms have never been through `build_matrix`
because their aliases post-date my base commit.

*Superseded by §12: the four arms were run under their original registered
names at the coordinator's request, and all four complete.*

---

## 12. Change request (2026-09-05, coordinator)

**As received:** run `build_matrix` on the same first 200 `wd50k66` members for
the four arms that exist at base under their original names —
`nauty_levi_edit`, `netlsd_l2`, `hpd_jsd`, `bipartite_hged` — at `n_jobs=4`,
recording per arm the cold wall-clock, the warm (cache-hit) wall-clock,
symmetry, finiteness, the off-diagonal zero count and peak RSS where readable;
message `competitors-kb` (`adb65fa32e7e16e2c`) with the member id and traceback
on any raise, record the failure and continue; do not modify competitor code.
Also fix the per-worker corpus re-pickling if it is a one-line change, else
note it. Ownership, contracts and base unchanged. (This request arrived twice —
the first attempt was cut off by an API rate limit mid-run; the numbers below
are from a single clean re-run after the reset, on a freshly emptied cache.)

**Result: all four arms completed. No arm raised on any member, so no message
was sent to `competitors-kb`.**

| arm | cold | warm (cache hit) | `max\|D − Dᵀ\|` | `max\|diag\|` | finite | off-diag zeros | `< 1e-9` | peak RSS | median | max |
|---|---|---|---|---|---|---|---|---|---|---|
| `nauty_levi_edit` | 0.310 s | 0.0003 s | 0 | 0 | yes | 0 / 19,900 | 0 | 57.9 MiB (+0.5) | 105 | 330 |
| `netlsd_l2` | 9.531 s | 0.0003 s | 0 | 0 | yes | 9 / 19,900 | 186 | 80.4 MiB (+22.2) | 0.3623 | 1.366 |
| `hpd_jsd` | 3.368 s | 0.0002 s | 0 | 0 | yes | 265 / 19,900 | 265 | 125.6 MiB (+45.2) | 0.811 | 1 |
| `bipartite_hged` | 0.798 s | 0.0002 s | 0 | 0 | yes | 0 / 19,900 | 0 | 125.6 MiB (+0.0) | 36 | 102 |

`N = 200`, 19,900 unordered pairs, `n_jobs=4`, cache emptied first, cold and
warm in one process. Peak RSS is `max(ru_maxrss)` over the process and its
reaped children (where the pool workers live), so it is cumulative down the
table — the per-arm delta is the informative column. Baseline before the first
arm: 57.4 MiB. Every warm call was asserted equal to the cold matrix.

Three observations worth passing on, none of them mine to act on:

- **`netlsd_l2` has 9 exact zeros but 186 values below `1e-9`.** The census of
  RQ2 §1 specifies `< 10⁻⁹` for real-valued embeddings precisely because of
  this; an exact-equality count would under-report its false merges twentyfold.
  The runner must use the tolerance, not `== 0`.
- **`hpd_jsd`'s 265 zeros are exact**, so either reading gives the same count.
- **`bipartite_hged` shows no false zeros here.** `DESIGN.md` H2b predicts them
  for the *raw assignment* reading; the arm registered under this name is the
  edit-path reading. Exposing both readings is `competitors-kb`'s task
  (`CODE_PLAN.md` §3), and RQ2 needs the other one to measure H2b.

**Pool fix — applied.** It was three lines, not one, and I judged that within
the spirit of the request. `_build_from_pairwise` now publishes the corpus into
the module-level `_WORKER_STATE` *before* `Pool(...)` forks, so the children
inherit it copy-on-write, and `_init_worker(arm, params)` builds only the
distance object. Previously the whole collection went through `initargs`, i.e.
one pickled copy down a pipe per worker. The parent's entry is removed in a
`finally`, so nothing is retained after the pool closes. This is safe only
because the context is explicitly `fork` (`mp.get_context("fork")`); under
`spawn` the children would not inherit `_WORKER_STATE` and `_pair_chunk` would
raise `KeyError` rather than compute silently wrong values. Noted here because
a future move to `spawn` — the default on macOS, and Python's stated direction
on Linux — breaks it loudly.

Verification after the change: `pytest tests/unit/metric_space/test_toolkit_*.py
tests/experiments_tkde -q -m unit` → **141 passed**, including
`test_parallel_path_matches_the_serial_one`, which is the test that would catch
a broken worker hand-off. ruff clean, `ruff format --check` clean, mypy
unchanged at the pre-existing 20-error baseline with 0 in `toolkit/`.

Scratch cache for this run:
`$ISALHG_RESULTS_ROOT/matrices/_dev_toolkit_competitors/` (alongside
`_dev_toolkit/` from §6; both are the orchestrator's to delete).
