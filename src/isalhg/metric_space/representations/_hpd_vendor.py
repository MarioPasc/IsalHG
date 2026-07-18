# mypy: ignore-errors
# ruff: noqa: ANN001, ANN202
"""Vendored Hyperedge Portrait Divergence functions from Agostinelli et al. (2026).

Provenance
----------
Source repository : https://github.com/cosimoagostinelli/Hor_dissimilarity_measures
Commit hash       : f190266b4ada36d57fd320422d70b915d11a7961
Retrieval date    : 2026-07-15
Source file       : code/hypergraph_distances.py

License (MIT)
-------------
MIT License

Copyright (c) 2025 cosimoagostinelli

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Functions copied (verbatim from upstream source file)
------------------------------------------------------
- ``H_to_G_mapping``            (lines 120-153 in upstream ``hypergraph_distances.py``)
- ``hyperedge_portrait``        (lines 157-207 in upstream ``hypergraph_distances.py``)
- ``pad_h_portraits``           (lines 211-247 in upstream ``hypergraph_distances.py``)
- ``hyper_portrait_divergence`` (lines 251-281 in upstream ``hypergraph_distances.py``)

Functions NOT copied (present in upstream, not HPD)
---------------------------------------------------
- ``feature_vec``  — Hyper-NetSimile descriptor; omitted (out of T-M3b scope).
- ``DunnIndex``    — clustering quality index; omitted (out of T-M3b scope).

Adaptations made (exhaustive list)
-----------------------------------
1. Module-level docstring (this block) added; not present in upstream file.
2. ``# mypy: ignore-errors`` directive added at the very top of this file.
   The upstream code is untyped; mypy strict mode raises several type errors
   in the function bodies (``no-untyped-call`` for ``xgi.unique_edge_sizes``,
   ``arg-type`` for the ``isinstance``-narrowed union branches in
   ``hyper_portrait_divergence``, ``no-any-return``). Suppressing the entire
   file is the standard practice for vendored third-party code.
3. ``from __future__ import annotations`` added (Python 3.10+ forward-ref
   compatibility); not present in upstream.
4. Import list trimmed to dependencies of the four extracted functions only:
   ``from scipy.stats import kurtosis, skew`` removed (``feature_vec`` only);
   ``from scipy.cluster import hierarchy`` removed (``DunnIndex`` only).
5. Section-comment banners (``# --- Hyper-NetSimile ---`` and
   ``# --- Hyper-Portrait Divergence ---``) omitted: only the HPD section
   is present here.
6. ``# noqa: N802`` added to ``def H_to_G_mapping`` (ruff N802: function
   name should be lowercase; the mixed-case name is verbatim upstream and
   carries mathematical convention: ``H`` = hypergraph, ``G`` = graph).
7. ``# noqa: E741`` added to ``for l in range(dia + 1)`` (ruff E741:
   ambiguous variable name; ``l`` is the distance/shell index in the paper's
   own notation, verbatim from upstream).
8. Upstream function signatures have NO type annotations; none are added here
   (adding annotations would be a non-trivial adaptation and is covered by
   point 2 — ``# mypy: ignore-errors`` means this file is not type-checked).
9. No other changes: function bodies, docstrings, logic, and variable names
   are byte-for-byte identical to the upstream source (modulo whitespace
   normalised by the project formatter on items 6-7 above).
"""

from __future__ import annotations

from itertools import combinations

import networkx as nx
import numpy as np
import xgi
from scipy.spatial import distance


def H_to_G_mapping(H):  # noqa: N802
    (
        """"""
        """""
    Map the hypergraph to a graph where each node represents
    a former hyperedge, and two nodes are connected if the original
    hyperedges shared at least one node. Every node has an attribute,
    that is the size of the hyperedge it represents.

    Parameters:
    ---------------
    H (xgi.hypergraph) : the hypergraph to map.
    ---------------

    Returns:
        G (networkx.Graph): the network G resulting from the mapping.

    """
        """"""
        ""
    )

    new_nodes = list(H.edges)
    new_edges = []
    sizes = H.edges.size.asdict()

    for id1, id2 in combinations(H.edges, 2):
        e1 = H.edges.members(id1)
        e2 = H.edges.members(id2)
        if len(e1.intersection(e2)) > 0:
            new_edges.append((id1, id2))

    G = nx.Graph()
    G.add_nodes_from(new_nodes)
    G.add_edges_from(new_edges)
    nx.set_node_attributes(G, sizes, name="size")

    return G


def hyperedge_portrait(H):
    (
        """"""
        """""
    The hyperedge-portrait of the given hypergraph H.
    The hyperedge portrait is a tensor with four indices whose entry B_{m,n,l,k}
    gives the number of hyperedges of size m having k hyperedges of size n at
    distance l. Two hyperedges are at distance 1 if they share at least one node.

    Parameters:
    ---------------
    H (xgi.Hypergraph) : the input hypergraph.
    ---------------

    Returns:
        B (numpy.array) : the hyperedge-portrait of H, as a 4-dimensional array.

    """
        """"""
        ""
    )

    G = H_to_G_mapping(H)
    N = G.number_of_nodes()
    sizes_dict = nx.get_node_attributes(G, "size")
    s_max = np.max(xgi.unique_edge_sizes(H))
    # connected components
    CC = [G.subgraph(c).copy() for c in nx.connected_components(G)]

    # compute all shortest paths and get diameter to inizialize B
    dist_dict = dict()
    lengths = set()
    for Gc in CC:
        for i in Gc.nodes:
            dist_dict[i] = nx.shortest_path_length(Gc, i)
            lengths |= set(dist_dict[i].values())

    dia = max(lengths)
    B = np.zeros((s_max - 1, s_max - 1, dia + 1, N), dtype=int)

    for Gc in CC:
        for i in Gc.nodes:
            m = sizes_dict[i] - 2
            dd_i = dist_dict[i]
            counter = np.zeros((s_max - 1, dia + 1), dtype=int)

            for j in Gc.nodes:
                counter[sizes_dict[j] - 2][dd_i[j]] += 1

            for n in range(s_max - 1):
                for l in range(dia + 1):  # noqa: E741
                    k = counter[n][l]
                    B[m][n][l][k] += 1

    return B


def pad_h_portraits(B1, B2):
    (
        """"""
        """
    Make sure that two tensors are padded with zeros and/or trimmed of
    zeros in order to have the same dimensions.

    Parameters:
    --------------
    B1, B2 : the two hyperedge portraits of the hypergraphs to compare.
    --------------

    Returns (B1, B2) : the two hyperedge portraits with same dimensions.

    """
        """"""
    )

    # the B tensors have last dimension = E (number of hyperedges)
    # by default. Find last occupied "column" and trim both down:
    lastcol1 = max(np.nonzero(B1)[3])
    lastcol2 = max(np.nonzero(B2)[3])
    lastcol = max(lastcol1, lastcol2)
    B1 = B1[:, :, :, : lastcol + 1]
    B2 = B2[:, :, :, : lastcol + 1]

    for i in range(4):
        max_dim = max(B1.shape[i], B2.shape[i])

        dims = list(B1.shape)
        dims[i] = max_dim - dims[i]
        to_stack = np.zeros(dims, dtype=int)
        B1 = np.append(B1, to_stack, axis=i)

        dims = list(B2.shape)
        dims[i] = max_dim - dims[i]
        to_stack = np.zeros(dims, dtype=int)
        B2 = np.append(B2, to_stack, axis=i)

    return (B1, B2)


def hyper_portrait_divergence(B1, B2):
    (
        """"""
        """
    Dissimilarity measure between the two hypergraphs H1, H2, based
    on the generalization of the portrait divergence. It is defined
    as the Jensen-Shannon divergence between the distributions P1, P2
    associated to the two hypergraphs. P is built upon the hyperedge
    portrait of the hypergraph (see edge_portrait(H) function):
    P(m,n,l,k) = B_{m,n,l,k} / normalization.

    Parameters :
    --------------
    B1, B2 : can be either the two hypergraphs to compare (xgi.Hypergraph)
             or their hyperedge portraits, obtained via the
             hyperedge_portrait(H) function.
    --------------

    Returns (float) : the hyperedge portrait divergence between H1 and H2.

    """
        """"""
    )

    if isinstance(B1, xgi.Hypergraph):
        B1 = hyperedge_portrait(B1)
        B2 = hyperedge_portrait(B2)

    B1, B2 = pad_h_portraits(B1, B2)
    P1 = np.ravel(B1)
    P2 = np.ravel(B2)
    JSD = distance.jensenshannon(P1, P2, base=2)

    return JSD * JSD
