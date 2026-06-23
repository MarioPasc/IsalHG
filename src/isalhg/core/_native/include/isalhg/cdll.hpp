// Array-backed circular doubly-linked list, AoS layout.
//
// Mirrors ``src/isalhg/core/cdll.py`` semantics 1:1. The free-list is
// initialised as a descending stack so the first allocation yields slot 0,
// matching the Python invariant relied on by S2H / H2S.
#pragma once

#include <cstdint>
#include <vector>

#include "isalhg/errors.hpp"

namespace isalhg {

using SlotIdx = std::int32_t;
using NodeId  = std::int32_t;

struct CdllNode {
    SlotIdx next;
    SlotIdx prev;
    NodeId  data;
};

class Cdll {
public:
    explicit Cdll(std::int32_t capacity);

    [[nodiscard]] std::int32_t size()     const noexcept { return size_; }
    [[nodiscard]] std::int32_t capacity() const noexcept { return capacity_; }

    [[nodiscard]] NodeId  get_value(SlotIdx p) const noexcept { return slots_[p].data; }
    void set_value(SlotIdx p, NodeId value) noexcept { slots_[p].data = value; }

    [[nodiscard]] SlotIdx next_node(SlotIdx p) const noexcept { return slots_[p].next; }
    [[nodiscard]] SlotIdx prev_node(SlotIdx p) const noexcept { return slots_[p].prev; }

    SlotIdx insert_after(SlotIdx p, NodeId value);
    void    remove(SlotIdx p) noexcept;

    [[nodiscard]] SlotIdx head() const { return 0; }  // valid only when size_>0

    // Forward circular walk starting at slot 0; used by tests and serialisers.
    [[nodiscard]] std::vector<SlotIdx> iter_slots() const;

private:
    std::int32_t          capacity_;
    std::int32_t          size_;
    std::vector<CdllNode> slots_;
    std::vector<SlotIdx>  free_;  // stack; pop_back() returns next slot
};

}  // namespace isalhg
