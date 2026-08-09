import time, collections, sys
from isalhg.datasets.registry import get_dataset
t=time.perf_counter()
ds = get_dataset("sts_catalog", {})
items = list(ds)
print(f"catalog loaded in {time.perf_counter()-t:.1f}s, {len(items)} items", flush=True)
by = collections.Counter()
for it in items:
    H = it.hypergraph
    by[(H.n_nodes, H.n_edges)] += 1
for k in sorted(by): print(f"  n={k[0]:>3} m={k[1]:>3}  {by[k]:>3} iso-classes", flush=True)
from isalhg.core.canonical import canonical_string
for target in [(7,7),(9,12),(13,26),(15,35)]:
    sel=[it for it in items if (it.hypergraph.n_nodes,it.hypergraph.n_edges)==target]
    if not sel:
        print(f"n={target[0]}: none", flush=True); continue
    H=sel[0].hypergraph
    t=time.perf_counter()
    w=canonical_string(H, k=3)
    print(f"n={target[0]} m={target[1]}: |w*_c|={len(w)} in {time.perf_counter()-t:.2f}s ({len(sel)} classes)", flush=True)
