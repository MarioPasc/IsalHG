#include "isalhg/canonical.hpp"

#include <algorithm>
#include <future>
#include <queue>
#include <thread>
#include <vector>

#include "isalhg/errors.hpp"
#include "isalhg/h2s.hpp"
#include "isalhg/structural_tuples.hpp"
#include "isalhg/thread_pool.hpp"
#include "isalhg/token.hpp"
#include "isalhg/wl.hpp"

namespace isalhg {

int required_k_compute(const SHG& H) {
    if (H.n_edges == 0) return 2;
    int max_arity = 2;
    for (const auto& members : H.edge_members) {
        const int a = static_cast<int>(members.size());
        if (a > max_arity) max_arity = a;
    }
    return max_arity < 2 ? 2 : max_arity;
}

namespace {

[[nodiscard]] bool is_connected(const SHG& H) {
    if (H.n_nodes == 0) return true;
    std::vector<std::uint8_t> seen(static_cast<std::size_t>(H.n_nodes), 0);
    std::queue<NodeId> q;
    seen[0] = 1;
    q.push(0);
    std::int32_t count = 1;
    while (!q.empty()) {
        const NodeId v = q.front();
        q.pop();
        for (NodeId w : H.primal_adj[static_cast<std::size_t>(v)]) {
            if (!seen[static_cast<std::size_t>(w)]) {
                seen[static_cast<std::size_t>(w)] = 1;
                ++count;
                q.push(w);
            }
        }
    }
    return count == H.n_nodes;
}

}  // namespace

std::string canonical_string_compute(const SHG& H, int k, int structural_depth,
                                     AlgorithmVariant variant) {
    if (H.n_nodes == 0) return "";
    if (!is_connected(H)) {
        throw DisconnectedHypergraphError(
            "canonical_string requires a connected hypergraph (decision B11)");
    }

    std::vector<NodeId> seeds = max_xi_nodes_compute(H, structural_depth);
    if (seeds.empty()) return "";

    // Variant-specific seed filtering.
    if (variant == AlgorithmVariant::GreedySingle) {
        // Smallest-id tiebreak.
        seeds.resize(1);  // max_xi_nodes_compute returns ascending node-id order.
    } else if (variant == AlgorithmVariant::GreedyMinWlPruned
               || variant == AlgorithmVariant::GreedyMinInplaceWlPruned) {
        // Keep seeds whose WL colour equals the lex-min WL colour among the
        // max-xi set. (See greedy_min_wl_pruned.py._wl_filtered_seeds.)
        const auto wl = wl_hash_compute(H);
        std::uint64_t min_col = wl[static_cast<std::size_t>(seeds.front())];
        for (NodeId s : seeds) {
            const std::uint64_t c = wl[static_cast<std::size_t>(s)];
            if (c < min_col) min_col = c;
        }
        std::vector<NodeId> filtered;
        filtered.reserve(seeds.size());
        for (NodeId s : seeds) {
            if (wl[static_cast<std::size_t>(s)] == min_col) filtered.push_back(s);
        }
        seeds.swap(filtered);
    }
    // GreedyMin / GreedyMinInplace keep all max-xi seeds.

    // None of the five fast variants pass wl_colors into greedy_h2s (see
    // greedy_min_wl_pruned.py — V-branch pruning is intentionally disabled).
    const std::optional<std::vector<std::int64_t>> wl_for_h2s = std::nullopt;

    // Multi-seed parallelism via a persistent thread pool. Each seed
    // runs an independent ``greedy_h2s_tokens`` over a shared read-only
    // ``SHG``; the per-seed ``EncoderState`` is thread-local. Workers
    // are reused across canonical_string calls, so back-to-back
    // fingerprinting (e.g. dataset sweeps) doesn't pay thread-creation
    // costs again. Single-seed (greedy_single) is sequential.
    // The caller releases the GIL at the FFI boundary so the C++ workers
    // don't contend with Python.
    const std::size_t n_seeds = seeds.size();
    std::vector<std::vector<Token>> per_seed(n_seeds);
    auto& pool = canonical_thread_pool();
    const bool parallel = (n_seeds >= 2 && pool.size() >= 2);
    if (parallel) {
        const std::size_t max_jobs = std::min<std::size_t>(pool.size(), n_seeds);
        std::vector<std::future<void>> futures;
        futures.reserve(max_jobs);
        std::atomic<std::size_t> next_idx{0};
        for (std::size_t w = 0; w < max_jobs; ++w) {
            futures.push_back(pool.submit([&]() {
                while (true) {
                    const std::size_t i =
                        next_idx.fetch_add(1, std::memory_order_relaxed);
                    if (i >= n_seeds) return;
                    per_seed[i] = greedy_h2s_tokens(H, seeds[i], k, wl_for_h2s);
                }
            }));
        }
        for (auto& f : futures) f.get();
    } else {
        for (std::size_t i = 0; i < n_seeds; ++i) {
            per_seed[i] = greedy_h2s_tokens(H, seeds[i], k, wl_for_h2s);
        }
    }

    bool have_best = false;
    std::vector<Token> best_tokens;
    for (auto& toks : per_seed) {
        if (!have_best || sequence_cmp(toks, best_tokens) < 0) {
            best_tokens = std::move(toks);
            have_best = true;
        }
    }
    return serialize(best_tokens);
}

}  // namespace isalhg
