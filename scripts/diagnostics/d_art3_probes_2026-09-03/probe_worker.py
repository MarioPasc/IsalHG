"""Single-instance canonicalization worker for the WD50K probe.

Reads a hypergraph spec as JSON on stdin, computes the tie-complete canonical
string with the C++ backend, and prints wall-clock and token length as JSON.
Run in a subprocess so a non-terminating instance cannot hang the driver.
"""

from __future__ import annotations

import json
import sys
import time


def main() -> None:
    spec = json.load(sys.stdin)
    from isalhg.core.canonical import canonical_string, required_k
    from isalhg.core.instructions import parse
    from isalhg.core.sparse_hypergraph import SparseHypergraph

    H = SparseHypergraph(
        spec["n_nodes"],
        [frozenset(e) for e in spec["edges"]],
        n_edge_labels=spec["n_edge_labels"],
        edge_labels=spec["edge_labels"],
    )
    k = required_k(H)
    t0 = time.perf_counter()
    w = canonical_string(H, k=k, algorithm="canonical", backend="cpp")
    wall = time.perf_counter() - t0
    json.dump({"wall_s": wall, "tokens": len(parse(w)), "k": k}, sys.stdout)


if __name__ == "__main__":
    main()
