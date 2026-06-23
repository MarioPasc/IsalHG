#include "isalhg/structural_tuples.hpp"

#include <algorithm>

namespace isalhg {

std::vector<std::vector<std::int32_t>> xi_labelled_counts(const SHG& H, NodeId v, int depth) {
    const int sigma_v = std::max(1, H.n_vertex_labels);
    std::vector<std::vector<std::int32_t>> out(
        static_cast<std::size_t>(std::max(0, depth)),
        std::vector<std::int32_t>(static_cast<std::size_t>(sigma_v), 0));
    if (depth < 1 || H.n_nodes == 0) return out;

    std::vector<std::uint8_t> seen(static_cast<std::size_t>(H.n_nodes), 0);
    std::vector<NodeId> frontier;
    std::vector<NodeId> next_frontier;
    frontier.reserve(static_cast<std::size_t>(H.n_nodes));
    next_frontier.reserve(static_cast<std::size_t>(H.n_nodes));

    seen[static_cast<std::size_t>(v)] = 1;
    frontier.push_back(v);

    for (int h = 0; h < depth; ++h) {
        next_frontier.clear();
        for (NodeId u : frontier) {
            for (NodeId w : H.primal_adj[static_cast<std::size_t>(u)]) {
                if (!seen[static_cast<std::size_t>(w)]) {
                    seen[static_cast<std::size_t>(w)] = 1;
                    next_frontier.push_back(w);
                }
            }
        }
        auto& counts = out[static_cast<std::size_t>(h)];
        for (NodeId w : next_frontier) {
            const int lab = H.vertex_labels[static_cast<std::size_t>(w)];
            ++counts[static_cast<std::size_t>(lab)];
        }
        frontier.swap(next_frontier);
    }
    return out;
}

namespace {

// Lex compare two label-count tuples (flattened representation).
int compare_xi_keys(const std::vector<std::vector<std::int32_t>>& a,
                    const std::vector<std::vector<std::int32_t>>& b) noexcept {
    const std::size_t common_h = std::min(a.size(), b.size());
    for (std::size_t h = 0; h < common_h; ++h) {
        const auto& ah = a[h];
        const auto& bh = b[h];
        const std::size_t common_l = std::min(ah.size(), bh.size());
        for (std::size_t l = 0; l < common_l; ++l) {
            if (ah[l] != bh[l]) return ah[l] < bh[l] ? -1 : 1;
        }
        if (ah.size() != bh.size()) return ah.size() < bh.size() ? -1 : 1;
    }
    if (a.size() != b.size()) return a.size() < b.size() ? -1 : 1;
    return 0;
}

}  // namespace

std::vector<NodeId> max_xi_nodes_compute(const SHG& H, int depth) {
    std::vector<NodeId> out;
    if (H.n_nodes == 0) return out;

    // Compute (xi_labelled(v), vertex_label(v)) per vertex.
    std::vector<std::vector<std::vector<std::int32_t>>> xi_per_v(
        static_cast<std::size_t>(H.n_nodes));
    for (NodeId v = 0; v < H.n_nodes; ++v) {
        xi_per_v[static_cast<std::size_t>(v)] = xi_labelled_counts(H, v, depth);
    }

    // Find lex-max key across (xi_labelled, vertex_label).
    NodeId best = 0;
    auto better_than_best = [&](NodeId cand) -> bool {
        const int c = compare_xi_keys(xi_per_v[static_cast<std::size_t>(cand)],
                                      xi_per_v[static_cast<std::size_t>(best)]);
        if (c != 0) return c > 0;
        return H.vertex_labels[static_cast<std::size_t>(cand)]
                   > H.vertex_labels[static_cast<std::size_t>(best)];
    };
    for (NodeId v = 1; v < H.n_nodes; ++v) {
        if (better_than_best(v)) best = v;
    }

    // Collect all vertices matching the best key.
    for (NodeId v = 0; v < H.n_nodes; ++v) {
        const int c = compare_xi_keys(xi_per_v[static_cast<std::size_t>(v)],
                                      xi_per_v[static_cast<std::size_t>(best)]);
        if (c == 0 && H.vertex_labels[static_cast<std::size_t>(v)]
                          == H.vertex_labels[static_cast<std::size_t>(best)]) {
            out.push_back(v);
        }
    }
    return out;
}

}  // namespace isalhg
