// C++ S2H interpreter — port of ``isalhg.core.string_to_hypergraph``.
//
// Closed-alphabet invariant: every well-formed Sigma_HG* string decodes to a
// valid hypergraph; the interpreter never rejects alphabet-valid input (the
// caller is responsible for validation via isalhg.core.instructions.validate).
//
// W tokens execute as no-ops and are NEVER stripped (invariant 6 of CLAUDE.md).
// Pointer moves advance/retreat to CDLL next/prev slots (invariant 1).
//
// Returns raw hypergraph data as S2HResult for reconstruction by the Python
// shim (``_cpp_string_to_hypergraph`` in string_to_hypergraph.py).
#pragma once

#include <string>
#include <vector>

#include "isalhg/cdll.hpp"  // NodeId

namespace isalhg {

// Raw output of the C++ S2H interpreter.
struct S2HResult {
    int n_vertex_labels;
    int n_edge_labels;
    // vertex_labels[v] = label of node v (ordered by node id; size = n_nodes).
    std::vector<NodeId> vertex_labels;
    // edge_labels[e] = edge label (ordered by insertion order).
    std::vector<int> edge_labels;
    // edge_members[e] = member node ids, in pointer-collection order (existing
    // first, then new nodes in insertion order). Python shim passes to
    // SparseHypergraph.add_hyperedge which converts to frozenset internally.
    std::vector<std::vector<NodeId>> edge_members;
};

// Execute the Sigma_HG* string ``s`` on a fresh VM and return the
// resulting hypergraph.
//
// Parameters
// ----------
// s : Sigma_HG* string to decode (semicolon-separated tokens).
// k : VM pointer count; must be >= max_arity of any V/C token in s.
// n_vertex_labels, n_edge_labels : vocabulary sizes (decision I45).
// seed_label : label of the initial seed vertex (default 0).
//
// Throws ``IsalHGError`` on malformed tokens or VM errors.
[[nodiscard]] S2HResult string_to_hypergraph_compute(
    const std::string& s,
    int k,
    int n_vertex_labels = 1,
    int n_edge_labels = 1,
    int seed_label = 0);

}  // namespace isalhg
