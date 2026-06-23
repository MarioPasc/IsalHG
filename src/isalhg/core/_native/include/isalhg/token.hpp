// Sigma_HG token, flat tagged representation.
//
// 28 bytes per token, no heap allocations. Lex comparison matches the
// Python ``Token.sort_key()`` cascade exactly:
//   W < N[i] < P[i] < V[le; i; j; labels...] < C[le; i]
// with ascending integer comparison within each tag.
#pragma once

#include <array>
#include <cstdint>
#include <string>
#include <vector>

#include "isalhg/cdll.hpp"  // for NodeId; not strictly needed here

namespace isalhg {

constexpr int K_MAX = 10;        // hyperedge arity cap (PROPOSAL B12)
constexpr int MAX_NEW = K_MAX - 1;  // max j in V[le; i; j; ...]

enum class TokenKind : std::uint8_t {
    W = 0,
    N = 1,
    P = 2,
    V = 3,
    C = 4,
};

struct Token {
    TokenKind kind = TokenKind::W;
    std::int16_t i = 0;            // N, P, V, C
    std::int16_t j = 0;            // V only
    std::int16_t edge_label = 0;   // V, C only
    std::uint8_t n_labels = 0;     // V only
    std::array<std::int16_t, MAX_NEW> labels{};  // V only; first n_labels entries

    static Token make_w() noexcept { return Token{TokenKind::W, 0, 0, 0, 0, {}}; }
    static Token make_n(int i_val) noexcept {
        return Token{TokenKind::N, static_cast<std::int16_t>(i_val), 0, 0, 0, {}};
    }
    static Token make_p(int i_val) noexcept {
        return Token{TokenKind::P, static_cast<std::int16_t>(i_val), 0, 0, 0, {}};
    }
    static Token make_c(int edge_label_, int i_val) noexcept {
        return Token{TokenKind::C, static_cast<std::int16_t>(i_val), 0,
                     static_cast<std::int16_t>(edge_label_), 0, {}};
    }
    static Token make_v(int edge_label_, int i_val, int j_val,
                        const std::int16_t* sorted_labels, int n_labels) noexcept {
        Token t{};
        t.kind = TokenKind::V;
        t.i = static_cast<std::int16_t>(i_val);
        t.j = static_cast<std::int16_t>(j_val);
        t.edge_label = static_cast<std::int16_t>(edge_label_);
        t.n_labels = static_cast<std::uint8_t>(n_labels);
        for (int k = 0; k < n_labels; ++k) {
            t.labels[static_cast<std::size_t>(k)] = sorted_labels[k];
        }
        return t;
    }
    static Token make_v(int edge_label_, int i_val, int j_val,
                        const std::vector<std::int16_t>& sorted_labels) {
        return make_v(edge_label_, i_val, j_val, sorted_labels.data(),
                      static_cast<int>(sorted_labels.size()));
    }
};

// Strict weak ordering matching Token.sort_key() in Python.
[[nodiscard]] int token_cmp(const Token& a, const Token& b) noexcept;

[[nodiscard]] inline bool operator<(const Token& a, const Token& b) noexcept {
    return token_cmp(a, b) < 0;
}
[[nodiscard]] inline bool operator==(const Token& a, const Token& b) noexcept {
    return token_cmp(a, b) == 0;
}

// sequence_sort_key compare: (len(a) < len(b)) || (len equal && element-wise compare).
// Matches the Python (length, *sort_keys) tuple comparison.
[[nodiscard]] int sequence_cmp(const std::vector<Token>& a,
                               const std::vector<Token>& b) noexcept;

// Serialize a single token to its surface form (e.g. "V[0;1;2;3,4]").
void serialize_into(std::string& out, const Token& t);

// Serialize a vector of tokens as ';'-joined surface forms.
[[nodiscard]] std::string serialize(const std::vector<Token>& tokens);

}  // namespace isalhg
