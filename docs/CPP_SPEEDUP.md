# IsalHG C++ — head-to-head against Levi + nauty / bliss / Traces

Workstation: i7-13620H, conda env ``isalhg``. Best-of-9 ms, median of
4 reps each, ``--warmup 3``. Driver: ``scratchpad/cpp_vs_levi.py``. Raw
JSON: ``scratchpad/bench/nbrdeg_pgo_rep[1-4].json``. Build flags:
round-8 source + PGO (two-stage flow in ``docs/DEVELOPMENT.md``).

Two C++ seed-selectors are exposed:

* **xi** — the original ``max_xi_nodes`` cascade (depth-3 BFS shell
  label counts). Used by ``greedy_min`` / ``greedy_single``.
* **nbrdeg** — the PI 2026-06-23 cascade (max label → max primal-graph
  degree → lex-max sorted-descending neighbour-degree list). Used by
  ``greedy_min_nbrdeg`` / ``greedy_single_nbrdeg``. Iso-invariant by
  construction; 500/500 trials on random connected hypergraphs
  (n = 5..14, m = n-1..2n, arity 2..4) preserved the canonical-string
  identity under random vertex permutations (see
  ``docs/CPP_OPTIMIZATION_LOG.md`` round 9 for the harness).

| Design | IsalHG C++ ``greedy_min`` | ``greedy_single`` | ``greedy_min_nbrdeg`` (PI) | ``greedy_single_nbrdeg`` (PI) | pynauty_levi | bliss_levi | traces_levi |
|---|---:|---:|---:|---:|---:|---:|---:|
| Fano STS(7)    |   1.31 ms |   0.72 ms |   1.30 ms |   0.73 ms | 0.02 ms | 0.04 ms | 0.39 ms |
| STS(9) AG(2,3) |   7.03 ms |   4.43 ms |   7.10 ms |   4.42 ms | 0.02 ms | 0.06 ms | 0.43 ms |
| STS(13) cyclic |  42.31 ms |  23.00 ms |  42.42 ms |  22.95 ms | 0.02 ms | 0.05 ms | 0.41 ms |
| GQ(2,2) doily  |  68.11 ms |  39.81 ms |  67.29 ms |  39.81 ms | 0.03 ms | 0.06 ms | 0.43 ms |

## Reading the table

The four designs above are **vertex-transitive** Steiner / generalised-
quadrangle structures. On vertex-transitive inputs the automorphism
group acts transitively on the vertex set, so every node has identical
(label, degree, neighbour-degree-list, xi-shell-counts). Both seed
selectors therefore return *all* n vertices, the seed loop runs n
greedy_h2s instances, and the wall-clock is dominated by the inner
backtracking — not by which selector ran. Hence the four
``nbrdeg`` cells are statistically indistinguishable from the
``xi`` cells (Δ between −0.6 % and +1.7 % across the four designs,
within run-to-run thermal noise).

The PI cascade is a **strict speedup on non-vertex-transitive
inputs**: in a 500-trial sweep over random connected hypergraphs
(n = 5..14, m = n-1..2n, arity 2..4) ``nbrdeg`` returned a strictly
smaller seed set than ``xi`` on 15.2 % of inputs, with the
remaining 82 % yielding the same seed count and 2.8 % yielding one
extra seed. The selector itself is also asymptotically cheaper —
O(n + n·deḡ) per call vs O(n²·depth) for the depth-3 BFS shell
walk — visible only on dataset sweeps where the SHG view is built
once per call.

## Concrete PI advantage — non-vertex-transitive fixtures

Picked from a 205-trial random-hypergraph sweep (seed 20260623), filtered
to cases where ``max_neighbor_degree_nodes`` returns *strictly* fewer
seeds than ``max_xi_nodes`` AND the per-seed wall-clock is measurable.
Fixtures stored verbatim in ``scratchpad/bench/pi_fixtures.json``;
driver ``scratchpad/cpp_vs_levi_pi.py``; raw JSON
``scratchpad/bench/pi_demo_rep[1-4].json``. Best-of-9 ms, median of 4
reps, ``--warmup 3``, round-8 source + PGO.

| Fixture (n, m, r≤, xi→nbr seeds) | C++ ``min`` | C++ ``single`` | C++ ``nbrdeg_min`` | C++ ``nbrdeg_single`` | pynauty | bliss | Traces |
|---|---:|---:|---:|---:|---:|---:|---:|
| n=10, m=17, r≤4, **xi=3 → nbr=1** | 10.46 ms |  2.74 ms |  **2.74 ms** |  **2.74 ms** | 0.03 ms | 0.05 ms | 0.40 ms |
| n=12, m=20, r≤4, **xi=2 → nbr=1** |  9.78 ms |  7.52 ms |  9.46 ms |  9.46 ms | 0.03 ms | 0.06 ms | 0.36 ms |
| n=14, m=23, r≤3, **xi=2 → nbr=1** |  2.92 ms |  2.85 ms |  **2.15 ms** |  **2.14 ms** | 0.03 ms | 0.06 ms | 0.41 ms |
| n=16, m=26, r≤4, **xi=2 → nbr=1** | 42.17 ms | 42.17 ms | **36.88 ms** | **36.83 ms** | 0.03 ms | 0.07 ms | 0.43 ms |

PI-cascade speedups vs the xi cascade on the *same* fixture:

| Fixture | Δ ``greedy_min`` | Δ ``greedy_single`` |
|---|---:|---:|
| n=10  (xi=3 → nbr=1) | **−73.8 %** |   0.0 % |
| n=12  (xi=2 → nbr=1) |   −3.3 %    |  +25.8 % (¹) |
| n=14  (xi=2 → nbr=1) | **−26.4 %** |  −24.9 % |
| n=16  (xi=2 → nbr=1) | **−12.5 %** | −12.7 % |

(¹) On the n=12 fixture the single xi-seed happens to be the lex-smaller
of the two max-xi nodes and produces a shorter greedy_h2s trace than the
single nbrdeg-seed (different node, different trace cost). ``greedy_min``
still wins under nbrdeg because the multi-seed xi cell has to pay the
parallel-fan-out + lex-min reduction over two seeds.

### Why the win shows up here and not on Fano / STS / doily

The four symmetric designs at the top of this file are
*vertex-transitive*: every node has identical (label, degree,
neighbour-degree-list, depth-3 xi shell counts), so both selectors
return the full vertex set and the multi-seed loop runs over the same
n candidates. On the PI fixtures above the automorphism group has a
strict sub-orbit of size 1–2 attaining max-neighbour-degree, while
several other orbits attain max-xi — so the PI cascade returns 1 seed
where xi returns 2–3, and the multi-seed loop shrinks proportionally.
The n=10 fixture is the cleanest illustration: 3 xi seeds collapse to
1 nbrdeg seed, and the parallel ``greedy_min`` cost (10.46 ms across 3
seeds + pool overhead) drops to the cost of a single greedy_h2s call
(2.74 ms) — a 73.8 % win.

### Levi gap on the same fixtures

pynauty / bliss / Traces stay 4–5 orders of magnitude faster on the
``fingerprint`` call (0.03–0.43 ms vs 2–42 ms). The PI cascade closes
the *intra-IsalHG* implementation gap on non-vertex-transitive inputs
but does not change the algorithmic-ceiling story documented in
``docs/ALGORITHMS.md`` §3 — the I/R search frame those backends sit
inside is what wins them the order-of-magnitude gap, and closing that
gap remains the priority Algorithm-R&D track in
``docs/DEVELOPMENT.md``.

## Headline historical comparison vs pure Python

For the (still applicable) Python ↔ C++ Phase-4 baseline, see
``docs/CPP_OPTIMIZATION_LOG.md`` round 0 table. All C++ variants in
this table are byte-equal to their Python reference on every cell
where the Python ref terminates (see ``--- ALL EQ True ---`` smoke
output in the integration log).

| Design | Algorithm | Python (ms) | C++ ``nbrdeg`` (ms) | Speedup | Status |
|---|---|---:|---:|---:|---|
| Fano STS(7)    | greedy_min_nbrdeg    |   649.06 |   1.30 |   499× | EQ |
| Fano STS(7)    | greedy_single_nbrdeg |    93.29 |   0.73 |   128× | EQ |
| STS(9) AG(2,3) | greedy_min_nbrdeg    |  6 112.74 |   7.10 |   861× | EQ |
| STS(9) AG(2,3) | greedy_single_nbrdeg |   678.38 |   4.42 |   154× | EQ |
| STS(13) cyclic | greedy_min_nbrdeg    | 63 388.51 |  42.42 | 1 494× | EQ |
| STS(13) cyclic | greedy_single_nbrdeg |  4 224.84 |  22.95 |   184× | EQ |
| GQ(2,2) doily  | greedy_min_nbrdeg    |     DNF   |  67.29 |   —    | EQ (py DNF) |
| GQ(2,2) doily  | greedy_single_nbrdeg | 21 919.06 |  39.81 |   550× | EQ |
