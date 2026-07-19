# Scope T-OPT — C++ engine revision for the metric-space workload

The native encoder was engineered for the iso-benchmark use case — small
design fixtures, arity capped at `K_MAX = 10`, one fingerprint at a time —
before the metric-space rescope made *corpus-scale* `w*_c` the workload. The
T-DQ3' gate measurement exposed the mismatch: automorphism/tie branching
DNFs on small near-symmetric real instances (n=10, m=5 exceeding 330 s), and
a compile-time arity cap that no real corpus-level `k` fits. This scope
covers the engine work that responds to it without touching the frozen
definition of `w*_c` (D-TA2): stabiliser-orbit pruning — the one
value-preserving speedup Proposition 6.0 sanctions — a runtime `k`, and the
C++ port of the S2H interpreter so decode matches encode in reach. Declared
at the S2 session (2026-07-19) on the user's direction.
