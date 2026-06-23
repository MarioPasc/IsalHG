// Encoder state for greedy H2S, with inplace + undo log.
//
// State is C++-internal; never crosses the FFI. The undo log lives on
// the stack during recursion (V branches allocate ``j <= MAX_NEW`` records).
#pragma once

#include <array>
#include <cstdint>
#include <vector>

#include "isalhg/cdll.hpp"
#include "isalhg/sparse_hypergraph.hpp"
#include "isalhg/token.hpp"  // K_MAX, MAX_NEW

namespace isalhg {

// Undo record for a single V-step insertion.
struct VStepUndo {
    SlotIdx slot;
    NodeId  input_v;
    NodeId  out_v;
};

struct EncoderState {
    Cdll cdll;
    std::array<SlotIdx, K_MAX> pointers{};
    // i2o[v] = output id, or -1 if v not yet mapped. Sized to n_nodes.
    std::vector<NodeId> i2o;
    // o2i[u] = input id, or -1 if u not yet allocated. Sized to n_nodes.
    std::vector<NodeId> o2i;
    // consumed[e] = true if edge e has been emitted.
    std::vector<std::uint8_t> consumed;  // bool but easier UB/ASan-wise
    NodeId next_output_id = 0;
    int k = 0;
    NodeId n_nodes = 0;
    EdgeId n_edges = 0;

    EncoderState(NodeId n_nodes_, EdgeId n_edges_, int k_, NodeId seed_node)
        : cdll(std::max(1, n_nodes_)),
          i2o(static_cast<std::size_t>(n_nodes_), -1),
          o2i(static_cast<std::size_t>(n_nodes_), -1),
          consumed(static_cast<std::size_t>(n_edges_), 0),
          k(k_),
          n_nodes(n_nodes_),
          n_edges(n_edges_) {
        SlotIdx seed_slot = cdll.insert_after(0, 0);
        for (int idx = 0; idx < K_MAX; ++idx) {
            pointers[idx] = seed_slot;
        }
        i2o[static_cast<std::size_t>(seed_node)] = 0;
        o2i[0] = seed_node;
        next_output_id = 1;
    }

    [[nodiscard]] SlotIdx get_ptr(int i_1based) const noexcept {
        return pointers[static_cast<std::size_t>(i_1based - 1)];
    }

    [[nodiscard]] bool i2o_has(NodeId v) const noexcept {
        return i2o[static_cast<std::size_t>(v)] != -1;
    }

    // Convenience: count of currently mapped input nodes. O(n) but only
    // called at recursion entry (cheap relative to the body).
    [[nodiscard]] std::int32_t i2o_count() const noexcept {
        std::int32_t c = 0;
        for (auto v : i2o) {
            if (v != -1) ++c;
        }
        return c;
    }

    [[nodiscard]] std::int32_t consumed_count() const noexcept {
        std::int32_t c = 0;
        for (auto b : consumed) {
            if (b) ++c;
        }
        return c;
    }
};

}  // namespace isalhg
