"""External hypergraph-library bridges.

Concrete adapters translate between :class:`isalhg.core.sparse_hypergraph.SparseHypergraph`
and the in-memory types of:

- HyperNetX (`hypernetx`)
- XGI (`xgi`)
- HypergraphX (`hypergraphx`)

DHG / DeepHypergraph was dropped pre-scaffold (deprecated ``sklearn`` shim +
torch 1.13 pin); see ``feedback_adapter_vetting.md`` in project memory.

Adapters are the *only* layer permitted to import the external libraries.
They guard imports with ``try/except ImportError`` so the package remains
importable when an optional dependency is missing.
"""

from __future__ import annotations
