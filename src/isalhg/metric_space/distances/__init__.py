"""Our distances and the HGED ground truth, each a ``HypergraphDistance``.

``isalhg_levenshtein`` (``d_I``, our method) lands here in T-M1b; the exact /
bipartite HGED oracle (``hged``) lands in T-M2. All import ``core`` only and
guard any optional external dependency inside method bodies.

``fact_levenshtein`` (``fact_rank`` / ``fact_rank_roles``) is the distance the
TKDE article adopts, over the fact alphabet of :mod:`isalhg.core.fact_word`;
``fact_addressing_ablations`` (``fact_local_colour`` / ``fact_local_key`` /
``fact_degree_key``) holds its three displaced-addressing comparison arms. Both
reach :func:`isalhg.iso_backends.canonical_order.canonical_ranks` inside
function bodies.
"""

from __future__ import annotations
