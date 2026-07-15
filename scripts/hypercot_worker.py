"""HyperCOT corpus worker — runs inside the ``isalhg-hypercot`` pinned env.

Upstream repository
-------------------
URL:         https://github.com/samirchowdhury/HyperCOT
Licence:     MIT
Commit hash: f190266  (HEAD when isalhg-hypercot was built)
Pinned deps: hypernetx==1.2  POT==0.8.0  numpy==1.23.5  scipy==1.9.3

Version-constraint rationale
----------------------------
* **scipy==1.9.3** — POT 0.8.0 calls
  ``scipy.optimize.linesearch.scalar_search_armijo``, which was removed in
  scipy 1.10.  Any newer scipy version breaks the import.
* **numpy==1.23.5** (< 1.24) — ``hypercot.get_omega`` uses integer array
  indexing that raises ``IndexError`` under NumPy 1.24+ strict integer
  enforcement.

HyperCOT functions called
-------------------------
All from ``hypercot.py`` (two flat files; no setup.py — both copied to
site-packages):

Per hypergraph ``h``:

* ``hypercot.get_hgraph_dual(h)`` → dual ``d``
* ``hypercot.convert_to_line_graph(h.incidence_dict)`` → line-graph ``l``
* ``hypercot.get_v(h.incidence_dict, d.incidence_dict)``
  → weight vector ``v``, length = number of hyperedges
* ``hypercot.get_omega(h, d, l, 'jaccard_index')``
  → coupling matrix ``omega``, shape ``(n_nodes, n_edges)``
  (``weight_type='jaccard_index'`` matches ``run_simulated.ipynb``)

Per pair ``(h_i, h_j)``:

* ``cot.cot_numpy(omega_i, omega_j, v1=v_i, v2=v_j, niter=100,
                  log=True, verbose=False)``
  → 4-tuple ``(Ts, Tv, cost_scalar, log_dict)``
  ``out[2]`` is the scalar COOT cost (≡ ``out[3]['cost'][-1]``).
  ``niter=100`` matches the paper notebook.

Naming convention required by ``get_omega``
--------------------------------------------
Nodes **must** be strings ``"0"``.."``str(n-1)``"; edges **must** be integers
``0``..``m-1``.  Build each HyperNetX 1.2 hypergraph as::

    hnx.Hypergraph(
        {edge_int: [str(v) for v in members]
         for edge_int, members in enumerate(edge_members)}
    )

Authorship boundary
-------------------
The ONLY code authored by the IsalHG project is the serialise/deserialise
glue (``load_corpus``, ``_precompute``, ``compute_matrix``, ``write_matrix``).
``hypercot`` and ``cot`` run unmodified.

Invocation
----------
::

    ~/.conda/envs/isalhg-hypercot/bin/python \\
        scripts/hypercot_worker.py <input_json> <output_json>

Input schema (``isalhg.metric_space.representations.subprocess_base._serialise_corpus``)::

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

The matrix is (N x N), symmetric, zero-diagonal.
"""

from __future__ import annotations

import json
import sys


def load_corpus(path: str) -> list:
    """Load corpus JSON and return HyperNetX 1.2 Hypergraph objects.

    Applies the naming convention required by ``hypercot.get_omega``:
    nodes become strings ``"0"``.."``str(n-1)``", edges become integers.

    Parameters
    ----------
    path : str
        Path to the input JSON file.

    Returns
    -------
    list of hypernetx.Hypergraph
    """
    import hypernetx as hnx  # v1.2 — pinned in isalhg-hypercot

    with open(path) as f:
        data = json.load(f)

    corpus = []
    for item in data["corpus"]:
        # Nodes as str, edges as int — required by get_omega's adjacency logic.
        edges = {
            edge_int: [str(v) for v in members]
            for edge_int, members in enumerate(item["edge_members"])
        }
        corpus.append(hnx.Hypergraph(edges))
    return corpus


def _precompute(h: object) -> tuple:
    """Compute ``(omega, v)`` for a single HyperNetX 1.2 hypergraph.

    Parameters
    ----------
    h : hypernetx.Hypergraph

    Returns
    -------
    omega : numpy.ndarray, shape (n_nodes, n_edges)
    v : numpy.ndarray, shape (n_edges,)
    """
    import hypercot as hc  # copied to site-packages from HyperCOT repo

    d = hc.get_hgraph_dual(h)
    line_graph = hc.convert_to_line_graph(h.incidence_dict)
    v = hc.get_v(h.incidence_dict, d.incidence_dict)
    omega = hc.get_omega(h, d, line_graph, "jaccard_index")
    return omega, v


def compute_matrix(corpus: list) -> list[list[float]]:
    """Compute the pairwise COOT distance matrix over the corpus.

    Pre-computes ``(omega, v)`` once per hypergraph, then fills the upper
    triangle of the symmetric N×N matrix via ``cot.cot_numpy``.

    Parameters
    ----------
    corpus : list of hypernetx.Hypergraph

    Returns
    -------
    list of list of float
        Dense symmetric (N x N) distance matrix; diagonal entries are 0.
    """
    import cot as cot_mod  # copied to site-packages from HyperCOT repo

    n = len(corpus)
    precomputed = [_precompute(h) for h in corpus]

    matrix: list[list[float]] = [[0.0] * n for _ in range(n)]
    for i in range(n):
        omega_i, v_i = precomputed[i]
        for j in range(i + 1, n):
            omega_j, v_j = precomputed[j]
            # out = (Ts, Tv, cost_scalar, log_dict); out[2] is the COOT cost.
            out = cot_mod.cot_numpy(
                omega_i,
                omega_j,
                v1=v_i,
                v2=v_j,
                niter=100,
                log=True,
                verbose=False,
            )
            d = float(out[2])
            matrix[i][j] = d
            matrix[j][i] = d
    return matrix


def write_matrix(matrix: list[list[float]], path: str) -> None:
    """Write the distance matrix as JSON.

    Parameters
    ----------
    matrix : list of list of float
    path : str
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
