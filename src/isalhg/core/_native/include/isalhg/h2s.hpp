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

#include "isalhg/orbit_oracle.hpp"
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
// tie_branch : when true, recurse over every V candidate tying on the
//   iso-invariant cascade key-prefix (i, j, edge_label, sorted new labels,
//   eta) instead of committing to the min-edge-id one, and keep the
//   lex-min completion. Removes edge ids from observable behaviour, making
//   the per-seed output isomorphism-equivariant. Mirrors the Python
//   ``_python_greedy_h2s(tie_branch=True)`` reference bit-for-bit.
// max_expansions : V-branch recursion budget per call; 0 = unlimited.
// ranks : when non-null, per-vertex canonical ranks (a permutation of
//   0..n-1) replacing, at every frame, the residual edge-id tie-break by
//   ``(sorted ranks of the edge's unplaced members, sorted ranks of its
//   pointed members)`` and the label-respecting orderings by the single
//   ascending ``(label, rank)`` order. Both branch sets collapse to a
//   singleton, so the walk becomes one deterministic path. Mutually
//   exclusive with ``tie_branch`` -- it is a different canonical program
//   (``canonical_rank``), not a pruning of ``w*_c``. Mirrors the Python
//   ``_python_greedy_h2s(ranks=...)`` reference bit-for-bit. The pointer is
//   borrowed; it must outlive the call.
// orbit_oracle : when non-null and ``tie_branch`` is set, the residual tie set
//   and the label-respecting orderings are each reduced to one representative
//   per stabiliser orbit before branching. Value-preserving: the returned
//   token sequence is unchanged (Proposition 7.3), only the search is smaller.
//   Ignored without ``tie_branch`` (the other variants branch over nothing).
//   The oracle may call back into Python, so a run using one must be
//   single-threaded. The pointer is borrowed; it must outlive the call.
// counters : when non-null, the diagnostic counters are accumulated into it.
//   Purely observational; it never changes the output.
//
// Throws ``H2SStuckError`` when the encoder cannot make progress from a
// non-terminal state.
// Throws ``CanonicalizationTimeoutError`` when ``max_expansions > 0`` and the
// number of V-branch recursions (tie-branch entries) exceeds the limit.
// Throws ``IsalHGError`` when ``ranks`` is combined with ``tie_branch`` or with
// ``orbit_oracle``, or when its length does not match ``H.n_nodes``.
[[nodiscard]] std::string greedy_h2s_str(
    const SHG& H,
    NodeId seed_node,
    int k,
    bool tie_branch = false,
    int max_expansions = 0,
    const std::vector<std::int32_t>* ranks = nullptr,
    OrbitOracleIface* orbit_oracle = nullptr,
    SearchCounters* counters = nullptr);

// Variant returning the token vector (for differential tests and canonical_string_compute).
[[nodiscard]] std::vector<Token> greedy_h2s_tokens(
    const SHG& H,
    NodeId seed_node,
    int k,
    bool tie_branch = false,
    int max_expansions = 0,
    const std::vector<std::int32_t>* ranks = nullptr,
    OrbitOracleIface* orbit_oracle = nullptr,
    SearchCounters* counters = nullptr);

}  // namespace isalhg
