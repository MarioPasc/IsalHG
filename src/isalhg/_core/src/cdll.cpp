#include "isalhg/cdll.hpp"

namespace isalhg {

Cdll::Cdll(std::int32_t capacity) : capacity_(capacity), size_(0) {
    if (capacity_ <= 0) {
        throw IsalHGError("CDLL capacity must be positive");
    }
    slots_.assign(static_cast<std::size_t>(capacity_), CdllNode{-1, -1, 0});
    free_.reserve(static_cast<std::size_t>(capacity_));
    // Descending stack so pop_back() returns slot 0 first; matches Python.
    for (std::int32_t i = capacity_ - 1; i >= 0; --i) {
        free_.push_back(i);
    }
}

SlotIdx Cdll::insert_after(SlotIdx p, NodeId value) {
    if (free_.empty()) {
        throw CapacityError("CircularDoublyLinkedList is full");
    }
    SlotIdx new_slot = free_.back();
    free_.pop_back();
    slots_[static_cast<std::size_t>(new_slot)].data = value;

    if (size_ == 0) {
        slots_[static_cast<std::size_t>(new_slot)].next = new_slot;
        slots_[static_cast<std::size_t>(new_slot)].prev = new_slot;
    } else {
        SlotIdx next_of_p = slots_[static_cast<std::size_t>(p)].next;
        slots_[static_cast<std::size_t>(p)].next = new_slot;
        slots_[static_cast<std::size_t>(new_slot)].prev = p;
        slots_[static_cast<std::size_t>(new_slot)].next = next_of_p;
        slots_[static_cast<std::size_t>(next_of_p)].prev = new_slot;
    }
    ++size_;
    return new_slot;
}

void Cdll::remove(SlotIdx p) noexcept {
    if (size_ == 0) return;
    if (size_ == 1) {
        free_.push_back(p);
        size_ = 0;
        return;
    }
    SlotIdx prev_of_p = slots_[static_cast<std::size_t>(p)].prev;
    SlotIdx next_of_p = slots_[static_cast<std::size_t>(p)].next;
    slots_[static_cast<std::size_t>(prev_of_p)].next = next_of_p;
    slots_[static_cast<std::size_t>(next_of_p)].prev = prev_of_p;
    free_.push_back(p);
    --size_;
}

std::vector<SlotIdx> Cdll::iter_slots() const {
    std::vector<SlotIdx> out;
    if (size_ == 0) return out;
    out.reserve(static_cast<std::size_t>(size_));
    SlotIdx s = 0;
    out.push_back(s);
    SlotIdx cur = slots_[0].next;
    while (cur != s) {
        out.push_back(cur);
        cur = slots_[static_cast<std::size_t>(cur)].next;
    }
    return out;
}

}  // namespace isalhg
