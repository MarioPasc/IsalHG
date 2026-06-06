"""SparseHypergraph -- adjacency-set hypergraph with contiguous int node IDs.

Generalizes IsalGraph/src/isalgraph/core/sparse_graph.py: hyperedges are
frozensets of NodeId (arity >= 2). No multi-hyperedges (a given node-set
appears at most once).
"""
