# C++ Optimization Log

Self-paced optimization rounds beyond the initial Phase 0–5 port. Each
row reports best-of-N timing of ``canonical_string`` (in ms, single
machine, i7-13620H, 16 threads, conda env ``isalhg``). Speedups are
quoted against the **post-restructure** baseline (round 0 below); the
"vs Python" column quotes against the pure-Python reference in
``analysis_full/cells.csv``.

## Round 0 — Post-restructure baseline (best-of-5)

| Design | greedy_min | greedy_single |
|---|---:|---:|
| Fano STS(7)    |   5.91 ms |   0.83 ms |
| STS(9) AG(2,3) |  44.17 ms |   4.92 ms |
| STS(13) cyclic | 353.46 ms |  24.83 ms |
| GQ(2,2) doily  | 654.90 ms |  43.73 ms |

## Round 1 — V-branch prefix shortcut

**Change.** In ``_native/src/h2s.cpp``, the V-branch recursion compared
``best_prefix + sub_completion`` against the running best. Since
``best_prefix`` is identical across all permutations of a single V
emission, the comparison is determined by ``sub_completion`` alone.
Eliminate the per-permutation prefix copy and compare only the
sub-completion vector; prepend the prefix once at the end.

**Result.** ~0.5–2 % win — modest because the prefix is short (≤10
tokens for our designs).

| Design | greedy_min | Δ vs round 0 |
|---|---:|---:|
| Fano        |   5.78 ms | −2.2 % |
| STS9        |  43.70 ms | −1.1 % |
| STS13       | 351.26 ms | −0.6 % |
| Doily       | 646.54 ms | −1.3 % |

## Round 2 — IPO/LTO + ``-funroll-loops``

**Change.** ``CMakeLists.txt`` enables ``CMAKE_INTERPROCEDURAL_OPTIMIZATION``
(LTO) plus ``-funroll-loops -fno-plt`` in Release builds. No source
edits.

**Result.** Consistent 2–5 % gain across the table.

| Design | greedy_min | Δ vs round 1 |
|---|---:|---:|
| Fano        |   5.67 ms | −1.9 % |
| STS9        |  41.71 ms | −4.6 % |
| STS13       | 338.20 ms | −3.7 % |
| Doily       | 620.96 ms | −4.0 % |

## Round 3 — Parallel seed loop (std::async + GIL release)

**Change.** ``canonical_string_compute`` now fans the max-xi seed loop
across ``min(seeds, hardware_concurrency())`` threads via ``std::async``
with a shared atomic work-queue counter. The nanobind binding wraps the
compute call in ``nb::gil_scoped_release`` so the threads run
concurrently with the rest of Python. ``greedy_single`` (1 seed) stays
on the sequential path.

**Result.** Dominant win on multi-seed (``greedy_min``) workloads. The
five symmetric designs are vertex-transitive — max-xi returns every
vertex, so the seed count equals ``n_nodes`` and the speedup is
near-linear up to the hardware limit. ``greedy_single`` unchanged.

| Design | greedy_min | Δ vs round 2 | Speedup vs round 0 | Speedup vs Python |
|---|---:|---:|---:|---:|
| Fano        |   1.55 ms |   −72.7 % |  3.8× |    419× |
| STS9        |   7.62 ms |   −81.7 % |  5.8× |    802× |
| STS13       |  42.89 ms |   −87.3 % |  8.2× |  1 478× |
| Doily       |  69.88 ms |   −88.8 % |  9.4× |  >4 290× (Python DNF) |

**Notes.**
- For inputs with very few seeds (e.g. structures where max-xi returns
  a small set after WL pruning), the spawn overhead can dominate. The
  current threshold is ``n_seeds >= 2 && pool.size() >= 2``.

## Round 4 — Stack-allocated VCandidate

**Change.** ``VCandidate`` previously held two ``std::vector``s
(``sorted_new_labels``, ``new_inputs``). These were rebuilt for every
edge that passed the eligibility filter inside
``best_v_for_displacement``, even when the candidate was immediately
rejected. Switched both to ``std::array<…, MAX_NEW>`` plus a length
counter; the candidate is now trivially copyable and never touches the
heap. ``Token::make_v`` got a pointer-plus-length overload to consume
the array form directly.

**Result.** Noise-level on its own (~0–2 %). The heap allocations being
removed were already cheap because most attempted edges short-circuit
before allocating, and the surviving allocation amortised through
``std::move`` into the running ``best`` candidate. Kept for cleanliness
(no allocator activity in the inner loop) and because it sets up
round 5 to actually win.

## Round 5 — Persistent thread pool

**Change.** Round 3 used ``std::async(std::launch::async)`` which
creates fresh OS threads per ``canonical_string`` call. For workloads
that fingerprint many hypergraphs back-to-back (dataset sweeps), thread
creation amortised badly. Added a process-wide ``ThreadPool`` sized to
``hardware_concurrency()`` in ``_native/include/isalhg/thread_pool.hpp``;
``canonical_string_compute`` submits work to it via a shared atomic
work-queue counter (same workstealing-style fan-out as round 3, just
without thread creation).

**Result.** Helps designs where per-seed work is small (Fano:
1.55 → 1.36 ms = −12 %; STS(9): 7.62 → 7.14 ms = −6 %). Doily/STS(13)
unchanged because per-seed work (~40 ms) already dominates any
thread-spawn overhead. greedy_single sequential path unchanged.

| Design | greedy_min round 3 | round 5 | Δ |
|---|---:|---:|---:|
| Fano        |  1.55 ms |  1.36 ms | −12.3 % |
| STS9        |  7.62 ms |  7.14 ms |  −6.3 % |
| STS13       | 42.89 ms | 43.04 ms |  +0.4 % (noise) |
| Doily       | 69.88 ms | 69.70 ms |  −0.3 % (noise) |

**Combined ratios vs the Python reference baseline (after round 5):**

| Design | C++ now | Python | Speedup vs Python |
|---|---:|---:|---:|
| Fano  |  1.36 ms |   649 ms |   477× |
| STS9  |  7.14 ms |  6 113 ms |   856× |
| STS13 | 43.04 ms | 63 389 ms | 1 472× |
| Doily | 69.70 ms |    DNF   |  >4 300× |

## Round 6 — Callback-based perm enumeration with stack groups

**Change.** ``enumerate_label_perms`` previously materialised a
``vector<vector<NodeId>>`` of permutations and the caller iterated over
it. Replaced by ``enumerate_label_perms_cb`` which receives a callback
``cb(const NodeId*, int)`` and invokes it inline as each permutation is
assembled. Both the label-grouping data structures
(``std::array<LabelGroupStack, MAX_NEW>``) and the odometer's per-group
permutation buffer are stack-allocated. Eliminates one
``vector<vector>`` build-up + a temporary input vector per V branch.

**Result.** Marginal on its own (~0–4 %); useful as cleanup that
removes the last heap allocations from the inner enumeration path.

| Design | greedy_min round 5 | round 6 | Δ |
|---|---:|---:|---:|
| Fano        |  1.36 ms |  1.31 ms |  −3.7 % |
| STS9        |  7.14 ms |  7.21 ms |  noise  |
| STS13       | 43.04 ms | 43.34 ms |  noise  |
| Doily       | 69.70 ms | 69.24 ms |  noise  |

## Round 7 — Profile-Guided Optimisation (PGO)

**Change.** Added ``ISALHG_PGO_GENERATE`` / ``ISALHG_PGO_USE`` CMake
options. Two-stage build flow:

```
CMAKE_ARGS="-DISALHG_PGO_GENERATE=ON" pip install -e ".[dev]" --no-build-isolation
python scratchpad/cpp_pgo_train.py
CMAKE_ARGS="-DISALHG_PGO_GENERATE=OFF -DISALHG_PGO_USE=ON" \
    pip install -e ".[dev]" --no-build-isolation --force-reinstall
```

Profile data persists in ``build/pgo-data/``. Training driver runs
``canonical_string`` on Fano / STS(9) / STS(13) / doily across all
three native variants so GCC sees the inner-loop branch distributions.

**Result.** Small Fano win, noise elsewhere — the bigger designs sit at
the parallel ceiling so improved codegen barely shows.

| Design | greedy_min round 6 | round 7 (PGO) | Δ |
|---|---:|---:|---:|
| Fano        |  1.31 ms |  1.27 ms |  −3.1 % |
| STS9        |  7.21 ms |  7.23 ms |  noise  |
| STS13       | 43.34 ms | 43.07 ms |  noise  |
| Doily       | 69.24 ms | 68.88 ms |  noise  |

PGO is opt-in (default off) because the workflow is two-stage and the
profile data is host-specific.

## Round 8 — Running counters in EncoderState

**Change.** ``encode_from`` called ``state.i2o_count()`` (O(n) scan)
and ``state.consumed_count()`` (O(m) scan) at every recursion entry.
Replaced both with running counters ``mapped_count`` and
``consumed_cnt`` on ``EncoderState``, incremented/decremented at each
V-emit + C-emit (and their undo) site. ``i2o_count()`` /
``consumed_count()`` now return field reads.

**Result.** Small but consistent win on the small-design / shallow-
recursion case; noise on the deep-recursion doily where the
O(n+m) scan was already a tiny fraction of the per-frame cost. Most
importantly the change is unambiguously correctness-preserving and
removes the only scaling-with-n operation that was repeated per
recursion entry, which sets a better baseline for future inputs where
n is large (1k+ vertices).

| Design | greedy_min HEAD | greedy_min rd8 | Δ |
|---|---:|---:|---:|
| Fano        |  1.51 ms |  1.36 ms |  −9.9 % |
| STS9        |  7.70 ms |  7.65 ms |  −0.6 % |
| STS13       | 48.84 ms | 48.31 ms |  −1.1 % |
| Doily       | 80.03 ms | 78.99 ms |  −1.3 % |

| Design | greedy_single HEAD | greedy_single rd8 | Δ |
|---|---:|---:|---:|
| Fano        |  0.75 ms |  0.73 ms |  −2.7 % |
| STS9        |  4.59 ms |  4.48 ms |  −2.4 % |
| STS13       | 23.78 ms | 23.40 ms |  −1.6 % |
| Doily       | 41.18 ms | 40.78 ms |  −1.0 % |

All Δ are *thermally matched* — both baseline and rd8 measured on the
same workstation thermal state (median of 4 best-of-9 runs each, with
6 s sleeps between runs and a 30 s cooldown after the rebuild). Raw
JSON in ``scratchpad/bench/HEAD_baseline_rep[1-4].json`` and
``scratchpad/bench/round8_matched_rep[1-4].json``.

## Round 8 + PGO regeneration

**Change.** Regenerated the GCC ``.gcda`` profile data against the
round 8 source via ``scratchpad/cpp_pgo_train.py`` (training rep
counts scaled per-design: Fano × 30, STS9 × 15, STS13 × 6,
Doily × 4 — each across all three native variants). Then rebuilt
with ``-DISALHG_PGO_USE=ON``. Same source as round 8.

**Result.** Small extra win across the larger designs; combined with
round 8 this is the best-shipped state.

| Design | greedy_min rd8 | greedy_min rd8+PGO | Δ |
|---|---:|---:|---:|
| Fano        |  1.36 ms |  1.34 ms |  −1.5 % |
| STS9        |  7.65 ms |  7.56 ms |  −1.2 % |
| STS13       | 48.31 ms | 47.82 ms |  −1.0 % |
| Doily       | 78.99 ms | 76.30 ms |  −3.4 % |

## Round 8 + PGO — vs HEAD baseline (final shipped speedup)

| Design | HEAD | rd8 + PGO | Δ vs HEAD | Speedup vs round 0 | Speedup vs Python (round 0 ref) |
|---|---:|---:|---:|---:|---:|
| Fano        |  1.51 ms |  1.34 ms |  −11.3 % |  4.4× |    484× |
| STS9        |  7.70 ms |  7.56 ms |   −1.8 % |  5.8× |    809× |
| STS13       | 48.84 ms | 47.82 ms |   −2.1 % |  7.4× |  1 325× |
| Doily       | 80.03 ms | 76.30 ms |   −4.7 % |  8.6× | >3 930× (Python DNF) |

(``Speedup vs round 0`` divides the post-restructure round-0 numbers
from the top of this file by the rd8+PGO numbers. ``Speedup vs
Python`` divides the pure-Python reference timings in
``analysis_full/cells.csv`` / ``scratchpad/bench/`` by the same.)

## Negative results — what did not work

Documented for future rounds so the same ground is not re-walked.

1. **Per-frame slot-displacement cache.** Pre-compute, at the top of
   ``encode_from``, every (pointer, signed offset) → CDLL slot at every
   offset in ``[-radius, +radius]``. Replaces ``displaced_slot`` walks
   in the cost-class loop with table lookups.
   *Outcome.* Math is exact net-zero (population cost equals per-disp
   savings), and the per-frame 2.5 kB stack array thrashes L1d under
   16-thread parallel load. Net regression of 5–15 % on greedy_min for
   the larger designs.
2. **Stack-allocated ``best_prefix`` + ``tmp_move_block``.** Replace
   the per-frame ``std::vector<Token>`` with
   ``std::array<Token, 32>``. Eliminates the heap-allocation churn from
   the move-block emit path.
   *Outcome.* Helped greedy_single by ~2 %; net regression on parallel
   greedy_min because each worker thread pays the same extra stack
   pressure and the heap allocator amortises well across the worker
   pool.
3. **Arena-pooled sub-completion vectors keyed by recursion depth.**
   Two ``std::vector<Token>`` per recursion level pooled in a per-call
   arena indexed by ``depth * 2 + slot``.
   *Outcome.* ``std::vector<std::vector<Token>>`` storage reallocates
   on grow and invalidates the references held by outer frames; the
   fix (``std::deque<std::vector<Token>>``) costs more in indirection
   than it saves in allocation. Reverted.
4. **Flat 1-D eta cache** (``vector<int32_t>`` + stride instead of
   ``vector<vector<int32_t>>``). Drops one pointer chase per V/C key
   comparison.
   *Outcome.* The eta comparison is past the cascade short-circuit
   gate (``(i, j, edge_label, sorted_new_labels)``) for the vast
   majority of candidate pairs; rarely reached. The extra arithmetic
   in the key constructor was visible on greedy_single (~3 % regression
   on STS13/Doily). Reverted.
5. **CPU pinning to P-cores via ``taskset -c 0-11``.** Hides hybrid-
   core scheduler noise.
   *Outcome.* With 15 seeds and the persistent thread pool, capping at
   12 cores leaves seeds queued and *worsens* doily greedy_min from
   ~80 ms to ~110 ms. The OS scheduler does the right thing when given
   all 16 logical CPUs — leave it alone.

## Round 8 + PGO — vs nauty / bliss / Traces

Apples-to-apples comparison of ``fingerprint(H)`` wall-clock across
the four IsoBackends (post-round-8+PGO IsalHG, pynauty 2.9, bliss via
python-igraph 1.0, Traces via dreadnaut 2.9), median of 4 best-of-9
runs on the same workstation in the same thermal state:

| Design | IsalHG cpp min | IsalHG cpp single | pynauty_levi | bliss_levi | traces_levi |
|---|---:|---:|---:|---:|---:|
| Fano STS(7)    |  1.34 ms |  0.74 ms | 0.02 ms | 0.04 ms | 0.40 ms |
| STS(9) AG(2,3) |  7.56 ms |  4.49 ms | 0.02 ms | 0.06 ms | 0.42 ms |
| STS(13) cyclic | 47.82 ms | 24.29 ms | 0.02 ms | 0.05 ms | 0.45 ms |
| GQ(2,2) doily  | 76.30 ms | 42.05 ms | 0.03 ms | 0.06 ms | 0.45 ms |

The factor against pynauty is 67× (Fano), 378× (STS9), 2 391× (STS13),
2 543× (doily). This is the algorithmic ceiling identified in
``docs/engineering/ALGORITHMS.md`` §3: a multi-seed greedy backtracking encoder
with no individualisation–refinement is structurally bounded by
``(j!)^E`` on vertex-transitive designs, and that bound is hit hardest
on Steiner triple systems and generalised quadrangles. Levi + nauty /
bliss / Traces operate inside an I/R search frame which prunes these
orbits, and run two decades of engineering ahead on the constants
(McKay & Piperno 2014; Junttila & Kaski 2007). Closing this gap
requires not a faster encoder but a *different* algorithm — the I/R
canonical-string variant from Schweitzer & Wiebking (STOC 2019), or
the PI-deferred pruned-canonical backtracking already listed as the
priority Algorithm-R&D track in ``docs/engineering/DEVELOPMENT.md``.

## Summary (round 0 → round 8+PGO)

| Design | round 0 | round 7 (PGO, prior log) | round 8 + PGO (this round) | Speedup vs round 0 |
|---|---:|---:|---:|---:|
| Fano        |   5.91 ms |   1.27 ms |   1.34 ms |  4.4× |
| STS9        |  44.17 ms |   7.23 ms |   7.56 ms |  5.8× |
| STS13       | 353.46 ms |  43.07 ms |  47.82 ms |  7.4× |
| Doily       | 654.90 ms |  68.88 ms |  76.30 ms |  8.6× |

The round-8 numbers above are ~5–10 % above the prior round-7 log
numbers in absolute terms; that is *thermal* — the round-7 numbers
were captured on a cold machine, the round-8 numbers on a workstation
that had been continuously benchmarking for several hours. The
*thermally matched* baseline (HEAD vs round 8+PGO on the same hot
workstation) shows the round-8 work consistently saves 2–11 %.

## Stop criterion

The 13th-Gen i7-13620H parallel ceiling on the doily sits at
~76 ms / 42 ms (parallel / single-seed). Removing the remaining ~34 ms
parallel-overhead gap requires one of the three exit ramps the user
flagged as out-of-scope for this loop:

- **Platform-specific.** Linux ``sched_setaffinity`` to P-cores only,
  ``pthread_setname_np`` + perf scheduling priority, or AVX-512
  intrinsics in the cascade compare. All Linux/x86-specific.
- **Hypergraph-type-specific.** Restrict to uniform-arity designs and
  hard-code the V-perm enumeration for j = 2 only (avoids
  ``std::next_permutation`` overhead). Loses generality for arity-k.
- **Algorithmic.** Implement the PI-deferred pruned-canonical
  backtracking (open question #1 in ``docs/engineering/DEVELOPMENT.md``) or the
  Schweitzer-Wiebking I/R encoder (``docs/engineering/ALGORITHMS.md`` §6). Either
  changes the asymptotic worst case from ``(j!)^E`` to something
  smaller and would dwarf any constant-factor work.

This loop stops here at round 8 + PGO for implementation-overhead work.

## Round 9 — PI 2026-06-23 neighbour-degree seed selector

**Source.** PI proposal (Pascual / López-Rubio working note, 2026-06-23):
*"optimizar algo más el algoritmo h2s — una forma de elegir los nodos
iniciales de h2s, para que haya menos nodos iniciales desde los que
empezar."* The proposed cascade is:

1. Keep nodes whose ``vertex_label`` is the per-graph maximum.
2. From those, keep nodes whose primal-graph degree is maximum.
3. For each surviving node v, build the descending-sorted list of its
   neighbours' primal-graph degrees; keep nodes whose list is
   lexicographically maximum.

Each rung is an iso-invariant projection of the vertex set (labels,
primal-graph degree, and the sorted-multiset of neighbour degrees are
all preserved by any vertex permutation that is a hypergraph
isomorphism), so the intersection is iso-invariant.

**Implementation.**

* C++: ``max_neighbor_degree_nodes_compute`` in
  ``src/isalhg/core/_native/src/structural_tuples.cpp``, exported via
  nanobind as ``_core.max_neighbor_degree_nodes``.
* Python reference: ``_python_max_neighbor_degree_nodes`` in
  ``src/isalhg/core/structural_tuples.py``; dispatch via
  ``max_neighbor_degree_nodes(H, backend=...)``.
* New ``AlgorithmVariant`` ids:
  ``GreedyMinNbrDeg = 5``, ``GreedySingleNbrDeg = 6``.
* Python-visible registry names: ``greedy_min_nbrdeg``,
  ``greedy_single_nbrdeg``.
* ``canonical_string_compute`` switches selector based on variant; the
  rest of the H2S pipeline (the greedy backtracking encoder + the
  multi-seed parallel fan-out) is reused unchanged.

The new variants are **distinct canonical strings** from
``greedy_min`` — both are sound iso fingerprints, but they pick lex-min
over different seed pools and so may produce different strings on the
same H. Fixtures fingerprinted under one variant cannot be compared
against fixtures fingerprinted under the other. Within a corpus that
uses one variant consistently, iso-equality holds.

**Iso-invariance — empirical evidence.** Property test in
``scratchpad/property_nbrdeg.py`` — 500 random connected hypergraphs
(n = 5..14, m = n−1..2n, arity 2..4, ``random.Random(2026)``), each
permuted by a random ``sigma``:

| check | pass rate |
|---|---:|
| ``canonical_string(H, greedy_min) == canonical_string(perm(H), greedy_min)`` | 500 / 500 |
| ``canonical_string(H, greedy_min_nbrdeg) == canonical_string(perm(H), greedy_min_nbrdeg)`` | 500 / 500 |
| ``canonical_string(H, greedy_min_inplace) == canonical_string(perm(H), greedy_min_inplace)`` | 500 / 500 |
| ``max_neighbor_degree_nodes`` selector ``sigma(seeds(H)) == seeds(perm(H))`` | 500 / 500 |

**Seed-count comparison (same 500 trials).**

| outcome | count | share |
|---|---:|---:|
| ``len(xi seeds) == len(nbrdeg seeds)`` | 410 | 82.0 % |
| ``len(nbrdeg seeds) < len(xi seeds)`` (PI wins) | 76 | 15.2 % |
| ``len(xi seeds) < len(nbrdeg seeds)`` (xi wins) | 14 | 2.8 % |

The PI cascade is **strictly cheaper to compute** per call
(O(n + n·d̄) primal-graph operations vs O(n²·depth) for the depth-3
BFS shell walk that ``max_xi_nodes`` runs), and on 15 % of random
connected inputs it returns a strictly smaller seed set — both wins
amortise across dataset sweeps.

**Wall-clock — same 4 symmetric designs.** Median of 4 reps of
best-of-9 ms, ``--warmup 3``, with round-8 source + PGO:

| Design | xi ``greedy_min`` | xi ``greedy_single`` | nbrdeg ``greedy_min`` | nbrdeg ``greedy_single`` |
|---|---:|---:|---:|---:|
| Fano STS(7)    |  1.31 ms |  0.72 ms |  1.30 ms |  0.73 ms |
| STS(9) AG(2,3) |  7.03 ms |  4.43 ms |  7.10 ms |  4.42 ms |
| STS(13) cyclic | 42.31 ms | 23.00 ms | 42.42 ms | 22.95 ms |
| GQ(2,2) doily  | 68.11 ms | 39.81 ms | 67.29 ms | 39.81 ms |

The four designs are vertex-transitive, so both selectors return the
full vertex set (Fano 7, STS9 9, STS13 13, doily 15 seeds) and the H2S
inner loop dominates — the selector itself is well under 1 µs per
call. Δ between the two columns is within thermal noise (Fano −0.8 %,
STS9 +1.0 %, STS13 +0.3 %, doily −1.2 %). The PI cascade is shipped
unconditionally as a new variant alongside the original xi cascade —
no regression on the vertex-transitive baseline, free pre-partitioning
power for any future labelled / non-vertex-transitive workload.

**Full comparison vs Levi + nauty / bliss / Traces.** Same workstation
state, same call shape; raw JSON in
``scratchpad/bench/nbrdeg_pgo_rep[1-4].json``.

| Design | C++ ``min`` | C++ ``single`` | C++ ``nbrdeg_min`` | C++ ``nbrdeg_single`` | pynauty | bliss | Traces |
|---|---:|---:|---:|---:|---:|---:|---:|
| Fano STS(7)    |  1.31 ms |  0.72 ms |  1.30 ms |  0.73 ms | 0.02 ms | 0.04 ms | 0.39 ms |
| STS(9) AG(2,3) |  7.03 ms |  4.43 ms |  7.10 ms |  4.42 ms | 0.02 ms | 0.06 ms | 0.43 ms |
| STS(13) cyclic | 42.31 ms | 23.00 ms | 42.42 ms | 22.95 ms | 0.02 ms | 0.05 ms | 0.41 ms |
| GQ(2,2) doily  | 68.11 ms | 39.81 ms | 67.29 ms | 39.81 ms | 0.03 ms | 0.06 ms | 0.43 ms |

The factor vs pynauty stays in the 67×–2 500× range from round 8 — the
algorithmic ceiling (``(j!)^E`` on vertex-transitive designs) is
unchanged because the seed *set* on these inputs is unchanged. Closing
that gap still requires the PI-deferred pruned-canonical algorithm or
the Schweitzer-Wiebking I/R encoder (``docs/engineering/ALGORITHMS.md`` §6).

**Where the win actually shows.** For typical non-vertex-transitive
workloads (random ER hypergraphs at Tier 2 scale, labelled HIC-atlas
data at Tier 5, the LLM4Hypergraph iso-recognition corpus — see
``docs/preprint/DATA.md``) the 15 % seed-count reduction multiplies through the
per-seed wall-clock.

### Round 9 demo — concrete PI-advantage fixtures

To show the seed-reduction win as actual wall-clock, we ran a
205-trial sweep of random connected hypergraphs (seed 20260623,
n = 10..16, m = n..2n, arity ≤ 3 or 4), filtered to cases where
``max_neighbor_degree_nodes`` returns *strictly* fewer seeds than
``max_xi_nodes`` and per-seed wall-clock is in the measurable range.
The screening identified 20 qualifying fixtures; we pick one per n for
the table. Fixtures are stored verbatim in
``scratchpad/bench/pi_fixtures.json``; driver
``scratchpad/cpp_vs_levi_pi.py``; raw output JSON in
``scratchpad/bench/pi_demo_rep[1-4].json``. Best-of-9 ms, median of 4
reps, ``--warmup 3``, round-8 source + PGO.

| Fixture (n, m, r≤, xi→nbr) | xi ``min`` | xi ``single`` | nbrdeg ``min`` | nbrdeg ``single`` | pynauty | bliss | Traces |
|---|---:|---:|---:|---:|---:|---:|---:|
| n=10, m=17, r≤4, **3 → 1** | 10.46 ms |  2.74 ms |  **2.74 ms** |  **2.74 ms** | 0.03 ms | 0.05 ms | 0.40 ms |
| n=12, m=20, r≤4, **2 → 1** |  9.78 ms |  7.52 ms |  9.46 ms |  9.46 ms | 0.03 ms | 0.06 ms | 0.36 ms |
| n=14, m=23, r≤3, **2 → 1** |  2.92 ms |  2.85 ms |  **2.15 ms** |  **2.14 ms** | 0.03 ms | 0.06 ms | 0.41 ms |
| n=16, m=26, r≤4, **2 → 1** | 42.17 ms | 42.17 ms | **36.88 ms** | **36.83 ms** | 0.03 ms | 0.07 ms | 0.43 ms |

Δ relative to the corresponding xi cell (negative = PI wins):

| Fixture | Δ ``greedy_min`` | Δ ``greedy_single`` |
|---|---:|---:|
| n=10  (3 → 1) | **−73.8 %** |   0.0 % |
| n=12  (2 → 1) |   −3.3 %    | **+25.8 %** (¹) |
| n=14  (2 → 1) | **−26.4 %** | **−24.9 %** |
| n=16  (2 → 1) | **−12.5 %** | **−12.7 %** |

(¹) The xi cascade on n=12 happens to surface a smaller-lex node whose
own greedy_h2s trace is shorter than the single nbrdeg seed's; in the
single-seed setting that gives xi the edge. The multi-seed cell still
loses to nbrdeg because xi has to pay parallel fan-out over 2 seeds
plus the lex-min reduction. The PI cascade is correct (lex-min over its
seed set is iso-invariant) but is not guaranteed to pick the
*cheapest* seed — only an *iso-invariant* one.

The n=10 fixture is the clean demonstration of the PI proposal: 3
seeds collapse to 1, the parallel ``greedy_min`` cell drops to the
cost of a single greedy_h2s call, and we save 73.8 % of the
wall-clock without any change to the H2S encoder itself. The n=14 and
n=16 cases show the smaller, more representative win (12–26 %) when
the seed-count reduction is 2 → 1.

The Levi backends remain 4–5 orders of magnitude faster — the PI
cascade closes the *intra-IsalHG* implementation gap on
non-vertex-transitive inputs but does not move the algorithmic ceiling
identified in ``docs/engineering/ALGORITHMS.md`` §3.

## Summary (round 0 → round 9)

| Design | round 0 | round 7 (PGO, prior) | round 8 + PGO | round 9 (nbrdeg) | Speedup r0 → r9 |
|---|---:|---:|---:|---:|---:|
| Fano        |   5.91 ms |   1.27 ms |   1.34 ms |   1.30 ms |  4.5× |
| STS9        |  44.17 ms |   7.23 ms |   7.56 ms |   7.10 ms |  6.2× |
| STS13       | 353.46 ms |  43.07 ms |  47.82 ms |  42.42 ms |  8.3× |
| Doily       | 654.90 ms |  68.88 ms |  76.30 ms |  67.29 ms |  9.7× |

The round-9 columns use the new ``nbrdeg`` variants; ``round 8 + PGO``
in the prior summary used the xi selector. On these four symmetric
designs the two selectors are within ±1.5 % of each other (noise),
so the round-9 numbers also confirm the round-8 + PGO work was not
lost. Net round 0 → round 9 speedup ranges from 4.5× (Fano, smallest
design — implementation overhead dominates) to 9.7× (doily, parallel
fan-out fully saturated).

## Round 10 — optimising the *canonical-complete* variant (the article target)

**Context — a different algorithm.** Rounds 0–9 optimised the **greedy**
encoder (``greedy_min`` / ``greedy_min_nbrdeg``, C++ variants 0/5). The
metric-space article (`docs/article/PROPOSAL.md`) does **not** use greedy: it
pivoted to the **tie-complete canonical algorithm** (``"canonical"``, C++
variant 7, computing the frozen ``w*_c``; T-TAd/T-TAf), the only variant whose
string is a complete isomorphism invariant and therefore the only one on which
``d_I`` is well-defined. That variant branches over the residual V-tie set ×
label-respecting permutations and is 15–20× slower than greedy on the design
fixtures. Rounds 0–9 barely touched it. This round optimises it directly.

Machine: i7-13620H, conda env ``isalhg``, **non-PGO** dev build (both baseline
and optimised measured non-PGO on the same thermal state, so the ratios are
sound). Baseline = the round-9 source at HEAD of this branch; optimised = the
three changes below. Correctness gate re-run after every change (see *Verification*).

**Where the time goes — two regimes (measured with per-call counters).**
The tie-complete search has two distinct cost regimes, and they need different
levers:

| Input | encode_from entries | displacements | max move cost c\* | bound by |
|---|---:|---:|---:|---|
| GQ(2,2) doily | 447 585 | 36.3 M | 6 | **branching** (automorphism-rich ties) |
| STS(9) | 33 345 | 2.48 M | — | branching |
| random n=12 (tail) | ~300 | 0.2 M | — | displacement enumeration |
| random sparse n=35 | 7 937 | 8.2 M | **46** | **per-frame displacement** |
| random sparse n=50 | 39 719 | 72.4 M | **58** | per-frame displacement |

Both regimes are ultimately **displacement-bound**: every recursion frame
enumerates all pointer-displacement tuples up to the first emittable cost
``c*``, and ``c*`` grows with ``n`` on sparse inputs (the next unconsumed edge
can be far in the CDLL). The doily is *also* branching-bound (447 k frames).

**The three changes (all output-preserving — ``w*_c`` is byte-identical).**

1. **Incidence-restricted candidate scan.** Both the V and C candidate scans
   iterated all ``E`` edges per displacement. But any candidate requires
   ``tentative_inputs[0]`` (pointer 1's landed vertex) to be a member of the
   edge, so only edges in ``SHG::vertex_edges[t0]`` can qualify — the candidate
   set is identical. For the doily this is 3 incident edges vs 15 total.
2. **Drop the per-cost-class sort.** ``enum_cost_class`` sorted each class. The
   caller picks the winner by an order-independent ``(total_len, move-block,
   main-token)`` comparison, and the move-block token sequence is injective in
   the displacement, so no two displacements tie — the winner is identical for
   any enumeration order. The sort was pure overhead.
3. **Displacement search only varies ``min(k, max_arity)`` pointers.** No V/C
   candidate ever reads ``tentative_inputs`` beyond ``max_arity − 1`` (the scan
   prefix is bounded by ``min(k, arity) ≤ max_arity``), so moving a pointer
   beyond ``max_arity`` is strictly cost-dominated and never wins. The
   enumeration therefore varies only the first ``k_disp = min(k, max_arity)``
   coordinates. A no-op when ``k = max_arity`` (uniform-arity corpora), but the
   ``d_I`` corpus path encodes **every** hypergraph with the corpus-wide
   ``k = max(required_k(H))`` (`isalhg_levenshtein.py::_resolve_corpus_k`), so a
   graph inside an arity-5 corpus previously enumerated 5-tuples where 2 suffice.
   Verified ``w*_c`` is invariant to ``k`` for ``k ≥ max_arity`` on 600/600
   random instances.

**Result — canonical variant ``w*_c`` (best-of-4 reps, ``scripts/bench_tie_complete.py``).**

| Design | baseline (r9 src) | round 10 | speedup |
|---|---:|---:|---:|
| Fano STS(7)    |    9.20 ms |    5.22 ms | 1.76× |
| STS(9) AG(2,3) |  199.57 ms |  106.44 ms | 1.87× |
| STS(13) cyclic |  401.16 ms |  210.30 ms | 1.91× |
| GQ(2,2) doily  | 1621.03 ms |  743.03 ms | **2.18×** |

Random corpus tail (max over 30 connected instances/n) also improves: n=11
19.16 → 10.71 ms, n=12 61.50 → 34.23 ms (~1.8×). The greedy variants share the
``encode_from`` code path and get the same ~2× for free (doily greedy 80.9 →
46.2 ms). All four ``test_wstar_c_frozen`` pins hold; the differential suite
(C++ ≡ Python tie-complete on random hypergraphs), the completeness
biconditional vs pynauty, and invariance are green (98 focused + 699 full-suite
tests passed).

**Verification.** `pytest tests/unit tests/property tests/integration -m "not
slow" --hypothesis-seed=0` → **699 passed, 13 skipped** (T-TAd baseline 674);
`tests/unit/core/test_wstar_c_frozen.py` → 4/4; k-invariance 600/600; ruff
unchanged from baseline.

**Round 10 vs the Levi competitors — the honest easy→hard picture**
(``scripts/bench_canonical_vs_competitors.py``, best-of-7,
``isalhg_canonical``; Traces skipped — no ``dreadnaut`` on PATH).

| Instance | IsalHG ``w*_c`` | pynauty_levi | bliss_levi |
|---|---:|---:|---:|
| easy n=6  sparse  |   0.09 ms | 0.02 ms | 0.04 ms |
| easy n=10 sparse  |   0.51 ms | 0.03 ms | 0.05 ms |
| medium n=20 sparse |  10.9 ms | 0.06 ms | 0.10 ms |
| medium n=35 sparse |  44.1 ms | 0.08 ms | 0.13 ms |
| medium n=50 sparse | ~2.9 s  | 0.15 ms | 0.24 ms |
| hard Fano STS(7)  |   5.9 ms | 0.02 ms | 0.05 ms |
| hard STS(9)       | 104.9 ms | 0.06 ms | 0.17 ms |
| hard cyclic STS(13) | 205.8 ms | 0.06 ms | 0.14 ms |
| hard GQ(2,2) doily | 727.6 ms | 0.04 ms | 0.08 ms |

The Levi + nauty/bliss backends stay 2–4 orders of magnitude faster. Round 10
closes the *intra-IsalHG* implementation gap by ~2× but does **not** move the
algorithmic ceiling. The two levers that would are, per regime:

- **Large-``n`` per-frame cost (the ``n=50`` cliff — the applications regime,
  T-M5b–e).** The blow-up is the ``O(c*^{k_disp})`` blind cost-class
  enumeration with ``c*`` up to ``O(n)``. The fix is to **invert** the search:
  for each unconsumed edge with mapped members, compute the minimal-cost
  displacement that emits it directly (a tiny ``≤ (k−1)``-pointer assignment
  problem), and take the shortlex-min over edges — ``O(edges)`` per frame
  instead of ``O(c*^{k_disp})``. Value-preserving in principle, but reproducing
  the exact shortlex move-block tie-break bit-for-bit is delicate against the
  frozen ``w*_c``; deferred to a dedicated task with extended differential
  coverage rather than rushed here.
- **Branching on automorphism-rich designs (Fano/STS/doily).** 447 k frames on
  the doily is the ``(j!)^E`` tie fan-out. The only value-preserving lever
  (T-TAf, Prop. 6.0) is **stabiliser-orbit pruning** — explore one branch per
  orbit of the prefix-fixing automorphism group. Detecting that group during
  search is the hard part of nauty; it is a research subtask, not a constant
  factor.

Both are recorded here as the next Algorithm-R&D levers (the same status the
round-8 *stop criterion* gave the I/R exit ramp). Round 10 ships the sound
constant-factor work: a verified ~2× on the article's actual canonical
algorithm with an unchanged canonical form. Round 11 (below) takes on the first
of the two levers.

## Round 11 — inverted displacement enumeration (the large-``n`` lever)

**Target.** The Round-10 diagnosis showed the per-frame cost is the blind
cost-class enumeration: for the first emittable cost ``c*`` the frame
enumerates every ``k_disp``-tuple displacement, ``O(c*^{k_disp})``, and ``c*``
grows with ``n`` on sparse inputs (the next unconsumed edge is far in the CDLL —
``c*`` up to 46/58 at n=35/50). This is the ``n=50 → 2.9 s`` cliff, i.e. the
applications regime (T-M5b–e run ``w*_c`` on larger real hypergraphs).

**The inversion.** A V/C emission of edge ``e`` is *uniquely determined* by the
edge: since every pointed vertex is mapped and every ``new`` vertex must be
unmapped, the only admissible V split is ``i = p`` (point **all** ``p`` mapped
members, create the ``q`` unmapped), and C requires ``q = 0``. So instead of
enumerating displacements blindly, enumerate **per edge**: for each unconsumed
edge, place pointers ``1..r`` on ``r`` of its members (``r = p`` for V, ``r =
arity`` for C) over all ``r!`` bijections and, per pointer, both minimal signed
displacements reaching its target (forward ``+f`` / backward ``f−N``);
unassigned pointers stay put. Every displacement so generated is a genuine
candidate the brute force would also produce, and each is fed to the **same**
``consider`` comparison — so the winner is identical. Cost drops from
``O(c*^{k_disp})`` to ``O(sum_e r_e!·2^{r_e})`` per frame, independent of ``c*``.
Forward distances are ``O(1)`` after one ``O(N)`` CDLL walk builds a position
rank.

**Hybrid, not replacement.** The brute-force loop is cheaper when ``c*`` is
small (all design fixtures: ``c* ≤ 6``), so it runs up to a cost cap
(``INVERSION_COST_CAP = 8``); only frames that find nothing by cost 8 (sparse,
far next edge) fall back to the inversion. Every design therefore stays on the
byte-identical, same-speed brute path — no regression — while the sparse frames
get the ``O(edges)`` search.

**Validation (byte-identical ``w*_c``).** The inverted path is refactored to
share the exact per-displacement comparison (``consider``), then validated three
ways: (i) built **inversion-only** (brute disabled) it passes the frozen pins,
the C++≡Python differential, and the completeness biconditional; (ii)
inversion-only vs brute-only agree on **84/84** sparse instances (n=12..36, incl.
``k=6`` mixed-arity encodes); (iii) the shipped hybrid (cap 8) agrees with the
brute build on the same 84/84. Full suite green.

**Result — canonical ``w*_c`` (non-PGO, i7-13620H).**

| Instance | Round 10 (brute) | Round 11 (hybrid) | speedup |
|---|---:|---:|---:|
| medium sparse n=20 |   10.9 ms |   4.5 ms | 2.4× |
| medium sparse n=35 |   44.1 ms |   6.1 ms | **7.3×** |
| medium sparse n=50 | ~2900 ms | 317.6 ms | **9.1×** |
| random corpus n=12 (max) | 34.2 ms | 8.7 ms | 3.9× |
| Fano / STS(9) / STS(13) / doily | — | unchanged | 1.0× (brute path) |

The design fixtures are within run-to-run noise of Round 10 (they never enter
the inversion). The win is concentrated exactly where the article needs it: the
random/real sparse corpus and the larger-``n`` applications regime. Combined
round-0-baseline → round-11 on the sparse tail, the ``n=50`` fingerprint went
from unusable (~3 s) to corpus-viable (~0.3 s), still 3–4 orders of magnitude
behind Levi+nauty but no longer a scaling wall.

The remaining lever is unchanged: **stabiliser-orbit pruning** for the
automorphism-rich designs and the tie-branch entry count (Round 10, still the
open Algorithm-R&D item).
