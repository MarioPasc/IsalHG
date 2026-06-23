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

}  // namespace isalhg
