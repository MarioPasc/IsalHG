// Structural tuples xi/eta + seed selection (max_xi_nodes).
//
// xi_h(v) = number of primal-graph neighbours of v at distance exactly h.
// xi_labelled_h(v, lab) = number of such neighbours with vertex_label == lab.
// max_xi_nodes picks the lex-max-(xi_labelled, vertex_label) node set.
#pragma once

#include <cstdint>
#include <vector>

#include "isalhg/sparse_hypergraph.hpp"

namespace isalhg {

// Per-shell label counts: out[h][lab] = #(vertices at distance h from v with label lab).
[[nodiscard]] std::vector<std::vector<std::int32_t>>
xi_labelled_counts(const SHG& H, NodeId v, int depth);

// The argmax-lex set of nodes under (xi_labelled(v), vertex_label(v)).
// Returns sorted vector of node ids.
[[nodiscard]] std::vector<NodeId> max_xi_nodes_compute(const SHG& H, int depth);

// Cheaper iso-invariant seed selector (PI 2026-06-23):
//
//   step 1: keep nodes whose vertex_label is the per-graph maximum.
//   step 2: from those, keep nodes whose primal-graph degree is maximum.
//   step 3: for each surviving node v, build the descending-sorted list of
//           its neighbours' primal-graph degrees; keep nodes whose list is
//           lexicographically maximum.
//
// Returns the lex-max set as a sorted-by-node-id vector. Iso-invariance:
// vertex labels, primal-graph degree, and the sorted-multiset of neighbour
// degrees are all preserved by any vertex permutation that is a hypergraph
// isomorphism. The cascade is strictly cheaper than ``max_xi_nodes_compute``
// (no depth-3 BFS), and on non-vertex-transitive inputs is typically more
// discriminating than max-xi alone — yielding fewer seeds and a shorter
// canonical_string lex-min loop.
[[nodiscard]] std::vector<NodeId> max_neighbor_degree_nodes_compute(const SHG& H);

}  // namespace isalhg
