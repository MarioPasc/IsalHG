// Canonical-string entry point.
//
// Runs the full multi-seed loop in C++ so the SHG view is built once per
// canonical_string call instead of once per seed. Dispatches on an
// AlgorithmVariant enum that covers the five fast registry names; the
// two exhaustive variants stay in pure Python.
#pragma once

#include <cstdint>
#include <string>

#include "isalhg/sparse_hypergraph.hpp"

namespace isalhg {

enum class AlgorithmVariant : std::uint8_t {
    GreedyMin              = 0,
    GreedySingle           = 1,
    GreedyMinInplace       = 2,  // identical output to GreedyMin
    GreedyMinWlPruned      = 3,
    GreedyMinInplaceWlPruned = 4,  // identical output to GreedyMinWlPruned
};

// Compute the canonical Sigma_HG* string for ``H``.
//
// Parameters
// ----------
// H : SHG view (finalised at the FFI boundary).
// k : VM pointer count; must be >= max arity.
// structural_depth : depth for xi/eta seed-selection.
// variant : which algorithm flavour to run.
//
// Throws ``DisconnectedHypergraphError`` if H is disconnected.
[[nodiscard]] std::string canonical_string_compute(const SHG& H, int k, int structural_depth,
                                                   AlgorithmVariant variant);

// Return required_k(H) = max(2, max arity).
[[nodiscard]] int required_k_compute(const SHG& H);

}  // namespace isalhg
