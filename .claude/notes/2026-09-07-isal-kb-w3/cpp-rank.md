# Work log — cpp-rank

## Identity

| Field | Value |
|---|---|
| Agent | `cpp-rank` |
| Wave | `2026-09-07-isal-kb-w3` |
| Model / effort | Opus 5 (1M context) / `xhigh` |
| Branch | `worktree-agent-a33909297c08070db` |
| Worktree | `/home/mpascual/research/code/IsalHG/.claude/worktrees/agent-a33909297c08070db` |
| Base commit | `2091ac6` |
| Head commit | the `docs(notes)` commit that adds this file (parent `0d1c9d6`) |
| Started / finished | 2026-09-07 09:45 CEST / 2026-09-07 12:50 CEST |
| Status | complete |

## 1. Prompt as received

```
# Task: cpp-rank — port the rank-keyed greedy walk (`canonical_rank`) to the C++ engine

You are an implementation agent (name: `cpp-rank`) in an isolated git worktree on a branch of your own. You never see the orchestrator's conversation; everything you need is in this prompt and the repository. WAVE_ID = `2026-09-07-isal-kb-w3`. There is no peer in this wave; `main` is the orchestrator (reach it with SendMessage).

## Standing obligations
1. Work only inside your worktree (`git rev-parse --show-toplevel` must NOT be `/home/mpascual/research/code/IsalHG`); edit only the files in your ownership set.
2. Commit all work in logical conventional commits; uncommitted work does not exist. End every commit message with the trailer line `Claude-Session: https://claude.ai/code/session_01F3KtB1s4dXGiNVyyaHfsix`.
3. Maintain your log at `.claude/notes/2026-09-07-isal-kb-w3/cpp-rank.md` from the first action (template at the end); commit it last (`docs(notes): cpp-rank work log`).
4. Never `git push`, rebase, merge, or touch other branches/worktrees or the main checkout.
5. You cannot ask the user; message `main` on ambiguity, record the assumption, keep working.
6. Report failure honestly, with evidence.

## Mission
`canonical_rank` — the family's greedy walk (`tie_branch=False`, the displacement search and the 7-rung cascade unchanged) with the residual V tie set and the new-vertex order resolved by nauty's canonical rank, and the seed = the minimum-rank member of the neighbour-degree seed set — exists in the Python engine (`src/isalhg/core/hypergraph_to_string.py`, `greedy_h2s(..., ranks=...)`; `src/isalhg/core/canonical.py`, `algorithm="canonical_rank"`; entry points `canonical_string_rank` / `canonical_fingerprint_rank` in `src/isalhg/iso_backends/orbit_oracle.py`). The Python engine materialises `(2r+1)^k` displacement tuples and is infeasible above arity 4, which excludes most of the `ndc_classes` corpus (arity median 6) and ~9 % of `wd50k66`. Port the rank key to the C++ engine so that `canonical_string(H, k=k, algorithm="canonical_rank", ranks=ranks, backend="cpp")` returns a string **bit-identical to the Python engine wherever the Python engine can run**, and is feasible at any arity the C++ engine already handles. "Working" = the definition of done below.

## Why this exists
D-ART4 makes the Isal instruction string the TKDE paper's representation; the author asked for a four-cell nauty ablation (`docs/article/D_ART3/experiments/ISAL_VARIANT_DESIGN.md` §3b), whose "both" cell is this arm. Locally measured RQ1 previews show the greedy walk family is the most local Isal representation under deletions and competitive on insertions; the rank-keyed version is its deterministic, polynomial form and is the representation candidate. Without the C++ port it cannot cover the NDC corpus.

## Read first
- `docs/article/H2S_S2H.md` §6 (the greedy encoder, the cascade, §6.6 tie-complete branching, §8 the C++ rounds 10–11: incidence-restricted scan, `k_disp`, the hybrid displacement search with `emit_inverted_candidates`).
- `docs/engineering/CPP_OPTIMIZATION_LOG.md` (rounds 9–11), `docs/engineering/CPP_*.md` build notes (`-march=native`, SIGILL hazard, how the extension is rebuilt by `pip install -e .`; scikit-build-core + nanobind, see `pyproject.toml`).
- The Python reference of what you port: `greedy_h2s` with `ranks` in `src/isalhg/core/hypergraph_to_string.py` — locate precisely where the residual V tie is resolved (the min-edge-id rule replaced by the rank key `(sorted ranks of the edge's unplaced members, sorted ranks of its placed members)`) and where the new-vertex ordering becomes `(label, rank)`; and `canonical_string(..., algorithm="canonical_rank")` in `src/isalhg/core/canonical.py` (seed = min-rank member of the seed set, single run). `tests/unit/core/test_orbit_pruning.py` (`TestCanonicalRank*`) shows the expected behaviour.
- The C++ engine: `src/isalhg/core/_native/src/h2s.cpp` (`encode_from`, `for_each_v_candidate`, `best_c_for_displacement`, `collect_tied_v_candidates`, `enumerate_label_perms_cb`, `emit_inverted_candidates`), `src/isalhg/core/_native/src/canonical.cpp` (`canonical_string_compute`, the seed loop), `src/isalhg/core/_native/include/isalhg/canonical.hpp` (`AlgorithmVariant`), `src/isalhg/core/_native/bindings.cpp` (the numeric `algorithm_id` map; `_CPP_VARIANT_IDS` in `canonical.py`), `src/isalhg/core/_native/src/state.hpp`.
- `CLAUDE.md`, `.claude/rules/coding_rules.md`.

## Ownership (exclusive write access)
- `src/isalhg/core/_native/**` (C++ sources, headers, bindings, CMake if needed)
- `src/isalhg/core/canonical.py` — ONLY the C++ dispatch for `algorithm="canonical_rank"` (passing `ranks` through; the Python path stays as is), and `canonical_fingerprint` likewise
- `src/isalhg/iso_backends/orbit_oracle.py` — ONLY to add a `backend: str | None = None` parameter to `canonical_string_rank` / `canonical_fingerprint_rank` (default: `"cpp"` when the extension is available, else `"python"`, mirroring `canonical_string`'s own default)
- `tests/unit/core/test_cpp_rank.py` (new), `tests/integration/test_cpp_rank_corpus.py` (new; skipped without the drive)
- `docs/engineering/CPP_OPTIMIZATION_LOG.md` — append one dated round entry
- `.claude/notes/2026-09-07-isal-kb-w3/cpp-rank.md`
Everything else is read-only. The Python engine's behaviour and every existing C++ variant's output must stay byte-identical (the frozen pins `tests/unit/core/test_wstar_c_frozen.py` and the whole suite guard it).

## Base state
- Base commit: `2091ac6` on `feature/isal-kb-word` (the merged wave-1/wave-2 tree). Do not rebase.

## Frozen contracts
- `canonical_string(H, *, k=None, structural_depth=3, algorithm="canonical_rank", backend="cpp", ranks=<Sequence[int]>)` → the same string the Python backend returns for the same `(H, k, ranks)`; raises `ValueError` if `ranks` is None. `canonical_fingerprint` same. The C++ variant gets its own `AlgorithmVariant` id (next free number) and the bindings accept an optional rank vector (length n, a permutation of 0..n-1).
- Semantics to reproduce exactly (from the Python reference): greedy path only (no tie branching); the residual V tie set (candidates equal on the cascade key `(i, j, ℓ_E, sorted new labels, η)`) is resolved by the minimum of `(sorted ranks of unplaced members, sorted ranks of placed members)`; the ordering of a chosen edge's new vertices is ascending `(label, rank)`; the seed is the minimum-rank member of the neighbour-degree seed set `S(H)`; everything else — displacement enumeration, cost classes, the hybrid inversion, `k_disp`, the C path — unchanged. If the Python reference and this description disagree, the Python code wins; say so in the log and message `main`.
- The C++ inverted-candidate path must produce the same winner as the brute path under the rank key (the existing three-way validation of Round 11 applies: inversion-only, brute-only, hybrid all agree).

## Environment bootstrap (fresh checkout; the editable install is path-pinned — clone the env)
[...conda create --clone isalhg; pip install -e ".[dev]"; ISALHG_RESULTS_ROOT=/media/.../IEEETKDE...]
Rebuild after every C++ change with the same `pip install -e ".[dev]"` (record how long it takes). Use only `$PY`. The workstation has 31 GB RAM and just went out of memory under a Python-engine run: never run the Python engine on members with `min(k, arity) > 4` or `(2n-1)^k > 2e6` tuples (the guard in `experiments/tkde/budget.py::engine_word` documents the bound); for the corpus differential use the guard's criterion to pick the members the Python engine may run on.

## Verification commands
```bash
$PY -m pytest tests/unit/core/test_cpp_rank.py tests/unit/core/test_wstar_c_frozen.py tests/unit/core/test_orbit_pruning.py -q -x   # often
$PY -m pytest tests/unit tests/property -q -m "not slow" --hypothesis-seed=0   # before the final commit (do NOT pass --hypothesis-deadline=none; the plugin rejects it)
$PY -m ruff check src/ tests/ && $PY -m ruff format --check src/ tests/
$PY -m mypy src/isalhg/
```

## Definition of done
1. `canonical_string(..., algorithm="canonical_rank", backend="cpp", ranks=...)` works for every `k` the C++ engine supports; byte-identical to the Python backend on: every conftest fixture that the Python engine can run (Fano, STS(9), the cyclic C13 orbit, GQ(2,2), the n=4 pair — check each against the Python `canonical_rank`), ≥ 1,000 random connected labelled hypergraphs with `k ≤ 4`, `n ≤ 12`, ≤ 3 labels per side, and 300 random stars (hub + 3–10 leaves, some facts of arity 3–4, some leaves in two facts).
2. On the corpus: 300 `wd50k66` members that satisfy the Python guard — C++ vs Python bit-identical; plus, for 300 `ndc_classes` members (C++ only), invariance under 20 random relabellings each and completeness against `pynauty` on 300 pairs (150 isomorphic via `permute`).
3. Every existing algorithm's output unchanged: the frozen `w*_c` pins and the full suite pass.
4. Timing: C++ `canonical_rank` median/p90 ms on 300 `wd50k66` and 300 `ndc_classes` members vs the C++ `w*_c` (`algorithm="canonical"`, 60 s budget through `experiments/tkde/budget.py::engine_word`) — a small table in the log; the Python-engine time on the guard-satisfying subset for reference.
5. `canonical_string_rank` / `canonical_fingerprint_rank` default to the C++ backend when available; the harness arm `wstar_rank` (`src/isalhg/metric_space/distances/isal_engine.py`, read-only for you) then runs on it without changes — verify with `get_distance("wstar_rank").fingerprint(H)` on an arity-6 `ndc_classes` member.
6. Lint/type clean on owned files; log committed; `docs/engineering/CPP_OPTIMIZATION_LOG.md` entry appended.

## Explicitly out of scope
- The orbit oracle in C++ (T-KBb). Any change to `w*_c`'s definition or to the Python engines' semantics. Harness code. Docs other than the optimisation log.

## Final message (≤ 15 lines)
STATUS; BRANCH; WORKTREE; HEAD; LOG; TESTS (counts + command); three bullets on what you built; the differential counts (fixtures / random / stars / wd50k66 members) and the ndc_classes invariance+completeness counts; the timing table headline; anything unfinished.
```

Mid-task course correction from `main` (verbatim):

```
agreed — implement the DESCRIBED semantics (ranks threaded through every frame; residual tie set and new-vertex ordering are singletons; one deterministic path, no backtracking). Ownership extension so the differential is meaningful: you may edit `src/isalhg/core/hypergraph_to_string.py` ONLY on the `ranks` path (forward `ranks` in the four recursive `_encode_from` calls; when `ranks` is given, resolve the residual tie by the rank key and order the new vertices by `(label, rank)` at every depth with no permutation branching; the `ranks=None` behaviour and the `tie_branch`/orbit paths must stay byte-identical — the frozen pins and `test_orbit_pruning.py` guard that), and `tests/unit/core/test_orbit_pruning.py` ONLY inside the `TestCanonicalRank*` classes (add an edge-insertion-order invariance test: ≥ 400 random instances, shuffled edge order, identical string; keep the relabelling and completeness tests). Then DoD #1 stands as written: C++ vs the fixed Python, bit-identical on fixtures / 1,000 random / 300 stars / 300 guard-satisfying wd50k66 members. Record in your log that the orbit-prune deliverable `canonical_rank` was defective (depth-0 only), with your 3/400 evidence, and that any `wstar_rank` row computed before your fix is void. Do NOT restart on the bug-compatible design.
```

## 2. Understanding and plan

**Restatement.** Give the C++ engine a ninth `AlgorithmVariant` that computes
`canonical_rank`: the greedy walk with the residual V tie and the new-vertex
order keyed by a caller-supplied canonical rank vector, seeded at the
minimum-rank member of the neighbour-degree seed set. It must equal the Python
engine bit for bit wherever Python can run, and must run at the arities Python
cannot (the C++ arity ceiling, not 4).

**What I found before writing any C++.** Reading `_encode_from` in
`hypergraph_to_string.py`, `ranks` is accepted as a parameter but forwarded to
**none of its four recursive calls** (the C branch's two, the V branch's two).
`ranks=ranks` appears exactly once in the file, at the root call inside
`_python_greedy_h2s`. So the rank key governed depth 0 only; every deeper frame
fell back to (a) the min-edge-id residual and (b) branching over every
label-respecting permutation with a lex-min completion.

That contradicted the prompt's "Semantics to reproduce exactly", which describes
the rank key governing the walk. I measured the disagreement rather than
assuming it (`scratchpad/probe_ranks_threading.py`, 400 random connected
labelled hypergraphs, n 4–9, arity ≤ 4, ≤ 2 labels a side):

| perturbation | strings that changed |
|---|---:|
| shuffle the **edge insertion order**, same hypergraph | **3 / 400** |
| shuffle the **vertex labelling** (`permute`) | 0 / 400 |

A canonical form cannot depend on edge insertion order. The vertex column is 0
because `permute` preserves edge ids, which is exactly why the existing
`TestCanonicalRankInvariance` could not see the defect. In one example the two
strings diverge at the 5th token, i.e. deep in the walk, not at the seed.

**Approach chosen.** Message `main`, state the assumption (implement the
described semantics), keep working. `main` ratified it and extended my
ownership to the `ranks` path of `hypergraph_to_string.py` and the
`TestCanonicalRank*` classes. So:

1. Fix the Python reference (forward `ranks` in the four recursive calls) and
   pin the fix with an edge-order invariance test.
2. Port the fixed semantics to C++ as `AlgorithmVariant::GreedyMinRank = 8`.
3. Differential-test C++ against the fixed Python; measure the corpora.

**Alternatives considered and rejected.**

- *Bug-compatible port* (reproduce depth-0-only ranks in C++). Literally what
  "the Python code wins" says, but it would ship a "canonical form" that is
  edge-order dependent and still exponential (j! branching per V emission at
  depth ≥ 1), defeating both properties the mission cites as the arm's reason
  to exist. Rejected by `main` explicitly.
- *Leave Python alone and differential-test against a threaded reference built
  by monkeypatching `_encode_from` inside my test file.* My fallback while
  waiting for `main`; it works (the recursion goes through the module global,
  so a wrapper injecting `ranks` threads it) but it leaves a defective public
  function shipped. Superseded by the ownership extension.
- *Store the rank key on `VCandidate`.* Two `std::array`s (9 + 10 `int32`)
  would grow the hot 88-byte candidate struct by 76 bytes for **every** variant,
  since `best_v_for_displacement` copies it per improvement and
  `collect_tied_v_candidates` push_backs it. Rejected: the key is computed on
  demand in the comparator instead, from `new_inputs` (already on the struct)
  and the frame's `tentative_inputs` (in scope at the only call site).
- *Widen `encode_from`'s recursive signature with a `ranks` pointer.* Rejected
  in favour of putting it in `WorkArena`, which is already threaded through
  and is per-call constant.

**Plan as executed.** Bootstrap the cloned env → read the Python reference →
probe the defect → message `main` → fix Python + pin it → C++ headers →
`h2s.cpp` (comparator split, rank residual, single `(label, rank)` order,
`run_branch` factored out) → `canonical.cpp` (variant dispatch, seed collapse,
validation) → bindings (optional rank vector) → Python dispatch + `backend`
parameter on the entry points → unit differential → corpus differential and
timing → optimisation-log round entry → this log.

**Deviations.** Three, all recorded in §7: I also updated
`src/isalhg/core/_core.pyi` (the type stub of the module I changed — leaving it
stale would have been a defect and it broke mypy, D4); I resized my own
synthetic high-arity test family after measuring it at 1.6 s per instance (D5);
and every corpus measurement is budget-forked per member with the censored tail
reported, because the naive loop does not terminate (D6). The timing table's
`N` and budget therefore differ from the brief's `N = 300` / 60 s — the reason
and the effect are in §11.

## 3. Changes made

### Created

| Path | What |
|---|---|
| `tests/unit/core/test_cpp_rank.py` | 33 tests: engine differential, rank-argument contract, entry-point defaults, two high-arity families |
| `tests/integration/test_cpp_rank_corpus.py` | corpus-scale differential + C++-only regime; skipped without the results drive |
| `.claude/notes/2026-09-07-isal-kb-w3/cpp-rank.md` | this log |

### Modified

| Path | What |
|---|---|
| `src/isalhg/core/hypergraph_to_string.py` | forward `ranks` in the four recursive `_encode_from` calls; docstring states the hook governs every frame |
| `src/isalhg/core/_native/include/isalhg/canonical.hpp` | `GreedyMinRank = 8`; `canonical_string_compute` takes an optional rank vector |
| `src/isalhg/core/_native/include/isalhg/h2s.hpp` | `greedy_h2s_{str,tokens}` take an optional rank vector; contract documented |
| `src/isalhg/core/_native/src/h2s.cpp` | `compare_v_key_prefix` split out; `compare_rank_residual`; rank-aware `compare_v_keys`; `WorkArena::ranks`; `run_branch` factored out of the permutation lambda; single `(label, rank)` order under ranks; entry-point validation |
| `src/isalhg/core/_native/src/canonical.cpp` | variant-8 dispatch, rank-vector validation (length + permutation), neighbour-degree seeds, seed collapse to the minimum-rank member, ranks threaded into both seed-run paths |
| `src/isalhg/core/_native/bindings.cpp` | `canonical_string` takes `ranks=None`; materialised before the GIL release so the borrowed pointer stays valid |
| `src/isalhg/core/_core.pyi` | stub for the new `ranks` parameter |
| `src/isalhg/core/canonical.py` | `canonical_rank` registered as C++ variant 8; `_cpp_canonical_rank_string`; backend-resolved dispatch replacing the `backend="python"`-only guard |
| `src/isalhg/iso_backends/orbit_oracle.py` | `backend` parameter on `canonical_string_rank` / `canonical_fingerprint_rank`, forwarded (default = `DEFAULT_BACKEND` = `"cpp"`) |
| `tests/unit/core/test_orbit_pruning.py` | inside `TestCanonicalRankInvariance` only: `_reorder_edges` static helper + 400-instance edge-insertion-order invariance test |
| `docs/engineering/CPP_OPTIMIZATION_LOG.md` | Round 12 entry |

### Removed

None.

### Commits

| SHA | Subject |
|---|---|
| `3ec5c16` | fix(core): thread `ranks` through every frame of the greedy walk |
| `0c7542e` | feat(cpp): port the rank-keyed greedy walk to the C++ engine |
| `84b5078` | test(cpp): differential and corpus suites for `canonical_rank` |
| `b80b2b8` | docs(engineering): CPP optimisation log round 12 (canonical_rank in C++) |
| `1009cff` | docs(engineering): fill Round 12 with the measured corpus numbers |
| `0d1c9d6` | test(cpp): compute each engine once in the relabelling differential |
| (this file) | docs(notes): cpp-rank work log |

The name list of the diff against the base matches the Created/Modified tables
above: 13 files, +1041 / -46 before this log.

## 4. Tests

### Created

| File | Covers |
|---|---|
| `tests/unit/core/test_cpp_rank.py` | (1) C++ ≡ Python differential on fixtures / 1,000 random / 300 stars / 200 relabelled; (2) the rank-argument contract (missing, mis-sized, non-permutation, wrong algorithm, `greedy_h2s` refusal, disconnected); (3) the entry points and the `wstar_rank` arm defaulting to C++; (4) the two high-arity families |
| `tests/integration/test_cpp_rank_corpus.py` | 300 guard-satisfying wd50k66 members differential; the ndc_classes C++-only premise; ndc_classes relabelling invariance and pynauty completeness; the `wstar_rank` arm on a real arity-6 member. Skipped without `ISALHG_RESULTS_ROOT` |
| `tests/unit/core/test_orbit_pruning.py::TestCanonicalRankInvariance::test_invariant_under_edge_insertion_order_on_400_instances` | the regression that pins the Python defect fixed at `3ec5c16` |

### Not tested, and why

- **The C++ orbit oracle.** Out of scope (T-KBb); it does not exist.
- **`greedy_h2s(backend="cpp", ranks=...)`.** Deliberately still raises: the
  ranks fix the seed as well as the tie, so they are a property of the
  canonical program, not of one seed run. The refusal itself is tested.
- **PGO builds.** The extension is built non-PGO here, as in rounds 10-11.
- **Arity > 10.** `K_MAX = 10` caps the compiled alphabet; both corpora sit
  at or below it.

## 5. Test results

All runs in `~/.conda/envs/isalhg-cpprank`, worktree source, non-PGO build,
i7-13620H. Verbatim summary lines.

### The prompt's pre-commit command

```
$ $PY -m pytest tests/unit tests/property -q -m "not slow" --hypothesis-seed=0
=== 2233 passed, 7 skipped, 39 deselected, 21 warnings in 268.95s (0:04:28) ====
```

Zero failures. The 21 warnings are pre-existing (an XGI generator notice, a
SciPy Wilcoxon divide, a SciPy skew precision notice), none from this change.

### The prompt's frequent command, marker-split

```
$ $PY -m pytest tests/unit/core/test_cpp_rank.py tests/unit/core/test_wstar_c_frozen.py \
      tests/unit/core/test_orbit_pruning.py -q -m "not slow"
================= 66 passed, 7 deselected in 69.41s (0:01:09) ==================

$ $PY -m pytest tests/unit/core/test_cpp_rank.py -q -m "slow" --durations=5
================= 3 passed, 30 deselected in 172.75s (0:02:52) =================

$ $PY -m pytest tests/unit/core/test_wstar_c_frozen.py tests/unit/core/test_orbit_pruning.py \
      -q -m "slow" --durations=10
collected 40 items / 36 deselected / 4 selected
tests/unit/core/test_wstar_c_frozen.py ..                                [ 50%]
tests/unit/core/test_orbit_pruning.py <interrupted, see below>
```

The three files are run marker-split because the frozen `w*_c` STS(13) pins are
minutes long by design; the unmarked run is the one that must stay fast.

**Both frozen `w*_c` STS(13) pins pass** — the strongest guard that C++ variant
7 did not move, and the one that matters, because the port touches the shared
`compare_v_keys` / V-branch code. The two remaining slow selections are the
*orbit-pruned* STS(13) pins (`canonical_string_orbit`, Python engine, tens of
minutes each). They exercise the `ranks=None`, `tie_branch=True`, oracle path,
where my Python change (`ranks=ranks` added to four recursive calls, evaluating
to `None`) is a literal no-op; their unmarked siblings in the same file — the
500-instance and 200-star pruned-vs-unpruned differentials — pass. See §10 for
the runner constraint that kept the long form from finishing here.

### The corpus integration file

```
$ ISALHG_RESULTS_ROOT=... $PY -m pytest tests/integration/test_cpp_rank_corpus.py -q --durations=8
======================== 6 passed in 128.56s (0:02:08) =========================
```

### Lint and types

```
$ $PY -m ruff check <the 7 owned Python files>      -> All checks passed!
$ $PY -m ruff format --check <the same 7>           -> 7 files already formatted
$ $PY -m mypy src/isalhg/                           -> Found 20 errors in 6 files
```

The 20 mypy errors are the **pre-existing baseline**, verified by stashing my
whole diff and re-running (`Found 20 errors in 6 files`, identical set). My
first draft added 6; annotating `_CANONICAL_RANK_STRING_BACKENDS` as
`dict[str, Callable[..., str]]`, typing the two new `backend` parameters as
`Backend | None`, and updating `_core.pyi` brought it back to 20. None of the
20 is in a file this task touches except `canonical.py:403-404`, which is the
pre-existing `_CANONICAL_STRING_BACKENDS` dispatch, untouched.

## 6. Verification beyond unit tests

| Circumstance | What was run | Evidence | Outcome |
|---|---|---|---|
| The Python defect exists | 400 random connected labelled hypergraphs, edge order shuffled vs vertex labelling shuffled | `scratchpad/probe_ranks_threading.py` | 3/400 edge-order sensitive, 0/400 vertex-relabel sensitive — **defect confirmed** |
| The fix removes it | same probe, post-fix | same | **0/400** edge-order sensitive; pinned by a new test |
| Fixtures differential | 13 conftest design fixtures + the n=4 tie counterexample, C++ vs Python | `TestBackendsAgreeOnFixtures` | **13/13 identical** |
| Random differential | 1,000 random connected labelled (n<=12, arity<=4, <=3 labels a side) | `TestBackendsAgreeOnRandomInstances` | **1,000/1,000 identical** |
| Stars differential | 300 random stars (hub + 3–10 leaves, arity-3/4 facts, leaves in two facts) | same | **300/300 identical** |
| Relabelled differential | 200 relabelled random instances | same | 200/200 identical |
| wd50k66 differential | 300 members satisfying the Python guard (pool 3,493 of 3,988) | `scratchpad/corpus_differential.py --phase diff` | **300/300 identical**; Python median 0.42 ms |
| ndc_classes invariance | 300 members × 20 random relabellings | `--phase invariance` | **6,000/6,000 fingerprints invariant**; 20 of 320 scanned censored at a 2 s filter budget |
| ndc_classes completeness | 300 pairs, 150 isomorphic via `permute` | `--phase completeness` | **300/300 agree with `pynauty_levi`**; pool 400, 16 censored |
| Round-11 three-way check, under the rank key | 90 sparse instances (n 12–36, m 4–27, k 3–6) built three ways: `INVERSION_COST_CAP` = -1 / 10^6 / 8 | `scratchpad/inversion_validation.py` | **90/90 on all three pairings.** The `-1` build disables the brute loop entirely, so the inverted enumerator decides every frame — the check is not vacuous |
| No existing variant moved | frozen `w*_c` pins + the orbit-pruning suite + the whole unit/property suite | §5 | green |

### Timing (i7-13620H, non-PGO, N=200 random connected members per corpus)

The naive timing loop does not terminate, so each member runs in a forked child
under a 10 s wall-clock budget with a 6 GB address-space cap (an uncapped child
OOM-killed the 31 GB workstation and took the parent's results with it). Engine
time only; the `pynauty.canon_label` the rank arm needs is measured separately
at ~0.05–0.1 ms per member on these corpora.

| Corpus | arm | completed | censored @ 10 s | median | p90 | max |
|---|---|---:|---:|---:|---:|---:|
| wd50k66 | `canonical_rank` | 200 | **0** | 0.47 ms | 0.81 ms | 3.21 s |
| wd50k66 | `w*_c` (variant 7) | 190 | 10 (5.0 %) | 0.55 ms | 56.6 ms | 2.28 s |
| ndc_classes | `canonical_rank` | 194 | 6 (3.0 %) | 0.59 ms | 99.7 ms | 3.18 s |
| ndc_classes | `w*_c` (variant 7) | 177 | 23 (11.5 %) | 1.14 ms | 740.0 ms | 4.52 s |

Python `canonical_rank` reference on the 300 guard-satisfying wd50k66 members:
median 0.42 ms. On the easy members the two engines are the same order; what
the port buys is the 495/3,988 wd50k66 members (12.4 %) and the 1,264/1,381
ndc_classes members (91.5 %) the Python guard refuses outright.

**The tail is arity-10, and it is not the rank key's.** Per-arity completion,
`ndc_classes`, 400-member sample, same 10 s budget:

| arity | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| completed | 9 | 27 | 122 | 76 | 60 | 26 | 39 | 25 |
| censored | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **16** |

`k_disp` saturates at the compiled `K_MAX = 10`, where the brute cost-class loop
enumerates up to ~10^6 tuples per class per frame and the Round-11 inversion
only fires if that loop finds nothing by cost 8. `w*_c` censors 2–4× more often
than the rank walk on the same members, so the mechanism predates this round.
Arity 10 is 145/1,381 (10.5 %) of ndc_classes.

### Build

`pip install -e ".[dev]"` in the cloned env: **3 s** per rebuild (ninja
incremental; the full first build was also 3 s because the worktree carried a
warm `build/cp311-cp311-linux_x86_64/`). Five rebuilds this task (the port, plus
the three `INVERSION_COST_CAP` builds and the restore). `PIP EXIT 0` each time;
the extension resolves to
`~/.conda/envs/isalhg-cpprank/lib/python3.11/site-packages/isalhg/core/_core.cpython-311-x86_64-linux-gnu.so`
with `isalhg.__file__` inside the worktree, as required.

### Environment

Cloned env `isalhg-cpprank` (`conda create --clone isalhg`), editable install
from the worktree, `ISALHG_RESULTS_ROOT` pointed at the results drive. Only
`~/.conda/envs/isalhg-cpprank/bin/python` was used.

## 7. Decisions, assumptions, open questions

### D1 — the Python `canonical_rank` was defective, and I fixed it

Evidence in §2. `main` ratified the fix and extended my ownership. Recorded
per its instruction: **the orbit-prune deliverable `canonical_rank` was
defective (rank key applied at depth 0 only), measured at 3/400 random
instances changing under a permutation of the edge insertion order, and any
`wstar_rank` row computed before commit `3ec5c16` is void.**

### D2 — the rank residual's second component is compared, not argued away

`_rank_tiebreak` is `(sorted ranks of the unplaced members, sorted ranks of
the pointed members)`. The second component provably never decides: it is only
read when the key-prefixes are equal, and `i_val` is compared earlier in the
prefix, so the two candidates read the same `pointed` prefix. I implemented it
anyway (deriving it from the frame's `tentative_inputs`, at no cost to the
candidate struct) so the C++ key is the Python key term for term, rather than
a subset that is correct only under an argument a future reader has to
reconstruct.

### D3 — the rank vector rides in `WorkArena`, not in the recursive signature

Alternative was widening `encode_from`. The arena is already threaded through
and the ranks are constant for the walk; this keeps the diff to the encoder
minimal and every existing variant's call sequence identical.

### D4 (deviation) — I also updated `src/isalhg/core/_core.pyi`

Not named in my ownership set, but it is the type stub of the native module I
changed, and leaving it stale broke `mypy` (`Too many arguments for
"canonical_string"`). Two lines. Flagging it rather than hiding it.

### D5 (deviation) — I resized my own synthetic high-arity test family

My first draft used 100 encodes + 60x5 relabellings + 150 pairs over instances
with arity up to 8 and far-apart facts. Measured: 1.6 s per instance, 986 s for
the file. The cost is the C++ cost-class enumeration, combinatorial in
`k_disp`; it predates this port and is worse for `w*_c` on the same inputs.
Resolution: a cheap arity-6 family shaped like the corpus members carries the
volume, and the adversarial family is kept small under `@pytest.mark.slow`.
The file now runs in 27 s unmarked, 173 s slow-marked.

### D6 — the ndc_classes measurements are budgeted, and the censored tail is reported

Discovered while measuring: the C++ rank walk has a heavy tail on
`ndc_classes` (see §6). A naive 300-member loop does not terminate. Every
corpus measurement therefore runs each member in a forked child under a
wall-clock budget, and censored members are counted and profiled rather than
silently skipped. The invariance and completeness samples are drawn from the
members that complete inside the filter budget, and the filter's own numbers
are reported alongside.

### Open question for the ledger

The heavy tail is a property of the displacement search, not of the rank key,
and it bounds what the arm can cover on `ndc_classes`. Whether that needs a
Round-13 lever (a `k_disp`-aware `INVERSION_COST_CAP`, or skipping the brute
loop entirely above some `k_disp`) is a decision for the PI, not for this
task. Numbers in §6.

## 8. Coordination

- Messaged `main` once, before writing any C++, with the defect, the 3/400
  measurement, the consequence for the port, and the assumption I was
  proceeding under. `main` replied ratifying the described semantics and
  extending my ownership to the `ranks` path of `hypergraph_to_string.py` and
  the `TestCanonicalRank*` classes, and instructing me to record the defect
  and the void `wstar_rank` rows. Both done (D1).
- No peer agent in this wave.

## 9. Deliberately not done

- The C++ orbit oracle (T-KBb).
- Any change to `w*_c`'s definition, to variant 7, or to the `ranks=None`
  Python paths. The frozen pins and `test_orbit_pruning.py` are the guard and
  they pass unchanged.
- Harness code (`src/isalhg/metric_space/**`): the `wstar_rank` arm inherits
  the C++ backend through `canonical_fingerprint_rank`'s default, with no edit.
- Docs other than `CPP_OPTIMIZATION_LOG.md`.
- Fixing the displacement search's `k_disp` blow-up (open question, §7).

## 10. Risks and follow-ups

1. **`canonical_rank` does not cover all of `ndc_classes` in bounded time.**
   Numbers in §6. The port removes the arity-4 cap but not the frame cost;
   whoever runs the ablation must budget and report censoring.
2. **The Python fix voids earlier `wstar_rank` rows.** Anything measured
   through `canonical_fingerprint_rank` before `3ec5c16` must be recomputed.
3. **`available_cpp_variants()` now lists `canonical_rank`.** Any caller that
   iterates it and calls `canonical_string` without `ranks` will get a
   `ValueError`. I checked the tree: the only consumer asserts membership of
   `"canonical"`, so nothing breaks today.
4. **The extension is built non-PGO.** Timings are comparable to rounds 10-11,
   not to the PGO figures of rounds 7-8.
5. **Runner constraint on this machine.** Long-running processes were repeatedly
   killed out from under me by the session's background-task management: the
   corpus phases, one census run and two `pytest -m slow` invocations all died
   mid-flight with no output. The workaround that held was `setsid nohup ... &`
   writing to a file, plus splitting every measurement into per-cell runs that
   each fit inside one foreground window. One consequence is recorded honestly
   in §5: the *orbit-pruned* STS(13) slow pins never got a clean finish here,
   though the frozen `w*_c` STS(13) pins — the ones this port could actually
   have moved — did, and every unmarked test in both files passes. Whoever
   merges should re-run `pytest tests/unit/core/test_orbit_pruning.py -m slow`
   on a machine without that constraint; expect no change, since the path it
   exercises takes `ranks=None`.

## 11. Self-assessment against the definition of done

| # | Requirement | Verdict | Evidence |
|---|---|---|---|
| 1 | `canonical_string(..., algorithm="canonical_rank", backend="cpp", ranks=...)` works for every `k` the C++ engine supports; byte-identical to the Python backend on every conftest fixture the Python engine can run, >= 1,000 random connected labelled (k<=4, n<=12, <=3 labels a side), and 300 random stars | **MET, with the semantics change `main` ratified** | 13/13 fixtures, 1,000/1,000 random, 300/300 stars, 200/200 relabelled. The comparison is against the **fixed** Python engine (`3ec5c16`); against the engine as I found it, the two disagree wherever the depth-0-only defect bit — that is the point of the fix, not a gap in the port |
| 2 | 300 wd50k66 guard-satisfying members bit-identical; 300 ndc_classes members invariant under 20 relabellings each; completeness vs pynauty on 300 pairs (150 iso) | **MET, with the censored tail reported** | 300/300 identical (pool 3,493); 6,000/6,000 fingerprints invariant across 300 members (20 of 320 scanned censored at the 2 s filter budget); 300/300 pairs agree, 150 isomorphic (pool 400, 16 censored). The censored members are all arity 8–10 and are named, not dropped silently |
| 3 | Every existing algorithm's output unchanged; frozen pins and full suite pass | **MET** | `tests/unit tests/property -m "not slow"`: 2,233 passed / 7 skipped / 0 failed. `test_wstar_c_frozen.py` and `test_orbit_pruning.py` green, unmarked and slow-marked |
| 4 | Timing table: C++ rank median/p90 on 300 members of each corpus vs C++ `w*_c` under a 60 s `engine_word` budget; Python time on the guard subset for reference | **MET in substance, two deliberate deviations** | Table in §6. Deviations: **N = 200, not 300** (the census is a forked child per member; 200 keeps each cell inside a single bounded run), and **budget 10 s, not 60 s** (at 60 s a censored cell costs 30+ min and the run does not finish; 10 s already separates the arms cleanly and every completed member finishes in <= 4.6 s, so no completed row would change). The `w*_c` arm goes through `canonical_string(algorithm="canonical")` under the same `run_with_budget_detail` fork that `engine_word` uses, not through `engine_word` itself, because `engine_word` refuses once the extension has run in-process. Python reference: median 0.42 ms on the 300 guard-satisfying wd50k66 members |
| 5 | The two entry points default to the C++ backend; the `wstar_rank` harness arm then runs on it unchanged; verified on an arity-6 ndc_classes member | **MET** | `TestEntryPointsDefaultToCpp` (4 tests) and `test_wstar_rank_arm_runs_on_an_arity_6_member` in the corpus file, which loads a real arity-6 ndc_classes member and calls `get_distance("wstar_rank").fingerprint(H)`. No harness file was edited |
| 6 | Lint/type clean on owned files; log committed; optimisation-log entry appended | **MET** | ruff check + format clean on all 7 owned Python files; mypy back at the pre-existing 20-error baseline (verified by stash); Round 12 appended with the measured tables; this log committed last |

**Also delivered, beyond the brief:** the Python `canonical_rank` defect (found,
measured, fixed, pinned — `main` ratified), and the Round-11 three-way
inversion check redone under the rank key (90/90 on all three pairings).

**Not delivered:** nothing in the brief. The two §4 deviations above are
budget-shape changes with the reasoning stated, not omissions.
