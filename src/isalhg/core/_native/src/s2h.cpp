// C++ S2H interpreter — port of ``isalhg.core.string_to_hypergraph``.
//
// Mirrors Python StringToHypergraph semantics exactly:
//   - Initial state: one seed node, CDLL capacity = 1 + sum(j for V tokens),
//     k pointers all at slot 0.
//   - V token: collect i existing nodes from p_1..p_i; insert j new nodes
//     after p_1's slot (chained); add the i+j-member hyperedge.
//   - C token: collect i nodes from p_1..p_i; add hyperedge (no-op if a
//     hyperedge with the same (label, member-set) already exists).
//   - P/N: advance/retreat the 1-based pointer via cdll.next/prev.
//   - W: no-op; never stripped (invariant 6).

#include "isalhg/s2h.hpp"

#include <algorithm>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

#include "isalhg/cdll.hpp"
#include "isalhg/errors.hpp"

namespace isalhg {

namespace {

// ---------------------------------------------------------------------------
// Internal token representation for S2H execution.
// Uses std::vector<int> for new_labels to avoid K_MAX constraint (correct
// decoding also for k > K_MAX when token j <= K_MAX-1 in practice).
// ---------------------------------------------------------------------------

struct S2HTok {
    char kind = 'W';       // 'W', 'P', 'N', 'V', 'C'
    int i = 0;             // pointer index (1-based); arity for V/C
    int j = 0;             // new-node count; V only
    int edge_label = 0;    // V, C only
    std::vector<int> new_labels;  // V only; length == j
};

// ---------------------------------------------------------------------------
// Parser helpers
// ---------------------------------------------------------------------------

static int parse_int_range(const char* s, const char* end) {
    if (s >= end) {
        throw InvalidInstructionError("expected integer, got empty field");
    }
    bool neg = false;
    const char* p = s;
    if (*p == '-') { neg = true; ++p; }
    int v = 0;
    while (p < end && *p >= '0' && *p <= '9') {
        v = v * 10 + (*p - '0');
        ++p;
    }
    return neg ? -v : v;
}

// Find next ';' at bracket depth 0.
static const char* next_top_sep(const char* s, const char* end) {
    int depth = 0;
    for (const char* p = s; p < end; ++p) {
        if      (*p == '[') ++depth;
        else if (*p == ']') --depth;
        else if (*p == ';' && depth == 0) return p;
    }
    return end;
}

// Parse a single token piece [s, end).
static S2HTok parse_one(const char* s, const char* end) {
    if (s >= end) throw InvalidInstructionError("empty token piece");

    S2HTok tok;
    tok.kind = *s;

    if (tok.kind == 'W') {
        // Must be exactly "W".
        if (end - s != 1) throw InvalidInstructionError("malformed W token");
        return tok;
    }

    // All remaining tokens: "X[body]"
    if (end - s < 4 || s[1] != '[' || *(end - 1) != ']') {
        throw InvalidInstructionError("malformed token: missing brackets");
    }
    const char* body = s + 2;         // skip "X["
    const char* body_end = end - 1;   // trim "]"

    if (tok.kind == 'P' || tok.kind == 'N') {
        tok.i = parse_int_range(body, body_end);
    } else if (tok.kind == 'C') {
        // body = "le;i"
        const char* sep = std::find(body, body_end, ';');
        if (sep == body_end) throw InvalidInstructionError("C token: missing ';'");
        tok.edge_label = parse_int_range(body, sep);
        tok.i = parse_int_range(sep + 1, body_end);
    } else if (tok.kind == 'V') {
        // body = "le;i;j;ln1,...,lnj"
        const char* p = body;
        const char* sep1 = std::find(p, body_end, ';');
        if (sep1 == body_end) throw InvalidInstructionError("V token: missing fields");
        tok.edge_label = parse_int_range(p, sep1);
        p = sep1 + 1;

        const char* sep2 = std::find(p, body_end, ';');
        if (sep2 == body_end) throw InvalidInstructionError("V token: missing fields");
        tok.i = parse_int_range(p, sep2);
        p = sep2 + 1;

        const char* sep3 = std::find(p, body_end, ';');
        if (sep3 == body_end) throw InvalidInstructionError("V token: missing fields");
        tok.j = parse_int_range(p, sep3);
        p = sep3 + 1;

        // Parse comma-separated labels; empty means j==0.
        if (p < body_end) {
            while (p <= body_end) {
                const char* comma = std::find(p, body_end, ',');
                tok.new_labels.push_back(parse_int_range(p, comma));
                p = (comma < body_end) ? comma + 1 : body_end + 1;
            }
        }
        if (static_cast<int>(tok.new_labels.size()) != tok.j) {
            throw InvalidInstructionError("V token: label count != j");
        }
    } else {
        throw InvalidInstructionError(std::string("unknown token kind: ") + tok.kind);
    }
    return tok;
}

// Parse all tokens from s.
static std::vector<S2HTok> parse_s2h_string(const std::string& s) {
    std::vector<S2HTok> tokens;
    if (s.empty()) return tokens;
    const char* start = s.c_str();
    const char* end   = start + s.size();
    const char* p     = start;
    while (p < end) {
        const char* next = next_top_sep(p, end);
        tokens.push_back(parse_one(p, next));
        p = (next < end) ? next + 1 : end;
    }
    return tokens;
}

// Capacity = 1 (seed) + sum of j across V tokens.
static int capacity_for(const std::vector<S2HTok>& tokens) {
    int cap = 1;
    for (const auto& t : tokens) {
        if (t.kind == 'V') cap += t.j;
    }
    return cap;
}

// Edge dedup key: (label, sorted-unique member ids).
struct EdgeKey {
    int label;
    std::vector<NodeId> members;  // sorted, unique
    bool operator<(const EdgeKey& o) const noexcept {
        if (label != o.label) return label < o.label;
        return members < o.members;
    }
};

static EdgeKey make_edge_key(int label, const std::vector<NodeId>& raw_members) {
    EdgeKey k{label, raw_members};
    std::sort(k.members.begin(), k.members.end());
    k.members.erase(
        std::unique(k.members.begin(), k.members.end()),
        k.members.end());
    return k;
}

}  // namespace

// ---------------------------------------------------------------------------
// Public entry point
// ---------------------------------------------------------------------------

S2HResult string_to_hypergraph_compute(
    const std::string& s,
    int k,
    int n_vertex_labels,
    int n_edge_labels,
    int seed_label)
{
    const std::vector<S2HTok> tokens = parse_s2h_string(s);

    S2HResult H;
    H.n_vertex_labels = n_vertex_labels;
    H.n_edge_labels   = n_edge_labels;

    // Seed node.
    H.vertex_labels.push_back(static_cast<NodeId>(seed_label));

    // CDLL pre-allocated to worst-case vertex count.
    const int cap = std::max(1, capacity_for(tokens));
    Cdll cdll(cap);
    // Insert seed at slot 0.
    cdll.insert_after(0, 0);

    // k pointers (1-based externally; 0-indexed here), all at slot 0.
    std::vector<SlotIdx> pointers(static_cast<std::size_t>(k), SlotIdx{0});

    // Edge-existence lookup for C token deduplication.
    // Key = (label, sorted-unique member ids). std::map avoids hash complexity.
    std::map<EdgeKey, int> edge_lookup;

    for (const auto& tok : tokens) {
        switch (tok.kind) {
        case 'W':
            // No-op — invariant 6: W tokens never stripped.
            break;

        case 'P': {
            // Advance pointer p_{tok.i} to next CDLL slot.
            const std::size_t idx = static_cast<std::size_t>(tok.i - 1);
            pointers[idx] = cdll.next_node(pointers[idx]);
            break;
        }

        case 'N': {
            // Retreat pointer p_{tok.i} to prev CDLL slot.
            const std::size_t idx = static_cast<std::size_t>(tok.i - 1);
            pointers[idx] = cdll.prev_node(pointers[idx]);
            break;
        }

        case 'C': {
            // Collect tok.i existing members from p_1..p_{tok.i}.
            // Pointers are CDLL slot indices; resolve via get_value (invariant 1).
            std::vector<NodeId> members;
            members.reserve(static_cast<std::size_t>(tok.i));
            for (int pi = 0; pi < tok.i; ++pi) {
                members.push_back(cdll.get_value(pointers[static_cast<std::size_t>(pi)]));
            }
            // Add hyperedge; no-op if (label, member-set) already exists.
            EdgeKey key = make_edge_key(tok.edge_label, members);
            if (edge_lookup.find(key) == edge_lookup.end()) {
                const int eid = static_cast<int>(H.edge_labels.size());
                H.edge_labels.push_back(tok.edge_label);
                H.edge_members.push_back(members);
                edge_lookup.emplace(std::move(key), eid);
            }
            break;
        }

        case 'V': {
            // Collect tok.i existing members from p_1..p_{tok.i}.
            std::vector<NodeId> members;
            members.reserve(static_cast<std::size_t>(tok.i + tok.j));
            for (int pi = 0; pi < tok.i; ++pi) {
                members.push_back(cdll.get_value(pointers[static_cast<std::size_t>(pi)]));
            }
            // Insert tok.j new nodes after p_1's current slot (chained).
            // p_1 is pointers[0] — its slot is the insertion anchor.
            SlotIdx insert_after = pointers[0];
            for (int jj = 0; jj < tok.j; ++jj) {
                const NodeId v = static_cast<NodeId>(H.vertex_labels.size());
                const int label = tok.new_labels[static_cast<std::size_t>(jj)];
                H.vertex_labels.push_back(label);
                const SlotIdx new_slot = cdll.insert_after(insert_after, v);
                members.push_back(v);
                insert_after = new_slot;
            }
            // Add hyperedge; V always adds (encoder never emits V for existing edges).
            // Still register in edge_lookup so any subsequent C can detect it.
            const int eid = static_cast<int>(H.edge_labels.size());
            H.edge_labels.push_back(tok.edge_label);
            H.edge_members.push_back(members);
            EdgeKey key = make_edge_key(tok.edge_label, members);
            edge_lookup.emplace(std::move(key), eid);
            break;
        }

        default:
            throw InvalidInstructionError(
                std::string("unknown S2HTok kind during execution: ") + tok.kind);
        }
    }

    return H;
}

}  // namespace isalhg
