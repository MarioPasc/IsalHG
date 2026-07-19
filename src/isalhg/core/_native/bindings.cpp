// IsalHG native core — nanobind module entry.
//
// Phase 1 surface:
//   _core.ping()
//   _core.greedy_h2s(py_H, seed_node, k, tie_branch=False) -> str
//   _core.greedy_h2s_tokens(py_H, seed_node, k, tie_branch=False) -> list[tuple]
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

#include "isalhg/canonical.hpp"
#include "isalhg/errors.hpp"
#include "isalhg/h2s.hpp"
#include "isalhg/s2h.hpp"
#include "isalhg/sparse_hypergraph.hpp"
#include "isalhg/structural_tuples.hpp"
#include "isalhg/token.hpp"
#include "isalhg/wl.hpp"

namespace nb = nanobind;
using namespace nb::literals;

namespace {

// Cached Python exception types (loaded from isalhg.errors at module init).
struct PyExcCache {
    PyObject* IsalHGError = nullptr;
    PyObject* H2SStuckError = nullptr;
    PyObject* DisconnectedHypergraphError = nullptr;
    PyObject* CanonicalizationTimeoutError = nullptr;
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
    g_exc.CanonicalizationTimeoutError = fetch(errors_mod, "CanonicalizationTimeoutError");
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
    } catch (const isalhg::CanonicalizationTimeoutError& e) {
        PyErr_SetString(g_exc.CanonicalizationTimeoutError, e.what());
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
           bool tie_branch) -> std::string {
            const isalhg::SHG H = shg_from_python(py_H);
            return isalhg::greedy_h2s_str(H, seed_node, k, tie_branch);
        },
        "H"_a, "seed_node"_a, "k"_a, "tie_branch"_a = false,
        "Greedy H2S encoder; returns the canonical-token sequence serialised as a ;-joined "
        "string. ``tie_branch`` recurses over every V candidate tying on the iso-invariant "
        "cascade key-prefix and keeps the lex-min completion.");

    m.def(
        "required_k",
        [](nb::object py_H) -> int {
            const isalhg::SHG H = shg_from_python(py_H);
            return isalhg::required_k_compute(H);
        },
        "H"_a, "Return max(2, max arity) — the smallest admissible VM pointer count.");

    m.def(
        "max_xi_nodes",
        [](nb::object py_H, int depth) -> std::vector<isalhg::NodeId> {
            const isalhg::SHG H = shg_from_python(py_H);
            return isalhg::max_xi_nodes_compute(H, depth);
        },
        "H"_a, "depth"_a = isalhg::DEFAULT_STRUCTURAL_DEPTH,
        "Return the lex-argmax-(xi_labelled, vertex_label) seed set.");

    m.def(
        "max_neighbor_degree_nodes",
        [](nb::object py_H) -> std::vector<isalhg::NodeId> {
            const isalhg::SHG H = shg_from_python(py_H);
            return isalhg::max_neighbor_degree_nodes_compute(H);
        },
        "H"_a,
        "Return the lex-argmax (vertex_label, degree, sorted-desc neighbour "
        "degrees) seed set (PI 2026-06-23). Iso-invariant by construction; "
        "strictly cheaper than max_xi_nodes (no depth-3 BFS) and typically "
        "more discriminating on non-vertex-transitive inputs.");

    m.def(
        "wl_hash",
        [](nb::object py_H, int max_rounds) -> std::vector<std::int64_t> {
            const isalhg::SHG H = shg_from_python(py_H);
            const auto raw = isalhg::wl_hash_compute(H, max_rounds);
            // Python uses signed Python int; FNV-1a values fit in uint64.
            // Cast through int64 for nanobind list-of-int conversion.
            std::vector<std::int64_t> out;
            out.reserve(raw.size());
            for (std::uint64_t c : raw) out.push_back(static_cast<std::int64_t>(c));
            return out;
        },
        "H"_a, "max_rounds"_a = isalhg::WL_MAX_ROUNDS,
        "Per-vertex stable 1-WL colour using FNV-1a 64-bit (cross-process stable).");

    m.def(
        "canonical_string",
        [](nb::object py_H, int k, int structural_depth, int algorithm_id,
           int max_expansions) -> std::string {
            // Build the SHG view under the GIL (touches Python objects).
            const isalhg::SHG H = shg_from_python(py_H);
            const auto variant = static_cast<isalhg::AlgorithmVariant>(algorithm_id);
            // The compute phase is GIL-free so the seed loop can fan
            // out across hardware threads without contending with Python.
            std::string result;
            {
                nb::gil_scoped_release release;
                result = isalhg::canonical_string_compute(
                    H, k, structural_depth, variant, max_expansions);
            }
            return result;
        },
        "H"_a, "k"_a, "structural_depth"_a, "algorithm_id"_a, "max_expansions"_a = 0,
        "Compute the canonical Sigma_HG* string. algorithm_id matches AlgorithmVariant:\n"
        "  0 = greedy_min, 1 = greedy_single, 2 = greedy_min_inplace,\n"
        "  3 = greedy_min_wl_pruned, 4 = greedy_min_inplace_wl_pruned,\n"
        "  5 = greedy_min_nbrdeg, 6 = greedy_single_nbrdeg, 7 = canonical.\n"
        "max_expansions: V-branch (tie-branch) budget per seed; 0 = unlimited.\n"
        "  Raises CanonicalizationTimeoutError when any seed exceeds the limit.");

    // For Phase 1 differential tests: return tokens as raw tuples to avoid
    // re-parsing the string. Each tuple is (kind:str, *fields).
    // S2H interpreter: parse a Sigma_HG* string and execute the VM,
    // returning raw hypergraph data for Python shim reconstruction.
    //
    // Returns (vertex_labels, edge_labels, edge_members):
    //   vertex_labels : list[int]  -- one per node, in node-id order.
    //   edge_labels   : list[int]  -- one per edge, in insertion order.
    //   edge_members  : list[list[int]] -- member node ids per edge.
    m.def(
        "string_to_hypergraph_raw",
        [](const std::string& s, int k, int n_vertex_labels, int n_edge_labels,
           int seed_label) -> nb::tuple {
            isalhg::S2HResult result;
            {
                nb::gil_scoped_release release;
                result = isalhg::string_to_hypergraph_compute(
                    s, k, n_vertex_labels, n_edge_labels, seed_label);
            }
            nb::list vertex_labels;
            for (const auto v : result.vertex_labels) {
                vertex_labels.append(static_cast<int>(v));
            }
            nb::list edge_labels;
            for (const auto el : result.edge_labels) {
                edge_labels.append(el);
            }
            nb::list edge_members_out;
            for (const auto& members : result.edge_members) {
                nb::list ml;
                for (const auto v : members) {
                    ml.append(static_cast<int>(v));
                }
                edge_members_out.append(ml);
            }
            return nb::make_tuple(vertex_labels, edge_labels, edge_members_out);
        },
        "s"_a, "k"_a, "n_vertex_labels"_a = 1, "n_edge_labels"_a = 1, "seed_label"_a = 0,
        "Parse and execute a Sigma_HG* string.\n"
        "Returns (vertex_labels, edge_labels, edge_members) for Python-side reconstruction.\n"
        "W tokens execute as no-ops (never stripped). Pointer moves use CDLL slots (invariant 1).\n"
        "Closed-alphabet: every well-formed string decodes without error.");

    m.def(
        "greedy_h2s_tokens",
        [](nb::object py_H, isalhg::NodeId seed_node, int k,
           bool tie_branch) -> nb::list {
            const isalhg::SHG H = shg_from_python(py_H);
            const std::vector<isalhg::Token> toks =
                isalhg::greedy_h2s_tokens(H, seed_node, k, tie_branch);
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
        "H"_a, "seed_node"_a, "k"_a, "tie_branch"_a = false);
}
