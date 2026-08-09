"""Does every intermediate string on a Levenshtein alignment path decode?

Takes pairs of design hypergraphs, computes w*_c token sequences, walks an
optimal Levenshtein alignment path, and decodes EVERY intermediate via S2H.

Reports per intermediate:
  - decodes without error?
  - resulting (n, m), connected?
  - is the intermediate itself canonical (w*_c(S2H(u)) == u)?
  - d_I to each endpoint (in the *canonical image*, i.e. after re-canonicalising)
"""

from __future__ import annotations

import warnings

import numpy as np

warnings.filterwarnings("ignore")

from isalhg.core.canonical import canonical_string, required_k
from isalhg.core.instructions import parse, serialize
from isalhg.core.string_to_hypergraph import string_to_hypergraph
from isalhg.datasets.synthetic.known_design_catalog import _make_all_designs


def align_path(a: tuple, b: tuple) -> list[tuple]:
    """Return the sequence of token tuples along one optimal Levenshtein path."""
    na, nb = len(a), len(b)
    dp = np.zeros((na + 1, nb + 1), dtype=int)
    dp[:, 0] = np.arange(na + 1)
    dp[0, :] = np.arange(nb + 1)
    for i in range(1, na + 1):
        for j in range(1, nb + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[i, j] = min(dp[i - 1, j] + 1, dp[i, j - 1] + 1, dp[i - 1, j - 1] + cost)
    # backtrace -> list of ops
    ops, i, j = [], na, nb
    while i > 0 or j > 0:
        if i > 0 and j > 0 and dp[i, j] == dp[i - 1, j - 1] + (0 if a[i - 1] == b[j - 1] else 1):
            ops.append(("sub" if a[i - 1] != b[j - 1] else "eq", i - 1, j - 1))
            i, j = i - 1, j - 1
        elif i > 0 and dp[i, j] == dp[i - 1, j] + 1:
            ops.append(("del", i - 1, None))
            i -= 1
        else:
            ops.append(("ins", None, j - 1))
            j -= 1
    ops.reverse()
    # apply ops left to right, emitting the string after each non-eq op
    cur, states = list(a), [tuple(a)]
    pos = 0
    for kind, ia, jb in ops:
        if kind == "eq":
            pos += 1
        elif kind == "sub":
            cur[pos] = b[jb]
            pos += 1
            states.append(tuple(cur))
        elif kind == "del":
            del cur[pos]
            states.append(tuple(cur))
        else:
            cur.insert(pos, b[jb])
            pos += 1
            states.append(tuple(cur))
    assert tuple(cur) == tuple(b), "alignment did not reach target"
    return states


def is_connected(H) -> bool:
    edges = [set(H.members(e)) for e in H.edges()]
    nodes = set(H.nodes())
    if not nodes:
        return True
    seen, stack = {next(iter(nodes))}, [next(iter(nodes))]
    while stack:
        v = stack.pop()
        for e in edges:
            if v in e:
                for u in e:
                    if u not in seen:
                        seen.add(u)
                        stack.append(u)
    return seen == nodes


def main():
    designs = {e.item_id: H for e, H in _make_all_designs()}
    pairs = [
        ("sts7", "tight_cycle_k3"),
        ("loose_path_k3", "tight_path_k3"),
        ("sts9", "gq22"),
        ("tight_path_k4", "loose_cycle_k4"),
        ("tight_cycle_k5", "loose_path_k5"),
    ]
    n_ok = n_tot = n_conn = n_canon = 0
    print(f"{'pair':<34}{'d_I':>5}{'steps':>7}{'decode':>8}{'conn':>7}{'canon':>7}")
    detail_rows = []
    for a_id, b_id in pairs:
        Ha, Hb = designs[a_id], designs[b_id]
        k = max(required_k(Ha), required_k(Hb))
        wa, wb = canonical_string(Ha, k=k), canonical_string(Hb, k=k)
        ta, tb = tuple(parse(wa)), tuple(parse(wb))
        states = align_path(ta, tb)
        d = len(states) - 1
        ok = conn = canon = 0
        for si, st in enumerate(states):
            n_tot += 1
            try:
                Hi = string_to_hypergraph(serialize(st), k=k, backend="python")
                ok += 1
                n_ok += 1
                c = is_connected(Hi)
                conn += c
                n_conn += c
                wi = canonical_string(Hi, k=k)
                isc = tuple(parse(wi)) == st
                canon += isc
                n_canon += isc
                if (a_id, b_id) == pairs[0]:
                    detail_rows.append((si, len(st), Hi.n_nodes, Hi.n_edges, c, isc))
            except Exception as exc:
                print(f"    DECODE FAILURE at step {si}: {type(exc).__name__}: {exc}")
        print(
            f"{a_id + '->' + b_id:<34}{d:>5}{len(states):>7}"
            f"{str(ok) + '/' + str(len(states)):>8}"
            f"{str(conn) + '/' + str(len(states)):>7}"
            f"{str(canon) + '/' + str(len(states)):>7}"
        )

    print(
        f"\nTOTAL: decoded {n_ok}/{n_tot} | connected {n_conn}/{n_tot} | "
        f"already-canonical {n_canon}/{n_tot} ({100 * n_canon / n_tot:.1f}%)"
    )

    print(f"\n=== detail: {pairs[0][0]} -> {pairs[0][1]} ===")
    print(f"{'step':>5}{'|w|':>6}{'n':>5}{'m':>5}{'conn':>6}{'canonical':>11}")
    for si, lw, nn, ee, c, isc in detail_rows:
        print(f"{si:>5}{lw:>6}{nn:>5}{ee:>5}{str(bool(c)):>6}{str(bool(isc)):>11}")


if __name__ == "__main__":
    main()
