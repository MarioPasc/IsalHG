#include "isalhg/sparse_hypergraph.hpp"

#include <algorithm>
#include <unordered_set>

namespace isalhg {

bool SHG::edge_contains(EdgeId e, NodeId v) const noexcept {
    const auto& members = edge_members[static_cast<std::size_t>(e)];
    // Sorted vector linear search (arity small).
    for (NodeId m : members) {
        if (m == v) return true;
        if (m > v) return false;
    }
    return false;
}

std::vector<std::int32_t> xi_counts(const SHG& H, NodeId v, int depth) {
    std::vector<std::int32_t> out(static_cast<std::size_t>(std::max(0, depth)), 0);
    if (depth < 1 || H.n_nodes == 0) return out;

    // BFS using a flat seen-array (avoids std::set overhead for n <= a few thousand).
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
            const auto& nbrs = H.primal_adj[static_cast<std::size_t>(u)];
            for (NodeId w : nbrs) {
                if (!seen[static_cast<std::size_t>(w)]) {
                    seen[static_cast<std::size_t>(w)] = 1;
                    next_frontier.push_back(w);
                }
            }
        }
        out[static_cast<std::size_t>(h)] = static_cast<std::int32_t>(next_frontier.size());
        frontier.swap(next_frontier);
    }
    return out;
}

void SHG::finalise(int depth) {
    // 1. Build vertex_edges from edge_members; record the max arity.
    vertex_edges.assign(static_cast<std::size_t>(n_nodes), {});
    max_arity = 0;
    for (EdgeId e = 0; e < n_edges; ++e) {
        const auto& members = edge_members[static_cast<std::size_t>(e)];
        if (static_cast<std::int32_t>(members.size()) > max_arity) {
            max_arity = static_cast<std::int32_t>(members.size());
        }
        for (NodeId v : members) {
            vertex_edges[static_cast<std::size_t>(v)].push_back(e);
        }
    }

    // 2. Build primal_adj. Two members of the same hyperedge are connected.
    //    Use a per-vertex unordered_set during build to dedup, then convert
    //    to a sorted vector for the cache.
    std::vector<std::unordered_set<NodeId>> adj_set(static_cast<std::size_t>(n_nodes));
    for (const auto& members : edge_members) {
        for (std::size_t a = 0; a < members.size(); ++a) {
            for (std::size_t b = a + 1; b < members.size(); ++b) {
                adj_set[static_cast<std::size_t>(members[a])].insert(members[b]);
                adj_set[static_cast<std::size_t>(members[b])].insert(members[a]);
            }
        }
    }
    primal_adj.assign(static_cast<std::size_t>(n_nodes), {});
    for (NodeId v = 0; v < n_nodes; ++v) {
        const auto& s = adj_set[static_cast<std::size_t>(v)];
        primal_adj[static_cast<std::size_t>(v)].assign(s.begin(), s.end());
        std::sort(primal_adj[static_cast<std::size_t>(v)].begin(),
                  primal_adj[static_cast<std::size_t>(v)].end());
    }

    // 3. Cache eta(e, depth) = sum_{v in e} xi(v, depth).
    eta_cache.assign(static_cast<std::size_t>(n_edges),
                     std::vector<std::int32_t>(static_cast<std::size_t>(std::max(0, depth)), 0));
    if (depth >= 1) {
        std::vector<std::vector<std::int32_t>> xi_per_v(static_cast<std::size_t>(n_nodes));
        for (NodeId v = 0; v < n_nodes; ++v) {
            xi_per_v[static_cast<std::size_t>(v)] = xi_counts(*this, v, depth);
        }
        for (EdgeId e = 0; e < n_edges; ++e) {
            auto& acc = eta_cache[static_cast<std::size_t>(e)];
            for (NodeId v : edge_members[static_cast<std::size_t>(e)]) {
                const auto& xv = xi_per_v[static_cast<std::size_t>(v)];
                for (std::size_t h = 0; h < acc.size(); ++h) {
                    acc[h] += xv[h];
                }
            }
        }
    }
}

}  // namespace isalhg
