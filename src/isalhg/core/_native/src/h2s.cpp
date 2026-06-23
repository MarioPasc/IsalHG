// Greedy H2S with bounded backtracking on V-emission label permutations.
//
// Translates ``src/isalhg/core/hypergraph_to_string.py`` (Python) to C++17
// preserving the exact tie-breaking cascade. The encoder uses inplace
// mutation with stack-allocated undo records — no per-branch CDLL clone.

#include "isalhg/h2s.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <numeric>
#include <stdexcept>

#include "isalhg/cdll.hpp"
#include "isalhg/errors.hpp"
#include "isalhg/state.hpp"
#include "isalhg/token.hpp"

namespace isalhg {

namespace {

// ---------------------------------------------------------------------------
// Displacement enumeration, cost-class lazy.
//
// Python's `_enum_displacements` materialises all (2r+1)^k tuples and sorts.
// That is wasteful: the early-exit by total length means we typically only
// need cost class 0 (current pointer hits an edge member already). We
// enumerate by cost class ascending and break as soon as the outer loop
// has a best emission.
// ---------------------------------------------------------------------------

struct Disp {
    std::array<int, K_MAX> d{};
    int k_used = 0;
    int cost = 0;

    bool operator<(const Disp& other) const noexcept {
        // Same-cost comparison only inside a class. (Sort within class.)
        for (int idx = 0; idx < k_used; ++idx) {
            const int ad = std::abs(d[static_cast<std::size_t>(idx)]);
            const int bd = std::abs(other.d[static_cast<std::size_t>(idx)]);
            if (ad != bd) return ad < bd;
        }
        for (int idx = 0; idx < k_used; ++idx) {
            if (d[static_cast<std::size_t>(idx)] != other.d[static_cast<std::size_t>(idx)]) {
                return d[static_cast<std::size_t>(idx)] < other.d[static_cast<std::size_t>(idx)];
            }
        }
        return false;
    }
};

// Recursively enumerate all k-tuples of non-negative ints with sum == cost
// and each entry <= radius. For each |d| tuple, emit all sign patterns.
void enum_cost_class_recursive(int k_remaining, int cost_remaining, int radius,
                               std::array<int, K_MAX>& abs_d_buf, int level, int k_total,
                               std::vector<Disp>& out) {
    if (k_remaining == 0) {
        if (cost_remaining != 0) return;
        // Determine non-zero positions; emit 2^nz sign patterns.
        std::array<int, K_MAX> nz_positions{};
        int nz_count = 0;
        for (int i = 0; i < k_total; ++i) {
            if (abs_d_buf[static_cast<std::size_t>(i)] > 0) {
                nz_positions[static_cast<std::size_t>(nz_count++)] = i;
            }
        }
        const int sign_patterns = 1 << nz_count;
        Disp d{};
        d.k_used = k_total;
        // Initialise positive |d|.
        for (int i = 0; i < k_total; ++i) d.d[static_cast<std::size_t>(i)] =
            abs_d_buf[static_cast<std::size_t>(i)];
        for (int sp = 0; sp < sign_patterns; ++sp) {
            Disp e = d;
            for (int n = 0; n < nz_count; ++n) {
                if (sp & (1 << n)) {
                    e.d[static_cast<std::size_t>(nz_positions[static_cast<std::size_t>(n)])] =
                        -abs_d_buf[static_cast<std::size_t>(
                            nz_positions[static_cast<std::size_t>(n)])];
                }
            }
            // cost = sum of absolute values = original sum (signs don't change |.|).
            int c = 0;
            for (int i = 0; i < k_total; ++i) c += std::abs(e.d[static_cast<std::size_t>(i)]);
            e.cost = c;
            out.push_back(e);
        }
        return;
    }
    const int max_here = std::min(radius, cost_remaining);
    for (int v = 0; v <= max_here; ++v) {
        abs_d_buf[static_cast<std::size_t>(level)] = v;
        enum_cost_class_recursive(k_remaining - 1, cost_remaining - v, radius, abs_d_buf,
                                  level + 1, k_total, out);
    }
}

void enum_cost_class(int k, int radius, int cost, std::vector<Disp>& out) {
    out.clear();
    if (cost == 0) {
        Disp z{};
        z.k_used = k;
        out.push_back(z);
        return;
    }
    if (radius <= 0) return;
    std::array<int, K_MAX> buf{};
    enum_cost_class_recursive(k, cost, radius, buf, 0, k, out);
    std::sort(out.begin(), out.end());
}

// ---------------------------------------------------------------------------
// Movement-token block: N's first (i=1..k), then P's (i=1..k).
// Matches Python ``_movement_tokens``.
// ---------------------------------------------------------------------------

void emit_movement_tokens(const Disp& disp, std::vector<Token>& out) {
    for (int idx = 0; idx < disp.k_used; ++idx) {
        const int d = disp.d[static_cast<std::size_t>(idx)];
        if (d < 0) {
            for (int r = 0; r < -d; ++r) out.push_back(Token::make_n(idx + 1));
        }
    }
    for (int idx = 0; idx < disp.k_used; ++idx) {
        const int d = disp.d[static_cast<std::size_t>(idx)];
        if (d > 0) {
            for (int r = 0; r < d; ++r) out.push_back(Token::make_p(idx + 1));
        }
    }
}

// Walk ``delta`` steps from ``start`` in the CDLL (forward if positive).
[[nodiscard]] SlotIdx displaced_slot(const Cdll& cdll, SlotIdx start, int delta) noexcept {
    SlotIdx s = start;
    if (delta > 0) {
        for (int r = 0; r < delta; ++r) s = cdll.next_node(s);
    } else if (delta < 0) {
        for (int r = 0; r < -delta; ++r) s = cdll.prev_node(s);
    }
    return s;
}

// ---------------------------------------------------------------------------
// Best V candidate.
//
// Returns true if a candidate was found. Output via reference parameters.
// Cascade key (lex-min): (i, j, edge_label, sorted_new_labels, eta(e), edge_id).
// ---------------------------------------------------------------------------

struct VCandidate {
    EdgeId edge_id;
    int i_val;
    int j_val;
    EdgeLabel edge_label;
    std::vector<std::int16_t> sorted_new_labels;  // size j_val
    std::vector<NodeId> new_inputs;               // size j_val, set form (sorted)

    // Key for cascade comparison.
    int key_i;
    int key_j;
    EdgeLabel key_le;
    // sorted_new_labels (already a member)
    const std::vector<std::int32_t>* key_eta = nullptr;
    EdgeId key_edge_id = 0;
};

[[nodiscard]] int compare_v_keys(const VCandidate& a, const VCandidate& b) noexcept {
    if (a.key_i != b.key_i) return a.key_i < b.key_i ? -1 : 1;
    if (a.key_j != b.key_j) return a.key_j < b.key_j ? -1 : 1;
    if (a.key_le != b.key_le) return a.key_le < b.key_le ? -1 : 1;
    // sorted_new_labels lex compare.
    {
        const auto& la = a.sorted_new_labels;
        const auto& lb = b.sorted_new_labels;
        const std::size_t common = std::min(la.size(), lb.size());
        for (std::size_t k = 0; k < common; ++k) {
            if (la[k] != lb[k]) return la[k] < lb[k] ? -1 : 1;
        }
        if (la.size() != lb.size()) return la.size() < lb.size() ? -1 : 1;
    }
    // eta tuple lex.
    {
        const auto& ea = *a.key_eta;
        const auto& eb = *b.key_eta;
        const std::size_t common = std::min(ea.size(), eb.size());
        for (std::size_t k = 0; k < common; ++k) {
            if (ea[k] != eb[k]) return ea[k] < eb[k] ? -1 : 1;
        }
        if (ea.size() != eb.size()) return ea.size() < eb.size() ? -1 : 1;
    }
    if (a.key_edge_id != b.key_edge_id) return a.key_edge_id < b.key_edge_id ? -1 : 1;
    return 0;
}

[[nodiscard]] bool best_v_for_displacement(const SHG& H, const EncoderState& state, int k,
                                           const std::array<NodeId, K_MAX>& tentative_inputs,
                                           int tentative_count, VCandidate& out) {
    bool have = false;
    VCandidate best{};

    for (EdgeId e = 0; e < H.n_edges; ++e) {
        if (state.consumed[static_cast<std::size_t>(e)]) continue;
        const auto& members = H.edge_members[static_cast<std::size_t>(e)];
        const int arity = static_cast<int>(members.size());
        if (arity < 2 || arity > k) continue;

        // Longest prefix of tentative_inputs[0..min(k,arity)-1] that is
        // distinct AND every element appears in members.
        int longest_prefix = 0;
        std::array<NodeId, K_MAX> seen_prefix{};
        int seen_prefix_n = 0;
        const int upper = std::min(k, arity);
        for (int idx = 0; idx < upper; ++idx) {
            if (idx >= tentative_count) break;
            const NodeId v = tentative_inputs[static_cast<std::size_t>(idx)];
            if (!H.edge_contains(e, v)) break;
            bool dup = false;
            for (int s = 0; s < seen_prefix_n; ++s) {
                if (seen_prefix[static_cast<std::size_t>(s)] == v) { dup = true; break; }
            }
            if (dup) break;
            seen_prefix[static_cast<std::size_t>(seen_prefix_n++)] = v;
            longest_prefix = idx + 1;
        }
        if (longest_prefix < 1) continue;

        for (int i_val = 1; i_val <= longest_prefix; ++i_val) {
            const int j_val = arity - i_val;
            if (j_val < 1) continue;
            if (i_val + j_val > k) continue;
            if (j_val > k - 1) continue;
            if (i_val > k - 1) continue;

            // pointed = set of tentative_inputs[0..i_val-1]; new_inputs = members - pointed.
            // Members are sorted; pointed is small (<=k). Linear scan.
            std::vector<NodeId> new_inputs;
            new_inputs.reserve(static_cast<std::size_t>(j_val));
            bool skip = false;
            for (NodeId m : members) {
                bool in_pointed = false;
                for (int idx = 0; idx < i_val; ++idx) {
                    if (tentative_inputs[static_cast<std::size_t>(idx)] == m) {
                        in_pointed = true;
                        break;
                    }
                }
                if (in_pointed) continue;
                if (state.i2o_has(m)) {
                    skip = true;
                    break;
                }
                new_inputs.push_back(m);
            }
            if (skip) continue;
            if (static_cast<int>(new_inputs.size()) != j_val) continue;

            std::vector<std::int16_t> sorted_new_labels;
            sorted_new_labels.reserve(static_cast<std::size_t>(j_val));
            for (NodeId v : new_inputs) {
                sorted_new_labels.push_back(
                    static_cast<std::int16_t>(H.vertex_labels[static_cast<std::size_t>(v)]));
            }
            std::sort(sorted_new_labels.begin(), sorted_new_labels.end());

            VCandidate cand{};
            cand.edge_id = e;
            cand.i_val = i_val;
            cand.j_val = j_val;
            cand.edge_label = H.edge_labels[static_cast<std::size_t>(e)];
            cand.sorted_new_labels = sorted_new_labels;
            cand.new_inputs = std::move(new_inputs);
            cand.key_i = i_val;
            cand.key_j = j_val;
            cand.key_le = cand.edge_label;
            cand.key_eta = &H.eta(e);
            cand.key_edge_id = e;

            if (!have || compare_v_keys(cand, best) < 0) {
                best = std::move(cand);
                have = true;
            }
        }
    }

    if (have) out = std::move(best);
    return have;
}

// ---------------------------------------------------------------------------
// Best C candidate.
//
// Cascade key (lex-min): (arity, edge_label, eta(e), edge_id).
// ---------------------------------------------------------------------------

struct CCandidate {
    EdgeId edge_id;
    int arity;
    EdgeLabel edge_label;
    const std::vector<std::int32_t>* key_eta = nullptr;
};

[[nodiscard]] int compare_c_keys(const CCandidate& a, const CCandidate& b) noexcept {
    if (a.arity != b.arity) return a.arity < b.arity ? -1 : 1;
    if (a.edge_label != b.edge_label) return a.edge_label < b.edge_label ? -1 : 1;
    const auto& ea = *a.key_eta;
    const auto& eb = *b.key_eta;
    const std::size_t common = std::min(ea.size(), eb.size());
    for (std::size_t k = 0; k < common; ++k) {
        if (ea[k] != eb[k]) return ea[k] < eb[k] ? -1 : 1;
    }
    if (ea.size() != eb.size()) return ea.size() < eb.size() ? -1 : 1;
    if (a.edge_id != b.edge_id) return a.edge_id < b.edge_id ? -1 : 1;
    return 0;
}

[[nodiscard]] bool best_c_for_displacement(const SHG& H, const EncoderState& state, int k,
                                           const std::array<NodeId, K_MAX>& tentative_inputs,
                                           int tentative_count, CCandidate& out) {
    bool have = false;
    CCandidate best{};

    for (EdgeId e = 0; e < H.n_edges; ++e) {
        if (state.consumed[static_cast<std::size_t>(e)]) continue;
        const auto& members = H.edge_members[static_cast<std::size_t>(e)];
        const int arity = static_cast<int>(members.size());
        if (arity > k) continue;
        if (arity > tentative_count) continue;
        // All members must already be mapped (in i2o).
        bool skip = false;
        for (NodeId v : members) {
            if (!state.i2o_has(v)) { skip = true; break; }
        }
        if (skip) continue;
        // tentative_inputs[0..arity-1] must equal members as a set, with no duplicates.
        std::array<NodeId, K_MAX> first_arity{};
        for (int idx = 0; idx < arity; ++idx) {
            first_arity[static_cast<std::size_t>(idx)] =
                tentative_inputs[static_cast<std::size_t>(idx)];
        }
        // Duplicate check.
        bool dup = false;
        for (int a = 0; a < arity && !dup; ++a) {
            for (int b = a + 1; b < arity && !dup; ++b) {
                if (first_arity[static_cast<std::size_t>(a)]
                    == first_arity[static_cast<std::size_t>(b)]) {
                    dup = true;
                }
            }
        }
        if (dup) continue;
        // Set equality: every element of first_arity is in members AND vice versa.
        // Since both have size arity and no duplicates in first_arity, it suffices
        // that every element of first_arity is in members.
        bool ok = true;
        for (int idx = 0; idx < arity; ++idx) {
            if (!H.edge_contains(e, first_arity[static_cast<std::size_t>(idx)])) {
                ok = false;
                break;
            }
        }
        if (!ok) continue;

        CCandidate cand{};
        cand.edge_id = e;
        cand.arity = arity;
        cand.edge_label = H.edge_labels[static_cast<std::size_t>(e)];
        cand.key_eta = &H.eta(e);
        if (!have || compare_c_keys(cand, best) < 0) {
            best = cand;
            have = true;
        }
    }
    if (have) out = best;
    return have;
}

// ---------------------------------------------------------------------------
// Label-respecting permutations of ``new_inputs``.
//
// Mirrors Python ``_label_respecting_perms``: group by label (label classes
// sorted ascending), then within each group emit all permutations. With
// ``wl_colors``, prune to permutations that place WL-equivalent vertices
// within a label class in ascending input-id order.
// ---------------------------------------------------------------------------

struct LabelGroup {
    std::int16_t label;
    std::vector<NodeId> members;
};

void group_by_label(const std::vector<NodeId>& new_inputs, const SHG& H,
                    std::vector<LabelGroup>& groups) {
    groups.clear();
    // Build a label -> members map; new_inputs is small (<= K_MAX).
    for (NodeId v : new_inputs) {
        const std::int16_t lab =
            static_cast<std::int16_t>(H.vertex_labels[static_cast<std::size_t>(v)]);
        // Find or insert group.
        std::size_t idx = groups.size();
        for (std::size_t g = 0; g < groups.size(); ++g) {
            if (groups[g].label == lab) { idx = g; break; }
        }
        if (idx == groups.size()) {
            groups.push_back(LabelGroup{lab, {}});
        }
        groups[idx].members.push_back(v);
    }
    std::sort(groups.begin(), groups.end(),
              [](const LabelGroup& a, const LabelGroup& b) { return a.label < b.label; });
    for (auto& g : groups) std::sort(g.members.begin(), g.members.end());
}

// WL-orbit canonical filter: within each group, WL-equivalent vertices must
// appear in ascending node-id order.
[[nodiscard]] bool wl_orbit_canonical(const std::vector<LabelGroup>& groups,
                                      const std::vector<std::array<NodeId, K_MAX>>& /*unused*/,
                                      const std::vector<std::int64_t>& wl_colors,
                                      const std::vector<std::vector<NodeId>>& current_perm)
{
    (void)groups;
    for (const auto& grp : current_perm) {
        // For each WL color present in the group, track the last node id we saw.
        // We use a small linear scan because group sizes are small.
        for (std::size_t a = 0; a < grp.size(); ++a) {
            const NodeId va = grp[a];
            const std::int64_t ca = wl_colors[static_cast<std::size_t>(va)];
            for (std::size_t b = a + 1; b < grp.size(); ++b) {
                const NodeId vb = grp[b];
                if (wl_colors[static_cast<std::size_t>(vb)] == ca && vb <= va) {
                    return false;
                }
            }
        }
    }
    return true;
}

void enumerate_label_perms(
    const std::vector<NodeId>& new_inputs, const SHG& H,
    const std::optional<std::vector<std::int64_t>>& wl_colors,
    std::vector<std::vector<NodeId>>& out_perms)
{
    out_perms.clear();
    std::vector<LabelGroup> groups;
    group_by_label(new_inputs, H, groups);

    // Recursive enumeration: for each group, permute, then combine across groups.
    std::vector<std::vector<NodeId>> current(groups.size());
    for (std::size_t g = 0; g < groups.size(); ++g) current[g] = groups[g].members;

    // We use std::next_permutation per group, iterating like an odometer.
    // The starting per-group permutation is the ascending one (already sorted).

    while (true) {
        if (!wl_colors.has_value()
            || wl_orbit_canonical(groups, /*unused*/{}, wl_colors.value(), current)) {
            std::vector<NodeId> flat;
            flat.reserve(new_inputs.size());
            for (const auto& grp : current) {
                for (NodeId v : grp) flat.push_back(v);
            }
            out_perms.push_back(std::move(flat));
        }
        // Advance: try next_permutation on group 0; if rolls over, roll group 1; ...
        std::size_t g = 0;
        bool rolled = true;
        while (g < current.size() && rolled) {
            rolled = !std::next_permutation(current[g].begin(), current[g].end());
            if (rolled) {
                // current[g] is now the smallest permutation; carry to the next group.
                ++g;
            }
        }
        if (rolled) break;
    }
}

// ---------------------------------------------------------------------------
// Main recursive encoder.
//
// emission_tokens_so_far : the token vector being built; we append on entry,
//                          pop on backtrack. The caller passes its own.
// Returns true on success (with ``best_completion_tokens`` populated for V
// branches that branched), or false if stuck.
//
// We follow the Python pattern: this function takes the current state and
// returns the lex-min completion as a fresh vector. For V branches we
// recurse over multiple permutations and take the lex-min.
// ---------------------------------------------------------------------------

[[nodiscard]] bool encode_from(const SHG& H, int k, EncoderState& state,
                               const std::optional<std::vector<std::int64_t>>& wl_colors,
                               std::vector<Token>& out_completion);

[[nodiscard]] bool encode_from(const SHG& H, int k, EncoderState& state,
                               const std::optional<std::vector<std::int64_t>>& wl_colors,
                               std::vector<Token>& out_completion)
{
    out_completion.clear();
    const std::int32_t mapped = state.i2o_count();
    const std::int32_t consumed = state.consumed_count();
    if (mapped == H.n_nodes && consumed == H.n_edges) {
        return true;
    }

    const int radius = std::max(0, mapped);
    const int max_cost = k * radius;

    // Track the best emission found across displacements.
    bool have_best = false;
    int best_total_len = 0;        // == best_cost + 1
    std::vector<Token> best_prefix;  // move_block + main_tok
    bool best_kind_is_v = false;
    EdgeId best_edge_id = -1;
    std::array<SlotIdx, K_MAX> best_new_slots{};
    std::vector<NodeId> best_new_inputs;  // V only

    std::vector<Token> tmp_move_block;
    std::array<NodeId, K_MAX> tentative_inputs{};
    int tentative_count = 0;

    std::vector<Disp> cost_class;

    for (int cost = 0; cost <= max_cost; ++cost) {
        // Cost classes higher than the current best's cost yield strictly
        // longer emissions; safe to stop.
        if (have_best && cost + 1 > best_total_len) break;

        enum_cost_class(k, radius, cost, cost_class);
        if (cost_class.empty()) continue;

    for (const Disp& disp : cost_class) {

        // Compute new_slots and tentative_inputs.
        std::array<SlotIdx, K_MAX> new_slots{};
        for (int idx = 0; idx < k; ++idx) {
            new_slots[static_cast<std::size_t>(idx)] = displaced_slot(
                state.cdll, state.get_ptr(idx + 1), disp.d[static_cast<std::size_t>(idx)]);
        }
        tentative_count = k;
        for (int idx = 0; idx < k; ++idx) {
            const NodeId out_v = state.cdll.get_value(new_slots[static_cast<std::size_t>(idx)]);
            tentative_inputs[static_cast<std::size_t>(idx)] =
                state.o2i[static_cast<std::size_t>(out_v)];
        }

        tmp_move_block.clear();
        emit_movement_tokens(disp, tmp_move_block);

        // Try V candidate.
        VCandidate v_cand{};
        const bool has_v = best_v_for_displacement(H, state, k, tentative_inputs, tentative_count,
                                                   v_cand);
        if (has_v) {
            Token main_tok = Token::make_v(v_cand.edge_label, v_cand.i_val, v_cand.j_val,
                                           v_cand.sorted_new_labels);
            const int total_len = static_cast<int>(tmp_move_block.size()) + 1;

            // Compare against current best by (total_len, *sort_keys).
            bool take = !have_best;
            if (!take && total_len != best_total_len) take = total_len < best_total_len;
            if (!take && total_len == best_total_len) {
                // Same length: compare element by element.
                const std::size_t mlen = tmp_move_block.size();
                bool decided = false;
                for (std::size_t pos = 0; pos < mlen && !decided; ++pos) {
                    const int c = token_cmp(tmp_move_block[pos], best_prefix[pos]);
                    if (c != 0) { take = c < 0; decided = true; }
                }
                if (!decided) {
                    take = token_cmp(main_tok, best_prefix.back()) < 0;
                }
            }
            if (take) {
                best_prefix = tmp_move_block;
                best_prefix.push_back(main_tok);
                best_total_len = total_len;
                best_kind_is_v = true;
                best_edge_id = v_cand.edge_id;
                best_new_slots = new_slots;
                best_new_inputs = v_cand.new_inputs;
                have_best = true;
            }
        }

        // Try C candidate.
        CCandidate c_cand{};
        const bool has_c = best_c_for_displacement(H, state, k, tentative_inputs, tentative_count,
                                                   c_cand);
        if (has_c) {
            Token main_tok_c = Token::make_c(c_cand.edge_label, c_cand.arity);
            const int total_len = static_cast<int>(tmp_move_block.size()) + 1;

            bool take = !have_best;
            if (!take && total_len != best_total_len) take = total_len < best_total_len;
            if (!take && total_len == best_total_len) {
                const std::size_t mlen = tmp_move_block.size();
                bool decided = false;
                for (std::size_t pos = 0; pos < mlen && !decided; ++pos) {
                    const int c = token_cmp(tmp_move_block[pos], best_prefix[pos]);
                    if (c != 0) { take = c < 0; decided = true; }
                }
                if (!decided) {
                    take = token_cmp(main_tok_c, best_prefix.back()) < 0;
                }
            }
            if (take) {
                best_prefix = tmp_move_block;
                best_prefix.push_back(main_tok_c);
                best_total_len = total_len;
                best_kind_is_v = false;
                best_edge_id = c_cand.edge_id;
                best_new_slots = new_slots;
                best_new_inputs.clear();
                have_best = true;
            }
        }
    }
    // End of cost-class loop body.
    }  // for cost

    if (!have_best) return false;

    if (!best_kind_is_v) {
        // C branch: simple inplace + undo.
        std::array<SlotIdx, K_MAX> saved_ptrs{};
        for (int idx = 0; idx < K_MAX; ++idx) saved_ptrs[idx] = state.pointers[idx];
        for (int idx = 0; idx < K_MAX; ++idx) state.pointers[idx] = best_new_slots[idx];
        state.consumed[static_cast<std::size_t>(best_edge_id)] = 1;

        std::vector<Token> sub_completion;
        const bool ok = encode_from(H, k, state, wl_colors, sub_completion);

        state.consumed[static_cast<std::size_t>(best_edge_id)] = 0;
        for (int idx = 0; idx < K_MAX; ++idx) state.pointers[idx] = saved_ptrs[idx];

        if (!ok) return false;
        out_completion = std::move(best_prefix);
        for (auto& t : sub_completion) out_completion.push_back(std::move(t));
        return true;
    }

    // V branch: enumerate label-respecting permutations and take the lex-min
    // sub_completion. ``best_prefix`` is identical across all permutations
    // of this V emission, so we compare only the per-permutation
    // sub_completion vectors — avoids allocating + copying the prefix per
    // permutation and avoids redundant element-by-element comparison of
    // the prefix tokens during lex-min selection.
    std::vector<std::vector<NodeId>> perms;
    enumerate_label_perms(best_new_inputs, H, wl_colors, perms);

    bool have_completion = false;
    std::vector<Token> best_sub_completion;
    std::vector<Token> sub_completion;

    for (const auto& perm : perms) {
        std::array<SlotIdx, K_MAX> saved_ptrs{};
        for (int idx = 0; idx < K_MAX; ++idx) saved_ptrs[idx] = state.pointers[idx];
        const NodeId saved_next_id = state.next_output_id;

        // Apply ptrs.
        for (int idx = 0; idx < K_MAX; ++idx) state.pointers[idx] = best_new_slots[idx];

        // Insert new nodes after pointer 1 (anchor).
        SlotIdx anchor = state.get_ptr(1);
        std::array<SlotIdx, K_MAX> recorded_slots{};
        std::array<NodeId, K_MAX> recorded_inputs{};
        std::array<NodeId, K_MAX> recorded_outs{};
        const int new_count = static_cast<int>(perm.size());

        for (int idx = 0; idx < new_count; ++idx) {
            const NodeId input_v = perm[static_cast<std::size_t>(idx)];
            const NodeId out_v = state.next_output_id++;
            const SlotIdx new_slot = state.cdll.insert_after(anchor, out_v);
            state.i2o[static_cast<std::size_t>(input_v)] = out_v;
            state.o2i[static_cast<std::size_t>(out_v)] = input_v;
            recorded_slots[static_cast<std::size_t>(idx)] = new_slot;
            recorded_inputs[static_cast<std::size_t>(idx)] = input_v;
            recorded_outs[static_cast<std::size_t>(idx)] = out_v;
            anchor = new_slot;
        }
        state.consumed[static_cast<std::size_t>(best_edge_id)] = 1;

        sub_completion.clear();
        const bool ok = encode_from(H, k, state, wl_colors, sub_completion);

        // Undo.
        state.consumed[static_cast<std::size_t>(best_edge_id)] = 0;
        for (int idx = new_count - 1; idx >= 0; --idx) {
            state.cdll.remove(recorded_slots[static_cast<std::size_t>(idx)]);
            state.i2o[static_cast<std::size_t>(
                recorded_inputs[static_cast<std::size_t>(idx)])] = -1;
            state.o2i[static_cast<std::size_t>(
                recorded_outs[static_cast<std::size_t>(idx)])] = -1;
        }
        state.next_output_id = saved_next_id;
        for (int idx = 0; idx < K_MAX; ++idx) state.pointers[idx] = saved_ptrs[idx];

        if (!ok) continue;

        if (!have_completion || sequence_cmp(sub_completion, best_sub_completion) < 0) {
            best_sub_completion.swap(sub_completion);
            have_completion = true;
        }
    }

    if (!have_completion) return false;
    out_completion.clear();
    out_completion.reserve(best_prefix.size() + best_sub_completion.size());
    for (const auto& t : best_prefix) out_completion.push_back(t);
    for (auto& t : best_sub_completion) out_completion.push_back(std::move(t));
    return true;
}

}  // namespace

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

std::vector<Token> greedy_h2s_tokens(const SHG& H, NodeId seed_node, int k,
                                     const std::optional<std::vector<std::int64_t>>& wl_colors)
{
    if (H.n_nodes == 0) return {};
    if (seed_node < 0 || seed_node >= H.n_nodes) {
        throw IsalHGError("seed_node out of range");
    }
    if (k < 1) {
        throw IsalHGError("k must be >= 1");
    }
    if (k > K_MAX) {
        throw IsalHGError("k exceeds K_MAX");
    }

    EncoderState state(H.n_nodes, H.n_edges, k, seed_node);

    std::vector<Token> out;
    const bool ok = encode_from(H, k, state, wl_colors, out);
    if (!ok) {
        throw H2SStuckError("H2S stuck from seed");
    }
    return out;
}

std::string greedy_h2s_str(const SHG& H, NodeId seed_node, int k,
                           const std::optional<std::vector<std::int64_t>>& wl_colors)
{
    return serialize(greedy_h2s_tokens(H, seed_node, k, wl_colors));
}

}  // namespace isalhg
