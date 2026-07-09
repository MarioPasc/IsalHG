"""Our distances and the HGED ground truth, each a ``HypergraphDistance``.

``isalhg_levenshtein`` (``d_I``, our method) lands here in T-M1b; the exact /
bipartite HGED oracle (``hged``) lands in T-M2. All import ``core`` only and
guard any optional external dependency inside method bodies.
"""

from __future__ import annotations
