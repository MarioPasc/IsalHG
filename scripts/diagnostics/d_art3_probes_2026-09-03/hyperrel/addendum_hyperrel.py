"""Addendum: census restricted to genuinely n-ary in-envelope KBs (max arity >= 3),
and the qualifier-folded edge-label census, per collection."""

from __future__ import annotations

from collections import Counter

from probe_hyperrel import (
    COLLECTIONS,
    ENV_M,
    ENV_N,
    K_MAX,
    MIN_STATEMENTS,
    build_star,
    load,
    star_spec,
)


def main() -> None:
    from isalhg.core.sparse_hypergraph import SparseHypergraph
    from isalhg.iso_backends.pynauty_levi import PynautyLeviBackend

    backend = PynautyLeviBackend()
    print(
        "| collection | in-env n-ary KBs | labelled classes | singletons | top-10 share | "
        "folded-label classes | folded labels used |"
    )
    print("|---|---|---|---|---|---|---|")
    for name, kind, files in COLLECTIONS:
        stmts = load(name, kind, files)
        rel_ids = {r: i for i, r in enumerate(sorted({s.relation for s in stmts}))}
        fold_ids = {r: i for i, r in enumerate(sorted({s.folded_label for s in stmts}))}
        by: dict[str, list] = {}
        for s in stmts:
            by.setdefault(s.subject, []).append(s)
        stars = [build_star(e, ss) for e, ss in by.items() if len(ss) >= MIN_STATEMENTS]
        env = [
            s
            for s in stars
            if s.n <= ENV_N and s.m <= ENV_M and s.max_arity <= K_MAX and s.max_arity >= 3
        ]
        fps: Counter = Counter()
        fps_f: Counter = Counter()
        used: set[int] = set()
        for st in env:
            for ids, sink in ((rel_ids, fps), (fold_ids, fps_f)):
                verts = sorted({v for s in st.statements for v in s.vertices})
                vid = {v: i for i, v in enumerate(verts)}
                seen: set = set()
                edges, labs = [], []
                for s in st.statements:
                    mem = frozenset(vid[v] for v in s.vertices)
                    lab = ids[s.relation if ids is rel_ids else s.folded_label]
                    if (lab, mem) in seen:
                        continue
                    seen.add((lab, mem))
                    edges.append(sorted(mem))
                    labs.append(lab)
                    if ids is fold_ids:
                        used.add(lab)
                H = SparseHypergraph(
                    len(verts),
                    [frozenset(e) for e in edges],
                    n_edge_labels=max(ids.values()) + 1,
                    edge_labels=labs,
                )
                sink[backend.fingerprint(H)] += 1
        top = sum(c for _, c in fps.most_common(10))
        print(
            f"| {name} | {len(env):,} | {len(fps):,} ({len(fps) / max(1, len(env)):.3f}/KB) | "
            f"{sum(1 for c in fps.values() if c == 1):,} | {100 * top / max(1, len(env)):.1f} % | "
            f"{len(fps_f):,} | {len(used):,} of {len(fold_ids):,} |"
        )
        _ = star_spec  # keep import used


if __name__ == "__main__":
    main()
