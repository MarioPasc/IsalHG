// IsalHG native core — nanobind module entry.
//
// Phase 1 surface:
//   _core.ping()
//   _core.greedy_h2s(py_H, seed_node, k, wl_colors=None) -> str
//   _core.greedy_h2s_tokens(py_H, seed_node, k, wl_colors=None) -> list[tuple]
//
// SparseHypergraph stays a Python class; we copy its data into a C++ SHG
// view at the FFI boundary on each call. The cost is O(n + sum arities)
// per call — negligible for the canonical hot loop, which dominates.

#include <algorithm>
#include <cstdint>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>

#include <nanobind/nanobind.h>
#include <nanobind/stl/optional.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/tuple.h>
#include <nanobind/stl/vector.h>

#include "isalhg/errors.hpp"
#include "isalhg/h2s.hpp"
#include "isalhg/sparse_hypergraph.hpp"
#include "isalhg/token.hpp"

namespace nb = nanobind;
using namespace nb::literals;

namespace {

// Cached Python exception types (loaded from isalhg.errors at module init).
struct PyExcCache {
    PyObject* IsalHGError = nullptr;
    PyObject* H2SStuckError = nullptr;
    PyObject* DisconnectedHypergraphError = nullptr;
    PyObject* VocabularyMismatchError = nullptr;
    PyObject* CapacityError = nullptr;
    PyObject* InvalidLabelError = nullptr;
    PyObject* ArityMismatchError = nullptr;
    PyObject* InvalidInstructionError = nullptr;
};
PyExcCache g_exc{};

void init_exception_cache() {
    nb::module_ errors_mod = nb::module_::import_("isalhg.errors");
    auto fetch = [&](nb::handle mod, const char* name) -> PyObject* {
        if (!nb::hasattr(mod, name)) return nullptr;
        return nb::object(mod.attr(name)).release().ptr();
    };
    g_exc.IsalHGError = fetch(errors_mod, "IsalHGError");
    g_exc.DisconnectedHypergraphError = fetch(errors_mod, "DisconnectedHypergraphError");
    g_exc.VocabularyMismatchError = fetch(errors_mod, "VocabularyMismatchError");
    g_exc.CapacityError = fetch(errors_mod, "CapacityError");
    g_exc.InvalidLabelError = fetch(errors_mod, "InvalidLabelError");
    g_exc.ArityMismatchError = fetch(errors_mod, "ArityMismatchError");
    g_exc.InvalidInstructionError = fetch(errors_mod, "InvalidInstructionError");

    // H2SStuckError lives inside isalhg.core.hypergraph_to_string.
    try {
        nb::module_ h2s_mod = nb::module_::import_("isalhg.core.hypergraph_to_string");
        g_exc.H2SStuckError = fetch(h2s_mod, "H2SStuckError");
    } catch (...) {
        g_exc.H2SStuckError = nullptr;
    }
    if (g_exc.H2SStuckError == nullptr) g_exc.H2SStuckError = g_exc.IsalHGError;
}

// Translate C++ isalhg::* exceptions to the Python types in isalhg.errors.
void translate_exception(const std::exception_ptr& p) {
    try {
        std::rethrow_exception(p);
    } catch (const isalhg::H2SStuckError& e) {
        PyErr_SetString(g_exc.H2SStuckError, e.what());
    } catch (const isalhg::DisconnectedHypergraphError& e) {
        PyErr_SetString(g_exc.DisconnectedHypergraphError, e.what());
    } catch (const isalhg::VocabularyMismatchError& e) {
        PyErr_SetString(g_exc.VocabularyMismatchError, e.what());
    } catch (const isalhg::CapacityError& e) {
        PyErr_SetString(g_exc.CapacityError, e.what());
    } catch (const isalhg::InvalidLabelError& e) {
        PyErr_SetString(g_exc.InvalidLabelError, e.what());
    } catch (const isalhg::ArityMismatchError& e) {
        PyErr_SetString(g_exc.ArityMismatchError, e.what());
    } catch (const isalhg::InvalidInstructionError& e) {
        PyErr_SetString(g_exc.InvalidInstructionError, e.what());
    } catch (const isalhg::IsalHGError& e) {
        PyErr_SetString(g_exc.IsalHGError, e.what());
    }
}

// Build an SHG view from a Python SparseHypergraph.
isalhg::SHG shg_from_python(nb::handle py_H) {
    isalhg::SHG H{};
    H.n_nodes = nb::cast<std::int32_t>(py_H.attr("n_nodes"));
    H.n_edges = nb::cast<std::int32_t>(py_H.attr("n_edges"));
    H.n_vertex_labels = nb::cast<std::int32_t>(py_H.attr("n_vertex_labels"));
    H.n_edge_labels = nb::cast<std::int32_t>(py_H.attr("n_edge_labels"));

    H.vertex_labels.resize(static_cast<std::size_t>(H.n_nodes));
    nb::object vertex_label = py_H.attr("vertex_label");
    for (std::int32_t v = 0; v < H.n_nodes; ++v) {
        H.vertex_labels[static_cast<std::size_t>(v)] = nb::cast<std::int32_t>(vertex_label(v));
    }

    H.edge_labels.resize(static_cast<std::size_t>(H.n_edges));
    H.edge_members.resize(static_cast<std::size_t>(H.n_edges));

    // H.iter_edges() yields (edge_id, frozenset[int], edge_label).
    nb::object iter_edges = py_H.attr("iter_edges");
    nb::object it = nb::iter(iter_edges());
    for (auto item : it) {
        nb::tuple t = nb::cast<nb::tuple>(item);
        const auto eid = nb::cast<std::int32_t>(t[0]);
        // Members come as a frozenset[int]; iterate.
        std::vector<isalhg::NodeId> members;
        for (auto m : t[1]) {
            members.push_back(nb::cast<isalhg::NodeId>(m));
        }
        std::sort(members.begin(), members.end());
        H.edge_members[static_cast<std::size_t>(eid)] = std::move(members);
        H.edge_labels[static_cast<std::size_t>(eid)] = nb::cast<std::int32_t>(t[2]);
    }

    H.finalise(isalhg::DEFAULT_STRUCTURAL_DEPTH);
    return H;
}

}  // namespace

NB_MODULE(_core, m) {
    m.doc() = "IsalHG native core (C++17 implementation, nanobind bindings).";

    init_exception_cache();
    nb::register_exception_translator(
        [](const std::exception_ptr& p, void* /*payload*/) { translate_exception(p); });

    m.def("ping", []() -> const char* { return "pong"; });

    m.def(
        "greedy_h2s",
        [](nb::object py_H, isalhg::NodeId seed_node, int k,
           std::optional<std::vector<std::int64_t>> wl_colors) -> std::string {
            const isalhg::SHG H = shg_from_python(py_H);
            return isalhg::greedy_h2s_str(H, seed_node, k, wl_colors);
        },
        "H"_a, "seed_node"_a, "k"_a, "wl_colors"_a = nb::none(),
        "Greedy H2S encoder; returns the canonical-token sequence serialised as a ;-joined "
        "string. ``wl_colors`` (length n_nodes) prunes V-branch label permutations to canonical "
        "orbit representatives when supplied.");

    // For Phase 1 differential tests: return tokens as raw tuples to avoid
    // re-parsing the string. Each tuple is (kind:str, *fields).
    m.def(
        "greedy_h2s_tokens",
        [](nb::object py_H, isalhg::NodeId seed_node, int k,
           std::optional<std::vector<std::int64_t>> wl_colors) -> nb::list {
            const isalhg::SHG H = shg_from_python(py_H);
            const std::vector<isalhg::Token> toks =
                isalhg::greedy_h2s_tokens(H, seed_node, k, wl_colors);
            nb::list out;
            for (const isalhg::Token& t : toks) {
                switch (t.kind) {
                case isalhg::TokenKind::W:
                    out.append(nb::make_tuple(std::string("W")));
                    break;
                case isalhg::TokenKind::N:
                    out.append(nb::make_tuple(std::string("N"), static_cast<int>(t.i)));
                    break;
                case isalhg::TokenKind::P:
                    out.append(nb::make_tuple(std::string("P"), static_cast<int>(t.i)));
                    break;
                case isalhg::TokenKind::V: {
                    nb::list labels;
                    for (std::size_t k_ = 0; k_ < t.n_labels; ++k_) {
                        labels.append(static_cast<int>(t.labels[k_]));
                    }
                    out.append(nb::make_tuple(std::string("V"), static_cast<int>(t.edge_label),
                                              static_cast<int>(t.i), static_cast<int>(t.j),
                                              nb::tuple(labels)));
                    break;
                }
                case isalhg::TokenKind::C:
                    out.append(nb::make_tuple(std::string("C"), static_cast<int>(t.edge_label),
                                              static_cast<int>(t.i)));
                    break;
                }
            }
            return out;
        },
        "H"_a, "seed_node"_a, "k"_a, "wl_colors"_a = nb::none());
}
