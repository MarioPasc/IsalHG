"""HyperCOT corpus worker — runs inside the ``isalhg-hypercot`` pinned env.

Upstream repository
-------------------
URL:         https://github.com/samirchowdhury/HyperCOT
Licence:     MIT
Commit hash: <populate after build: git -C /path/to/HyperCOT rev-parse HEAD>
Pinned deps: hypernetx==1.2  POT==0.8.0

HyperCOT functions called
-------------------------
``hypercot.hypercot_distance(H1, H2)`` where ``H1``, ``H2`` are
:class:`hypernetx.Hypergraph` objects (HyperNetX v1.2 API).

.. note::
    Verify the exact function name against the upstream source when the
    ``isalhg-hypercot`` env is first built (network access required).
    If the function is named differently (e.g. ``hypercot.distance`` or a
    class-based API), update only this file and re-run the end-to-end tests.

Authorship boundary
-------------------
The ONLY code authored by the IsalHG project is the serialise/deserialise
glue (``load_corpus`` and ``write_matrix``).  HyperCOT itself is imported
unmodified.

Invocation
----------
::

    ~/.conda/envs/isalhg-hypercot/bin/python \\
        scripts/hypercot_worker.py <input_json> <output_json>

Input schema  (see :func:`isalhg.metric_space.representations.subprocess_base._serialise_corpus`)::

    {
        "corpus": [
            {
                "n_nodes": <int>,
                "n_vertex_labels": <int>,
                "n_edge_labels": <int>,
                "vertex_labels": [<int>, ...],
                "edge_members": [[<int>, ...], ...]
            },
            ...
        ]
    }

Output schema::

    {"matrix": [[<float>, ...], ...]}

The output matrix is (N x N), symmetric, zero-diagonal.
"""

from __future__ import annotations

import json
import sys


def load_corpus(path: str) -> list:
    """Load and convert serialised corpus to HyperNetX 1.2 hypergraphs.

    Parameters
    ----------
    path : str
        Path to the JSON input file.

    Returns
    -------
    list of hypernetx.Hypergraph
        One hypergraph per item in the corpus.
    """
    import hypernetx as hnx  # v1.2 — pinned in isalhg-hypercot

    with open(path) as f:
        data = json.load(f)

    corpus = []
    for item in data["corpus"]:
        # HyperNetX 1.2 Hypergraph: dict mapping edge_id -> iterable of nodes.
        edges = {i: members for i, members in enumerate(item["edge_members"])}
        H = hnx.Hypergraph(edges)
        corpus.append(H)
    return corpus


def compute_matrix(corpus: list) -> list[list[float]]:
    """Compute the pairwise HyperCOT distance matrix.

    Parameters
    ----------
    corpus : list of hypernetx.Hypergraph
        The hypergraphs to compare.

    Returns
    -------
    list of list of float
        Dense symmetric (N x N) distance matrix.
    """
    import hypercot  # installed from samirchowdhury/HyperCOT

    n = len(corpus)
    matrix: list[list[float]] = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = float(hypercot.hypercot_distance(corpus[i], corpus[j]))
            matrix[i][j] = d
            matrix[j][i] = d
    return matrix


def write_matrix(matrix: list[list[float]], path: str) -> None:
    """Write the distance matrix to a JSON output file.

    Parameters
    ----------
    matrix : list of list of float
        Dense (N x N) distance matrix.
    path : str
        Destination file path.
    """
    with open(path, "w") as f:
        json.dump({"matrix": matrix}, f)


def main(input_path: str, output_path: str) -> None:
    corpus = load_corpus(input_path)
    matrix = compute_matrix(corpus)
    write_matrix(matrix, output_path)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.stderr.write(f"Usage: {sys.argv[0]} <input_json> <output_json>\n")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
