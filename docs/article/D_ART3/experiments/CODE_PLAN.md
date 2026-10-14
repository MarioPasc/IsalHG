# IEEE TKDE experiments — engineering plan

*Companion to `DESIGN.md` (the science). This file is the engineering: module
map, frozen interface contracts, wave partition with file ownership, the
Picasso layout, and the results layout. Written 2026-09-05 by the orchestrator.
Agents implement against this file and `DESIGN.md`; they do not renegotiate
either. Anything an agent finds missing or wrong here is reported to the
orchestrator (`main`) and recorded as an assumption in its work log, never
solved by widening scope.*

## 0. Standing rules for every agent

- Read `CLAUDE.md`, `.claude/rules/coding_rules.md`, `docs/engineering/CODE_DESIGN.md`
  (layering: `core/` is stdlib-only; optional deps imported inside method
  bodies; registries), `DESIGN.md`, and this file. Read the probe reference
  implementations named in your task before writing code.
- Python 3.10+ syntax, type hints everywhere, NumPy docstrings, frozen
  dataclasses for values, `logging` not `print` in library code, pytest with
  markers, `ruff` clean, `mypy` clean on `src/isalhg/`.
- **Environment hazard (`CLAUDE.md`).** The editable install is path-pinned to
  the main checkout. In a worktree you MUST clone the env and reinstall:
  `conda create -y -n isalhg-<task> --clone isalhg && ~/.conda/envs/isalhg-<task>/bin/pip install -e ".[dev]"`
  and use only `~/.conda/envs/isalhg-<task>/bin/python`. Never share an env.
- Tests: `~/.conda/envs/isalhg-<task>/bin/python -m pytest tests/unit -q -m unit`
  (fast) and the property suite for anything touching words/canonical forms.
  Lint: `python -m ruff check src/ tests/`; types: `python -m mypy src/isalhg/`.
- Scope discipline: implement exactly the files you own; if a needed change
  falls in another agent's files, write an interface note in your log and
  message `main`. Prefer maintained public code over reimplementation
  (`rapidfuzz`, `pynauty`, `scikit-learn`, `scikit-learn-extra`, `scipy`,
  `netlsd`).
- Data root: `ISALHG_DATA_ROOT` (default
  `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/data`); results root:
  `ISALHG_RESULTS_ROOT` (default
  `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE`). On
  Picasso the data root is `~/fscratch/datasets/isalhg_tkde` and the results
  root is **`$HOME/results/IEEETKDE`** (permanent filesystem; decided
  2026-09-05 because FSCRATCH is purged and was over its file quota).
- Work log: `.claude/notes/<WAVE_ID>/<task-slug>.md` inside your worktree,
  committed; everything committed before you finish.

## 1. Module map (who owns what)

```
src/isalhg/
  core/fact_word.py                         W1-A   tokens, encoder (given ranks), TOTAL decoder, key, vocabulary
  iso_backends/canonical_order.py           W1-A   canonical_ranks(H) via pynauty on the Levi graph; certificate bytes/rows
  metric_space/distances/fact_levenshtein.py             W1-A   "fact_rank" (+ roles option) HypergraphDistance + word_distance()
  metric_space/distances/fact_addressing_ablations.py    W1-A   "fact_local_colour", "fact_local_key", "fact_degree_key" (RQ1 arms C, D, D1)
  datasets/schemas.py  (LabelVocabulary.fit)             W1-A
  datasets/kb/                              W1-B   KBRecord + JSONL io, wd50k.py, ndc_quarterly.py, ladders.py, corruptions.py, envelope_sweep.py, registry entries
  language/                                 W2-A   reach.py (delete-and-match), ball.py (string ball, decodability), alignment.py (path interiors), consensus.py (alignment-transfer candidates, coverage), majority.py
  generation/                               W2-C   ngram.py (KN/WB token n-gram), incidence_baseline.py (flat serialization + strict decoder), fidelity.py (JSD, novelty)
  metric_space/toolkit/                     W2-B   matrix.py (N×N builder w/ cache + multiprocessing), medoid.py (medoid, LB, ratio), clustering.py, outliers.py, mds.py, geometry.py (ν, hubness)
  metric_space/representations/*            W2-C   audit for labelled KBs (edge labels!), "nauty_cert_rows", bipartite both readings exposed
experiments/tkde/
  config.py, io.py (rows/manifest/summary writers), stats.py (harness)        W2-B
  corpora.py (load frozen JSONL → SparseHypergraph + roles/ids)               W1-B
  rq1.py, rq2.py, rq7.py + analyze_rq{1,2,7}.py                               W3-A
  rq3.py, rq6.py + analyze_rq{3,6}.py                                         W3-B
  rq4.py, rq5.py + analyze_rq{4,5}.py                                         W3-C
slurm/tkde/
  common.sh (env block, LOCALSCRATCH staging, copy-back, traps)               W1-C
  <rq>_launcher.sh / <rq>_worker.sh                                           W3-*
scripts/tkde/
  freeze_corpora.py                                                           W1-B
  sync_to_picasso.sh, harvest_from_picasso.sh, picasso_env_setup.sh           W1-C
docs/article/D_ART3/experiments/PICASSO.md                                    W1-C
tests/ mirror src/ (each agent owns the tests of its modules)
```

## 2. Frozen interface contracts

### 2.1 Tokens and the fact word (`core/fact_word.py`, W1-A)

```python
Rank: TypeAlias = int
RoleId: TypeAlias = int
Token: TypeAlias = tuple  # ("T", type_id) | ("F", pred_id, operands)
# operands: tuple[Rank, ...] sorted ascending (no roles)
#        or tuple[tuple[RoleId, Rank], ...] sorted by rank (with roles)
Word: TypeAlias = tuple[Token, ...]
RolesMap: TypeAlias = Mapping[EdgeId, Mapping[NodeId, RoleId]]

def encode_fact_word(H: SparseHypergraph, rank: Sequence[int], roles: RolesMap | None = None) -> Word
def decode_fact_word(tokens: Sequence[Token], *, n_types: int, n_preds: int) -> tuple[SparseHypergraph, RolesMap | None]
    # TOTAL: never raises on a sequence of well-formed tokens; see DESIGN.md G2 for the semantics
def fact_key(word: Word) -> Word            # hashable canonical key = the word itself (documented identity)
def word_length(H: SparseHypergraph) -> int # n + m
def token_vocabulary(n: int, k: int, n_preds: int, n_types: int) -> Iterator[Token]  # F tokens over ranks < n, arity 2..k; T tokens
```
Round-trip: `decode(encode(H, rank))` is isomorphic to `H` (and equal up to the
rank relabelling). Property tests: iso-invariance under random permutation
(word equality); completeness vs `pynauty_levi` fingerprint partition on random
labelled hypergraphs (0 false merges/splits); totality on random token
sequences; position-insensitivity of the decoded class (shuffled F tokens
decode to an isomorphic KB).

### 2.2 Canonical order (`iso_backends/canonical_order.py`, W1-A)

```python
def canonical_ranks(H: SparseHypergraph) -> tuple[int, ...]     # rank[v] in 0..n-1, iso-invariant (pynauty.canon_label on to_levi(H))
def nauty_certificate_bytes(H: SparseHypergraph) -> bytes       # color_signature ++ certificate (the existing nauty_levi_edit form)
def nauty_certificate_rows(H: SparseHypergraph) -> tuple[tuple[int, ...], ...]  # canonical Levi adjacency rows as symbols
```
Reference: `scripts/diagnostics/d_art3_probes_2026-09-03/f4_topology/f4_encodings.py`
(`canonical_ranks`, `word_B`, `word_C`, `_to_pynauty`) and
`f4_local_key.py` (arms D, D1). pynauty is imported inside function bodies.

### 2.3 Distances (W1-A)

`FactRankLevenshtein(roles: bool = False)` subclasses `HypergraphDistance`
(`metric_space/base.py`), registered as `"fact_rank"`; `pairwise(H1, H2)`
computes ranks + words + `rapidfuzz.distance.Levenshtein.distance` on tuples.
Module-level `word_distance(w1: Word, w2: Word) -> int`. Roles cannot travel
through `pairwise(H1, H2)`; the matrix builder (W2-B) computes words once per
member with roles from the record and calls `word_distance`. Ablation arms
registered as `"fact_local_colour"`, `"fact_local_key"`, `"fact_degree_key"`.

### 2.4 Knowledge-base records (`datasets/kb/base.py`, W1-B)

```python
@dataclass(frozen=True)
class KBRecord:
    kb_id: str
    n: int
    types: tuple[int, ...]                                   # per constant, in [0, n_types)
    facts: tuple[tuple[int, tuple[int, ...]], ...]           # (pred_id, sorted distinct constant ids), arity >= 2, no duplicates
    roles: tuple[tuple[int, ...], ...] | None = None         # per fact, role id per operand, aligned with the operand tuple
    constant_ids: tuple[str, ...] | None = None              # external identities — EVALUATION ONLY
    label: str | None = None                                 # class label (RQ5)
    meta: Mapping[str, Any] = field(default_factory=dict)    # e.g. {"class": "...", "quarter": "2015Q3", "regime": ...}
    def to_hypergraph(self) -> SparseHypergraph: ...
    def roles_map(self) -> RolesMap | None: ...              # {edge_id: {node_id: role_id}} in to_hypergraph()'s edge order

@dataclass(frozen=True)
class KBCollection:
    name: str
    records: tuple[KBRecord, ...]
    type_names: tuple[str, ...]
    pred_names: tuple[str, ...]
    role_names: tuple[str, ...]
    k_max: int
    meta: Mapping[str, Any]
    # io: write_jsonl(path) / read_jsonl(path); vocab.json beside the JSONL
```
Loaders: `wd50k.py` (`load_wd50k(subset ∈ {"66","100","all"}, envelope=True, roles=True, types_tsv=...)`,
reproducing `../supplementary_data.md` S1: statements → one KB per subject entity, hyperedge = {subject, object, qualifier values}
labelled by main relation, qualifier relations dropped, entities with < 3 statements dropped, envelope filter, P31 class label),
`ndc_quarterly.py` (`load_ndc(nodes ∈ {"classes","substances"}, window="quarter")` reproducing S2: 1,432 encodable class-quarters,
consecutive pairs with `Δ` from identities and the constant-preserving flag, runs per class; class type from the name suffix).
Reference implementations: `scripts/diagnostics/d_art3_probes_2026-09-03/{hyperrel/probe_hyperrel.py, hyperrel/wd50k66_types.py,
arb_temporal/arb_temporal_lib.py, f4_topology/f4_corpora.py}`. Acceptance = the census numbers of `supplementary_data.md`.
Generators (`ladders.py`, `corruptions.py`, `envelope_sweep.py`) implement DESIGN.md §RQ1 M1/M2, §RQ3 Corpus A, §RQ4 corruptions,
§RQ7 grid exactly, seeded, with the rejection rules stated there; each returns records with `constant_ids` carried for evaluation.

### 2.5 Language layer (`language/`, W2-A)

```python
def reach(K: SparseHypergraph, K2: SparseHypergraph, r_max: int = 2, *, key=fact_key_of) -> int | None   # exact reach_F ≤ r_max else None
def alignments(K, K2, r_max) -> list[Alignment]     # (A, B, bijection node->node) found by delete-and-match
def string_ball(word: Word, radius: int, vocab: Iterable[Token]) -> Iterator[Word]  # string-level indel(+subst flag) ball (small radii; decodability)
def alignment_path(w1: Word, w2: Word) -> list[Word] # every interior word of one optimal Levenshtein alignment
def coverage_consensus(members: Sequence[SparseHypergraph], r: int) -> ConsensusResult  # DESIGN.md §RQ3 objective, alignment-transfer candidates
def majority_merge(members_with_ids: Sequence[KBRecord]) -> KBRecord
```
`ConsensusResult` carries the winning KB (as a KBRecord in the anchor member's constant space, with that member's identities),
coverage, Σ reach, the number of candidates and ties, and per-candidate scores for the rows.

### 2.6 Toolkit (`metric_space/toolkit/`, W2-B)

`build_matrix(collection, arm, *, cache_dir, n_jobs) -> np.ndarray` (words-first for `fact_rank*`; `HypergraphDistance.pairwise`
for the rest; `.npy` + `manifest.json` cache keyed by collection name, member order hash, arm name and parameters);
`medoid(D) -> (index, cost, LB, ratio)`; `pam(D, k, seed)`, `average_linkage(D) -> (Z, cophenetic)`; `knn_score(D, k)`,
`lof_score(D, k)`; `metric_mds(D, dim, seed) -> (X, stress1)`; `non_euclidean_mass(D)`, `hubness(D, k)`. Statistics
(`experiments/tkde/stats.py`): reuse `experiments/analysis/stats.py` (`bca_bootstrap_ci`, `holm_bonferroni`) and add two-sided
Wilcoxon with rank-biserial, Wilson CI, Cliff's δ, cluster bootstrap, Spearman with clustered bootstrap, and
`paired_family(ours, others) -> table`. `experiments/tkde/io.py`: writers for `rows_*.csv`, `config.json`, `manifest.json`
(git SHA, host, `lscpu` model, versions, SLURM ids), `summary.json`, `stats.json`, `tables.md` (DESIGN.md G6).

### 2.7 Runners (W3-*)

`python -m experiments.tkde.rqN --config experiments/tkde/configs/rqN.yaml --shard i/N --out <RESULTS_ROOT>/RQN/<experiment>`;
idempotent per unit (skip units whose row file exists and validates); `--smoke` runs a tiny configuration locally in < 5 min;
`analyze_rqN.py` aggregates rows → `summary.json`, `stats.json`, `tables.md`. Every runner records the manifest of G6.

## 3. Waves and ownership

Base commit per wave is recorded in the wave summary. Concurrency ≤ 3.

| wave | agent | model / effort | mission | owns (create/edit) |
|---|---|---|---|---|
| W1 | `fact-alphabet` | opus, xhigh | the adopted encoder, total decoder, canonical order, distances, `LabelVocabulary.fit`, tests | `src/isalhg/core/fact_word.py`, `src/isalhg/iso_backends/canonical_order.py`, `src/isalhg/metric_space/distances/fact_*.py`, `src/isalhg/datasets/schemas.py`, `tests/unit/core/test_fact_word.py`, `tests/unit/iso_backends/test_canonical_order.py`, `tests/unit/metric_space/test_fact_levenshtein.py`, `tests/property/test_fact_word_properties.py` |
| W1 | `kb-corpora` | opus, high | KB records, the two real loaders (+ controls), ladders / corruptions / envelope generators, freeze script, `experiments/tkde/corpora.py` | `src/isalhg/datasets/kb/**`, `src/isalhg/datasets/registry.py` (registration lines only), `experiments/tkde/__init__.py`, `experiments/tkde/corpora.py`, `scripts/tkde/freeze_corpora.py`, `tests/unit/datasets/test_kb_*.py` |
| W1 | `picasso-env` | opus, high | Picasso: fresh repo dir, env, portable-or-pinned C++ build verified on an `sd` compute node, data staged, `common.sh`, sync/harvest scripts, `PICASSO.md` | `slurm/tkde/common.sh`, `slurm/tkde/README.md`, `scripts/tkde/sync_to_picasso.sh`, `scripts/tkde/harvest_from_picasso.sh`, `scripts/tkde/picasso_env_setup.sh`, `docs/article/D_ART3/experiments/PICASSO.md`; remote: `~/fscratch/repos/IsalHG-tkde`, env `isalhg-tkde`, `~/fscratch/datasets/isalhg_tkde`, `~/fscratch/results/IEEETKDE` |
| W2 | `language-layer` | opus, xhigh | reach, ball, alignment interiors, alignment-transfer coverage consensus, majority merge; tests incl. source recovery on synthetic insertion ladders | `src/isalhg/language/**`, `tests/unit/language/**` |
| W2 | `toolkit-stats` | opus, high | matrix builder + cache, medoid/PAM/agglo/kNN/LOF/MDS/geometry wrappers, stats harness, io writers | `src/isalhg/metric_space/toolkit/**`, `experiments/tkde/{config,io,stats}.py`, `tests/unit/metric_space/test_toolkit_*.py`, `tests/experiments_tkde/test_stats.py` |
| W2 | `competitors-kb` | opus, high | audit competitors for labelled KBs (edge labels, roles ignored), `nauty_cert_rows`, bipartite both readings, generation package | `src/isalhg/metric_space/representations/**`, `src/isalhg/metric_space/distances/hged.py`, `src/isalhg/generation/**`, their tests |
| W3 | `rq-1-2-7` | opus, high | RQ1, RQ2, RQ7 runners + analyzers + SLURM; smoke locally; submit; monitor; harvest | `experiments/tkde/{rq1,rq2,rq7,analyze_rq1,analyze_rq2,analyze_rq7}.py`, `experiments/tkde/configs/rq{1,2,7}.yaml`, `slurm/tkde/rq{1,2,7}_*.sh` |
| W3 | `rq-3-6` | opus, xhigh | RQ3, RQ6 runners + analyzers + SLURM | `experiments/tkde/{rq3,rq6,analyze_rq3,analyze_rq6}.py`, configs, `slurm/tkde/rq{3,6}_*.sh` |
| W3 | `rq-4-5` | opus, high | RQ4, RQ5 runners + analyzers + SLURM | `experiments/tkde/{rq4,rq5,analyze_rq4,analyze_rq5}.py`, configs, `slurm/tkde/rq{4,5}_*.sh` |

Merge order within a wave: contracts first (W1: `fact-alphabet` → `kb-corpora` → `picasso-env`; W2: `toolkit-stats` →
`language-layer` → `competitors-kb`), fast tests after each merge, full suite + lint + mypy after the last.

## 4. Picasso layout

- Repo: `/mnt/home/users/tic_163_uma/mpascual/fscratch/repos/IsalHG-tkde` (fresh; the existing `IsalHG` checkout is left
  untouched). Deployed by `rsync` from the local main checkout after every merged wave (`scripts/tkde/sync_to_picasso.sh`),
  never by git.
- Env: `isalhg-tkde` (Python 3.11; `pip install -e ".[dev]"` inside the Picasso repo; `pynauty`, `rapidfuzz`, `scikit-learn`,
  `scikit-learn-extra`, `netlsd`, `scipy`, `pandas`, `pyarrow`). C++ extension built on the login node with the project's
  default flags (`-march=native`) → **every job pins `--constraint=sd`**; the build was verified by smoke job `2210893` on
  `sd030` importing the extension module `isalhg.core._core` (not `_native`) and canonicalizing a fixture with
  `backend="cpp"`. Conda envs live under `~/fscratch/conda_envs/` on Picasso (not `~/.conda/envs`); `common.sh` exports the
  absolute interpreter as `PY`. Single (non-array) jobs use `%j` in log names — `%a` expands to a sentinel there. Fallback
  documented in `PICASSO.md`: rebuild with `-march=haswell` to run on `cpu`.
- Data: `~/fscratch/datasets/isalhg_tkde/{raw/, corpora/}` — raw files (WD50K subsets + P31 types TSV, ARB temporal
  NDC-classes and NDC-substances) and the frozen JSONL corpora (the runners read only `corpora/`).
- Results: `/mnt/home/users/tic_163_uma/mpascual/results/IEEETKDE/<RQ>/...` on the permanent HOME filesystem
  (mirror of the local root; HOME quota read 2026-09-05: 24 GB / 280 GB, 3.3k / 35k files soft, 150k hard); logs
  `~/execs/tkde/logs/` (also HOME). FSCRATCH holds only the re-creatable inputs (repo, env, raw data, corpora); it is
  purged after two months of inactivity and was over its file soft quota (251.7k / 250k, hard 400k) at wave 1.
- Jobs: `--account=tic_163_uma --constraint=sd`, arrays throttled, units bundled to ≥ 2 h with a start-cutoff (first unit
  exempt), `$LOCALSCRATCH` staging with whole-tree copy-back and `EXIT`/`TERM` traps, `--output/--error` explicit,
  `OMP_NUM_THREADS` from `SLURM_CPUS_PER_TASK` (1 for timing arms). `sbatch --test-only` before every submission; one real
  task before an array.
- Harvest: `scripts/tkde/harvest_from_picasso.sh` = `rsync -a picasso:~/fscratch/results/IEEETKDE/ $ISALHG_RESULTS_ROOT/`.

## 5. Results layout (local drive, the deliverable)

```
/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE/
  README.md               manifest: what each folder holds, git SHAs, job ids, harvest dates
  corpora/<collection>/   frozen JSONL + vocab.json + census.json
  matrices/<collection>/<arm>.npy + manifest.json
  RQ1_addressing/ RQ2_wellposedness/ RQ3_representative/ RQ4_screen/ RQ5_patterns/ RQ6_generation/ RQ7_envelope/
      <experiment>/ rows_*.csv config.json manifest.json summary.json stats.json tables.md
  supplementary/          pointers to the arms/tables designated supplementary by DECISIONS.md
  article/                pointers to the tables/figure inputs designated main-text by DECISIONS.md
  DECISIONS.md            the A → A′ decisions with the numbers that drove them
```
