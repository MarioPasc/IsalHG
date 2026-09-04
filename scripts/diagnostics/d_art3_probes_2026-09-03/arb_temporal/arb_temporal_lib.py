"""Shared loading / windowing / star-KB machinery for the ARB temporal probe.

Star knowledge base ``S_t(v)``: the set of *distinct* simplices containing ``v``
whose timestamp falls in window ``t``, read as a hypergraph whose vertex set is
the union of those simplices. Every hyperedge contains ``v``, so every star KB
is connected by construction.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

import numpy as np

ROOT = "/media/mpascual/Sandisk2TB/research/ISAL/isalhg/data/arb_benson/temporal"
LABELED_ROOT = "/media/mpascual/Sandisk2TB/research/ISAL/isalhg/data/arb_benson/labeled"
OUT = os.path.dirname(os.path.abspath(__file__))

MS_CANDS = [
    ("day", 86_400_000),
    ("week", 604_800_000),
    ("month", 2_629_746_000),
    ("quarter", 7_889_238_000),
    ("year", 31_556_952_000),
]
S_CANDS = [
    ("day", 86_400),
    ("week", 604_800),
    ("month", 2_629_746),
    ("quarter", 7_889_238),
    ("year", 31_556_952),
]
CONTACT_CANDS = [
    ("5min", 300),
    ("15min", 900),
    ("hour", 3_600),
    ("4hour", 14_400),
    ("day", 86_400),
]
MS_REL_CANDS = [("hour", 3_600_000)] + MS_CANDS

DATASETS: dict[str, dict] = {
    "email-Enron": dict(unit="ms since year 0", cands=MS_CANDS),
    "email-Eu": dict(unit="s (Unix epoch)", cands=S_CANDS),
    "contact-high-school": dict(unit="s (20 s resolution)", cands=CONTACT_CANDS),
    "contact-primary-school": dict(unit="s (20 s resolution)", cands=CONTACT_CANDS),
    "DAWN": dict(
        unit="quarter code (year*4+quarter)",
        cands=[("quarter", 1), ("year", 4), ("2year", 8)],
    ),
    "NDC-classes": dict(unit="ms since year 0", cands=MS_CANDS),
    "NDC-substances": dict(unit="ms since year 0", cands=MS_CANDS),
    "tags-math-sx": dict(unit="ms (relative)", cands=MS_REL_CANDS),
    "tags-ask-ubuntu": dict(unit="ms (relative)", cands=MS_REL_CANDS),
    "threads-ask-ubuntu": dict(unit="ms (relative)", cands=MS_REL_CANDS),
    "coauth-MAG-History": dict(
        unit="year", cands=[("year", 1), ("2year", 2), ("5year", 5), ("10year", 10)]
    ),
    "congress-bills": dict(
        unit="days since year 0",
        cands=[("month", 30), ("quarter", 91), ("year", 365), ("2year", 730)],
    ),
}

# priority order set by the coordinator (2026-09-04)
PRIORITY = [
    "email-Enron",
    "contact-high-school",
    "email-Eu",
    "DAWN",
    "NDC-classes",
    "contact-primary-school",
    "NDC-substances",
    "tags-math-sx",
    "tags-ask-ubuntu",
    "threads-ask-ubuntu",
    "coauth-MAG-History",
    "congress-bills",
]

ENV_N, ENV_M = 24, 110
K_MAX = 10  # compiled encoder ceiling on hyperedge arity
SEED = 20260903


def read_ints(path: str) -> np.ndarray:
    """Read a whitespace-separated integer file into an int64 array."""
    with open(path) as fh:
        data = fh.read()
    return np.array(data.split(), dtype=np.int64)


@dataclass
class Corpus:
    name: str
    n_simplices: int
    n_nodes: int  # max node id + 1 (ids are 1-based in ARB)
    times: np.ndarray  # int64, per original simplex
    orig_sid: np.ndarray  # canonical simplex id per original simplex
    c_indptr: np.ndarray  # canonical (deduplicated) simplex CSR
    c_members: np.ndarray
    c_arity: np.ndarray
    node_names: dict[int, str] = field(default_factory=dict)

    @property
    def n_canon(self) -> int:
        return len(self.c_arity)


def load(name: str) -> Corpus:
    base = os.path.join(ROOT, name, name)
    nverts = read_ints(base + "-nverts.txt")
    flat = read_ints(base + "-simplices.txt")
    times = read_ints(base + "-times.txt")
    assert len(nverts) == len(times), (len(nverts), len(times))
    assert nverts.sum() == len(flat), (nverts.sum(), len(flat))

    indptr = np.zeros(len(nverts) + 1, dtype=np.int64)
    np.cumsum(nverts, out=indptr[1:])

    lut: dict[bytes, int] = {}
    orig_sid = np.empty(len(nverts), dtype=np.int64)
    c_members_l: list[np.ndarray] = []
    c_arity_l: list[int] = []
    flat_l = flat.tolist()
    ip = indptr.tolist()
    for i in range(len(nverts)):
        t = sorted(set(flat_l[ip[i] : ip[i + 1]]))
        key = np.array(t, dtype=np.int64).tobytes()
        sid = lut.get(key)
        if sid is None:
            sid = len(c_arity_l)
            lut[key] = sid
            c_members_l.append(np.array(t, dtype=np.int64))
            c_arity_l.append(len(t))
        orig_sid[i] = sid
    c_arity = np.array(c_arity_l, dtype=np.int64)
    c_indptr = np.zeros(len(c_arity) + 1, dtype=np.int64)
    np.cumsum(c_arity, out=c_indptr[1:])
    c_members = np.concatenate(c_members_l) if c_members_l else np.zeros(0, dtype=np.int64)

    names: dict[int, str] = {}
    lab = base + "-node-labels.txt"
    if os.path.exists(lab):
        with open(lab, errors="replace") as fh:
            for line in fh:
                line = line.rstrip("\n")
                if not line:
                    continue
                parts = line.split(None, 1)
                try:
                    names[int(parts[0])] = parts[1] if len(parts) > 1 else ""
                except ValueError:
                    continue

    return Corpus(
        name=name,
        n_simplices=len(nverts),
        n_nodes=int(flat.max()) + 1,
        times=times,
        orig_sid=orig_sid,
        c_indptr=c_indptr,
        c_members=c_members,
        c_arity=c_arity,
        node_names=names,
    )


def ragged_positions(starts: np.ndarray, lens: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Expand ragged groups. Returns (source positions, group ids)."""
    tot = int(lens.sum())
    if tot == 0:
        return np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int64)
    gs = np.zeros(len(lens), dtype=np.int64)
    np.cumsum(lens[:-1], out=gs[1:])
    res = np.ones(tot, dtype=np.int64)
    res[gs[0]] = starts[0]
    if len(lens) > 1:
        res[gs[1:]] = starts[1:] - (starts[:-1] + lens[:-1] - 1)
    pos = np.cumsum(res)
    gid = np.repeat(np.arange(len(lens), dtype=np.int64), lens)
    return pos, gid


@dataclass
class Groups:
    """All non-empty star KBs at one granularity."""

    n_windows: int
    key: np.ndarray  # node * n_windows + window, sorted ascending, unique
    node: np.ndarray
    window: np.ndarray
    m: np.ndarray
    n: np.ndarray
    max_arity: np.ndarray
    gstart: np.ndarray  # index into usid of the first pair of each group
    usid: np.ndarray  # canonical simplex ids, grouped
    inter: np.ndarray  # |S_t(v) cap S_{t+1}(v)|, aligned with key


def build_groups(c: Corpus, step: int, with_full: bool = True) -> Groups:
    w = (c.times - c.times.min()) // step
    nw = int(w.max()) + 1
    ns = c.n_canon

    arity_o = c.c_arity[c.orig_sid]
    pos, gid = ragged_positions(c.c_indptr[c.orig_sid], arity_o)
    nodes = c.c_members[pos]
    wins = w[gid]
    sids = c.orig_sid[gid]
    del pos, gid

    key_all = nodes * nw + wins
    pair = key_all * ns + sids
    del key_all, nodes, wins, sids
    upair = np.unique(pair)
    del pair
    ukey = upair // ns
    usid = upair % ns
    del upair

    bnd = np.flatnonzero(np.diff(ukey)) + 1
    gstart = np.concatenate(([0], bnd))
    gend = np.concatenate((bnd, [len(ukey)]))
    key = ukey[gstart]
    m = (gend - gstart).astype(np.int64)
    gid_pair = np.repeat(np.arange(len(gstart), dtype=np.int64), m)

    ar = c.c_arity[usid]
    max_arity = np.maximum.reduceat(ar, gstart)

    if with_full:
        pos2, g2 = ragged_positions(c.c_indptr[usid], ar)
        mem = c.c_members[pos2]
        gg = gid_pair[g2]
        enc = gg * c.n_nodes + mem
        uenc = np.unique(enc)
        n = np.bincount(uenc // c.n_nodes, minlength=len(gstart)).astype(np.int64)
        del pos2, g2, mem, gg, enc, uenc
    else:
        n = np.zeros(len(gstart), dtype=np.int64)

    node = key // nw
    window = key % nw

    # |A cap B| for consecutive windows of the same node
    node_p = ukey // nw
    win_p = ukey % nw
    k2 = node_p * ns + usid
    order = np.lexsort((win_p, k2))
    k2s, wps = k2[order], win_p[order]
    if len(k2s) > 1:
        same = (k2s[1:] == k2s[:-1]) & (wps[1:] == wps[:-1] + 1)
        idx = np.flatnonzero(same)
        hit_key = (k2s[idx] // ns) * nw + wps[idx]
    else:
        hit_key = np.zeros(0, dtype=np.int64)
    inter = np.zeros(len(key), dtype=np.int64)
    if len(hit_key):
        loc = np.searchsorted(key, hit_key)
        np.add.at(inter, loc, 1)

    return Groups(nw, key, node, window, m, n, max_arity, gstart, usid, inter)


def pct(a: np.ndarray) -> dict[str, float | None]:
    if len(a) == 0:
        return {k: None for k in ("min", "p25", "med", "p75", "p90", "max")}
    q = np.percentile(a, [25, 50, 75, 90])
    return dict(
        min=int(a.min()),
        p25=float(q[0]),
        med=float(q[1]),
        p75=float(q[2]),
        p90=float(q[3]),
        max=int(a.max()),
    )


def kb_edges(c: Corpus, g: Groups, gi: int) -> list[list[int]]:
    s = g.gstart[gi]
    e = g.gstart[gi + 1] if gi + 1 < len(g.gstart) else len(g.usid)
    return [c.c_members[c.c_indptr[sid] : c.c_indptr[sid + 1]].tolist() for sid in g.usid[s:e]]


def dump(obj, path: str) -> None:
    with open(path, "w") as fh:
        json.dump(obj, fh, default=lambda o: int(o) if isinstance(o, np.integer) else float(o))
