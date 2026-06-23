// Greedy H2S with bounded backtracking on V-emission label permutations.
//
// Public entry: greedy_h2s_str() returns the serialised canonical string
// for the given seed. The Python shim calls into this and parses back to
// a list[Token] (Phase 1) or compares strings directly (Phase 3).
#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

#include "isalhg/sparse_hypergraph.hpp"
#include "isalhg/token.hpp"

namespace isalhg {

// Returns the serialised greedy H2S output for the given seed.
//
// Parameters
// ----------
// H : SHG view, finalised.
// seed_node : node id placed at slot 0.
// k : VM pointer count; must be >= max arity.
// wl_colors : optional length-n_nodes array; when present, prunes the
//   V-branch permutation set to canonical-orbit reps (matches Python
//   wl_colors=... behaviour in greedy_h2s).
//
// Throws ``H2SStuckError`` when the encoder cannot make progress from a
// non-terminal state.
[[nodiscard]] std::string greedy_h2s_str(
    const SHG& H,
    NodeId seed_node,
    int k,
    const std::optional<std::vector<std::int64_t>>& wl_colors = std::nullopt);

// Variant returning the token vector (for the differential test).
[[nodiscard]] std::vector<Token> greedy_h2s_tokens(
    const SHG& H,
    NodeId seed_node,
    int k,
    const std::optional<std::vector<std::int64_t>>& wl_colors = std::nullopt);

}  // namespace isalhg
