// Read-only C++ view over an isalhg.core.SparseHypergraph.
//
// Built once at the FFI boundary from the Python object. Pre-computes
// the primal adjacency, per-vertex xi (depth=3 by default), and per-edge
// eta so the encoder inner loop runs in pure C++ with O(1) eta lookups.
#pragma once

#include <cstdint>
#include <vector>

#include "isalhg/cdll.hpp"  // NodeId, SlotIdx

namespace isalhg {

using EdgeId       = std::int32_t;
using VertexLabel  = std::int32_t;
using EdgeLabel    = std::int32_t;

// Default xi/eta depth (DEFAULT_DEPTH in structural_tuples.py).
constexpr int DEFAULT_STRUCTURAL_DEPTH = 3;

struct SHG {
    std::int32_t n_nodes = 0;
    std::int32_t n_edges = 0;
    std::int32_t n_vertex_labels = 1;
    std::int32_t n_edge_labels = 1;
    // max arity over all edges (>= 2 by construction; 0 if edgeless). Set by
    // finalise(). Pointers beyond this index can never satisfy a V/C emission,
    // so the displacement search only varies the first min(k, max_arity) ones.
    std::int32_t max_arity = 0;

    // Per-vertex label.
    std::vector<VertexLabel> vertex_labels;          // size n_nodes
    // Per-edge label.
    std::vector<EdgeLabel> edge_labels;              // size n_edges
    // Edge -> sorted member ids. Sorted vector beats unordered_set at
    // arity <= K_MAX: linear search is ~3 comparisons average; the set
    // form is membership-only and we never need iteration ordering.
    std::vector<std::vector<NodeId>> edge_members;   // size n_edges
    // Vertex -> incident edge ids.
    std::vector<std::vector<EdgeId>> vertex_edges;   // size n_nodes
    // Vertex -> sorted primal-graph neighbours (used by structural_tuples).
    std::vector<std::vector<NodeId>> primal_adj;     // size n_nodes
    // Cached eta(e, depth) for the depth fixed at construction.
    std::vector<std::vector<std::int32_t>> eta_cache;  // size n_edges, inner size depth

    // Test whether ``v`` is a member of edge ``e`` (O(arity)).
    [[nodiscard]] bool edge_contains(EdgeId e, NodeId v) const noexcept;

    // Eta lookup; O(1) after construction (relies on cache filled by build).
    [[nodiscard]] const std::vector<std::int32_t>& eta(EdgeId e) const noexcept {
        return eta_cache[static_cast<std::size_t>(e)];
    }

    // Build the SHG from raw data. depth defaults to 3.
    void finalise(int depth = DEFAULT_STRUCTURAL_DEPTH);
};

// Compute xi(v, depth) as a length-``depth`` tuple of shell sizes.
// Used internally by finalise(); exposed for tests / structural tuples.
[[nodiscard]] std::vector<std::int32_t> xi_counts(const SHG& H, NodeId v, int depth);

}  // namespace isalhg
