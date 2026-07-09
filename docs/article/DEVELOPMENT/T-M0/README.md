# Scope T-M0 — seed selection for `w*`

The canonical string is the lexicographic minimum of greedy H2S runs started from
every node of an *iso-invariant* seed set, so the seed rule fixes both the
correctness of `w*` (a non-invariant rule silently breaks the isomorphism-
invariance claim) and its cost (fewer seeds means fewer encoder fan-outs, and a
smaller avalanche surface for the stability theorem). This scope covers the
promotion of the neighbour-degree cascade — maximal label, then maximal degree,
then lexicographically-maximal decreasing neighbour-degree list — to the package
default, plus the residual defects it surfaced: a design fixture that is not the
design it claims to be, and a quadratic rebuild in the Python reference seeder.
