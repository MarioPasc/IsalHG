// IsalHG native core — nanobind module entry point.
//
// Phase 0: stub only. Exposes _core.ping() to verify the build pipeline.
// Subsequent phases add greedy_h2s, structural tuples, WL, canonical_string.

#include <nanobind/nanobind.h>

namespace nb = nanobind;

NB_MODULE(_core, m) {
    m.doc() = "IsalHG native core (C++17 implementation, nanobind bindings).";
    m.def("ping", []() -> const char* { return "pong"; },
          "Build smoke test — returns the literal string \"pong\".");
}
