# Scope T-M2 — HGED, the ground-truth structural distance

Hypergraph edit distance is the right-hand side of Theorem B and the ground truth
of the Layer-1 correlation study: without it there is nothing to correlate `d_I`
against and no head-to-head axis versus the competing representations. No public
HGED solver exists, so this scope builds one — an LSAP branch-and-bound oracle
(`exact_hged`) plus a faithful re-implementation of the paper's own HGED-BFS
(`qin_hged`) that anchors fidelity on its published Example 2 — under the single
official cost model, Qin et al. (ICDE 2023) Definition 3 verbatim, where deleting
an arity-`a` hyperedge costs `a + 1`. It also owns the corpora HGED is computed
on (perturbation ladder, correlation corpus) and the domain gap that HGED exposes:
optimal edit paths pass through disconnected hypergraphs, on which `d_I` is not
defined.
