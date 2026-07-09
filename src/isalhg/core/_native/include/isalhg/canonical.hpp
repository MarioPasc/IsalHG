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
    // PI 2026-06-23 — replace max-xi seed selector with the (label, degree,
    // sorted-desc neighbour degrees) cascade. Output is identical to
    // GreedyMin / GreedySingle on any input where both seed sets coincide;
    // on non-vertex-transitive inputs the new selector typically yields
    // fewer seeds and a strictly faster canonical_string call.
    GreedyMinNbrDeg          = 5,
    GreedySingleNbrDeg       = 6,
    // T-TAd/T-TAa — neighbour-degree seed set plus tie-complete V branching.
    // The only variant whose w* is a complete isomorphism invariant: the
    // others resolve the residual V tie by raw edge id and are therefore
    // functions of the presentation (edge insertion order).
    GreedyMinComplete        = 7,
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
// Throws ``CanonicalizationTimeoutError`` when ``max_expansions > 0`` and any
// per-seed greedy run exceeds that many V-branch (tie-branch) recursions.
[[nodiscard]] std::string canonical_string_compute(const SHG& H, int k, int structural_depth,
                                                   AlgorithmVariant variant,
                                                   int max_expansions = 0);

// Return required_k(H) = max(2, max arity).
[[nodiscard]] int required_k_compute(const SHG& H);

}  // namespace isalhg
