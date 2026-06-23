#include "isalhg/wl.hpp"

#include <algorithm>
#include <unordered_map>

#include "isalhg/fnv.hpp"

namespace isalhg {

namespace {

// True iff ``a`` and ``b`` induce the same partition. Colours are opaque so
// we relabel by first-appearance order before comparing.
[[nodiscard]] bool partition_equiv(const std::vector<std::uint64_t>& a,
                                   const std::vector<std::uint64_t>& b) noexcept {
    if (a.size() != b.size()) return false;
    std::unordered_map<std::uint64_t, std::int32_t> map_a;
    std::unordered_map<std::uint64_t, std::int32_t> map_b;
    map_a.reserve(a.size());
    map_b.reserve(b.size());
    std::int32_t next_a = 0;
    std::int32_t next_b = 0;
    for (std::size_t i = 0; i < a.size(); ++i) {
        auto [it_a, ins_a] = map_a.emplace(a[i], next_a);
        if (ins_a) ++next_a;
        auto [it_b, ins_b] = map_b.emplace(b[i], next_b);
        if (ins_b) ++next_b;
        if (it_a->second != it_b->second) return false;
    }
    return true;
}

}  // namespace

std::vector<std::uint64_t> wl_hash_compute(const SHG& H, int max_rounds) {
    std::vector<std::uint64_t> colours(static_cast<std::size_t>(H.n_nodes), 0);
    if (H.n_nodes == 0) return colours;

    for (NodeId v = 0; v < H.n_nodes; ++v) {
        std::uint64_t h = fnv1a_init(FNV_DOMAIN_VERTEX_INIT);
        h = fnv1a_mix(h, static_cast<std::uint64_t>(H.vertex_labels[static_cast<std::size_t>(v)]));
        colours[static_cast<std::size_t>(v)] = h;
    }

    if (H.n_edges == 0) return colours;

    std::vector<std::uint64_t> edge_sigs(static_cast<std::size_t>(H.n_edges), 0);
    std::vector<std::uint64_t> new_colours(static_cast<std::size_t>(H.n_nodes), 0);
    std::vector<std::uint64_t> tmp_sigs;

    for (int round = 0; round < max_rounds; ++round) {
        // Edge signatures: hash(domain, edge_label, sorted_colours_of_members).
        for (EdgeId e = 0; e < H.n_edges; ++e) {
            tmp_sigs.clear();
            for (NodeId u : H.edge_members[static_cast<std::size_t>(e)]) {
                tmp_sigs.push_back(colours[static_cast<std::size_t>(u)]);
            }
            std::sort(tmp_sigs.begin(), tmp_sigs.end());
            std::uint64_t h = fnv1a_init(FNV_DOMAIN_EDGE_SIG);
            h = fnv1a_mix(
                h, static_cast<std::uint64_t>(H.edge_labels[static_cast<std::size_t>(e)]));
            for (std::uint64_t c : tmp_sigs) h = fnv1a_mix(h, c);
            edge_sigs[static_cast<std::size_t>(e)] = h;
        }
        // New vertex colours: hash(domain, old_colour, sorted_sigs_of_incident_edges).
        for (NodeId v = 0; v < H.n_nodes; ++v) {
            tmp_sigs.clear();
            for (EdgeId e : H.vertex_edges[static_cast<std::size_t>(v)]) {
                tmp_sigs.push_back(edge_sigs[static_cast<std::size_t>(e)]);
            }
            std::sort(tmp_sigs.begin(), tmp_sigs.end());
            std::uint64_t h = fnv1a_init(FNV_DOMAIN_VERTEX_NEW);
            h = fnv1a_mix(h, colours[static_cast<std::size_t>(v)]);
            for (std::uint64_t c : tmp_sigs) h = fnv1a_mix(h, c);
            new_colours[static_cast<std::size_t>(v)] = h;
        }
        const bool stable = partition_equiv(new_colours, colours);
        colours.swap(new_colours);
        if (stable) break;
    }
    return colours;
}

std::unordered_map<std::uint64_t, std::vector<NodeId>>
wl_partition_compute(const SHG& H, int max_rounds) {
    const auto hashes = wl_hash_compute(H, max_rounds);
    std::unordered_map<std::uint64_t, std::vector<NodeId>> out;
    for (NodeId v = 0; v < H.n_nodes; ++v) {
        out[hashes[static_cast<std::size_t>(v)]].push_back(v);
    }
    return out;
}

}  // namespace isalhg
