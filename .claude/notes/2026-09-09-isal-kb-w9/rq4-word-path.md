# RQ4 — the word fast path, budgeted (wave 9)

Branch `feature/isal-kb-word`, worktree `.claude/worktrees/agent-af88f26a1ae7b1661`,
base `21f64c5` (worktree HEAD at start: `80472bb`, three docs-only commits ahead).
Env: `isalhg-rq4fix`, cloned from `isalhg`, editable-installed **in the
worktree**; `isalhg.__file__` resolves to
`.../agent-af88f26a1ae7b1661/src/isalhg/__init__.py`.

## 1. What changed, per file

### `experiments/tkde/rq4.py`

* **`WORD_ARM = "fact_rank"` → `WORD_ARMS`.** The set is
  `("fact_rank", "isal_ow_struct", "wstar_rank", "wstar_orbit")` — every arm
  whose distance is a token-level Levenshtein over a per-member word, so every
  arm for which `pairwise` re-derives the canonical labelling on *both* sides
  of *every* call. `ENGINE_ARMS` maps `wstar_rank`/`wstar_orbit` to
  `budget.engine_word`'s engine selector.
* **`_plain_word(arm, H)`** — the word of a non-engine word arm: `fact_word`
  for `fact_rank`, the distance object's own `fingerprint` otherwise (which is
  exactly what `IsalOrderedLevenshtein.pairwise` encodes).
* **`member_word(arm, H, *, augment, budget_s)`** — one member's word,
  computed **in a forked child under the per-member budget**: through
  `budget.engine_word` for the engine arms (which already carries the
  fork-health canary and the Python-engine memory guard), through
  `budget.guarded_budget_call` otherwise, with `cpp_engine` read off
  `budget.CPP_ENGINE_ARMS`. Returns `None` when the child was censored or
  raised. `k` is the member's own `required_k(H)` — neither Isal engine word
  changes with `k` above the widest edge, so this is the same value the pair
  maximum `pairwise` resolves would produce, and it is what
  `IsalEngineLevenshtein.fingerprint` itself uses.
* **`member_words` / `unit_words`** — one word per item, memoised **by member
  id, per (arm, sub-collection)** in the runner's `collection_cache`. The
  pristine members are the same hypergraphs in every unit of a sub-collection,
  so their forks are paid once per process; only the corrupted members are
  re-encoded per unit, and they are the only place an anomaly can be lost.
* **`word_rows(words, positions, *, n_jobs)`** — one shared private alphabet
  (`budget.encode_symbols`) then a single `rapidfuzz.process.cdist` call, the
  encode-once pattern `IsalEngineLevenshtein.matrix` uses. Levenshtein is
  invariant under bijective symbol relabelling, so a corpus-wide alphabet
  returns exactly the per-pair values a per-call alphabet returns.
* **`anomaly_rows(items, words, positions, arms, *, n_jobs)`** — the second
  argument changed from `Sequence | None` (fact words only) to
  `Mapping[str, Sequence[tuple]] | None` (arm → words). Every arm present in
  the mapping is served from `word_rows`; the rest keep the existing
  `fork`-pool `pairwise` path unchanged (point 4 of the brief — the vector and
  spectral competitors are cheap and terminate).
* **`Census`** gained `n_censored_word_anomaly`, `n_censored_word_clean`,
  `word_censored_arms` (defaults `0/0/""`, so every existing constructor and
  reader is unaffected). **`fold_word_census`** folds the members lost to the
  word budget into the existing totals *and* reports them separately, so a
  reader can tell an upstream (matrices-job) censoring from one this run made.
  `ROWS_AUC_COLUMNS` gained the three columns; `_auc_row` emits them.
* **`_restrict(records, modified, realised, keep)`** and
  **`_restrict_words(columns, keep)`** — the restriction pass, extracted
  because it now runs twice (matrix census, then word census). The word
  variant *raises* on a surviving hole rather than filtering it: a filtered
  hole would shorten one column and silently misalign it with the
  hypergraphs.
* **`run_unit` reordered.** Matrices are loaded and the census taken **before**
  any word is computed, so the members the matrices job already censored are
  never canonicalised here. Then the words; then, if any member lost its word,
  a second restriction that drops it **for every arm** — the same common-member
  rule `common_positions` enforces one level up, because a cross-arm AUC on
  different member sets is not answering the same question for each arm. When
  every anomaly is lost, `realised` is empty and the existing "every corrupted
  member was censored; no AUC" path fires unchanged.
* **`scored_arms`** — an arm with no cached matrix is censored whatever its
  rows say, so its anomaly rows are no longer computed. Before this change the
  runner computed `2 A N` `wstar_orbit` canonicalizations for an arm whose row
  was then thrown away.
* **`member_budget_s`** threaded through `run_unit`, `refill_unit` and `main`
  (config key `member_budget_s`, default `DEFAULT_MEMBER_BUDGET_S = 60.0`), and
  recorded in the shard `config.json`.

`budget.py` was **not** modified — `engine_word`, `guarded_budget_call`,
`encode_symbols` and `pointer_symbols` already had the shapes this needed. No
`spawn` change was made anywhere.

### `experiments/tkde/configs/rq4.yaml`

`member_budget_s: 60.0` plus the comment explaining what it budgets and why it
matches the matrices job's `fingerprint_budget_s`. Nothing else touched.

### `tests/experiments_tkde/test_rq4_word_path.py` (new)

16 tests, `pytestmark = pytest.mark.unit`.

* `TestWordPathEqualsPairwise` — for `fact_rank`, `isal_ow_struct` and
  `wstar_orbit`, the `word_rows` matrix equals the matrix `pairwise` produces,
  entry by entry, on six structurally distinct connected records (path, star,
  arity-3, alternating path, single arity-4 fact, two arity-3 facts). The
  reference is computed **inside a forked child**, because a `pairwise` call on
  an engine arm canonicalizes in-process and would poison every later budgeted
  fork (`budget.cpp_fork_is_healthy`); the engine case skips if the process is
  already poisoned. The test asserts `min(off-diagonal) > 0` first, so it
  cannot pass on a degenerate all-zero corpus. Plus zero-diagonal and
  `n_items ∈ {1, 2}` edge cases.
* `TestUnitWords` — the memo encodes each pristine member exactly once across
  two units; a member whose word does not finish comes back as a hole with its
  arm named.
* `TestFoldWordCensus` — anomaly/clean split, rate denominators, and that the
  lost positions are read against `census.kept` rather than the parent order.
* `TestAnomalyCensoring` — end-to-end `run_unit` on a synthetic 40-member
  collection with a stubbed word oracle: no censoring scores all 40; one
  censored anomaly is dropped (`n_inliers + n_anomalies == 39`,
  `n_censored_word_anomaly == 1`, AUC finite); every censored anomaly gives
  `censored == 1` and `auc == nan`; an arm with no cached matrix costs no word
  computations at all.

## 2. Verification

### 2.1 Baseline, measured here (not assumed)

```
$ ~/.conda/envs/isalhg-rq4fix/bin/python -m pytest tests/experiments_tkde/ -q -p no:randomly
================== 6 failed, 327 passed in 413.20s (0:06:53) ===================
```

The six are the pre-existing `deploy_stamps` / `rq6` failures:
`test_rq36_smoke.py::TestUnitEnumeration::test_rq6_units_are_unique`,
`TestModelIsNotSharedAcrossUnits::{test_each_call_returns_a_fresh_model,
test_the_fresh_model_samples_identically,
test_a_used_model_is_not_reachable_from_the_context}`,
`TestDeployStamps::test_the_stamps_name_the_imported_package`,
`test_rq45_smoke.py::TestSmokeIsolation::test_deploy_stamps_name_both_trees`.

### 2.2 After

```
$ ~/.conda/envs/isalhg-rq4fix/bin/python -m pytest tests/experiments_tkde/ -q -p no:randomly
================== 6 failed, 343 passed in 413.86s (0:06:53) ===================
```

Same six names, `327 + 16 = 343` passing. **No new failure.**

New file alone:

```
$ ~/.conda/envs/isalhg-rq4fix/bin/python -m pytest tests/experiments_tkde/test_rq4_word_path.py -q -p no:randomly
16 passed in 0.84s
```

Lint and types on the files touched:

```
$ ~/.conda/envs/isalhg-rq4fix/bin/python -m ruff check experiments/tkde/rq4.py tests/experiments_tkde/test_rq4_word_path.py
All checks passed!
$ ~/.conda/envs/isalhg-rq4fix/bin/python -m mypy experiments/tkde/rq4.py   # rq4.py lines only
experiments/tkde/rq4.py:1372: error: Returning Any from function declared to return "str | None"
experiments/tkde/rq4.py:1471: error: Argument 1 to "int" has incompatible type "Any | str | None"
```

Both mypy errors are pre-existing (`_shard_manifest_stamp`'s `json.loads`, and
`int(config.get("n_jobs") or ...)`); the four my first draft introduced were
fixed. `experiments/` is not in the project's mypy gate (`mypy src/isalhg/`),
but the file is clean apart from those two.

### 2.3 Equality on real data — the strongest check

The local `--smoke` run was executed on both the base `rq4.py` (restored
non-destructively into a scratch copy of the `experiments` package, via
`git show 21f64c5:experiments/tkde/rq4.py`) and the new one, against the real
1,381-member `ndc_classes` corpus, four arms, two corruptions, two seeds:

```
rows before/final: 32 32 same keys: True
differing rows: 0
```

Every `auc`, `n_inliers`, `n_anomalies` and `censored` value is byte-identical.
`fact_rank` moved from `word_distance` (per-call alphabet, Python loop) to the
shared-alphabet `cdist` pass, and `isal_ow_struct` moved off `pairwise`
entirely; neither changed a number.

### 2.4 The local smoke — before and after

```
$ ISALHG_RESULTS_ROOT=/media/.../results/IEEETKDE \
  ~/.conda/envs/isalhg-rq4fix/bin/python -m experiments.tkde.rq4 \
      --config experiments/tkde/configs/rq4.yaml --smoke --out <scratch>
```

| | unit 0 | unit 1 | unit 2 | unit 3 | Σ units |
|---|---|---|---|---|---|
| base `21f64c5` (14:03, contended) | 14.1 s | 11.0 s | 13.3 s | 10.8 s | **49.2 s** |
| this branch (14:11, contended, final code) | 13.8 s | 4.0 s | 5.1 s | 3.8 s | **26.7 s** |
| this branch (13:57, uncontended) | 8.6 s | 3.6 s | 4.4 s | 3.5 s | **20.1 s** |

Whole-process wall for the uncontended run, matrix builds included: 13:57:21 →
13:57:42, **21 s**. The base and the 14:11 runs shared the machine with the
§2.5 probe, so the like-for-like pair is 49.2 s → 26.7 s. All three are far
inside the 30-minute wall, which is why this is *not* the interesting
comparison: `--smoke` does not score `wstar_orbit` at all (§3.1). §2.5 is.

Rows written: 4 × `rows_auc__*.csv` (8 data rows each: 4 arms × {knn, lof}) and
4 × `rows_anomalies__*.csv` (69 data rows each). Population 1,312 inliers + 69
anomalies = 1,381, no censoring (the smoke builds its own unscreened matrices).

### 2.5 The defect itself, on the real corpus

The `--smoke` flag does **not** reach the defect (see §3.1), so it was measured
directly: real `ndc_classes` members, a real corruption, the real
`wstar_orbit` arm, sub-collection truncated to `N` so the quadratic old path
stays affordable. The inlier–inlier block is a synthetic matrix — only the
anomaly rows are timed, and those are computed for real.

**`N = 60`, 3 anomalies, uncontended** — the whole unit under the new code took
7.6 s; the two paths for `wstar_orbit`'s rows alone:

```
wstar_orbit      N=60 anomalies=3: pairwise    20.87 s -> words     7.13 s (2.9x)
isal_ow_struct   N=60 anomalies=3: pairwise     0.02 s -> words     0.24 s (0.1x)
fact_rank        N=60 anomalies=3: pairwise     0.01 s -> words     0.21 s (0.0x)
```

**`N = 200`, 10 anomalies** — the decisive one. The new code ran the whole unit
in **140.3 s**, including one real member whose word overran its 60 s budget and
was dropped and counted:

```
WARNING unit 0 (ndc_classes__spurious_fact_b1__seed40000): 1 member(s) lost to
the 60 s word budget of wstar_orbit (0 selected for corruption, 1 clean);
scoring the remaining 199
AFTER  N=200 anomalies=10: 140.3 s, 4 auc rows
```

The old `pairwise` path for the same arm, same members, same anomalies, was
given a **1,800 s cap and hit it** (`EXIT=124` from `timeout 1800`) — it never
produced a number. That is the reported failure reproduced at 15 % of the
production sub-collection and 15 % of its anomalies: `ndc_classes` is 1,311
members and 66 anomalies, roughly **43× more `pairwise` work** than the run
that already exceeded half an hour.

The asymmetry is structural, not a constant factor. The old path costs
`2 A N` canonicalizations and is unbudgeted, so a single member in the 60 s
tail is paid `2 A` times over; the new path costs `N + A`, each one bounded,
and the `N` part is memoised across the sub-collection's units.

## 3. What in the brief is wrong

### 3.1 The failing job is not what `--smoke` runs

The brief's acceptance command,
`python -m experiments.tkde.rq4 --config .../rq4.yaml --smoke`, **cannot
reproduce the defect**. `main()` overrides the arm list under `--smoke`:

```python
arms = (
    ("fact_rank", "isal_ow_struct", "nauty_cert", "size_l1")
    if args.smoke
    else tuple(str(a) for a in config.get("arms", DEFAULT_ARMS))
)
```

`wstar_orbit` is not in that set, so the `--smoke` run never touches the arm
that hung. The cluster "smoke" is a different thing: `slurm/tkde/rq4_worker.sh`
runs the **real** config with `--tag _smoke --unit ${TKDE_SMOKE_UNIT}` — 11
arms, `wstar_orbit` among them — which is where the brief's "11 arms" comes
from. I ran the brief's command anyway (§2.4, and it is a real regression
guard: it is what produced the byte-identical comparison of §2.3), and measured
the defect separately on the real corpus (§2.5).

### 3.2 There is no local `ndc_classes/wstar_orbit` matrix

`/media/.../results/IEEETKDE/matrices/ndc_classes/` holds
`bipartite_ged_{assign,path}`, `degree_seq_l1`, `fact_rank`, `hpd_jsd`,
`nauty_cert`, `nauty_cert_rows`, `netlsd`, `size_l1`, `wl_l1` — and no
`wstar_orbit`. A local run of the real config would therefore censor
`wstar_orbit` for want of a matrix. That is also how I found the *second*
defect: `anomaly_rows` was called with the full `arms` list, so before this
change the runner paid the full `2 A N` canonicalizations for an arm whose row
was then discarded by `if arm not in loaded`. Fixed (`scored_arms`).

### 3.3 Budgeting every word arm is not free at small `N`

The brief asks for every word arm's representation to go through a forked child
under the per-member budget. That is right for the engine arms and right for
*anomalies* of every arm, but the fork is not free where the representation is
microseconds. Measured at `N = 60`, 3 anomalies:

| arm | `pairwise` (old) | words + fork (new) |
|---|---|---|
| `wstar_orbit` | 20.87 s | 7.13 s |
| `isal_ow_struct` | 0.02 s | 0.24 s |
| `fact_rank` | 0.01 s | 0.21 s |

(Reproduction:
`scratchpad/probe_before_after.py <N> <dir>`, kept out of the repo; it builds a
synthetic inlier–inlier block so that only the anomaly rows are timed.)

The fork costs ≈3.5 ms per member. It pays for itself as `A·N` grows — the old
path is `O(A·N)` representations, the new one `O(N)` — and at the production
`ndc_classes` scale (`N ≈ 1,311`, `A = 66`) `fact_rank`'s old path is ≈4.8 s
*per unit* against ≈0.23 s per unit plus a one-off ≈4.6 s memo fill amortised
over the sub-collection's 189 units. I kept the uniform budget (it is what
makes the L15 guarantee uniform too) and am flagging the small-`N` cost rather
than hiding it.

### 3.4 Unverified from the brief

"p99 canonicalisation is 43 s and 70 of 1,381 members do not finish within 60 s"
could not be checked here: there is no local `wstar_orbit` censoring sidecar for
`ndc_classes`. What I *did* observe independently is consistent with it — at
`N = 200` exactly one real `ndc_classes` member's `wstar_orbit` word overran the
60 s budget, and the new code dropped it and counted it:

```
WARNING unit 0 (ndc_classes__spurious_fact_b1__seed40000): 1 member(s) lost to
the 60 s word budget of wstar_orbit (0 selected for corruption, 1 clean);
scoring the remaining 199
```

## 4. Residual risk

1. **Word computation is sequential.** `unit_words` forks one child at a time.
   It cannot use a `multiprocessing.Pool`: pool workers are daemonic and a
   daemonic process may not fork, which is the failure that killed matrices job
   2264827. `n_jobs` still parallelises the `cdist` pass (`workers=n_jobs`) and
   the surviving `pairwise` arms. If the cluster wall is still tight, the fix
   is a non-daemonic worker pool in `budget.py` — a change to a module other
   runners depend on, deliberately not made here.
2. **A clean member can now be dropped by the word budget.** It is the same
   common-member rule the matrices census already applies, and it is counted in
   `n_censored_word_clean`, but it means one slow arm can shrink the scored
   population for every arm of that unit. Observed once at `N = 200` (§3.4).
   L15's third clause therefore now has a second source, which is why the two
   are reported in separate columns.
3. **The word memo is per process, keyed by member id and sub-collection.** A
   shard that runs units of many sub-collections holds one word list per
   `(arm, sub-collection)` in memory. For `wd50k66_Q5` (1,830 members) that is
   1,830 token tuples per word arm — small next to the cached matrices already
   held, but it is new resident memory and no RQ4 MaxRSS was ever measured
   (`rq4_worker.sh` says so itself).
4. **`augment` is a corpus-level flag** computed as
   `any(H.n_vertex_labels > 1)` over the unit population, mirroring
   `IsalEngineLevenshtein.matrix`. It is constant across a knowledge-base
   collection because `n_vertex_labels` is the declared type alphabet, not the
   used one — but if a future corruption ever changed the declared alphabet,
   the memoised pristine words would have been computed under the other flag.
   The equality test would not catch that; a assertion could be added if any
   corruption starts varying `n_types`.
5. **A poisoned runner now fails loudly instead of censoring falsely.**
   `member_word` reaches `guarded_budget_call`, which raises `TkdeBudgetError`
   if the C++ canonicalizer has already run in this process — a censoring there
   would be a fiction. The production path never canonicalizes in-process
   (`ensure_smoke_matrices` runs only under `--smoke`, and none of the four
   smoke arms poisons: `budget.py` records that the ordered-walk emitter does
   not, unlike `wstar_rank`/`wstar_orbit`). If a future `--smoke` arm list ever
   gains an engine arm, `ensure_smoke_matrices`' in-process `build_matrix`
   would poison the runner and every subsequent unit would raise.
6. **`refill_unit` merges old rows with new ones.** Rows written before this
   change have no `n_censored_word_*` columns; `write_rows` fills them with the
   empty string. A refilled table is therefore mixed, which is already the
   documented condition of a refill (the manifest records both provenances).
