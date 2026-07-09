# Scope T-M1 — `metric_space/` foundation and the first distances

Everything the metric-space article computes flows through one abstraction: a
`HypergraphDistance` that turns a pair (or a corpus) of hypergraphs into a
number (or a matrix `D`). This scope builds that layer — the ABC, its registry,
the `MetricSpaceError` hierarchy, the six structural edit ops on
`SparseHypergraph`, and the relocation of `levi_reduction` into `core/` so
`metric_space` never depends on `isomorphisms` — and then lands the two distances
that need no external competitor: `d_I`, raw Levenshtein on the canonical string,
and the hypergraph-WL colour-histogram baseline. Concrete competitors (T-M3) and
the HGED oracle (T-M2) register alongside them.
