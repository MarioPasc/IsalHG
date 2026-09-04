"""Can the labeled/ class labels be joined onto the temporal/ node ids?

The labeled/ family is the deduplicated hyperedge set of the temporal corpus. If
the node ids agree, the per-node distinct-simplex degree vectors must be equal
entry by entry; agreement only up to a permutation would show as equal sorted
vectors with a non-zero mismatch count.
"""

from __future__ import annotations

import json
import os
from collections import Counter

import arb_temporal_lib as L
import numpy as np

out = {}
for ds in ("contact-high-school", "contact-primary-school"):
    c = L.load(ds)
    deg_t = Counter(c.c_members.tolist())
    path = os.path.join(L.LABELED_ROOT, ds, f"hyperedges-{ds}.txt")
    deg_l: Counter = Counter()
    n_edges = 0
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            n_edges += 1
            for tok in line.split(","):
                deg_l[int(tok)] += 1
    nl = os.path.join(L.LABELED_ROOT, ds, f"node-labels-{ds}.txt")
    labels = [int(x) for x in open(nl).read().split()]
    names = open(os.path.join(L.LABELED_ROOT, ds, f"label-names-{ds}.txt")).read().split()
    ids = sorted(set(deg_t) | set(deg_l))
    vt = np.array([deg_t.get(i, 0) for i in ids])
    vl = np.array([deg_l.get(i, 0) for i in ids])
    rec = dict(
        dataset=ds,
        temporal_distinct_simplices=c.n_canon,
        labeled_hyperedges=n_edges,
        nodes_temporal=len(deg_t),
        nodes_labeled=len(deg_l),
        n_node_label_entries=len(labels),
        n_classes=len(names),
        class_names=names,
        identical_degree_vector=bool((vt == vl).all()),
        equal_as_multiset=sorted(vt.tolist()) == sorted(vl.tolist()),
        n_mismatching_ids=int((vt != vl).sum()),
    )
    out[ds] = rec
    print(json.dumps({k: v for k, v in rec.items() if k != "class_names"}), flush=True)

with open(os.path.join(L.OUT, "contact_join.json"), "w") as fh:
    json.dump(out, fh, indent=1)
