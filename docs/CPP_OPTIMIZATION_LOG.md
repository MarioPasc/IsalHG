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

**Combined ratios vs the Python reference baseline:**

| Design | C++ now | Python | Speedup vs Python |
|---|---:|---:|---:|
| Fano  |  1.36 ms |   649 ms |   477× |
| STS9  |  7.14 ms |  6 113 ms |   856× |
| STS13 | 43.04 ms | 63 389 ms | 1 472× |
| Doily | 69.70 ms |    DNF   |  >4 300× |
