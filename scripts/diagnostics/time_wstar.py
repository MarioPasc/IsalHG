"""Time canonical_string on one hypergraph loaded from a JSON edge list.

Usage: python time_wstar.py <path.json>
Prints: TIMING <label> |w|=<len> t=<sec>s rss=<MB>MB
"""

import json
import resource
import sys
import time

from isalhg.core.canonical import canonical_string
from isalhg.core.sparse_hypergraph import SparseHypergraph


def main() -> None:
    path = sys.argv[1]
    with open(path) as f:
        spec = json.load(f)
    H = SparseHypergraph(spec["n"], [frozenset(e) for e in spec["edges"]])
    assert H.n_edges == len(spec["edges"]), "duplicate edge dropped on load"
    t0 = time.perf_counter()
    w = canonical_string(H, k=3)
    dt = time.perf_counter() - t0
    rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    print(f"TIMING {spec['label']} |w|={len(w)} t={dt:.2f}s rss={rss_mb:.0f}MB", flush=True)


if __name__ == "__main__":
    main()
