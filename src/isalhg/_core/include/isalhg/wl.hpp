// Weisfeiler-Leman colour refinement on hypergraph incidence.
//
// Uses FNV-1a 64-bit so the colour partition is cross-process stable
// (Python's hash() is salted; this implementation is not). Caller-side
// Python shim shares the same FNV-1a constants -> byte-equal output.
#pragma once

#include <cstdint>
#include <unordered_map>
#include <vector>

#include "isalhg/sparse_hypergraph.hpp"

namespace isalhg {

constexpr int WL_MAX_ROUNDS = 64;

// Per-vertex stable WL colour (raw uint64); equality => WL-equivalent.
[[nodiscard]] std::vector<std::uint64_t> wl_hash_compute(const SHG& H, int max_rounds = WL_MAX_ROUNDS);

// Group node ids by stable colour; values sorted in ascending node-id order.
[[nodiscard]] std::unordered_map<std::uint64_t, std::vector<NodeId>>
wl_partition_compute(const SHG& H, int max_rounds = WL_MAX_ROUNDS);

}  // namespace isalhg
