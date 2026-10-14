#include "isalhg/ordered_walk.hpp"

#include <algorithm>
#include <cstddef>
#include <string>
#include <utility>
#include <vector>

#include "isalhg/errors.hpp"

namespace isalhg {

namespace {

// ``(type of u, sorted multiset of (predicate, arity) over the facts containing u)``
// -- _Signature in ordered_walk.py.
using SigFacts = std::vector<std::pair<EdgeLabel, std::int32_t>>;

struct Sig {
    VertexLabel type = 0;
    SigFacts facts;
};

[[nodiscard]] inline int cmp_i(std::int32_t a, std::int32_t b) noexcept {
    return a < b ? -1 : (a > b ? 1 : 0);
}

// Python tuple comparison: element-wise, then the shorter tuple first.
template <typename T, typename Cmp>
[[nodiscard]] int cmp_seq(const std::vector<T>& a, const std::vector<T>& b, Cmp cmp) {
    const std::size_t n = std::min(a.size(), b.size());
    for (std::size_t idx = 0; idx < n; ++idx) {
        const int c = cmp(a[idx], b[idx]);
        if (c != 0) return c;
    }
    return cmp_i(static_cast<std::int32_t>(a.size()), static_cast<std::int32_t>(b.size()));
}

[[nodiscard]] int cmp_int_elem(std::int32_t a, std::int32_t b) noexcept { return cmp_i(a, b); }

[[nodiscard]] int cmp_fact(const std::pair<EdgeLabel, std::int32_t>& a,
                           const std::pair<EdgeLabel, std::int32_t>& b) noexcept {
    const int c = cmp_i(a.first, b.first);
    return c != 0 ? c : cmp_i(a.second, b.second);
}

[[nodiscard]] int cmp_sig(const Sig& a, const Sig& b) {
    const int c = cmp_i(a.type, b.type);
    return c != 0 ? c : cmp_seq(a.facts, b.facts, cmp_fact);
}

[[nodiscard]] int cmp_sig_ptr(const Sig* a, const Sig* b) { return cmp_sig(*a, *b); }

// ``K_V(e)`` split into its components; the two policies differ only in where the
// ``by_rank`` field sits relative to ``structure``.
struct VKey {
    std::int32_t anchor = 0;  // placed_c[0]
    EdgeLabel edge_label = 0;
    std::int32_t n_placed = 0;
    std::int32_t n_fresh = 0;
    std::vector<std::int32_t> placed_c;
    std::vector<const Sig*> sigs;
    std::vector<std::int32_t> by_rank;
};

[[nodiscard]] int cmp_structure(const VKey& a, const VKey& b) {
    int c = cmp_i(a.edge_label, b.edge_label);
    if (c != 0) return c;
    c = cmp_i(a.n_placed, b.n_placed);
    if (c != 0) return c;
    c = cmp_i(a.n_fresh, b.n_fresh);
    if (c != 0) return c;
    c = cmp_seq(a.placed_c, b.placed_c, cmp_int_elem);
    if (c != 0) return c;
    return cmp_seq(a.sigs, b.sigs, cmp_sig_ptr);
}

[[nodiscard]] int cmp_vkey(const VKey& a, const VKey& b, bool rank_first) {
    const int anchor = cmp_i(a.anchor, b.anchor);
    if (anchor != 0) return anchor;
    if (rank_first) {
        const int c = cmp_seq(a.by_rank, b.by_rank, cmp_int_elem);
        return c != 0 ? c : cmp_structure(a, b);
    }
    const int c = cmp_structure(a, b);
    return c != 0 ? c : cmp_seq(a.by_rank, b.by_rank, cmp_int_elem);
}

[[nodiscard]] std::vector<Sig> signatures(const SHG& H) {
    std::vector<Sig> out(static_cast<std::size_t>(H.n_nodes));
    for (NodeId v = 0; v < H.n_nodes; ++v) {
        Sig& s = out[static_cast<std::size_t>(v)];
        s.type = H.vertex_labels[static_cast<std::size_t>(v)];
        const auto& incident = H.vertex_edges[static_cast<std::size_t>(v)];
        s.facts.reserve(incident.size());
        for (EdgeId e : incident) {
            s.facts.emplace_back(
                H.edge_labels[static_cast<std::size_t>(e)],
                static_cast<std::int32_t>(H.edge_members[static_cast<std::size_t>(e)].size()));
        }
        std::sort(s.facts.begin(), s.facts.end(),
                  [](const auto& a, const auto& b) { return cmp_fact(a, b) < 0; });
    }
    return out;
}

[[nodiscard]] NodeId select_root(const SHG& H, const std::vector<std::int32_t>& ranks,
                                 const OwPolicy& policy) {
    if (policy.root_rule == OwRootRule::Rank0) {
        for (NodeId v = 0; v < H.n_nodes; ++v) {
            if (ranks[static_cast<std::size_t>(v)] == 0) return v;
        }
        throw IsalHGError("ranks contains no 0 entry");
    }
    // max over (degree, type, -rank); the -rank field makes the key injective, so the
    // "first maximal element" rule of Python's ``max`` never applies.
    NodeId best = 0;
    for (NodeId v = 1; v < H.n_nodes; ++v) {
        const auto deg = static_cast<std::int32_t>(H.vertex_edges[static_cast<std::size_t>(v)].size());
        const auto best_deg =
            static_cast<std::int32_t>(H.vertex_edges[static_cast<std::size_t>(best)].size());
        int c = cmp_i(deg, best_deg);
        if (c == 0) {
            c = cmp_i(H.vertex_labels[static_cast<std::size_t>(v)],
                      H.vertex_labels[static_cast<std::size_t>(best)]);
        }
        if (c == 0) {
            c = cmp_i(-ranks[static_cast<std::size_t>(v)], -ranks[static_cast<std::size_t>(best)]);
        }
        if (c > 0) best = v;
    }
    return best;
}

class Emitter {
public:
    Emitter(const SHG& H, const std::vector<std::int32_t>& ranks, const OwPolicy& policy,
            int n_ptr, NodeId root)
        : H_(H),
          ranks_(ranks),
          policy_(policy),
          sig_(signatures(H)),
          n_ptr_(n_ptr),
          index_of_(static_cast<std::size_t>(H.n_nodes), -1),
          ptr_(static_cast<std::size_t>(n_ptr), root),
          placed_(static_cast<std::size_t>(H.n_nodes), 0),
          c_(static_cast<std::size_t>(H.n_nodes), -1),
          consumed_(static_cast<std::size_t>(H.n_edges), 0),
          in_cand_(static_cast<std::size_t>(H.n_edges), 0) {
        order_.push_back(root);
        index_of_[static_cast<std::size_t>(root)] = 0;
        placed_[static_cast<std::size_t>(root)] = 1;
        c_[static_cast<std::size_t>(root)] = 0;
        creation_.push_back(root);
        n_placed_ = 1;
    }

    void run() {
        v_phase();
        c_phase();
    }

    std::vector<Token> take_tokens() { return std::move(tokens_); }
    std::vector<NodeId> take_creation() { return std::move(creation_); }

private:
    // ------------------------------------------------------------------
    // Movement
    // ------------------------------------------------------------------

    [[nodiscard]] std::int32_t pos(NodeId v) const noexcept {
        const auto size = static_cast<std::int32_t>(order_.size());
        return (size - index_of_[static_cast<std::size_t>(v)]) % size;
    }

    // The no-crossing rule: displacement in backward-position coordinates from the
    // root, never wrapping. ``targets`` is (1-based pointer index, constant).
    void move(const std::vector<NodeId>& targets) {
        displacement_.assign(static_cast<std::size_t>(n_ptr_), 0);
        for (std::size_t t = 0; t < targets.size(); ++t) {
            displacement_[t] = pos(ptr_[t]) - pos(targets[t]);
            ptr_[t] = targets[t];
        }
        for (std::size_t t = 0; t < displacement_.size(); ++t) {
            for (std::int32_t step = displacement_[t]; step < 0; ++step) {
                tokens_.push_back(Token::make_n(static_cast<int>(t) + 1));
            }
        }
        for (std::size_t t = 0; t < displacement_.size(); ++t) {
            for (std::int32_t step = displacement_[t]; step > 0; --step) {
                tokens_.push_back(Token::make_p(static_cast<int>(t) + 1));
            }
        }
    }

    // ------------------------------------------------------------------
    // V-phase
    // ------------------------------------------------------------------

    void build_key(EdgeId e, VKey& key) const {
        const auto& members = H_.edge_members[static_cast<std::size_t>(e)];
        key.placed_c.clear();
        key.sigs.clear();
        key.by_rank.clear();
        for (NodeId v : members) {
            if (placed_[static_cast<std::size_t>(v)] != 0) {
                key.placed_c.push_back(c_[static_cast<std::size_t>(v)]);
            } else {
                key.sigs.push_back(&sig_[static_cast<std::size_t>(v)]);
                key.by_rank.push_back(ranks_[static_cast<std::size_t>(v)]);
            }
        }
        std::sort(key.placed_c.begin(), key.placed_c.end());
        std::sort(key.sigs.begin(), key.sigs.end(),
                  [](const Sig* a, const Sig* b) { return cmp_sig(*a, *b) < 0; });
        std::sort(key.by_rank.begin(), key.by_rank.end());
        key.anchor = key.placed_c.front();
        key.edge_label = H_.edge_labels[static_cast<std::size_t>(e)];
        key.n_placed = static_cast<std::int32_t>(key.placed_c.size());
        key.n_fresh = static_cast<std::int32_t>(key.sigs.size());
    }

    void add_candidate(EdgeId e) {
        if (in_cand_[static_cast<std::size_t>(e)] == 0) {
            in_cand_[static_cast<std::size_t>(e)] = 1;
            cand_.push_back(e);
        }
    }

    // Drop the consumed and the fully-placed facts, mirroring the set comprehension
    // that rebinds ``candidates`` at the top of every V-phase iteration.
    void filter_candidates() {
        std::size_t out = 0;
        for (std::size_t idx = 0; idx < cand_.size(); ++idx) {
            const EdgeId e = cand_[idx];
            bool has_fresh = false;
            for (NodeId v : H_.edge_members[static_cast<std::size_t>(e)]) {
                if (placed_[static_cast<std::size_t>(v)] == 0) {
                    has_fresh = true;
                    break;
                }
            }
            if (consumed_[static_cast<std::size_t>(e)] == 0 && has_fresh) {
                cand_[out++] = e;
            } else {
                in_cand_[static_cast<std::size_t>(e)] = 0;
            }
        }
        cand_.resize(out);
    }

    void v_phase() {
        for (EdgeId e : H_.vertex_edges[static_cast<std::size_t>(creation_.front())]) {
            add_candidate(e);
        }
        VKey best_key;
        VKey trial_key;
        while (n_placed_ < H_.n_nodes) {
            filter_candidates();
            if (cand_.empty()) {
                throw IsalHGError(
                    "the V-phase ran out of frontier facts before every constant was "
                    "placed; the input is not connected");
            }
            EdgeId best = cand_.front();
            build_key(best, best_key);
            for (std::size_t idx = 1; idx < cand_.size(); ++idx) {
                build_key(cand_[idx], trial_key);
                if (cmp_vkey(trial_key, best_key, policy_.rank_first) < 0) {
                    best = cand_[idx];
                    std::swap(best_key, trial_key);
                }
            }
            const auto before = creation_.size();
            emit_v(best);
            for (std::size_t idx = before; idx < creation_.size(); ++idx) {
                for (EdgeId e : H_.vertex_edges[static_cast<std::size_t>(creation_[idx])]) {
                    add_candidate(e);
                }
            }
        }
    }

    void emit_v(EdgeId e) {
        const auto& members = H_.edge_members[static_cast<std::size_t>(e)];
        std::vector<NodeId> anchored;
        std::vector<NodeId> fresh;
        for (NodeId v : members) {
            if (placed_[static_cast<std::size_t>(v)] != 0) {
                anchored.push_back(v);
            } else {
                fresh.push_back(v);
            }
        }
        std::sort(anchored.begin(), anchored.end(), [this](NodeId a, NodeId b) {
            return c_[static_cast<std::size_t>(a)] < c_[static_cast<std::size_t>(b)];
        });
        std::sort(fresh.begin(), fresh.end(), [this](NodeId a, NodeId b) {
            const int c = cmp_i(H_.vertex_labels[static_cast<std::size_t>(a)],
                                H_.vertex_labels[static_cast<std::size_t>(b)]);
            return c != 0 ? c < 0
                          : ranks_[static_cast<std::size_t>(a)] < ranks_[static_cast<std::size_t>(b)];
        });

        move(anchored);

        std::vector<std::int16_t> new_labels;
        new_labels.reserve(fresh.size());
        for (NodeId u : fresh) {
            new_labels.push_back(
                static_cast<std::int16_t>(H_.vertex_labels[static_cast<std::size_t>(u)]));
        }
        tokens_.push_back(Token::make_v(H_.edge_labels[static_cast<std::size_t>(e)],
                                        static_cast<int>(anchored.size()),
                                        static_cast<int>(fresh.size()), new_labels));
        insert_after_p1(fresh);
        consumed_[static_cast<std::size_t>(e)] = 1;
    }

    // Chain ``fresh`` into the order right after p_1, mirroring the decoder.
    void insert_after_p1(const std::vector<NodeId>& fresh) {
        if (fresh.empty()) return;
        const auto base = static_cast<std::size_t>(index_of_[static_cast<std::size_t>(ptr_[0])]);
        order_.insert(order_.begin() + static_cast<std::ptrdiff_t>(base) + 1, fresh.begin(),
                      fresh.end());
        for (NodeId u : fresh) {
            c_[static_cast<std::size_t>(u)] = static_cast<std::int32_t>(creation_.size());
            creation_.push_back(u);
            placed_[static_cast<std::size_t>(u)] = 1;
        }
        n_placed_ += static_cast<std::int32_t>(fresh.size());
        for (std::size_t idx = base + 1; idx < order_.size(); ++idx) {
            index_of_[static_cast<std::size_t>(order_[idx])] = static_cast<std::int32_t>(idx);
        }
    }

    // ------------------------------------------------------------------
    // C-phase
    // ------------------------------------------------------------------

    void c_phase() {
        // The order no longer changes, so every ``pos`` is computed once here.
        std::vector<std::int32_t> pos_of(static_cast<std::size_t>(H_.n_nodes), 0);
        for (NodeId v : order_) {
            pos_of[static_cast<std::size_t>(v)] = pos(v);
        }
        std::vector<EdgeId> remaining;
        for (EdgeId e = 0; e < H_.n_edges; ++e) {
            if (consumed_[static_cast<std::size_t>(e)] == 0) remaining.push_back(e);
        }
        std::vector<std::vector<std::int32_t>> sorted_pos(remaining.size());
        for (std::size_t idx = 0; idx < remaining.size(); ++idx) {
            const auto& members = H_.edge_members[static_cast<std::size_t>(remaining[idx])];
            auto& row = sorted_pos[idx];
            row.reserve(members.size());
            for (NodeId v : members) row.push_back(pos_of[static_cast<std::size_t>(v)]);
            std::sort(row.begin(), row.end());
        }
        std::vector<std::size_t> order_idx(remaining.size());
        for (std::size_t idx = 0; idx < order_idx.size(); ++idx) order_idx[idx] = idx;
        // Stable, matching Python's sort over ``H.edges()`` order. The key is in fact
        // injective (positions determine the member set; SparseHypergraph forbids a
        // duplicate (label, member-set)), so stability is belt and braces.
        std::stable_sort(order_idx.begin(), order_idx.end(),
                         [&](std::size_t a, std::size_t b) {
                             const int c = cmp_seq(sorted_pos[a], sorted_pos[b], cmp_int_elem);
                             if (c != 0) return c < 0;
                             return H_.edge_labels[static_cast<std::size_t>(remaining[a])] <
                                    H_.edge_labels[static_cast<std::size_t>(remaining[b])];
                         });

        std::vector<NodeId> members_sorted;
        for (std::size_t idx : order_idx) {
            const EdgeId e = remaining[idx];
            members_sorted = H_.edge_members[static_cast<std::size_t>(e)];
            std::sort(members_sorted.begin(), members_sorted.end(),
                      [&pos_of](NodeId a, NodeId b) {
                          return pos_of[static_cast<std::size_t>(a)] <
                                 pos_of[static_cast<std::size_t>(b)];
                      });
            move(members_sorted);
            tokens_.push_back(Token::make_c(H_.edge_labels[static_cast<std::size_t>(e)],
                                            static_cast<int>(members_sorted.size())));
            consumed_[static_cast<std::size_t>(e)] = 1;
        }
    }

    const SHG& H_;
    const std::vector<std::int32_t>& ranks_;
    OwPolicy policy_;
    std::vector<Sig> sig_;
    int n_ptr_;

    std::vector<NodeId> order_;
    std::vector<std::int32_t> index_of_;
    std::vector<NodeId> ptr_;
    std::vector<std::uint8_t> placed_;
    std::vector<std::int32_t> c_;
    std::vector<std::uint8_t> consumed_;
    std::vector<std::uint8_t> in_cand_;
    std::vector<EdgeId> cand_;
    std::vector<NodeId> creation_;
    std::vector<Token> tokens_;
    std::vector<std::int32_t> displacement_;
    std::int32_t n_placed_ = 0;
};

}  // namespace

OwResult ordered_walk_compute(const SHG& H, const std::vector<std::int32_t>& ranks,
                              const OwPolicy& policy) {
    if (static_cast<std::int32_t>(ranks.size()) != H.n_nodes) {
        throw IsalHGError("ranks must be a permutation of range(" + std::to_string(H.n_nodes) +
                          "); got " + std::to_string(ranks.size()) + " entries");
    }
    const std::int32_t max_arity = H.n_edges > 0 ? H.max_arity : 2;
    const int n_ptr = std::max(2, static_cast<int>(max_arity));
    const NodeId root = select_root(H, ranks, policy);

    Emitter emitter(H, ranks, policy, n_ptr, root);
    emitter.run();

    OwResult result;
    result.root = root;
    result.root_label = H.vertex_labels[static_cast<std::size_t>(root)];
    result.tokens = emitter.take_tokens();
    result.creation_order = emitter.take_creation();
    return result;
}

}  // namespace isalhg
