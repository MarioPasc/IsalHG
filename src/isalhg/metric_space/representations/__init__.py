"""Competing hypergraph representations, each wrapped as a ``HypergraphDistance``.

``hypergraph_wl`` (the fair WL baseline) lands here in T-M1b; the nauty-Levi
contrast and the vendored / subprocess competitors land in T-M3a-d. All guard
their optional external dependencies inside method bodies.
"""

from __future__ import annotations
