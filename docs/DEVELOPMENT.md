# Development notes

Living document for IsalHG development. Pair-read with `CLAUDE.md` at the repo
root and the seed proposal (`docs/isalhg_idea.pdf`).

## TODO

- Port `cdll.py` from IsalGraph.
- Port `sparse_hypergraph.py` from IsalGraph's `sparse_graph.py`, generalizing
  edges to hyperedge sets.
- Implement Sigma_HG token parser and the constraint validator.
- Implement S2H interpreter.
- Implement H2S greedy with the tie-breaking cascade.
- Implement structural tuples xi and eta.
- Implement canonical entry point (greedy seeded from max-xi).
- Add HyperNetX and XGI adapters first; HyperGraphX after the core
  stabilizes. DHG dropped (see `feedback_adapter_vetting.md` in project memory).
- Hypothesis property tests for round-trip and canonical invariance.

## Open research questions (from the seed proposal)

1. Backtracking procedure for greedy ties: unspecified.
2. Value of `k`: global / input-dependent / adaptive.
3. Structural-tuple depth: fixed at 3 by analogy; ablation needed.
4. Complexity bound for canonical encoding.
5. Completeness proof for canonical-string invariant.
