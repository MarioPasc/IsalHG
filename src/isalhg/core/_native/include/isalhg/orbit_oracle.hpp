// Stabiliser-orbit oracle interface for the tie-complete search.
//
// The tie-complete encoder branches over the full residual tie set and, per
// tied edge, over every label-respecting ordering of its new vertices. On
// symmetric inputs that branch set is dominated by automorphic duplicates.
// Proposition 7.3 of the ordered-walk completeness note licenses keeping one
// representative per orbit of the automorphism group fixing the placed prefix:
// two candidates in the same orbit yield equal completions, so the shortlex
// minimum over the tie set equals the minimum over the representatives. The
// pruned search is therefore *value-preserving* -- it returns the frozen
// ``w*_c`` bit for bit, unlike a tie-set refinement (also complete, but a
// different canonical form; forbidden by D-TA2).
//
// The groups themselves are NOT computed here: this core is stdlib-only and
// carries no graph-automorphism engine. The interface is a callback the caller
// implements; the production implementation is the nanobind adapter in
// ``bindings.cpp``, which forwards to the Python
// ``isalhg.iso_backends.orbit_oracle.PynautyOrbitOracle`` (individualised Levi
// colouring + ``pynauty.autgrp`` + union-find orbits).
//
// Every method receives the candidate sequence the unpruned search would
// branch over and returns a subsequence holding one element per orbit, in
// input order. Returning the input unchanged is always legal -- that is the
// unpruned search. The encoder consumes the answer verbatim (beyond dropping
// tied edges the oracle did not return); it never re-sorts or re-filters,
// because any representative is value-equivalent and fixing the choice is what
// keeps the pruned search reproducible.
#pragma once

#include <atomic>
#include <cstdint>
#include <vector>

#include "isalhg/sparse_hypergraph.hpp"

namespace isalhg {

// Diagnostic counters for one canonical_string_compute call.
//
// Mirrors the ``stats`` dict of the Python reference
// (``_encode_from(stats=...)``) term for term:
//   frames       -- one per ``encode_from`` entry, terminal frames included.
//   v_branches   -- one per V branch actually run (edge x ordering).
//   oracle_calls -- edge + ordering oracle invocations made by the encoder.
//                   The single ``seed_representatives`` call is counted
//                   separately in ``seed_oracle_calls`` so this field stays
//                   comparable with the Python counter.
// Atomic because the seed loop may run on the thread pool (it does not for the
// orbit variant, which is forced sequential, but the counters are also
// collected for the unpruned variant, whose seeds do fan out).
struct SearchCounters {
    std::atomic<std::int64_t> frames{0};
    std::atomic<std::int64_t> v_branches{0};
    std::atomic<std::int64_t> oracle_calls{0};
    std::atomic<std::int64_t> seed_oracle_calls{0};
    std::atomic<std::int64_t> seeds_run{0};
};

// Callback consulted at every residual tie of the tie-complete search.
//
// Node and edge ids are the ids of the *input* hypergraph (the SHG view keeps
// the Python ``SparseHypergraph`` numbering unchanged), so an implementation
// backed by the Python object needs no remapping.
class OrbitOracleIface {
public:
    OrbitOracleIface() = default;
    virtual ~OrbitOracleIface() = default;
    OrbitOracleIface(const OrbitOracleIface&) = delete;
    OrbitOracleIface& operator=(const OrbitOracleIface&) = delete;

    // One seed per Aut(H)-orbit of ``seeds``, in input order.
    [[nodiscard]] virtual std::vector<NodeId> seed_representatives(
        const std::vector<NodeId>& seeds) = 0;

    // One edge per G_sigma-orbit of ``tied``, in input order. ``placed`` is
    // ``dom mu``: the input node ids already mapped, in creation (output-id)
    // order.
    [[nodiscard]] virtual std::vector<EdgeId> edge_representatives(
        const NodeId* placed, int n_placed, const std::vector<EdgeId>& tied) = 0;

    // One ordering per G_{sigma,e}-orbit of ``orderings``, in input order.
    //
    // ``orderings`` is row-major: ``n_orderings`` rows of ``n_new`` node ids.
    // The return value is the same layout, holding the representative rows;
    // its size is always a multiple of ``n_new``.
    [[nodiscard]] virtual std::vector<NodeId> ordering_representatives(
        const NodeId* placed, int n_placed, EdgeId edge, const NodeId* orderings,
        int n_orderings, int n_new) = 0;
};

}  // namespace isalhg
