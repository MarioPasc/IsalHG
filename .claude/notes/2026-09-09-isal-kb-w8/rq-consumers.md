# RQ consumers of the two censoring decisions (D-KBf1, D-KBf2)

Branch `feature/isal-kb-word`, base `d53b686`, worktree
`.claude/worktrees/agent-a2d50b3447d1b94a5`.
Env: `isalhg-kbf-consumers` (cloned, editable-installed into this worktree;
`isalhg.__file__` verified to resolve inside the worktree).

Five commits:

| sha | subject |
|---|---|
| `f42fa5b` | `feat(tkde): sidecar-aware matrix reader for censored arms` |
| `4c3eaeb` | `chore(tkde): apply the D-ART5 arm set to RQ2-RQ7 configs` |
| `aab60aa` | `feat(tkde/rq3): censor the medoid at the collection (D-KBf1)` |
| `da7ec01` | `test(tkde/rq3): run the RQ3 smoke in a child, as a shard does` |
| `68ec7c1` | `feat(tkde): RQ2/RQ4/RQ5 consume a censored arm's short matrix (D-KBf2)` |

---

## 1. What changed, per file

### `experiments/tkde/matrices.py`

- **`MatrixCensoringError(TkdeError)`** — new. Deliberately *not* a subclass of
  `MatrixCacheMissingError`: `cached_arms` swallows that one, and a sidecar that
  does not partition the frozen order is a corrupted artefact, not a unit that
  has yet to run.
- **`load_cached_matrix_censored(root, collection, arm, member_ids)`** →
  `(matrix, kept_ids, censored_ids)`. Reads `read_censoring` first (its first
  consumer outside this module). No sidecar ⇒ delegates to `load_cached_matrix`
  and returns the full order with an empty censored list, so an unscreened arm
  behaves exactly as before. With a sidecar, validates the manifest against
  `kept_ids` and asserts a *partition*: both `set(kept) | set(censored) ==
  set(frozen)` **and** `len(kept) + len(censored) == len(frozen)` — set equality
  alone would admit an id repeated on both sides, which would index two matrix
  rows under one member.
- **`load_arm_matrices(root, collection, arms, member_ids, *, cache=None)`** →
  `{arm: (matrix, {member_id: row})}`, with the per-process memo the consumers
  need (wd50k66 is 64 MB per arm). An arm with no matrix is logged and omitted.
- **`common_member_ids(member_ids, loaded)`** — the intersection of the loaded
  arms' survivor sets, in input order. With no arms loaded it returns its input
  (nothing to intersect over).
- **`load_cached_matrix` is untouched**, as the brief required.

Both shared helpers live here rather than being written three times: the module
docstring already declares itself "the contract RQ2 / RQ4 / RQ5 all read
through".

### `experiments/tkde/rq3.py` (D-KBf1)

- `VARIANT_COLUMNS` and `NATURAL_COLUMNS` gain **`n_censored_members`**.
  `CERTIFICATE_COLUMNS` deliberately does **not**: a censored collection emits no
  certificate row at all.
- `BUILD_MARGIN_S = 60.0` — slack over `N` per-member budgets for the pairwise
  pass the screen does not bound.
- **`censored_members(arm, members_H, member_ids, budget_s)`** — wraps
  `arm_fingerprint_screen`, so the screen is byte-for-byte the one `matrices.py`
  runs and the census is the one the reader met in RQ1.
- **`medoid_matrix(members_H, member_ids, arm, budget_s)`** — an arm in
  `CPP_ENGINE_ARMS` builds inside `run_guarded(..., cpp_engine=True)` (a child
  that then dies); every other arm builds in-process. The parent is therefore
  never poisoned, which is what keeps the consensus guard's forks trustworthy.
  `cpp_engine` is passed explicitly, as `budget.py` requires.
- **`survivor_medoid_row(...)`** — the D-KBf1 sensitivity supplement.
  `method="medoid_survivors"`, `LB` and `ratio` blank (not certified),
  `n_censored_members` set. Returns `None` on <2 survivors or a failed build.
  `medoid_cost` is kept: it is the argmin objective over the survivors and
  certifies nothing on its own.
- `evaluate_collection` gains `fingerprint_budget_s: float | None = None`.
  Screening applies when it is set **and** `arm in BUDGETED_MATRIX_ARMS`, mirroring
  `matrices.py` exactly. Any censored member ⇒ `censored=1` row with
  `fact_dist`/`medoid_cost`/`LB`/`ratio` blank, plus the supplement row, then
  `continue` — no medoid over survivors in the main path.
- `n_censored_members` is `0` on a screened-and-clean arm and `""` on an
  unscreened one, so "screened, nothing censored" is distinguishable from "not
  screened". It is set **only on medoid rows** — not in `shared` — so the
  consensus and `majority_merge` rows keep their own `censored` untouched and
  render the column blank. Census granularity is per (collection, method), as
  D-KBf1 requires.
- The screen sits **outside** the `try` that guards a dead arm: a refused fork is
  a dead *process*, and swallowing `TkdeBudgetError` into `censored=1` would mark
  every collection censored on a fiction.
- `_apply_smoke` forwards `fingerprint_budget_s` (it whitelists keys; without
  this the smoke would have screened at 60 s/member).

### `experiments/tkde/rq4.py` (D-KBf2 + the L15 label split)

- Reads through `load_arm_matrices`; `full[np.ix_(indices, indices)]` becomes
  `full[np.ix_(arm_rows, arm_rows)]` with `arm_rows = [row_of[id] for id in kept_ids]`.
- **`Census`** dataclass + **`common_positions(member_ids, loaded, anomaly_positions)`**.
  The subcollection is restricted to the members every loaded arm completed.
- L15: `ROWS_AUC_COLUMNS` gains `n_censored_members`, `n_censored_anomaly`,
  `n_censored_clean`, `censor_rate_anomaly`, `censor_rate_clean`. Corruption type
  is already a column on every AUC row, so "by corruption type" needs no new
  plumbing — the analyzer groups on it.
- Order preserved deliberately: choose → corrupt → **then** restrict. The brief's
  own words are "Mechanics unchanged; the caption changes", and restricting
  *before* the draw would make the label-conditioned rate vacuous (no chosen
  member could ever be censored) — i.e. it would delete the very disclosure L15
  asks for.
- Every member censored among the positives ⇒ censored AUC rows carrying the
  census, not a crash.
- Pre-flight (`ensure_smoke_matrices`) switched to the censoring-aware reader.

### `experiments/tkde/rq5.py` (D-KBf2 + the L15 type split)

- Same id-alignment change against `selected`.
- **`censored_by_class(selected_labels, kept_labels)`** → `label -> (lost, rate)`,
  plus `_class_census_columns` projecting it onto each `rows_per_class` row.
- `ROWS_CLUSTERING_COLUMNS` and `ROWS_GEOMETRY_COLUMNS` gain `n_censored_members`;
  `ROWS_PER_CLASS_COLUMNS` gains `n_censored_class` and `censor_rate_class`.
- Guard: `arm not in loaded or len(selected) < k` ⇒ a censored clustering row
  rather than a PAM call on fewer members than clusters.
- No backfilling of a balanced design after censoring: L15 says report the yield.
  Refilling would be the defect `RefillMismatchError` guards against in RQ4.

### `experiments/tkde/rq2.py` (D-KBf2)

- `matrix_for` returns `(matrix, member_ids_of_D, source)` and delegates to
  `load_cached_matrix_censored` (which keeps the member-order SHA-1 check that
  the hand-rolled manifest validation provided). Only one caller existed.
- **`census_common_ids(...)`** reads the *sidecars only* — no matrices — so a
  shard scoring one arm still knows what the other census arms lost. The
  `own=True` path (ndc_substances, built here) is never screened, so the common
  set is the frozen order.
- `COLUMNS_CENSUS` gains `n_requested`, `n_censored_arm`, `n_censored_common`.
  A false-merge count is comparable across arms only over a shared member set:
  both the pair count and the opportunities to merge move with it.

### Configs (item 4)

IN everywhere in RQ2–RQ7: `wstar_orbit`, `nauty_cert`, `nauty_cert_rows`,
`fact_rank`, `wl_l1`, `netlsd`, `hpd_jsd`, `bipartite_ged_path`,
`bipartite_ged_assign`, `size_l1`, `degree_seq_l1`.
OUT everywhere: `wstar_rank`, `isal_ow_rank`, `isal_ow_rank0`, `fact_rank_roles`
(verified absent by grep across all five files).
`isal_ow_struct` survives **only** in `rq7.yaml` (grep-verified).
`rq2.yaml`'s `exact0_arms` additionally keeps `isalhg_levenshtein`, `exact_ged`,
`hypercot`. `rq3.yaml` gains `fingerprint_budget_s: 60.0` (top level) and `5.0`
in `smoke`. All five files re-parsed with `yaml.safe_load`.

---

## 2. Test commands and verbatim output

Every run used `~/.conda/envs/isalhg-kbf-consumers/bin/python`.

**Environment check**

```
$ ~/.conda/envs/isalhg-kbf-consumers/bin/python -c "import isalhg; print(isalhg.__file__)"
/home/mpascual/research/code/IsalHG/.claude/worktrees/agent-a2d50b3447d1b94a5/src/isalhg/__init__.py
```

**New test files, individually**

```
$ python -m pytest tests/experiments_tkde/test_matrix_censoring.py -q
tests/experiments_tkde/test_matrix_censoring.py .............            [100%]
============================== 13 passed in 0.15s ==============================

$ python -m pytest tests/experiments_tkde/test_rq3_censoring.py -q
tests/experiments_tkde/test_rq3_censoring.py ...................         [100%]
============================== 19 passed in 0.14s ==============================

$ python -m pytest tests/experiments_tkde/test_rq245_consumers.py -q
tests/experiments_tkde/test_rq245_consumers.py ......................... [ 83%]
.....                                                                    [100%]
============================== 30 passed in 0.14s ==============================

$ python -m pytest tests/experiments_tkde/test_rq45_censored_units.py -q
tests/experiments_tkde/test_rq45_censored_units.py .....                 [100%]
============================== 5 passed in 2.80s ===============================
```

**Lint / format, whole touched tree**

```
$ python -m ruff check experiments/tkde/ tests/experiments_tkde/
All checks passed!
$ python -m ruff format --check experiments/tkde/ tests/experiments_tkde/
33 files already formatted
```

**Baseline, measured — not assumed.** Files reverted to `d53b686`
(`git checkout d53b686 -- experiments/tkde/configs experiments/tkde/matrices.py
experiments/tkde/rq3.py`, new test files moved aside), suite run, then restored:

```
================== 9 failed, 244 passed in 236.49s (0:03:56) ===================
FAILED test_rq127_smoke.py::TestSmokeEndToEnd::test_runner_then_analyzer[experiments.tkde.rq7]
FAILED test_rq127_smoke.py::TestSmokeEndToEnd::test_a_rerun_skips_the_units_already_written
FAILED test_rq36_smoke.py::TestUnitEnumeration::test_rq6_units_are_unique
FAILED test_rq36_smoke.py::TestModelIsNotSharedAcrossUnits::test_each_call_returns_a_fresh_model
FAILED test_rq36_smoke.py::TestModelIsNotSharedAcrossUnits::test_the_fresh_model_samples_identically
FAILED test_rq36_smoke.py::TestModelIsNotSharedAcrossUnits::test_a_used_model_is_not_reachable_from_the_context
FAILED test_rq36_smoke.py::TestDeployStamps::test_the_stamps_name_the_imported_package
FAILED test_rq45_smoke.py::TestMatrixUnits::test_default_specs_cover_the_frozen_arms
FAILED test_rq45_smoke.py::TestSmokeIsolation::test_deploy_stamps_name_both_trees
```

**Final, with all five commits applied:**

```
$ python -m pytest tests/experiments_tkde/ -q
================== 9 failed, 311 passed in 397.39s (0:06:37) ===================
```

Identical failure set, identical ids. **+67 passing, 0 new failures.**

Mid-way there were briefly 11 failures; the two extra were
`test_rq36_smoke.py::TestEndToEnd::{test_rq3_smoke_and_analysis,
test_rq3_is_idempotent_per_unit}`. Diagnosed and fixed — see §3.2.

---

## 3. Where this brief was wrong, or where I had to decide

### 3.1 `rq4.yaml` and `rq5.yaml` have no `smoke:` block — WRONG in the brief

The brief says to apply the arm set to "`rq2.yaml` …, `rq3.yaml` …, `rq4.yaml`,
`rq5.yaml`, `rq7.yaml`, **and their `smoke` blocks**".

```
$ for f in rq2 rq3 rq4 rq5 rq7; do echo -n "$f.yaml smoke: "; grep -c "^smoke:" $f.yaml; done
rq2.yaml smoke: 1
rq3.yaml smoke: 1
rq4.yaml smoke: 0
rq5.yaml smoke: 0
rq7.yaml smoke: 1
```

`rq4.yaml` (55 lines) and `rq5.yaml` (77 lines) have none, and `rq3.yaml`'s smoke
block overrides no arm list (`rq3.py::_apply_smoke` forwards `seed_count`,
`corpus_a`, `corpus_b`, `medoid_arms` only). Only `rq2.yaml` and `rq7.yaml` had
smoke arms to correct; both were corrected.

### 3.2 The brief's process-model instruction is right, and it broke a test — fixed

"Mind the process model: an in-process C++ canonicalisation poisons later forks"
is exactly right, and the fix landed as specified. It also exposed an
order-dependence in the existing suite:

```
$ python -m pytest tests/experiments_tkde/test_rq127_smoke.py tests/experiments_tkde/test_rq36_smoke.py -q
E   experiments.tkde.budget.TkdeBudgetError: the C++ canonicalizer has already run in
    this process, so a forked child deadlocks on it and every result here would be a
    false censoring; route every cpp canonicalization through engine_word, or run this
    measurement in a fresh process
```

`test_rq127_smoke.py` runs the engine in-process and sorts before
`test_rq36_smoke.py`, so an in-process `rq3.main` inherited a poisoned
interpreter. Both RQ3 end-to-end tests **passed in isolation** (`1 passed in
80.54s`) and failed only in a full-suite run — the canary doing its job on a
poisoned session, not a defect in the runner.

The campaign never has this problem: each shard is a fresh process, and
`evaluate_collection` now keeps its own engine builds in children. I therefore
made the test model the campaign — `_run_rq3` invokes
`python -m experiments.tkde.rq3` in a subprocess — rather than weaken the guard.
I did **not** touch `run_guarded`'s consensus call site, which keeps
`cpp_engine=False` per the brief.

### 3.3 `rq5.yaml`'s `wd50k100` control cannot take the full arm set — a hard constraint

`matrices.py::DEFAULT_SPECS` (which I was told not to touch) builds only
`fact_rank`, `ISAL_MATRIX_ARMS`, `nauty_cert`, `wl_l1`, `size_l1`,
`degree_seq_l1` for `wd50k100`. `nauty_cert_rows`, `netlsd`, `hpd_jsd` and both
`bipartite_*` have no matrix there. That control keeps
`fact_rank, wstar_orbit, nauty_cert, wl_l1, size_l1, degree_seq_l1` — OUT arms
removed, `wstar_orbit` added, nothing unbuildable requested. "Both tokenisations
everywhere" cannot apply to a collection where the second one was never built.

### 3.4 `rq7.yaml`'s `yield_arms` left alone — a judgement call

`yield_arms: [isalhg_levenshtein, isal_ow_struct, fact_rank]` contains no OUT
arm. Adding `wstar_orbit` there would be a scope expansion with real queue cost
(the yield pass deliberately places collections by measured canonicalization
time, and `wd50k66_full` is explicitly outside the envelope). Flagging rather
than deciding.

### 3.5 The brief's claim about the RQ3 row schema is accurate

Verified: `censored` is already on both the medoid rows (`rq3.py` 490/511/527 at
base) and the consensus/`majority_merge` rows (580/638). `n_censored_members` is
set only on medoid rows and is absent from `shared`, so the consensus census is
neither overwritten nor hidden. `io.write_rows` renders a missing key as an empty
field (pinned by the existing `test_missing_key_becomes_an_empty_field`).

---

## 4. Residual risk

1. **RQ2's `own` build of `wstar_orbit` on `ndc_substances` is unbudgeted and
   in-process — the highest risk here.** `ndc_substances` is absent from
   `DEFAULT_SPECS`, so `census_own_collections: [ndc_substances]` makes `rq2`
   build every census arm itself via `matrix_for`'s `build_matrix(...)` — no
   screen, no fork. The arm set puts `wstar_orbit` in `census_arms`, so RQ2 will
   canonicalize that collection in-process with the C++ engine. Two consequences:
   a single arity-heavy member can hang the unit, and the build poisons that
   process for any later fork. The 77 measured censorings were on `ndc_classes`
   (70) and `wd50k66` (7); `ndc_substances` was never screened, so its exposure is
   **unmeasured**. Budgeting RQ2's own build is a design decision outside this
   brief; I did not make it. **Measure `ndc_substances` before submitting RQ2**,
   or move it into the matrices job.

2. **No pre-existing end-to-end test calls `rq4.run_unit` or `rq5.run_unit`.**
   The repo's `test_rq45_smoke.py` covers unit enumeration, selection and
   verdicts only. I closed the gap for RQ5 with
   `test_rq45_censored_units.py`, whose load-bearing test is differential (a
   censored arm must score exactly what an uncensored arm restricted to the same
   survivors scores — positional indexing fails it). **RQ4's `run_unit` body is
   still not covered end to end**: it needs realised corruptions, so a synthetic
   fixture is much heavier. Its helpers (`common_positions`, `Census`, the row
   schema) are unit-tested; the `arm_rows` splice in `run_unit` is not.

3. **`rq5.geometry_row` raises below 11 members.** `hubness(D, HUBNESS_K=10)`
   requires `N >= 11`, and censoring lowers `N`. Surfaced by my own test at
   `N=10` (`MetricSpaceError: k must satisfy 1 <= k <= 9, got 10`). Not a
   practical risk on wd50k66 (3,492 selected members), and pre-existing — but the
   `full` design has no `try` around `geometry_row`, so a heavily censored small
   collection would kill the arm rather than censor it. Left alone as
   out of scope.

4. **Restricting RQ5's balanced design does not re-balance it.** Censoring can
   make classes uneven and can in principle drop one below `min_class_size` while
   `k` is still computed on the parent. Reported per type
   (`n_censored_class` / `censor_rate_class`) rather than repaired, per L15.

5. **`BUILD_MARGIN_S = 60.0` is a judgement, not a measurement.** The screen
   bounds each member, so the guarded build's ceiling is `N·budget + 60 s`; the
   margin covers the pairwise Levenshtein pass. If a large Corpus B run (T−1 up
   to 40 members) has an unusually slow pairwise pass, the build would be
   reported censored with `n_censored_members = 0` — honest, but distinguishable
   only by that combination.

6. **Nine pre-existing failures untouched**, none in scope: the RQ6 unit/model
   tests, the deploy-stamp assertions (an artefact of the worktree editable
   install adding `isalhg_git_sha` / `isalhg_path`), the RQ7 smoke, and
   `test_default_specs_cover_the_frozen_arms`, which asserts
   `sum(len(arms)) == 37` while `DEFAULT_SPECS` now totals **31** — stale since
   `ISAL_MATRIX_ARMS` changed at D-KBf3. I did not touch `DEFAULT_SPECS`; the
   test needs updating by whoever owns that change.
