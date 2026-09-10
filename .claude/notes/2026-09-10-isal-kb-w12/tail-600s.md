# T-KBp — the 600 s tail characterisation

**Agent:** worker, isolated worktree `agent-a61c36e1da5850229`, base `880ba49`,
branch `feature/isal-kb-word`. **Date:** 2026-09-10.

Nothing was submitted to Picasso. Everything below was built and measured
locally.

---

## 1. The brief was wrong about the input, and the correction matters

The brief said to read the censored ids from
`results/IEEETKDE/matrices/{wd50k66,ndc_classes,wd50k100}/wstar_orbit.censored.json`.
Those sidecars are a **different population** from the one T-KBe's pre-stated
expectation is about, and the arm the expectation turns on has no sidecar at
all. Measured, not suspected:

### 1.1 The sidecars do not carry the 77

```
$ ls /media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE/matrices/*/*.censored.json
ndc_classes/wstar_orbit.censored.json      20.2K
ndc_substances/wstar_orbit.censored.json   26.1K
wd50k100/wstar_orbit.censored.json         26.6K
wd50k66/wstar_orbit.censored.json          57.3K
```

Their `n_censored`:

| collection | `n_requested` | `n_censored` (`wstar_orbit`) |
|---|---|---|
| ndc_classes | 1,381 | 70 |
| ndc_substances | 1,745 | 84 |
| wd50k100 | 1,837 | 11 |
| wd50k66 | 3,988 | 5 |

Three points the brief did not have:

1. **The three collections it names total 86, not 77** (70 + 11 + 5).
2. **A fourth collection, `ndc_substances`, also carries a sidecar** (84), which
   the brief does not mention. Over all four the sidecar total is **170**.
3. **`wstar_rank.censored.json` and `isalhg_levenshtein.censored.json` do not
   exist anywhere on the drive.** The brief anticipated this possibility
   ("if they do not, say so"); it turns out to be the case, and it is fatal for
   the sidecar route, because `wstar_rank`'s 53 are the *refutable* clause.

The sidecars are the members a **distance-matrix build** dropped — a legitimate
tail, but not this one.

The rest of the brief's reading of the code checks out: sidecars do carry
`member_ids` / `censored_ids` / `n_requested` (plus `arm`, `n_censored`,
`member_order_sha1`); `engine_word` / `guarded_budget_call` / `CPP_ENGINE_ARMS`
are as described; `aut_bucket` and the M3 row shape are as described; the RQ7
launcher/worker pair is the right model. Only the input is wrong, and only in a
way that could not be seen without looking at the disk.

### 1.2 The 77 / 53 reproduce exactly from the RQ1 M3 census

Census over `RQ1_*/{addressing,addressing_cpp,addressing_rank,merged}/rows_m3__*.csv`,
deduplicated on `(collection, member_id, arm)`:

```
==== addressing
   isalhg_levenshtein       total=  7369 censored=  353
   wstar_orbit              total=  7369 censored=   77
==== addressing_cpp
   wstar_orbit              total=  7369 censored=   77
==== addressing_rank
   wstar_rank               total=  7369 censored=   53
==== merged
   isalhg_levenshtein       total=  7369 censored=  356
   wstar_orbit              total=  7369 censored=   77
   wstar_rank               total=  7369 censored=   53
```

`merged` reproduces T-KBe's table exactly (77 / 53, and 356 for the unpruned
engine against its recorded 354–357 drift). D-ART5 corroborates the source in
words: "The 600 s re-run of **the 77 orbit-censored members** folds into the RQ7
envelope sweep."

Composition of the two tails, which also re-derives D-ART5's R2 sentence:

```
=== wstar_orbit: 77 censored ===
  by collection: {'ndc_classes': 70, 'wd50k66': 7}
  by aut_bucket: {'<1e3': 69, '1e3-1e6': 8}
  by k:          {7: 6, 8: 1, 9: 1, 10: 69}

=== wstar_rank: 53 censored ===
  by collection: {'ndc_classes': 53}
  by aut_bucket: {'<1e3': 52, '1e3-1e6': 1}
  by k:          {10: 53}

orbit ∩ rank: 53   orbit only: 24   rank only: 0   union: 77
```

D-ART5 R2 says "the residual 77 being 69 arity-10 members at |Aut| < 10³" —
confirmed to the member.

**A structural fact neither brief states: the 53 are a strict subset of the 77.**
Every `wstar_rank`-censored member is also `wstar_orbit`-censored; the union is
77 members, 130 (member, arm) calls. The brief's "~130 members × 600 s ≈ 22 h"
cost gate is therefore right in its arithmetic, but it is 130 *calls* over 77
*members* — which is why a shard groups by collection and pays one corpus load
for both arms of a member.

That subset relation is itself evidence for the pre-stated expectation's
mechanism reading and was not available when T-KBe was written: the rank engine
censors on a strict sub-population of what the orbit engine censors on, and both
sub-populations are entirely arity-10 (`k: {10: 53}` for rank; 69 of 77 for
orbit). Whatever stops the rank engine stops the orbit engine too. The run will
say whether 600 s changes that.

### 1.4 The sidecar source, exercised against the real files

```
$ python -c "read_sidecar_census(R, ('wstar_orbit','wstar_rank','isalhg_levenshtein'))"
WARNING arm 'isalhg_levenshtein' has no censored members in source 'sidecar'; it is not measurable
WARNING arm 'wstar_rank' has no censored members in source 'sidecar'; it is not measurable
members: 170
by collection: {'ndc_classes': 70, 'ndc_substances': 84, 'wd50k100': 11, 'wd50k66': 5}
  wstar_orbit            sidecars in: ['ndc_classes', 'ndc_substances', 'wd50k100', 'wd50k66']
  wstar_rank             sidecars in: []
  isalhg_levenshtein     sidecars in: []
measurable  : ['wstar_orbit']
unmeasurable: ['isalhg_levenshtein', 'wstar_rank']
```

That is the brief's "if they do not, say so and report which arms are
measurable" satisfied by the code itself, not only by this note.

### 1.3 What was built as a result

The runner takes **both** sources. `--source m3` (default) reads the RQ1 M3
census and is the only source that can answer the pre-stated expectation;
`--source sidecar` reads the matrix-build sidecars, reports per arm which
collections carry one, and warns for every arm that carries none. Supporting
the m3 source is not scope creep: without it the acceptance criterion
("completion counts reported per arm against the pre-stated expectation")
cannot be met, since `wstar_rank` is unmeasurable from sidecars.

The m3 source has a second, independent advantage: its rows already carry
`n`, `m`, `k` and `aut_bucket` per member, so a tail row is paired with its own
60 s row and uses the *same* `k` — not a recomputed one.

---

## 2. Files

All six are new. **No existing file was modified** (`git status` shows six
untracked paths and nothing else), so `rq1`–`rq7`, `matrices.py`, `budget.py`
and `language/` are untouched; they are imported, never edited.

| File | What it is |
|---|---|
| `experiments/tkde/tail600.py` | The runner. Two census readers, the work list, the stride shard, the per-member budgeted call, the row writer, the CLI. |
| `experiments/tkde/analyze_tail600.py` | The scorer. Per-arm census plus the three clause verdicts, printed as CONFIRMED / REFUTED / INDETERMINATE. |
| `experiments/tkde/configs/tail600.yaml` | 600 s, both arms, 16 shards; a smoke overlay at 5 s / 4 items. |
| `slurm/tkde/tail600_launcher.sh` | Launcher, modelled on `rq7_launcher.sh` (`--test-only`, `--smoke`, `--no-sweep`, the `_clean_job_id` ANSI guard, the `cd REPO_DIR` before `--count`). Shard arithmetic in the header. |
| `slurm/tkde/tail600_worker.sh` | Worker, modelled on `rq7_worker.sh` (`common.sh`, `TKDE_THREADS=1`, localscratch staging, `tkde_run_synced`, the start cutoff). |
| `tests/experiments_tkde/test_tail600.py` | 90 unit tests. |

### Design points worth stating

**The rows cannot be swept into a published table.** D-ART5 decision 2 is
"never a row", and three independent things enforce it rather than one
convention:

- the results folder is `TAIL600_characterisation/`, which matches neither
  `RQ*` nor `RQ1_*` — every analyzer and merge tool of the campaign globs one of
  those;
- the row file is `rows_tail600__*.csv`, so a `rows_m3__*` glob never sees it;
- every row carries `kind="tail_characterisation"`, and the analyzer *raises*
  on a row whose `kind` is anything else. A row copied out of the folder still
  says what it is.

**Only the budget differs from the 60 s run.** `measure_member` calls
`engine_word(H, k, budget, engine=BUDGETED_ARMS[arm])` — the same function,
the same engine per arm (`orbit` / `rank`), the same forked child under the same
`guarded_budget_call` fork-health canary, and `k` taken from the 60 s row. The
worker sets `TKDE_THREADS=1` before sourcing `common.sh` for the same reason
RQ7 does: a wall-clock compared against a single-threaded row must itself be
single-threaded.

**Two smaller deviations from the brief's letter, both deliberate.**

- The brief asks for "the correct `cpp_engine` declaration". The runner does not
  declare it: it calls `engine_word`, which routes the nauty-assisted engines
  through `guarded_budget_call(_engine_payload, …)` with the declaration
  already correct. Declaring it again at this level would be a second copy of a
  fact `budget.py` owns, and `budget.py`'s own docstring says `cpp_engine` "is
  the caller's declaration of what the child does, not a switch to be turned off
  for convenience" — the caller here is `engine_word`.
- `aut_bucket` is **read from the census row, not recomputed**. Recomputing it
  would pay pynauty on 77 members for a value already measured, and — worse —
  could return a different stratum from the 60 s row this row is meant to be
  paired with. The same argument applies to `k`, which is also taken from the
  census so the two calls encode at the same pointer count. The sidecar source
  has neither field, so there `k` falls back to `required_k(H)` and
  `aut_bucket` is empty; that is stated in the row rather than guessed.

**The thresholds are pre-registered in code, before the run.** "Material
fraction" is `MATERIAL_FRACTION = 0.25` and "most" is `MOST_FRACTION = 0.50`,
both constants in `analyze_tail600.py`, both pinned by a test that asserts they
have not drifted. Raw counts print beside every verdict so a reader who prefers
another threshold can apply it. The rationale for 0.25 is in the module
docstring: a tenfold budget that recovers less than a quarter of a tail has not
shown that tail to continue the feasible-search distribution.

---

## 3. Shard arithmetic (as in the launcher header)

```
Work list (RQ1 merged M3 census, measured 2026-09-10):
    wstar_orbit   77 censored members  (70 ndc_classes + 7 wd50k66)
    wstar_rank    53 censored members  (all ndc_classes; a strict SUBSET)
    total        130 (member, arm) calls

Worst case = every call hits the ceiling:
    130 x 600 s                            = 78,000 s = 21.7 h sequential

n_shards = 16:
    ceil(130 / 16)                         = 9 calls in the largest shard
    9 x (600 s + ~10 s fork/join)          =  5,490 s = 1.53 h payload
  + corpus load (ndc_classes 1,381 members, wd50k66 3,988; a shard
    touches at most both, loading each once)   ~ 900 s = 0.25 h
    ---------------------------------------------------------------
    worst case per task                    =  6,390 s = 1.78 h

WALL = 4 h  ->  worst-case task uses 44 % of its wall.
```

`BUNDLE = 1` (RQ7 uses 5): one shard here is already 1.5 h of payload, so
bundling would push a task towards its wall for no scheduling gain.

The 130 and the 9 are both verified rather than asserted:

```
$ python -m experiments.tkde.tail600 --config .../tail600.yaml \
      --census-root /media/.../IEEETKDE --list-work | wc -l
130
$ python -m experiments.tkde.tail600 --config .../tail600.yaml --count
16
```

and `test_the_campaign_worst_case_shard_is_nine_calls` pins
`max(len(shard_slice(range(130), i, 16))) == 9`.

---

## 4. Commands and verbatim output

### 4.1 Environment

```
$ conda create -y -n isalhg-tail --clone isalhg
CLONE_EXIT=0

$ ~/.conda/envs/isalhg-tail/bin/python -m pip install -e ".[dev]" --no-deps --no-build-isolation
EXIT=2
pip._vendor.pyproject_hooks._impl.BackendUnavailable: Cannot import 'scikit_build_core.build'
```

**The editable install failed on missing build deps, as the brief anticipated.**
Installed into the clone and retried:

```
$ ~/.conda/envs/isalhg-tail/bin/python -m pip install scikit-build-core nanobind cmake ninja
Successfully installed cmake-4.4.3 nanobind-3.0.1 ninja-1.13.2 scikit-build-core-1.0.3

$ ~/.conda/envs/isalhg-tail/bin/python -m pip install -e ".[dev]" --no-deps --no-build-isolation
EXIT=0
Successfully installed isalhg-0.0.1

$ ~/.conda/envs/isalhg-tail/bin/python -c "import isalhg, isalhg.core._core as c; print(isalhg.__file__); print(c.__file__)"
/home/mpascual/research/code/IsalHG/.claude/worktrees/agent-a61c36e1da5850229/src/isalhg/__init__.py
/home/mpascual/.conda/envs/isalhg-tail/lib/python3.11/site-packages/isalhg/core/_core.cpython-311-x86_64-linux-gnu.so
```

`isalhg` resolves inside this worktree.

### 4.2 Lint

```
$ ~/.conda/envs/isalhg-tail/bin/python -m ruff check \
    experiments/tkde/tail600.py experiments/tkde/analyze_tail600.py \
    tests/experiments_tkde/test_tail600.py
All checks passed!

$ bash -n slurm/tkde/tail600_launcher.sh && bash -n slurm/tkde/tail600_worker.sh
BASH SYNTAX OK
```

`shellcheck` is not installed on this machine, so the shell scripts were
checked with `bash -n` only.

### 4.3 The new unit tests

```
$ ~/.conda/envs/isalhg-tail/bin/python -m pytest tests/experiments_tkde/test_tail600.py -q -p no:randomly
90 passed in 0.13s
```

Three defects were found and fixed before anything left this machine. Each is
its own commit, and each would have corrupted the completion count the verdict
turns on.

**(a) The smoke's rows would have been scored with the real ones** — found by a
test on its first run:

```
FAILED tests/experiments_tkde/test_tail600.py::TestReadRows::test_the_smoke_subtree_is_read_only_on_request
E   Failed: DID NOT RAISE
```

`read_rows` globbed `<root>/TAIL600_characterisation/**/rows_tail600__*.csv`
recursively, and the smoke subtree lives *inside* that folder — so a 5 s smoke's
four censored rows would have joined the 600 s tally. Fixed by addressing the
exact directory through `resolve_paths`, so analyzer and runner cannot drift
apart (commit `0aefa29`).

**(b) A truncated shard would have been skipped, not re-run** — found by
self-review (`397cb08`). A shard here is **one** row file, unlike RQ7 where a
shard is many per-unit files, so a run cut short by `--start-cutoff-epoch`
leaves a partial file. The presence-only idempotence check would then let the
`afterany` recovery sweep skip that shard and the deferred members would never
be measured — silently subtracting them from the completion count, with nothing
in the logs saying so. `shard_is_done()` now counts data rows against the
shard's own size, re-runs on a mismatch, and the runner warns when it writes a
partial shard.

**(c) Fifteen shards' provenance was being overwritten** — self-review
(`6008724`). Sixteen shards share one experiment directory, so `config.json`,
`summary.json` and `manifest.json` were last-writer-wins. RQ7 answers this by
writing a second copy under `<experiment>/_shards/<nnn>/`; mirrored here.

**(d) The report heading hard-coded "600 s"** while the smoke ran at 5 s. It is
now read from the rows' own `budget_s` and says `5/600` when the rows are mixed.
A report that misstates its own budget is exactly the sentence that reaches
prose unchallenged.

### 4.4 The smoke, end to end (~20 s)

```
$ python -m experiments.tkde.tail600 --config experiments/tkde/configs/tail600.yaml \
    --out <scratch> --census-root /media/.../IEEETKDE --data-root /media/.../IEEETKDE --smoke
INFO tail600: source=m3 budget=5s shard 0/1 -> 4 of 4 (wstar_orbit, wstar_rank) tag=b17322f3
INFO ndc_classes/100@440 wstar_orbit: 5.0s censored=1
INFO ndc_classes/100@440 wstar_rank: 5.0s censored=1
INFO ndc_classes/101@440 wstar_orbit: 5.0s censored=1
INFO ndc_classes/101@440 wstar_rank: 5.0s censored=1
INFO wrote 4 rows to <scratch>/TAIL600_characterisation/_smoke/tail_600s/rows_tail600__b17322f3-000of001.csv
```

Re-run, confirming idempotence:

```
INFO skip shard 0/1 (rows present at <scratch>/.../rows_tail600__b17322f3-000of001.csv)
```

Scored:

```
$ python -m experiments.tkde.analyze_tail600 --root <scratch> --smoke
# 5 s tail characterisation (D-ART5 decision 2 -- never a published row)

| arm | re-run | completed at 5 s | still censored | completion |
|---|---|---|---|---|
| `wstar_orbit` | 2 | 0 | 2 | 0.0% |
| `wstar_rank` | 2 | 0 | 2 | 0.0% |

## Verdict against the pre-stated expectation (T-KBe)

- **material-fraction** (`wstar_orbit`): **REFUTED** — 0/2 = 0.0% completed ...
- **most-still-censored** (`wstar_rank`): **CONFIRMED** — 2/2 = 100.0% still censored ...
- **displacement-not-budget** (`wstar_rank`): **CONFIRMED** — 2/2 = 100.0% still
  censored at a tenfold budget: the gap is the mechanism ..., and D-ART5 stands
```

**This smoke verdict is meaningless as science and must not be read as one.**
The smoke budget is 5 s, so every 60 s-censored member censors by construction.
It demonstrates the pipeline, not the tail. The first draft of the report
hard-coded "600 s" in the heading; that is now read from the rows' own
`budget_s`, which is why the heading above says 5 s.

### 4.5 The completion path, which the smoke cannot exercise

Every member in the work list is censored by construction, so the smoke only
ever exercised the *censored* branch. Probed the other branch directly on a
four-node hypergraph:

```
$ python -c "... measure_member(TailMember('probe','p1',arm,k=3), H, 30.0) ..."
wstar_orbit {'secs': 0.001969, 'censored': 0, 'tokens': 3, 'error': '', 'k': 3}
wstar_rank  {'secs': 0.001874, 'censored': 0, 'tokens': 3, 'error': '', 'k': 3}
```

Both arms completed in the same process, so the fork-health canary holds across
an arm switch — which the real run depends on, since a shard runs both arms of
the same member back to back.

---

## 5. Test table (full suite, `-p no:randomly`)

The baseline was measured on this worktree at base `880ba49` with the working
tree clean — not taken on trust from the brief — and the suite then re-run with
the six new files present. `-p no:randomly` pins the order so the two runs are
comparable.

| run | passed | failed | verdict |
|---|---|---|---|
| baseline (`880ba49`, clean) | 2,942 | 8 | — |
| with T-KBp | 3,038 | 8 | no new failures |

Verbatim summary lines:

```
===== 8 failed, 2942 passed, 30 skipped, 21 warnings in 1962.36s (0:32:42) =====
===== 8 failed, 3038 passed, 30 skipped, 21 warnings in 1968.38s (0:32:48) =====
```

3,038 − 2,942 = **96 new passes**, which is exactly the size of
`test_tail600.py`. The failure sets were compared as sets, not counted:

```
$ diff <(grep '^FAILED' baseline.log | sed 's/ - .*//' | sort) \
       <(grep '^FAILED' after.log    | sed 's/ - .*//' | sort)
(no output)
```

The 8 baseline failures, named, so a future reader can check they are the same
set rather than the same count:

```
FAILED tests/experiments_tkde/test_rq36_smoke.py::TestUnitEnumeration::test_rq6_units_are_unique
FAILED tests/experiments_tkde/test_rq36_smoke.py::TestModelIsNotSharedAcrossUnits::test_each_call_returns_a_fresh_model
FAILED tests/experiments_tkde/test_rq36_smoke.py::TestModelIsNotSharedAcrossUnits::test_the_fresh_model_samples_identically
FAILED tests/experiments_tkde/test_rq36_smoke.py::TestModelIsNotSharedAcrossUnits::test_a_used_model_is_not_reachable_from_the_context
FAILED tests/experiments_tkde/test_rq36_smoke.py::TestDeployStamps::test_the_stamps_name_the_imported_package
FAILED tests/experiments_tkde/test_rq45_smoke.py::TestSmokeIsolation::test_deploy_stamps_name_both_trees
FAILED tests/integration/test_cpp_orbit_corpus.py::test_orbit_matches_unpruned_wstar_c[wd50k66]
FAILED tests/integration/test_cpp_orbit_corpus.py::test_orbit_matches_unpruned_wstar_c[ndc_classes]
```

The last two are the load-sensitive pair T-KBr records. They appear in both
runs, identically, so no isolation re-run was needed to tell them apart from a
regression — the set diff already does that.

`ruff` on the files touched:

```
$ ~/.conda/envs/isalhg-tail/bin/python -m ruff check \
    experiments/tkde/tail600.py experiments/tkde/analyze_tail600.py \
    tests/experiments_tkde/test_tail600.py
All checks passed!
```

---

## 6. Residual risk

1. **The census must be deployed on Picasso.** The runner reads
   `${ISALHG_RESULTS_ROOT}/RQ1_*/merged/rows_m3__*.csv`. That tree exists on the
   local drive; I could not verify Picasso's copy, and the brief forbids
   submitting. If it is absent the runner raises a named error
   (`no RQ1 M3 census under <path>; deploy the merged RQ1 rows, or run with
   --source sidecar`) rather than measuring something else — but the failure
   arrives at job start, not at submission. **Check first:**
   `ls ~/results/IEEETKDE/RQ1_*/merged/rows_m3__*.csv | wc -l` on the login
   node; it should be 36.
2. **`--test-only` was not exercised.** `sbatch` does not exist on this machine,
   so the launcher was validated by `bash -n` and by driving its `--count` path
   directly. The submission command below runs `--test-only` first for exactly
   this reason.
3. **The 600 s budget is wall clock, so the tail counts are not exactly
   reproducible** — the same reason T-KBe records the unpruned engine drifting
   357 → 354. A member whose true cost sits near 600 s is decided by node load.
   This affects the *count*, never a value, and the near-boundary mass at 600 s
   is itself part of what the run measures.
4. **`ndc_substances` is absent from both tails.** It has 84 sidecar-censored
   members but zero in the M3 census, because the RQ1 census covers 7,369
   members and `ndc_substances` is not among its collections. If the author
   wants that population characterised it is a `--source sidecar` run, and a
   different question from the pre-stated expectation.
5. **`isalhg_levenshtein` is not in the default arms.** Its 356 censored members
   would cost ~59 h of budget against the default pair's 22 h, and it is the
   unpruned engine, not the published representation. Naming it in `arms:`
   measures it; the shard count would need raising with it.
6. **Memory at 600 s was not measured.** The worker asks `--mem=16G`, matching
   RQ7 and the 60 s runs that produced these rows. A tenfold budget is a
   tenfold-longer search, and the record shows the *Python* engines OOM-killing
   whole array tasks on exactly this population (RQ1 array 2247394), which is
   why `PYTHON_ENGINE_MAX_TUPLES` exists. The reason 16G is nevertheless
   defensible is that on the cluster these arms run the **C++** engine, and
   `budget.py` records the relevant difference measured: "the Python
   displacement search materialises `(2r+1)^k` tuples per frame (the C++
   engine's Round-11 inversion does not)". So the blowup mechanism is absent on
   the path this job takes. If a task is nevertheless OOM-killed, `BUNDLE=1`
   confines the loss to that shard's ≤ 9 members — but the recovery sweep would
   re-run it and hit the same wall, so raise `--mem` in the worker rather than
   re-submitting unchanged.

---

## 7. Submission command (nothing was submitted)

From the Picasso login node, after `scripts/tkde/sync_to_picasso.sh` has
deployed this branch:

```bash
# 1. validate the array without queuing anything
bash ~/fscratch/repos/IsalHG-tkde/slurm/tkde/tail600_launcher.sh --test-only

# 2. a 30-minute smoke (four members at 5 s, its own results subtree)
bash ~/fscratch/repos/IsalHG-tkde/slurm/tkde/tail600_launcher.sh --smoke

# 3. the real array: 16 tasks, 4 h wall each, plus one afterany recovery sweep
bash ~/fscratch/repos/IsalHG-tkde/slurm/tkde/tail600_launcher.sh

# 4. score it
~/fscratch/conda_envs/isalhg-tkde/bin/python -m experiments.tkde.analyze_tail600 \
    --root ~/results/IEEETKDE \
    --out ~/results/IEEETKDE/TAIL600_characterisation/verdict.md
```

`--no-sweep` skips the recovery pass. There are four campaign jobs in flight;
this array throttles at 16 concurrent tasks and can be lowered with
`MAX_CONCURRENT=8 bash .../tail600_launcher.sh`.
