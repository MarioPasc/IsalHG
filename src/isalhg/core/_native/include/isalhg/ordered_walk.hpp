// The ordered walk OW_pi -- a deterministic Isal program along a canonical order.
//
// Bit-identical port of ``src/isalhg/core/algorithms/ordered_walk.py`` (Definition 3.2
// of theorem_c_ordered_walk.tex). The Python module stays the reference; this is the
// engine the article runs on. Every ordering decision below mirrors a Python tuple
// comparison, so the two emitters agree token for token on every input and policy.
//
// The Python emitter carries a CDLL purely as a slot allocator: ``_slot_of`` is a
// bijection onto the constants and ``_order`` is maintained by explicit splicing.
// Here the constants index the order vector directly -- no CDLL, same semantics.
#pragma once

#include <cstdint>
#include <vector>

#include "isalhg/sparse_hypergraph.hpp"
#include "isalhg/token.hpp"

namespace isalhg {

// Root rule of OrderedWalkPolicy.root_rule.
enum class OwRootRule : std::uint8_t {
    Hub = 0,    // argmax (deg_E, type, -rank)
    Rank0 = 1,  // the constant nauty ranks first
};

struct OwPolicy {
    OwRootRule root_rule = OwRootRule::Hub;
    // false = ow-struct (rank decides inside a signature class);
    // true  = ow-rank   (rank moves ahead of the predicate in K_V).
    bool rank_first = false;
};

struct OwResult {
    NodeId root = 0;
    VertexLabel root_label = 0;
    std::vector<Token> tokens;
    std::vector<NodeId> creation_order;
};

// Emit the ordered-walk program of ``H`` under ``ranks`` and ``policy``.
//
// ``ranks`` must be a permutation of 0..n_nodes-1 and ``H`` connected with at least
// one constant; both preconditions are checked by the Python wrapper, which owns the
// DegenerateHypergraphError / DisconnectedHypergraphError / OrderedWalkError contract.
//
// Throws isalhg::IsalHGError if the V-phase runs out of frontier facts (unreachable
// on connected input) or if ``ranks`` has the wrong length.
[[nodiscard]] OwResult ordered_walk_compute(const SHG& H,
                                            const std::vector<std::int32_t>& ranks,
                                            const OwPolicy& policy);

}  // namespace isalhg
