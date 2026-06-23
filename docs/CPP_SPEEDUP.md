# Phase 4 — IsalHG C++ vs Python speedup

Local laptop, single-threaded. Python timings use the pre-port
reference implementations kept under ``_python_greedy_h2s`` and
``_python_max_xi_nodes``. C++ timings call the production entry
``isalhg.core.canonical.canonical_string`` which dispatches to the
C++ ``_core.canonical_string`` for the five native variants.

All cells are byte-equal between Python and C++ on the runs that
completed (column ``status``).

| Design | Algorithm | Python (ms) | C++ (ms) | Speedup | Status |
|---|---|---:|---:|---:|---|
| Fano STS(7) | greedy_min | 649.06 | 6.40 | 101.4× | EQ |
| Fano STS(7) | greedy_single | 93.29 | 0.83 | 112.4× | EQ |
| STS(9) AG(2,3) | greedy_min | 6112.74 | 44.18 | 138.3× | EQ |
| STS(9) AG(2,3) | greedy_single | 678.38 | 4.91 | 138.1× | EQ |
| STS(13) cyclic | greedy_min | 63388.51 | 351.97 | 180.1× | EQ |
| STS(13) cyclic | greedy_single | 4224.84 | 25.21 | 167.6× | EQ |
| GQ(2,2) doily | greedy_min | DNF | 658.45 | — | EQ |
| GQ(2,2) doily | greedy_single | 21919.06 | 44.19 | 496.0× | EQ |
