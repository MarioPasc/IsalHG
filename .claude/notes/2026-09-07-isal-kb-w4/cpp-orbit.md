# Work log — cpp-orbit

## Identity

| Field | Value |
|---|---|
| Agent | `cpp-orbit` |
| Wave | `2026-09-07-isal-kb-w4` |
| Model / effort | Opus 5 (1M context) / `xhigh` |
| Branch | `worktree-agent-a23721da4d3fa93b9` |
| Worktree | `/home/mpascual/research/code/IsalHG/.claude/worktrees/agent-a23721da4d3fa93b9` |
| Base commit | `45ce493747ba943f652c919a9e73de1d0b5891f0` |
| Head commit | `a858609` (+ this log) |
| Started / finished | 2026-09-07 13:24 CEST / 2026-09-07 16:47 CEST |
| Status | complete |

## 1. Prompt as received

```
# Task: cpp-orbit — the stabiliser-orbit oracle inside the C++ tie-complete search (value-preserving `w*_c`)

You are an implementation agent (name: `cpp-orbit`) in an isolated git worktree on a branch of your own. You never see the orchestrator's conversation; everything you need is in this prompt and the repository. WAVE_ID = `2026-09-07-isal-kb-w4`. No peer in this wave; `main` is the orchestrator (SendMessage).

## Standing obligations
1. Work only inside your worktree (`git rev-parse --show-toplevel` must NOT be `/home/mpascual/research/code/IsalHG`); edit only files in your ownership set.
2. Commit all work in logical conventional commits; uncommitted work does not exist. End every commit message with the trailer line `Claude-Session: https://claude.ai/code/session_01F3KtB1s4dXGiNVyyaHfsix`.
3. Maintain your log at `.claude/notes/2026-09-07-isal-kb-w4/cpp-orbit.md` from the first action (template below); commit it last (`docs(notes): cpp-orbit work log`).
4. Never `git push`, rebase, merge, or touch other branches/worktrees or the main checkout.
5. You cannot ask the user; message `main` on ambiguity, record the assumption, keep working. Commit early and often: this session's plan quota can terminate you without warning, and committed work survives.
6. Report failure honestly, with evidence.

## Mission
The Python tie-complete encoder has a stabiliser-orbit hook (`core/orbit_oracle.py::OrbitOracle` protocol; `core/hypergraph_to_string.py`, the `orbit_oracle` parameter of `greedy_h2s`; `core/canonical.py`, `algorithm="canonical_orbit"`; `iso_backends/orbit_oracle.py::PynautyOrbitOracle` and `canonical_string_orbit` / `canonical_fingerprint_orbit`). It returns the frozen `w*_c` bit for bit while branching over one representative per orbit of the automorphism group fixing the placed prefix (Proposition 7.3 of `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/completeness/theorem_c_ordered_walk.tex`). Its measured effect is the article's symmetric-input number (R2): on the wd50k66 members the C++ engine censors at 60 s, 97 % of those with `|Aut| ≥ 1e7` complete in a median 0.3 s. But the Python engine is infeasible above arity 4 and the author's rule is that everything in the final article runs on the C++ engine. Port the hook: `canonical_string(H, k=k, algorithm="canonical_orbit", orbit_oracle=<PynautyOrbitOracle>, backend="cpp")` returns `w*_c` bit for bit, with the C++ tie-branch consulting the oracle at every residual tie and the seed loop reduced to one seed per `Aut(H)`-orbit.

## Design (fixed — do not redesign)
- **Callback, not native automorphisms.** The bindings accept a Python object implementing the `OrbitOracle` protocol (three methods: `seed_representatives(H, seeds)`, `edge_representatives(H, placed, tied_edges)`, `ordering_representatives(H, placed, edge, orderings)`; `placed` = INPUT node ids already mapped, in creation order; each returns representatives chosen from its input, in input order). A new `AlgorithmVariant` (`GreedyMinCompleteOrbit`, next free id after `GreedyMinRank = 8`) makes `encode_from`'s tie branch call the oracle with `(placed input ids, tied edge ids)` and, per representative edge, with the label-respecting orderings of its new vertices, and branch only over what comes back. Calls go through nanobind under `nb::gil_scoped_acquire`; the seed loop for this variant is **single-threaded** (the persistent thread pool must never call into Python concurrently) — reduce the seeds with `seed_representatives` first. The oracle needs the *input* hypergraph object it was constructed for: pass the Python `SparseHypergraph` handle to the bindings alongside the C++ structure, or let the oracle capture it at construction (the Python `PynautyOrbitOracle` already caches its Levi graph per `id(H)`); document the choice.
- Representatives are used verbatim (value-equivalent by Prop. 7.3); the C++ side must not re-sort or filter them beyond mapping ids.
- Every other variant's code path and output must be byte-identical (the frozen pins and the full suite guard it). No change to the Python engines' semantics.

## Read first
- `docs/article/H2S_S2H.md` §6.5–6.7, §8; `docs/engineering/CPP_OPTIMIZATION_LOG.md` (rounds 9–11 and the wave-3 entry for `GreedyMinRank`, which shows how a variant and a per-run vector were threaded through `WorkArena`, the bindings and `canonical.py`).
- The Python reference of what you port: the tie-branch in `core/hypergraph_to_string.py` (`_tied_v_candidates`, `_label_respecting_perms`, the `orbit_oracle` calls and the `stats` counters), `core/orbit_oracle.py`, `iso_backends/orbit_oracle.py` (`PynautyOrbitOracle` — the individualised Levi colouring, `autgrp`, union–find orbits), `core/canonical.py` (`canonical_orbit` dispatch, seed reduction), `tests/unit/core/test_orbit_pruning.py`, `scripts/diagnostics/orbit_pruning_probe.py`, and the wave-1 log `.claude/notes/2026-09-06-isal-kb-w1/orbit-prune.md`.
- The C++ engine: `src/isalhg/core/_native/src/h2s.cpp` (`encode_from`, `collect_tied_v_candidates`, `enumerate_label_perms_cb`, `run_branch` from wave 3), `canonical.cpp` (`canonical_string_compute`, the thread pool), `include/isalhg/canonical.hpp`, `state.hpp`, `bindings.cpp`, `_core.pyi`, `CMakeLists.txt`.
- `CLAUDE.md`, `.claude/rules/coding_rules.md`.

## Ownership (exclusive write access)
- `src/isalhg/core/_native/**`
- `src/isalhg/core/canonical.py` — ONLY the C++ dispatch for `algorithm="canonical_orbit"` (passing the oracle through; the Python path stays)
- `src/isalhg/iso_backends/orbit_oracle.py` — ONLY to add `backend: str | None = None` to `canonical_string_orbit` / `canonical_fingerprint_orbit` (default `"cpp"` when the extension is importable, else `"python"`), and any id-mapping helper the C++ callback needs
- `experiments/tkde/budget.py` — ONLY `_runs_in_python`: the orbit engine runs in C++ when the extension is importable (mirror the rank case), so the memory guard no longer applies to it
- `tests/unit/core/test_cpp_orbit.py` (new), `tests/integration/test_cpp_orbit_corpus.py` (new; skipped without the drive)
- `docs/engineering/CPP_OPTIMIZATION_LOG.md` — append one dated entry
- `.claude/notes/2026-09-07-isal-kb-w4/cpp-orbit.md`
Everything else is read-only: `core/hypergraph_to_string.py`, `core/orbit_oracle.py`, `core/algorithms/**`, `metric_space/**`, `experiments/tkde/**` except the one function above, all existing tests (`test_wstar_c_frozen.py` is frozen).

## Base state
- Base commit: the head of `feature/isal-kb-word` at spawn (`e372bf3` or its immediate successor). Do not rebase.

## Frozen contracts
- `canonical_string(H, *, k=None, structural_depth=3, algorithm="canonical_orbit", backend="cpp", orbit_oracle=<OrbitOracle>)` → identical to `backend="python"` for the same inputs and to `algorithm="canonical"` (any backend) wherever that completes; `ValueError` if `orbit_oracle` is None. `canonical_fingerprint` likewise. `engine_word(H, k, seconds, engine="orbit")` (harness) must run on the C++ path with no harness edit beyond `_runs_in_python`.
- The `OrbitOracle` protocol is unchanged (do not add methods; if the C++ side needs a different id space, map on the C++/binding side or in `iso_backends/orbit_oracle.py`).
- Bit-exactness is the acceptance gate: any divergence from the Python orbit engine or from the unpruned C++ `w*_c` is a bug, never a "new canonical form".

## Environment bootstrap (fresh checkout; the editable install is path-pinned — clone the env)
```bash
cd "$(git rev-parse --show-toplevel)"
conda create -y -n isalhg-cpporbit --clone isalhg > /tmp/claude-1000/conda-cpporbit.log 2>&1; echo "CONDA EXIT: $?"
~/.conda/envs/isalhg-cpporbit/bin/python -m pip install -e ".[dev]" > /tmp/claude-1000/build-cpporbit.log 2>&1; echo "PIP EXIT: $?"
PY=~/.conda/envs/isalhg-cpporbit/bin/python
$PY -c "import isalhg, isalhg.core._core, pynauty; print(isalhg.__file__)"   # path INSIDE your worktree
export ISALHG_RESULTS_ROOT=/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE
```
Rebuild after every C++ change with the same `pip install -e ".[dev]"`. Use only `$PY`. The workstation has 31 GB RAM; never run the Python engines on members with `min(k, arity) > 4` or `(2n-1)^k > 2e6` tuples (`experiments/tkde/budget.py::engine_word` documents the bound) — use that criterion to choose the members for the Python-vs-C++ differential; the C++-vs-C++ differential (orbit vs unpruned) has no such limit.

## Verification commands
```bash
$PY -m pytest tests/unit/core/test_cpp_orbit.py tests/unit/core/test_wstar_c_frozen.py tests/unit/core/test_orbit_pruning.py tests/unit/core/test_cpp_rank.py -q -x   # often
$PY -m pytest tests/unit tests/property -q -m "not slow" --hypothesis-seed=0   # before the final commit (do NOT pass --hypothesis-deadline=none)
$PY -m pytest tests/unit/core/test_cpp_orbit.py -q -m slow                      # the STS(13) pins through C++, once
$PY -m ruff check src/ tests/ experiments/ && $PY -m ruff format --check src/ tests/ experiments/
$PY -m mypy src/isalhg/
```

## Definition of done
1. Frozen `w*_c` pins bit-exact through the C++ orbit path: Fano, STS(9), `C_13(0,1,3)`, n=4, GQ(2,2) (fast) and **both STS(13)** (slow marker; report wall-clock — the C++ engine should make them minutes).
2. Differential vs the Python orbit engine on ≥ 500 guard-satisfying random connected labelled hypergraphs (n ≤ 8, arity ≤ 4, ≤ 3 labels per side) and 200 random stars; vs the unpruned C++ `w*_c` on ≥ 300 wd50k66 and 300 ndc_classes members that the unpruned engine completes within 60 s (through `engine_word`, forked-child budget) — all bit-identical.
3. Branch collapse reproduced in C++: stars with q ∈ {5..10} interchangeable leaves — frames visited and oracle calls, unpruned vs pruned (add the counters to the C++ path; expose them through the bindings or a debug hook).
4. **The article's R2 number:** the 100 highest-|Aut| wd50k66 members censored by the unpruned C++ engine at 60 s and the 100 ndc_classes members likewise (identify them with the symmetry probe's method, `scripts/diagnostics/pointer_timeout_symmetry_probe.py`, or from the campaign rows under `$ISALHG_RESULTS_ROOT/RQ1_addressing/`): run the C++ orbit engine with a 60 s budget; completion fraction per |Aut| bucket (`<1e3`, `1e3–1e6`, `≥1e7`) and median seconds of the completed; a table in the log.
5. `engine_word(engine="orbit")` runs on the C++ path; `_runs_in_python("orbit")` is False when the extension imports.
6. Full suite, lint, mypy at the pre-existing baseline; optimisation-log entry; log committed.

## Explicitly out of scope
- Native automorphism computation. The ordered-walk emitter port (a later wave). Harness changes beyond `_runs_in_python`. Any docs other than the optimisation log.

## Final message (≤ 15 lines)
STATUS; BRANCH; WORKTREE; HEAD; LOG; TESTS (counts + command); three bullets on what you built; the differential counts; the STS(13) wall-clock; the branch-collapse headline; the R2 table headline (completion per |Aut| bucket, both corpora); anything unfinished.

## Work log — mandatory (template)
[template omitted here; this file follows it]
```

## 2. Understanding and plan

**Restatement.** Make the C++ tie-complete search consult a Python
stabiliser-orbit oracle at every residual tie, so
`canonical_string(H, algorithm="canonical_orbit", backend="cpp",
orbit_oracle=PynautyOrbitOracle())` returns the frozen `w*_c` bit for bit
while exploring one representative per orbit. The value claim is the whole
point: orbit pruning is licensed by Proposition 7.3, so the pruned search must
return the *same string*, not a smaller one.

**Approach chosen.**

- A stdlib-only abstract interface `isalhg::OrbitOracleIface`
  (`include/isalhg/orbit_oracle.hpp`) with the three protocol methods, plus a
  `SearchCounters` block. `core/` computes no automorphisms; the group work
  stays in Python where `pynauty` lives.
- A nanobind adapter `PyOrbitOracle` in `bindings.cpp` holding the Python
  oracle **and the Python `SparseHypergraph` handle**. The handle is the one
  the caller passed to `canonical_string`, forwarded verbatim: `PynautyOrbitOracle`
  caches its Levi graph and its per-state generator sets under `id(H)`, so
  passing a different object would silently defeat the cache. No id mapping is
  needed — `shg_from_python` keeps the Python node/edge numbering.
- `AlgorithmVariant::GreedyMinCompleteOrbit = 9`. The oracle pointer and the
  counters ride in `WorkArena`, following the Round-12 precedent for `ranks`
  (constant for the whole walk, so they do not widen the recursive signature).
- The seed loop for the variant is forced sequential
  (`parallel = ... && orbit_oracle == nullptr`), because the persistent worker
  pool must never call into Python from more than one thread.
- A new binding `canonical_string_stats` returns `(word, counters)` for **any**
  variant, which is what makes the branch collapse measurable (unpruned vs
  pruned on the same input).

**Alternatives considered and rejected.**

- *Computing automorphisms natively in C++.* Explicitly out of scope, and it
  would put a graph-automorphism engine inside a package layer whose contract
  is stdlib-only.
- *Returning representative indices instead of values from the callback.*
  Cheaper, but the protocol returns tuples and the brief says representatives
  are used verbatim; mapping values back to indices would add a lookup whose
  only purpose is to reintroduce a choice the oracle already made.
- *Letting `nb::python_error` propagate out of the callback.* Its destructor
  touches PyObject refcounts, and the unwind path crosses `gil_scoped_release`.
  Converted to an `isalhg::IsalHGError` (message text only) while the GIL is
  still held instead.
- *Streaming the orderings to the oracle.* `enumerate_label_perms_cb` is
  callback-driven precisely to avoid materialising the permutation list
  (Round 6), but the oracle needs the list. The orbit path materialises;
  every other path keeps the streaming enumerator untouched.

**Plan as executed.** Read the Python reference and the C++ engine → header +
adapter + variant → build → smoke-test on Fano → commit → tests → lint/mypy
baseline comparison → the four measurements → optimisation-log entry → log.

**Deviations.** One existing test had to be deleted (see §3); `main` agreed.

## 3. Changes made

### Created

| File | What |
|---|---|
| `src/isalhg/core/_native/include/isalhg/orbit_oracle.hpp` | `OrbitOracleIface` (3 virtual methods) + `SearchCounters` (atomic frames / v_branches / oracle_calls / seed_oracle_calls / seeds_run) |
| `tests/unit/core/test_cpp_orbit.py` | 32 tests: frozen pins through the C++ orbit path (incl. both STS(13), slow), differentials, branch collapse, contracts |
| `.claude/notes/2026-09-07-isal-kb-w4/cpp-orbit.md` | this log |

### Modified

| File | What |
|---|---|
| `src/isalhg/core/_native/include/isalhg/canonical.hpp` | `GreedyMinCompleteOrbit = 9`; `canonical_string_compute` takes `orbit_oracle` + `counters` |
| `src/isalhg/core/_native/include/isalhg/h2s.hpp` | `greedy_h2s_str` / `greedy_h2s_tokens` take `orbit_oracle` + `counters` |
| `src/isalhg/core/_native/src/h2s.cpp` | `WorkArena.orbit_oracle` / `.counters`; frame + v_branch counters; `placed` built once per frame; edge-representative filter; materialised orderings on the orbit path only; `ranks`/`orbit_oracle` and `orbit_oracle`-without-`tie_branch` rejected |
| `src/isalhg/core/_native/src/canonical.cpp` | variant 9 dispatch, neighbour-degree seeds, seed reduction via `seed_representatives`, `tie_branch` on, forced-sequential seed loop, counters plumbed |
| `src/isalhg/core/_native/bindings.cpp` | `PyOrbitOracle` adapter; `orbit_oracle` parameter on `canonical_string`; new `canonical_string_stats` |
| `src/isalhg/core/_core.pyi` | stubs for both |
| `src/isalhg/core/canonical.py` | `CANONICAL_ORBIT_ALGORITHM: 9` in `_CPP_VARIANT_IDS`; `_python_canonical_string_orbit` / `_cpp_canonical_string_orbit` + `_CANONICAL_ORBIT_STRING_BACKENDS`; the dispatch resolves the backend normally instead of refusing `"cpp"` |
| `src/isalhg/iso_backends/orbit_oracle.py` | `backend=` on `canonical_string_orbit` / `canonical_fingerprint_orbit` |
| `experiments/tkde/budget.py` | `_runs_in_python`: `"orbit"` joins `"rank"` — Python only when the extension is missing |

### Removed

| What | Why |
|---|---|
| `tests/unit/core/test_orbit_pruning.py::TestUnhonourableRequestsRaise::test_canonical_orbit_on_the_cpp_backend_raises` | It pinned `canonical_string(algorithm="canonical_orbit", backend="cpp")` raising `ValueError("... Python backend only")` — exactly the restriction this wave removes. Flagged to `main` before deleting; `main` agreed (2026-09-07) and asked that the deletion be recorded here. Its sibling `test_oracle_on_the_cpp_backend_raises` (the low-level `greedy_h2s(backend="cpp", orbit_oracle=...)` refusal) **stays**: `greedy_h2s` was not touched and is still Python-only for the oracle. |

### Commits

| Commit | Subject |
|---|---|
| `6b09d6d` | `feat(cpp-orbit): stabiliser-orbit oracle inside the C++ tie-complete search` |
| `b02276b` | `test(cpp-orbit): pins, differential and branch collapse for the C++ orbit path` |
| `2be8776` | `docs(cpp): round 13 — the stabiliser-orbit oracle in the C++ engine` |
| `a858609` | `docs(cpp): round 13 — the R2 censored-tail measurement` |
| *(this commit)* | `docs(notes): cpp-orbit work log` |

`git diff --name-only 45ce493..a858609` lists exactly the 14 files of the three
tables above.

## 4. Tests

### Created — `tests/unit/core/test_cpp_orbit.py` (32 tests)

| Class | What it pins |
|---|---|
| `TestFrozenPinsThroughTheCppOrbitPath` | the `(length, sha256)` pins of `test_wstar_c_frozen.py` re-asserted through the C++ orbit path — Fano, STS(9), `C_13(0,1,3)`, the n=4 counterexample, GQ(2,2) (new pin), and both true STS(13) under `slow` |
| `TestDifferentialAgainstTheReferences` | C++ orbit == Python orbit == unpruned C++ on 100 random connected labelled hypergraphs (5 seeds × 20) and on stars q = 2..8; `TrivialOrbitOracle` value-neutrality (isolates plumbing from group theory); the `canonical_string_orbit` / `canonical_fingerprint_orbit` entry points on all three backend settings |
| `TestBranchCollapse` | frames strictly drop, oracle calls > 0, `seed_oracle_calls` exactly 1 pruned / 0 unpruned, and the unpruned/pruned frame **ratio grows with q** — a port that consulted the oracle at only *some* ties would still be bit-exact but would show a flat ratio |
| `TestContracts` | `ValueError` without an oracle; native `IsalHGError` for oracle-without-variant-9 and variant-9-without-oracle; `DisconnectedHypergraphError`; a Python exception raised inside a callback surfaces as `IsalHGError` |

### Created — `tests/integration/test_cpp_orbit_corpus.py` (3 tests, `integration` + `slow`)

Corpus-backed contract check: `_runs_in_python("orbit") is False`, and 25
members per collection (wd50k66, ndc_classes) with both arms driven through
`experiments.tkde.budget.engine_word` — so the harness path itself is pinned,
not just the library call. Skips without the results drive.

### Not tested, and why

- **`greedy_h2s(backend="cpp", orbit_oracle=...)`.** Still refused, and the
  existing guard test still pins the refusal. The seed reduction is a property
  of the canonical program, not of one seed run, so the per-seed entry point is
  the wrong place for the oracle — the same reasoning Round 12 applied to
  `ranks`.
- **Concurrency.** The variant's seed loop is single-threaded by construction,
  so there is no interleaving to test. What *would* need a test is a future
  change that re-enables the pool for it.
- **`k > 10` / arity > `K_MAX`.** Rejected earlier in `greedy_h2s_tokens`,
  before the oracle is reachable; unchanged by this wave.

## 5. Test results

**Full suite** — `~/.conda/envs/isalhg-cpporbit/bin/python -m pytest tests/unit
tests/property -q -m "not slow" --hypothesis-seed=0`, run against the rebuilt
extension at `sha 2be8776` + the comment fix:

```
2262 passed, 7 skipped, 41 deselected, 21 warnings in 224.52s (0:03:44)
```

No failures. The 7 skips and 21 warnings are the pre-existing ones (ABC
placeholder tests; XGI's `fast_random_hypergraph` notice; two SciPy numerical
warnings). Baseline at the base commit was 2,233 passed / 7 skipped — the 29
extra passes are this wave's new unit tests.

**Slow marker** — `pytest tests/unit/core/test_cpp_orbit.py -q -m slow`:

```
2 passed, 30 deselected in 56.93s
```

Both true STS(13) pins bit-exact through the C++ orbit path. Per-test
wall-clock: **50.35 s** (catalog system 1) and **7.35 s** (system 2).

**Integration** — `ISALHG_RESULTS_ROOT=... pytest
tests/integration/test_cpp_orbit_corpus.py -q -m "integration and slow"`:

```
3 passed in 255.15s (0:04:15)
```

Both collections reached the 25-member comparison quota with the drive mounted;
without it the module skips.

**Lint / types** — each compared against the base commit by extracting it with
`git archive` into a scratch tree and running the same three commands there:

| Check | base `45ce493` | HEAD | verdict |
|---|---|---|---|
| `ruff check src/ tests/ experiments/` | 38 errors | 38 errors | at baseline |
| `ruff format --check` | 2 would reformat (403 clean) | 2 would reformat (405 clean) | at baseline; both new files formatted |
| `mypy src/isalhg/` | 20 errors in 6 files | 20 errors in 6 files | at baseline |

The two `ruff format` offenders (`src/isalhg/generation/fidelity.py`,
`tests/unit/experiments_article/test_runner.py`) are pre-existing and outside
my ownership set.

## 6. Verification beyond unit tests

| Circumstance | What was run | Evidence | Outcome |
|---|---|---|---|
| Environment | `conda create --clone isalhg` → `isalhg-cpporbit`, then `pip install -e ".[dev]"` in the worktree | `import isalhg` resolves to `.../worktrees/agent-a23721da4d3fa93b9/src/isalhg/__init__.py` | correct tree, not the main checkout |
| Build | `pip install -e ".[dev]"` after every C++ change (3 rebuilds) | `PIP EXIT 0`, no warnings introduced | clean |
| Frozen pins, fast | `canonical_string(algorithm="canonical_orbit", backend="cpp")` vs the pinned `(len, sha256)` and vs variant 7 | Fano 0.001 s / 0.004 s · STS(9) 0.001 / 0.078 · `C_13(0,1,3)` 0.092 / 0.132 · n=4 <0.001 / <0.001 · GQ(2,2) 0.008 / 0.485 | all bit-exact |
| Frozen pins, STS(13) | same, both catalog systems | **50.42 s** and **7.37 s**, pins matched | bit-exact; the honest caveat is that rigid instances gain nothing from the oracle |
| Python-vs-C++ differential | 500 random connected labelled hypergraphs (n ≤ 8, arity ≤ 4, 3 labels/side) + 200 random stars (q = 2..9); cpp-orbit vs python-orbit vs unpruned cpp | `RANDOM n=500 cpp_mismatch=0 py_mismatch=0`; `STARS n=200 cpp_mismatch=0 py_mismatch=0`; 12.7 s | 700/700 three-way identical |
| Corpus differential | 300 wd50k66 + 300 ndc_classes members the unpruned engine completes, **both arms through `engine_word` @ 60 s** (forked child) | `wd50k66: verified=300 mismatched=0 skipped=0 median_cpp=0.001s median_orbit=0.002s`; `ndc_classes: verified=300 mismatched=0 skipped=0 median_cpp=0.001s median_orbit=0.003s` | 600/600 identical, 0 skipped |
| Harness contract | the same script printed the flags before any C++ call | `_runs_in_python('orbit') = False`, `_runs_in_python('rank') = False` | orbit now runs in C++ |
| Branch collapse | `canonical_string_stats`, `q`-star, `q = 5..10`, k = 2 | table below | collapse to a single path, string equal on every row |
| R2 censored tail | 100 highest-`\|Aut\|` censored members per corpus, orbit engine @ 60 s through `engine_word` | table below | wd50k66 0.98 overall, **1.00 at `\|Aut\| >= 1e7`** |
| Fork hygiene | both corpus scripts are separate processes that touch no C++ before the first fork; `engine_word` runs `cpp_fork_is_healthy()` itself | 0 `TkdeBudgetError`, 0 `error` rows across 1,400 forked calls | no fork poisoning |

**Branch collapse** (`q`-star, k = 2; string equal on every row):

| q | frames unpruned | frames pruned | v-branches pruned | oracle calls | ratio | secs unpruned | secs pruned |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | 326 | 6 | 5 | 4 | 54× | 0.000 | 0.000 |
| 6 | 1,957 | 7 | 6 | 5 | 280× | 0.001 | 0.000 |
| 7 | 13,700 | 8 | 7 | 6 | 1,713× | 0.004 | 0.000 |
| 8 | 109,601 | 9 | 8 | 7 | 12,178× | 0.031 | 0.000 |
| 9 | 986,410 | 10 | 9 | 8 | 98,641× | 0.284 | 0.000 |
| 10 | 9,864,101 | 11 | 10 | 9 | 896,737× | 2.833 | 0.000 |

Pruned frames are `q + 1` and pruned V branches are `q`: one branch per level,
i.e. the search has collapsed to a single path — which is what `S_q` acting on
the leaves predicts. The `q = 7` row reproduces the **Python** engine's counters
exactly (`test_orbit_pruning.py` pins 13,700 unpruned frames, 8 pruned frames,
7 pruned V branches), so the two engines consult the oracle at the same ties;
they do not merely agree on the answer.

**R2 — the censored tail.** Population: the 100 highest-`|Aut(Levi)|` members
per collection that the *unpruned* C++ engine censored at 60 s in the RQ1
campaign (`rows_m3__*`, arm `isalhg_levenshtein`, `pointer_budget_s: 60.0`),
re-run here with the C++ orbit engine at the same budget through `engine_word`.
Middle bucket is `[1e3, 1e7)`.

| Collection | `\|Aut\|` bucket | n | completed | fraction | median s |
|---|---|---:|---:|---:|---:|
| wd50k66 | `[1e3, 1e7)` | 63 | 61 | **0.97** | 0.185 |
| wd50k66 | `>= 1e7` | 37 | 37 | **1.00** | 0.003 |
| wd50k66 | all | 100 | 98 | 0.98 | 0.030 |
| ndc_classes | `< 1e3` | 95 | 45 | 0.47 | 12.855 |
| ndc_classes | `[1e3, 1e7)` | 5 | 3 | 0.60 | 0.015 |
| ndc_classes | all | 100 | 48 | 0.48 | 12.846 |

wd50k66 reproduces the article's claim and slightly exceeds it. **ndc_classes
is the counterweight and it identifies what the lever actually is.** Its
censored tail is not symmetric — the top-100 `|Aut|` runs from 1.45e6 down to
6, so 95 of 100 sit in the lowest bucket. Split by outcome:

| Collection | outcome | n | median k | median n | median m | median log10\|Aut\| |
|---|---|---:|---:|---:|---:|---:|
| wd50k66 | completed | 98 | 4 | 22 | 13 | 5.7 |
| wd50k66 | censored | 2 | 7 | 23 | 14 | 5.7 |
| ndc_classes | completed | 48 | 9 | 12 | 5 | 2.1 |
| ndc_classes | censored | 52 | 10 | 10 | 4 | 1.1 |

The ndc_classes members the oracle does not rescue are the **arity-10** ones —
exactly the Round-12 displacement tail (`k_disp` saturating at `K_MAX = 10`
against the cost-8 brute loop), which is a property of the displacement search
and carries no symmetry for an orbit oracle to exploit. Orbit pruning rescues
*symmetry*-driven censoring, not *cost*-driven censoring, and ndc_classes'
censored tail is mostly the latter. 0 errors in either corpus (every censoring
is a genuine time-out, not an exception).

## 7. Decisions, assumptions, open questions

**D1 — the Python `SparseHypergraph` handle is forwarded, not reconstructed.**
The brief allowed either. `PyOrbitOracle` stores the very object the caller
passed to `canonical_string` and hands it to every callback. Reason:
`PynautyOrbitOracle._entry` keys its cache on `id(H)` *and* checks
`hit.hypergraph is H`, so a reconstructed twin would miss on every call and
turn a memoised group lookup into a fresh `pynauty.autgrp` per tie. The cache
also pins the object's lifetime, which is what makes the `id()` key safe.

**D2 — `canonical_orbit` resolves its backend normally, so it defaults to
`"cpp"`.** The frozen contract requires `backend="cpp"` to work and the
`iso_backends` entry points to default to the extension. Rather than special-case
the default, `canonical_string` now routes `canonical_orbit` through
`resolve(backend, _CANONICAL_ORBIT_STRING_BACKENDS)` like every other variant.
Consequence: code that called `canonical_string(algorithm="canonical_orbit",
orbit_oracle=...)` with no backend previously ran the Python engine and now
runs the C++ one. The string is identical (differential below), so this is a
speed change, not a semantic one.

**D3 — a Python exception inside a callback becomes `IsalHGError`, losing its
type.** `nb::python_error` owns `PyObject` references and its destructor would
run on the GIL-free side of the unwind (the compute phase holds
`gil_scoped_release`). It is caught inside the `gil_scoped_acquire` scope,
rendered to text, and rethrown as a plain C++ error. The message is preserved;
the type is not. Tested (`test_oracle_exception_surfaces`).

**D4 — the orbit path materialises the label-respecting orderings.** Round 6
made the enumerator callback-driven to avoid the permutation list; the oracle
needs the list. Only variant 9 pays for it, and only when the list is not a
singleton. Worst case is `MAX_NEW! = 9!` rows of 9 ids (~13 MB) — the same
worst case the Python reference already carries, and unreachable in the
corpora (`j <= k-1`, and high-arity members censor on displacement cost long
before this).

**A1 — assumption, recorded.** `tests/unit/core/test_orbit_pruning.py::
TestUnhonourableRequestsRaise::test_canonical_orbit_on_the_cpp_backend_raises`
was deleted. It is in the read-only part of my ownership set, but it pins the
exact restriction the mission removes, so the mission and the ownership rule
could not both be satisfied. I messaged `main` before deleting and proceeded on
the assumption that the test is superseded; `main` confirmed and asked for the
deletion to be recorded here (§3).

**A2 — assumption, recorded.** The "members the unpruned C++ engine censors at
60 s" for the R2 table are identified from the RQ1 campaign rows
(`rows_m3__*`, arm `isalhg_levenshtein`, `pointer_budget_s: 60.0`), as the
brief permits. Those censorings were measured on Picasso, not on this
workstation, so the R2 population is "censored on the campaign hardware",
re-run here. Re-confirming each censoring locally would cost ~100 × 60 s per
corpus for a selector the brief already sanctions.

**OQ1.** The oracle is consulted at every tie and `PynautyOrbitOracle`
memoises per *state* (`tuple(placed)`), never inheriting from an ancestor —
correct, and the reason the STS(13) rows are slower than the pruning saves. A
cheap iso-invariant pre-filter that proves `G_sigma` trivial without calling
`autgrp` would remove most of that overhead. Out of scope here; it is a pure
speed question with no effect on the value.

## 8. Coordination

One exchange with `main`, both directions, recorded in §7 A1: I flagged the
one existing test that contradicts the mission's frozen contract, stated the
assumption I was proceeding on, and continued. `main` agreed with the deletion,
confirmed the sibling `greedy_h2s` guard should stay, and reminded me of the
fork-poisoning hazard (`budget.cpp_fork_is_healthy`) — never call the C++
engine in-process before forking. Both measurement scripts that use
`engine_word` are separate processes that touch no C++ before the first fork.

## 9. Deliberately not done

- **Native automorphism computation.** Out of scope, and it would put a
  graph-automorphism engine inside the stdlib-only `core/` layer.
- **The ordered-walk emitter port.** A later wave.
- **Harness changes beyond `_runs_in_python`.** `rq1.py` already registers the
  `wstar_orbit` arm through `BUDGETED_ARMS`, so nothing else needed touching.
- **A diagnostics script for the measurements.** `scripts/diagnostics/` is not
  in my ownership set; the four measurements ran from the scratchpad and their
  results are tabulated here and in the optimisation log.
- **Any doc other than `CPP_OPTIMIZATION_LOG.md`.** The article-facing R2
  number belongs to whoever writes that section; this log is where the
  measurement lives.

## 10. Risks and follow-ups

- **R1 — the default backend flip (D2) is user-visible.** Anything that
  deliberately wanted the Python orbit engine now gets the C++ one unless it
  passes `backend="python"`. Both return the same string, so the only exposure
  is a caller depending on Python-side timing or on the `stats` dict the Python
  engine can fill (the C++ engine reports through `canonical_string_stats`
  instead).
- **R2 — the oracle overhead is not free on rigid inputs.** STS(13) #1 costs
  50.4 s pruned. The pruning is a symmetric-input lever; a caller that runs it
  indiscriminately pays `autgrp` per tie for nothing. Recorded in the
  optimisation log so the article does not overclaim.
- **R3 — the counters are diagnostic, not a contract.** `canonical_string_stats`
  is not covered by the frozen pins. If a future round changes the search
  shape, the counter values move even though `w*_c` does not; the branch-collapse
  test asserts a *ratio trend*, not absolute numbers, for that reason.
- **F1 — follow-up.** OQ1: a trivial-stabiliser pre-filter to cut `autgrp`
  calls on rigid inputs.

## 11. Self-assessment against the definition of done

| # | Requirement | Status | Evidence |
|---|---|---|---|
| 1 | Frozen pins bit-exact through the C++ orbit path: Fano, STS(9), `C_13(0,1,3)`, n=4, GQ(2,2), both STS(13) (slow, wall-clock reported) | **met** | §6 rows 3–4; `TestFrozenPinsThroughTheCppOrbitPath`; STS(13) **50.4 s** / **7.4 s** |
| 2 | Differential vs Python orbit on ≥ 500 guard-satisfying random + 200 stars; vs unpruned C++ on ≥ 300 wd50k66 + 300 ndc_classes through `engine_word` | **met** | 700/700 three-way identical; 300 + 300 identical, 0 skipped, 0 errors |
| 3 | Branch collapse in C++ for stars q ∈ {5..10}: frames + oracle calls, unpruned vs pruned, counters exposed | **met** | `canonical_string_stats` binding; table in §6; q=7 matches the Python counters exactly |
| 4 | R2: 100 highest-`\|Aut\|` censored members per corpus, orbit @ 60 s, completion per bucket + median seconds, table in the log | **met** | §6 R2 table; wd50k66 **1.00** at `\|Aut\| ≥ 1e7` (median 3 ms), 0.98 overall; ndc_classes 0.48 with the mechanism identified |
| 5 | `engine_word(engine="orbit")` on the C++ path; `_runs_in_python("orbit")` False | **met** | printed by both corpus scripts; pinned by `tests/integration/test_cpp_orbit_corpus.py` |
| 6 | Full suite, lint, mypy at the pre-existing baseline; optimisation-log entry; log committed | **met** | 2,262 passed / 7 skipped; ruff 38 / format 2 / mypy 20 — each equal to the base commit measured on a `git archive` of it; Round 13 appended; this file committed last |

**One deviation from the ownership rule**, recorded in §3 and §7 A1: a single
superseded test method was deleted from a read-only test file because it pinned
the exact restriction the mission removes. Flagged to `main` first; `main`
agreed.
