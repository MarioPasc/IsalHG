"""Token-length of w*_c vs vertex count: settles the d_I per-pair cost question."""

import random

from isalhg.core.canonical import canonical_string
from isalhg.core.instructions import parse
from isalhg.datasets.synthetic._random_hg import random_connected_hypergraph

print(f"{'n':>3} {'m':>3} {'chars':>6} {'tokens':>7} {'tok^2':>8} {'n^3':>7}")
for n, m in [(6, 8), (8, 10), (10, 20), (12, 20), (15, 20)]:
    rng = random.Random(0)
    H, _ = random_connected_hypergraph(n_nodes=n, n_edges=m, arity_range=(3, 3), rng=rng)
    w = canonical_string(H, algorithm="canonical")
    t = len(tuple(parse(w)))
    print(f"{n:>3} {m:>3} {len(w):>6} {t:>7} {t * t:>8} {n**3:>7}")
