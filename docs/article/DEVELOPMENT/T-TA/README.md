# Scope T-TA — Theorem A, completeness of the canonical form

Every metric-space claim in the article rests on one biconditional: two
hypergraphs have the same canonical fingerprint if and only if they are
isomorphic. The forward direction holds unconditionally for every encoder variant
by round-trip soundness of S2H. The converse is **false** for the greedy variants,
which break residual `V`-ties by raw edge id and therefore return a function of the
*presentation* rather than of the abstract hypergraph; it is proved only for the
tie-complete encoder `w*_c`, which branches over the full tie set and takes the
lex-min completion. Two further deficiencies live here: the string never emits the
seed vertex's label, so the fingerprint must be augmented to `F = (ℓ_max, w*_c)`
on non-trivial vocabularies, and the Levi reduction used by the nauty/bliss/Traces
baselines erases absolute label identity. This scope owns the proof, the C++
implementation that makes `w*_c` affordable, its promotion to the package default,
the definitional freeze that fixes *which* tie-complete lex-min the article means,
and the honest re-documentation of the variants that are not canonical.
