// FNV-1a 64-bit deterministic hash.
//
// Replaces Python's ``hash()`` in the WL refiner so that the produced
// colour partition is identical across processes (Python's ``hash`` is
// salted by ``PYTHONHASHSEED`` and breaks cross-process determinism on
// strings/tuples).
#pragma once

#include <cstdint>

namespace isalhg {

constexpr std::uint64_t FNV_OFFSET = 14695981039346656037ULL;
constexpr std::uint64_t FNV_PRIME  = 1099511628211ULL;

// Domain tags so vertex / edge / final-vertex hashing live in distinct
// integer ranges (zero collision probability across roles).
constexpr std::uint64_t FNV_DOMAIN_VERTEX_INIT  = 0xABCD0001ULL;
constexpr std::uint64_t FNV_DOMAIN_EDGE_SIG     = 0xABCD0002ULL;
constexpr std::uint64_t FNV_DOMAIN_VERTEX_NEW   = 0xABCD0003ULL;

[[nodiscard]] inline std::uint64_t fnv1a_mix(std::uint64_t h, std::uint64_t v) noexcept {
    h ^= v;
    h *= FNV_PRIME;
    return h;
}

[[nodiscard]] inline std::uint64_t fnv1a_init(std::uint64_t v) noexcept {
    return fnv1a_mix(FNV_OFFSET, v);
}

}  // namespace isalhg
