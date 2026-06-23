#include "isalhg/token.hpp"

#include <cstdio>

namespace isalhg {

int token_cmp(const Token& a, const Token& b) noexcept {
    const auto ka = static_cast<std::uint8_t>(a.kind);
    const auto kb = static_cast<std::uint8_t>(b.kind);
    if (ka != kb) {
        return ka < kb ? -1 : 1;
    }
    switch (a.kind) {
    case TokenKind::W:
        return 0;
    case TokenKind::N:
    case TokenKind::P:
        if (a.i != b.i) return a.i < b.i ? -1 : 1;
        return 0;
    case TokenKind::V:
        if (a.edge_label != b.edge_label) return a.edge_label < b.edge_label ? -1 : 1;
        if (a.i != b.i) return a.i < b.i ? -1 : 1;
        if (a.j != b.j) return a.j < b.j ? -1 : 1;
        {
            const int la = a.n_labels;
            const int lb = b.n_labels;
            const int common = la < lb ? la : lb;
            for (int k = 0; k < common; ++k) {
                if (a.labels[static_cast<std::size_t>(k)]
                    != b.labels[static_cast<std::size_t>(k)]) {
                    return a.labels[static_cast<std::size_t>(k)]
                                   < b.labels[static_cast<std::size_t>(k)]
                               ? -1
                               : 1;
                }
            }
            if (la != lb) return la < lb ? -1 : 1;
        }
        return 0;
    case TokenKind::C:
        if (a.edge_label != b.edge_label) return a.edge_label < b.edge_label ? -1 : 1;
        if (a.i != b.i) return a.i < b.i ? -1 : 1;
        return 0;
    }
    return 0;  // unreachable
}

int sequence_cmp(const std::vector<Token>& a, const std::vector<Token>& b) noexcept {
    if (a.size() != b.size()) {
        return a.size() < b.size() ? -1 : 1;
    }
    for (std::size_t k = 0; k < a.size(); ++k) {
        const int c = token_cmp(a[k], b[k]);
        if (c != 0) return c;
    }
    return 0;
}

namespace {

void append_int(std::string& out, std::int32_t v) {
    char buf[16];
    const int n = std::snprintf(buf, sizeof(buf), "%d", v);
    if (n > 0) {
        out.append(buf, static_cast<std::size_t>(n));
    }
}

}  // namespace

void serialize_into(std::string& out, const Token& t) {
    switch (t.kind) {
    case TokenKind::W:
        out.push_back('W');
        return;
    case TokenKind::N:
        out.push_back('N');
        out.push_back('[');
        append_int(out, t.i);
        out.push_back(']');
        return;
    case TokenKind::P:
        out.push_back('P');
        out.push_back('[');
        append_int(out, t.i);
        out.push_back(']');
        return;
    case TokenKind::V:
        out.push_back('V');
        out.push_back('[');
        append_int(out, t.edge_label);
        out.push_back(';');
        append_int(out, t.i);
        out.push_back(';');
        append_int(out, t.j);
        out.push_back(';');
        for (std::size_t k = 0; k < t.n_labels; ++k) {
            if (k > 0) out.push_back(',');
            append_int(out, t.labels[k]);
        }
        out.push_back(']');
        return;
    case TokenKind::C:
        out.push_back('C');
        out.push_back('[');
        append_int(out, t.edge_label);
        out.push_back(';');
        append_int(out, t.i);
        out.push_back(']');
        return;
    }
}

std::string serialize(const std::vector<Token>& tokens) {
    std::string out;
    // Heuristic capacity: 8 bytes/token average. Avoids growth in tight loops.
    out.reserve(tokens.size() * 8u);
    for (std::size_t k = 0; k < tokens.size(); ++k) {
        if (k > 0) out.push_back(';');
        serialize_into(out, tokens[k]);
    }
    return out;
}

}  // namespace isalhg
