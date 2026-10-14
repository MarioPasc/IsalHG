# Work log — cpp-ow

## Identity

| Field | Value |
|---|---|
| Agent | `cpp-ow` |
| Wave | `2026-09-07-isal-kb-w5` |
| Model / effort | Opus 5 (1M) @ xhigh |
| Branch | `worktree-agent-a0ea029508b5ee207` |
| Worktree | `/home/mpascual/research/code/IsalHG/.claude/worktrees/agent-a0ea029508b5ee207` |
| Base commit | `33010ad` |
| Head commit | `c6f7732` |
| Started / finished | 2026-09-07, ~13:50 → 15:50 CEST |
| Conda env | `isalhg-cppow` (clone of `isalhg`, editable install into this worktree) |
| Status | complete |

## 1. Prompt as received

```
# Task: cpp-ow — the ordered-walk emitter in the C++ extension (bit-identical to the Python emitter)

You are an implementation agent (name: `cpp-ow`) in an isolated git worktree on a branch of your own. You never see the orchestrator's conversation; everything you need is in this prompt and the repository. WAVE_ID = `2026-09-07-isal-kb-w5`. No peer; `main` is the orchestrator (SendMessage).

## Standing obligations
1. Work only inside your worktree (`git rev-parse --show-toplevel` must NOT be `/home/mpascual/research/code/IsalHG`); edit only files in your ownership set.
2. Commit all work in logical conventional commits, early and often (the plan's quota can terminate you without warning; committed work survives). End every commit message with the trailer line `Claude-Session: https://claude.ai/code/session_01F3KtB1s4dXGiNVyyaHfsix`.
3. Maintain your log at `.claude/notes/2026-09-07-isal-kb-w5/cpp-ow.md` from the first action (template below); commit it last (`docs(notes): cpp-ow work log`).
4. Never `git push`, rebase, merge, or touch other branches/worktrees or the main checkout.
5. You cannot ask the user; message `main` on ambiguity, record the assumption, keep working.
6. Report failure honestly, with evidence.

## Mission
The ordered-walk emitter `src/isalhg/core/algorithms/ordered_walk.py` (`ordered_walk(H, ranks, *, policy, k=None) -> OrderedWalkResult`; Definition 3.2 of `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/completeness/theorem_c_ordered_walk.tex`: root rule, V-key with the local signature, C-key by backward position, the **no-crossing** move rule, three policies `struct` / `rank` / `rank0`) is pure Python. The author's rule is that everything in the final article runs on the C++ engine. Port the emitter to the extension so that `ordered_walk(H, ranks, policy=..., backend="cpp")` returns a token sequence **bit-identical** to the Python emitter for every input and policy, and make the C++ path the default in the entry points. No change to the definition; the Python emitter stays as the reference.

## Read first
- The Python emitter `src/isalhg/core/algorithms/ordered_walk.py` (the spec you port; read every line), its tests `tests/unit/core/test_ordered_walk.py` (the golden `(len, sha256)` table per fixture × policy is your acceptance gate; the star-locality tests; the k-independence test), `tests/property/test_ordered_walk_roundtrip.py`, `src/isalhg/iso_backends/isal_ordered.py` (`ordered_word`, `ordered_fingerprint`, `ordered_symbols`, `POLICIES`), `src/isalhg/metric_space/distances/isal_ordered.py`, the wave-1 log `.claude/notes/2026-09-06-isal-kb-w1/ow-emitter.md` (design notes, the no-crossing rule decision), and `docs/article/D_ART3/experiments/ISAL_VARIANT_DESIGN.md` §1.
- The C++ extension: `src/isalhg/core/_native/src/{h2s,s2h,cdll,canonical}.cpp`, `include/isalhg/*.hpp` (the CDLL, token structs, `token.hpp` serialization), `bindings.cpp` and `_core.pyi` (how `canonical_string`, `canonical_string_rank` and the wave-4 orbit path are exposed — mirror their style), `CMakeLists.txt`; build notes `docs/engineering/CPP_*.md`; the wave-3/4 entries of `docs/engineering/CPP_OPTIMIZATION_LOG.md`.
- `CLAUDE.md`, `.claude/rules/coding_rules.md`.

## Ownership (exclusive write access)
- `src/isalhg/core/_native/src/ordered_walk.cpp` (new), `src/isalhg/core/_native/include/isalhg/ordered_walk.hpp` (new), `src/isalhg/core/_native/bindings.cpp`, `src/isalhg/core/_core.pyi`, `src/isalhg/core/_native/CMakeLists.txt` (or wherever the source list lives)
- `src/isalhg/core/algorithms/ordered_walk.py` — ONLY a `backend: str | None = None` parameter on `ordered_walk` dispatching to the extension when `"cpp"` (default: cpp when importable, else python — mirror `canonical_string`'s resolution), leaving the Python emitter untouched
- `src/isalhg/iso_backends/isal_ordered.py`, `src/isalhg/metric_space/distances/isal_ordered.py` — ONLY to thread `backend` through (defaults unchanged in meaning: cpp when available)
- `tests/unit/core/test_cpp_ordered_walk.py` (new), `tests/integration/test_cpp_ordered_walk_corpus.py` (new; skipped without the drive)
- `docs/engineering/CPP_OPTIMIZATION_LOG.md` — one dated entry
- `.claude/notes/2026-09-07-isal-kb-w5/cpp-ow.md`
Everything else is read-only (in particular `h2s.cpp`, `canonical.cpp`, the orbit and rank code, `test_ordered_walk.py`'s golden table — you read it, you never edit it).

## Base state
- Base commit: the head of `feature/isal-kb-word` at spawn (`33010ad` or its immediate successor; it contains the merged wave-3 rank port and wave-4 orbit port). Do not rebase.

## Frozen contracts
- `ordered_walk(H, ranks, *, policy=OrderedWalkPolicy(), k=None, backend=None) -> OrderedWalkResult` with `OrderedWalkResult(root, root_label, tokens, creation_order)` exactly as today; `backend="cpp"` and `backend="python"` return equal results (tokens as the same `Token` dataclasses, same `creation_order`).
- The C++ function receives the hypergraph, the rank vector (a permutation of `0..n-1`), the policy as two scalars (`root_rule` ∈ {hub, rank0}; `rank_first` bool) and returns the token list in the extension's existing token representation plus the root id and the creation order; the Python wrapper converts to `Token` dataclasses (or reuse the existing C++→Python token conversion used by `canonical_string`).
- Errors: `DegenerateHypergraphError` on n = 0 and `DisconnectedHypergraphError` on disconnected input, raised from the Python wrapper exactly as the Python emitter does (check connectivity where the Python emitter checks it, so both backends agree on the error).
- Tokens are independent of `k` for every `k ≥ max arity` (pinned by the Python tests); the port must keep that.

## Environment bootstrap (fresh checkout; the editable install is path-pinned — clone the env)
[bootstrap block]

## Verification commands
[verification block]

## Definition of done
1. The golden `(len, sha256)` table of `tests/unit/core/test_ordered_walk.py` reproduced through `backend="cpp"` for every fixture × policy (36 entries), asserted in your test file by importing that table.
2. Differential C++ vs Python: all conftest fixtures; ≥ 2,000 random connected labelled hypergraphs (n ≤ 10, arity ≤ 5, ≤ 3 labels per side) × 3 policies; 400 random binary stars; **all 3,988 `wd50k66` and all 1,381 `ndc_classes` members × 3 policies** (both engines are ms) — token sequences and `creation_order` identical; errors identical on n = 0 and on a disconnected input.
3. Round trip (`string_to_hypergraph` → pynauty iso) and invariance under 50 random relabellings re-pinned through the C++ path on the fixtures and 300 random instances.
4. The existing `test_ordered_walk.py` and `test_isal_ordered.py` still pass with the default backend now C++ (they exercise the public entry points), and pass with `backend="python"` forced.
5. Timing table in the log: median / p90 µs per member, C++ vs Python, on 300 members of each corpus; build time.
6. Full suite, lint, mypy at the pre-existing baseline; optimisation-log entry; log committed; tree clean.

## Explicitly out of scope
- Any change to the emitter's definition or policies. Harness code (`experiments/`). The `w*_c` engines. Docs other than the optimisation log.

## Final message (≤ 15 lines)
STATUS; BRANCH; WORKTREE; HEAD; LOG; TESTS (counts + command); three bullets on what you built; the differential counts (fixtures / random / stars / wd50k66 / ndc_classes, per policy); the timing headline; anything unfinished.
```

## 2. Understanding and plan

**Restatement.** Port the ordered-walk emitter (Definition 3.2 of
`theorem_c_ordered_walk.tex`) into the C++ extension so that
`ordered_walk(H, ranks, policy=..., backend="cpp")` returns a token sequence
*bit-identical* to the pure-Python emitter on every input and every policy, make
the C++ path the default in the public entry points, and leave the definition
and the Python reference untouched.

**Approach chosen — transcription, not reimplementation.** The Python emitter is
a sequence of Python tuple comparisons over a hand-maintained order list. Every
one of them is transcribed into an explicit three-way comparison in C++:

| Python | C++ |
|---|---|
| `max(range(n), key=(deg, label, -rank))` | `select_root`, three-field cascade; ties impossible because `-rank` is injective |
| `_key_v` structure/`by_rank` split under `rank_first` | `VKey` + `cmp_structure` + `cmp_vkey` |
| tuple comparison of variable-length fields | `cmp_seq` — element-wise, then shorter-first (Python's rule exactly) |
| `_Signature = (label, sorted (pred, arity))` | `Sig` + `cmp_sig`, sorted once per node |
| `_movement_tokens(displacement)` | `Emitter::move` — all `N` by ascending index, then all `P` |
| `_pos(slot) = (size - index_of[slot]) % size` | `Emitter::pos(v)`, same formula |
| `sorted(remaining, key=(sorted pos, edge_label))` | `std::stable_sort` over the `H.edges()` order |

**Two structural simplifications, neither of which changes a token.**
1. *Drop the CDLL.* The Python emitter keeps a `CircularDoublyLinkedList` purely
   as a slot allocator: `_slot_of` is a bijection onto the constants and the
   authoritative order is `_order`, spliced explicitly by `_insert_after_p1`; the
   CDLL itself is read only through `get_value` in the C-phase. The port indexes
   the order vector by constant directly.
2. *Skip the depth-3 BFS.* `shg_from_python` grew a `depth` parameter; the
   ordered walk passes `0`, so `SHG::finalise` builds `vertex_edges`,
   `max_arity` and `primal_adj` but not the `xi`/`eta` cache the walk never
   reads.

**Alternatives considered and rejected.**
- *Return the serialised string and re-parse it in Python.* Rejected: the
  contract is `Token` dataclasses and `creation_order`, and re-parsing would add
  a second place where the grammar could drift.
- *A native `Token` type exposed through nanobind.* Would remove the tuple
  re-hydration (now the dominant cost on small members), but forces a second
  `Token` representation on every consumer. Out of scope; recorded in §9.
- *An unguarded `from isalhg.core._core import ordered_walk`, exactly as
  `canonical.py` does.* Rejected in favour of a guarded import: the prompt's
  frozen contract says "default: cpp when importable, else python", and
  `ordered_walk.py` is the language's front door for the KB campaign — it should
  stay importable without a compiler. The *resolution* still mirrors
  `canonical_string` (a `_ORDERED_WALK_BACKENDS` dict + `backends.resolve`,
  default `"cpp"`).
- *A final tie-break on edge id in the V-phase min.* Rejected: it would deviate
  from Python's `min` over a `set`. The key is injective on valid input
  (`SparseHypergraph` forbids a duplicate `(label, member-set)`, and
  `tuple(placed_c)` + `by_rank` determine the member set), so no tie exists to
  break. Reasoning recorded in the C-phase comment.

**Plan as executed.** Read the Python emitter, its tests, the entry points and
the extension's existing FFI style → write `ordered_walk.{hpp,cpp}` and the
binding → smoke-test on Fano → 2,000-instance differential → commit → thread
`backend=` through the three entry points and the stub → write both test files →
commit → lint/mypy/full suite + timing table → optimisation log → work log.

**Deviations.** One: the first `_core.pyi` draft typed the token list as
`list[tuple]`, which mypy flagged (`type-arg`) as the single new finding over the
base commit. Fixed to `list[tuple[Any, ...]]` and re-diffed against a
`git archive` of the base tree until the two `mypy` outputs were identical.

## 3. Changes made

**Created**

| Path | What |
|---|---|
| `src/isalhg/core/_native/include/isalhg/ordered_walk.hpp` | `OwRootRule`, `OwPolicy`, `OwResult`, `ordered_walk_compute` |
| `src/isalhg/core/_native/src/ordered_walk.cpp` | the emitter: signatures, root rule, `VKey` comparison, V-phase, C-phase, no-crossing `move` |
| `tests/unit/core/test_cpp_ordered_walk.py` | golden pins through cpp, differential, error parity, round trip / invariance / k-independence on the cpp path, entry-point threading |
| `tests/integration/test_cpp_ordered_walk_corpus.py` | whole-corpus differential on `wd50k66` + `ndc_classes`, word validity, the arity-10 coverage guard |

**Modified**

| Path | What |
|---|---|
| `CMakeLists.txt` | one line: `ordered_walk.cpp` in the `nanobind_add_module` source list |
| `src/isalhg/core/_native/bindings.cpp` | `tokens_to_pylist` helper factored out of `greedy_h2s_tokens`; `shg_from_python` takes `depth`; new `_core.ordered_walk` binding (GIL released for the compute phase) |
| `src/isalhg/core/_core.pyi` | `ordered_walk` declaration; `from typing import Any` |
| `src/isalhg/core/algorithms/ordered_walk.py` | guarded `_core` import, `_python_ordered_walk` / `_cpp_ordered_walk` / `_token_from_tuple`, `_ORDERED_WALK_BACKENDS`, `backend=` on `ordered_walk`. **The `_Emitter` class, `_select_root`, `_signatures` and every ordering rule are byte-unchanged.** |
| `src/isalhg/iso_backends/isal_ordered.py` | `backend=` threaded through `ordered_word` / `ordered_fingerprint` / `ordered_symbols` |
| `src/isalhg/metric_space/distances/isal_ordered.py` | `IsalOrderedLevenshtein(policy, backend=None)`, forwarded in `fingerprint` |
| `docs/engineering/CPP_OPTIMIZATION_LOG.md` | Round 14 entry |

**Removed.** Nothing.

**Commits** (match `git diff --name-only 33010ad..HEAD`, 11 files)

| SHA | Subject |
|---|---|
| `dd890ca` | `feat(cpp): port the ordered-walk emitter to the C++ extension` |
| `e5d7070` | `test(cpp): pin the ordered-walk port against the Python emitter` |
| `c6f7732` | `docs(cpp): Round 14 — the ordered-walk emitter on the engine` |
| (this file) | `docs(notes): cpp-ow work log` |

## 4. Tests

**Created — `tests/unit/core/test_cpp_ordered_walk.py` (74 tests).**

| Class / test | Covers |
|---|---|
| `TestBackendRegistration` | `"cpp"` is registered; the no-argument default *is* the cpp result; an unknown backend raises `ValueError` |
| `test_cpp_reproduces_the_golden_pins` (36 params) | the `(len, sha256)` table of `test_ordered_walk.py`, **imported by path**, recomputed through `backend="cpp"` |
| `TestDifferential` | design fixtures, the reference file's own 2,000-instance random corpus, 400 random binary stars, and 9 shared `conftest` fixtures — tokens, creation order, root, root type, all 3 policies |
| `TestErrorParity` | `n = 0`, disconnected, malformed ranks — same exception from both backends |
| `TestRoundTripThroughTheExtension` | `S2H(w_o) ≅ H` by pynauty, design fixtures + 300 random, 3 policies |
| `TestInvarianceThroughTheExtension` | 50 random relabellings per instance, design fixtures + 300 random, 3 policies |
| `TestKIndependenceThroughTheExtension` | the word is unchanged for every `k` from `required_k(H)` to 10 |
| `TestEntryPoints` | `ordered_word` and the `d_o` distance arm agree across backends |

The golden table is *imported*, never copied: `_load_reference_module()` loads
`test_ordered_walk.py` by path, so editing a pin there fails here too and the two
files can never drift.

**Created — `tests/integration/test_cpp_ordered_walk_corpus.py` (9 tests).**
Whole-corpus differential (both collections × 3 policies), `validate()` of every
cpp word at its own `k` plus a creation-order length check, and a guard that the
arity-10 members exist and encode. Skips cleanly without `ISALHG_RESULTS_ROOT`
(verified: 9 skipped in 0.07 s).

**Not tested, and why.** The `IsalHGError` raised by the C++ V-phase when it runs
out of frontier facts is unreachable through `ordered_walk` (the wrapper's
`H.is_connected()` check precedes the dispatch), so it has no test; it exists to
keep the C++ function total if it is ever called directly. The extension's
`_core.ordered_walk` is not tested with a malformed `ranks` length either — the
wrapper rejects that first, which is the frozen contract.

## 5. Test results

**New files, fresh clean build**

```
$ python -m pytest tests/unit/core/test_cpp_ordered_walk.py \
      tests/unit/core/test_ordered_walk.py \
      tests/unit/metric_space/test_isal_ordered.py \
      tests/integration/test_cpp_ordered_walk_corpus.py -q
188 passed in 17.94s
```

**Existing ordered-walk suites on the new default (cpp)**

```
$ python -m pytest tests/unit/core/test_ordered_walk.py \
      tests/unit/metric_space/test_isal_ordered.py \
      tests/property/test_ordered_walk_roundtrip.py -q --hypothesis-seed=0
114 passed in 11.73s
```

**The same suites with the extension unregistered (Python forced)**

```
$ PYTHONPATH=<scratchpad> python -m pytest ... -p force_python_ow --hypothesis-seed=0
114 passed in 20.47s
```

The plugin does `ow._ORDERED_WALK_BACKENDS.pop("cpp", None)`; its effect was
confirmed independently — under it, `TestBackendRegistration` fails with
`ValueError: unknown backend 'cpp'; valid options: python`, so the 114 above
really did run on the Python emitter (and 20.5 s vs 11.7 s is the same 1.75×).

**Full unit + property suite**

```
$ python -m pytest tests/unit tests/property -q -m "not slow" --hypothesis-seed=0
2336 passed, 7 skipped, 41 deselected, 21 warnings in 224.92s (0:03:44)
```

**Integration suite**

```
$ ISALHG_RESULTS_ROOT=... python -m pytest tests/integration -q -m "not slow"
1 failed, 131 passed, 8 skipped, 4 deselected in 218.91s (0:03:38)

FAILED tests/integration/test_tkde_isal_arms.py::TestArmResolution
       ::test_budgeted_arms_are_the_two_unbounded_engines
E   AssertionError: assert {'isalhg_leve... 'wstar_rank'} == {'isalhg_leve...'wstar_orbit'}
E     Extra items in the left set: {'wstar_rank'}
```

**This failure is pre-existing and unrelated.** Reproduced on a `git archive` of
the base commit `33010ad` with `PYTHONPATH` pointed at the base tree:
`1 failed, 8 passed in 0.11s`, identical assertion. It asserts a constant in the
TKDE harness (`BUDGETED_ARMS`), which this task never touches; it is a leftover
from the wave-3 rank port. Reported in §10, not fixed (out of scope).

**Lint and types**

```
$ python -m ruff check src/ tests/           →  Found 3 errors.       (base: 3)
$ python -m ruff format --check src/ tests/  →  2 files would be reformatted,
                                                339 already formatted (base: 2 / 337)
$ python -m mypy src/isalhg/                 →  21 → 20 errors in 6 files (base: 20)
```

The three ruff findings and the two unformatted files are in
`iso_backends/isalhg_backend.py`, `viz/instruction_view.py`,
`generation/fidelity.py` and `tests/unit/experiments_article/test_runner.py` —
none of them touched here; the two extra "already formatted" files are the two
new test files. `mypy` initially reported 21: the extra one was mine
(`_core.pyi` bare nested `tuple`), fixed, after which the two outputs are
**byte-identical**:

```
$ diff <(mypy base-tree/src/isalhg | sort) <(mypy worktree/src/isalhg | sort)
Files are identical
```

Restricted to the files this task touched, `ruff check` reports
`All checks passed!`, `ruff format --check` reports `5 files already formatted`,
and `mypy` reports zero findings.

## 6. Verification beyond unit tests

| Circumstance | What was run | Evidence | Outcome |
|---|---|---|---|
| Golden table on the engine | 12 design fixtures × 3 policies through `backend="cpp"` | `test_cpp_reproduces_the_golden_pins`, 36 params, table imported from `test_ordered_walk.py` | 36/36 pins reproduced |
| Differential, random | 2,000 connected labelled hypergraphs (n ≤ 10, arity ≤ 5, 3 types / 3 predicates, seed 20260906) × 3 policies | standalone probe + `TestDifferential::test_random_corpus` | `{'struct': 0, 'rank': 0, 'rank0': 0}` mismatches of 6,000 |
| Differential, stars | 400 random binary stars (1–12 leaves, seed 20260907) × 3 policies | `TestDifferential::test_binary_stars` | 1,200/1,200 identical |
| Differential, fixtures | 12 design + 12 `conftest` fixtures × 3 policies | `TestDifferential` | 72/72 identical |
| Differential, `wd50k66` | **all 3,988** connected members × 3 policies | standalone probe (1.4 s) + `TestBackendsAgreeOnTheWholeCorpus` | 11,964/11,964 identical, 0 mismatches |
| Differential, `ndc_classes` | **all 1,381** connected members × 3 policies | standalone probe (0.4 s) + same class | 4,143/4,143 identical, 0 mismatches |
| Error parity | `SparseHypergraph(0)`, a 2-component input, two malformed rank vectors, on both backends | `TestErrorParity` | `DegenerateHypergraphError` / `DisconnectedHypergraphError` / `OrderedWalkError` from both |
| Round trip on the cpp path | `S2H(serialize(tokens); required_k, root_label)` vs pynauty on the coloured Levi graph — 12 fixtures + 300 random × 3 policies | `TestRoundTripThroughTheExtension` | 936/936 isomorphic |
| Invariance on the cpp path | 50 random relabellings per instance, 12 fixtures + 300 random × 3 policies | `TestInvarianceThroughTheExtension` | 46,800/46,800 fingerprints unchanged |
| k-independence on the cpp path | every `k` from `required_k(H)` to `K_MAX = 10`, 12 fixtures × 3 policies | `TestKIndependenceThroughTheExtension` | word unchanged at every `k` |
| Word validity at corpus scale | `instructions.validate` on every cpp word of both collections × 3 policies, plus `len(creation_order) == n_nodes` | `TestTheCppWordsAreWellFormed` | all pass |
| Arity-10 coverage | the `wd50k66` members at the compiled `K_MAX` | `TestTheArityTailIsCovered` | present, and both backends serialise identically |
| Fallback path | extension unregistered via a pytest plugin | §5 | default resolves to `"python"`, 114 tests pass |
| Skip path | integration file without `ISALHG_RESULTS_ROOT` | `9 skipped in 0.07s` | clean skip |

**Differential totals: 23,379 (member, policy) comparisons, 0 mismatches**, on
tokens, creation order, root and root type.

**Timing** — 300-member random sample of each collection, 20 repetitions per
member, wall clock through the public `ordered_walk` entry point (so the numbers
include the `SHG` rebuild at the FFI boundary and the re-hydration of every token
into its Python dataclass — the cost a caller actually pays, not a kernel ratio).

| Collection | policy | median µs py | median µs cpp | p90 µs py | p90 µs cpp | speedup (median) |
|---|---|---:|---:|---:|---:|---:|
| wd50k66 | struct | 53.6 | 12.6 | 168.2 | 32.7 | 4.26× |
| wd50k66 | rank | 53.4 | 12.5 | 164.2 | 33.5 | 4.27× |
| wd50k66 | rank0 | 49.9 | 12.5 | 151.1 | 34.4 | 4.00× |
| ndc_classes | struct | 53.0 | 15.0 | 78.1 | 27.5 | 3.54× |
| ndc_classes | rank | 48.7 | 16.3 | 68.0 | 28.3 | 2.99× |
| ndc_classes | rank0 | 49.2 | 15.4 | 72.8 | 27.6 | 3.19× |

The tail matters more than the median: on wd50k66 the Python p90 is 3.2× its own
median and the C++ p90 is 2.6× its own, so the gap widens exactly where the
corpus is expensive.

**Build.** `pip install -e ".[dev]"` after the two changed translation units plus
the LTO relink: **4 s**. From a deleted `build/` tree (full CMake reconfigure,
all eleven TUs): **3 s**. 24-core dev workstation, ninja, `-O3 -march=native`
with IPO. Every result in this log was produced on the fresh clean build.

**Environment.** `~/.conda/envs/isalhg-cppow` (clone of `isalhg`), editable
install pointed at this worktree — verified: `isalhg.__file__` resolves to
`.../worktrees/agent-a0ea029508b5ee207/src/isalhg/__init__.py`. The main
checkout and the `isalhg` env were never touched.

## 7. Decisions, assumptions, open questions

**D1 — the `_core` import is guarded (assumption, recorded).** The prompt's
frozen contract says the default is "cpp when importable, else python", while
`canonical.py` imports `_core` unguarded and would fail at import without a built
extension. Resolved in favour of the prompt: `try/except ImportError` at module
level, and `"cpp"` enters `_ORDERED_WALK_BACKENDS` only when the import
succeeded. The *dispatch* still mirrors `canonical_string` exactly (a per-module
backend dict + `backends.resolve`, `DEFAULT_BACKEND = "cpp"`). If the wave wants
strict symmetry with `canonical.py` instead, deleting the `try` and the
`if "cpp" not in ...` line is a two-line change.

**D2 — no edge-id tie-break in the V-phase.** Python picks `min(candidates,
key=_key_v)` over a `set`, whose iteration order is not the edge-id order, so a
genuine tie would already be ill-defined *in the reference*. It cannot occur:
`tuple(placed_c)` determines the placed member set and `by_rank` the fresh one
(both injective), and `SparseHypergraph` forbids two edges sharing a
`(label, member-set)`. The C++ scan therefore keeps the first strict minimum and
adds no tie-break. The C-phase sort is `stable_sort` over `H.edges()` order
anyway, so even the unreachable tie would resolve identically.

**D3 — `finalise(0)` for the ordered walk.** The walk reads `vertex_labels`,
`edge_labels`, `edge_members`, `vertex_edges` and `max_arity`, never `xi`/`eta`.
Passing depth 0 skips the per-vertex depth-3 BFS. `primal_adj` is still built
(`finalise` does not separate it); it costs O(Σ arity²) and was left alone rather
than restructure a file outside the ownership set.

**D4 — the `Sig` table is built once per call**, not per candidate: it is a pure
function of `H`, exactly as `_signatures(H)` is in Python.

**Open question (for the orchestrator, not blocking).** Nothing in this task
uses `_core.ordered_walk` directly; the only caller is `_cpp_ordered_walk`. If a
harness arm ever wants all three policies for one member, it currently pays the
FFI boundary three times — a `policies` vector argument would amortise it. Noted
in the optimisation log's "Not done".

## 8. Coordination

No messages sent. No ambiguity rose to the level of needing `main`: D1 was
resolvable from the prompt's own wording (the frozen contract is explicit about
the fallback), and it is recorded above with the two-line reversal if the wave
disagrees. No peer agent.

## 9. Deliberately not done

- **A native `Token` type through nanobind.** Tokens cross the boundary as
  `(kind, *fields)` tuples and are re-hydrated into the existing frozen
  dataclasses, which is now the dominant cost on small members. A native type
  would remove it but forces a second `Token` representation on every consumer —
  a package-wide design change, not a port.
- **Any change to the emitter's definition or to the three policies.** The
  golden table is the definitional record; the port had to reproduce it, not
  improve on it.
- **`experiments/` harness code.** No arm was re-pointed; they inherit the new
  default through `ordered_word` / `ordered_symbols` automatically.
- **The `w*_c` engines** (`h2s.cpp`, `canonical.cpp`, the rank and orbit paths).
  Read only.
- **The pre-existing `test_tkde_isal_arms.py` failure** (§10) — out of scope,
  and it belongs to whoever owns `BUDGETED_ARMS`.
- **Docs other than `CPP_OPTIMIZATION_LOG.md`.** The ledger, `DECISIONS.md` and
  the `D_ART3` design docs are untouched.

## 10. Risks and follow-ups

**Pre-existing failure found, not fixed (out of scope).**
`tests/integration/test_tkde_isal_arms.py::TestArmResolution::test_budgeted_arms_are_the_two_unbounded_engines`
asserts `set(BUDGETED_ARMS) == {"isalhg_levenshtein", "wstar_orbit"}` but
`BUDGETED_ARMS` also contains `"wstar_rank"`. Reproduced verbatim on a
`git archive` of the base commit `33010ad`, so it predates this branch — most
likely a leftover of the wave-3 rank port that added the arm without updating the
assertion. Someone owning the TKDE harness should decide whether the arm belongs
in `BUDGETED_ARMS` (update the test) or not (update the constant).

**Risks of this change.**
1. *A future edit to the Python emitter silently diverges from the C++ one.* The
   unit differential covers it for generated instances and the corpus file for
   real data, but nothing forces a Python-side change to touch the C++ file. The
   golden table is the real backstop: any definitional change fails 72 pins (36
   in each file) at once.
2. *The `stable_sort` in the C-phase is belt-and-braces for a tie that
   `SparseHypergraph` currently forbids.* If the no-duplicate-hyperedge invariant
   is ever relaxed, Python's `min` over a `set` in the V-phase becomes the
   ill-defined half, not the C++ scan — the fix would then belong in the
   reference, and D2 above is where to start reading.
3. *The `depth = 0` FFI shortcut is per-call-site.* Every other binding still
   passes `DEFAULT_STRUCTURAL_DEPTH`; a future binding that forgets to choose
   pays the BFS. The default argument keeps existing call sites correct.

## 11. Self-assessment against the definition of done

| # | Requirement | Status | Evidence |
|---|---|---|---|
| 1 | Golden `(len, sha256)` table reproduced through `backend="cpp"`, 36 entries, table imported | **met** | `test_cpp_reproduces_the_golden_pins`, 36 params, `_load_reference_module()` |
| 2 | Differential: fixtures; ≥ 2,000 random × 3; 400 stars; all 3,988 `wd50k66` and all 1,381 `ndc_classes` × 3; tokens + creation order; error parity | **met** | §6 table — 23,379 comparisons, 0 mismatches; `TestErrorParity` |
| 3 | Round trip (S2H → pynauty) and 50-relabelling invariance re-pinned on the cpp path, fixtures + 300 random | **met** | 936 round trips, 46,800 invariance checks, all 3 policies |
| 4 | `test_ordered_walk.py` and `test_isal_ordered.py` pass on the new default *and* with `backend="python"` forced | **met** | 114 passed both ways; the forcing plugin's effect independently confirmed |
| 5 | Timing table (median / p90 µs, 300 members of each corpus) + build time | **met** | §6 — 3.0–4.3× median; build 3 s clean / 4 s incremental |
| 6 | Full suite, lint, mypy at the pre-existing baseline; optimisation-log entry; log committed; tree clean | **met** | 2,336 passed / 7 skipped (unit + property); integration 131 passed + the 1 pre-existing failure reproduced at base; ruff 3/2 and mypy 20 byte-identical to base; Round 14 entry; this file |

One caveat stated plainly: DoD 6 says "at the pre-existing baseline", and the
integration suite's one failure *is* the pre-existing baseline — it fails
identically at `33010ad`. It is not caused by, and is not affected by, this
change.
